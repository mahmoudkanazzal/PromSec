"""Statement graphs of Python programs.

A program becomes a graph of its statements (nested statements included) with three
edge types, each in both directions: next statement in the same block, parent to
child, and reaching definition to use. Each statement carries features computed from
the code alone: statement type, called functions, keyword arguments with constant
values, and string-construction and data flags (f-strings, concatenation, hard-coded
secrets, ``0.0.0.0`` binds, temporary paths, user input). No analyzer output enters
the features.

Bandit findings are attached to statements only to build training labels and to
score localization, never as model input.

An accepted fix (before, after) labels every statement of ``before`` with an edit
class; the supervised gGAN of PromSec-S learns these classes.
"""

from __future__ import annotations

import ast
import copy
import difflib
import hashlib
import re
import warnings
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field

import torch

EDIT_CLASSES = ("keep", "replace_call", "change_args", "modify_other", "delete", "insert_before")
STMT_TYPES = (
    "Expr", "Assign", "AugAssign", "AnnAssign", "Return", "If", "For", "While", "With", "Try",
    "FunctionDef", "AsyncFunctionDef", "ClassDef", "Import", "ImportFrom", "Raise", "Assert",
    "Pass", "Break", "Continue", "Global", "Delete",
)
BANDIT_TESTS = (
    "B101", "B102", "B103", "B104", "B105", "B106", "B107", "B108", "B110", "B112", "B113",
    "B201", "B301", "B302", "B303", "B304", "B305", "B306", "B307", "B308", "B310", "B311",
    "B312", "B313", "B314", "B320", "B321", "B323", "B324", "B401", "B402", "B403", "B404",
    "B405", "B406", "B407", "B408", "B409", "B410", "B411", "B412", "B413", "B501", "B502",
    "B503", "B504", "B505", "B506", "B507", "B508", "B509", "B601", "B602", "B603", "B604",
    "B605", "B606", "B607", "B608", "B609", "B610", "B611", "B701", "B702", "B703",
)
CALL_BUCKETS = 64
KW_BUCKETS = 32
FLAG_NAMES = (
    "fstring", "str_concat", "percent_format", "format_call", "secret_literal",
    "bind_all", "tmp_path", "user_input", "is_compound", "depth",
)
NUM_RELATIONS = 6  # three edge types, both directions
FEATURE_DIM = len(STMT_TYPES) + 1 + CALL_BUCKETS + KW_BUCKETS + len(FLAG_NAMES)  # code features only
_BODY_FIELDS = ("body", "orelse", "finalbody")
_SECRET_NAME = re.compile(r"pass|pwd|secret|token|api_?key", re.IGNORECASE)


@dataclass
class Statement:
    index: int
    type: str
    lineno: int
    end_lineno: int
    header: str
    calls: tuple[str, ...]
    keywords: tuple[str, ...]
    flags: dict
    parent: int | None
    depth: int
    block: int
    scope: int
    defs: frozenset
    uses: frozenset
    findings: list = field(default_factory=list)


def _dotted(func: ast.AST) -> str:
    parts = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
    elif isinstance(func, ast.Call):
        parts.append(_dotted(func.func) + "()")
    else:
        parts.append("<expr>")
    return ".".join(reversed(parts))


def _shallow_nodes(stmt: ast.stmt) -> Iterator[ast.AST]:
    """Nodes of ``stmt`` excluding nested statement bodies."""
    stack: list[ast.AST] = [stmt]
    while stack:
        node = stack.pop()
        yield node
        for name, value in ast.iter_fields(node):
            if node is stmt and name in _BODY_FIELDS + ("handlers", "cases"):
                continue
            if isinstance(value, list):
                stack.extend(v for v in value if isinstance(v, ast.AST) and not isinstance(v, ast.stmt))
            elif isinstance(value, ast.AST) and not isinstance(value, ast.stmt):
                stack.append(value)


def _header(stmt: ast.stmt) -> str:
    if not any(getattr(stmt, f, None) for f in _BODY_FIELDS + ("handlers", "cases")):
        try:
            return ast.unparse(stmt)
        except Exception:
            return type(stmt).__name__
    shell = copy.deepcopy(stmt)
    for name in _BODY_FIELDS:
        if getattr(shell, name, None):
            setattr(shell, name, [ast.Pass()])
    if getattr(shell, "handlers", None):
        setattr(shell, "handlers", [ast.ExceptHandler(type=None, name=None, body=[ast.Pass()])])  # noqa: B010
    if getattr(shell, "cases", None):
        setattr(shell, "cases", [])  # noqa: B010
    try:
        lines = ast.unparse(shell).splitlines()
    except Exception:
        return type(stmt).__name__
    head = []
    for line in lines:
        head.append(line.strip())
        if line.rstrip().endswith(":"):
            break
    return " ".join(head)


