from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import tempfile
import warnings
from pathlib import Path

import torch
from torch_geometric.data import Data
from promsec.metrics import strip_code_fences
from promsec.model import Generator, Discriminator
from promsec.train import compute_contrastive_loss

warnings.filterwarnings("ignore", category=SyntaxWarning)

from evaluation.functional_similarity import extract_behavioral_contract, score_candidate_functionality
from utils import FEATURE_NAMES, NODE_FEATURE_DIM, cfg_to_tensors, generate_cfg_from_code, get_cfg_node_features

ROOT = Path(__file__).resolve().parent
TRAIN_DIR = ROOT / "data" / "training"
TEST_DIR = ROOT / "data" / "test"
GENERATOR = ROOT / "models" / "trained_generator_cfg.pt"
DISCRIMINATOR = ROOT / "models" / "trained_discriminator_cfg.pt"
NOTEBOOK = ROOT / "PromSec.ipynb"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def check_dataset(directory: Path, expected_count: int):
    files = sorted(directory.glob("*.py"))
    require(len(files) == expected_count, f"{directory}: expected {expected_count} Python files, found {len(files)}")

    nonzero_graphs = 0
    total_nodes = 0
    total_edges = 0
    feature_hits = [0, 0, 0, 0]

    for path in files:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
        graph = generate_cfg_from_code(path)
        require(graph.number_of_nodes() > 0, f"Empty graph: {path.name}")

        x, edge_index, raw = cfg_to_tensors(graph)
        require(x.shape == (graph.number_of_nodes(), NODE_FEATURE_DIM), f"x shape mismatch: {path.name}")
        require(raw.shape == (graph.number_of_nodes(), 4), f"raw feature shape mismatch: {path.name}")
        if edge_index.numel():
            require(int(edge_index.min()) >= 0, f"negative edge index: {path.name}")
            require(int(edge_index.max()) < graph.number_of_nodes(), f"edge index out of range: {path.name}")

        for node in graph.nodes():
            values = get_cfg_node_features(graph, node)
            require(len(values) == 4, f"feature width mismatch: {path.name}")
            require(all(v in (0, 1) for v in values), f"non-binary feature: {path.name}")

        hits = raw.sum(dim=0).tolist()
        feature_hits = [a + int(b) for a, b in zip(feature_hits, hits)]
        if bool(raw.any()):
            nonzero_graphs += 1
        total_nodes += graph.number_of_nodes()
        total_edges += graph.number_of_edges()

    require(nonzero_graphs > 0, f"No non-zero structural features found in {directory}")
    return {
        "files": len(files),
        "nonzero_feature_graphs": nonzero_graphs,
        "nodes": total_nodes,
        "edges": total_edges,
        "feature_hits": dict(zip(FEATURE_NAMES, feature_hits)),
    }


def check_checkpoint(path: Path, hidden: int, model):
    state = torch.load(path, map_location="cpu", weights_only=True)
    required_keys = {
        "conv1.lin_rel.weight",
        "conv1.lin_rel.bias",
        "conv1.lin_root.weight",
        "conv2.lin_rel.weight",
        "conv2.lin_rel.bias",
        "conv2.lin_root.weight",
    }
    require(required_keys <= set(state), f"Missing checkpoint tensors in {path.name}")
    require(tuple(state["conv1.lin_rel.weight"].shape) == (hidden, NODE_FEATURE_DIM), f"Unexpected first-layer shape in {path.name}")
    require(tuple(state["conv1.lin_root.weight"].shape) == (hidden, NODE_FEATURE_DIM), f"Unexpected root-layer shape in {path.name}")
    require(state["conv2.lin_rel.weight"].shape[1] == hidden, f"Unexpected second-layer shape in {path.name}")
    model.load_state_dict(state, strict=True)

    sample = generate_cfg_from_code(sorted(TRAIN_DIR.glob("*.py"))[0])
    x, edge_index, _ = cfg_to_tensors(sample)
    y = model(x, edge_index)
    if isinstance(y, tuple):
        y = y[0]
        require(y.shape == x.shape, f"Checkpoint forward shape mismatch in {path.name}")
    else:
        require(y.shape == (x.shape[0], 1), f"Checkpoint forward shape mismatch in {path.name}")
    require(bool(torch.isfinite(y).all()), f"Non-finite checkpoint output in {path.name}")
    return len(state)


