#!/usr/bin/env python3
"""
FDCデータセットの単位・表記パターン網羅的調査スクリプト
"""

import sqlite3
import re
from collections import defaultdict, Counter
from pathlib import Path
import json


def analyze_fdc_units():
    """FDCデータベースの単位・表記パターンを分析"""

    # データベース接続
    db_path = Path(__file__).parent.parent.parent.parent / "db" / "FoodData_Central" / "fdc_barcode.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=== FDC データセット単位・表記パターン調査 ===\n")

    # 1. サービング単位の調査
    print("1. serving_size_unit の調査:")
    cursor.execute("SELECT serving_size_unit, COUNT(*) as count FROM branded_food WHERE serving_size_unit IS NOT NULL GROUP BY serving_size_unit ORDER BY count DESC")
    serving_units = cursor.fetchall()

    for unit, count in serving_units:
        print(f"  {unit}: {count:,} 件")

    # 2. household_serving_fulltext のパターン分析
    print("\n2. household_serving_fulltext のパターン分析:")
    cursor.execute("SELECT household_serving_fulltext FROM branded_food WHERE household_serving_fulltext IS NOT NULL")
    household_texts = [row[0] for row in cursor.fetchall()]

    # パターン分類
    patterns = {
        'volume': [],      # カップ、大さじ等
        'count': [],       # 個数ベース
        'weight': [],      # 重量ベース
        'mixed': [],       # 混合パターン
        'other': []        # その他
    }

    volume_keywords = ['cup', 'tbsp', 'tsp', 'fl oz', 'fl.oz', 'oz', 'ml', 'mL', 'liter']
    count_keywords = ['piece', 'pieces', 'item', 'bar', 'slice', 'link', 'links', 'cookie', 'cracker', 'chip', 'chips']
    weight_keywords = ['g', 'gram', 'kg', 'lb', 'oz']

    for text in household_texts[:1000]:  # サンプル1000件で分析
        text_lower = text.lower()

        has_volume = any(keyword in text_lower for keyword in volume_keywords)
        has_count = any(keyword in text_lower for keyword in count_keywords)
        has_weight = any(f'{keyword}' in text_lower for keyword in weight_keywords)

        category_count = sum([has_volume, has_count, has_weight])

        if category_count > 1:
            patterns['mixed'].append(text)
        elif has_volume:
            patterns['volume'].append(text)
        elif has_count:
            patterns['count'].append(text)
        elif has_weight:
            patterns['weight'].append(text)
        else:
            patterns['other'].append(text)

    for category, items in patterns.items():
        print(f"\n  {category.upper()} パターン ({len(items)} 件):")
        for item in items[:10]:  # 最初の10件を表示
            print(f"    {item}")
        if len(items) > 10:
            print(f"    ... 他 {len(items) - 10} 件")

    # 3. 体積単位の詳細分析
    print("\n3. 体積単位の詳細分析:")
    volume_units = extract_volume_units(household_texts)
    for unit, count in volume_units.most_common(20):
        print(f"  {unit}: {count} 回")

    # 4. 個数単位の詳細分析
    print("\n4. 個数単位の詳細分析:")
    count_units = extract_count_units(household_texts)
    for unit, count in count_units.most_common(20):
        print(f"  {unit}: {count} 回")

    # 5. 数値パターンの分析
    print("\n5. 数値パターンの分析:")
    number_patterns = extract_number_patterns(household_texts)
    for pattern, count in number_patterns.most_common(15):
        print(f"  {pattern}: {count} 回")

    conn.close()

    return {
        'serving_units': dict(serving_units),
        'patterns': patterns,
        'volume_units': dict(volume_units.most_common(50)),
        'count_units': dict(count_units.most_common(50)),
        'number_patterns': dict(number_patterns.most_common(30))
    }


def extract_volume_units(texts):
    """体積単位を抽出"""
    volume_pattern = r'\b(\d*\s*(?:cup|cups|tbsp|tsp|fl\s*oz|fl\.oz|oz|ml|mL|liter|liters|gallon|gallons|pint|pints|quart|quarts))\b'
    units = Counter()

    for text in texts:
        matches = re.findall(volume_pattern, text.lower())
        for match in matches:
            units[match.strip()] += 1

    return units


def extract_count_units(texts):
    """個数単位を抽出"""
    count_pattern = r'\b(\d+\s*(?:piece|pieces|item|items|bar|bars|slice|slices|link|links|cookie|cookies|cracker|crackers|chip|chips|pastry|pastries|pizza|pizzas))\b'
    units = Counter()

    for text in texts:
        matches = re.findall(count_pattern, text.lower())
        for match in matches:
            units[match.strip()] += 1

    return units


def extract_number_patterns(texts):
    """数値表記パターンを抽出"""
    number_pattern = r'\b(\d+(?:/\d+)?(?:\s+\d+/\d+)?)\b'
    patterns = Counter()

    for text in texts:
        matches = re.findall(number_pattern, text)
        for match in matches:
            patterns[match] += 1

    return patterns


def save_analysis_data(analysis_results):
    """分析結果をJSONファイルに保存"""
    output_path = Path(__file__).parent.parent / "data" / "fdc_unit_analysis.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)

    print(f"\n分析結果を保存しました: {output_path}")


if __name__ == "__main__":
    results = analyze_fdc_units()
    save_analysis_data(results)