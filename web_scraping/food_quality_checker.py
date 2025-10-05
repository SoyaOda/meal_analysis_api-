#!/usr/bin/env python3
"""
1,154食材品質段階チェッカー

カタログベース1,154食材について段階的品質チェックを実行し、
serving情報とnutrition情報の取りこぼしを詳細に検証する
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple
from pathlib import Path
from collections import defaultdict


class FoodQualityChecker:
    """食材品質段階チェッククラス"""

    def __init__(self, catalog_dir: str = "food_catalog_data", data_dir: str = "data"):
        self.catalog_dir = catalog_dir
        self.data_dir = data_dir
        self.catalog_foods = []
        self.collected_data = {}
        self.quality_results = {}

    def load_catalog_foods(self) -> List[Dict[str, Any]]:
        """カタログから全1,154食材を読み込み"""
        print("📁 カタログ食材読み込み中...")

        all_foods = []
        catalog_files = [f for f in os.listdir(self.catalog_dir) if f.endswith('.json')]

        for file_name in catalog_files:
            file_path = os.path.join(self.catalog_dir, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                category_data = data.get("category_data", {})
                foods = category_data.get("foods", [])

                for food in foods:
                    food_name = food.get("food_name", "").strip()
                    if food_name:
                        # 正規化（改行除去）
                        normalized_name = re.sub(r'\n', ' ', food_name).strip()
                        food["normalized_name"] = normalized_name
                        all_foods.append(food)

            except Exception as e:
                print(f"  ❌ {file_name}読み込みエラー: {e}")

        print(f"✅ カタログ食材: {len(all_foods)}個読み込み完了")
        self.catalog_foods = all_foods
        return all_foods

    def load_collected_data(self) -> Dict[str, Any]:
        """収集済みデータを読み込み"""
        print("📁 収集済みデータ読み込み中...")

        # 最新ファイル検索
        latest_file = self.find_latest_collection_file()
        if not latest_file:
            print("❌ 収集済みデータファイルが見つかりません")
            return {}

        print(f"📄 対象ファイル: {os.path.basename(latest_file)}")

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            collection_results = data.get("collection_results", [])

            # 食材名をキーとした辞書を作成
            collected_dict = {}
            for result in collection_results:
                food_name = result.get("food_name", "").strip()
                normalized_name = re.sub(r'\n', ' ', food_name).strip()
                collected_dict[normalized_name] = result

            print(f"✅ 収集データ: {len(collected_dict)}個読み込み完了")
            self.collected_data = collected_dict
            return collected_dict

        except Exception as e:
            print(f"❌ 収集データ読み込みエラー: {e}")
            return {}

    def find_latest_collection_file(self) -> str:
        """最新の収集ファイルを検索"""
        pattern = r"comprehensive_food_collection_.*\.json$"
        latest_file = ""
        latest_time = None

        for filename in os.listdir(self.data_dir):
            if re.match(pattern, filename) and not filename.endswith('.backup.json'):
                full_path = os.path.join(self.data_dir, filename)
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

    def extract_valid_nutrients(self, nutrition_data: Dict[str, Any]) -> List[str]:
        """有効な栄養素を抽出"""
        if not nutrition_data:
            return []

        detailed_nutrients = nutrition_data.get("detailed_nutrients", {})
        if not detailed_nutrients:
            return []

        raw_nutrition_data = detailed_nutrients.get("raw_nutrition_data", [])
        if not raw_nutrition_data:
            return []

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

        valid_nutrients = []
        for item in raw_nutrition_data:
            if not isinstance(item, str):
                continue

            for pattern in valid_nutrition_patterns:
                if re.search(pattern, item, re.IGNORECASE):
                    valid_nutrients.append(item)
                    break

        return valid_nutrients

    def extract_valid_servings(self, serving_options: Dict[str, Any]) -> List[str]:
        """有効なserving単位を抽出"""
        if not serving_options:
            return []

        raw_serving_data = serving_options.get("raw_serving_data", [])
        if not raw_serving_data:
            return []

        # 有効なサービングパターン
        valid_serving_patterns = [
            r"\d+\.?\d*\s*(cup|cups|oz|ounce|gram|g|ml|tsp|tbsp|lb|kg|serving|piece|slice)\b",
            r"\d+\.?\d*\s*(container|can|bottle|package)\b",
            r"(cup|oz|gram|g|ml|tsp|tbsp|lb|serving|piece|slice)\b"
        ]

        valid_servings = []
        for item in raw_serving_data:
            if not isinstance(item, str):
                continue

            for pattern in valid_serving_patterns:
                if re.search(pattern, item, re.IGNORECASE):
                    valid_servings.append(item)
                    break

        return valid_servings

    def check_food_quality(self, food_name: str, collected_result: Dict[str, Any]) -> Dict[str, Any]:
        """単一食材の品質チェック"""
        result = {
            "food_name": food_name,
            "level1_pass": False,
            "level2_pass": False,
            "level3_pass": False,
            "issues": [],
            "serving_count": 0,
            "nutrition_count": 0,
            "valid_servings": [],
            "valid_nutrients": []
        }

        # 収集成功チェック
        if not collected_result.get("data_collection_success", False):
            result["issues"].append("data_collection_failed")
            return result

        comprehensive_data = collected_result.get("comprehensive_data", {})
        if not comprehensive_data:
            result["issues"].append("no_comprehensive_data")
            return result

        # レベル1: データ存在チェック
        serving_options = comprehensive_data.get("serving_options", {})
        nutrition_data = comprehensive_data.get("nutrition_data", {})

        has_serving_data = bool(serving_options.get("raw_serving_data"))
        has_nutrition_data = bool(nutrition_data.get("detailed_nutrients", {}).get("raw_nutrition_data"))

        if has_serving_data and has_nutrition_data:
            result["level1_pass"] = True
        else:
            if not has_serving_data:
                result["issues"].append("no_serving_data")
            if not has_nutrition_data:
                result["issues"].append("no_nutrition_data")

        # 有効データ抽出
        valid_servings = self.extract_valid_servings(serving_options)
        valid_nutrients = self.extract_valid_nutrients(nutrition_data)

        result["serving_count"] = len(valid_servings)
        result["nutrition_count"] = len(valid_nutrients)
        result["valid_servings"] = valid_servings[:5]  # サンプル表示用
        result["valid_nutrients"] = valid_nutrients[:5]  # サンプル表示用

        # レベル2: 基本品質チェック（2個以上）
        if result["level1_pass"] and result["serving_count"] >= 2 and result["nutrition_count"] >= 2:
            result["level2_pass"] = True
        else:
            if result["serving_count"] < 2:
                result["issues"].append(f"insufficient_servings_{result['serving_count']}")
            if result["nutrition_count"] < 2:
                result["issues"].append(f"insufficient_nutrients_{result['nutrition_count']}")

        # レベル3: 高品質チェック（2個以上、実質レベル2と同じ）
        if result["level2_pass"]:
            result["level3_pass"] = True

        return result

    def run_quality_check(self) -> Dict[str, Any]:
        """全食材の品質チェック実行"""
        print("\n🔍 1,154食材品質チェック実行中...")

        if not self.catalog_foods or not self.collected_data:
            print("❌ カタログまたは収集データが読み込まれていません")
            return {}

        results = {
            "total_foods": len(self.catalog_foods),
            "level1_pass": 0,
            "level2_pass": 0,
            "level3_pass": 0,
            "details": [],
            "issues_summary": defaultdict(int),
            "category_results": defaultdict(lambda: {
                "total": 0,
                "level1_pass": 0,
                "level2_pass": 0,
                "level3_pass": 0
            })
        }

        for food in self.catalog_foods:
            food_name = food["normalized_name"]
            category = food.get("category", "Unknown")

            # 収集データから該当食材を検索
            collected_result = self.collected_data.get(food_name, {})

            # 品質チェック実行
            quality_result = self.check_food_quality(food_name, collected_result)
            quality_result["category"] = category

            results["details"].append(quality_result)

            # 統計更新
            if quality_result["level1_pass"]:
                results["level1_pass"] += 1
            if quality_result["level2_pass"]:
                results["level2_pass"] += 1
            if quality_result["level3_pass"]:
                results["level3_pass"] += 1

            # カテゴリ別統計
            results["category_results"][category]["total"] += 1
            if quality_result["level1_pass"]:
                results["category_results"][category]["level1_pass"] += 1
            if quality_result["level2_pass"]:
                results["category_results"][category]["level2_pass"] += 1
            if quality_result["level3_pass"]:
                results["category_results"][category]["level3_pass"] += 1

            # 問題統計
            for issue in quality_result["issues"]:
                results["issues_summary"][issue] += 1

        # パーセンテージ計算
        total = results["total_foods"]
        results["percentages"] = {
            "level1_pass": (results["level1_pass"] / total) * 100 if total > 0 else 0,
            "level2_pass": (results["level2_pass"] / total) * 100 if total > 0 else 0,
            "level3_pass": (results["level3_pass"] / total) * 100 if total > 0 else 0
        }

        self.quality_results = results
        return results

    def generate_quality_report(self) -> str:
        """品質レポートを生成"""
        if not self.quality_results:
            return "品質チェックが実行されていません"

        results = self.quality_results
        report = []

        report.append("=" * 100)
        report.append("🔍 1,154食材段階的品質チェック結果")
        report.append("=" * 100)
        report.append(f"📅 チェック実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📋 対象食材数: {results['total_foods']:,}個")
        report.append("")

        # レベル別合格状況
        report.append("📊 レベル別合格状況")
        report.append("-" * 60)
        report.append(f"レベル1合格: {results['level1_pass']:,}/{results['total_foods']:,}食材 ({results['percentages']['level1_pass']:.1f}%)")
        report.append(f"  └─ データ存在: serving情報 + nutrition情報")
        report.append(f"レベル2合格: {results['level2_pass']:,}/{results['total_foods']:,}食材 ({results['percentages']['level2_pass']:.1f}%)")
        report.append(f"  └─ 基本品質: 有効serving2個以上 + 有効nutrition2個以上")
        report.append(f"レベル3合格: {results['level3_pass']:,}/{results['total_foods']:,}食材 ({results['percentages']['level3_pass']:.1f}%)")
        report.append(f"  └─ 高品質: レベル2と同基準")
        report.append("")

        # 問題統計
        if results["issues_summary"]:
            report.append("⚠️ 問題統計")
            report.append("-" * 60)
            sorted_issues = sorted(results["issues_summary"].items(), key=lambda x: x[1], reverse=True)
            for issue, count in sorted_issues:
                report.append(f"  {issue}: {count}個")
            report.append("")

        # カテゴリ別結果
        report.append("📂 カテゴリ別結果")
        report.append("-" * 60)
        category_results = results["category_results"]
        sorted_categories = sorted(category_results.items(), key=lambda x: x[1]["level3_pass"], reverse=True)

        for category, cat_data in sorted_categories:
            total = cat_data["total"]
            l1_rate = (cat_data["level1_pass"] / total) * 100 if total > 0 else 0
            l2_rate = (cat_data["level2_pass"] / total) * 100 if total > 0 else 0
            l3_rate = (cat_data["level3_pass"] / total) * 100 if total > 0 else 0

            report.append(f"📁 {category}")
            report.append(f"   📊 総数: {total}個")
            report.append(f"   📊 L1: {cat_data['level1_pass']}個 ({l1_rate:.1f}%)")
            report.append(f"   📊 L2: {cat_data['level2_pass']}個 ({l2_rate:.1f}%)")
            report.append(f"   📊 L3: {cat_data['level3_pass']}個 ({l3_rate:.1f}%)")
            report.append("")

        # 失敗食材サンプル
        failed_foods = [detail for detail in results["details"] if not detail["level3_pass"]]
        if failed_foods:
            report.append("❌ レベル3不合格食材（サンプル）")
            report.append("-" * 60)
            for food in failed_foods[:20]:
                issues_str = ", ".join(food["issues"])
                report.append(f"  • {food['food_name']}")
                report.append(f"    └─ 問題: {issues_str}")
                report.append(f"    └─ serving: {food['serving_count']}個, nutrition: {food['nutrition_count']}個")
            if len(failed_foods) > 20:
                report.append(f"  ... 他{len(failed_foods)-20}個")
            report.append("")

        # 結論
        report.append("🎯 結論")
        report.append("-" * 60)
        l3_rate = results['percentages']['level3_pass']
        if l3_rate >= 95:
            report.append("✅ 優秀: 高品質データ率が95%以上です")
        elif l3_rate >= 85:
            report.append("🟡 良好: 高品質データ率が85%以上です")
        else:
            report.append("🔴 要改善: 高品質データ率が85%未満です")

        missing_data = results['total_foods'] - results['level1_pass']
        if missing_data == 0:
            report.append("✅ 完璧: 全食材でデータが存在します")
        else:
            report.append(f"⚠️ 注意: {missing_data}個の食材でデータが不足しています")

        report.append("")
        report.append("=" * 100)

        return "\n".join(report)

    def save_quality_report(self, output_dir: str = "reports") -> str:
        """品質レポートを保存"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSONレポート
        json_path = os.path.join(output_dir, f"food_quality_check_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.quality_results, f, ensure_ascii=False, indent=2, default=str)

        # テキストレポート
        txt_path = os.path.join(output_dir, f"food_quality_check_{timestamp}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_quality_report())

        return f"品質レポート保存完了:\n  📄 JSON: {json_path}\n  📝 テキスト: {txt_path}"


def main():
    """メイン処理"""
    print("🔍 1,154食材段階的品質チェッカー")
    print("=" * 70)

    checker = FoodQualityChecker()

    # 1. カタログ食材読み込み
    catalog_foods = checker.load_catalog_foods()
    if not catalog_foods:
        print("❌ カタログデータの読み込みに失敗しました")
        return

    # 2. 収集データ読み込み
    collected_data = checker.load_collected_data()
    if not collected_data:
        print("❌ 収集データの読み込みに失敗しました")
        return

    # 3. 品質チェック実行
    results = checker.run_quality_check()
    if not results:
        print("❌ 品質チェックの実行に失敗しました")
        return

    # 4. レポート表示
    print(checker.generate_quality_report())

    # 5. レポート保存
    save_result = checker.save_quality_report()
    print(save_result)


if __name__ == "__main__":
    main()