def check_notebook():
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code_text = "\n".join(
        "".join(cell.get("source", []))
        for cell in nb.get("cells", [])
        if cell.get("cell_type") == "code"
    )

    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") == "code":
            require(cell.get("execution_count") is None, f"Notebook cell {i} contains an execution count")
            require(not cell.get("outputs"), f"Notebook cell {i} contains saved output")
            compile("".join(cell.get("source", [])), f"notebook-cell-{i}", "exec")

    require("TRAIN_FROM_SCRATCH = 0" in code_text, "Training is not protected by the default pretrained-mode switch")
    require("RUN_ENFORCEMENT_EVALUATION = False" in code_text, "Security evaluation default-off switch is missing")
    require("RUN_LAAJ_EVALUATION = False" in code_text, "LAAJ default-off switch is missing")

    require("gnn_feature_change" in code_text and "ast_similarity" in code_text, "PromSec comparison quantities are missing")

    namespace = {"__name__": "__main__"}
    old_cwd = Path.cwd()
    try:
        os.chdir(ROOT)
        for i, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            exec(compile(source, f"notebook-cell-{i}", "exec"), namespace)
    finally:
        os.chdir(old_cwd)

    require(len(namespace["training_graphs"]) == 500, "Notebook did not prepare 500 training graphs")
    require(len(namespace["test_graphs"]) == 100, "Notebook did not prepare 100 evaluation graphs")
    require(namespace["security_df"].empty, "Default notebook execution unexpectedly ran security evaluation")
    require(namespace["laaj_df"].empty, "Default notebook execution unexpectedly ran LAAJ evaluation")

    require(strip_code_fences("```python\nprint('ok')\n```") == "print('ok')", "Code-fence sanitizer failed")

    calls = []

    def offline_transport(prompt, model, temperature):
        calls.append(prompt)
        if prompt.startswith("Estimate a detailed prompt"):
            return "Generate a secure Python program that preserves the supplied program's behavior.", 10, 5
        return "```python\nprint('validated')\n```", 10, 5

    namespace["PROMSEC_LLM_MODEL"] = "offline-validator"
    with tempfile.TemporaryDirectory() as tmp:
        namespace["RESULTS_DIR"] = Path(tmp)
        llm = namespace["make_llm"](offline_transport)
        source = sorted(TEST_DIR.glob("*.py"))[0].read_text(encoding="utf-8")
        with torch.no_grad():
            step = namespace["run_iteration"](source, llm)
    compile(step["code"], "<offline-vetted>", "exec")
    require(step["code"] == "print('validated')", "Security-generation output normalization failed")
    require(step["feature_change"] >= 0.0, "Negative GNN feature-change value")
    require(len(calls) == 3, "An iteration did not issue reconstruction, prompt inference, and generation calls")
    require("Original CFG:" in calls[0] and "Updated CFG:" in calls[0], "Reconstruction prompt lacks the two graphs")
    require(step["flagged"], "The packaged generator flagged no statement in the first evaluation program")
    flagged_code = step["flagged"][0]["code"].splitlines()[0]
    require(flagged_code in calls[0].split("largest first):", 1)[1], "Flagged statement missing from the reconstruction prompt")

    sample_data = namespace["test_graphs"][sorted(namespace["test_graphs"])[0]]
    x = sample_data.x.detach().clone()
    updated_x, _ = namespace["generator"](x.to(namespace["device"]), sample_data.edge_index.to(namespace["device"]))
    updated_x = updated_x.detach().cpu().requires_grad_(True)
    labels = torch.zeros(x.shape[0])
    labels[0] = 1.0
    training_loss, delta_k, similarity = compute_contrastive_loss(
        updated_x, x, labels, 1.0, torch.tensor([0.0, 1.0]), torch.tensor([0.5, 0.9])
    )
    require(bool(torch.isfinite(training_loss)), "Training loss is non-finite")
    require(float(delta_k.detach()) >= 0.0 and float(similarity.detach()) <= 1.0, "Unexpected contrastive-loss terms")
    training_loss.backward()
    require(float(updated_x.grad.abs().sum()) > 0.0, "Contrastive loss does not reach the generator output")



def check_cluster_assets():
    require("api_key.txt" in (ROOT / ".gitignore").read_text(encoding="utf-8"), "api_key.txt is not ignored")
    scripts = [
        "cluster_env.sh", "gpu_preflight.sh", "setup_gpu_venv.sh", "start_or_resume.sh",
        "supervise.sh", "watch.sh", "results_watch.sh", "stop.sh",
    ]
    for name in scripts:
        path = ROOT / "scripts" / name
        require(path.is_file(), f"Missing cluster script: {name}")
        if shutil.which("bash"):
            result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            require(result.returncode == 0, f"Shell syntax error in {name}: {result.stderr}")



