#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLEAR_STOP=0
if [[ "${1:-}" == "--clear-stop" ]]; then
  CLEAR_STOP=1
elif [[ $# -gt 0 ]]; then
  echo "Usage: bash scripts/start_or_resume.sh [--clear-stop]" >&2
  exit 2
fi

# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"
RUN_NAME="$(python - <<'PY'
from promsec.config import load_config
import os
cfg=load_config(os.environ['PROMSEC_CONFIG'])
print(cfg['run']['name'])
PY
)"
RUN_ROOT="$(python - <<'PY'
from promsec.config import load_config, resolve_path
import os
cfg=load_config(os.environ['PROMSEC_CONFIG'])
print(resolve_path(cfg, cfg['run']['root']))
PY
)"
RUN_DIR="$RUN_ROOT/$RUN_NAME"
STOP_FILE="$RUN_DIR/STOP"
mkdir -p "$RUN_DIR"

if [[ $CLEAR_STOP -eq 1 ]]; then
  rm -f "$STOP_FILE"
fi
if [[ -e "$STOP_FILE" ]]; then
  echo "STOP flag exists: $STOP_FILE"
  echo "Use --clear-stop to explicitly resume."
  exit 1
fi

bash "$ROOT/scripts/gpu_preflight.sh"

if tmux has-session -t "$PROMSEC_TMUX_SESSION" 2>/dev/null; then
  echo "PromSec is already running in tmux session: $PROMSEC_TMUX_SESSION"
  echo "Watch with: bash scripts/watch.sh"
  exit 0
fi

mkdir -p "$RUN_DIR/logs"
tmux new-session -d -s "$PROMSEC_TMUX_SESSION" "cd '$ROOT' && export PROMSEC_TMUX_SESSION='$PROMSEC_TMUX_SESSION' PROMSEC_CONFIG='$PROMSEC_CONFIG' && exec bash scripts/supervise.sh"
echo "Started/resumed PromSec in tmux session: $PROMSEC_TMUX_SESSION"
echo "Run directory: $RUN_DIR"
echo "Watch with: bash scripts/watch.sh"
echo "Stop with:  bash scripts/stop.sh"
