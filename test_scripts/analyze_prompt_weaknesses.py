#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
3つのプロンプトの弱点を詳細分析
"""

import json
from pathlib import Path
from typing import Dict, List
import statistics

def load_results(json_path: str) -> List[Dict]:
    """結果JSONファイルを読み込む"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_prompt_weaknesses(results: List[Dict]):
    """各プロンプトの弱点を分析"""

    print("=" * 100)
    print("📊 プロンプト別弱点分析")
    print("=" * 100)

    # プロンプトごとの統計を収集
    prompt_stats = {
        "v4_light": {
            "errors": [],
            "overestimate": [],
            "underestimate": [],
            "missing_items": [],
            "weight_errors": [],
            "usda_mismatches": []
        },
        "v5_qwen3": {
            "errors": [],
            "overestimate": [],
            "underestimate": [],
            "missing_items": [],
            "weight_errors": [],
            "usda_mismatches": []
        },
        "v5_streamlined": {
            "errors": [],
            "overestimate": [],
            "underestimate": [],
            "missing_items": [],
            "weight_errors": [],
            "usda_mismatches": []
        }
    }

    for result in results:
        image_name = result["image_name"]
        label_items = result["label_nutrition"]["items"]
        label_cal = result["label_nutrition"]["total_calorie"]
        label_weight = result["label_nutrition"].get("total_weight", 0)

        for version in ["v4_light", "v5_qwen3", "v5_streamlined"]:
            if version not in result["prompt_results"]:
                continue

            pr = result["prompt_results"][version]
            if "error" in pr:
                continue

            # カロリー誤差
            cal_error = pr["diff"]["calorie"]["percent"]
            prompt_stats[version]["errors"].append(abs(cal_error))

            # 過大/過小評価
            if cal_error > 30:
                prompt_stats[version]["overestimate"].append(image_name)
            elif cal_error < -30:
                prompt_stats[version]["underestimate"].append(image_name)

            # アイテム数の差
            vlm_items = 0
            total_weight = 0

            for dish in pr.get("dishes", []):
                if dish.get("main_food"):
                    vlm_items += 1
                    total_weight += dish["main_food"].get("weight_g", 0)

                    # USDAマッチングスコア
                    score = dish["main_food"].get("matched_usda", {}).get("score", 0)
                    if score < 0.95 and score > 0:
                        prompt_stats[version]["usda_mismatches"].append(score)

                for extra in dish.get("extras", []):
                    vlm_items += 1
                    total_weight += extra.get("weight_g", 0)

                    score = extra.get("matched_usda", {}).get("score", 0)
                    if score < 0.95 and score > 0:
                        prompt_stats[version]["usda_mismatches"].append(score)

            # アイテム見落とし
            item_diff = len(label_items) - vlm_items
            if item_diff > 0:
                prompt_stats[version]["missing_items"].append(item_diff)

            # 重量誤差
            if label_weight > 0 and total_weight > 0:
                weight_error = abs((total_weight - label_weight) / label_weight * 100)
                prompt_stats[version]["weight_errors"].append(weight_error)

    # 結果を表示
    for version, stats in prompt_stats.items():
        print(f"\n{'='*80}")
        print(f"📌 {version} の弱点分析")
        print(f"{'='*80}")

        # カロリー誤差統計
        if stats["errors"]:
            print(f"\n📊 カロリー誤差:")
            print(f"  - 平均誤差: {statistics.mean(stats['errors']):.1f}%")
            print(f"  - 中央値: {statistics.median(stats['errors']):.1f}%")
            print(f"  - 最大誤差: {max(stats['errors']):.1f}%")
            print(f"  - 30%以上誤差: {len([e for e in stats['errors'] if e >= 30])}件")

        # 過大/過小評価
        print(f"\n⚖️ 推定傾向:")
        print(f"  - 過大評価(+30%以上): {len(stats['overestimate'])}件")
        if stats['overestimate'][:3]:
            print(f"    例: {', '.join(stats['overestimate'][:3])}")
        print(f"  - 過小評価(-30%以上): {len(stats['underestimate'])}件")
        if stats['underestimate'][:3]:
            print(f"    例: {', '.join(stats['underestimate'][:3])}")

        # アイテム見落とし
        if stats["missing_items"]:
            print(f"\n👁️ アイテム見落とし:")
            print(f"  - 発生件数: {len(stats['missing_items'])}件")
            print(f"  - 平均見落とし数: {statistics.mean(stats['missing_items']):.1f}個")
            print(f"  - 最大見落とし数: {max(stats['missing_items'])}個")

        # 重量誤差
        if stats["weight_errors"]:
            print(f"\n⚖️ 重量推定誤差:")
            print(f"  - 平均誤差: {statistics.mean(stats['weight_errors']):.1f}%")
            print(f"  - 最大誤差: {max(stats['weight_errors']):.1f}%")

            # 特に問題のある重量誤差
            large_weight_errors = [e for e in stats['weight_errors'] if e > 50]
            if large_weight_errors:
                print(f"  - 50%以上の重量誤差: {len(large_weight_errors)}件")

        # USDAマッチング問題
        if stats["usda_mismatches"]:
            print(f"\n🔍 USDAマッチング精度:")
            print(f"  - 低スコア(<0.95)件数: {len(stats['usda_mismatches'])}件")
            print(f"  - 平均スコア: {statistics.mean(stats['usda_mismatches']):.3f}")
            print(f"  - 最低スコア: {min(stats['usda_mismatches']):.3f}")

        # 弱点サマリー
        print(f"\n🎯 主要な弱点:")
        weaknesses = []

        if version == "v4_light":
            if len(stats['overestimate']) > len(stats['underestimate']):
                weaknesses.append("• 過大評価傾向が強い（特に複合料理）")
            if stats["missing_items"]:
                weaknesses.append("• 小物アイテムの見落とし")
            if any(e > 100 for e in stats['errors']):
                weaknesses.append("• 極端な誤差ケースが存在（+100%以上）")

        elif version == "v5_qwen3":
            if len(stats['underestimate']) > len(stats['overestimate']):
                weaknesses.append("• 系統的な過小評価（密度値の問題）")
            if stats["weight_errors"] and statistics.mean(stats['weight_errors']) > 40:
                weaknesses.append("• 重量推定が不正確（weight_derivation計算エラー）")
            if len(stats['underestimate']) > 30:
                weaknesses.append("• ほぼ全ての画像で過小評価")

        elif version == "v5_streamlined":
            if stats["missing_items"]:
                weaknesses.append("• 詳細アイテムの見落とし")
            if stats["usda_mismatches"]:
                weaknesses.append("• USDAマッチング精度が不安定")
            if len(stats['overestimate']) > 5:
                weaknesses.append("• 時々大幅な過大評価")

        for weakness in weaknesses:
            print(weakness)

