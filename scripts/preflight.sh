#!/usr/bin/env bash
# Checks before a launch: tmux, Bandit, and the device (a GPU is used only for gGAN training).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/cluster_env.sh"

command -v tmux >/dev/null 2>&1 || { echo "ERROR: tmux is required." >&2; exit 1; }
command -v bandit >/dev/null 2>&1 || { echo "ERROR: Bandit is required in the virtual environment." >&2; exit 1; }

python - <<'PY'
import torch

print(f"torch={torch.__version__}")
if torch.cuda.is_available():
    print(f"gpu={torch.cuda.get_device_name(0)}")
else:
    print("gpu=none (the PromSec loop runs on CPU; gGAN training is faster on a GPU)")
PY
