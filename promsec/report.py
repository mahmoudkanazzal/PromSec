"""Per-program tables, aggregate summaries and figures of a PromSec run."""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path

from .figures import write_performance_eval
from .io import atomic_write_json, rounded
from .records import (
    COMPLETED_STATUSES,
    TERMINAL_STATUSES,
    _run_dir,
    _test_files,
    collect_records,
    judge_record_issue,
)
from .similarity import similarities

FIELDS = (
    "file", "status", "error", "judge_status", "cwe_count_before", "cwe_count_after", "cwes_before", "cwes_after",
    "iterations_used", "selected_iteration", "ast_similarity", "graph_similarity", "embedding_similarity",
    "laaj_score", "laaj_gated_score", "laaj_stability_abs_difference",
)


def _mean(values):
    values = [float(v) for v in values if v is not None and v != ""]
    return sum(values) / len(values) if values else None


def _json_list(value) -> str:
    return json.dumps(value if isinstance(value, list) else [], separators=(",", ":"))


def _row(rec: dict, judge: dict, judge_status: str, original: str | None, output: str | None) -> dict:
    sims = similarities(original, output) if rec.get("status") in COMPLETED_STATUSES and original and output else {}
    return {
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
        "ast_similarity": rec.get("ast_similarity"),
        "graph_similarity": sims.get("graph_similarity"),
        "embedding_similarity": sims.get("embedding_similarity"),
        "laaj_score": judge.get("laaj_score"),
        "laaj_gated_score": judge.get("gated_score"),
        "laaj_stability_abs_difference": judge.get("stability_abs_difference"),
    }


def summarize(rows: list[dict], selected: int) -> dict:
    """Aggregate security and functionality numbers of the per-program rows."""
    status_counts: dict[str, int] = {}
    for row in rows:
        status = row["status"] or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
    vulnerable = [r for r in rows if isinstance(r.get("cwe_count_before"), int) and r["cwe_count_before"] > 0]
    secured = [r for r in vulnerable if r["status"] == "secured" and r.get("cwe_count_after") == 0]
    completed = [r for r in rows if r["status"] in COMPLETED_STATUSES]
    measured = [r for r in vulnerable if isinstance(r.get("cwe_count_after"), int)]
    before = sum(int(r["cwe_count_before"]) for r in measured)
    after = sum(int(r["cwe_count_after"]) for r in measured)
    remaining: Counter = Counter()
    for r in completed:
        remaining.update(int(c) for c in json.loads(r["cwes_after"] or "[]"))
    return {
        "programs": len(rows),
        "programs_selected": selected,
        "terminal_programs": sum(1 for r in rows if r["status"] in TERMINAL_STATUSES),
        "completed_programs": len(completed),
        "failed_programs": status_counts.get("failed", 0),
        "status_counts": status_counts,
        "vulnerable_programs": len(vulnerable),
        "secured_programs": len(secured),
        "programs_with_cwes_left": sum(1 for r in measured if int(r["cwe_count_after"]) > 0),
        "cwes_before": before,
        "cwes_after": after,
        "cwe_reduction_rate": (before - after) / before if before else None,
        "remaining_cwe_ids": {f"CWE-{k}": v for k, v in sorted(remaining.items())},
        "mean_iterations_vulnerable": _mean(r.get("iterations_used") for r in vulnerable if r["status"] in COMPLETED_STATUSES),
        "mean_ast_similarity": _mean(r.get("ast_similarity") for r in completed),
        "mean_graph_similarity": _mean(r.get("graph_similarity") for r in completed),
        "mean_embedding_similarity": _mean(r.get("embedding_similarity") for r in completed),
        "mean_laaj_score": _mean(r.get("laaj_score") for r in completed),
        "mean_laaj_gated_score": _mean(r.get("laaj_gated_score") for r in completed),
    }


