#!/usr/bin/env python3
"""
有効なデータ状態への復元スクリプト

指定された以前の有効なデータ状態（comprehensive_food_collection_all_20250930_134533_intermediate_1490.json）
に基づいて、失敗したアイテムを適切にマークし、resume機能で再実行できるようにする。
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any, Set
import re

def load_reference_data(file_path: str) -> Dict[str, Any]:
    """参照用の有効データをロード"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 参照データロード成功: {file_path}")
        return data
    except Exception as e:
        print(f"❌ 参照データロード失敗: {e}")
        return {}

def is_valid_food_item(item: Dict[str, Any]) -> bool:
    """食材アイテムが有効かチェック（厳格な基準）"""
    if not item or not isinstance(item, dict):
        return False

    # collection_successが明示的にTrueである必要がある
    if not item.get("collection_success", False):
        return False

    # 栄養データの有効性チェック
    nutrition_data = item.get("nutrition_data", {})
    if nutrition_data:
        raw_nutrition = nutrition_data.get("raw_nutrition_data", [])
        if raw_nutrition and len(raw_nutrition) > 5:
            # 有効な栄養素パターンが含まれているかチェック
            valid_nutrition_patterns = [
                r"Total Fat \d+\.?\d*g",
                r"Saturated Fat \d+\.?\d*g",
                r"Trans Fat \d+\.?\d*g",
                r"Cholesterol \d+\.?\d*mg",
                r"Sodium \d+\.?\d*mg",
                r"Total Carbohydrate \d+\.?\d*g",
                r"Dietary Fiber \d+\.?\d*g",
                r"Total Sugars \d+\.?\d*g",
                r"Protein \d+\.?\d*g",
            ]

            valid_count = 0
            for raw_item in raw_nutrition:
                if isinstance(raw_item, str):
                    for pattern in valid_nutrition_patterns:
                        if re.search(pattern, raw_item, re.IGNORECASE):
                            valid_count += 1
                            break

            if valid_count >= 5:  # 最低5個の有効な栄養素
                return True

    # サービングデータの有効性チェック
    serving_options = item.get("serving_options", {})
    if serving_options:
        raw_serving = serving_options.get("raw_serving_data", [])
        if raw_serving and len(raw_serving) > 3:
            # 有効なサービング形式パターンが含まれているかチェック
            valid_serving_patterns = [
                r"\d+\.?\d*\s*(cup|cups)\b",
                r"\d+\.?\d*\s*(oz|ounce|ounces)\b",
                r"\d+\.?\d*\s*(g|gram|grams)\b",
                r"\d+\.?\d*\s*(ml|milliliter)\b",
                r"\d+\.?\d*\s*(tsp|teaspoon)\b",
                r"\d+\.?\d*\s*(tbsp|tablespoon)\b",
            ]

            valid_count = 0
            for raw_item in raw_serving:
                if isinstance(raw_item, str):
                    for pattern in valid_serving_patterns:
                        if re.search(pattern, raw_item, re.IGNORECASE):
                            valid_count += 1
                            break

            if valid_count >= 3:  # 最低3個の有効なサービング
                return True

    return False

def extract_successfully_collected_foods(data: Dict[str, Any]) -> Set[str]:
    """成功したアイテムの食材名セットを抽出"""
    successful_foods = set()

    # collection_results配列から有効なアイテムを抽出
    collection_results = data.get("collection_results", [])
    for result in collection_results:
        # data_collection_successがTrueのアイテムを抽出
        if result.get("data_collection_success", False):
            comprehensive_data = result.get("comprehensive_data", {})
            if comprehensive_data and is_valid_food_item(comprehensive_data):
                food_name = result.get("food_name", "").strip()
                if food_name:
                    successful_foods.add(food_name)

    print(f"✅ 有効データから成功食材数: {len(successful_foods)}")
    return successful_foods

