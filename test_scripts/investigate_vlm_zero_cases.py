#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VLM認識0料理ケースの徹底調査
なぜカロリーが計算されているのか？どこから来ているのか？
"""

import json
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def investigate_case(case: dict) -> dict:
    """
    VLM認識0料理ケースの詳細調査
    """
    image_name = case["image_name"]
    vlm_output = case["pipeline_result"].get("vlm_output", {})
    vlm_dishes = vlm_output.get("dishes", [])
    enriched_dishes = case["pipeline_result"].get("enriched_dishes", [])
    total_nutrition = case["pipeline_result"]["total_nutrition"]

    # カロリーの出所
    cal_sources = []

    # 1. VLM出力全体を確認
    vlm_str = json.dumps(vlm_output, ensure_ascii=False)
    vlm_keys = list(vlm_output.keys())

    # 2. enriched_dishesの確認
    enriched_count = len(enriched_dishes)
    usda_match_count = sum(1 for e in enriched_dishes if e.get("usda_match"))

    # 3. total_nutritionの内訳
    nutrition_details = {
        "calories": total_nutrition.get("calories", total_nutrition.get("calorie", 0)),
        "protein_g": total_nutrition.get("protein_g", 0),
        "fat_g": total_nutrition.get("fat_g", 0),
        "carbs_g": total_nutrition.get("carbs_g", 0)
    }

    # 4. enriched_dishesの栄養素合計
    enriched_cal = 0
    enriched_p = 0
    enriched_f = 0
    enriched_c = 0

    for e in enriched_dishes:
        usda = e.get("usda_match", {})
        if usda:
            nutrients = usda.get("nutrients", {})
            weight = e.get("weight_g", 0)
            # per 100gの栄養素を重量に応じて計算
            enriched_cal += nutrients.get("Energy", {}).get("value", 0) * weight / 100
            enriched_p += nutrients.get("Protein", {}).get("value", 0) * weight / 100
            enriched_f += nutrients.get("Total lipid (fat)", {}).get("value", 0) * weight / 100
            enriched_c += nutrients.get("Carbohydrate, by difference", {}).get("value", 0) * weight / 100

    return {
        "image_name": image_name,
        "vlm_dish_count": len(vlm_dishes),
        "vlm_keys": vlm_keys,
        "enriched_dish_count": enriched_count,
        "usda_match_count": usda_match_count,
        "total_nutrition": nutrition_details,
        "enriched_nutrition": {
            "calories": enriched_cal,
            "protein_g": enriched_p,
            "fat_g": enriched_f,
            "carbs_g": enriched_c
        },
        "nutrition_match": abs(nutrition_details["calories"] - enriched_cal) < 1
    }


def main():
    # 過去のレポート（正常動作時）
    json_file = "test_scripts/output/nutrition_comparison_all_50_20251026_200915.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    print("=" * 100)
    print("VLM認識0料理ケースの徹底調査")
    print("=" * 100)
    print()

    # VLM認識0料理ケースを抽出
    zero_cases = []
    for case in results:
        vlm_dishes = case["pipeline_result"].get("vlm_output", {}).get("dishes", [])
        if len(vlm_dishes) == 0:
            zero_cases.append(case)

    print(f"VLM認識0料理ケース数: {len(zero_cases)}/{len(results)}")
    print()

    # 各ケースの調査
    investigations = []
    for case in zero_cases:
        investigation = investigate_case(case)
        investigations.append(investigation)

    # パターン分析
    has_enriched = sum(1 for i in investigations if i["enriched_dish_count"] > 0)
    has_usda_match = sum(1 for i in investigations if i["usda_match_count"] > 0)
    nutrition_from_enriched = sum(1 for i in investigations if i["nutrition_match"])

    print("【パターン分析】")
    print("-" * 100)
    print(f"enriched_dishesが存在: {has_enriched}/{len(investigations)}")
    print(f"USDA matchが存在: {has_usda_match}/{len(investigations)}")
    print(f"栄養素がenriched_dishesから計算: {nutrition_from_enriched}/{len(investigations)}")
    print()

    # 詳細
    print("【個別ケース詳細】")
    print("-" * 100)
    for inv in investigations:
        print(f"\n{inv['image_name']}")
        print(f"  VLM dishes: {inv['vlm_dish_count']}")
        print(f"  VLM keys: {inv['vlm_keys']}")
        print(f"  Enriched dishes: {inv['enriched_dish_count']}")
        print(f"  USDA match: {inv['usda_match_count']}")
        print(f"  Total nutrition: {inv['total_nutrition']['calories']:.0f} kcal")
        print(f"  Enriched nutrition: {inv['enriched_nutrition']['calories']:.0f} kcal")
        print(f"  Match: {'✅' if inv['nutrition_match'] else '❌'}")

        if not inv['nutrition_match'] and inv['total_nutrition']['calories'] > 0:
            print(f"  ⚠️  栄養素の出所不明（{inv['total_nutrition']['calories']:.0f} kcalがどこから？）")

    print()
    print("=" * 100)

    # 結論
    print("\n【結論】")
    print("-" * 100)
    if has_enriched == 0:
        print("❌ VLM認識0の場合、enriched_dishesも0 → パイプラインが完全に失敗")
    else:
        print("⚠️  VLM認識0でもenriched_dishesが存在 → フォールバックロジックが動作中？")

    if has_usda_match > 0:
        print("⚠️  VLM認識0でもUSDA matchが存在 → デフォルト値や推測が使用されている可能性")

    print()


if __name__ == "__main__":
    main()
