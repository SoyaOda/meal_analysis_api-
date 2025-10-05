#!/usr/bin/env python3
"""
改善されたサービング情報抽出ロジック
個別要素から意味のあるサービング情報を再構築
"""

import re
from typing import List, Dict, Any

class ImprovedServingExtractor:
    """改善されたサービング情報抽出クラス"""

    def __init__(self):
        self.unit_keywords = [
            'cup', 'tablespoon', 'tbsp', 'teaspoon', 'tsp',
            'gram', 'g', 'ml', 'oz', 'ounce', 'serving',
            'piece', 'slice', 'medium', 'large', 'small'
        ]

    def extract_serving_info_from_raw_data(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """生データから実際のサービング情報を抽出"""

        # 1. 基本情報の抽出
        serving_size_info = self._extract_serving_size_info(raw_data)

        # 2. Amount eaten ドロップダウン情報の抽出
        dropdown_units = self._extract_dropdown_units(raw_data)

        # 3. 重量・カロリー情報の抽出
        weight_calorie_info = self._extract_weight_calorie_info(raw_data)

        # 4. 組み合わせてサービング情報を構築
        serving_options = self._build_serving_options(
            serving_size_info, dropdown_units, weight_calorie_info
        )

        return serving_options

    def _extract_serving_size_info(self, raw_data: List[Any]) -> Dict[str, Any]:
        """基本のServing Size情報を抽出"""
        serving_info = {}

        data_str = ' '.join(str(item) for item in raw_data)

        # "Serving Size cup (128g)" パターンを探す
        serving_size_pattern = r'Serving Size\s+([a-zA-Z\s]+?)\s*\((\d+(?:\.\d+)?)g?\)'
        match = re.search(serving_size_pattern, data_str)

        if match:
            unit = match.group(1).strip()
            weight = float(match.group(2))
            serving_info = {
                'base_unit': unit,
                'base_weight_g': weight,
                'pattern': 'serving_size'
            }

        return serving_info

    def _extract_dropdown_units(self, raw_data: List[Any]) -> List[str]:
        """Amount eaten ドロップダウンの単位を抽出"""
        dropdown_units = []

        # Amount eaten の近くにある単位を探す
        found_amount_eaten = False
        collection_window = 0

        for i, item in enumerate(raw_data):
            item_str = str(item).strip().lower()

            # Amount eaten の発見
            if 'amount eaten' in item_str:
                found_amount_eaten = True
                collection_window = 0
                continue

            # Amount eaten の後で単位語を探す（10要素以内）
            if found_amount_eaten:
                collection_window += 1

                # 単位語の判定
                for unit in self.unit_keywords:
                    if unit.lower() == item_str:
                        dropdown_units.append(item_str)
                        print(f"  🔍 単位発見: {item_str} (position {i})")
                        break

                # "3 more servings" のような終了パターン
                if 'more serving' in item_str:
                    print(f"  🛑 終了パターン検出: {item_str}")
                    break

                # 10個以上離れたら終了
                if collection_window > 10:
                    print(f"  ⏰ 収集ウィンドウ終了 (position {i})")
                    break

        print(f"  📊 ドロップダウン単位: {dropdown_units}")
        return dropdown_units

    def _extract_weight_calorie_info(self, raw_data: List[Any]) -> Dict[str, Any]:
        """重量とカロリー情報を抽出"""
        info = {}

        data_str = ' '.join(str(item) for item in raw_data)

        # "488 cals" パターン
        calorie_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*cals?'
        calorie_matches = re.findall(calorie_pattern, data_str)

        # "Weight 128 g" パターン
        weight_pattern = r'Weight\s+(\d+(?:\.\d+)?)\s*g'
        weight_match = re.search(weight_pattern, data_str)

        if calorie_matches:
            # 最初の（通常は主要な）カロリー値を使用
            main_calories = float(calorie_matches[0].replace(',', ''))
            info['main_calories'] = main_calories

        if weight_match:
            main_weight = float(weight_match.group(1))
            info['main_weight_g'] = main_weight

            # カロリー密度を計算
            if 'main_calories' in info:
                info['calories_per_gram'] = info['main_calories'] / main_weight

        return info

    def _build_serving_options(self, serving_size_info: Dict, dropdown_units: List[str],
                             weight_calorie_info: Dict) -> List[Dict[str, Any]]:
        """サービング情報を組み合わせて構築"""
        serving_options = []

        # 基本情報があるかチェック
        if not weight_calorie_info.get('calories_per_gram'):
            return serving_options

        base_unit = serving_size_info.get('base_unit', 'cup')
        base_weight = serving_size_info.get('base_weight_g', 128)
        base_calories = weight_calorie_info.get('main_calories', 488)
        calories_per_gram = weight_calorie_info['calories_per_gram']

        # 1. 基本単位を追加
        serving_options.append({
            'unit': base_unit,
            'calories_per_unit': base_calories,
            'grams_per_unit': base_weight,
            'conversion_factor': base_weight,
            'calories_per_gram': round(calories_per_gram, 4),
            'display_text': f"1 {base_unit} ({base_weight}g) = {base_calories} kcal",
            'source': 'serving_size_info'
        })

        # 2. 標準変換単位を追加
        unit_conversions = {
            'tablespoon': 8,      # 1 tablespoon ≈ 8g (flour)
            'tbsp': 8,
            'teaspoon': 2.7,      # 1 teaspoon ≈ 2.7g (flour)
            'tsp': 2.7,
            'gram': 1,
            'g': 1,
            'ml': 0.5,            # cornstarch density ≈ 0.5g/ml
            'oz': 28.3,           # 1 oz = 28.3g
            'ounce': 28.3
        }

        # ドロップダウンから見つかった単位で標準変換を適用
        for unit in dropdown_units:
            unit_clean = unit.lower().strip()
            if unit_clean in unit_conversions and unit_clean != base_unit.lower():
                unit_weight = unit_conversions[unit_clean]
                unit_calories = round(unit_weight * calories_per_gram, 1)

                serving_options.append({
                    'unit': unit_clean,
                    'calories_per_unit': unit_calories,
                    'grams_per_unit': unit_weight,
                    'conversion_factor': unit_weight,
                    'calories_per_gram': round(calories_per_gram, 4),
                    'display_text': f"1 {unit_clean} ({unit_weight}g) = {unit_calories} kcal",
                    'source': 'standard_conversion'
                })

        # 3. 重複削除とソート
        unique_options = []
        seen_units = set()

        for option in serving_options:
            unit_key = option['unit'].lower()
            if unit_key not in seen_units:
                seen_units.add(unit_key)
                unique_options.append(option)

        # gram を最初に、その後アルファベット順
        def sort_key(option):
            unit = option['unit'].lower()
            if unit in ['gram', 'g']:
                return '0_gram'
            return f'1_{unit}'

        unique_options.sort(key=sort_key)

        return unique_options

    def test_with_cornstarch_data(self):
        """Cornstarchのサンプルデータでテスト"""

        # サンプル生データ（実際の収集結果を模擬）
        sample_raw_data = [
            'Cornstarch', '488 cals', '488', 'cals', 'Amount eaten', 'cup',
            'tablespoon', 'teaspoon', 'gram', 'ml', '3 more servings',
            'Weight', '128', 'g', 'Food Grade', 'D+',
            'Serving Size', 'cup (128g)', 'Amount per serving', 'Calories', '488cals'
        ]

        print("🧪 Cornstarchデータでテスト実行")
        print(f"入力データ: {len(sample_raw_data)}個の要素")

        extracted_options = self.extract_serving_info_from_raw_data(sample_raw_data)

        print(f"\n✅ 抽出されたサービングオプション: {len(extracted_options)}個")
        for i, option in enumerate(extracted_options, 1):
            print(f"  {i}. {option['display_text']} (出典: {option['source']})")

        return extracted_options

if __name__ == "__main__":
    extractor = ImprovedServingExtractor()

    # テスト実行
    results = extractor.test_with_cornstarch_data()

    print(f"\n🎯 結果: {'✅成功' if len(results) >= 3 else '❌失敗'}")
    print(f"期待: 3個以上のサービングオプション")
    print(f"実際: {len(results)}個のサービングオプション")