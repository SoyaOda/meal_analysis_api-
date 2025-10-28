#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VLMプロンプトバージョン比較テスト
異なるプロンプトで同じ画像を分析し、結果を比較
"""

import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.freeform_usda_meal_analysis_api.services.vlm_service import VLMService


class PromptComparison:
    """異なるプロンプトバージョンの比較"""

    def __init__(self):
        self.results = {}

    async def test_single_image(self, image_path: str) -> Dict[str, Any]:
        """単一画像を複数のプロンプトでテスト"""

        prompts = {
            "v3_current": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v3_with_weight_20251026.txt",
            "v4_light": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v4_light_20251027.txt",
            "v4_cot": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v4_cot_20251027.txt"
        }

        results = {}

        for version, prompt_file in prompts.items():
            print(f"\n{'='*80}")
            print(f"Testing {version} with {Path(image_path).name}")
            print(f"{'='*80}")

            try:
                # VLMサービス初期化（プロンプト指定）
                vlm_service = VLMService()

                # プロンプトを手動で変更
                prompt_path = project_root / prompt_file
                if prompt_path.exists():
                    vlm_service.prompt = vlm_service._load_prompt(str(prompt_path))
                    print(f"✅ Loaded prompt: {prompt_file}")
                else:
                    print(f"❌ Prompt file not found: {prompt_file}")
                    continue

                # 画像分析実行
                result = await vlm_service.analyze_image_from_file(image_path)

                # 結果を保存
                results[version] = {
                    "success": True,
                    "data": result,
                    "total_weight": self._calculate_total_weight(result),
                    "item_count": self._count_items(result),
                    "has_reasoning": self._check_reasoning(result)
                }

                # 結果サマリー表示
                self._print_summary(version, results[version])

            except Exception as e:
                print(f"❌ Error with {version}: {str(e)}")
                results[version] = {
                    "success": False,
                    "error": str(e)
                }

        return results

    def _calculate_total_weight(self, result: Dict) -> int:
        """総重量を計算"""
        total = 0
        for dish in result.get("dishes", []):
            if dish.get("main_food"):
                total += dish["main_food"].get("weight_g", 0)
            for extra in dish.get("extras", []):
                total += extra.get("weight_g", 0)
        return total

    def _count_items(self, result: Dict) -> int:
        """アイテム数をカウント"""
        count = 0
        for dish in result.get("dishes", []):
            if dish.get("main_food"):
                count += 1
            count += len(dish.get("extras", []))
        return count

    def _check_reasoning(self, result: Dict) -> Dict[str, bool]:
        """推論理由の有無をチェック"""
        has_reasoning_steps = "reasoning_steps" in result
        has_weight_reasoning = False
        reasoning_count = 0

        for dish in result.get("dishes", []):
            if dish.get("main_food") and "weight_reasoning" in dish["main_food"]:
                has_weight_reasoning = True
                reasoning_count += 1
            for extra in dish.get("extras", []):
                if "weight_reasoning" in extra:
                    has_weight_reasoning = True
                    reasoning_count += 1

        return {
            "has_reasoning_steps": has_reasoning_steps,
            "has_weight_reasoning": has_weight_reasoning,
            "reasoning_count": reasoning_count
        }

    def _print_summary(self, version: str, result: Dict):
        """結果サマリーを表示"""
        print(f"\n📊 {version} Summary:")
        print(f"  Total Weight: {result['total_weight']}g")
        print(f"  Item Count: {result['item_count']}")
        print(f"  Has Reasoning Steps: {result['has_reasoning'].get('has_reasoning_steps', False)}")
        print(f"  Has Weight Reasoning: {result['has_reasoning'].get('has_weight_reasoning', False)}")
        print(f"  Reasoning Count: {result['has_reasoning'].get('reasoning_count', 0)}")

    def compare_results(self, results: Dict) -> Dict:
        """結果を比較"""
        comparison = {
            "weight_differences": {},
            "reasoning_quality": {},
            "item_count_differences": {}
        }

        versions = list(results.keys())
        if len(versions) < 2:
            return comparison

        # v3を基準として比較
        base_version = "v3_current"
        if base_version not in results or not results[base_version]["success"]:
            return comparison

        base_weight = results[base_version]["total_weight"]
        base_count = results[base_version]["item_count"]

        for version in versions:
            if version == base_version or not results[version]["success"]:
                continue

            # 重量差
            weight_diff = results[version]["total_weight"] - base_weight
            weight_diff_pct = (weight_diff / base_weight * 100) if base_weight > 0 else 0
            comparison["weight_differences"][version] = {
                "absolute": weight_diff,
                "percentage": weight_diff_pct
            }

            # アイテム数差
            comparison["item_count_differences"][version] = (
                results[version]["item_count"] - base_count
            )

            # 推論品質
            comparison["reasoning_quality"][version] = results[version]["has_reasoning"]

        return comparison

    async def test_high_error_images(self):
        """高誤差画像をテスト"""
        high_error_images = [
            "test_images/test_food4.jpg",   # +63.0% error
            "test_images/test_food13.jpg",  # +61.4% error
            "test_images/test_food47.jpg",  # +57.9% error
        ]

        all_results = {}
        for image_path in high_error_images:
            if not Path(image_path).exists():
                print(f"⚠️ Image not found: {image_path}")
                continue

            results = await self.test_single_image(image_path)
            all_results[Path(image_path).name] = results

            # 比較結果を表示
            print(f"\n{'='*80}")
            print(f"📊 Comparison for {Path(image_path).name}")
            print(f"{'='*80}")
            comparison = self.compare_results(results)
            self._print_comparison(comparison)

        # 結果を保存
        self._save_results(all_results)

    def _print_comparison(self, comparison: Dict):
        """比較結果を表示"""
        print("\n🔄 Weight Differences from v3_current:")
        for version, diff in comparison["weight_differences"].items():
            sign = "+" if diff["absolute"] >= 0 else ""
            print(f"  {version}: {sign}{diff['absolute']}g ({sign}{diff['percentage']:.1f}%)")

        print("\n📝 Reasoning Quality:")
        for version, quality in comparison["reasoning_quality"].items():
            print(f"  {version}:")
            print(f"    - Reasoning Steps: {quality.get('has_reasoning_steps', False)}")
            print(f"    - Weight Reasoning: {quality.get('has_weight_reasoning', False)}")
            print(f"    - Reasoning Count: {quality.get('reasoning_count', 0)}")

    def _save_results(self, results: Dict):
        """結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_scripts/output/vlm_prompt_comparison_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {output_file}")

    def extract_reasoning_examples(self, results: Dict) -> List[Dict]:
        """推論理由の例を抽出"""
        examples = []

        for image, versions in results.items():
            for version, data in versions.items():
                if not data.get("success"):
                    continue

                result = data.get("data", {})

                # reasoning_stepsの例
                if "reasoning_steps" in result:
                    examples.append({
                        "image": image,
                        "version": version,
                        "type": "reasoning_steps",
                        "content": result["reasoning_steps"]
                    })

                # weight_reasoningの例
                for dish in result.get("dishes", []):
                    if dish.get("main_food") and "weight_reasoning" in dish["main_food"]:
                        examples.append({
                            "image": image,
                            "version": version,
                            "type": "weight_reasoning",
                            "food": dish["main_food"]["search_name"],
                            "weight": dish["main_food"]["weight_g"],
                            "reasoning": dish["main_food"]["weight_reasoning"]
                        })

        return examples


async def main():
    """メイン実行"""
    print("🚀 VLM Prompt Comparison Test")
    print("=" * 80)

    comparison = PromptComparison()

    # オプション1: 単一画像のテスト
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        results = await comparison.test_single_image(image_path)
        comp_results = comparison.compare_results(results)
        comparison._print_comparison(comp_results)
    else:
        # オプション2: 高誤差画像の自動テスト
        await comparison.test_high_error_images()


if __name__ == "__main__":
    asyncio.run(main())