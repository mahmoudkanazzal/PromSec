"""Statement graphs, edit labels, fix rendering, similarity measures, and the exact LLM requests."""

from __future__ import annotations

import hashlib
import unittest

import torch

from promsec import graph as g
from promsec import prompts as p
from promsec.similarity import embedding_similarity, graph_similarity
from tests.helpers import VULN

BEFORE = (
    "import os\nimport yaml\nimport requests\n\n\n"
    "def handle(name, text, url):\n"
    "    cmd = 'ls ' + name\n"
    "    os.system(cmd)\n"
    "    data = yaml.load(text)\n"
    "    r = requests.get(url)\n"
    "    debug = True\n"
    "    return data, r\n"
)
AFTER = (
    "import os\nimport yaml\nimport requests\n\n\n"
    "def handle(name, text, url):\n"
    "    cmd = 'ls ' + name\n"
    "    print(cmd)\n"
    "    data = yaml.safe_load(text)\n"
    "    r = requests.get(url, timeout=10)\n"
    "    if not url.startswith('https://'):\n"
    "        raise ValueError(url)\n"
    "    return data, r\n"
)


class StatementGraphTests(unittest.TestCase):
    def test_statements_cover_nested_code_in_source_order(self):
        stmts = g.statements(BEFORE)
        self.assertEqual([s.type for s in stmts][:4], ["Import", "Import", "Import", "FunctionDef"])
        self.assertEqual([s.lineno for s in stmts], sorted(s.lineno for s in stmts))
        self.assertEqual(stmts[5].calls, ("os.system",))
        self.assertIn("requests.get:timeout=10", g.statements(AFTER)[7].keywords)
        self.assertEqual(stmts[4].flags["str_concat"], 1.0)

    def test_edges_include_reaching_definitions(self):
        stmts, x, edge_index, edge_type = g.graph(BEFORE)
        defuse = {(a, b) for a, b, t in zip(edge_index[0].tolist(), edge_index[1].tolist(), edge_type.tolist()) if t == 4}
        self.assertIn((4, 5), defuse)  # cmd = ... -> os.system(cmd)
        self.assertEqual(x.shape, (len(stmts), g.FEATURE_DIM))

    def test_features_carry_no_analyzer_output(self):
        plain = g.statements(BEFORE)
        flagged = g.statements(BEFORE)
        g.attach_findings(flagged, [{"line_number": 8, "test_id": "B605"}])
        self.assertEqual([s.lineno for s in flagged if s.findings], [8])
        self.assertTrue(torch.equal(g.features(plain), g.features(flagged)))

    def test_edit_labels_from_a_fix(self):
        stmts, labels, detail = g.edit_labels(BEFORE, AFTER)
        by_line = {s.lineno: label for s, label in zip(stmts, labels)}
        self.assertEqual((by_line[8], by_line[9], by_line[10], by_line[1]), ("replace_call", "replace_call", "change_args", "keep"))
        self.assertIn("requests.get:timeout=10", detail[[s.lineno for s in stmts].index(10)]["added_keywords"])

    def test_insert_and_delete(self):
        before = "def f(x):\n    y = x\n    z = 2\n    return y\n"
        after = "def f(x):\n    if x is None:\n        raise ValueError\n    y = x\n    return y\n"
        stmts, labels, _ = g.edit_labels(before, after)
        self.assertEqual(dict(zip([s.header for s in stmts], labels)),
                         {"def f(x):": "keep", "y = x": "insert_before", "z = 2": "delete", "return y": "keep"})

    def test_plan_rendering_and_hint_table(self):
        stmts, labels, detail = g.edit_labels(BEFORE, AFTER)
        plan = g.render_plan(BEFORE, stmts, labels, detail=detail)
        self.assertIn("Line 8 (`os.system(cmd)`): replace the risky call with a safer API, for example `print`", plan)
        self.assertTrue(plan.endswith("Keep every other statement unchanged."))
        self.assertEqual(g.render_plan(BEFORE, stmts, ["keep"] * len(stmts)), "No statement needs to change.")
        table = g.HintTable.fit([{"statements": stmts, "labels": labels, "detail": detail}])
        self.assertEqual(table.replacements["yaml.load"], "yaml.safe_load")
        self.assertEqual(g.HintTable.from_dict(table.to_dict()), table)

    def test_macro_f1(self):
        self.assertEqual(g.macro_f1([1, 1, 0], [1, 1, 0], [1]), 1.0)
        self.assertEqual(g.macro_f1([1, 0], [0, 1], [1]), 0.0)


