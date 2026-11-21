"""Security enforcement: the PromSec iteration loop over the evaluation programs."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import torch

from utils import (
    build_generation_prompt,
    build_prompt_inference_request,
    build_reconstruction_prompt,
    cfg_to_pyg_data,
    generate_cfg_from_source,
    load_original_code,
    node_change_scores,
)

from .config import relevant_config_hash, resolve_path
from .io import atomic_write_json, atomic_write_text, sha256_text
from .llm import LLMClient, LLMValidationError, client_from_config
from .metrics import (
    ast_similarity,
    strip_code_fences,
    validate_python_source,
)
from .records import (
    RESULT_SCHEMA,
    TERMINAL_STATUSES,
    _run_dir,
    _test_files,
    collect_records,
    record_issue,
)
from .security import scan_cwes


def _device() -> torch.device:
    require_gpu = os.environ.get("PROMSEC_REQUIRE_GPU", "0").strip().lower() in {"1", "true", "yes", "on"}
    if torch.cuda.is_available():
        return torch.device("cuda")
    if require_gpu:
        raise RuntimeError("PROMSEC_REQUIRE_GPU is enabled but CUDA is not available")
    return torch.device("cpu")


def _device_summary(device: torch.device) -> dict:
    result = {"device": str(device), "cuda_available": bool(torch.cuda.is_available())}
    if device.type == "cuda":
        result.update(
            cuda_device_index=int(torch.cuda.current_device()),
            cuda_device_name=torch.cuda.get_device_name(torch.cuda.current_device()),
        )
    return result


def _atomic_torch_save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    try:
        torch.save(value, tmp)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _checkpoint_paths(run_dir: Path, source: Path, iteration: int) -> tuple[Path, Path]:
    checkpoint_dir = run_dir / "checkpoints" / source.stem
    stem = f"iter_{int(iteration):04d}"
    return checkpoint_dir / f"{stem}.py", checkpoint_dir / f"{stem}.pt"


def _clear_checkpoint(run_dir: Path, source: Path) -> None:
    shutil.rmtree(run_dir / "checkpoints" / source.stem, ignore_errors=True)


def _best_iteration_index(iterations: list[dict]) -> int:
    """Index of the iteration with the fewest CWEs; ties go to the earliest iteration."""
    return min(range(len(iterations)), key=lambda i: (int(iterations[i]["cwe_count"]), i))


def _best_candidate_path(run_dir: Path, source: Path) -> Path:
    return run_dir / "checkpoints" / source.stem / "best_candidate.py"


def _load_best_candidate(run_dir: Path, source: Path, expected_hash: str) -> str:
    path = _best_candidate_path(run_dir, source)
    code = path.read_text(encoding="utf-8") if path.is_file() else ""
    if sha256_text(code) != expected_hash:
        raise RuntimeError(f"Selected candidate for {source.name} is missing or does not match its recorded hash")
    return code


def _save_iteration_checkpoint(run_dir: Path, source: Path, record: dict, current_code: str, current_graph) -> None:
    iteration = len(record.get("iterations", []))
    code_path, graph_path = _checkpoint_paths(run_dir, source, iteration)
    atomic_write_text(code_path, current_code)
    _atomic_torch_save(
        graph_path,
        {
            "x": current_graph.x.detach().cpu(),
            "edge_index": current_graph.edge_index.detach().cpu(),
        },
    )
    record["resume"] = {
        "iteration_completed": iteration,
        "candidate_hash": sha256_text(current_code),
        "candidate_file": str(code_path.relative_to(run_dir)),
        "graph_file": str(graph_path.relative_to(run_dir)),
    }
    record["status"] = "running"
    record["complete"] = False
    record["iterations_used"] = iteration
    atomic_write_json(run_dir / "samples" / f"{source.stem}.json", record)

    checkpoint_dir = code_path.parent
    for old in checkpoint_dir.glob("iter_*.*"):
        if old not in {code_path, graph_path}:
            old.unlink(missing_ok=True)


def _load_iteration_checkpoint(run_dir: Path, source: Path, previous: dict, source_hash: str, config_hash: str, device: torch.device):
    from torch_geometric.data import Data

    resume = previous.get("resume")
    if not isinstance(resume, dict):
        return None
    if previous.get("schema") != RESULT_SCHEMA or previous.get("file") != source.name:
        return None
    if previous.get("source_hash") != source_hash or previous.get("config_hash") != config_hash:
        return None
    iteration = int(resume.get("iteration_completed", -1))
    if iteration < 1:
        return None
    code_path, graph_path = _checkpoint_paths(run_dir, source, iteration)
    if resume.get("candidate_file") != str(code_path.relative_to(run_dir)) or resume.get("graph_file") != str(graph_path.relative_to(run_dir)):
        return None
    if not code_path.is_file() or not graph_path.is_file():
        return None
    code = code_path.read_text(encoding="utf-8")
    if resume.get("candidate_hash") != sha256_text(code):
        return None
    try:
        state = torch.load(graph_path, map_location=device, weights_only=True)
        x = state["x"].to(device)
        edge_index = state["edge_index"].to(device)
    except (OSError, RuntimeError, KeyError, TypeError, ValueError):
        return None
    if x.ndim != 2 or edge_index.ndim != 2 or edge_index.shape[0] != 2:
        return None
    if int(resume.get("iteration_completed", -1)) != len(previous.get("iterations", [])):
        return None
    if previous.get("cwe_count_before") is None or previous.get("cwe_count_after") is None:
        return None
    return previous, code, Data(x=x, edge_index=edge_index)


def load_models(cfg: dict, device: torch.device) -> tuple[torch.nn.Module, torch.nn.Module]:
    """Load the active generator and discriminator checkpoints in evaluation mode."""
    from .model import Discriminator, Generator

    generator = Generator().to(device)
    discriminator = Discriminator().to(device)
    generator.load_state_dict(
        torch.load(resolve_path(cfg, cfg["models"]["generator"]), map_location=device, weights_only=True),
        strict=True,
    )
    discriminator.load_state_dict(
        torch.load(resolve_path(cfg, cfg["models"]["discriminator"]), map_location=device, weights_only=True),
        strict=True,
    )
    generator.eval()
    discriminator.eval()
    return generator, discriminator


def _generate_valid_python(prompt: str, llm: LLMClient, code_cache_tag: str, repair_attempts: int, purpose: str = "secure_generation") -> tuple[str, int]:
    """Generate Python source that compiles, repairing rejected LLM output."""
    base_requirements = (
        "Return only the complete Python source code. Do not include Markdown fences, labels, or explanatory text. "
        "The result must parse and compile as Python. Use ordinary ASCII punctuation/operators in Python syntax; "
        "do not use typographic hyphens, arrows, or non-breaking spaces as syntax. Keep any __future__ imports at the beginning of the file."
    )
    last_error = None
    request = prompt + "\n" + base_requirements
    for repair_round in range(int(repair_attempts) + 1):
        tag = f"{purpose}:{code_cache_tag}:repair{repair_round}"
        try:
            response = llm.complete(
                request,
                purpose=purpose,
                tag=tag,
                meta={"syntax_repair_round": repair_round},
                validate=lambda text: validate_python_source(strip_code_fences(text)),
                retry_on_validation_error=False,
            )
            candidate = strip_code_fences(response.text)
            validate_python_source(candidate)
            return candidate, repair_round
        except LLMValidationError as exc:
            last_error = exc
            if repair_round >= int(repair_attempts):
                raise
            rejected = strip_code_fences(exc.rejected_text or "").strip()
            if rejected:
                request = (
                    prompt
                    + "\n\nThe program below was generated for this task but was rejected by the Python parser/compiler.\n"
                    + "Error: " + str(exc) + "\n\nRejected program:\n" + rejected[:18000]
                    + "\n\nReturn the complete corrected program. Fix the reported error and any other syntax or "
                    + "compile-time error, and keep the program otherwise unchanged. " + base_requirements
                )
            else:
                request = (
                    prompt
                    + "\n\nA previous generated program was rejected by the Python parser/compiler with this error:\n"
                    + str(exc)
                    + "\nRegenerate the entire program from scratch and correct that error. "
                    + base_requirements
                )
    raise LLMValidationError(f"{purpose}: validation failed: {last_error}")


def run_iteration(
    code: str,
    generator: torch.nn.Module,
    llm: LLMClient,
    device: torch.device,
    *,
    syntax_repair_attempts: int = 3,
    top_k: int = 5,
    min_abs_change: float = 0.1,
) -> dict:
    """Run one PromSec iteration (Fig. 3) on code ``c``."""
    from torch_geometric.data import Data

    cfg_graph = generate_cfg_from_source(code)
    graph_data = cfg_to_pyg_data(cfg_graph).to(device)
    x = graph_data.x
    edge_index = graph_data.edge_index
    updated_x, updated_edge_index = generator(x, edge_index)
    feature_change = float(node_change_scores(x, updated_x).mean().item())

    code_cache_tag = sha256_text(code)
    reconstruction_prompt, flagged = build_reconstruction_prompt(
        code, cfg_graph, x, updated_x, top_k=top_k, min_abs_change=min_abs_change
    )
    reconstructed, reconstruction_repairs = _generate_valid_python(
        reconstruction_prompt, llm, code_cache_tag, syntax_repair_attempts, "code_reconstruction"
    )
    optimized_prompt = llm.complete(
        build_prompt_inference_request(reconstructed),
        purpose="prompt_inference",
        tag="prompt_inference:" + sha256_text(reconstructed),
    ).text.strip()
    if not optimized_prompt:
        raise LLMValidationError("prompt_inference: the LLM returned an empty prompt")
    candidate, generation_repairs = _generate_valid_python(
        build_generation_prompt(optimized_prompt), llm, sha256_text(optimized_prompt), syntax_repair_attempts,
        "secure_generation",
    )

    updated_data = Data(x=updated_x.detach(), edge_index=updated_edge_index.detach())
    return {
        "code": candidate,
        "reconstructed_code": reconstructed,
        "optimized_prompt": optimized_prompt,
        "feature_change": feature_change,
        "updated_graph": updated_data,
        "syntax_repair_rounds": reconstruction_repairs + generation_repairs,
        "flagged": flagged,
    }


def run_enforcement(cfg: dict, *, llm: LLMClient | None = None, force: bool = False) -> dict:
    """Run PromSec on every selected evaluation program; resumable per completed iteration."""
    if shutil.which("bandit") is None:
        raise RuntimeError("Bandit is required for security evaluation")

    run_dir = _run_dir(cfg)
    samples_dir = run_dir / "samples"
    vetted_dir = run_dir / "vetted_code"
    samples_dir.mkdir(parents=True, exist_ok=True)
    vetted_dir.mkdir(parents=True, exist_ok=True)
    call_log = run_dir / "calls.jsonl"
    llm = llm or client_from_config(cfg, "llm", call_log=call_log)

    device = _device()
    generator, _ = load_models(cfg, device)
    config_hash = relevant_config_hash(cfg)
    max_iterations = int(cfg["loop"]["max_iterations"])
    syntax_repair_attempts = int(cfg["llm"].get("syntax_repair_attempts", 3))
    guidance_top_k = int(cfg["guidance"]["top_k"])
    guidance_min_abs_change = float(cfg["guidance"]["min_abs_change"])

    files = _test_files(cfg)
    if not files:
        raise RuntimeError("No evaluation programs were selected")
    started = time.perf_counter()

    def process(path: Path) -> tuple[str, bool]:
        """Run PromSec on one program; return its outcome and whether it resumed mid-program."""
        with torch.no_grad():
            partial = False
            outcome = "completed"
            original_code = load_original_code(path)
            source_hash = sha256_text(original_code)
            sample_path = samples_dir / f"{path.stem}.json"
            previous = None
            resume_state = None
            if sample_path.exists() and not force:
                try:
                    previous = json.loads(sample_path.read_text(encoding="utf-8"))
                    if not record_issue(previous, cfg, path, config_hash) and (previous.get("complete") or previous.get("status") == "failed"):
                        return "resumed", False
                    resume_state = _load_iteration_checkpoint(run_dir, path, previous, source_hash, config_hash, device)
                except (OSError, ValueError, TypeError):
                    previous = None
                    resume_state = None

            if force or resume_state is None:
                _clear_checkpoint(run_dir, path)
                (vetted_dir / path.name).unlink(missing_ok=True)
                (run_dir / "judge" / f"{path.stem}.json").unlink(missing_ok=True)
                (run_dir / "judge" / "errors" / f"{path.stem}.json").unlink(missing_ok=True)
                record: dict[str, Any] = {
                    "schema": RESULT_SCHEMA,
                    "file": path.name,
                    "source_hash": source_hash,
                    "config_hash": config_hash,
                    "status": None,
                    "complete": False,
                    "iterations": [],
                    "error": "",
                    "cwe_count_before": None,
                    "cwe_count_after": None,
                    "candidate_hash": None,
                }
                current_code = original_code
                current_graph = None
            else:
                record, current_code, current_graph = resume_state
                record["status"] = "running"
                record["complete"] = False
                record["error"] = ""
                partial = True

            try:
                if current_graph is None:
                    current_graph = cfg_to_pyg_data(generate_cfg_from_source(original_code, filename=str(path))).to(device)
                    before_count, before_cwes = scan_cwes(original_code, require_compile=False)
                    after_count, after_cwes = before_count, before_cwes
                    record.update(
                        cwe_count_before=before_count,
                        cwes_before=before_cwes,
                        cwe_count_after=after_count,
                        cwes_after=after_cwes,
                    )
                else:
                    before_count = int(record["cwe_count_before"])
                    before_cwes = record.get("cwes_before", [])
                    after_count = int(record["cwe_count_after"])
                    after_cwes = record.get("cwes_after", [])

                if before_count == 0:
                    record["status"] = "already_clean"
                    output_code = original_code
                    best_index = None
                else:
                    start_iteration = len(record["iterations"]) + 1
                    for iteration in range(start_iteration, max_iterations + 1):
                        if record["iterations"] and min(item["cwe_count"] for item in record["iterations"]) == 0:
                            break
                        try:
                            step = run_iteration(
                                current_code, generator, llm, device,
                                syntax_repair_attempts=syntax_repair_attempts,
                                top_k=guidance_top_k,
                                min_abs_change=guidance_min_abs_change,
                            )
                        except LLMValidationError as exc:
                            if not record["iterations"]:
                                raise
                            record["stopped_at_iteration"] = iteration
                            record["stop_reason"] = f"{type(exc).__name__}: {exc}"
                            break
                        candidate = step["code"]
                        current_graph = step["updated_graph"]
                        candidate_count, candidate_cwes = scan_cwes(candidate)
                        record["iterations"].append(
                            {
                                "iteration": iteration,
                                "cwe_count": candidate_count,
                                "cwes": candidate_cwes,
                                "candidate_hash": sha256_text(candidate),
                                "gnn_feature_change": step["feature_change"],
                                "ast_similarity_to_original": ast_similarity(original_code, candidate),
                                "syntax_repair_rounds": step["syntax_repair_rounds"],
                                "optimized_prompt": step["optimized_prompt"],
                                "gnn_flagged_statements": [
                                    {
                                        "node": item["node"],
                                        "ast_type": item["ast_type"],
                                        "lineno": item["lineno"],
                                        "end_lineno": item["end_lineno"],
                                        "change": item["change"],
                                    }
                                    for item in step["flagged"]
                                ],
                            }
                        )
                        current_code = candidate
                        best_index = _best_iteration_index(record["iterations"])
                        if best_index == len(record["iterations"]) - 1:
                            atomic_write_text(_best_candidate_path(run_dir, path), candidate)
                        best_step = record["iterations"][best_index]
                        record.update(cwe_count_after=best_step["cwe_count"], cwes_after=best_step["cwes"])
                        _save_iteration_checkpoint(run_dir, path, record, current_code, current_graph)

                    best_index = _best_iteration_index(record["iterations"])
                    best = record["iterations"][best_index]
                    output_code = current_code
                    if best_index != len(record["iterations"]) - 1:
                        output_code = _load_best_candidate(run_dir, path, best["candidate_hash"])
                    after_count, after_cwes = best["cwe_count"], best["cwes"]
                    record["status"] = "secured" if after_count == 0 else "max_iterations_reached"

                best_step = record["iterations"][best_index] if best_index is not None else None
                record.update(
                    cwe_count_after=after_count,
                    cwes_after=after_cwes,
                    iterations_used=len(record["iterations"]),
                    selected_iteration=(best_step["iteration"] if best_step else 0),
                    gnn_feature_change=(best_step["gnn_feature_change"] if best_step else 0.0),
                    ast_similarity=ast_similarity(original_code, output_code),
                )
                atomic_write_text(vetted_dir / path.name, output_code)
                record["candidate_hash"] = sha256_text(output_code)
                record.pop("resume", None)
                _clear_checkpoint(run_dir, path)
                outcome = "completed"
            except Exception as exc:
                record["status"] = "failed"
                record["error"] = f"{type(exc).__name__}: {exc}"
                if "resume" not in record:
                    record["cwe_count_after"] = None
                    record["candidate_hash"] = None
                outcome = "failed"
            record["iterations_used"] = len(record["iterations"])
            record["complete"] = record["status"] in TERMINAL_STATUSES
            atomic_write_json(sample_path, record)
            return outcome, partial

    parallel = max(1, int(cfg["loop"].get("parallel_programs", 1)))
    if parallel == 1:
        outcomes = [process(path) for path in files]
    else:
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            outcomes = list(pool.map(process, files))
    completed = sum(1 for outcome, _ in outcomes if outcome == "completed")
    failed = sum(1 for outcome, _ in outcomes if outcome == "failed")
    resumed = sum(1 for outcome, _ in outcomes if outcome == "resumed")
    resumed_partial = sum(1 for _, partial in outcomes if partial)

    summary = {
        "run_dir": str(run_dir),
        "files_selected": len(files),
        "completed_now": completed,
        "resumed": resumed,
        "resumed_completed": resumed,
        "resumed_partial": resumed_partial,
        "failed_now": failed,
        "seconds": round(time.perf_counter() - started, 3),
        **_device_summary(device),
    }
    atomic_write_json(run_dir / "run_summary.json", summary)
    return summary


def status(cfg: dict) -> dict:
    """Progress of an enforcement run."""
    run_dir = _run_dir(cfg)
    samples, excluded = collect_records(cfg)
    counts: dict[str, int] = {}
    in_progress = []
    config_hash = relevant_config_hash(cfg)
    for source in _test_files(cfg):
        sample_path = run_dir / "samples" / f"{source.stem}.json"
        if not sample_path.is_file():
            continue
        try:
            rec = json.loads(sample_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        if rec.get("source_hash") != sha256_text(source.read_text(encoding="utf-8")) or rec.get("config_hash") != config_hash:
            continue
        key = str(rec.get("status") or "unknown")
        counts[key] = counts.get(key, 0) + 1
        if rec.get("status") == "running" and not rec.get("complete") and rec.get("resume"):
            in_progress.append(
                {
                    "file": rec.get("file"),
                    "iteration_completed": rec["resume"].get("iteration_completed"),
                    "cwe_count": rec.get("cwe_count_after"),
                    "last_error": rec.get("error") or "",
                }
            )
    terminal = sum(1 for r in samples if r.get("status") in TERMINAL_STATUSES and (r.get("complete") is True or r.get("status") == "failed"))
    successful = sum(1 for r in samples if r.get("status") in {"already_clean", "secured", "max_iterations_reached"})
    failed = sum(1 for r in samples if r.get("status") == "failed")
    return {
        "run_dir": str(run_dir),
        "samples_done": terminal,
        "samples_successful": successful,
        "samples_failed": failed,
        "samples_total": len(_test_files(cfg)),
        "status_counts": counts,
        "in_progress": in_progress,
        "excluded": excluded,
    }