def write_outputs(rows: list[dict], summary: dict, out_dir: Path, llm_name: str, label: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "per_sample.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FIELDS))
        writer.writeheader()
        writer.writerows([rounded(row) for row in rows])
    if rows:
        summary["figures"] = [str(Path(p).relative_to(out_dir)) for p in write_performance_eval(rows, out_dir, llm_name, label)]
    atomic_write_json(out_dir / "summary.json", rounded(summary))
    return summary


def build_report(cfg: dict) -> dict:
    """Write ``report/`` of a run: per-program table, summary and figures (current records only)."""
    run_dir = _run_dir(cfg)
    records, excluded = collect_records(cfg)
    sources = {p.name: p for p in _test_files(cfg)}
    rows = []
    for rec in records:
        judge, judge_status = {}, "not_available"
        judge_path = run_dir / "judge" / (Path(rec["file"]).stem + ".json")
        if rec["status"] not in COMPLETED_STATUSES:
            judge_status = "sample_failed"
        elif judge_path.exists():
            try:
                candidate = json.loads(judge_path.read_text(encoding="utf-8"))
                issue = judge_record_issue(candidate, cfg, rec)
                judge, judge_status = ({}, issue) if issue else (candidate, "current")
            except (OSError, ValueError, TypeError):
                judge_status = "unreadable_judge_record"
        output = run_dir / "vetted_code" / rec["file"]
        rows.append(_row(rec, judge, judge_status, sources[rec["file"]].read_text(encoding="utf-8"),
                         output.read_text(encoding="utf-8") if output.is_file() else None))
    summary = summarize(rows, len(sources))
    summary.update(run=cfg["run"]["name"], variant=cfg["guidance"]["mode"],
                   excluded_programs=[e for e in excluded if e["reason"] != "not_evaluated"])
    calls = _calls(run_dir / "calls.jsonl")
    summary.update(_usage(calls))
    models = Counter(str(c["model"]) for c in calls if c.get("model"))
    llm_name = models.most_common(1)[0][0] if models else os.environ.get(str(cfg["llm"].get("model_env", "")), "LLM")
    return write_outputs(rows, summary, run_dir / "report", llm_name, variant_label(cfg["guidance"]["mode"]))


def _calls(path: Path) -> list[dict]:
    calls = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                call = json.loads(line)
            except ValueError:
                continue
            if isinstance(call, dict):
                calls.append(call)
    return calls


def _usage(calls: list[dict]) -> dict:
    return {
        "llm_requests_logged": len(calls),
        "llm_cache_hits": sum(1 for c in calls if c.get("cached")),
        "prompt_tokens": sum(int(c.get("prompt_tokens", 0) or 0) for c in calls if not c.get("cached")),
        "completion_tokens": sum(int(c.get("completion_tokens", 0) or 0) for c in calls if not c.get("cached")),
    }


VARIANT_LABELS = {"promsec": "PromSec", "promsec-s": "PromSec-S", "none": "No gGAN"}


def variant_label(mode: str) -> str:
    return VARIANT_LABELS.get(mode, mode)


def build_archive_report(run_dir: Path, test_dir: Path, llm_name: str) -> dict:
    """Report of a finished run folder (``results/<variant>/run<k>``): no identity checks against the current code."""
    sources = {p.name: p for p in sorted(test_dir.glob("*.py"))}
    rows: list[dict] = []
    variants: Counter = Counter()
    for path in sorted((run_dir / "samples").glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("status") not in TERMINAL_STATUSES:
            continue
        variants[rec.get("guidance_mode")] += 1
        judge_path = run_dir / "judge" / path.name
        judge = json.loads(judge_path.read_text(encoding="utf-8")) if judge_path.is_file() else {}
        status = "current" if judge else ("sample_failed" if rec["status"] not in COMPLETED_STATUSES else "not_available")
        output = run_dir / "outputs" / rec["file"]
        rows.append(_row(rec, judge, status, sources[rec["file"]].read_text(encoding="utf-8"),
                         output.read_text(encoding="utf-8") if output.is_file() else None))
    mode = variants.most_common(1)[0][0] if variants else ""
    summary = summarize(rows, len(sources))
    summary.update(run=run_dir.name, variant=mode)
    return write_outputs(rows, summary, run_dir, llm_name, variant_label(mode))
