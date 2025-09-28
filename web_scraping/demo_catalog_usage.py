#!/usr/bin/env python3
"""
食材カタログ活用デモンストレーション
既存カタログを使用して任意食材のserving情報を効率的に抽出
"""

import time
import json
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

from src.components.food_catalog_manager import FoodCatalogManager
from src.components.raw_serving_extractor import RawServingExtractor
from src.components.modal_handler import ModalHandler
from src.components.navigation_manager import NavigationManager
from config import config


class CatalogUsageDemo:
    """カタログ活用デモクラス"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.catalog_manager = None
        self.serving_extractor = None
        self.modal_handler = None
        self.navigation_manager = None
        self.demo_results = []

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

    def load_catalog(self, catalog_file: str = "test_results/food_catalog_latest.json"):
        """カタログを読み込み"""
        print(f"📁 カタログ読み込み: {catalog_file}")

        if not Path(catalog_file).exists():
            print(f"❌ カタログファイルが見つかりません: {catalog_file}")
            print("💡 先にカタログを構築してください:")
            print("   python build_food_catalog.py")
            return False

        success = self.catalog_manager.load_catalog(catalog_file)
        if success:
            stats = self.catalog_manager.food_catalog.get("statistics", {})
            print(f"✅ カタログ読み込み成功:")
            print(f"   📊 総食材数: {stats.get('total_foods', 0):,}個")
            print(f"   📂 総カテゴリ数: {stats.get('total_categories', 0)}個")
        return success

    def demo_food_search(self, search_queries: list):
        """食材検索デモ"""
        print(f"\n🔍 食材検索デモ")
        print("="*50)

        search_results = []

        for query in search_queries:
            print(f"\n🔎 検索クエリ: '{query}'")

            # カタログ検索
            food_info = self.catalog_manager.find_food_by_name(query)

            if food_info:
                print(f"✅ 発見: {food_info['original_name']}")
                print(f"   📂 カテゴリ: {food_info['category']}")

                result = {
                    "query": query,
                    "found": True,
                    "original_name": food_info['original_name'],
                    "category": food_info['category'],
                    "navigation_info": food_info['navigation_info']
                }
            else:
                print(f"❌ 未発見")
                result = {
                    "query": query,
                    "found": False
                }

            search_results.append(result)

        return search_results

    def demo_direct_navigation_and_serving_extraction(self, food_name: str):
        """直接ナビゲーション & serving抽出デモ"""
        print(f"\n🎯 直接ナビゲーション & serving抽出デモ")
        print("="*50)
        print(f"対象食材: {food_name}")

        try:
            # 初回ログインが必要
            print("\n🔐 初回ログイン...")
            login_success = self.navigation_manager.login_and_navigate_to_category("Dairy, Dairy Substitutes & Egg")
            if not login_success:
                raise Exception("ログイン失敗")

            # 1. カタログ検索
            print(f"\n📋 ステップ1: カタログ検索")
            food_info = self.catalog_manager.find_food_by_name(food_name)

            if not food_info:
                raise Exception(f"食材がカタログで見つかりません: {food_name}")

            print(f"✅ カタログで発見:")
            print(f"   📛 正式名: {food_info['original_name']}")
            print(f"   📂 カテゴリ: {food_info['category']}")

            # 2. 直接ナビゲーション
            print(f"\n🧭 ステップ2: 直接ナビゲーション")
            nav_start = time.time()

            nav_success = self.catalog_manager.navigate_to_food(food_name)

            nav_duration = time.time() - nav_start

            if not nav_success:
                raise Exception(f"ナビゲーション失敗: {food_name}")

            print(f"✅ ナビゲーション成功 ({nav_duration:.2f}秒)")

            # 3. Serving情報抽出
            print(f"\n📊 ステップ3: Serving情報抽出")

            # モーダルを開く
            modal_opened = self.modal_handler.open_serving_modal()
            if not modal_opened:
                raise Exception("Select Servingモーダルが開けませんでした")

            # serving情報を抽出
            raw_serving_options = self.serving_extractor.extract_raw_serving_options()

            # モーダルを閉じる
            self.modal_handler.close_modal()

            # 結果表示
            demo_result = {
                "food_name": food_name,
                "original_name": food_info['original_name'],
                "category": food_info['category'],
                "navigation_duration_seconds": nav_duration,
                "serving_options_count": len(raw_serving_options),
                "raw_serving_options": raw_serving_options,
                "success": len(raw_serving_options) > 0,
                "timestamp": datetime.now().isoformat()
            }

            if raw_serving_options:
                print(f"✅ Serving情報抽出成功: {len(raw_serving_options)}個のオプション")
                print(f"📋 Serving Options:")
                for i, option in enumerate(raw_serving_options, 1):
                    print(f"   {i}. {option['raw_text']}")
                    print(f"      Radio Value: {option['radio_value']}")
            else:
                print("❌ Serving情報抽出失敗")

            self.demo_results.append(demo_result)
            return demo_result

        except Exception as e:
            print(f"❌ デモエラー: {e}")
            return {
                "food_name": food_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def save_demo_results(self):
        """デモ結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results/catalog_usage_demo_{timestamp}.json"

        demo_summary = {
            "demo_summary": {
                "timestamp": datetime.now().isoformat(),
                "description": "食材カタログ活用デモンストレーション",
                "total_demos": len(self.demo_results),
                "successful_demos": sum(1 for r in self.demo_results if r.get("success"))
            },
            "demo_results": self.demo_results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(demo_summary, f, ensure_ascii=False, indent=2)

        print(f"\n📄 デモ結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def run_full_demo(self, catalog_file: str = "test_results/food_catalog_latest.json"):
        """完全デモを実行"""
        try:
            print("🎬 食材カタログ活用デモンストレーション開始")
            print("="*60)

            self.setup_driver()

            # 1. カタログ読み込み
            if not self.load_catalog(catalog_file):
                return False

            # 2. 食材検索デモ
            search_queries = [
                "almond milk",      # 部分一致テスト
                "greek yogurt",     # 部分一致テスト
                "cheddar cheese",   # 完全一致テスト
                "unknown food"      # 未発見テスト
            ]

            search_results = self.demo_food_search(search_queries)

            # 3. 直接ナビゲーション & serving抽出デモ
            # 検索成功した食材から1つ選択
            found_foods = [r for r in search_results if r.get("found")]
            if found_foods:
                target_food = found_foods[0]["original_name"]
                self.demo_direct_navigation_and_serving_extraction(target_food)
            else:
                print("❌ 検索成功した食材がないため、ナビゲーションデモをスキップ")

            # 結果サマリー
            print(f"\n{'='*60}")
            print("🏁 デモンストレーション完了")
            print(f"{'='*60}")

            successful_demos = sum(1 for r in self.demo_results if r.get("success"))
            total_demos = len(self.demo_results)

            print(f"📊 デモ結果: {successful_demos}/{total_demos} 成功")

            # 結果保存
            filename = self.save_demo_results()
            print(f"✅ デモンストレーションが完了しました: {filename}")

            return True

        except Exception as e:
            print(f"❌ デモ実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="食材カタログ活用デモ")
    parser.add_argument("-c", "--catalog",
                       default="test_results/food_catalog_latest.json",
                       help="使用するカタログファイル")
    parser.add_argument("--headless", action="store_true",
                       help="ヘッドレスモードで実行")

    args = parser.parse_args()

    # ヘッドレスモード設定を一時的に上書き
    if args.headless:
        config.HEADLESS = True

    demo = CatalogUsageDemo()
    success = demo.run_full_demo(args.catalog)

    if success:
        print("\n✅ デモンストレーションが正常に完了しました！")
        exit(0)
    else:
        print("\n❌ デモンストレーションに失敗しました。")
        exit(1)