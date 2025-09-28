#!/usr/bin/env python3
"""
F、C、P要素を探すスクリプト
"""

import json

def find_fcp_elements(json_file: str):
    """F、C、P要素を探す"""

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    food = data['foods'][0]
    raw_data = food['raw_data']

    print(f"📊 F、C、P要素を検索: {food['name']}")
    print("=" * 60)

    before_data = raw_data['before_nutrients']

    print("🔍 F、C、P、§ の単体文字を検索:")
    fcp_elements = []

    for i, item in enumerate(before_data.get('all_texts', []), 1):
        text = item['text'].strip()
        # 単体の文字F、C、P、または§を探す
        if text in ['F', 'C', 'P', '§']:
            fcp_elements.append(item)
            print(f"  {i:2d}: '{text}' (tag: {item['tag']}, class: '{item['class']}')")

    print(f"\n発見されたF/C/P/§要素: {len(fcp_elements)}個")

    # 前後の要素も確認
    print(f"\n🔍 F、C、P要素の前後関係:")
    for i, item in enumerate(before_data.get('all_texts', [])):
        text = item['text'].strip()
        if text in ['F', 'C', 'P']:
            print(f"\n📍 '{text}' の前後:")
            # 前の要素
            if i > 0:
                prev_item = before_data['all_texts'][i-1]
                print(f"  前: '{prev_item['text']}' (tag: {prev_item['tag']})")

            # 現在の要素
            print(f"  現在: '{text}' (tag: {item['tag']}, class: '{item['class']}')")

            # 後の要素
            if i < len(before_data['all_texts']) - 1:
                next_item = before_data['all_texts'][i+1]
                print(f"  後: '{next_item['text']}' (tag: {next_item['tag']})")

    # div要素を詳しく調べる
    print(f"\n🔍 div要素の詳細分析:")
    div_elements = []
    for item in before_data.get('all_texts', []):
        if item['tag'] == 'div' and item['text'].strip() in ['F', 'C', 'P']:
            div_elements.append(item)
            print(f"  div: '{item['text']}' (class: '{item['class']}')")

    print(f"\ndiv要素のF/C/P: {len(div_elements)}個")

    # クリック可能そうな要素を推測
    print(f"\n💡 クリック可能性の分析:")
    for item in fcp_elements:
        clickable_indicators = []
        class_attr = item['class'].lower()

        if 'button' in class_attr:
            clickable_indicators.append('button class')
        if 'click' in class_attr:
            clickable_indicators.append('click class')
        if 'mui' in class_attr:
            clickable_indicators.append('Material-UI component')
        if item['tag'] == 'button':
            clickable_indicators.append('button tag')
        if item['tag'] == 'div':
            clickable_indicators.append('div (potentially clickable)')

        print(f"  '{item['text']}': {', '.join(clickable_indicators) if clickable_indicators else 'No obvious click indicators'}")

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

    find_fcp_elements(json_file)