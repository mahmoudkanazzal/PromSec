"""Training data for the gGANs: fix-and-rescan chains on training programs.

Stages, run in order by ``run`` and resumable per item:

pool   the training programs: a scenario-balanced subset of ``data/training`` plus
       programs the LLM synthesizes for common Bandit weakness types (``SCENARIOS``),
       each kept only if Bandit reports the intended finding.
fix    per program and sample: the LLM fixes the code given the Bandit report, and
       Bandit re-scans it, for up to ``rounds`` rounds. A step is accepted only if it
       compiles, keeps the program's public functions and entry points, reduces the
       findings and adds no new finding type.

``promsec states`` then turns every program version of the chains into a training
state with Bandit labels (``promsec.states``). The 100 evaluation programs are never read.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evaluation.functional_similarity import (
    api_preserved,
    entrypoints,
    extract_behavioral_contract,
    public_api,
    score_candidate_functionality,
)

from .config import resolve_path
from .io import atomic_write_json, atomic_write_text, sha256_text
from .judge import _completion
from .llm import LLMClient, client_from_config
from .metrics import validate_python_source
from .runner import _generate_valid_python
from .security import AnalysisInterrupted, run_bandit

# --------------------------------------------------------------------------- lifecycles

ITEM_TRANSITIONS = {
    "pending": {"running"},
    "running": {"ok", "failed", "rejected"},
    "failed": {"running"},
    "ok": set(),
    "rejected": set(),
}
STAGE_TRANSITIONS = {
    "pending": {"running"},
    "running": {"running", "complete"},
    "complete": set(),
}
STAGES = ("pool", "fix")
MAX_RETRIES = 2


class TransitionError(RuntimeError):
    """A lifecycle transition that the transition table does not allow."""


def transition(table: dict, current: str, new: str) -> str:
    if new not in table.get(current, set()):
        raise TransitionError(f"Invalid transition {current} -> {new}")
    return new


# --------------------------------------------------------------------------- synthesized scenarios

SCENARIOS = (
    ("cwe78_os_system", "B605", "runs a shell command built from user-supplied input with os.system"),
    ("cwe78_shell_true", "B602", "runs a command built from user-supplied input with subprocess and shell=True"),
    ("cwe89_sql_format", "B608", "builds an SQL query by string formatting or concatenation with user-supplied values and executes it with sqlite3"),
    ("cwe20_yaml_load", "B506", "parses user-supplied YAML with yaml.load without a safe loader"),
    ("cwe259_password_literal", "B105", "stores a hard-coded password in a variable and compares user input against it"),
    ("cwe259_password_argument", "B106", "passes a hard-coded password as a keyword argument to a connection or login function"),
    ("cwe703_assert_check", "B101", "uses assert statements to check user input or permissions"),
    ("cwe327_weak_hash", "B324", "hashes passwords or tokens with hashlib.md5 or hashlib.sha1"),
    ("cwe502_pickle_loads", "B301", "deserializes user-supplied data with pickle.loads"),
    ("cwe400_no_timeout", "B113", "calls an external HTTP API with the requests library without a timeout"),
    ("cwe377_tmp_path", "B108", "writes temporary files to a hard-coded /tmp path"),
    ("cwe605_bind_all", "B104", "starts its server bound to host 0.0.0.0"),
)
CONTEXTS = (
    "a Flask web service that manages user profiles",
    "a command-line backup utility",
    "a Flask endpoint that uploads and processes files",
    "an inventory management module for a small shop",
    "a log analysis script run by administrators",
    "a Flask API for a library book catalog",
    "a configuration loader for a microservice",
    "a script that synchronizes records with a remote server",
    "a Flask login and session service",
    "a job scheduler that runs maintenance tasks",
)


def synth_prompt(context: str, behavior: str) -> str:
    return (
        f"Write a realistic, self-contained Python program of 30 to 100 lines: {context}. "
        f"As part of its normal behavior, the program {behavior}. "
        "Write it the way a developer in a hurry would, without security hardening. "
        "Use functions with clear names; you may use Flask, sqlite3, requests, yaml, subprocess, hashlib, "
        "pickle and the standard library. Do not add comments about security."
    )


def fix_prompt(code: str, findings: list[dict]) -> str:
    """Repair request with the Bandit report."""
    lines = code.splitlines()
    report = "\n".join(
        f"- Line {f['line_number']}: {f['test_id']} (CWE-{f['issue_cwe']['id']}) {f['issue_text'].strip()} "
        f"Code: `{' '.join(lines[f['line_number'] - 1].split())[:160] if 0 < f['line_number'] <= len(lines) else ''}`"
        for f in findings
    ) or "- No findings."
    text = (
        "You are a security engineer. Fix the security weaknesses that the static analysis report lists in the "
        "Python program below. Keep the program's functionality, its public functions and their signatures, its "
        "routes and its entry points unchanged. Make the smallest changes each fix needs, and do not remove "
        "functionality to silence a finding.\n\n"
        "Program:\n" + code + "\n\nStatic analysis report:\n" + report
    )
    return text + "\n\nReturn the complete fixed program."


# --------------------------------------------------------------------------- helpers


class Progress:
    """One status line per finished item and a status file for the current stage."""

    def __init__(self, run_dir: Path, stage: str, total: int):
        self.run_dir, self.stage, self.total = run_dir, stage, total
        self.done = self.ok = self.failed = self.rejected = 0
        self.started = time.monotonic()
        self.lock = threading.Lock()

    def item(self, status: str, text: str) -> None:
        with self.lock:
            self.done += 1
            if status == "ok":
                self.ok += 1
            elif status == "rejected":
                self.rejected += 1
            else:
                self.failed += 1
            elapsed = max(time.monotonic() - self.started, 1e-6)
            rate = self.done / elapsed
            eta = (self.total - self.done) / rate if rate > 0 else 0.0
            line = (
                f"[{self.stage} {self.done}/{self.total}] {100 * self.done / max(self.total, 1):.1f}% | ok={self.ok} "
                f"rejected={self.rejected} fail={self.failed} | {rate * 60:.1f}/min | ETA {int(eta // 3600):02d}:"
                f"{int(eta % 3600 // 60):02d}"
            )
            print(f"{line} | {text}", flush=True)
            atomic_write_text(self.run_dir / "status.txt", line + "\n")


def _config_hash(cfg: dict, stage: str) -> str:
    """Identity of the settings that change a stage's records (not counts or parallelism)."""
    t = cfg["training_data"]
    material: dict = {"stage": stage, "model": os.environ.get(cfg["llm"]["model_env"], ""),
                      "temperature": t["temperature"], "prompts": sha256_text(synth_prompt("", "") + fix_prompt("", []))}
    if stage == "fix":
        material.update(judge_model=os.environ.get(cfg["judge"]["model_env"], ""), laaj_min=t["laaj_min"],
                        rounds=t["rounds"])
    return sha256_text(json.dumps(material, sort_keys=True))[:16]


