#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PROMSEC_TMUX_SESSION="${PROMSEC_TMUX_SESSION:-promsec_compare}"
# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"
python -m promsec compare-status
if tmux has-session -t "$PROMSEC_TMUX_SESSION" 2>/dev/null; then
  echo "tmux session: $PROMSEC_TMUX_SESSION (running)"
else
  echo "tmux session: $PROMSEC_TMUX_SESSION (not running)"
fi
for name in $(python -m promsec compare-queue | cut -d' ' -f1); do
  totals="$ROOT/runs/$name/live_totals.txt"
  [[ -s "$totals" ]] && echo "$name: $(cat "$totals")"
done
exit 0
