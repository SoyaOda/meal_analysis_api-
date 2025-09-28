#!/usr/bin/env python3
"""
セッション再開アプローチによる食材データ収集テストスクリプト
各食材ごとにブラウザを再起動してChromeDriverクラッシュを回避
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


class SessionRestartTester:
    """セッション再開アプローチによる食材データ収集テストクラス"""

    def __init__(self):
        self.test_results = []
        self.food_catalog = None

    def create_fresh_session(self):
        """新しいブラウザセッションを作成"""
        print("🚀 新しいブラウザセッション作成中...")
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(config.IMPLICIT_WAIT)
        wait = WebDriverWait(driver, config.TIMEOUT)

        # コンポーネントを初期化
        navigator = StableMultiFoodNavigator(driver, wait, config)
        data_collector = ComprehensiveFoodDataCollector(driver, wait, config)

        print("✅ 新しいブラウザセッション作成完了")
        return driver, wait, navigator, data_collector

    def cleanup_session(self, driver, navigator):
        """セッションをクリーンアップ"""
        try:
            if navigator:
                navigator.cleanup_session()
            if driver:
                driver.quit()
            print("🧹 セッションクリーンアップ完了")
        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")

    def load_food_catalog_once(self) -> bool:
        """食材カタログを一度だけ読み込み（後続のセッションで再利用）"""
        if self.food_catalog is not None:
            return True

        print("📁 食材カタログ読み込み...")
        # 一時的なナビゲーターを作成してカタログを読み込み
        driver, wait, navigator, data_collector = self.create_fresh_session()

        try:
            success = navigator.load_food_catalog()
            if success:
                self.food_catalog = navigator.food_catalog
                print(f"✅ 食材カタログ読み込み完了: {len(self.food_catalog)}カテゴリ")

            self.cleanup_session(driver, navigator)
            return success
        except Exception as e:
            print(f"❌ 食材カタログ読み込みエラー: {e}")
            self.cleanup_session(driver, navigator)
            return False

    def select_test_foods(self, count: int = 3) -> List[str]:
        """
        テスト用食材を選択（事前読み込みされたカタログから）

        Args:
            count: 選択する食材数

        Returns:
            List[str]: 選択された食材名のリスト
        """
        print(f"🎯 テスト用食材を選択中（{count}個）...")

        if not self.food_catalog:
            raise Exception("食材カタログが読み込まれていません")

        # 最初のカテゴリから食材を取得
        first_category = list(self.food_catalog.keys())[0]
        category_data = self.food_catalog[first_category]

        print(f"📂 対象カテゴリ: {first_category}")
        print(f"🍽️ カテゴリ内食材数: {len(category_data['foods'])}個")

        # 最初のN個の食材を選択（元の食材名をそのまま使用）
        selected_foods = []
        foods = category_data['foods']

        for i in range(min(count, len(foods))):
            food_name = foods[i]['food_name']
            selected_foods.append(food_name)

        print(f"✅ テスト食材選択完了:")
        for i, food_name in enumerate(selected_foods, 1):
            # 表示用のみ改行を空白に変換
            display_name = food_name.replace('\n', ' ')
            print(f"   {i}. {display_name[:50]}...")

        return selected_foods

    def collect_single_food_with_restart(self, food_name: str, sequence: int) -> Dict:
        """
        セッション再開アプローチで単一食材のデータを収集

        Args:
            food_name: 収集対象の食材名
            sequence: 食材の順番

        Returns:
            Dict: 食材の包括的データ収集結果
        """
        print(f"\n{'='*80}")
        print(f"🔄 セッション再開アプローチ食材データ収集 {sequence}: {food_name[:50]}...")
        print(f"{'='*80}")

        start_time = datetime.now()
        driver = None
        navigator = None

        try:
            # 1. 新しいブラウザセッションを作成
            print("🚀 新しいセッション作成...")
            driver, wait, navigator, data_collector = self.create_fresh_session()

            # 2. カタログを再設定（既に読み込み済みのデータを使用）
            navigator.food_catalog = self.food_catalog
            print("📁 食材カタログ再設定完了")

            # 3. 検索インデックスを再構築
            print("🔍 検索インデックス再構築中...")
            navigator.food_index = {}
            for category_name, category_data in self.food_catalog.items():
                for food in category_data['foods']:
                    normalized_name = navigator._normalize_food_name(food['food_name'])
                    navigator.food_index[normalized_name] = {
                        "original_name": food['food_name'],
                        "category": category_name,
                        "navigation_info": food
                    }
            print(f"✅ 検索インデックス構築完了: {len(navigator.food_index)}個の食材")

            # 4. セッション初期化（ログイン）
            print("🔐 セッション初期化...")
            if not navigator.initialize_session():
                raise Exception("セッション初期化失敗")

            # 5. 食材ページに移動
            print("🧭 食材ページに移動中...")
            nav_success = navigator.navigate_to_food_stable(food_name)

            if not nav_success:
                raise Exception("食材ナビゲーション失敗")

            # 6. 包括的データ収集（serving + 栄養素）
            print("📊 包括的データ収集実行...")
            food_data = data_collector.collect_complete_food_data(food_name)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 結果をまとめる
            result = {
                "sequence": sequence,
                "food_name": food_name,
                "navigation_success": nav_success,
                "data_collection_success": food_data.get("collection_success", False),
                "session_restart_success": True,
                "serving_options_count": len(food_data.get("serving_options", [])),
                "nutrition_data_count": len(food_data.get("nutrition_data", {}).get("detailed_nutrients", {})),
                "food_grade": food_data.get("nutrition_data", {}).get("food_grade", ""),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "comprehensive_data": food_data,
                "overall_success": nav_success and food_data.get("collection_success", False)
            }

            if result["overall_success"]:
                print(f"✅ セッション再開アプローチ収集成功: {duration:.2f}秒")
                print(f"   📋 Serving: {result['serving_options_count']}個")
                print(f"   🥗 栄養素: {result['nutrition_data_count']}種類")
                print(f"   🔄 セッション再起動: 成功")
            else:
                print(f"❌ データ収集失敗")

            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "sequence": sequence,
                "food_name": food_name,
                "navigation_success": False,
                "data_collection_success": False,
                "session_restart_success": False,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "overall_success": False
            }

            print(f"❌ セッション再開アプローチエラー: {e}")
            return result

        finally:
            # 7. セッションクリーンアップ
            print("🧹 セッションクリーンアップ...")
            self.cleanup_session(driver, navigator)

            # 次の食材のための待機
            print("⏳ 次の食材処理のための待機...")
            time.sleep(3)

    def collect_foods_with_restart(self, food_names: List[str]) -> List[Dict]:
        """
        セッション再開アプローチで複数食材のデータを収集

        Args:
            food_names: 収集対象の食材名リスト

        Returns:
            List[Dict]: 各食材の包括的データ収集結果
        """
        print(f"🔬 セッション再開アプローチ開始")
        print(f"📊 対象食材数: {len(food_names)}個")
        print(f"🎯 新ワークフロー: 食材→セッション作成→ログイン→データ収集→セッション破棄→次の食材")

        results = []

        for i, food_name in enumerate(food_names, 1):
            result = self.collect_single_food_with_restart(food_name, i)
            results.append(result)

        return results

    def print_session_restart_summary(self, results: List[Dict]):
        """セッション再開アプローチ結果サマリーを表示"""
        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_data = [r for r in results if r.get("data_collection_success")]
        successful_restart = [r for r in results if r.get("session_restart_success")]
        overall_successful = [r for r in results if r.get("overall_success")]

        print(f"\n{'='*80}")
        print("🏁 セッション再開アプローチ結果サマリー")
        print(f"{'='*80}")
        print(f"📊 総テスト数: {len(results)}個")
        print(f"🧭 ナビゲーション成功: {len(successful_nav)}/{len(results)} ({len(successful_nav)/len(results)*100:.1f}%)")
        print(f"📋 データ収集成功: {len(successful_data)}/{len(results)} ({len(successful_data)/len(results)*100:.1f}%)")
        print(f"🔄 セッション再起動成功: {len(successful_restart)}/{len(results)} ({len(successful_restart)/len(results)*100:.1f}%)")
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
            restart_status = "✓" if result.get("session_restart_success") else "✗"
            duration = result.get("duration_seconds", 0)
            serving_count = result.get("serving_options_count", 0)
            nutrient_count = result.get("nutrition_data_count", 0)

            print(f"  {status} {food_name:<30} N:{nav_status} D:{data_status} R:{restart_status} {duration:5.1f}s S:{serving_count:2d} Nu:{nutrient_count:2d}")

    def save_session_restart_results(self, results: List[Dict]) -> str:
        """セッション再開アプローチ収集結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/session_restart_collection_{timestamp}.json"

        # dataディレクトリ作成
        Path("data").mkdir(exist_ok=True)

        # 統計情報を計算
        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_data = [r for r in results if r.get("data_collection_success")]
        successful_restart = [r for r in results if r.get("session_restart_success")]
        overall_successful = [r for r in results if r.get("overall_success")]

        collection_data = {
            "collection_summary": {
                "timestamp": datetime.now().isoformat(),
                "method": "session_restart_approach_browser_restart_per_food",
                "total_foods": len(results),
                "successful_navigation": len(successful_nav),
                "successful_data_collection": len(successful_data),
                "successful_session_restart": len(successful_restart),
                "overall_successful": len(overall_successful),
                "navigation_success_rate": len(successful_nav) / len(results) * 100 if results else 0,
                "data_collection_success_rate": len(successful_data) / len(results) * 100 if results else 0,
                "session_restart_success_rate": len(successful_restart) / len(results) * 100 if results else 0,
                "overall_success_rate": len(overall_successful) / len(results) * 100 if results else 0
            },
            "collection_results": results,
            "improvements": {
                "session_restart_per_food": "implemented",
                "browser_memory_leak_prevention": "complete",
                "chromedriver_crash_avoidance": "complete"
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 セッション再開アプローチ収集結果を保存: {filename}")
        return filename

    def run_session_restart_test(self, food_count: int = 3):
        """セッション再開アプローチテストを実行"""
        try:
            print("🔬 セッション再開アプローチ食材データ収集テスト開始")
            print("="*90)

            # 1. 食材カタログ読み込み（一度だけ）
            if not self.load_food_catalog_once():
                print("❌ カタログ読み込み失敗")
                return False

            # 2. テスト食材選択
            test_foods = self.select_test_foods(food_count)

            # 3. セッション再開アプローチデータ収集実行
            results = self.collect_foods_with_restart(test_foods)

            # 4. 結果サマリー表示
            self.print_session_restart_summary(results)

            # 5. 結果保存
            filename = self.save_session_restart_results(results)

            overall_successful = [r for r in results if r.get("overall_success")]
            success_rate = len(overall_successful) / len(results) * 100 if results else 0

            print(f"\n🎉 セッション再開アプローチテスト完了!")
            print(f"✅ 総合成功率: {success_rate:.1f}%")
            print(f"📁 結果ファイル: {filename}")

            return success_rate >= 66.7  # 2/3以上の成功率で成功とみなす

        except Exception as e:
            print(f"❌ セッション再開アプローチテストエラー: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="セッション再開アプローチ食材データ収集テスト")
    parser.add_argument("-n", "--count", type=int, default=3,
                       help="収集する食材数")

    args = parser.parse_args()

    tester = SessionRestartTester()
    success = tester.run_session_restart_test(args.count)

    if success:
        print(f"\n🎉 セッション再開アプローチテストが成功しました！")
        exit(0)
    else:
        print(f"\n💥 セッション再開アプローチテストが失敗しました。")
        exit(1)


if __name__ == "__main__":
    main()