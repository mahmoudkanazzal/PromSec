"""Core utilities for the PromSec implementation package."""

from __future__ import annotations

import ast
import hashlib
import math
import tokenize
import warnings
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Sequence

import networkx as nx
import torch

from promsec.security import run_bandit

if TYPE_CHECKING:
    from torch_geometric.data import Data

FEATURE_NAMES = (
    "contains_function",
    "contains_loop",
    "contains_if",
    "contains_comment",
)


def load_original_code(file_path: str | Path) -> str:
    """Read a Python source file as UTF-8 text."""
    return Path(file_path).read_text(encoding="utf-8")


def _comment_lines(source: str | None) -> set[int]:
    if not source:
        return set()
    lines: set[int] = set()
    try:
        for tok in tokenize.generate_tokens(StringIO(source).readline):
            if tok.type == tokenize.COMMENT:
                lines.add(tok.start[0])
    except (tokenize.TokenError, IndentationError):
        return lines
    return lines


def _is_string_expression(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(getattr(node, "value", None), ast.Constant)
        and isinstance(node.value.value, str)
    )


def get_node_features(node: ast.AST, comment_lines: set[int] | None = None) -> list[int]:
    """Return the four binary structural features used by the graph pipeline."""
    descendants = list(ast.walk(node))
    contains_function = any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in descendants)
    contains_loop = any(isinstance(n, (ast.For, ast.AsyncFor, ast.While)) for n in descendants)
    contains_if = any(isinstance(n, ast.If) for n in descendants)

    contains_comment = any(_is_string_expression(n) for n in descendants)
    if comment_lines:
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", start)
        if start is not None and end is not None:
            contains_comment = contains_comment or any(start <= line <= end for line in comment_lines)

    return [
        int(contains_function),
        int(contains_loop),
        int(contains_if),
        int(contains_comment),
    ]


def _add_cfg_node(graph: nx.DiGraph, stmt: ast.stmt, source: str, comments: set[int]) -> int:
    node_id = graph.number_of_nodes()
    features = get_node_features(stmt, comments)
    attrs = dict(zip(FEATURE_NAMES, features))
    attrs.update(
        ast_node=stmt,
        ast_type=type(stmt).__name__,
        lineno=getattr(stmt, "lineno", None),
        end_lineno=getattr(stmt, "end_lineno", getattr(stmt, "lineno", None)),
        code=ast.get_source_segment(source, stmt) or "",
        features=features,
    )
    graph.add_node(node_id, **attrs)
    return node_id


def _unique_nodes(nodes: Iterable[int]) -> list[int]:
    return list(dict.fromkeys(nodes))


def _build_cfg_block(
    statements: Sequence[ast.stmt],
    graph: nx.DiGraph,
    incoming: Sequence[int],
    source: str,
    comments: set[int],
) -> list[int]:
    exits = list(incoming)

    for stmt in statements:
        current = _add_cfg_node(graph, stmt, source, comments)
        for predecessor in exits:
            graph.add_edge(predecessor, current)

        if isinstance(stmt, ast.If):
            body_exits = _build_cfg_block(stmt.body, graph, [current], source, comments) if stmt.body else [current]
            else_exits = _build_cfg_block(stmt.orelse, graph, [current], source, comments) if stmt.orelse else [current]
            exits = _unique_nodes(body_exits + else_exits)
            continue

        if isinstance(stmt, (ast.For, ast.AsyncFor, ast.While)):
            body_exits = _build_cfg_block(stmt.body, graph, [current], source, comments) if stmt.body else [current]
            for body_exit in body_exits:
                if body_exit != current:
                    graph.add_edge(body_exit, current, edge_type="loop_back")
            if stmt.orelse:
                exits = _build_cfg_block(stmt.orelse, graph, [current], source, comments)
            else:
                exits = [current]
            continue

        if isinstance(stmt, (ast.With, ast.AsyncWith)):
            exits = _build_cfg_block(stmt.body, graph, [current], source, comments) if stmt.body else [current]
            continue

        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if stmt.body:
                nested_exits = _build_cfg_block(stmt.body, graph, [current], source, comments)
                exits = _unique_nodes([current] + nested_exits)
            else:
                exits = [current]
            continue

        if isinstance(stmt, ast.Try):
            branch_exits = _build_cfg_block(stmt.body, graph, [current], source, comments) if stmt.body else [current]
            for handler in stmt.handlers:
                branch_exits += _build_cfg_block(handler.body, graph, [current], source, comments)
            if stmt.orelse:
                branch_exits = _build_cfg_block(stmt.orelse, graph, _unique_nodes(branch_exits), source, comments)
            if stmt.finalbody:
                branch_exits = _build_cfg_block(stmt.finalbody, graph, _unique_nodes(branch_exits), source, comments)
            exits = _unique_nodes(branch_exits)
            continue

        exits = [current]

    return exits


