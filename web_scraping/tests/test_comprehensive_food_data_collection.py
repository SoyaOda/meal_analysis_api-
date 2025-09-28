#!/usr/bin/env python3
"""
包括的食材データ収集テストスクリプト
serving情報 + 栄養素情報を効率的に収集してJSONで保存
栄養素を閉じずにFOODタブで初期状態に戻る効率的ワークフロー
"""

import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.components.stable_multi_food_navigator import StableMultiFoodNavigator
from src.components.comprehensive_food_data_collector import ComprehensiveFoodDataCollector
from src.components.modal_handler import ModalHandler
from config import config


class ComprehensiveFoodDataTester:
    """包括的食材データ収集テストクラス"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.navigator = None
        self.data_collector = None
        self.modal_handler = None
        self.test_results = []

    def setup_driver(self):
        """ChromeDriverを設定"""
        print("🚀 ChromeDriverを起動中...")
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)

        # コンポーネントを初期化
        self.navigator = StableMultiFoodNavigator(self.driver, self.wait, config)
        self.data_collector = ComprehensiveFoodDataCollector(self.driver, self.wait, config)
        self.modal_handler = ModalHandler(self.driver)

        print("✅ ChromeDriver起動完了")

    def select_first_category_foods(self, count: int = 5) -> List[str]:
        """
        最初のカテゴリから指定数の食材を選択

        Args:
            count: 選択する食材数

        Returns:
            List[str]: 選択された食材名のリスト
        """
        print(f"🎯 最初のカテゴリから{count}個の食材を選択中...")

        # 食材カタログから最初のカテゴリを取得
        first_category = list(self.navigator.food_catalog.keys())[0]
        category_data = self.navigator.food_catalog[first_category]

        print(f"📂 対象カテゴリ: {first_category}")
        print(f"🍽️ カテゴリ内食材数: {len(category_data['foods'])}個")

        # 最初のN個の食材を選択
        selected_foods = []
        foods = category_data['foods']

        for i in range(min(count, len(foods))):
            food_name = foods[i]['food_name']
            selected_foods.append(food_name)

        print(f"✅ 食材選択完了:")
        for i, food_name in enumerate(selected_foods, 1):
            print(f"   {i}. {food_name[:60]}...")

        return selected_foods

    def collect_comprehensive_food_data_sequence(self, food_names: List[str]) -> List[Dict]:
        """
        包括的食材データを順次収集（効率的ワークフロー版）

        Args:
            food_names: 収集対象の食材名リスト

        Returns:
            List[Dict]: 各食材の包括的データ収集結果
        """
        print(f"🔬 包括的データ収集開始")
        print(f"📊 対象食材数: {len(food_names)}個")
        print(f"🎯 ワークフロー: serving→栄養素→FOODタブ復帰→次の食材")

        results = []

        for i, food_name in enumerate(food_names, 1):
            print(f"\n{'='*80}")
            print(f"🔄 食材データ収集 {i}/{len(food_names)}: {food_name[:50]}...")
            print(f"{'='*80}")

            start_time = datetime.now()

            try:
                # 1. 食材ページに移動
                print("🧭 食材ページに移動中...")
                nav_success = self.navigator.navigate_to_food_stable(food_name)

                if not nav_success:
                    print(f"❌ 食材移動失敗: {food_name}")
                    results.append({
                        "sequence": i,
                        "food_name": food_name,
                        "navigation_success": False,
                        "data_collection_success": False,
                        "error": "食材ナビゲーション失敗",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue

                # 2. 包括的データ収集（serving + 栄養素）
                print("📊 包括的データ収集実行...")
                food_data = self.data_collector.collect_complete_food_data(food_name)

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # 結果をまとめる
                result = {
                    "sequence": i,
                    "food_name": food_name,
                    "navigation_success": nav_success,
                    "data_collection_success": food_data.get("collection_success", False),
                    "serving_options_count": len(food_data.get("serving_options", [])),
                    "nutrition_data_count": len(food_data.get("nutrition_data", {}).get("detailed_nutrients", {})),
                    "food_grade": food_data.get("nutrition_data", {}).get("food_grade", ""),
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "comprehensive_data": food_data  # 完全なデータを保存
                }

                if result["data_collection_success"]:
                    print(f"✅ 包括的データ収集成功: {duration:.2f}秒")
                    print(f"   📋 Serving: {result['serving_options_count']}個")
                    print(f"   🥗 栄養素: {result['nutrition_data_count']}種類")
                else:
                    print(f"❌ データ収集失敗")

                results.append(result)

                # 3. 次の食材のための短い待機（最後の食材以外）
                if i < len(food_names):
                    print("⏳ 次の食材処理のための待機...")
                    time.sleep(3)

            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                result = {
                    "sequence": i,
                    "food_name": food_name,
                    "navigation_success": False,
                    "data_collection_success": False,
                    "error": str(e),
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat()
                }

                print(f"❌ 包括的データ収集エラー: {e}")
                results.append(result)

        return results

    def print_collection_summary(self, results: List[Dict]):
        """収集結果サマリーを表示"""
        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_data = [r for r in results if r.get("data_collection_success")]

        print(f"\n{'='*80}")
        print("🏁 包括的データ収集結果サマリー")
        print(f"{'='*80}")
        print(f"📊 総テスト数: {len(results)}個")
        print(f"🧭 ナビゲーション成功: {len(successful_nav)}/{len(results)} ({len(successful_nav)/len(results)*100:.1f}%)")
        print(f"📋 データ収集成功: {len(successful_data)}/{len(results)} ({len(successful_data)/len(results)*100:.1f}%)")

        if successful_data:
            durations = [r["duration_seconds"] for r in successful_data]
            total_serving = sum(r.get("serving_options_count", 0) for r in successful_data)
            total_nutrients = sum(r.get("nutrition_data_count", 0) for r in successful_data)

            print(f"⏱️ 平均処理時間: {sum(durations)/len(durations):.2f}秒")
            print(f"📈 総serving options数: {total_serving}個")
            print(f"🥗 総栄養素数: {total_nutrients}種類")
            print(f"📊 平均serving/食材: {total_serving/len(successful_data):.1f}個")
            print(f"🧬 平均栄養素/食材: {total_nutrients/len(successful_data):.1f}種類")

        print(f"\n📋 個別結果:")
        for result in results:
            status = "✅" if result.get("data_collection_success") else "❌"
            food_name = result["food_name"][:30] + "..." if len(result["food_name"]) > 30 else result["food_name"]
            nav_status = "✓" if result.get("navigation_success") else "✗"
            data_status = "✓" if result.get("data_collection_success") else "✗"
            duration = result.get("duration_seconds", 0)
            serving_count = result.get("serving_options_count", 0)
            nutrient_count = result.get("nutrition_data_count", 0)

            print(f"  {status} {food_name:<35} Nav:{nav_status} Data:{data_status} {duration:5.1f}s S:{serving_count:2d} N:{nutrient_count:2d}")

    def save_comprehensive_results(self, results: List[Dict]) -> str:
        """包括的収集結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"food_catalog_data/comprehensive_food_data_collection_{timestamp}.json"

        # 統計情報を計算
        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_data = [r for r in results if r.get("data_collection_success")]

        collection_data = {
            "collection_summary": {
                "timestamp": datetime.now().isoformat(),
                "method": "comprehensive_food_data_collection",
                "total_foods": len(results),
                "successful_navigation": len(successful_nav),
                "successful_data_collection": len(successful_data),
                "navigation_success_rate": len(successful_nav) / len(results) * 100 if results else 0,
                "data_collection_success_rate": len(successful_data) / len(results) * 100 if results else 0
            },
            "collection_results": results,
            "statistics": {
                "total_serving_options": sum(r.get("serving_options_count", 0) for r in results),
                "total_nutrients": sum(r.get("nutrition_data_count", 0) for r in results),
                "avg_serving_per_food": sum(r.get("serving_options_count", 0) for r in successful_data) / len(successful_data) if successful_data else 0,
                "avg_nutrients_per_food": sum(r.get("nutrition_data_count", 0) for r in successful_data) / len(successful_data) if successful_data else 0
            }
        }

        # 統計情報を追加計算
        if successful_data:
            durations = [r["duration_seconds"] for r in successful_data]
            collection_data["statistics"].update({
                "avg_duration_seconds": sum(durations) / len(durations),
                "min_duration_seconds": min(durations),
                "max_duration_seconds": max(durations)
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 包括的収集結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースクリーンアップ"""
        if self.navigator:
            self.navigator.cleanup_session()
        if self.driver:
            self.driver.quit()

    def run_comprehensive_collection_test(self, food_count: int = 5):
        """包括的データ収集テストを実行"""
        try:
            print("🔬 包括的食材データ収集テスト開始")
            print("="*90)

            self.setup_driver()

            # 1. カタログ読み込み
            print("📁 食材カタログ読み込み...")
            if not self.navigator.load_food_catalog():
                print("❌ カタログ読み込み失敗")
                return False

            # 2. セッション初期化（ログイン）
            print("🔐 セッション初期化...")
            if not self.navigator.initialize_session():
                print("❌ セッション初期化失敗")
                return False

            # 3. 最初のカテゴリから食材選択
            test_foods = self.select_first_category_foods(food_count)

            # 4. 包括的データ収集実行
            results = self.collect_comprehensive_food_data_sequence(test_foods)

            # 5. 結果サマリー表示
            self.print_collection_summary(results)

            # 6. 結果保存
            filename = self.save_comprehensive_results(results)

            successful_data = [r for r in results if r.get("data_collection_success")]
            success_rate = len(successful_data) / len(results) * 100 if results else 0

            print(f"\n🎉 包括的データ収集テスト完了!")
            print(f"✅ データ収集成功率: {success_rate:.1f}%")
            print(f"📁 結果ファイル: {filename}")

            return success_rate > 50  # 50%以上の成功率で成功とみなす

        except Exception as e:
            print(f"❌ 包括的データ収集テストエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="包括的食材データ収集テスト")
    parser.add_argument("-n", "--count", type=int, default=5,
                       help="収集する食材数")

    args = parser.parse_args()

    tester = ComprehensiveFoodDataTester()
    success = tester.run_comprehensive_collection_test(args.count)

    if success:
        print(f"\n🎉 包括的データ収集テストが成功しました！")
        exit(0)
    else:
        print(f"\n💥 包括的データ収集テストが失敗しました。")
        exit(1)


if __name__ == "__main__":
    main()