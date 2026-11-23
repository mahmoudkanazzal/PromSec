"""Self-test of caching, enforcement, resume, judging, and reporting with controlled LLM responses."""

from __future__ import annotations

import json
import tempfile
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=SyntaxWarning)

from .config import load_config
from .io import sha256_text
from .llm import LLMClient
from .manifest import check_manifest
from .metrics import ast_similarity, strip_code_fences

RECONSTRUCTION_PREFIX = "You are a coding assistant."
PROMPT_INFERENCE_PREFIX = "Estimate a detailed prompt"


def run(root: str | Path) -> dict:
    """Run the self-test and return a pass summary."""
    root = Path(root).resolve()
    cfg = load_config(root=root)
    manifest = check_manifest(cfg)
    calls = {"cache": 0}

    def cache_transport(prompt: str, model: str, temperature: float):
        calls["cache"] += 1
        return "response:" + prompt, len(prompt) // 4, 2

    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "cache.sqlite"
        client = LLMClient("selftest-model", cache_path=cache, transport=cache_transport)
        first = client.complete("cache-check", purpose="selftest")
        second = client.complete("cache-check", purpose="selftest")
        if first.cached or not second.cached or calls["cache"] != 1:
            raise AssertionError("LLM cache regression")

    if strip_code_fences("```python\nprint('x')\n```") != "print('x')":
        raise AssertionError("Code-fence normalization regression")
    if ast_similarity("x = 1\n", "x = 1\n") != 1.0:
        raise AssertionError("AST similarity regression")

    import torch_geometric  # noqa: F401

    from . import runner
    from .judge import calibrate_judge, judge_run
    from .report import build_report

    with tempfile.TemporaryDirectory() as tmp:
        cfg = load_config(root=root)
        cfg["run"]["root"] = str(Path(tmp) / "runs")
        cfg["run"]["name"] = "selftest"
        cfg["data"]["test_limit"] = 2
        cfg["loop"]["max_iterations"] = 1
        cfg["llm"]["cache_path"] = str(Path(tmp) / "cache.sqlite")
        llm_calls = {"n": 0}

        def enforcement_transport(prompt: str, model: str, temperature: float):
            llm_calls["n"] += 1
            stamp = sha256_text(prompt)[:12]
            if prompt.startswith(PROMPT_INFERENCE_PREFIX):
                return f"Produce a complete secure Python program ({stamp}).", 10, 5
            if prompt.startswith(RECONSTRUCTION_PREFIX):
                return f"print('PROMSEC_SELFTEST_SAFE', '{stamp}')\n", 10, 5
            return "print('PROMSEC_SELFTEST_SAFE')\n", 10, 5

        llm = LLMClient(
            "selftest-enforcement",
            cache_path=Path(tmp) / "cache.sqlite",
            call_log=Path(tmp) / "calls.jsonl",
            transport=enforcement_transport,
        )
        original_which, original_scan, original_nodes = runner.shutil.which, runner.scan_cwes, runner.bandit_nodes
        runner.shutil.which = lambda name: "/usr/bin/bandit"  # type: ignore[assignment]
        runner.scan_cwes = lambda code, require_compile=True: (0, []) if "PROMSEC_SELFTEST_SAFE" in code else (1, [999])
        runner.bandit_nodes = lambda code: []
        try:
            first_run = runner.run_enforcement(cfg, llm=llm)
            second_run = runner.run_enforcement(cfg, llm=llm)
        finally:
            runner.shutil.which, runner.scan_cwes, runner.bandit_nodes = original_which, original_scan, original_nodes
        if first_run["completed_now"] != 2 or second_run["resumed_completed"] != 2:
            raise AssertionError("Run resume regression")
        if llm_calls["n"] != 6:
            raise AssertionError(
                f"Unexpected enforcement LLM call count: {llm_calls['n']} (expected 6: reconstruction, prompt inference, generation per program)"
            )

        partial_cfg = load_config(root=root)
        partial_cfg["run"]["root"] = str(Path(tmp) / "runs")
        partial_cfg["run"]["name"] = "partial-resume"
        partial_cfg["data"]["test_limit"] = 1
        partial_cfg["loop"]["max_iterations"] = 2
        partial_cfg["llm"]["cache_path"] = str(Path(tmp) / "partial_cache.sqlite")
        reconstruction_calls = {"n": 0}

        def interrupted_transport(prompt: str, model: str, temperature: float):
            if prompt.startswith(PROMPT_INFERENCE_PREFIX):
                return "Produce a complete secure Python program.", 10, 5
            if prompt.startswith(RECONSTRUCTION_PREFIX):
                reconstruction_calls["n"] += 1
                if reconstruction_calls["n"] == 1:
                    return "print('PROMSEC_RECONSTRUCTED')\n", 10, 5
                raise KeyboardInterrupt("simulated process interruption")
            return "print('PROMSEC_STEP1')\n", 10, 5

        def resumed_transport(prompt: str, model: str, temperature: float):
            if prompt.startswith(PROMPT_INFERENCE_PREFIX):
                return "Produce a complete secure Python program after resume.", 10, 5
            return "print('PROMSEC_STEP2')\n", 10, 5

        def partial_scan(code: str, require_compile: bool = True):
            if "PROMSEC_STEP2" in code:
                return 0, []
            if "PROMSEC_STEP1" in code:
                return 1, [998]
            return 2, [998, 999]

        original_which, original_scan, original_nodes = runner.shutil.which, runner.scan_cwes, runner.bandit_nodes
        runner.shutil.which = lambda name: "/usr/bin/bandit"  # type: ignore[assignment]
        runner.scan_cwes = partial_scan
        runner.bandit_nodes = lambda code: []
        try:
            try:
                runner.run_enforcement(
                    partial_cfg,
                    llm=LLMClient(
                        "partial-resume-model", cache_path=Path(tmp) / "partial_resume_cache.sqlite",
                        max_retries=0, transport=interrupted_transport,
                    ),
                )
            except KeyboardInterrupt:
                pass
            resumed_run = runner.run_enforcement(
                partial_cfg,
                llm=LLMClient(
                    "partial-resume-model", cache_path=Path(tmp) / "partial_resume_cache.sqlite",
                    max_retries=0, transport=resumed_transport,
                ),
            )
        finally:
            runner.shutil.which, runner.scan_cwes, runner.bandit_nodes = original_which, original_scan, original_nodes
        if resumed_run["resumed_partial"] != 1:
            raise AssertionError("Iteration-level resume regression")
        partial_record = json.loads((Path(tmp) / "runs" / "partial-resume" / "samples" / (Path(min((root / "data" / "test").glob("*.py"))).stem + ".json")).read_text(encoding="utf-8"))
        if partial_record.get("status") != "secured" or [row.get("iteration") for row in partial_record.get("iterations", [])] != [1, 2]:
            raise AssertionError("Iteration-level resume did not continue at the next durable iteration")

        def judge_transport(prompt: str, model: str, temperature: float):
            if "behavior: number in [0,1]" in prompt or "dimension order is intentionally reversed" in prompt:
                return json.dumps({
                    "behavior": 0.95,
                    "io_semantics": 0.95,
                    "side_effects": 0.95,
                    "invariants": 0.95,
                    "edge_cases": 0.95,
                    "confidence": 0.9,
                    "rationale": "Behavior is preserved for this validation response.",
                }), 10, 10
            return json.dumps({
                "intent": "Preserve the program's externally observable behavior.",
                "io_behavior": ["Produces its documented output."],
                "side_effects": [],
                "invariants": ["Retains the program entry behavior."],
                "edge_cases": [],
            }), 10, 10

        judge_client = LLMClient(
            "selftest-judge",
            cache_path=Path(tmp) / "judge_cache.sqlite",
            transport=judge_transport,
        )
        judged = judge_run(cfg, llm=judge_client)
        if judged["judged_now"] != 2:
            raise AssertionError("Judge-run regression")
        report = build_report(cfg)
        if report["programs"] != 2 or report["secured_programs"] != 2:
            raise AssertionError("Report regression")
        calibration = calibrate_judge(cfg, llm=judge_client, limit=1)
        if calibration["controls"] != 4:
            raise AssertionError("Judge calibration regression")

    return {
        "manifest": manifest,
        "llm_cache": "pass",
        "metrics": "pass",
        "resume": "pass",
        "judge": "pass",
        "report": "pass",
        "calibration": "pass",
    }
