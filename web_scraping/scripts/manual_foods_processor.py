#!/usr/bin/env python3
"""
manual_work_50_foods.txt専用の後処理プロセッサー
既存のfood_data_processor.pyと同じフォーマットで出力
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


class ManualFoodsProcessor:
    """手作業食材データの後処理プロセッサー"""

    def __init__(self):
        self.base_dir = Path('.')
        self.data_dir = self.base_dir / 'data'
        self.output_dir = self.base_dir / 'processed_data'
        self.processed_foods = []

    def parse_manual_foods_file(self, file_path: str) -> List[Dict[str, Any]]:
        """manual_work_50_foods.txtをパースする"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 食材ごとに分割（================で区切られている）
        food_sections = content.split('================================================================================')

        foods = []
        for section in food_sections:
            section = section.strip()
            if not section or 'リスト' in section or '各食材名' in section:
                continue

            # 食材名を抽出（数字. で始まる行）
            name_match = re.search(r'^\d+\.\s+(.+?)$', section, re.MULTILINE)
            if not name_match:
                continue

            food_name = name_match.group(1).strip()

            # 栄養情報を抽出
            nutrition_text = self._extract_section(section, '【栄養情報】')
            # Serving情報を抽出
            serving_text = self._extract_section(section, '【Serving情報】')

            if nutrition_text and serving_text:
                foods.append({
                    'food_name': food_name,
                    'nutrition_text': nutrition_text,
                    'serving_text': serving_text
                })

        return foods

    def _extract_section(self, text: str, section_header: str) -> Optional[str]:
        """セクションを抽出"""
        pattern = rf'{re.escape(section_header)}\s*\n(.*?)(?=【|$)'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            if content and content != 'nan':
                return content
        return None

    def parse_nutrition_data(self, nutrition_text: str) -> List[Dict[str, Any]]:
        """栄養情報をパースする"""
        nutrients = []

        # 各行から栄養素を抽出
        lines = nutrition_text.split('\n')
        for line in lines:
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

            # "Total Fat 0.1g\t0%" のようなパターン
            nutrient_match = re.match(r'(.+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)(g|mg|mcg)\s*(?:\t.*)?$', line)
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

        return nutrients

    def parse_serving_data(self, serving_text: str) -> List[Dict[str, Any]]:
        """Serving情報をパースする"""
        servings = []

        lines = serving_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line == 'Select Serving':
                continue

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
                    'source': 'manual_entry'
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
                    'source': 'manual_entry'
                })

        return servings

    def _clean_unit_name(self, unit_text: str) -> Optional[str]:
        """単位名をクリーニング"""
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
        """単位を標準化（完全一致のみ）"""
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

    def extract_essential_nutrition(self, nutrients: List[Dict]) -> Dict[str, Any]:
        """必須栄養情報を抽出"""
        nutrient_dict = {n['key']: n for n in nutrients}

        # カロリー
        calories = None
        if 'calories' in nutrient_dict:
            calories = {
                'value': nutrient_dict['calories']['value'],
                'unit': 'kcal',
                'source': 'nutrition_data'
            }

        # Serving size（最初のserving情報から）
        serving_size = None

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
            'macros': macros,
            'serving_info': {}
        }

    def process_food(self, food_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """1つの食材を処理"""
        food_name = food_data['food_name']

        # 栄養情報とserving情報をパース
        nutrients = self.parse_nutrition_data(food_data['nutrition_text'])
        servings = self.parse_serving_data(food_data['serving_text'])

        # 最低2個のservingが必要
        if len(servings) < 2:
            print(f"⚠️  スキップ: {food_name} (serving数不足: {len(servings)}個)")
            return None

        # 必須栄養情報を抽出
        essential_nutrition = self.extract_essential_nutrition(nutrients)

        # カテゴリを推定（食材名から）
        category = self._infer_category(food_name)

        return {
            'food_id': f"manual_{len(self.processed_foods) + 1:04d}",
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
                'source': 'manual_work_50_foods',
                'raw_nutrition_count': len(nutrients),
                'raw_serving_count': len(servings),
                'essential_extraction_success': {
                    'calories': essential_nutrition['calories'] is not None,
                    'serving_size': essential_nutrition['serving_size'] is not None,
                    'total_fat': essential_nutrition['macros']['total_fat'] is not None,
                    'total_carbs': essential_nutrition['macros']['total_carbs'] is not None,
                    'protein': essential_nutrition['macros']['protein'] is not None
                }
            }
        }

    def _infer_category(self, food_name: str) -> str:
        """食材名からカテゴリを推定"""
        name_lower = food_name.lower()

        # スパイス・調味料
        if any(word in name_lower for word in ['seasoning', 'salt', 'spice', 'paprika', 'cardamom']):
            return 'Spices & Herbs'

        # 野菜
        if any(word in name_lower for word in ['okra', 'vegetable']):
            return 'Vegetables - raw, frozen, or cooked'

        # 魚介類
        if any(word in name_lower for word in ['bass', 'fish', 'seafood']):
            return 'Fish & Seafood'

        # 豆類
        if any(word in name_lower for word in ['hummus', 'natto', 'bean']):
            return 'Beans & Peas'

        # 乳製品
        if any(word in name_lower for word in ['milk', 'dairy']):
            return 'Dairy, Dairy Substitutes & Egg'

        # ソース・調味料
        if any(word in name_lower for word in ['sauce', 'guacamole', 'salsa', 'olives']):
            return 'Condiments, Dressings & Sauces'

        # 甘味料
        if any(word in name_lower for word in ['allulose', 'erythritol', 'honey', 'jelly', 'molasses', 'sweetener']):
            return 'Sweets & Sweeteners'

        # 飲料
        if any(word in name_lower for word in ['water', 'soda', 'cola', 'ginger ale', 'tonic', 'champagne', 'cognac', 'liqueur', 'martini', 'seltzer', 'ice']):
            return 'Beverages'

        # フルーツ
        if any(word in name_lower for word in ['watermelon', 'fruit']):
            return 'Fruit - raw or frozen'

        # ナッツ・種子
        if any(word in name_lower for word in ['flaxseed', 'walnut', 'seed', 'nut']):
            return 'Nuts & Seeds'

        # 穀物
        if any(word in name_lower for word in ['cornstarch', 'yeast', 'grain']):
            return 'Grains & Grain Products'

        return 'Other'

    def save_processed_data(self) -> str:
        """処理済みデータを保存"""
        os.makedirs(self.output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"manual_foods_processed_{timestamp}.json"

        output_data = {
            'metadata': {
                'version': '1.0',
                'processed_at': datetime.now().isoformat(),
                'total_foods': len(self.processed_foods),
                'source_file': 'manual_work_50_foods.txt',
                'processing_notes': 'Manually entered foods from MyNetDiary'
            },
            'foods': self.processed_foods
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        return str(output_file)


def main():
    """メイン処理"""
    import os

    print("🍽️ 手作業食材データ後処理システム")
    print("=" * 60)

    processor = ManualFoodsProcessor()

    # manual_work_50_foods.txtをパース
    manual_file = processor.data_dir / 'manual_work_50_foods.txt'
    print(f"📁 ファイル読み込み: {manual_file}")

    foods_data = processor.parse_manual_foods_file(str(manual_file))
    print(f"✅ {len(foods_data)}個の食材を抽出")

    # 各食材を処理
    print(f"\n🔄 食材の後処理実行中...")
    processed_count = 0
    skipped_count = 0

    for food_data in foods_data:
        processed_food = processor.process_food(food_data)
        if processed_food:
            processor.processed_foods.append(processed_food)
            processed_count += 1
        else:
            skipped_count += 1

    print(f"✅ 処理完了: {processed_count}個成功, {skipped_count}個スキップ")

    # 保存
    output_file = processor.save_processed_data()
    print(f"\n💾 保存完了: {output_file}")

    # サマリー表示
    print("\n" + "=" * 60)
    print("📊 処理結果サマリー")
    print("=" * 60)
    print(f"総食材数: {len(foods_data)}個")
    print(f"処理成功: {processed_count}個")
    print(f"スキップ: {skipped_count}個")

    # カテゴリ別集計
    categories = {}
    for food in processor.processed_foods:
        cat = food['category']
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1

    print(f"\n📂 カテゴリ別内訳:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: {count}個")


if __name__ == "__main__":
    main()
