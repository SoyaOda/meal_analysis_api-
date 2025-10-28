#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
30%以上の誤差ケースの詳細分析
パイプラインのどの部分が問題なのかを特定
"""

import json
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def analyze_case(case: dict) -> dict:
    """
    1ケースの詳細分析

    Returns:
        問題の種類と詳細
    """
    image_name = case["image_name"]
    label = case["label_nutrition"]
    pipeline = case["pipeline_result"]["total_nutrition"]

    # カロリー誤差率
    label_cal = label["total_calorie"]
    pipeline_cal = pipeline.get("calories") or pipeline.get("calorie", 0)
    cal_error_pct = ((pipeline_cal - label_cal) / label_cal) * 100 if label_cal > 0 else 0

    # VLM出力チェック
    vlm_dishes = case["pipeline_result"].get("vlm_output", {}).get("dishes", [])
    enriched_dishes = case["pipeline_result"].get("enriched_dishes", [])

    # Label items
    label_items = {item["search_name"]: item for item in label["items"]}

    # 問題分析
    problems = []

    # 1. VLMが認識した料理の数
    vlm_dish_count = len(vlm_dishes)
    label_main_count = len([i for i in label["items"] if i["type"] == "main_food"])
    label_extra_count = len([i for i in label["items"] if i["type"] == "extra"])

    if vlm_dish_count < label_main_count + label_extra_count:
        problems.append(f"VLM認識不足: VLM={vlm_dish_count}, Label={label_main_count + label_extra_count}")
    elif vlm_dish_count > label_main_count + label_extra_count:
        problems.append(f"VLM過剰認識: VLM={vlm_dish_count}, Label={label_main_count + label_extra_count}")

    # 2. VLMの料理名とLabelの比較
    vlm_food_names = [d.get("main_food", "") for d in vlm_dishes]
    label_food_names = [item["search_name"] for item in label["items"]]

    missing_foods = []
    for label_food in label_food_names:
        if not any(label_food.lower() in vlm_name.lower() or vlm_name.lower() in label_food.lower()
                   for vlm_name in vlm_food_names):
            missing_foods.append(label_food)

    if missing_foods:
        problems.append(f"VLM認識漏れ: {', '.join(missing_foods)}")

    # 3. USDA検索結果の確認
    search_issues = []
    for i, enriched in enumerate(enriched_dishes):
        vlm_dish = vlm_dishes[i] if i < len(vlm_dishes) else {}
        usda_match = enriched.get("usda_match", {})

        if not usda_match:
            search_issues.append(f"{vlm_dish.get('main_food', 'unknown')}: USDA検索失敗")
            continue

        # Reranker scoreが低い場合
        score = usda_match.get("reranker_score", 0)
        if score < 0.5:
            search_issues.append(f"{vlm_dish.get('main_food', 'unknown')}: 低reranker score ({score:.3f})")

    if search_issues:
        problems.append(f"USDA検索問題: {'; '.join(search_issues)}")

    # 4. 重量推定の確認
    weight_issues = []
    for i, enriched in enumerate(enriched_dishes):
        vlm_dish = vlm_dishes[i] if i < len(vlm_dishes) else {}
        vlm_weight = vlm_dish.get("weight_g", 0)

        # Labelから対応する料理を探す
        main_food = vlm_dish.get("main_food", "")
        matching_label = None
        for label_name, label_item in label_items.items():
            if label_name.lower() in main_food.lower() or main_food.lower() in label_name.lower():
                matching_label = label_item
                break

        if matching_label:
            label_weight = matching_label["weight_g"]
            weight_error_pct = ((vlm_weight - label_weight) / label_weight) * 100 if label_weight > 0 else 0
            if abs(weight_error_pct) > 50:
                weight_issues.append(f"{main_food}: VLM={vlm_weight}g, Label={label_weight}g ({weight_error_pct:+.1f}%)")

    if weight_issues:
        problems.append(f"重量推定問題: {'; '.join(weight_issues)}")

    # 5. 栄養素パターンの確認
    label_p = label["total_protein_g"]
    label_f = label["total_fat_g"]
    label_c = label["total_carbs_g"]

    pipeline_p = pipeline.get("protein_g", 0)
    pipeline_f = pipeline.get("fat_g", 0)
    pipeline_c = pipeline.get("carbs_g", 0)

    p_error_pct = ((pipeline_p - label_p) / label_p) * 100 if label_p > 0 else 0
    f_error_pct = ((pipeline_f - label_f) / label_f) * 100 if label_f > 0 else 0
    c_error_pct = ((pipeline_c - label_c) / label_c) * 100 if label_c > 0 else 0

    # 極端なバランスのずれ
    if abs(f_error_pct) > 50:
        problems.append(f"脂質推定問題: {f_error_pct:+.1f}%")
    if abs(c_error_pct) > 50:
        problems.append(f"炭水化物推定問題: {c_error_pct:+.1f}%")

    return {
        "image_name": image_name,
        "cal_error_pct": cal_error_pct,
        "problems": problems,
        "vlm_dish_count": vlm_dish_count,
        "label_item_count": len(label["items"]),
        "nutrition_errors": {
            "protein": p_error_pct,
            "fat": f_error_pct,
            "carbs": c_error_pct
        }
    }


def main():
    # 最新のJSONファイルを読み込み
    json_file = "test_scripts/output/nutrition_comparison_all_50_20251026_214129.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    print("=" * 100)
    print("30%以上の誤差ケース詳細分析")
    print("=" * 100)
    print()

    # 30%以上の誤差を持つケースを抽出
    high_error_cases = []
    for case in results:
        label_cal = case["label_nutrition"]["total_calorie"]
        pipeline_cal = case["pipeline_result"]["total_nutrition"].get("calories") or \
                       case["pipeline_result"]["total_nutrition"].get("calorie", 0)
        cal_error_pct = ((pipeline_cal - label_cal) / label_cal) * 100 if label_cal > 0 else 0

        if abs(cal_error_pct) >= 30:
            high_error_cases.append(case)

    print(f"対象ケース数: {len(high_error_cases)}/{len(results)}")
    print()

    # 問題パターンの集計
    problem_counts = {
        "VLM認識不足": 0,
        "VLM過剰認識": 0,
        "VLM認識漏れ": 0,
        "USDA検索問題": 0,
        "重量推定問題": 0,
        "脂質推定問題": 0,
        "炭水化物推定問題": 0
    }

    # 各ケースの分析
    analyses = []
    for case in high_error_cases:
        analysis = analyze_case(case)
        analyses.append(analysis)

        # 問題カウント
        for problem in analysis["problems"]:
            for key in problem_counts.keys():
                if key in problem:
                    problem_counts[key] += 1
                    break

    # 問題パターン別のサマリー
    print("【問題パターン別発生頻度】")
    print("-" * 100)
    for key, count in sorted(problem_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / len(high_error_cases)) * 100
            print(f"{key}: {count}件 ({pct:.1f}%)")
    print()

    # 各ケースの詳細
    print("【各ケースの詳細分析】")
    print("-" * 100)
    for analysis in sorted(analyses, key=lambda x: abs(x["cal_error_pct"]), reverse=True):
        print(f"\n{analysis['image_name']}: カロリー誤差 {analysis['cal_error_pct']:+.1f}%")
        print(f"  VLM料理数: {analysis['vlm_dish_count']}, Label項目数: {analysis['label_item_count']}")
        print(f"  栄養素誤差: P={analysis['nutrition_errors']['protein']:+.1f}%, " +
              f"F={analysis['nutrition_errors']['fat']:+.1f}%, " +
              f"C={analysis['nutrition_errors']['carbs']:+.1f}%")

        if analysis["problems"]:
            print("  問題点:")
            for problem in analysis["problems"]:
                print(f"    - {problem}")
        else:
            print("  問題点: 特定できず（全体的なバランス誤差）")

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()
