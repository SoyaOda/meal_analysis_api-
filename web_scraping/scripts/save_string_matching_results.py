#!/usr/bin/env python3
"""
文字列マッチング結果を保存
- 1個マッチ（ユニーク）: JSON形式で対応関係を保存
- 0個マッチ: TXT形式でリスト保存
- 2個以上マッチ: TXT形式で全候補を列挙
"""

import json
import re

# ファイル読み込み
with open('/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed.json', 'r', encoding='utf-8') as f:
    stemmed_data = json.load(f)

with open('processed_data/all_foods_final_1152.json', 'r', encoding='utf-8') as f:
    final_data = json.load(f)

final_foods = final_data['foods']

def normalize_name(name):
    """カンマを削除し、小文字に変換して正規化"""
    if not name:
        return ''
    normalized = name.replace(',', '')
    normalized = normalized.lower()
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()

# Final食材名を正規化
final_normalized_names = [normalize_name(f['food_name']) for f in final_foods]

# マッチング実行
unique_matches = []  # 1個マッチ
zero_matches = []    # 0個マッチ
multi_matches = []   # 2個以上マッチ

for stemmed in stemmed_data:
    stemmed_name = stemmed['original_name']
    stemmed_id = stemmed['id']
    stemmed_normalized = normalize_name(stemmed_name)

    # Final JSONに含まれる候補を探す
    found_matches = []

    for i, final_name in enumerate(final_normalized_names):
        if stemmed_normalized in final_name or final_name in stemmed_normalized:
            found_matches.append({
                'final_food_name': final_foods[i]['food_name'],
                'final_food_id': final_foods[i]['food_id']
            })

    if len(found_matches) == 0:
        zero_matches.append({
            'stemmed_id': stemmed_id,
            'stemmed_name': stemmed_name
        })
    elif len(found_matches) == 1:
        unique_matches.append({
            'stemmed_id': stemmed_id,
            'stemmed_name': stemmed_name,
            'final_food_id': found_matches[0]['final_food_id'],
            'final_food_name': found_matches[0]['final_food_name']
        })
    else:
        multi_matches.append({
            'stemmed_id': stemmed_id,
            'stemmed_name': stemmed_name,
            'match_count': len(found_matches),
            'candidates': found_matches
        })

# 1. ユニークマッチをJSON形式で保存
unique_output = 'processed_data/string_match_unique_1to1.json'
with open(unique_output, 'w', encoding='utf-8') as f:
    json.dump({
        'total_unique_matches': len(unique_matches),
        'mappings': unique_matches
    }, f, ensure_ascii=False, indent=2)

print(f'✅ ユニークマッチ（1対1対応）: {len(unique_matches)}個')
print(f'   保存先: {unique_output}')

# 2. 0個マッチをTXT形式で保存
zero_output = 'processed_data/string_match_zero_matches.txt'
with open(zero_output, 'w', encoding='utf-8') as f:
    f.write('=' * 80 + '\n')
    f.write('マッチなし食材リスト（0個マッチ）\n')
    f.write('=' * 80 + '\n')
    f.write(f'総数: {len(zero_matches)}個\n')
    f.write('=' * 80 + '\n\n')

    for i, item in enumerate(zero_matches, 1):
        f.write(f'{i}. {item["stemmed_name"]}\n')
        f.write(f'   ID: {item["stemmed_id"]}\n')
        f.write(f'   マッチ: なし\n')
        f.write('\n')

print(f'✅ マッチなし: {len(zero_matches)}個')
print(f'   保存先: {zero_output}')

# 3. 2個以上マッチをTXT形式で保存
multi_output = 'processed_data/string_match_multiple_candidates.txt'
with open(multi_output, 'w', encoding='utf-8') as f:
    f.write('=' * 80 + '\n')
    f.write('複数候補あり食材リスト（2個以上マッチ）\n')
    f.write('=' * 80 + '\n')
    f.write(f'総数: {len(multi_matches)}個\n')
    f.write('=' * 80 + '\n\n')

    for i, item in enumerate(multi_matches, 1):
        f.write(f'{i}. {item["stemmed_name"]}\n')
        f.write(f'   ID: {item["stemmed_id"]}\n')
        f.write(f'   マッチ数: {item["match_count"]}個\n')
        f.write(f'   候補:\n')
        for j, candidate in enumerate(item['candidates'], 1):
            f.write(f'      {j}. {candidate["final_food_name"]}\n')
            f.write(f'         ID: {candidate["final_food_id"]}\n')
        f.write('\n')

print(f'✅ 複数マッチ: {len(multi_matches)}個')
print(f'   保存先: {multi_output}')

# サマリー表示
print(f'\n' + '=' * 80)
print(f'📊 文字列マッチング結果サマリー')
print(f'=' * 80)
print(f'総Stemmed食材数: {len(stemmed_data)}個')
print(f'')
print(f'✅ ユニークマッチ（1対1）: {len(unique_matches)}個 ({len(unique_matches)/len(stemmed_data)*100:.1f}%)')
print(f'❌ マッチなし（0個）: {len(zero_matches)}個 ({len(zero_matches)/len(stemmed_data)*100:.1f}%)')
print(f'⚠️  複数マッチ（2個以上）: {len(multi_matches)}個 ({len(multi_matches)/len(stemmed_data)*100:.1f}%)')
print(f'')
print(f'保存ファイル:')
print(f'  1. {unique_output} (JSON)')
print(f'  2. {zero_output} (TXT)')
print(f'  3. {multi_output} (TXT)')
