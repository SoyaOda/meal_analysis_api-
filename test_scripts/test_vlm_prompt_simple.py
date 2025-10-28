#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
シンプルなVLMプロンプト比較テスト
DeepInfraServiceを直接使用して、依存関係の問題を回避
"""

import asyncio
import json
import base64
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.services.deepinfra_service import DeepInfraService


class SimpleVLMTester:
    """シンプルなVLMテスター"""

    def __init__(self):
        self.deepinfra = DeepInfraService()

    def load_prompt(self, prompt_path: str) -> str:
        """プロンプトファイルを読み込む"""
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    async def test_with_prompt(self, image_path: str, prompt_text: str, version: str) -> dict:
        """特定のプロンプトで画像を分析"""
        print(f"\n{'='*80}")
        print(f"🔍 Testing {version}")
        print(f"{'='*80}")

        try:
            # 画像を読み込み
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            # MIMEタイプを判定
            if image_path.lower().endswith('.png'):
                mime_type = 'image/png'
            elif image_path.lower().endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            else:
                mime_type = 'image/jpeg'  # デフォルト

            print("📡 Calling DeepInfra API...")
            # analyze_imageメソッドを使用（return_usage=Trueで使用量も取得）
            content, usage = await self.deepinfra.analyze_image(
                image_bytes=image_bytes,
                image_mime_type=mime_type,
                prompt=prompt_text,
                max_tokens=8192,
                temperature=0.1,
                return_usage=True
            )

            # JSONをパース
            try:
                result = json.loads(content)
                print("✅ Successfully parsed JSON response")
                return {
                    "success": True,
                    "data": result,
                    "raw_response": content,
                    "usage": usage
                }
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {str(e)}")
                print(f"Raw response: {content[:500]}...")
                return {
                    "success": False,
                    "error": f"JSON parse error: {str(e)}",
                    "raw_response": content
                }

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
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

    def extract_weight_reasoning(self, result: dict) -> list:
        """weight_reasoningを抽出"""
        reasoning_list = []
        for dish in result.get("dishes", []):
            if dish.get("main_food") and "weight_reasoning" in dish["main_food"]:
                reasoning_list.append({
                    "item": dish["main_food"].get("search_name"),
                    "weight": dish["main_food"].get("weight_g"),
                    "reasoning": dish["main_food"]["weight_reasoning"]
                })
            for extra in dish.get("extras", []):
                if "weight_reasoning" in extra:
                    reasoning_list.append({
                        "item": extra.get("search_name"),
                        "weight": extra.get("weight_g"),
                        "reasoning": extra["weight_reasoning"]
                    })
        return reasoning_list

    def print_summary(self, version: str, result_data: dict):
        """結果サマリーを表示"""
        if not result_data["success"]:
            print(f"\n❌ {version} failed: {result_data.get('error')}")
            return

        data = result_data["data"]
        total_weight = self.calculate_total_weight(data)
        item_count = self.count_items(data)
        reasoning = self.extract_weight_reasoning(data)

        print(f"\n📊 {version} Summary:")
        print(f"  Total Weight: {total_weight}g")
        print(f"  Item Count: {item_count}")
        print(f"  Has Reasoning Steps: {'reasoning_steps' in data}")
        print(f"  Weight Reasoning Count: {len(reasoning)}")

        if reasoning:
            print(f"\n💭 Weight Reasoning Examples:")
            for i, r in enumerate(reasoning[:3], 1):  # 最初の3つだけ表示
                print(f"\n  {i}. {r['item']} ({r['weight']}g)")
                print(f"     → {r['reasoning'][:150]}...")

        # Usage統計
        usage = result_data.get("usage", {})
        if usage:
            print(f"\n📈 Token Usage:")
            print(f"  Prompt: {usage.get('prompt_tokens', 0)}")
            print(f"  Completion: {usage.get('completion_tokens', 0)}")
            print(f"  Total: {usage.get('total_tokens', 0)}")

    async def compare_prompts(self, image_path: str):
        """複数のプロンプトで比較"""
        print(f"\n🚀 VLM Prompt Comparison Test")
        print(f"Image: {image_path}")
        print(f"=" * 80)

        # プロンプトファイルのパス
        prompts = {
            "v3_current": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v3_with_weight_20251026.txt",
            "v4_light": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v4_light_20251027.txt",
        }

        results = {}

        for version, prompt_file in prompts.items():
            prompt_path = project_root / prompt_file
            if not prompt_path.exists():
                print(f"⚠️ Prompt file not found: {prompt_file}")
                continue

            # プロンプトを読み込み
            prompt_text = self.load_prompt(str(prompt_path))
            print(f"\n📄 Loaded prompt: {prompt_file}")
            print(f"   Length: {len(prompt_text)} characters")

            # テスト実行
            result = await self.test_with_prompt(image_path, prompt_text, version)
            results[version] = result

            # サマリー表示
            self.print_summary(version, result)

        # 比較結果
        self.print_comparison(results)

        # 結果を保存
        self.save_results(image_path, results)

    def print_comparison(self, results: dict):
        """比較結果を表示"""
        print(f"\n{'='*80}")
        print("📊 Comparison Summary")
        print(f"{'='*80}")

        versions = list(results.keys())
        if len(versions) < 2:
            print("⚠️ Need at least 2 versions to compare")
            return

        # v3を基準として比較
        base_version = "v3_current"
        if base_version not in results or not results[base_version]["success"]:
            print(f"⚠️ Base version {base_version} not available")
            return

        base_weight = self.calculate_total_weight(results[base_version]["data"])

        print(f"\n🔄 Weight Differences from {base_version} ({base_weight}g):")
        for version in versions:
            if version == base_version or not results[version]["success"]:
                continue

            new_weight = self.calculate_total_weight(results[version]["data"])
            diff = new_weight - base_weight
            diff_pct = (diff / base_weight * 100) if base_weight > 0 else 0
            sign = "+" if diff >= 0 else ""
            print(f"  {version}: {new_weight}g ({sign}{diff}g, {sign}{diff_pct:.1f}%)")

        print(f"\n📝 Reasoning Quality:")
        for version, result_data in results.items():
            if not result_data["success"]:
                continue

            data = result_data["data"]
            reasoning_count = len(self.extract_weight_reasoning(data))
            has_steps = "reasoning_steps" in data

            print(f"  {version}:")
            print(f"    - Reasoning Steps: {has_steps}")
            print(f"    - Weight Reasoning: {reasoning_count} items")

    def save_results(self, image_path: str, results: dict):
        """結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = Path(image_path).stem
        output_file = project_root / f"test_scripts/output/vlm_comparison_{image_name}_{timestamp}.json"

        # 保存用データを整形
        save_data = {
            "image": image_path,
            "timestamp": timestamp,
            "results": {}
        }

        for version, result_data in results.items():
            if result_data["success"]:
                save_data["results"][version] = {
                    "data": result_data["data"],
                    "total_weight": self.calculate_total_weight(result_data["data"]),
                    "item_count": self.count_items(result_data["data"]),
                    "weight_reasoning": self.extract_weight_reasoning(result_data["data"]),
                    "usage": result_data.get("usage", {})
                }
            else:
                save_data["results"][version] = {
                    "error": result_data.get("error")
                }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {output_file}")


async def main():
    """メイン実行"""
    # テスト画像のパス
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # デフォルト: test_food4.jpg（最も高い誤差）
        image_path = "test_images/test_food4.jpg"

    # 画像の存在確認
    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return

    # テスト実行
    tester = SimpleVLMTester()
    await tester.compare_prompts(image_path)


if __name__ == "__main__":
    asyncio.run(main())
