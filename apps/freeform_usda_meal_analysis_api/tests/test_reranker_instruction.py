"""Tests for format_reranker_query: the reranker instruction must be BAKED INTO the
query (Qwen3-Reranker format), because the DeepInfra rerank endpoint ignores a separate
top-level 'instruction' payload field (verified empirically 2026-06-02). A whitespace-only
or empty instruction means "raw, no-instruction" and must leave the query untouched.
"""

from apps.freeform_usda_meal_analysis_api.services.deepinfra_service import (
    format_reranker_query,
)


def test_instruction_is_baked_into_query() -> None:
    out = format_reranker_query("sour cream", "Prefer the regular full-fat product.")
    assert out == "Instruct: Prefer the regular full-fat product.\nQuery: sour cream"


def test_no_instruction_returns_bare_query() -> None:
    assert format_reranker_query("sour cream", None) == "sour cream"
    assert format_reranker_query("sour cream", "") == "sour cream"


def test_whitespace_instruction_is_treated_as_raw() -> None:
    # The eval "raw" arm passes a single space to force current-production (no-instruction)
    # behavior; it must NOT wrap the query in an empty Instruct block.
    assert format_reranker_query("sour cream", " ") == "sour cream"
    assert format_reranker_query("sour cream", "   \n  ") == "sour cream"


def test_instruction_is_stripped_before_baking() -> None:
    out = format_reranker_query("chicken", "  prefer cooked  ")
    assert out == "Instruct: prefer cooked\nQuery: chicken"
