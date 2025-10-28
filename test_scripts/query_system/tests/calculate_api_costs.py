#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepInfra API コスト計算ツール

Embedding & Reranker APIの使用token数とコストを計算します。

料金:
- Qwen3-Embedding-8B: $0.025 / 1M tokens
- Qwen3-Reranker-8B: $0.050 / 1M tokens
"""

import sys
import json
from pathlib import Path
from typing import Dict, List
import requests
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# API料金設定（per 1M tokens）
PRICING = {
    "embedding": 0.025,  # $0.025 / 1M tokens
    "reranker": 0.050    # $0.050 / 1M tokens
}


def test_embedding_api(text: str) -> Dict:
    """
    Embedding APIを呼び出してtoken使用量を取得

    Returns:
        {
            "text": str,
            "tokens": int,
            "cost_usd": float
        }
    """
    api_url = "https://api.deepinfra.com/v1/openai/embeddings"
    api_token = os.getenv("DEEPINFRA_TOKEN") or os.getenv("DEEPINFRA_API_KEY")

    if not api_token:
        raise ValueError("DEEPINFRA_TOKEN or DEEPINFRA_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "input": [text],
        "model": "Qwen/Qwen3-Embedding-8B",
        "encoding_format": "float"
    }

    response = requests.post(api_url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()

    # Extract token usage
    usage = result.get("usage", {})
    tokens = usage.get("total_tokens", 0)

    # Calculate cost
    cost_usd = (tokens / 1_000_000) * PRICING["embedding"]

    return {
        "text": text,
        "tokens": tokens,
        "cost_usd": cost_usd
    }


def test_reranker_api(query: str, documents: List[str]) -> Dict:
    """
    Reranker APIを呼び出してtoken使用量を取得

    Returns:
        {
            "query": str,
            "num_documents": int,
            "tokens": int,
            "cost_usd": float
        }
    """
    api_url = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-8B"
    api_token = os.getenv("DEEPINFRA_TOKEN") or os.getenv("DEEPINFRA_API_KEY")

    if not api_token:
        raise ValueError("DEEPINFRA_TOKEN or DEEPINFRA_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "queries": [query],
        "documents": documents
    }

    response = requests.post(api_url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    result = response.json()

    # Extract token usage
    # Reranker APIは "input_tokens" フィールドを返す
    tokens = result.get("input_tokens", 0)

    # Calculate cost
    cost_usd = (tokens / 1_000_000) * PRICING["reranker"]

    return {
        "query": query,
        "num_documents": len(documents),
        "tokens": tokens,
        "cost_usd": cost_usd
    }


def estimate_query_cost(
    query_main: str,
    query_desc: str,
    stage1_top_k: int = 100,
    stage2_top_k: int = 10
) -> Dict:
    """
    1クエリあたりのコストを推定

    Args:
        query_main: 主要食品名
        query_desc: 説明
        stage1_top_k: Stage 1で取得する候補数
        stage2_top_k: Stage 2で再ランク付けする候補数

    Returns:
        コスト内訳
    """
    print(f"\n{'='*80}")
    print(f"Query: {query_main} | {query_desc}")
    print(f"{'='*80}")

    # Stage 1: Embedding API (2回呼び出し: main-only + full)
    print("\n📊 Stage 1: Embedding API")
    print("-" * 80)

    text_main = f"{query_main}"
    text_full = f"{query_main} {query_desc}" if query_desc else query_main

    print(f"1. Main-only query: '{text_main}'")
    result_main = test_embedding_api(text_main)
    print(f"   Tokens: {result_main['tokens']}, Cost: ${result_main['cost_usd']:.6f}")

    print(f"\n2. Full query: '{text_full}'")
    result_full = test_embedding_api(text_full)
    print(f"   Tokens: {result_full['tokens']}, Cost: ${result_full['cost_usd']:.6f}")

    stage1_tokens = result_main['tokens'] + result_full['tokens']
    stage1_cost = result_main['cost_usd'] + result_full['cost_usd']

    print(f"\n📌 Stage 1 Total: {stage1_tokens} tokens, ${stage1_cost:.6f}")

    # Stage 2: Reranker API
    print(f"\n📊 Stage 2: Reranker API")
    print("-" * 80)

    # Stage 2用のquery作成
    rerank_query = f"query\nname: {query_main}\ndescription: {query_desc}"

    # Stage 2候補を模擬（実際のデータベースから取得される想定）
    sample_candidates = [
        f"candidate\nname: Sample food {i}\ndescription: cooked"
        for i in range(stage2_top_k)
    ]

    print(f"Query: '{rerank_query[:50]}...'")
    print(f"Candidates: {len(sample_candidates)} items")

    result_rerank = test_reranker_api(rerank_query, sample_candidates)
    print(f"Tokens: {result_rerank['tokens']}, Cost: ${result_rerank['cost_usd']:.6f}")

    stage2_tokens = result_rerank['tokens']
    stage2_cost = result_rerank['cost_usd']

    print(f"\n📌 Stage 2 Total: {stage2_tokens} tokens, ${stage2_cost:.6f}")

    # Total
    total_tokens = stage1_tokens + stage2_tokens
    total_cost = stage1_cost + stage2_cost

    print(f"\n{'='*80}")
    print(f"💰 TOTAL COST PER QUERY")
    print(f"{'='*80}")
    print(f"Total Tokens: {total_tokens}")
    print(f"Total Cost: ${total_cost:.6f}")
    print(f"{'='*80}")

    return {
        "query_main": query_main,
        "query_desc": query_desc,
        "stage1": {
            "tokens": stage1_tokens,
            "cost_usd": stage1_cost
        },
        "stage2": {
            "tokens": stage2_tokens,
            "cost_usd": stage2_cost
        },
        "total": {
            "tokens": total_tokens,
            "cost_usd": total_cost
        }
    }


def main():
    """メイン処理"""
    print("=" * 80)
    print("DeepInfra API Cost Calculator")
    print("=" * 80)
    print("\n料金:")
    print(f"  Qwen3-Embedding-8B: ${PRICING['embedding']} / 1M tokens")
    print(f"  Qwen3-Reranker-8B: ${PRICING['reranker']} / 1M tokens")

    # テストクエリ
    test_queries = [
        {"main": "beef steak", "desc": "grilled, sliced"},
        {"main": "chicken breast", "desc": "cooked, boneless, skinless"},
        {"main": "mixed greens", "desc": "raw"},
    ]

    all_results = []

    for query in test_queries:
        result = estimate_query_cost(query["main"], query["desc"])
        all_results.append(result)

    # 平均コスト計算
    avg_tokens = sum(r['total']['tokens'] for r in all_results) / len(all_results)
    avg_cost = sum(r['total']['cost_usd'] for r in all_results) / len(all_results)

    print("\n\n" + "=" * 80)
    print("📊 AVERAGE COST PER QUERY")
    print("=" * 80)
    print(f"Average Tokens: {avg_tokens:.0f}")
    print(f"Average Cost: ${avg_cost:.6f}")
    print(f"\nEstimated cost for 1,000 queries: ${avg_cost * 1000:.2f}")
    print(f"Estimated cost for 10,000 queries: ${avg_cost * 10000:.2f}")
    print(f"Estimated cost for 100,000 queries: ${avg_cost * 100000:.2f}")
    print("=" * 80)

    # 内訳
    print("\n📋 Cost Breakdown:")
    print("-" * 80)
    stage1_pct = (all_results[0]['stage1']['cost_usd'] / all_results[0]['total']['cost_usd']) * 100
    stage2_pct = (all_results[0]['stage2']['cost_usd'] / all_results[0]['total']['cost_usd']) * 100
    print(f"Stage 1 (Embedding): {stage1_pct:.1f}%")
    print(f"Stage 2 (Reranker):  {stage2_pct:.1f}%")
    print("-" * 80)

    # Save results
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "api_cost_analysis.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "pricing": PRICING,
            "test_queries": all_results,
            "average": {
                "tokens": avg_tokens,
                "cost_usd": avg_cost
            },
            "estimates": {
                "1k_queries": avg_cost * 1000,
                "10k_queries": avg_cost * 10000,
                "100k_queries": avg_cost * 100000
            }
        }, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
