"""Variant comparison: PromSec, PromSec-S and the loop without a gGAN, over repeated runs.

``configs/compare/`` holds one configuration per run (variant and run number). The
comparison reports, per variant, the mean and range over runs of the CWEs left, the
programs secured and the functionality scores, the remaining CWE IDs, and the
in-loop localization of the gGAN: how many of the statements it passes to the LLM
hold a Bandit finding (precision) and how many Bandit-flagged statements it passes
(recall), over all iterations.
"""

from __future__ import annotations

import csv
import io
import json
from collections import Counter
from pathlib import Path

from .config import GUIDANCE_MODES, load_config
from .io import atomic_write_json, atomic_write_text, rounded
from .records import TERMINAL_STATUSES, _run_dir, _test_files, collect_records
from .report import variant_label

COMPARE_DIR = "configs/compare"


def queue(root: Path) -> list[dict]:
    """Comparison runs in launch order: run 1 of every variant, then run 2, and so on."""
    entries = []
    for path in sorted((root / COMPARE_DIR).glob("*.yaml")):
        cfg = load_config(path, root=root)
        name = str(cfg["run"]["name"])
        entries.append({"name": name, "config": str(path.relative_to(root)), "variant": cfg["guidance"]["mode"],
                        "run": int(name.rsplit("run", 1)[1]) if "run" in name else 0})
    return sorted(entries, key=lambda e: (e["run"], GUIDANCE_MODES.index(e["variant"]), e["name"]))


def status(root: Path) -> str:
    lines = [f"  {'run':<16} {'variant':<10} {'done':>9}  {'failed':>6}  state"]
    for e in queue(root):
        cfg = load_config(e["config"], root=root)
        records, _ = collect_records(cfg)
        total = len(_test_files(cfg))
        done = [r for r in records if r.get("status") in TERMINAL_STATUSES]
        failed = sum(1 for r in done if r["status"] == "failed")
        run_dir = _run_dir(cfg)
        if (run_dir / "COMPLETE").is_file() and len(done) == total:
            state = "COMPLETE"
        elif (run_dir / "STOP").is_file():
            state = "stopped"
        else:
            state = "in progress" if done else "pending"
        lines.append(f"  {e['name']:<16} {e['variant']:<10} {len(done):>4}/{total:<4}  {failed:>6}  {state}")
    return "\n".join(lines)


def _localization(samples: list[dict]) -> dict:
    flagged = hits = positives = 0
    for rec in samples:
        for step in rec.get("iterations") or []:
            given = {s["node"] for s in step.get("guidance_statements") or []}
            truth = set(step.get("bandit_statement_nodes") or [])
            flagged += len(given)
            positives += len(truth)
            hits += len(given & truth)
    return {"precision": round(hits / flagged, 3) if flagged else None,
            "recall": round(hits / positives, 3) if positives and flagged else None}


def _run_entry(name: str, variant: str, run_dir: Path, report_dir: Path) -> dict:
    summary = json.loads((report_dir / "summary.json").read_text(encoding="utf-8"))
    samples = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((run_dir / "samples").glob("*.json"))]
    return {"name": name, "variant": variant, "summary": summary, "localization": _localization(samples)}


def collect_live(root: Path) -> list[dict]:
    """Comparison runs under ``runs/`` (reports rebuilt from the current records)."""
    from .report import build_report

    runs = []
    for e in queue(root):
        cfg = load_config(e["config"], root=root)
        if not (_run_dir(cfg) / "samples").is_dir():
            continue
        build_report(cfg)
        runs.append(_run_entry(e["name"], e["variant"], _run_dir(cfg), _run_dir(cfg) / "report"))
    return runs


def collect_archive(results_dir: Path) -> list[dict]:
    """Finished runs under ``results/<variant>/run<k>`` (each with summary.json)."""
    runs = []
    for summary_path in sorted(results_dir.glob("*/run*/summary.json")):
        run_dir = summary_path.parent
        variant = json.loads(summary_path.read_text(encoding="utf-8")).get("variant", run_dir.parent.name)
        runs.append(_run_entry(f"{run_dir.parent.name}/{run_dir.name}", variant, run_dir, run_dir))
    return runs


def _rng(values: list, digits: int = 0) -> str:
    values = [v for v in values if v is not None]
    if not values:
        return "-"
    mean = sum(values) / len(values)
    if digits == 0:
        return f"{mean:.1f} [{min(values):.0f}-{max(values):.0f}]" if len(values) > 1 else f"{mean:.0f}"
    return (f"{mean:.{digits}f} [{min(values):.{digits}f}-{max(values):.{digits}f}]" if len(values) > 1
            else f"{mean:.{digits}f}")


