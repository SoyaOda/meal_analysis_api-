#!/usr/bin/env python3
"""
食材データの完全性チェッカー

保存済み食材データのserving情報と栄養情報の漏れをチェックし、
詳細な統計レポートを生成する
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path


class FoodDataIntegrityChecker:
    """食材データの完全性をチェックするクラス"""

    def __init__(self, data_file_path: str):
        self.data_file_path = data_file_path
        self.data = {}
        self.stats = {}

    def load_data(self) -> bool:
        """データファイルを読み込み"""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"✅ データファイル読み込み成功: {self.data_file_path}")
            return True
        except Exception as e:
            print(f"❌ データファイル読み込み失敗: {e}")
            return False

    def analyze_serving_data(self, serving_options: Dict[str, Any]) -> Dict[str, Any]:
        """serving情報の詳細分析"""
        if not serving_options:
            return {
                "has_data": False,
                "total_items": 0,
                "valid_servings": [],
                "invalid_ratio": 1.0
            }

        raw_serving_data = serving_options.get("raw_serving_data", [])
        total_items = len(raw_serving_data)

        if total_items == 0:
            return {
                "has_data": False,
                "total_items": 0,
                "valid_servings": [],
                "invalid_ratio": 1.0
            }

        # 有効なサービングパターン
        valid_serving_patterns = [
            r"\d+\.?\d*\s*(cup|cups|oz|ounce|gram|g|ml|tsp|tbsp|lb|kg|serving|piece|slice)\b",
            r"\d+\.?\d*\s*(container|can|bottle|package)\b",
            r"(cup|oz|gram|g|ml|tsp|tbsp|lb|serving|piece|slice)\b"
        ]

        # 無効パターン（ナビゲーション、フッター等）
        invalid_patterns = [
            r"© \d{4}.*Inc\.",
            r"Privacy policy|Terms of use",
            r"iPhone.*app|Android.*app",
            r"Dashboard|Analysis|Community|Settings",
            r"Success stories|Member testimonials",
            r"var\s+\w+\s*=|\.Mui\w+|\{.*\}",
            r"All rights reserved"
        ]

        valid_servings = []
        invalid_count = 0

        for item in raw_serving_data:
            if not isinstance(item, str) or len(item.strip()) == 0:
                continue

            # 無効パターンチェック
            is_invalid = False
            for invalid_pattern in invalid_patterns:
                if re.search(invalid_pattern, item, re.IGNORECASE):
                    invalid_count += 1
                    is_invalid = True
                    break

            if is_invalid:
                continue

            # 有効パターンチェック
            for valid_pattern in valid_serving_patterns:
                if re.search(valid_pattern, item, re.IGNORECASE):
                    valid_servings.append(item)
                    break

        invalid_ratio = invalid_count / total_items if total_items > 0 else 0

        return {
            "has_data": True,
            "total_items": total_items,
            "valid_servings": valid_servings,
            "valid_count": len(valid_servings),
            "invalid_count": invalid_count,
            "invalid_ratio": invalid_ratio,
            "has_sufficient_data": len(valid_servings) >= 3 and invalid_ratio <= 0.7
        }

    def analyze_nutrition_data(self, nutrition_data: Dict[str, Any]) -> Dict[str, Any]:
        """栄養情報の詳細分析"""
        if not nutrition_data:
            return {
                "has_data": False,
                "total_nutrients": 0,
                "valid_nutrients": [],
                "invalid_ratio": 1.0
            }

        detailed_nutrients = nutrition_data.get("detailed_nutrients", {})
        if not detailed_nutrients:
            return {
                "has_data": False,
                "total_nutrients": 0,
                "valid_nutrients": [],
                "invalid_ratio": 1.0
            }

        raw_nutrition_data = detailed_nutrients.get("raw_nutrition_data", [])
        total_nutrients = len(raw_nutrition_data)

        if total_nutrients == 0:
            return {
                "has_data": False,
                "total_nutrients": 0,
                "valid_nutrients": [],
                "invalid_ratio": 1.0
            }

        # 有効な栄養素パターン
        valid_nutrition_patterns = [
            r"Total Fat \d+\.?\d*g",
            r"Saturated Fat \d+\.?\d*g",
            r"Trans Fat \d+\.?\d*g",
            r"Cholesterol \d+\.?\d*mg",
            r"Sodium \d+\.?\d*mg",
            r"Total Carbs \d+\.?\d*g",
            r"Dietary Fiber \d+\.?\d*g",
            r"Total Sugars \d+\.?\d*g",
            r"Protein \d+\.?\d*g",
            r"Calories \d+\.?\d*cals",
            r"Vitamin [A-Z] \d+\.?\d*(mg|mcg|g)",
            r"Calcium \d+\.?\d*mg",
            r"Iron \d+\.?\d*mg",
            r"Potassium \d+\.?\d*mg",
            r"Alcohol \d+\.?\d*g",
            r"Caffeine \d+\.?\d*mg"
        ]

        # 無効パターン
        invalid_patterns = [
            r"var\s+\w+\s*=",
            r"\.(Mui|jss)\w+",
            r"© \d{4}.*Inc\.",
            r"Privacy policy|Terms of use",
            r"Dashboard|Analysis|Community|Settings",
            r"iPhone.*app|Android.*app",
            r"overflow:\s*hidden",
            r"Success stories|Member testimonials"
        ]

        valid_nutrients = []
        invalid_count = 0

        for item in raw_nutrition_data:
            if not isinstance(item, str) or len(item.strip()) == 0:
                continue

            # 無効パターンチェック
            is_invalid = False
            for invalid_pattern in invalid_patterns:
                if re.search(invalid_pattern, item, re.IGNORECASE):
                    invalid_count += 1
                    is_invalid = True
                    break

            if is_invalid:
                continue

            # 有効パターンチェック
            for valid_pattern in valid_nutrition_patterns:
                if re.search(valid_pattern, item, re.IGNORECASE):
                    valid_nutrients.append(item)
                    break

        invalid_ratio = invalid_count / total_nutrients if total_nutrients > 0 else 0

        return {
            "has_data": True,
            "total_nutrients": total_nutrients,
            "valid_nutrients": valid_nutrients,
            "valid_count": len(valid_nutrients),
            "invalid_count": invalid_count,
            "invalid_ratio": invalid_ratio,
            "has_sufficient_data": len(valid_nutrients) >= 8 and invalid_ratio <= 0.5
        }

    def check_data_integrity(self) -> Dict[str, Any]:
        """全体のデータ完全性をチェック"""
        if not self.data:
            return {"error": "データが読み込まれていません"}

        collection_results = self.data.get("collection_results", [])
        total_foods = len(collection_results)

        # 統計カウンター
        stats = {
            "total_foods": total_foods,
            "successful_foods": 0,
            "foods_with_serving": 0,
            "foods_with_nutrition": 0,
            "foods_with_both": 0,
            "foods_with_complete_serving": 0,
            "foods_with_complete_nutrition": 0,
            "foods_completely_valid": 0,
            "detailed_results": []
        }

        for i, result in enumerate(collection_results):
            food_name = result.get("food_name", f"食材_{i+1}")
            data_collection_success = result.get("data_collection_success", False)
            comprehensive_data = result.get("comprehensive_data", {})

            # 基本情報
            food_analysis = {
                "food_name": food_name,
                "index": i + 1,
                "collection_success": data_collection_success,
                "has_comprehensive_data": bool(comprehensive_data)
            }

            if data_collection_success:
                stats["successful_foods"] += 1

            if comprehensive_data:
                # Serving情報の分析
                serving_options = comprehensive_data.get("serving_options", {})
                serving_analysis = self.analyze_serving_data(serving_options)
                food_analysis["serving_analysis"] = serving_analysis

                if serving_analysis["has_data"]:
                    stats["foods_with_serving"] += 1
                    if serving_analysis["has_sufficient_data"]:
                        stats["foods_with_complete_serving"] += 1

                # 栄養情報の分析
                nutrition_data = comprehensive_data.get("nutrition_data", {})
                nutrition_analysis = self.analyze_nutrition_data(nutrition_data)
                food_analysis["nutrition_analysis"] = nutrition_analysis

                if nutrition_analysis["has_data"]:
                    stats["foods_with_nutrition"] += 1
                    if nutrition_analysis["has_sufficient_data"]:
                        stats["foods_with_complete_nutrition"] += 1

                # 両方のデータがあるかチェック
                if serving_analysis["has_data"] and nutrition_analysis["has_data"]:
                    stats["foods_with_both"] += 1

                # 完全に有効なデータ
                if (serving_analysis["has_sufficient_data"] and
                    nutrition_analysis["has_sufficient_data"]):
                    stats["foods_completely_valid"] += 1

            stats["detailed_results"].append(food_analysis)

        # パーセンテージ計算
        if total_foods > 0:
            stats["percentages"] = {
                "success_rate": (stats["successful_foods"] / total_foods) * 100,
                "serving_coverage": (stats["foods_with_serving"] / total_foods) * 100,
                "nutrition_coverage": (stats["foods_with_nutrition"] / total_foods) * 100,
                "both_data_coverage": (stats["foods_with_both"] / total_foods) * 100,
                "complete_serving_rate": (stats["foods_with_complete_serving"] / total_foods) * 100,
                "complete_nutrition_rate": (stats["foods_with_complete_nutrition"] / total_foods) * 100,
                "complete_validity_rate": (stats["foods_completely_valid"] / total_foods) * 100
            }

        self.stats = stats
        return stats

    def generate_report(self) -> str:
        """詳細レポートを生成"""
        if not self.stats:
            return "統計データが生成されていません"

        stats = self.stats

        report = []
        report.append("=" * 80)
        report.append("🔍 食材データ完全性チェック結果")
        report.append("=" * 80)
        report.append(f"📁 データファイル: {os.path.basename(self.data_file_path)}")
        report.append(f"📅 チェック実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 全体統計
        report.append("📊 全体統計")
        report.append("-" * 40)
        report.append(f"📝 総食材数: {stats['total_foods']:,}個")
        report.append(f"✅ 成功食材数: {stats['successful_foods']:,}個 ({stats['percentages']['success_rate']:.1f}%)")
        report.append("")

        # データカバレッジ
        report.append("📋 データカバレッジ")
        report.append("-" * 40)
        report.append(f"🍽️ Serving情報あり: {stats['foods_with_serving']:,}個 ({stats['percentages']['serving_coverage']:.1f}%)")
        report.append(f"🥗 栄養情報あり: {stats['foods_with_nutrition']:,}個 ({stats['percentages']['nutrition_coverage']:.1f}%)")
        report.append(f"📊 両方のデータあり: {stats['foods_with_both']:,}個 ({stats['percentages']['both_data_coverage']:.1f}%)")
        report.append("")

        # データ品質
        report.append("✨ データ品質")
        report.append("-" * 40)
        report.append(f"🍽️ 完全なServing情報: {stats['foods_with_complete_serving']:,}個 ({stats['percentages']['complete_serving_rate']:.1f}%)")
        report.append(f"🥗 完全な栄養情報: {stats['foods_with_complete_nutrition']:,}個 ({stats['percentages']['complete_nutrition_rate']:.1f}%)")
        report.append(f"🏆 完全に有効なデータ: {stats['foods_completely_valid']:,}個 ({stats['percentages']['complete_validity_rate']:.1f}%)")
        report.append("")

        # 問題のある食材の特定
        problematic_foods = []
        missing_serving = []
        missing_nutrition = []

        for food in stats['detailed_results']:
            if not food['collection_success']:
                problematic_foods.append(food['food_name'])
            elif food['has_comprehensive_data']:
                serving = food.get('serving_analysis', {})
                nutrition = food.get('nutrition_analysis', {})

                if not serving.get('has_sufficient_data', False):
                    missing_serving.append(food['food_name'])
                if not nutrition.get('has_sufficient_data', False):
                    missing_nutrition.append(food['food_name'])

        # 問題レポート
        if problematic_foods or missing_serving or missing_nutrition:
            report.append("⚠️ 問題検出")
            report.append("-" * 40)

            if problematic_foods:
                report.append(f"❌ 収集失敗: {len(problematic_foods)}個")
                if len(problematic_foods) <= 20:
                    for food in problematic_foods[:20]:
                        report.append(f"   • {food}")
                else:
                    for food in problematic_foods[:10]:
                        report.append(f"   • {food}")
                    report.append(f"   ... 他{len(problematic_foods)-10}個")

            if missing_serving:
                report.append(f"🍽️ Serving情報不完全: {len(missing_serving)}個")
                if len(missing_serving) <= 20:
                    for food in missing_serving[:20]:
                        report.append(f"   • {food}")
                else:
                    for food in missing_serving[:10]:
                        report.append(f"   • {food}")
                    report.append(f"   ... 他{len(missing_serving)-10}個")

            if missing_nutrition:
                report.append(f"🥗 栄養情報不完全: {len(missing_nutrition)}個")
                if len(missing_nutrition) <= 20:
                    for food in missing_nutrition[:20]:
                        report.append(f"   • {food}")
                else:
                    for food in missing_nutrition[:10]:
                        report.append(f"   • {food}")
                    report.append(f"   ... 他{len(missing_nutrition)-10}個")
        else:
            report.append("🎉 問題なし: すべての食材で完全なデータが取得されています！")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def save_detailed_report(self, output_dir: str = "reports") -> str:
        """詳細レポートをJSONとテキストで保存"""
        if not self.stats:
            return "統計データが生成されていません"

        # レポートディレクトリ作成
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"data_integrity_report_{timestamp}"

        # JSONレポート
        json_path = os.path.join(output_dir, f"{base_filename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

        # テキストレポート
        txt_path = os.path.join(output_dir, f"{base_filename}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())

        return f"レポート保存完了:\n  📄 JSON: {json_path}\n  📝 テキスト: {txt_path}"


def find_latest_data_file(data_dir: str = "data") -> str:
    """最新のデータファイルを検索"""
    pattern = r"comprehensive_food_collection_.*\.json$"

    latest_file = ""
    latest_time = None

    for filename in os.listdir(data_dir):
        if re.match(pattern, filename) and not filename.endswith('.backup.json'):
            full_path = os.path.join(data_dir, filename)
            if os.path.isfile(full_path):
                try:
                    stat_result = os.stat(full_path)
                    file_time = datetime.fromtimestamp(stat_result.st_mtime)
                    if not latest_time or file_time > latest_time:
                        latest_time = file_time
                        latest_file = full_path
                except:
                    continue

    return latest_file


def main():
    """メイン処理"""
    print("🔍 食材データ完全性チェッカー")
    print("=" * 50)

    # 最新のデータファイルを検索
    latest_file = find_latest_data_file()

    if not latest_file:
        print("❌ データファイルが見つかりません")
        return

    print(f"📁 対象ファイル: {latest_file}")
    print()

    # チェッカー初期化
    checker = FoodDataIntegrityChecker(latest_file)

    # データ読み込み
    if not checker.load_data():
        return

    # 完全性チェック実行
    print("🔄 完全性チェック実行中...")
    stats = checker.check_data_integrity()

    # レポート表示
    print(checker.generate_report())

    # 詳細レポート保存
    save_result = checker.save_detailed_report()
    print(save_result)


if __name__ == "__main__":
    main()