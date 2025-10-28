#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最悪ケースの詳細分析 - VLM出力と正解ラベルを比較
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import statistics

def load_results(json_path: str) -> List[Dict]:
    """結果JSONファイルを読み込む"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_labels_from_results(results: List[Dict]) -> Dict[str, Dict]:
    """結果JSONからラベルデータを抽出"""
    labels_dict = {}

    for result in results:
        image_name = result["image_name"]
        label_nutrition = result.get("label_nutrition", {})

        # ラベルデータを再構築
        labels_dict[image_name] = {
            "nutritions": label_nutrition.get("items", []),
            "total_calorie": label_nutrition.get("total_calorie", 0),
            "total_weight": label_nutrition.get("total_weight", 0)
        }

    return labels_dict

def analyze_worst_cases(results: List[Dict], labels_dict: Dict[str, Dict], top_n: int = 10):
    """最悪ケースを詳細分析"""

    print("=" * 100)
    print("🔍 最悪ケースの詳細分析 - VLM出力 vs 正解ラベル")
    print("=" * 100)
    print()

    # 全バージョンの最悪ケースを収集
    worst_cases = []

    for result in results:
        image_name = result["image_name"]
        label = labels_dict.get(image_name)
        if not label:
            continue

        label_cal = result["label_nutrition"]["total_calorie"]

        for version in ["v4_light", "v5_qwen3", "v5_streamlined"]:
            if version not in result["prompt_results"]:
                continue

            prompt_result = result["prompt_results"][version]
            if "error" in prompt_result:
                continue

            diff = prompt_result["diff"]["calorie"]

            # 30%以上の誤差があるケース
            if abs(diff["percent"]) >= 30:
                predicted_cal = prompt_result["total_nutrition"].get("calories", 0)

                worst_cases.append({
                    "image": image_name,
                    "version": version,
                    "error_percent": diff["percent"],
                    "label_cal": label_cal,
                    "predicted_cal": predicted_cal,
                    "label_data": label,
                    "vlm_output": prompt_result
                })

    # エラー率でソート
    worst_cases.sort(key=lambda x: abs(x["error_percent"]), reverse=True)

    # トップNケースを詳細分析
    print(f"📊 上位{top_n}件の最悪ケース:")
    print("=" * 100)

    for i, case in enumerate(worst_cases[:top_n], 1):
        print(f"\n{i}. {case['image']} [{case['version']}]")
        print(f"   誤差: {case['error_percent']:+.1f}%")
        print(f"   カロリー: Label {case['label_cal']:.0f} kcal → Predicted {case['predicted_cal']:.0f} kcal")
        print()

        # ラベル内容と VLM出力を比較
        print("   📝 正解ラベル:")
        label_items = case['label_data'].get('nutritions', [])
        for item in label_items:
            name = item.get('search_name', 'Unknown')
            weight = item.get('weight_g', 0)
            calories = item.get('nutrition', {}).get('calorie', 0)
            print(f"      - {name}: {weight}g → {calories:.0f} kcal")

        print("\n   🤖 VLM認識結果:")
        vlm_dishes = case['vlm_output'].get('dishes', [])
        for dish in vlm_dishes:
            # main_food
            if dish.get('main_food'):
                mf = dish['main_food']
                name = mf.get('search_name', 'Unknown')
                weight = mf.get('weight_g', 0)
                calories = mf.get('nutrition', {}).get('calorie', 0)
                usda_match = mf.get('matched_usda', {}).get('description', 'N/A')
                score = mf.get('matched_usda', {}).get('score', 0)

                print(f"      - {name}: {weight}g → {calories:.0f} kcal")
                if score > 0:
                    print(f"        USDA: {usda_match[:60]}... (Score: {score:.3f})")

            # extras
            for extra in dish.get('extras', []):
                name = extra.get('search_name', 'Unknown')
                weight = extra.get('weight_g', 0)
                calories = extra.get('nutrition', {}).get('calorie', 0)
                usda_match = extra.get('matched_usda', {}).get('description', 'N/A')
                score = extra.get('matched_usda', {}).get('score', 0)

                print(f"      - {name}: {weight}g → {calories:.0f} kcal")
                if score > 0:
                    print(f"        USDA: {usda_match[:60]}... (Score: {score:.3f})")

        # 差分分析
        print("\n   ⚠️ 問題分析:")
        problems = analyze_case_problems(case)
        for problem in problems:
            print(f"      {problem}")

        print("-" * 100)

def analyze_case_problems(case: Dict) -> List[str]:
    """個別ケースの問題を分析"""
    problems = []

    # ラベル内容を取得
    label_items = case['label_data'].get('nutritions', [])
    label_names = [item.get('search_name', '').lower() for item in label_items]
    label_weights = {item.get('search_name', '').lower(): item.get('weight_g', 0) for item in label_items}

    # VLM出力を取得
    vlm_items = []
    vlm_weights = {}

    for dish in case['vlm_output'].get('dishes', []):
        if dish.get('main_food'):
            mf = dish['main_food']
            name = mf.get('search_name', '').lower()
            vlm_items.append(name)
            vlm_weights[name] = mf.get('weight_g', 0)

        for extra in dish.get('extras', []):
            name = extra.get('search_name', '').lower()
            vlm_items.append(name)
            vlm_weights[name] = extra.get('weight_g', 0)

    # アイテムの見落とし
    missing = set(label_names) - set(vlm_items)
    if missing:
        problems.append(f"🔴 見落とし: {', '.join(missing)}")

    # 誤認識（ラベルにないものを検出）
    extra_detected = set(vlm_items) - set(label_names)
    if extra_detected:
        problems.append(f"🔵 過検出: {', '.join(extra_detected)}")

    # 重量推定の大きなずれ
    for name in set(label_names) & set(vlm_items):
        if name in label_weights and name in vlm_weights:
            label_w = label_weights[name]
            vlm_w = vlm_weights[name]
            if label_w > 0:
                diff_pct = (vlm_w - label_w) / label_w * 100
                if abs(diff_pct) > 50:
                    problems.append(f"⚖️ 重量誤差: {name} {label_w}g → {vlm_w}g ({diff_pct:+.0f}%)")

    # v5_qwen3特有の問題
    if case['version'] == 'v5_qwen3':
        # weight_derivationの問題をチェック
        for dish in case['vlm_output'].get('dishes', []):
            if dish.get('main_food') and 'weight_derivation' in dish['main_food']:
                wd = dish['main_food']['weight_derivation']
                density = wd.get('density_g_cm3', 0)
                if density < 0.5:  # 異常に低い密度
                    problems.append(f"🔧 異常な密度値: {density:.2f} g/cm³")

    # カロリー計算の問題
    if case['error_percent'] < -30:
        problems.append("📉 系統的な過小評価")
    elif case['error_percent'] > 30:
        problems.append("📈 系統的な過大評価")

    if not problems:
        problems.append("❓ 明確な問題点が特定できず")

    return problems

def analyze_common_patterns(results: List[Dict], labels_dict: Dict[str, Dict]):
    """共通パターンを分析"""

    print("\n" + "=" * 100)
    print("🎯 共通パターン分析")
    print("=" * 100)

    # パターンカウント
    patterns = {
        "missing_vegetables": 0,
        "missing_sauces": 0,
        "missing_grains": 0,
        "weight_underestimation_meat": 0,
        "weight_overestimation_meat": 0,
        "wrong_meat_type": 0,
        "density_issues": 0
    }

    for result in results:
        image_name = result["image_name"]
        label = labels_dict.get(image_name)
        if not label:
            continue

        for version in ["v4_light", "v5_qwen3", "v5_streamlined"]:
            if version not in result["prompt_results"]:
                continue

            prompt_result = result["prompt_results"][version]
            if "error" in prompt_result or abs(prompt_result["diff"]["calorie"]["percent"]) < 30:
                continue

            # パターン検出
            label_items = {item.get('search_name', '').lower() for item in label.get('nutritions', [])}
            vlm_items = set()

            for dish in prompt_result.get('dishes', []):
                if dish.get('main_food'):
                    vlm_items.add(dish['main_food'].get('search_name', '').lower())
                for extra in dish.get('extras', []):
                    vlm_items.add(extra.get('search_name', '').lower())

            # 野菜の見落とし
            vegetables = ['lettuce', 'tomato', 'cucumber', 'carrot', 'onion', 'pepper', 'broccoli']
            for veg in vegetables:
                if any(veg in item for item in label_items) and not any(veg in item for item in vlm_items):
                    patterns["missing_vegetables"] += 1
                    break

            # ソースの見落とし
            sauces = ['sauce', 'dressing', 'mayo', 'ketchup', 'mustard']
            for sauce in sauces:
                if any(sauce in item for item in label_items) and not any(sauce in item for item in vlm_items):
                    patterns["missing_sauces"] += 1
                    break

            # 肉の誤認識
            meats = {'chicken': 'poultry', 'pork': 'pork', 'beef': 'beef', 'fish': 'seafood'}
            for meat_label, meat_type in meats.items():
                if any(meat_label in item for item in label_items):
                    # 異なる肉種を認識
                    for other_meat in meats:
                        if other_meat != meat_label and any(other_meat in item for item in vlm_items):
                            patterns["wrong_meat_type"] += 1
                            break

    # パターン統計を表示
    print("\n📊 エラーパターン統計:")
    print("-" * 50)

    sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)
    for pattern, count in sorted_patterns:
        if count > 0:
            pattern_name = pattern.replace('_', ' ').title()
            print(f"  {pattern_name}: {count}件")

    # 改善提案
    print("\n💡 改善提案:")
    print("-" * 50)

    if patterns["missing_vegetables"] > 5:
        print("  1. 野菜検出の強化 - 特に小さい野菜や混ざった野菜")

    if patterns["missing_sauces"] > 3:
        print("  2. ソース・調味料の検出改善 - 見た目が不明瞭なものも含める")

    if patterns["wrong_meat_type"] > 2:
        print("  3. 肉種識別の精度向上 - chicken vs pork vs beef の区別")

    if patterns["density_issues"] > 0:
        print("  4. 密度値の妥当性チェック - 食品カテゴリ別の適正値を使用")

def generate_improvement_plan():
    """改善計画を生成"""

    print("\n" + "=" * 100)
    print("📋 パイプライン改善計画")
    print("=" * 100)

    improvements = """
