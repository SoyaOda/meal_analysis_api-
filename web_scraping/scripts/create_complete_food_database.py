#!/usr/bin/env python3
"""
完全な食材データベース作成
Nutrition情報とServing変換情報の両方を含む食材のみを抽出
"""

import json
from pathlib import Path
from datetime import datetime


def main():
    print("🍽️  完全食材データベース作成")
    print("=" * 80)

    # Nutrition データ読み込み
    nutrition_file = Path('important_data/complete_nutrition_1185_foods.json')
    with open(nutrition_file, 'r', encoding='utf-8') as f:
        nutrition_data = json.load(f)

    # Serving変換データ読み込み
    serving_file = Path('important_data/serving_conversions_1188_foods.json')
    with open(serving_file, 'r', encoding='utf-8') as f:
        serving_data = json.load(f)

    print(f"📊 Nutrition データ: {len(nutrition_data['nutrition_data'])}食材")
    print(f"📊 Serving変換データ: {len(serving_data['serving_conversions'])}食材")
    print()

    # 食材名をキーとした辞書作成
    nutrition_dict = {item['food_name']: item for item in nutrition_data['nutrition_data']}
    serving_dict = {item['food_name']: item for item in serving_data['serving_conversions']}

    # 両方に存在する食材のみを抽出
    complete_foods = []
    nutrition_only_details = []
    serving_only_details = []

    # Nutrition データを基準に統合
    for food_name, nutrition_item in nutrition_dict.items():
        if food_name in serving_dict:
            serving_item = serving_dict[food_name]

            # 統合データ構築
            complete_food = {
                'sequence': nutrition_item['sequence'],
                'food_name': food_name,
                'catalog_category': nutrition_item['catalog_category'],

                # Serving Size情報
                'serving_info': nutrition_item['serving_info'],

                # Nutrition情報
                'nutrition': {
                    'essential_nutrients': nutrition_item['essential_nutrients'],
                    'all_nutrients': nutrition_item['all_nutrients'],
                    'total_nutrients_found': nutrition_item['total_nutrients_found']
                },

                # Serving変換情報
                'serving_conversions': {
                    'base_unit': serving_item['base_unit'],
                    'conversions': serving_item['conversions'],
                    'total_conversions': serving_item['total_conversions'],
                    'source': serving_item.get('source', 'auto')
                },

                # データソース情報
                'data_sources': {
                    'nutrition_source': nutrition_item['serving_info'].get('source', 'auto'),
                    'serving_conversion_source': serving_item.get('source', 'auto')
                }
            }

            complete_foods.append(complete_food)
        else:
            # Nutritionのみ（Serving変換なし）
            nutrition_only_details.append({
                'sequence': nutrition_item['sequence'],
                'food_name': food_name,
                'catalog_category': nutrition_item['catalog_category'],
                'reason': 'No serving conversion data available',
                'has_nutrition': True,
                'has_serving_conversion': False,
                'nutrition_info': {
                    'serving_info': nutrition_item['serving_info'],
                    'total_nutrients_found': nutrition_item['total_nutrients_found']
                }
            })

    # Servingデータのみに存在する食材を確認
    for food_name in serving_dict.keys():
        if food_name not in nutrition_dict:
            serving_item = serving_dict[food_name]
            serving_only_details.append({
                'sequence': serving_item['sequence'],
                'food_name': food_name,
                'catalog_category': serving_item['catalog_category'],
                'reason': 'No nutrition data available (failed nutrition extraction)',
                'has_nutrition': False,
                'has_serving_conversion': True,
                'serving_conversion_info': {
                    'base_unit': serving_item['base_unit'],
                    'total_conversions': serving_item['total_conversions'],
                    'source': serving_item.get('source', 'auto')
                }
            })

    print("=" * 80)
    print("【統合結果】")
    print("=" * 80)
    print(f"✅ 完全データ: {len(complete_foods)}食材 (Nutrition + Serving変換)")
    print(f"⚠️  Nutritionのみ: {len(nutrition_only_details)}食材")
    print(f"⚠️  Serving変換のみ: {len(serving_only_details)}食材")
    print()

    # データソース統計
    auto_nutrition_count = sum(1 for f in complete_foods if f['data_sources']['nutrition_source'] == 'auto')
    manual_nutrition_count = sum(1 for f in complete_foods if f['data_sources']['nutrition_source'] == 'manual')
    auto_serving_count = sum(1 for f in complete_foods if f['data_sources']['serving_conversion_source'] == 'auto')
    manual_serving_count = sum(1 for f in complete_foods if f['data_sources']['serving_conversion_source'] == 'manual')

    print("=" * 80)
    print("【データソース統計】")
    print("=" * 80)
    print(f"Nutrition情報:")
    print(f"  - 自動抽出: {auto_nutrition_count}食材")
    print(f"  - マニュアル: {manual_nutrition_count}食材")
    print()
    print(f"Serving変換情報:")
    print(f"  - 自動抽出: {auto_serving_count}食材")
    print(f"  - マニュアル: {manual_serving_count}食材")
    print()

    # 栄養素統計
    all_nutrients = set()
    for food in complete_foods:
        all_nutrients.update(food['nutrition']['all_nutrients'].keys())

    print("=" * 80)
    print("【栄養素統計】")
    print("=" * 80)
    print(f"栄養素の種類: {len(all_nutrients)}種類")
    print(f"平均栄養素数: {sum(f['nutrition']['total_nutrients_found'] for f in complete_foods) / len(complete_foods):.1f}種類/食材")
    print()

    # Serving変換統計
    all_units = set()
    for food in complete_foods:
        for conv in food['serving_conversions']['conversions']:
            all_units.add(conv['unit'])

    print("=" * 80)
    print("【Serving変換統計】")
    print("=" * 80)
    print(f"Unit種類: {len(all_units)}種類")
    print(f"平均変換数: {sum(f['serving_conversions']['total_conversions'] for f in complete_foods) / len(complete_foods):.1f}種類/食材")
    print()

    # 保存データ構築
    output_data = {
        'database_summary': {
            'timestamp': datetime.now().isoformat(),
            'total_foods': len(complete_foods),
            'nutrition_source_file': str(nutrition_file),
            'serving_source_file': str(serving_file),
            'data_quality': {
                'complete_foods': len(complete_foods),
                'nutrition_only': len(nutrition_only_details),
                'serving_only': len(serving_only_details)
            },
            'data_sources': {
                'nutrition': {
                    'auto': auto_nutrition_count,
                    'manual': manual_nutrition_count
                },
                'serving_conversions': {
                    'auto': auto_serving_count,
                    'manual': manual_serving_count
                }
            },
            'statistics': {
                'total_nutrients_found': len(all_nutrients),
                'avg_nutrients_per_food': sum(f['nutrition']['total_nutrients_found'] for f in complete_foods) / len(complete_foods),
                'total_units_found': len(all_units),
                'avg_conversions_per_food': sum(f['serving_conversions']['total_conversions'] for f in complete_foods) / len(complete_foods)
            }
        },
        'foods': complete_foods,
        'excluded_foods': {
            'nutrition_only': nutrition_only_details,
            'serving_only': serving_only_details,
            'total_excluded': len(nutrition_only_details) + len(serving_only_details)
        }
    }

    # JSON保存
    output_file = Path('important_data/complete_food_database.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print("【保存完了】")
    print("=" * 80)
    print(f"💾 ファイル: {output_file}")
    print(f"📊 データサイズ: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
    print()

    # サンプルデータ表示（最初の3食材）
    print("=" * 80)
    print("【サンプルデータ（最初の3食材）】")
    print("=" * 80)

    for i, food in enumerate(complete_foods[:3], 1):
        print(f"\n{i}. {food['food_name']}")
        print(f"   カテゴリ: {food['catalog_category']}")

        # Serving情報
        serving_info = food['serving_info']
        print(f"\n   📏 Serving Size:")
        print(f"      {serving_info['unit']} = {serving_info['grams_per_unit']}g")
        print(f"      カロリー: {serving_info['calories_per_unit']} kcal")
        print(f"      ソース: {food['data_sources']['nutrition_source']}")

        # 必須栄養素
        nutrients = food['nutrition']['essential_nutrients']
        print(f"\n   🥗 必須栄養素:")
        print(f"      Total Fat: {nutrients['total_fat']}g")
        print(f"      Total Carbs: {nutrients['total_carbs']}g")
        print(f"      Protein: {nutrients['protein']}g")

        # Serving変換
        conversions = food['serving_conversions']
        print(f"\n   🔄 Serving変換 ({conversions['total_conversions']}種類):")
        print(f"      Base unit: {conversions['base_unit']}")
        print(f"      ソース: {food['data_sources']['serving_conversion_source']}")
        for conv in conversions['conversions'][:3]:
            print(f"        • {conv['unit']:20s} = {conv['grams']:7.1f}g ({conv['calories']:6.1f} kcal)")

    # 除外食材詳細（あれば）
    if nutrition_only_details:
        print()
        print("=" * 80)
        print("【Nutritionデータのみの食材（Serving変換なし）】")
        print("=" * 80)
        for i, item in enumerate(nutrition_only_details[:10], 1):
            print(f"{i}. {item['food_name']}")
            print(f"   カテゴリ: {item['catalog_category']}")
            print(f"   理由: {item['reason']}")
        if len(nutrition_only_details) > 10:
            print(f"   ... 他 {len(nutrition_only_details) - 10}食材")

    if serving_only_details:
        print()
        print("=" * 80)
        print("【Serving変換データのみの食材（Nutritionなし）】")
        print("=" * 80)
        for i, item in enumerate(serving_only_details[:10], 1):
            print(f"{i}. {item['food_name']}")
            print(f"   カテゴリ: {item['catalog_category']}")
            print(f"   理由: {item['reason']}")

    print()
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)
    print(f"🎉 {len(complete_foods)}食材の完全データベースを作成しました！")
    print(f"   - Nutrition情報: 100%")
    print(f"   - Serving変換情報: 100%")
    print(f"   - 平均栄養素数: {sum(f['nutrition']['total_nutrients_found'] for f in complete_foods) / len(complete_foods):.1f}種類")
    print(f"   - 平均変換数: {sum(f['serving_conversions']['total_conversions'] for f in complete_foods) / len(complete_foods):.1f}種類")


if __name__ == "__main__":
    main()
