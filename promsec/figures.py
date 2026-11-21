"""Performance evaluation figure of a PromSec run."""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

ORIGINAL_COLOR = "red"
PROMSEC_COLOR = "green"
SCORE_SPECS = (
    ("graph_similarity", "Graph similarity", "#1f5bd6"),
    ("laaj_score", "LAAJ", "#ff8c00"),
    ("laaj_gated_score", "LAAJ (gated)", "#8a2be2"),
)
FIGURE_STEM = "performance_eval"
DPI = 200


def _number(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _cwe_list(value) -> list[int]:
    if isinstance(value, list):
        items = value
    else:
        try:
            items = json.loads(value) if value else []
        except ValueError:
            return []
    return [int(item) for item in items if isinstance(item, (int, str)) and str(item).isdigit()]


def _code_base_index(file_name: str, position: int) -> int:
    match = re.search(r"(\d+)\.py$", file_name or "")
    return int(match.group(1)) if match else position


def _style(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel(xlabel, fontsize=11, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=11, fontweight="bold")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight("bold")


def _prepare(rows: list[dict]) -> list[dict]:
    """Normalize report rows; graph similarity is 1 minus the generator's feature change."""
    out = []
    for position, row in enumerate(rows):
        change = _number(row.get("gnn_feature_change"))
        out.append(
            {
                "index": _code_base_index(str(row.get("file", "")), position),
                "before": _number(row.get("cwe_count_before")),
                "after": _number(row.get("cwe_count_after")),
                "cwes_before": _cwe_list(row.get("cwes_before")),
                "cwes_after": _cwe_list(row.get("cwes_after")),
                "graph_similarity": None if change is None else 1.0 - change,
                "laaj_score": _number(row.get("laaj_score")),
                "laaj_gated_score": _number(row.get("laaj_gated_score")),
            }
        )
    return sorted(out, key=lambda item: item["index"])


def cwe_count_per_code_base(ax, items: list[dict], llm: str) -> None:
    before = [(item["index"], item["before"]) for item in items if item["before"] is not None]
    after = [(item["index"], item["after"]) for item in items if item["after"] is not None]
    ax.scatter([x for x, _ in before], [y for _, y in before], s=22, color=ORIGINAL_COLOR, label="Original", zorder=3)
    ax.scatter([x for x, _ in after], [y for _, y in after], s=8, color=PROMSEC_COLOR, label="PromSec", zorder=4)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(-0.2, max([y for _, y in before + after] or [1]) + 0.4)
    ax.grid(True, linestyle=":", linewidth=0.8, color="gray")
    legend = ax.legend(loc="upper right", fontsize=8, frameon=True)
    for text in legend.get_texts():
        text.set_fontweight("bold")
    _style(ax, f"CWE Count Per Code Base ({llm})", "Code Base Index", "CWE Count")


def _bar_labels(ax, bars, fmt: str) -> None:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(fmt.format(height), (bar.get_x() + bar.get_width() / 2, height), xytext=(0, 2),
                    textcoords="offset points", ha="center", va="bottom", fontsize=7, fontweight="bold")


def _cwe_axis(ax, ids: list[int]) -> None:
    ax.set_xticks(range(len(ids)))
    ax.set_xticklabels([str(cwe) for cwe in ids], rotation=45, ha="right")
    ax.set_xlim(-0.6, len(ids) - 0.4)


def functionality_per_code_base(ax, items: list[dict], llm: str) -> None:
    """Graph similarity, LAAJ, and gated LAAJ of every program's PromSec output."""
    sizes = {"graph_similarity": 22, "laaj_score": 14, "laaj_gated_score": 6}
    for key, label, color in SCORE_SPECS:
        points = [(item["index"], item[key]) for item in items if item[key] is not None]
        ax.scatter([x for x, _ in points], [y for _, y in points], s=sizes[key], color=color, label=label, zorder=3)
    ax.set_ylim(-0.05, 1.2)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.grid(True, linestyle=":", linewidth=0.8, color="gray")
    legend = ax.legend(loc="upper right", ncol=3, fontsize=8, frameon=True)
    for text in legend.get_texts():
        text.set_fontweight("bold")
    _style(ax, f"Functionality Preservation Per Code Base ({llm})", "Code Base Index", "Score")


def cwe_id_histogram(ax, items: list[dict], llm: str) -> None:
    before, after = Counter(), Counter()
    for item in items:
        before.update(set(item["cwes_before"]))
        after.update(set(item["cwes_after"]))
    ids = sorted(set(before) | set(after))
    width = 0.38
    positions = range(len(ids))
    bars_before = ax.bar([i - width / 2 for i in positions], [before[c] for c in ids], width=width,
                         color=ORIGINAL_COLOR, label="Original", zorder=3)
    bars_after = ax.bar([i + width / 2 for i in positions], [after[c] for c in ids], width=width,
                        color=PROMSEC_COLOR, label="PromSec", zorder=3)
    _bar_labels(ax, bars_before, "{:.0f}")
    _bar_labels(ax, bars_after, "{:.0f}")
    _cwe_axis(ax, ids)
    top = max([before[c] for c in ids] + [1])
    ax.set_ylim(0, top * 1.12 + 1)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=8, integer=True, steps=[1, 2, 4, 5, 8, 10]))
    ax.grid(True, axis="both", linestyle=":", linewidth=0.8, color="gray", zorder=0)
    legend = ax.legend(loc="upper right", fontsize=10, frameon=True)
    for text in legend.get_texts():
        text.set_fontweight("bold")
    _style(ax, f"CWE ID Histogram ({llm})", "CWE ID", "CWE Count")