def _flags(stmt: ast.stmt, depth: int) -> dict:
    flags = dict.fromkeys(FLAG_NAMES, 0.0)
    for node in _shallow_nodes(stmt):
        if isinstance(node, ast.JoinedStr):
            flags["fstring"] = 1.0
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            if any(isinstance(side, (ast.JoinedStr,)) or (isinstance(side, ast.Constant) and isinstance(side.value, str))
                   for side in (node.left, node.right)):
                flags["str_concat"] = 1.0
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                flags["percent_format"] = 1.0
        elif isinstance(node, ast.Call):
            name = _dotted(node.func)
            if name.endswith(".format"):
                flags["format_call"] = 1.0
            if name in ("input",) or name.startswith("request."):
                flags["user_input"] = 1.0
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value == "0.0.0.0":
                flags["bind_all"] = 1.0
            if node.value.startswith("/tmp") or node.value.startswith("/var/tmp"):
                flags["tmp_path"] = 1.0
        elif isinstance(node, ast.Attribute) and _dotted(node).startswith(("request.", "sys.argv")):
            flags["user_input"] = 1.0
    if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        value = stmt.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value:
            for target in targets:
                if isinstance(target, (ast.Name, ast.Attribute)) and _SECRET_NAME.search(_dotted(target) if isinstance(target, ast.Attribute) else target.id):
                    flags["secret_literal"] = 1.0
    flags["is_compound"] = 1.0 if any(getattr(stmt, f, None) for f in _BODY_FIELDS) else 0.0
    flags["depth"] = min(depth, 10) / 10.0
    return flags


def _keywords(stmt: ast.stmt) -> tuple[str, ...]:
    out = []
    for node in _shallow_nodes(stmt):
        if isinstance(node, ast.Call):
            name = _dotted(node.func)
            for kw in node.keywords:
                if kw.arg is None:
                    continue
                if isinstance(kw.value, ast.Constant):
                    out.append(f"{name}:{kw.arg}={kw.value.value!r}"[:80])
                else:
                    out.append(f"{name}:{kw.arg}=*")
    return tuple(sorted(set(out)))


def _names(stmt: ast.stmt) -> tuple[frozenset, frozenset]:
    defs: set[str] = set()
    uses: set[str] = set()
    for node in _shallow_nodes(stmt):
        if isinstance(node, ast.Name):
            (defs if isinstance(node.ctx, (ast.Store, ast.Del)) else uses).add(node.id)
        elif isinstance(node, ast.arg):
            defs.add(node.arg)
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        defs.add(stmt.name)
        for arg in stmt.args.args + stmt.args.kwonlyargs if not isinstance(stmt, ast.ClassDef) else []:
            defs.add(arg.arg)
    if isinstance(stmt, (ast.Import, ast.ImportFrom)):
        for alias in stmt.names:
            defs.add((alias.asname or alias.name).split(".")[0])
    return frozenset(defs), frozenset(uses)


