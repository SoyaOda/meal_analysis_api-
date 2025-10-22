#!/usr/bin/env python
"""
オートコンプリート検索のシミュレーションテスト
実際のユーザー入力パターンでsearch_nameの品質を検証
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

def load_search_patterns(file_path: str) -> List[Dict]:
    """検索パターンファイルを読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('items', [])

def simulate_autocomplete(query: str, items: List[Dict], max_results: int = 10) -> List[Tuple[Dict, str]]:
    """
    オートコンプリート検索をシミュレート
    部分一致で候補を返す（大文字小文字無視）
    """
    query_lower = query.lower()
    matches = []

    for item in items:
        for pattern in item.get('search_name', []):
            if query_lower in pattern.lower():
                # マッチしたパターンと共に返す
                matches.append((item, pattern))
                break  # 1つのアイテムは1回だけ含める

    # 最もクエリに近いものを優先
    # 1. 完全一致（先頭）
    # 2. 先頭一致
    # 3. 部分一致
    def sort_key(match):
        item, pattern = match
        pattern_lower = pattern.lower()
        if pattern_lower == query_lower:
            return (0, pattern)  # 完全一致
        elif pattern_lower.startswith(query_lower):
            return (1, pattern)  # 先頭一致
        else:
            return (2, pattern)  # 部分一致

    matches.sort(key=sort_key)
    return matches[:max_results]

