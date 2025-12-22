#!/usr/bin/env python3
"""
Reranker 詳細分析スクリプト

各フォーマットでのスコア分布を詳細に分析
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


INSTRUCTION = "Match USDA food entries by exact preparation method (grilled, raw, fried, steamed, etc.)"

# より多くのテストケース
TEST_CASES = [
    {
        "query": "grilled chicken breast",
        "expected_idx": 0,
        "documents": [
            "Chicken, broilers or fryers, breast, meat only, cooked, grilled",  # 正解
            "Chicken, broilers or fryers, breast, meat only, raw",
            "Chicken, broilers or fryers, breast, meat and skin, cooked, roasted",
            "Chicken, broilers or fryers, drumstick, meat only, cooked, grilled",
        ]
    },
    {
        "query": "fried rice",
        "expected_idx": 1,
        "documents": [
            "Rice, white, long-grain, regular, cooked",
            "Rice, fried, meatless",  # 正解
            "Rice, brown, long-grain, cooked",
            "Noodles, egg, cooked, enriched",
        ]
    },
    {
        "query": "scrambled eggs",
        "expected_idx": 1,
        "documents": [
            "Egg, whole, raw, fresh",
            "Egg, whole, cooked, scrambled",  # 正解
            "Egg, whole, cooked, fried",
            "Egg, whole, cooked, poached",
        ]
    },
    {
        "query": "raw salmon sashimi",
        "expected_idx": 0,
        "documents": [
            "Fish, salmon, Atlantic, wild, raw",  # 正解
            "Fish, salmon, Atlantic, wild, cooked, dry heat",
            "Fish, salmon, pink, canned, drained solids with bone",
            "Fish, tuna, fresh, bluefin, raw",
        ]
    },
    {
        "query": "boiled potato",
        "expected_idx": 1,
        "documents": [
            "Potatoes, flesh and skin, raw",
            "Potatoes, boiled, cooked in skin, flesh, without salt",  # 正解
            "Potatoes, baked, flesh and skin, without salt",
            "Potatoes, mashed, home-prepared, whole milk and butter added",
        ]
    },
    {
        "query": "steamed white rice",
        "expected_idx": 0,
        "documents": [
            "Rice, white, long-grain, regular, cooked",  # 正解（steamedはcookedに近い）
            "Rice, white, long-grain, regular, raw",
            "Rice, brown, long-grain, cooked",
            "Rice, fried, meatless",
        ]
    },
]


async def test_format(format_func, format_name: str):
    """特定フォーマットでテスト実行"""
    from apps.freeform_usda_meal_analysis_api.core.http_client import get_async_client

    client = get_async_client()
    api_key = os.getenv("NOVITA_API_KEY")
    base_url = "https://api.novita.ai/openai/v1"
    model_id = "qwen/qwen3-reranker-8b"

    print(f"\n{'='*60}")
    print(f"📋 Format: {format_name}")
    print(f"{'='*60}")

    correct = 0
    total = len(TEST_CASES)
    score_improvements = []

    for i, case in enumerate(TEST_CASES):
        query = case["query"]
        documents = case["documents"]
        expected_idx = case["expected_idx"]

        # フォーマット適用
        formatted_query = format_func(query, INSTRUCTION)

        payload = {
            "model": model_id,
            "query": formatted_query,
            "documents": documents,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = await client.post(f"{base_url}/rerank", json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()

        results = result.get("results", [])
        scores = [0.0] * len(documents)
        for item in results:
            idx = item.get("index", 0)
            score = item.get("relevance_score", 0.0)
            if idx < len(scores):
                scores[idx] = score

        best_idx = scores.index(max(scores)) if scores else 0
        is_correct = best_idx == expected_idx

        if is_correct:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        # 正解のスコアと最高スコアの差
        expected_score = scores[expected_idx]
        best_score = max(scores)
        gap = best_score - expected_score if not is_correct else 0

        print(f"\n{status} Test {i+1}: '{query}'")
        print(f"   Expected: [{expected_idx}] {documents[expected_idx][:50]}...")
        print(f"   Actual:   [{best_idx}] {documents[best_idx][:50]}...")
        print(f"   Scores: ", end="")
        for j, s in enumerate(scores):
            marker = "🎯" if j == expected_idx else ("👑" if j == best_idx else "  ")
            print(f"{marker}[{j}]:{s:.3f} ", end="")
        print()

        if not is_correct:
            print(f"   ⚠️  Gap: {gap:.3f} (expected needs +{gap:.3f} to win)")

    accuracy = correct / total * 100
    print(f"\n📊 Result: {correct}/{total} ({accuracy:.1f}%)")

    return correct, total, accuracy


async def main():
    print("\n" + "="*70)
    print("🔬 Reranker Detailed Score Analysis")
    print("="*70)

    # 各フォーマット定義
    formats = [
        (lambda q, i: q, "No instruction (baseline)"),
        (lambda q, i: f"<Instruct>: {i}\n<Query>: {q}", "Qwen3 official tags"),
        (lambda q, i: f"[Task: {i}] {q}", "Inline [Task:] format"),
        (lambda q, i: f"Instruction: {i}\nQuery: {q}", "Instruction/Query format"),
        (lambda q, i: f"{i}. Search for: {q}", "Natural language format"),
    ]

    results = []
    for format_func, format_name in formats:
        correct, total, accuracy = await test_format(format_func, format_name)
        results.append((format_name, correct, total, accuracy))

    # 最終サマリー
    print("\n" + "="*70)
    print("📈 FINAL SUMMARY")
    print("="*70)

    results.sort(key=lambda x: x[3], reverse=True)
    for name, correct, total, accuracy in results:
        bar = "█" * int(accuracy / 10) + "░" * (10 - int(accuracy / 10))
        status = "🏆" if accuracy == results[0][3] else "  "
        print(f"{status} {bar} {accuracy:5.1f}% | {name}")

    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
