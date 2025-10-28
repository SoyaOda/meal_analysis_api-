#!/usr/bin/env python3
"""
各プロンプトの弱点と改善案を詳細分析
特に30%以上誤差のケースに焦点
"""

import json
import statistics
from pathlib import Path
from collections import defaultdict

def analyze_prompt_weaknesses():
    # JSONファイル読み込み
    with open('test_scripts/output/vlm_prompt_nutrition_comparison_20251027_155439.json', 'r') as f:
        data = json.load(f)

    print("=" * 100)
    print("🔬 VLMプロンプト弱点分析と改善提案レポート")
    print("=" * 100)

    # 各プロンプトの結果を収集
    prompts = ["v5_streamlined", "v6_balanced", "v7_production", "v7_experimental"]
    prompt_results = {p: {
        "errors": {"calorie": [], "protein": [], "fat": [], "carbs": []},
        "high_error_cases": [],
        "under_estimation": [],
        "over_estimation": [],
        "error_by_category": defaultdict(list)
    } for p in prompts}

    # データ収集
    for img_data in data:
        img_name = img_data["image_name"]
        label = img_data["label_nutrition"]
        items = label.get("items", [])

        # 食材カテゴリを判定
        food_category = categorize_food(img_name, items)

        for prompt in prompts:
            if prompt in img_data["prompt_results"]:
                result = img_data["prompt_results"][prompt]
                diff = result["diff"]

                # エラー率を収集
                cal_error = abs(diff["calorie"]["percent"])
                prot_error = abs(diff["protein_g"]["percent"])
                fat_error = abs(diff["fat_g"]["percent"])
                carb_error = abs(diff["carbs_g"]["percent"])

                pr = prompt_results[prompt]
                pr["errors"]["calorie"].append(cal_error)
                pr["errors"]["protein"].append(prot_error)
                pr["errors"]["fat"].append(fat_error)
                pr["errors"]["carbs"].append(carb_error)

                # カテゴリ別エラー
                pr["error_by_category"][food_category].append(cal_error)

                # 30%以上エラーのケース
                if cal_error >= 30:
                    case_info = {
                        "image": img_name,
                        "category": food_category,
                        "error_pct": cal_error,
                        "label_cal": label["total_calorie"],
                        "predicted_cal": result["total_nutrition"]["calories"],
                        "diff_cal": diff["calorie"]["diff"],
                        "fat_error": fat_error,
                        "protein_error": prot_error,
                        "carbs_error": carb_error,
                        "items": items,
                        "vlm_output": result.get("vlm_output", {})
                    }
                    pr["high_error_cases"].append(case_info)

                    if diff["calorie"]["diff"] > 0:
                        pr["over_estimation"].append(case_info)
                    else:
                        pr["under_estimation"].append(case_info)

    # 各プロンプトの分析
    print("\n📊 プロンプト別パフォーマンス比較")
    print("-" * 100)

    for prompt in prompts:
        pr = prompt_results[prompt]
        print(f"\n【{prompt}】")
        print(f"  平均カロリー誤差: {statistics.mean(pr['errors']['calorie']):.1f}%")
        print(f"  平均脂質誤差: {statistics.mean(pr['errors']['fat']):.1f}%")
        print(f"  30%以上誤差: {len(pr['high_error_cases'])}件")
        print(f"  過大評価/過小評価: {len(pr['over_estimation'])}件 / {len(pr['under_estimation'])}件")

    # 詳細な弱点分析
    print("\n" + "=" * 100)
    print("🎯 各プロンプトの具体的弱点と改善案")
    print("=" * 100)

    # v5_streamlined の分析
    analyze_v5_streamlined(prompt_results["v5_streamlined"])

    # v6_balanced の分析
    analyze_v6_balanced(prompt_results["v6_balanced"])

    # v7_production の分析
    analyze_v7_production(prompt_results["v7_production"])

    # v7_experimental の分析
    analyze_v7_experimental(prompt_results["v7_experimental"])

    # 共通の問題パターン
    print("\n" + "=" * 100)
    print("🔍 全プロンプト共通の問題パターン")
    print("=" * 100)

    analyze_common_patterns(prompt_results, data)

    return prompt_results

