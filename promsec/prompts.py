"""LLM requests of the PromSec iteration.

One iteration sends three requests:

1. code reconstruction: the LLM revises the code, guided by the statements the gGAN selects;
2. prompt inference: the LLM writes a prompt that would generate the revised code securely;
3. generation: the LLM generates new code from that prompt.

The reconstruction request depends on the variant (``guidance.mode``):

``promsec``   the statements whose graph nodes the gGAN changes most;
``promsec-s`` the same, plus the supervised gGAN's proposed fix per statement;
``none``      the code alone (no gGAN; ablation).
"""

from __future__ import annotations

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


def span_text(start, end) -> str:
    if start is None:
        return "L?"
    return f"L{start}" if end in (None, start) else f"L{start}-{end}"


def snippet(code: str, max_lines: int = 3) -> str:
    lines = (code or "").splitlines()
    shown = lines[:max_lines]
    if len(lines) > max_lines:
        shown.append("...")
    return "\n".join("    " + line for line in shown)


def statements_with_code(code: str, marked: list[dict]) -> list[dict]:
    """Attach each selected statement's source lines (for the statement list in the request)."""
    lines = code.splitlines()
    return [{**m, "code": "\n".join(lines[m["lineno"] - 1: m["end_lineno"]])} for m in marked]


def build_unguided_reconstruction_prompt(code: str) -> str:
    """Reconstruction request without guidance (the ``none`` ablation)."""
    return (
        "You are a coding assistant. Given an original Python code, generate an updated version of the code "
        "that maintains the original functionality. "
        "Revise the statements that carry security weaknesses to remove those weaknesses, and keep the other "
        "statements functionally unchanged unless a security fix requires otherwise.\n\n"
        "Original code:\n" + code
        + "\n\nProvide the updated Python code."
    )


def build_reconstruction_prompt(code: str, statements: list[dict], fixes: str | None = None) -> str:
    """Reconstruction request with the gGAN's selected statements (in source order) and, optionally, proposed fixes."""
    if statements:
        listed = "\n".join(
            f"{rank}. {item['ast_type']} at {span_text(item['lineno'], item['end_lineno'])}:\n{snippet(item['code'])}"
            for rank, item in enumerate(statements, start=1)
        )
    else:
        listed = "No statement is listed."
    text = (
        "You are a coding assistant. Given an original Python code and the statements that carry security "
        "weaknesses, generate an updated version of the code that maintains the original functionality. "
        "Revise the listed statements to remove security weaknesses, and keep the other statements functionally "
        "unchanged unless a security fix requires otherwise. "
        "Each listed statement gives its statement type, source lines, and code.\n\n"
        "Original code:\n" + code
        + "\n\nStatements that carry security weaknesses (in source order):\n" + listed
    )
    if fixes:
        text += "\n\nProposed fixes:\n" + fixes
    return text + "\n\nProvide the updated Python code."
