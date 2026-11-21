#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PIP_NO_CACHE_DIR="${PIP_NO_CACHE_DIR:-1}" bash scripts/setup_venv.sh
export PATH="$HOME/.local/tmux-env/bin:$HOME/.local/bin:$PATH"
if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed; install it before launching." >&2
fi

# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"
python - <<'PY'
import torch
print(f"torch={torch.__version__}")
print(f"cuda_available={torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"gpu={torch.cuda.get_device_name(0)}")
else:
    print("WARNING: CUDA is not visible yet. Run setup on the GPU node or install a CUDA-enabled PyTorch build compatible with the cluster driver.")
PY