def statements(code: str) -> list[Statement]:
    """Every statement of ``code`` in source order, nested statements included."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(code)
    out: list[Statement] = []
    block_counter = [0]

    def visit(stmts: list, parent: int | None, depth: int, scope: int) -> None:
        block_counter[0] += 1
        block = block_counter[0]
        for stmt in stmts:
            if not isinstance(stmt, ast.stmt):
                continue
            defs, uses = _names(stmt)
            calls = tuple(sorted({_dotted(n.func) for n in _shallow_nodes(stmt) if isinstance(n, ast.Call)}))
            item = Statement(
                index=len(out), type=type(stmt).__name__, lineno=stmt.lineno,
                end_lineno=getattr(stmt, "end_lineno", stmt.lineno) or stmt.lineno,
                header=_header(stmt), calls=calls, keywords=_keywords(stmt), flags=_flags(stmt, depth),
                parent=parent, depth=depth, block=block, scope=scope, defs=defs, uses=uses,
            )
            out.append(item)
            inner_scope = item.index if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) else scope
            for name in _BODY_FIELDS:
                child = getattr(stmt, name, None)
                if child:
                    visit(child, item.index, depth + 1, inner_scope)
            for handler in getattr(stmt, "handlers", []) or []:
                visit(handler.body, item.index, depth + 1, inner_scope)
            for case in getattr(stmt, "cases", []) or []:
                visit(case.body, item.index, depth + 1, inner_scope)

    visit(tree.body, None, 0, -1)
    return out


def attach_findings(stmts: list[Statement], findings: list[dict]) -> None:
    """Attach each Bandit finding to the smallest statement whose span contains its line."""
    for finding in findings:
        line = int(finding["line_number"])
        best = None
        for s in stmts:
            if s.lineno <= line <= s.end_lineno:
                span = s.end_lineno - s.lineno
                if best is None or span < best[0] or (span == best[0] and s.depth > stmts[best[1]].depth):
                    best = (span, s.index)
        if best is not None:
            stmts[best[1]].findings.append(finding)


def _bucket(text: str, size: int) -> int:
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:4], "big") % size


def features(stmts: list[Statement]) -> torch.Tensor:
    """Per-statement features computed from the code alone (no analyzer output)."""
    x = torch.zeros((len(stmts), FEATURE_DIM), dtype=torch.float32)
    off_calls = len(STMT_TYPES) + 1
    off_kw = off_calls + CALL_BUCKETS
    off_flags = off_kw + KW_BUCKETS
    for s in stmts:
        row = x[s.index]
        row[STMT_TYPES.index(s.type) if s.type in STMT_TYPES else len(STMT_TYPES)] = 1.0
        for call in s.calls:
            row[off_calls + _bucket(".".join(call.split(".")[-2:]), CALL_BUCKETS)] = 1.0
        for kw in s.keywords:
            row[off_kw + _bucket(kw, KW_BUCKETS)] = 1.0
        for i, name in enumerate(FLAG_NAMES):
            row[off_flags + i] = float(s.flags[name])
    return x


def graph(code: str) -> tuple[list[Statement], torch.Tensor, torch.Tensor, torch.Tensor]:
    """Statements, node features, edge index and edge types of ``code``."""
    stmts = statements(code)
    ei, et = edges(stmts)
    return stmts, features(stmts), ei, et


def node_change_scores(x: torch.Tensor, updated_x: torch.Tensor) -> torch.Tensor:
    """Mean absolute feature change per node."""
    return torch.abs(updated_x - x).reshape(int(x.shape[0]), -1).mean(dim=1)


def edges(stmts: list[Statement]) -> tuple[torch.Tensor, torch.Tensor]:
    """Edge index and relation type: next-in-block, parent-child, reaching definition-use (both directions)."""
    src, dst, rel = [], [], []

    def add(a: int, b: int, r: int) -> None:
        src.extend([a, b])
        dst.extend([b, a])
        rel.extend([2 * r, 2 * r + 1])

    last_in_block: dict[int, int] = {}
    last_def: dict[tuple[int, str], int] = {}
    for s in stmts:
        if s.block in last_in_block:
            add(last_in_block[s.block], s.index, 0)
        last_in_block[s.block] = s.index
        if s.parent is not None:
            add(s.parent, s.index, 1)
        for name in s.uses:
            for scope in (s.scope, -1):
                d = last_def.get((scope, name))
                if d is not None and d != s.index:
                    add(d, s.index, 2)
                    break
        for name in s.defs:
            last_def[(s.scope, name)] = s.index
    if not src:
        return torch.zeros((2, 0), dtype=torch.long), torch.zeros((0,), dtype=torch.long)
    return torch.tensor([src, dst], dtype=torch.long), torch.tensor(rel, dtype=torch.long)


# ------------------------------------------------------------------ labels from accepted fixes


def _call_change(b: Statement, a: Statement) -> str:
    if set(b.calls) != set(a.calls):
        return "replace_call"
    if set(b.keywords) != set(a.keywords):
        return "change_args"
    return "modify_other"


def edit_labels(before: str, after: str) -> tuple[list[Statement], list[str], list[dict]]:
    """Statements of ``before``, one edit class per statement, and the concrete edit per statement.

    Statements are aligned by their normalized headers (difflib, no autojunk).
    """
    sb, sa = statements(before), statements(after)
    labels = ["keep"] * len(sb)
    detail: list[dict] = [{} for _ in sb]
    matcher = difflib.SequenceMatcher(a=[s.header for s in sb], b=[s.header for s in sa], autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag in ("replace", "delete"):
            pairs = list(zip(range(i1, i2), range(j1, j2))) if tag == "replace" else []
            for i, j in pairs:
                labels[i] = _call_change(sb[i], sa[j])
                detail[i] = {
                    "after": sa[j].header[:300],
                    "added_calls": sorted(set(sa[j].calls) - set(sb[i].calls)),
                    "removed_calls": sorted(set(sb[i].calls) - set(sa[j].calls)),
                    "added_keywords": sorted(set(sa[j].keywords) - set(sb[i].keywords)),
                    "removed_keywords": sorted(set(sb[i].keywords) - set(sa[j].keywords)),
                }
            for i in range(i1 + len(pairs), i2):
                labels[i] = "delete"
            extra = list(range(j1 + len(pairs), j2))
        else:
            extra = list(range(j1, j2))
        if extra:
            target = i2 if i2 < len(sb) else len(sb) - 1
            if target >= 0 and labels[target] == "keep":
                labels[target] = "insert_before"
                detail[target] = {"inserted": [sa[j].header[:200] for j in extra][:3]}
    return sb, labels, detail


# ------------------------------------------------------------------ scores


def macro_f1(truth: list[int], pred: list[int], classes: list[int]) -> float:
    scores = []
    for c in classes:
        tp = sum(1 for t, p in zip(truth, pred) if t == c and p == c)
        fp = sum(1 for t, p in zip(truth, pred) if t != c and p == c)
        fn = sum(1 for t, p in zip(truth, pred) if t == c and p != c)
        if tp + fp + fn == 0:
            continue
        scores.append(2 * tp / (2 * tp + fp + fn))
    return sum(scores) / len(scores) if scores else 0.0


# ------------------------------------------------------------------ hint tables and plan rendering


@dataclass
class HintTable:
    """Most frequent concrete edit per (edit class, called API), learned from training pairs only."""

    replacements: dict = field(default_factory=dict)
    keyword_changes: dict = field(default_factory=dict)
    class_by_test: dict = field(default_factory=dict)

    @classmethod
    def fit(cls, examples: list[dict]) -> HintTable:
        repl: dict[str, Counter] = defaultdict(Counter)
        kwc: dict[str, Counter] = defaultdict(Counter)
        by_test: dict[str, Counter] = defaultdict(Counter)
        for ex in examples:
            for s, label, det in zip(ex["statements"], ex["labels"], ex["detail"]):
                for finding in s.findings:
                    by_test[finding.get("test_id", "")][label] += 1
                for call in det.get("removed_calls", []):
                    for new in det.get("added_calls", []):
                        repl[call][new] += 1
                for call in s.calls:
                    for kw in det.get("added_keywords", []):
                        if kw.startswith(call + ":"):
                            kwc[call][kw.split(":", 1)[1]] += 1
        return cls(
            replacements={k: v.most_common(1)[0][0] for k, v in repl.items()},
            keyword_changes={k: v.most_common(1)[0][0] for k, v in kwc.items()},
            class_by_test={k: v.most_common(1)[0][0] for k, v in by_test.items()},
        )

    def to_dict(self) -> dict:
        return {"replacements": self.replacements, "keyword_changes": self.keyword_changes, "class_by_test": self.class_by_test}

    @classmethod
    def from_dict(cls, data: dict) -> HintTable:
        return cls(data.get("replacements", {}), data.get("keyword_changes", {}), data.get("class_by_test", {}))


def _snippet(s: Statement, code_lines: list[str]) -> str:
    text = " ".join(code_lines[s.lineno - 1].split()) if 0 < s.lineno <= len(code_lines) else s.header
    return text[:120]


def render_plan(code: str, stmts: list[Statement], labels: list[str], *, hints: HintTable | None = None,
                detail: list[dict] | None = None) -> str:
    """Plain-language edit instructions, one per statement to change.

    ``detail`` (the concrete edit of an accepted fix) gives exact suggestions;
    ``hints`` (tables mined from accepted fixes) give suggestions for predicted edits.
    """
    lines = code.splitlines()
    out = []
    for s, label in zip(stmts, labels):
        if label == "keep":
            continue
        det = (detail[s.index] if detail else {}) or {}
        where = f"Line {s.lineno} (`{_snippet(s, lines)}`)"
        if label == "replace_call":
            new = det.get("added_calls") or ([hints.replacements[c] for c in s.calls if hints and c in hints.replacements][:1])
            text = "replace the risky call with a safer API" + (f", for example `{new[0]}`" if new else "")
        elif label == "change_args":
            kws = det.get("added_keywords") or [f"{c}:{hints.keyword_changes[c]}" for c in s.calls if hints and c in hints.keyword_changes][:1]
            text = "keep the call but change its arguments" + (
                f", for example `{kws[0].split(':', 1)[1]}`" if kws else "")
        elif label == "modify_other":
            text = "rewrite this statement to remove the weakness"
        elif label == "delete":
            text = "remove this statement"
        else:
            text = "insert a validation or safe setup step before this statement"
        out.append(f"- {where}: {text}.")
    if not out:
        return "No statement needs to change."
    return "\n".join(out) + "\n- Keep every other statement unchanged."
