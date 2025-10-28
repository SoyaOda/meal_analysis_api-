#!/usr/bin/env python3
"""
50画像テスト結果の徹底分析
特に30%以上誤差のケースに焦点
"""

import json
import statistics
from pathlib import Path

def analyze_results():
    # JSONファイル読み込み
    with open('test_scripts/output/vlm_prompt_nutrition_comparison_20251027_155439.json', 'r') as f:
        data = json.load(f)

    print("=" * 80)
    print("🔬 50画像テスト結果 - 徹底分析レポート")
    print("=" * 80)

    # v5_streamlinedの結果を収集
    errors = {
        "calorie": [],
        "protein": [],
        "fat": [],
        "carbs": []
    }

    high_error_cases = []  # 30%以上のエラーケース
    error_categories = {
        "over_estimation": [],  # 過大評価
        "under_estimation": [],  # 過小評価
        "very_high_error": []   # 50%以上エラー
    }

    # 各画像の分析
    for img_data in data:
        img_name = img_data["image_name"]
        label = img_data["label_nutrition"]

        if "v5_streamlined" in img_data["prompt_results"]:
            result = img_data["prompt_results"]["v5_streamlined"]
            diff = result["diff"]

            # エラー率を収集
            cal_error = abs(diff["calorie"]["percent"])
            prot_error = abs(diff["protein_g"]["percent"])
            fat_error = abs(diff["fat_g"]["percent"])
            carb_error = abs(diff["carbs_g"]["percent"])

            errors["calorie"].append(cal_error)
            errors["protein"].append(prot_error)
            errors["fat"].append(fat_error)
            errors["carbs"].append(carb_error)

            # 30%以上エラーのケース
            if cal_error >= 30:
                case_info = {
                    "image": img_name,
                    "error_pct": cal_error,
                    "label_cal": label["total_calorie"],
                    "predicted_cal": result["total_nutrition"]["calories"],
                    "diff_cal": diff["calorie"]["diff"],
                    "fat_error": fat_error,
                    "protein_error": prot_error,
                    "carbs_error": carb_error,
                    "items": img_data.get("label_nutrition", {}).get("items", [])
                }
                high_error_cases.append(case_info)

                # カテゴリー分け
                if diff["calorie"]["diff"] > 0:
                    error_categories["over_estimation"].append(case_info)
                else:
                    error_categories["under_estimation"].append(case_info)

                if cal_error >= 50:
                    error_categories["very_high_error"].append(case_info)

    # 統計情報
    print("\n📊 全体統計（50画像）")
    print("-" * 40)
    print(f"平均カロリー誤差: {statistics.mean(errors['calorie']):.1f}%")
    print(f"平均タンパク質誤差: {statistics.mean(errors['protein']):.1f}%")
    print(f"平均脂質誤差: {statistics.mean(errors['fat']):.1f}%")
    print(f"平均炭水化物誤差: {statistics.mean(errors['carbs']):.1f}%")
    print(f"\n中央値カロリー誤差: {statistics.median(errors['calorie']):.1f}%")
    print(f"標準偏差: {statistics.stdev(errors['calorie']):.1f}%")

    # 30%以上エラーの分析
    print("\n" + "=" * 80)
    print("⚠️  30%以上カロリー誤差のケース（16件）")
    print("=" * 80)

    # エラー率でソート
    high_error_cases.sort(key=lambda x: x["error_pct"], reverse=True)

    print(f"\n過大評価: {len(error_categories['over_estimation'])}件")
    print(f"過小評価: {len(error_categories['under_estimation'])}件")
    print(f"50%以上誤差: {len(error_categories['very_high_error'])}件")

    # トップ10の詳細
    print("\n📝 最も誤差の大きい10ケース:")
    print("-" * 80)
    for i, case in enumerate(high_error_cases[:10], 1):
        print(f"\n{i}. {case['image']} - カロリー誤差 {case['error_pct']:.1f}%")
        print(f"   実際: {case['label_cal']:.0f} kcal → 予測: {case['predicted_cal']:.0f} kcal")
        print(f"   差分: {case['diff_cal']:+.0f} kcal")
        print(f"   その他誤差: 脂質 {case['fat_error']:.1f}%, タンパク質 {case['protein_error']:.1f}%, 炭水化物 {case['carbs_error']:.1f}%")

        # 主な食材
        if case['items']:
            main_items = [item['search_name'] for item in case['items'][:3]]
            print(f"   主な食材: {', '.join(main_items)}")

    # パターン分析
    print("\n" + "=" * 80)
    print("🔍 エラーパターン分析")
    print("=" * 80)

    # 食材タイプ別分析
    food_patterns = {
        "sandwich/burger": [],
        "pasta/noodles": [],
        "meat_dishes": [],
        "mixed_dishes": [],
        "fried_foods": []
    }

    for case in high_error_cases:
        items_str = ' '.join([item.get('search_name', '') for item in case['items']])

        if any(word in case['image'].lower() or word in items_str.lower()
               for word in ['sandwich', 'burger', 'hot dog', 'chili dog']):
            food_patterns["sandwich/burger"].append(case)
        elif any(word in items_str.lower() for word in ['pasta', 'noodle', 'macaroni', 'spaghetti']):
            food_patterns["pasta/noodles"].append(case)
        elif any(word in items_str.lower() for word in ['steak', 'chicken', 'beef', 'pork', 'fish']):
            food_patterns["meat_dishes"].append(case)
        elif any(word in items_str.lower() for word in ['fried', 'tempura', 'crispy']):
            food_patterns["fried_foods"].append(case)
        else:
            food_patterns["mixed_dishes"].append(case)

    print("\n食材カテゴリ別エラー傾向:")
    for category, cases in food_patterns.items():
        if cases:
            avg_error = statistics.mean([c['error_pct'] for c in cases])
            print(f"  {category}: {len(cases)}件 (平均誤差 {avg_error:.1f}%)")

    # 栄養素別の相関
    print("\n栄養素間の相関:")
    high_fat_error = [case for case in high_error_cases if case['fat_error'] > 50]
    high_protein_error = [case for case in high_error_cases if case['protein_error'] > 50]

    print(f"  脂質誤差>50%のケース: {len(high_fat_error)}件")
    print(f"  タンパク質誤差>50%のケース: {len(high_protein_error)}件")

    return high_error_cases, error_categories, food_patterns

if __name__ == "__main__":
    high_error_cases, error_categories, food_patterns = analyze_results()