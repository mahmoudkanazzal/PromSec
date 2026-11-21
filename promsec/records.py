"""Identity checks shared by enforcement, judging, and reporting."""

from __future__ import annotations

import json
from pathlib import Path

from .config import judge_config_hash, relevant_config_hash, resolve_path
from .io import sha256_text

RESULT_SCHEMA = 1
COMPLETED_STATUSES = {"already_clean", "secured", "max_iterations_reached"}
TERMINAL_STATUSES = COMPLETED_STATUSES | {"failed"}


def _run_dir(cfg: dict) -> Path:
    return resolve_path(cfg, cfg["run"]["root"]) / cfg["run"]["name"]


def _test_files(cfg: dict) -> list[Path]:
    files = sorted(resolve_path(cfg, cfg["data"]["test_dir"]).glob("*.py"))
    limit = cfg["data"].get("test_limit")
    return files[:int(limit)] if limit else files


def record_issue(rec: dict, cfg: dict, source: Path, config_hash: str | None = None) -> str | None:
    """Reason a stored enforcement record is not valid for the current inputs, or ``None``."""
    if not isinstance(rec, dict) or rec.get("schema") != RESULT_SCHEMA:
        return "record_schema_mismatch"
    if rec.get("file") != source.name:
        return "filename_mismatch"
    if rec.get("source_hash") != sha256_text(source.read_text(encoding="utf-8")):
        return "source_changed"
    if rec.get("config_hash") != (config_hash or relevant_config_hash(cfg)):
        return "enforcement_configuration_changed"

    status = rec.get("status")
    if status == "failed":
        return None
    if status not in COMPLETED_STATUSES or rec.get("complete") is not True:
        return "incomplete_record"

    candidate = _run_dir(cfg) / "vetted_code" / source.name
    if not candidate.is_file():
        return "candidate_missing"
    if rec.get("candidate_hash") != sha256_text(candidate.read_text(encoding="utf-8")):
        return "candidate_changed"
    return None


def collect_records(cfg: dict) -> tuple[list[dict], list[dict]]:
    """Valid enforcement records for the selected programs, and the excluded ones with reasons."""
    records, excluded = [], []
    config_hash = relevant_config_hash(cfg)
    for source in _test_files(cfg):
        path = _run_dir(cfg) / "samples" / (source.stem + ".json")
        if not path.exists():
            excluded.append({"file": source.name, "reason": "not_evaluated"})
            continue
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
            issue = record_issue(rec, cfg, source, config_hash)
        except (OSError, ValueError, TypeError) as exc:
            issue = "unreadable_record: " + type(exc).__name__
        if issue:
            excluded.append({"file": source.name, "reason": issue})
        else:
            records.append(rec)
    return records, excluded


def judge_record_issue(row: dict, cfg: dict, rec: dict) -> str | None:
    """Reason a stored judge record does not match its enforcement record, or ``None``."""
    if not isinstance(row, dict) or row.get("schema") != RESULT_SCHEMA:
        return "judge_schema_mismatch"
    expected = {
        "file": rec["file"],
        "original_hash": rec["source_hash"],
        "candidate_hash": rec.get("candidate_hash"),
        "enforcement_config_hash": rec["config_hash"],
        "judge_config_hash": judge_config_hash(cfg),
    }
    for key, value in expected.items():
        if row.get(key) != value:
            return "judge_" + key + "_mismatch"
    return None
