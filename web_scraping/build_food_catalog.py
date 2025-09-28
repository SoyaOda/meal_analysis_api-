#!/usr/bin/env python3
"""
食材カタログ構築スクリプト
全カテゴリの食材リストを収集してJSONファイルに保存
"""

import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

from src.components.food_catalog_manager import FoodCatalogManager
from src.components.navigation_manager import NavigationManager
from config import config


class FoodCatalogBuilder:
    """食材カタログ構築クラス"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.catalog_manager = None
        self.navigation_manager = None

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

        # コンポーネントを初期化
        self.catalog_manager = FoodCatalogManager(self.driver, self.wait, config)
        self.navigation_manager = NavigationManager(self.driver, self.wait, config)

    def build_and_save_catalog(self, output_filename: str = None):
        """カタログを構築して保存"""
        try:
            print("🏗️ 食材カタログ構築開始")
            print("="*60)

            # ログイン & 初期ナビゲーション
            print("🔐 ログイン中...")
            login_success = self.navigation_manager.login_and_navigate_to_category("Dairy, Dairy Substitutes & Egg")
            if not login_success:
                print("❌ ログイン失敗")
                return False

            print("✅ ログイン成功")

            # カタログ構築開始
            print("\n🏗️ 全カテゴリ食材カタログを構築中...")
            start_time = datetime.now()

            catalog = self.catalog_manager.build_complete_catalog()

            end_time = datetime.now()
            duration = end_time - start_time

            if not catalog:
                print("❌ カタログ構築失敗")
                return False

            # 構築結果表示
            stats = catalog.get("statistics", {})
            print(f"\n🎉 カタログ構築完了!")
            print(f"{'='*60}")
            print(f"📊 総食材数: {stats.get('total_foods', 0):,}個")
            print(f"📂 総カテゴリ数: {stats.get('total_categories', 0)}個")
            print(f"📈 平均食材数/カテゴリ: {stats.get('avg_foods_per_category', 0):.1f}個")
            print(f"⏱️ 所要時間: {duration}")

            # カテゴリ別詳細
            print(f"\n📂 カテゴリ別詳細:")
            categories = catalog.get("categories", {})
            for cat_name, cat_data in categories.items():
                food_count = cat_data.get("food_count", 0)
                print(f"   📋 {cat_name}: {food_count}個")

            # ファイル保存
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"test_results/food_catalog_{timestamp}.json"

            saved_file = self.catalog_manager.save_catalog(output_filename)

            # 最新版としても保存
            latest_file = "test_results/food_catalog_latest.json"
            self.catalog_manager.save_catalog(latest_file)

            print(f"\n📄 カタログファイル:")
            print(f"   📁 メイン: {saved_file}")
            print(f"   🔗 最新版: {latest_file}")

            # 使用例表示
            print(f"\n💡 使用例:")
            print(f"   # カタログ読み込み")
            print(f"   catalog_manager.load_catalog('{latest_file}')")
            print(f"   ")
            print(f"   # 食材検索")
            print(f"   food_info = catalog_manager.find_food_by_name('Almond milk')")
            print(f"   ")
            print(f"   # 直接ナビゲーション")
            print(f"   catalog_manager.navigate_to_food('Greek yogurt plain')")

            return True

        except Exception as e:
            print(f"❌ カタログ構築エラー: {e}")
            import traceback
            traceback.print_exc()
            return False

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def run_catalog_build(self, output_filename: str = None):
        """カタログ構築を実行"""
        try:
            self.setup_driver()
            success = self.build_and_save_catalog(output_filename)
            return success
        finally:
            self.cleanup()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MyNetDiary食材カタログ構築")
    parser.add_argument("-o", "--output", help="出力ファイル名")
    parser.add_argument("--headless", action="store_true", help="ヘッドレスモードで実行")

    args = parser.parse_args()

    # ヘッドレスモード設定を一時的に上書き
    if args.headless:
        config.HEADLESS = True

    builder = FoodCatalogBuilder()
    success = builder.run_catalog_build(args.output)

    if success:
        print("\n✅ 食材カタログ構築が正常に完了しました！")
        exit(0)
    else:
        print("\n❌ 食材カタログ構築に失敗しました。")
        exit(1)