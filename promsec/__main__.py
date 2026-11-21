"""Command-line interface: ``python -m promsec <command>``."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .config import load_config


def _print(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> None:
    """Parse the command line and run the selected command."""
    parser = argparse.ArgumentParser(prog="promsec")
    parser.add_argument("command", choices=["validate", "train", "run", "judge", "calibrate-judge", "report", "status", "manifest", "selftest", "selftest-offline", "localization", "results"])
    parser.add_argument("--config", default="configs/default.yaml")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--no-judge", action="store_true", help="results: print CWE results without LAAJ scoring")
    parser.add_argument("--interval", type=float, default=15.0, help="results: seconds between checks")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parents[1]
    cfg = load_config(args.config, root=root)

    if args.command == "validate":
        from .manifest import check_manifest
        _print(check_manifest(cfg))
    elif args.command == "manifest":
        from .manifest import write_manifest
        _print({"manifest": str(write_manifest(cfg))})
    elif args.command == "train":
        from .train import train_models
        _print(train_models(cfg, force=args.force))
    elif args.command == "run":
        from .runner import run_enforcement
        _print(run_enforcement(cfg, force=args.force))
    elif args.command == "judge":
        from .judge import judge_run
        _print(judge_run(cfg, force=args.force))
    elif args.command == "calibrate-judge":
        from .judge import calibrate_judge
        _print(calibrate_judge(cfg, limit=args.limit))
    elif args.command == "report":
        from .report import build_report
        _print(build_report(cfg))
    elif args.command == "status":
        from .runner import status
        _print(status(cfg))
    elif args.command == "selftest":
        from .selftest import run
        _print(run(root))
    elif args.command == "results":
        from .live import watch_results
        judge = not args.no_judge and os.environ.get("PROMSEC_SKIP_JUDGE", "0") != "1"
        watch_results(cfg, judge=judge, interval=args.interval)
    elif args.command == "localization":
        from .localization import evaluate_localization
        _print(evaluate_localization(cfg))
    elif args.command == "selftest-offline":
        import unittest
        suite = unittest.defaultTestLoader.discover(str(root / "tests"), top_level_dir=str(root))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)


if __name__ == "__main__":
    main()