def comparison(runs: list[dict]) -> tuple[str, list[dict]]:
    """Markdown comparison and one CSV row per run."""
    complete = [r for r in runs if r["summary"]["terminal_programs"] == r["summary"]["programs_selected"]]
    lines = ["# Variant comparison", "",
             ("Per variant: mean [min-max] over complete runs. CWEs: distinct CWE IDs per program, summed over the "
              "programs (Bandit). Secured: programs with no CWE left. Localization: share of the statements passed to "
              "the LLM that hold a Bandit finding (precision) and share of Bandit-flagged statements passed (recall), "
              "over all iterations."), "",
             ("| Variant | Runs | CWEs before | CWEs left | Programs secured | Graph sim. | Embedding sim. | LAAJ | "
              "Gated LAAJ | Localization precision | Localization recall |"),
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for mode in GUIDANCE_MODES:
        rs = [r for r in complete if r["variant"] == mode]
        if not rs:
            continue
        s = [r["summary"] for r in rs]
        lines.append(
            f"| {variant_label(mode)} | {len(rs)} | {_rng([x['cwes_before'] for x in s])} | "
            f"{_rng([x['cwes_after'] for x in s])} | {_rng([x['secured_programs'] for x in s])} | "
            f"{_rng([x['mean_graph_similarity'] for x in s], 2)} | {_rng([x['mean_embedding_similarity'] for x in s], 2)} | "
            f"{_rng([x['mean_laaj_score'] for x in s], 2)} | {_rng([x['mean_laaj_gated_score'] for x in s], 2)} | "
            f"{_rng([r['localization']['precision'] for r in rs], 2)} | {_rng([r['localization']['recall'] for r in rs], 2)} |")
    lines += ["", "## Runs", "",
              "| Run | Variant | Done | Failed | CWEs before | CWEs left | Programs secured | Mean LAAJ | Mean gated LAAJ |",
              "|---|---|---|---|---|---|---|---|---|"]
    csv_rows = []
    order = {m: i for i, m in enumerate(GUIDANCE_MODES)}
    for r in sorted(runs, key=lambda r: (order.get(r["variant"], 99), r["name"])):
        s = r["summary"]
        lines.append(f"| {r['name']} | {variant_label(r['variant'])} | {s['terminal_programs']}/{s['programs_selected']} | "
                     f"{s['failed_programs']} | {s['cwes_before']} | {s['cwes_after']} | {s['secured_programs']} | "
                     f"{_fmt(s['mean_laaj_score'])} | {_fmt(s['mean_laaj_gated_score'])} |")
        csv_rows.append({"run": r["name"], "variant": r["variant"], "done": s["terminal_programs"],
                         "selected": s["programs_selected"], "failed": s["failed_programs"],
                         "cwes_before": s["cwes_before"], "cwes_left": s["cwes_after"],
                         "programs_secured": s["secured_programs"], "vulnerable_programs": s["vulnerable_programs"],
                         "mean_graph_similarity": s["mean_graph_similarity"],
                         "mean_embedding_similarity": s["mean_embedding_similarity"],
                         "mean_laaj": s["mean_laaj_score"], "mean_gated_laaj": s["mean_laaj_gated_score"],
                         "localization_precision": r["localization"]["precision"],
                         "localization_recall": r["localization"]["recall"],
                         **{f"left_{k}": v for k, v in s["remaining_cwe_ids"].items()}})
    cwes = sorted({c for r in runs for c in r["summary"]["remaining_cwe_ids"]}, key=lambda c: int(c.split("-")[1]))
    if cwes:
        lines += ["", "## Programs with each CWE left", "", "| Run | " + " | ".join(cwes) + " |", "|---|" + "---|" * len(cwes)]
        for r in sorted(runs, key=lambda r: (order.get(r["variant"], 99), r["name"])):
            left: Counter = Counter(r["summary"]["remaining_cwe_ids"])
            lines.append(f"| {r['name']} | " + " | ".join(str(left.get(c, 0)) for c in cwes) + " |")
    return "\n".join(lines) + "\n", csv_rows


def _fmt(value) -> str:
    return "-" if value is None else f"{value:.2f}"


def write(runs: list[dict], out_dir: Path) -> str:
    text, rows = comparison(runs)
    out_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_text(out_dir / "comparison.md", text)
    fields = sorted({k for row in rows for k in row}, key=lambda k: (k.startswith("left_"), list(rows[0]).index(k)
                                                                    if k in rows[0] else 99, k)) if rows else []
    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=fields)
        writer.writeheader()
        writer.writerows([rounded(row) for row in rows])
    atomic_write_text(out_dir / "comparison.csv", buffer.getvalue())
    atomic_write_json(out_dir / "comparison.json", rounded({"runs": runs}))
    return text
