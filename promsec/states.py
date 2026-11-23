"""gGAN training states: program versions with Bandit labels per statement.

A state is one version of a training program: an original or an LLM-revised version
from a fix-and-rescan chain (``promsec.trainingdata``). Bandit labels each state's
statements once, offline:

* ``loc``: 1 if the statement holds a Bandit finding;
* ``cwe_count``: number of distinct CWE IDs in the state, k(c) in the paper;
* ``fix``: if the chain accepted a fix of this state, the edit class of every statement.

The states are stored in ``training_data.states_dir`` (``data/states`` in this
repository) as ``<id>.py``, ``<id>.next.py`` (the accepted fix, if any) and
``<id>.json`` (labels and provenance). The labels are used only for training and
evaluation; neither gGAN sees analyzer output as input.
"""

from __future__ import annotations

import hashlib
import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import torch

from . import graph as g
from .config import resolve_path
from .io import atomic_write_json, atomic_write_text, sha256_text
from .security import run_bandit


def states_dir(cfg: dict) -> Path:
    return resolve_path(cfg, cfg["training_data"]["states_dir"])


def _records(directory: Path) -> list[dict]:
    out = []
    if directory.is_dir():
        for p in sorted(directory.glob("*.json")):
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                continue
    return out


def collect_states(run_dir: Path) -> list[dict]:
    """Every distinct program version of a finished training-data run, with its next accepted fix if any."""
    if not (run_dir / "pool").is_dir() or not (run_dir / "fix").is_dir():
        raise FileNotFoundError(f"Not a finished training-data run: {run_dir}")
    pool = {r["id"]: r for r in _records(run_dir / "pool") if r.get("status") == "ok"}
    states: dict[str, dict] = {}

    def add(code: str, program: dict, round_: int, next_code: str | None) -> None:
        key = sha256_text(code)
        state = states.get(key)
        if state is None:
            state = {"id": key[:20], "code": code, "program": program["id"], "group": program["group"],
                     "scenario": program.get("scenario") or program["group"], "source": program["source"],
                     "round": round_, "next_code": None}
            states[key] = state
        if state["next_code"] is None and next_code is not None:
            state["next_code"] = next_code

    for chain in sorted((r for r in _records(run_dir / "fix") if r.get("status") == "ok"), key=lambda r: r["id"]):
        program = pool.get(chain["program"])
        if program is None:
            continue
        code = (run_dir / program["code_path"]).read_text(encoding="utf-8")
        for step in chain["steps"]:
            after = (run_dir / step["after_path"]).read_text(encoding="utf-8")
            add(code, program, step["round"] - 1, after if step["accepted"] else None)
            add(after, program, step["round"], None)
            if not step["accepted"]:
                break
            code = after
    for program in pool.values():
        add((run_dir / program["code_path"]).read_text(encoding="utf-8"), program, 0, None)
    return sorted(states.values(), key=lambda s: s["id"])


def label_states(cfg: dict, states: list[dict]) -> list[dict]:
    """Write every state with its Bandit labels to the states directory; skip states already labeled."""
    out_dir = states_dir(cfg)
    out_dir.mkdir(parents=True, exist_ok=True)

    def one(state: dict) -> dict | None:
        path = out_dir / f"{state['id']}.json"
        next_hash = sha256_text(state["next_code"]) if state["next_code"] else None
        if path.is_file():
            cached = json.loads(path.read_text(encoding="utf-8"))
            if cached.get("next_hash") == next_hash and "cwe_count" in cached:
                return cached if cached.get("ok") else None
        record = {k: v for k, v in state.items() if k not in ("code", "next_code")}
        record["next_hash"] = next_hash
        try:
            stmts = g.statements(state["code"])
            findings = run_bandit(state["code"], require_compile=False)["results"]
            g.attach_findings(stmts, findings)
            record["loc"] = [1 if s.findings else 0 for s in stmts]
            record["tests"] = sorted({f["test_id"] for f in findings})
            record["cwe_count"] = len({int(f["issue_cwe"]["id"]) for f in findings if f.get("issue_cwe")})
            if state["next_code"]:
                _, labels, _ = g.edit_labels(state["code"], state["next_code"])
                record["fix"] = labels
            record["ok"] = True
        except SyntaxError as exc:
            record.update(ok=False, error=str(exc)[:200])
        atomic_write_text(out_dir / f"{state['id']}.py", state["code"])
        if state["next_code"]:
            atomic_write_text(out_dir / f"{state['id']}.next.py", state["next_code"])
        atomic_write_json(path, record)
        return record if record.get("ok") else None

    workers = max(1, int(cfg["training_data"].get("cpu_workers", 8)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return [r for r in pool.map(one, states) if r is not None]


def load_states(cfg: dict) -> list[dict]:
    """Labeled states from the states directory, in a fixed order (by state id)."""
    directory = states_dir(cfg)
    records = [r for r in _records(directory) if r.get("ok")]
    if not records:
        raise FileNotFoundError(f"No labeled training states in {directory}")
    return records


def state_code(cfg: dict, record: dict) -> str:
    return (states_dir(cfg) / f"{record['id']}.py").read_text(encoding="utf-8")


def tensors(cfg: dict, record: dict):
    """Node features, edges, localization labels and fix labels of one state."""
    _, x, ei, et = g.graph(state_code(cfg, record))
    loc = torch.tensor(record["loc"], dtype=torch.float32)
    if "fix" in record:
        fix = torch.tensor([g.EDIT_CLASSES.index(lb) for lb in record["fix"]], dtype=torch.long)
    else:
        fix = torch.full((x.shape[0],), -100, dtype=torch.long)
    return x, ei, et, loc, fix


def split_groups(groups: list[str], fraction: float, seed: int) -> set[str]:
    """Held-out program groups: ``fraction`` of the training-program groups and of the synthesized groups."""
    held = set()
    for prefix in ("train:", "synth:"):
        family = sorted({grp for grp in groups if grp.startswith(prefix)},
                        key=lambda grp: hashlib.sha256(f"{seed}:{grp}".encode()).hexdigest())
        if len(family) >= 2:
            held.update(family[: max(1, math.ceil(fraction * len(family)))])
    return held


def loc_scores(truth: list[int], pred: list[int]) -> dict:
    """Statement-level precision, recall and F1 of a selection against Bandit's flagged statements."""
    tp = sum(1 for t, p in zip(truth, pred) if t and p)
    fp = sum(1 for t, p in zip(truth, pred) if not t and p)
    fn = sum(1 for t, p in zip(truth, pred) if t and not p)

    def r(v):
        return None if v is None else round(v, 4)

    return {"precision": r(tp / (tp + fp) if tp + fp else None), "recall": r(tp / (tp + fn) if tp + fn else None),
            "f1": r(2 * tp / (2 * tp + fp + fn) if tp + fp + fn else None), "flagged": tp + fn, "predicted": tp + fp}


def bandit_nodes(code: str) -> list[int]:
    """Statements of ``code`` that hold a Bandit finding: for scoring the gGAN's selection only."""
    findings = run_bandit(code, require_compile=False)["results"]
    stmts = g.statements(code)
    g.attach_findings(stmts, findings)
    return [s.index for s in stmts if s.findings]
