#!/usr/bin/env python3
"""
マニュアルServing Sizeデータの読み込み
"""

import re
from typing import Dict, Optional


class ManualServingDataLoader:
    """nutrition_failure_foods.txtからマニュアルServing Sizeデータを読み込み"""

    def __init__(self, manual_data_path: str = 'important_data/nutrition_failure_foods.txt'):
        """
        Args:
            manual_data_path: マニュアルデータファイルのパス
        """
        self.manual_data_path = manual_data_path
        self.manual_data = self._load_manual_data()

    def _load_manual_data(self) -> Dict[str, Dict]:
        """
        マニュアルデータを読み込み

        Returns:
            {
                "Chicken fat, cup\n1,845cals": {
                    "unit": "cup",
                    "grams": 205.0,
                    "calories": 1845.0
                },
                ...
            }
        """
        manual_data = {}

        try:
            with open(self.manual_data_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            current_food_name = None
            current_serving_size = None

            for line in lines:
                line = line.rstrip()

                # 食材名パターン（数字で始まる行）
                food_match = re.match(r'^\s*\d+\.\s+(.+)$', line)
                if food_match:
                    food_name_part1 = food_match.group(1)
                    current_food_name = food_name_part1
                    current_serving_size = None
                    continue

                # カロリー行（前の行に続く）
                if current_food_name and re.match(r'^\d+(?:,\d+)?cals$', line):
                    current_food_name = current_food_name + '\n' + line
                    continue

                # Serving Sizeパターン
                serving_match = re.match(r'^Serving Size\s+(.+?)\s*\((\d+(?:\.\d+)?)g\)$', line)
                if serving_match and current_food_name:
                    unit = serving_match.group(1).strip()
                    grams = float(serving_match.group(2))

                    # カロリーを抽出
                    cal_match = re.search(r'(\d+(?:,\d+)?(?:\.\d+)?)cals', current_food_name)
                    calories = None
                    if cal_match:
                        calories = float(cal_match.group(1).replace(',', ''))

                    manual_data[current_food_name] = {
                        'unit': unit,
                        'grams': grams,
                        'calories': calories
                    }

                    current_serving_size = line
                    continue

                # "None" または除外指示
                if line.strip() in ['None', '除外']:
                    current_food_name = None
                    current_serving_size = None
                    continue

                # "同様の内容なので除外" パターン
                if '同様の内容' in line or '除外' in line:
                    current_food_name = None
                    current_serving_size = None
                    continue

        except FileNotFoundError:
            # ファイルがない場合は空の辞書を返す
            pass

        return manual_data

    def get_serving_info(self, food_name: str) -> Optional[Dict]:
        """
        食材名からServing Size情報を取得

        Args:
            food_name: 食材名（改行含む）

        Returns:
            {
                "unit": "cup",
                "grams_per_unit": 205.0,
                "calories_per_unit": 1845.0,
                "source": "manual"
            }
            または None
        """
        if food_name in self.manual_data:
            data = self.manual_data[food_name]
            return {
                'unit': data['unit'],
                'grams_per_unit': data['grams'],
                'calories_per_unit': data['calories'],
                'source': 'manual'
            }
        return None

    def get_all_food_names(self):
        """登録されている全ての食材名を取得"""
        return list(self.manual_data.keys())


class ManualServingConversionLoader:
    """serving_conversion_failure_foods.txtからマニュアルServing変換データを読み込み"""

    def __init__(self, manual_data_path: str = 'important_data/serving_conversion_failure_foods.txt'):
        """
        Args:
            manual_data_path: マニュアル変換データファイルのパス
        """
        self.manual_data_path = manual_data_path
        self.manual_data = self._load_manual_conversion_data()

    def _load_manual_conversion_data(self) -> Dict[str, list]:
        """
        マニュアルServing変換データを読み込み

        Returns:
            {
                "Baker's yeast compressed, cake (0.6 oz)\n18cals": [
                    {"unit": "cake (0.6 oz)", "calories": 18.0, "grams": 17.0},
                    {"unit": "gram", "calories": 1.0, "grams": 1.0},
                    ...
                ],
                ...
            }
        """
        manual_data = {}

        try:
            with open(self.manual_data_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            current_food_name = None
            current_conversions = []

            for line in lines:
                line = line.rstrip()

                # "入力例"セクション以降は無視
                if '入力例' in line:
                    break

                # 食材名パターン（数字で始まる行）
                food_match = re.match(r'^\s*\d+\.\s+(.+)$', line)
                if food_match:
                    # 前の食材データを保存
                    if current_food_name and current_conversions:
                        manual_data[current_food_name] = current_conversions

                    food_name_part1 = food_match.group(1)
                    current_food_name = food_name_part1
                    current_conversions = []
                    continue

                # カロリー行（前の行に続く）
                if current_food_name and re.match(r'^\d+(?:,\d+)?cals$', line):
                    current_food_name = current_food_name + '\n' + line
                    continue

                # "Select Serving" 行はスキップ
                if line.strip() == 'Select Serving':
                    continue

                # Serving変換パターン: "unit XXXcals / YYYg"
                conversion_match = re.match(
                    r'^(.+?)\s+(\d+(?:,\d+)?(?:\.\d+)?)cals?\s*/\s+(\d+(?:\.\d+)?)\s*g$',
                    line
                )
                if conversion_match and current_food_name:
                    unit = conversion_match.group(1).strip()
                    calories = float(conversion_match.group(2).replace(',', ''))
                    grams = float(conversion_match.group(3))

                    current_conversions.append({
                        'unit': unit,
                        'calories': calories,
                        'grams': grams,
                        'raw_text': line
                    })
                    continue

                # 区切り線 "---" で1つの食材終了
                if line.strip() == '---':
                    if current_food_name and current_conversions:
                        manual_data[current_food_name] = current_conversions
                    current_food_name = None
                    current_conversions = []
                    continue

                # "None" または除外指示
                if line.strip() in ['None', '除外', 'Web情報なし']:
                    current_food_name = None
                    current_conversions = []
                    continue

            # 最後の食材データを保存
            if current_food_name and current_conversions:
                manual_data[current_food_name] = current_conversions

        except FileNotFoundError:
            # ファイルがない場合は空の辞書を返す
            pass

        return manual_data

    def get_conversion_info(self, food_name: str) -> Optional[list]:
        """
        食材名からServing変換情報を取得

        Args:
            food_name: 食材名（改行含む）

        Returns:
            [
                {"unit": "cake (0.6 oz)", "calories": 18.0, "grams": 17.0},
                {"unit": "gram", "calories": 1.0, "grams": 1.0},
                ...
            ]
            または None
        """
        return self.manual_data.get(food_name)

    def get_all_food_names(self):
        """登録されている全ての食材名を取得"""
        return list(self.manual_data.keys())


# テスト
if __name__ == "__main__":
    print("📋 マニュアルデータ読み込みテスト")
    print("=" * 80)
    print()

    # 1. Serving Size データテスト
    print("1️⃣  ManualServingDataLoader (Serving Size)")
    print("-" * 80)
    loader = ManualServingDataLoader()
    print(f"登録食材数: {len(loader.manual_data)}個")
    print()

    # サンプル表示
    print("サンプル（最初の3個）:")
    for i, (food_name, data) in enumerate(list(loader.manual_data.items())[:3], 1):
        print(f"{i}. {food_name.replace(chr(10), ' ')}")
        print(f"   Unit: {data['unit']}, Grams: {data['grams']}g, Calories: {data['calories']} kcal")
    print()

    # 2. Serving Conversion データテスト
    print("2️⃣  ManualServingConversionLoader (Serving Conversions)")
    print("-" * 80)
    conversion_loader = ManualServingConversionLoader()
    print(f"登録食材数: {len(conversion_loader.manual_data)}個")
    print()

    # サンプル表示
    print("サンプル（最初の3個）:")
    for i, (food_name, conversions) in enumerate(list(conversion_loader.manual_data.items())[:3], 1):
        print(f"{i}. {food_name.replace(chr(10), ' ')}")
        print(f"   変換数: {len(conversions)}種類")
        for conv in conversions[:3]:
            print(f"     • {conv['unit']:20s} = {conv['grams']:6.1f}g ({conv['calories']:6.1f} kcal)")
    print()

    # 検索テスト
    test_food = "Baker's yeast compressed, cake (0.6 oz)\n18cals"
    conversions = conversion_loader.get_conversion_info(test_food)
    if conversions:
        print("検索テスト:")
        print(f"  食材: {test_food.replace(chr(10), ' ')}")
        print(f"  変換情報:")
        for conv in conversions:
            print(f"    • {conv['unit']:20s} = {conv['grams']:6.1f}g ({conv['calories']:6.1f} kcal)")
