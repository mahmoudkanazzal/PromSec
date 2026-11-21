"""Functional-similarity evaluation."""

from .functional_similarity import (
    BehavioralContract,
    FunctionalityReport,
    extract_behavioral_contract,
    make_openai_json_completion,
    score_candidate_functionality,
)

__all__ = [
    "BehavioralContract",
    "FunctionalityReport",
    "extract_behavioral_contract",
    "make_openai_json_completion",
    "score_candidate_functionality",
]
