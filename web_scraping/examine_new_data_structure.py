#!/usr/bin/env python3
"""
新しいデータ構造を確認するスクリプト
"""

import json

def examine_new_data_structure(json_file: str):
    """新しいデータ構造を確認"""

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    food = data['foods'][0]
    raw_data = food['raw_data']

    print(f"📊 データ構造確認: {food['name']}")
    print("=" * 60)

    # before_nutrients の情報を確認
    if 'before_nutrients' in raw_data:
        before_data = raw_data['before_nutrients']
        print(f"SHOW NUTRIENTS前のテキスト要素: {len(before_data.get('all_texts', []))}個")

        print("\n🔍 SHOW NUTRIENTS ボタンを検索:")
        nutrients_button_found = False
        for i, item in enumerate(before_data.get('all_texts', []), 1):
            if 'NUTRIENT' in item['text'].upper():
                print(f"  {i:2d}: '{item['text']}' (tag: {item['tag']}, class: {item['class'][:50]})")
                nutrients_button_found = True

        if not nutrients_button_found:
            print("  ❌ SHOW NUTRIENTSボタンが見つかりません")

    # after_nutrients の情報を確認
    if 'after_nutrients' in raw_data:
        after_data = raw_data['after_nutrients']
        print(f"\nSHOW NUTRIENTS後のテキスト要素: {len(after_data.get('all_texts', []))}個")

        if len(after_data.get('all_texts', [])) == 0:
            print("  ⚠️ 栄養素展開後のデータが取得されていません")

    # detailed_nutrients の情報を確認
    detailed_nutrients = food.get('detailed_nutrients', {})
    print(f"\n📊 詳細栄養素情報: {len(detailed_nutrients)}個")
    if detailed_nutrients:
        for nutrient, info in detailed_nutrients.items():
            print(f"  {nutrient}: {info['value']} ({info['text']})")
    else:
        print("  ❌ 詳細栄養素情報が取得されていません")

    # 全ての利用可能なテキストから栄養素を検索
    print(f"\n🔍 全テキストから栄養素関連情報を検索:")
    nutrition_keywords = ['protein', 'fat', 'carb', 'fiber', 'sugar', 'sodium', 'calcium', 'iron', 'vitamin', 'potassium']

    found_nutrition_info = []
    for item in before_data.get('all_texts', []):
        text_lower = item['text'].lower()
        for keyword in nutrition_keywords:
            if keyword in text_lower:
                found_nutrition_info.append(item['text'])
                print(f"  🎯 '{item['text']}'")
                break

    if not found_nutrition_info:
        print("  ❌ 栄養素関連の情報が見つかりません")
        print("\n💡 MyNetDiaryの詳細ページにアクセスしていない可能性があります")
        print("   食材リストページではなく、食材詳細ページに移動する必要があります")

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

    examine_new_data_structure(json_file)