#!/usr/bin/env python3
"""
ChromeDriver安定性の迅速テスト（1食品のみ）
最終的な安定化ソリューションの動作確認用
"""

import sys
import time
import json
import os
import psutil
import subprocess
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.components.stable_multi_food_navigator import StableMultiFoodNavigator
from src.components.comprehensive_food_data_collector import ComprehensiveFoodDataCollector
from config import config


class QuickChromeStabilityTest:
    """ChromeDriver安定性の迅速テスト"""

    def __init__(self):
        self.test_result = None

    def get_stable_chrome_options(self):
        """Chrome 115+対応の安定化オプション（macOS最適化）"""
        chrome_options = Options()

        # Chrome 115+の新しいヘッドレスモード
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--remote-debugging-port=0")

        # macOS特有の安定化設定
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")

        # メモリ最適化
        chrome_options.add_argument("--max_old_space_size=4096")
        chrome_options.add_argument("--disable-dev-shm-usage")  # 注意：メモリリーク対策済み

        # プライベートモード
        chrome_options.add_argument("--incognito")

        # ログ抑制
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")

        # User-Agent設定
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

        # 一時ディレクトリ指定（クリーンアップ対象）
        temp_dir = f"/tmp/chrome_test_{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")

        return chrome_options, temp_dir

    def create_stable_driver_session(self):
        """安定化されたドライバーセッションを作成"""
        print("🚀 安定化Chromeドライバーセッション作成中...")

        # Chrome安定化オプション取得
        chrome_options, temp_profile = self.get_stable_chrome_options()

        try:
            # Selenium Manager使用（Chrome 115+対応）
            service = Service()  # パラメータなしでSelenium Managerを活用

            # WebDriverインスタンス作成
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.implicitly_wait(10)

            # WebDriverWait設定
            wait = WebDriverWait(driver, 30)

            # コンポーネント初期化（configパラメータを追加）
            navigator = StableMultiFoodNavigator(driver, wait)
            data_collector = ComprehensiveFoodDataCollector(driver, wait, config)

            print("✅ 安定化Chromeドライバーセッション作成完了")

            return driver, wait, navigator, data_collector, temp_profile

        except Exception as e:
            print(f"❌ ドライバーセッション作成エラー: {e}")
            raise

    def cleanup_session(self, driver, navigator, temp_profile):
        """セッションクリーンアップ"""
        print("🧹 セッションクリーンアップ開始...")

        try:
            if navigator:
                navigator.cleanup_session()
        except:
            pass

        try:
            if driver:
                driver.quit()
        except:
            pass

        # 一時ディレクトリクリーンアップ
        try:
            import shutil
            if os.path.exists(temp_profile):
                shutil.rmtree(temp_profile, ignore_errors=True)
                print(f"  🗑️ 一時プロファイル削除: {temp_profile}")
        except:
            pass

        print("✅ セッションクリーンアップ完了")

    def test_single_food_stability(self):
        """1つの食品で安定性をテスト"""
        print("🧪 Chrome安定性テスト開始（1食品）...")

        driver = None
        navigator = None
        temp_profile = None

        try:
            # セッション作成
            driver, wait, navigator, data_collector, temp_profile = self.create_stable_driver_session()

            # 食材カタログ読み込み
            print("📁 食材カタログ読み込み...")
            success = navigator.load_food_catalog()
            if not success:
                raise Exception("食材カタログ読み込み失敗")

            # 最初のカテゴリから1つの食品を選択
            first_category = list(navigator.food_catalog.keys())[0]
            first_food = navigator.food_catalog[first_category]['foods'][0]

            print(f"🎯 テスト対象食品: {first_food}")

            # 食品を選択してページに移動
            print("🔍 食品選択とページ移動中...")
            navigation_success = navigator.navigate_to_food_stable(first_food['food_name'])
            if not navigation_success:
                raise Exception("食品ページへの移動に失敗")

            # 食品データ収集
            start_time = time.time()

            food_result = data_collector.collect_complete_food_data(
                food_name=first_food['food_name']
            )

            collection_time = time.time() - start_time

            # 結果評価
            is_success = (
                food_result and
                food_result.get('collection_success', False) and
                food_result.get('nutrition_data') and
                food_result.get('serving_options')
            )

            self.test_result = {
                'food_name': first_food['food_name'],
                'category': first_category,
                'success': is_success,
                'collection_time': round(collection_time, 1),
                'nutrition_available': bool(food_result.get('nutrition_data')),
                'serving_available': bool(food_result.get('serving_options')),
                'nutrition_count': food_result.get('nutrition_data', {}).get('detailed_nutrients', {}).get('total_nutrients_found', 0) if food_result.get('nutrition_data') else 0,
                'serving_count': food_result.get('serving_options', {}).get('total_servings_found', 0) if food_result.get('serving_options') else 0,
                'completed_at': datetime.now().isoformat()
            }

            if is_success:
                print(f"✅ Chrome安定性テスト成功!")
                print(f"  📊 栄養データ: {self.test_result['nutrition_count']}件")
                print(f"  🥄 サービングデータ: {self.test_result['serving_count']}件")
                print(f"  ⏱️ 処理時間: {self.test_result['collection_time']}秒")
            else:
                print(f"❌ Chrome安定性テスト失敗")

        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            self.test_result = {
                'success': False,
                'error': str(e),
                'completed_at': datetime.now().isoformat()
            }

        finally:
            # クリーンアップ
            self.cleanup_session(driver, navigator, temp_profile)

        return self.test_result

    def save_results(self):
        """テスト結果を保存"""
        if self.test_result:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/chrome_stability_test_{timestamp}.json"

            os.makedirs("data", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_result, f, ensure_ascii=False, indent=2)

            print(f"💾 テスト結果保存: {filename}")


def main():
    """メイン実行"""
    print("🔬 ChromeDriver安定性クイックテスト開始")
    print("=" * 50)

    tester = QuickChromeStabilityTest()

    try:
        # テスト実行
        result = tester.test_single_food_stability()

        # 結果保存
        tester.save_results()

        # 結果表示
        print("\n📋 テスト結果サマリー:")
        print("=" * 30)
        if result['success']:
            print(f"✅ ステータス: 成功")
            print(f"🍽️ 食品: {result['food_name']}")
            print(f"📂 カテゴリ: {result['category']}")
            print(f"⏱️ 処理時間: {result['collection_time']}秒")
            print(f"📊 栄養データ: {result['nutrition_count']}件")
            print(f"🥄 サービングデータ: {result['serving_count']}件")
        else:
            print(f"❌ ステータス: 失敗")
            if 'error' in result:
                print(f"🚨 エラー: {result['error']}")

        print(f"🕐 完了時刻: {result['completed_at']}")

    except Exception as e:
        print(f"❌ テスト実行中にエラー: {e}")
        return 1

    return 0 if result['success'] else 1


if __name__ == "__main__":
    exit(main())