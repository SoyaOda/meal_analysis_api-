#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Full-only search結果の全300例レポート生成

全クエリと結果を確認できるMarkdownレポートを生成
"""

import sys
import json
from pathlib import Path
from typing import Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_full_report():
    """全300例のレポート生成"""

    print("=" * 80)
    print("Full-only Search 300例レポート生成")
    print("=" * 80)

    # Load evaluation results
    results_file = project_root / "output" / "evaluation_results_300_full_only.json"
    print(f"\n📂 Loading: {results_file}")

    with open(results_file, 'r', encoding='utf-8') as f:
        eval_data = json.load(f)

    results = eval_data['results']
    summary = eval_data['summary']

    # Load nutrition analysis
    nutrition_file = project_root / "output" / "nutrition_analysis_300_full_only.json"
    print(f"📂 Loading: {nutrition_file}")

    with open(nutrition_file, 'r', encoding='utf-8') as f:
        nutrition_data = json.load(f)

    nutrition_results = nutrition_data['results']

    # Create lookup dict for nutrition analysis
    nutrition_lookup = {r['query_id']: r['nutrition_analysis'] for r in nutrition_results}

    # Generate Markdown report
    output_file = project_root / "output" / "full_only_search_report_300.md"
    print(f"\n📝 Generating report: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("# Full-only Search 結果レポート (300例)\n\n")
        f.write(f"**実行日時**: {summary.get('timestamp', 'N/A')}\n")
        f.write(f"**設定**: weight_main=0.0, weight_full=1.0 (Full検索のみ)\n\n")

        # Summary
        f.write("## 📊 サマリー統計\n\n")
        f.write(f"- **総クエリ数**: {summary['total_queries']}\n")
        f.write(f"- **Exact Match**: {summary['exact_matches']} ({summary['exact_match_rate']*100:.1f}%)\n")
        f.write(f"- **Problematic**: {summary['problematic']} ({summary['problematic']/summary['total_queries']*100:.1f}%)\n")
        f.write(f"- **Errors**: {summary['errors']}\n")
        f.write(f"- **栄養学的許容率**: {nutrition_data['summary']['nutrition_acceptable_rate']*100:.1f}%\n")
        f.write(f"- **API Cost**: ${summary['api_usage']['total_cost_usd']:.4f}\n")
        f.write(f"- **平均Cost/query**: ${summary['api_usage']['total_cost_usd']/summary['total_queries']:.6f}\n\n")

        # Nutrition Categories
        f.write("### 栄養学的カテゴリ分類\n\n")
        nutrition_summary = nutrition_data['summary']
        f.write(f"- ✅ **PERFECT**: {nutrition_summary['perfect']} ({nutrition_summary['perfect']/summary['total_queries']*100:.1f}%)\n")
        f.write(f"- ✅ **ACCEPTABLE**: {nutrition_summary['acceptable']} ({nutrition_summary['acceptable']/summary['total_queries']*100:.1f}%)\n")
        f.write(f"- ⚠️ **MINOR_DIFFERENCE**: {nutrition_summary['minor_difference']} ({nutrition_summary['minor_difference']/summary['total_queries']*100:.1f}%)\n")
        f.write(f"- ⚠️ **MAJOR_DIFFERENCE**: {nutrition_summary['major_difference']} ({nutrition_summary['major_difference']/summary['total_queries']*100:.1f}%)\n")
        f.write(f"- ❌ **WRONG_FOOD**: {nutrition_summary['wrong_food']} ({nutrition_summary['wrong_food']/summary['total_queries']*100:.1f}%)\n\n")

        # Comparison with Original
        f.write("### Original (weight_main=0.6, full=0.4) との比較\n\n")

        original_file = project_root / "output" / "evaluation_results_300_with_retry.json"
        original_nutrition_file = project_root / "output" / "nutrition_analysis_300.json"

        if original_file.exists() and original_nutrition_file.exists():
            with open(original_file, 'r', encoding='utf-8') as of:
                original_eval = json.load(of)
            with open(original_nutrition_file, 'r', encoding='utf-8') as onf:
                original_nutrition = json.load(onf)

            f.write("| 指標 | Original | Full-only | 変化 |\n")
            f.write("|------|----------|-----------|------|\n")

            # Exact Match
            orig_exact = original_eval['summary']['exact_matches']
            full_exact = summary['exact_matches']
            diff_exact = full_exact - orig_exact
            change_exact = f"+{diff_exact} ✅" if diff_exact > 0 else f"{diff_exact} ⚠️" if diff_exact < 0 else "変化なし"
            f.write(f"| Exact Match | {orig_exact} ({orig_exact/300*100:.1f}%) | {full_exact} ({full_exact/300*100:.1f}%) | {change_exact} |\n")

            # Problematic
            orig_prob = original_eval['summary']['problematic']
            full_prob = summary['problematic']
            diff_prob = full_prob - orig_prob
            change_prob = f"+{diff_prob} ⚠️" if diff_prob > 0 else f"{diff_prob} ✅" if diff_prob < 0 else "変化なし"
            f.write(f"| Problematic | {orig_prob} ({orig_prob/300*100:.1f}%) | {full_prob} ({full_prob/300*100:.1f}%) | {change_prob} |\n")

            # Nutrition Acceptable
            orig_nut = original_nutrition['summary']['nutrition_acceptable_rate'] * 100
            full_nut = nutrition_data['summary']['nutrition_acceptable_rate'] * 100
            diff_nut = full_nut - orig_nut
            change_nut = f"+{diff_nut:.1f}% ✅" if diff_nut > 0 else f"{diff_nut:.1f}% ⚠️" if diff_nut < 0 else "変化なし"
            f.write(f"| 栄養学的許容率 | {orig_nut:.1f}% | {full_nut:.1f}% | {change_nut} |\n")

            # WRONG_FOOD
            orig_wrong = original_nutrition['summary']['wrong_food']
            full_wrong = nutrition_data['summary']['wrong_food']
            diff_wrong = full_wrong - orig_wrong
            change_wrong = f"+{diff_wrong} ⚠️" if diff_wrong > 0 else f"{diff_wrong} ✅" if diff_wrong < 0 else "変化なし"
            f.write(f"| WRONG_FOOD | {orig_wrong} | {full_wrong} | {change_wrong} |\n\n")

        # All 300 Results
        f.write("---\n\n")
        f.write("## 📋 全300例の詳細\n\n")

        # Group by nutrition category
        categories = {
            'PERFECT': [],
            'ACCEPTABLE': [],
            'MINOR_DIFFERENCE': [],
            'MAJOR_DIFFERENCE': [],
            'WRONG_FOOD': []
        }

        for result in results:
            query_id = result['query_id']
            nutrition_analysis = nutrition_lookup.get(query_id, {})
            category = nutrition_analysis.get('category', 'UNKNOWN')
            if category in categories:
                categories[category].append(result)

        # Display by category
        for category in ['PERFECT', 'ACCEPTABLE', 'MINOR_DIFFERENCE', 'MAJOR_DIFFERENCE', 'WRONG_FOOD']:
            cases = categories[category]
            if not cases:
                continue

            # Category header
            category_emoji = {
                'PERFECT': '✅',
                'ACCEPTABLE': '✅',
                'MINOR_DIFFERENCE': '⚠️',
                'MAJOR_DIFFERENCE': '⚠️',
                'WRONG_FOOD': '❌'
            }
            emoji = category_emoji.get(category, '❓')

            f.write(f"### {emoji} {category} ({len(cases)}件)\n\n")

            # Table header
            f.write("| No. | Query | Matched | Score | 理由 |\n")
            f.write("|-----|-------|---------|-------|------|\n")

            for case in cases:
                query_id = case['query_id']
                query_text = f"{case['query_name']} | {case['query_desc']}"
                matched_desc = case['matched_description']
                score = case['rerank_score']

                nutrition_analysis = nutrition_lookup.get(query_id, {})
                reason = nutrition_analysis.get('reason', 'N/A')

                # Escape pipe characters in text
                query_text = query_text.replace('|', '\\|')
                matched_desc = matched_desc.replace('|', '\\|')
                reason = reason.replace('|', '\\|')

                f.write(f"| {query_id} | {query_text} | {matched_desc} | {score:.4f} | {reason} |\n")

            f.write("\n")

        # Special Cases Section
        f.write("---\n\n")
        f.write("## 🔍 特別なケース\n\n")

        # Prosciutto cases
        f.write("### Prosciuttoケース\n\n")
        prosciutto_cases = [r for r in results if 'prosciutto' in r['query_name'].lower() and 'pizza' not in r['query_name'].lower()]

        if prosciutto_cases:
            f.write("| No. | Query | Matched | FDC ID | Rerank Score | Stage1 Score |\n")
            f.write("|-----|-------|---------|--------|--------------|-------------|\n")

            for case in prosciutto_cases:
                query_text = f"{case['query_name']} | {case['query_desc']}".replace('|', '\\|')
                matched_desc = case['matched_description'].replace('|', '\\|')
                fdc_id = case['fdc_id']
                rerank_score = case['rerank_score']
                stage1_score = case['stage1_score']

                # Check if this is the correct match
                marker = "✅" if fdc_id == 2705879 else "⚠️"

                f.write(f"| {marker} {case['query_id']} | {query_text} | {matched_desc} | {fdc_id} | {rerank_score:.4f} | {stage1_score:.4f} |\n")

            f.write("\n**正解**: Ham, prosciutto (FDC ID: 2705879)\n\n")
        else:
            f.write("Prosciuttoケースが見つかりませんでした。\n\n")

        # Low score cases (potential issues)
        f.write("### 低スコアケース (Rerank Score < 0.5)\n\n")
        low_score_cases = [r for r in results if r['rerank_score'] < 0.5]

        if low_score_cases:
            f.write(f"**{len(low_score_cases)}件**のケースでRerank Scoreが0.5未満です。\n\n")
            f.write("| No. | Query | Matched | Score | 栄養カテゴリ |\n")
            f.write("|-----|-------|---------|-------|-------------|\n")

            for case in sorted(low_score_cases, key=lambda x: x['rerank_score']):
                query_id = case['query_id']
                query_text = f"{case['query_name']} | {case['query_desc']}".replace('|', '\\|')
                matched_desc = case['matched_description'].replace('|', '\\|')
                score = case['rerank_score']

                nutrition_analysis = nutrition_lookup.get(query_id, {})
                category = nutrition_analysis.get('category', 'N/A')

                f.write(f"| {query_id} | {query_text} | {matched_desc} | {score:.4f} | {category} |\n")

            f.write("\n")
        else:
            f.write("全てのケースでRerank Score >= 0.5です。✅\n\n")

        # Footer
        f.write("---\n\n")
        f.write("## 📌 結論\n\n")

        if nutrition_data['summary']['nutrition_acceptable_rate'] == 1.0:
            f.write("✅ **全300例が栄養学的に許容可能です。本番環境での使用に適しています。**\n\n")
        elif nutrition_data['summary']['nutrition_acceptable_rate'] >= 0.98:
            f.write("✅ **栄養学的許容率が非常に高く、本番環境での使用に適しています。**\n\n")
        else:
            f.write("⚠️ **一部のケースで栄養学的に問題がある可能性があります。詳細確認が必要です。**\n\n")

        # Recommendation
        f.write("### 推奨事項\n\n")

        if nutrition_data['summary']['wrong_food'] == 0:
            f.write("- ✅ WRONG_FOODケースがゼロ - 完全に正しい食品がマッチしています\n")

        if nutrition_data['summary']['major_difference'] == 0:
            f.write("- ✅ MAJOR_DIFFERENCEケースがゼロ - 調理法の重大な違いはありません\n")

        f.write("\n**Full-only search (weight_main=0.0, weight_full=1.0) の採用を推奨します。**\n")

    print(f"✅ Report generated: {output_file}")

    # File size
    file_size_kb = output_file.stat().st_size / 1024
    print(f"   File size: {file_size_kb:.2f} KB")

    print("\n" + "=" * 80)
    print("✅ レポート生成完了！")
    print("=" * 80)


if __name__ == "__main__":
    try:
        generate_full_report()
    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