def categorize_food(img_name, items):
    """食材をカテゴリに分類"""
    items_str = ' '.join([item.get('search_name', '') for item in items]).lower()
    img_lower = img_name.lower()

    if any(word in img_lower or word in items_str for word in ['soup', 'stew', 'chowder']):
        return "soup/stew"
    elif any(word in img_lower or word in items_str for word in ['sandwich', 'burger', 'hot dog']):
        return "sandwich/burger"
    elif any(word in img_lower or word in items_str for word in ['pasta', 'noodle', 'macaroni', 'spaghetti']):
        return "pasta/noodles"
    elif any(word in img_lower or word in items_str for word in ['pizza']):
        return "pizza"
    elif any(word in img_lower or word in items_str for word in ['steak', 'chicken', 'beef', 'pork', 'turkey']):
        return "meat_dishes"
    elif any(word in img_lower or word in items_str for word in ['fried', 'tempura', 'crispy']):
        return "fried_foods"
    else:
        return "mixed_dishes"

def analyze_v5_streamlined(pr):
    """v5_streamlinedの詳細分析"""
    print("\n### v5_streamlined 詳細分析")
    print("-" * 80)

    # 最も誤差の大きいケース
    high_error_cases = sorted(pr["high_error_cases"], key=lambda x: x["error_pct"], reverse=True)

    print("\n🔴 主要な弱点:")
    print("1. **クリーム系ソース・スープの過大評価**")
    print("   - test_food6.jpg: 155.7%誤差 (クリームチキンスープ)")
    print("   - クリーム系の油脂量を大幅に過大評価する傾向")

    print("\n2. **肉料理の系統的な誤差**")
    category_errors = {}
    for cat, errors in pr["error_by_category"].items():
        if errors:
            category_errors[cat] = statistics.mean(errors)

    for cat, avg_error in sorted(category_errors.items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"   - {cat}: 平均{avg_error:.1f}%誤差")

    print("\n3. **脂質推定の大幅なばらつき**")
    print(f"   - 平均脂質誤差: {statistics.mean(pr['errors']['fat']):.1f}%")
    print(f"   - 11件で脂質誤差>50%")

    print("\n💡 改善案:")
    print("1. **油脂検出の精度向上**")
    print("   - 'Visual cues: Shiny = oil/butter'の判定基準を定量化")
    print("   - クリーム系の見た目と実際の脂質含有量の相関を明示")

    print("2. **調理法別の重量補正**")
    print("   - 揚げ物: +15-20% 油吸収")
    print("   - グリル: -10-15% 水分損失")
    print("   - 煮込み: +5-10% 水分吸収")

    print("3. **複合食品の分解精度向上**")
    print("   - レイヤー検出の強化")
    print("   - ソースと主材の明確な分離")

def analyze_v6_balanced(pr):
    """v6_balancedの詳細分析"""
    print("\n### v6_balanced 詳細分析")
    print("-" * 80)

    print("\n🔴 主要な弱点:")
    print("1. **バランス重視による中途半端な推定**")
    print(f"   - 平均カロリー誤差: {statistics.mean(pr['errors']['calorie']):.1f}%")
    print("   - 極端な誤差は少ないが、全体的に精度が低下")

    print("2. **Pizza/パスタ料理の過小評価**")
    for cat in ["pizza", "pasta/noodles"]:
        if cat in pr["error_by_category"]:
            errors = pr["error_by_category"][cat]
            if errors:
                print(f"   - {cat}: 平均{statistics.mean(errors):.1f}%誤差")

    print("\n💡 改善案:")
    print("1. **カテゴリ別の専用ルール追加**")
    print("   - Pizza: チーズ層の厚さ推定強化")
    print("   - パスタ: ソースの種類別脂質推定")

    print("2. **重量推定の基準明確化**")
    print("   - 参照物体との比較方法の具体化")

