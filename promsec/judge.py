"""LLM-judged functional similarity of final programs."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from evaluation.calibration import CASES
from evaluation.functional_similarity import (
    extract_behavioral_contract,
    score_candidate_functionality,
    validated_scores,
)

from .config import judge_config_hash, resolve_path
from .io import atomic_write_json, sha256_text
from .llm import LLMClient, client_from_config
from .records import (
    COMPLETED_STATUSES,
    RESULT_SCHEMA,
    _run_dir,
    collect_records,
    judge_record_issue,
)


def _json_from_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].lower().strip() in {"```", "```json"}:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Judge response did not contain a JSON object")
        value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Judge response must be a JSON object")
    return value


def _completion(llm: LLMClient, tag: str):
    def validate(text: str):
        data = _json_from_text(text)
        if tag == "contract" or tag.startswith("calibration_contract_"):
            if not isinstance(data.get("intent"), str) or not data["intent"].strip():
                raise ValueError("Behavioral contract must include an intent")
        else:
            validated_scores(data)

    def complete(prompt: str) -> dict:
        response = llm.complete(
            prompt,
            purpose="functional_similarity",
            system="Return only the requested JSON object.",
            tag=tag,
            validate=validate,
        )
        return _json_from_text(response.text)
    return complete


def _stability_prompt(contract, candidate: str) -> str:
    return f'''Evaluate functional preservation using the behavioral contract below. Score each dimension from 0 to 1. The dimension order is intentionally reversed for a stability check.
Return exactly one JSON object with keys: edge_cases, invariants, side_effects, io_semantics, behavior, confidence, rationale.
Do not reward security improvements by themselves and do not judge coding style.

BEHAVIORAL CONTRACT:
{contract.render()[:9000]}

CANDIDATE PROGRAM:
```python
{candidate[:18000]}
```'''


def _score_stability(contract, candidate: str, llm: LLMClient) -> dict:
    from evaluation.functional_similarity import DIMENSION_WEIGHTS

    data = _json_from_text(
        llm.complete(
            _stability_prompt(contract, candidate),
            purpose="functional_similarity_stability",
            system="Return only the requested JSON object.",
            tag="reverse_dimension_order",
            validate=lambda text: validated_scores(_json_from_text(text)),
        ).text
    )
    dims, confidence = validated_scores(data)
    weighted = sum(DIMENSION_WEIGHTS[name] * dims[name] for name in dims)
    worst = min(dims.values()) if dims else 0.0
    return {
        "laaj_score": round(0.75 * weighted + 0.25 * worst, 5),
        "dimensions": dims,
        "confidence": confidence,
    }


def judge_run(cfg: dict, *, llm: LLMClient | None = None, force: bool = False) -> dict:
    """Score the functional similarity of every completed enforcement result; resumable per program."""
    run_dir = _run_dir(cfg)
    judge_dir = run_dir / "judge"
    judge_dir.mkdir(parents=True, exist_ok=True)
    records, excluded = collect_records(cfg)
    eligible = [rec for rec in records if rec["status"] in COMPLETED_STATUSES]
    skipped_failed = sum(rec["status"] == "failed" for rec in records)
    client: LLMClient | None = None
    if eligible:
        client = llm or client_from_config(cfg, "judge", call_log=run_dir / "calls.jsonl")
    judged = resumed = failed = 0
    config_hash = judge_config_hash(cfg)
    test_dir = resolve_path(cfg, cfg["data"]["test_dir"])
    for rec in eligible:
        assert client is not None
        filename = rec["file"]
        out_path = judge_dir / f"{Path(filename).stem}.json"
        error_path = judge_dir / "errors" / out_path.name
        if out_path.exists() and not force:
            try:
                previous = json.loads(out_path.read_text(encoding="utf-8"))
                if judge_record_issue(previous, cfg, rec) is None:
                    resumed += 1
                    continue
            except (OSError, ValueError, TypeError):
                pass
        out_path.unlink(missing_ok=True)
        error_path.unlink(missing_ok=True)
        try:
            original = (test_dir / filename).read_text(encoding="utf-8")
            candidate = (run_dir / "vetted_code" / filename).read_text(encoding="utf-8")
            if sha256_text(original) != rec["source_hash"] or sha256_text(candidate) != rec["candidate_hash"]:
                raise ValueError("Sample content changed during judge preparation")
            contract = extract_behavioral_contract(original, _completion(client, "contract"))
            report = score_candidate_functionality(contract, candidate, _completion(client, "primary"))
            row = report.to_dict()
            row.update(
                schema=RESULT_SCHEMA, file=filename, contract=contract.to_dict(),
                original_hash=rec["source_hash"], candidate_hash=rec["candidate_hash"],
                enforcement_config_hash=rec["config_hash"], judge_config_hash=config_hash,
            )
            if cfg["judge"].get("stability_check", True):
                stability = _score_stability(contract, candidate, client)
                row["stability_score"] = stability["laaj_score"]
                row["stability_abs_difference"] = round(abs(row["laaj_score"] - stability["laaj_score"]), 5)
                row["stability_dimensions"] = stability["dimensions"]
            atomic_write_json(out_path, row)
            judged += 1
        except Exception as exc:
            failed += 1
            atomic_write_json(error_path, {
                "file": filename, "candidate_hash": rec["candidate_hash"],
                "judge_config_hash": config_hash, "error": f"{type(exc).__name__}: {exc}",
            })
    summary = {
        "judged_now": judged, "resumed": resumed, "failed_now": failed,
        "skipped_failed_samples": skipped_failed, "excluded": excluded, "judge_dir": str(judge_dir),
    }
    atomic_write_json(run_dir / "judge_summary.json", summary)
    return summary


def _semantic_reformat(code: str) -> str:
    tree = ast.parse(code)
    return ast.unparse(tree) + "\n"


def _reduced_negative_control(code: str) -> str:
    tree = ast.parse(code)
    parts = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            args = ast.unparse(node.args)
            parts.append(f"{prefix} {node.name}({args}):\n    return None\n")
        elif isinstance(node, ast.ClassDef):
            parts.append(f"class {node.name}:\n    pass\n")
    return "\n".join(parts) or "pass\n"


def calibrate_judge(cfg: dict, *, llm: LLMClient | None = None, limit: int | None = None) -> dict:
    """Score fixed positive and negative calibration controls to check judge separation."""
    run_dir = _run_dir(cfg)
    run_dir.mkdir(parents=True, exist_ok=True)
    llm = llm or client_from_config(cfg, "judge", call_log=run_dir / "calls.jsonl")
    n = int(limit if limit is not None else cfg["judge"].get("calibration_limit", len(CASES)))
    if n < 1:
        raise ValueError("Calibration limit must be at least 1")
    cases = CASES[:n]
    rows: list[dict] = []
    for case in cases:
        original = case["original"]
        contract = extract_behavioral_contract(original, _completion(llm, "calibration_contract_" + case["name"]))
        controls = [
            ("identical", original, "positive"),
            ("semantic_reformat", _semantic_reformat(original), "positive"),
            ("changed_behavior", case["changed"], "negative"),
            ("reduced_program", _reduced_negative_control(original), "negative"),
        ]
        for control, candidate, expected in controls:
            report = score_candidate_functionality(contract, candidate, _completion(llm, "calibration_" + control + "_" + case["name"]))
            rows.append({"case": case["name"], "control": control, "expected": expected, "laaj_score": report.laaj_score, "gated_score": report.gated_score})
    positive = [r["laaj_score"] for r in rows if r["expected"] == "positive"]
    negative = [r["laaj_score"] for r in rows if r["expected"] == "negative"]
    positive_mean = sum(positive) / len(positive)
    negative_mean = sum(negative) / len(negative)
    summary = {
        "cases": len(cases), "controls": len(rows), "judge_config_hash": judge_config_hash(cfg),
        "positive_mean": round(positive_mean, 5), "negative_mean": round(negative_mean, 5),
        "separation": round(positive_mean - negative_mean, 5), "rows": rows,
        "witnesses": [{key: case[key] for key in ("name", "arguments", "expected", "changed_expected")} for case in cases],
    }
    atomic_write_json(run_dir / "judge_calibration.json", summary)
    return summary
