#!/usr/bin/env python3
"""
DeepInfra Reranker Instruction詳細テスト

DeepInfraのネイティブinstructionサポートを検証：
1. instruction有無での精度比較
2. APIに渡されるpayloadの確認
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


RERANKER_INSTRUCTION = """Match USDA food database entries that exactly match the query's food name, cooking/preparation method, and form.

Nutritional values (calories, protein, fat, carbs per 100g) vary significantly based on preparation method, so precise matching is essential for accurate nutrition calculation.

Examples:
- 'grilled chicken' → 'Chicken, grilled' NOT 'Chicken, raw'
- 'caesar salad' → 'Caesar salad, with romaine' NOT 'Caesar dressing'
- 'fried rice' → 'Rice, fried' NOT 'Rice, white, cooked'

Prioritize: Complete phrase match > Preparation method match > Ingredient name similarity"""


TEST_CASES = [
    {
        "query": "grilled chicken breast",
        "expected_idx": 0,
        "documents": [
            "Chicken, broilers or fryers, breast, meat only, cooked, grilled",
            "Chicken, broilers or fryers, breast, meat only, raw",
            "Chicken, broilers or fryers, breast, meat and skin, cooked, roasted",
            "Chicken, broilers or fryers, drumstick, meat only, cooked, grilled",
            "Turkey, breast, meat only, cooked, roasted",
        ]
    },
    {
        "query": "fried rice with vegetables",
        "expected_idx": 0,
        "documents": [
            "Rice, fried, meatless",
            "Rice, white, long-grain, regular, cooked",
            "Rice, brown, long-grain, cooked",
            "Vegetables, mixed, frozen, cooked, boiled",
            "Noodles, egg, cooked",
        ]
    },
    {
        "query": "scrambled eggs",
        "expected_idx": 1,
        "documents": [
            "Egg, whole, raw, fresh",
            "Egg, whole, cooked, scrambled",
            "Egg, whole, cooked, fried",
            "Egg, whole, cooked, hard-boiled",
            "Egg, whole, cooked, poached",
        ]
    },
    {
        "query": "raw salmon sashimi",
        "expected_idx": 0,
        "documents": [
            "Fish, salmon, Atlantic, wild, raw",
            "Fish, salmon, Atlantic, wild, cooked, dry heat",
            "Fish, salmon, pink, canned",
            "Fish, tuna, fresh, bluefin, raw",
            "Fish, salmon, sockeye, cooked",
        ]
    },
    {
        "query": "steamed broccoli",
        "expected_idx": 1,
        "documents": [
            "Broccoli, raw",
            "Broccoli, cooked, boiled, drained, without salt",
            "Broccoli, frozen, chopped, unprepared",
            "Cauliflower, cooked, boiled",
            "Broccoli, chinese, cooked",
        ]
    },
    {
        "query": "vanilla ice cream",
        "expected_idx": 0,
        "documents": [
            "Ice creams, vanilla",
            "Ice creams, chocolate",
            "Frozen yogurts, vanilla, soft-serve",
            "Milk, whole",
            "Cream, heavy whipping",
        ]
    },
    {
        "query": "boiled potato",
        "expected_idx": 1,
        "documents": [
            "Potatoes, flesh and skin, raw",
            "Potatoes, boiled, cooked in skin, flesh, without salt",
            "Potatoes, baked, flesh and skin",
            "Potatoes, mashed, home-prepared",
            "Potatoes, french fried",
        ]
    },
    {
        "query": "miso soup",
        "expected_idx": 0,
        "documents": [
            "Soup, miso, prepared with water",
            "Miso",
            "Soup, vegetable beef, canned",
            "Tofu, firm",
            "Seaweed, wakame, raw",
        ]
    },
]


async def rerank_deepinfra(query, documents, instruction=None, verbose=False):
    """DeepInfra APIで直接リランキング"""
    import httpx

    api_key = os.getenv("DEEPINFRA_API_KEY")
    model = "Qwen/Qwen3-Reranker-8B"
    url = f"https://api.deepinfra.com/v1/inference/{model}"

    payload = {
        "queries": [query],
        "documents": documents
    }
    if instruction is not None:
        payload["instruction"] = instruction

    if verbose:
        print(f"\n📦 Payload sent to DeepInfra:")
        print(f"   queries: {payload['queries']}")
        print(f"   documents: {len(documents)} items")
        print(f"   instruction: {'✅ Included' if instruction else '❌ Not included'}")
        if instruction:
            print(f"   instruction length: {len(instruction)} chars")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        result = response.json()

    scores = result.get("scores", [])
    best_idx = scores.index(max(scores)) if scores else 0

    return best_idx, scores


async def test_with_and_without_instruction():
    """Instruction有無での精度比較"""
    print("\n" + "="*70)
    print("🔬 DeepInfra Reranker: With vs Without Instruction")
    print("="*70)

    # Instructionなしでテスト
    print("\n📊 Test WITHOUT instruction:")
    correct_no_inst = 0
    for case in TEST_CASES:
        best_idx, scores = await rerank_deepinfra(
            query=case["query"],
            documents=case["documents"],
            instruction=None
        )
        is_correct = best_idx == case["expected_idx"]
        if is_correct:
            correct_no_inst += 1
        status = "✅" if is_correct else "❌"
        print(f"   {status} {case['query'][:30]:30} -> [{best_idx}] score={scores[best_idx]:.4f}")

    accuracy_no_inst = correct_no_inst / len(TEST_CASES) * 100
    print(f"\n   📈 Accuracy (no instruction): {correct_no_inst}/{len(TEST_CASES)} ({accuracy_no_inst:.1f}%)")

    # Instructionありでテスト
    print("\n📊 Test WITH instruction:")
    correct_with_inst = 0
    for case in TEST_CASES:
        best_idx, scores = await rerank_deepinfra(
            query=case["query"],
            documents=case["documents"],
            instruction=RERANKER_INSTRUCTION
        )
        is_correct = best_idx == case["expected_idx"]
        if is_correct:
            correct_with_inst += 1
        status = "✅" if is_correct else "❌"
        print(f"   {status} {case['query'][:30]:30} -> [{best_idx}] score={scores[best_idx]:.4f}")

    accuracy_with_inst = correct_with_inst / len(TEST_CASES) * 100
    print(f"\n   📈 Accuracy (with instruction): {correct_with_inst}/{len(TEST_CASES)} ({accuracy_with_inst:.1f}%)")

    # 比較
    print("\n" + "="*70)
    print("📊 COMPARISON")
    print("="*70)
    print(f"   Without instruction: {accuracy_no_inst:.1f}%")
    print(f"   With instruction:    {accuracy_with_inst:.1f}%")

    diff = accuracy_with_inst - accuracy_no_inst
    if diff > 0:
        print(f"   ✅ Instruction improved accuracy by {diff:.1f}%")
    elif diff < 0:
        print(f"   ⚠️ Instruction decreased accuracy by {-diff:.1f}%")
    else:
        print(f"   ➡️ No difference in accuracy")


async def test_payload_detail():
    """Payloadの詳細確認"""
    print("\n" + "="*70)
    print("🔍 DeepInfra API Payload Detail")
    print("="*70)

    # 単一テストケース
    case = TEST_CASES[0]

    print("\n🧪 Test case: grilled chicken breast")

    # Verbose mode でリランキング
    best_idx, scores = await rerank_deepinfra(
        query=case["query"],
        documents=case["documents"],
        instruction=RERANKER_INSTRUCTION,
        verbose=True
    )

    print(f"\n📋 Results:")
    for i, (doc, score) in enumerate(zip(case["documents"], scores)):
        marker = "👑" if i == best_idx else "  "
        expected = "🎯" if i == case["expected_idx"] else "  "
        print(f"   {marker}{expected} [{i}] {score:.4f} - {doc[:50]}...")

    is_correct = best_idx == case["expected_idx"]
    print(f"\n   {'✅ CORRECT' if is_correct else '❌ INCORRECT'}")


async def main():
    print("\n" + "="*70)
    print("🔬 DeepInfra Reranker Instruction Detail Test")
    print("="*70)

    api_key = os.getenv("DEEPINFRA_API_KEY")
    if not api_key:
        print("❌ DEEPINFRA_API_KEY not found!")
        return

    print(f"✅ DEEPINFRA_API_KEY: Found")

    # Test 1: Payload詳細確認
    await test_payload_detail()

    # Test 2: Instruction有無比較
    await test_with_and_without_instruction()

    print("\n" + "="*70)
    print("✅ All tests completed")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