def build_cfg_from_ast(node: ast.AST | list[ast.stmt], graph: nx.DiGraph | None = None, prev_node: int | None = None, source: str | None = None) -> int | None:
    """Populate a statement-level directed control-flow graph from an AST root."""
    if graph is None:
        graph = nx.DiGraph()
    if source is None:
        source = ""
    comments = _comment_lines(source)
    incoming = [] if prev_node is None else [prev_node]

    if isinstance(node, ast.Module):
        exits = _build_cfg_block(node.body, graph, incoming, source, comments)
    elif isinstance(node, list):
        exits = _build_cfg_block(node, graph, incoming, source, comments)
    elif isinstance(node, ast.stmt):
        exits = _build_cfg_block([node], graph, incoming, source, comments)
    else:
        raise TypeError(f"Unsupported AST root type: {type(node).__name__}")

    return exits[-1] if exits else prev_node


def generate_cfg_from_source(source: str, filename: str = "<source>") -> nx.DiGraph:
    """Parse Python source text and return its statement-level directed graph."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(source, filename=filename)
    graph = nx.DiGraph()
    build_cfg_from_ast(tree, graph, source=source)
    return graph


def generate_cfg_from_code(file_path: str | Path) -> nx.DiGraph:
    """Parse a Python file and return its statement-level directed graph."""
    source = Path(file_path).read_text(encoding="utf-8")
    return generate_cfg_from_source(source, filename=str(file_path))


def get_cfg_node_features(graph: nx.DiGraph, node: int) -> list[int]:
    """Read the four stored binary features for one graph node."""
    data = graph.nodes[node]
    return [int(bool(data.get(name, 0))) for name in FEATURE_NAMES]


STATEMENT_TYPES = (
    "Assign", "AugAssign", "AnnAssign", "Expr", "Return", "If", "For", "While", "With", "Try",
    "FunctionDef", "ClassDef", "Import", "ImportFrom", "Raise", "Assert", "Delete", "Global",
    "Pass", "Break", "Continue",
)
EXPRESSION_TYPES = (
    "Call", "Attribute", "Subscript", "Name", "Constant", "JoinedStr", "FormattedValue", "BinOp",
    "Compare", "BoolOp", "Dict", "List", "Tuple", "Lambda", "keyword", "Starred", "IfExp",
    "ListComp", "Await", "UnaryOp",
)
STRING_OPERATORS = ("Add", "Mod")
IDENTIFIER_BUCKETS = 64
NODE_FEATURE_DIM = len(FEATURE_NAMES) + len(STATEMENT_TYPES) + len(EXPRESSION_TYPES) + len(STRING_OPERATORS) + IDENTIFIER_BUCKETS


def _statement_header_nodes(stmt: ast.stmt) -> list[ast.AST]:
    """AST nodes that belong to ``stmt`` itself, excluding nested statements and handlers."""
    collected: list[ast.AST] = []
    stack: list[ast.AST] = [stmt]
    while stack:
        node = stack.pop()
        collected.append(node)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.stmt, ast.excepthandler)):
                continue
            stack.append(child)
    return collected


def _dotted_name(node: ast.AST) -> str:
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _identifier_bucket(token: str) -> int:
    return int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % IDENTIFIER_BUCKETS


def statement_feature_vector(stmt: ast.stmt) -> list[float]:
    """Statement-level node features."""
    nodes = _statement_header_nodes(stmt)
    statement = [float(type(stmt).__name__ == name) for name in STATEMENT_TYPES]
    counts: dict[str, int] = {}
    for node in nodes:
        counts[type(node).__name__] = counts.get(type(node).__name__, 0) + 1
    expressions = [min(math.log1p(counts.get(name, 0)) / 2.0, 1.0) for name in EXPRESSION_TYPES]
    operators = [
        float(any(isinstance(node, ast.BinOp) and type(node.op).__name__ == name for node in nodes))
        for name in STRING_OPERATORS
    ]
    identifiers = [0.0] * IDENTIFIER_BUCKETS
    for node in nodes:
        tokens = []
        if isinstance(node, ast.Call):
            tokens.append("call:" + _dotted_name(node.func))
        elif isinstance(node, ast.Attribute):
            tokens.append("attr:" + node.attr)
        elif isinstance(node, ast.Name):
            tokens.append("name:" + node.id.lower())
        elif isinstance(node, ast.keyword) and node.arg:
            tokens.append("kw:" + node.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            tokens.extend("import:" + alias.name for alias in node.names)
        for token in tokens:
            identifiers[_identifier_bucket(token)] = 1.0
    return statement + expressions + operators + identifiers


def node_feature_vector(graph: nx.DiGraph, node: int) -> list[float]:
    """Full GNN input row: the four structural flags followed by the statement features."""
    flags = [float(v) for v in get_cfg_node_features(graph, node)]
    stmt = graph.nodes[node].get("ast_node")
    if stmt is None:
        return flags + [0.0] * (NODE_FEATURE_DIM - len(FEATURE_NAMES))
    return flags + statement_feature_vector(stmt)


def cfg_to_tensors(graph: nx.DiGraph) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Convert a CFG to node features, edge index, and the four raw structural flags."""
    nodes = list(graph.nodes())
    node_to_idx = {node: idx for idx, node in enumerate(nodes)}
    raw = torch.tensor([get_cfg_node_features(graph, node) for node in nodes], dtype=torch.float32).reshape(len(nodes), len(FEATURE_NAMES))
    x = torch.tensor([node_feature_vector(graph, node) for node in nodes], dtype=torch.float32).reshape(len(nodes), NODE_FEATURE_DIM)

    edges = [(node_to_idx[u], node_to_idx[v]) for u, v in graph.edges()]
    if edges:
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
    return x, edge_index, raw


