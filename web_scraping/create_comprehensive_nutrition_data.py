#!/usr/bin/env python3
"""
生データを基に、各単位でのすべての栄養素情報を計算して整理するスクリプト
"""

import json
from datetime import datetime
from typing import Dict, List, Any

def create_comprehensive_nutrition_data(input_file: str) -> str:
    """生データから包括的な栄養情報を作成"""

    with open(input_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    food = original_data['foods'][0]

    print(f"📊 包括的栄養データを作成: {food['name']}")
    print("=" * 60)

    # 基準値（元データから）
    base_calories = food['calories']  # 239cal
    base_weight_g = food['weight_g']  # 254g
    base_nutrients = food.get('detailed_nutrients', {})

    # 単位定義（重量ベース）
    unit_weights = {
        'cup': 254.0,
        'gram': 1.0,
        'tablespoon': 15.9,
        'oz': 28.3,
        'ml': 1.1,
        'teaspoon': 5.3,
        'fl oz': 31.8,
        'lb': 453.6
    }

    # すべての栄養素を抽出（元データから）
    all_nutrients = {}

    # 基本栄養素
    all_nutrients['calories'] = {'value': base_calories, 'unit': 'cal', 'base_amount': base_weight_g}

    # 詳細栄養素から抽出
    nutrient_mappings = {
        'protein': 'Protein',
        'total_fat': 'Total Fat',
        'saturated_fat': 'Saturated Fat',
        'trans_fat': 'Trans Fat',
        'monounsaturated_fat': 'Monounsaturated Fat',
        'polyunsaturated_fat': 'Polyunsaturated Fat',
        'total_carbs': 'Total Carbs',
        'net_carbs': 'Net Carbs',
        'dietary_fiber': 'Dietary Fiber',
        'total_sugars': 'Total Sugars',
        'added_sugars': 'Added Sugars',
        'sodium': 'Sodium',
        'calcium': 'Calcium',
        'iron': 'Iron',
        'vitamin_c': 'Vitamin C',
        'potassium': 'Potassium'
    }

    # 生データの後処理でより詳細な栄養素を抽出
    after_nutrients = food['raw_data']['after_nutrients']['all_texts']

    for text_item in after_nutrients:
        text = text_item['text']

        # 各栄養素を検索
        for key, display_name in nutrient_mappings.items():
            if display_name.lower() in text.lower():
                # 数値と単位を抽出
                import re
                # パターン: "栄養素名 数値単位" (例: "Protein 12g", "Sodium 871mg")
                pattern = rf'{display_name}\s+(\d+(?:\.\d+)?)(mg|g|mcg|ug)'
                match = re.search(pattern, text, re.IGNORECASE)

                if match:
                    value = float(match.group(1))
                    unit = match.group(2)
                    all_nutrients[key] = {
                        'value': value,
                        'unit': unit,
                        'base_amount': base_weight_g,
                        'text': text
                    }
                    print(f"  🎯 {key}: {value}{unit} (from: {text})")

    print(f"\n発見された栄養素: {len(all_nutrients)}個")

    # 各単位での栄養素を計算
    comprehensive_nutrition = {}

    for unit_name, unit_weight in unit_weights.items():
        unit_data = {
            'weight_g': unit_weight,
            'nutrients': {}
        }

        # 各栄養素を単位に合わせて計算
        for nutrient_key, nutrient_info in all_nutrients.items():
            base_value = nutrient_info['value']
            base_amount = nutrient_info['base_amount']  # 254g

            # 比例計算: (栄養素値 / 基準重量) × 単位重量
            unit_value = (base_value / base_amount) * unit_weight

            unit_data['nutrients'][nutrient_key] = {
                'value': round(unit_value, 2),
                'unit': nutrient_info['unit'],
                'display': f"{round(unit_value, 1)}{nutrient_info['unit']}"
            }

        comprehensive_nutrition[unit_name] = unit_data
        print(f"  ✅ {unit_name}: {len(unit_data['nutrients'])}個の栄養素を計算")

    # 包括的なデータ構造を作成
    comprehensive_data = {
        'food_info': {
            'name': food['name'],
            'food_grade': food.get('food_grade', ''),
            'url': food['url'],
            'scraped_at': food['scraped_at']
        },
        'base_reference': {
            'amount': base_weight_g,
            'unit': 'g',
            'description': 'Base serving size (1 cup)'
        },
        'nutrition_by_unit': comprehensive_nutrition,
        'available_nutrients': list(all_nutrients.keys()),
        'original_raw_data': food['raw_data']  # 元データも保持
    }

    # ファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"web_scraping/data/comprehensive_nutrition_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 包括的栄養データを保存: {output_file}")

    # サンプル表示
    print(f"\n📋 サンプル表示 (1 gram あたり):")
    gram_data = comprehensive_nutrition['gram']['nutrients']
    for nutrient, info in list(gram_data.items())[:5]:
        print(f"  {nutrient}: {info['display']}")

    print(f"\n📋 サンプル表示 (1 cup あたり):")
    cup_data = comprehensive_nutrition['cup']['nutrients']
    for nutrient, info in list(cup_data.items())[:5]:
        print(f"  {nutrient}: {info['display']}")

    return output_file

if __name__ == "__main__":
    import sys
    import glob

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # 最新のtop3_nutritionファイルを使用
        files = glob.glob("web_scraping/data/top3_nutrition_*.json")
        if files:
            input_file = max(files)
        else:
            print("❌ 入力ファイルが見つかりません")
            sys.exit(1)

    print(f"📂 入力ファイル: {input_file}")
    output_file = create_comprehensive_nutrition_data(input_file)

    print(f"\n🎉 完了: {output_file}")
    print("このファイルでは任意の単位で全栄養素を表示できます")