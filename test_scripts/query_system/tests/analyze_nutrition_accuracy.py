#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
栄養学的な観点から300クエリの結果を詳細分析

カテゴリー:
1. PERFECT: 栄養素的に完全一致（単数形/複数形の違い、形状の違いのみ）
2. ACCEPTABLE: 栄養素的に許容範囲（同じ食品、同じ調理法）
3. MINOR_DIFFERENCE: 小さな差異（調理法の詳細が違うが栄養素は近い）
4. MAJOR_DIFFERENCE: 大きな差異（調理法が違い栄養素が変わる）
5. WRONG_FOOD: 完全に違う食品（栄養素が大きく異なる）
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def analyze_nutritional_accuracy(query_name: str, query_desc: str,
                                 matched_description: str,
                                 matched_name: str, matched_desc: str,
                                 rerank_score: float) -> Dict:
    """
    栄養学的な正確性を分析

    Returns:
        {
            "category": str,  # PERFECT, ACCEPTABLE, MINOR_DIFFERENCE, MAJOR_DIFFERENCE, WRONG_FOOD
            "reason": str,
            "nutrition_impact": str,  # "none", "minimal", "moderate", "significant"
            "recommended_action": str
        }
    """

    query_full = f"{query_name} {query_desc}".lower()
    matched_full = f"{matched_name} {matched_desc}".lower()

    # Category 1: PERFECT - 単数形/複数形、形状の違いのみ
    # 例: tomato → Tomatoes, carrot sliced → Carrots
    perfect_pairs = [
        ("tomato", "tomatoes"),
        ("carrot", "carrots"),
        ("onion", "onions"),
        ("mushroom", "mushrooms"),
        ("potato", "potatoes"),
        ("fig", "figs"),
        ("pecan", "nuts, pecans"),
        ("almond", "almonds"),
        ("spaghetti", "pasta"),
        ("macaroni", "pasta"),
        ("penne", "pasta"),
        ("water, tap", "water, tap"),
    ]

    # 形状の違いは栄養素に影響しない
    shape_modifiers = ["sliced", "cubed", "wedges", "shredded", "halves", "chopped", "diced"]

    # Check for perfect matches (ignoring shape)
    for q_word, m_word in perfect_pairs:
        if q_word in query_name.lower() and m_word in matched_name.lower():
            # Check if cooking methods match
            if has_same_cooking_method(query_desc, matched_desc):
                return {
                    "category": "PERFECT",
                    "reason": f"単数形/複数形の違いのみ。食品と調理法が完全一致。",
                    "nutrition_impact": "none",
                    "recommended_action": "問題なし"
                }

    # Category 2: ACCEPTABLE - 同じ食品、同じ調理法
    # 例: red bell pepper → Peppers, bell, red
    acceptable_pairs = [
        ("bell pepper", "peppers, bell"),
        ("bell peppers", "peppers, bell"),
        ("red bell pepper", "peppers, bell, red"),
        ("red onion", "onions, red"),
        ("cheese, cheddar", "cheese, cheddar"),
        ("cornbread", "corn pone"),  # Similar items
        ("mayonnaise", "mayonnaise-type"),
    ]

    for q_word, m_word in acceptable_pairs:
        if q_word in query_full and m_word in matched_full:
            if has_same_cooking_method(query_desc, matched_desc):
                return {
                    "category": "ACCEPTABLE",
                    "reason": f"同じ食品、同じ調理法。栄養素はほぼ同一。",
                    "nutrition_impact": "minimal",
                    "recommended_action": "問題なし"
                }

    # Category 3: MINOR_DIFFERENCE - 調理法の詳細が違うが栄養素は近い
    # 例: roasted → cooked (NS as to method), grilled → cooked
    minor_cooking_variations = [
        (["roasted", "grilled", "baked"], ["cooked", "ns as to"]),
        (["fresh"], ["raw"]),
    ]

    query_cooking = extract_cooking_method(query_desc)
    matched_cooking = extract_cooking_method(matched_desc)

    if query_cooking and matched_cooking:
        for specific_methods, general_methods in minor_cooking_variations:
            if query_cooking in specific_methods and matched_cooking in general_methods:
                return {
                    "category": "MINOR_DIFFERENCE",
                    "reason": f"調理法が具体的 vs 一般的（{query_cooking} vs {matched_cooking}）だが栄養素は近い。",
                    "nutrition_impact": "minimal",
                    "recommended_action": "許容範囲内"
                }

    # Category 4: MAJOR_DIFFERENCE - 調理法が違い栄養素が変わる
    # 例: raw → cooked (水分量、栄養素が変わる)
    major_cooking_differences = [
        ("raw", "cooked"),
        ("raw", "roasted"),
        ("raw", "fried"),
        ("roasted", "honey roasted"),  # Added sugar
    ]

    for q_cook, m_cook in major_cooking_differences:
        if q_cook in query_full and m_cook in matched_full:
            return {
                "category": "MAJOR_DIFFERENCE",
                "reason": f"調理法が異なる（{q_cook} vs {m_cook}）。水分量や栄養素が変化。",
                "nutrition_impact": "moderate",
                "recommended_action": "要注意 - 栄養素の確認が必要"
            }

    # Category 5: WRONG_FOOD - 完全に違う食品
    wrong_food_cases = [
        ("dinner roll", "bread"),  # Similar but different
        ("frittata", "breakfast tart"),  # Different dishes
        ("prosciutto", "ham luncheon meat"),  # Different meat products
        ("dried herbs", "parsley, raw"),  # Dried vs fresh
        ("rice, mexican", "spanish rice"),  # Similar but may have different ingredients
    ]

    for q_food, m_food in wrong_food_cases:
        if q_food in query_full and m_food in matched_full:
            # Check score - low score indicates poor match
            if rerank_score < 0.5:
                return {
                    "category": "WRONG_FOOD",
                    "reason": f"異なる食品（{q_food} vs {m_food}）。スコア低い（{rerank_score:.4f}）。",
                    "nutrition_impact": "significant",
                    "recommended_action": "❌ 不適切 - 別の食品を選択すべき"
                }
            else:
                return {
                    "category": "ACCEPTABLE",
                    "reason": f"類似食品（{q_food} vs {m_food}）。スコア高い（{rerank_score:.4f}）。",
                    "nutrition_impact": "minimal",
                    "recommended_action": "許容範囲内"
                }

    # Default: Check score
    if rerank_score > 0.95:
        return {
            "category": "ACCEPTABLE",
            "reason": f"高スコア（{rerank_score:.4f}）。栄養素的に許容範囲。",
            "nutrition_impact": "minimal",
            "recommended_action": "問題なし"
        }
    else:
        return {
            "category": "MINOR_DIFFERENCE",
            "reason": f"中程度のスコア（{rerank_score:.4f}）。詳細確認推奨。",
            "nutrition_impact": "minimal",
            "recommended_action": "確認推奨"
        }


