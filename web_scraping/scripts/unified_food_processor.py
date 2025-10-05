#!/usr/bin/env python3
"""
統一食材プロセッサー
ManualデータとScrapingデータを同じロジックで処理
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class UnifiedFoodProcessor:
    """Manual/Scraping両方に対応する統一プロセッサー"""

    def __init__(self):
        self.base_dir = Path('.')
        self.data_dir = self.base_dir / 'data'
        self.output_dir = self.base_dir / 'processed_data'

    def extract_clean_nutrition_data(self, raw_data: List[str]) -> List[str]:
        """raw_nutrition_dataからクリーンな栄養情報のみ抽出"""
        clean_items = []

        for item in raw_data:
            if not item or not isinstance(item, str):
                continue

            item = item.strip()

            # "Serving Size"情報を抽出（後で使用）
            # 例: "Serving Size", "block (455g)"
            if item == "Serving Size":
                clean_items.append(item)
                continue

            # Serving Sizeの次の行（unit (grams)形式）を抽出
            # 例: "block (455g)", "cup (128g)"
            if re.match(r'^[\w\s\.\-\(\)"/,]+\s*\(\d+(?:\.\d+)?g\)$', item):
                clean_items.append(item)
                continue

            # 有効な栄養情報パターン
            # "Calories 457cals" または "457cals"
            if re.match(r'^Calories\s+\d+(?:,\d{3})*(?:\.\d+)?cals$', item):
                clean_items.append(item)
                continue

            if re.match(r'^\d+(?:,\d{3})*(?:\.\d+)?cals$', item):
                clean_items.append(f"Calories {item}")
                continue

            # "Total Fat 0.1g" のようなパターン
            if re.match(r'^.+?\s+\d+(?:,\d{3})*(?:\.\d+)?(g|mg|mcg)$', item):
                clean_items.append(item)
                continue

        return clean_items

    def extract_clean_serving_data(self, raw_data: List[str]) -> List[str]:
        """raw_serving_dataからクリーンなserving情報のみ抽出"""
        clean_items = []

        # パターン: "unit Xcals / Y g" または "X unit Ycals / Z g"
        pattern1 = r'^\d+(?:\.\d+)?\s+[\w\s\.\-\(\)"/,]+?\s+\d+(?:,\d{3})*(?:\.\d+)?\s*cals?\s*/\s*\d+(?:\.\d+)?\s*g\s*$'
        pattern2 = r'^[\w\s\.\-\(\)"/,]+?\s+\d+(?:,\d{3})*(?:\.\d+)?\s*cals?\s*/\s*\d+(?:\.\d+)?\s*g\s*$'

        for item in raw_data:
            if not item or not isinstance(item, str):
                continue

            item = item.strip()

            # パターンマッチング
            if re.match(pattern1, item, re.IGNORECASE) or re.match(pattern2, item, re.IGNORECASE):
                clean_items.append(item)

        return clean_items

    def parse_nutrition_data(self, nutrition_items: List[str]) -> Dict[str, Any]:
        """栄養情報をパースする（Serving Size情報も含む）"""
        nutrients = []
        serving_size_info = None

        # Serving Size情報を探す
        for i, line in enumerate(nutrition_items):
            if line.strip() == "Serving Size" and i + 1 < len(nutrition_items):
                next_line = nutrition_items[i + 1].strip()
                # "block (455g)" のようなパターン
                match = re.match(r'^([\w\s\.\-\(\)"/,]+?)\s*\((\d+(?:\.\d+)?)g\)$', next_line)
                if match:
                    serving_size_info = {
                        'unit': match.group(1).strip(),
                        'grams': float(match.group(2))
                    }
                break

        for line in nutrition_items:
            line = line.strip()

            # "Calories 488cals" のようなパターン
            cal_match = re.match(r'Calories\s+(\d+(?:,\d{3})*(?:\.\d+)?)cals', line)
            if cal_match:
                nutrients.append({
                    'name': 'Calories',
                    'key': 'calories',
                    'value': float(cal_match.group(1).replace(',', '')),
                    'unit': 'kcal',
                    'raw_text': line
                })
                continue

            # "Total Fat 0.1g" のようなパターン
            nutrient_match = re.match(r'(.+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)(g|mg|mcg)\s*$', line)
            if nutrient_match:
                nutrient_name = nutrient_match.group(1).strip()
                value = float(nutrient_match.group(2).replace(',', ''))
                unit = nutrient_match.group(3)

                key = nutrient_name.lower().replace(' ', '_').replace('-', '_')

                nutrients.append({
                    'name': nutrient_name,
                    'key': key,
                    'value': value,
                    'unit': unit,
                    'raw_text': line
                })

        return {
            'nutrients': nutrients,
            'serving_size_info': serving_size_info
        }

    def parse_serving_data(self, serving_items: List[str]) -> List[Dict[str, Any]]:
        """Serving情報をパースする（manual_foods_processorと同じロジック）"""
        servings = []

        for line in serving_items:
            line = line.strip()

            # "cup 488cals / 128 g" のようなパターン
            # 数値プレフィックス付き: "0.5 fillet 280cals / 154 g"
            pattern1 = r'^(\d+(?:\.\d+)?)\s+([\w\s\.\-\(\)"/,]+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g\s*$'
            pattern2 = r'^([\w\s\.\-\(\)"/,]+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g\s*$'

            match1 = re.match(pattern1, line, re.IGNORECASE)
            match2 = re.match(pattern2, line, re.IGNORECASE)

            if match1:
                quantity = match1.group(1)
                unit = match1.group(2).strip()
                full_unit = f"{quantity} {unit}"
                calories = float(match1.group(3).replace(',', ''))
                grams = float(match1.group(4))

                servings.append({
                    'unit': self._clean_unit_name(full_unit) or full_unit,
                    'calories_per_unit': calories,
                    'grams_per_unit': grams,
                    'conversion_factor': grams,
                    'calories_per_gram': round(calories / grams, 4) if grams > 0 else 0,
                    'display_text': f"1 {full_unit} ({grams}g) = {calories} kcal",
                    'source': 'unified_processor'
                })
            elif match2:
                unit = match2.group(1).strip()
                calories = float(match2.group(2).replace(',', ''))
                grams = float(match2.group(3))

                servings.append({
                    'unit': self._clean_unit_name(unit) or unit,
                    'calories_per_unit': calories,
                    'grams_per_unit': grams,
                    'conversion_factor': grams,
                    'calories_per_gram': round(calories / grams, 4) if grams > 0 else 0,
                    'display_text': f"1 {unit} ({grams}g) = {calories} kcal",
                    'source': 'unified_processor'
                })

        return servings

    def _clean_unit_name(self, unit_text: str) -> Optional[str]:
        """単位名をクリーニング（manual_foods_processorと同じロジック）"""
        if not unit_text or not isinstance(unit_text, str):
            return None

        unit_lower = unit_text.lower().strip()

        # 数値プレフィックスを持つunitの場合
        numeric_prefix_match = re.match(r'^(\d+(?:\.\d+)?)\s+(.+)$', unit_lower)

        if numeric_prefix_match:
            quantity = numeric_prefix_match.group(1)
            unit_part = numeric_prefix_match.group(2).strip()
            standardized_unit = self._standardize_unit(unit_part)
            return f"{quantity} {standardized_unit}"

        standardized = self._standardize_unit(unit_lower)
        return standardized

    def _standardize_unit(self, unit_text: str) -> str:
        """単位を標準化（manual_foods_processorと同じロジック）"""
        if not unit_text:
            return unit_text

        unit_lower = unit_text.lower().strip()

        standard_units = {
            'fl oz': 'fl oz',
            'fluid ounce': 'fl oz',
            'tablespoon': 'tablespoon',
            'tbsp': 'tablespoon',
            'tbs': 'tablespoon',
            'teaspoon': 'teaspoon',
            'tsp': 'teaspoon',
            'ounce': 'oz',
            'oz': 'oz',
            'gram': 'gram',
            'g': 'gram',
            'cup': 'cup',
            'cups': 'cup',
            'pound': 'lb',
            'lb': 'lb',
            'lbs': 'lb',
            'ml': 'ml',
            'milliliter': 'ml',
            'liter': 'liter',
            'l': 'liter',
            'serving': 'serving',
            'servings': 'serving',
            'piece': 'piece',
            'pieces': 'piece',
            'slice': 'slice',
            'slices': 'slice',
            'each': 'each'
        }

        # 完全一致チェック
        if unit_lower in standard_units:
            return standard_units[unit_lower]

        # 特殊unit形式として全体を保存
        if len(unit_lower) <= 50 and re.match(r'^[\w\s\.\-\(\)"/,]+$', unit_lower):
            return unit_lower

        return unit_text

    def extract_essential_nutrition(self, nutrients: List[Dict], servings: List[Dict], serving_size_info: Optional[Dict] = None) -> Dict[str, Any]:
        """必須栄養情報を抽出"""
        nutrient_dict = {n['key']: n for n in nutrients}

        # カロリー
        calories = None
        calories_value = 0
        if 'calories' in nutrient_dict:
            calories_value = nutrient_dict['calories']['value']
            calories = {
                'value': calories_value,
                'unit': 'kcal',
                'source': 'nutrition_data'
            }

        # Serving size（優先順位付き選択）
        serving_size = None

        # 優先順位1: Nutrition FactsのServing Size情報を使用（gramsが0より大きい場合のみ）
        if serving_size_info and calories_value > 0 and serving_size_info.get('grams', 0) > 0:
            serving_size = {
                'unit': serving_size_info['unit'],
                'grams': serving_size_info['grams'],
                'calories': calories_value
            }

        # 優先順位2: caloriesと一致するservingを探す
        if not serving_size and servings and len(servings) > 0 and calories_value > 0:
            for serving in servings:
                if abs(serving['calories_per_unit'] - calories_value) < 0.1:
                    serving_size = {
                        'unit': serving['unit'],
                        'grams': serving['grams_per_unit'],
                        'calories': serving['calories_per_unit']
                    }
                    break

        # 優先順位3: gramが1.0のservingは避け、cup/tablespoon等を優先
        if not serving_size and servings:
            preferred_units = ['cup', 'tablespoon', 'teaspoon', 'oz', 'piece', 'slice']
            for unit_name in preferred_units:
                for serving in servings:
                    if unit_name in serving['unit'].lower():
                        serving_size = {
                            'unit': serving['unit'],
                            'grams': serving['grams_per_unit'],
                            'calories': serving['calories_per_unit']
                        }
                        break
                if serving_size:
                    break

        # 優先順位4: 最も大きいgrams_per_unitのservingを選ぶ（gramは除外）
        if not serving_size and servings:
            non_gram_servings = [s for s in servings if 'gram' not in s['unit'].lower() or s['grams_per_unit'] > 10]
            if non_gram_servings:
                largest_serving = max(non_gram_servings, key=lambda s: s['grams_per_unit'])
                serving_size = {
                    'unit': largest_serving['unit'],
                    'grams': largest_serving['grams_per_unit'],
                    'calories': largest_serving['calories_per_unit']
                }

        # 優先順位5: それでもない場合は最初のservingを使用
        if not serving_size and servings and len(servings) > 0:
            first_serving = servings[0]
            serving_size = {
                'unit': first_serving['unit'],
                'grams': first_serving['grams_per_unit'],
                'calories': first_serving['calories_per_unit']
            }

        # マクロ栄養素
        macros = {
            'total_fat': None,
            'total_carbs': None,
            'protein': None
        }

        for key in ['total_fat', 'total_carbs', 'protein']:
            if key in nutrient_dict:
                macros[key] = {
                    'value': nutrient_dict[key]['value'],
                    'unit': nutrient_dict[key]['unit'],
                    'raw_text': nutrient_dict[key]['raw_text']
                }

        return {
            'calories': calories,
            'serving_size': serving_size,
            'macros': macros
        }

    def process_scraped_food(self, food_data: Dict[str, Any], food_id: str) -> Optional[Dict[str, Any]]:
        """Scrapingデータを処理"""

        # Raw dataを取得
        raw_nutrition = food_data.get('nutrition_data', {}).get('detailed_nutrients', {}).get('raw_nutrition_data', [])
        raw_serving = food_data.get('serving_options', {}).get('raw_serving_data', [])

        # クリーンなデータを抽出
        clean_nutrition = self.extract_clean_nutrition_data(raw_nutrition)
        clean_serving = self.extract_clean_serving_data(raw_serving)

        # パース
        nutrition_result = self.parse_nutrition_data(clean_nutrition)
        nutrients = nutrition_result['nutrients']
        serving_size_info = nutrition_result['serving_size_info']
        servings = self.parse_serving_data(clean_serving)

        # 最低2個のservingが必要
        if len(servings) < 2:
            return None

        # 必須栄養情報を抽出
        essential_nutrition = self.extract_essential_nutrition(nutrients, servings, serving_size_info)

        # カテゴリ
        category = food_data.get('catalog_category', 'Other')

        # Food name
        food_name = food_data.get('food_name', '').replace('\n', ', ')

        return {
            'food_id': food_id,
            'food_name': food_name,
            'category': category,
            'essential_nutrition': essential_nutrition,
            'nutrition_facts': {
                'nutrients': nutrients,
                'total_nutrients': len(nutrients)
            },
            'serving_options': {
                'servings': servings,
                'total_servings': len(servings)
            },
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'source': 'scraped_data',
                'processor': 'unified_food_processor',
                'raw_nutrition_count': len(clean_nutrition),
                'raw_serving_count': len(clean_serving),
                'serving_size_info': serving_size_info,
                'essential_extraction_success': {
                    'calories': essential_nutrition['calories'] is not None,
                    'serving_size': essential_nutrition['serving_size'] is not None,
                    'total_fat': essential_nutrition['macros']['total_fat'] is not None,
                    'total_carbs': essential_nutrition['macros']['total_carbs'] is not None,
                    'protein': essential_nutrition['macros']['protein'] is not None
                }
            }
        }


def main():
    """テスト実行"""
    print("🔄 統一プロセッサーテスト")
    print("=" * 80)

    processor = UnifiedFoodProcessor()

    # Scrapingデータを読み込み
    scraping_file = processor.data_dir / 'comprehensive_food_collection_all_20251001_124446.json'

    with open(scraping_file, 'r', encoding='utf-8') as f:
        scraping_data = json.load(f)

    # 最初の10個をテスト
    results = []
    success_count = 0
    fail_count = 0

    for i, item in enumerate(scraping_data['collection_results'][:10]):
        if not item.get('data_collection_success'):
            continue

        food_data = item.get('comprehensive_data', {})
        food_id = f"food_{i+1:04d}"

        processed = processor.process_scraped_food(food_data, food_id)

        if processed:
            results.append(processed)
            success_count += 1
            print(f"✅ {processed['food_name'][:50]}")
        else:
            fail_count += 1
            print(f"❌ {food_data.get('food_name', 'Unknown')[:50]}")

    print(f"\n📊 結果: 成功 {success_count}個, 失敗 {fail_count}個")

    # 最初の結果を表示
    if results:
        print(f"\n📝 最初の結果サンプル:")
        print(json.dumps(results[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
