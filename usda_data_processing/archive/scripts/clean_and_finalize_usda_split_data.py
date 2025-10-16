#!/usr/bin/env python3
"""
USDA食材データの最終クリーンアップ処理

処理内容:
1. NS as toを含む食材の削除（Regular Yogurt除く）
2. Regular Yogurtのdescription修正
3. 文字列"None"をPythonのNone（null）に統一
4. 元のカテゴリ構造にsearch_nameとdescriptionを追加
"""
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

# ファイルパス
RAW_SPLIT_INPUT = Path('/Users/odasoya/meal_analysis_api_2/usda_data_processing/output/usda_raw_ingredients_split.json')
PREPARED_SPLIT_INPUT = Path('/Users/odasoya/meal_analysis_api_2/usda_data_processing/output/usda_prepared_ingredients_split.json')

RAW_ORIGINAL_INPUT = Path('/Users/odasoya/meal_analysis_api_2/usda_data_processing/docs/usda_raw_ingredients_all.json')
PREPARED_ORIGINAL_INPUT = Path('/Users/odasoya/meal_analysis_api_2/usda_data_processing/docs/usda_prepared_ingredients_all.json')

RAW_OUTPUT = Path('/Users/odasoya/meal_analysis_api_2/usda_data_processing/output/usda_raw_ingredients_split_cleaned.json')
PREPARED_OUTPUT = Path('/Users/odasoya/meal_analysis_api_2/usda_data_processing/output/usda_prepared_ingredients_split_cleaned.json')

def clean_yogurt_description(original_name: str, description: str) -> Optional[str]:
    """Regular Yogurt (non-Greek) のdescriptionから 'NS as to type of milk' を削除"""
    # "Yogurt, Greek" はスキップ
    if "Greek" in original_name:
        return description

    # Regular Yogurt のdescription修正
    # パターン1: "NS as to type of milk, or flavor" → None
    if "NS as to type of milk, or flavor" in description or "NS as to type of milk or flavor" in description:
        return None

    # パターン2: "NS as to type of milk, plain" → "plain"
    if description == "NS as to type of milk, plain":
        return "plain"

    # パターン3: "NS as to type of milk, fruit" → "fruit"
    if description == "NS as to type of milk, fruit":
        return "fruit"

    # パターン4: "NS as to type of milk, flavors other than fruit" → "flavors other than fruit"
    if description == "NS as to type of milk, flavors other than fruit":
        return "flavors other than fruit"

    return description

def normalize_description(description: Optional[str]) -> Optional[str]:
    """
    descriptionフィールドの正規化
    - 文字列 "None" → Python None (null)
    - 空文字列 "" → None
    - "NFS" を削除（単独、または他の要素と組み合わせ）
    - 括弧とその内容を削除
    - その他の文字列 → そのまま
    """
    if description is None:
        return None

    if isinstance(description, str):
        # 文字列"None"をNoneに変換
        if description.strip() == "None":
            return None

        # 括弧とその内容を削除
        import re
        description = re.sub(r'\s*\([^)]*\)', '', description)

        # "NFS"を削除
        # パターン1: 単独の "NFS" → None
        if description.strip() == "NFS":
            return None

        # パターン2: "..., NFS" → "..."
        if description.endswith(", NFS"):
            description = description[:-5].strip()

        # パターン3: "NFS, ..." → "..."
        if description.startswith("NFS, "):
            description = description[5:].strip()

        # 空文字列もNoneに変換
        if description.strip() == "":
            return None

    return description


def extract_brand_or_variety(original_name: str) -> Optional[str]:
    """
    元の食材名から括弧内の情報（ブランド名や品種）を抽出
    
    例:
    - "Crackers, butter (Ritz)" → "Ritz"
    - "Milk, reduced fat (2%)" → "2%"
    - "Regular food name" → None
    """
    import re
    match = re.search(r'\(([^)]+)\)$', original_name.strip())
    if match:
        return match.group(1)
    return None

