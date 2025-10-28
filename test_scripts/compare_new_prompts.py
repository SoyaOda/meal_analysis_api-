#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
新しい3つの改善版プロンプトと既存プロンプトを比較
"""

import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any
import statistics
import argparse
import sys
sys.path.append('/Users/odasoya/meal_analysis_api_2')

from apps.freeform_usda_meal_analysis_api.services.pipeline import MealAnalysisPipeline

# テスト対象のプロンプトバージョン
PROMPT_VERSIONS = {
    "v5_streamlined": "freeform_prompt_usda_format_ver_v5_streamlined_20251027.txt",
    "v6_balanced": "freeform_prompt_usda_format_ver_v6_balanced_20251027.txt",
    "v6_corrected": "freeform_prompt_usda_format_ver_v6_corrected_20251027.txt",
    "v6_enhanced": "freeform_prompt_usda_format_ver_v6_enhanced_20251027.txt",
}

# パイプライン設定
PIPELINE_CONFIG = {
    "index_dir": "test_scripts/query_system/data",
    "usda_survey_file": "usda_database/surveyDownload.json",
    "usda_foundation_file": "usda_database/FoodData_Central_foundation_food_json_2025-04-24 2.json",
    "usda_sr_legacy_file": "usda_database/FoodData_Central_sr_legacy_food_json_2018-04 2.json",
    "weight_main": 0.0,
    "weight_full": 1.0,
}

async def process_single_image(label_file: str, idx: int, total: int, pipelines: Dict, concurrency: int = 1):
    """単一画像を全プロンプトで処理（並列処理対応）"""

    # ラベルデータを読み込み
    with open(label_file, 'r', encoding='utf-8') as f:
        label = json.load(f)

    image_name = label_file.name
    # 画像パスを修正（test_food01.json → test_food1.jpg）
    image_filename = image_name.replace('.json', '.jpg').replace('test_food0', 'test_food')
    image_path = Path("test_images/images") / image_filename

    if not image_path.exists():
        print(f"  ⚠️  画像が見つかりません: {image_path}")
        return None

    print(f"\n[{idx}/{total}] 📷 {image_name}")

    # ラベルから栄養素を集計
    total_calorie = 0.0
    total_protein_g = 0.0
    total_fat_g = 0.0
    total_carbs_g = 0.0
    items = []

    for dish in label.get("dishes", []):
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

    # 結果を格納
    image_result = {
        "image_name": image_name,
        "label_nutrition": {
            "total_calorie": total_calorie,
            "total_protein_g": total_protein_g,
            "total_fat_g": total_fat_g,
            "total_carbs_g": total_carbs_g,
            "items": items
        },
        "prompt_results": {},
        "processing_time": {},
        "total_processing_time": 0
    }

    # セマフォーを使った並列処理
    semaphore = asyncio.Semaphore(concurrency)

    async def process_prompt(version: str, pipeline):
        async with semaphore:
            start_time = time.time()

            try:
                # 非同期メソッドを直接呼び出し
                result = await pipeline.analyze_image(str(image_path))

                # 結果を処理
                total_nutrition = {
                    "calories": 0,
                    "protein_g": 0,
                    "fat_g": 0,
                    "carbs_g": 0
                }

                dishes_data = []

                for dish in result.get("dishes", []):
                    dish_data = {}

                    # main_food の処理
                    if dish.get("main_food"):
                        mf = dish["main_food"]
                        if mf.get("nutrition"):
                            for key in total_nutrition:
                                total_nutrition[key] += mf["nutrition"].get(key.replace("_g", ""), 0)
                        dish_data["main_food"] = mf
                    else:
                        dish_data["main_food"] = None

                    # extras の処理
                    dish_data["extras"] = []
                    for extra in dish.get("extras", []):
                        if extra.get("nutrition"):
                            for key in total_nutrition:
                                total_nutrition[key] += extra["nutrition"].get(key.replace("_g", ""), 0)
                        dish_data["extras"].append(extra)

                    dishes_data.append(dish_data)

                # 誤差計算（image_result["label_nutrition"]から参照）
                label_cal = image_result["label_nutrition"]["total_calorie"]
                label_pro = image_result["label_nutrition"]["total_protein_g"]
                label_fat = image_result["label_nutrition"]["total_fat_g"]
                label_carbs = image_result["label_nutrition"]["total_carbs_g"]

                diff = {
                    "calorie": {
                        "absolute": total_nutrition["calories"] - label_cal,
                        "percent": ((total_nutrition["calories"] - label_cal) /
                                  label_cal * 100) if label_cal > 0 else 0
                    },
                    "protein": {
                        "absolute": total_nutrition["protein_g"] - label_pro,
                        "percent": ((total_nutrition["protein_g"] - label_pro) /
                                  label_pro * 100) if label_pro > 0 else 0
                    },
                    "fat": {
                        "absolute": total_nutrition["fat_g"] - label_fat,
                        "percent": ((total_nutrition["fat_g"] - label_fat) /
                                  label_fat * 100) if label_fat > 0 else 0
                    },
                    "carbs": {
                        "absolute": total_nutrition["carbs_g"] - label_carbs,
                        "percent": ((total_nutrition["carbs_g"] - label_carbs) /
                                  label_carbs * 100) if label_carbs > 0 else 0
                    }
                }

                processing_time = time.time() - start_time

                return version, {
                    "data": result,
                    "total_nutrition": total_nutrition,
                    "dishes": dishes_data,
                    "diff": diff,
                    "processing_time": round(processing_time, 2)
                }

            except Exception as e:
                processing_time = time.time() - start_time
                return version, {
                    "error": str(e),
                    "processing_time": round(processing_time, 2)
                }

    # 全プロンプトを並列処理
    total_start_time = time.time()
    tasks = []
    for version, pipeline in pipelines.items():
        task = process_prompt(version, pipeline)
        tasks.append(task)

    # 全タスクを実行
    results = await asyncio.gather(*tasks)

    # 結果を格納
    for version, result in results:
        image_result["prompt_results"][version] = result
        image_result["processing_time"][version] = result.get("processing_time", 0)

        # 結果を表示
        if "error" in result:
            print(f"    {version:15s}: ❌ エラー: {result['error'][:50]}")
        else:
            diff = result["diff"]["calorie"]["percent"]
            p_diff = result["diff"]["protein"]["percent"]
            f_diff = result["diff"]["fat"]["percent"]
            c_diff = result["diff"]["carbs"]["percent"]

            # エラーレベルに応じて色分け
            if abs(diff) < 20:
                symbol = "✅"
            elif abs(diff) < 30:
                symbol = "⚠️"
            else:
                symbol = "❌"

            print(f"    {version:15s}: {symbol} Cal {diff:+6.1f}%, P {p_diff:+6.1f}%, F {f_diff:+6.1f}%, C {c_diff:+6.1f}%")

    image_result["total_processing_time"] = round(time.time() - total_start_time, 2)

    return image_result

async def main():
    """メイン処理"""

    parser = argparse.ArgumentParser(description='VLMプロンプトの栄養推定精度比較（新バージョン）')
    parser.add_argument('--limit', type=int, default=3, help='テストする画像数（デフォルト: 3）')
    parser.add_argument('--concurrency', type=int, default=2, help='並列実行数（デフォルト: 2）')
    args = parser.parse_args()

    print("\n🚀 新VLMプロンプト比較テスト")
    print("=" * 80)
    print(f"📋 比較対象: {len(PROMPT_VERSIONS)}プロンプト")
    for version in PROMPT_VERSIONS.keys():
        prefix = "🆕" if "v6" in version else "📌"
        print(f"   {prefix} {version}")
    print("=" * 80)

    # パイプラインを初期化
    print("\n🔄 パイプライン初期化中...")
    pipelines = {}
    for version, prompt_file in PROMPT_VERSIONS.items():
        print(f"  {version}...")
        pipeline = MealAnalysisPipeline(
            vlm_prompt_file=f"apps/freeform_usda_meal_analysis_api/prompts/{prompt_file}",
            **PIPELINE_CONFIG
        )
        pipelines[version] = pipeline
    print("✅ 初期化完了")

    # テスト画像を取得（正しいパス）
    label_dir = Path("test_images/images_label_with_nutrition")
    label_files = sorted(label_dir.glob("test_food*.json"))[:args.limit]

    # 全画像を処理
    all_results = []
    for idx, label_file in enumerate(label_files, 1):
        result = await process_single_image(label_file, idx, len(label_files), pipelines, args.concurrency)
        if result:
            all_results.append(result)

    # 統計分析
    print("\n" + "=" * 80)
    print("📊 統計分析")
    print("=" * 80)

    # 各プロンプトの統計
    stats = {version: {"errors": [], "high_errors": 0} for version in PROMPT_VERSIONS.keys()}

    for result in all_results:
        for version in PROMPT_VERSIONS.keys():
            if version in result["prompt_results"]:
                pr = result["prompt_results"][version]
                if "diff" in pr:
                    error = abs(pr["diff"]["calorie"]["percent"])
                    stats[version]["errors"].append(error)
                    if error >= 30:
                        stats[version]["high_errors"] += 1

    print("\n📈 カロリー誤差統計")
    print("-" * 80)
    print(f"{'Version':<15} | {'平均誤差':<10} | {'中央値':<10} | {'最大誤差':<10} | {'30%以上':<10}")
    print("-" * 80)

    best_version = None
    best_error = float('inf')

    for version in PROMPT_VERSIONS.keys():
        if stats[version]["errors"]:
            avg_error = statistics.mean(stats[version]["errors"])
            median_error = statistics.median(stats[version]["errors"])
            max_error = max(stats[version]["errors"])
            high_count = stats[version]["high_errors"]

            # 新バージョンはマーク
            mark = "🆕" if "v6" in version else "  "

            print(f"{version:<15} | {avg_error:>9.1f}% | {median_error:>9.1f}% | {max_error:>9.1f}% | {high_count:>9}件 {mark}")

            if avg_error < best_error:
                best_error = avg_error
                best_version = version

    # 改善率を計算
    if "v5_streamlined" in stats and stats["v5_streamlined"]["errors"]:
        baseline = statistics.mean(stats["v5_streamlined"]["errors"])

        print("\n📊 v5_streamlinedからの改善率")
        print("-" * 50)

        for version in ["v6_balanced", "v6_corrected", "v6_enhanced"]:
            if version in stats and stats[version]["errors"]:
                new_avg = statistics.mean(stats[version]["errors"])
                improvement = ((baseline - new_avg) / baseline * 100)

                if improvement > 0:
                    symbol = "✅"
                else:
                    symbol = "❌"

                print(f"{version}: {improvement:+.1f}% {symbol}")

    print("\n🏆 ベストパフォーマンス")
    print("-" * 50)
    if best_version:
        print(f"✨ {best_version}: 平均誤差 {best_error:.1f}%")

    # 結果をJSON保存
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"test_scripts/output/new_prompts_comparison_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 結果を保存: {output_file}")
if __name__ == "__main__":
    asyncio.run(main())