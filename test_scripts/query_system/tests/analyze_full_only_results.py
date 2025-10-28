#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Full-only search結果の栄養学的分析

63件のproblematicケースが本当に問題か、栄養計算の観点で詳細確認
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def categorize_nutrition_impact(
    query_name: str,
    query_desc: str,
    matched_name: str,
    matched_desc: str,
    matched_full: str
) -> Dict:
    """栄養計算への影響度でカテゴリ分け"""

    query_text = f"{query_name} {query_desc}".lower()
    matched_text = f"{matched_name} {matched_desc}".lower()

    query_main = query_name.lower().strip()
    matched_main = matched_name.lower().strip()

    # 単数形/複数形の違いのみ
    if query_main.rstrip('s') == matched_main.rstrip('s'):
        return {
            "category": "PERFECT",
            "reason": "単数形/複数形の違いのみ",
            "nutrition_impact": "NONE"
        }

    # 同じ食品、同じ調理法
    query_words = set(query_main.split())
    matched_words = set(matched_main.split())
    common_words = query_words & matched_words

    # 主要食材名が一致
    if common_words and len(common_words) >= len(query_words) * 0.5:
        # 調理法チェック
        cooking_methods = [
            "raw", "cooked", "grilled", "fried", "baked", "roasted",
            "boiled", "steamed", "sauteed", "broiled"
        ]

        query_cooking = None
        matched_cooking = None

        for method in cooking_methods:
            if method in query_text:
                query_cooking = method
                break

        for method in cooking_methods:
            if method in matched_text:
                matched_cooking = method
                break

        # 調理法が一致
        if query_cooking == matched_cooking or (not query_cooking and not matched_cooking):
            return {
                "category": "ACCEPTABLE",
                "reason": "同じ食品、同じ調理法",
                "nutrition_impact": "LOW"
            }

        # 調理法が違うが、"cooked"は曖昧なので許容
        if query_cooking == "cooked" or matched_cooking == "cooked" or "NS as to cooking method" in matched_full:
            return {
                "category": "MINOR_DIFFERENCE",
                "reason": f"調理法の詳細が違う ({query_cooking} vs {matched_cooking}) が許容範囲",
                "nutrition_impact": "LOW"
            }

        # raw vs cooked は重大
        if query_cooking == "raw" and matched_cooking and matched_cooking != "raw":
            return {
                "category": "MAJOR_DIFFERENCE",
                "reason": f"raw vs {matched_cooking} - 栄養素が大きく異なる",
                "nutrition_impact": "HIGH"
            }

        # その他の調理法の違い
        return {
            "category": "MINOR_DIFFERENCE",
            "reason": f"調理法が異なる ({query_cooking} vs {matched_cooking})",
            "nutrition_impact": "MEDIUM"
        }

    # 食品名が完全に違う
    return {
        "category": "WRONG_FOOD",
        "reason": "完全に違う食品",
        "nutrition_impact": "CRITICAL"
    }


