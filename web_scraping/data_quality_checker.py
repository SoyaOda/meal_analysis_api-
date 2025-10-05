#!/usr/bin/env python3
"""
MyNetDiary収集データの品質チェックと修正ツール
無効データ（UIノイズ）を検出して適切な失敗状態に修正する
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime


class DataQualityChecker:
    """データ品質チェッカー"""

    def __init__(self):
        self.valid_nutrition_patterns = [
            r"Total Fat \d+\.?\d*g",
            r"Saturated Fat \d+\.?\d*g",
            r"Trans Fat \d+\.?\d*g",
            r"Cholesterol \d+\.?\d*mg",
            r"Sodium \d+\.?\d*mg",
            r"Total Carbohydrate \d+\.?\d*g",
            r"Dietary Fiber \d+\.?\d*g",
            r"Total Sugars \d+\.?\d*g",
            r"Protein \d+\.?\d*g",
            r"Vitamin [A-Z] \d+\.?\d*",
            r"Calcium \d+\.?\d*mg",
            r"Iron \d+\.?\d*mg",
            r"\d+\.?\d* cal/g",
            r"\d+\.?\d* calories",
        ]

        self.invalid_data_indicators = [
            # UI要素
            r"Meals",
            r"Dashboard",
            r"Plan",
            r"Food",
            r"Exercise",
            r"Analysis",
            r"Health",
            r"Community",
            r"Settings",

            # ナビゲーション要素
            r"Today",
            r"Calorie Budget",
            r"Eaten",
            r"Left",
            r"PREMIUM TRACKING",

            # JavaScript/CSS
            r"var \w+ = ",
            r"\.Mui\w+-\w+-\d+",
            r"function\s*\(",
            r"{\s*\w+:\s*\w+",

            # 法的文書
            r"Privacy Policy",
            r"Terms of Service",
            r"Copyright",
            r"All rights reserved",

            # 外部サービス
            r"Garmin linking",
            r"iPhone\/iPad app",
            r"Android app",

            # 数値のみの行（UI表示値）
            r"^\d+$",
            r"^\d+,\d+$",
        ]

    def is_valid_nutrition_data(self, data_items: List[str]) -> bool:
        """栄養データが有効かチェック"""
        if not data_items or len(data_items) < 5:
            return False

        # 有効な栄養素パターンの数をカウント
        valid_nutrition_count = 0
        for item in data_items:
            if isinstance(item, str):
                for pattern in self.valid_nutrition_patterns:
                    if re.search(pattern, item, re.IGNORECASE):
                        valid_nutrition_count += 1
                        break

        # 無効なデータ指標の数をカウント
        invalid_count = 0
        for item in data_items:
            if isinstance(item, str):
                for pattern in self.invalid_data_indicators:
                    if re.search(pattern, item):
                        invalid_count += 1
                        break

        # 判定基準：
        # - 有効な栄養素が5個以上
        # - 無効データが全体の30%未満
        has_enough_nutrition = valid_nutrition_count >= 5
        invalid_ratio = invalid_count / len(data_items) if data_items else 1
        has_low_noise = invalid_ratio < 0.3

        return has_enough_nutrition and has_low_noise

    def is_valid_serving_data(self, data_items: List[str]) -> bool:
        """サービングデータが有効かチェック"""
        if not data_items or len(data_items) < 3:
            return False

        # 有効なサービング形式のパターン
        valid_serving_patterns = [
            r"\d+\.?\d*\s*(cup|cups)",
            r"\d+\.?\d*\s*(oz|ounce|ounces)",
            r"\d+\.?\d*\s*(g|gram|grams)",
            r"\d+\.?\d*\s*(ml|milliliter)",
            r"\d+\.?\d*\s*(tsp|teaspoon)",
            r"\d+\.?\d*\s*(tbsp|tablespoon)",
            r"\d+\.?\d*\s*(piece|pieces)",
            r"\d+\.?\d*\s*(slice|slices)",
        ]

        # 有効なサービング形式の数をカウント
        valid_serving_count = 0
        for item in data_items:
            if isinstance(item, str):
                for pattern in valid_serving_patterns:
                    if re.search(pattern, item, re.IGNORECASE):
                        valid_serving_count += 1
                        break

        # 無効なデータ指標の数をカウント
        invalid_count = 0
        for item in data_items:
            if isinstance(item, str):
                for pattern in self.invalid_data_indicators:
                    if re.search(pattern, item):
                        invalid_count += 1
                        break

        # 判定基準：
        # - 有効なサービング形式が3個以上
        # - 無効データが全体の50%未満
        has_enough_servings = valid_serving_count >= 3
        invalid_ratio = invalid_count / len(data_items) if data_items else 1
        has_low_noise = invalid_ratio < 0.5

        return has_enough_servings and has_low_noise

    def check_food_data_quality(self, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """単一食材データの品質チェック"""
        if not food_data.get("data_collection_success"):
            return {
                "is_valid": False,
                "reason": "data_collection_success is False",
                "needs_retry": True
            }

        comprehensive_data = food_data.get("comprehensive_data", {})

        # serving_optionsチェック
        serving_data = comprehensive_data.get("serving_options", {}).get("raw_serving_data", [])
        is_valid_serving = self.is_valid_serving_data(serving_data)

        # nutrition_dataチェック
        nutrition_data = comprehensive_data.get("nutrition_data", {}).get("raw_nutrition_data", [])
        is_valid_nutrition = self.is_valid_nutrition_data(nutrition_data)

        # 総合判定
        is_valid = is_valid_serving and is_valid_nutrition

        result = {
            "is_valid": is_valid,
            "serving_data_valid": is_valid_serving,
            "nutrition_data_valid": is_valid_nutrition,
            "serving_count": len(serving_data),
            "nutrition_count": len(nutrition_data),
            "needs_retry": not is_valid
        }

        if not is_valid:
            reasons = []
            if not is_valid_serving:
                reasons.append("invalid serving data (mostly UI noise)")
            if not is_valid_nutrition:
                reasons.append("invalid nutrition data (mostly UI noise)")
            result["reason"] = "; ".join(reasons)

        return result

    def check_file_quality(self, file_path: Path) -> Dict[str, Any]:
        """JSONファイル全体の品質チェック"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            collection_results = data.get("collection_results", [])
            total_foods = len(collection_results)

            if total_foods == 0:
                return {
                    "file_path": str(file_path),
                    "total_foods": 0,
                    "valid_foods": 0,
                    "invalid_foods": 0,
                    "needs_correction": False,
                    "error": "No food data found"
                }

            valid_count = 0
            invalid_count = 0
            foods_to_mark_failed = []

            for food_data in collection_results:
                quality_check = self.check_food_data_quality(food_data)

                if quality_check["is_valid"]:
                    valid_count += 1
                else:
                    invalid_count += 1
                    if food_data.get("data_collection_success"):  # 現在成功とマークされているが実際は無効
                        foods_to_mark_failed.append({
                            "sequence": food_data.get("sequence"),
                            "food_name": food_data.get("food_name"),
                            "reason": quality_check.get("reason", "unknown")
                        })

            return {
                "file_path": str(file_path),
                "total_foods": total_foods,
                "valid_foods": valid_count,
                "invalid_foods": invalid_count,
                "false_positives": len(foods_to_mark_failed),
                "needs_correction": len(foods_to_mark_failed) > 0,
                "foods_to_mark_failed": foods_to_mark_failed,
                "summary": data.get("collection_summary", {})
            }

        except Exception as e:
            return {
                "file_path": str(file_path),
                "error": str(e),
                "needs_correction": False
            }

    def correct_file_data(self, file_path: Path, backup: bool = True) -> Dict[str, Any]:
        """ファイルのデータ品質を修正"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # バックアップ作成
            if backup:
                backup_path = file_path.with_suffix('.backup.json')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            collection_results = data.get("collection_results", [])
            corrections_made = 0

            for food_data in collection_results:
                if not food_data.get("data_collection_success"):
                    continue  # 既に失敗とマークされているものはスキップ

                quality_check = self.check_food_data_quality(food_data)

                if not quality_check["is_valid"]:
                    # 失敗としてマーク
                    food_data["data_collection_success"] = False
                    food_data["data_quality_issue"] = quality_check.get("reason", "Invalid data quality")
                    food_data["corrected_by_quality_checker"] = True
                    food_data["correction_timestamp"] = datetime.now().isoformat()
                    corrections_made += 1

            # サマリー情報を更新
            if "collection_summary" in data:
                original_successful = data["collection_summary"].get("successful", 0)
                original_failed = data["collection_summary"].get("failed", 0)

                new_successful = original_successful - corrections_made
                new_failed = original_failed + corrections_made

                data["collection_summary"]["successful"] = new_successful
                data["collection_summary"]["failed"] = new_failed
                data["collection_summary"]["success_rate"] = (new_successful / data["collection_summary"]["total_foods"]) * 100 if data["collection_summary"]["total_foods"] > 0 else 0
                data["collection_summary"]["quality_corrected"] = True
                data["collection_summary"]["corrections_made"] = corrections_made
                data["collection_summary"]["correction_timestamp"] = datetime.now().isoformat()

            # 修正されたデータを保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return {
                "file_path": str(file_path),
                "corrections_made": corrections_made,
                "success": True,
                "backup_created": backup,
                "backup_path": str(backup_path) if backup else None
            }

        except Exception as e:
            return {
                "file_path": str(file_path),
                "error": str(e),
                "success": False
            }


def main():
    """メイン実行関数"""
    print("🔍 MyNetDiary データ品質チェッカー開始")
    print("="*80)

    checker = DataQualityChecker()
    data_dir = Path("data")

    if not data_dir.exists():
        print(f"❌ データディレクトリが見つかりません: {data_dir}")
        return

    # 最新のファイルを特定
    json_files = list(data_dir.glob("comprehensive_food_collection_all_*.json"))
    if not json_files:
        print("❌ 対象ファイルが見つかりません")
        return

    # 最新のファイルを処理
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"📊 最新ファイルを分析: {latest_file.name}")

    # 品質チェック実行
    quality_result = checker.check_file_quality(latest_file)

    print(f"\n📈 品質分析結果:")
    print(f"   総食材数: {quality_result.get('total_foods', 0)}")
    print(f"   有効データ: {quality_result.get('valid_foods', 0)}")
    print(f"   無効データ: {quality_result.get('invalid_foods', 0)}")
    print(f"   誤って成功とマークされたもの: {quality_result.get('false_positives', 0)}")

    if quality_result.get('needs_correction'):
        print(f"\n⚠️ データ修正が必要です！")
        print(f"   修正対象の食材例:")
        for i, food in enumerate(quality_result.get('foods_to_mark_failed', [])[:5]):
            print(f"     {i+1}. {food.get('food_name', 'unknown')} - {food.get('reason', 'unknown')}")

        print(f"🔧 データ修正を自動実行中...")
        correction_result = checker.correct_file_data(latest_file)

        if correction_result.get('success'):
            print(f"✅ 修正完了!")
            print(f"   修正された食材数: {correction_result.get('corrections_made', 0)}")
            if correction_result.get('backup_created'):
                print(f"   バックアップ: {correction_result.get('backup_path')}")
        else:
            print(f"❌ 修正失敗: {correction_result.get('error')}")
    else:
        print(f"✅ データ品質に問題はありません")


if __name__ == "__main__":
    main()