def _run_dir(cfg: dict) -> Path:
    path = resolve_path(cfg, cfg["training_data"]["run_dir"])
    path.mkdir(parents=True, exist_ok=True)
    return path


def _llm_client(cfg: dict) -> LLMClient:
    settings = cfg["llm"]
    model = os.environ.get(settings["model_env"])
    if not model:
        raise RuntimeError(f"Environment variable {settings['model_env']} is not set")
    return LLMClient(
        model=model, api_key_env=settings.get("api_key_env", "OPENAI_API_KEY"),
        base_url=os.environ.get(settings.get("base_url_env", "")) or None,
        temperature=float(cfg["training_data"]["temperature"]), max_retries=int(settings.get("max_retries", 4)),
        cache_path=_run_dir(cfg) / "cache" / "training_data.sqlite", call_log=_run_dir(cfg) / "calls.jsonl",
    )


def _findings(code: str, require_compile: bool) -> list[dict]:
    payload = run_bandit(code, require_compile=require_compile)
    return sorted(payload["results"], key=lambda f: (f["line_number"], f["test_id"]))


def _scenario_group(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"_\d+$", "", stem)
    return "train:" + re.sub(r"_(copilot|codex|davinci|gpt[^_]*)$", "", stem)


def _load_item(path: Path, config_hash: str) -> dict | None:
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if record.get("config_hash") != config_hash:
        return None
    return record


