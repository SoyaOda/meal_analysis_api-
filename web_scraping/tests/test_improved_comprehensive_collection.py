#!/usr/bin/env python3
"""
改善版包括的食材データ収集テストスクリプト
FOODタブ経由リセット機能を使用した安定版
"""

import sys
import time
import json
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
from config import config


class ImprovedComprehensiveTester:
    """改善版包括的食材データ収集テストクラス"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.navigator = None
        self.data_collector = None
        self.test_results = []

    def setup_driver(self):
        """ChromeDriverを設定"""
        print("🚀 改善版ChromeDriverを起動中...")
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

        print("✅ 改善版ChromeDriver起動完了")

    def select_test_foods(self, count: int = 3) -> List[str]:
        """
        テスト用食材を選択（最初のカテゴリから）

        Args:
            count: 選択する食材数

        Returns:
            List[str]: 選択された食材名のリスト
        """
        print(f"🎯 テスト用食材を選択中（{count}個）...")

        # 最初のカテゴリから食材を取得
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

        print(f"✅ テスト食材選択完了:")
        for i, food_name in enumerate(selected_foods, 1):
            print(f"   {i}. {food_name[:50]}...")

        return selected_foods

    def collect_food_data_with_reset(self, food_names: List[str]) -> List[Dict]:
        """
        改善版：FOODタブリセット機能を使った食材データ収集

        Args:
            food_names: 収集対象の食材名リスト

        Returns:
            List[Dict]: 各食材の包括的データ収集結果
        """
        print(f"🔬 改善版包括的データ収集開始")
        print(f"📊 対象食材数: {len(food_names)}個")
        print(f"🎯 新ワークフロー: 食材→serving→栄養素→FOODタブリセット→次の食材")

        results = []

        for i, food_name in enumerate(food_names, 1):
            print(f"\n{'='*80}")
            print(f"🔄 改善版食材データ収集 {i}/{len(food_names)}: {food_name[:50]}...")
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
                        "reset_success": False,
                        "error": "食材ナビゲーション失敗",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue

                # 2. 包括的データ収集（serving + 栄養素）
                print("📊 包括的データ収集実行...")
                food_data = self.data_collector.collect_complete_food_data(food_name)

                # 3. FOODタブ経由リセット（新機能）
                print("🔄 FOODタブ経由リセット実行...")
                reset_success = self.navigator.reset_to_food_base_via_food_tab()

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # 結果をまとめる
                result = {
                    "sequence": i,
                    "food_name": food_name,
                    "navigation_success": nav_success,
                    "data_collection_success": food_data.get("collection_success", False),
                    "reset_success": reset_success,
                    "serving_options_count": len(food_data.get("serving_options", [])),
                    "nutrition_data_count": len(food_data.get("nutrition_data", {}).get("detailed_nutrients", {})),
                    "food_grade": food_data.get("nutrition_data", {}).get("food_grade", ""),
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "comprehensive_data": food_data,
                    "overall_success": nav_success and food_data.get("collection_success", False) and reset_success
                }

                if result["overall_success"]:
                    print(f"✅ 改善版データ収集成功: {duration:.2f}秒")
                    print(f"   📋 Serving: {result['serving_options_count']}個")
                    print(f"   🥗 栄養素: {result['nutrition_data_count']}種類")
                    print(f"   🔄 リセット: {'成功' if reset_success else '失敗'}")
                else:
                    print(f"❌ データ収集失敗")

                results.append(result)

                # 4. 次の食材のための安定化待機（最後の食材以外）
                if i < len(food_names):
                    print("⏳ 次の食材処理のための安定化待機...")
                    time.sleep(5)  # 安定化のため待機時間を増加

            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                result = {
                    "sequence": i,
                    "food_name": food_name,
                    "navigation_success": False,
                    "data_collection_success": False,
                    "reset_success": False,
                    "error": str(e),
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "overall_success": False
                }

                print(f"❌ 改善版データ収集エラー: {e}")
                results.append(result)

        return results

    def print_improved_summary(self, results: List[Dict]):
        """改善版結果サマリーを表示"""
        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_data = [r for r in results if r.get("data_collection_success")]
        successful_reset = [r for r in results if r.get("reset_success")]
        overall_successful = [r for r in results if r.get("overall_success")]

        print(f"\n{'='*80}")
        print("🏁 改善版包括的データ収集結果サマリー")
        print(f"{'='*80}")
        print(f"📊 総テスト数: {len(results)}個")
        print(f"🧭 ナビゲーション成功: {len(successful_nav)}/{len(results)} ({len(successful_nav)/len(results)*100:.1f}%)")
        print(f"📋 データ収集成功: {len(successful_data)}/{len(results)} ({len(successful_data)/len(results)*100:.1f}%)")
        print(f"🔄 リセット成功: {len(successful_reset)}/{len(results)} ({len(successful_reset)/len(results)*100:.1f}%)")
        print(f"✅ 総合成功: {len(overall_successful)}/{len(results)} ({len(overall_successful)/len(results)*100:.1f}%)")

        if overall_successful:
            durations = [r["duration_seconds"] for r in overall_successful]
            total_serving = sum(r.get("serving_options_count", 0) for r in overall_successful)
            total_nutrients = sum(r.get("nutrition_data_count", 0) for r in overall_successful)

            print(f"⏱️ 平均処理時間: {sum(durations)/len(durations):.2f}秒")
            print(f"📈 総serving options数: {total_serving}個")
            print(f"🥗 総栄養素数: {total_nutrients}種類")
            print(f"📊 平均serving/食材: {total_serving/len(overall_successful):.1f}個")
            print(f"🧬 平均栄養素/食材: {total_nutrients/len(overall_successful):.1f}種類")

        print(f"\n📋 個別結果:")
        for result in results:
            status = "✅" if result.get("overall_success") else "❌"
            food_name = result["food_name"][:25] + "..." if len(result["food_name"]) > 25 else result["food_name"]
            nav_status = "✓" if result.get("navigation_success") else "✗"
            data_status = "✓" if result.get("data_collection_success") else "✗"
            reset_status = "✓" if result.get("reset_success") else "✗"
            duration = result.get("duration_seconds", 0)
            serving_count = result.get("serving_options_count", 0)
            nutrient_count = result.get("nutrition_data_count", 0)

            print(f"  {status} {food_name:<30} N:{nav_status} D:{data_status} R:{reset_status} {duration:5.1f}s S:{serving_count:2d} Nu:{nutrient_count:2d}")

    def save_improved_results(self, results: List[Dict]) -> str:
        """改善版収集結果を保存（data/ディレクトリに保存）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/improved_comprehensive_collection_{timestamp}.json"

        # dataディレクトリ作成
        Path("data").mkdir(exist_ok=True)

        # 統計情報を計算
        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_data = [r for r in results if r.get("data_collection_success")]
        successful_reset = [r for r in results if r.get("reset_success")]
        overall_successful = [r for r in results if r.get("overall_success")]

        collection_data = {
            "collection_summary": {
                "timestamp": datetime.now().isoformat(),
                "method": "improved_comprehensive_collection_with_food_tab_reset",
                "total_foods": len(results),
                "successful_navigation": len(successful_nav),
                "successful_data_collection": len(successful_data),
                "successful_reset": len(successful_reset),
                "overall_successful": len(overall_successful),
                "navigation_success_rate": len(successful_nav) / len(results) * 100 if results else 0,
                "data_collection_success_rate": len(successful_data) / len(results) * 100 if results else 0,
                "reset_success_rate": len(successful_reset) / len(results) * 100 if results else 0,
                "overall_success_rate": len(overall_successful) / len(results) * 100 if results else 0
            },
            "collection_results": results,
            "improvements": {
                "food_tab_reset_function": "implemented",
                "reduced_wait_times": "2_seconds_between_foods",
                "enhanced_error_handling": "comprehensive"
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 改善版収集結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースクリーンアップ"""
        if self.navigator:
            self.navigator.cleanup_session()
        if self.driver:
            self.driver.quit()

    def run_improved_collection_test(self, food_count: int = 3):
        """改善版包括的データ収集テストを実行"""
        try:
            print("🔬 改善版包括的食材データ収集テスト開始")
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

            # 3. テスト食材選択
            test_foods = self.select_test_foods(food_count)

            # 4. 改善版データ収集実行
            results = self.collect_food_data_with_reset(test_foods)

            # 5. 結果サマリー表示
            self.print_improved_summary(results)

            # 6. 結果保存
            filename = self.save_improved_results(results)

            overall_successful = [r for r in results if r.get("overall_success")]
            success_rate = len(overall_successful) / len(results) * 100 if results else 0

            print(f"\n🎉 改善版データ収集テスト完了!")
            print(f"✅ 総合成功率: {success_rate:.1f}%")
            print(f"📁 結果ファイル: {filename}")

            return success_rate >= 66.7  # 2/3以上の成功率で成功とみなす

        except Exception as e:
            print(f"❌ 改善版データ収集テストエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="改善版包括的食材データ収集テスト")
    parser.add_argument("-n", "--count", type=int, default=3,
                       help="収集する食材数")

    args = parser.parse_args()

    tester = ImprovedComprehensiveTester()
    success = tester.run_improved_collection_test(args.count)

    if success:
        print(f"\n🎉 改善版包括的データ収集テストが成功しました！")
        exit(0)
    else:
        print(f"\n💥 改善版包括的データ収集テストが失敗しました。")
        exit(1)


if __name__ == "__main__":
    main()