class SimilarityTests(unittest.TestCase):
    def test_identical_programs(self):
        self.assertAlmostEqual(graph_similarity(BEFORE, BEFORE), 1.0)
        self.assertAlmostEqual(embedding_similarity(BEFORE, BEFORE), 1.0, places=6)

    def test_related_programs_score_between(self):
        gs, es = graph_similarity(BEFORE, AFTER), embedding_similarity(BEFORE, AFTER)
        self.assertTrue(0.0 < gs < 1.0 and 0.0 < es < 1.0)
        self.assertLess(graph_similarity(BEFORE, VULN["hashlib.md5"]), gs)

    def test_unparsable_program(self):
        self.assertIsNone(graph_similarity(BEFORE, "def (:"))
        self.assertIsNone(embedding_similarity(BEFORE, "def (:"))


# SHA-256 of the requests that produced the results in results/ (same input as below).
REQUEST_SHA256 = {
    "promsec": "1a43ab9e452de2e61e3687eebe848e4558d83ffac2b701271fcc19bfdd177ae7",
    "promsec-s": "aea225e0ce1e65669fcc8b3cf0f105e64d89a8a79d6e0ac6169c3b5c5fb4cb68",
    "none": "7bdf7ecf3acf56b174df699adfc96dbfb0bcc1561cdef5fed269f6866ec1938d",
    "inference": "9979ebbb41a0f9fb3c1f9ef8fd47ec8a28734dec6b20bd32cb4cd15c4c164041",
    "generation": "80c2acc6f194d45d075239280adec16389e15780fd9b52abc241457f53ce8df7",
}


class RequestTests(unittest.TestCase):
    def test_requests_are_the_ones_behind_the_results(self):
        code = VULN["os.system"]
        selected = p.statements_with_code(code, [{"node": 3, "ast_type": "Expr", "lineno": 6, "end_lineno": 6, "change": 0.9}])
        fixes = "- Line 6 (`os.system(cmd)`): rewrite this statement to remove the weakness.\n- Keep every other statement unchanged."
        requests = {
            "promsec": p.build_reconstruction_prompt(code, selected),
            "promsec-s": p.build_reconstruction_prompt(code, selected, fixes),
            "none": p.build_unguided_reconstruction_prompt(code),
            "inference": p.build_prompt_inference_request("print(1)"),
            "generation": p.build_generation_prompt("Write a program"),
        }
        for name, text in requests.items():
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), REQUEST_SHA256[name], name)

    def test_request_structure(self):
        code = VULN["os.system"]
        selected = p.statements_with_code(code, [{"node": 3, "ast_type": "Expr", "lineno": 6, "end_lineno": 6, "change": 0.9}])
        text = p.build_reconstruction_prompt(code, selected, "- fix")
        self.assertIn("Statements that carry security weaknesses (in source order):\n1. Expr at L6:\n        os.system(cmd)", text)
        self.assertLess(text.index("Proposed fixes:\n- fix"), text.index("Provide the updated Python code."))
        self.assertIn("No statement is listed.", p.build_reconstruction_prompt(code, []))
        self.assertNotIn("Statements", p.build_unguided_reconstruction_prompt(code))


if __name__ == "__main__":
    unittest.main()