def _run_items(cfg: dict, stage: str, items: list[dict], work, describe) -> list[dict]:
    """Run ``work(item) -> record`` for each item; skip finished records, retry failed ones up to MAX_RETRIES."""
    run_dir = _run_dir(cfg)
    out_dir = run_dir / stage
    out_dir.mkdir(parents=True, exist_ok=True)
    config_hash = _config_hash(cfg, stage)
    todo, done = [], []
    for item in items:
        previous = _load_item(out_dir / f"{item['id']}.json", config_hash)
        if previous and (previous["status"] in ("ok", "rejected") or previous.get("retries", 0) >= MAX_RETRIES):
            done.append(previous)
        else:
            todo.append((item, previous))
    progress = Progress(run_dir, stage, len(todo))
    print(f"== {stage}: {len(items)} items, {len(done)} already finished, {len(todo)} to run", flush=True)

    def process(pair) -> dict:
        item, previous = pair
        status = transition(ITEM_TRANSITIONS, previous["status"] if previous else "pending", "running")
        retries = (previous.get("retries", 0) + 1) if previous and previous["status"] == "failed" else 0
        try:
            record = work(item)
            status = transition(ITEM_TRANSITIONS, status, record.pop("status", "ok"))
        except AnalysisInterrupted:
            raise
        except Exception as exc:
            record = {"error": f"{type(exc).__name__}: {exc}"[:1000]}
            status = transition(ITEM_TRANSITIONS, status, "failed")
        record.update(id=item["id"], status=status, retries=retries, config_hash=config_hash,
                      timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        atomic_write_json(out_dir / f"{item['id']}.json", record)
        progress.item(status, describe(item, record))
        return record

    with ThreadPoolExecutor(max_workers=max(1, int(cfg["training_data"]["parallel"]))) as pool:
        done.extend(pool.map(process, todo))
    return done


# --------------------------------------------------------------------------- stage: pool


def pool_items(cfg: dict) -> list[dict]:
    t = cfg["training_data"]
    items = []
    training_dir = resolve_path(cfg, cfg["data"]["training_dir"])
    groups: dict[str, list[Path]] = {}
    for path in sorted(training_dir.glob("*.py"), key=lambda p: hashlib.sha256(p.name.encode()).hexdigest()):
        groups.setdefault(_scenario_group(path.name), []).append(path)
    chosen: list[Path] = []
    while len(chosen) < int(t["training_programs"]) and any(groups.values()):
        for key in sorted(groups):
            if groups[key] and len(chosen) < int(t["training_programs"]):
                chosen.append(groups[key].pop(0))
    for path in chosen:
        items.append({"id": "train_" + path.stem[-80:].replace("-", "_") + "_" + hashlib.sha256(path.name.encode()).hexdigest()[:6],
                      "source": "training", "file": str(Path(cfg["data"]["training_dir"]) / path.name),
                      "group": _scenario_group(path.name)})
    scenarios = [s for s in SCENARIOS if not t.get("scenarios") or s[0] in t["scenarios"]]
    for key, test_id, behavior in scenarios:
        for ctx in range(int(t["synth_per_scenario"])):
            items.append({"id": f"synth_{key}_c{ctx}", "source": "synth", "scenario": key, "expected_test": test_id,
                          "behavior": behavior, "context": CONTEXTS[ctx % len(CONTEXTS)], "group": f"synth:c{ctx % len(CONTEXTS)}"})
    return items


def _pool_work(cfg: dict, llm: LLMClient):
    run_dir = _run_dir(cfg)

    def work(item: dict) -> dict:
        code_path = run_dir / "pool" / "code" / f"{item['id']}.py"
        if item["source"] == "training":
            code = resolve_path(cfg, item["file"]).read_text(encoding="utf-8")
            try:
                validate_python_source(code, require_compile=True)
            except Exception as exc:
                return {"status": "rejected", "reason": f"does not compile: {exc}"[:300], **item}
        else:
            synthesized: str | None = None
            reason = ""
            for attempt in range(2):
                candidate, _ = _generate_valid_python(
                    synth_prompt(item["context"], item["behavior"]), llm, f"{item['id']}:a{attempt}", 3, purpose="training_data_synth")
                tests = {f["test_id"] for f in _findings(candidate, True)}
                if item["expected_test"] in tests:
                    synthesized = candidate
                    break
                reason = f"expected {item['expected_test']}, Bandit found {sorted(tests)}"
            if synthesized is None:
                return {"status": "rejected", "reason": reason, **item}
            code = synthesized
        findings = _findings(code, True)
        if not findings:
            return {"status": "rejected", "reason": "no Bandit findings", **item}
        atomic_write_text(code_path, code)
        return {**item, "code_path": str(code_path.relative_to(run_dir)), "code_hash": sha256_text(code),
                "findings": [f["test_id"] for f in findings]}

    return work


# --------------------------------------------------------------------------- stage: fix


def _judge(cfg: dict, judge_llm: LLMClient, original: str, candidate: str) -> dict:
    contract = extract_behavioral_contract(original, _completion(judge_llm, "contract"))
    report = score_candidate_functionality(contract, candidate, _completion(judge_llm, "primary"))
    return {"laaj": report.laaj_score, "gated_laaj": report.gated_score, "api_preserved": report.api_preserved,
            "entrypoints_ok": report.entrypoints_ok}


def _interface_ok(original: str, candidate: str) -> bool:
    if not api_preserved(public_api(original), candidate):
        return False
    return all(re.search(pattern, candidate) for pattern in entrypoints(original))


def _fix_work(cfg: dict, llm: LLMClient, judge_llm: LLMClient):
    run_dir = _run_dir(cfg)
    rounds = int(cfg["training_data"]["rounds"])
    laaj_min = float(cfg["training_data"]["laaj_min"])

    def work(item: dict) -> dict:
        original = (run_dir / item["code_path"]).read_text(encoding="utf-8")
        code = original
        steps = []
        for r in range(1, rounds + 1):
            before = _findings(code, False)
            if not before:
                break
            candidate, repairs = _generate_valid_python(
                fix_prompt(code, before), llm, f"{item['program']}:s{item['sample']}:r{r}:{sha256_text(code)[:12]}", 3,
                purpose="training_data_fix")
            after = _findings(candidate, True)
            reason = None
            if not _interface_ok(original, candidate):
                reason = "interface changed"
            elif len(after) >= len(before):
                reason = f"findings not reduced ({len(before)} -> {len(after)})"
            elif not {f["test_id"] for f in after} <= {f["test_id"] for f in before}:
                reason = "new finding type"
            path = run_dir / "fix" / "code" / f"{item['id']}_r{r}.py"
            atomic_write_text(path, candidate)
            steps.append({"round": r, "before_hash": sha256_text(code), "after_path": str(path.relative_to(run_dir)),
                          "findings_before": [f["test_id"] for f in before], "findings_after": [f["test_id"] for f in after],
                          "accepted": reason is None, "reason": reason, "syntax_repairs": repairs})
            if reason is not None:
                break
            code = candidate
        accepted = [s for s in steps if s["accepted"]]
        clean = bool(accepted) and not _findings(code, True)
        record = {"program": item["program"], "sample": item["sample"], "group": item["group"], "source": item["source"],
                  "steps": steps, "accepted_steps": len(accepted), "clean": clean, "verified": False}
        if clean:
            final_path = run_dir / "fix" / "code" / f"{item['id']}_final.py"
            atomic_write_text(final_path, code)
            record["final_path"] = str(final_path.relative_to(run_dir))
            record.update(_judge(cfg, judge_llm, original, code))
            record["verified"] = record["gated_laaj"] >= laaj_min
        return record

    return work


def _records(directory: Path) -> list[dict]:
    out = []
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            try:
                out.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                continue
    return out


def _stage_state(run_dir: Path) -> dict:
    path = run_dir / "stages.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return dict.fromkeys(STAGES, "pending")


def _set_stage(run_dir: Path, states: dict, stage: str, new: str) -> None:
    states[stage] = transition(STAGE_TRANSITIONS, states[stage], new)
    atomic_write_json(run_dir / "stages.json", states)


def _verify(stage: str, records: list[dict], items: list[dict]) -> None:
    """A stage completes only when every item has a terminal record."""
    finished = {r["id"] for r in records if r["status"] in ("ok", "rejected") or r.get("retries", 0) >= MAX_RETRIES}
    missing = [i["id"] for i in items if i["id"] not in finished]
    if missing:
        raise RuntimeError(f"{stage}: {len(missing)} items without a terminal record, e.g. {missing[:3]}")


def run(cfg: dict, *, transport=None) -> dict:
    """Run every pending stage; resumable. ``transport`` replaces the endpoint only in tests."""
    run_dir = _run_dir(cfg)
    states = _stage_state(run_dir)
    llm = _llm_client(cfg)
    judge_llm = client_from_config(cfg, "judge", call_log=run_dir / "calls.jsonl")
    if transport is not None:
        llm.transport = transport
        judge_llm.transport = transport
    for stage in STAGES:
        if states[stage] == "complete":
            continue
        _set_stage(run_dir, states, stage, "running")
        if stage == "pool":
            items = pool_items(cfg)
            _verify(stage, _run_items(cfg, stage, items, _pool_work(cfg, llm), _describe_pool), items)
        else:
            pool = [r for r in _records(run_dir / "pool") if r["status"] == "ok"]
            items = [{"id": f"{p['id']}__s{k}", "program": p["id"], "sample": k, "group": p["group"],
                      "source": p["source"], "code_path": p["code_path"]}
                     for p in pool for k in range(int(cfg["training_data"]["samples"]))]
            _verify(stage, _run_items(cfg, stage, items, _fix_work(cfg, llm, judge_llm), _describe_fix), items)
        _set_stage(run_dir, states, stage, "complete")
    return states


def run_dir(cfg: dict) -> Path:
    return _run_dir(cfg)


def status(cfg: dict) -> str:
    """Stage states and item counts of the training-data run."""
    directory = _run_dir(cfg)
    states = _stage_state(directory)
    lines = []
    for stage in STAGES:
        records = _records(directory / stage)
        counts: dict[str, int] = {}
        for r in records:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        lines.append(f"{stage:<6} {states[stage]:<9} " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return "\n".join(lines)


def _describe_pool(item: dict, record: dict) -> str:
    if record["status"] != "ok":
        return f"{item['id']}: {record['status']} {record.get('reason') or record.get('error', '')}"[:200]
    return f"{item['id']}: findings {','.join(record['findings'])}"


def _describe_fix(item: dict, record: dict) -> str:
    if record["status"] != "ok":
        return f"{item['id']}: {record['status']} {record.get('error', '')}"[:200]
    laaj = f" gated LAAJ {record['gated_laaj']:.2f}" if "gated_laaj" in record else ""
    last = record["steps"][-1]["reason"] if record["steps"] and record["steps"][-1]["reason"] else ""
    return (f"{item['id']}: steps {record['accepted_steps']}/{len(record['steps'])} clean={record['clean']}{laaj} "
            f"verified={record['verified']} {last}")
