#!/usr/bin/env python3
"""
1,188食材のServing変換情報を抽出
unit間の変換情報（cup→tablespoon, gram等）を提供
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.manual_serving_data_loader import ManualServingConversionLoader


def parse_serving_conversion(serving_text: str) -> dict:
    """
    "cup 488cals / 128 g" のような文字列をパース

    Returns:
        {
            "unit": "cup",
            "calories": 488.0,
            "grams": 128.0,
            "raw_text": "cup 488cals / 128 g"
        }
    """
    # パターン: "unit XXXcals / YYY g"
    pattern = r'^(.+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)cals?\s*/\s+(\d+(?:\.\d+)?)\s*g$'
    match = re.match(pattern, serving_text.strip())

    if match:
        unit = match.group(1).strip()
        calories = float(match.group(2).replace(',', ''))
        grams = float(match.group(3))

        return {
            'unit': unit,
            'calories': calories,
            'grams': grams,
            'raw_text': serving_text
        }

    return None


def main():
    print("🔄 Serving変換情報抽出")
    print("=" * 80)

    # マニュアルデータローダー初期化
    manual_loader = ManualServingConversionLoader()
    print(f"📋 マニュアルデータ: {len(manual_loader.manual_data)}件")
    print()

    # 元データ読み込み
    source_file = Path('important_data/complete_scraping_data_1188_foods_final.json')
    with open(source_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['collection_results']
    print(f"📊 総食材数: {len(results)}個")
    print()

    # Serving変換情報抽出
    serving_conversions_data = []
    auto_success_count = 0
    manual_success_count = 0
    failed_foods = []

    for i, item in enumerate(results, 1):
        food_name = item.get('food_name', '')
        catalog_category = item.get('catalog_category', 'unknown')
        comp_data = item.get('comprehensive_data', {})
        serving_options = comp_data.get('serving_options', {})
        raw_serving_data = serving_options.get('raw_serving_data', [])

        # "XXX cals / YYY g"パターンを抽出
        serving_conversions = []
        data_source = 'auto'

        for element in raw_serving_data:
            if isinstance(element, str):
                parsed = parse_serving_conversion(element)
                if parsed:
                    serving_conversions.append(parsed)

        # 自動抽出が失敗した場合、マニュアルデータを確認
        if not serving_conversions:
            manual_conversions = manual_loader.get_conversion_info(food_name)
            if manual_conversions:
                serving_conversions = manual_conversions
                data_source = 'manual'

        if serving_conversions:
            # 基本unitを特定（食材名から抽出）
            base_unit = None
            for conversion in serving_conversions:
                if conversion['unit'].lower() in food_name.lower():
                    base_unit = conversion['unit']
                    break

            if not base_unit and serving_conversions:
                # 食材名にunitが含まれていない場合、最初のconversionをbase_unitとする
                base_unit = serving_conversions[0]['unit']

            food_conversion_data = {
                'sequence': i,
                'food_name': food_name,
                'catalog_category': catalog_category,
                'base_unit': base_unit,
                'conversions': serving_conversions,
                'total_conversions': len(serving_conversions),
                'source': data_source
            }

            serving_conversions_data.append(food_conversion_data)

            if data_source == 'auto':
                auto_success_count += 1
            else:
                manual_success_count += 1
        else:
            failed_foods.append({
                'sequence': i,
                'food_name': food_name,
                'reason': 'No serving conversion patterns found'
            })

        # 進捗表示（100食材ごと）
        if i % 100 == 0:
            print(f"  処理中... {i}/{len(results)} ({i/len(results)*100:.1f}%)")

    success_count = auto_success_count + manual_success_count
    print(f"\n✅ 抽出完了: {success_count}食材")
    print(f"   - 自動抽出: {auto_success_count}食材")
    print(f"   - マニュアル: {manual_success_count}食材")
    print(f"❌ 失敗: {len(failed_foods)}食材")
    print()

    # 統計情報
    print("=" * 80)
    print("【統計情報】")
    print("=" * 80)

    # 変換数の分布
    conversion_counts = {}
    for food_data in serving_conversions_data:
        count = food_data['total_conversions']
        if count not in conversion_counts:
            conversion_counts[count] = 0
        conversion_counts[count] += 1

    print(f"\n変換数の分布:")
    for count in sorted(conversion_counts.keys()):
        num_foods = conversion_counts[count]
        print(f"  {count}種類の変換: {num_foods}食材")

    # 出現するunit一覧
    all_units = set()
    for food_data in serving_conversions_data:
        for conversion in food_data['conversions']:
            all_units.add(conversion['unit'])

    print(f"\n出現するunit（{len(all_units)}種類）:")
    for unit in sorted(all_units):
        count = sum(1 for food in serving_conversions_data
                   for conv in food['conversions'] if conv['unit'] == unit)
        print(f"  {unit:20s}: {count}食材")

    # 保存データ構築
    output_data = {
        'extraction_summary': {
            'timestamp': datetime.now().isoformat(),
            'source_file': str(source_file),
            'total_foods': len(results),
            'successful_extractions': success_count,
            'auto_extractions': auto_success_count,
            'manual_extractions': manual_success_count,
            'failed_extractions': len(failed_foods),
            'total_unique_units': len(all_units),
            'conversion_count_distribution': conversion_counts
        },
        'serving_conversions': serving_conversions_data,
        'failed_foods': failed_foods
    }

    # JSON保存
    output_file = Path('important_data/serving_conversions_1188_foods.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print()
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

    for i, food_data in enumerate(serving_conversions_data[:3], 1):
        print(f"\n{i}. {food_data['food_name']}")
        print(f"   カテゴリ: {food_data['catalog_category']}")
        print(f"   Base unit: {food_data['base_unit']}")
        print(f"   変換数: {food_data['total_conversions']}種類")
        print(f"   変換情報:")
        for conv in food_data['conversions'][:5]:
            print(f"     • {conv['unit']:15s} = {conv['grams']:7.1f}g ({conv['calories']:6.1f} kcal)")

    # 失敗詳細
    if failed_foods:
        print()
        print("=" * 80)
        print("【抽出失敗詳細】")
        print("=" * 80)
        for item in failed_foods[:10]:
            print(f"{item['sequence']:4d}. {item['food_name']}")
            print(f"       理由: {item['reason']}")

    print()
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)
    print(f"🎉 {success_count}食材のServing変換情報を抽出しました！")
    print(f"   - 自動抽出: {auto_success_count}食材")
    print(f"   - マニュアル補完: {manual_success_count}食材")
    print(f"   - 平均変換数: {sum(f['total_conversions'] for f in serving_conversions_data) / len(serving_conversions_data):.1f}種類/食材")
    print(f"   - Unit種類: {len(all_units)}種類")


if __name__ == "__main__":
    main()
