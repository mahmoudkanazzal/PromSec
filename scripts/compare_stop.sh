#!/usr/bin/env bash
# Stop the comparison. Completed iterations are kept; resume with: bash scripts/compare_start.sh --clear-stop
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"
SESSION="${PROMSEC_TMUX_SESSION:-promsec_compare}"
mkdir -p "$ROOT/runs"
touch "$ROOT/runs/STOP_compare"
if command -v tmux >/dev/null 2>&1 && tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux kill-session -t "$SESSION" 2>/dev/null || true
fi
echo "Stopped. Resume with: bash scripts/compare_start.sh --clear-stop"
