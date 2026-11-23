#!/usr/bin/env bash
# Progress of the run in PROMSEC_CONFIG (default: configs/default.yaml).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"
python - <<'PY'
import json, os
from promsec.config import load_config
from promsec.records import _run_dir
from promsec.runner import status
cfg = load_config(os.environ["PROMSEC_CONFIG"])
s = status(cfg)
print(json.dumps({k: s[k] for k in ("run", "samples_done", "samples_total", "samples_failed", "status_counts")}, indent=2))
totals = _run_dir(cfg) / "live_totals.txt"
if totals.is_file():
    print(totals.read_text().strip())
for flag in ("COMPLETE", "INCOMPLETE", "STOP"):
    if (_run_dir(cfg) / flag).is_file():
        print(f"{flag}: {(_run_dir(cfg) / flag).read_text().strip() or 'set'}")
PY
if tmux has-session -t "$PROMSEC_TMUX_SESSION" 2>/dev/null; then
  echo "tmux session: $PROMSEC_TMUX_SESSION (running)"
else
  echo "tmux session: $PROMSEC_TMUX_SESSION (not running)"
fi
