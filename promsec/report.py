"""Aggregate reports and figures."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path

from .figures import write_performance_eval
from .io import atomic_write_json
from .records import (
    COMPLETED_STATUSES,
    TERMINAL_STATUSES,
    _run_dir,
    _test_files,
    collect_records,
    judge_record_issue,
)


def _mean(values):
    values = [float(v) for v in values if v is not None]
    return sum(values) / len(values) if values else None


def _json_list(value) -> str:
    return json.dumps(value if isinstance(value, list) else [], separators=(",", ":"))


def _training_summary(cfg: dict, run_dir: Path, report_dir: Path) -> dict | None:
    """Final training and validation losses of the active gGAN, with its loss curves."""
    from .config import resolve_path
    from .train import LOSS_KEYS, _last_log_row, write_training_curves

    if int(cfg["training"].get("train_from_scratch", 0)):
        source, log_path = "fresh training", run_dir / "training" / "training.jsonl"
    else:
        source, log_path = "packaged checkpoints", resolve_path(cfg, "models/training_log.jsonl")
    if not log_path.is_file():
        return None
    final = _last_log_row(log_path)
    if "val_generator_loss" not in final:
        return None
    write_training_curves(log_path, report_dir)
    return {
        "source": source,
        "epochs": final["epoch"],
        "train_samples": final.get("train_samples"),
        "validation_samples": final.get("validation_samples"),
        **{f"final_{split}_{key}": final[f"{split}_{key}"] for split in ("train", "val") for key in LOSS_KEYS},
    }


def build_report(cfg: dict) -> dict:
    """Write the per-program and aggregate reports and figures for a run."""
    run_dir = _run_dir(cfg)
    report_dir = run_dir / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "performance_eval.png",
        "performance_eval.pdf",
        "training_curves.png",
        "training_curves.csv",
    ):
        (report_dir / name).unlink(missing_ok=True)
    samples, excluded = collect_records(cfg)

    rows = []
    raw_by_file = {}
    for rec in samples:
        raw_by_file[rec.get("file")] = rec
        key = Path(rec["file"]).stem
        judge = {}
        judge_status = "not_available"
        judge_path = run_dir / "judge" / (key + ".json")
        if rec["status"] not in COMPLETED_STATUSES:
            judge_status = "sample_failed"
        elif judge_path.exists():
            try:
                candidate = json.loads(judge_path.read_text(encoding="utf-8"))
                issue = judge_record_issue(candidate, cfg, rec)
                if issue:
                    judge_status = issue
                else:
                    judge = candidate
                    judge_status = "current"
            except (OSError, ValueError, TypeError):
                judge_status = "unreadable_judge_record"
        row = {
            "file": rec.get("file"),
            "status": rec.get("status"),
            "error": rec.get("error", ""),
            "judge_status": judge_status,
            "cwe_count_before": rec.get("cwe_count_before"),
            "cwe_count_after": rec.get("cwe_count_after"),
            "cwes_before": _json_list(rec.get("cwes_before")),
            "cwes_after": _json_list(rec.get("cwes_after")),
            "iterations_used": rec.get("iterations_used"),
            "selected_iteration": rec.get("selected_iteration"),
            "gnn_feature_change": rec.get("gnn_feature_change"),
            "ast_similarity": rec.get("ast_similarity"),
            "laaj_score": judge.get("laaj_score"),
            "laaj_gated_score": judge.get("gated_score"),
            "laaj_stability_abs_difference": judge.get("stability_abs_difference"),
        }
        rows.append(row)

    fieldnames = list(rows[0]) if rows else [
        "file", "status", "error", "judge_status", "cwe_count_before", "cwe_count_after",
        "cwes_before", "cwes_after", "iterations_used", "selected_iteration",
        "gnn_feature_change", "ast_similarity", "laaj_score", "laaj_gated_score",
        "laaj_stability_abs_difference",
    ]
    with (report_dir / "per_sample.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    status_counts = {}
    for row in rows:
        status = row["status"] or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
    vulnerable = [r for r in rows if isinstance(r.get("cwe_count_before"), int) and r["cwe_count_before"] > 0]
    secured = [r for r in vulnerable if r["status"] == "secured" and r.get("cwe_count_after") == 0]
    completed = [r for r in rows if r["status"] in COMPLETED_STATUSES]
    terminal = [r for r in rows if r["status"] in TERMINAL_STATUSES]
    completed_vulnerable = [r for r in completed if isinstance(r.get("cwe_count_before"), int) and r["cwe_count_before"] > 0]
    measured_vulnerable = [r for r in vulnerable if isinstance(r.get("cwe_count_after"), int)]
    total_before = sum(int(r["cwe_count_before"]) for r in measured_vulnerable)
    total_after = sum(int(r["cwe_count_after"]) for r in measured_vulnerable)
    total_removed = total_before - total_after

    calls = []
    invalid_call_log_lines = []
    call_log = run_dir / "calls.jsonl"
    if call_log.exists():
        for number, line in enumerate(call_log.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    call = json.loads(line)
                    if not isinstance(call, dict):
                        raise ValueError("Call record must be an object")
                    calls.append(call)
                except ValueError:
                    invalid_call_log_lines.append(number)

    summary = {
        "samples": len(rows),
        "samples_selected": len(_test_files(cfg)),
        "excluded_samples": excluded,
        "terminal_samples": len(terminal),
        "completed_samples": len(completed),
        "failed_samples": status_counts.get("failed", 0),
        "status_counts": status_counts,
        "vulnerable_inputs": len(vulnerable),
        "vulnerable_inputs_with_after_scan": len(measured_vulnerable),
        "secured_vulnerable_inputs": len(secured),
        "remaining_vulnerable_inputs": sum(1 for r in measured_vulnerable if int(r["cwe_count_after"]) > 0),
        "enforcement_success_rate": (len(secured) / len(vulnerable)) if vulnerable else None,
        "enforcement_success_rate_completed": (len(secured) / len(completed_vulnerable)) if completed_vulnerable else None,
        "aggregate_unique_cwe_occurrences_before": total_before,
        "aggregate_unique_cwe_occurrences_after": total_after,
        "aggregate_unique_cwe_occurrences_removed": total_removed,
        "aggregate_cwe_reduction_rate": (total_removed / total_before) if total_before else None,
        "mean_cwe_count_before": _mean(r.get("cwe_count_before") for r in completed),
        "mean_cwe_count_after": _mean(r.get("cwe_count_after") for r in completed),
        "mean_gnn_feature_change": _mean(r.get("gnn_feature_change") for r in rows),
        "mean_ast_similarity": _mean(r.get("ast_similarity") for r in rows),
        "mean_laaj_score": _mean(r.get("laaj_score") for r in rows),
        "mean_laaj_gated_score": _mean(r.get("laaj_gated_score") for r in rows),
        "mean_laaj_stability_abs_difference": _mean(r.get("laaj_stability_abs_difference") for r in rows),
        "llm_requests_logged": len(calls),
        "invalid_call_log_lines": invalid_call_log_lines,
        "llm_cache_hits": sum(1 for c in calls if c.get("cached")),
        "prompt_tokens": sum(int(c.get("prompt_tokens", 0) or 0) for c in calls if not c.get("cached")),
        "completion_tokens": sum(int(c.get("completion_tokens", 0) or 0) for c in calls if not c.get("cached")),
        "cached_prompt_tokens": sum(int(c.get("prompt_tokens", 0) or 0) for c in calls if c.get("cached")),
        "cached_completion_tokens": sum(int(c.get("completion_tokens", 0) or 0) for c in calls if c.get("cached")),
        "llm_seconds": round(sum(float(c.get("seconds", 0) or 0) for c in calls), 3),
    }
    summary["training"] = _training_summary(cfg, run_dir, report_dir)
    atomic_write_json(report_dir / "summary.json", summary)

    if rows:
        models = Counter(str(c["model"]) for c in calls if c.get("model"))
        llm_name = models.most_common(1)[0][0] if models else os.environ.get(str(cfg["llm"].get("model_env", "")), "LLM")
        summary["figures"] = write_performance_eval(rows, report_dir, llm_name)
        atomic_write_json(report_dir / "summary.json", summary)

    return summary
