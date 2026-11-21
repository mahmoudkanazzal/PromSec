#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"
exec python -W ignore -m promsec results --config "$PROMSEC_CONFIG" "$@"