def cfg_to_pyg_data(graph: nx.DiGraph) -> Data:
    """Convert a CFG to ``torch_geometric.data.Data``."""
    try:
        from torch_geometric.data import Data
    except ImportError as exc:
        raise ImportError("torch-geometric is required for cfg_to_pyg_data") from exc

    x, edge_index, raw_features = cfg_to_tensors(graph)
    return Data(x=x, edge_index=edge_index, raw_features=raw_features)


def extract_graph_from_pyg_data(pyg_data: Data) -> nx.DiGraph:
    """Rebuild a NetworkX graph from a PyG object, keeping node values."""
    graph = nx.DiGraph()
    x = pyg_data.x.detach().cpu()
    raw = getattr(pyg_data, "raw_features", None)
    if raw is not None:
        raw = raw.detach().cpu()
    for idx in range(int(x.size(0))):
        attrs = {"x": [float(v) for v in x[idx].reshape(-1).tolist()]}
        if raw is not None:
            attrs["features"] = [int(v) for v in raw[idx].tolist()]
        graph.add_node(idx, **attrs)
    if getattr(pyg_data, "edge_index", None) is not None and pyg_data.edge_index.numel():
        graph.add_edges_from(pyg_data.edge_index.detach().cpu().t().tolist())
    return graph


def bandit_findings(code: str, require_compile: bool = False) -> tuple[list[int], int]:
    """Run Bandit on an input program; return the covered source lines and the unique-CWE count k(c)."""
    payload = run_bandit(code, require_compile=require_compile)
    lines: set[int] = set()
    cwes: set[int] = set()
    for issue in payload["results"]:
        covered = issue.get("line_range") or [issue.get("line_number")]
        lines.update(int(line) for line in covered if line)
        cwes.add(int(issue["issue_cwe"]["id"]))
    return sorted(lines), len(cwes)


