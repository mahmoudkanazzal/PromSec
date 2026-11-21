"""The generator output must reach the LLM, and the training loss must reward
CWE reduction and similarity (Eqs. 4-5 with e(z) = exp(z))."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import torch
from torch_geometric.data import Data

from promsec.llm import LLMClient
from promsec.metrics import validate_python_source
from promsec.model import Generator
from promsec.runner import run_iteration
from promsec.security import scan_cwes
from promsec.train import compute_contrastive_loss
from utils import (
    NODE_FEATURE_DIM,
    bandit_findings,
    build_reconstruction_prompt,
    cfg_to_pyg_data,
    extract_graph_from_pyg_data,
    generate_cfg_from_source,
    node_change_scores,
    security_node_labels,
    serialize_cfg,
)

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = (
    "import os\n"
    "import subprocess\n"
    "\n"
    "def run(user):\n"
    "    path = '/tmp/' + user\n"
    "    subprocess.call('ls ' + path, shell=True)\n"
    "    return path\n"
)


def _shifted(x: torch.Tensor, row: int, amount: float = 0.6) -> torch.Tensor:
    updated = x.clone()
    updated[row] += amount
    return updated


class GraphExtractionTests(unittest.TestCase):
    def test_node_values_survive_extraction(self):
        edge_index = torch.tensor([[0], [1]], dtype=torch.long)
        before = extract_graph_from_pyg_data(Data(x=torch.zeros(2, 3), edge_index=edge_index))
        after = extract_graph_from_pyg_data(Data(x=torch.ones(2, 3), edge_index=edge_index))
        self.assertEqual(set(before.edges()), set(after.edges()))
        self.assertNotEqual(before.nodes[0]["x"], after.nodes[0]["x"])

    def test_feature_rows_match_cfg_nodes(self):
        graph = generate_cfg_from_source(PROGRAM)
        data = cfg_to_pyg_data(graph)
        self.assertEqual(tuple(data.x.shape), (graph.number_of_nodes(), NODE_FEATURE_DIM))
        self.assertEqual(tuple(data.raw_features.shape), (graph.number_of_nodes(), 4))


class PromptTests(unittest.TestCase):
    def setUp(self):
        self.graph = generate_cfg_from_source(PROGRAM)
        self.x = cfg_to_pyg_data(self.graph).x
        self.nodes = list(self.graph.nodes())
        self.call_row = next(i for i, n in enumerate(self.nodes) if "subprocess.call" in self.graph.nodes[n]["code"] and self.graph.nodes[n]["ast_type"] == "Expr")
        self.return_row = next(i for i, n in enumerate(self.nodes) if self.graph.nodes[n]["ast_type"] == "Return")

    def test_prompt_carries_both_graphs_and_flagged_statement(self):
        prompt, flagged = build_reconstruction_prompt(PROGRAM, self.graph, self.x, _shifted(self.x, self.call_row))
        self.assertTrue(prompt.startswith("You are a coding assistant."))
        self.assertIn("Original CFG:", prompt)
        self.assertIn("Updated CFG:", prompt)
        self.assertIn(PROGRAM, prompt)
        self.assertEqual([item["node"] for item in flagged], [self.call_row])
        self.assertIn("subprocess.call('ls ' + path, shell=True)", prompt.split("largest first):", 1)[1])

    def test_cfg_lines_carry_code(self):
        lines = serialize_cfg(self.graph).splitlines()
        self.assertEqual(len(lines), self.graph.number_of_nodes())
        self.assertTrue(all(" code: " in line for line in lines))
        self.assertIn("code: subprocess.call('ls ' + path, shell=True)", lines[self.call_row])

    def test_prompt_changes_with_generator_output(self):
        first, _ = build_reconstruction_prompt(PROGRAM, self.graph, self.x, _shifted(self.x, self.call_row))
        second, _ = build_reconstruction_prompt(PROGRAM, self.graph, self.x, _shifted(self.x, self.return_row))
        unchanged, flagged = build_reconstruction_prompt(PROGRAM, self.graph, self.x, self.x.clone())
        self.assertNotEqual(first, second)
        self.assertNotEqual(first, unchanged)
        self.assertEqual(flagged, [])

    def test_vet_code_sends_generator_output_to_llm(self):
        prompts = []

        def transport(prompt, model, temperature):
            prompts.append(prompt)
            if prompt.startswith("Estimate a detailed prompt"):
                return "Write a Python function run(user) that lists a directory safely.", 5, 5
            return "def run(user):\n    return user\n", 5, 5

        class Shift(torch.nn.Module):
            def __init__(self, row):
                super().__init__()
                self.row = row

            def forward(self, x, edge_index):
                return _shifted(x, self.row), edge_index

        reconstruction_prompts = []
        for row in (self.call_row, self.return_row):
            prompts.clear()
            with tempfile.TemporaryDirectory() as tmp:
                llm = LLMClient("offline", cache_path=Path(tmp) / "cache.sqlite", transport=transport)
                step = run_iteration(PROGRAM, Shift(row), llm, torch.device("cpu"))
            self.assertEqual(len(prompts), 3)
            self.assertTrue(prompts[0].startswith("You are a coding assistant."))
            self.assertTrue(prompts[1].startswith("Estimate a detailed prompt"))
            self.assertTrue(prompts[2].startswith("In your code generation, ensure that sensitive information"))
            self.assertIn(step["optimized_prompt"], prompts[2])
            self.assertEqual(step["flagged"][0]["node"], row)
            reconstruction_prompts.append(prompts[0])
        self.assertNotEqual(reconstruction_prompts[0], reconstruction_prompts[1])


class LossTests(unittest.TestCase):
    def setUp(self):
        self.x = torch.zeros(10, NODE_FEATURE_DIM)
        self.labels = torch.zeros(10)
        self.labels[3] = 1.0
        self.negative_delta_k = torch.tensor([0.0, 1.0, -1.0])
        self.negative_similarity = torch.tensor([0.5, 0.6, 0.7])

    def loss(self, updated_x):
        return compute_contrastive_loss(
            updated_x, self.x, self.labels, 2.0, self.negative_delta_k, self.negative_similarity,
            alpha=1.0, beta=10.0, margin=0.25,
        )

    def test_changing_flagged_statement_lowers_loss(self):
        unchanged, dk0, _ = self.loss(self.x.clone())
        fixed, dk1, _ = self.loss(_shifted(self.x, 3, 0.3))
        self.assertEqual(float(dk0), 0.0)
        self.assertAlmostEqual(float(dk1), 2.0, places=5)
        self.assertLess(float(fixed), float(unchanged))

    def test_changing_clean_statement_raises_loss(self):
        unchanged, _, s0 = self.loss(self.x.clone())
        drifted, dk, s1 = self.loss(_shifted(self.x, 5, 0.3))
        self.assertEqual(float(dk), 0.0)
        self.assertLess(float(s1), float(s0))
        self.assertGreater(float(drifted), float(unchanged))

    def test_gradient_reaches_generator(self):
        updated = self.x.clone().requires_grad_(True)
        loss, _, _ = self.loss(updated + 0.01)
        loss.backward()
        self.assertGreater(float(updated.grad.abs().sum()), 0.0)


@unittest.skipIf(shutil.which("bandit") is None, "Bandit is required")
class PackagedGeneratorTests(unittest.TestCase):
    def test_finding_maps_to_innermost_statement(self):
        graph = generate_cfg_from_source(PROGRAM)
        lines, cwe_count = bandit_findings(PROGRAM)
        labels = security_node_labels(graph, lines)
        flagged = [graph.nodes[n]["ast_type"] for n, y in zip(graph.nodes(), labels.tolist()) if y]
        self.assertGreaterEqual(cwe_count, 1)
        self.assertNotIn("FunctionDef", flagged)
        self.assertIn("Expr", flagged)

    def test_input_programs_need_not_compile(self):
        # Parses but does not compile: assignment before the global declaration.
        source = "TOKEN = 'a'\n\ndef reset():\n    TOKEN = 'b'\n    global TOKEN\n    return eval(TOKEN)\n"
        with self.assertRaises(SyntaxError):
            validate_python_source(source)
        count, _ = scan_cwes(source, require_compile=False)
        self.assertGreaterEqual(count, 1)
        with self.assertRaises(SyntaxError):
            scan_cwes(source)

    def test_packaged_generator_flags_bandit_statements(self):
        generator = Generator()
        generator.load_state_dict(torch.load(ROOT / "models" / "trained_generator_cfg.pt", map_location="cpu", weights_only=True))
        generator.eval()
        hits = flagged = positives = nodes = 0
        for path in sorted((ROOT / "data" / "test").glob("*.py")):
            source = path.read_text(encoding="utf-8")
            lines, _ = bandit_findings(source)
            graph = generate_cfg_from_source(source)
            labels = security_node_labels(graph, lines)
            data = cfg_to_pyg_data(graph)
            with torch.no_grad():
                updated_x, _ = generator(data.x, data.edge_index)
            scores = node_change_scores(data.x, updated_x)
            top = [i for i in torch.argsort(scores, descending=True).tolist() if scores[i] >= 0.1][:5]
            hits += int(labels[top].sum()) if top else 0
            flagged += len(top)
            positives += int(labels.sum())
            nodes += len(labels)
        self.assertGreater(flagged, 0)
        base_rate = positives / nodes
        self.assertGreater(hits / flagged, 3 * base_rate)


if __name__ == "__main__":
    unittest.main()
