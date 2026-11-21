#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PATH="$HOME/.local/tmux-env/bin:$HOME/.local/bin:$PATH"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "ERROR: $ROOT/.venv is missing. Run: bash scripts/setup_gpu_venv.sh" >&2
  return 1 2>/dev/null || exit 1
fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

KEY_FILE="${PROMSEC_API_KEY_FILE:-$ROOT/api_key.txt}"
if [[ ! -s "$KEY_FILE" ]]; then
  echo "ERROR: API key file not found or empty: $KEY_FILE" >&2
  return 1 2>/dev/null || exit 1
fi
export OPENAI_API_KEY="$(tr -d '\r\n' < "$KEY_FILE")"
if [[ -z "$OPENAI_API_KEY" ]]; then
  echo "ERROR: API key file is empty after trimming line endings." >&2
  return 1 2>/dev/null || exit 1
fi

LLM_CONFIG_FILE="${PROMSEC_LLM_CONFIG_FILE:-$ROOT/llm_config.env}"
if [[ -f "$LLM_CONFIG_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$LLM_CONFIG_FILE"
fi

if [[ -z "${PROMSEC_LLM_BASE_URL:-}" ]]; then
  echo "ERROR: PROMSEC_LLM_BASE_URL is not set. Configure your OpenAI-compatible API endpoint before launch." >&2
  return 1 2>/dev/null || exit 1
fi
if [[ -z "${PROMSEC_LLM_MODEL:-}" ]]; then
  echo "ERROR: PROMSEC_LLM_MODEL is not set. Configure the enforcement model identifier before launch." >&2
  return 1 2>/dev/null || exit 1
fi
export PROMSEC_LLM_BASE_URL
export PROMSEC_LLM_MODEL
export PROMSEC_JUDGE_BASE_URL="${PROMSEC_JUDGE_BASE_URL:-$PROMSEC_LLM_BASE_URL}"
export PROMSEC_JUDGE_MODEL="${PROMSEC_JUDGE_MODEL:-$PROMSEC_LLM_MODEL}"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PROMSEC_REQUIRE_GPU="${PROMSEC_REQUIRE_GPU:-1}"
export PYTHONUNBUFFERED=1
export PYTHONHASHSEED="${PYTHONHASHSEED:-0}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

export PROMSEC_CONFIG="${PROMSEC_CONFIG:-configs/cluster_gpu.yaml}"
export PROMSEC_TMUX_SESSION="${PROMSEC_TMUX_SESSION:-promsec}"
