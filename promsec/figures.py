"""Figures: performance evaluation of a PromSec run, and gGAN training curves."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import MaxNLocator

_AVAILABLE_FONTS = {f.name for f in font_manager.fontManager.ttflist}
# Calibri, or its metric-compatible equivalent Carlito; otherwise matplotlib's default.
plt.rcParams["font.family"] = next((f for f in ("Calibri", "Carlito") if f in _AVAILABLE_FONTS), "DejaVu Sans")

ORIGINAL_COLOR = "red"
PROMSEC_COLOR = "green"
SCORE_SPECS = (
    ("graph_similarity", "Graph similarity", "#1f5bd6"),
    ("embedding_similarity", "Embedding similarity", "#2ca02c"),
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
    """Normalize report rows (failed programs have no output and are left out of the panels)."""
    out = []
    for position, row in enumerate(rows):
        if row.get("status") == "failed":
            continue
        out.append(
            {
                "index": _code_base_index(str(row.get("file", "")), position),
                "before": _number(row.get("cwe_count_before")),
                "after": _number(row.get("cwe_count_after")),
                "cwes_before": _cwe_list(row.get("cwes_before")),
                "cwes_after": _cwe_list(row.get("cwes_after")),
                "graph_similarity": _number(row.get("graph_similarity")),
                "embedding_similarity": _number(row.get("embedding_similarity")),
                "laaj_score": _number(row.get("laaj_score")),
                "laaj_gated_score": _number(row.get("laaj_gated_score")),
            }
        )
    return sorted(out, key=lambda item: item["index"])


def cwe_count_per_code_base(ax, items: list[dict], llm: str, label: str = "PromSec") -> None:
    before = [(item["index"], item["before"]) for item in items if item["before"] is not None]
    after = [(item["index"], item["after"]) for item in items if item["after"] is not None]
    ax.scatter([x for x, _ in before], [y for _, y in before], s=22, color=ORIGINAL_COLOR, label="Original", zorder=3)
    ax.scatter([x for x, _ in after], [y for _, y in after], s=8, color=PROMSEC_COLOR, label=label, zorder=4)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(-0.2, max([y for _, y in before + after] or [1]) + 0.4)
    ax.grid(True, linestyle=":", linewidth=0.8, color="gray")
    legend = ax.legend(loc="upper right", fontsize=8, frameon=True)
    for text in legend.get_texts():
        text.set_fontweight("bold")
    _style(ax, f"CWE Count Per Code Base ({llm}, {label})", "Code Base Index", "CWE Count")


def _bar_labels(ax, bars, fmt: str) -> None:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(fmt.format(height), (bar.get_x() + bar.get_width() / 2, height), xytext=(0, 2),
                    textcoords="offset points", ha="center", va="bottom", fontsize=7, fontweight="bold")


def _cwe_axis(ax, ids: list[int]) -> None:
    ax.set_xticks(range(len(ids)))
    ax.set_xticklabels([str(cwe) for cwe in ids], rotation=45, ha="right")
    ax.set_xlim(-0.6, len(ids) - 0.4)


def functionality_per_code_base(ax, items: list[dict], llm: str, label: str = "PromSec") -> None:
    """Graph similarity, embedding similarity, LAAJ and gated LAAJ of every program's output."""
    sizes = {"graph_similarity": 26, "embedding_similarity": 18, "laaj_score": 12, "laaj_gated_score": 6}
    for key, name, color in SCORE_SPECS:
        points = [(item["index"], item[key]) for item in items if item[key] is not None]
        ax.scatter([x for x, _ in points], [y for _, y in points], s=sizes[key], color=color, label=name, zorder=3)
    ax.set_ylim(-0.05, 1.2)
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.grid(True, linestyle=":", linewidth=0.8, color="gray")
    legend = ax.legend(loc="upper right", ncol=4, fontsize=8, frameon=True)
    for text in legend.get_texts():
        text.set_fontweight("bold")
    _style(ax, f"Functionality Preservation Per Code Base ({llm}, {label})", "Code Base Index", "Score")


