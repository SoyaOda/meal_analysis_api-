#!/usr/bin/env python3
"""
食材カタログ統合テストスクリプト
カタログ構築 → 特定食材検索 → serving情報抽出の統合フローをテスト
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# 自作コンポーネントをインポート
from src.components.food_catalog_manager import FoodCatalogManager
from src.components.raw_serving_extractor import RawServingExtractor
from src.components.modal_handler import ModalHandler
from src.components.navigation_manager import NavigationManager
from config import config


class CatalogIntegrationTester:
    """カタログ統合テストクラス"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.catalog_manager = None
        self.serving_extractor = None
        self.modal_handler = None
        self.navigation_manager = None
        self.test_results = []

    def setup_driver(self):
        """ChromeDriverを設定"""
        print("🚀 ChromeDriverを起動中...")
        chrome_options = Options()
        if config.HEADLESS:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)

        # 全コンポーネントを初期化
        self.catalog_manager = FoodCatalogManager(self.driver, self.wait, config)
        self.serving_extractor = RawServingExtractor(self.driver)
        self.modal_handler = ModalHandler(self.driver)
        self.navigation_manager = NavigationManager(self.driver, self.wait, config)

    def test_catalog_build_or_load(self, force_rebuild: bool = False):
        """
        カタログ構築またはロードをテスト

        Args:
            force_rebuild: Trueの場合、既存カタログがあっても再構築
        """
        test_name = "catalog_build_or_load"
        print(f"\n{'='*60}")
        print(f"🧪 テスト開始: {test_name}")
        print(f"{'='*60}")

        try:
            # 既存カタログファイルをチェック
            catalog_file = "test_results/food_catalog_latest.json"
            catalog_exists = Path(catalog_file).exists()

            if catalog_exists and not force_rebuild:
                print("📁 既存カタログを読み込み中...")
                success = self.catalog_manager.load_catalog(catalog_file)
                method = "loaded_existing"
            else:
                print("🏗️ 新規カタログを構築中...")
                # ログイン & ナビゲーション
                login_success = self.navigation_manager.login_and_navigate_to_category("Dairy, Dairy Substitutes & Egg")
                if not login_success:
                    raise Exception("ログイン・ナビゲーション失敗")

                catalog = self.catalog_manager.build_complete_catalog()
                success = len(catalog) > 0

                if success:
                    # 最新カタログとして保存
                    self.catalog_manager.save_catalog(catalog_file)
                method = "built_new"

            test_result = {
                "test_name": test_name,
                "success": success,
                "method": method,
                "catalog_stats": self.catalog_manager.food_catalog.get("statistics", {}),
                "timestamp": datetime.now().isoformat()
            }

            if success:
                stats = self.catalog_manager.food_catalog.get("statistics", {})
                print(f"✅ カタログ準備成功:")
                print(f"   📊 総食材数: {stats.get('total_foods', 0)}個")
                print(f"   📂 総カテゴリ数: {stats.get('total_categories', 0)}個")
                print(f"   📈 平均食材数/カテゴリ: {stats.get('avg_foods_per_category', 0):.1f}個")
            else:
                print("❌ カタログ準備失敗")

            self.test_results.append(test_result)
            return test_result

        except Exception as e:
            print(f"❌ カタログテストエラー: {e}")
            test_result = {
                "test_name": test_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(test_result)
            return test_result

    def test_food_search_and_navigation(self, food_names: list):
        """
        食材検索・ナビゲーションをテスト

        Args:
            food_names: テストする食材名のリスト
        """
        test_name = "food_search_and_navigation"
        print(f"\n{'='*60}")
        print(f"🧪 テスト開始: {test_name}")
        print(f"{'='*60}")

        search_results = []

        for food_name in food_names:
            try:
                print(f"\n🔍 食材検索: {food_name}")

                # カタログから食材を検索
                food_info = self.catalog_manager.find_food_by_name(food_name)

                if food_info:
                    print(f"✅ カタログで発見: {food_info['category']}カテゴリ")

                    # 食材ページに移動
                    nav_success = self.catalog_manager.navigate_to_food(food_name)

                    result = {
                        "food_name": food_name,
                        "found_in_catalog": True,
                        "category": food_info["category"],
                        "navigation_success": nav_success,
                        "original_name": food_info["original_name"]
                    }

                    if nav_success:
                        print(f"✅ ナビゲーション成功")
                    else:
                        print(f"❌ ナビゲーション失敗")
                else:
                    print(f"❌ カタログで未発見")
                    result = {
                        "food_name": food_name,
                        "found_in_catalog": False,
                        "navigation_success": False
                    }

                search_results.append(result)

            except Exception as e:
                print(f"❌ 食材検索エラー ({food_name}): {e}")
                search_results.append({
                    "food_name": food_name,
                    "found_in_catalog": False,
                    "navigation_success": False,
                    "error": str(e)
                })

        test_result = {
            "test_name": test_name,
            "success": any(r.get("navigation_success") for r in search_results),
            "search_results": search_results,
            "total_searched": len(food_names),
            "successful_navigations": sum(1 for r in search_results if r.get("navigation_success")),
            "timestamp": datetime.now().isoformat()
        }

        self.test_results.append(test_result)
        return test_result

    def test_serving_extraction_with_catalog(self, food_name: str):
        """
        カタログ経由での食材serving情報抽出をテスト

        Args:
            food_name: テストする食材名
        """
        test_name = f"serving_extraction_via_catalog_{food_name.replace(' ', '_').lower()}"
        print(f"\n{'='*60}")
        print(f"🧪 テスト開始: {test_name}")
        print(f"{'='*60}")

        try:
            # 1. カタログから食材を検索
            print(f"🔍 ステップ1: カタログ検索 - {food_name}")
            food_info = self.catalog_manager.find_food_by_name(food_name)

            if not food_info:
                raise Exception(f"食材がカタログで見つかりません: {food_name}")

            print(f"✅ カタログで発見: {food_info['original_name']} ({food_info['category']})")

            # 2. 食材ページに移動
            print(f"🎯 ステップ2: 食材ページに移動")
            nav_success = self.catalog_manager.navigate_to_food(food_name)

            if not nav_success:
                raise Exception(f"食材ページへの移動失敗: {food_name}")

            print(f"✅ 食材ページ移動成功")

            # 3. Select Servingモーダルを開く
            print(f"🖱️ ステップ3: Select Servingモーダルを開く")
            modal_opened = self.modal_handler.open_serving_modal()

            if not modal_opened:
                raise Exception("Select Servingモーダルが開けませんでした")

            print(f"✅ Select Servingモーダル開放成功")

            # 4. 生serving情報を抽出
            print(f"📊 ステップ4: 生serving情報を抽出")
            raw_serving_options = self.serving_extractor.extract_raw_serving_options()

            # 5. モーダルを閉じる
            self.modal_handler.close_modal()

            # 結果を検証
            test_result = {
                "test_name": test_name,
                "food_name": food_name,
                "original_name": food_info['original_name'],
                "category": food_info['category'],
                "success": len(raw_serving_options) > 0,
                "serving_options_count": len(raw_serving_options),
                "raw_serving_options": raw_serving_options,
                "timestamp": datetime.now().isoformat()
            }

            if raw_serving_options:
                print(f"✅ serving情報抽出成功: {len(raw_serving_options)}個のオプション")
                for i, option in enumerate(raw_serving_options, 1):
                    print(f"  {i}. {option['raw_text']} (radio: {option['radio_value']})")
            else:
                print("❌ serving情報抽出失敗")

            self.test_results.append(test_result)
            return test_result

        except Exception as e:
            print(f"❌ カタログ経由serving抽出エラー: {e}")
            test_result = {
                "test_name": test_name,
                "food_name": food_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(test_result)
            return test_result

    def save_integration_test_results(self):
        """統合テスト結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results/catalog_integration_test_results_{timestamp}.json"

        test_summary = {
            "integration_test_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "successful_tests": sum(1 for r in self.test_results if r.get("success")),
                "failed_tests": sum(1 for r in self.test_results if not r.get("success")),
                "description": "食材カタログ統合テスト - カタログ構築/ロード → 食材検索 → serving抽出"
            },
            "test_results": self.test_results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, ensure_ascii=False, indent=2)

        print(f"📄 統合テスト結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def run_full_integration_test(self, force_rebuild_catalog: bool = False):
        """完全統合テストを実行"""
        try:
            print("🧪 食材カタログ統合テスト開始")
            print("="*60)

            self.setup_driver()

            # 1. カタログ構築/ロードテスト
            catalog_result = self.test_catalog_build_or_load(force_rebuild_catalog)
            if not catalog_result.get("success"):
                print("❌ カタログ準備失敗。テスト中断")
                return False

            # 2. 食材検索・ナビゲーションテスト
            test_foods = [
                "Almond milk unsweetened fortified",
                "Greek yogurt plain",
                "Cheddar cheese"
            ]

            search_result = self.test_food_search_and_navigation(test_foods)
            successful_foods = [r for r in search_result.get("search_results", [])
                              if r.get("navigation_success")]

            # 3. serving情報抽出テスト（成功した食材で）
            if successful_foods:
                target_food = successful_foods[0]["original_name"]
                serving_result = self.test_serving_extraction_with_catalog(target_food)
            else:
                print("❌ ナビゲーション成功食材なし。serving抽出テストスキップ")

            # 結果サマリー
            print(f"\n{'='*60}")
            print("🏁 統合テスト完了")
            print(f"{'='*60}")

            successful_tests = sum(1 for r in self.test_results if r.get("success"))
            total_tests = len(self.test_results)

            print(f"📊 統合テスト結果: {successful_tests}/{total_tests} 成功")

            # 詳細結果
            for result in self.test_results:
                status = "✅" if result.get("success") else "❌"
                print(f"   {status} {result['test_name']}")

            # 結果保存
            filename = self.save_integration_test_results()
            print(f"✅ 統合テストが完了しました: {filename}")

            return True

        except Exception as e:
            print(f"❌ 統合テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="食材カタログ統合テスト")
    parser.add_argument("--rebuild-catalog", action="store_true",
                       help="既存カタログがあっても強制的に再構築")

    args = parser.parse_args()

    tester = CatalogIntegrationTester()
    tester.run_full_integration_test(force_rebuild_catalog=args.rebuild_catalog)