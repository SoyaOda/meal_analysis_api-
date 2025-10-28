#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
30%以上誤差ケースの徹底分析
パイプラインの各ステップで何が問題か特定
"""

import json
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def analyze_single_case(case_data: dict, image_name: str) -> dict:
    """
    1ケースの詳細分析

    Args:
        case_data: JSON結果の1ケース分
        image_name: 画像ファイル名

    Returns:
        分析結果
    """
    label_nutrition = case_data["label_nutrition"]
    pipeline_result = case_data["pipeline_result"]

    # 1. Label料理リスト
    label_items = []
    for item in label_nutrition["items"]:
        label_items.append({
            "type": item["type"],
            "name": item["search_name"],
            "weight_g": item["weight_g"],
            "calories": item["nutrition"]["calorie"]
        })

    # 2. VLM認識結果
    vlm_response = pipeline_result.get("vlm_response", {})
    vlm_dishes = vlm_response.get("dishes", [])

    vlm_recognized_items = []
    for dish in vlm_dishes:
        main_food = dish.get("main_food")
        if main_food:
            vlm_recognized_items.append({
                "type": "main_food",
                "name": main_food.get("search_name"),
                "weight_g": main_food.get("weight_g", 0),
                "confidence": main_food.get("confidence", 0)
            })

        for extra in dish.get("extras", []):
            vlm_recognized_items.append({
                "type": "extra",
                "name": extra.get("search_name"),
                "weight_g": extra.get("weight_g", 0),
                "confidence": extra.get("confidence", 0)
            })

    # 3. USDA検索結果
    enriched_dishes = pipeline_result.get("enriched_dishes", [])

    usda_matches = []
    usda_failures = []

    for dish in enriched_dishes:
        # main_foodのUSDA検索
        main_food = dish.get("main_food")
        if main_food:
            usda_match = main_food.get("usda_match")
            if usda_match:
                usda_matches.append({
                    "type": "main_food",
                    "search_name": main_food.get("search_name"),
                    "matched_name": usda_match.get("matched_full_description"),
                    "rerank_score": usda_match.get("rerank_score", 0),
                    "weight_g": main_food.get("weight_g", 0),
                    "calories": main_food.get("nutrition", {}).get("calories", 0)
                })
            else:
                usda_failures.append({
                    "type": "main_food",
                    "search_name": main_food.get("search_name"),
                    "weight_g": main_food.get("weight_g", 0)
                })

        # extrasのUSDA検索
        for extra in dish.get("extras", []):
            usda_match = extra.get("usda_match")
            if usda_match:
                usda_matches.append({
                    "type": "extra",
                    "search_name": extra.get("search_name"),
                    "matched_name": usda_match.get("matched_full_description"),
                    "rerank_score": usda_match.get("rerank_score", 0),
                    "weight_g": extra.get("weight_g", 0),
                    "calories": extra.get("nutrition", {}).get("calories", 0)
                })
            else:
                usda_failures.append({
                    "type": "extra",
                    "search_name": extra.get("search_name"),
                    "weight_g": extra.get("weight_g", 0)
                })

    # 4. 栄養素差分
    label_cal = label_nutrition["total_calorie"]
    pipeline_cal = pipeline_result["total_nutrition"].get("calories", 0)
    cal_diff = pipeline_cal - label_cal
    cal_diff_pct = (cal_diff / label_cal * 100) if label_cal > 0 else 0

    # 5. 問題パターン分析
    problems = []

    # VLM認識の問題
    label_item_count = len(label_items)
    vlm_item_count = len(vlm_recognized_items)
    if vlm_item_count < label_item_count:
        problems.append(f"VLM認識不足: Label {label_item_count}品 → VLM {vlm_item_count}品")

    # 重量推定の問題
    label_total_weight = sum(item["weight_g"] for item in label_items)
    vlm_total_weight = sum(item["weight_g"] for item in vlm_recognized_items)
    weight_diff_pct = ((vlm_total_weight - label_total_weight) / label_total_weight * 100) if label_total_weight > 0 else 0
    if abs(weight_diff_pct) > 20:
        problems.append(f"重量推定誤差: {weight_diff_pct:+.1f}% (Label {label_total_weight}g → VLM {vlm_total_weight}g)")

    # USDA検索の問題
    if len(usda_failures) > 0:
        problems.append(f"USDA検索失敗: {len(usda_failures)}品")

    # reranker scoreが低い
    low_score_matches = [m for m in usda_matches if m["rerank_score"] < 0.8]
    if len(low_score_matches) > 0:
        problems.append(f"低reranker score: {len(low_score_matches)}品（<0.8）")

    return {
        "image_name": image_name,
        "calorie_diff": {
            "label": label_cal,
            "pipeline": pipeline_cal,
            "diff": cal_diff,
            "diff_pct": cal_diff_pct
        },
        "label_items": label_items,
        "vlm_recognized_items": vlm_recognized_items,
        "usda_matches": usda_matches,
        "usda_failures": usda_failures,
        "problems": problems
    }


def main():
    # JSON結果を読み込み
    json_file = "test_scripts/output/nutrition_comparison_all_50_20251026_220152.json"

    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    # 30%以上誤差ケースを抽出
    high_error_cases = []
    for r in results:
        label_cal = r["label_nutrition"]["total_calorie"]
        pipeline_cal = r["pipeline_result"]["total_nutrition"].get("calories", 0)
        cal_error_pct = ((pipeline_cal - label_cal) / label_cal) * 100 if label_cal > 0 else 0

        if abs(cal_error_pct) >= 30:
            analysis = analyze_single_case(r, r["image_name"])
            high_error_cases.append(analysis)

    # 誤差の大きい順にソート
    high_error_cases.sort(key=lambda x: abs(x["calorie_diff"]["diff_pct"]), reverse=True)

    print("=" * 100)
    print("30%以上誤差ケースの徹底分析")
    print("=" * 100)
    print()
    print(f"対象ケース数: {len(high_error_cases)}/50件")
    print()

    # 各ケースの詳細
    for i, case in enumerate(high_error_cases, 1):
        print("=" * 100)
        print(f"{i}. {case['image_name']}: カロリー誤差 {case['calorie_diff']['diff_pct']:+.1f}%")
        print("=" * 100)
        print(f"Label: {case['calorie_diff']['label']:.0f} kcal → Pipeline: {case['calorie_diff']['pipeline']:.0f} kcal")
        print()

        # 問題パターン
        print("【問題パターン】")
        for problem in case['problems']:
            print(f"  ⚠️  {problem}")
        print()

        # Label料理リスト
        print("【Label料理リスト】")
        for item in case['label_items']:
            print(f"  [{item['type']:10s}] {item['name']:40s} {item['weight_g']:4.0f}g ({item['calories']:4.0f} kcal)")
        print()

        # VLM認識結果
        print("【VLM認識結果】")
        if len(case['vlm_recognized_items']) == 0:
            print("  （認識なし）")
        else:
            for item in case['vlm_recognized_items']:
                print(f"  [{item['type']:10s}] {item['name']:40s} {item['weight_g']:4.0f}g (confidence: {item['confidence']:.2f})")
        print()

        # USDA検索結果
        print("【USDA検索結果】")
        print(f"  成功: {len(case['usda_matches'])}品")
        for match in case['usda_matches']:
            print(f"    [{match['type']:10s}] {match['search_name']:30s} → {match['matched_name']:50s}")
            print(f"                    rerank_score={match['rerank_score']:.3f}, weight={match['weight_g']:.0f}g, cal={match['calories']:.0f}kcal")

        if len(case['usda_failures']) > 0:
            print(f"  失敗: {len(case['usda_failures'])}品")
            for failure in case['usda_failures']:
                print(f"    [{failure['type']:10s}] {failure['search_name']:30s} (weight={failure['weight_g']:.0f}g)")
        print()

    # 問題パターンの統計
    print()
    print("=" * 100)
    print("【問題パターン統計】")
    print("=" * 100)
    print()

    pattern_counts = {}
    for case in high_error_cases:
        for problem in case['problems']:
            # パターンを抽出（最初の部分のみ）
            pattern = problem.split(':')[0]
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(high_error_cases)) * 100
        print(f"  {pattern:30s} {count:2d}件 ({pct:5.1f}%)")
    print()

    # JSON出力
    output_file = "test_scripts/output/30pct_error_analysis_detailed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(high_error_cases, f, indent=2, ensure_ascii=False)

    print(f"✅ 詳細分析結果保存: {output_file}")
    print()


if __name__ == "__main__":
    main()