def process_split_data(split_items: list) -> tuple:
    """
    AIで生成したsplit dataを処理してfoodCodeでマップ化

    Returns:
        (foodcode_map, removed_count, modified_count, normalized_count)
    """
    foodcode_map = {}
    removed_count = 0
    modified_count = 0
    normalized_count = 0

    for item in split_items:
        original_name = item['original_name']
        food_code = item['foodCode']

        # "NS as to"を含むか確認
        if 'ns as to' in original_name.lower():
            # Regular Yogurt (非Greek) の4件は残して修正
            if original_name.startswith("Yogurt, NS as to") and "Greek" not in original_name:
                # descriptionを修正
                old_desc = item['description']
                new_desc = clean_yogurt_description(original_name, old_desc)

                if old_desc != new_desc:
                    print(f"✏️  修正: \"{original_name}\"")
                    print(f"    description: \"{old_desc}\" → {repr(new_desc)}")
                    modified_count += 1

                # 正規化
                new_desc = normalize_description(new_desc)
                if item['description'] != new_desc:
                    normalized_count += 1

                foodcode_map[food_code] = {
                    'search_name': item['search_name'],
                    'description': new_desc
                }
            else:
                # その他の"NS as to"アイテムは削除
                print(f"🗑️  削除: \"{original_name}\"")
                removed_count += 1
        else:
            # "NS as to"を含まないアイテムは保持
            # descriptionを正規化
            old_desc = item['description']
            new_desc = normalize_description(old_desc)

            if old_desc != new_desc:
                normalized_count += 1

            foodcode_map[food_code] = {
                'search_name': item['search_name'],
                'description': new_desc
            }

    return foodcode_map, removed_count, modified_count, normalized_count

def merge_with_original(original_data: dict, foodcode_map: dict) -> dict:
    """
    元のカテゴリ構造JSONにsearch_nameとdescriptionを追加
    """
    merged_data = {
        "metadata": original_data["metadata"].copy(),
        "categories": {}
    }

    # メタデータを更新
    merged_data["metadata"]["generated"] = datetime.now().isoformat()
    merged_data["metadata"]["note"] = "AIで生成したsearch_nameとdescriptionを含む"

    # 統計情報
    total_foods = 0
    matched_foods = 0
    brand_removed_count = 0

    # カテゴリごとに処理
    for category_name, category_data in original_data["categories"].items():
        updated_foods = []

        for food in category_data["foods"]:
            food_code = food["foodCode"]

            # foodCodeでマッチング
            if food_code in foodcode_map:
                # search_name、ai_description、brand_or_varietyを追加
                ai_description = foodcode_map[food_code]["description"]

                # 元の名前から括弧内の情報（ブランド名や品種）を抽出
                brand_or_variety = extract_brand_or_variety(food["description"])

                # ai_descriptionからブランド名を除去
                if brand_or_variety is not None and ai_description is not None:
                    # ai_descriptionを", "で分割してリスト化
                    desc_parts = [part.strip() for part in ai_description.split(", ")]
                    
                    # ブランド名と一致する要素を除去
                    filtered_parts = [part for part in desc_parts if part != brand_or_variety]
                    
                    # 除去が発生したかチェック
                    if len(filtered_parts) < len(desc_parts):
                        brand_removed_count += 1
                    
                    # 残った要素を結合
                    if filtered_parts:
                        ai_description = ", ".join(filtered_parts)
                    else:
                        ai_description = None

                # フィールドの順序を明示的に指定
                food_with_ai = {
                    "foodCode": food["foodCode"],
                    "description": food["description"],
                    "search_name": foodcode_map[food_code]["search_name"],
                    "ai_description": ai_description,
                    "brand_or_variety": brand_or_variety
                }

                updated_foods.append(food_with_ai)
                matched_foods += 1
            else:
                # マッチしない場合はスキップ（NS as toで削除された食材）
                pass

            total_foods += 1

        # カテゴリが空でない場合のみ追加
        if updated_foods:
            merged_data["categories"][category_name] = {
                "count": len(updated_foods),
                "foods": updated_foods
            }

    # メタデータを更新
    merged_data["metadata"]["total_foods"] = matched_foods
    merged_data["metadata"]["original_total_foods"] = total_foods
    merged_data["metadata"]["removed_foods"] = total_foods - matched_foods
    merged_data["metadata"]["brand_removed_from_ai_description"] = brand_removed_count

    return merged_data, matched_foods, total_foods

