#!/usr/bin/env python
"""
実際のユーザー入力シミュレーションテスト（本番データ版）
1,542件のUSDAデータで実際のユーザー検索をシミュレート
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict, Counter

def load_search_patterns(raw_file: str, prepared_file: str) -> List[Dict]:
    """両方のファイルから検索パターンを読み込み"""
    items = []

    # 生食材データ
    if Path(raw_file).exists():
        with open(raw_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            items.extend(data.get('items', []))
            print(f"✅ 生食材: {len(data.get('items', []))}件")

    # 準備済み食材データ
    if Path(prepared_file).exists():
        with open(prepared_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            items.extend(data.get('items', []))
            print(f"✅ 準備済み: {len(data.get('items', []))}件")

    return items

def search_items(query: str, items: List[Dict], max_results: int = 10) -> List[Tuple[Dict, str, float]]:
    """
    検索シミュレーション（スコアリング付き）
    Returns: List of (item, matched_pattern, score)
    """
    query_lower = query.lower()
    query_words = query_lower.split()
    matches = []

    for item in items:
        best_score = 0
        best_pattern = None

        for pattern in item.get('search_name', []):
            pattern_lower = pattern.lower()
            score = 0

            # 1. 完全一致（最高スコア）
            if pattern_lower == query_lower:
                score = 100
            # 2. 先頭一致
            elif pattern_lower.startswith(query_lower):
                score = 80 + (20 * len(query) / len(pattern))  # 短いほど高スコア
            # 3. 単語単位の完全一致
            elif all(word in pattern_lower.split() for word in query_words):
                score = 60 + (10 * len(query_words))
            # 4. 部分一致
            elif query_lower in pattern_lower:
                position = pattern_lower.find(query_lower)
                score = 40 - (position * 2)  # 前方にあるほど高スコア
            # 5. 各単語の部分一致
            elif any(word in pattern_lower for word in query_words):
                matched_words = sum(1 for word in query_words if word in pattern_lower)
                score = 20 + (10 * matched_words / len(query_words))

            if score > best_score:
                best_score = score
                best_pattern = pattern

        if best_score > 0:
            matches.append((item, best_pattern, best_score))

    # スコア順でソート
    matches.sort(key=lambda x: (-x[2], x[0]['display_name']))
    return matches[:max_results]

def run_user_scenarios():
    """実際のユーザー検索シナリオを実行"""

    # データ読み込み
    base_dir = Path("/Users/odasoya/meal_analysis_api_2/usda_data_processing/output")
    raw_file = base_dir / "usda_raw_ingredients_search_patterns.json"
    prepared_file = base_dir / "usda_prepared_ingredients_search_patterns.json"

    print("="*80)
    print("🔍 実際のユーザー入力シミュレーション")
    print("="*80)

    items = load_search_patterns(str(raw_file), str(prepared_file))
    print(f"📊 総アイテム数: {len(items)}件\n")

    # 実際のユーザー検索シナリオ
    user_scenarios = [
        {
            "name": "朝食を作る人",
            "searches": [
                ("egg", "卵を探す"),
                ("bread", "パンを探す"),
                ("milk", "牛乳を探す"),
                ("bacon", "ベーコンを探す"),
                ("coffee", "コーヒーを探す"),
                ("orange juice", "オレンジジュースを探す"),
                ("cereal", "シリアルを探す"),
            ]
        },
        {
            "name": "ランチを準備する人",
            "searches": [
                ("chicken", "鶏肉を探す"),
                ("salad", "サラダを探す"),
                ("sandwich", "サンドイッチを探す"),
                ("cheese", "チーズを探す"),
                ("tomato", "トマトを探す"),
                ("lettuce", "レタスを探す"),
            ]
        },
        {
            "name": "健康志向の人",
            "searches": [
                ("quinoa", "キヌアを探す"),
                ("kale", "ケールを探す"),
                ("tofu", "豆腐を探す"),
                ("avocado", "アボカドを探す"),
                ("nuts", "ナッツを探す"),
                ("yogurt", "ヨーグルトを探す"),
                ("salmon", "サーモンを探す"),
            ]
        },
        {
            "name": "デザートを探す人",
            "searches": [
                ("cookie", "クッキーを探す"),
                ("cake", "ケーキを探す"),
                ("ice cream", "アイスクリームを探す"),
                ("chocolate", "チョコレートを探す"),
                ("pie", "パイを探す"),
                ("pudding", "プディングを探す"),
            ]
        },
        {
            "name": "アジア料理を作る人",
            "searches": [
                ("rice", "米を探す"),
                ("soy", "大豆製品を探す"),
                ("tofu", "豆腐を探す"),
                ("noodle", "麺を探す"),
                ("miso", "味噌を探す"),
                ("rice wine", "日本酒を探す"),
            ]
        },
        {
            "name": "プログレッシブタイピング（段階的入力）",
            "searches": [
                ("c", "1文字目"),
                ("ch", "2文字目"),
                ("chi", "3文字目"),
                ("chic", "4文字目"),
                ("chick", "5文字目"),
                ("chicke", "6文字目"),
                ("chicken", "完全入力"),
            ]
        },
        {
            "name": "略語・短縮形での検索",
            "searches": [
                ("pb", "ピーナッツバター"),
                ("oj", "オレンジジュース"),
                ("mac", "マカロニ"),
                ("mayo", "マヨネーズ"),
            ]
        },
        {
            "name": "複合検索（複数単語）",
            "searches": [
                ("chocolate chip", "チョコチップ"),
                ("whole wheat", "全粒粉"),
                ("low fat", "低脂肪"),
                ("sugar free", "無糖"),
                ("grilled chicken", "グリルチキン"),
            ]
        }
    ]

    # 各シナリオを実行
    total_searches = 0
    successful_searches = 0

    for scenario in user_scenarios:
        print(f"\n{'='*60}")
        print(f"👤 {scenario['name']}")
        print('='*60)

        for query, context in scenario['searches']:
            results = search_items(query, items, max_results=5)
            total_searches += 1

            print(f"\n🔍 「{query}」({context})")

            if results:
                successful_searches += 1
                print(f"   ✅ {len(results)}件ヒット:")

                for i, (item, pattern, score) in enumerate(results[:3], 1):
                    emoji = item.get('category_emoji', '🍽️')
                    specific_emoji = item.get('food_specific_emoji', '')
                    display_emoji = specific_emoji if specific_emoji else emoji

                    print(f"   {i}. {display_emoji} {item['display_name']}")
                    if item.get('display_variant'):
                        print(f"      バリエーション: {item['display_variant']}")
                    print(f"      マッチパターン: \"{pattern}\" (スコア: {score:.1f})")
                    print(f"      元の説明: {item['description'][:50]}...")

                if len(results) > 3:
                    print(f"   ... 他{len(results)-3}件")
            else:
                print(f"   ❌ ヒットなし")

    # カテゴリ別の検索性能分析
    print("\n" + "="*80)
    print("📊 カテゴリ別カバレッジ分析")
    print("="*80)

    category_stats = defaultdict(list)
    for item in items:
        category = item.get('category', 'Unknown')
        patterns_count = len(item.get('search_name', []))
        category_stats[category].append(patterns_count)

    print("\nカテゴリ別平均パターン数（上位10）:")
    category_averages = []
    for category, pattern_counts in category_stats.items():
        avg = sum(pattern_counts) / len(pattern_counts)
        category_averages.append((category, avg, len(pattern_counts)))

    category_averages.sort(key=lambda x: -x[1])
    for category, avg_patterns, item_count in category_averages[:10]:
        emoji = "🍽️"  # デフォルト絵文字
        # カテゴリに応じた絵文字を選択（サンプル）
        if "Cookie" in category: emoji = "🍪"
        elif "Bread" in category: emoji = "🍞"
        elif "Cheese" in category: emoji = "🧀"
        elif "Fruit" in category: emoji = "🍎"
        elif "Vegetable" in category: emoji = "🥬"

        print(f"   {emoji} {category[:30]:30} : 平均{avg_patterns:.1f}パターン ({item_count}件)")

    # 最終統計
    print("\n" + "="*80)
    print("🎯 総合評価")
    print("="*80)

    success_rate = (successful_searches / total_searches * 100) if total_searches > 0 else 0
    print(f"\n検索成功率: {success_rate:.1f}% ({successful_searches}/{total_searches})")

    # パターン数の分布
    pattern_counts = Counter(len(item.get('search_name', [])) for item in items)
    print("\nパターン数の分布:")
    for count in sorted(pattern_counts.keys()):
        items_count = pattern_counts[count]
        percentage = (items_count / len(items)) * 100
        bar = "█" * int(percentage / 2)
        print(f"   {count}パターン: {items_count:4}件 ({percentage:5.1f}%) {bar}")

    # 問題のあるアイテム
    print("\n⚠️ 改善が必要なアイテム（パターン数が少ない）:")
    problematic_items = [item for item in items if len(item.get('search_name', [])) < 3]
    for item in problematic_items[:10]:
        emoji = item.get('category_emoji', '🍽️')
        patterns = item.get('search_name', [])
        print(f"   {emoji} {item['description'][:40]:40} : {len(patterns)}パターンのみ")
        print(f"      → {patterns}")

    if len(problematic_items) > 10:
        print(f"   ... 他{len(problematic_items)-10}件")

    # 推奨事項
    print("\n" + "="*80)
    print("💡 推奨事項")
    print("="*80)

    if success_rate >= 90:
        print("\n✅ 優秀な検索性能です！")
        print("   - ほとんどのユーザー検索に対応可能")
        print("   - オートコンプリートが効果的に機能します")
    elif success_rate >= 70:
        print("\n⚠️ 良好ですが改善余地があります")
        print("   - 一般的な検索には対応")
        print("   - 略語や特殊な表記への対応を強化すべき")
    else:
        print("\n❌ 改善が必要です")
        print("   - 検索パターンの追加が必要")
        print("   - ユーザーの検索意図の理解を深める必要があります")

def run_performance_test():
    """検索性能テスト"""

    print("\n" + "="*80)
    print("⚡ パフォーマンステスト")
    print("="*80)

    base_dir = Path("/Users/odasoya/meal_analysis_api_2/usda_data_processing/output")
    raw_file = base_dir / "usda_raw_ingredients_search_patterns.json"
    prepared_file = base_dir / "usda_prepared_ingredients_search_patterns.json"

    items = load_search_patterns(str(raw_file), str(prepared_file))

    test_queries = ["chicken", "bread", "milk", "cheese", "apple", "rice", "chocolate", "salmon"]

    print(f"\n{len(items)}件のアイテムで{len(test_queries)}種類のクエリをテスト...")

    start_time = time.time()
    total_results = 0

    for query in test_queries:
        results = search_items(query, items, max_results=10)
        total_results += len(results)

    elapsed_time = time.time() - start_time

    print(f"\n✅ 完了:")
    print(f"   - 処理時間: {elapsed_time:.3f}秒")
    print(f"   - 平均検索時間: {(elapsed_time / len(test_queries) * 1000):.1f}ms/クエリ")
    print(f"   - 総ヒット数: {total_results}件")
    print(f"   - 平均ヒット数: {total_results / len(test_queries):.1f}件/クエリ")

if __name__ == "__main__":
    # メイン実行
    run_user_scenarios()

    # パフォーマンステスト
    run_performance_test()