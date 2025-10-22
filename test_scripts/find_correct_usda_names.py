#!/usr/bin/env python
"""
food_name_mappings3.jsonの存在しないUSDA名に対して正しい名前を探す
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# パス設定
project_root = Path(__file__).parent.parent
usda_names_dir = project_root / "usda_database" / "names_list"

def load_usda_database():
    """すべてのUSDAデータベースファイルを読み込み（番号を除外）"""
    db_files = {
        'survey_fndds': 'survey_food_names.txt',
        'sr_legacy': 'sr_legacy_food_names.txt',
        'foundation': 'foundation_food_names.txt',
        'branded': 'branded_food_names.txt'
    }

    all_items = {}
    for db_name, file_name in db_files.items():
        db_path = usda_names_dir / file_name
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        # 行頭の番号とドットを除去
                        match = re.match(r'^\d+\.\s+(.+)$', line)
                        if match:
                            food_name = match.group(1)
                            if food_name not in all_items:
                                all_items[food_name] = db_name
    return all_items

def find_similar_names(target, usda_items, limit=5):
    """類似する名前を検索"""
    results = []
    target_lower = target.lower()

    # キーワードを抽出
    keywords = []

    # 特定のパターンで検索
    if "bagel" in target_lower:
        keywords = ["bagel"]
        if "plain" in target_lower:
            # plainは基本形なので、修飾語のないものを優先
            for name, db in usda_items.items():
                name_lower = name.lower()
                if name_lower == "bagel":
                    results.append((100, name, db))
                elif name_lower.startswith("bagel") and "," not in name:
                    results.append((50, name, db))
                elif "bagel" in name_lower:
                    results.append((10, name, db))

    elif "mayonnaise" in target_lower:
        keywords = ["mayonnaise"]
        for name, db in usda_items.items():
            name_lower = name.lower()
            if "mayonnaise" in name_lower:
                # 短い名前を優先（シンプルなものが汎用的）
                score = 100 - len(name)
                results.append((score, name, db))

    elif "bacon" in target_lower:
        keywords = ["bacon"]
        for name, db in usda_items.items():
            name_lower = name.lower()
            if "bacon" in name_lower:
                score = 0
                if "cooked" in target_lower and "cooked" in name_lower:
                    score += 50
                if name_lower.startswith("bacon"):
                    score += 30
                # Canadian baconなど修飾語付きは減点
                if "canadian" not in name_lower and "turkey" not in name_lower:
                    score += 20
                results.append((score, name, db))

    elif "butter" in target_lower:
        keywords = ["butter"]
        for name, db in usda_items.items():
            name_lower = name.lower()
            if name_lower.startswith("butter"):
                score = 0
                if "unsalted" in target_lower and "unsalted" in name_lower:
                    score += 50
                elif "salted" in target_lower and "salted" in name_lower and "unsalted" not in name_lower:
                    score += 50
                # シンプルなものを優先
                if "," not in name:
                    score += 30
                results.append((score, name, db))

    elif "sausage" in target_lower and "breakfast" in target_lower:
        for name, db in usda_items.items():
            name_lower = name.lower()
            if "sausage" in name_lower:
                score = 0
                if "breakfast" in name_lower:
                    score += 50
                if "patty" in target_lower and "patty" in name_lower:
                    score += 30
                elif "link" in target_lower and "link" in name_lower:
                    score += 30
                if "pork" in target_lower and "pork" in name_lower:
                    score += 20
                results.append((score, name, db))

    elif "oatmeal" in target_lower:
        for name, db in usda_items.items():
            name_lower = name.lower()
            if "oatmeal" in name_lower:
                score = 0
                if "cooked" in target_lower and "cooked" in name_lower:
                    score += 30
                elif "instant" in target_lower and "instant" in name_lower:
                    score += 30
                # NFSがあれば優先
                if "nfs" in name_lower:
                    score += 50
                results.append((score, name, db))

    elif "salad dressing" in target_lower:
        for name, db in usda_items.items():
            name_lower = name.lower()
            if "salad dressing" in name_lower:
                score = 0
                if "nfs" in target_lower and "nfs" in name_lower:
                    score += 30
                    if "for salads" in name_lower:
                        score += 20  # for saladsが一般的
                results.append((score, name, db))

    elif "fish" in target_lower and ("battered" in target_lower or "breaded" in target_lower):
        for name, db in usda_items.items():
            name_lower = name.lower()
            if "fish" in name_lower and ("battered" in name_lower or "breaded" in name_lower):
                score = 0
                if "fried" in target_lower and "fried" in name_lower:
                    score += 30
                results.append((score, name, db))

    elif "shrimp" in target_lower and "breaded" in target_lower:
        for name, db in usda_items.items():
            name_lower = name.lower()
            if "shrimp" in name_lower and "breaded" in name_lower:
                score = 0
                if "fried" in target_lower and "fried" in name_lower:
                    score += 30
                results.append((score, name, db))

    elif "onion ring" in target_lower:
        for name, db in usda_items.items():
            name_lower = name.lower()
            if "onion ring" in name_lower:
                score = 0
                if "breaded" in target_lower and "breaded" in name_lower:
                    score += 20
                if "fried" in target_lower and "fried" in name_lower:
                    score += 20
                results.append((score, name, db))

    elif "pancake" in target_lower:
        for name, db in usda_items.items():
            name_lower = name.lower()
            if "pancake" in name_lower:
                score = 0
                if "plain" in target_lower and "plain" in name_lower:
                    score += 30
                # NFSがあれば優先
                if "nfs" in name_lower:
                    score += 50
                results.append((score, name, db))

    elif "syrup" in target_lower:
        for name, db in usda_items.items():
            name_lower = name.lower()
            if "syrup" in name_lower:
                score = 0
                if "maple" in target_lower and "maple" in name_lower:
                    score += 30
                elif "pancake" in target_lower and "pancake" in name_lower:
                    score += 30
                results.append((score, name, db))

    # ソートして上位を返す
    results.sort(key=lambda x: (-x[0], len(x[1])))  # スコア降順、文字長昇順
    return results[:limit]

def main():
    print("="*80)
    print("food_name_mappings3.jsonの存在しないUSDA名の修正対応表")
    print("="*80)
    print()

    # エラーレポートを読み込み
    error_file = Path(__file__).parent / "mappings" / "food_name_mappings3_detailed_validation_errors.json"

    if not error_file.exists():
        print("エラーファイルが見つかりません。先に検証を実行してください。")
        return

    with open(error_file, 'r', encoding='utf-8') as f:
        error_data = json.load(f)

    # USDAデータベースを読み込み
    print("📚 USDAデータベースを読み込み中...")
    usda_items = load_usda_database()
    print(f"✅ 総USDA項目数: {len(usda_items):,}\n")

    # 存在しない項目を収集
    invalid_names = set()

    # デフォルトUSDAの無効項目
    for item in error_data.get('invalid_defaults', []):
        invalid_names.add(item['usda_name'])

    # all_usda_mappingsの無効項目
    for item in error_data.get('invalid_all_mappings', []):
        invalid_names.add(item['usda_name'])

    # 修正対応表を作成
    correction_table = {}

    print("🔍 各項目の正しいUSDA名を検索中...\n")

    for invalid_name in sorted(invalid_names):
        print(f"❌ 無効: \"{invalid_name}\"")
        similar = find_similar_names(invalid_name, usda_items)

        if similar:
            # 最もスコアが高いものを選択
            best = similar[0]
            correction_table[invalid_name] = {
                "original": invalid_name,
                "corrected": best[1],
                "database": best[2],
                "alternatives": [{"name": s[1], "database": s[2], "score": s[0]} for s in similar]
            }
            print(f"  ✅ 修正案: \"{best[1]}\" ({best[2]})")

            # 他の候補も表示
            if len(similar) > 1:
                print(f"  他の候補:")
                for i, (score, name, db) in enumerate(similar[1:], 1):
                    print(f"    {i}. \"{name}\" ({db}, score: {score})")
        else:
            print(f"  ⚠️  類似項目が見つかりません")
            correction_table[invalid_name] = {
                "original": invalid_name,
                "corrected": None,
                "database": None,
                "alternatives": []
            }
        print()

    # 対応表をJSON形式で保存
    output_file = Path(__file__).parent / "mappings" / "food_name_corrections.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(correction_table, f, ensure_ascii=False, indent=2)

    print("="*80)
    print(f"📝 修正対応表を保存: {output_file}")
    print(f"   総修正項目数: {len(correction_table)}")

    # サマリー表示
    print("\n📊 修正対応表サマリー:")
    print("-"*40)

    for invalid_name, correction in correction_table.items():
        if correction['corrected']:
            print(f"{invalid_name:40} → {correction['corrected']}")
        else:
            print(f"{invalid_name:40} → (修正案なし)")

if __name__ == "__main__":
    main()