def find_latest_data_file() -> str:
    """最新のデータファイルを検索"""
    data_dir = "web_scraping/data"
    pattern = r"comprehensive_food_collection_.*\.json$"

    latest_file = ""
    latest_time = ""

    for filename in os.listdir(data_dir):
        if re.match(pattern, filename) and not filename.endswith('.backup.json'):
            full_path = os.path.join(data_dir, filename)
            if os.path.isfile(full_path):
                # ファイルの作成時間を取得
                try:
                    stat_result = os.stat(full_path)
                    file_time = datetime.fromtimestamp(stat_result.st_mtime)
                    if not latest_time or file_time > latest_time:
                        latest_time = file_time
                        latest_file = full_path
                except:
                    continue

    return latest_file

def restore_data_state(reference_file: str):
    """データ状態を復元する"""
    # 1. 参照データをロード
    reference_data = load_reference_data(reference_file)
    if not reference_data:
        print("❌ 参照データの読み込みに失敗しました")
        return False

    # 2. 成功した食材のセットを抽出
    successful_foods = extract_successfully_collected_foods(reference_data)

    # 3. 最新のデータファイルを検索
    latest_file = find_latest_data_file()
    if not latest_file:
        print("❌ 最新のデータファイルが見つかりません")
        return False

    print(f"📂 最新データファイル: {latest_file}")

    # 4. 最新ファイルのバックアップ作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{latest_file}.backup_{timestamp}.json"
    shutil.copy2(latest_file, backup_file)
    print(f"💾 バックアップ作成: {backup_file}")

    # 5. 最新データをロード
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            current_data = json.load(f)
    except Exception as e:
        print(f"❌ 最新データの読み込み失敗: {e}")
        return False

    # 6. 失敗したアイテムを適切にマーク
    processed_count = 0
    failed_count = 0
    success_count = 0

    # collection_results配列を処理
    collection_results = current_data.get("collection_results", [])
    for result in collection_results:
        food_name = result.get("food_name", "").strip()
        if not food_name:
            continue

        processed_count += 1

        # 参照データに含まれている場合は成功として保持
        if food_name in successful_foods:
            result["data_collection_success"] = True
            result["restored_from_reference"] = True
            success_count += 1
        else:
            # 含まれていない場合は失敗としてマーク
            result["data_collection_success"] = False
            result["failure_reason"] = "invalid_data_detected"
            result["marked_for_retry"] = True
            result["marked_at"] = datetime.now().isoformat()
            failed_count += 1

    # 7. 統計情報を更新
    current_data["restoration_info"] = {
        "restored_at": datetime.now().isoformat(),
        "reference_file": reference_file,
        "total_processed": processed_count,
        "marked_as_success": success_count,
        "marked_as_failed": failed_count,
        "backup_file": backup_file
    }

    # 8. 更新されたデータを保存
    try:
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        print(f"✅ データ復元完了:")
        print(f"   📊 処理総数: {processed_count}")
        print(f"   ✅ 成功維持: {success_count}")
        print(f"   ❌ 失敗マーク: {failed_count}")
        print(f"   💾 保存先: {latest_file}")
        return True
    except Exception as e:
        print(f"❌ データ保存失敗: {e}")
        return False

def main():
    """メイン処理"""
    print("🔄 データ復元処理開始")
    print("=" * 50)

    reference_file = "web_scraping/data/comprehensive_food_collection_all_20250930_134533_intermediate_1490.json"

    if not os.path.exists(reference_file):
        print(f"❌ 参照ファイルが存在しません: {reference_file}")
        return

    success = restore_data_state(reference_file)

    print("=" * 50)
    if success:
        print("✅ データ復元処理が正常に完了しました")
        print("📝 次のステップ:")
        print("   1. resume機能で失敗したアイテムを再実行")
        print("   2. 強化された検証ロジックで品質チェック")
    else:
        print("❌ データ復元処理に失敗しました")

if __name__ == "__main__":
    main()