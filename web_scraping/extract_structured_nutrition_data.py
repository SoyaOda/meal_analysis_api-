#!/usr/bin/env python3
"""
生データから構造化された栄養情報を抽出するスクリプト
ユーザーが示したWebページの情報を参考に、必要な情報を整理
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any


def extract_serving_info(raw_serving_data: List[str]) -> Dict[str, Any]:
    """
    生のserving情報から構造化されたserving情報を抽出

    期待される情報例:
    - anchovy 8cals / 4 g
    - gram 2cals / 1 g
    - can (2 oz) 95cals / 45 g
    - 5 anchovies 42cals / 20 g
    - oz, boneless 60cals / 28.4 g
    """
    serving_options = []

    # Serving情報のパターンを検索
    for text in raw_serving_data:
        # パターン1: "serving名 カロリー / 重量"形式
        pattern1 = r'^([^0-9]+?)\s+(\d+)cals?\s*/\s*([0-9.]+)\s*g$'
        match = re.match(pattern1, text.strip())
        if match:
            serving_name = match.group(1).strip()
            calories = int(match.group(2))
            weight_g = float(match.group(3))

            serving_options.append({
                "serving_name": serving_name,
                "calories": calories,
                "weight_g": weight_g,
                "raw_text": text
            })
            continue

        # パターン2: 単純なserving名（"anchovy", "gram"など）
        serving_candidates = [
            "anchovy", "gram", "can", "anchovies", "oz, boneless", "oz", "lb",
            "cup", "tbsp", "tsp", "piece", "slice"
        ]

        for candidate in serving_candidates:
            if candidate in text.lower() and len(text.strip()) <= 20:
                # 近くのカロリー情報を探す
                for cal_text in raw_serving_data:
                    if f"{candidate}" in cal_text.lower():
                        cal_match = re.search(r'(\d+)\s*cals?', cal_text)
                        weight_match = re.search(r'([0-9.]+)\s*g', cal_text)

                        if cal_match:
                            serving_options.append({
                                "serving_name": candidate,
                                "calories": int(cal_match.group(1)),
                                "weight_g": float(weight_match.group(1)) if weight_match else None,
                                "raw_text": text
                            })
                            break

    # 重複除去
    unique_servings = []
    seen_names = set()
    for serving in serving_options:
        if serving["serving_name"] not in seen_names:
            unique_servings.append(serving)
            seen_names.add(serving["serving_name"])

    return {
        "serving_options": unique_servings,
        "total_servings": len(unique_servings),
        "extraction_method": "pattern_based_structured"
    }


def extract_nutrition_info(raw_nutrition_data: List[str]) -> Dict[str, Any]:
    """
    生の栄養素情報から構造化された栄養素情報を抽出

    期待される情報例:
    - Total Fat 2.8g    4%
    - Saturated Fat 0.6g    3%
    - Protein 8g    16%
    - Cholesterol 24mg    8%
    - Sodium 1,042mg    43%
    """
    nutrients = {}
    serving_size_info = {}

    # 基本カロリー情報
    for text in raw_nutrition_data:
        # カロリー情報
        cal_match = re.search(r'Calories?\s+(\d+)cals?', text, re.IGNORECASE)
        if cal_match:
            nutrients["calories"] = int(cal_match.group(1))

        # Serving Size情報
        serving_size_match = re.search(r'Serving Size\s+(.+?)\s*\(([^)]+)\)', text, re.IGNORECASE)
        if serving_size_match:
            serving_size_info = {
                "serving_name": serving_size_match.group(1).strip(),
                "weight": serving_size_match.group(2).strip()
            }

    # 栄養素情報のパターン
    nutrient_patterns = [
        (r'Total Fat\s+([0-9.]+)g\s+(\d+)%', 'total_fat'),
        (r'Saturated Fat\s+([0-9.]+)g\s+(\d+)%', 'saturated_fat'),
        (r'Trans Fat\s+([0-9.]+)g', 'trans_fat'),
        (r'Monounsaturated Fat\s+([0-9.]+)g', 'monounsaturated_fat'),
        (r'Polyunsaturated Fat\s+([0-9.]+)g', 'polyunsaturated_fat'),
        (r'Total Carbs?\s+([0-9.]+)g\s+(\d+)%', 'total_carbs'),
        (r'Net Carbs?\s+([0-9.]+)g', 'net_carbs'),
        (r'Dietary Fiber\s+([0-9.]+)g\s+(\d+)%', 'dietary_fiber'),
        (r'Total Sugars?\s+([0-9.]+)g', 'total_sugars'),
        (r'Added Sugars?\s+([0-9.]+)g\s+(\d+)%', 'added_sugars'),
        (r'Protein\s+([0-9.]+)g\s+(\d+)%', 'protein'),
        (r'Cholesterol\s+([0-9.]+)mg\s+(\d+)%', 'cholesterol'),
        (r'Sodium\s+([0-9,]+)mg\s+(\d+)%', 'sodium'),
        (r'Vitamin A\s+([0-9.]+)mcg\s+(\d+)%', 'vitamin_a'),
        (r'Vitamin C\s+([0-9.]+)mg\s+(\d+)%', 'vitamin_c'),
        (r'Calcium\s+([0-9.]+)mg\s+(\d+)%', 'calcium'),
        (r'Iron\s+([0-9.]+)mg\s+(\d+)%', 'iron'),
        (r'Potassium\s+([0-9.]+)mg\s+(\d+)%', 'potassium'),
        (r'Alcohol\s+([0-9.]+)g', 'alcohol'),
        (r'Caffeine\s+([0-9.]+)mg', 'caffeine'),
    ]

    # 全テキストを結合して検索
    full_text = " ".join(raw_nutrition_data)

    for pattern, nutrient_name in nutrient_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '')  # カンマを除去
            nutrients[nutrient_name] = {
                "value": float(value),
                "unit": "g" if "g" in pattern else "mg" if "mg" in pattern else "mcg",
                "daily_value_percent": int(match.group(2)) if len(match.groups()) > 1 and match.group(2) else None
            }

    return {
        "serving_size_info": serving_size_info,
        "nutrients": nutrients,
        "total_nutrients": len(nutrients),
        "extraction_method": "regex_pattern_based"
    }


def process_json_file(input_file: str, output_file: str):
    """JSONファイルを処理して構造化データを生成"""

    print(f"📄 処理中: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    processed_results = []

    for result in data['collection_results']:
        food_name = result['food_name']
        catalog_category = result.get('catalog_category', 'unknown')
        catalog_food_name = result.get('catalog_food_name', food_name)

        print(f"\n🍽️ 処理中: {food_name[:30]}...")

        # 生データを取得
        comprehensive_data = result['comprehensive_data']
        raw_serving_data = comprehensive_data['serving_options']['raw_serving_data']
        raw_nutrition_data = comprehensive_data['nutrition_data']['detailed_nutrients']['raw_nutrition_data']

        # 構造化データを抽出
        structured_serving = extract_serving_info(raw_serving_data)
        structured_nutrition = extract_nutrition_info(raw_nutrition_data)

        processed_result = {
            "sequence": result['sequence'],
            "food_name": food_name,
            "catalog_category": catalog_category,
            "catalog_food_name": catalog_food_name,
            "duration_seconds": result['duration_seconds'],
            "structured_serving_info": structured_serving,
            "structured_nutrition_info": structured_nutrition,
            "raw_data_counts": {
                "raw_serving_items": len(raw_serving_data),
                "raw_nutrition_items": len(raw_nutrition_data)
            },
            "extraction_success": {
                "serving_extracted": structured_serving['total_servings'] > 0,
                "nutrition_extracted": structured_nutrition['total_nutrients'] > 0
            },
            "timestamp": datetime.now().isoformat()
        }

        processed_results.append(processed_result)

        print(f"  📊 Serving抽出: {structured_serving['total_servings']}個")
        print(f"  🥗 栄養素抽出: {structured_nutrition['total_nutrients']}個")

    # 結果をまとめる
    output_data = {
        "processing_summary": {
            "source_file": input_file,
            "processed_at": datetime.now().isoformat(),
            "total_foods": len(processed_results),
            "extraction_method": "structured_pattern_based",
            "successful_serving_extractions": sum(1 for r in processed_results if r['extraction_success']['serving_extracted']),
            "successful_nutrition_extractions": sum(1 for r in processed_results if r['extraction_success']['nutrition_extracted'])
        },
        "structured_results": processed_results
    }

    # ファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 構造化データを保存: {output_file}")
    print(f"📊 総食材数: {len(processed_results)}")
    print(f"🍽️ Serving抽出成功: {output_data['processing_summary']['successful_serving_extractions']}/{len(processed_results)}")
    print(f"🥗 栄養素抽出成功: {output_data['processing_summary']['successful_nutrition_extractions']}/{len(processed_results)}")


def main():
    """メイン処理"""
    input_file = "data/playwright_improved_comprehensive_collection_20250928_173306.json"
    output_file = "data/structured_nutrition_data_20250928.json"

    try:
        process_json_file(input_file, output_file)
        print("\n🎉 構造化データ抽出完了！")

        # 結果の内容確認
        print("\n📋 構造化データの内容確認:")
        with open(output_file, 'r', encoding='utf-8') as f:
            structured_data = json.load(f)

        for result in structured_data['structured_results']:
            print(f"\n食材: {result['food_name'][:30]}...")
            print(f"  カテゴリ: {result['catalog_category']}")

            # Serving情報表示
            serving_info = result['structured_serving_info']
            print(f"  📊 Serving Options ({serving_info['total_servings']}個):")
            for serving in serving_info['serving_options'][:3]:  # 最初の3個のみ表示
                print(f"    - {serving['serving_name']}: {serving['calories']}cals")
                if serving['weight_g']:
                    print(f"      重量: {serving['weight_g']}g")

            # 栄養素情報表示
            nutrition_info = result['structured_nutrition_info']
            print(f"  🥗 Nutrition Info ({nutrition_info['total_nutrients']}個):")
            nutrients = nutrition_info['nutrients']
            for nutrient_name, nutrient_data in list(nutrients.items())[:5]:  # 最初の5個のみ表示
                if isinstance(nutrient_data, dict):
                    print(f"    - {nutrient_name}: {nutrient_data['value']}{nutrient_data['unit']}")
                    if nutrient_data.get('daily_value_percent'):
                        print(f"      (%日摂取量: {nutrient_data['daily_value_percent']}%)")

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()