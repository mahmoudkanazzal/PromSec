#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/tmux-env/bin:$HOME/.local/bin:$PATH"
SESSION="${PROMSEC_TMUX_SESSION:-promsec}"
CONFIG="${PROMSEC_CONFIG:-configs/cluster_gpu.yaml}"
RUN_NAME="$(awk '/^run:/{in_run=1; next} /^[^ ]/{in_run=0} in_run && $1=="name:"{print $2; exit}' "$ROOT/$CONFIG")"
RUN_DIR="${PROMSEC_RUN_DIR:-$ROOT/runs/${RUN_NAME:-cluster_gpu}}"
mkdir -p "$RUN_DIR"
touch "$RUN_DIR/STOP"

if command -v tmux >/dev/null 2>&1 && tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux send-keys -t "$SESSION" C-c || true
  sleep 2
  tmux kill-session -t "$SESSION" 2>/dev/null || true
fi
echo "Stopped. The STOP flag prevents automatic restart: $RUN_DIR/STOP"
echo "Resume explicitly with: bash scripts/start_or_resume.sh --clear-stop"
