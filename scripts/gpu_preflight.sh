#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"

command -v tmux >/dev/null 2>&1 || { echo "ERROR: tmux is required." >&2; exit 1; }
command -v bandit >/dev/null 2>&1 || { echo "ERROR: Bandit is required in the virtual environment." >&2; exit 1; }

python - <<'PY'
import os
import torch

print(f"torch={torch.__version__}")
print(f"CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES')}")
if not torch.cuda.is_available():
    raise SystemExit("ERROR: CUDA is not available to PyTorch.")
name = torch.cuda.get_device_name(0)
props = torch.cuda.get_device_properties(0)
print(f"gpu={name}")
print(f"compute_capability={props.major}.{props.minor}")
print(f"memory_gib={props.total_memory / (1024**3):.1f}")
PY