def main():
    print("="*80)
    print("USDA食材データの最終クリーンアップ")
    print("="*80)

    # Raw ingredients処理
    print("\n📂 Raw Ingredients処理中...")

    # AIで生成したsplit dataを読み込み
    with open(RAW_SPLIT_INPUT, 'r', encoding='utf-8') as f:
        raw_split_items = json.load(f)

    print(f"   AIで生成したデータ: {len(raw_split_items)}件")

    # split dataを処理してfoodCodeマップを作成
    raw_foodcode_map, raw_removed, raw_modified, raw_normalized = process_split_data(raw_split_items)

    print(f"\n   処理結果:")
    print(f"   - 削除: {raw_removed}件")
    print(f"   - 修正: {raw_modified}件")
    print(f"   - 正規化: {raw_normalized}件（文字列\"None\" → null）")
    print(f"   - マップ化: {len(raw_foodcode_map)}件")

    # 元のカテゴリ構造JSONを読み込み
    with open(RAW_ORIGINAL_INPUT, 'r', encoding='utf-8') as f:
        raw_original_data = json.load(f)

    # マージ
    print(f"\n   元のカテゴリ構造と統合中...")
    raw_merged, raw_matched, raw_total = merge_with_original(raw_original_data, raw_foodcode_map)

    print(f"   - 元データ: {raw_total}件")
    print(f"   - マッチ: {raw_matched}件")
    print(f"   - 最終: {raw_matched}件")

    # Prepared ingredients処理
    print("\n📂 Prepared Ingredients処理中...")

    with open(PREPARED_SPLIT_INPUT, 'r', encoding='utf-8') as f:
        prepared_split_items = json.load(f)

    print(f"   AIで生成したデータ: {len(prepared_split_items)}件")

    prepared_foodcode_map, prepared_removed, prepared_modified, prepared_normalized = process_split_data(prepared_split_items)

    print(f"\n   処理結果:")
    print(f"   - 削除: {prepared_removed}件")
    print(f"   - 修正: {prepared_modified}件")
    print(f"   - 正規化: {prepared_normalized}件（文字列\"None\" → null）")
    print(f"   - マップ化: {len(prepared_foodcode_map)}件")

    with open(PREPARED_ORIGINAL_INPUT, 'r', encoding='utf-8') as f:
        prepared_original_data = json.load(f)

    print(f"\n   元のカテゴリ構造と統合中...")
    prepared_merged, prepared_matched, prepared_total = merge_with_original(prepared_original_data, prepared_foodcode_map)

    print(f"   - 元データ: {prepared_total}件")
    print(f"   - マッチ: {prepared_matched}件")
    print(f"   - 最終: {prepared_matched}件")

    # 保存
    print("\n💾 保存中...")
    with open(RAW_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(raw_merged, f, ensure_ascii=False, indent=2)
    print(f"   ✅ {RAW_OUTPUT}")

    with open(PREPARED_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(prepared_merged, f, ensure_ascii=False, indent=2)
    print(f"   ✅ {PREPARED_OUTPUT}")

    # サマリー
    print("\n" + "="*80)
    print("📊 クリーンアップ完了サマリー")
    print("="*80)
    print(f"元データ総数: {raw_total + prepared_total}件")
    print(f"削除総数: {raw_removed + prepared_removed}件")
    print(f"修正総数: {raw_modified + prepared_modified}件")
    print(f"正規化総数: {raw_normalized + prepared_normalized}件")
    print(f"最終データ総数: {raw_matched + prepared_matched}件")
    print("="*80)

if __name__ == "__main__":
    main()
