"""The per-program results monitor prints CWE before/after, their difference, and LAAJ."""

from __future__ import annotations

import csv
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from promsec import runner
from promsec.config import load_config
from promsec.live import watch_results
from promsec.llm import LLMClient

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r"^\s+\d+\s+test_file\S+\s+secured\s+(\d+)\s+0\s+(\d+)\s+1\s+\d\.\d{3}\s+(.+)$")


def _rows(text: str) -> list[re.Match]:
    return [m for m in (ROW.match(line) for line in text.splitlines()) if m]
SCORES = {"behavior": 0.9, "io_semantics": 0.9, "side_effects": 1.0, "invariants": 0.8, "edge_cases": 0.8,
          "confidence": 0.9, "rationale": "Behavior is preserved."}
CONTRACT = {"intent": "Serve the original routes.", "io_behavior": ["Same responses."], "side_effects": [],
            "invariants": [], "edge_cases": []}


def _enforcement_transport(prompt, model, temperature):
    if prompt.startswith("Estimate a detailed prompt"):
        return "Write the secured program.", 5, 5
    return "print('PROMSEC_MONITOR_SAFE')\n", 5, 5


def _judge_transport(prompt, model, temperature):
    if "externally observable behavior" in prompt:
        return json.dumps(CONTRACT), 5, 5
    return json.dumps(SCORES), 5, 5


@unittest.skipIf(shutil.which("bandit") is None, "Bandit is required")
class ResultsMonitorTests(unittest.TestCase):
    def test_lines_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_config(root=ROOT)
            cfg["run"]["root"] = str(Path(tmp) / "runs")
            cfg["run"]["name"] = "monitor"
            cfg["data"]["test_limit"] = 2
            cfg["loop"]["max_iterations"] = 1
            cfg["llm"]["cache_path"] = str(Path(tmp) / "cache.sqlite")
            scan = lambda code, require_compile=True: (0, []) if "PROMSEC_MONITOR_SAFE" in code else (2, [78, 89])
            with patch.object(runner, "scan_cwes", scan):
                runner.run_enforcement(cfg, llm=LLMClient("m", cache_path=Path(tmp) / "c.sqlite", transport=_enforcement_transport))
            judge = LLMClient("j", cache_path=Path(tmp) / "j.sqlite", transport=_judge_transport)
            out = io.StringIO()
            rows = watch_results(cfg, judge=True, interval=0.01, llm=judge, stream=out)
            text = out.getvalue()
            matches = _rows(text)
            self.assertEqual(len(rows), 2)
            self.assertEqual(len(matches), 2)
            for match in matches:
                self.assertEqual(match.group(1), "2")
                self.assertEqual(match.group(2), "2")
                self.assertRegex(match.group(3), r"^\d\.\d\d \(\d\.\d\d\)$")
            self.assertIn("Graph sim.", text)
            self.assertIn("CWEs 4 -> 0 (100.0% fewer)", text)
            self.assertEqual(text.count("Graph sim."), 1)
            self.assertEqual(text.count("Total:"), 1)
            self.assertLess(text.rindex("test_file"), text.index("Total:"))
            self.assertTrue((Path(tmp) / "runs" / "monitor" / "live_totals.txt").is_file())
            csv_path = Path(cfg["run"]["root"]) / "monitor" / "live_results.csv"
            with csv_path.open(newline="", encoding="utf-8") as handle:
                stored = list(csv.DictReader(handle))
            self.assertEqual([r["cwe_reduction"] for r in stored], ["2", "2"])
            again = io.StringIO()
            watch_results(cfg, judge=True, interval=0.01, llm=judge, stream=again)
            self.assertEqual(len(_rows(again.getvalue())), 2)
            with csv_path.open(newline="", encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 2)

    def test_csv_with_fewer_columns_is_upgraded(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_config(root=ROOT)
            cfg["run"]["root"] = str(Path(tmp) / "runs")
            cfg["run"]["name"] = "monitor_upgrade"
            cfg["data"]["test_limit"] = 1
            cfg["loop"]["max_iterations"] = 1
            cfg["llm"]["cache_path"] = str(Path(tmp) / "cache.sqlite")
            scan = lambda code, require_compile=True: (1, [78]) if "PROMSEC_MONITOR_SAFE" not in code else (0, [])
            with patch.object(runner, "scan_cwes", scan):
                runner.run_enforcement(cfg, llm=LLMClient("m", cache_path=Path(tmp) / "c.sqlite", transport=_enforcement_transport))
            csv_path = Path(cfg["run"]["root"]) / "monitor_upgrade" / "live_results.csv"
            first = min((ROOT / "data" / "test").glob("*.py")).name
            csv_path.write_text("file,status,cwe_before,cwe_after,cwe_reduction,iterations,laaj_score,laaj_gated_score,error,timestamp\n"
                                f"{first},secured,1,0,1,1,,,,2026-01-01T00:00:00+00:00\n", encoding="utf-8")
            out = io.StringIO()
            watch_results(cfg, judge=False, interval=0.01, stream=out)
            with csv_path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                stored = list(reader)
                self.assertIn("graph_similarity", reader.fieldnames)
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored[0]["cwe_reduction"], "1")
            self.assertIn("Graph sim.", out.getvalue())

    def test_without_judge(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = load_config(root=ROOT)
            cfg["run"]["root"] = str(Path(tmp) / "runs")
            cfg["run"]["name"] = "monitor_nojudge"
            cfg["data"]["test_limit"] = 1
            cfg["loop"]["max_iterations"] = 1
            cfg["llm"]["cache_path"] = str(Path(tmp) / "cache.sqlite")
            scan = lambda code, require_compile=True: (1, [78]) if "PROMSEC_MONITOR_SAFE" not in code else (0, [])
            with patch.object(runner, "scan_cwes", scan):
                runner.run_enforcement(cfg, llm=LLMClient("m", cache_path=Path(tmp) / "c.sqlite", transport=_enforcement_transport))
            out = io.StringIO()
            watch_results(cfg, judge=False, interval=0.01, stream=out)
            matches = _rows(out.getvalue())
            self.assertEqual(len(matches), 1)
            self.assertEqual((matches[0].group(1), matches[0].group(2), matches[0].group(3)), ("1", "1", "-"))


if __name__ == "__main__":
    unittest.main()
