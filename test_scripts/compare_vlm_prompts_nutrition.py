#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
3つのVLMプロンプトバージョンを栄養素レベルで比較
v4_light, v5_qwen3, v5_streamlinedを全50画像でテスト

各プロンプト用のPipelineを作成し、栄養素を計算してラベルと比較
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import statistics
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.freeform_usda_meal_analysis_api.services.pipeline import MealAnalysisPipeline


class VLMPromptNutritionComparator:
    """VLMプロンプトを栄養素レベルで比較"""

    # 利用可能な全プロンプト
    AVAILABLE_PROMPTS = {
        "v4_light": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v4_light_20251027.txt",
        "v5_qwen3": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v5_qwen3_thinking_20251027.txt",
        "v5_streamlined": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v5_streamlined_20251027.txt",
        "v6_balanced": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v6_balanced_20251027.txt",
        "v6_corrected": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v6_corrected_20251027.txt",
        "v6_enhanced": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v6_enhanced_20251027.txt",
        "v7_production": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v7_production_20251027.txt",
        "v7_experimental": "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v7_experimental_20251027.txt"
    }

    def __init__(self, selected_prompts=None, model_id=None):
        """
        Args:
            selected_prompts: 使用するプロンプトのリスト。Noneの場合はv4_light, v5_qwen3, v5_streamlinedを使用
            model_id: VLMモデルID（Noneの場合はデフォルト値を使用）
        """
        self.pipelines = {}  # プロンプトバージョンごとのPipeline
        self.model_id = model_id  # VLMモデルID保存

        # 使用するプロンプトを決定
        if selected_prompts is None:
            # デフォルト: 既存の3つ
            self.prompt_versions = {
                k: v for k, v in self.AVAILABLE_PROMPTS.items()
                if k in ["v4_light", "v5_qwen3", "v5_streamlined"]
            }
        else:
            # 指定されたプロンプトのみ
            self.prompt_versions = {
                k: v for k, v in self.AVAILABLE_PROMPTS.items()
                if k in selected_prompts
            }

        self._initialize_pipelines()

    def _initialize_pipelines(self):
        """各プロンプトバージョン用のPipelineを初期化"""
        logger.info("Initializing pipelines for each prompt version...")

        # モデルID表示
        if self.model_id:
            logger.info(f"🤖 Using VLM model: {self.model_id}")
        else:
            logger.info("🤖 Using default VLM model (Qwen/Qwen3-VL-235B-A22B-Thinking)")

        # Pipeline共通設定
        index_dir = "test_scripts/query_system/data"
        usda_survey_file = "usda_database/surveyDownload.json"
        usda_foundation_file = "usda_database/FoodData_Central_foundation_food_json_2025-04-24 2.json"
        usda_sr_legacy_file = "usda_database/FoodData_Central_sr_legacy_food_json_2018-04 2.json"

        for version, prompt_file in self.prompt_versions.items():
            prompt_path = project_root / prompt_file
            if not prompt_path.exists():
                logger.warning(f"Prompt file not found: {prompt_file}")
                continue

            logger.info(f"Creating pipeline for {version}...")
            self.pipelines[version] = MealAnalysisPipeline(
                vlm_model_id=self.model_id,  # モデルIDを渡す
                vlm_prompt_file=str(prompt_path),
                index_dir=index_dir,
                usda_survey_file=usda_survey_file,
                usda_foundation_file=usda_foundation_file,
                usda_sr_legacy_file=usda_sr_legacy_file
            )

        logger.info(f"✅ Initialized {len(self.pipelines)} pipelines")

    def load_label_nutrition(self, label_path: str) -> dict:
        """
        VLM Labelから栄養素を集計

        Returns:
            {
                "total_calorie": float,
                "total_protein_g": float,
                "total_fat_g": float,
                "total_carbs_g": float,
                "items": [...]
            }
        """
        with open(label_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        total_calorie = 0.0
        total_protein_g = 0.0
        total_fat_g = 0.0
        total_carbs_g = 0.0
        items = []

        for dish in data.get("dishes", []):
            # main_food
            main_food = dish.get("main_food")
            if main_food:
                nutrition = main_food.get("nutrition", {})
                total_calorie += nutrition.get("calorie", 0)
                total_protein_g += nutrition.get("protein_g", 0)
                total_fat_g += nutrition.get("fat_g", 0)
                total_carbs_g += nutrition.get("carbs_g", 0)

                items.append({
                    "type": "main_food",
                    "search_name": main_food.get("search_name"),
                    "weight_g": main_food.get("weight_g"),
                    "nutrition": nutrition
                })

            # extras
            for extra in dish.get("extras", []):
                nutrition = extra.get("nutrition", {})
                total_calorie += nutrition.get("calorie", 0)
                total_protein_g += nutrition.get("protein_g", 0)
                total_fat_g += nutrition.get("fat_g", 0)
                total_carbs_g += nutrition.get("carbs_g", 0)

                items.append({
                    "type": "extra",
                    "search_name": extra.get("search_name"),
                    "weight_g": extra.get("weight_g"),
                    "nutrition": nutrition
                })

        return {
            "total_calorie": total_calorie,
            "total_protein_g": total_protein_g,
            "total_fat_g": total_fat_g,
            "total_carbs_g": total_carbs_g,
            "items": items
        }

    async def analyze_with_pipeline(
        self,
        pipeline: MealAnalysisPipeline,
        image_path: str
    ) -> dict:
        """Pipelineで画像を分析し栄養素を取得"""
        try:
            # 画像を読み込み
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            # Pipeline実行
            result = await pipeline.analyze_image(
                image_bytes=image_bytes,
                image_mime_type="image/jpeg"
            )

            return {
                "success": True,
                "total_nutrition": result.get("total_nutrition", {}),
                "dishes": result.get("dishes", []),
                "vlm_output": result.get("vlm_output", {}),
                "performance": result.get("performance", {}),
                "usage": result.get("usage", {})
            }

        except Exception as e:
            logger.error(f"Pipeline analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def calculate_nutrition_diff(self, label: dict, predicted: dict) -> dict:
        """栄養素の差分を計算"""
        predicted_calories = predicted.get('calories', 0) or predicted.get('calorie', 0)

        diff_cal = predicted_calories - label['total_calorie']
        diff_protein = predicted.get('protein_g', 0) - label['total_protein_g']
        diff_fat = predicted.get('fat_g', 0) - label['total_fat_g']
        diff_carbs = predicted.get('carbs_g', 0) - label['total_carbs_g']

        return {
            "calorie": {
                "diff": diff_cal,
                "percent": (diff_cal / label['total_calorie'] * 100) if label['total_calorie'] > 0 else 0
            },
            "protein_g": {
                "diff": diff_protein,
                "percent": (diff_protein / label['total_protein_g'] * 100) if label['total_protein_g'] > 0 else 0
            },
            "fat_g": {
                "diff": diff_fat,
                "percent": (diff_fat / label['total_fat_g'] * 100) if label['total_fat_g'] > 0 else 0
            },
            "carbs_g": {
                "diff": diff_carbs,
                "percent": (diff_carbs / label['total_carbs_g'] * 100) if label['total_carbs_g'] > 0 else 0
            }
        }

    async def test_all_images(self, limit: int = None, concurrency: int = 5):
        """全画像をバッチ処理（並列実行）
        
        Args:
            limit: テスト画像数の上限
            concurrency: 同時処理する画像数（デフォルト5）
        """
        print("\n🚀 VLM Prompt Nutrition Comparison (Parallel Mode)")
        print("=" * 80)
        print("📋 Comparing 3 prompt versions on nutrition accuracy")
        print("   - v4_light")
        print("   - v5_qwen3")
        print("   - v5_streamlined")
        print(f"⚡ Concurrency: {concurrency} images in parallel")
        print("=" * 80)

        # ラベルデータを収集
        label_dir = project_root / "test_images/images_label_with_nutrition"
        label_files = sorted(label_dir.glob("test_food*.json"))

        if limit:
            label_files = label_files[:limit]

        # 並列処理用のSemaphore
        semaphore = asyncio.Semaphore(concurrency)

        async def process_single_image(label_file, idx, total):
            """1画像を全プロンプトでテスト（プロンプトは並列実行）"""
            async with semaphore:
                start_time = time.time()  # 開始時刻を記録
                
                image_num = label_file.stem.replace("test_food", "")
                image_num_int = int(image_num)
                image_name = f"test_food{image_num_int}.jpg"
                image_path = project_root / "test_images/images" / image_name

                if not image_path.exists():
                    logger.warning(f"Image not found: {image_name}")
                    return None

                logger.info(f"[{idx}/{total}] Processing {image_name}...")

                # ラベル栄養素を読み込み
                label_nutrition = self.load_label_nutrition(str(label_file))

                # 3つのプロンプトを並列実行（個別に時間計測）
                prompt_times = {}
                tasks = {}
                prompt_start_times = {}
                
                for version, pipeline in self.pipelines.items():
                    prompt_start_times[version] = time.time()
                    tasks[version] = self.analyze_with_pipeline(pipeline, str(image_path))

                # 並列実行
                results = await asyncio.gather(*tasks.values(), return_exceptions=True)
                
                # 各プロンプトの処理時間を計算
                for version in tasks.keys():
                    prompt_times[version] = time.time() - prompt_start_times[version]

                # 結果を整理
                image_result = {
                    "image_name": image_name,
                    "label_nutrition": label_nutrition,
                    "prompt_results": {},
                    "processing_time": {}  # 処理時間を追加
                }

                for (version, _), result in zip(tasks.items(), results):
                    # 処理時間を記録
                    image_result["processing_time"][version] = round(prompt_times[version], 2)
                    
                    if isinstance(result, Exception):
                        image_result["prompt_results"][version] = {"error": str(result)}
                        logger.error(f"  {version}: ERROR - {str(result)}")
                    elif result["success"]:
                        diff = self.calculate_nutrition_diff(
                            label_nutrition,
                            result["total_nutrition"]
                        )

                        image_result["prompt_results"][version] = {
                            "total_nutrition": result["total_nutrition"],
                            "dishes": result["dishes"],
                            "vlm_output": result.get("vlm_output", {}),  # VLM raw outputを追加
                            "diff": diff,
                            "performance": result.get("performance", {})
                        }

                        logger.info(
                            f"  {version:15s}: Cal {diff['calorie']['percent']:+6.1f}%, "
                            f"P {diff['protein_g']['percent']:+6.1f}%, "
                            f"F {diff['fat_g']['percent']:+6.1f}%, "
                            f"C {diff['carbs_g']['percent']:+6.1f}% "
                            f"({prompt_times[version]:.1f}s)"
                        )
                    else:
                        image_result["prompt_results"][version] = {"error": result["error"]}
                        logger.error(f"  {version}: ERROR - {result['error']}")

                # 全体の処理時間を記録
                total_time = time.time() - start_time
                image_result["total_processing_time"] = round(total_time, 2)
                
                logger.info(f"  Total time for {image_name}: {total_time:.1f}s")

                return image_result

        # 全画像を並列処理
        tasks = [
            process_single_image(label_file, idx, len(label_files))
            for idx, label_file in enumerate(label_files, 1)
        ]

        all_results = await asyncio.gather(*tasks)
        
        # Noneを除外
        all_results = [r for r in all_results if r is not None]

        # 統計分析
        self._analyze_results(all_results)

        # 結果を保存
        self._save_results(all_results)

        return all_results

    def _analyze_results(self, results: List[dict]):
        """結果を分析"""
        print("\n" + "=" * 80)
        print("📊 NUTRITION ACCURACY ANALYSIS")
        print("=" * 80)

        # バージョンごとの統計
        stats = {
            "v4_light": {"cal": [], "protein": [], "fat": [], "carbs": [], "times": []},
            "v5_qwen3": {"cal": [], "protein": [], "fat": [], "carbs": [], "times": []},
            "v5_streamlined": {"cal": [], "protein": [], "fat": [], "carbs": [], "times": []}
        }
        
        total_times = []  # 画像ごとの全体処理時間

        for result in results:
            # 全体処理時間を収集
            if "total_processing_time" in result:
                total_times.append(result["total_processing_time"])
            
            for version in stats.keys():
                if version in result["prompt_results"] and "error" not in result["prompt_results"][version]:
                    diff = result["prompt_results"][version]["diff"]
                    stats[version]["cal"].append(abs(diff["calorie"]["percent"]))
                    stats[version]["protein"].append(abs(diff["protein_g"]["percent"]))
                    stats[version]["fat"].append(abs(diff["fat_g"]["percent"]))
                    stats[version]["carbs"].append(abs(diff["carbs_g"]["percent"]))
                    
                    # 処理時間を収集
                    if "processing_time" in result and version in result["processing_time"]:
                        stats[version]["times"].append(result["processing_time"][version])

        # サマリーテーブル
        print("\n📈 Average Absolute Error (%)  |  ⏱️ Processing Time")
        print("-" * 80)
        print(f"{'Version':<15} | {'Calories':<10} | {'Protein':<10} | {'Fat':<10} | {'Carbs':<10} | {'Avg Time':<10}")
        print("-" * 80)

        for version, stat in stats.items():
            if stat["cal"]:
                avg_cal = statistics.mean(stat["cal"])
                avg_protein = statistics.mean(stat["protein"])
                avg_fat = statistics.mean(stat["fat"])
                avg_carbs = statistics.mean(stat["carbs"])
                avg_time = statistics.mean(stat["times"]) if stat["times"] else 0

                print(f"{version:<15} | {avg_cal:>10.1f} | {avg_protein:>10.1f} | {avg_fat:>10.1f} | {avg_carbs:>10.1f} | {avg_time:>8.1f}s")

        # 30%以上の誤差件数
        print("\n⚠️  High Error Cases (≥30% calorie error)")
        print("-" * 80)
        for version in stats.keys():
            if stats[version]["cal"]:
                high_error_count = sum(1 for e in stats[version]["cal"] if e >= 30)
                print(f"{version:<15}: {high_error_count} cases")

        # 処理時間統計
        if total_times:
            print("\n⏱️  Processing Time Statistics")
            print("-" * 80)
            avg_total = statistics.mean(total_times)
            min_total = min(total_times)
            max_total = max(total_times)
            print(f"Average time per image (3 prompts parallel): {avg_total:.1f}s")
            print(f"Min: {min_total:.1f}s | Max: {max_total:.1f}s")
            
            # 50画像の推定時間（並列実行）
            if len(results) > 0:
                estimated_total = avg_total * 50 / 5  # 5画像並列と仮定
                print(f"\nEstimated time for 50 images (concurrency=5): {estimated_total/60:.1f} minutes")

        # ベストパフォーマー
        print("\n🏆 Best Performer")
        print("-" * 80)

        best_version = None
        best_score = float('inf')

        for version, stat in stats.items():
            if stat["cal"]:
                # 総合スコア: カロリー誤差を重視
                score = statistics.mean(stat["cal"])
                avg_time = statistics.mean(stat["times"]) if stat["times"] else 0
                print(f"{version}: {score:.2f}% error, {avg_time:.1f}s avg")
                if score < best_score:
                    best_score = score
                    best_version = version

        if best_version:
            print(f"\n✨ Recommended: {best_version} with {best_score:.2f}% average calorie error")

    def _save_results(self, results: List[dict]):
        """結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON保存（完全版 - VLM出力の詳細を含む）
        json_file = project_root / f"test_scripts/output/vlm_prompt_nutrition_comparison_{timestamp}.json"

        # 完全な結果を作成（Pipeline分析用）
        full_results = []
        for result in results:
            full_result = {
                "image_name": result["image_name"],
                "label_nutrition": result["label_nutrition"],
                "prompt_results": {}
            }
            for version, data in result["prompt_results"].items():
                if "error" in data:
                    full_result["prompt_results"][version] = {"error": data["error"]}
                else:
                    full_result["prompt_results"][version] = {
                        "total_nutrition": data["total_nutrition"],
                        "diff": data["diff"],
                        "dishes": data.get("dishes", []),  # 検出されたdishesとアイテムの詳細
                        "vlm_output": data.get("vlm_output", {})  # VLM raw output
                    }
            full_results.append(full_result)

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(full_results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {json_file}")

        # Markdownレポート生成
        self._generate_markdown_report(results, timestamp)

    def _generate_markdown_report(self, results: List[dict], timestamp: str):
        """Markdownレポートを生成"""
        md_file = project_root / f"test_scripts/output/vlm_prompt_nutrition_comparison_{timestamp}.md"

        md = []
        md.append("# VLMプロンプト栄養素比較レポート\n")
        md.append(f"**生成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
        md.append(f"**テスト画像数**: {len(results)}\n")

        # サマリー統計
        stats = {
            "v4_light": {"cal": [], "protein": [], "fat": [], "carbs": []},
            "v5_qwen3": {"cal": [], "protein": [], "fat": [], "carbs": []},
            "v5_streamlined": {"cal": [], "protein": [], "fat": [], "carbs": []}
        }

        for result in results:
            for version in stats.keys():
                if version in result["prompt_results"] and "error" not in result["prompt_results"][version]:
                    diff = result["prompt_results"][version]["diff"]
                    stats[version]["cal"].append(abs(diff["calorie"]["percent"]))
                    stats[version]["protein"].append(abs(diff["protein_g"]["percent"]))
                    stats[version]["fat"].append(abs(diff["fat_g"]["percent"]))
                    stats[version]["carbs"].append(abs(diff["carbs_g"]["percent"]))

        md.append("## 📊 サマリー\n")
        md.append("| プロンプト | カロリー誤差(%) | タンパク質誤差(%) | 脂質誤差(%) | 炭水化物誤差(%) | 30%以上誤差件数 |")
        md.append("|-----------|----------------|-----------------|------------|----------------|----------------|")

        for version, stat in stats.items():
            if stat["cal"]:
                avg_cal = statistics.mean(stat["cal"])
                avg_protein = statistics.mean(stat["protein"])
                avg_fat = statistics.mean(stat["fat"])
                avg_carbs = statistics.mean(stat["carbs"])
                high_error = sum(1 for e in stat["cal"] if e >= 30)

                md.append(f"| {version} | {avg_cal:.1f} | {avg_protein:.1f} | {avg_fat:.1f} | {avg_carbs:.1f} | {high_error} |")

        md.append("\n## 🏆 推奨事項\n")

        best_version = None
        best_score = float('inf')
        for version, stat in stats.items():
            if stat["cal"]:
                score = statistics.mean(stat["cal"])
                if score < best_score:
                    best_score = score
                    best_version = version

        if best_version:
            md.append(f"最も精度が高いプロンプトは **{best_version}** (平均カロリー誤差: {best_score:.1f}%)\n")

        md.append("")

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md))

        print(f"📄 Markdown report saved to: {md_file}")


async def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description='VLMプロンプト栄養素比較（並列処理対応）')
    parser.add_argument('--limit', type=int, default=None, help='テスト画像数の上限')
    parser.add_argument('--concurrency', type=int, default=5, help='同時処理する画像数（デフォルト5）')
    parser.add_argument('--prompts', nargs='+', default=None,
                        choices=list(VLMPromptNutritionComparator.AVAILABLE_PROMPTS.keys()),
                        help='使用するプロンプト（複数指定可）。デフォルト: v4_light v5_qwen3 v5_streamlined。'
                             '利用可能: %(choices)s')
    parser.add_argument('--model', type=str, default=None,
                        help='VLMモデルID（例: Qwen/Qwen3-VL-235B-A22B-Thinking）。'
                             'デフォルト: Qwen/Qwen3-VL-235B-A22B-Thinking')
    args = parser.parse_args()

    # 選択されたプロンプトを表示
    if args.prompts:
        print(f"🎯 選択されたプロンプト: {', '.join(args.prompts)}")
    else:
        print("🎯 デフォルトプロンプト: v4_light, v5_qwen3, v5_streamlined")

    # モデルIDを表示
    if args.model:
        print(f"🤖 使用モデル: {args.model}")
    else:
        print("🤖 使用モデル: デフォルト (Qwen/Qwen3-VL-235B-A22B-Thinking)")

    comparator = VLMPromptNutritionComparator(selected_prompts=args.prompts, model_id=args.model)
    await comparator.test_all_images(limit=args.limit, concurrency=args.concurrency)


if __name__ == "__main__":
    asyncio.run(main())