def security_node_labels(cfg_graph: nx.DiGraph, finding_lines: Iterable[int]) -> torch.Tensor:
    """Label CFG nodes that hold a Bandit finding (1.0) or not (0.0)."""
    nodes = list(cfg_graph.nodes())
    labels = torch.zeros(len(nodes), dtype=torch.float32)
    for line in finding_lines:
        best = None
        for idx, node in enumerate(nodes):
            attrs = cfg_graph.nodes[node]
            start = attrs.get("lineno")
            end = attrs.get("end_lineno") or start
            if start is not None and start <= int(line) <= end:
                span = end - start
                if best is None or span < best[0]:
                    best = (span, idx)
        if best is not None:
            labels[best[1]] = 1.0
    return labels


def node_change_scores(x: torch.Tensor, updated_x: torch.Tensor) -> torch.Tensor:
    """Per-node size of the generator update: mean absolute change over features."""
    if tuple(x.shape) != tuple(updated_x.shape):
        raise ValueError("Generator output shape differs from its input")
    return torch.abs(updated_x - x).reshape(int(x.shape[0]), -1).mean(dim=1)


def _flag_text(features: Sequence[int]) -> str:
    names = [name for name, value in zip(FEATURE_NAMES, features) if int(value)]
    return ",".join(names) if names else "none"


def _updated_flags(row) -> list[int]:
    return [int(float(v) >= 0.5) for v in row[: len(FEATURE_NAMES)].tolist()]


def _span_text(start, end) -> str:
    if start is None:
        return "L?"
    return f"L{start}" if end in (None, start) else f"L{start}-{end}"


def _snippet(code: str, max_lines: int = 3) -> str:
    lines = (code or "").splitlines()
    shown = lines[:max_lines]
    if len(lines) > max_lines:
        shown.append("...")
    return "\n".join("    " + line for line in shown)


def _one_line_code(code: str, max_chars: int = 80) -> str:
    """First non-empty line of a statement, whitespace-collapsed and truncated."""
    lines = [line.strip() for line in (code or "").splitlines() if line.strip()]
    if not lines:
        return ""
    single = " ".join(lines[0].split())
    return single if len(single) <= max_chars else single[:max_chars].rstrip() + " ..."


def _check_rows(nodes: list, x) -> None:
    if int(x.shape[0]) != len(nodes):
        raise ValueError("Generator tensors do not match the CFG node count")


def rank_generator_updates(cfg_graph: nx.DiGraph, x: torch.Tensor, updated_x: torch.Tensor, top_k: int = 5, min_abs_change: float = 0.1) -> list[dict]:
    """Rank CFG statements by the size of the generator's update to their node."""
    nodes = list(cfg_graph.nodes())
    _check_rows(nodes, x)
    scores = node_change_scores(x.detach().cpu(), updated_x.detach().cpu())
    after = updated_x.detach().cpu()
    order = sorted(range(len(nodes)), key=lambda i: (-float(scores[i]), i))
    flagged: list[dict] = []
    for idx in order:
        score = float(scores[idx])
        if len(flagged) >= int(top_k) or score < float(min_abs_change):
            break
        attrs = cfg_graph.nodes[nodes[idx]]
        flagged.append(
            {
                "node": idx,
                "ast_type": attrs.get("ast_type", ""),
                "lineno": attrs.get("lineno"),
                "end_lineno": attrs.get("end_lineno"),
                "code": attrs.get("code", ""),
                "change": score,
                "features_before": get_cfg_node_features(cfg_graph, nodes[idx]),
                "features_after": _updated_flags(after[idx]),
            }
        )
    return flagged


