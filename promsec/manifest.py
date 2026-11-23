"""Dataset manifest: hashes, sizes, and parse status of the packaged programs."""

from __future__ import annotations

import ast
import csv
import hashlib
import warnings
from collections import defaultdict
from pathlib import Path

from .config import resolve_path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(cfg: dict) -> list[dict]:
    """Manifest rows for every training and evaluation program."""
    all_rows = []
    for split, key in (("training", "training_dir"), ("test", "test_dir")):
        directory = resolve_path(cfg, cfg["data"][key])
        for path in sorted(directory.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            parse_ok = True
            try:
                with warnings.catch_warnings():  # dataset programs contain invalid escape sequences
                    warnings.simplefilter("ignore", SyntaxWarning)
                    ast.parse(text, filename=str(path))
            except SyntaxError:
                parse_ok = False
            all_rows.append(
                {
                    "split": split,
                    "filename": path.name,
                    "sha256": _sha256(path),
                    "bytes": path.stat().st_size,
                    "parse_ok": parse_ok,
                }
            )
    groups = defaultdict(list)
    for row in all_rows:
        groups[row["sha256"]].append(row)
    duplicate_id = 0
    for same in groups.values():
        if len(same) > 1:
            duplicate_id += 1
            for row in same:
                row["duplicate_group"] = duplicate_id
        else:
            same[0]["duplicate_group"] = ""
    return all_rows


def write_manifest(cfg: dict, path: str | Path | None = None) -> Path:
    """Write the dataset manifest CSV."""
    output = Path(path) if path else Path(cfg["_root"]) / "data" / "MANIFEST.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    data = rows(cfg)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["split", "filename", "sha256", "bytes", "parse_ok", "duplicate_group"])
        writer.writeheader()
        writer.writerows(data)
    return output


def check_manifest(cfg: dict, path: str | Path | None = None) -> dict:
    """Verify the packaged programs against the dataset manifest."""
    manifest = Path(path) if path else Path(cfg["_root"]) / "data" / "MANIFEST.csv"
    if not manifest.exists():
        raise FileNotFoundError(manifest)
    expected = {(row["split"], row["filename"]): row for row in rows(cfg)}
    with manifest.open("r", newline="", encoding="utf-8") as handle:
        recorded = {(row["split"], row["filename"]): row for row in csv.DictReader(handle)}
    if set(expected) != set(recorded):
        raise AssertionError("Dataset manifest file list does not match packaged data")
    mismatches = []
    for key, row in expected.items():
        old = recorded[key]
        if old["sha256"] != row["sha256"] or old["parse_ok"].lower() != str(row["parse_ok"]).lower():
            mismatches.append(key)
    if mismatches:
        raise AssertionError(f"Dataset manifest mismatch for {len(mismatches)} files")
    return {"entries": len(expected), "training": sum(k[0] == "training" for k in expected), "test": sum(k[0] == "test" for k in expected)}
