"""Tests for E5 embedding A/B plumbing:

1. format_embedding_query / format_embedding_document — per-model conventions so a fair
   A/B applies the RIGHT prompt scheme to each model (Qwen3 instruct prefix / EmbeddingGemma
   task format / bge-m3 & others plain). Documents stay plain except EmbeddingGemma.
2. VLMCache disk persistence — when VLM_CACHE_DIR is set, entries survive a process restart
   so the SAME frozen VLM output can be shared across embedding-arm servers (clean retrieval
   isolation). Without it, behavior is memory-only (production default).
"""

import asyncio

from apps.freeform_usda_meal_analysis_api.services.deepinfra_service import (
    format_embedding_document,
    format_embedding_query,
)
from apps.freeform_usda_meal_analysis_api.core.vlm_cache import VLMCache


# ---------- format_embedding_query ----------


def test_qwen3_query_gets_instruct_prefix() -> None:
    out = format_embedding_query(
        "chicken", "Qwen/Qwen3-Embedding-8B", "Match food names"
    )
    assert out == "Instruct: Match food names\nQuery: chicken"
    # 0.6B shares the family convention
    out06 = format_embedding_query(
        "rice", "Qwen/Qwen3-Embedding-0.6B", "Match food names"
    )
    assert out06 == "Instruct: Match food names\nQuery: rice"


def test_qwen3_without_instruction_is_bare() -> None:
    assert (
        format_embedding_query("chicken", "Qwen/Qwen3-Embedding-8B", None) == "chicken"
    )
    assert (
        format_embedding_query("chicken", "Qwen/Qwen3-Embedding-8B", "  ") == "chicken"
    )


def test_bge_m3_ignores_instruction_and_stays_plain() -> None:
    # bge-m3 is NOT instruct-aware; a Qwen-style prefix would hurt recall, so it must be bare
    # even when an instruction is configured.
    assert (
        format_embedding_query("chicken", "BAAI/bge-m3", "Match food names")
        == "chicken"
    )


def test_embeddinggemma_query_uses_task_format() -> None:
    out = format_embedding_query(
        "chicken", "google/embeddinggemma-300m", "Match food names"
    )
    assert out == "task: search result | query: chicken"


# ---------- format_embedding_document ----------


def test_documents_plain_for_qwen_and_bge() -> None:
    assert (
        format_embedding_document("Chicken, raw", "Qwen/Qwen3-Embedding-8B")
        == "Chicken, raw"
    )
    assert format_embedding_document("Chicken, raw", "BAAI/bge-m3") == "Chicken, raw"


def test_embeddinggemma_document_uses_text_format() -> None:
    out = format_embedding_document("Chicken, raw", "google/embeddinggemma-300m")
    assert out == "title: none | text: Chicken, raw"


# ---------- VLMCache disk persistence ----------


def test_vlm_cache_disk_persists_across_restart(tmp_path) -> None:
    img = b"\x89PNG fake image bytes"
    prompt = "analyze this meal"
    model_id = "openrouter:google/gemini-3-flash-preview"
    response = {"dishes": [{"name": "salad"}]}
    usage = {"prompt_tokens": 10, "completion_tokens": 5, "cached": False}
    cache_dir = str(tmp_path / "vlm_cache")

    async def scenario():
        # 1st process: write
        c1 = VLMCache(cache_dir=cache_dir)
        assert await c1.get(img, prompt, model_id) is None  # cold miss
        await c1.set(img, prompt, model_id, response, usage)

        # 2nd process (fresh in-memory cache, same disk dir): must HIT from disk
        c2 = VLMCache(cache_dir=cache_dir)
        hit = await c2.get(img, prompt, model_id)
        assert hit is not None
        got_response, got_usage = hit
        assert got_response == response
        assert got_usage["prompt_tokens"] == 10

    asyncio.run(scenario())


def test_vlm_cache_memory_only_without_dir(tmp_path) -> None:
    img = b"img"
    prompt = "p"
    model_id = "m"

    async def scenario():
        c1 = VLMCache()  # no disk
        await c1.set(img, prompt, model_id, {"dishes": []}, {"cached": False})
        # a fresh memory-only cache does NOT see the prior entry (no disk persistence)
        c2 = VLMCache()
        assert await c2.get(img, prompt, model_id) is None

    asyncio.run(scenario())
