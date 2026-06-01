#!/usr/bin/env python3
"""高誤差ケースの食材認識レビュー"""
import json

models = {
    'Gemma4-26B': 'test_scripts/output/prompt_eval_default_20260405_212805.json',
    'Gemma4-31B': 'test_scripts/output/prompt_eval_default_20260405_212824.json',
    'Qwen3.6-Plus': 'test_scripts/output/prompt_eval_default_20260405_214100.json',
}

labels_dir = 'test_images/images_label_with_nutrition'

for model_name, path in models.items():
    with open(path) as f:
        data = json.load(f)

    sep = "=" * 70
    print(f"\n{sep}")
    print(f"  {model_name} — クリティカル誤認識チェック (カロリー誤差30%以上)")
    print(sep)

    runs = data.get('runs', [])
    if not runs:
        print("  No runs found")
        continue

    for img_result in runs[0].get('image_results', []):
        if not img_result.get('success'):
            img_name = img_result.get('image_name', '?')
            err_msg = str(img_result.get('error_message', 'unknown'))[:80]
            print(f"  [FAIL] {img_name}: {err_msg}")
            continue

        cal_err = abs(img_result['error']['calorie']['percent'])
        if cal_err < 30:
            continue

        img_name = img_result['image_name']
        img_idx = img_result['image_index']

        # ラベル読み込み
        label_path = f"{labels_dir}/test_food{img_idx:02d}.json"
        with open(label_path) as f:
            label = json.load(f)

        # ラベルの食材名リスト
        label_foods = []
        for dish in label.get('dishes', []):
            mf = dish.get('main_food')
            if mf:
                label_foods.append(f"{mf['search_name']} ({mf.get('weight_g', 0)}g)")
            for ex in dish.get('extras', []):
                label_foods.append(f"{ex['search_name']} ({ex.get('weight_g', 0)}g)")

        # API結果の食材名リスト (dishes[].ingredients[] 構造)
        api_foods = []
        api_data = img_result.get('api_result', {})
        for dish in api_data.get('dishes', []):
            dish_name = dish.get('dish_name', '?')
            for ing in dish.get('ingredients', []):
                name = ing.get('ingredient_name') or ing.get('vlm_query', '?')
                wg = ing.get('weight_g', 0)
                api_foods.append(f"{name} ({wg}g)")

        label_cal = img_result['label_nutrition']['total_calorie']
        api_cal = img_result['api_result']['total_nutrition']['calories']
        err_pct = img_result['error']['calorie']['percent']

        print(f"\n  [{img_name}] カロリー誤差: {err_pct:+.1f}% (Label:{label_cal:.0f} vs API:{api_cal:.0f})")
        print(f"    Label: {label_foods}")
        print(f"    API:   {api_foods}")
