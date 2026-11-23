"""Command-line interface: ``python -m promsec <command>``."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .config import load_config

COMMANDS = {
    "run": "run the PromSec loop on the evaluation programs",
    "judge": "score functionality preservation of a run with the LLM judge (LAAJ)",
    "results": "print one result row per finished program while a run is in progress",
    "report": "write the per-program table, summary and figures of a run",
    "status": "progress of a run",
    "select": "show the statements the configured gGAN selects in a Python file (--file)",
    "compare": "compare the runs in configs/compare (or, with --results, the runs under results/)",
    "compare-queue": "list the comparison runs in launch order",
    "compare-status": "progress of the comparison runs",
    "archive-report": "rebuild the reports and the comparison of the runs under results/",
    "train": "train the PromSec gGAN on the training states (writes models/promsec unless --out)",
    "train-s": "train the PromSec-S gGAN on the training states (writes models/promsec_s unless --out)",
    "training-curves": "print the per-epoch training losses of the gGANs and redraw their training curves",
    "training-data": "generate fix-and-rescan chains on the training programs (LLM)",
    "training-data-status": "progress of the training-data run",
    "states": "label every program version of the training-data run as a training state",
    "calibrate-judge": "check the LLM judge on a few programs",
    "llm-check": "ask the LLM a one-word toy question",
    "validate": "check the data manifest",
    "manifest": "write the data manifest",
    "selftest": "offline end-to-end check with a mock LLM",
    "selftest-offline": "run the unit tests",
}


def _print(value):
    print(json.dumps(value, indent=2, sort_keys=True))


_CURVE_LABELS = {
    "generator_loss": "generator", "discriminator_loss": "discriminator", "contrastive_loss": "contrastive",
    "adversarial_loss": "adversarial", "delta_k_surrogate": "delta_k", "similarity": "similarity",
    "loc": "localization", "fix": "fix class", "adv": "gen. adversarial", "disc": "discriminator",
    "val_inloop_f1": "validation F1",
}


def _training_curves(model_dirs: list[Path]) -> None:
    """Per-epoch losses of each trained gGAN (from its training.json), and its training curves redrawn."""
    from . import ggan, ggan_s

    for model_dir in model_dirs:
        record = json.loads((Path(model_dir) / "training.json").read_text(encoding="utf-8"))
        if "training" in record:
            name, history, plot = "PromSec-S gGAN", record["training"]["history"], ggan_s.plot_training
            note = f"kept epoch: {record['training']['kept_epoch']}"
        else:
            name, history, plot = "PromSec gGAN", record["history"], ggan.plot_training
            note = f"settings: {json.dumps(record['settings'], sort_keys=True)}"
        keys = [k for k in history[0] if k != "epoch"]
        print(f"\n{name} ({model_dir}); {len(history)} epochs; {note}")
        print("  epoch  " + "  ".join(f"{_CURVE_LABELS.get(k, k):>18}" for k in keys))
        for row in history:
            print(f"  {row['epoch']:>5}  " + "  ".join(f"{row[k]:>18.4f}" for k in keys))
        held = record.get("heldout_localization", {}).get("all")
        if held:
            print(f"  held-out localization: precision {held['precision']:.2f}  recall {held['recall']:.2f}  f1 {held['f1']:.2f}")
        for path in plot(record, Path(model_dir)):
            print(f"  figure: {path}")


def main(argv: list[str] | None = None) -> None:
    """Parse the command line and run the selected command."""
    parser = argparse.ArgumentParser(prog="python -m promsec", formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="\n".join(f"  {k:<21} {v}" for k, v in COMMANDS.items()))
    parser.add_argument("command", choices=list(COMMANDS), metavar="command")
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--force", action="store_true", help="run: recompute finished programs")
    parser.add_argument("--limit", type=int, help="calibrate-judge: number of programs")
    parser.add_argument("--no-judge", action="store_true", help="results: print CWE results without LAAJ scoring")
    parser.add_argument("--interval", type=float, default=15.0, help="results: seconds between checks")
    parser.add_argument("--file", type=Path, help="select: Python file")
    parser.add_argument("--out", type=Path, help="train, train-s: output folder")
    parser.add_argument("--model-dir", type=Path, action="append",
                        help="training-curves: model folder (repeatable; default: models/promsec and models/promsec_s)")
    parser.add_argument("--results", action="store_true", help="compare: use the runs under results/")
    parser.add_argument("--llm-name", default="gpt-oss-120b", help="archive-report: LLM name in the figure titles")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    cfg = load_config(args.config, root=root)

    if args.command == "run":
        from .runner import run_enforcement
        _print(run_enforcement(cfg, force=args.force))
    elif args.command == "judge":
        from .judge import judge_run
        _print(judge_run(cfg, force=args.force))
    elif args.command == "results":
        from .live import watch_results
        judge = not args.no_judge and os.environ.get("PROMSEC_SKIP_JUDGE", "0") != "1"
        watch_results(cfg, judge=judge, interval=args.interval)
    elif args.command == "report":
        from .report import build_report
        _print(build_report(cfg))
    elif args.command == "status":
        from .runner import status
        _print(status(cfg))
    elif args.command == "select":
        from .prompts import span_text
        from .runner import load_selector
        if not args.file:
            raise SystemExit("select needs --file <program.py>")
        selector = load_selector(cfg)
        if selector is None:
            raise SystemExit("The configured variant has no gGAN; use configs/default.yaml or configs/promsec_s.yaml")
        code = args.file.read_text(encoding="utf-8")
        stmts, marked = selector(code)
        print(f"{len(stmts)} statements; {len(marked)} selected by the {cfg['guidance']['mode']} gGAN:")
        lines = code.splitlines()
        for m in marked:
            fix = f"  [{m['fix']}]" if "fix" in m else ""
            print(f"  {span_text(m['lineno'], m['end_lineno']):<9} change {m['change']:.3f}{fix}  "
                  f"{' '.join(lines[m['lineno'] - 1].split())[:100]}")
        if cfg["guidance"]["mode"] == "promsec-s" and marked:
            print("\nProposed fixes:\n" + selector.fix_text(code, stmts, marked))
    elif args.command in ("compare", "compare-queue", "compare-status", "archive-report"):
        from . import compare
        if args.command == "compare-queue":
            for entry in compare.queue(root):
                print(entry["name"], entry["config"])
        elif args.command == "compare-status":
            print(compare.status(root))
        elif args.command == "archive-report":
            from .report import build_archive_report
            test_dir = root / cfg["data"]["test_dir"]
            for run_dir in sorted((root / "results").glob("*/run*")):
                summary = build_archive_report(run_dir, test_dir, args.llm_name)
                print(f"{run_dir.relative_to(root)}: {summary['secured_programs']} secured, "
                      f"CWEs {summary['cwes_before']} -> {summary['cwes_after']}")
            print(compare.write(compare.collect_archive(root / "results"), root / "results"))
        else:
            runs = compare.collect_archive(root / "results") if args.results else compare.collect_live(root)
            out = root / ("results" if args.results else "runs")
            print(compare.write(runs, out))
    elif args.command == "train":
        from .ggan import run_training
        record = run_training(cfg, out_dir=args.out)
        _print({"heldout_localization": record["heldout_localization"], "model": str(args.out or cfg["ggan"]["model_dir"])})
    elif args.command == "train-s":
        from .ggan_s import run_training as run_training_s
        record = run_training_s(cfg, out_dir=args.out)
        _print({"heldout_localization": record["heldout_localization"], "model": str(args.out or cfg["ggan_s"]["model_dir"])})
    elif args.command == "training-curves":
        _training_curves(args.model_dir or [root / "models/promsec", root / "models/promsec_s"])
    elif args.command == "training-data":
        from . import trainingdata
        _print(trainingdata.run(cfg))
    elif args.command == "training-data-status":
        from . import trainingdata
        print(trainingdata.status(cfg))
    elif args.command == "states":
        from . import states, trainingdata
        labeled = states.label_states(cfg, states.collect_states(trainingdata.run_dir(cfg)))
        _print({"states": len(labeled), "with_findings": sum(1 for r in labeled if r["tests"]),
                "with_fix": sum(1 for r in labeled if "fix" in r), "states_dir": str(states.states_dir(cfg))})
    elif args.command == "calibrate-judge":
        from .judge import calibrate_judge
        _print(calibrate_judge(cfg, limit=args.limit))
    elif args.command == "llm-check":
        import tempfile

        from .llm import client_from_config
        question = "What is the capital city of France? Answer in one word."
        with tempfile.TemporaryDirectory() as tmp:
            cfg["llm"]["cache_path"] = str(Path(tmp) / "llm_check.sqlite")
            reply = client_from_config(cfg, "llm").complete(question, purpose="llm_check").text.strip()
        print(f"LLM check: {question!r} -> {reply[:200]!r}")
        if not reply:
            raise SystemExit("LLM check failed: empty reply")
    elif args.command == "validate":
        from .manifest import check_manifest
        _print(check_manifest(cfg))
    elif args.command == "manifest":
        from .manifest import write_manifest
        _print({"manifest": str(write_manifest(cfg))})
    elif args.command == "selftest":
        from .selftest import run
        _print(run(root))
    elif args.command == "selftest-offline":
        import unittest
        suite = unittest.defaultTestLoader.discover(str(root / "tests"), top_level_dir=str(root))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)


if __name__ == "__main__":
    main()