def serialize_cfg(cfg_graph: nx.DiGraph, x: torch.Tensor | None = None, updated_x: torch.Tensor | None = None) -> str:
    """Write a CFG as one line per statement node."""
    nodes = list(cfg_graph.nodes())
    index = {node: i for i, node in enumerate(nodes)}
    scores = after = None
    if updated_x is not None:
        if x is None:
            raise ValueError("serialize_cfg needs the generator input x together with updated_x")
        _check_rows(nodes, x)
        after = updated_x.detach().cpu()
        scores = node_change_scores(x.detach().cpu(), after)
    lines = []
    for i, node in enumerate(nodes):
        attrs = cfg_graph.nodes[node]
        successors = ",".join(f"n{index[s]}" for s in cfg_graph.successors(node)) or "end"
        flags = _updated_flags(after[i]) if after is not None else get_cfg_node_features(cfg_graph, node)
        line = f"n{i} {attrs.get('ast_type', '')} {_span_text(attrs.get('lineno'), attrs.get('end_lineno'))} flags={_flag_text(flags)}"
        if scores is not None:
            line += f" change={float(scores[i]):.3f}"
        code = _one_line_code(attrs.get("code") or "")
        line += f" code: {code if code else '(none)'}"
        lines.append(line + f" next={successors}")
    return "\n".join(lines)


def build_reconstruction_prompt(code: str, cfg_graph: nx.DiGraph, x: torch.Tensor, updated_x: torch.Tensor, top_k: int = 5, min_abs_change: float = 0.1) -> tuple[str, list[dict]]:
    """Code reconstruction request: original code, original CFG, and generator-updated CFG."""
    flagged = rank_generator_updates(cfg_graph, x, updated_x, top_k=top_k, min_abs_change=min_abs_change)
    if flagged:
        flagged_text = "\n".join(
            f"{rank}. n{item['node']} {item['ast_type']} at {_span_text(item['lineno'], item['end_lineno'])}"
            f" (change {item['change']:.3f}; flags {_flag_text(item['features_before'])}"
            f" -> {_flag_text(item['features_after'])}):\n{_snippet(item['code'])}"
            for rank, item in enumerate(flagged, start=1)
        )
    else:
        flagged_text = f"No statement node has a change score of at least {float(min_abs_change):.3f}."
    prompt = (
        "You are a coding assistant. Given an original Python code, its original control-flow graph (CFG), "
        "and an updated CFG produced by a graph generator trained to change the statements that carry security "
        "weaknesses, generate an updated version of the code that aligns with the updated CFG and maintains the "
        "original functionality. "
        "Revise the statements with the largest changes in the updated CFG to remove security weaknesses, and "
        "keep the other statements functionally unchanged unless a security fix requires otherwise. "
        "Each CFG line gives a statement node id, statement type, source lines, structural flags, "
        "change score (updated CFG only), the statement's first code line, and successor nodes.\n\n"
        "Original code:\n" + code
        + "\n\nOriginal CFG:\n" + serialize_cfg(cfg_graph)
        + "\n\nUpdated CFG:\n" + serialize_cfg(cfg_graph, x, updated_x)
        + "\n\nStatements with the largest changes in the updated CFG (largest first):\n" + flagged_text
        + "\n\nProvide the updated Python code."
    )
    return prompt, flagged


PROMPT_INFERENCE_INSTRUCTION = (
    "Estimate a detailed prompt that could be given to a large language model to generate the following Python code "
    "making sure that the code generated is secure and maintains the same functionality of the code:"
)
GENERATION_PREFIX = (
    "In your code generation, ensure that sensitive information (secret keys, passwords) "
    "is stored in environment variables not hard-coded."
)


def build_prompt_inference_request(reconstructed_code: str) -> str:
    """Prompt-inference request."""
    return (
        PROMPT_INFERENCE_INSTRUCTION
        + "\n["
        + reconstructed_code
        + "]. Try to be as specific as possible. The prompt must assure that the code must be in Python, "
        "not any other language. Do not provide any explanatory text, marks, or comments. Only give the prompt requested."
    )


def build_generation_prompt(optimized_prompt: str) -> str:
    """Code-generation request."""
    return (
        GENERATION_PREFIX
        + " "
        + optimized_prompt
        + ". Do not put any explanatory text, marks, or comments. Only give the source code as a response."
    )


