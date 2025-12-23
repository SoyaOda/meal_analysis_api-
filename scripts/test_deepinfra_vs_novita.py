#!/usr/bin/env python3
"""
DeepInfra vs Novita AI Reranker 包括比較テスト

1. 並列処理性能テスト
2. パイプラインコンテキストでの精度テスト
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


# settings.py と同じ Reranker Instruction
RERANKER_INSTRUCTION = """Match USDA food database entries that exactly match the query's food name, cooking/preparation method, and form.

Nutritional values (calories, protein, fat, carbs per 100g) vary significantly based on preparation method, so precise matching is essential for accurate nutrition calculation.

Examples:
- 'grilled chicken' → 'Chicken, grilled' NOT 'Chicken, raw'
- 'caesar salad' → 'Caesar salad, with romaine' NOT 'Caesar dressing'
- 'fried rice' → 'Rice, fried' NOT 'Rice, white, cooked'

Prioritize: Complete phrase match > Preparation method match > Ingredient name similarity"""


# パイプラインの実際の使用シナリオを模したテストケース
# VLMが画像から抽出した食品クエリ → USDA候補リスト → Rerankerで最適マッチ
PIPELINE_TEST_CASES = [
    {
        "scenario": "朝食: スクランブルエッグ",
        "query": "scrambled eggs",
        "expected_idx": 1,
        "candidates": [
            {"description": "Egg, whole, raw, fresh", "fdc_id": 1},
            {"description": "Egg, whole, cooked, scrambled", "fdc_id": 2},  # 正解
            {"description": "Egg, whole, cooked, fried", "fdc_id": 3},
            {"description": "Egg, whole, cooked, hard-boiled", "fdc_id": 4},
            {"description": "Egg, whole, cooked, poached", "fdc_id": 5},
        ]
    },
    {
        "scenario": "昼食: グリルチキンブレスト",
        "query": "grilled chicken breast",
        "expected_idx": 0,
        "candidates": [
            {"description": "Chicken, broilers or fryers, breast, meat only, cooked, grilled", "fdc_id": 10},  # 正解
            {"description": "Chicken, broilers or fryers, breast, meat only, raw", "fdc_id": 11},
            {"description": "Chicken, broilers or fryers, breast, meat and skin, cooked, roasted", "fdc_id": 12},
            {"description": "Chicken, broilers or fryers, drumstick, meat only, cooked, grilled", "fdc_id": 13},
            {"description": "Turkey, breast, meat only, cooked, roasted", "fdc_id": 14},
        ]
    },
    {
        "scenario": "昼食: 白ご飯",
        "query": "steamed white rice",
        "expected_idx": 0,
        "candidates": [
            {"description": "Rice, white, long-grain, regular, cooked", "fdc_id": 20},  # 正解（steamedはcookedに相当）
            {"description": "Rice, white, long-grain, regular, raw, unenriched", "fdc_id": 21},
            {"description": "Rice, brown, long-grain, cooked", "fdc_id": 22},
            {"description": "Rice, fried, meatless", "fdc_id": 23},
            {"description": "Rice, white, short-grain, cooked", "fdc_id": 24},
        ]
    },
    {
        "scenario": "昼食: チャーハン",
        "query": "fried rice with vegetables",
        "expected_idx": 0,
        "candidates": [
            {"description": "Rice, fried, meatless", "fdc_id": 30},  # 正解
            {"description": "Rice, white, long-grain, regular, cooked", "fdc_id": 31},
            {"description": "Rice, brown, long-grain, cooked", "fdc_id": 32},
            {"description": "Vegetables, mixed, frozen, cooked, boiled, drained, without salt", "fdc_id": 33},
            {"description": "Noodles, egg, cooked, enriched", "fdc_id": 34},
        ]
    },
    {
        "scenario": "夕食: サーモン刺身",
        "query": "raw salmon sashimi",
        "expected_idx": 0,
        "candidates": [
            {"description": "Fish, salmon, Atlantic, wild, raw", "fdc_id": 40},  # 正解
            {"description": "Fish, salmon, Atlantic, wild, cooked, dry heat", "fdc_id": 41},
            {"description": "Fish, salmon, pink, canned, drained solids with bone", "fdc_id": 42},
            {"description": "Fish, tuna, fresh, bluefin, raw", "fdc_id": 43},
            {"description": "Fish, salmon, sockeye, cooked, dry heat", "fdc_id": 44},
        ]
    },
    {
        "scenario": "夕食: 味噌汁",
        "query": "miso soup",
        "expected_idx": 0,
        "candidates": [
            {"description": "Soup, miso, prepared with water", "fdc_id": 50},  # 正解
            {"description": "Miso", "fdc_id": 51},
            {"description": "Soup, vegetable beef, canned, prepared with equal volume water", "fdc_id": 52},
            {"description": "Tofu, firm, prepared with calcium sulfate", "fdc_id": 53},
            {"description": "Seaweed, wakame, raw", "fdc_id": 54},
        ]
    },
    {
        "scenario": "サイド: 蒸しブロッコリー",
        "query": "steamed broccoli",
        "expected_idx": 1,
        "candidates": [
            {"description": "Broccoli, raw", "fdc_id": 60},
            {"description": "Broccoli, cooked, boiled, drained, without salt", "fdc_id": 61},  # 正解
            {"description": "Broccoli, frozen, chopped, unprepared", "fdc_id": 62},
            {"description": "Cauliflower, cooked, boiled, drained, without salt", "fdc_id": 63},
            {"description": "Broccoli, chinese, cooked", "fdc_id": 64},
        ]
    },
    {
        "scenario": "デザート: バニラアイスクリーム",
        "query": "vanilla ice cream",
        "expected_idx": 0,
        "candidates": [
            {"description": "Ice creams, vanilla", "fdc_id": 70},  # 正解
            {"description": "Ice creams, chocolate", "fdc_id": 71},
            {"description": "Frozen yogurts, vanilla, soft-serve", "fdc_id": 72},
            {"description": "Milk, whole, 3.25% milkfat", "fdc_id": 73},
            {"description": "Cream, heavy whipping", "fdc_id": 74},
        ]
    },
]


async def test_parallel_performance(provider_name: str, num_parallel: int = 5):
    """並列処理性能テスト"""
    from apps.freeform_usda_meal_analysis_api.services.reranker_providers import RerankerProviderFactory

    print(f"\n{'='*60}")
    print(f"⏱️  Parallel Performance Test: {provider_name.upper()}")
    print(f"{'='*60}")

    try:
        provider = RerankerProviderFactory.create(provider_name)
    except Exception as e:
        print(f"❌ Failed to create provider: {e}")
        return None, None

    # 並列実行用のタスク準備
    test_cases = PIPELINE_TEST_CASES[:num_parallel]

    async def single_rerank(idx, case):
        start = time.time()
        documents = [c["description"] for c in case["candidates"]]
        best_idx, scores = await provider.rerank(
            query=case["query"],
            documents=documents,
            instruction=RERANKER_INSTRUCTION
        )
        elapsed = time.time() - start
        return idx, elapsed, best_idx, scores

    # 逐次実行テスト
    print(f"\n📊 Sequential execution ({num_parallel} queries)...")
    sequential_start = time.time()
    sequential_results = []
    for i, case in enumerate(test_cases):
        result = await single_rerank(i, case)
        sequential_results.append(result)
        print(f"   Query {i+1}: {result[1]:.2f}s")
    sequential_total = time.time() - sequential_start
    print(f"   Total: {sequential_total:.2f}s")

    # 並列実行テスト
    print(f"\n📊 Parallel execution ({num_parallel} queries)...")
    parallel_start = time.time()
    tasks = [single_rerank(i, case) for i, case in enumerate(test_cases)]
    parallel_results = await asyncio.gather(*tasks)
    parallel_total = time.time() - parallel_start

    individual_times = [r[1] for r in parallel_results]
    print(f"   Individual times: {[f'{t:.2f}s' for t in individual_times]}")
    print(f"   Total: {parallel_total:.2f}s")

    # 結果分析
    speedup = sequential_total / parallel_total if parallel_total > 0 else 0
    is_truly_parallel = speedup > 1.5  # 1.5倍以上なら真の並列

    print(f"\n📈 Results:")
    print(f"   Sequential: {sequential_total:.2f}s")
    print(f"   Parallel:   {parallel_total:.2f}s")
    print(f"   Speedup:    {speedup:.2f}x")

    if is_truly_parallel:
        print(f"   ✅ TRUE PARALLEL EXECUTION")
    else:
        print(f"   ⚠️  SEQUENTIAL-LIKE (speedup < 1.5x)")

    return sequential_total, parallel_total, speedup, is_truly_parallel


async def test_accuracy(provider_name: str):
    """パイプラインコンテキストでの精度テスト"""
    from apps.freeform_usda_meal_analysis_api.services.reranker_providers import RerankerProviderFactory

    print(f"\n{'='*60}")
    print(f"🎯 Accuracy Test: {provider_name.upper()}")
    print(f"{'='*60}")

    try:
        provider = RerankerProviderFactory.create(provider_name)
    except Exception as e:
        print(f"❌ Failed to create provider: {e}")
        return 0, len(PIPELINE_TEST_CASES), []

    correct = 0
    total = len(PIPELINE_TEST_CASES)
    details = []

    for case in PIPELINE_TEST_CASES:
        documents = [c["description"] for c in case["candidates"]]
        best_idx, scores = await provider.rerank(
            query=case["query"],
            documents=documents,
            instruction=RERANKER_INSTRUCTION
        )

        expected_idx = case["expected_idx"]
        is_correct = best_idx == expected_idx

        if is_correct:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        expected_score = scores[expected_idx]
        actual_score = scores[best_idx]
        gap = actual_score - expected_score if not is_correct else 0

        detail = {
            "scenario": case["scenario"],
            "query": case["query"],
            "correct": is_correct,
            "expected": documents[expected_idx][:50],
            "actual": documents[best_idx][:50],
            "expected_score": expected_score,
            "actual_score": actual_score,
            "gap": gap
        }
        details.append(detail)

        print(f"\n{status} {case['scenario']}")
        print(f"   Query: '{case['query']}'")
        print(f"   Expected: [{expected_idx}] {documents[expected_idx][:45]}...")
        print(f"   Actual:   [{best_idx}] {documents[best_idx][:45]}...")
        print(f"   Scores: expected={expected_score:.4f}, actual={actual_score:.4f}", end="")
        if not is_correct:
            print(f" (gap={gap:.4f})")
        else:
            print()

    accuracy = correct / total * 100
    print(f"\n📊 Accuracy: {correct}/{total} ({accuracy:.1f}%)")

    return correct, total, details


async def main():
    print("\n" + "="*70)
    print("🔬 DeepInfra vs Novita AI Comprehensive Comparison")
    print("="*70)

    # 環境変数チェック
    deepinfra_key = os.getenv("DEEPINFRA_API_KEY")
    novita_key = os.getenv("NOVITA_API_KEY")

    print(f"\n✅ DEEPINFRA_API_KEY: {'Found' if deepinfra_key else '❌ Missing'}")
    print(f"✅ NOVITA_API_KEY: {'Found' if novita_key else '❌ Missing'}")

    providers_to_test = []
    if deepinfra_key:
        providers_to_test.append("deepinfra")
    if novita_key:
        providers_to_test.append("novita")

    if not providers_to_test:
        print("\n❌ No API keys found!")
        return

    # 並列処理テスト
    print("\n" + "="*70)
    print("PART 1: PARALLEL PROCESSING TEST")
    print("="*70)

    parallel_results = {}
    for provider in providers_to_test:
        result = await test_parallel_performance(provider, num_parallel=5)
        if result[0] is not None:
            parallel_results[provider] = {
                "sequential": result[0],
                "parallel": result[1],
                "speedup": result[2],
                "is_truly_parallel": result[3]
            }

    # 精度テスト
    print("\n" + "="*70)
    print("PART 2: ACCURACY TEST (Pipeline Context)")
    print("="*70)

    accuracy_results = {}
    for provider in providers_to_test:
        correct, total, details = await test_accuracy(provider)
        accuracy_results[provider] = {
            "correct": correct,
            "total": total,
            "accuracy": correct / total * 100,
            "details": details
        }

    # 最終サマリー
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)

    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│                    PARALLEL PROCESSING                          │")
    print("├──────────────┬──────────────┬──────────────┬──────────────────┤")
    print("│ Provider     │ Sequential   │ Parallel     │ Speedup          │")
    print("├──────────────┼──────────────┼──────────────┼──────────────────┤")

    for provider, result in parallel_results.items():
        status = "✅ TRUE" if result["is_truly_parallel"] else "⚠️ FAKE"
        print(f"│ {provider:12} │ {result['sequential']:10.2f}s │ {result['parallel']:10.2f}s │ {result['speedup']:.2f}x {status:6} │")

    print("└──────────────┴──────────────┴──────────────┴──────────────────┘")

    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│                         ACCURACY                                │")
    print("├──────────────┬──────────────┬──────────────────────────────────┤")
    print("│ Provider     │ Correct      │ Accuracy                         │")
    print("├──────────────┼──────────────┼──────────────────────────────────┤")

    for provider, result in accuracy_results.items():
        bar = "█" * int(result["accuracy"] / 10) + "░" * (10 - int(result["accuracy"] / 10))
        print(f"│ {provider:12} │ {result['correct']}/{result['total']:11} │ {bar} {result['accuracy']:5.1f}% │")

    print("└──────────────┴──────────────┴──────────────────────────────────┘")

    # 推奨事項
    print("\n📋 RECOMMENDATION:")

    best_parallel = max(parallel_results.items(), key=lambda x: x[1]["speedup"]) if parallel_results else None
    best_accuracy = max(accuracy_results.items(), key=lambda x: x[1]["accuracy"]) if accuracy_results else None

    if best_parallel and best_accuracy:
        if best_parallel[0] == best_accuracy[0]:
            print(f"   🏆 {best_parallel[0].upper()} is best for both parallel processing and accuracy")
        else:
            print(f"   ⚡ Best for parallel: {best_parallel[0].upper()} ({best_parallel[1]['speedup']:.2f}x speedup)")
            print(f"   🎯 Best for accuracy: {best_accuracy[0].upper()} ({best_accuracy[1]['accuracy']:.1f}%)")

            # トレードオフ分析
            if best_parallel[1]["is_truly_parallel"] and not parallel_results.get(best_accuracy[0], {}).get("is_truly_parallel", True):
                print(f"\n   ⚠️  Trade-off: {best_accuracy[0]} has better accuracy but fake parallel processing")
                print(f"   💡 Consider: Use {best_parallel[0]} for production (speed) or {best_accuracy[0]} for accuracy-critical cases")

    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
