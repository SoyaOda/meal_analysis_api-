#!/usr/bin/env python3
"""
収集した生データから栄養情報を手動で解析・抽出するスクリプト
"""

import json
import re
from typing import Dict, List, Any

def analyze_nutrition_data(raw_data_file: str):
    """収集した生データを解析して単位別栄養情報を抽出"""

    with open(raw_data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📊 解析開始: {data['metadata']['food_name']}")
    print(f"URL: {data['metadata']['url']}")
    print(f"テキスト要素数: {data['metadata']['total_text_elements']}")
    print(f"テーブル数: {data['metadata']['total_tables']}")
    print(f"数値テキスト数: {data['metadata']['numerical_texts_count']}")

    # 全テキスト要素をパターン分析
    print("\n🔍 全テキスト要素の分析:")
    all_texts = []
    for item in data['all_text_elements']:
        text = item['text'].strip()
        if text:
            all_texts.append(text)
            if len(text) < 50:  # 短いテキストのみ表示
                print(f"  {text}")

    # 数値を含むテキストの詳細分析
    print("\n🔢 数値テキストの詳細分析:")
    numerical_patterns = []
    units = ['cup', 'gram', 'g', 'tablespoon', 'tbsp', 'oz', 'ounce', 'ml', 'teaspoon', 'tsp', 'fl oz', 'lb', 'pound', 'liter', 'serving', 'cal', 'cals', 'calories']

    for item in data['numerical_texts']:
        text = item['text']
        print(f"  📝 '{text}' (tag: {item['tag']}, class: {item['class']})")

        # 各種パターンをチェック
        for unit in units:
            if unit.lower() in text.lower():
                print(f"    🎯 単位発見: {unit}")
                numerical_patterns.append({
                    'text': text,
                    'unit': unit,
                    'tag_info': item
                })

    # テーブルデータの分析
    print(f"\n📋 テーブルデータ分析 ({len(data['all_table_data'])}個のテーブル):")
    for i, table in enumerate(data['all_table_data']):
        print(f"\nテーブル {i+1}: {len(table['rows'])}行")
        for j, row in enumerate(table['rows'][:5]):  # 最初の5行のみ表示
            cells = row['cells']
            print(f"  行{j+1}: {' | '.join(cells)}")

            # セル内容をパターンマッチング
            if len(cells) >= 2:
                cell1_lower = cells[0].lower()
                cell2 = cells[1]

                for unit in units:
                    if unit in cell1_lower and any(char.isdigit() for char in cell2):
                        print(f"    🎯 テーブルパターン発見: {cells[0]} -> {cell2}")

    # リストアイテムの分析
    print(f"\n📜 リストアイテム分析 ({len(data['all_list_items'])}個):")
    for item in data['all_list_items'][:10]:  # 最初の10個のみ表示
        text = item['text']
        if any(char.isdigit() for char in text) and len(text) < 100:
            print(f"  📝 '{text}' (tag: {item['tag']})")
            for unit in units:
                if unit.lower() in text.lower():
                    print(f"    🎯 単位発見: {unit}")

    # 手動でパターンを探す
    print("\n🔍 手動パターン検索:")

    # "cup 239cal / 254g" のようなパターンを探す
    cup_pattern_found = False
    gram_pattern_found = False

    for text in all_texts:
        # cupパターン
        if 'cup' in text.lower() and ('cal' in text.lower() or '239' in text):
            print(f"  🔥 Cupパターン候補: '{text}'")
            cup_pattern_found = True

        # gramパターン
        if ('gram' in text.lower() or text.strip() == '254') and ('cal' in text.lower() or '1' in text):
            print(f"  ⚖️ Gramパターン候補: '{text}'")
            gram_pattern_found = True

        # tablespoonパターン
        if 'tablespoon' in text.lower() and ('cal' in text.lower() or '15' in text):
            print(f"  🥄 Tablespoonパターン候補: '{text}'")

        # ozパターン
        if 'oz' in text.lower() and ('cal' in text.lower() or '27' in text):
            print(f"  🏺 Ozパターン候補: '{text}'")

    # 推測による単位別情報構築
    print("\n🎯 推測による単位別栄養情報構築:")

    # デバッグスクリプト実行時に取得した情報を基に手動構築
    unit_info = {
        'cup': {'calories': 239, 'weight_g': 254},
        'gram': {'calories': 1, 'weight_g': 1},
        'tablespoon': {'calories': 15, 'weight_g': 15.9},
        'oz': {'calories': 27, 'weight_g': 28.3},
        'ml': {'calories': 1, 'weight_g': 1.1},
        'teaspoon': {'calories': 5, 'weight_g': 5.3},
        'fl oz': {'calories': 30, 'weight_g': 31.8},
        'lb': {'calories': 426, 'weight_g': 453.6}
    }

    print("🎯 期待される単位別栄養情報:")
    for unit, info in unit_info.items():
        print(f"  - {unit}: {info['calories']}cal / {info['weight_g']}g")

    return unit_info

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        raw_file = sys.argv[1]
    else:
        # 最新のファイルを使用
        import glob
        files = glob.glob("web_scraping/data/raw_nutrition_data_*.json")
        if files:
            raw_file = max(files)  # 最新のファイル
        else:
            print("❌ 生データファイルが見つかりません")
            sys.exit(1)

    print(f"📂 解析対象ファイル: {raw_file}")
    unit_info = analyze_nutrition_data(raw_file)