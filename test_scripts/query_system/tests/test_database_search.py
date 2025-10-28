#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
データベース全体から最も近い正解候補を検索
"""

import sys
from pathlib import Path
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# メタデータを直接読み込み
metadata_path = project_root / "data" / "usda_metadata.json"

with open(metadata_path, 'r', encoding='utf-8') as f:
    all_items = json.load(f)

print(f"📊 データベース全体: {len(all_items)}件")

# 失敗した4ケースについて、キーワード検索
search_cases = [
    {
        "id": 1,
        "query": "beef steak | grilled, sliced",
        "keywords": ["beef", "steak", "grilled"],
        "alt_keywords": ["beef", "steak", "broiled"],
        "description": "grilled beef steak"
    },
    {
        "id": 2,
        "query": "macaroni and cheese | cooked",
        "keywords": ["macaroni", "cheese", "cooked"],
        "alt_keywords": ["macaroni", "cheese"],
        "description": "macaroni and cheese"
    },
    {
        "id": 3,
        "query": "beef sirloin | cooked, roasted",
        "keywords": ["beef", "sirloin", "roasted"],
        "alt_keywords": ["beef", "sirloin", "roast"],
        "description": "roasted beef sirloin"
    },
    {
        "id": 4,
        "query": "asparagus | roasted",
        "keywords": ["asparagus", "roasted"],
        "alt_keywords": ["asparagus", "roast"],
        "description": "roasted asparagus"
    }
]

for case in search_cases:
    print("\n" + "=" * 80)
    print(f"[Case {case['id']}] {case['query']}")
    print(f"探している内容: {case['description']}")
    print("=" * 80)

    # 完全一致検索
    print(f"\n🔍 完全一致検索: {' + '.join(case['keywords'])}")
    exact_matches = []
    for item in all_items:
        desc = item['description'].lower()
        if all(kw in desc for kw in case['keywords']):
            exact_matches.append(item)

    print(f"   見つかった候補: {len(exact_matches)}件")
    for i, item in enumerate(exact_matches[:10], 1):
        print(f"   {i}. {item['description']}")
        print(f"      Source: {item['source']}, FDC ID: {item['fdc_id']}")

    # 代替キーワード検索
    if len(exact_matches) == 0:
        print(f"\n🔍 代替キーワード検索: {' + '.join(case['alt_keywords'])}")
        alt_matches = []
        for item in all_items:
            desc = item['description'].lower()
            if all(kw in desc for kw in case['alt_keywords']):
                alt_matches.append(item)

        print(f"   見つかった候補: {len(alt_matches)}件")
        for i, item in enumerate(alt_matches[:10], 1):
            print(f"   {i}. {item['description']}")
            print(f"      Source: {item['source']}, FDC ID: {item['fdc_id']}")

    # キーワード別の候補数を表示
    print(f"\n📋 キーワード別候補数:")
    for kw in case['keywords']:
        count = sum(1 for item in all_items if kw in item['description'].lower())
        print(f"   '{kw}': {count}件")

print("\n\n" + "=" * 80)
print("検索完了")
print("=" * 80)
