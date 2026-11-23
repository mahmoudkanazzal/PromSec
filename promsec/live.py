"""Per-program results printed while an enforcement run is in progress."""

from __future__ import annotations

import csv
import json
import os
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

from .io import atomic_write_text
from .judge import judge_run
from .llm import LLMClient
from .records import (
    COMPLETED_STATUSES,
    TERMINAL_STATUSES,
    _run_dir,
    _test_files,
    collect_records,
    judge_record_issue,
)
from .similarity import similarities

LIVE_FIELDS = (
    "file", "status", "cwe_before", "cwe_after", "cwe_reduction", "iterations",
    "ast_similarity", "graph_similarity", "embedding_similarity", "laaj_score", "laaj_gated_score", "error", "timestamp",
)


def _judge_client(cfg: dict, run_dir: Path) -> LLMClient:
    """Judge client with its own response cache, so it can run beside enforcement."""
    settings = cfg["judge"]
    model = os.environ.get(settings["model_env"])
    if not model:
        raise RuntimeError(f"Environment variable {settings['model_env']} is not set")
    return LLMClient(
        model,
        api_key_env=settings.get("api_key_env", "OPENAI_API_KEY"),
        base_url=os.environ.get(settings.get("base_url_env", "")) or None,
        temperature=float(settings.get("temperature", 0.0)),
        max_retries=int(settings.get("max_retries", 2)),
        cache_path=Path(cfg["_root"]) / "cache" / "live_judge_cache.sqlite",
        call_log=run_dir / "calls.jsonl",
    )


def _judge_result(cfg: dict, run_dir: Path, rec: dict) -> tuple[dict | None, str]:
    """Valid judge record for ``rec``, or the judge error text, or neither yet."""
    stem = Path(rec["file"]).stem
    path = run_dir / "judge" / f"{stem}.json"
    if path.is_file():
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            row = None
        if isinstance(row, dict) and judge_record_issue(row, cfg, rec) is None:
            return row, ""
    error_path = run_dir / "judge" / "errors" / f"{stem}.json"
    if error_path.is_file():
        try:
            return None, str(json.loads(error_path.read_text(encoding="utf-8")).get("error", "judge error"))
        except (OSError, ValueError):
            return None, "judge error"
    return None, ""


def _row(rec: dict, judged: dict | None, judge_error: str, sims: dict | None = None) -> dict:
    before, after = rec.get("cwe_count_before"), rec.get("cwe_count_after")
    reduction = before - after if isinstance(before, int) and isinstance(after, int) else None
    sims = sims or {}
    return {
        "file": rec["file"],
        "status": rec.get("status"),
        "cwe_before": before,
        "cwe_after": after,
        "cwe_reduction": reduction,
        "iterations": len(rec.get("iterations") or []),
        "ast_similarity": rec.get("ast_similarity"),
        "graph_similarity": sims.get("graph_similarity"),
        "embedding_similarity": sims.get("embedding_similarity"),
        "laaj_score": judged.get("laaj_score") if judged else None,
        "laaj_gated_score": judged.get("gated_score") if judged else None,
        "error": rec.get("error") or judge_error,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),  # noqa: UP017 (Python 3.10 support)
    }


def _similarities(sources: dict[str, Path], run_dir: Path, rec: dict) -> dict:
    """Graph and embedding similarity of the program's output to the original (completed programs only)."""
    output = run_dir / "vetted_code" / rec["file"]
    source = sources.get(rec["file"])
    if rec.get("status") not in COMPLETED_STATUSES or not output.is_file() or source is None:
        return {}
    return similarities(source.read_text(encoding="utf-8"), output.read_text(encoding="utf-8"))


def _fmt(value, digits: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}" if isinstance(value, float) else str(value)


def _number(value) -> float | None:
    try:
        return None if value is None or value == "" else float(value)
    except (TypeError, ValueError):
        return None


_COLUMNS = (
    ("#", 4, ">"), ("File", 16, "<"), ("Status", 14, "<"), ("CWE before", 10, ">"), ("CWE after", 9, ">"),
    ("Reduction", 9, ">"), ("Iterations", 10, ">"), ("Graph sim.", 10, ">"), ("LAAJ (gated)", 14, ">"),
)
_STATUS = {"secured": "secured", "max_iterations_reached": "CWEs remain", "already_clean": "clean at start", "failed": "failed"}


def _table_line(values: list[str]) -> str:
    return "  " + "  ".join(f"{value:{align}{width}}" for value, (_, width, align) in zip(values, _COLUMNS))


def _header() -> str:
    return "\n".join([
        "",
        _table_line([name for name, _, _ in _COLUMNS]),
        _table_line(["-" * width for _, width, _ in _COLUMNS]),
    ])


def _reduction_text(reduction) -> str:
    if not isinstance(reduction, int):
        return "-"
    return str(reduction) if reduction >= 0 else f"+{-reduction} more"


