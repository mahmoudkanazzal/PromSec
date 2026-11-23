#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PATH="$HOME/.local/bin:$PATH"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "ERROR: $ROOT/.venv is missing. Run: bash scripts/setup_venv.sh" >&2
  return 1 2>/dev/null || exit 1
fi
# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

# API key: OPENAI_API_KEY if already exported, otherwise the first line of api_key.txt.
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  KEY_FILE="${PROMSEC_API_KEY_FILE:-$ROOT/api_key.txt}"
  if [[ ! -s "$KEY_FILE" ]]; then
    echo "ERROR: set OPENAI_API_KEY or put the API key in $KEY_FILE" >&2
    return 1 2>/dev/null || exit 1
  fi
  OPENAI_API_KEY="$(head -n 1 "$KEY_FILE" | tr -d '\r\n')"
  if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "ERROR: the first line of $KEY_FILE is empty." >&2
    return 1 2>/dev/null || exit 1
  fi
fi
export OPENAI_API_KEY

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
  echo "ERROR: PROMSEC_LLM_MODEL is not set. Set the LLM model name before launch." >&2
  return 1 2>/dev/null || exit 1
fi
export PROMSEC_LLM_BASE_URL
export PROMSEC_LLM_MODEL
export PROMSEC_JUDGE_BASE_URL="${PROMSEC_JUDGE_BASE_URL:-$PROMSEC_LLM_BASE_URL}"
export PROMSEC_JUDGE_MODEL="${PROMSEC_JUDGE_MODEL:-$PROMSEC_LLM_MODEL}"

export PYTHONUNBUFFERED=1
export PYTHONHASHSEED="${PYTHONHASHSEED:-0}"
export TOKENIZERS_PARALLELISM="${TOKENIZERS_PARALLELISM:-false}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

export PROMSEC_CONFIG="${PROMSEC_CONFIG:-configs/default.yaml}"
# One tmux session per configuration, e.g. promsec_default, promsec_smoke, promsec_promsec_s.
export PROMSEC_TMUX_SESSION="${PROMSEC_TMUX_SESSION:-promsec_$(basename "$PROMSEC_CONFIG" .yaml)}"
