#!/usr/bin/env python3
"""
全Scrapingデータを統一プロセッサーで処理し、100gカロリー検証を実行
"""

import json
from pathlib import Path
from unified_food_processor import UnifiedFoodProcessor


def calculate_100g_calories(food_data: dict) -> float:
    """100gカロリーを計算"""
    essential = food_data.get('essential_nutrition', {})

    # Serving sizeがある場合
    serving_size = essential.get('serving_size')
    calories = essential.get('calories', {}).get('value', 0)

    if serving_size and serving_size.get('grams', 0) > 0:
        grams = serving_size['grams']
        return (calories / grams) * 100

    return None


def main():
    print("🔄 全Scrapingデータの統一処理 + 100g検証")
    print("=" * 80)

    processor = UnifiedFoodProcessor()

    # Scrapingデータを読み込み
    scraping_file = processor.data_dir / 'comprehensive_food_collection_all_20251001_124446.json'

    with open(scraping_file, 'r', encoding='utf-8') as f:
        scraping_data = json.load(f)

    # Stemmed DBを読み込み
    stemmed_file = Path('/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed.json')
    with open(stemmed_file, 'r', encoding='utf-8') as f:
        stemmed_data = json.load(f)

    # Mappingsを読み込み
    mapping_file = processor.output_dir / 'complete_1to1_mappings.json'
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mappings_data = json.load(f)

    # Stemmed DBをdict化（IDを文字列に統一）
    stemmed_dict = {str(s['id']): s for s in stemmed_data}

    # 処理
    results = []
    success_count = 0
    fail_count = 0
    skipped_count = 0

    # food_nameでマッピング作成（Final JSON用）
    final_name_to_id = {}

    for i, item in enumerate(scraping_data['collection_results']):
        if not item.get('data_collection_success'):
            skipped_count += 1
            continue

        food_data = item.get('comprehensive_data', {})
        food_id = f"food_{i+1:04d}"

        processed = processor.process_scraped_food(food_data, food_id)

        if processed:
            results.append(processed)
            success_count += 1

            # food_nameでマッピング
            food_name = processed['food_name']
            final_name_to_id[food_name] = food_id
        else:
            fail_count += 1

    print(f"📊 処理結果:")
    print(f"   成功: {success_count}個")
    print(f"   失敗: {fail_count}個")
    print(f"   スキップ: {skipped_count}個")
    print()

    # 100g検証
    print(f"🔍 100gカロリー検証（1,126ペア）")
    print("=" * 80)

    # Final JSONをdict化
    final_dict = {f['food_id']: f for f in results}

    within_5pct = 0
    over_5pct = 0
    calculation_failed = 0
    over_5pct_samples = []

    for mapping in mappings_data['mappings']:
        stemmed_id = mapping['stemmed_id']
        final_food_name = mapping['final_food_name']

        # Stemmed DBのカロリー（100g）
        stemmed_food = stemmed_dict.get(stemmed_id)
        if not stemmed_food:
            calculation_failed += 1
            continue

        stemmed_cal_100g = stemmed_food['nutrition']['calories']

        # Final JSONのfood_idを取得
        # final_food_nameで検索
        final_food_id = None
        for f in results:
            # Normalize comparison
            if f['food_name'].replace(',', '').lower() == final_food_name.replace(',', '').lower():
                final_food_id = f['food_id']
                break

        if not final_food_id:
            calculation_failed += 1
            continue

        final_food = final_dict.get(final_food_id)
        if not final_food:
            calculation_failed += 1
            continue

        # 100g計算
        final_cal_100g = calculate_100g_calories(final_food)

        if final_cal_100g is None:
            calculation_failed += 1
            continue

        # 差分パーセンテージを計算
        if stemmed_cal_100g == 0 and final_cal_100g == 0:
            diff_pct = 0.0
        elif stemmed_cal_100g == 0:
            diff_pct = 100.0
        else:
            diff_pct = abs(stemmed_cal_100g - final_cal_100g) / stemmed_cal_100g * 100

        if diff_pct <= 5.0:
            within_5pct += 1
        else:
            over_5pct += 1
            over_5pct_samples.append({
                'stemmed_name': mapping['stemmed_name'],
                'final_name': mapping['final_food_name'],
                'stemmed_cal': stemmed_cal_100g,
                'final_cal': final_cal_100g,
                'diff_pct': diff_pct
            })

    # 結果表示
    total_checked = within_5pct + over_5pct

    print(f"📊 検証結果:")
    print(f"   ✅ 5%以内: {within_5pct}個 ({within_5pct/total_checked*100:.1f}%)")
    print(f"   ❌ 5%超過: {over_5pct}個 ({over_5pct/total_checked*100:.1f}%)")
    print(f"   ⚠️  計算失敗: {calculation_failed}個")
    print()

    # 5%超過サンプル
    if over_5pct_samples:
        print(f"❌ 5%超過サンプル（最初の10個、差分が大きい順）:")
        over_5pct_samples.sort(key=lambda x: x['diff_pct'], reverse=True)
        for i, item in enumerate(over_5pct_samples[:10], 1):
            print(f"   {i}. {item['stemmed_name']}")
            print(f"      Stemmed 100g: {item['stemmed_cal']:.1f} kcal")
            print(f"      Final 100g: {item['final_cal']:.1f} kcal")
            print(f"      差分: {item['diff_pct']:.1f}%")
            print()

    # 結果保存
    output_data = {
        'metadata': {
            'version': '2.0_unified',
            'processed_at': results[0]['metadata']['processed_at'] if results else '',
            'total_foods': len(results),
            'processor': 'unified_food_processor'
        },
        'foods': results
    }

    output_file = processor.output_dir / 'all_foods_unified_processed.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, ensure_ascii=False, indent=2, fp=f)

    print(f"💾 統一処理済みデータ保存: {output_file}")

    # 検証結果保存
    verification_result = {
        'total_checked': total_checked,
        'within_5pct': within_5pct,
        'over_5pct': over_5pct,
        'calculation_failed': calculation_failed,
        'within_5pct_rate': within_5pct / total_checked * 100 if total_checked > 0 else 0,
        'over_5pct_details': over_5pct_samples
    }

    verification_file = processor.output_dir / 'unified_calorie_verification.json'
    with open(verification_file, 'w', encoding='utf-8') as f:
        json.dump(verification_result, ensure_ascii=False, indent=2, fp=f)

    print(f"💾 検証結果保存: {verification_file}")


if __name__ == "__main__":
    main()
