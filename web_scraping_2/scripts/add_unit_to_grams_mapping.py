#!/usr/bin/env python3
"""
all_foods_default_unit_calories.jsonを複製し、各食材にunit対応g数情報を追加
"""

import json
import re
from pathlib import Path
from collections import OrderedDict

def extract_serving_info(file_path, title_full_name):
    """指定した食材の【Serving情報】からunit→g数のマッピングを抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 食材のセクションを見つける
    # title_full_nameをエスケープ（特殊文字対応）
    escaped_name = re.escape(title_full_name)
    pattern = rf'\d+\.\s*{escaped_name}\n[\d,.]+cals'

    match = re.search(pattern, content)
    if not match:
        return None, []

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
        return None, []

    serving_info = serving_match.group(1)

    # unit→g数のマッピングを作成
    unit_to_grams = OrderedDict()
    failed_lines = []  # パース失敗した行を記録

    # " / "を含む行を探す
    calorie_pattern = r' [\d,.]+cals'
    gram_pattern = r'^([\d,.]+) g'

    for line in serving_info.split('\n'):
        line = line.strip()

        if ' / ' not in line:
            continue

        # " / "で分割
        parts = line.split(' / ')
        if len(parts) != 2:
            failed_lines.append({
                'line': line,
                'reason': f'Split error: {len(parts)} parts instead of 2'
            })
            continue

        front_part = parts[0].strip()
        back_part = parts[1].strip()

        # 前半部分からカロリー部分を削除してunit名を取得
        unit_name = re.sub(calorie_pattern, '', front_part).strip()

        # 後半部分からg数を抽出
        gram_match = re.match(gram_pattern, back_part)
        if not gram_match:
            failed_lines.append({
                'line': line,
                'reason': f'Gram pattern not matched in back_part: {repr(back_part)}',
                'front_part': front_part,
                'back_part': back_part,
                'unit_name': unit_name
            })
            continue

        # g数をfloatに変換（カンマ除去）
        try:
            gram_value = float(gram_match.group(1).replace(',', ''))
        except ValueError as e:
            failed_lines.append({
                'line': line,
                'reason': f'Float conversion error: {e}',
                'gram_string': gram_match.group(1)
            })
            continue

        # マッピングに追加
        unit_to_grams[unit_name] = gram_value

    # 分数・数値付き単位から基本単位を逆算して追加
    base_units_to_add = {}
    number_units_to_remove = []  # 削除する数字付き単位

    # イテレーション用にコピーを作成
    for unit_name, gram_value in list(unit_to_grams.items()):
        # 数値 + スペース + 単位名のパターン（例: "0.5 cup", "12 fl oz", "0.2 block"）
        match = re.match(r'^([\d.]+)\s+(.+)$', unit_name)
        if match:
            coefficient = float(match.group(1))
            base_unit = match.group(2)

            # 数字付き単位は常に削除リストに追加
            number_units_to_remove.append(unit_name)

            # 基本単位が存在せず、かつ追加予定にもない場合のみ計算して追加
            if base_unit not in unit_to_grams and base_unit not in base_units_to_add:
                # 基本単位のグラム数を計算
                base_gram_value = gram_value / coefficient
                base_units_to_add[base_unit] = base_gram_value

    # 逆算した基本単位を追加
    for base_unit, base_gram_value in base_units_to_add.items():
        unit_to_grams[base_unit] = base_gram_value

    # 数字付き単位を削除
    for unit_name in number_units_to_remove:
        if unit_name in unit_to_grams:
            del unit_to_grams[unit_name]

    return (unit_to_grams if unit_to_grams else None), failed_lines

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
    all_failed_lines = []  # 全ての失敗行を記録

    # 各食材にunit_to_gramsを追加
    for food in data['foods']:
        # 除外食材はスキップ
        if food['status'] == 'excluded_no_nutrition':
            food['unit_to_grams'] = None
            excluded_count += 1
            continue

        # ファイルパスを構築
        file_path = templates_dir / food['file']

        # unit→g数マッピングを抽出（失敗行も取得）
        unit_to_grams, failed_lines = extract_serving_info(file_path, food['title_full_name'])

        if unit_to_grams:
            # 【栄養情報】のdefault_unitを優先: unit_to_gramsに存在しない場合、類似unitから追加
            default_unit = food.get('default_unit')
            if default_unit and default_unit not in unit_to_grams:
                # 類似するunitを探す（単数/複数形、複合単語の違いなど）
                similar_unit = None
                similar_gram_value = None

                for unit_name, gram_value in unit_to_grams.items():
                    # 完全一致ならスキップ（既にチェック済み）
                    if unit_name == default_unit:
                        continue

                    # 単数/複数形の関係をチェック
                    # 例: "cracker" vs "crackers", "spear (1/2" base)" vs "spears (1/2" base)"
                    if ' ' in default_unit or ' ' in unit_name:
                        # 複合単語の場合: 最初または最後の単語が単数/複数の関係
                        default_parts = default_unit.split()
                        unit_parts = unit_name.split()

                        # 単語数が同じ場合のみチェック
                        if len(default_parts) == len(unit_parts):
                            # 全ての単語が一致するか、単数/複数の関係かチェック
                            is_similar = True
                            for i in range(len(default_parts)):
                                d_word = default_parts[i]
                                u_word = unit_parts[i]

                                # 完全一致
                                if d_word == u_word:
                                    continue
                                # 単数 vs 複数 (単純な's'の追加/削除)
                                elif d_word + 's' == u_word or u_word + 's' == d_word:
                                    continue
                                else:
                                    is_similar = False
                                    break

                            if is_similar:
                                similar_unit = unit_name
                                similar_gram_value = gram_value
                                break
                    else:
                        # 単純な単語の場合: 単数/複数の関係
                        if default_unit + 's' == unit_name or unit_name + 's' == default_unit:
                            similar_unit = unit_name
                            similar_gram_value = gram_value
                            break

                # 類似unitが見つかった場合、default_unitをキーとして追加
                if similar_unit and similar_gram_value is not None:
                    unit_to_grams[default_unit] = similar_gram_value

            food['unit_to_grams'] = unit_to_grams
            success_count += 1
            if failed_lines:
                print(f"⚠️  {food['food_name']}: {len(unit_to_grams)}個のunit取得（{len(failed_lines)}行失敗）")
            else:
                print(f"✅ {food['food_name']}: {len(unit_to_grams)}個のunit取得")
        else:
            food['unit_to_grams'] = {}
            failed_count += 1
            print(f"⚠️  {food['food_name']}: Serving情報なし")

        # 失敗行を記録
        if failed_lines:
            all_failed_lines.append({
                'food_name': food['food_name'],
                'file': food['file'],
                'default_unit': food['default_unit'],
                'failed_lines': failed_lines
            })

    # メタデータを更新
    data['metadata']['description'] = 'All foods with default unit, calories, and unit-to-grams mapping'

    # 新しいJSONファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 失敗行の情報をJSONファイルに保存
    if all_failed_lines:
        failed_lines_file = Path(__file__).parent.parent / "output" / "unit_to_grams_failed_lines.json"
        failed_report = {
            'total_foods_with_failures': len(all_failed_lines),
            'total_failed_lines': sum(len(item['failed_lines']) for item in all_failed_lines),
            'foods': all_failed_lines
        }
        with open(failed_lines_file, 'w', encoding='utf-8') as f:
            json.dump(failed_report, f, ensure_ascii=False, indent=2)
        print(f"\n⚠️  失敗行レポート: {failed_lines_file}")

    print("\n" + "=" * 80)
    print("処理完了！")
    print("=" * 80)
    print(f"総食材数: {len(data['foods'])}")
    print(f"成功: {success_count}件")
    print(f"失敗: {failed_count}件")
    print(f"除外: {excluded_count}件")
    if all_failed_lines:
        print(f"パース失敗行あり: {len(all_failed_lines)}食材")
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
