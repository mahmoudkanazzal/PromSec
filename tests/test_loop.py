"""The PromSec loop for each variant (mock LLM), configuration, reports, and the variant comparison."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from promsec import compare, runner
from promsec.config import GUIDANCE_MODES, load_config
from promsec.llm import LLMClient
from promsec.report import build_archive_report, build_report
from tests.helpers import ROOT, VULN, FakeEndpoint


def _client(tmp: Path, transport) -> LLMClient:
    return LLMClient("offline", cache_path=Path(tmp) / "cache.sqlite", transport=transport)


class VariantRequestTests(unittest.TestCase):
    def test_each_variant_sends_its_reconstruction_request(self):
        code = (ROOT / "data/test/test_file11.py").read_text()
        with tempfile.TemporaryDirectory() as tmp:
            for config, expect in (("configs/default.yaml", "Statements that carry security weaknesses"),
                                   ("configs/promsec_s.yaml", "Proposed fixes:"),
                                   ("configs/no_ggan.yaml", None)):
                cfg = load_config(config, root=ROOT)
                endpoint = FakeEndpoint()
                with patch.object(runner, "bandit_nodes", lambda c: []):
                    step = runner.run_iteration(code, runner.load_selector(cfg), _client(Path(tmp) / config.replace("/", "_"), endpoint),
                                                mode=cfg["guidance"]["mode"])
                reconstruction = endpoint.prompts[0]
                self.assertTrue(reconstruction.startswith("You are a coding assistant."))
                if expect:
                    self.assertIn(expect, reconstruction)
                    self.assertEqual([m["lineno"] for m in step["flagged"]], [3, 7, 13, 29, 112])
                else:
                    self.assertNotIn("Statements that carry", reconstruction)
                    self.assertEqual(step["flagged"], [])
                self.assertTrue(endpoint.prompts[1].startswith("Estimate a detailed prompt"))
                self.assertTrue(endpoint.prompts[2].startswith("In your code generation"))

    def test_unknown_variant(self):
        with self.assertRaises(ValueError):
            runner.run_iteration("x = 1\n", None, None, mode="other")
        with self.assertRaises(ValueError):
            runner.run_iteration("x = 1\n", None, None, mode="promsec")


class ConfigTests(unittest.TestCase):
    def test_variants_and_inheritance(self):
        self.assertEqual(GUIDANCE_MODES, ("promsec", "promsec-s", "none"))
        self.assertEqual(load_config("configs/compare/promsec_s_run2.yaml", root=ROOT)["guidance"]["mode"], "promsec-s")
        self.assertEqual(load_config("configs/compare/no_ggan_run3.yaml", root=ROOT)["run"]["name"], "no_ggan_run3")

    def test_invalid_values_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ("guidance:\n  mode: other\n", "loop:\n  max_iterations: 0\n", "ggan:\n  epochs: 0\n",
                        "ggan_s:\n  threshold: 2\n"):
                path = Path(tmp) / "bad.yaml"
                path.write_text("base: configs/default.yaml\n" + bad)
                with self.assertRaises(ValueError, msg=bad):
                    load_config(path, root=ROOT)

    def test_run_identity_includes_the_checkpoint(self):
        from promsec.config import relevant_config_hash
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT / "models/promsec", Path(tmp) / "m")
            cfg = load_config(root=ROOT)
            cfg["ggan"]["model_dir"] = str(Path(tmp) / "m")
            before = relevant_config_hash(cfg)
            (Path(tmp) / "m" / "generator.pt").write_bytes(b"changed")
            self.assertNotEqual(relevant_config_hash(cfg), before)

    def test_compare_queue_interleaves_variants(self):
        names = [e["name"] for e in compare.queue(ROOT)]
        self.assertEqual(names[:3], ["promsec_run1", "promsec_s_run1", "no_ggan_run1"])
        self.assertEqual(names[-1], "no_ggan_run3")


@unittest.skipIf(shutil.which("bandit") is None, "Bandit is required")
class EnforcementTests(unittest.TestCase):
    def test_run_report_and_comparison(self):
        os.environ.setdefault("PROMSEC_LLM_MODEL", "offline-model")
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_config(root=ROOT)
            cfg["run"]["root"] = str(Path(tmp) / "runs")
            cfg["data"]["test_limit"] = 3
            cfg["loop"]["max_iterations"] = 2

            def transport(prompt, model, temperature):
                if prompt.startswith("Estimate a detailed prompt"):
                    return "Write the program securely.", 5, 5
                return VULN["hashlib.md5"].replace("md5", "sha256"), 5, 5

            summary = runner.run_enforcement(cfg, llm=_client(tmp, transport))
            self.assertEqual(summary["completed_now"], 3)
            again = runner.run_enforcement(cfg, llm=_client(tmp, transport))
            self.assertEqual(again["resumed_completed"], 3)
            report = build_report(cfg)
            self.assertEqual(report["programs"], 3)
            self.assertEqual(report["secured_programs"], report["vulnerable_programs"])
            self.assertIsNotNone(report["mean_graph_similarity"])
            run_dir = Path(tmp) / "runs" / "promsec"
            sample = json.loads(next((run_dir / "samples").glob("*.json")).read_text())
            self.assertEqual(sample["guidance_mode"], "promsec")
            self.assertTrue(all(len(it["guidance_statements"]) <= 5 for it in sample["iterations"]))
            self.assertTrue((run_dir / "report" / "performance_eval.png").is_file())

            archive = Path(tmp) / "results" / "promsec" / "run1"
            archive.mkdir(parents=True)
            shutil.copytree(run_dir / "samples", archive / "samples")
            shutil.copytree(run_dir / "vetted_code", archive / "outputs")
            archived = build_archive_report(archive, ROOT / "data/test", "offline")
            self.assertEqual(archived["cwes_after"], report["cwes_after"])
            self.assertEqual(archived["variant"], "promsec")
            text = compare.write(compare.collect_archive(Path(tmp) / "results"), Path(tmp) / "results")
            self.assertIn("| promsec/run1 | PromSec | 3/100 | 0 |", text)
            self.assertTrue((Path(tmp) / "results" / "comparison.csv").is_file())


class ShippedResultsTests(unittest.TestCase):
    """The comparison in results/ matches the per-program records it is built from."""

    def test_comparison_matches_records(self):
        rows = {r["run"]: r for r in compare.comparison(compare.collect_archive(ROOT / "results"))[1]}
        self.assertEqual(set(rows), {"promsec/run1", "promsec/run2", "promsec_s/run1", "promsec_s/run2",
                                     "no_ggan/run1", "no_ggan/run2", "no_ggan/run3"})
        for name, row in rows.items():
            samples = [json.loads(p.read_text()) for p in (ROOT / "results" / name / "samples").glob("*.json")]
            vulnerable = [s for s in samples if (s.get("cwe_count_before") or 0) > 0 and isinstance(s.get("cwe_count_after"), int)]
            self.assertEqual(row["cwes_left"], sum(s["cwe_count_after"] for s in vulnerable), name)
            self.assertEqual(row["programs_secured"], sum(1 for s in vulnerable if s["status"] == "secured"), name)
            self.assertEqual({s["guidance_mode"] for s in samples}, {row["variant"]})


if __name__ == "__main__":
    unittest.main()
