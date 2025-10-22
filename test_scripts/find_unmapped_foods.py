#!/usr/bin/env python
"""
mappings.jsonのall_usda_mappingsに含まれていない食品名を特定
"""

import json
from pathlib import Path
from collections import defaultdict

# ファイルパス
mappings_file = Path(__file__).parent / "mappings" / "mappings.json"
survey_names_file = Path(__file__).parent.parent / "usda_database" / "names_list" / "survey_food_names.txt"
foundation_names_file = Path(__file__).parent.parent / "usda_database" / "names_list" / "foundation_food_names.txt"
output_file = Path(__file__).parent / "mappings" / "unmapped_foods_analysis.md"

def load_all_mapped_names():
    """mappings.jsonから全てのマップ済み名前を収集"""
    with open(mappings_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mapped_names = set()

    for key, mapping in data['mappings'].items():
        # default_usda
        if 'default_usda' in mapping and mapping['default_usda']:
            if 'name' in mapping['default_usda']:
                mapped_names.add(mapping['default_usda']['name'])

        # survey_alternative
        if 'survey_alternative' in mapping:
            if 'name' in mapping['survey_alternative']:
                mapped_names.add(mapping['survey_alternative']['name'])

        # all_usda_mappings
        if 'all_usda_mappings' in mapping:
            for item in mapping['all_usda_mappings']:
                # itemが辞書の場合とstringの場合に対応
                if isinstance(item, dict):
                    if 'name' in item:
                        mapped_names.add(item['name'])
                else:
                    mapped_names.add(item)

    return mapped_names

def load_database_names(file_path):
    """データベースの食品名を読み込み"""
    names = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # 番号を除去（例: "1. Food name" -> "Food name"）
                if '. ' in line and line.split('. ', 1)[0].isdigit():
                    name = line.split('. ', 1)[1]
                else:
                    name = line
                names.append(name)
    return names

def categorize_unmapped_foods(unmapped_foods):
    """未マップ食品をカテゴリ別に分類"""
    categories = defaultdict(list)

    # カテゴリ判定のキーワード
    category_keywords = {
        'Baby food': ['baby', 'infant', 'toddler'],
        'Restaurant/Brand': ['mcdonald', 'burger king', 'subway', 'pizza hut', 'kfc', 'wendy',
                            'taco bell', 'domino', 'starbucks', 'dunkin', 'chipotle', 'panera'],
        'School/Institutional': ['school', 'cafeteria', 'usda commodity', 'wic'],
        'Ethnic dishes': ['chinese', 'mexican', 'italian', 'indian', 'thai', 'korean', 'japanese',
                         'vietnamese', 'greek', 'spanish', 'puerto rican'],
        'Mixed dishes': ['casserole', 'stew', 'soup', 'salad', 'sandwich', 'wrap', 'bowl'],
        'Breakfast': ['breakfast', 'cereal', 'pancake', 'waffle', 'french toast', 'omelet'],
        'Desserts': ['cake', 'cookie', 'pie', 'ice cream', 'pudding', 'candy', 'chocolate'],
        'Beverages': ['drink', 'juice', 'soda', 'coffee', 'tea', 'milk', 'shake', 'smoothie'],
        'Snacks': ['chips', 'crackers', 'popcorn', 'pretzel', 'nuts'],
        'Condiments': ['sauce', 'dressing', 'mayo', 'ketchup', 'mustard', 'salsa'],
        'Specific preparations': ['fried', 'baked', 'grilled', 'roasted', 'steamed', 'boiled'],
        'With additions': ['with cheese', 'with sauce', 'with gravy', 'with butter', 'with cream'],
        'NFS/NS': ['nfs', 'ns as to', 'not specified', 'not further specified']
    }

    for food in unmapped_foods:
        food_lower = food.lower()
        categorized = False

        for category, keywords in category_keywords.items():
            if any(keyword in food_lower for keyword in keywords):
                categories[category].append(food)
                categorized = True
                break

        if not categorized:
            categories['Other'].append(food)

    return categories

def search_potential_matches(unmapped_food, mapped_names):
    """潜在的なマッチを探す"""
    food_lower = unmapped_food.lower()
    matches = []

    # 主要な単語を抽出（最初の3単語程度）
    main_words = food_lower.split()[:3]

    for mapped in mapped_names:
        mapped_lower = mapped.lower()
        # 主要単語が含まれているか確認
        if any(word in mapped_lower for word in main_words if len(word) > 3):
            matches.append(mapped)

    return matches[:3]  # 最大3件まで

def analyze_unmapped():
    """未マップ食品の分析"""

    print("📚 データ読み込み中...")

    # マップ済み名前を収集
    mapped_names = load_all_mapped_names()
    print(f"   マップ済み食品名: {len(mapped_names)}個")

    # データベースの全名前を読み込み
    survey_names = load_database_names(survey_names_file)
    foundation_names = load_database_names(foundation_names_file)
    print(f"   Survey FNDDS: {len(survey_names)}個")
    print(f"   Foundation Food: {len(foundation_names)}個")

    # 未マップを特定
    unmapped_survey = [name for name in survey_names if name not in mapped_names]
    unmapped_foundation = [name for name in foundation_names if name not in mapped_names]

    print(f"\n🔍 未マップ食品:")
    print(f"   Survey FNDDS: {len(unmapped_survey)}個 ({len(unmapped_survey)/len(survey_names)*100:.1f}%)")
    print(f"   Foundation Food: {len(unmapped_foundation)}個 ({len(unmapped_foundation)/len(foundation_names)*100:.1f}%)")

    # カテゴリ別に分類
    survey_categories = categorize_unmapped_foods(unmapped_survey)
    foundation_categories = categorize_unmapped_foods(unmapped_foundation)

    # レポート作成
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 未マップ食品分析レポート\n\n")
        f.write(f"生成日時: {Path(__file__).parent}\n\n")

        f.write("## 📊 サマリー\n\n")
        f.write("| データベース | 総数 | マップ済み | 未マップ | 未マップ率 |\n")
        f.write("|------------|------|-----------|---------|----------|\n")
        f.write(f"| Survey FNDDS | {len(survey_names)} | {len(survey_names)-len(unmapped_survey)} | {len(unmapped_survey)} | {len(unmapped_survey)/len(survey_names)*100:.1f}% |\n")
        f.write(f"| Foundation Food | {len(foundation_names)} | {len(foundation_names)-len(unmapped_foundation)} | {len(unmapped_foundation)} | {len(unmapped_foundation)/len(foundation_names)*100:.1f}% |\n")

        # Survey FNDDS未マップ
        f.write("\n## 🔍 Survey FNDDS 未マップ食品\n\n")
        f.write(f"総数: {len(unmapped_survey)}個\n\n")

        for category, foods in sorted(survey_categories.items()):
            if foods:
                f.write(f"### {category} ({len(foods)}個)\n\n")
                # 最初の10個を表示
                for food in foods[:10]:
                    f.write(f"- {food}\n")
                    # 潜在的マッチを探す
                    matches = search_potential_matches(food, mapped_names)
                    if matches:
                        f.write(f"  → 類似: {', '.join(matches[:2])}\n")
                if len(foods) > 10:
                    f.write(f"  ... 他 {len(foods)-10}個\n")
                f.write("\n")

        # Foundation Food未マップ
        f.write("\n## 🔍 Foundation Food 未マップ食品\n\n")
        f.write(f"総数: {len(unmapped_foundation)}個\n\n")

        for category, foods in sorted(foundation_categories.items()):
            if foods:
                f.write(f"### {category} ({len(foods)}個)\n\n")
                for food in foods[:10]:
                    f.write(f"- {food}\n")
                    matches = search_potential_matches(food, mapped_names)
                    if matches:
                        f.write(f"  → 類似: {', '.join(matches[:2])}\n")
                if len(foods) > 10:
                    f.write(f"  ... 他 {len(foods)-10}個\n")
                f.write("\n")

        # 重要な未マップ食品（一般的な食品）
        f.write("\n## ⚠️ 要確認項目\n\n")
        f.write("以下は一般的な食品名を含むが未マップの項目です：\n\n")

        important_keywords = ['meat loaf', 'caesar', 'french fries', 'hamburger', 'hot dog',
                            'pizza', 'sandwich', 'chicken', 'beef', 'pork', 'fish', 'egg',
                            'bread', 'rice', 'pasta', 'potato', 'tomato', 'lettuce']

        important_unmapped = []
        for food in unmapped_survey + unmapped_foundation:
            food_lower = food.lower()
            for keyword in important_keywords:
                if keyword in food_lower and food not in important_unmapped:
                    important_unmapped.append(food)
                    break

        for food in sorted(important_unmapped)[:30]:
            f.write(f"- {food}\n")

        if len(important_unmapped) > 30:
            f.write(f"\n... 他 {len(important_unmapped)-30}個\n")

    print(f"\n📁 レポート保存: {output_file}")

    return unmapped_survey, unmapped_foundation

if __name__ == "__main__":
    print("="*80)
    print("未マップ食品分析")
    print("="*80)
    print()

    unmapped_survey, unmapped_foundation = analyze_unmapped()

    print("\n" + "="*80)
    print("✅ 分析完了")
    print("="*80)