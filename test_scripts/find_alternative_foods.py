#!/usr/bin/env python
"""
USDAデータベースに存在しない食品の代替品を検索
"""

import re
from pathlib import Path
from collections import defaultdict

# パス設定
project_root = Path(__file__).parent.parent
usda_names_dir = project_root / "usda_database" / "names_list"

def load_usda_database(file_path):
    """USDAデータベースファイルを読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def search_alternatives(target_foods, usda_items):
    """類似する食品名を検索"""
    results = {}

    for target in target_foods:
        matches = defaultdict(list)
        target_lower = target.lower()

        # キーワードを抽出
        keywords = []
        if "carrots" in target_lower or "carrot" in target_lower:
            keywords = ["carrot"]
        elif "mixed vegetables" in target_lower:
            keywords = ["mixed vegetable", "vegetable", "mixed"]

        for item in usda_items:
            item_lower = item.lower()

            # キーワードマッチング
            for keyword in keywords:
                if keyword in item_lower:
                    # スコアを計算（より具体的な一致ほど高スコア）
                    score = 0
                    if "shredded" in target_lower and "shredded" in item_lower:
                        score += 10
                    if "cooked" in target_lower and "cooked" in item_lower:
                        score += 10
                    if "raw" in target_lower and "raw" in item_lower:
                        score += 10
                    if "mixed" in target_lower and "mixed" in item_lower:
                        score += 5

                    # 基本スコア（キーワードの位置）
                    if item_lower.startswith(keyword):
                        score += 3

                    matches[score].append(item)

        results[target] = matches

    return results

def main():
    print("="*80)
    print("USDAデータベースに存在しない食品の代替検索")
    print("="*80)
    print()

    # ターゲット食品
    missing_foods = [
        "Carrots, shredded",
        "Mixed vegetables, cooked"
    ]

    print("検索対象:")
    for food in missing_foods:
        print(f"  - {food}")
    print()

    # 各データベースを検索
    db_files = {
        'survey_food_names.txt': 'Survey (FNDDS)',
        'sr_legacy_food_names.txt': 'SR Legacy',
        'foundation_food_names.txt': 'Foundation Foods',
        'branded_food_names.txt': 'Branded Foods'
    }

    all_alternatives = defaultdict(list)

    for file_name, db_label in db_files.items():
        db_path = usda_names_dir / file_name
        if db_path.exists():
            print(f"\n検索中: {db_label}")
            print("-" * 40)

            items = load_usda_database(db_path)
            results = search_alternatives(missing_foods, items)

            for target, matches in results.items():
                if matches:
                    print(f"\n'{target}' の候補:")

                    # スコア順にソート（高い順）
                    sorted_scores = sorted(matches.keys(), reverse=True)
                    shown = 0
                    for score in sorted_scores[:5]:  # 上位5スコアまで
                        for item in matches[score][:3]:  # 各スコアで最大3件
                            if shown < 10:  # 全体で最大10件
                                print(f"  [{score:2d}] {item}")
                                all_alternatives[target].append((score, item, db_label))
                                shown += 1

    # 最終的な推奨
    print("\n" + "="*80)
    print("📌 推奨される代替品")
    print("="*80)

    for target in missing_foods:
        print(f"\n【{target}】")

        if target == "Carrots, shredded":
            # Carrotsの最適な代替を探す
            carrot_alternatives = []
            for score, item, db in all_alternatives[target]:
                if "carrot" in item.lower():
                    carrot_alternatives.append((score, item, db))

            # ソートして上位を表示
            carrot_alternatives.sort(reverse=True, key=lambda x: x[0])

            print("  推奨候補:")
            for i, (score, item, db) in enumerate(carrot_alternatives[:5], 1):
                print(f"    {i}. \"{item}\" ({db})")

            # 最も適切なものを提案
            if carrot_alternatives:
                if any("grated" in item[1].lower() for item in carrot_alternatives):
                    best = next(item for item in carrot_alternatives if "grated" in item[1].lower())
                    print(f"\n  ✅ 最適な代替: \"{best[1]}\"")
                    print(f"     理由: 'shredded'と'grated'は類似の調理法")
                elif any("sliced" in item[1].lower() or "cut" in item[1].lower() for item in carrot_alternatives):
                    best = next(item for item in carrot_alternatives if "sliced" in item[1].lower() or "cut" in item[1].lower())
                    print(f"\n  ✅ 代替案: \"{best[1]}\"")
                    print(f"     理由: カット済みの人参")
                else:
                    print(f"\n  ✅ 代替案: \"Carrots, raw\" または \"Carrots, cooked\"")
                    print(f"     理由: 基本的な人参（調理法の指定なし）")

        elif target == "Mixed vegetables, cooked":
            # Mixed vegetablesの最適な代替を探す
            mixed_alternatives = []
            for score, item, db in all_alternatives[target]:
                if "mixed" in item.lower() or "vegetable" in item.lower():
                    mixed_alternatives.append((score, item, db))

            # ソートして上位を表示
            mixed_alternatives.sort(reverse=True, key=lambda x: x[0])

            print("  推奨候補:")
            for i, (score, item, db) in enumerate(mixed_alternatives[:5], 1):
                print(f"    {i}. \"{item}\" ({db})")

            # 最も適切なものを提案
            if mixed_alternatives:
                if any("mixed vegetables" in item[1].lower() for item in mixed_alternatives):
                    best = next(item for item in mixed_alternatives if "mixed vegetables" in item[1].lower())
                    print(f"\n  ✅ 最適な代替: \"{best[1]}\"")
                elif any("vegetable" in item[1].lower() and "cooked" in item[1].lower() for item in mixed_alternatives):
                    best = next(item for item in mixed_alternatives if "vegetable" in item[1].lower() and "cooked" in item[1].lower())
                    print(f"\n  ✅ 代替案: \"{best[1]}\"")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()