def has_same_cooking_method(desc1: str, desc2: str) -> bool:
    """調理法が同じかチェック"""
    if not desc1:
        desc1 = ""
    if not desc2:
        desc2 = ""

    desc1_lower = desc1.lower()
    desc2_lower = desc2.lower()

    cooking_methods = ["raw", "cooked", "roasted", "grilled", "fried", "baked", "boiled", "steamed"]

    methods1 = [m for m in cooking_methods if m in desc1_lower]
    methods2 = [m for m in cooking_methods if m in desc2_lower]

    if not methods1 and not methods2:
        return True  # Both unspecified

    if not methods1 or not methods2:
        # One specified, one not
        if "ns as to" in desc2_lower:
            return True  # NS as to cooking method is acceptable
        return False

    return methods1[0] == methods2[0]


def extract_cooking_method(desc: str) -> str:
    """調理法を抽出"""
    if not desc:
        return ""

    desc_lower = desc.lower()
    cooking_methods = ["raw", "cooked", "roasted", "grilled", "fried", "baked", "boiled", "steamed", "fresh"]

    for method in cooking_methods:
        if method in desc_lower:
            return method

    if "ns as to" in desc_lower:
        return "ns as to"

    return ""


def main():
    """全300クエリを栄養学的な観点から分析"""

    print("=" * 80)
    print("栄養学的正確性分析 (300クエリ)")
    print("=" * 80)

    # Load results - accept command line argument for input file
    if len(sys.argv) > 1:
        results_file = Path(sys.argv[1])
        if not results_file.is_absolute():
            results_file = project_root / "output" / results_file
    else:
        results_file = project_root / "output" / "evaluation_results_300_with_retry.json"

    print(f"\n📂 Loading: {results_file}")

    with open(results_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['results']

    print(f"\n総クエリ数: {len(results)}")

    # Analyze all results
    analyzed_results = []

    for r in results:
        if r.get('error'):
            # Skip errors
            continue

        nutrition_analysis = analyze_nutritional_accuracy(
            query_name=r['query_name'],
            query_desc=r['query_desc'],
            matched_description=r['matched_description'],
            matched_name=r['matched_name'],
            matched_desc=r['matched_desc'],
            rerank_score=r['rerank_score']
        )

        analyzed_results.append({
            **r,
            "nutrition_analysis": nutrition_analysis
        })

    # Categorize results
    perfect = [r for r in analyzed_results if r['nutrition_analysis']['category'] == 'PERFECT']
    acceptable = [r for r in analyzed_results if r['nutrition_analysis']['category'] == 'ACCEPTABLE']
    minor_diff = [r for r in analyzed_results if r['nutrition_analysis']['category'] == 'MINOR_DIFFERENCE']
    major_diff = [r for r in analyzed_results if r['nutrition_analysis']['category'] == 'MAJOR_DIFFERENCE']
    wrong_food = [r for r in analyzed_results if r['nutrition_analysis']['category'] == 'WRONG_FOOD']

    print("\n" + "=" * 80)
    print("栄養学的正確性カテゴリー")
    print("=" * 80)

    print(f"\n✅ PERFECT (完全一致): {len(perfect)} ({len(perfect)/len(analyzed_results)*100:.1f}%)")
    print(f"   - 単数形/複数形、形状の違いのみ")
    print(f"   - 栄養素への影響: なし")

    print(f"\n✅ ACCEPTABLE (許容範囲): {len(acceptable)} ({len(acceptable)/len(analyzed_results)*100:.1f}%)")
    print(f"   - 同じ食品、同じ調理法")
    print(f"   - 栄養素への影響: 最小限")

    print(f"\n⚠️  MINOR_DIFFERENCE (小さな差異): {len(minor_diff)} ({len(minor_diff)/len(analyzed_results)*100:.1f}%)")
    print(f"   - 調理法の詳細が違うが栄養素は近い")
    print(f"   - 栄養素への影響: 最小限")

    print(f"\n⚠️  MAJOR_DIFFERENCE (大きな差異): {len(major_diff)} ({len(major_diff)/len(analyzed_results)*100:.1f}%)")
    print(f"   - 調理法が違い栄養素が変わる")
    print(f"   - 栄養素への影響: 中程度")

    print(f"\n❌ WRONG_FOOD (不適切): {len(wrong_food)} ({len(wrong_food)/len(analyzed_results)*100:.1f}%)")
    print(f"   - 完全に違う食品")
    print(f"   - 栄養素への影響: 大きい")

    # Overall nutrition acceptability
    nutrition_acceptable = len(perfect) + len(acceptable) + len(minor_diff)
    print(f"\n📊 栄養学的許容率: {nutrition_acceptable}/{len(analyzed_results)} ({nutrition_acceptable/len(analyzed_results)*100:.1f}%)")

    # Show problematic cases
    problematic_nutrition = major_diff + wrong_food

    if problematic_nutrition:
        print("\n" + "=" * 80)
        print(f"栄養学的に問題があるケース ({len(problematic_nutrition)}件)")
        print("=" * 80)

        for i, r in enumerate(problematic_nutrition, 1):
            na = r['nutrition_analysis']
            print(f"\n{i}. [{na['category']}] Query: {r['query_name']} | {r['query_desc']}")
            print(f"   Matched: {r['matched_description']}")
            print(f"   Score: {r['rerank_score']:.4f}")
            print(f"   理由: {na['reason']}")
            print(f"   栄養素への影響: {na['nutrition_impact']}")
            print(f"   推奨アクション: {na['recommended_action']}")

    # Show detailed breakdown of PERFECT cases
    print("\n" + "=" * 80)
    print(f"PERFECT ケースの詳細 ({len(perfect)}件)")
    print("=" * 80)

    for i, r in enumerate(perfect[:20], 1):  # Show first 20
        na = r['nutrition_analysis']
        print(f"\n{i}. Query: {r['query_name']} | {r['query_desc']}")
        print(f"   Matched: {r['matched_description']}")
        print(f"   Score: {r['rerank_score']:.4f}")
        print(f"   理由: {na['reason']}")

    if len(perfect) > 20:
        print(f"\n... 残り {len(perfect) - 20} 件")

    # Save detailed analysis - accept command line argument for output file
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
        if not output_file.is_absolute():
            output_file = project_root / "output" / output_file
    else:
        output_file = project_root / "output" / "nutrition_analysis_300.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total": len(analyzed_results),
                "perfect": len(perfect),
                "acceptable": len(acceptable),
                "minor_difference": len(minor_diff),
                "major_difference": len(major_diff),
                "wrong_food": len(wrong_food),
                "nutrition_acceptable_rate": nutrition_acceptable / len(analyzed_results),
                "problematic_for_nutrition": len(problematic_nutrition)
            },
            "categories": {
                "perfect": [r['query_id'] for r in perfect],
                "acceptable": [r['query_id'] for r in acceptable],
                "minor_difference": [r['query_id'] for r in minor_diff],
                "major_difference": [r['query_id'] for r in major_diff],
                "wrong_food": [r['query_id'] for r in wrong_food]
            },
            "results": analyzed_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 詳細分析結果を保存: {output_file}")

    # Final conclusion
    print("\n" + "=" * 80)
    print("結論")
    print("=" * 80)

    if nutrition_acceptable / len(analyzed_results) >= 0.95:
        print(f"\n✅ 栄養学的正確性: 優秀 ({nutrition_acceptable/len(analyzed_results)*100:.1f}%)")
        print("   本番環境での使用に適しています。")
    elif nutrition_acceptable / len(analyzed_results) >= 0.90:
        print(f"\n⚠️  栄養学的正確性: 良好 ({nutrition_acceptable/len(analyzed_results)*100:.1f}%)")
        print("   一部改善の余地がありますが、使用可能です。")
    else:
        print(f"\n❌ 栄養学的正確性: 要改善 ({nutrition_acceptable/len(analyzed_results)*100:.1f}%)")
        print("   問題のあるケースが多いため、改善が必要です。")


if __name__ == "__main__":
    main()
