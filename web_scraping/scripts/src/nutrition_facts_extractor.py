#!/usr/bin/env python3
"""
Nutrition Facts情報抽出コンポーネント
"""

import re
from typing import Dict, List, Optional, Any


class NutritionFactsExtractor:
    """Nutrition Facts Serving Size情報を抽出"""

    @staticmethod
    def extract_serving_size_info(
        raw_nutrition_data: List[str],
        food_name: Optional[str] = None,
        manual_loader: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Serving Size情報を抽出

        パターン:
        "Serving Size", "cup (128g)", "Amount per serving", "Calories", "457cals"

        Args:
            raw_nutrition_data: 生の栄養データリスト
            food_name: 食材名（マニュアルデータ検索用、オプション）
            manual_loader: ManualServingDataLoaderインスタンス（オプション）

        Returns:
            {
                "unit": "cup",
                "grams_per_unit": 128.0,
                "calories_per_unit": 457.0,
                "raw_sequence": [...],
                "source": "auto" or "manual"
            }
            または None (見つからない場合)
        """
        # まずマニュアルデータをチェック
        if food_name and manual_loader:
            manual_info = manual_loader.get_serving_info(food_name)
            if manual_info:
                return manual_info

        # 自動抽出
        if not raw_nutrition_data:
            return None

        for idx, item in enumerate(raw_nutrition_data):
            if not isinstance(item, str):
                continue

            # "Serving Size" を探す
            if item.strip() == "Serving Size":
                # 次の要素を確認（unit (Xg)パターン）
                if idx + 1 < len(raw_nutrition_data):
                    next_item = raw_nutrition_data[idx + 1]

                    # "cup (128g)" のようなパターンをマッチ
                    unit_pattern = r'^(.+?)\s*\((\d+(?:\.\d+)?)g\)$'
                    unit_match = re.match(unit_pattern, str(next_item))

                    if unit_match:
                        unit = unit_match.group(1).strip()
                        grams = float(unit_match.group(2))

                        # さらに"Amount per serving", "Calories", "Xcals"を確認
                        if idx + 4 < len(raw_nutrition_data):
                            if (raw_nutrition_data[idx + 2] == "Amount per serving" and
                                raw_nutrition_data[idx + 3] == "Calories"):

                                # "457cals" パターンをマッチ
                                cals_pattern = r'^(\d+(?:\.\d+)?)cals?$'
                                cals_match = re.match(cals_pattern, str(raw_nutrition_data[idx + 4]))

                                if cals_match:
                                    calories = float(cals_match.group(1))

                                    return {
                                        "unit": unit,
                                        "grams_per_unit": grams,
                                        "calories_per_unit": calories,
                                        "raw_sequence": [
                                            raw_nutrition_data[idx],
                                            raw_nutrition_data[idx + 1],
                                            raw_nutrition_data[idx + 2],
                                            raw_nutrition_data[idx + 3],
                                            raw_nutrition_data[idx + 4]
                                        ],
                                        "source": "auto"
                                    }

        return None


class NutrientExtractor:
    """個別栄養素の値を抽出"""

    # 栄養素名とその値のパターン定義
    NUTRIENT_PATTERNS = {
        # 主要栄養素 (g単位)
        'total_fat': ('Total Fat', r'^\d+(?:\.\d+)?g$'),
        'saturated_fat': ('Saturated Fat', r'^\d+(?:\.\d+)?g$'),
        'trans_fat': ('Trans Fat', r'^\d+(?:\.\d+)?g$'),
        'monounsaturated_fat': ('Monounsaturated Fat', r'^\d+(?:\.\d+)?g$'),
        'polyunsaturated_fat': ('Polyunsaturated Fat', r'^\d+(?:\.\d+)?g$'),

        'total_carbs': ('Total Carbs', r'^\d+(?:\.\d+)?g$'),
        'net_carbs': ('Net Carbs', r'^\d+(?:\.\d+)?g$'),
        'dietary_fiber': ('Dietary Fiber', r'^\d+(?:\.\d+)?g$'),
        'total_sugars': ('Total Sugars', r'^\d+(?:\.\d+)?g$'),
        'added_sugars': ('Added Sugars', r'^\d+(?:\.\d+)?g$'),

        'protein': ('Protein', r'^\d+(?:\.\d+)?g$'),
        'alcohol': ('Alcohol', r'^\d+(?:\.\d+)?g$'),

        # ミネラル・ビタミン (mg単位)
        'cholesterol': ('Cholesterol', r'^\d+(?:\.\d+)?mg$'),
        'sodium': ('Sodium', r'^\d+(?:\.\d+)?mg$'),
        'vitamin_c': ('Vitamin C', r'^\d+(?:\.\d+)?mg$'),
        'calcium': ('Calcium', r'^\d+(?:\.\d+)?mg$'),
        'iron': ('Iron', r'^\d+(?:\.\d+)?mg$'),
        'potassium': ('Potassium', r'^\d+(?:\.\d+)?mg$'),
        'caffeine': ('Caffeine', r'^\d+(?:\.\d+)?mg$'),

        # ビタミン (mcg単位)
        'vitamin_a': ('Vitamin A', r'^\d+(?:\.\d+)?mcg$'),
    }

    @staticmethod
    def extract_nutrient_value(
        raw_nutrition_data: List[str],
        nutrient_key: str
    ) -> Optional[float]:
        """
        指定された栄養素の値を抽出

        Args:
            raw_nutrition_data: 生の栄養データリスト
            nutrient_key: 栄養素キー ('total_fat', 'protein', etc.)

        Returns:
            栄養素の値 (float) または None (見つからない場合)
        """
        if nutrient_key not in NutrientExtractor.NUTRIENT_PATTERNS:
            return None

        nutrient_name, value_pattern = NutrientExtractor.NUTRIENT_PATTERNS[nutrient_key]

        for idx, item in enumerate(raw_nutrition_data):
            if not isinstance(item, str):
                continue

            # パターン1: 栄養素名の次に値がある
            if item.strip() == nutrient_name:
                if idx + 1 < len(raw_nutrition_data):
                    next_item = str(raw_nutrition_data[idx + 1])
                    if re.match(value_pattern, next_item):
                        # 数値部分を抽出
                        num_match = re.match(r'^(\d+(?:\.\d+)?)', next_item)
                        if num_match:
                            return float(num_match.group(1))

            # パターン2: "栄養素名 値" の形式 (例: "Total Fat 23.9g")
            combined_pattern = f'^{re.escape(nutrient_name)}\\s+({value_pattern[1:-1]})$'
            match = re.match(combined_pattern, item.strip())
            if match:
                # 数値部分を抽出
                num_match = re.match(r'^(\d+(?:\.\d+)?)', match.group(1))
                if num_match:
                    return float(num_match.group(1))

        return None

    @staticmethod
    def extract_all_nutrients(raw_nutrition_data: List[str]) -> Dict[str, Optional[float]]:
        """
        全ての栄養素を抽出

        Args:
            raw_nutrition_data: 生の栄養データリスト

        Returns:
            栄養素辞書 (見つからない場合はNone)
        """
        nutrients = {}

        for nutrient_key in NutrientExtractor.NUTRIENT_PATTERNS.keys():
            value = NutrientExtractor.extract_nutrient_value(
                raw_nutrition_data,
                nutrient_key
            )
            nutrients[nutrient_key] = value

        return nutrients


# 使用例
if __name__ == "__main__":
    # サンプルデータ
    sample_raw_data = [
        "Serving Size",
        "cup (128g)",
        "Amount per serving",
        "Calories",
        "457cals",
        "Total Fat",
        "0.1g",
        "Saturated Fat",
        "0g",
        "Total Carbs",
        "113g",
        "Dietary Fiber",
        "4g",
        "Protein",
        "0g",
        "Sodium",
        "0mg",
        "Calcium",
        "40mg"
    ]

    # Serving Size抽出
    serving_info = NutritionFactsExtractor.extract_serving_size_info(sample_raw_data)
    print("Serving Size情報:")
    if serving_info:
        print(f"  Unit: {serving_info['unit']}")
        print(f"  Grams per unit: {serving_info['grams_per_unit']}g")
        print(f"  Calories per unit: {serving_info['calories_per_unit']} kcal")
    else:
        print("  見つかりませんでした")

    print()

    # 全栄養素抽出
    nutrients = NutrientExtractor.extract_all_nutrients(sample_raw_data)
    print("栄養素:")
    for key, value in nutrients.items():
        if value is not None:
            print(f"  {key}: {value}")
