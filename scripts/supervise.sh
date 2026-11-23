#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"

read_cfg() {
  local expr="$1"
  python - "$expr" <<'PY'
import os, sys
from promsec.config import load_config
cfg=load_config(os.environ['PROMSEC_CONFIG'])
expr=sys.argv[1]
value=cfg
for part in expr.split('.'):
    value=value[part]
print(value)
PY
}

RUN_NAME="$(read_cfg run.name)"
RUN_ROOT="$(python - <<'PY'
from promsec.config import load_config, resolve_path
import os
cfg=load_config(os.environ['PROMSEC_CONFIG'])
print(resolve_path(cfg, cfg['run']['root']))
PY
)"
RUN_DIR="$RUN_ROOT/$RUN_NAME"
STOP_FILE="$RUN_DIR/STOP"
LOG_FILE="$RUN_DIR/logs/supervisor.log"
RETRY_SECONDS="${PROMSEC_RETRY_SECONDS:-$(read_cfg supervisor.retry_seconds)}"
MAX_ENFORCEMENT_PASSES="${PROMSEC_MAX_ENFORCEMENT_PASSES:-$(read_cfg supervisor.max_enforcement_passes)}"
MAX_JUDGE_PASSES="${PROMSEC_MAX_JUDGE_PASSES:-$(read_cfg supervisor.max_judge_passes)}"
mkdir -p "$RUN_DIR/logs"
exec > >(tee -a "$LOG_FILE") 2>&1

if command -v flock >/dev/null 2>&1; then
  exec 9>"$RUN_DIR/supervisor.lock"
  if ! flock -n 9; then
    echo "Another PromSec supervisor already owns the run lock."
    exit 0
  fi
fi

stop_requested() { [[ -e "$STOP_FILE" ]]; }

sleep_or_stop() {
  local remaining="$RETRY_SECONDS"
  while (( remaining > 0 )); do
    stop_requested && return 1
    sleep 5
    remaining=$((remaining - 5))
  done
  return 0
}

enforcement_complete() {
  python - <<'PY'
import os
from promsec.config import load_config
from promsec.runner import status
cfg=load_config(os.environ['PROMSEC_CONFIG'])
s=status(cfg)
print({k:s[k] for k in ('samples_done','samples_successful','samples_failed','samples_total','status_counts','in_progress')})
raise SystemExit(0 if s['samples_done'] == s['samples_total'] else 1)
PY
}

judge_complete() {
  python - <<'PY'
import json, os
from pathlib import Path
from promsec.config import load_config
from promsec.records import COMPLETED_STATUSES, _run_dir, collect_records, judge_record_issue
cfg=load_config(os.environ['PROMSEC_CONFIG'])
run_dir=_run_dir(cfg)
records,_=collect_records(cfg)
eligible=[r for r in records if r.get('status') in COMPLETED_STATUSES]
valid=0
for rec in eligible:
    p=run_dir/'judge'/(Path(rec['file']).stem+'.json')
    if not p.is_file():
        continue
    try:
        row=json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        continue
    if judge_record_issue(row, cfg, rec) is None:
        valid += 1
print({'eligible': len(eligible), 'valid_judge_records': valid})
raise SystemExit(0 if valid == len(eligible) else 1)
PY
}

fail_stage() {
  local stage="$1"
  echo "[$(date -Is)] ERROR: $stage did not complete within the configured retry budget."
  python -m promsec report --config "$PROMSEC_CONFIG" || true
  printf '%s\n' "$stage incomplete $(date -Is)" > "$RUN_DIR/INCOMPLETE"
  exit 1
}

echo "============================================================"
echo "PromSec unattended run"
echo "started: $(date -Is)"
echo "config:  $PROMSEC_CONFIG"
echo "run:     $RUN_DIR"
echo "model:   $PROMSEC_LLM_MODEL"
echo "endpoint:$PROMSEC_LLM_BASE_URL"
echo "variant: $(read_cfg guidance.mode)"
echo "============================================================"
bash "$ROOT/scripts/preflight.sh"

start_results_monitor() {
  command -v tmux >/dev/null 2>&1 || return 0
  tmux has-session -t "$PROMSEC_TMUX_SESSION" 2>/dev/null || return 0
  if ! tmux list-windows -t "$PROMSEC_TMUX_SESSION" -F '#{window_name}' | grep -qx results; then
    tmux new-window -d -t "$PROMSEC_TMUX_SESSION" -n results \
      "cd '$ROOT' && export PROMSEC_CONFIG='$PROMSEC_CONFIG' && bash scripts/results_watch.sh 2>&1 | tee -a '$RUN_DIR/logs/results.log'"
  fi
}

wait_for_results_monitor() {
  command -v tmux >/dev/null 2>&1 || return 0
  while tmux list-windows -t "$PROMSEC_TMUX_SESSION" -F '#{window_name}' 2>/dev/null | grep -qx results; do
    stop_requested && return 1
    sleep 10
  done
  return 0
}

start_results_monitor

pass=1
while ! enforcement_complete; do
  stop_requested && { echo "STOP requested before enforcement completion."; exit 0; }
  (( pass > MAX_ENFORCEMENT_PASSES )) && fail_stage "enforcement"
  echo "[$(date -Is)] Running/resuming enforcement (pass $pass/$MAX_ENFORCEMENT_PASSES)..."
  python -m promsec run --config "$PROMSEC_CONFIG" || true
  enforcement_complete && break
  pass=$((pass + 1))
  echo "[$(date -Is)] Enforcement remains nonterminal; retrying after ${RETRY_SECONDS}s."
  sleep_or_stop || exit 0
done

echo "[$(date -Is)] Enforcement terminal for all selected samples. Failed samples remain failures and are not counted as secured."
echo "[$(date -Is)] Waiting for the per-program results monitor to finish..."
wait_for_results_monitor || { echo "STOP requested while the results monitor was running."; exit 0; }

if [[ "${PROMSEC_SKIP_JUDGE:-0}" != "1" ]]; then
  pass=1
  while ! judge_complete; do
    stop_requested && { echo "STOP requested before LAAJ completion."; exit 0; }
    (( pass > MAX_JUDGE_PASSES )) && fail_stage "LAAJ"
    echo "[$(date -Is)] Running/resuming LAAJ evaluation (pass $pass/$MAX_JUDGE_PASSES)..."
    python -m promsec judge --config "$PROMSEC_CONFIG" || true
    judge_complete && break
    pass=$((pass + 1))
    echo "[$(date -Is)] LAAJ remains incomplete; retrying after ${RETRY_SECONDS}s."
    sleep_or_stop || exit 0
  done
  echo "[$(date -Is)] LAAJ evaluation complete."
else
  echo "[$(date -Is)] LAAJ skipped because PROMSEC_SKIP_JUDGE=1."
fi

stop_requested && { echo "STOP requested before report generation."; exit 0; }
python -m promsec report --config "$PROMSEC_CONFIG"
rm -f "$RUN_DIR/INCOMPLETE"
printf '%s\n' "completed $(date -Is)" > "$RUN_DIR/COMPLETE"
echo "[$(date -Is)] COMPLETE: $RUN_DIR"