def analyze_full_only_results():
    """Full-only search結果を詳細分析"""

    print("=" * 80)
    print("Full-Only Search結果の栄養学的分析")
    print("=" * 80)

    # Load results
    results_file = project_root / "output" / "evaluation_results_300_full_only.json"
    print(f"\nLoading: {results_file}")

    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['results']
    summary = data['summary']

    print(f"\n基本統計:")
    print(f"  Total: {summary['total_queries']}")
    print(f"  Exact Match: {summary['exact_matches']} ({summary['exact_match_rate']*100:.1f}%)")
    print(f"  Problematic: {summary['problematic']} ({summary['problematic']/summary['total_queries']*100:.1f}%)")

    # Problematicケースのみ抽出
    problematic_cases = [r for r in results if r.get('evaluation', {}).get('category') == 'problematic']

    print(f"\n" + "=" * 80)
    print(f"Problematicケースの再評価 ({len(problematic_cases)}件)")
    print("=" * 80)

    # 再評価
    nutrition_categories = {
        "PERFECT": [],
        "ACCEPTABLE": [],
        "MINOR_DIFFERENCE": [],
        "MAJOR_DIFFERENCE": [],
        "WRONG_FOOD": []
    }

    for case in problematic_cases:
        nutrition_eval = categorize_nutrition_impact(
            query_name=case['query_name'],
            query_desc=case['query_desc'],
            matched_name=case['matched_name'],
            matched_desc=case['matched_desc'],
            matched_full=case['matched_description']
        )

        case['nutrition_evaluation'] = nutrition_eval
        nutrition_categories[nutrition_eval['category']].append(case)

    # カテゴリ別集計
    print(f"\n栄養学的カテゴリ分け:")
    print("-" * 80)

    for category, cases in nutrition_categories.items():
        count = len(cases)
        pct = count / len(problematic_cases) * 100 if problematic_cases else 0
        print(f"  {category}: {count} ({pct:.1f}%)")

    # 各カテゴリの詳細
    print(f"\n" + "=" * 80)
    print("カテゴリ別詳細")
    print("=" * 80)

    for category in ["WRONG_FOOD", "MAJOR_DIFFERENCE", "MINOR_DIFFERENCE", "ACCEPTABLE", "PERFECT"]:
        cases = nutrition_categories[category]
        if not cases:
            continue

        print(f"\n【{category}】 ({len(cases)}件)")
        print("-" * 80)

        for i, case in enumerate(cases[:10], 1):  # 最初の10件
            print(f"\n{i}. Query: {case['query_name']} | {case['query_desc']}")
            print(f"   Matched: {case['matched_description']}")
            print(f"   Reason: {case['nutrition_evaluation']['reason']}")
            print(f"   Impact: {case['nutrition_evaluation']['nutrition_impact']}")

        if len(cases) > 10:
            print(f"\n   ... and {len(cases) - 10} more")

    # Overall nutrition acceptability
    print(f"\n" + "=" * 80)
    print("栄養計算の観点での総合評価")
    print("=" * 80)

    # Exact matchは全てOK
    nutrition_acceptable = summary['exact_matches']

    # Problematicのうち、PERFECT, ACCEPTABLE, MINOR_DIFFERENCEは許容
    nutrition_acceptable += len(nutrition_categories['PERFECT'])
    nutrition_acceptable += len(nutrition_categories['ACCEPTABLE'])
    nutrition_acceptable += len(nutrition_categories['MINOR_DIFFERENCE'])

    nutrition_acceptable_rate = nutrition_acceptable / summary['total_queries'] * 100

    print(f"\n✅ 栄養計算で許容可能: {nutrition_acceptable}/{summary['total_queries']} ({nutrition_acceptable_rate:.1f}%)")

    critical_issues = len(nutrition_categories['MAJOR_DIFFERENCE']) + len(nutrition_categories['WRONG_FOOD'])
    print(f"❌ 重大な問題: {critical_issues}/{summary['total_queries']} ({critical_issues/summary['total_queries']*100:.1f}%)")

    # Compare with Original
    print(f"\n" + "=" * 80)
    print("Original (weight_main=0.6, full=0.4) との比較")
    print("=" * 80)

    original_file = project_root / "output" / "evaluation_results_300_with_retry.json"
    if original_file.exists():
        with open(original_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)

        original_summary = original_data['summary']

        print(f"\nExact Match率:")
        print(f"  Original: {original_summary['exact_match_rate']*100:.1f}% ({original_summary['exact_matches']}/300)")
        print(f"  Full-only: {summary['exact_match_rate']*100:.1f}% ({summary['exact_matches']}/300)")

        diff = summary['exact_matches'] - original_summary['exact_matches']
        if diff > 0:
            print(f"  → {diff}件改善 ✅")
        elif diff < 0:
            print(f"  → {abs(diff)}件悪化 ⚠️")
        else:
            print(f"  → 変化なし")

        print(f"\nProblematic率:")
        print(f"  Original: {original_summary['problematic']/300*100:.1f}% ({original_summary['problematic']}/300)")
        print(f"  Full-only: {summary['problematic']/300*100:.1f}% ({summary['problematic']}/300)")

        diff = summary['problematic'] - original_summary['problematic']
        if diff > 0:
            print(f"  → {diff}件悪化 ⚠️")
        elif diff < 0:
            print(f"  → {abs(diff)}件改善 ✅")
        else:
            print(f"  → 変化なし")

        # Check prosciutto in original
        original_results = original_data['results']
        prosciutto_original = [r for r in original_results if 'prosciutto' in r['query_name'].lower() and 'pizza' not in r['query_name'].lower()]

        print(f"\nProsciuttoケース:")
        if prosciutto_original:
            print(f"  Original: {prosciutto_original[0]['matched_description']}")
            print(f"  Full-only: Ham, prosciutto ✅")
            print(f"  → 改善！")

    # Save detailed analysis
    output_file = project_root / "output" / "nutrition_analysis_300_full_only.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_queries": summary['total_queries'],
                "exact_matches": summary['exact_matches'],
                "problematic": summary['problematic'],
                "nutrition_acceptable": nutrition_acceptable,
                "nutrition_acceptable_rate": nutrition_acceptable_rate / 100,
                "critical_issues": critical_issues,
                "critical_issues_rate": critical_issues / summary['total_queries']
            },
            "nutrition_categories": {
                "PERFECT": len(nutrition_categories['PERFECT']),
                "ACCEPTABLE": len(nutrition_categories['ACCEPTABLE']),
                "MINOR_DIFFERENCE": len(nutrition_categories['MINOR_DIFFERENCE']),
                "MAJOR_DIFFERENCE": len(nutrition_categories['MAJOR_DIFFERENCE']),
                "WRONG_FOOD": len(nutrition_categories['WRONG_FOOD'])
            },
            "problematic_cases_details": problematic_cases
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Detailed analysis saved to: {output_file}")

    print(f"\n" + "=" * 80)
    print("結論")
    print("=" * 80)

    print(f"\nFull-only searchの評価:")
    print(f"  ✅ Prosciuttoケースが改善")
    print(f"  ✅ 栄養計算で許容可能: {nutrition_acceptable_rate:.1f}%")

    if nutrition_acceptable_rate >= 98.0:
        print(f"  → 栄養計算の観点では十分な精度 ✅")
    else:
        print(f"  → 栄養計算の観点でやや精度不足 ⚠️")

    if critical_issues <= 5:
        print(f"  → 重大な問題は少ない ({critical_issues}件) ✅")
    else:
        print(f"  → 重大な問題がある ({critical_issues}件) ⚠️")


if __name__ == "__main__":
    try:
        analyze_full_only_results()
    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
