#!/usr/bin/env python3
"""
Reranker Instruction フォーマット比較テスト

異なるinstruction埋め込みフォーマットの効果を検証
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


# シンプルなinstruction
SIMPLE_INSTRUCTION = "Match USDA food entries by exact preparation method (grilled, raw, fried, etc.)"

# 詳細instruction
DETAILED_INSTRUCTION = """Match USDA food database entries that exactly match the query's food name, cooking/preparation method, and form.
Prioritize: Complete phrase match > Preparation method match > Ingredient name similarity"""


# テストケース
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


class TestRerankerFormats:
    def __init__(self):
        from apps.freeform_usda_meal_analysis_api.services.reranker_providers import NovitaRerankerProvider
        self.api_key = os.getenv("NOVITA_API_KEY")
        self.base_url = "https://api.novita.ai/openai/v1"
        self.model_id = "qwen/qwen3-reranker-8b"

        from apps.freeform_usda_meal_analysis_api.core.http_client import get_async_client
        self.client = get_async_client()

    async def rerank_with_format(
        self,
        query: str,
        documents: list,
        format_type: str,
        instruction: str = None
    ):
        """異なるフォーマットでリランキング"""
        url = f"{self.base_url}/rerank"

        # フォーマットタイプに応じてqueryを整形
        if format_type == "none":
            formatted_query = query
        elif format_type == "qwen3_tags":
            # Qwen3公式フォーマット
            formatted_query = f"<Instruct>: {instruction}\n<Query>: {query}"
        elif format_type == "simple_prefix":
            # シンプルなプレフィックス
            formatted_query = f"{instruction}\n\nQuery: {query}"
        elif format_type == "inline":
            # インライン
            formatted_query = f"[Task: {instruction}] {query}"
        elif format_type == "context":
            # コンテキスト形式
            formatted_query = f"Context: {instruction}\nFind: {query}"
        else:
            formatted_query = query

        payload = {
            "model": self.model_id,
            "query": formatted_query,
            "documents": documents,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = await self.client.post(url, json=payload, headers=headers)
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
        return best_idx, scores

    async def run_test(self, format_type: str, instruction: str = None):
        """特定フォーマットで全テスト実行"""
        correct = 0
        total = len(TEST_CASES)

        for case in TEST_CASES:
            best_idx, scores = await self.rerank_with_format(
                query=case["query"],
                documents=case["documents"],
                format_type=format_type,
                instruction=instruction
            )
            if case["documents"][best_idx] == case["expected_best"]:
                correct += 1

        return correct, total


async def main():
    print("\n" + "="*70)
    print("🔬 Reranker Instruction Format Comparison")
    print("="*70)

    tester = TestRerankerFormats()

    formats_to_test = [
        ("none", None, "No instruction"),
        ("qwen3_tags", SIMPLE_INSTRUCTION, "Qwen3 <Instruct>/<Query> tags"),
        ("simple_prefix", SIMPLE_INSTRUCTION, "Simple prefix format"),
        ("inline", SIMPLE_INSTRUCTION, "Inline [Task:] format"),
        ("context", SIMPLE_INSTRUCTION, "Context/Find format"),
        ("qwen3_tags", DETAILED_INSTRUCTION, "Qwen3 tags + detailed"),
        ("simple_prefix", DETAILED_INSTRUCTION, "Simple prefix + detailed"),
    ]

    results = []

    for format_type, instruction, description in formats_to_test:
        print(f"\n🧪 Testing: {description}...")
        correct, total = await tester.run_test(format_type, instruction)
        accuracy = correct / total * 100
        results.append((description, correct, total, accuracy))
        print(f"   Result: {correct}/{total} ({accuracy:.1f}%)")

    # 結果サマリー
    print("\n" + "="*70)
    print("📊 RESULTS SUMMARY")
    print("="*70)

    # 精度順にソート
    results.sort(key=lambda x: x[3], reverse=True)

    for desc, correct, total, accuracy in results:
        bar = "█" * int(accuracy / 10) + "░" * (10 - int(accuracy / 10))
        print(f"  {bar} {accuracy:5.1f}% | {desc}")

    best = results[0]
    print(f"\n🏆 Best format: {best[0]} ({best[3]:.1f}%)")

    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
