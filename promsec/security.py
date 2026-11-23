"""Bandit execution and unique-CWE counting."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile

from .metrics import validate_python_source


class SecurityAnalysisError(RuntimeError):
    """Security analysis did not complete successfully."""


class AnalysisInterrupted(SecurityAnalysisError):
    """Bandit was terminated by a signal (stop, Ctrl-C, kill): an interruption, not a property of the program."""


def run_bandit(code: str, require_compile: bool = True) -> dict:
    """Run Bandit on ``code`` and return its validated JSON report."""
    validate_python_source(code, require_compile=require_compile)
    executable = shutil.which("bandit")
    if executable is None:
        raise SecurityAnalysisError("Bandit is required. Install requirements.txt first.")
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", encoding="utf-8", delete=False) as handle:
            handle.write(code)
            tmp_name = handle.name
        result = subprocess.run(
            [executable, "-f", "json", tmp_name],
            capture_output=True, text=True, check=False, timeout=120,
        )
        if result.returncode < 0:
            raise AnalysisInterrupted(f"Bandit was terminated by signal {-result.returncode}")
        if result.returncode not in (0, 1):
            raise SecurityAnalysisError(f"Bandit exited with status {result.returncode}: {result.stderr.strip()}")
        try:
            payload = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            raise SecurityAnalysisError("Bandit did not return valid JSON") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list) or not isinstance(payload.get("errors"), list):
            raise SecurityAnalysisError("Bandit returned an incomplete analysis record")
        if payload["errors"]:
            raise SecurityAnalysisError("Bandit reported scan errors: " + json.dumps(payload["errors"]))
        for issue in payload["results"]:
            cwe = issue.get("issue_cwe") if isinstance(issue, dict) else None
            if not isinstance(cwe, dict) or type(cwe.get("id")) is not int or cwe["id"] < 0:
                raise SecurityAnalysisError("A Bandit finding has no usable CWE identifier")
        if result.returncode == 1 and not payload["results"]:
            raise SecurityAnalysisError("Bandit reported findings without returning them")
        return payload
    except subprocess.TimeoutExpired as exc:
        raise SecurityAnalysisError("Bandit analysis exceeded 120 seconds") from exc
    finally:
        if tmp_name and os.path.exists(tmp_name):
            os.unlink(tmp_name)


def scan_cwes(code: str, require_compile: bool = True) -> tuple[int, list[int]]:
    """Run Bandit and return the number of unique CWE identifiers and their sorted list."""
    payload = run_bandit(code, require_compile=require_compile)
    cwes = {int(issue["issue_cwe"]["id"]) for issue in payload["results"]}
    return len(cwes), sorted(cwes)
