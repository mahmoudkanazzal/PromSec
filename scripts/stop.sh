#!/usr/bin/env bash
# Stop the run in PROMSEC_CONFIG. Completed iterations are kept; resume with: bash scripts/run.sh --clear-stop
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"
CONFIG="${PROMSEC_CONFIG:-configs/default.yaml}"
SESSION="${PROMSEC_TMUX_SESSION:-promsec_$(basename "$CONFIG" .yaml)}"
RUN_DIR="$(cd "$ROOT" && "$ROOT/.venv/bin/python" -c "
from promsec.config import load_config
from promsec.records import _run_dir
print(_run_dir(load_config('$CONFIG')))")"
mkdir -p "$RUN_DIR"
touch "$RUN_DIR/STOP"
if command -v tmux >/dev/null 2>&1 && tmux has-session -t "$SESSION" 2>/dev/null; then
  # No Ctrl-C: SIGINT would reach Bandit subprocesses. Killing the session ends the run between atomic writes.
  tmux kill-session -t "$SESSION" 2>/dev/null || true
fi
echo "Stopped. Resume with: bash scripts/run.sh --clear-stop"
