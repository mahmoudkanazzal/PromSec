"""LLM-as-a-Judge (LAAJ) functional-similarity evaluation."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import re
from dataclasses import asdict, dataclass
from typing import Callable

JsonCompletion = Callable[[str], dict]


@dataclass
class BehavioralContract:
    """Implementation-independent description of a program's observable behavior."""
    intent: str
    io_behavior: list[str]
    side_effects: list[str]
    invariants: list[str]
    edge_cases: list[str]
    public_api: dict[str, str]
    entrypoints: list[str]
    source_hash: str

    def to_dict(self) -> dict:
        return asdict(self)

    def render(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass
class FunctionalityReport:
    """Functional-similarity scores and checks for one candidate program."""
    laaj_score: float
    weighted_mean: float
    worst_dimension: float
    dimensions: dict[str, float]
    confidence: float
    compile_ok: bool
    api_preserved: bool
    entrypoints_ok: bool
    gated_score: float
    rationale: str

    def to_dict(self) -> dict:
        return asdict(self)


def _signature(args: ast.arguments) -> str:
    try:
        return "(" + ast.unparse(args) + ")"
    except (AttributeError, TypeError, ValueError):
        parts = [a.arg for a in list(args.posonlyargs) + list(args.args)]
        if args.vararg:
            parts.append("*" + args.vararg.arg)
        parts.extend(a.arg for a in args.kwonlyargs)
        if args.kwarg:
            parts.append("**" + args.kwarg.arg)
        return "(" + ", ".join(parts) + ")"


_ROUTE_METHODS = {"route": None, "get": "GET", "post": "POST", "put": "PUT", "patch": "PATCH", "delete": "DELETE"}


def _route_key(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Return a key for a web route handler, identified by its route rather than its name."""
    for decorator in node.decorator_list:
        if not (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)):
            continue
        if decorator.func.attr not in _ROUTE_METHODS or not decorator.args:
            continue
        path = decorator.args[0]
        if not (isinstance(path, ast.Constant) and isinstance(path.value, str)):
            continue
        default_method = _ROUTE_METHODS[decorator.func.attr]
        methods: list[str] = [default_method] if default_method else []
        for keyword in decorator.keywords:
            if keyword.arg == "methods" and isinstance(keyword.value, (ast.List, ast.Tuple, ast.Set)):
                methods.extend(
                    str(item.value).upper()
                    for item in keyword.value.elts
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                )
        return "route:" + ",".join(sorted(set(methods)) or ["GET"]) + " " + path.value
    return None


def public_api(code: str) -> dict[str, str]:
    """Return the top-level public interface of a program."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}

    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            route = _route_key(node)
            if route is not None:
                out[route] = ""
            elif not node.name.startswith("_"):
                out["func:" + node.name] = _signature(node.args)
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            methods = []
            for method in node.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and not method.name.startswith("_"):
                    methods.append(method.name + _signature(method.args))
            out["class:" + node.name] = ";".join(sorted(methods))
    return out


def api_preserved(original_api: dict[str, str], candidate_code: str) -> bool:
    """Return whether every public interface element of the original is present, unchanged, in the candidate."""
    candidate_api = public_api(candidate_code)
    return all(candidate_api.get(key) == value for key, value in original_api.items())


def entrypoints(code: str) -> list[str]:
    """Return regex signatures for common Python program entry points present in code."""
    patterns = [
        r"if\s+__name__\s*==\s*['\"]__main__['\"]",
        r"app\.run\s*\(",
        r"argparse\.",
        r"click\.command",
        r"typer\.Typer",
    ]
    return [pattern for pattern in patterns if re.search(pattern, code)]


def compile_ok(code: str) -> bool:
    """Return whether ``code`` compiles as Python."""
    try:
        compile(code, "<candidate>", "exec")
        return True
    except (SyntaxError, TypeError, ValueError):
        return False


def _clean_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [" ".join(str(item).split()) for item in value][:6]


def _extract_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Judge response did not contain a JSON object")
        value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Judge response must be a JSON object")
    return value


def make_openai_json_completion(model: str | None = None) -> JsonCompletion:
    """Create a JSON-completion callable using the OpenAI Python SDK."""
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY before running LAAJ evaluation.")

    judge_model = model or os.environ.get("PROMSEC_JUDGE_MODEL")
    if not judge_model:
        raise RuntimeError("Set PROMSEC_JUDGE_MODEL or pass a model name explicitly.")

    base_url = os.environ.get("PROMSEC_JUDGE_BASE_URL") or None
    client = OpenAI(api_key=api_key, base_url=base_url)

    def complete(prompt: str) -> dict:
        response = client.chat.completions.create(
            model=judge_model,
            messages=[
                {"role": "system", "content": "Return only the requested JSON object."},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        return _extract_json_object(content)

    return complete


def extract_behavioral_contract(original_code: str, json_completion: JsonCompletion) -> BehavioralContract:
    """Extract an implementation-independent behavioral contract from original code."""
    source_hash = hashlib.sha256(original_code.encode("utf-8")).hexdigest()
    prompt = f'''Describe the externally observable behavior of this Python program.
Return exactly one JSON object with these keys and value types:
- intent: string
- io_behavior: array of strings
- side_effects: array of strings
- invariants: array of strings
- edge_cases: array of strings

Requirements:
- Describe intended behavior, inputs, outputs, externally visible side effects, invariants, and edge cases.
- Do not score security and do not reward or penalize implementation style.
- Do not quote implementation details unnecessarily.
- Use at most six concise items in each list.

ORIGINAL PROGRAM:
```python
{original_code[:18000]}
```'''
    data = json_completion(prompt)
    intent = " ".join(str(data.get("intent", "")).split())
    if not intent:
        raise ValueError("Behavioral-contract extraction returned an empty intent")
    return BehavioralContract(
        intent=intent,
        io_behavior=_clean_list(data.get("io_behavior")),
        side_effects=_clean_list(data.get("side_effects")),
        invariants=_clean_list(data.get("invariants")),
        edge_cases=_clean_list(data.get("edge_cases")),
        public_api=public_api(original_code),
        entrypoints=entrypoints(original_code),
        source_hash=source_hash,
    )


DIMENSION_WEIGHTS: dict[str, float] = {
    "behavior": 0.35,
    "io_semantics": 0.20,
    "side_effects": 0.15,
    "invariants": 0.15,
    "edge_cases": 0.15,
}


def validated_scores(data: dict) -> tuple[dict[str, float], float]:
    """Require all requested scores to be finite numbers in the unit interval."""
    if not isinstance(data, dict):
        raise ValueError("Judge response must be a JSON object")
    values = {}
    for name in (*DIMENSION_WEIGHTS, "confidence"):
        raw = data.get(name)
        if raw is None or isinstance(raw, bool):
            raise ValueError(f"Judge response has no numeric {name} score")
        try:
            value = float(raw)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Judge {name} score is not numeric") from exc
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"Judge {name} score must be finite and in [0,1]")
        values[name] = value
    confidence = values.pop("confidence")
    return values, confidence


def score_candidate_functionality(
    contract: BehavioralContract,
    candidate_code: str,
    json_completion: JsonCompletion,
) -> FunctionalityReport:
    """Score candidate functionality against a fixed behavioral contract."""
    prompt = f'''You are a functionality-preservation judge. Evaluate the candidate Python program ONLY against the behavioral contract. Do not compare coding style and do not reward security improvements by themselves.

Return exactly one JSON object with these keys:
- behavior: number in [0,1]
- io_semantics: number in [0,1]
- side_effects: number in [0,1]
- invariants: number in [0,1]
- edge_cases: number in [0,1]
- confidence: number in [0,1]
- rationale: concise string

A score of 1 means the dimension is fully preserved; 0 means it is contradicted or missing. Judge semantics rather than lexical similarity.

BEHAVIORAL CONTRACT:
{contract.render()[:9000]}

CANDIDATE PROGRAM:
```python
{candidate_code[:18000]}
```'''
    data = json_completion(prompt)
    dimensions, confidence = validated_scores(data)

    weighted_mean = sum(DIMENSION_WEIGHTS[name] * dimensions[name] for name in dimensions)
    worst_dimension = min(dimensions.values()) if dimensions else 0.0
    laaj_score = 0.75 * weighted_mean + 0.25 * worst_dimension

    comp = compile_ok(candidate_code)
    api_ok = api_preserved(contract.public_api, candidate_code)
    entrypoints_ok = all(re.search(pattern, candidate_code) for pattern in contract.entrypoints)
    gated_score = laaj_score if (comp and api_ok and entrypoints_ok) else 0.0

    return FunctionalityReport(
        laaj_score=round(laaj_score, 5),
        weighted_mean=round(weighted_mean, 5),
        worst_dimension=round(worst_dimension, 5),
        dimensions=dimensions,
        confidence=round(confidence, 5),
        compile_ok=comp,
        api_preserved=api_ok,
        entrypoints_ok=entrypoints_ok,
        gated_score=round(gated_score, 5),
        rationale=" ".join(str(data.get("rationale", "")).split())[:500],
    )
