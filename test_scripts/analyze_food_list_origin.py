#!/usr/bin/env python
"""
food_names_list.txtの食品名がどのUSDAデータベースに存在するかを分析
"""

import re
from pathlib import Path
from collections import defaultdict, Counter

# パス設定
project_root = Path(__file__).parent.parent
food_names_list_path = project_root / "test_scripts" / "food_names_list" / "food_names_list.txt"
usda_names_dir = project_root / "usda_database" / "names_list"

def load_food_names(file_path):
    """食品名リストを読み込み（セクションヘッダーを除外）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    foods = []
    for line in lines:
        line = line.strip()
        # アスタリスクで始まる行が食品名
        if line.startswith('* '):
            food_name = line[2:].strip()  # "* "を削除
            if food_name:
                foods.append(food_name)
    return foods

def load_usda_database(file_path):
    """USDAデータベースファイルを読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def main():
    print("="*80)
    print("食品名リストの由来分析")
    print("="*80)
    print()

    # food_names_list.txtを読み込み
    print(f"読み込み中: {food_names_list_path}")
    food_items = load_food_names(food_names_list_path)
    print(f"✅ 食品アイテム数: {len(food_items)}")
    print()

    # USDAデータベースを読み込み
    usda_databases = {}
    db_names = {
        'branded_food_names.txt': 'Branded Foods',
        'foundation_food_names.txt': 'Foundation Foods',
        'sr_legacy_food_names.txt': 'SR Legacy',
        'survey_food_names.txt': 'Survey (FNDDS)'
    }

    print("USDAデータベースを読み込み中...")
    for file_name, db_label in db_names.items():
        db_path = usda_names_dir / file_name
        if db_path.exists():
            usda_databases[db_label] = load_usda_database(db_path)
            print(f"  {db_label}: {len(usda_databases[db_label]):,} items")
    print()

    # 各食品がどのデータベースに存在するか確認
    found_in = defaultdict(list)  # food -> [databases]
    not_found = []

    for food in food_items:
        found = False
        for db_name, db_items in usda_databases.items():
            if food in db_items:
                found_in[food].append(db_name)
                found = True
        if not found:
            not_found.append(food)

    # 統計を集計
    print("="*80)
    print("📊 統計結果")
    print("="*80)
    print()

    # 全体統計
    print("【全体統計】")
    print(f"総食品数: {len(food_items)}")
    print(f"USDAデータベースに存在: {len(found_in)} ({100*len(found_in)/len(food_items):.1f}%)")
    print(f"USDAデータベースに存在しない: {len(not_found)} ({100*len(not_found)/len(food_items):.1f}%)")
    print()

    # データベース別統計
    db_counter = Counter()
    for food, dbs in found_in.items():
        for db in dbs:
            db_counter[db] += 1

    print("【データベース別出現回数】")
    for db_name in db_names.values():
        count = db_counter.get(db_name, 0)
        percentage = 100 * count / len(food_items) if len(food_items) > 0 else 0
        print(f"  {db_name:20s}: {count:4d} ({percentage:5.1f}%)")
    print()

    # 重複（複数のDBに存在）
    multiple_db_foods = {food: dbs for food, dbs in found_in.items() if len(dbs) > 1}
    print(f"【複数のデータベースに存在】: {len(multiple_db_foods)}件")
    if multiple_db_foods:
        # 最初の5件を表示
        for i, (food, dbs) in enumerate(list(multiple_db_foods.items())[:5], 1):
            print(f"  {i}. \"{food}\" -> {', '.join(dbs)}")
        if len(multiple_db_foods) > 5:
            print(f"  ... 他 {len(multiple_db_foods) - 5} 件")
    print()

    # USDAに存在しない食品
    print(f"【USDAデータベースに存在しない食品】: {len(not_found)}件")
    if not_found:
        print("最初の20件:")
        for i, food in enumerate(not_found[:20], 1):
            print(f"  {i:2d}. {food}")
        if len(not_found) > 20:
            print(f"  ... 他 {len(not_found) - 20} 件")
    print()

    # カテゴリ別分析（NFS, NSなどの特殊表記）
    special_notations = {
        'NFS': [],  # Not Further Specified
        'NS': [],   # Not Specified
        'NEC': [],  # Not Elsewhere Classified
    }

    for food in food_items:
        for notation in special_notations:
            if f", {notation}" in food or f" {notation} " in food:
                special_notations[notation].append(food)

    print("【特殊表記を含む食品】")
    for notation, foods in special_notations.items():
        print(f"  {notation}: {len(foods)}件")
    print()

    # 結果をファイルに保存
    output_path = project_root / "test_scripts" / "output" / "food_list_origin_analysis.txt"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("食品名リストの由来分析レポート\n")
        f.write("="*80 + "\n\n")

        f.write(f"総食品数: {len(food_items)}\n")
        f.write(f"USDAデータベースに存在: {len(found_in)} ({100*len(found_in)/len(food_items):.1f}%)\n")
        f.write(f"USDAデータベースに存在しない: {len(not_found)} ({100*len(not_found)/len(food_items):.1f}%)\n\n")

        f.write("データベース別出現回数:\n")
        for db_name in db_names.values():
            count = db_counter.get(db_name, 0)
            percentage = 100 * count / len(food_items) if len(food_items) > 0 else 0
            f.write(f"  {db_name:20s}: {count:4d} ({percentage:5.1f}%)\n")
        f.write("\n")

        if not_found:
            f.write(f"USDAデータベースに存在しない食品 ({len(not_found)}件):\n")
            for food in not_found:
                f.write(f"  - {food}\n")

    print(f"✅ 詳細レポートを保存しました: {output_path}")
    print("="*80)

if __name__ == "__main__":
    main()