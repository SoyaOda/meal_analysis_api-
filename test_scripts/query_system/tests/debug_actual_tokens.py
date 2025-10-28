#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
実際のReranker API呼び出しのデバッグ

実際に送信されるテキストとAPIレスポンスのトークン情報を確認します。
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline
from src.preprocessing.text_normalizer import build_rerank_text


def debug_actual_api_calls():
    """実際のパイプライン実行でRerankerに送られるテキストを確認"""

    print("=" * 80)
    print("Actual Reranker API Call Debug")
    print("=" * 80)

    # Initialize pipeline
    index_dir = project_root / "data"
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=10  # 少数の候補でテスト
    )

    print(f"\n{pipeline}\n")

    # Reset stats
    pipeline.reset_usage_stats()

    # Test query
    query_main = "chicken breast"
    query_desc = "cooked, boneless, skinless"

    print(f"\nTest Query:")
    print(f"  Main: {query_main}")
    print(f"  Desc: {query_desc}")
    print()

    # Stage 1: Get candidates
    print("Stage 1: Retrieving candidates...")
    candidates = pipeline.searcher.search(
        query_main=query_main,
        query_descriptors=query_desc,
        top_k=10
    )
    print(f"Retrieved {len(candidates)} candidates\n")

    # Build rerank texts (same as pipeline does)
    from src.preprocessing.text_normalizer import normalize_compound_words
    normalized_query_main = normalize_compound_words(query_main)

    query_text = build_rerank_text(normalized_query_main, query_desc, is_query=True)

    print("=" * 80)
    print("Reranker Input - Query Text")
    print("=" * 80)
    print(query_text)
    print(f"\nQuery Text Length: {len(query_text)} characters")
    print()

    # Build candidate texts
    candidate_texts = [
        build_rerank_text(cand['main_name'], cand['descriptors'], is_query=False)
        for cand in candidates
    ]

    print("=" * 80)
    print("Reranker Input - Candidate Texts (First 3)")
    print("=" * 80)
    for i, (cand, text) in enumerate(zip(candidates[:3], candidate_texts[:3]), 1):
        print(f"\nCandidate {i}:")
        print(f"  Original: {cand['description']}")
        print(f"  Rerank Text:")
        print(f"    {text.replace(chr(10), chr(10) + '    ')}")
        print(f"  Length: {len(text)} characters")

    # Calculate total characters
    total_chars = len(query_text) + sum(len(t) for t in candidate_texts)
    avg_candidate_chars = sum(len(t) for t in candidate_texts) / len(candidate_texts)

    print("\n" + "=" * 80)
    print("Character Count Summary")
    print("=" * 80)
    print(f"Query Text: {len(query_text)} characters")
    print(f"Candidate Texts Total: {sum(len(t) for t in candidate_texts)} characters")
    print(f"Average per Candidate: {avg_candidate_chars:.1f} characters")
    print(f"Total Input: {total_chars} characters")
    print()

    # Call Reranker API directly with instrumentation
    print("=" * 80)
    print("Calling Reranker API...")
    print("=" * 80)

    import requests
    import os

    api_url = f"https://api.deepinfra.com/v1/inference/{pipeline.reranker.model_name}"
    api_token = os.getenv("DEEPINFRA_TOKEN") or os.getenv("DEEPINFRA_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "queries": [query_text],
        "documents": candidate_texts,
        "instruction": pipeline.reranker.task_instruction
    }

    # Add instruction length
    print(f"Instruction Length: {len(pipeline.reranker.task_instruction)} characters")
    print()

    response = requests.post(api_url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()

    print("API Response:")
    print("-" * 80)
    print(f"Response Keys: {list(result.keys())}")

    if "input_tokens" in result:
        print(f"\n✅ input_tokens: {result['input_tokens']:,}")

    if "inference_status" in result:
        print(f"\n✅ inference_status:")
        for key, value in result["inference_status"].items():
            print(f"   {key}: {value}")

    # Calculate tokens per candidate
    if "input_tokens" in result:
        total_tokens = result["input_tokens"]
        tokens_per_candidate = total_tokens / len(candidate_texts)
        chars_per_token = total_chars / total_tokens

        print("\n" + "=" * 80)
        print("Token Analysis")
        print("=" * 80)
        print(f"Total Tokens: {total_tokens:,}")
        print(f"Tokens per Candidate: {tokens_per_candidate:.1f}")
        print(f"Characters per Token: {chars_per_token:.2f}")
        print()

        # Cost calculation
        cost_per_1m = 0.050
        cost = (total_tokens / 1_000_000) * cost_per_1m
        print(f"Cost for this query (10 candidates): ${cost:.6f}")

        # Extrapolate to 100 candidates
        estimated_tokens_100 = (total_tokens / 10) * 100
        estimated_cost_100 = (estimated_tokens_100 / 1_000_000) * cost_per_1m
        print(f"\nExtrapolated to 100 candidates:")
        print(f"  Tokens: {estimated_tokens_100:,.0f}")
        print(f"  Cost: ${estimated_cost_100:.6f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        debug_actual_api_calls()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
