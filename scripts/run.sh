#!/usr/bin/env bash
# Launch or resume one PromSec run in tmux: enforcement, per-program results, LAAJ and report.
#   PROMSEC_CONFIG=configs/default.yaml bash scripts/run.sh [--clear-stop]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLEAR_STOP=0
if [[ "${1:-}" == "--clear-stop" ]]; then
  CLEAR_STOP=1
elif [[ $# -gt 0 ]]; then
  echo "Usage: bash scripts/run.sh [--clear-stop]" >&2
  exit 2
fi
# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"
RUN_DIR="$(python - <<'PY'
import os
from promsec.config import load_config
from promsec.records import _run_dir
print(_run_dir(load_config(os.environ["PROMSEC_CONFIG"])))
PY
)"
mkdir -p "$RUN_DIR/logs"
[[ $CLEAR_STOP -eq 1 ]] && rm -f "$RUN_DIR/STOP"
if [[ -e "$RUN_DIR/STOP" ]]; then
  echo "STOP flag exists: $RUN_DIR/STOP"
  echo "Use --clear-stop to resume."
  exit 1
fi
bash "$ROOT/scripts/preflight.sh"
python -m promsec llm-check --config "$PROMSEC_CONFIG"
if tmux has-session -t "$PROMSEC_TMUX_SESSION" 2>/dev/null; then
  echo "PromSec is already running in tmux session: $PROMSEC_TMUX_SESSION"
  exit 0
fi
tmux new-session -d -s "$PROMSEC_TMUX_SESSION" \
  "cd '$ROOT' && export PROMSEC_TMUX_SESSION='$PROMSEC_TMUX_SESSION' PROMSEC_CONFIG='$PROMSEC_CONFIG' && exec bash scripts/supervise.sh"
echo "Started/resumed $PROMSEC_CONFIG in tmux session: $PROMSEC_TMUX_SESSION"
echo "Run folder: $RUN_DIR"
PREFIX=""
if [[ "$PROMSEC_CONFIG" != "configs/default.yaml" ]]; then PREFIX="PROMSEC_CONFIG=$PROMSEC_CONFIG "; fi
echo "Watch:  ${PREFIX}bash scripts/watch.sh"
echo "Status: ${PREFIX}bash scripts/status.sh"
echo "Stop:   ${PREFIX}bash scripts/stop.sh"
