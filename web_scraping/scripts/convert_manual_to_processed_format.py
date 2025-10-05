#!/usr/bin/env python3
"""
47食材のデータを1104食材の形式に変換するスクリプト

変換内容:
1. essential_nutrition.micronutrients → nutrition_facts.nutrients に追加
2. detailed_nutrition → 削除（重複のため）
3. data_quality → metadata に変換
4. food_id を再採番（1104の次から開始）
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ManualToProcessedConverter:
    """47食材を1104食材の形式に変換"""

    def __init__(self, manual_file: str, processed_file: str):
        self.manual_file = Path(manual_file)
        self.processed_file = Path(processed_file)
        self.converted_foods = []

        # 1104食材のデータを読み込み（food_idの最大値を取得するため）
        with open(self.processed_file, 'r', encoding='utf-8') as f:
            self.processed_data = json.load(f)

        # 最大food_idを取得
        max_id = 0
        for food in self.processed_data['foods']:
            food_id = food['food_id']
            # "food_1234" から数字部分を抽出
            if food_id.startswith('food_'):
                num = int(food_id.split('_')[1])
                max_id = max(max_id, num)

        self.next_food_id = max_id + 1
        print(f"📌 次のfood_id: food_{self.next_food_id:04d}")

    def convert_all_foods(self):
        """全食材を変換"""
        with open(self.manual_file, 'r', encoding='utf-8') as f:
            manual_data = json.load(f)

        print(f"\n🔄 {len(manual_data['foods'])}食材を変換中...")

        for food in manual_data['foods']:
            converted = self._convert_single_food(food)
            self.converted_foods.append(converted)

        print(f"✅ {len(self.converted_foods)}食材の変換完了")

    def _convert_single_food(self, food: Dict[str, Any]) -> Dict[str, Any]:
        """1食材を変換"""

        # 新しいfood_idを生成
        new_food_id = f"food_{self.next_food_id:04d}"
        self.next_food_id += 1

        # essential_nutritionからmicronutrientsを取り出す
        micronutrients = food['essential_nutrition'].pop('micronutrients', {})

        # nutrition_factsを構築
        nutrition_facts = self._build_nutrition_facts(
            food['essential_nutrition']['macros'],
            micronutrients
        )

        # metadataを構築（data_qualityから変換）
        metadata = self._build_metadata(food.get('data_quality', {}))

        # 変換後の構造
        converted = {
            'food_id': new_food_id,
            'food_name': food['food_name'],
            'category': food['category'],
            'essential_nutrition': {
                'calories': food['essential_nutrition']['calories'],
                'serving_size': food['essential_nutrition']['serving_size'],
                'macros': food['essential_nutrition']['macros'],
                'serving_info': food['essential_nutrition'].get('serving_info', {})
            },
            'nutrition_facts': nutrition_facts,
            'serving_options': food['serving_options'],
            'metadata': metadata
        }

        return converted

    def _build_nutrition_facts(self, macros: Dict, micronutrients: Dict) -> Dict[str, List]:
        """nutrition_factsを構築（配列形式）"""
        nutrients = []

        # Macrosを追加
        macro_mapping = {
            'total_fat': 'Total Fat',
            'saturated_fat': 'Saturated Fat',
            'trans_fat': 'Trans Fat',
            'monounsaturated_fat': 'Monounsaturated Fat',
            'polyunsaturated_fat': 'Polyunsaturated Fat',
            'total_carbs': 'Total Carbs',
            'dietary_fiber': 'Dietary Fiber',
            'total_sugars': 'Total Sugars',
            'protein': 'Protein',
            'cholesterol': 'Cholesterol',
            'sodium': 'Sodium'
        }

        for key, name in macro_mapping.items():
            if key in macros:
                nutrient_data = macros[key]
                nutrients.append({
                    'name': name,
                    'key': key,
                    'value': nutrient_data['value'],
                    'unit': nutrient_data['unit'],
                    'raw_text': nutrient_data.get('raw_text', f"{name} {nutrient_data['value']}{nutrient_data['unit']}")
                })

        # Micronutrientsを追加
        micro_mapping = {
            'vitamin_a': 'Vitamin A',
            'vitamin_c': 'Vitamin C',
            'calcium': 'Calcium',
            'iron': 'Iron',
            'potassium': 'Potassium'
        }

        for key, name in micro_mapping.items():
            if key in micronutrients:
                nutrient_data = micronutrients[key]
                nutrients.append({
                    'name': name,
                    'key': key,
                    'value': nutrient_data['value'],
                    'unit': nutrient_data['unit'],
                    'raw_text': nutrient_data.get('raw_text', f"{name} {nutrient_data['value']}{nutrient_data['unit']}")
                })

        return {'nutrients': nutrients}

    def _build_metadata(self, data_quality: Dict) -> Dict[str, Any]:
        """metadataを構築（data_qualityから変換）"""
        return {
            'processed_at': datetime.now().isoformat(),
            'original_collection_success': True,
            'raw_nutrition_count': 0,  # 手作業入力のため0
            'raw_serving_count': 0,    # 手作業入力のため0
            'quality_score': data_quality.get('completeness_score', 1.0),
            'source': 'manual_input',
            'essential_extraction_success': {
                'calories': True,
                'serving_size': True,
                'total_fat': True,
                'total_carbs': True,
                'protein': True
            }
        }

    def save_converted_data(self, output_file: str):
        """変換後のデータを保存"""
        output = {
            'metadata': {
                'version': '1.0_converted',
                'processed_at': datetime.now().isoformat(),
                'total_foods': len(self.converted_foods),
                'source': 'manual_input_converted_to_processed_format',
                'processing_notes': '47食材を1104食材の形式に変換'
            },
            'foods': self.converted_foods
        }

        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 変換済みデータ保存: {output_path}")
        print(f"📊 総食材数: {len(self.converted_foods)}個")


def main():
    print("🔄 47食材を1104食材の形式に変換")
    print("=" * 80)

    # ファイルパス
    manual_file = "processed_data/manual_foods_formatted_46.json"
    processed_file = "processed_data/processed_foods_20251001_125923.json"
    output_file = "processed_data/manual_foods_converted_to_processed_format.json"

    # 変換実行
    converter = ManualToProcessedConverter(manual_file, processed_file)
    converter.convert_all_foods()
    converter.save_converted_data(output_file)

    print("\n" + "=" * 80)
    print("✅ 変換完了！")


if __name__ == "__main__":
    main()
