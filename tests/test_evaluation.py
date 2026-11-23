from __future__ import annotations

import json
import math
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation.calibration import CASES
from evaluation.functional_similarity import (
    extract_behavioral_contract,
    score_candidate_functionality,
    validated_scores,
)
from promsec.config import load_config, relevant_config_hash
from promsec.io import append_jsonl, atomic_write_json, sha256_text
from promsec.judge import (
    _reduced_negative_control,
    _score_stability,
    calibrate_judge,
    judge_run,
)
from promsec.llm import LLMClient, LLMError, LLMValidationError
from promsec.metrics import validate_python_source
from promsec.records import (
    RESULT_SCHEMA,
    TERMINAL_STATUSES,
    collect_records,
    record_issue,
)
from promsec.report import build_report
from promsec.runner import _generate_valid_python
from promsec.security import SecurityAnalysisError, scan_cwes

ROOT = Path(__file__).resolve().parents[1]
SCORES = dict(behavior=1.0, io_semantics=0.9, side_effects=1.0, invariants=0.8, edge_cases=0.7, confidence=0.95, rationale="Behavioral comparison.")
CONTRACT = dict(intent="Return the sum of two inputs.", io_behavior=["Return a + b."], side_effects=[], invariants=[], edge_cases=[])
SOURCE = "def add(a, b):\n    return a + b\n"


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cfg = load_config(root=ROOT)
        self.cfg["run"].update(root=str(self.root / "runs"), name="checks")
        self.cfg["data"]["test_dir"] = str(self.root / "input")
        self.cfg["judge"]["max_retries"] = 0
        self.input = Path(self.cfg["data"]["test_dir"])
        self.input.mkdir()
        self.run = self.root / "runs" / "checks"
        (self.run / "samples").mkdir(parents=True)
        (self.run / "vetted_code").mkdir()
        self.calls = []

    def client(self, transport=None, **settings):
        def respond(prompt, model, temperature):
            self.calls.append(prompt)
            value = CONTRACT if "externally observable behavior" in prompt else SCORES
            return json.dumps(value), 10, 5
        settings.setdefault("model", "evaluation-test")
        settings.setdefault("max_retries", 0)
        client = LLMClient(cache_path=self.root / "cache.sqlite", transport=transport or respond, **settings)
        self.addCleanup(client.cache._db.close)
        return client

    def record(self, name="example.py", status="secured"):
        (self.input / name).write_text(SOURCE, encoding="utf-8")
        (self.run / "vetted_code" / name).write_text(SOURCE, encoding="utf-8")
        rec = dict(schema=RESULT_SCHEMA, file=name, source_hash=sha256_text(SOURCE),
                   candidate_hash=sha256_text(SOURCE), config_hash=relevant_config_hash(self.cfg),
                   status=status, complete=True, cwe_count_before=2,
                   cwe_count_after=0 if status != "failed" else None, iterations_used=1,
                   gnn_feature_change=0.2, ast_similarity=1.0, error="")
        atomic_write_json(self.run / "samples" / (Path(name).stem + ".json"), rec)
        return rec

    def score(self, code=SOURCE, values=None):
        contract = extract_behavioral_contract(SOURCE, lambda _: CONTRACT)
        return score_candidate_functionality(contract, code, lambda _: values or SCORES)

    def test_aggregate_and_separate_gate(self):
        good = self.score()
        self.assertEqual(good.laaj_score, 0.85375)
        self.assertEqual(good.gated_score, good.laaj_score)
        changed = self.score("def add(a):\n    return a\n")
        self.assertEqual(changed.laaj_score, good.laaj_score)
        self.assertEqual(changed.gated_score, 0)
        invalid = self.score("def add(:")
        self.assertFalse(invalid.compile_ok)
        self.assertEqual(invalid.gated_score, 0)

    def test_invalid_judge_values_rejected(self):
        for value in ("NaN", math.nan, math.inf, -math.inf, -0.1, 1.1, True, None, "invalid"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validated_scores({**SCORES, "behavior": value})
        missing = dict(SCORES)
        del missing["edge_cases"]
        with self.assertRaises(ValueError):
            validated_scores(missing)

    def test_empty_candidate_rejected(self):
        for code in ("", "   ", "# no statements\n", "```python\n```", "def broken(:"):
            with self.subTest(code=code), self.assertRaises((ValueError, SyntaxError)):
                validate_python_source(code)
        validate_python_source(SOURCE)

    def bandit(self, payload, returncode=0):
        response = subprocess.CompletedProcess(["bandit"], returncode, json.dumps(payload), "")
        with patch("promsec.security.shutil.which", return_value="bandit"), patch("promsec.security.subprocess.run", return_value=response):
            return scan_cwes(SOURCE)

    def test_bandit_counts_unique_cwes(self):
        results = [{"issue_cwe": {"id": n}} for n in (89, 89, 78)]
        self.assertEqual(self.bandit({"errors": [], "results": results}, 1), (2, [78, 89]))
        self.assertEqual(self.bandit({"errors": [], "results": []}), (0, []))

    def test_bandit_errors_never_clean(self):
        cases = [({"errors": [{"reason": "analysis failed"}], "results": []}, 0),
                 ({"errors": [], "results": []}, 2), ({"results": []}, 0),
                 ({"errors": [], "results": []}, 1),
                 ({"errors": [], "results": [{"test_id": "B999"}]}, 1)]
        for payload, status in cases:
            with self.subTest(payload=payload, status=status), self.assertRaises(SecurityAnalysisError):
                self.bandit(payload, status)

    def test_bandit_timeout_and_invalid_json(self):
        with patch("promsec.security.shutil.which", return_value="bandit"):
            with patch("promsec.security.subprocess.run", side_effect=subprocess.TimeoutExpired("bandit", 120)):
                with self.assertRaises(SecurityAnalysisError):
                    scan_cwes(SOURCE)
            response = subprocess.CompletedProcess(["bandit"], 0, "invalid", "")
            with patch("promsec.security.subprocess.run", return_value=response):
                with self.assertRaises(SecurityAnalysisError):
                    scan_cwes(SOURCE)

    def test_cache_identity(self):
        a = self.client()
        self.assertFalse(a.complete("first", purpose="check").cached)
        self.assertTrue(a.complete("first", purpose="check").cached)
        for client, prompt in ((self.client(model="different"), "first"),
                               (self.client(temperature=0.5), "first"),
                               (self.client(base_url="http://example.invalid"), "first"), (a, "changed")):
            self.assertFalse(client.complete(prompt, purpose="check").cached)

    def test_empty_response_not_cached(self):
        attempts = []
        def respond(*args):
            attempts.append(1)
            return "", 0, 0
        client = self.client(transport=respond)
        for _ in range(2):
            with self.assertRaises(LLMError):
                client.complete("request", purpose="check")
        self.assertEqual(len(attempts), 2)

    def test_invalid_cached_score_revalidated(self):
        answers = iter([json.dumps({**SCORES, "behavior": "NaN"}), json.dumps(SCORES)])
        client = self.client(transport=lambda *args: (next(answers), 10, 5))
        client.complete("score", purpose="check")
        result = client.complete("score", purpose="check", validate=lambda text: validated_scores(json.loads(text)))
        self.assertFalse(result.cached)
        self.assertEqual(json.loads(result.text)["behavior"], 1.0)


    def test_validation_error_can_bypass_same_prompt_retries(self):
        calls = []
        def invalid(*args):
            calls.append(1)
            return "def broken(:", 10, 5
        client = self.client(transport=invalid, max_retries=4)
        with self.assertRaises(LLMValidationError):
            client.complete(
                "generate", purpose="check", validate=validate_python_source,
                retry_on_validation_error=False,
            )
        self.assertEqual(len(calls), 1)

    def test_syntax_repair_returns_rejected_program(self):
        calls = []
        def transport(prompt, model, temperature):
            calls.append(prompt)
            if len(calls) == 1:
                return "def broken(:", 10, 5
            return SOURCE, 10, 5
        client = self.client(transport=transport, max_retries=0)
        candidate, repairs = _generate_valid_python("Generate the program.", client, "abc", 2)
        self.assertEqual(candidate, SOURCE.rstrip())
        self.assertEqual(repairs, 1)
        self.assertEqual(len(calls), 2)
        self.assertIn("Rejected program:\ndef broken(:", calls[1])

    def test_failed_is_terminal_for_orchestration(self):
        rec = self.record(status="failed")
        self.assertIn(rec["status"], TERMINAL_STATUSES)
        records, excluded = collect_records(self.cfg)
        self.assertEqual(len(records), 1)
        self.assertEqual(excluded, [])

    def test_candidate_integrity_for_resume(self):
        rec = self.record()
        source = self.input / rec["file"]
        self.assertIsNone(record_issue(rec, self.cfg, source))
        candidate = self.run / "vetted_code" / rec["file"]
        candidate.write_text("pass\n", encoding="utf-8")
        self.assertEqual(record_issue(rec, self.cfg, source), "candidate_changed")
        candidate.unlink()
        self.assertEqual(record_issue(rec, self.cfg, source), "candidate_missing")

    def test_changed_source_or_configuration_excluded(self):
        self.record()
        (self.input / "example.py").write_text("pass\n", encoding="utf-8")
        self.assertEqual(collect_records(self.cfg)[1][0]["reason"], "source_changed")
        self.record()
        self.cfg["loop"]["max_iterations"] += 1
        self.assertEqual(collect_records(self.cfg)[1][0]["reason"], "enforcement_configuration_changed")

    def test_judge_resume_and_stability(self):
        self.record()
        client = self.client()
        self.assertEqual(judge_run(self.cfg, llm=client)["judged_now"], 1)
        self.assertEqual(judge_run(self.cfg, llm=client)["resumed"], 1)
        self.assertEqual(len(self.calls), 3)
        row = json.loads((self.run / "judge/example.json").read_text())
        self.assertEqual(row["stability_abs_difference"], 0)

    def test_stability_rejects_invalid_scores(self):
        contract = extract_behavioral_contract(SOURCE, lambda _: CONTRACT)
        client = self.client(transport=lambda *args: (json.dumps({**SCORES, "confidence": "NaN"}), 10, 5))
        with self.assertRaises(LLMError):
            _score_stability(contract, SOURCE, client)

    def test_failed_sample_never_judged(self):
        self.record(status="failed")
        result = judge_run(self.cfg, llm=self.client())
        self.assertEqual(result["judged_now"], 0)
        self.assertEqual(result["skipped_failed_samples"], 1)
        self.assertEqual(self.calls, [])

    def test_failed_judge_removes_previous_score(self):
        self.record()
        judge_run(self.cfg, llm=self.client())
        def invalid(prompt, *args):
            value = CONTRACT if "externally observable behavior" in prompt else {**SCORES, "behavior": "NaN"}
            return json.dumps(value), 10, 5
        result = judge_run(self.cfg, llm=self.client(model="invalid-response-check", transport=invalid), force=True)
        self.assertEqual(result["failed_now"], 1)
        self.assertFalse((self.run / "judge/example.json").exists())
        self.assertTrue((self.run / "judge/errors/example.json").exists())

    def test_stale_judge_not_joined(self):
        rec = self.record()
        judge_run(self.cfg, llm=self.client())
        changed = "def add(a, b):\n    return a - b\n"
        (self.run / "vetted_code/example.py").write_text(changed, encoding="utf-8")
        rec["candidate_hash"] = sha256_text(changed)
        atomic_write_json(self.run / "samples/example.json", rec)
        self.assertIsNone(build_report(self.cfg)["mean_laaj_score"])
        self.assertEqual(judge_run(self.cfg, llm=self.client())["judged_now"], 1)
        self.cfg["judge"]["temperature"] = 0.2
        self.assertIsNone(build_report(self.cfg)["mean_laaj_score"])
        self.assertEqual(judge_run(self.cfg, llm=self.client())["judged_now"], 1)

    def test_report_tokens_and_failure_denominator(self):
        self.record()
        self.record("failed.py", "failed")
        for cached in (False, True):
            append_jsonl(self.run / "calls.jsonl", dict(cached=cached, prompt_tokens=10, completion_tokens=5))
        result = build_report(self.cfg)
        self.assertEqual(result["secured_programs"] / result["vulnerable_programs"], 0.5)
        self.assertEqual(result["completed_programs"], 1)
        self.assertEqual(result["failed_programs"], 1)
        self.assertEqual(result["prompt_tokens"], 10)
        self.assertEqual(result["llm_cache_hits"], 1)
        self.assertEqual(result["cwes_before"], 2)
        self.assertEqual(result["cwes_after"], 0)
        self.assertEqual(result["cwe_reduction_rate"], 1.0)

    def test_performance_figure_written_and_regenerated(self):
        self.record()
        judge_run(self.cfg, llm=self.client())
        result = build_report(self.cfg)
        figure = self.run / "report/performance_eval.png"
        self.assertTrue(figure.exists())
        self.assertTrue((self.run / "report/performance_eval.pdf").exists())
        self.assertIn("performance_eval.png", result["figures"])
        figure.write_bytes(b"")
        self.cfg["judge"]["temperature"] = 0.2
        build_report(self.cfg)
        self.assertGreater(figure.stat().st_size, 0)

    def test_interrupted_call_log_reported(self):
        self.record()
        (self.run / "calls.jsonl").write_text('{"cached": false, "prompt_tokens": 3}\n{"cached":', encoding="utf-8")
        result = build_report(self.cfg)
        self.assertEqual(result["llm_requests_logged"], 1)
        self.assertEqual(result["prompt_tokens"], 3)

    def test_calibration_witnesses(self):
        for case in CASES:
            for key, expected in (("original", case["expected"]), ("changed", case["changed_expected"])):
                scope = {}
                exec(case[key], scope)
                self.assertEqual(scope["calculate"](*case["arguments"]), expected)
            self.assertNotEqual(case["expected"], case["changed_expected"])
            scope = {}
            exec(_reduced_negative_control(case["original"]), scope)
            self.assertIsNone(scope["calculate"](*case["arguments"]))
            self.assertIsNotNone(case["expected"])

    def test_calibration_flow(self):
        result = calibrate_judge(self.cfg, llm=self.client(), limit=1)
        self.assertEqual(result["controls"], 4)
        self.assertEqual(result["separation"], 0)

    def test_invalid_training_configuration_rejected(self):
        from promsec.config import validate_config
        self.cfg["ggan"]["discriminator_steps"] = 0
        with self.assertRaises(ValueError):
            validate_config(self.cfg)
        self.cfg["ggan"]["discriminator_steps"] = 1
        self.cfg["ggan"]["seed"] = -1
        with self.assertRaises(ValueError):
            validate_config(self.cfg)
        self.cfg["ggan"]["seed"] = 0
        self.cfg["ggan_s"]["holdout_fraction"] = 1.5
        with self.assertRaises(ValueError):
            validate_config(self.cfg)


if __name__ == "__main__":
    unittest.main()
