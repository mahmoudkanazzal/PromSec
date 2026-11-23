#!/usr/bin/env bash
# Launch or resume all comparison runs (configs/compare) in tmux, then write runs/comparison.md.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PROMSEC_TMUX_SESSION="${PROMSEC_TMUX_SESSION:-promsec_compare}"
CLEAR_STOP=0
if [[ "${1:-}" == "--clear-stop" ]]; then
  CLEAR_STOP=1
elif [[ $# -gt 0 ]]; then
  echo "Usage: bash scripts/compare_start.sh [--clear-stop]" >&2
  exit 2
fi
# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"
mkdir -p "$ROOT/runs"
[[ $CLEAR_STOP -eq 1 ]] && rm -f "$ROOT/runs/STOP_compare"
if [[ -e "$ROOT/runs/STOP_compare" ]]; then
  echo "STOP flag exists: $ROOT/runs/STOP_compare (use --clear-stop to resume)"
  exit 1
fi
bash "$ROOT/scripts/preflight.sh"
python -m promsec llm-check
if tmux has-session -t "$PROMSEC_TMUX_SESSION" 2>/dev/null; then
  echo "The comparison is already running in tmux session: $PROMSEC_TMUX_SESSION"
  exit 0
fi
tmux new-session -d -s "$PROMSEC_TMUX_SESSION" \
  "cd '$ROOT' && export PROMSEC_TMUX_SESSION='$PROMSEC_TMUX_SESSION' && exec bash scripts/compare.sh"
echo "Started/resumed the comparison in tmux session: $PROMSEC_TMUX_SESSION"
python -m promsec compare-queue | sed 's/^/  /'
echo "Status: bash scripts/compare_status.sh      Stop: bash scripts/compare_stop.sh"
