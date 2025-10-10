#!/usr/bin/env python3
"""
Stemmed Only Foodsの栄養情報とServing情報を収集・構造化するスクリプト

既存の栄養情報（100gあたり）を基に、一般的なserving sizeの情報を生成します。
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 食材タイプ別の標準serving sizes（グラム換算）
STANDARD_SERVINGS = {
    # 肉類
    "meat": {
        "oz": 28.35,
        "3 oz": 85,
        "4 oz": 113,
        "6 oz": 170,
        "lb": 453.6,
        "gram": 1
    },
    # 油脂類
    "oil_fat": {
        "tablespoon": 13.6,  # 油の場合
        "tbsp": 13.6,
        "teaspoon": 4.5,
        "tsp": 4.5,
        "cup": 218,
        "ml": 0.92,  # 油の密度
        "fl oz": 29.6,
        "gram": 1
    },
    # ナッツバター類
    "nut_butter": {
        "tablespoon": 16,
        "tbsp": 16,
        "teaspoon": 5.3,
        "tsp": 5.3,
        "cup": 256,
        "oz": 28.35,
        "gram": 1
    },
    # 豆類
    "beans": {
        "cup": 177,
        "half cup": 88.5,
        "oz": 28.35,
        "gram": 1
    },
    # バター・マーガリン
    "butter": {
        "tablespoon": 14.2,
        "tbsp": 14.2,
        "teaspoon": 4.7,
        "tsp": 4.7,
        "pat": 5,
        "stick": 113,
        "cup": 227,
        "oz": 28.35,
        "gram": 1
    },
    # ドレッシング・ソース
    "sauce_dressing": {
        "tablespoon": 15,
        "tbsp": 15,
        "teaspoon": 5,
        "tsp": 5,
        "cup": 240,
        "oz": 28.35,
        "fl oz": 30,
        "ml": 1,
        "gram": 1
    },
    # 豆腐
    "tofu": {
        "block": 396,
        "half block": 198,
        "3 oz": 85,
        "cup": 252,
        "oz": 28.35,
        "gram": 1
    },
    # ペスト
    "pesto": {
        "tablespoon": 15,
        "tbsp": 15,
        "teaspoon": 5,
        "tsp": 5,
        "cup": 240,
        "oz": 28.35,
        "gram": 1
    },
    # パイクラスト
    "pie_crust": {
        "slice": 28,
        "oz": 28.35,
        "crust": 120,
        "gram": 1
    },
    # 塩
    "salt": {
        "teaspoon": 6,
        "tsp": 6,
        "tablespoon": 18,
        "tbsp": 18,
        "pinch": 0.36,
        "gram": 1
    },
    # 蜂蜜
    "honey": {
        "tablespoon": 21,
        "tbsp": 21,
        "teaspoon": 7,
        "tsp": 7,
        "cup": 339,
        "oz": 28.35,
        "gram": 1
    }
}

# 食材タイプ分類
FOOD_TYPE_MAPPING = {
    "Beef brisket": "meat",
    "Beef top sirloin": "meat",
    "Lard": "oil_fat",
    "Almond butter": "nut_butter",
    "Kidney beans": "beans",
    "Peanut butter": "nut_butter",
    "Butter": "butter",
    "Chicken fat": "oil_fat",
    "Cod liver": "oil_fat",
    "Margarine": "butter",
    "Salad dressing": "sauce_dressing",
    "Tofu": "tofu",
    "Pesto": "pesto",
    "Pie crust": "pie_crust",
    "Sea salt": "salt",
    "Flaxseed oil": "oil_fat",
    "Sunflower oil": "oil_fat",
    "Walnut oil": "oil_fat",
    "Honey": "honey"
}


def determine_food_type(food_name: str) -> str:
    """食材名から食材タイプを判定"""
    for key, food_type in FOOD_TYPE_MAPPING.items():
        if key.lower() in food_name.lower():
            return food_type
    return "oil_fat"  # デフォルト


def calculate_serving_nutrition(base_nutrition: Dict, serving_grams: float) -> Dict:
    """100gあたりの栄養情報から、指定グラム数の栄養情報を計算"""
    multiplier = serving_grams / 100.0
    return {
        "calories": round(base_nutrition["calories"] * multiplier, 2),
        "protein": round(base_nutrition["protein"] * multiplier, 2),
        "fat": round(base_nutrition["fat"] * multiplier, 2),
        "carbs": round(base_nutrition["carbs"] * multiplier, 2),
        "serving_size_grams": serving_grams
    }


def generate_serving_options(food_name: str, base_nutrition: Dict) -> List[Dict]:
    """食材に対応するserving optionsを生成"""
    food_type = determine_food_type(food_name)
    servings = STANDARD_SERVINGS.get(food_type, STANDARD_SERVINGS["oil_fat"])

    serving_options = []

    for unit_name, grams in servings.items():
        nutrition = calculate_serving_nutrition(base_nutrition, grams)
        serving_options.append({
            "unit": unit_name,
            "grams": grams,
            "calories": nutrition["calories"],
            "protein": nutrition["protein"],
            "fat": nutrition["fat"],
            "carbs": nutrition["carbs"]
        })

    # グラム数で並び替え
    serving_options.sort(key=lambda x: x["grams"])

    return serving_options


def process_stemmed_only_foods():
    """メイン処理"""
    print("=" * 80)
    print("🔍 Stemmed Only Foods の栄養情報・Serving情報収集")
    print("=" * 80)

    # 入力ファイル
    input_file = Path("/Users/odasoya/meal_analysis_api_2/web_scraping_2/output/stemmed_only_foods.json")

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    foods = data['foods']
    print(f"\n📊 処理対象: {len(foods)}件\n")

    # 各食材を処理
    enriched_foods = []

    for i, food in enumerate(foods, 1):
        food_name = food['original_name']
        base_nutrition = food['nutrition']

        print(f"{i}. {food_name}")

        # Serving optionsを生成
        serving_options = generate_serving_options(food_name, base_nutrition)

        # 拡張データ
        enriched_food = {
            **food,  # 既存データを保持
            "serving_options": serving_options,
            "base_nutrition_per_100g": base_nutrition,
            "total_serving_options": len(serving_options),
            "food_type": determine_food_type(food_name),
            "data_source": "calculated_from_100g_nutrition",
            "enriched_at": datetime.now().isoformat()
        }

        enriched_foods.append(enriched_food)
        print(f"   ✅ {len(serving_options)} serving options生成")

    # 結果を保存
    output_dir = Path("/Users/odasoya/meal_analysis_api_2/web_scraping_2/output")
    output_file = output_dir / "stemmed_only_foods_enriched.json"

    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_foods": len(enriched_foods),
            "description": "Stemmed DBのみに存在する食材の栄養情報とServing情報（拡張版）",
            "data_source": "既存100g栄養情報から計算",
            "serving_options_generated": True
        },
        "foods": enriched_foods
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完了: {output_file}")
    print(f"   総食材数: {len(enriched_foods)}件")

    # サマリー統計
    print("\n" + "=" * 80)
    print("📊 統計サマリー")
    print("=" * 80)

    food_type_counts = {}
    for food in enriched_foods:
        food_type = food['food_type']
        food_type_counts[food_type] = food_type_counts.get(food_type, 0) + 1

    print("\n食材タイプ別内訳:")
    for food_type, count in sorted(food_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {food_type}: {count}件")

    total_serving_options = sum(food['total_serving_options'] for food in enriched_foods)
    avg_serving_options = total_serving_options / len(enriched_foods)
    print(f"\n総Serving Options: {total_serving_options}個")
    print(f"平均Serving Options/食材: {avg_serving_options:.1f}個")


if __name__ == "__main__":
    process_stemmed_only_foods()