def suggest_improvements():
    """改善提案を生成"""

    print("\n" + "=" * 100)
    print("💡 改善提案")
    print("=" * 100)

    improvements = {
        "v4_light": [
            "過大評価の修正：",
            "  - 典型的なポーションサイズの上限を設定",
            "  - 'total weight typically 400-600g'を追加",
            "  - 複合料理の重量を抑制的に推定",
            "",
            "小物検出の強化：",
            "  - 'MUST detect ALL visible items'を強調",
            "  - 野菜、ソースの明示的なチェックリスト追加",
        ],
        "v5_qwen3": [
            "密度値の修正（最重要）：",
            "  - cooked_meat: 0.5 → 1.05",
            "  - cooked_pasta: 0.3 → 0.85",
            "  - cooked_vegetables: 0.2 → 0.6",
            "",
            "weight_derivation計算の改善：",
            "  - 最小重量の設定（main_food >= 80g）",
            "  - 合計重量の妥当性チェック（300-800g）",
        ],
        "v5_streamlined": [
            "詳細度の向上：",
            "  - extras検出の閾値を下げる",
            "  - 'include small items'を明記",
            "",
            "構造の明確化：",
            "  - weight_reasoning欄の追加",
            "  - 各アイテムの重量根拠を記録",
        ]
    }

    for version, items in improvements.items():
        print(f"\n📌 {version}の改善案:")
        for item in items:
            print(f"  {item}")

def main():
    """メイン処理"""

    # 最新の結果ファイルを読み込み
    result_file = "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_prompt_nutrition_comparison_20251027_130543.json"

    if not Path(result_file).exists():
        print(f"❌ ファイルが見つかりません: {result_file}")
        return

    results = load_results(result_file)
    print(f"📂 {len(results)}画像の結果を分析中...\n")

    # 弱点分析
    analyze_prompt_weaknesses(results)

    # 改善提案
    suggest_improvements()

if __name__ == "__main__":
    main()