#!/usr/bin/env python3
"""
包括的栄養データの表示・アクセス用スクリプト
"""

import json
from typing import Dict, List, Any, Optional

class NutritionViewer:
    """栄養情報の表示・アクセス用クラス"""

    def __init__(self, data_file: str):
        """データファイルを読み込み"""
        with open(data_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        self.food_name = self.data['food_info']['name']
        self.available_units = list(self.data['nutrition_by_unit'].keys())
        self.available_nutrients = self.data['available_nutrients']

    def show_food_info(self):
        """食材基本情報を表示"""
        info = self.data['food_info']
        base_ref = self.data['base_reference']

        print(f"🍽️  食材名: {info['name']}")
        print(f"⭐ Food Grade: {info['food_grade']}")
        print(f"📏 基準量: {base_ref['amount']}{base_ref['unit']} ({base_ref['description']})")
        print(f"📅 取得日時: {info['scraped_at']}")

    def show_available_units(self):
        """利用可能な単位を表示"""
        print(f"\n📐 利用可能な単位:")
        for i, unit in enumerate(self.available_units, 1):
            weight = self.data['nutrition_by_unit'][unit]['weight_g']
            print(f"  {i}. {unit} ({weight}g)")

    def show_available_nutrients(self):
        """利用可能な栄養素を表示"""
        print(f"\n🥗 利用可能な栄養素 ({len(self.available_nutrients)}個):")
        for i, nutrient in enumerate(self.available_nutrients, 1):
            print(f"  {i:2d}. {nutrient}")

    def get_nutrition_by_unit(self, unit: str) -> Optional[Dict]:
        """指定された単位での栄養情報を取得"""
        if unit not in self.available_units:
            print(f"❌ 単位 '{unit}' は利用できません")
            print(f"利用可能な単位: {', '.join(self.available_units)}")
            return None

        return self.data['nutrition_by_unit'][unit]

    def show_nutrition_by_unit(self, unit: str):
        """指定された単位での全栄養素を表示"""
        unit_data = self.get_nutrition_by_unit(unit)
        if not unit_data:
            return

        print(f"\n📊 {self.food_name} - {unit} ({unit_data['weight_g']}g) あたりの栄養素:")
        print("=" * 80)

        nutrients = unit_data['nutrients']

        # カテゴリ別に整理して表示
        categories = {
            '🔥 エネルギー': ['calories'],
            '🥩 タンパク質': ['protein'],
            '🧈 脂質': ['total_fat', 'saturated_fat', 'trans_fat', 'monounsaturated_fat', 'polyunsaturated_fat'],
            '🍞 炭水化物': ['total_carbs', 'net_carbs', 'dietary_fiber', 'total_sugars', 'added_sugars'],
            '🧂 ミネラル': ['sodium', 'calcium', 'iron', 'potassium'],
            '🍊 ビタミン': ['vitamin_c']
        }

        for category, nutrient_list in categories.items():
            category_nutrients = [n for n in nutrient_list if n in nutrients]
            if category_nutrients:
                print(f"\n{category}")
                for nutrient in category_nutrients:
                    info = nutrients[nutrient]
                    print(f"  {nutrient:20s}: {info['display']:>10s}")

    def compare_units(self, nutrients: List[str]):
        """指定された栄養素について各単位での値を比較表示"""
        print(f"\n🔍 栄養素比較: {', '.join(nutrients)}")
        print("=" * 100)

        # ヘッダー
        header = "Unit".ljust(12)
        for nutrient in nutrients:
            header += f"{nutrient[:15]:>16s}"
        print(header)
        print("-" * 100)

        # 各単位の値
        for unit in self.available_units:
            unit_data = self.data['nutrition_by_unit'][unit]
            row = f"{unit}".ljust(12)

            for nutrient in nutrients:
                if nutrient in unit_data['nutrients']:
                    value = unit_data['nutrients'][nutrient]['display']
                    row += f"{value:>16s}"
                else:
                    row += f"{'N/A':>16s}"

            print(row)

    def get_nutrient_value(self, nutrient: str, unit: str) -> Optional[Dict]:
        """特定の栄養素の特定単位での値を取得"""
        unit_data = self.get_nutrition_by_unit(unit)
        if not unit_data:
            return None

        if nutrient not in unit_data['nutrients']:
            print(f"❌ 栄養素 '{nutrient}' は利用できません")
            return None

        return unit_data['nutrients'][nutrient]

    def search_nutrients(self, keyword: str) -> List[str]:
        """栄養素名をキーワード検索"""
        matches = []
        for nutrient in self.available_nutrients:
            if keyword.lower() in nutrient.lower():
                matches.append(nutrient)
        return matches

def main():
    """メイン関数 - インタラクティブな使用例"""
    import sys
    import glob

    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        # 最新のcomprehensive_nutritionファイルを使用
        files = glob.glob("web_scraping/data/comprehensive_nutrition_*.json")
        if files:
            data_file = max(files)
        else:
            print("❌ データファイルが見つかりません")
            sys.exit(1)

    print(f"📂 データファイル: {data_file}")

    viewer = NutritionViewer(data_file)

    # 基本情報表示
    viewer.show_food_info()
    viewer.show_available_units()
    viewer.show_available_nutrients()

    # サンプル表示
    print(f"\n" + "="*80)
    print("📋 サンプル表示")
    print(f"="*80)

    # 1 cupあたり
    viewer.show_nutrition_by_unit('cup')

    # 100gあたり（gramを100倍）
    print(f"\n📊 参考: 100gあたりの栄養素:")
    print("=" * 50)
    gram_data = viewer.get_nutrition_by_unit('gram')
    if gram_data:
        for nutrient, info in list(gram_data['nutrients'].items())[:10]:
            value_per_100g = info['value'] * 100
            unit = info['unit']
            print(f"  {nutrient:20s}: {value_per_100g:.1f}{unit}")

    # 比較表示例
    print(f"\n")
    viewer.compare_units(['calories', 'protein', 'total_fat', 'total_carbs'])

if __name__ == "__main__":
    main()