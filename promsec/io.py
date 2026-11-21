"""Atomic file writes and hashing."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path


def sha256_text(text: str) -> str:
    """SHA-256 hex digest of ``text`` encoded as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_write_text(path: str | Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically (temporary file, fsync, rename)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def atomic_write_json(path: str | Path, value: object) -> None:
    """Write ``value`` as JSON to ``path`` atomically."""
    atomic_write_text(path, json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def append_jsonl(path: str | Path, value: object) -> None:
    """Append ``value`` as one JSON line to ``path`` and fsync."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
