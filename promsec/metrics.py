"""Source validation and similarity measures."""

from __future__ import annotations

import ast
import re
import warnings


def validate_python_source(code: str, require_compile: bool = True) -> None:
    """Require Python that parses and contains at least one statement."""
    if not isinstance(code, str) or not code.strip():
        raise ValueError("The Python source is empty")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(code, filename="<promsec-source>")
        if require_compile:
            compile(tree, "<promsec-source>", "exec")
    if not tree.body:
        raise ValueError("The Python source contains no statements")


def compare_asts(tree1: ast.AST, tree2: ast.AST) -> float:
    """Fraction of AST nodes whose type also occurs in the other tree."""
    nodes1 = list(ast.walk(tree1))
    nodes2 = list(ast.walk(tree2))
    if not nodes1 and not nodes2:
        return 1.0
    common_nodes = sum(1 for node in nodes1 if any(isinstance(node, type(other)) for other in nodes2))
    return common_nodes / max(len(nodes1), len(nodes2), 1)


def ast_similarity(code1: str, code2: str) -> float:
    """AST similarity of two programs; 0.0 if either does not parse."""
    try:
        return compare_asts(ast.parse(code1), ast.parse(code2))
    except SyntaxError:
        return 0.0


def strip_code_fences(text: str) -> str:
    """Return the code in an LLM response, without Markdown fences or surrounding text."""
    text = text.strip()
    if not text.startswith("```"):
        blocks = re.findall(r"```[ \t]*(?:python|py)?[ \t]*\n(.*?)\n[ \t]*```", text, flags=re.DOTALL | re.IGNORECASE)
        return max(blocks, key=len).strip() if blocks else text
    lines = text.splitlines()
    if lines and lines[0].strip().lower() in {"```", "```python", "```py"}:
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()
