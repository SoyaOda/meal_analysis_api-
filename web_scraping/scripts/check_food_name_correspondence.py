#!/usr/bin/env python3
"""
mynetdiary_search_names.txtの1,142食材と
all_foods_final_1152.jsonの対応を確認するスクリプト
"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher


def normalize_food_name(name: str) -> str:
    """食材名を正規化（比較用）"""
    # 小文字化
    normalized = name.lower().strip()

    # カロリー情報を削除（"60cals", "0cals"など）
    normalized = re.sub(r'\s+\d+cals?$', '', normalized)

    # 改行削除
    normalized = normalized.replace('\n', ' ')

    # 連続スペースを1つに
    normalized = re.sub(r'\s+', ' ', normalized)

    return normalized


def extract_base_name(display_name: str) -> str:
    """
    表示名からベース名を抽出
    例: "Anchovy canned, oz, boneless\n60cals" -> "Anchovy canned"
    """
    # カロリー情報削除
    base = re.sub(r'\s+\d+cals?$', '', display_name)

    # 改行削除
    base = base.replace('\n', ' ')

    # ", oz, boneless"のような詳細情報を削除
    # カンマの後の情報を削除
    if ',' in base:
        base = base.split(',')[0]

    return base.strip()


def similarity_ratio(str1: str, str2: str) -> float:
    """2つの文字列の類似度を計算（0.0-1.0）"""
    return SequenceMatcher(None, str1, str2).ratio()


def main():
    # ファイルパス
    search_names_file = Path('/Users/odasoya/meal_analysis_api_2/data/mynetdiary_search_names.txt')
    final_json_file = Path('processed_data/all_foods_final_1152.json')

    print("🔍 食材名対応チェックシステム")
    print("=" * 80)

    # 1. mynetdiary_search_names.txtを読み込み
    with open(search_names_file, 'r', encoding='utf-8') as f:
        search_names = [line.strip() for line in f if line.strip()]

    print(f"📋 検索名ファイル: {len(search_names)}個の食材")

    # 2. all_foods_final_1152.jsonを読み込み
    with open(final_json_file, 'r', encoding='utf-8') as f:
        final_data = json.load(f)

    foods = final_data['foods']
    print(f"📋 最終JSONファイル: {len(foods)}個の食材")

    # 3. 正規化された名前でインデックス作成
    json_foods_index = {}
    json_foods_base_index = {}

    for food in foods:
        food_name = food['food_name']
        normalized = normalize_food_name(food_name)
        base_name = normalize_food_name(extract_base_name(food_name))

        # 完全一致用インデックス
        json_foods_index[normalized] = food

        # ベース名用インデックス
        if base_name not in json_foods_base_index:
            json_foods_base_index[base_name] = []
        json_foods_base_index[base_name].append(food)

    print(f"\n📊 インデックス構築完了")
    print(f"   完全一致インデックス: {len(json_foods_index)}個")
    print(f"   ベース名インデックス: {len(json_foods_base_index)}個")

    # 4. 対応チェック
    print(f"\n🔍 対応チェック実行中...")
    print("=" * 80)

    exact_matches = []
    base_matches = []
    no_matches = []

    for search_name in search_names:
        normalized_search = normalize_food_name(search_name)

        # 完全一致チェック
        if normalized_search in json_foods_index:
            exact_matches.append({
                'search_name': search_name,
                'matched_food': json_foods_index[normalized_search]['food_name'],
                'match_type': 'exact'
            })
        # ベース名一致チェック
        elif normalized_search in json_foods_base_index:
            matched_foods = json_foods_base_index[normalized_search]
            base_matches.append({
                'search_name': search_name,
                'matched_foods': [f['food_name'] for f in matched_foods],
                'match_type': 'base',
                'count': len(matched_foods)
            })
        else:
            # 類似度チェック（上位3件）
            similarities = []
            for json_name, food in json_foods_index.items():
                ratio = similarity_ratio(normalized_search, json_name)
                if ratio > 0.6:  # 60%以上の類似度
                    similarities.append({
                        'food_name': food['food_name'],
                        'ratio': ratio
                    })

            similarities.sort(key=lambda x: x['ratio'], reverse=True)

            no_matches.append({
                'search_name': search_name,
                'similar_foods': similarities[:3] if similarities else []
            })

    # 5. 結果表示
    print(f"\n✅ 完全一致: {len(exact_matches)}個")
    print(f"🔶 ベース名一致: {len(base_matches)}個")
    print(f"❌ 未一致: {len(no_matches)}個")

    print(f"\n" + "=" * 80)
    print("📊 詳細結果")
    print("=" * 80)

    # ベース名一致の詳細
    if base_matches:
        print(f"\n🔶 ベース名一致（{len(base_matches)}個）:")
        for i, match in enumerate(base_matches[:10], 1):
            print(f"\n{i}. 検索名: {match['search_name']}")
            print(f"   一致食材 ({match['count']}個):")
            for food_name in match['matched_foods']:
                print(f"      - {food_name}")

        if len(base_matches) > 10:
            print(f"\n   ... 他 {len(base_matches) - 10}個")

    # 未一致の詳細
    if no_matches:
        print(f"\n❌ 未一致食材（{len(no_matches)}個）:")
        for i, no_match in enumerate(no_matches[:20], 1):
            print(f"\n{i}. 検索名: {no_match['search_name']}")
            if no_match['similar_foods']:
                print(f"   類似食材:")
                for sim in no_match['similar_foods']:
                    print(f"      - {sim['food_name']} (類似度: {sim['ratio']:.2%})")
            else:
                print(f"   類似食材: なし")

        if len(no_matches) > 20:
            print(f"\n   ... 他 {len(no_matches) - 20}個")

    # 6. サマリー保存
    summary = {
        'total_search_names': len(search_names),
        'total_json_foods': len(foods),
        'exact_matches': len(exact_matches),
        'base_matches': len(base_matches),
        'no_matches': len(no_matches),
        'match_rate': (len(exact_matches) + len(base_matches)) / len(search_names) * 100,
        'exact_match_list': exact_matches,
        'base_match_list': base_matches,
        'no_match_list': no_matches
    }

    output_file = 'processed_data/food_name_correspondence_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n" + "=" * 80)
    print(f"💾 レポート保存: {output_file}")
    print(f"\n📈 一致率: {summary['match_rate']:.1f}%")
    print(f"   完全一致: {len(exact_matches)}個")
    print(f"   ベース名一致: {len(base_matches)}個")
    print(f"   未一致: {len(no_matches)}個")


if __name__ == "__main__":
    main()
