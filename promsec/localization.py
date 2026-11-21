"""How well the active generator flags statements that hold Bandit findings."""

from __future__ import annotations

import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import torch

from utils import (
    bandit_findings,
    cfg_to_pyg_data,
    generate_cfg_from_source,
    load_original_code,
    rank_generator_updates,
    security_node_labels,
)

from .config import resolve_path
from .io import atomic_write_json
from .records import _run_dir
from .runner import _device, load_models
from .security import SecurityAnalysisError


def evaluate_localization(cfg: dict, split: str = "test") -> dict:
    """Compare the generator's flagged statements with Bandit findings."""
    if shutil.which("bandit") is None:
        raise RuntimeError("Bandit is required for localization evaluation")
    directory = resolve_path(cfg, cfg["data"]["test_dir" if split == "test" else "training_dir"])
    files = sorted(directory.glob("*.py"))
    if not files:
        raise RuntimeError(f"No programs found in {directory}")
    top_k = int(cfg["guidance"]["top_k"])
    min_abs_change = float(cfg["guidance"]["min_abs_change"])
    device = _device()
    generator, _ = load_models(cfg, device)

    def scan(path: Path):
        try:
            return path, bandit_findings(load_original_code(path))[0], ""
        except (SecurityAnalysisError, SyntaxError, ValueError) as exc:
            return path, None, f"{type(exc).__name__}: {exc}"

    with ThreadPoolExecutor(max_workers=max(1, int(cfg["training"]["label_workers"]))) as pool:
        scans = list(pool.map(scan, files))

    unscanned = []
    programs = programs_with_findings = programs_with_hit = 0
    flagged_total = hits = positives = nodes_in_programs_with_findings = 0
    flagged_on_clean = 0
    with torch.no_grad():
        for path, lines, error in scans:
            if lines is None:
                unscanned.append({"file": path.name, "error": error})
                continue
            programs += 1
            graph = generate_cfg_from_source(load_original_code(path), filename=str(path))
            labels = security_node_labels(graph, lines)
            data = cfg_to_pyg_data(graph).to(device)
            updated_x, _ = generator(data.x, data.edge_index)
            flagged = [item["node"] for item in rank_generator_updates(graph, data.x, updated_x, top_k=top_k, min_abs_change=min_abs_change)]
            hit = int(labels[flagged].sum()) if flagged else 0
            if float(labels.sum()) == 0.0:
                flagged_on_clean += len(flagged)
                continue
            programs_with_findings += 1
            positives += int(labels.sum())
            nodes_in_programs_with_findings += len(labels)
            flagged_total += len(flagged)
            hits += hit
            programs_with_hit += int(hit > 0)

    def ratio(a: float, b: float):
        return round(a / b, 4) if b else None

    result = {
        "split": split,
        "programs": len(files),
        "programs_scanned": programs,
        "programs_not_scannable": unscanned,
        "programs_with_findings": programs_with_findings,
        "top_k": top_k,
        "min_abs_change": min_abs_change,
        "flagged_per_program_with_findings": ratio(flagged_total, programs_with_findings),
        "flagged_precision": ratio(hits, flagged_total),
        "finding_statement_base_rate": ratio(positives, nodes_in_programs_with_findings),
        "finding_statement_recall": ratio(hits, positives),
        "programs_with_correct_flag": ratio(programs_with_hit, programs_with_findings),
        "flagged_statements_in_programs_without_findings": flagged_on_clean,
    }
    atomic_write_json(_run_dir(cfg) / f"localization_{split}.json", result)
    return result
