#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pipeline栄養素 vs VLM Label栄養素の比較 (全50画像)
Markdownレポート生成

Usage:
    # デフォルトモデル (Qwen3-VL-235B-A22B-Thinking)
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_scripts/compare_all_50_nutrition.py

    # カスタムモデル指定
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_scripts/compare_all_50_nutrition.py \
      --model Qwen/Qwen3-VL-30B-A3B-Thinking

Arguments:
    --model MODEL_ID    VLMモデルID (デフォルト: Qwen/Qwen3-VL-235B-A22B-Thinking)
"""

import json
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.freeform_usda_meal_analysis_api.services.pipeline import MealAnalysisPipeline


def load_label_nutrition(label_path: str) -> dict:
    """
    VLM Labelから栄養素を集計

    Args:
        label_path: images_label_with_nutrition/test_foodXX.json のパス

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


async def get_pipeline_nutrition(
    pipeline: MealAnalysisPipeline,
    image_path: str
) -> dict:
    """
    Pipelineで画像分析して栄養素を取得

    Args:
        pipeline: 初期化済みのMealAnalysisPipeline
        image_path: 画像ファイルパス

    Returns:
        Pipeline分析結果
    """
    # 画像を読み込み
    with open(image_path, 'rb') as f:
        image_bytes = f.read()

    # 分析実行 (async)
    result = await pipeline.analyze_image(
        image_bytes=image_bytes,
        image_mime_type="image/jpeg"
    )

    return {
        "total_nutrition": result.get("total_nutrition", {}),
        "enriched_dishes": result.get("dishes", []),  # pipeline.pyでは"dishes"
        "vlm_response": result.get("vlm_output", {}),  # pipeline.pyでは"vlm_output"
        "performance": result.get("performance", {}),
        "usage": result.get("usage", {})
    }


def calculate_diff(label: dict, pipeline: dict) -> dict:
    """
    差分計算

    Args:
        label: label栄養素
        pipeline: pipeline栄養素 (total_nutrition)

    Returns:
        差分情報
    """
    pipeline_calories = pipeline.get('calories') or pipeline.get('calorie', 0)

    diff_cal = pipeline_calories - label['total_calorie']
    diff_protein = pipeline.get('protein_g', 0) - label['total_protein_g']
    diff_fat = pipeline.get('fat_g', 0) - label['total_fat_g']
    diff_carbs = pipeline.get('carbs_g', 0) - label['total_carbs_g']

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


