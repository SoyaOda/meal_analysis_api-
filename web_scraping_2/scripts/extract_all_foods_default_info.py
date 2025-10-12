#!/usr/bin/env python3
"""
manual_input_templatesから全食材のデフォルトunitとカロリーを抽出してJSONファイルを作成
"""

import json
import re
from pathlib import Path
from collections import OrderedDict

def extract_default_info(file_path):
    """ファイルから全食材のデフォルト情報を抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 食材ごとに分割（番号付きタイトル行で分割）
    # 小数点カロリー対応: 8.75cals, 1,849cals など
    food_pattern = r'(\d+)\.\s*(.+?),\s*(.+?)\n([\d,.]+)cals'
    foods = []

    for match in re.finditer(food_pattern, content):
        sequence = int(match.group(1))
        first_part = match.group(2).strip()
        rest_part = match.group(3).strip()
        calories_str = match.group(4).strip()

        # タイトル全体とカロリー文字列を保存
        title_full_name = f"{first_part}, {rest_part}"
        title_calories = f"{calories_str}cals"

        # food_nameはfirst_partのみ（カンマの前）
        food_name = first_part

        # 食材の全セクションを取得（次の番号付きタイトルまで）
        start_pos = match.end()
        next_match = re.search(r'\n\d+\.\s+', content[start_pos:])
        if next_match:
            end_pos = start_pos + next_match.start()
            food_content = content[match.start():end_pos]
        else:
            food_content = content[match.start():]

        # 【栄養情報】セクションからdefault_unitとdefault_caloriesを抽出
        nutrition_match = re.search(r'【栄養情報】\n(.*?)(?=\n【|$)', food_content, re.DOTALL)

        default_unit = None
        calories_float = None
        unit_coefficient = 1.0

        if nutrition_match:
            nutrition_content = nutrition_match.group(1).strip()

            # 【栄養情報】が"None"の場合をチェック
            if nutrition_content != "None":
                # Serving Size行からdefault_unitを抽出
                # 例: "Serving Size	bagel, mini (2-1/2" dia) (26g)"
                serving_size_match = re.search(r'Serving Size\s+(.+?)\s+\(([\d,.]+)g\)', nutrition_content)
                if serving_size_match:
                    default_unit = serving_size_match.group(1).strip()

                # Calories行からdefault_caloriesを抽出
                # 例: "Calories	72cals"
                calories_match = re.search(r'Calories\s+([\d,.]+)cals', nutrition_content)
                if calories_match:
                    calories_float = float(calories_match.group(1).replace(',', ''))

        # default_unitの数字係数を処理
        if default_unit:
            number_pattern = re.compile(r'^([\d.]+)\s+(.+)$')
            unit_match = number_pattern.match(default_unit)
            if unit_match:
                unit_coefficient = float(unit_match.group(1))
                default_unit = unit_match.group(2)  # 基本単位のみに正規化
                # カロリーを係数で割る
                if calories_float:
                    calories_float = calories_float / unit_coefficient

        # 【栄養情報】セクションの有無を確認
        has_nutrition = '【栄養情報】' in food_content

        # ステータスを判定
        status = "valid" if has_nutrition else "excluded_no_nutrition"

        # 除外食材の場合はNoneに設定
        if not has_nutrition:
            default_unit = None
            calories_float = None

        foods.append({
            'sequence': sequence,
            'food_name': food_name,
            'default_unit': default_unit,
            'default_calories': calories_float,
            'unit_coefficient': unit_coefficient,  # 係数を保存
            'title_full_name': title_full_name,
            'title_calories': title_calories,
            'status': status,
            'has_nutrition': has_nutrition
        })

    return foods

def main():
    # manual_input_templatesディレクトリのパス
    templates_dir = Path(__file__).parent.parent / "manual_input_templates"

    all_foods = []

    # カテゴリ名のマッピング（ファイル名から表示名へ）
    category_mapping = {
        'beans_and_peas': 'Beans & Peas',
        'breads': 'Breads',
        'breakfast_cereals': 'Breakfast Cereals',
        'cheese': 'Cheese',
        'condiments_dressings_and_sauces': 'Condiments, Dressings & Sauces',
        'eggs': 'Eggs',
        'fats_and_oils': 'Fats & Oils',
        'fish_and_shellfish': 'Fish & Shellfish',
        'fruits': 'Fruits',
        'grains_and_grain_products': 'Grains & Grain Products',
        'meats': 'Meats',
        'milk_and_dairy': 'Milk & Dairy',
        'nuts_and_seeds': 'Nuts & Seeds',
        'pasta_and_noodles': 'Pasta & Noodles',
        'snacks': 'Snacks',
        'soups': 'Soups',
        'spices_and_herbs': 'Spices & Herbs',
        'sweets': 'Sweets',
        'vegetables': 'Vegetables'
    }

    # 全ファイルを処理
    for file_path in sorted(templates_dir.glob('*_manual_input.txt')):
        # カテゴリ名を取得
        file_stem = file_path.stem.replace('_manual_input', '')
        category = category_mapping.get(file_stem, file_stem.replace('_', ' ').title())

        print(f"処理中: {file_path.name} (カテゴリ: {category})")

        # 食材情報を抽出
        foods = extract_default_info(file_path)

        # カテゴリとファイル名を追加
        for food in foods:
            food['category'] = category
            food['file'] = file_path.name

        all_foods.extend(foods)
        print(f"  → {len(foods)}件の食材を抽出")

    # ステータス別に集計
    valid_foods = [f for f in all_foods if f['status'] == 'valid']
    excluded_foods = [f for f in all_foods if f['status'] == 'excluded_no_nutrition']

    # メタデータを作成
    metadata = OrderedDict([
        ('total_foods', len(all_foods)),
        ('valid_foods', len(valid_foods)),
        ('excluded_foods', len(excluded_foods)),
        ('no_nutrition_foods', len(excluded_foods)),
        ('description', 'All foods with default unit and calories (calories as float)'),
        ('excluded_food_names', [f['food_name'] for f in excluded_foods])
    ])

    # 最終的なJSON構造を作成
    output_data = OrderedDict([
        ('metadata', metadata),
        ('foods', [OrderedDict([
            ('sequence', f['sequence']),
            ('category', f['category']),
            ('file', f['file']),
            ('food_name', f['food_name']),
            ('default_unit', f['default_unit']),
            ('default_calories', f['default_calories']),
            ('unit_coefficient', f['unit_coefficient']),
            ('title_full_name', f['title_full_name']),
            ('title_calories', f['title_calories']),
            ('status', f['status'])
        ]) for f in all_foods])
    ])

    # JSONファイルに保存
    output_file = Path(__file__).parent.parent / "output" / "all_foods_default_unit_calories.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 80}")
    print(f"抽出完了！")
    print(f"{'=' * 80}")
    print(f"総食材数: {len(all_foods)}")
    print(f"有効食材数: {len(valid_foods)}")
    print(f"除外食材数: {len(excluded_foods)}")
    print(f"\n除外食材: {', '.join([f['food_name'] for f in excluded_foods])}")
    print(f"\nJSONファイルを保存: {output_file}")

if __name__ == "__main__":
    main()