def check_iteration_checkpoint():
    from promsec.io import sha256_text
    from promsec.records import RESULT_SCHEMA
    from promsec.runner import _load_iteration_checkpoint, _save_iteration_checkpoint

    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp)
        (run_dir / "samples").mkdir()
        source = run_dir / "example.py"
        original = "print('source')\n"
        source.write_text(original, encoding="utf-8")
        record = {
            "schema": RESULT_SCHEMA, "file": source.name, "source_hash": sha256_text(original),
            "config_hash": "checkpoint-test", "status": None, "complete": False,
            "iterations": [{"iteration": 1}], "cwe_count_before": 2, "cwe_count_after": 1,
            "cwes_before": [89, 94], "cwes_after": [89], "candidate_hash": None, "error": "",
        }
        graph = Data(x=torch.tensor([[0.25], [0.75]], dtype=torch.float32), edge_index=torch.tensor([[0], [1]], dtype=torch.long))
        candidate = "print('candidate')\n"
        _save_iteration_checkpoint(run_dir, source, record, candidate, graph)
        restored = _load_iteration_checkpoint(
            run_dir, source, record, record["source_hash"], record["config_hash"], torch.device("cpu")
        )
        require(restored is not None, "Iteration checkpoint did not reload")
        _, restored_code, restored_graph = restored
        require(restored_code == candidate, "Iteration checkpoint source changed")
        require(torch.equal(restored_graph.x, graph.x), "Iteration checkpoint node tensor changed")
        require(torch.equal(restored_graph.edge_index, graph.edge_index), "Iteration checkpoint edge index changed")


def check_functional_similarity_metric():
    original = "def add(a, b):\n    return a + b\n"
    candidate = "def add(a, b):\n    return a + b\n"

    def deterministic_json(prompt):
        if "externally observable behavior" in prompt:
            return {
                "intent": "Return the sum of two inputs.",
                "io_behavior": ["Accept two inputs and return their sum."],
                "side_effects": [],
                "invariants": ["The public add(a, b) interface is preserved."],
                "edge_cases": ["Works for values supported by Python addition."],
            }
        return {
            "behavior": 1.0,
            "io_semantics": 0.9,
            "side_effects": 1.0,
            "invariants": 0.8,
            "edge_cases": 0.7,
            "confidence": 0.95,
            "rationale": "Functionality is preserved.",
        }

    contract = extract_behavioral_contract(original, deterministic_json)
    report = score_candidate_functionality(contract, candidate, deterministic_json)
    expected_wm = 0.35 * 1.0 + 0.20 * 0.9 + 0.15 * 1.0 + 0.15 * 0.8 + 0.15 * 0.7
    expected = 0.75 * expected_wm + 0.25 * 0.7
    require(abs(report.weighted_mean - round(expected_wm, 5)) < 1e-8, "Unexpected LAAJ weighted mean")
    require(abs(report.laaj_score - round(expected, 5)) < 1e-8, "Unexpected LAAJ aggregate score")
    require(report.compile_ok and report.api_preserved and report.entrypoints_ok, "Unexpected functional gate failure")
    require(report.gated_score == report.laaj_score, "Gated score should equal LAAJ score when checks pass")

    changed_api = "def add(a):\n    return a\n"
    changed_report = score_candidate_functionality(contract, changed_api, deterministic_json)
    require(changed_report.laaj_score > 0, "Raw LAAJ score should remain separately reported")
    require(not changed_report.api_preserved, "API mismatch was not detected")
    require(changed_report.gated_score == 0.0, "API mismatch should zero only the companion gated score")
    return report.to_dict()


def main():
    train = check_dataset(TRAIN_DIR, 500)
    test = check_dataset(TEST_DIR, 100)
    gen_params = check_checkpoint(GENERATOR, 128, Generator())
    disc_params = check_checkpoint(DISCRIMINATOR, 64, Discriminator())
    check_notebook()
    check_cluster_assets()
    check_iteration_checkpoint()
    functional = check_functional_similarity_metric()

    print("PASS: PromSec package validation")
    print("training:", train)
    print("test:", test)
    print(f"checkpoint tensors: generator={gen_params}, discriminator={disc_params}")
    print("functional similarity metric:", functional)


if __name__ == "__main__":
    main()
