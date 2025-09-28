#!/usr/bin/env python3
"""
生データの全テキスト要素を確認するスクリプト
"""

import json

def examine_all_texts(json_file: str):
    """全テキスト要素を表示"""

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    food = data['foods'][0]
    raw_data = food['raw_data']

    print(f"📊 全テキスト要素 ({len(raw_data['all_texts'])}個):")
    print("=" * 60)

    for i, item in enumerate(raw_data['all_texts'], 1):
        print(f"{i:2d}: '{item['text']}' (tag: {item['tag']}, class: {item['class'][:50]})")

    print(f"\n📊 数値テキスト要素 ({len(raw_data['numerical_texts'])}個):")
    print("=" * 60)

    for i, item in enumerate(raw_data['numerical_texts'], 1):
        print(f"{i:2d}: '{item['text']}' (tag: {item['tag']}, class: {item['class'][:50]})")

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

    examine_all_texts(json_file)