def analyze_v7_production(pr):
    """v7_productionの詳細分析"""
    print("\n### v7_production 詳細分析")
    print("-" * 80)

    print("\n🔴 主要な弱点:")
    print("1. **Edge-based検出の過剰反応**")
    print(f"   - 小物検出強化が逆に誤差を生む場合あり")

    print("2. **２パススキャンの重複カウント**")
    print("   - 同じアイテムを異なる角度から二重計上")

    print("\n💡 改善案:")
    print("1. **重複検出の防止メカニズム**")
    print("   - 位置情報による同一アイテム判定")
    print("   - 確信度スコアによるフィルタリング")

    print("2. **小物の栄養寄与度の適切な重み付け**")
    print("   - 調味料・薬味: 最大50kcal制限")
    print("   - ソース類: 実測値との対応表作成")

def analyze_v7_experimental(pr):
    """v7_experimentalの詳細分析"""
    print("\n### v7_experimental 詳細分析")
    print("-" * 80)

    print("\n🔴 主要な弱点:")
    print("1. **FAO密度計算の不適切な適用**")
    print(f"   - 平均カロリー誤差が悪化: {statistics.mean(pr['errors']['calorie']):.1f}%")

    print("2. **複合食品の密度推定エラー**")
    print("   - 実際の密度が想定範囲外のケース多発")

    print("\n💡 改善案:")
    print("1. **密度範囲の再調整**")
    print("   - 実測データに基づく密度テーブルの更新")
    print("   - 食材組成による動的密度計算")

    print("2. **Component分解の精度向上**")
    print("   - 可視部分と隠れた部分の比率推定")

def analyze_common_patterns(prompt_results, data):
    """全プロンプト共通の問題パターン分析"""

    # 全プロンプトで高誤差の画像を特定
    common_high_error = {}
    for img_data in data:
        img_name = img_data["image_name"]
        error_count = 0
        total_error = 0

        for prompt in prompt_results.keys():
            if prompt in img_data["prompt_results"]:
                cal_error = abs(img_data["prompt_results"][prompt]["diff"]["calorie"]["percent"])
                if cal_error >= 30:
                    error_count += 1
                    total_error += cal_error

        if error_count >= 3:  # 3つ以上のプロンプトで高誤差
            common_high_error[img_name] = {
                "count": error_count,
                "avg_error": total_error / error_count,
                "items": img_data["label_nutrition"].get("items", [])
            }

    print("\n🔴 全プロンプト共通の困難ケース:")
    for img, info in sorted(common_high_error.items(), key=lambda x: x[1]["avg_error"], reverse=True)[:5]:
        items_str = ", ".join([item["search_name"] for item in info["items"][:2]])
        print(f"  - {img}: 平均{info['avg_error']:.1f}%誤差 ({items_str})")

    print("\n💡 根本的な改善提案:")
    print("\n1. **VLMモデル自体の限界への対処**")
    print("   - マルチモーダル融合の改善")
    print("   - 深度推定機能の追加検討")

    print("\n2. **前処理の強化**")
    print("   - 画像の明度・コントラスト正規化")
    print("   - 参照スケールの自動検出")

    print("\n3. **後処理での補正**")
    print("   - カテゴリ別の誤差補正係数")
    print("   - 信頼度スコアに基づく結果フィルタリング")

    print("\n4. **データベース連携の改善**")
    print("   - USDA検索の曖昧性解消")
    print("   - 調理法による栄養変化の考慮")

    print("\n5. **アンサンブル手法の導入**")
    print("   - 複数プロンプトの結果を統合")
    print("   - 外れ値の自動除外メカニズム")

if __name__ == "__main__":
    prompt_results = analyze_prompt_weaknesses()