def generate_markdown_report(results: List[dict], output_path: str):
    """
    Markdownレポート生成

    Args:
        results: 比較結果リスト
        output_path: 出力ファイルパス
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = []
    md.append("# Pipeline vs VLM Label 栄養素比較レポート")
    md.append(f"\n生成日時: {timestamp}\n")
    md.append(f"対象画像数: {len(results)}\n")

    # サマリー統計
    md.append("## サマリー\n")

    avg_cal_diff = sum(r['diff']['calorie']['percent'] for r in results) / len(results)
    avg_protein_diff = sum(r['diff']['protein_g']['percent'] for r in results) / len(results)
    avg_fat_diff = sum(r['diff']['fat_g']['percent'] for r in results) / len(results)
    avg_carbs_diff = sum(r['diff']['carbs_g']['percent'] for r in results) / len(results)

    md.append("### 平均差分（Pipeline - Label）\n")
    md.append("| 栄養素 | 平均差分 (%) |")
    md.append("|--------|--------------|")
    md.append(f"| カロリー | {avg_cal_diff:+.1f}% |")
    md.append(f"| タンパク質 | {avg_protein_diff:+.1f}% |")
    md.append(f"| 脂質 | {avg_fat_diff:+.1f}% |")
    md.append(f"| 炭水化物 | {avg_carbs_diff:+.1f}% |")
    md.append("")

    # 詳細比較表
    md.append("## 詳細比較表\n")
    md.append("| 画像 | Label Cal | Pipeline Cal | 差分 | Label P | Pipeline P | 差分 | Label F | Pipeline F | 差分 | Label C | Pipeline C | 差分 |")
    md.append("|------|-----------|--------------|------|---------|------------|------|---------|------------|------|---------|------------|------|")

    for r in results:
        label_nut = r['label_nutrition']
        pipeline_nut = r['pipeline_result']['total_nutrition']
        diff = r['diff']

        pipeline_calories = pipeline_nut.get('calories') or pipeline_nut.get('calorie', 0)

        md.append(
            f"| {r['image_name']} | "
            f"{label_nut['total_calorie']:.0f} | "
            f"{pipeline_calories:.0f} | "
            f"{diff['calorie']['percent']:+.1f}% | "
            f"{label_nut['total_protein_g']:.1f} | "
            f"{pipeline_nut.get('protein_g', 0):.1f} | "
            f"{diff['protein_g']['percent']:+.1f}% | "
            f"{label_nut['total_fat_g']:.1f} | "
            f"{pipeline_nut.get('fat_g', 0):.1f} | "
            f"{diff['fat_g']['percent']:+.1f}% | "
            f"{label_nut['total_carbs_g']:.1f} | "
            f"{pipeline_nut.get('carbs_g', 0):.1f} | "
            f"{diff['carbs_g']['percent']:+.1f}% |"
        )

    md.append("")

    # 個別詳細
    md.append("## 個別詳細\n")

    for r in results:
        md.append(f"### {r['image_name']}\n")

        # Label
        md.append("**VLM Label栄養素**\n")
        md.append("| Type | Food | Weight | Cal | P | F | C |")
        md.append("|------|------|--------|-----|---|---|---|")

        for item in r['label_nutrition']['items']:
            nut = item['nutrition']
            md.append(
                f"| {item['type']} | {item['search_name']} | {item['weight_g']}g | "
                f"{nut.get('calorie', 0):.0f} | {nut.get('protein_g', 0):.1f}g | "
                f"{nut.get('fat_g', 0):.1f}g | {nut.get('carbs_g', 0):.1f}g |"
            )

        label_nut = r['label_nutrition']
        md.append(
            f"| **合計** | - | - | "
            f"**{label_nut['total_calorie']:.0f}** | **{label_nut['total_protein_g']:.1f}g** | "
            f"**{label_nut['total_fat_g']:.1f}g** | **{label_nut['total_carbs_g']:.1f}g** |"
        )
        md.append("")

        # Pipeline
        pipeline_nut = r['pipeline_result']['total_nutrition']
        pipeline_calories = pipeline_nut.get('calories') or pipeline_nut.get('calorie', 0)

        md.append("**Pipeline栄養素**\n")
        md.append(
            f"合計: {pipeline_calories:.0f} kcal, "
            f"P: {pipeline_nut.get('protein_g', 0):.1f}g, "
            f"F: {pipeline_nut.get('fat_g', 0):.1f}g, "
            f"C: {pipeline_nut.get('carbs_g', 0):.1f}g\n"
        )

        # 差分
        diff = r['diff']
        md.append("**差分 (Pipeline - Label)**\n")
        md.append(
            f"- カロリー: {diff['calorie']['diff']:+.1f} kcal ({diff['calorie']['percent']:+.1f}%)\n"
            f"- タンパク質: {diff['protein_g']['diff']:+.1f}g ({diff['protein_g']['percent']:+.1f}%)\n"
            f"- 脂質: {diff['fat_g']['diff']:+.1f}g ({diff['fat_g']['percent']:+.1f}%)\n"
            f"- 炭水化物: {diff['carbs_g']['diff']:+.1f}g ({diff['carbs_g']['percent']:+.1f}%)\n"
        )

        md.append("---\n")

    # ファイル出力
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print(f"✅ Markdownレポート生成: {output_path}")


async def process_single_image(
    pipeline: MealAnalysisPipeline,
    image_index: int,
    semaphore: asyncio.Semaphore
) -> dict:
    """
    1画像を処理（並行制御あり）

    Args:
        pipeline: 初期化済みのPipeline
        image_index: 画像番号 (1-50)
        semaphore: 並行数制御用セマフォ

    Returns:
        処理結果辞書
    """
    async with semaphore:
        image_name = f"test_food{image_index}.jpg"
        image_path = f"test_images/images/{image_name}"
        label_path = f"test_images/images_label_with_nutrition/test_food{image_index:02d}.json"

        try:
            # Label読み込み
            label_nutrition = load_label_nutrition(label_path)

            # Pipeline実行
            pipeline_result = await get_pipeline_nutrition(pipeline, image_path)

            # 差分計算
            diff = calculate_diff(label_nutrition, pipeline_result['total_nutrition'])

            pipeline_calories = pipeline_result['total_nutrition'].get('calories') or \
                                pipeline_result['total_nutrition'].get('calorie', 0)

            print(f"✅ [{image_index}/50] {image_name}: "
                  f"Label {label_nutrition['total_calorie']:.0f} kcal | "
                  f"Pipeline {pipeline_calories:.0f} kcal | "
                  f"差分 {diff['calorie']['percent']:+.1f}%")

            return {
                "image_name": image_name,
                "label_nutrition": label_nutrition,
                "pipeline_result": pipeline_result,
                "diff": diff
            }

        except Exception as e:
            print(f"❌ [{image_index}/50] {image_name}: エラー - {e}")
            return None


async def main():
    # コマンドライン引数の解析
    import argparse
    parser = argparse.ArgumentParser(
        description="Pipeline栄養素 vs VLM Label栄養素の比較 (全50画像)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen3-VL-235B-A22B-Thinking",
        help="VLMモデルID (デフォルト: Qwen/Qwen3-VL-235B-A22B-Thinking)"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("Pipeline vs VLM Label 栄養素比較 (全50画像)")
    print("=" * 80)
    print()

    # Pipeline初期化 (1回のみ)
    print("Pipeline初期化中...")
    print(f"VLMモデル: {args.model}")
    index_dir = "test_scripts/query_system/data"
    usda_survey_file = "usda_database/surveyDownload.json"
    usda_foundation_file = "usda_database/FoodData_Central_foundation_food_json_2025-04-24 2.json"
    usda_sr_legacy_file = "usda_database/FoodData_Central_sr_legacy_food_json_2018-04 2.json"

    pipeline = MealAnalysisPipeline(
        vlm_model_id=args.model,
        index_dir=index_dir,
        usda_survey_file=usda_survey_file,
        usda_foundation_file=usda_foundation_file,
        usda_sr_legacy_file=usda_sr_legacy_file
    )
    print("✅ Pipeline初期化完了")
    print()

    # 並行処理設定（DeepInfraの制限: 200並行/モデル、安全のため10並行に制限）
    MAX_CONCURRENT = 10
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    print(f"🚀 並行処理開始（最大{MAX_CONCURRENT}並行）")
    print()

    # 全50画像を並行処理
    tasks = [
        process_single_image(pipeline, i, semaphore)
        for i in range(1, 51)
    ]

    # 並行実行
    results_raw = await asyncio.gather(*tasks)

    # Noneを除外し、画像名でソート
    results = [r for r in results_raw if r is not None]
    results.sort(key=lambda x: x["image_name"])

    print()
    print(f"✅ 処理完了: {len(results)}/{50}画像")
    print()

    # Markdownレポート生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_output = f"test_scripts/output/nutrition_comparison_all_50_{timestamp}.md"
    generate_markdown_report(results, md_output)

    # JSON詳細結果も保存
    json_output = f"test_scripts/output/nutrition_comparison_all_50_{timestamp}.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ JSON詳細結果保存: {json_output}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
