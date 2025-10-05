#!/usr/bin/env python3
"""
手作業で入力した46食材のデータをパースしてフォーマット化
processed_foods_20251001_125923.jsonと同じ形式に変換
"""
import json
import re
from pathlib import Path
from datetime import datetime


class ManualFoodFormatter:
    """手作業食材データのフォーマッター"""

    def __init__(self, manual_file_path: str):
        self.manual_file = Path(manual_file_path)
        self.formatted_foods = []

    def parse_manual_file(self):
        """手作業ファイルをパースして構造化"""
        with open(self.manual_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 各食材のブロックを分割
        blocks = content.split('=' * 80)

        for block in blocks:
            if not block.strip():
                continue

            # 食材名を抽出
            name_match = re.search(r'\d+\.\s+(.+?)(?=\n|$)', block)
            if not name_match:
                continue

            food_name = name_match.group(1).strip()

            # nanチェック
            if 'nan' in block.lower():
                print(f"⏭️  スキップ（nan）: {food_name}")
                continue

            # 栄養情報とserving情報を抽出
            nutrition_data = self._extract_nutrition(block, food_name)
            serving_data = self._extract_servings(block, food_name)

            if nutrition_data and serving_data:
                food_data = self._format_food_data(food_name, nutrition_data, serving_data)
                self.formatted_foods.append(food_data)
                print(f"✅ フォーマット完了: {food_name}")
            else:
                print(f"⚠️  不完全データ: {food_name} (栄養: {bool(nutrition_data)}, Serving: {bool(serving_data)})")

    def _extract_nutrition(self, block: str, food_name: str) -> dict:
        """栄養情報を抽出"""
        nutrition = {}

        # Serving Size
        serving_size_match = re.search(r'Serving Size\s+(.+?)\s*\((\d+)g\)', block)
        if serving_size_match:
            nutrition['serving_size'] = {
                'text': serving_size_match.group(1).strip(),
                'grams': float(serving_size_match.group(2))
            }

        # Calories (カンマ区切り対応)
        cal_match = re.search(r'Calories\s+([\d,]+)cals', block)
        if cal_match:
            nutrition['calories'] = float(cal_match.group(1).replace(',', ''))

        # Macros
        macros = {}

        # Total Fat
        fat_match = re.search(r'Total Fat\s+([\d.]+)g', block)
        if fat_match:
            macros['total_fat'] = {
                'value': float(fat_match.group(1)),
                'unit': 'g',
                'raw_text': f"Total Fat {fat_match.group(1)}g"
            }

        # Saturated Fat
        sat_fat_match = re.search(r'Saturated Fat\s+([\d.]+)g', block)
        if sat_fat_match:
            macros['saturated_fat'] = {
                'value': float(sat_fat_match.group(1)),
                'unit': 'g',
                'raw_text': f"Saturated Fat {sat_fat_match.group(1)}g"
            }

        # Trans Fat
        trans_fat_match = re.search(r'Trans Fat\s+([\d.]+)g', block)
        if trans_fat_match:
            macros['trans_fat'] = {
                'value': float(trans_fat_match.group(1)),
                'unit': 'g',
                'raw_text': f"Trans Fat {trans_fat_match.group(1)}g"
            }

        # Monounsaturated Fat
        mono_match = re.search(r'Monounsaturated Fat\s+([\d.]+)g', block)
        if mono_match:
            macros['monounsaturated_fat'] = {
                'value': float(mono_match.group(1)),
                'unit': 'g',
                'raw_text': f"Monounsaturated Fat {mono_match.group(1)}g"
            }

        # Polyunsaturated Fat
        poly_match = re.search(r'Polyunsaturated Fat\s+([\d.]+)g', block)
        if poly_match:
            macros['polyunsaturated_fat'] = {
                'value': float(poly_match.group(1)),
                'unit': 'g',
                'raw_text': f"Polyunsaturated Fat {poly_match.group(1)}g"
            }

        # Total Carbs
        carbs_match = re.search(r'Total Carbs\s+([\d.]+)g', block)
        if carbs_match:
            macros['total_carbs'] = {
                'value': float(carbs_match.group(1)),
                'unit': 'g',
                'raw_text': f"Total Carbs {carbs_match.group(1)}g"
            }

        # Dietary Fiber
        fiber_match = re.search(r'Dietary Fiber\s+([\d.]+)g', block)
        if fiber_match:
            macros['dietary_fiber'] = {
                'value': float(fiber_match.group(1)),
                'unit': 'g',
                'raw_text': f"Dietary Fiber {fiber_match.group(1)}g"
            }

        # Total Sugars
        sugar_match = re.search(r'Total Sugars\s+([\d.]+)g', block)
        if sugar_match:
            macros['total_sugars'] = {
                'value': float(sugar_match.group(1)),
                'unit': 'g',
                'raw_text': f"Total Sugars {sugar_match.group(1)}g"
            }

        # Protein
        protein_match = re.search(r'Protein\s+([\d.]+)g', block)
        if protein_match:
            macros['protein'] = {
                'value': float(protein_match.group(1)),
                'unit': 'g',
                'raw_text': f"Protein {protein_match.group(1)}g"
            }

        # Cholesterol
        chol_match = re.search(r'Cholesterol\s+([\d.]+)mg', block)
        if chol_match:
            macros['cholesterol'] = {
                'value': float(chol_match.group(1)),
                'unit': 'mg',
                'raw_text': f"Cholesterol {chol_match.group(1)}mg"
            }

        # Sodium
        sodium_match = re.search(r'Sodium\s+([\d,]+)mg', block)
        if sodium_match:
            sodium_val = float(sodium_match.group(1).replace(',', ''))
            macros['sodium'] = {
                'value': sodium_val,
                'unit': 'mg',
                'raw_text': f"Sodium {sodium_match.group(1)}mg"
            }

        nutrition['macros'] = macros

        # Micronutrients
        micros = {}

        # Vitamin A
        vita_match = re.search(r'Vitamin A\s+([\d.]+)mcg', block)
        if vita_match:
            micros['vitamin_a'] = {
                'value': float(vita_match.group(1)),
                'unit': 'mcg',
                'raw_text': f"Vitamin A {vita_match.group(1)}mcg"
            }

        # Vitamin C
        vitc_match = re.search(r'Vitamin C\s+([\d.]+)mg', block)
        if vitc_match:
            micros['vitamin_c'] = {
                'value': float(vitc_match.group(1)),
                'unit': 'mg',
                'raw_text': f"Vitamin C {vitc_match.group(1)}mg"
            }

        # Calcium
        calcium_match = re.search(r'Calcium\s+([\d.]+)mg', block)
        if calcium_match:
            micros['calcium'] = {
                'value': float(calcium_match.group(1)),
                'unit': 'mg',
                'raw_text': f"Calcium {calcium_match.group(1)}mg"
            }

        # Iron
        iron_match = re.search(r'Iron\s+([\d.]+)mg', block)
        if iron_match:
            micros['iron'] = {
                'value': float(iron_match.group(1)),
                'unit': 'mg',
                'raw_text': f"Iron {iron_match.group(1)}mg"
            }

        # Potassium
        potassium_match = re.search(r'Potassium\s+([\d,]+)mg', block)
        if potassium_match:
            potassium_val = float(potassium_match.group(1).replace(',', ''))
            micros['potassium'] = {
                'value': potassium_val,
                'unit': 'mg',
                'raw_text': f"Potassium {potassium_match.group(1)}mg"
            }

        nutrition['micros'] = micros

        return nutrition if nutrition.get('calories') is not None else None

    def _extract_servings(self, block: str, food_name: str) -> list:
        """Serving情報を抽出"""
        servings = []

        # "unit Xcals / Yg" パターンを抽出
        # 複数のパターンに対応（優先順位が重要）
        patterns = [
            # 括弧付きパターン: "cake (0.6 oz) 18cals / 17 g"
            r'([a-zA-Z\s]+\([^)]+\))\s+(\d+(?:,\d{3})*)cals\s+/\s+([\d.]+)\s*g',
            # 数字付きパターン: "0.25 tsp 0cals / 0.8 g", "100 gram 0cals / 100 g"
            r'([\d.]+\s+[a-zA-Z\s\.\-\(\),]+)\s+(\d+(?:,\d{3})*)cals\s+/\s+([\d.]+)\s*g',
            # 通常パターン: "cup 488cals / 128 g", "tbsp, ground 18cals / 5.8 g"
            r'([a-zA-Z\s\.\-\(\),]+)\s+(\d+(?:,\d{3})*)cals\s+/\s+([\d.]+)\s*g',
        ]

        seen_units = set()

        for pattern in patterns:
            for match in re.finditer(pattern, block):
                unit = match.group(1).strip()
                calories_str = match.group(2).replace(',', '')
                grams = float(match.group(3))
                calories = float(calories_str)

                # ユニット名をクリーニング
                unit_clean = unit.lower().strip()

                # 重複チェック
                if unit_clean in seen_units:
                    continue

                seen_units.add(unit_clean)

                # 数字で始まる場合の処理（0.25 tsp など）
                quantity_match = re.match(r'([\d.]+)\s+(.+)', unit)
                if quantity_match:
                    quantity = float(quantity_match.group(1))
                    base_unit = quantity_match.group(2).strip()

                    # 1単位あたりに正規化
                    if quantity > 0:
                        calories_per_unit = calories / quantity
                        grams_per_unit = grams / quantity
                        unit_display = base_unit
                    else:
                        continue
                else:
                    calories_per_unit = calories
                    grams_per_unit = grams
                    unit_display = unit

                servings.append({
                    'unit': unit_display,
                    'calories_per_unit': round(calories_per_unit, 1),
                    'grams_per_unit': round(grams_per_unit, 1),
                    'conversion_factor': round(grams_per_unit, 1),
                    'calories_per_gram': round(calories_per_unit / grams_per_unit, 4) if grams_per_unit > 0 else 0,
                    'display_text': f"1 {unit_display} ({round(grams_per_unit, 1)}g) = {round(calories_per_unit, 1)} kcal",
                    'source': 'manual_input'
                })

        # gramを最初に、その後アルファベット順
        servings.sort(key=lambda s: ("0_gram" if s['unit'].lower() == "gram" else f"1_{s['unit'].lower()}"))

        return servings

    def _format_food_data(self, food_name: str, nutrition: dict, servings: list) -> dict:
        """processed_foods形式にフォーマット"""

        # food_idを生成（既存の最大IDに追加）
        food_id = f"food_manual_{len(self.formatted_foods) + 1:04d}"

        # カテゴリを推定（簡易版）
        category = self._estimate_category(food_name)

        # serving_sizeから基本情報を取得
        serving_info = nutrition.get('serving_size', {})

        formatted = {
            'food_id': food_id,
            'food_name': food_name,
            'category': category,
            'essential_nutrition': {
                'calories': {
                    'value': nutrition.get('calories', 0),
                    'unit': 'kcal',
                    'source': 'manual_input'
                },
                'serving_size': {
                    'value': 1.0,
                    'unit': serving_info.get('text', 'serving'),
                    'grams': serving_info.get('grams', servings[0]['grams_per_unit'] if servings else 0),
                    'calories': nutrition.get('calories', 0),
                    'raw_text': f"{serving_info.get('text', 'serving')} {nutrition.get('calories', 0)}cals"
                },
                'macros': nutrition.get('macros', {}),
                'micronutrients': nutrition.get('micros', {}),
                'serving_info': {
                    'unit': serving_info.get('text', servings[0]['unit'] if servings else 'serving'),
                    'grams': serving_info.get('grams', servings[0]['grams_per_unit'] if servings else 0)
                }
            },
            'detailed_nutrition': nutrition.get('micros', {}),
            'serving_options': servings,
            'data_quality': {
                'completeness_score': self._calculate_completeness(nutrition, servings),
                'source': 'manual_input',
                'last_updated': datetime.now().isoformat()
            }
        }

        return formatted

    def _estimate_category(self, food_name: str) -> str:
        """食材名からカテゴリを推定"""
        name_lower = food_name.lower()

        if any(word in name_lower for word in ['salt', 'seasoning', 'spice', 'paprika', 'cardamom', 'cajun', 'italian', 'sumac', "za'atar"]):
            return 'Spices & Herbs'
        elif any(word in name_lower for word in ['yeast', 'cornstarch']):
            return 'Grains & Grain Products'
        elif any(word in name_lower for word in ['okra']):
            return 'Vegetables'
        elif any(word in name_lower for word in ['bass']):
            return 'Seafood'
        elif any(word in name_lower for word in ['hummus', 'natto']):
            return 'Beans & Peas'
        elif any(word in name_lower for word in ['milk', 'goat']):
            return 'Dairy, Dairy Substitutes & Egg'
        elif any(word in name_lower for word in ['allulose', 'erythritol', 'honey', 'molasses']):
            return 'Sweets & Sweeteners'
        elif any(word in name_lower for word in ['sauce', 'guacamole', 'salsa', 'chili garlic']):
            return 'Condiments, Dressings & Sauces'
        elif any(word in name_lower for word in ['soda', 'cola', 'ginger ale', 'tonic', 'champagne', 'cognac', 'liqueur', 'martini', 'water', 'ice', 'seltzer']):
            return 'Beverages'
        elif any(word in name_lower for word in ['jelly', 'jellies']):
            return 'Sweets & Sweeteners'
        elif any(word in name_lower for word in ['watermelon', 'fruit']):
            return 'Fruits'
        elif any(word in name_lower for word in ['flaxseed', 'walnut', 'nut', 'seed']):
            return 'Nuts, Seeds & Nut Products'
        elif 'olive' in name_lower:
            return 'Fats & Oils'
        else:
            return 'Other'

    def _calculate_completeness(self, nutrition: dict, servings: list) -> float:
        """データ完全性スコアを計算"""
        score = 0.0

        # 栄養情報
        if nutrition.get('calories') is not None:
            score += 0.2
        if nutrition.get('macros'):
            score += 0.3 * (len(nutrition['macros']) / 10)  # 最大10項目想定
        if nutrition.get('micros'):
            score += 0.2 * (len(nutrition['micros']) / 5)   # 最大5項目想定

        # Serving情報
        if servings:
            score += 0.3 * min(len(servings) / 7, 1.0)  # 7個以上で満点

        return round(min(score, 1.0), 3)

    def save_formatted_data(self, output_path: str):
        """フォーマット済みデータを保存"""
        output = {
            'metadata': {
                'version': '1.0_manual',
                'processed_at': datetime.now().isoformat(),
                'total_foods': len(self.formatted_foods),
                'source': 'manual_input_from_txt',
                'processing_notes': '手作業で入力した46食材をフォーマット化'
            },
            'foods': self.formatted_foods
        }

        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n✅ フォーマット済みデータ保存: {output_file}")
        print(f"📊 総食材数: {len(self.formatted_foods)}個")


def main():
    print("🍽️ 手作業食材データのフォーマット化")
    print("=" * 60)

    # 入力・出力パス
    manual_file = "data/manual_work_50_foods.txt"
    output_file = "processed_data/manual_foods_formatted_46.json"

    # フォーマッター実行
    formatter = ManualFoodFormatter(manual_file)
    formatter.parse_manual_file()

    # 保存
    formatter.save_formatted_data(output_file)

    # サマリー
    print(f"\n📋 カテゴリ別内訳:")
    from collections import Counter
    categories = Counter([f['category'] for f in formatter.formatted_foods])
    for cat, count in categories.most_common():
        print(f"  {cat}: {count}個")


if __name__ == "__main__":
    main()
