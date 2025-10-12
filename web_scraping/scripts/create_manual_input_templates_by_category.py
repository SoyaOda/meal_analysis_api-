#!/usr/bin/env python3
"""
web_scraping/food_catalog_dataの全食材に対して、
カテゴリごとにマニュアル入力用のテンプレートファイルを作成

出力:
- カテゴリごとのtxtファイル
- 栄養情報とserving情報のコピペ用フォーマット

Usage:
    python create_manual_input_templates_by_category.py
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def load_food_catalog_data(catalog_dir: Path) -> list:
    """food_catalog_dataから全食材を読み込み"""
    all_foods = []

    for json_file in sorted(catalog_dir.glob('*.json')):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # category_dataから食材を取得
        category_data = data.get('category_data', {})
        category = category_data.get('name', 'Unknown')
        foods = category_data.get('foods', [])

        # カテゴリ情報を追加
        for food in foods:
            food['catalog_category'] = category
            all_foods.append(food)

    return all_foods


def group_by_category(foods: list) -> dict:
    """食材をカテゴリごとにグループ化"""
    categories = defaultdict(list)

    for food in foods:
        category = food.get('catalog_category', 'Unknown')
        categories[category].append(food)

    return categories


def sanitize_filename(name: str) -> str:
    """ファイル名として使用できるように文字列をサニタイズ"""
    # 特殊文字を置換
    replacements = {
        '/': '_',
        '\\': '_',
        ':': '_',
        '*': '_',
        '?': '_',
        '"': '_',
        '<': '_',
        '>': '_',
        '|': '_',
        '&': 'and',
        ' ': '_',
        ',': ''
    }

    sanitized = name
    for old, new in replacements.items():
        sanitized = sanitized.replace(old, new)

    # 連続するアンダースコアを1つに
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')

    return sanitized.lower()


def create_category_template(category: str, foods: list, output_file: Path):
    """カテゴリごとのテンプレートファイルを作成"""

    with open(output_file, 'w', encoding='utf-8') as f:
        # ヘッダー
        f.write("=" * 80 + "\n")
        f.write(f"カテゴリ: {category}\n")
        f.write(f"食材数: {len(foods)}\n")
        f.write(f"作成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        f.write("【使用方法】\n")
        f.write("1. MyNetDiaryで各食材を検索\n")
        f.write("2. Serving Size情報をコピーして【Serving情報】セクションに貼り付け\n")
        f.write("3. Nutrition Facts情報をコピーして【栄養情報】セクションに貼り付け\n")
        f.write("\n" + "=" * 80 + "\n\n")

        # 各食材のテンプレート
        for i, food in enumerate(foods, 1):
            food_name = food.get('food_name', 'N/A')

            f.write(f"{i}. {food_name}\n")
            f.write("-" * 80 + "\n")
            f.write("\n")

            f.write("【Serving情報】\n")
            f.write("\n")
            f.write("\n")
            f.write("\n")

            f.write("【栄養情報】\n")
            f.write("\n")
            f.write("\n")
            f.write("\n")

            f.write("=" * 80 + "\n")
            f.write("\n")


def print_summary(categories: dict, output_dir: Path):
    """処理サマリーを出力"""
    print("=" * 80)
    print("カテゴリ別マニュアル入力テンプレート作成レポート")
    print("=" * 80)

    print(f"\n【統計】")
    print(f"総カテゴリ数: {len(categories)}")
    total_foods = sum(len(foods) for foods in categories.values())
    print(f"総食材数: {total_foods:,}")

    print(f"\n【カテゴリ別食材数】")
    for category, foods in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        sanitized = sanitize_filename(category)
        filename = f"{sanitized}_manual_input.txt"
        print(f"{category}: {len(foods):,}食材 → {filename}")

    print(f"\n【出力先】")
    print(f"{output_dir}/")


def main():
    # ファイルパス
    base_dir = Path('/Users/odasoya/meal_analysis_api_2')
    catalog_dir = base_dir / 'web_scraping' / 'food_catalog_data'
    output_dir = base_dir / 'web_scraping' / 'manual_input_templates'

    # 出力ディレクトリを作成
    output_dir.mkdir(exist_ok=True)

    print("【1. food_catalog_data読み込み中】")
    all_foods = load_food_catalog_data(catalog_dir)
    print(f"✓ 総食材数: {len(all_foods):,}")

    print("\n【2. カテゴリごとにグループ化中】")
    categories = group_by_category(all_foods)
    print(f"✓ カテゴリ数: {len(categories)}")

    print("\n【3. テンプレートファイル作成中】")
    for category, foods in categories.items():
        # カテゴリ名をファイル名に変換
        sanitized_category = sanitize_filename(category)
        output_file = output_dir / f"{sanitized_category}_manual_input.txt"

        create_category_template(category, foods, output_file)
        print(f"✓ {category}: {len(foods)}食材 → {output_file.name}")

    print("\n")
    print_summary(categories, output_dir)

    print(f"\n完了！")
    print(f"\n出力先: {output_dir}")


if __name__ == '__main__':
    main()
