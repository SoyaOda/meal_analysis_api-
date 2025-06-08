#!/usr/bin/env python3
"""
Nutrition Search Results Formatter

栄養検索結果を読みやすい形式に整形するスクリプト
特に、どのクエリでどの結果が採択されたかを明確に表示する
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse


def format_search_results(analysis_dir: str, output_format: str = "markdown"):
    """
    分析結果ディレクトリから検索結果を読み込み、読みやすい形式に整形する
    
    Args:
        analysis_dir: 分析結果ディレクトリのパス
        output_format: 出力形式 ("markdown" または "html")
    """
    
    # ファイルパスの設定
    search_query_dir = Path(analysis_dir) / "nutrition_search_query"
    input_output_file = search_query_dir / "input_output.json"
    search_results_file = search_query_dir / "search_results.md"
    
    if not input_output_file.exists():
        print(f"❌ Error: {input_output_file} not found")
        return
    
    # データの読み込み
    with open(input_output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 入力データの解析
    input_str = data['input_data']['data']
    input_data = eval(input_str)  # 注意: 本来はastを使う方が安全
    
    # 出力データの解析
    output_str = data['output_data']['data']
    output_data = eval(output_str)  # 注意: 本来はastを使う方が安全
    
    matches = output_data['matches']
    statistics = output_data['statistics']
    metadata = data['search_metadata']
    
    # 整形された結果を生成
    if output_format == "markdown":
        formatted_content = generate_markdown_report(
            input_data, matches, statistics, metadata, data['execution_time_seconds']
        )
        output_file = search_query_dir / "formatted_search_results.md"
    else:  # HTML
        formatted_content = generate_html_report(
            input_data, matches, statistics, metadata, data['execution_time_seconds']
        )
        output_file = search_query_dir / "formatted_search_results.html"
    
    # ファイルに出力
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(formatted_content)
    
    print(f"✅ Formatted results saved to: {output_file}")
    return output_file


def generate_markdown_report(input_data, matches, statistics, metadata, execution_time):
    """Markdown形式のレポートを生成"""
    
    report = []
    
    # ヘッダー
    report.append("# 🔍 栄養データベース検索結果レポート")
    report.append("")
    report.append(f"**実行時間**: {execution_time:.3f}秒")
    report.append(f"**検索方法**: {metadata['search_method']}")
    report.append(f"**データベース**: {metadata['database_source']}")
    report.append(f"**実行日時**: {metadata['timestamp']}")
    report.append("")
    
    # 統計情報
    report.append("## 📊 検索統計")
    report.append(f"- **総検索数**: {statistics['total_searches']}")
    report.append(f"- **成功マッチ数**: {statistics['successful_matches']}")
    report.append(f"- **マッチ率**: {statistics['match_rate']:.1f}%")
    report.append("")
    
    # 目標栄養プロファイル
    target_nutrition = input_data.get('target_nutrition_profile', {})
    if target_nutrition:
        report.append("## 🎯 目標栄養プロファイル")
        report.append(f"- **カロリー**: {target_nutrition.get('calories', 0):.1f} kcal")
        report.append(f"- **タンパク質**: {target_nutrition.get('protein_g', 0):.1f} g")
        report.append(f"- **脂質**: {target_nutrition.get('fat_total_g', 0):.1f} g")
        report.append(f"- **炭水化物**: {target_nutrition.get('carbohydrate_by_difference_g', 0):.1f} g")
        report.append("")
    
    # 食材検索結果
    ingredient_names = input_data.get('ingredient_names', [])
    if ingredient_names:
        report.append("## 🥗 食材検索結果")
        report.append("")
        
        for i, ingredient in enumerate(ingredient_names, 1):
            if ingredient in matches:
                match = matches[ingredient]
                report.append(f"### {i}. {ingredient}")
                report.append("")
                report.append(f"**🎯 クエリ**: `{ingredient}`")
                report.append(f"**✅ 採択結果**: {match['description']}")
                report.append(f"**📊 スコア**: {match['score']:.4f}")
                report.append(f"**🏷️ タイプ**: {match['data_type']}")
                report.append(f"**🆔 ID**: {match['id']}")
                report.append("")
                
                # 栄養情報
                report.append("**🍽️ 栄養情報 (100gあたり)**:")
                for nutrient in match['nutrients']:
                    report.append(f"- {nutrient['name']}: {nutrient['amount']:.1f} {nutrient['unit_name']}")
                report.append("")
                
                # 検索詳細
                original_data = match.get('original_data', {})
                if original_data:
                    report.append("**🔍 検索詳細**:")
                    report.append(f"- 元スコア: {original_data.get('score_normalization', 'N/A')}")
                    report.append(f"- 検索方法: {original_data.get('search_method', 'N/A')}")
                    report.append(f"- 検索タイプ: {original_data.get('search_type', 'N/A')}")
                report.append("")
                report.append("---")
                report.append("")
            else:
                report.append(f"### {i}. {ingredient}")
                report.append("**❌ マッチなし**")
                report.append("---")
                report.append("")
    
    # 料理検索結果
    dish_names = input_data.get('dish_names', [])
    if dish_names:
        report.append("## 🍽️ 料理検索結果")
        report.append("")
        
        for i, dish in enumerate(dish_names, 1):
            if dish in matches:
                match = matches[dish]
                report.append(f"### {i}. {dish}")
                report.append("")
                report.append(f"**🎯 クエリ**: `{dish}`")
                report.append(f"**✅ 採択結果**: {match['description']}")
                report.append(f"**📊 スコア**: {match['score']:.4f}")
                report.append(f"**🏷️ タイプ**: {match['data_type']}")
                report.append(f"**🆔 ID**: {match['id']}")
                report.append("")
                
                # 栄養情報
                report.append("**🍽️ 栄養情報 (100gあたり)**:")
                for nutrient in match['nutrients']:
                    report.append(f"- {nutrient['name']}: {nutrient['amount']:.1f} {nutrient['unit_name']}")
                report.append("")
                
                # 検索詳細
                original_data = match.get('original_data', {})
                if original_data:
                    report.append("**🔍 検索詳細**:")
                    report.append(f"- 元スコア: {original_data.get('score_normalization', 'N/A')}")
                    report.append(f"- 検索方法: {original_data.get('search_method', 'N/A')}")
                    report.append(f"- 検索タイプ: {original_data.get('search_type', 'N/A')}")
                report.append("")
                report.append("---")
                report.append("")
            else:
                report.append(f"### {i}. {dish}")
                report.append("**❌ マッチなし**")
                report.append("---")
                report.append("")
    
    # スコア順ランキング
    report.append("## 🏆 スコア順ランキング")
    report.append("")
    
    # すべてのマッチをスコア順にソート
    sorted_matches = sorted(matches.items(), key=lambda x: x[1]['score'], reverse=True)
    
    for rank, (query, match) in enumerate(sorted_matches, 1):
        score_bar = "🟩" * int(match['score'] * 10) + "⬜" * (10 - int(match['score'] * 10))
        report.append(f"{rank}. **{query}** → {match['description']}")
        report.append(f"   スコア: {match['score']:.4f} {score_bar}")
        report.append("")
    
    return "\n".join(report)


def generate_html_report(input_data, matches, statistics, metadata, execution_time):
    """HTML形式のレポートを生成"""
    
    html = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>栄養データベース検索結果レポート</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }
        .stats { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .search-item { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .match { background: #d4edda; border-color: #c3e6cb; }
        .no-match { background: #f8d7da; border-color: #f5c6cb; }
        .score-bar { display: inline-block; width: 100px; height: 10px; background: #eee; border-radius: 5px; overflow: hidden; }
        .score-fill { height: 100%; background: linear-gradient(90deg, #28a745, #ffc107, #dc3545); transition: width 0.3s; }
        .nutrition-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin: 10px 0; }
        .nutrition-item { background: #e9ecef; padding: 8px; border-radius: 3px; text-align: center; }
        .ranking { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .rank-item { display: flex; align-items: center; justify-content: space-between; padding: 8px; margin: 5px 0; background: white; border-radius: 3px; }
    </style>
</head>
<body>
"""
    
    # ヘッダー
    html += f"""
    <div class="header">
        <h1>🔍 栄養データベース検索結果レポート</h1>
        <p><strong>実行時間:</strong> {execution_time:.3f}秒 | 
        <strong>検索方法:</strong> {metadata['search_method']} | 
        <strong>データベース:</strong> {metadata['database_source']}</p>
        <p><strong>実行日時:</strong> {metadata['timestamp']}</p>
    </div>
    """
    
    # 統計情報
    match_rate = statistics['match_rate']
    html += f"""
    <div class="stats">
        <h2>📊 検索統計</h2>
        <p><strong>総検索数:</strong> {statistics['total_searches']} | 
        <strong>成功マッチ数:</strong> {statistics['successful_matches']} | 
        <strong>マッチ率:</strong> {match_rate:.1f}%</p>
        <div class="score-bar">
            <div class="score-fill" style="width: {match_rate}%"></div>
        </div>
    </div>
    """
    
    # 検索結果
    ingredient_names = input_data.get('ingredient_names', [])
    dish_names = input_data.get('dish_names', [])
    
    # 食材検索結果
    if ingredient_names:
        html += "<h2>🥗 食材検索結果</h2>"
        for ingredient in ingredient_names:
            if ingredient in matches:
                match = matches[ingredient]
                html += f"""
                <div class="search-item match">
                    <h3>🎯 {ingredient} → ✅ {match['description']}</h3>
                    <p><strong>スコア:</strong> {match['score']:.4f} | 
                    <strong>タイプ:</strong> {match['data_type']} | 
                    <strong>ID:</strong> {match['id']}</p>
                    
                    <div class="nutrition-grid">
                """
                for nutrient in match['nutrients']:
                    html += f'<div class="nutrition-item"><strong>{nutrient["name"]}</strong><br>{nutrient["amount"]:.1f} {nutrient["unit_name"]}</div>'
                
                html += "</div></div>"
            else:
                html += f'<div class="search-item no-match"><h3>🎯 {ingredient} → ❌ マッチなし</h3></div>'
    
    # 料理検索結果
    if dish_names:
        html += "<h2>🍽️ 料理検索結果</h2>"
        for dish in dish_names:
            if dish in matches:
                match = matches[dish]
                html += f"""
                <div class="search-item match">
                    <h3>🎯 {dish} → ✅ {match['description']}</h3>
                    <p><strong>スコア:</strong> {match['score']:.4f} | 
                    <strong>タイプ:</strong> {match['data_type']} | 
                    <strong>ID:</strong> {match['id']}</p>
                    
                    <div class="nutrition-grid">
                """
                for nutrient in match['nutrients']:
                    html += f'<div class="nutrition-item"><strong>{nutrient["name"]}</strong><br>{nutrient["amount"]:.1f} {nutrient["unit_name"]}</div>'
                
                html += "</div></div>"
            else:
                html += f'<div class="search-item no-match"><h3>🎯 {dish} → ❌ マッチなし</h3></div>'
    
    # スコア順ランキング
    html += '<div class="ranking"><h2>🏆 スコア順ランキング</h2>'
    sorted_matches = sorted(matches.items(), key=lambda x: x[1]['score'], reverse=True)
    
    for rank, (query, match) in enumerate(sorted_matches, 1):
        score_width = int(match['score'] * 100)
        html += f"""
        <div class="rank-item">
            <span><strong>{rank}.</strong> {query} → {match['description']}</span>
            <span>
                {match['score']:.4f}
                <div class="score-bar">
                    <div class="score-fill" style="width: {score_width}%"></div>
                </div>
            </span>
        </div>
        """
    
    html += "</div>"
    html += "</body></html>"
    
    return html


def main():
    parser = argparse.ArgumentParser(description="栄養検索結果を読みやすい形式に整形")
    parser.add_argument("analysis_dir", help="分析結果ディレクトリのパス")
    parser.add_argument("--format", choices=["markdown", "html"], default="markdown", 
                       help="出力形式 (default: markdown)")
    parser.add_argument("--latest", action="store_true", 
                       help="最新の分析結果を自動選択")
    
    args = parser.parse_args()
    
    if args.latest:
        # analysis_resultsディレクトリから最新を選択
        analysis_results_dir = Path("analysis_results")
        if not analysis_results_dir.exists():
            print("❌ Error: analysis_results directory not found")
            return
        
        # 最新のディレクトリを取得
        analysis_dirs = [d for d in analysis_results_dir.iterdir() if d.is_dir()]
        if not analysis_dirs:
            print("❌ Error: No analysis directories found")
            return
        
        latest_dir = max(analysis_dirs, key=lambda x: x.name)
        print(f"📂 Using latest analysis: {latest_dir.name}")
        args.analysis_dir = str(latest_dir)
    
    format_search_results(args.analysis_dir, args.format)


if __name__ == "__main__":
    main() 