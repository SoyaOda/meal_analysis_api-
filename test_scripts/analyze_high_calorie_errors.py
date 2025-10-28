#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
30%以上のカロリー誤差がある画像のパイプライン問題を徹底分析
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import statistics

def load_results(json_path: str) -> List[Dict]:
    """結果JSONファイルを読み込む"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_high_error_cases(results: List[Dict]):
    """30%以上のカロリー誤差ケースを分析"""

    print("=" * 100)
    print("📊 30%以上カロリー誤差ケースの徹底分析")
    print("=" * 100)
    print()

    # プロンプトごとの高エラーケースを収集
    high_error_cases = {
        "v4_light": [],
        "v5_qwen3": [],
        "v5_streamlined": []
    }

    # エラーパターン分析用
    error_patterns = {
        "weight_underestimation": [],  # 重量過小推定
        "weight_overestimation": [],   # 重量過大推定
        "food_misidentification": [],  # 食品誤認識
        "missing_items": [],           # アイテム見落とし
        "wrong_usda_match": []         # USDA誤マッチング
    }

    for result in results:
        image_name = result["image_name"]
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

                case_info = {
                    "image": image_name,
                    "label_cal": label_cal,
                    "predicted_cal": predicted_cal,
                    "error_percent": diff["percent"],
                    "dishes": prompt_result.get("dishes", [])
                }

                high_error_cases[version].append(case_info)

                # エラーパターンを分析
                analyze_error_pattern(case_info, result["label_nutrition"], error_patterns)

    # 結果を表示
    print("🔍 プロンプトごとの高エラーケース数")
    print("-" * 50)
    for version, cases in high_error_cases.items():
        print(f"{version:15s}: {len(cases)}件")
    print()

    # 各プロンプトの詳細分析
    for version, cases in high_error_cases.items():
        if not cases:
            continue

        print(f"\n{'='*80}")
        print(f"📌 {version} の高エラーケース詳細 ({len(cases)}件)")
        print(f"{'='*80}")

        # エラー率でソート
        cases.sort(key=lambda x: abs(x["error_percent"]), reverse=True)

        # トップ10のワーストケース
        for i, case in enumerate(cases[:10], 1):
            print(f"\n{i}. {case['image']} - エラー: {case['error_percent']:+.1f}%")
            print(f"   Label: {case['label_cal']:.0f} kcal → Predicted: {case['predicted_cal']:.0f} kcal")

            # dishesの詳細
            if case['dishes']:
                print("   検出された食品:")
                for dish in case['dishes'][:3]:  # 最初の3品のみ表示
                    if dish.get('main_food'):
                        mf = dish['main_food']
                        print(f"   - {mf.get('search_name', 'Unknown')}: {mf.get('weight_g', 0)}g")
                        if mf.get('nutrition'):
                            print(f"     → {mf['nutrition'].get('calorie', 0):.0f} kcal")

        # 統計サマリー
        errors = [abs(c["error_percent"]) for c in cases]
        print(f"\n📊 {version} の高エラーケース統計:")
        print(f"   - 平均誤差: {statistics.mean(errors):.1f}%")
        print(f"   - 最大誤差: {max(errors):.1f}%")
        print(f"   - 中央値: {statistics.median(errors):.1f}%")

        # 過小評価 vs 過大評価
        underestimate = [c for c in cases if c["error_percent"] < 0]
        overestimate = [c for c in cases if c["error_percent"] > 0]
        print(f"   - 過小評価: {len(underestimate)}件 (カロリーを低く見積もり)")
        print(f"   - 過大評価: {len(overestimate)}件 (カロリーを高く見積もり)")

    # エラーパターン分析
    print(f"\n{'='*80}")
    print("🎯 エラーパターン分析（全プロンプト合計）")
    print(f"{'='*80}")

    # パターンの統計を表示
    for pattern_name, pattern_cases in error_patterns.items():
        if pattern_cases:
            print(f"\n{pattern_name}: {len(pattern_cases)}件")
            # 上位5件を表示
            for case in pattern_cases[:5]:
                print(f"  - {case}")

def analyze_error_pattern(case_info: Dict, label_nutrition: Dict, patterns: Dict):
    """エラーパターンを分析"""

    # ラベルのアイテム数と予測のアイテム数を比較
    label_items = len(label_nutrition["items"])
    predicted_items = sum(
        len(d.get("extras", [])) + (1 if d.get("main_food") else 0)
        for d in case_info.get("dishes", [])
    )

    # アイテム数の差が大きい場合
    if predicted_items < label_items - 2:
        patterns["missing_items"].append(
            f"{case_info['image']}: Label {label_items}品 → Predicted {predicted_items}品"
        )

    # カロリー誤差が-50%以下の場合（重量過小推定の可能性）
    if case_info["error_percent"] < -50:
        patterns["weight_underestimation"].append(
            f"{case_info['image']}: {case_info['error_percent']:.1f}%"
        )

    # カロリー誤差が+50%以上の場合（重量過大推定の可能性）
    elif case_info["error_percent"] > 50:
        patterns["weight_overestimation"].append(
            f"{case_info['image']}: {case_info['error_percent']:.1f}%"
        )

def identify_common_problems(results: List[Dict]):
    """共通の問題点を特定"""

    print(f"\n{'='*80}")
    print("🔬 パイプライン問題の根本原因分析")
    print(f"{'='*80}")

    problems = {
        "vlm_issues": [],
        "search_issues": [],
        "nutrition_calc_issues": []
    }

    for result in results:
        image_name = result["image_name"]
        label_cal = result["label_nutrition"]["total_calorie"]

        # 最も精度が良いv5_streamlinedでも30%以上誤差がある場合
        if "v5_streamlined" in result["prompt_results"]:
            pr = result["prompt_results"]["v5_streamlined"]
            if "diff" in pr and abs(pr["diff"]["calorie"]["percent"]) >= 30:
                # これは根本的な問題の可能性が高い
                problems["vlm_issues"].append({
                    "image": image_name,
                    "error": pr["diff"]["calorie"]["percent"],
                    "possible_cause": analyze_root_cause(result)
                })

    # 問題の分類と表示
    print("\n1️⃣ VLM（画像認識）の問題:")
    vlm_problems = problems["vlm_issues"]
    if vlm_problems:
        # 原因別に分類
        causes = {}
        for p in vlm_problems:
            cause = p["possible_cause"]
            if cause not in causes:
                causes[cause] = []
            causes[cause].append(p)

        for cause, cases in causes.items():
            print(f"\n   {cause}: {len(cases)}件")
            for case in cases[:3]:
                print(f"      - {case['image']}: {case['error']:.1f}%誤差")

    print("\n2️⃣ 改善提案:")
    print("   - 重量推定の改善: プレートサイズ基準の見直し")
    print("   - 食品認識の改善: 類似食品の区別強化")
    print("   - 見落とし防止: 小物アイテムの検出強化")
    print("   - USDA検索精度: 検索クエリの最適化")

def analyze_root_cause(result: Dict) -> str:
    """根本原因を分析"""

    # 全プロンプトで大きな誤差がある場合
    errors = []
    for version in ["v4_light", "v5_qwen3", "v5_streamlined"]:
        if version in result["prompt_results"]:
            pr = result["prompt_results"][version]
            if "diff" in pr:
                errors.append(abs(pr["diff"]["calorie"]["percent"]))

    if errors and min(errors) > 40:
        return "重量推定が根本的に誤っている可能性"
    elif errors and statistics.stdev(errors) > 20:
        return "プロンプトによる認識のばらつきが大きい"
    else:
        return "特定食品のUSDAマッチングミス"

def main():
    """メイン処理"""

    # 最新の結果ファイルを読み込み
    result_file = "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_prompt_nutrition_comparison_20251027_130543.json"

    if not Path(result_file).exists():
        print(f"❌ ファイルが見つかりません: {result_file}")
        return

    results = load_results(result_file)
    print(f"📂 {len(results)}画像の結果を分析中...\n")

    # 高エラーケースの分析
    analyze_high_error_cases(results)

    # 共通問題の特定
    identify_common_problems(results)

    # 改善優先度の提案
    print(f"\n{'='*80}")
    print("🎯 改善優先度の提案")
    print(f"{'='*80}")

    print("""
1. 【最優先】v5_qwen3の重量推定ロジック修正
   - 40件/50件で30%以上誤差
   - weight_derivationの密度値が不適切の可能性

2. 【高優先】共通の重量推定改善
   - プレートサイズ推定の精度向上
   - 食品別の典型的な密度DB構築

3. 【中優先】食品認識精度向上
   - 類似食品（chicken vs pork等）の区別
   - ソース・調味料の検出強化

4. 【低優先】USDA検索の最適化
   - rerankerスコアの閾値調整
   - 代替候補の活用
""")

if __name__ == "__main__":
    main()