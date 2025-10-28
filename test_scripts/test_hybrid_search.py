#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hybrid Search API テストスクリプト

3つのモード（fast, accurate, hybrid）で同じクエリを検索して比較
"""

import requests
import json
from typing import Dict, List

# API URL
BASE_URL = "http://localhost:8006"

# テストクエリ
TEST_QUERIES = [
    "chicken breast grilled",
    "rice cooked",
    "tomato raw",
    "beef steak",
    "salmon"
]


def test_retrieval_mode(query: str, mode: str, top_k: int = 10) -> Dict:
    """
    指定モードで検索を実行

    Args:
        query: 検索クエリ
        mode: fast | accurate | hybrid
        top_k: 取得件数

    Returns:
        APIレスポンス
    """
    url = f"{BASE_URL}/api/v1/retrieve"
    params = {
        "q": query,
        "mode": mode,
        "top_k": top_k,
        "include_nutrition": True,
        "debug": True
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def compare_results(query: str):
    """3つのモードで結果を比較"""
    print(f"\n{'='*80}")
    print(f"🔍 Query: '{query}'")
    print(f"{'='*80}\n")

    modes = ["fast", "accurate", "hybrid"]
    results = {}

    # 各モードで検索
    for mode in modes:
        print(f"Testing {mode} mode...")
        try:
            result = test_retrieval_mode(query, mode, top_k=5)
            results[mode] = result
            print(f"✅ {mode}: {len(result['results'])} results in {result['metadata']['search_time_ms']}ms")
        except Exception as e:
            print(f"❌ {mode}: Error - {e}")
            results[mode] = None

    # 結果の比較
    print(f"\n📊 Results Comparison:")
    print(f"{'-'*80}")

    # 各モードのトップ3を表示
    for mode in modes:
        if results[mode] and results[mode]['results']:
            print(f"\n{mode.upper()} Mode - Top 3:")
            for i, item in enumerate(results[mode]['results'][:3], 1):
                score_info = f"Score: {item['score']:.4f}"

                # Hybridモードの場合、コンポーネントスコアも表示
                if mode == "hybrid" and "component_scores" in item:
                    comp = item["component_scores"]
                    score_info += f" (BM25: {comp.get('bm25', 0):.4f}, Vector: {comp.get('vector', 0):.4f}, RRF: {comp.get('rrf', 0):.4f})"

                print(f"  {i}. {item['name']}")
                print(f"     {score_info}")
                print(f"     Calories: {item['nutrition_per_100g']['calories']} kcal/100g")

    # デバッグ情報の比較
    if all(results[mode] for mode in modes):
        print(f"\n⚙️ Algorithm Details:")
        for mode in modes:
            if 'metadata' in results[mode]:
                algo = results[mode]['metadata'].get('algorithm', 'N/A')
                print(f"  {mode}: {algo}")

            if 'debug_info' in results[mode]:
                debug = results[mode]['debug_info']
                if mode == "hybrid" and 'bm25_weight' in debug:
                    print(f"    Weights: BM25={debug['bm25_weight']}, Vector={debug['vector_weight']}, RRF_k={debug['rrf_k']}")


def main():
    """メイン処理"""
    print("\n" + "="*80)
    print("🚀 Hybrid Search API Test")
    print("="*80)
    print(f"Testing {len(TEST_QUERIES)} queries with 3 modes (fast, accurate, hybrid)")
    print("="*80)

    for query in TEST_QUERIES:
        try:
            compare_results(query)
        except Exception as e:
            print(f"\n❌ Error testing query '{query}': {e}")

    print("\n" + "="*80)
    print("✅ Test completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
