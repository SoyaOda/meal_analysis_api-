#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2つのレポートを比較して、30%以上誤差ケースの詳細分析
"""

import json
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def extract_high_error_cases(results):
    """30%以上の誤差ケースを抽出"""
    high_error_cases = []
    for case in results:
        label_cal = case["label_nutrition"]["total_calorie"]
        pipeline_cal = case["pipeline_result"]["total_nutrition"].get("calories") or \
                       case["pipeline_result"]["total_nutrition"].get("calorie", 0)
        cal_error_pct = ((pipeline_cal - label_cal) / label_cal) * 100 if label_cal > 0 else 0

        if abs(cal_error_pct) >= 30:
            high_error_cases.append({
                "image_name": case["image_name"],
                "cal_error_pct": cal_error_pct,
                "label_cal": label_cal,
                "pipeline_cal": pipeline_cal,
                "vlm_dishes": case["pipeline_result"].get("vlm_output", {}).get("dishes", []),
                "enriched_dishes": case["pipeline_result"].get("enriched_dishes", [])
            })
    return high_error_cases


def main():
    # 過去のレポート（正常動作時）
    past_json = "test_scripts/output/nutrition_comparison_all_50_20251026_200915.json"
    # 最新のレポート（VLM失敗）
    current_json = "test_scripts/output/nutrition_comparison_all_50_20251026_214129.json"

    with open(past_json, 'r', encoding='utf-8') as f:
        past_results = json.load(f)

    with open(current_json, 'r', encoding='utf-8') as f:
        current_results = json.load(f)

    past_high_errors = extract_high_error_cases(past_results)
    current_high_errors = extract_high_error_cases(current_results)

    print("=" * 100)
    print("過去 vs 現在のレポート比較")
    print("=" * 100)
    print()
    print(f"過去レポート (20251026_200915): 30%以上誤差 {len(past_high_errors)}件")
    print(f"現在レポート (20251026_214129): 30%以上誤差 {len(current_high_errors)}件")
    print()

    # 過去レポートの30%以上誤差ケースを詳細分析
    print("【過去レポートの30%以上誤差ケース詳細】")
    print("-" * 100)

    for case in sorted(past_high_errors, key=lambda x: abs(x["cal_error_pct"]), reverse=True):
        print(f"\n{case['image_name']}: カロリー誤差 {case['cal_error_pct']:+.1f}%")
        print(f"  Label: {case['label_cal']:.0f} kcal → Pipeline: {case['pipeline_cal']:.0f} kcal")
        print(f"  VLM認識料理数: {len(case['vlm_dishes'])}")

        if len(case['vlm_dishes']) == 0:
            print("  ❌ VLM認識失敗（0料理）")
            continue

        print(f"  VLM認識料理:")
        for i, dish in enumerate(case['vlm_dishes'][:5], 1):  # 最初の5つだけ表示
            main_food = dish.get("main_food", "")
            weight = dish.get("weight_g", 0)
            print(f"    {i}. {main_food} ({weight}g)")

        # USDA検索結果
        search_ok = sum(1 for e in case['enriched_dishes'] if e.get("usda_match"))
        search_ng = len(case['enriched_dishes']) - search_ok
        print(f"  USDA検索: 成功={search_ok}, 失敗={search_ng}")

        # Reranker score
        scores = [e.get("usda_match", {}).get("reranker_score", 0)
                  for e in case['enriched_dishes']
                  if e.get("usda_match")]
        if scores:
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            print(f"  Reranker Score: 平均={avg_score:.3f}, 最小={min_score:.3f}")

    print()
    print("=" * 100)


if __name__ == "__main__":
    main()
