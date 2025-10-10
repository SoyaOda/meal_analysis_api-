#!/usr/bin/env python3
"""
全食材の栄養素情報を検証するスクリプト
1. 数字+単位の行を抽出（Serving Size行は除外）
2. 行のフォーマットを検証
3. 同じ栄養素名で単位が統一されているか確認
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_nutrition_info(file_path, food_name):
    """指定した食材の【栄養情報】セクションを抽出"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 食材のセクションを見つける
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

    # 【栄養情報】セクションを抽出
    nutrition_match = re.search(r'【栄養情報】\n(.*?)(?=\n【|$)', food_content, re.DOTALL)
    if not nutrition_match:
        return None

    return nutrition_match.group(1)

def parse_nutrition_lines(nutrition_info):
    """栄養情報から栄養素行を抽出・解析"""
    # 除外するパターン
    exclude_patterns = [
        r'^Serving Size',
        r'^Amount per serving',
        r'^Calories\s+\d+cals',
        r'^% Daily Value',
        r'^Nutrition Facts',
        r'^\s*$',  # 空行
        r'^grade\s*[A-F]',
        r'^\*'
    ]

    # 栄養素行のパターン
    # 栄養素名 + 数値（小数可、コンマ可） + 単位 + オプションのパーセント
    nutrient_pattern = r'^([A-Za-z\s\-\']+?)\s+([\d,.]+)(g|mg|mcg|μg|IU|kcal)\s*(?:(\d+)%)?'

    results = []

    for line in nutrition_info.split('\n'):
        line = line.strip()

        # 除外パターンに一致する行はスキップ
        if any(re.match(pattern, line) for pattern in exclude_patterns):
            continue

        # 栄養素行にマッチするか確認
        match = re.match(nutrient_pattern, line)
        if match:
            nutrient_name = match.group(1).strip()
            value = match.group(2)
            unit = match.group(3)
            percent = match.group(4) if match.group(4) else None

            results.append({
                'line': line,
                'nutrient_name': nutrient_name,
                'value': value,
                'unit': unit,
                'percent': percent
            })

    return results

