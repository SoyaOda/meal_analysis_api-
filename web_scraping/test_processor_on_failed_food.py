#!/usr/bin/env python3
"""
既存のfood_data_processorで失敗食材のserving情報を抽出できるかテスト
"""
import json
import sys
from pathlib import Path

# processorをインポート
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
from food_data_processor import FoodDataProcessor

def test_failed_food():
    print("=" * 80)
    print("🧪 失敗食材でのProcessor抽出テスト")
    print("=" * 80)

    # 結果ファイルを読み込み
    result_file = Path("data/retry_failed_foods_20251001_184207.json")
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data.get('collection_results', [])

    # 失敗食材を抽出（improved_servingsが0個のもの）
    failed_foods = []
    for food in results:
        comp_data = food.get('comprehensive_data', {})
        serving_opts = comp_data.get('serving_options', {})
        improved_servings = serving_opts.get('improved_servings', [])

        if len(improved_servings) == 0:
            failed_foods.append(food)

    print(f"\n📊 失敗食材: {len(failed_foods)}個")

    # 2番目の失敗食材でテスト（Cajun seasoning - serving情報を含む）
    test_food = failed_foods[1]  # 0番目ではなく1番目
    food_name = test_food.get('food_name', 'Unknown')

    print(f"\n🎯 テスト対象: {food_name}")
    print("=" * 80)

    # Serving dataを取得
    comp_data = test_food.get('comprehensive_data', {})
    serving_opts = comp_data.get('serving_options', {})
    raw_serving_data = serving_opts.get('raw_serving_data', [])

    print(f"\n📋 Raw serving data: {len(raw_serving_data)}個")
    print(f"\n🔍 最初の30個:")
    for i, text in enumerate(raw_serving_data[:30], 1):
        print(f"   [{i}] {text}")

    # Processorのクリーニングメソッドを実行
    processor = FoodDataProcessor()

    print(f"\n🧠 Processor実行中...")
    print("=" * 80)

    # serving_optsをそのまま渡す（dictとして）
    cleaned_servings = processor.clean_serving_data(serving_opts)

    print(f"\n✅ 抽出結果: {len(cleaned_servings)}個のserving")
    print("=" * 80)

    if cleaned_servings:
        for i, serving in enumerate(cleaned_servings, 1):
            print(f"\n{i}. {serving.get('display_text', 'N/A')}")
            print(f"   Unit: {serving.get('unit')}")
            print(f"   Calories: {serving.get('calories_per_unit')}")
            print(f"   Grams: {serving.get('grams_per_unit')}")
            print(f"   Source: {serving.get('source')}")
    else:
        print("\n❌ 抽出失敗")

    # 結果を保存
    output_file = Path(f"debug/processor_test_{food_name.replace('/', '_').replace(' ', '_')[:30]}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'food_name': food_name,
            'raw_serving_count': len(raw_serving_data),
            'raw_serving_data': raw_serving_data,
            'cleaned_servings': cleaned_servings
        }, f, ensure_ascii=False, indent=2)

    print(f"\n📄 結果保存: {output_file}")

    # 成功判定
    success = len(cleaned_servings) > 0
    print(f"\n🎯 テスト結果: {'✅ 成功' if success else '❌ 失敗'}")

    return success

if __name__ == "__main__":
    success = test_failed_food()
    sys.exit(0 if success else 1)
