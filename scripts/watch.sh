#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"
RUN_NAME="$(python - <<'PY'
from promsec.config import load_config
import os
print(load_config(os.environ['PROMSEC_CONFIG'])['run']['name'])
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
LOG_FILE="$RUN_DIR/logs/supervisor.log"

python - <<'PY2'
import json, os
from promsec.config import load_config
from promsec.runner import status
s=status(load_config(os.environ["PROMSEC_CONFIG"]))
print(json.dumps({k:s[k] for k in ("run_dir","samples_done","samples_total","status_counts","in_progress")}, indent=2))
PY2
echo
if tmux has-session -t "$PROMSEC_TMUX_SESSION" 2>/dev/null; then
  echo "tmux session: $PROMSEC_TMUX_SESSION (running)"
else
  echo "tmux session: $PROMSEC_TMUX_SESSION (not running)"
fi
if [[ -e "$RUN_DIR/COMPLETE" ]]; then
  cat "$RUN_DIR/COMPLETE"
fi

echo "Following $LOG_FILE (Ctrl-C only stops this viewer)..."
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"
tail -n 80 -F "$LOG_FILE"