def _table_row(position: int, row: dict) -> str:
    failed = row["status"] == "failed"
    laaj = "-" if row["laaj_score"] is None else f"{row['laaj_score']:.2f} ({_fmt(row['laaj_gated_score'])})"
    graph = _number(row["graph_similarity"])
    values = [
        str(position),
        row["file"],
        _STATUS.get(row["status"], str(row["status"])),
        _fmt(row["cwe_before"]),
        "-" if failed else _fmt(row["cwe_after"]),
        "-" if failed else _reduction_text(row["cwe_reduction"]),
        "-" if failed else str(row["iterations"]),
        "-" if graph is None or failed else f"{graph:.3f}",
        laaj,
    ]
    return _table_line(values)


def _summary(rows: list[dict], total: int) -> str:
    done = [r for r in rows if r["status"] in COMPLETED_STATUSES]
    secured = sum(1 for r in done if r["status"] == "secured")
    failed = sum(1 for r in rows if r["status"] == "failed")
    vulnerable = [r for r in done if isinstance(r["cwe_before"], int) and r["cwe_before"] > 0]
    before = sum(r["cwe_before"] for r in vulnerable)
    after = sum(r["cwe_after"] for r in vulnerable if isinstance(r["cwe_after"], int))
    fewer = f"{100.0 * (before - after) / before:.1f}% fewer" if before else "-"
    laaj = [r["laaj_score"] for r in done if r["laaj_score"] is not None]
    graph = [v for r in done if (v := _number(r["graph_similarity"])) is not None]
    mean_laaj = f"{sum(laaj) / len(laaj):.2f}" if laaj else "-"
    mean_graph = f"{sum(graph) / len(graph):.3f}" if graph else "-"
    return (
        f"  Total: {len(rows)} of {total} done  |  {secured} secured  |  {failed} failed  |  "
        f"CWEs {before} -> {after} ({fewer})  |  mean graph sim. {mean_graph}  |  mean LAAJ {mean_laaj}"
    )


def watch_results(
    cfg: dict,
    *,
    judge: bool = True,
    interval: float = 15.0,
    once: bool = False,
    llm: LLMClient | None = None,
    stream: TextIO | None = None,
) -> list[dict]:
    """Print one table row per finished program, with LAAJ when judging is enabled."""
    warnings.filterwarnings("ignore")
    out = stream
    run_dir = _run_dir(cfg)
    total = len(_test_files(cfg))
    order = {path.name: i for i, path in enumerate(_test_files(cfg))}
    sources = {path.name: path for path in _test_files(cfg)}
    csv_path = run_dir / "live_results.csv"
    rows: list[dict] = []
    printed: set[str] = set()
    if csv_path.is_file():
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            existing_rows = list(reader)
            header = tuple(reader.fieldnames or ())
        printed.update(r["file"] for r in existing_rows)
        if header != LIVE_FIELDS:
            tmp = csv_path.with_suffix(".csv.tmp")
            with tmp.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=LIVE_FIELDS, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(existing_rows)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, csv_path)
    judge_llm = llm
    shown: set[str] = set()
    totals_path = run_dir / "live_totals.txt"

    def emit(text: str) -> None:
        print(text, file=out, flush=True)

    header_printed = False

    def show(row: dict) -> None:
        nonlocal header_printed
        if not header_printed:
            emit(f"\n  Run {cfg['run']['name']}  |  variant {cfg['guidance']['mode']}")
            emit(_header())
            header_printed = True
        emit(_table_row(len(shown), row))

    while True:
        records, _ = collect_records(cfg)
        terminal = [rec for rec in records if rec.get("status") in TERMINAL_STATUSES]
        if judge and any(rec.get("status") in COMPLETED_STATUSES for rec in terminal):
            pending = [
                rec for rec in terminal
                if rec.get("status") in COMPLETED_STATUSES and rec["file"] not in printed
                and _judge_result(cfg, run_dir, rec) == (None, "")
            ]
            if pending:
                judge_llm = judge_llm or _judge_client(cfg, run_dir)
                judge_run(cfg, llm=judge_llm)
        before_count = len(shown)
        for rec in sorted(terminal, key=lambda r: order.get(r["file"], 0)):
            judged, judge_error = _judge_result(cfg, run_dir, rec)
            row = _row(rec, judged, judge_error, _similarities(sources, run_dir, rec) if rec["file"] not in shown else None)
            if rec["file"] in printed:
                if rec["file"] not in shown:
                    rows.append(row)
                    shown.add(rec["file"])
                    show(row)
                continue
            if judge and rec.get("status") in COMPLETED_STATUSES and judged is None and not judge_error:
                continue
            rows.append(row)
            printed.add(rec["file"])
            shown.add(rec["file"])
            new_file = not csv_path.exists()
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            with csv_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=LIVE_FIELDS)
                if new_file:
                    writer.writeheader()
                writer.writerow(row)
                handle.flush()
                os.fsync(handle.fileno())
            show(row)
        finished = len(printed) >= total or once
        if len(shown) > before_count:
            atomic_write_text(totals_path, _summary(rows, total).strip() + "\n")
        if finished:
            if rows:
                emit("")
                emit(_summary(rows, total))
            return rows
        time.sleep(interval)
