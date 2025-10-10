#!/usr/bin/env python3
"""
all_foods_default_unit_calories.jsonを複製し、各食材にunit対応g数情報を追加
"""

import json
import re
from pathlib import Path
from collections import OrderedDict

def extract_serving_info(file_path, food_name):
    """指定した食材の【Serving情報】からunit→g数のマッピングを抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 食材のセクションを見つける
    # 食材名をエスケープ（特殊文字対応）
    escaped_name = re.escape(food_name)
    pattern = rf'\d+\.\s*{escaped_name},.*?\n[\d,]+cals'

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

    # 【Serving情報】セクションを抽出
    serving_match = re.search(r'【Serving情報】\n(.*?)(?=\n【|$)', food_content, re.DOTALL)
    if not serving_match:
        return None

    serving_info = serving_match.group(1)

    # unit→g数のマッピングを作成
    unit_to_grams = OrderedDict()

    # " / "を含む行を探す
    calorie_pattern = r' [\d,]+cals'
    gram_pattern = r'^([\d,.]+) g'

    for line in serving_info.split('\n'):
        if ' / ' not in line:
            continue

        # " / "で分割
        parts = line.split(' / ')
        if len(parts) != 2:
            continue

        front_part = parts[0].strip()
        back_part = parts[1].strip()

        # 前半部分からカロリー部分を削除してunit名を取得
        unit_name = re.sub(calorie_pattern, '', front_part).strip()

        # 後半部分からg数を抽出
        gram_match = re.match(gram_pattern, back_part)
        if not gram_match:
            continue

        # g数をfloatに変換（カンマ除去）
        gram_value = float(gram_match.group(1).replace(',', ''))

        # マッピングに追加
        unit_to_grams[unit_name] = gram_value

    return unit_to_grams if unit_to_grams else None

def main():
    # 入力JSONファイル
    input_file = Path(__file__).parent.parent / "output" / "all_foods_default_unit_calories.json"

    # 出力JSONファイル（複製）
    output_file = Path(__file__).parent.parent / "output" / "all_foods_with_unit_grams.json"

    # manual_input_templatesディレクトリ
    templates_dir = Path(__file__).parent.parent / "manual_input_templates"

    # JSONファイルを読み込み
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=" * 80)
    print("unit→g数マッピング追加処理")
    print("=" * 80)

    success_count = 0
    failed_count = 0
    excluded_count = 0

    # 各食材にunit_to_gramsを追加
    for food in data['foods']:
        # 除外食材はスキップ
        if food['status'] == 'excluded_no_nutrition':
            food['unit_to_grams'] = None
            excluded_count += 1
            continue

        # ファイルパスを構築
        file_path = templates_dir / food['file']

        # unit→g数マッピングを抽出
        unit_to_grams = extract_serving_info(file_path, food['food_name'])

        if unit_to_grams:
            food['unit_to_grams'] = unit_to_grams
            success_count += 1
            print(f"✅ {food['food_name']}: {len(unit_to_grams)}個のunit取得")
        else:
            food['unit_to_grams'] = {}
            failed_count += 1
            print(f"⚠️  {food['food_name']}: Serving情報なし")

    # メタデータを更新
    data['metadata']['description'] = 'All foods with default unit, calories, and unit-to-grams mapping'

    # 新しいJSONファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("処理完了！")
    print("=" * 80)
    print(f"総食材数: {len(data['foods'])}")
    print(f"成功: {success_count}件")
    print(f"失敗: {failed_count}件")
    print(f"除外: {excluded_count}件")
    print(f"\n出力ファイル: {output_file}")

    # サンプルを表示
    if success_count > 0:
        print("\n" + "=" * 80)
        print("サンプル（最初の3件）:")
        print("=" * 80)

        sample_count = 0
        for food in data['foods']:
            if food['unit_to_grams'] and sample_count < 3:
                print(f"\n{food['food_name']}:")
                print(f"  デフォルトunit: {food['default_unit']}")
                print(f"  unit→g数マッピング:")
                for unit, grams in food['unit_to_grams'].items():
                    print(f"    {unit}: {grams}g")
                sample_count += 1

if __name__ == "__main__":
    main()