def main():
    templates_dir = Path(__file__).parent.parent / "manual_input_templates"

    # 栄養素名ごとの単位を記録
    nutrient_units = defaultdict(set)

    # 全食材の栄養素情報を記録
    all_nutrients = []

    # 形式エラーを記録
    format_errors = []

    # 単位の不一致を記録
    unit_mismatches = []

    total_foods = 0
    foods_with_nutrition = 0
    total_nutrient_lines = 0

    print("=" * 80)
    print("栄養素情報検証開始")
    print("=" * 80)

    # 全ファイルを処理
    for file_path in sorted(templates_dir.glob('*_manual_input.txt')):
        print(f"\n処理中: {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 食材ごとに分割
        food_pattern = r'(\d+)\.\s*(.+?),\s*(.+?)\n([\d,]+)cals'

        for match in re.finditer(food_pattern, content):
            total_foods += 1
            food_name = match.group(2).strip()

            # 栄養情報を抽出
            nutrition_info = extract_nutrition_info(file_path, food_name)

            if not nutrition_info:
                continue

            foods_with_nutrition += 1

            # 栄養素行を解析
            nutrients = parse_nutrition_lines(nutrition_info)

            if not nutrients:
                # 栄養情報があるのに栄養素行が抽出できない場合
                format_errors.append({
                    'food_name': food_name,
                    'file': file_path.name,
                    'issue': '栄養素行が抽出できない',
                    'nutrition_info': nutrition_info[:200]  # 最初の200文字のみ
                })
                continue

            total_nutrient_lines += len(nutrients)

            # 栄養素名と単位を記録
            for nutrient in nutrients:
                nutrient_name = nutrient['nutrient_name']
                unit = nutrient['unit']

                # 栄養素名ごとに単位を記録
                nutrient_units[nutrient_name].add(unit)

                # 全栄養素情報を記録
                all_nutrients.append({
                    'food_name': food_name,
                    'file': file_path.name,
                    'nutrient_name': nutrient_name,
                    'value': nutrient['value'],
                    'unit': unit,
                    'percent': nutrient['percent'],
                    'line': nutrient['line']
                })

    # 単位の不一致をチェック
    for nutrient_name, units in nutrient_units.items():
        if len(units) > 1:
            unit_mismatches.append({
                'nutrient_name': nutrient_name,
                'units': sorted(units)
            })

    # 結果を表示
    print("\n" + "=" * 80)
    print("検証結果")
    print("=" * 80)
    print(f"総食材数: {total_foods}")
    print(f"栄養情報がある食材: {foods_with_nutrition}")
    print(f"抽出された栄養素行の総数: {total_nutrient_lines}")
    print(f"ユニークな栄養素名の数: {len(nutrient_units)}")

    # 形式エラーの表示
    if format_errors:
        print(f"\n⚠️  形式エラー: {len(format_errors)}件")
        for i, error in enumerate(format_errors[:5], 1):  # 最初の5件のみ表示
            print(f"\n{i}. {error['food_name']} ({error['file']})")
            print(f"   問題: {error['issue']}")
            print(f"   栄養情報の一部: {error['nutrition_info'][:100]}...")
    else:
        print("\n✅ 形式エラー: なし")

    # 単位の不一致を表示
    if unit_mismatches:
        print(f"\n⚠️  単位の不一致: {len(unit_mismatches)}件")
        for mismatch in unit_mismatches:
            print(f"\n栄養素名: {mismatch['nutrient_name']}")
            print(f"  使用されている単位: {', '.join(mismatch['units'])}")

            # この栄養素を含む食材をいくつか表示
            examples = [n for n in all_nutrients if n['nutrient_name'] == mismatch['nutrient_name']][:3]
            print(f"  例:")
            for ex in examples:
                print(f"    - {ex['food_name']}: {ex['value']}{ex['unit']} ({ex['file']})")
    else:
        print("\n✅ 単位の不一致: なし（全ての栄養素で単位が統一されています）")

    # レポートファイルに保存
    report_file = Path(__file__).parent.parent / "output" / "NUTRITION_VALUES_VERIFICATION_REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 栄養素情報検証レポート\n\n")
        f.write("## 概要\n\n")
        f.write(f"- 総食材数: {total_foods}\n")
        f.write(f"- 栄養情報がある食材: {foods_with_nutrition}\n")
        f.write(f"- 抽出された栄養素行の総数: {total_nutrient_lines}\n")
        f.write(f"- ユニークな栄養素名の数: {len(nutrient_units)}\n\n")

        f.write("## 栄養素名と単位の一覧\n\n")
        for nutrient_name, units in sorted(nutrient_units.items()):
            f.write(f"- **{nutrient_name}**: {', '.join(sorted(units))}\n")

        if unit_mismatches:
            f.write(f"\n## 単位の不一致 ({len(unit_mismatches)}件)\n\n")
            for mismatch in unit_mismatches:
                f.write(f"### {mismatch['nutrient_name']}\n\n")
                f.write(f"使用されている単位: {', '.join(mismatch['units'])}\n\n")

                # この栄養素を含む全ての食材を表示
                examples = [n for n in all_nutrients if n['nutrient_name'] == mismatch['nutrient_name']]
                f.write(f"該当食材 ({len(examples)}件):\n\n")
                for ex in examples[:10]:  # 最初の10件
                    f.write(f"- {ex['food_name']}: {ex['value']}{ex['unit']} ({ex['file']})\n")
                if len(examples) > 10:
                    f.write(f"- ... 他{len(examples) - 10}件\n")
                f.write("\n")

        if format_errors:
            f.write(f"\n## 形式エラー ({len(format_errors)}件)\n\n")
            for error in format_errors:
                f.write(f"### {error['food_name']}\n\n")
                f.write(f"- ファイル: {error['file']}\n")
                f.write(f"- 問題: {error['issue']}\n")
                f.write(f"- 栄養情報の一部:\n```\n{error['nutrition_info'][:200]}\n```\n\n")

    print(f"\nレポートを保存: {report_file}")

if __name__ == "__main__":
    main()
