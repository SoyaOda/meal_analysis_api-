#!/usr/bin/env python3
"""
生の栄養データを解析して利用可能な栄養素情報を特定するスクリプト
"""

import json
import re
from typing import Dict, List, Any

def analyze_raw_nutrition_data(json_file: str):
    """生の栄養データを解析して利用可能な情報を特定"""

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    food = data['foods'][0]
    raw_data = food['raw_data']

    print(f"📊 生データ解析: {food['name']}")
    print(f"=" * 60)
    print(f"全テキスト要素数: {len(raw_data['all_texts'])}")
    print(f"数値テキスト要素数: {len(raw_data['numerical_texts'])}")
    print(f"テーブル数: {len(raw_data['table_data'])}")
    print(f"リスト項目数: {len(raw_data['list_items'])}")

    # 栄養素関連のキーワードを定義
    nutrition_keywords = [
        'protein', 'タンパク質', 'プロテイン',
        'fat', 'lipid', '脂質', '脂肪',
        'carb', 'carbohydrate', '炭水化物', '糖質',
        'fiber', 'fibre', '繊維', '食物繊維',
        'sugar', '砂糖', '糖分',
        'sodium', 'ナトリウム', '塩分',
        'calcium', 'カルシウム',
        'iron', '鉄', 'アイアン',
        'vitamin', 'ビタミン',
        'potassium', 'カリウム',
        'magnesium', 'マグネシウム',
        'zinc', '亜鉛',
        'cholesterol', 'コレステロール'
    ]

    print("\n🔍 栄養素関連テキストの検索:")
    print("-" * 40)

    nutrition_related_texts = []

    # 全テキストから栄養素関連を検索
    for item in raw_data['all_texts']:
        text = item['text'].lower()
        for keyword in nutrition_keywords:
            if keyword.lower() in text:
                nutrition_related_texts.append(item)
                print(f"  ✅ '{item['text']}' (tag: {item['tag']}, class: {item['class'][:30]})")
                break

    print(f"\n栄養素関連テキスト数: {len(nutrition_related_texts)}")

    # 数値を含むテキストで栄養素関連のものを検索
    print("\n🔢 数値付き栄養素情報:")
    print("-" * 40)

    nutritional_values = []
    for item in raw_data['numerical_texts']:
        text = item['text'].lower()
        for keyword in nutrition_keywords:
            if keyword.lower() in text:
                nutritional_values.append(item)
                print(f"  📊 '{item['text']}' (tag: {item['tag']})")

                # 数値を抽出してみる
                numbers = re.findall(r'\d+(?:\.\d+)?', item['text'])
                if numbers:
                    print(f"      数値: {numbers}")
                break

    # テーブルデータから栄養情報を検索
    print(f"\n📋 テーブル内容解析 ({len(raw_data['table_data'])}個のテーブル):")
    print("-" * 40)

    for i, table in enumerate(raw_data['table_data']):
        print(f"\nテーブル {i+1}:")
        for j, row in enumerate(table['rows'][:10]):  # 最初の10行のみ
            cells = row['cells']
            print(f"  行{j+1}: {' | '.join(cells[:4])}")  # 最初の4列のみ表示

            # セル内容で栄養素を検索
            for cell in cells:
                cell_lower = cell.lower()
                for keyword in nutrition_keywords:
                    if keyword.lower() in cell_lower:
                        print(f"    🎯 栄養素発見: {cell} (キーワード: {keyword})")

    # パーセンテージ情報の検索
    print("\n📊 パーセンテージ情報:")
    print("-" * 40)

    percentage_texts = []
    for item in raw_data['all_texts']:
        if '%' in item['text'] or 'percent' in item['text'].lower():
            percentage_texts.append(item['text'])
            print(f"  📈 '{item['text']}'")

    # 単位情報の検索
    print("\n⚖️ 単位情報:")
    print("-" * 40)

    unit_keywords = ['g', 'mg', 'mcg', 'ug', 'kg', 'oz', 'lb', 'cup', 'ml', 'l', 'fl oz', 'tsp', 'tbsp', 'serving']

    unit_texts = []
    for item in raw_data['all_texts']:
        text = item['text']
        for unit in unit_keywords:
            if f" {unit}" in text or f"{unit} " in text or text.endswith(unit):
                unit_texts.append(text)
                print(f"  ⚖️ '{text}'")
                break

    print(f"\n📈 発見された情報の要約:")
    print(f"=" * 60)
    print(f"栄養素関連テキスト: {len(nutrition_related_texts)}個")
    print(f"数値付き栄養素情報: {len(nutritional_values)}個")
    print(f"パーセンテージ情報: {len(percentage_texts)}個")
    print(f"単位情報: {len(unit_texts)}個")

    # 推奨される次のステップ
    print(f"\n🎯 推奨される次のステップ:")
    print(f"1. テーブルデータを詳細に解析して栄養素の数値を抽出")
    print(f"2. パーセンテージ情報から栄養バランスを取得")
    print(f"3. 単位別の栄養素情報を構築")
    print(f"4. 抽出ロジックを改善してより多くの栄養素を取得")

if __name__ == "__main__":
    import sys
    import glob

    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # 最新のファイルを使用
        files = glob.glob("web_scraping/data/top3_nutrition_*.json")
        if files:
            json_file = max(files)  # 最新のファイル
        else:
            print("❌ データファイルが見つかりません")
            sys.exit(1)

    print(f"📂 解析対象ファイル: {json_file}")
    analyze_raw_nutrition_data(json_file)