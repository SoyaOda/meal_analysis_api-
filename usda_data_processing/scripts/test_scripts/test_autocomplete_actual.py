#!/usr/bin/env python
"""
実際のサンプル内容に基づくオートコンプリートテスト
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple

def load_search_patterns(file_path: str) -> List[Dict]:
    """検索パターンファイルを読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('items', [])

def simulate_autocomplete(query: str, items: List[Dict], max_results: int = 10) -> List[Tuple[Dict, str]]:
    """オートコンプリート検索をシミュレート"""
    query_lower = query.lower()
    matches = []

    for item in items:
        for pattern in item.get('search_name', []):
            if query_lower in pattern.lower():
                matches.append((item, pattern))
                break

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

def run_actual_tests():
    """実際のサンプル内容に基づくテスト"""

    test_file = Path("/Users/odasoya/meal_analysis_api_2/usda_data_processing/output/test_results/test_search_patterns.json")

    if not test_file.exists():
        print("❌ テスト結果ファイルが見つかりません")
        return

    items = load_search_patterns(str(test_file))

    # 実際のサンプルに基づくシナリオ
    test_scenarios = [
        {
            "description": "🥤 ジュース・飲料を探す",
            "queries": [
                ("jui", "juice入力中"),
                ("juice", "juice完全"),
                ("mango", "マンゴー"),
                ("lemon", "レモネード"),
                ("fruit j", "フルーツジュース"),
                ("nectar", "ネクター"),
            ]
        },
        {
            "description": "🍘 クラッカーを探す",
            "queries": [
                ("cra", "cracker入力中"),
                ("cracker", "cracker完全"),
                ("cheese cr", "チーズクラッカー"),
                ("matzo", "マッツォ"),
            ]
        },
        {
            "description": "🫐 フルーツを探す",
            "queries": [
                ("blu", "blueberry入力中"),
                ("blue", "blue入力"),
                ("blueberry", "blueberry完全"),
                ("berr", "berry系"),
            ]
        },
        {
            "description": "🍕 ピザを探す",
            "queries": [
                ("piz", "pizza入力中"),
                ("pizza", "pizza完全"),
                ("meat p", "ミートピザ"),
                ("thin", "薄生地"),
            ]
        },
        {
            "description": "🧅 野菜を探す",
            "queries": [
                ("oni", "onion入力中"),
                ("onion", "onion完全"),
                ("green o", "グリーンオニオン"),
                ("carr", "carrot入力中"),
                ("carrot", "carrot完全"),
            ]
        },
        {
            "description": "🍰 デザートを探す",
            "queries": [
                ("pie", "パイ"),
                ("sher", "シャーベット"),
                ("choc", "チョコレート"),
                ("waff", "ワッフル"),
            ]
        },
        {
            "description": "🫒 オイル・ドレッシングを探す",
            "queries": [
                ("oil", "オイル"),
                ("cano", "キャノーラ"),
                ("dress", "ドレッシング"),
                ("poppy", "ポピーシード"),
                ("salad", "サラダ"),
            ]
        }
    ]

    print("="*80)
    print("🧪 実際のサンプル内容でのオートコンプリートテスト")
    print("="*80)
    print(f"\n📊 テスト対象: {len(items)}件のアイテム")

    # アイテムリスト表示
    print("\n📋 含まれるアイテム:")
    for item in sorted(items, key=lambda x: x['display_name'])[:10]:
        emoji = item.get('category_emoji', '🍽️')
        print(f"   {emoji} {item['display_name']}")
    if len(items) > 10:
        print(f"   ... 他{len(items)-10}件")
    print()

    # 統計
    success_count = 0
    total_queries = 0

    for scenario in test_scenarios:
        print(f"\n{scenario['description']}")
        print("-"*60)

        scenario_success = 0
        scenario_total = 0

        for query, context in scenario['queries']:
            results = simulate_autocomplete(query, items, max_results=5)
            total_queries += 1
            scenario_total += 1

            if results:
                success_count += 1
                scenario_success += 1

            print(f"\n🔍 \"{query}\" ({context})")

            if results:
                print(f"   ✅ {len(results)}件ヒット:")
                for i, (item, matched_pattern) in enumerate(results[:3], 1):
                    emoji = item.get('category_emoji', '🍽️')
                    print(f"      {i}. {emoji} {item['display_name']}")
                    print(f"         パターン: \"{matched_pattern}\"")
                if len(results) > 3:
                    print(f"      ... 他{len(results)-3}件")
            else:
                print("   ❌ ヒットなし")

        # シナリオごとの成功率
        if scenario_total > 0:
            success_rate = (scenario_success / scenario_total) * 100
            print(f"\n   📈 成功率: {success_rate:.1f}% ({scenario_success}/{scenario_total})")

    # 全体統計
    print("\n" + "="*80)
    print("📊 全体統計")
    print("="*80)

    if total_queries > 0:
        overall_success_rate = (success_count / total_queries) * 100
        print(f"\n✅ 全体成功率: {overall_success_rate:.1f}% ({success_count}/{total_queries}クエリ)")

        if overall_success_rate >= 80:
            print("\n🎯 評価: 優秀")
            print("   オートコンプリートとして十分な品質です")
        elif overall_success_rate >= 60:
            print("\n⚠️ 評価: 良好だが改善余地あり")
            print("   基本的な検索は機能しますが、パターンを増やすと良いでしょう")
        else:
            print("\n❌ 評価: 改善が必要")
            print("   検索パターンの見直しが必要です")

    # パターン分析
    print("\n" + "="*80)
    print("🔍 パターン品質分析")
    print("="*80)

    pattern_stats = {
        "完全名称あり": 0,
        "略称あり": 0,
        "カテゴリ名あり": 0,
        "部分一致可能": 0,
    }

    for item in items:
        patterns = item.get('search_name', [])
        patterns_lower = [p.lower() for p in patterns]

        # 完全名称チェック
        display_lower = item['display_name'].lower()
        if any(display_lower in p for p in patterns_lower):
            pattern_stats["完全名称あり"] += 1

        # 略称チェック（3文字以下のパターン）
        if any(len(p) <= 5 for p in patterns):
            pattern_stats["略称あり"] += 1

        # カテゴリ名チェック
        categories = ["juice", "oil", "cracker", "pie", "drink", "bar", "fruit"]
        if any(any(cat in p for cat in categories) for p in patterns_lower):
            pattern_stats["カテゴリ名あり"] += 1

        # 部分一致可能（スペースを含むパターン）
        if any(' ' in p for p in patterns):
            pattern_stats["部分一致可能"] += 1

    print("\nパターン特徴（20件中）:")
    for feature, count in pattern_stats.items():
        percentage = (count / len(items)) * 100
        print(f"   {feature}: {count}件 ({percentage:.1f}%)")

    # 推奨事項
    print("\n" + "="*80)
    print("💡 推奨事項")
    print("="*80)

    if overall_success_rate >= 80:
        print("\n✅ 現在のプロンプトは良好に機能しています")
        print("   本番処理に進んでも問題ないでしょう")
    else:
        print("\n改善案:")
        print("   1. より多くの略称パターンを追加")
        print("   2. 一般的な入力ミス（タイポ）を考慮")
        print("   3. 複数形/単数形のバリエーション追加")

if __name__ == "__main__":
    run_actual_tests()