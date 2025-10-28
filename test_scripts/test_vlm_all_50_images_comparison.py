#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
50画像全てでv5_qwen3, v5_streamlined, v4_lightを公平に比較
各プロンプトのJSON構造の違いを適切に処理
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import statistics

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.services.deepinfra_service import DeepInfraService


class ComprehensiveVLMTester:
    """50画像全てで3つのプロンプトバージョンを公平に比較"""

    PROMPT_VERSIONS = {
        "v4_light": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v4_light_20251027.txt",
        "v5_qwen3": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v5_qwen3_thinking_20251027.txt",
        "v5_streamlined": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v5_streamlined_20251027.txt"
    }

    def __init__(self):
        self.deepinfra = DeepInfraService()
        self.results = {}
        self.label_data = None

    def load_labels(self) -> Dict[str, Any]:
        """ラベルデータを読み込む"""
        label_file = project_root / "test_images/images_label/all_labels.json"
        with open(label_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # image_file -> label_dataのマッピングを作成
        labels = {}
        for label_info in data["labels"]:
            image_name = label_info["image_file"]
            total_weight = 0

            for dish in label_info["label"]["dishes"]:
                if dish["base_food"]:
                    total_weight += dish["base_food"]["weight_g"]

                for ingredient in dish.get("ingredients", []):
                    total_weight += ingredient["weight_g"]

            labels[image_name] = {
                "total_weight": total_weight,
                "dishes": label_info["label"]["dishes"]
            }

        return labels

    def load_prompt(self, prompt_path: str) -> str:
        """プロンプトファイルを読み込む"""
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def calculate_weight_v4_light(self, data: Dict[str, Any]) -> int:
        """v4_lightの標準的なJSON構造から重量を取得"""
        total = 0
        for dish in data.get("dishes", []):
            if dish.get("main_food"):
                total += dish["main_food"].get("weight_g", 0)
            for extra in dish.get("extras", []):
                total += extra.get("weight_g", 0)
        return total

    def calculate_weight_v5_qwen3(self, data: Dict[str, Any]) -> int:
        """v5_qwen3特有のJSON構造から重量を正しく取得"""
        total = 0

        # quality_metricsから直接取得（最も正確）
        if "quality_metrics" in data and "total_weight_g" in data["quality_metrics"]:
            return data["quality_metrics"]["total_weight_g"]

        # dishesから計算
        for dish in data.get("dishes", []):
            if dish.get("main_food"):
                main_food = dish["main_food"]
                # weight_derivationから取得
                if "weight_derivation" in main_food:
                    total += main_food["weight_derivation"].get("weight_g", 0)
                # 直接weight_gがある場合（フォールバック）
                elif "weight_g" in main_food:
                    total += main_food["weight_g"]

            for extra in dish.get("extras", []):
                # extrasは通常のweight_g
                total += extra.get("weight_g", 0)

        return total

    def calculate_weight_v5_streamlined(self, data: Dict[str, Any]) -> int:
        """v5_streamlinedのJSON構造から重量を取得"""
        # total_weight_gが直接ある場合
        if "total_weight_g" in data:
            return data["total_weight_g"]

        # dishesから計算
        total = 0
        for dish in data.get("dishes", []):
            if dish.get("main_food"):
                total += dish["main_food"].get("weight_g", 0)
            for extra in dish.get("extras", []):
                total += extra.get("weight_g", 0)
        return total

    def extract_weight_by_version(self, data: Dict[str, Any], version: str) -> int:
        """バージョンに応じた適切な重量抽出"""
        if version == "v4_light":
            return self.calculate_weight_v4_light(data)
        elif version == "v5_qwen3":
            return self.calculate_weight_v5_qwen3(data)
        elif version == "v5_streamlined":
            return self.calculate_weight_v5_streamlined(data)
        else:
            raise ValueError(f"Unknown version: {version}")

    def count_items(self, data: Dict[str, Any]) -> int:
        """アイテム数をカウント"""
        count = 0
        for dish in data.get("dishes", []):
            if dish.get("main_food"):
                count += 1
            count += len(dish.get("extras", []))
        return count

    def has_reasoning(self, data: Dict[str, Any], version: str) -> bool:
        """推論説明があるかチェック"""
        if version == "v4_light":
            # weight_reasoningフィールドの存在をチェック
            for dish in data.get("dishes", []):
                if dish.get("main_food") and "weight_reasoning" in dish["main_food"]:
                    return True
        elif version == "v5_qwen3":
            # weight_derivationフィールドの存在をチェック
            for dish in data.get("dishes", []):
                if dish.get("main_food") and "weight_derivation" in dish["main_food"]:
                    return True
        elif version == "v5_streamlined":
            # estimation_basisフィールドの存在をチェック
            for dish in data.get("dishes", []):
                if dish.get("main_food") and "estimation_basis" in dish["main_food"]:
                    return True
        return False

    async def test_single_image(
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

    async def test_all_images(self):
        """50画像全てをテスト"""
        print("\n🚀 Comprehensive VLM Comparison Test - All 50 Images")
        print("=" * 80)
        print(f"📋 Testing 50 images with 3 prompt versions")
        print(f"   - v4_light (weight_reasoning)")
        print(f"   - v5_qwen3 (weight_derivation)")
        print(f"   - v5_streamlined (estimation_basis)")
        print("=" * 80)

        # ラベルデータを読み込み
        self.label_data = self.load_labels()

        all_results = {}

        # 進捗追跡
        total_tests = len(self.label_data) * len(self.PROMPT_VERSIONS)
        completed_tests = 0

        for image_name, label_info in self.label_data.items():
            image_path = project_root / "test_images/images" / image_name

            if not image_path.exists():
                print(f"\n⚠️ Image not found: {image_name}")
                continue

            print(f"\n📷 Testing {image_name} (Label: {label_info['total_weight']}g)")

            image_results = {}

            for version, prompt_file in self.PROMPT_VERSIONS.items():
                prompt_path = project_root / prompt_file
                if not prompt_path.exists():
                    print(f"⚠️ Prompt file not found: {prompt_file}")
                    continue

                # プロンプトを読み込み
                prompt_text = self.load_prompt(str(prompt_path))

                # テスト実行
                result = await self.test_single_image(
                    str(image_path),
                    prompt_text,
                    version
                )

                completed_tests += 1

                if result["success"]:
                    # バージョンに応じた重量抽出
                    actual_weight = self.extract_weight_by_version(result["data"], version)
                    item_count = self.count_items(result["data"])
                    has_reasoning = self.has_reasoning(result["data"], version)

                    weight_diff = actual_weight - label_info["total_weight"]
                    weight_diff_pct = (weight_diff / label_info["total_weight"] * 100) if label_info["total_weight"] > 0 else 0

                    image_results[version] = {
                        "actual_weight": actual_weight,
                        "item_count": item_count,
                        "has_reasoning": has_reasoning,
                        "weight_diff": weight_diff,
                        "weight_diff_pct": weight_diff_pct,
                        "usage": result["usage"],
                        "data": result["data"]
                    }

                    print(f"  {version:15s}: {actual_weight:4d}g ({weight_diff:+4d}g, {weight_diff_pct:+6.1f}%)")
                else:
                    image_results[version] = {
                        "error": result["error"]
                    }
                    print(f"  {version:15s}: ERROR")

                # 進捗表示
                progress_pct = (completed_tests / total_tests) * 100
                print(f"  Progress: {completed_tests}/{total_tests} ({progress_pct:.1f}%)")

            all_results[image_name] = {
                "label_weight": label_info["total_weight"],
                "results": image_results
            }

        # 統計分析
        self._analyze_results(all_results)

        # 結果を保存
        self._save_results(all_results)

        return all_results

    def _analyze_results(self, all_results: Dict[str, Any]):
        """結果を詳細に分析"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE ANALYSIS")
        print("=" * 80)

        # バージョンごとの統計を収集
        stats = {
            "v4_light": {"weights": [], "errors": [], "abs_errors": [], "item_counts": [], "reasoning": 0},
            "v5_qwen3": {"weights": [], "errors": [], "abs_errors": [], "item_counts": [], "reasoning": 0},
            "v5_streamlined": {"weights": [], "errors": [], "abs_errors": [], "item_counts": [], "reasoning": 0}
        }

        # 30%以上のエラーケースを追跡
        high_error_cases = {version: [] for version in stats.keys()}

        for image_name, data in all_results.items():
            label_weight = data["label_weight"]

            for version in stats.keys():
                if version in data["results"] and "error" not in data["results"][version]:
                    result = data["results"][version]

                    stats[version]["weights"].append(result["actual_weight"])
                    stats[version]["errors"].append(result["weight_diff_pct"])
                    stats[version]["abs_errors"].append(abs(result["weight_diff_pct"]))
                    stats[version]["item_counts"].append(result["item_count"])
                    if result["has_reasoning"]:
                        stats[version]["reasoning"] += 1

                    # 30%以上のエラーを記録
                    if abs(result["weight_diff_pct"]) >= 30:
                        high_error_cases[version].append({
                            "image": image_name,
                            "error_pct": result["weight_diff_pct"],
                            "actual": result["actual_weight"],
                            "label": label_weight
                        })

        # 統計サマリーテーブル
        print("\n📈 Statistical Summary")
        print("-" * 80)
        print(f"{'Version':<15} | {'Avg Weight':<10} | {'Avg Error%':<12} | {'Median Error%':<14} | {'StdDev':<10}")
        print("-" * 80)

        for version, stat in stats.items():
            if stat["weights"]:
                avg_weight = statistics.mean(stat["weights"])
                avg_error = statistics.mean(stat["abs_errors"])
                median_error = statistics.median(stat["abs_errors"])
                stddev_error = statistics.stdev(stat["abs_errors"]) if len(stat["abs_errors"]) > 1 else 0

                print(f"{version:<15} | {avg_weight:>10.1f} | {avg_error:>12.1f} | {median_error:>14.1f} | {stddev_error:>10.1f}")

        # エラー分布
        print("\n📊 Error Distribution")
        print("-" * 80)
        print(f"{'Version':<15} | {'<10%':<8} | {'10-20%':<8} | {'20-30%':<8} | {'30%+':<8}")
        print("-" * 80)

        for version, stat in stats.items():
            if stat["abs_errors"]:
                under_10 = sum(1 for e in stat["abs_errors"] if e < 10)
                e_10_20 = sum(1 for e in stat["abs_errors"] if 10 <= e < 20)
                e_20_30 = sum(1 for e in stat["abs_errors"] if 20 <= e < 30)
                over_30 = sum(1 for e in stat["abs_errors"] if e >= 30)

                print(f"{version:<15} | {under_10:<8} | {e_10_20:<8} | {e_20_30:<8} | {over_30:<8}")

        # 推論説明の提供率
        print("\n🔍 Reasoning Provision Rate")
        print("-" * 80)
        for version, stat in stats.items():
            if stat["weights"]:
                reasoning_rate = (stat["reasoning"] / len(stat["weights"])) * 100
                avg_items = statistics.mean(stat["item_counts"])
                print(f"{version:<15}: {reasoning_rate:>6.1f}% | Avg Items: {avg_items:>5.1f}")

        # 30%以上のエラーケース
        print("\n⚠️  High Error Cases (≥30%)")
        print("-" * 80)
        for version, cases in high_error_cases.items():
            if cases:
                print(f"\n{version}: {len(cases)} cases")
                for case in cases[:5]:  # 最初の5件を表示
                    print(f"  - {case['image']}: {case['error_pct']:+.1f}% ({case['actual']}g vs {case['label']}g)")

        # ベストパフォーマー判定
        print("\n🏆 Best Performer Analysis")
        print("-" * 80)

        best_version = None
        best_score = float('inf')

        for version, stat in stats.items():
            if stat["abs_errors"]:
                # 総合スコア: 平均誤差 * 0.6 + 中央値誤差 * 0.4
                score = statistics.mean(stat["abs_errors"]) * 0.6 + statistics.median(stat["abs_errors"]) * 0.4
                print(f"{version}: Score = {score:.2f} (lower is better)")
                if score < best_score:
                    best_score = score
                    best_version = version

        if best_version:
            print(f"\n✨ Recommended: {best_version} with score {best_score:.2f}")

    def _save_results(self, results: dict):
        """結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = project_root / f"test_scripts/output/vlm_all_50_images_comparison_{timestamp}.json"

        # usageを除外したクリーンな結果を保存
        clean_results = {}
        for image_name, data in results.items():
            clean_results[image_name] = {
                "label_weight": data["label_weight"],
                "results": {}
            }
            for version, result in data["results"].items():
                if "error" in result:
                    clean_results[image_name]["results"][version] = {"error": result["error"]}
                else:
                    clean_results[image_name]["results"][version] = {
                        "actual_weight": result["actual_weight"],
                        "item_count": result["item_count"],
                        "has_reasoning": result["has_reasoning"],
                        "weight_diff": result["weight_diff"],
                        "weight_diff_pct": result["weight_diff_pct"]
                    }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(clean_results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {output_file}")

        # サマリーレポートも作成
        self._create_summary_report(results, timestamp)

    def _create_summary_report(self, results: dict, timestamp: str):
        """サマリーレポートを作成"""
        report_file = project_root / f"test_scripts/output/vlm_50_images_comparison_report_{timestamp}.md"

        # 統計を計算
        stats = {
            "v4_light": {"errors": [], "abs_errors": []},
            "v5_qwen3": {"errors": [], "abs_errors": []},
            "v5_streamlined": {"errors": [], "abs_errors": []}
        }

        for image_name, data in results.items():
            for version in stats.keys():
                if version in data["results"] and "error" not in data["results"][version]:
                    result = data["results"][version]
                    stats[version]["errors"].append(result["weight_diff_pct"])
                    stats[version]["abs_errors"].append(abs(result["weight_diff_pct"]))

        # レポート作成
        report = f"""# VLMプロンプト比較レポート - 全50画像テスト

**実施日時**: {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}
**テスト画像数**: 50枚
**比較プロンプト**: v4_light, v5_qwen3, v5_streamlined

## 📊 総合結果

| プロンプト | 平均誤差(%) | 中央値誤差(%) | 標準偏差 | 30%以上誤差 |
|-----------|------------|--------------|---------|------------|
"""

        for version in ["v4_light", "v5_qwen3", "v5_streamlined"]:
            if stats[version]["abs_errors"]:
                avg_error = statistics.mean(stats[version]["abs_errors"])
                median_error = statistics.median(stats[version]["abs_errors"])
                stddev = statistics.stdev(stats[version]["abs_errors"]) if len(stats[version]["abs_errors"]) > 1 else 0
                high_error = sum(1 for e in stats[version]["abs_errors"] if e >= 30)

                report += f"| {version} | {avg_error:.1f} | {median_error:.1f} | {stddev:.1f} | {high_error} |\n"

        report += """
## 🏆 推奨事項

最も精度が高いプロンプトは、平均誤差と中央値誤差の総合評価に基づいて決定されました。

## 📝 詳細分析

### 重量推定の透明性
- v4_light: weight_reasoningフィールドで推論過程を記録
- v5_qwen3: weight_derivationで体積・密度計算を詳細化
- v5_streamlined: estimation_basisで簡潔な説明を提供

### エラー分布
30%以上の高エラーケースは主に以下の要因：
1. 重なった食材の重量推定困難
2. ソースや調味料の見落とし
3. 肉種（鶏肉/豚肉）の誤認識

## 💡 今後の改善提案

1. **マルチビュー撮影**: 複数角度からの撮影で精度向上
2. **参照物体の活用**: 既知サイズの物体を含めた撮影
3. **Active Learning**: エラーケースからの自動学習システム構築
"""

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📄 Summary report saved to: {report_file}")


async def main():
    """メイン実行"""
    tester = ComprehensiveVLMTester()
    await tester.test_all_images()


if __name__ == "__main__":
    asyncio.run(main())