def cwe_id_histogram(ax, items: list[dict], llm: str, label: str = "PromSec") -> None:
    before: Counter = Counter()
    after: Counter = Counter()
    for item in items:
        before.update(set(item["cwes_before"]))
        after.update(set(item["cwes_after"]))
    ids = sorted(set(before) | set(after))
    width = 0.38
    positions = range(len(ids))
    bars_before = ax.bar([i - width / 2 for i in positions], [before[c] for c in ids], width=width,
                         color=ORIGINAL_COLOR, label="Original", zorder=3)
    bars_after = ax.bar([i + width / 2 for i in positions], [after[c] for c in ids], width=width,
                        color=PROMSEC_COLOR, label=label, zorder=3)
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
    _style(ax, f"CWE ID Histogram ({llm}, {label})", "CWE ID", "CWE Count")


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


def write_performance_eval(rows: list[dict], out_dir: Path, llm: str, label: str = "PromSec") -> list[str]:
    """Write performance_eval.{png,pdf} with panels (a)-(c), and each panel as its own figure, at 200 dpi."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    items = _prepare(rows)
    if not items:
        return []
    fig, axes = plt.subplots(3, 1, figsize=(9, 12.5), gridspec_kw={"height_ratios": [0.75, 0.75, 1], "hspace": 0.62})
    for ax, (_, draw, _), tag in zip(axes, PANELS, ("(a)", "(b)", "(c)")):
        draw(ax, items, llm, label)
        offset = -0.3 if draw is cwe_id_histogram else -0.36
        ax.text(0.5, offset, tag, transform=ax.transAxes, ha="center", va="top", fontsize=13)
    paths = _save(fig, out_dir, FIGURE_STEM)
    for stem, draw, size in PANELS:
        fig, ax = plt.subplots(figsize=size)
        draw(ax, items, llm, label)
        paths += _save(fig, out_dir, stem)
    return paths


def line_figure(x: list, title: str, ylabel: str, series: list[tuple], stem: Path) -> list[Path]:
    """One line panel. ``series``: [(name, ys)]."""
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    for k, (name, ys) in enumerate(series):
        ax.plot(x, ys, marker="os"[k % 2], markersize=4, label=name)
    ax.set_title(title, fontsize=11, fontweight="bold")
    ax.set_xlabel("Epoch")
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle=":", linewidth=0.8, color="gray")
    ax.set_xticks(x)
    ax.legend(frameon=False, fontsize=8)
    paths = []
    for suffix in (".png", ".pdf"):
        path = Path(str(stem) + suffix)
        fig.savefig(path, dpi=DPI, bbox_inches="tight")
        paths.append(path)
    plt.close(fig)
    return paths


def three_panel_figure(x: list, panels: list[tuple], stem: Path, *, markers: bool = True,
                       vline: tuple[int, int, str] | None = None) -> list[Path]:
    """Three line panels: two side by side on top, the third centred below. ``panels``: (title, ylabel, [(name, ys)])."""
    fig = plt.figure(figsize=(9, 6.4))
    grid = fig.add_gridspec(2, 4, hspace=0.45, wspace=0.6)
    axes = [fig.add_subplot(grid[0, 0:2]), fig.add_subplot(grid[0, 2:4]), fig.add_subplot(grid[1, 1:3])]
    for index, (ax, (title, ylabel, series)) in enumerate(zip(axes, panels)):
        for k, (name, ys) in enumerate(series):
            ax.plot(x, ys, marker=("os"[k % 2] if markers else None), markersize=4, label=name)
        if vline and vline[0] == index:
            ax.axvline(vline[1], color="0.4", linestyle="--", linewidth=1)
            ax.annotate(vline[2], (vline[1], ax.get_ylim()[0]), textcoords="offset points", xytext=(4, 4), fontsize=8)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("Epoch")
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle=":", linewidth=0.8, color="gray")
        if markers:
            ax.set_xticks(x)
        ax.legend(frameon=False, fontsize=8)
    paths = []
    for suffix in (".png", ".pdf"):
        path = Path(str(stem) + suffix)
        fig.savefig(path, dpi=DPI, bbox_inches="tight")
        paths.append(path)
    plt.close(fig)
    return paths
