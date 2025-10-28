#!/usr/bin/env python
"""
Elasticsearch Word Query APIの速度測定スクリプト
"""

import requests
import time
from typing import List, Dict
import statistics

# テストクエリ
TEST_QUERIES = [
    "chicken",
    "rice",
    "tomato",
    "beef steak",
    "salmon",
    "apple",
    "broccoli",
    "pasta",
    "egg",
    "milk"
]

def measure_elasticsearch_api(
    base_url: str,
    queries: List[str],
    runs_per_query: int = 3
) -> Dict:
    """
    Elasticsearch APIの速度を測定

    Args:
        base_url: APIのベースURL
        queries: テストクエリのリスト
        runs_per_query: クエリごとの実行回数

    Returns:
        測定結果
    """
    all_times = []

    print(f"\n{'='*80}")
    print(f"Testing Elasticsearch API: {base_url}")
    print(f"{'='*80}\n")

    for query in queries:
        query_times = []

        for run in range(runs_per_query):
            start_time = time.time()

            try:
                response = requests.get(
                    f"{base_url}/api/v1/usda/suggest",
                    params={"q": query, "limit": 10},
                    timeout=10
                )
                response.raise_for_status()

                elapsed = (time.time() - start_time) * 1000  # ms
                query_times.append(elapsed)
                all_times.append(elapsed)

                result = response.json()
                num_results = result.get("metadata", {}).get("total_suggestions", 0)

                print(f"  Query: '{query}' | Run {run+1}/{runs_per_query} | {elapsed:.1f}ms | {num_results} results")

            except Exception as e:
                print(f"  Error for '{query}': {e}")
                continue

        if query_times:
            avg_time = statistics.mean(query_times)
            print(f"  Average for '{query}': {avg_time:.1f}ms\n")

    if all_times:
        return {
            "api_type": "Elasticsearch",
            "base_url": base_url,
            "num_queries": len(queries),
            "runs_per_query": runs_per_query,
            "total_requests": len(all_times),
            "min_ms": min(all_times),
            "max_ms": max(all_times),
            "mean_ms": statistics.mean(all_times),
            "median_ms": statistics.median(all_times),
            "stdev_ms": statistics.stdev(all_times) if len(all_times) > 1 else 0
        }

    return {}


def print_summary(result: Dict):
    """結果サマリーを表示"""
    if not result:
        print("\n❌ No results to display")
        return

    print(f"\n{'='*80}")
    print(f"SUMMARY: {result['api_type']} API")
    print(f"{'='*80}")
    print(f"Base URL: {result['base_url']}")
    print(f"Total requests: {result['total_requests']}")
    print(f"\nTiming Statistics:")
    print(f"  Min:    {result['min_ms']:.1f}ms")
    print(f"  Max:    {result['max_ms']:.1f}ms")
    print(f"  Mean:   {result['mean_ms']:.1f}ms")
    print(f"  Median: {result['median_ms']:.1f}ms")
    print(f"  StdDev: {result['stdev_ms']:.1f}ms")
    print(f"{'='*80}\n")


def main():
    """メイン処理"""
    # Elasticsearch USDA Word Query API (port 8004)
    elasticsearch_url = "http://localhost:8004"

    print("\n🚀 Starting API Speed Measurement\n")
    print(f"Test queries: {len(TEST_QUERIES)}")
    print(f"Runs per query: 3")

    # Elasticsearch測定
    es_result = measure_elasticsearch_api(
        base_url=elasticsearch_url,
        queries=TEST_QUERIES,
        runs_per_query=3
    )

    # サマリー表示
    print_summary(es_result)


if __name__ == "__main__":
    main()
