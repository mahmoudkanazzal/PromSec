#!/usr/bin/env bash
# Inside tmux (started by scripts/compare_start.sh): every comparison run in order, then the comparison.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"
STOP_FILE="$ROOT/runs/STOP_compare"
LOG_FILE="$ROOT/runs/logs/compare.log"
mkdir -p "$ROOT/runs/logs"
exec > >(tee -a "$LOG_FILE") 2>&1

if command -v flock >/dev/null 2>&1; then
  exec 8>"$ROOT/runs/compare.lock"
  if ! flock -n 8; then
    echo "Another comparison supervisor is already running."
    exit 0
  fi
fi

records_current() {
  python - "$1" <<'PY'
import sys
from promsec.config import load_config
from promsec.runner import status
s = status(load_config(sys.argv[1]))
raise SystemExit(0 if s["samples_done"] == s["samples_total"] else 1)
PY
}

mapfile -t QUEUE < <(python -m promsec compare-queue)
echo "============================================================"
echo "PromSec variant comparison   started: $(date -Is)"
echo "model: $PROMSEC_LLM_MODEL @ $PROMSEC_LLM_BASE_URL"
printf 'queue: %s\n' "${QUEUE[@]}"
echo "============================================================"
for line in "${QUEUE[@]}"; do
  [[ -e "$STOP_FILE" ]] && { echo "[$(date -Is)] STOP requested."; exit 0; }
  name="${line%% *}"
  config="${line#* }"
  run_dir="$ROOT/runs/$name"
  if [[ -e "$run_dir/COMPLETE" ]]; then
    if records_current "$config"; then
      echo "[$(date -Is)] $name: complete, skipping."
      continue
    fi
    echo "[$(date -Is)] $name: records do not match the current code or config; rerunning."
    rm -f "$run_dir/COMPLETE"
  fi
  echo "[$(date -Is)] ===== $name ($config) ====="
  rm -f "$run_dir/INCOMPLETE"
  status=0
  PROMSEC_CONFIG="$config" bash "$ROOT/scripts/supervise.sh" || status=$?
  echo "[$(date -Is)] $name: finished with status $status."
done
python -m promsec compare
echo "[$(date -Is)] Comparison: $ROOT/runs/comparison.md"
