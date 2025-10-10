#!/usr/bin/env python3
"""
all_foods_with_unit_grams.jsonを複製し、各食材に栄養素情報(default_nutrition)を追加
"""

import json
import re
from pathlib import Path
from collections import OrderedDict

def extract_nutrition_info(file_path, food_name):
    """指定した食材の【栄養情報】セクションを抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 食材のセクションを見つける
    escaped_name = re.escape(food_name)
    # 小数点対応: 8.75cals, 1,849cals など
    pattern = rf'\d+\.\s*{escaped_name},.*?\n[\d,.]+cals'

    match = re.search(pattern, content)
    if not match:
        return None

    # 食材セクションの開始位置
    start_pos = match.start()

    # 次の番号付きタイトルまでを取得
    next_match = re.search(r'\n\d+\.\s+', content[match.end():])
    if next_match:
        end_pos = match.end() + next_match.start()
        food_content = content[start_pos:end_pos]
    else:
        food_content = content[start_pos:]

    # 【栄養情報】セクションを抽出
    nutrition_match = re.search(r'【栄養情報】\n(.*?)(?=\n【|$)', food_content, re.DOTALL)
    if not nutrition_match:
        return None

    nutrition_content = nutrition_match.group(1).strip()

    # "None"の場合はNoneを返す
    if nutrition_content == "None":
        return "None"

    return nutrition_content

def parse_nutrition_to_dict(nutrition_info):
    """栄養情報から栄養素辞書を作成"""
    if nutrition_info is None or nutrition_info == "None":
        return None

    # 除外するパターン
    exclude_patterns = [
        r'^Serving Size',
        r'^Amount per serving',
        r'^% Daily Value',
        r'^Nutrition Facts',
        r'^\s*$',
        r'^grade\s*[A-F]',
        r'^\*'
    ]

    # Caloriesパターン（特別処理）
    # 小数点対応: 8.75cals, 1,849cals など
    calories_pattern = r'^Calories\s+([\d,.]+)cals'

    # 栄養素行のパターン
    nutrient_pattern = r'^([A-Za-z\s\-\']+?)\s+([\d,.]+)(g|mg|mcg|μg|IU|kcal)\s*(?:(\d+)%)?'

    nutrition_dict = OrderedDict()

    for line in nutrition_info.split('\n'):
        line = line.strip()

        # Caloriesを先にチェック
        calories_match = re.match(calories_pattern, line)
        if calories_match:
            value_str = calories_match.group(1)
            value = float(value_str.replace(',', ''))
            nutrition_dict['calorie'] = value
            continue

        # 除外パターンに一致する行はスキップ
        if any(re.match(pattern, line) for pattern in exclude_patterns):
            continue

        # 栄養素行にマッチするか確認
        match = re.match(nutrient_pattern, line)
        if match:
            nutrient_name = match.group(1).strip()
            value_str = match.group(2)
            unit = match.group(3)

            # キー名を作成: スペースをアンダースコアに置き換え + 単位
            key_name = nutrient_name.replace(' ', '_') + '_' + unit

            # 値をfloatに変換（カンマを除去）
            value = float(value_str.replace(',', ''))

            nutrition_dict[key_name] = value

    return nutrition_dict if nutrition_dict else None

def main():
    # 入力JSONファイル
    input_file = Path(__file__).parent.parent / "output" / "all_foods_with_unit_grams.json"

    # 出力JSONファイル（複製）
    output_file = Path(__file__).parent.parent / "output" / "all_foods_with_nutrition.json"

    # manual_input_templatesディレクトリ
    templates_dir = Path(__file__).parent.parent / "manual_input_templates"

    # JSONファイルを読み込み
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=" * 80)
    print("栄養素情報追加処理")
    print("=" * 80)

    success_count = 0
    none_nutrition_count = 0
    failed_count = 0

    # 各食材に default_nutrition を追加
    for i, food in enumerate(data['foods'], 1):
        # ファイルパスを構築
        file_path = templates_dir / food['file']

        # 栄養情報を抽出（title_full_nameからdefault_unitを除いた部分で検索）
        # "Nougat, homemade, piece" → "Nougat, homemade"
        title_parts = food['title_full_name'].rsplit(', ', 1)
        search_name = title_parts[0] if len(title_parts) > 1 else food['title_full_name']
        nutrition_info = extract_nutrition_info(file_path, search_name)

        if nutrition_info == "None":
            # 栄養情報が"None"の場合
            food['default_nutrition'] = None
            none_nutrition_count += 1
            print(f"{i}. ⚪ {food['food_name']}: 栄養情報なし（None）")
        elif nutrition_info is None:
            # 栄養情報セクションが見つからない場合
            food['default_nutrition'] = None
            failed_count += 1
            print(f"{i}. ⚠️  {food['food_name']}: 栄養情報セクションなし")
        else:
            # 栄養情報を辞書に変換
            nutrition_dict = parse_nutrition_to_dict(nutrition_info)

            if nutrition_dict:
                food['default_nutrition'] = nutrition_dict
                success_count += 1
                if i <= 3:  # 最初の3件は詳細表示
                    print(f"{i}. ✅ {food['food_name']}: {len(nutrition_dict)}種類の栄養素取得")
                elif i % 100 == 0:  # 100件ごとに進捗表示
                    print(f"{i}. ✅ {food['food_name']}: {len(nutrition_dict)}種類の栄養素取得")
            else:
                food['default_nutrition'] = None
                failed_count += 1
                print(f"{i}. ⚠️  {food['food_name']}: 栄養素行が抽出できない")

    # メタデータを更新
    data['metadata']['description'] = 'All foods with default unit, calories, unit-to-grams mapping, and nutrition data'

    # 新しいJSONファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("処理完了！")
    print("=" * 80)
    print(f"総食材数: {len(data['foods'])}")
    print(f"成功: {success_count}件")
    print(f"栄養情報なし(None): {none_nutrition_count}件")
    print(f"失敗: {failed_count}件")
    print(f"\n出力ファイル: {output_file}")

    # サンプルを表示
    if success_count > 0:
        print("\n" + "=" * 80)
        print("サンプル（最初の2件）:")
        print("=" * 80)

        sample_count = 0
        for food in data['foods']:
            if food['default_nutrition'] and sample_count < 2:
                print(f"\n{food['food_name']}:")
                print(f"  カテゴリ: {food['category']}")
                print(f"  デフォルトunit: {food['default_unit']}")
                print(f"  デフォルトcalories: {food['default_calories']}")
                print(f"  栄養素情報 ({len(food['default_nutrition'])}種類):")

                # 最初の5つの栄養素を表示
                for j, (key, value) in enumerate(food['default_nutrition'].items()):
                    if j < 5:
                        print(f"    {key}: {value}")
                    else:
                        print(f"    ... 他{len(food['default_nutrition']) - 5}種類")
                        break

                sample_count += 1

if __name__ == "__main__":
    main()