PANELS = (
    ("cwe_count_per_code_base", cwe_count_per_code_base, (10, 3.4)),
    ("functionality_per_code_base", functionality_per_code_base, (10, 3.4)),
    ("cwe_id_histogram", cwe_id_histogram, (9, 4.6)),
)


def _save(fig, out_dir: Path, stem: str) -> list[str]:
    paths = []
    for suffix in (".png", ".pdf"):
        path = out_dir / (stem + suffix)
        fig.savefig(path, dpi=DPI, bbox_inches="tight")
        paths.append(str(path))
    plt.close(fig)
    return paths


def write_performance_eval(rows: list[dict], out_dir: Path, llm: str) -> list[str]:
    """Write performance_eval.{png,pdf} with panels (a)-(c), and each panel as its own figure, at 200 dpi."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    items = _prepare(rows)
    if not items:
        return []
    fig, axes = plt.subplots(3, 1, figsize=(9, 12.5), gridspec_kw={"height_ratios": [0.75, 0.75, 1], "hspace": 0.62})
    for ax, (_, draw, _), tag in zip(axes, PANELS, ("(a)", "(b)", "(c)")):
        draw(ax, items, llm)
        offset = -0.3 if draw is cwe_id_histogram else -0.36
        ax.text(0.5, offset, tag, transform=ax.transAxes, ha="center", va="top", fontsize=13)
    paths = _save(fig, out_dir, FIGURE_STEM)
    for stem, draw, size in PANELS:
        fig, ax = plt.subplots(figsize=size)
        draw(ax, items, llm)
        paths += _save(fig, out_dir, stem)
    return paths


def rows_from_run_dir(run_dir: Path) -> list[dict]:
    """Report rows built from a run directory: per-program records plus the LAAJ scores of the results monitor."""
    laaj: dict[str, dict] = {}
    live = run_dir / "live_results.csv"
    if live.is_file():
        with live.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                laaj[row.get("file", "")] = row
    rows = []
    for path in sorted((run_dir / "samples").glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") == "failed" or not record.get("complete"):
            continue
        scores = laaj.get(record.get("file", ""), {})
        rows.append({**record, "laaj_score": scores.get("laaj_score"), "laaj_gated_score": scores.get("laaj_gated_score")})
    return rows


def main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m promsec.figures", description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="run directory (e.g. runs/cluster_gpu) or report per_sample.csv")
    parser.add_argument("--llm", required=True, help="name of the tested LLM, shown in the panel titles")
    parser.add_argument("--out", type=Path, help="output directory (default: <run>/report)")
    args = parser.parse_args(argv)
    if args.source.is_dir():
        rows = rows_from_run_dir(args.source)
        out = args.out or args.source / "report"
    else:
        with args.source.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        out = args.out or args.source.parent
    for path in write_performance_eval(rows, out, args.llm):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
