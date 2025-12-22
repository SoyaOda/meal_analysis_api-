#!/usr/bin/env python3
"""
Reranker Instruction 効果検証スクリプト

instruction埋め込みの有無でReranker精度がどう変わるかを検証
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


# USDA食材マッチング用のinstruction（settings.pyと同じ）
USDA_RERANKER_INSTRUCTION = """Match USDA food database entries that exactly match the query's food name, cooking/preparation method, and form.

Nutritional values (calories, protein, fat, carbs per 100g) vary significantly based on preparation method, so precise matching is essential for accurate nutrition calculation.

Examples:
- 'grilled chicken' → 'Chicken, grilled' NOT 'Chicken, raw'
- 'caesar salad' → 'Caesar salad, with romaine' NOT 'Caesar dressing'
- 'fried rice' → 'Rice, fried' NOT 'Rice, white, cooked'

Prioritize: Complete phrase match > Preparation method match > Ingredient name similarity"""


# テストケース: クエリと期待される正解（USDA形式）
TEST_CASES = [
    {
        "query": "grilled chicken breast",
        "expected_best": "Chicken, broilers or fryers, breast, meat only, cooked, grilled",
        "documents": [
            "Chicken, broilers or fryers, breast, meat only, cooked, grilled",
            "Chicken, broilers or fryers, breast, meat only, raw",
            "Chicken, broilers or fryers, breast, meat and skin, cooked, roasted",
            "Chicken, broilers or fryers, drumstick, meat only, cooked, grilled",
            "Turkey, breast, meat only, cooked, roasted",
        ]
    },
    {
        "query": "fried rice",
        "expected_best": "Rice, fried, meatless",
        "documents": [
            "Rice, white, long-grain, regular, cooked",
            "Rice, fried, meatless",
            "Rice, brown, long-grain, cooked",
            "Rice, white, short-grain, cooked",
            "Noodles, egg, cooked, enriched",
        ]
    },
    {
        "query": "steamed broccoli",
        "expected_best": "Broccoli, cooked, boiled, drained, without salt",
        "documents": [
            "Broccoli, raw",
            "Broccoli, cooked, boiled, drained, without salt",
            "Broccoli, frozen, chopped, unprepared",
            "Cauliflower, cooked, boiled, drained, without salt",
            "Spinach, cooked, boiled, drained, without salt",
        ]
    },
    {
        "query": "scrambled eggs",
        "expected_best": "Egg, whole, cooked, scrambled",
        "documents": [
            "Egg, whole, raw, fresh",
            "Egg, whole, cooked, scrambled",
            "Egg, whole, cooked, fried",
            "Egg, whole, cooked, hard-boiled",
            "Egg, whole, cooked, poached",
        ]
    },
    {
        "query": "raw salmon",
        "expected_best": "Fish, salmon, Atlantic, wild, raw",
        "documents": [
            "Fish, salmon, Atlantic, wild, raw",
            "Fish, salmon, Atlantic, wild, cooked, dry heat",
            "Fish, salmon, pink, canned, drained solids with bone",
            "Fish, tuna, fresh, bluefin, raw",
            "Fish, salmon, sockeye, cooked, dry heat",
        ]
    },
]


async def test_reranker_with_instruction():
    """instruction付きでRerankerテスト"""
    from apps.freeform_usda_meal_analysis_api.services.reranker_providers import RerankerProviderFactory

    provider = RerankerProviderFactory.create("novita")

    print("\n" + "="*70)
    print("🧪 TEST: Reranker WITH Instruction")
    print("="*70)

    correct = 0
    total = len(TEST_CASES)

    for i, case in enumerate(TEST_CASES):
        query = case["query"]
        documents = case["documents"]
        expected = case["expected_best"]

        best_idx, scores = await provider.rerank(
            query=query,
            documents=documents,
            instruction=USDA_RERANKER_INSTRUCTION
        )

        actual_best = documents[best_idx]
        is_correct = actual_best == expected

        if is_correct:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        print(f"\n{status} Test {i+1}: '{query}'")
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual_best}")
        print(f"   Scores:   {[f'{s:.4f}' for s in scores]}")

    accuracy = correct / total * 100
    print(f"\n📊 With Instruction: {correct}/{total} correct ({accuracy:.1f}%)")

    return correct, total


async def test_reranker_without_instruction():
    """instruction無しでRerankerテスト"""
    from apps.freeform_usda_meal_analysis_api.services.reranker_providers import RerankerProviderFactory

    provider = RerankerProviderFactory.create("novita")

    print("\n" + "="*70)
    print("🧪 TEST: Reranker WITHOUT Instruction")
    print("="*70)

    correct = 0
    total = len(TEST_CASES)

    for i, case in enumerate(TEST_CASES):
        query = case["query"]
        documents = case["documents"]
        expected = case["expected_best"]

        # instructionなしで実行
        best_idx, scores = await provider.rerank(
            query=query,
            documents=documents,
            instruction=None  # No instruction
        )

        actual_best = documents[best_idx]
        is_correct = actual_best == expected

        if is_correct:
            correct += 1
            status = "✅"
        else:
            status = "❌"

        print(f"\n{status} Test {i+1}: '{query}'")
        print(f"   Expected: {expected}")
        print(f"   Actual:   {actual_best}")
        print(f"   Scores:   {[f'{s:.4f}' for s in scores]}")

    accuracy = correct / total * 100
    print(f"\n📊 Without Instruction: {correct}/{total} correct ({accuracy:.1f}%)")

    return correct, total


async def main():
    print("\n" + "="*70)
    print("🔬 Reranker Instruction Effect Verification")
    print("="*70)

    # 環境変数チェック
    novita_key = os.getenv("NOVITA_API_KEY")
    if not novita_key:
        print("❌ NOVITA_API_KEY not set!")
        return
    print(f"✅ NOVITA_API_KEY: {novita_key[:20]}...")

    # Without instruction
    without_correct, without_total = await test_reranker_without_instruction()

    # With instruction
    with_correct, with_total = await test_reranker_with_instruction()

    # 結果比較
    print("\n" + "="*70)
    print("📈 COMPARISON RESULTS")
    print("="*70)

    without_acc = without_correct / without_total * 100
    with_acc = with_correct / with_total * 100
    improvement = with_acc - without_acc

    print(f"\n  Without Instruction: {without_correct}/{without_total} ({without_acc:.1f}%)")
    print(f"  With Instruction:    {with_correct}/{with_total} ({with_acc:.1f}%)")
    print(f"\n  Improvement: {improvement:+.1f}%")

    if improvement > 0:
        print("\n  🎉 Instruction embedding IMPROVES accuracy!")
    elif improvement < 0:
        print("\n  ⚠️ Instruction embedding DECREASES accuracy")
    else:
        print("\n  ➡️ No significant difference")

    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
