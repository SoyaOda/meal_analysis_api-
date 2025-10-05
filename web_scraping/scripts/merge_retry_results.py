#!/usr/bin/env python3
"""
再収集した63食材のデータを元のcomplete_scraping_data_1188_foods.jsonに統合
"""

import json
from pathlib import Path
from datetime import datetime


def main():
    print("🔄 再収集データの統合")
    print("=" * 80)

    # 元データ読み込み
    original_file = Path('important_data/complete_scraping_data_1188_foods.json')
    with open(original_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)

    original_results = original_data['collection_results']
    print(f"📂 元データ: {len(original_results)}食材")

    # 再収集結果読み込み
    retry_file = Path('important_data/retry_select_serving_results.json')
    with open(retry_file, 'r', encoding='utf-8') as f:
        retry_data = json.load(f)

    retry_results = retry_data['retry_results']
    print(f"🔄 再収集データ: {len(retry_results)}食材")
    print()

    # 再収集食材名をマップに変換
    retry_map = {}
    for item in retry_results:
        food_name = item.get('food_name', '')
        if item.get('data_collection_success'):
            retry_map[food_name] = item.get('comprehensive_data', {})

    print(f"📋 統合可能な再収集データ: {len(retry_map)}個")
    print()

    # 統合処理
    updated_count = 0
    not_found_count = 0

    for i, item in enumerate(original_results):
        food_name = item.get('food_name', '')

        if food_name in retry_map:
            # comprehensive_dataを更新
            new_comp_data = retry_map[food_name]

            # 既存のcomprehensive_dataと比較
            old_comp_data = item.get('comprehensive_data', {})
            old_serving_options = old_comp_data.get('serving_options', {})
            old_raw_serving = old_serving_options.get('raw_serving_data', [])

            new_serving_options = new_comp_data.get('serving_options', {})
            new_raw_serving = new_serving_options.get('raw_serving_data', [])

            # 更新実行
            item['comprehensive_data'] = new_comp_data

            # 統計
            old_has_select = 'Select Serving' in old_raw_serving
            new_has_select = 'Select Serving' in new_raw_serving

            if not old_has_select and new_has_select:
                updated_count += 1
                print(f"✅ 更新: {food_name[:60]}...")
                print(f"   'Select Serving': なし → あり")

    print()
    print("=" * 80)
    print("【統合結果】")
    print("=" * 80)
    print(f"更新成功: {updated_count}食材")
    print(f"未発見: {not_found_count}食材")
    print()

    # 統合データを保存
    output_data = {
        'collection_summary': {
            **original_data.get('collection_summary', {}),
            'last_retry_update': datetime.now().isoformat(),
            'retry_updated_count': updated_count
        },
        'collection_results': original_results
    }

    output_file = Path('important_data/complete_scraping_data_1188_foods_with_retry.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"💾 統合データ保存: {output_file}")
    print()

    # 最終検証: 'Select Serving'の存在確認
    print("=" * 80)
    print("【最終検証: 'Select Serving'存在確認】")
    print("=" * 80)

    has_select_serving = 0
    no_select_serving = []

    for i, item in enumerate(original_results, 1):
        food_name = item.get('food_name', '')
        comp_data = item.get('comprehensive_data', {})
        serving_options = comp_data.get('serving_options', {})
        raw_serving_data = serving_options.get('raw_serving_data', [])

        if 'Select Serving' in raw_serving_data:
            has_select_serving += 1
        else:
            if len(no_select_serving) < 10:
                no_select_serving.append({
                    'sequence': i,
                    'food_name': food_name
                })

    total = len(original_results)
    print(f"✅ 'Select Serving'存在: {has_select_serving}/{total} ({has_select_serving/total*100:.1f}%)")
    print(f"❌ 'Select Serving'不在: {total - has_select_serving}/{total} ({(total - has_select_serving)/total*100:.1f}%)")
    print()

    if no_select_serving:
        print("【'Select Serving'不在サンプル（最初の10個）】")
        for item in no_select_serving:
            print(f"  {item['sequence']:4d}. {item['food_name']}")
        print()

    # 総合判定
    print("=" * 80)
    print("【総合判定】")
    print("=" * 80)

    if has_select_serving == total:
        print("🎉 全1,188食材で'Select Serving'が存在します！")
    else:
        missing_count = total - has_select_serving
        print(f"📊 統合後の状況:")
        print(f"   'Select Serving'存在: {has_select_serving}個")
        print(f"   'Select Serving'不在: {missing_count}個")
        print()
        print(f"💡 不在の{missing_count}食材は0カロリー食材等で栄養情報が存在しない可能性があります")


if __name__ == "__main__":
    main()
