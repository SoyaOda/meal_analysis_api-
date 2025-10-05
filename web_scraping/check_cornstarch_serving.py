#!/usr/bin/env python3
import json

with open('data/comprehensive_food_collection_all_20251001_124446.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# collection_resultsを取得
results = data['collection_results']

# Cornstarchを探す
for entry in results:
    if entry.get('food_name') == 'Cornstarch, cup 488cals':
        # serving_optionsを確認
        serving_opts = entry.get('comprehensive_data', {}).get('serving_options', {})

        # 全servingを確認
        valid_count = 0
        print('=== Cornstarch serving data (有効なservingのみ) ===')
        for i in range(1, 200):
            key = 'serving_{:02d}'.format(i)
            if key in serving_opts:
                raw = serving_opts[key].get('raw_text', '')
                # calsとgを含むか
                if 'cals' in raw.lower() and 'g' in raw.lower():
                    print('{}: {}'.format(key, raw))
                    valid_count += 1

        print('\n有効なserving数: {}'.format(valid_count))
        print('全serving数: {}'.format(len([k for k in serving_opts.keys() if k.startswith('serving_')])))
        break
