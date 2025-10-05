#!/usr/bin/env python3
"""
包括的食材データ分析ツール

food_catalog_dataと収集済みデータを比較分析し、
重複、欠落、収集状況を詳細に調査する
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple
from pathlib import Path
from collections import defaultdict


class ComprehensiveFoodDataAnalyzer:
    """包括的食材データ分析クラス"""

    def __init__(self, catalog_dir: str = "food_catalog_data", data_dir: str = "data"):
        self.catalog_dir = catalog_dir
        self.data_dir = data_dir
        self.catalog_foods = {}
        self.collected_foods = {}
        self.analysis_results = {}

    def load_catalog_data(self) -> Dict[str, Any]:
        """食材カタログデータを全て読み込み"""
        print("📁 食材カタログデータ読み込み中...")

        catalog_data = {
            "categories": {},
            "total_foods": 0,
            "all_foods": [],
            "food_name_to_category": {},
            "categories_summary": {}
        }

        catalog_files = [f for f in os.listdir(self.catalog_dir) if f.endswith('.json')]

        for file_name in catalog_files:
            file_path = os.path.join(self.catalog_dir, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                category_info = data.get("collection_info", {})
                category_data = data.get("category_data", {})

                category_name = category_info.get("category_name", "Unknown")
                foods = category_data.get("foods", [])

                catalog_data["categories"][category_name] = {
                    "file_name": file_name,
                    "total_foods": len(foods),
                    "foods": foods,
                    "collection_info": category_info
                }

                catalog_data["categories_summary"][category_name] = len(foods)

                # 全食材リストに追加
                for food in foods:
                    food_name = food.get("food_name", "").strip()
                    if food_name:
                        # 正規化（改行除去）
                        normalized_name = re.sub(r'\n', ' ', food_name).strip()
                        food["normalized_name"] = normalized_name

                        catalog_data["all_foods"].append(food)
                        catalog_data["food_name_to_category"][normalized_name] = category_name
                        catalog_data["total_foods"] += 1

                print(f"  ✅ {category_name}: {len(foods)}個")

            except Exception as e:
                print(f"  ❌ {file_name}の読み込みエラー: {e}")

        print(f"📊 カタログ合計: {catalog_data['total_foods']}個の食材")
        self.catalog_foods = catalog_data
        return catalog_data

    def load_collected_data(self) -> Dict[str, Any]:
        """収集済みデータを読み込み"""
        print("\n📁 収集済みデータ読み込み中...")

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

            collected_data = {
                "file_path": latest_file,
                "total_processed": len(collection_results),
                "successful_collections": 0,
                "failed_collections": 0,
                "foods_by_status": {},
                "foods_by_category": defaultdict(list),
                "collected_food_names": set(),
                "food_details": {}
            }

            for result in collection_results:
                food_name = result.get("food_name", "").strip()
                normalized_name = re.sub(r'\n', ' ', food_name).strip()
                collection_success = result.get("data_collection_success", False)

                if collection_success:
                    collected_data["successful_collections"] += 1
                    status = "success"
                else:
                    collected_data["failed_collections"] += 1
                    status = "failed"

                collected_data["foods_by_status"][normalized_name] = status
                collected_data["collected_food_names"].add(normalized_name)
                collected_data["food_details"][normalized_name] = result

                # カテゴリ分類（カタログデータから取得）
                if hasattr(self, 'catalog_foods') and self.catalog_foods:
                    category = self.catalog_foods["food_name_to_category"].get(normalized_name, "Unknown")
                    collected_data["foods_by_category"][category].append(normalized_name)

            print(f"📊 収集結果: 総{collected_data['total_processed']}個")
            print(f"  ✅ 成功: {collected_data['successful_collections']}個")
            print(f"  ❌ 失敗: {collected_data['failed_collections']}個")

            self.collected_foods = collected_data
            return collected_data

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

    def analyze_coverage_and_duplicates(self) -> Dict[str, Any]:
        """カバレッジと重複の詳細分析"""
        print("\n🔍 カバレッジと重複分析中...")

        if not self.catalog_foods or not self.collected_foods:
            print("❌ カタログまたは収集データが読み込まれていません")
            return {}

        catalog_names = set()
        for food in self.catalog_foods["all_foods"]:
            normalized_name = food.get("normalized_name", "")
            if normalized_name:
                catalog_names.add(normalized_name)

        collected_names = self.collected_foods["collected_food_names"]

        analysis = {
            "catalog_total": len(catalog_names),
            "collected_total": len(collected_names),
            "successfully_collected": self.collected_foods["successful_collections"],
            "failed_collections": self.collected_foods["failed_collections"],

            # カバレッジ分析
            "covered_foods": catalog_names.intersection(collected_names),
            "missing_foods": catalog_names - collected_names,
            "extra_foods": collected_names - catalog_names,

            # 重複チェック（食材名の類似度）
            "potential_duplicates": self.find_potential_duplicates(catalog_names),

            # カテゴリ別分析
            "category_analysis": self.analyze_by_category(),

            # 統計
            "coverage_rate": 0,
            "success_rate_of_covered": 0
        }

        # カバレッジ率計算
        analysis["coverage_rate"] = (len(analysis["covered_foods"]) / analysis["catalog_total"]) * 100 if analysis["catalog_total"] > 0 else 0

        # カバーされた食材の成功率
        covered_successful = 0
        for food_name in analysis["covered_foods"]:
            if self.collected_foods["foods_by_status"].get(food_name) == "success":
                covered_successful += 1

        analysis["success_rate_of_covered"] = (covered_successful / len(analysis["covered_foods"])) * 100 if analysis["covered_foods"] else 0

        self.analysis_results = analysis
        return analysis

    def find_potential_duplicates(self, food_names: Set[str]) -> List[Tuple[str, str, float]]:
        """潜在的な重複食材を検出"""
        from difflib import SequenceMatcher

        duplicates = []
        food_list = list(food_names)

        for i, food1 in enumerate(food_list):
            for j, food2 in enumerate(food_list[i+1:], i+1):
                # 基本的な前処理
                name1 = re.sub(r'\d+cals.*$', '', food1).strip()
                name2 = re.sub(r'\d+cals.*$', '', food2).strip()

                # 類似度計算
                similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

                if similarity > 0.8:  # 80%以上の類似度
                    duplicates.append((food1, food2, similarity))

        return sorted(duplicates, key=lambda x: x[2], reverse=True)

    def analyze_by_category(self) -> Dict[str, Any]:
        """カテゴリ別詳細分析"""
        category_analysis = {}

        for category_name, foods in self.catalog_foods["categories"].items():
            category_foods = foods["foods"]
            category_food_names = set()
            for food in category_foods:
                normalized_name = food.get("normalized_name", "")
                if normalized_name:
                    category_food_names.add(normalized_name)

            collected_in_category = category_food_names.intersection(self.collected_foods["collected_food_names"])
            successful_in_category = 0

            for food_name in collected_in_category:
                if self.collected_foods["foods_by_status"].get(food_name) == "success":
                    successful_in_category += 1

            category_analysis[category_name] = {
                "total_in_catalog": len(category_food_names),
                "collected": len(collected_in_category),
                "successful": successful_in_category,
                "missing": list(category_food_names - self.collected_foods["collected_food_names"]),
                "coverage_rate": (len(collected_in_category) / len(category_food_names)) * 100 if category_food_names else 0,
                "success_rate": (successful_in_category / len(collected_in_category)) * 100 if collected_in_category else 0
            }

        return category_analysis

    def generate_comprehensive_report(self) -> str:
        """包括的レポートを生成"""
        if not self.analysis_results:
            return "分析が実行されていません"

        analysis = self.analysis_results

        report = []
        report.append("=" * 100)
        report.append("🔍 包括的食材データ分析レポート")
        report.append("=" * 100)
        report.append(f"📅 分析実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 基本統計
        report.append("📊 基本統計")
        report.append("-" * 60)
        report.append(f"📋 カタログ総食材数: {analysis['catalog_total']:,}個")
        report.append(f"📝 収集処理数: {analysis['collected_total']:,}個")
        report.append(f"✅ 成功収集数: {analysis['successfully_collected']:,}個")
        report.append(f"❌ 失敗収集数: {analysis['failed_collections']:,}個")
        report.append("")

        # カバレッジ分析
        report.append("📋 カバレッジ分析")
        report.append("-" * 60)
        report.append(f"🎯 カバー済み食材: {len(analysis['covered_foods']):,}個 ({analysis['coverage_rate']:.1f}%)")
        report.append(f"📊 カバー済み成功率: {analysis['success_rate_of_covered']:.1f}%")
        report.append(f"❓ 未カバー食材: {len(analysis['missing_foods']):,}個")
        report.append(f"🆕 カタログ外食材: {len(analysis['extra_foods']):,}個")
        report.append("")

        # 重複チェック結果
        duplicates = analysis.get("potential_duplicates", [])
        if duplicates:
            report.append("🔄 潜在的重複食材")
            report.append("-" * 60)
            report.append(f"検出数: {len(duplicates)}組")
            for food1, food2, similarity in duplicates[:10]:  # 上位10組
                report.append(f"  • {similarity:.1%}: '{food1}' ↔ '{food2}'")
            if len(duplicates) > 10:
                report.append(f"  ... 他{len(duplicates)-10}組")
            report.append("")
        else:
            report.append("🔄 潜在的重複食材: 検出されませんでした")
            report.append("")

        # カテゴリ別分析
        report.append("📂 カテゴリ別分析")
        report.append("-" * 60)
        category_analysis = analysis.get("category_analysis", {})

        # カテゴリを成功率でソート
        sorted_categories = sorted(category_analysis.items(),
                                 key=lambda x: x[1]["success_rate"], reverse=True)

        for category_name, cat_data in sorted_categories:
            report.append(f"📁 {category_name}")
            report.append(f"   📋 カタログ: {cat_data['total_in_catalog']}個")
            report.append(f"   📝 収集: {cat_data['collected']}個 ({cat_data['coverage_rate']:.1f}%)")
            report.append(f"   ✅ 成功: {cat_data['successful']}個 ({cat_data['success_rate']:.1f}%)")
            if cat_data['missing']:
                missing_count = len(cat_data['missing'])
                if missing_count <= 5:
                    report.append(f"   ❓ 未収集: {', '.join(cat_data['missing'][:5])}")
                else:
                    report.append(f"   ❓ 未収集: {missing_count}個 (例: {', '.join(cat_data['missing'][:3])}...)")
            report.append("")

        # 問題のある食材
        if analysis['missing_foods']:
            report.append("❓ 未カバー食材（サンプル）")
            report.append("-" * 60)
            missing_list = list(analysis['missing_foods'])[:20]
            for food in missing_list:
                report.append(f"   • {food}")
            if len(analysis['missing_foods']) > 20:
                report.append(f"   ... 他{len(analysis['missing_foods'])-20}個")
            report.append("")

        if analysis['extra_foods']:
            report.append("🆕 カタログ外食材（サンプル）")
            report.append("-" * 60)
            extra_list = list(analysis['extra_foods'])[:20]
            for food in extra_list:
                report.append(f"   • {food}")
            if len(analysis['extra_foods']) > 20:
                report.append(f"   ... 他{len(analysis['extra_foods'])-20}個")
            report.append("")

        # 結論
        report.append("🎯 結論")
        report.append("-" * 60)
        if analysis['coverage_rate'] >= 95:
            report.append("✅ 優秀: カバレッジ率が95%以上です")
        elif analysis['coverage_rate'] >= 85:
            report.append("🟡 良好: カバレッジ率が85%以上です")
        else:
            report.append("🔴 要改善: カバレッジ率が85%未満です")

        if analysis['success_rate_of_covered'] >= 90:
            report.append("✅ 優秀: カバー済み食材の成功率が90%以上です")
        elif analysis['success_rate_of_covered'] >= 75:
            report.append("🟡 良好: カバー済み食材の成功率が75%以上です")
        else:
            report.append("🔴 要改善: カバー済み食材の成功率が75%未満です")

        if len(analysis['extra_foods']) > 0:
            report.append(f"⚠️ 注意: {len(analysis['extra_foods'])}個のカタログ外食材が検出されました")

        report.append("")
        report.append("=" * 100)

        return "\n".join(report)

    def save_analysis_report(self, output_dir: str = "reports") -> str:
        """分析レポートを保存"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSONレポート
        json_path = os.path.join(output_dir, f"comprehensive_analysis_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "catalog_data": self.catalog_foods,
                "collected_data": self.collected_foods,
                "analysis_results": self.analysis_results
            }, f, ensure_ascii=False, indent=2, default=str)

        # テキストレポート
        txt_path = os.path.join(output_dir, f"comprehensive_analysis_{timestamp}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_comprehensive_report())

        return f"レポート保存完了:\n  📄 JSON: {json_path}\n  📝 テキスト: {txt_path}"


def main():
    """メイン処理"""
    print("🔍 包括的食材データ分析ツール")
    print("=" * 70)

    analyzer = ComprehensiveFoodDataAnalyzer()

    # 1. カタログデータ読み込み
    catalog_data = analyzer.load_catalog_data()
    if not catalog_data:
        print("❌ カタログデータの読み込みに失敗しました")
        return

    # 2. 収集データ読み込み
    collected_data = analyzer.load_collected_data()
    if not collected_data:
        print("❌ 収集データの読み込みに失敗しました")
        return

    # 3. 詳細分析実行
    analysis = analyzer.analyze_coverage_and_duplicates()
    if not analysis:
        print("❌ 分析の実行に失敗しました")
        return

    # 4. レポート表示
    print(analyzer.generate_comprehensive_report())

    # 5. レポート保存
    save_result = analyzer.save_analysis_report()
    print(save_result)


if __name__ == "__main__":
    main()