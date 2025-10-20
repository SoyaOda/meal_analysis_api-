#!/usr/bin/env python3
"""
飲料カテゴリの重複を修正するスクリプト
"""
import os

def main():
    # ファイルパスの設定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    selected_food_file = os.path.join(base_dir, "display_name_generation", "selected_food_list.txt")

    # ファイルを読み込む
    with open(selected_food_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 修正処理
    result_lines = []
    skip_non_alcoholic_beverages = False
    water_nfs_already_exists = False

    for i, line in enumerate(lines):
        original_line = line.rstrip('\n')

        # 【Non‑alcoholic Beverages】セクションをスキップ
        if '【Non‑alcoholic Beverages】' in line or '【Non-alcoholic Beverages】' in line:
            skip_non_alcoholic_beverages = True
            # 次の【】が出るまでスキップ
            continue

        # 新しいセクションが始まったらスキップを解除
        if skip_non_alcoholic_beverages and line.startswith('【') and 'Non' not in line and 'alcoholic' not in line:
            skip_non_alcoholic_beverages = False

        # スキップ中の行は追加しない
        if skip_non_alcoholic_beverages:
            if line.strip() == '* Water, NFS':
                # Water, NFSがすでに【Beverages — non-alcoholic】にあるか確認
                water_nfs_already_exists = True
            continue

        result_lines.append(original_line)

    # Water, NFSを【Beverages — non-alcoholic】に追加（まだない場合）
    if water_nfs_already_exists and not any('* Water, NFS' in line for line in result_lines):
        # 【Beverages — non-alcoholic】セクションを探して追加
        for i, line in enumerate(result_lines):
            if '【Beverages — non-alcoholic】' in line or '【Beverages - non-alcoholic】' in line:
                # 次の空行を探す
                j = i + 1
                while j < len(result_lines) and result_lines[j].strip():
                    j += 1
                # Water, NFSを最初に追加
                result_lines.insert(i + 2, '* Water, NFS')
                break

    # 重複する飲料アイテムも削除（Water beverage, fruit flavoredなど）
    # これは【Beverages — non-alcoholic】内でも重複している可能性があるため
    seen_beverages = set()
    final_lines = []
    in_beverages_section = False

    for line in result_lines:
        if '【Beverages — non-alcoholic】' in line or '【Beverages - non-alcoholic】' in line:
            in_beverages_section = True
        elif line.startswith('【'):
            in_beverages_section = False

        if in_beverages_section and line.startswith('* '):
            beverage_name = line.strip()
            if beverage_name not in seen_beverages:
                seen_beverages.add(beverage_name)
                final_lines.append(line)
        else:
            final_lines.append(line)

    # ファイルを書き戻す
    with open(selected_food_file, 'w', encoding='utf-8') as f:
        for line in final_lines:
            f.write(line + '\n')

    print("飲料カテゴリの重複を修正しました")
    print(f"削除したセクション: 【Non‑alcoholic Beverages】")

    # カテゴリ数をカウント
    categories = [line for line in final_lines if line.startswith('【')]
    print(f"カテゴリ総数: {len(categories)}")

    # 食品数をカウント
    food_count = sum(1 for line in final_lines if line.startswith('* '))
    print(f"食品総数: {food_count}件")

if __name__ == "__main__":
    main()