1. 🎯 VLMプロンプトの改善
   - v5_qwen3の密度値を修正（現在の値が低すぎる）
   - 小物アイテムの検出を強調
   - 肉種識別のヒントを追加

2. 🔍 USDA検索の最適化
   - 低スコア（<0.95）の結果に対して代替候補を検討
   - 検索クエリの前処理を改善（同義語展開など）
   - rerankerの閾値調整

3. ⚖️ 重量推定の改善
   - プレートサイズの自動推定
   - 食品カテゴリ別の密度データベース構築
   - 視覚的な深度情報の活用

4. 📊 品質管理
   - 信頼度スコアの導入
   - 異常値検出（極端な重量や密度）
   - 複数プロンプトの結果を統合

5. 🔄 継続的改善
   - エラーケースのログ収集
   - 定期的な精度評価
   - プロンプトのA/Bテスト
"""

    print(improvements)

def main():
    """メイン処理"""

    # 最新の結果ファイルを読み込み
    result_file = "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_prompt_nutrition_comparison_20251027_130543.json"

    if not Path(result_file).exists():
        print(f"❌ ファイルが見つかりません: {result_file}")
        return

    results = load_results(result_file)
    labels_dict = extract_labels_from_results(results)

    print(f"📂 {len(results)}画像の結果を分析中...\n")

    # 最悪ケースの詳細分析
    analyze_worst_cases(results, labels_dict, top_n=10)

    # 共通パターン分析
    analyze_common_patterns(results, labels_dict)

    # 改善計画の生成
    generate_improvement_plan()

if __name__ == "__main__":
    main()