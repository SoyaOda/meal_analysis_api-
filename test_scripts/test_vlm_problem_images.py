#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VLMの問題があった画像で3つのプロンプトバージョンを比較
- v3_current: 現在のプロンプト
- v4_cot: Chain-of-Thought版（詳細推論）
- v4_light: 軽量版（理由付きのみ）
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.services.deepinfra_service import DeepInfraService


class VLMProblemImagesTester:
    """VLMの問題があった画像専用のテスター"""

    # VLMの問題があった画像リスト
    VLM_PROBLEM_IMAGES = [
        {
            "file": "test_images/images/test_food4.jpg",
            "name": "test_food4.jpg",
            "issues": "VLM認識不足（7→3品）、重量+42.6%",
            "error_pct": 63.0,
            "label_weight": 505
        },
        {
            "file": "test_images/images/test_food13.jpg",
            "name": "test_food13.jpg",
            "issues": "VLM認識不足（4→3品）、重量+25.5%",
            "error_pct": 61.4,
            "label_weight": 470
        },
        {
            "file": "test_images/images/test_food27.jpg",
            "name": "test_food27.jpg",
            "issues": "重量推定誤差（-29.8%）",
            "error_pct": -53.7,
            "label_weight": 620
        },
        {
            "file": "test_images/images/test_food20.jpg",
            "name": "test_food20.jpg",
            "issues": "重量推定誤差（+20.7%）",
            "error_pct": 47.7,
            "label_weight": 590
        },
        {
            "file": "test_images/images/test_food8.jpg",
            "name": "test_food8.jpg",
            "issues": "重量推定誤差（-32.5%）、fish→chicken誤認識",
            "error_pct": -35.2,
            "label_weight": 570
        }
    ]

    PROMPT_VERSIONS = {
        "v3_current": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v3_with_weight_20251026.txt",
        "v4_light": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v4_light_20251027.txt",
        "v5_qwen3": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v5_qwen3_thinking_20251027.txt",
        "v5_streamlined": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v5_streamlined_20251027.txt"
    }

    def __init__(self):
        self.deepinfra = DeepInfraService()
        self.results = {}

    def load_prompt(self, prompt_path: str) -> str:
        """プロンプトファイルを読み込む"""
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    async def test_single_image_with_prompt(
        self,
        image_path: str,
        prompt_text: str,
        version: str
    ) -> dict:
        """単一画像を単一プロンプトでテスト"""
        try:
            # 画像を読み込み
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            # MIMEタイプを判定
            if image_path.lower().endswith('.png'):
                mime_type = 'image/png'
            else:
                mime_type = 'image/jpeg'

            # DeepInfra APIを呼び出し
            content, usage = await self.deepinfra.analyze_image(
                image_bytes=image_bytes,
                image_mime_type=mime_type,
                prompt=prompt_text,
                max_tokens=8192,
                temperature=0.1,
                return_usage=True
            )

            # JSONをパース
            result = json.loads(content)

            return {
                "success": True,
                "data": result,
                "usage": usage
            }

        except Exception as e:
            print(f"❌ Error testing {version}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def calculate_total_weight(self, result: dict) -> int:
        """総重量を計算"""
        total = 0
        for dish in result.get("dishes", []):
            if dish.get("main_food"):
                total += dish["main_food"].get("weight_g", 0)
            for extra in dish.get("extras", []):
                total += extra.get("weight_g", 0)
        return total

    def count_items(self, result: dict) -> int:
        """アイテム数をカウント"""
        count = 0
        for dish in result.get("dishes", []):
            if dish.get("main_food"):
                count += 1
            count += len(dish.get("extras", []))
        return count

    def extract_reasoning_count(self, result: dict) -> int:
        """weight_reasoningの数をカウント"""
        count = 0
        for dish in result.get("dishes", []):
            if dish.get("main_food") and "weight_reasoning" in dish["main_food"]:
                count += 1
            for extra in dish.get("extras", []):
                if "weight_reasoning" in extra:
                    count += 1
        return count

    async def test_all_images(self):
        """全てのVLM問題画像をテスト"""
        print("\n🚀 VLM Problem Images Comprehensive Test")
        print("=" * 80)
        print(f"\n📋 Testing {len(self.VLM_PROBLEM_IMAGES)} images with VLM issues")
        print(f"📝 Testing {len(self.PROMPT_VERSIONS)} prompt versions\n")

        all_results = {}

        for image_info in self.VLM_PROBLEM_IMAGES:
            image_path = image_info["file"]
            image_name = image_info["name"]

            print(f"\n{'='*80}")
            print(f"📷 Image: {image_name}")
            print(f"   Issues: {image_info['issues']}")
            print(f"   Error: {image_info['error_pct']:+.1f}%")
            print(f"   Label Weight: {image_info['label_weight']}g")
            print(f"{'='*80}")

            if not Path(image_path).exists():
                print(f"⚠️ Image not found: {image_path}")
                continue

            image_results = {}

            for version, prompt_file in self.PROMPT_VERSIONS.items():
                prompt_path = project_root / prompt_file
                if not prompt_path.exists():
                    print(f"⚠️ Prompt file not found: {prompt_file}")
                    continue

                print(f"\n🔍 Testing {version}...")

                # プロンプトを読み込み
                prompt_text = self.load_prompt(str(prompt_path))

                # テスト実行
                result = await self.test_single_image_with_prompt(
                    image_path,
                    prompt_text,
                    version
                )

                if result["success"]:
                    total_weight = self.calculate_total_weight(result["data"])
                    item_count = self.count_items(result["data"])
                    reasoning_count = self.extract_reasoning_count(result["data"])

                    weight_diff = total_weight - image_info["label_weight"]
                    weight_diff_pct = (weight_diff / image_info["label_weight"] * 100) if image_info["label_weight"] > 0 else 0

                    image_results[version] = {
                        "total_weight": total_weight,
                        "item_count": item_count,
                        "reasoning_count": reasoning_count,
                        "weight_diff": weight_diff,
                        "weight_diff_pct": weight_diff_pct,
                        "usage": result["usage"],
                        "data": result["data"]
                    }

                    print(f"   ✅ Weight: {total_weight}g ({weight_diff:+d}g, {weight_diff_pct:+.1f}%)")
                    print(f"      Items: {item_count}, Reasoning: {reasoning_count}")
                else:
                    image_results[version] = {
                        "error": result["error"]
                    }
                    print(f"   ❌ Failed: {result['error']}")

            all_results[image_name] = {
                "image_info": image_info,
                "results": image_results
            }

            # 画像ごとの比較サマリー
            self._print_image_comparison(image_name, image_info, image_results)

        # 全体サマリー
        self._print_overall_summary(all_results)

        # 結果を保存
        self._save_results(all_results)

        return all_results

    def _print_image_comparison(self, image_name: str, image_info: dict, results: dict):
        """画像ごとの比較結果を表示"""
        if not results:
            return

        print(f"\n📊 Comparison for {image_name}:")
        print(f"   Label: {image_info['label_weight']}g")

        for version in ["v3_current", "v4_cot", "v4_light"]:
            if version not in results or "error" in results[version]:
                continue

            r = results[version]
            print(f"   {version:12s}: {r['total_weight']:4d}g ({r['weight_diff']:+4d}g, {r['weight_diff_pct']:+6.1f}%) | Items: {r['item_count']:2d} | Reasoning: {r['reasoning_count']:2d}")

    def _print_overall_summary(self, all_results: dict):
        """全体サマリーを表示"""
        print(f"\n{'='*80}")
        print("📊 OVERALL SUMMARY")
        print(f"{'='*80}\n")

        # バージョンごとの統計
        version_stats = {
            "v3_current": {"weights": [], "diffs": [], "items": [], "reasoning": []},
            "v4_cot": {"weights": [], "diffs": [], "items": [], "reasoning": []},
            "v4_light": {"weights": [], "diffs": [], "items": [], "reasoning": []}
        }

        for image_name, data in all_results.items():
            results = data["results"]
            for version, stats in version_stats.items():
                if version in results and "error" not in results[version]:
                    r = results[version]
                    stats["weights"].append(r["total_weight"])
                    stats["diffs"].append(abs(r["weight_diff_pct"]))
                    stats["items"].append(r["item_count"])
                    stats["reasoning"].append(r["reasoning_count"])

        # 統計を表示
        print("Average Metrics by Version:")
        print(f"{'Version':<15} | {'Avg Weight':<10} | {'Avg Error%':<12} | {'Avg Items':<10} | {'Avg Reasoning':<12}")
        print("-" * 80)

        for version, stats in version_stats.items():
            if not stats["weights"]:
                continue

            avg_weight = sum(stats["weights"]) / len(stats["weights"])
            avg_diff = sum(stats["diffs"]) / len(stats["diffs"])
            avg_items = sum(stats["items"]) / len(stats["items"])
            avg_reasoning = sum(stats["reasoning"]) / len(stats["reasoning"])

            print(f"{version:<15} | {avg_weight:>10.1f} | {avg_diff:>12.1f} | {avg_items:>10.1f} | {avg_reasoning:>12.1f}")

    def _save_results(self, results: dict):
        """結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = project_root / f"test_scripts/output/vlm_problem_images_comparison_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {output_file}")


async def main():
    """メイン実行"""
    tester = VLMProblemImagesTester()
    await tester.test_all_images()


if __name__ == "__main__":
    asyncio.run(main())