def run_test_queries():
    """実際のユーザー入力パターンでテスト"""

    # テスト結果ファイルを読み込み
    test_file = Path("/Users/odasoya/meal_analysis_api_2/usda_data_processing/output/test_results/test_search_patterns.json")

    if not test_file.exists():
        print("❌ テスト結果ファイルが見つかりません")
        print("   先に python split_ingredient_names_with_llm_v2.py --test を実行してください")
        return

    items = load_search_patterns(str(test_file))

    # 実際のユーザー入力シナリオ
    test_scenarios = [
        {
            "description": "🍪 ユーザーがクッキーを探す",
            "queries": [
                ("c", "最初の1文字"),
                ("co", "2文字目"),
                ("coo", "3文字目"),
                ("cook", "4文字目"),
                ("cookie", "完全入力"),
                ("choc", "チョコレート系を探す"),
                ("chocolate", "チョコレート"),
            ]
        },
        {
            "description": "🍕 ユーザーがピザを探す",
            "queries": [
                ("p", "最初の1文字"),
                ("pi", "2文字目"),
                ("piz", "3文字目"),
                ("pizza", "完全入力"),
                ("cheese p", "チーズピザを探す"),
                ("thin", "薄生地を探す"),
            ]
        },
        {
            "description": "🍗 ユーザーが鶏肉を探す",
            "queries": [
                ("ch", "最初の2文字"),
                ("chi", "3文字目"),
                ("chick", "4-5文字目"),
                ("chicken", "完全入力"),
                ("grilled", "グリルされたもの"),
                ("breast", "胸肉"),
            ]
        },
        {
            "description": "☕ ユーザーが飲み物を探す",
            "queries": [
                ("tea", "お茶"),
                ("green t", "緑茶"),
                ("coffee", "コーヒー"),
                ("coff cream", "コーヒークリーマー"),
            ]
        },
        {
            "description": "🥗 ユーザーがサラダ関連を探す",
            "queries": [
                ("dress", "ドレッシング"),
                ("caesar", "シーザー"),
                ("salad", "サラダ"),
            ]
        },
        {
            "description": "🍞 ユーザーがパンを探す",
            "queries": [
                ("bre", "パンの略"),
                ("bread", "パン"),
                ("roll", "ロール"),
                ("bun", "バンズ"),
                ("hot dog", "ホットドッグ"),
            ]
        }
    ]

    print("="*80)
    print("🧪 オートコンプリート検索シミュレーション")
    print("="*80)
    print(f"\n📊 テスト対象: {len(items)}件のアイテム")
    print()

    # 各シナリオをテスト
    for scenario in test_scenarios:
        print(f"\n{scenario['description']}")
        print("-"*60)

        for query, context in scenario['queries']:
            results = simulate_autocomplete(query, items, max_results=5)

            print(f"\n🔍 入力: \"{query}\" ({context})")

            if results:
                print(f"   → {len(results)}件ヒット:")
                for i, (item, matched_pattern) in enumerate(results[:3], 1):
                    emoji = item.get('category_emoji', '🍽️')
                    print(f"      {i}. {emoji} {item['display_name']}")
                    print(f"         マッチ: \"{matched_pattern}\"")
                    print(f"         元: {item['description'][:40]}...")

                if len(results) > 3:
                    print(f"      ... 他{len(results)-3}件")
            else:
                print("   ❌ ヒットなし")

    # 統計分析
    print("\n" + "="*80)
    print("📊 カバレッジ分析")
    print("="*80)

    # 各アイテムがどれくらいの入力パターンでヒットするか
    coverage_stats = defaultdict(int)

    test_patterns = [
        # 1文字
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        # 一般的な食品検索
        "ch", "br", "co", "sa", "pi", "be", "gr", "fr", "to", "ba",
        "chicken", "bread", "cookie", "salad", "pizza", "beef", "rice",
        "tea", "coffee", "cheese", "milk", "egg", "fish", "pasta"
    ]

    for item in items:
        hit_count = 0
        for query in test_patterns:
            for pattern in item.get('search_name', []):
                if query.lower() in pattern.lower():
                    hit_count += 1
                    break

        if hit_count == 0:
            coverage_stats["ヒットなし"] += 1
        elif hit_count <= 2:
            coverage_stats["低カバレッジ(1-2)"] += 1
        elif hit_count <= 5:
            coverage_stats["中カバレッジ(3-5)"] += 1
        else:
            coverage_stats["高カバレッジ(6+)"] += 1

    print("\nアイテムのアクセシビリティ:")
    for category, count in sorted(coverage_stats.items()):
        percentage = (count / len(items)) * 100
        print(f"   {category}: {count}件 ({percentage:.1f}%)")

    # パターン品質チェック
    print("\n" + "="*80)
    print("⚠️ 潜在的な問題")
    print("="*80)

    issues = []
    for item in items:
        patterns = item.get('search_name', [])

        # 過度に短い/一般的なパターンをチェック
        for pattern in patterns:
            if len(pattern) <= 2 and pattern.lower() in ["a", "an", "in", "on", "or", "of"]:
                issues.append(f"過度に一般的: \"{pattern}\" in {item['description']}")

        # パターンが少なすぎる
        if len(patterns) < 3:
            issues.append(f"パターン不足({len(patterns)}個): {item['description']}")

    if issues:
        for i, issue in enumerate(issues[:10], 1):
            print(f"   {i}. {issue}")
        if len(issues) > 10:
            print(f"   ... 他{len(issues)-10}件")
    else:
        print("   ✅ 重大な問題は検出されませんでした")

    # 推奨事項
    print("\n" + "="*80)
    print("💡 結論と推奨事項")
    print("="*80)

    high_coverage = coverage_stats.get("高カバレッジ(6+)", 0)
    no_coverage = coverage_stats.get("ヒットなし", 0)

    total = len(items)
    high_percentage = (high_coverage / total) * 100 if total > 0 else 0
    no_percentage = (no_coverage / total) * 100 if total > 0 else 0

    print(f"\n✅ 良好な点:")
    print(f"   - {high_percentage:.1f}%のアイテムが高カバレッジ")
    print(f"   - 多様な入力パターンに対応")

    if no_percentage > 10:
        print(f"\n⚠️ 改善が必要な点:")
        print(f"   - {no_percentage:.1f}%のアイテムがヒットしにくい")
        print(f"   - より一般的なパターンの追加を検討")

    print("\n📋 次のステップ:")
    print("   1. 問題のあるアイテムのパターンを確認")
    print("   2. 必要に応じてプロンプトを微調整")
    print("   3. 本番データで処理を実行")

if __name__ == "__main__":
    run_test_queries()