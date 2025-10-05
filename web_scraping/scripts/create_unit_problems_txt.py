#!/usr/bin/env python3
"""
単位問題パターンをtxtファイルにまとめる
"""

import json


def main():
    # 検証結果を読み込み
    with open('processed_data/food_name_unit_verification.json', 'r', encoding='utf-8') as f:
        result = json.load(f)

    # Complete版
    with open('processed_data/all_foods_final_1125_complete.json', 'r', encoding='utf-8') as f:
        complete_data = json.load(f)

    complete_dict = {f['food_id']: f for f in complete_data['foods']}

    # txtファイル作成
    output_lines = []

    output_lines.append('=' * 80)
    output_lines.append('食材名単位の問題パターン分析')
    output_lines.append('=' * 80)
    output_lines.append('')

    # パターン1: 単位抽出失敗
    output_lines.append(f'【パターン1】単位抽出失敗 ({len(result["no_unit_samples"])}個)')
    output_lines.append('=' * 80)
    output_lines.append('')

    for i, item in enumerate(result['no_unit_samples'], 1):
        food_id = item['food_id']
        food_name = item['food_name']

        # Complete版から詳細取得
        food = complete_dict.get(food_id)
        if food:
            servings = food.get('serving_options', {}).get('servings', [])
            serving_units = [s.get('unit', 'N/A') for s in servings[:3]]

            output_lines.append(f'{i}. {food_id}: {food_name}')
            output_lines.append(f'   利用可能単位: {", ".join(serving_units)}')
            output_lines.append('')

    # パターン2のデータを全件読み込み
    # result['not_found_samples']には最初の10個しか含まれていないので、
    # 完全なリストを再構築

    # Complete版から全ての不一致食材を抽出
    from verify_food_name_units import extract_unit_from_food_name, normalize_unit

    not_found_all = []
    for food in complete_data['foods']:
        food_id = food['food_id']
        food_name = food['food_name']

        unit = extract_unit_from_food_name(food_name)
        if unit:
            unit_normalized = normalize_unit(unit)
            servings = food.get('serving_options', {}).get('servings', [])

            found = False
            for serving in servings:
                serving_unit = serving.get('unit', '').lower().strip()
                if unit_normalized and unit_normalized in serving_unit:
                    found = True
                    break
                elif unit.lower() in serving_unit:
                    found = True
                    break

            if not found:
                not_found_all.append({
                    'food_id': food_id,
                    'food_name': food_name,
                    'extracted_unit': unit,
                    'available_units': [s.get('unit', 'N/A') for s in servings[:5]]
                })

    output_lines.append('')
    output_lines.append('=' * 80)
    output_lines.append(f'【パターン2】Serving options不一致 ({len(not_found_all)}個全て)')
    output_lines.append('=' * 80)
    output_lines.append('')

    for i, item in enumerate(not_found_all, 1):
        food_id = item['food_id']
        food_name = item['food_name']
        extracted_unit = item['extracted_unit']
        available_units = item['available_units']

        output_lines.append(f'{i}. {food_id}: {food_name}')
        output_lines.append(f'   抽出単位: {extracted_unit}')
        output_lines.append(f'   利用可能単位: {", ".join(available_units)}')
        output_lines.append('')

    # 統計情報
    output_lines.append('')
    output_lines.append('=' * 80)
    output_lines.append('統計情報')
    output_lines.append('=' * 80)
    output_lines.append(f'総食材数: {result["total_foods"]}個')
    output_lines.append(f'単位抽出成功: {result["unit_extracted"]}個 ({result["unit_extracted"]/result["total_foods"]*100:.1f}%)')
    output_lines.append(f'単位抽出失敗: {result["unit_not_extracted"]}個 ({result["unit_not_extracted"]/result["total_foods"]*100:.1f}%)')
    output_lines.append(f'Serving一致: {result["unit_found_in_servings"]}個 ({result["unit_found_in_servings"]/result["unit_extracted"]*100:.1f}%)')
    output_lines.append(f'Serving不一致: {result["unit_not_found_in_servings"]}個 ({result["unit_not_found_in_servings"]/result["unit_extracted"]*100:.1f}%)')

    # 保存
    with open('processed_data/food_name_unit_problems.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print('✅ 保存完了: processed_data/food_name_unit_problems.txt')
    print(f'   パターン1: {len(result["no_unit_samples"])}個')
    print(f'   パターン2: {len(not_found_all)}個')


if __name__ == "__main__":
    main()
