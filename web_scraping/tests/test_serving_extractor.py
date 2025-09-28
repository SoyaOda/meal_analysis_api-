#!/usr/bin/env python3
"""
ServingExtractor コンポーネントのテストスクリプト
実際のMyNetDiaryページでserving情報抽出をテスト
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
from src.components.raw_serving_extractor import RawServingExtractor
from src.components.modal_handler import ModalHandler
from src.components.navigation_manager import NavigationManager
from src.models.serving_data import ExtractionResult, FoodData
from config import config


class RawServingExtractorTester:
    """RawServingExtractorコンポーネントのテストクラス"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.raw_serving_extractor = None
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

        # コンポーネントを初期化
        self.raw_serving_extractor = RawServingExtractor(self.driver)
        self.modal_handler = ModalHandler(self.driver)
        self.navigation_manager = NavigationManager(self.driver, self.wait, config)

    def login_and_navigate(self):
        """ログイン & カテゴリナビゲーション"""
        return self.navigation_manager.login_and_navigate_to_category("Dairy, Dairy Substitutes & Egg")

    def test_single_food_serving_extraction(self, food_index: int = 0):
        """
        単一食材のserving情報抽出をテスト

        Args:
            food_index: テストする食材のインデックス
        """
        test_name = f"food_{food_index + 1}_serving_extraction"
        print(f"\n{'='*60}")
        print(f"🧪 テスト開始: {test_name}")
        print(f"{'='*60}")

        try:
            # NavigationManagerから食材リストを取得
            food_list_items = self.navigation_manager.get_food_list_items()
            print(f"🔍 発見された食材数: {len(food_list_items)}個")

            if len(food_list_items) <= food_index:
                raise Exception(f"食材 {food_index + 1} が見つかりません（利用可能: {len(food_list_items)}個）")

            food_item = food_list_items[food_index]
            food_name = food_item.text.strip()
            print(f"🎯 テスト食材: {food_name[:50]}...")

            # 食材をクリック
            food_item.click()
            time.sleep(config.REQUEST_DELAY * 2)

            # モーダルを開く
            modal_opened = self.modal_handler.open_serving_modal()
            if not modal_opened:
                raise Exception("Select Servingモーダルが開けませんでした")

            # 生serving情報を抽出
            raw_serving_options = self.raw_serving_extractor.extract_raw_serving_options()

            # 結果を検証
            test_result = {
                "test_name": test_name,
                "food_name": food_name,
                "success": len(raw_serving_options) > 0,
                "serving_options_count": len(raw_serving_options),
                "raw_serving_options": raw_serving_options,
                "timestamp": datetime.now().isoformat()
            }

            if raw_serving_options:
                print(f"✅ テスト成功: {len(raw_serving_options)}個の生serving options抽出")
                for i, option in enumerate(raw_serving_options, 1):
                    print(f"  {i}. {option['raw_text']} (radio: {option['radio_value']})")
            else:
                print("❌ テスト失敗: serving options抽出できませんでした")

            # モーダルを閉じる
            self.modal_handler.close_modal()

            self.test_results.append(test_result)
            return test_result

        except Exception as e:
            print(f"❌ テストエラー: {e}")
            test_result = {
                "test_name": test_name,
                "food_name": "不明",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.test_results.append(test_result)
            return test_result

    def test_multiple_foods(self, food_count: int = 3):
        """複数食材のserving情報抽出をテスト"""
        print(f"\n🔄 複数食材テスト開始 (最大{food_count}個)")

        for i in range(food_count):
            # 各食材をテスト
            test_result = self.test_single_food_serving_extraction(i)

            # 成功した場合、次の食材のために戻る（最後の食材以外）
            if test_result.get("success") and i < food_count - 1:
                print(f"🔄 食材リストに戻る...")
                success = self.navigation_manager.return_to_food_list("Dairy, Dairy Substitutes & Egg")
                if not success:
                    print(f"❌ 食材リストに戻れませんでした。テスト中断")
                    break


    def test_modal_state_detection(self):
        """モーダル状態検出機能をテスト"""
        print(f"\n{'='*60}")
        print("🧪 モーダル状態検出テスト")
        print(f"{'='*60}")

        try:
            # 最初はモーダルが閉じているはず
            is_open_before = self.raw_serving_extractor.is_serving_modal_open()
            print(f"🔍 モーダル開く前: {is_open_before}")

            # NavigationManagerから食材を取得してモーダルを開く
            food_list_items = self.navigation_manager.get_food_list_items()

            if food_list_items:
                food_list_items[0].click()
                time.sleep(2)

                # モーダルを開く
                modal_opened = self.modal_handler.open_serving_modal()
                is_open_after = self.raw_serving_extractor.is_serving_modal_open()
                print(f"🔍 モーダル開いた後: {is_open_after}")

                # モーダルを閉じる
                self.modal_handler.close_modal()
                time.sleep(1)
                is_open_closed = self.raw_serving_extractor.is_serving_modal_open()
                print(f"🔍 モーダル閉じた後: {is_open_closed}")

                # *** 重要: テスト後は食材リストに戻る ***
                print("🔄 モーダルテスト完了後、食材リストに戻る...")
                self.navigation_manager.return_to_food_list("Dairy, Dairy Substitutes & Egg")

                test_result = {
                    "test_name": "modal_state_detection",
                    "success": is_open_before == False and is_open_after == True,
                    "states": {
                        "before_open": is_open_before,
                        "after_open": is_open_after,
                        "after_close": is_open_closed
                    },
                    "timestamp": datetime.now().isoformat()
                }

                if test_result["success"]:
                    print("✅ モーダル状態検出テスト成功")
                else:
                    print("❌ モーダル状態検出テスト失敗")

                self.test_results.append(test_result)
                return test_result

        except Exception as e:
            print(f"❌ モーダル状態検出テストエラー: {e}")
            return {"test_name": "modal_state_detection", "success": False, "error": str(e)}

    def save_test_results(self):
        """テスト結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # test_resultsフォルダに保存
        results_dir = "test_results"
        filename = f"{results_dir}/raw_serving_extractor_test_results_{timestamp}.json"

        test_summary = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "successful_tests": sum(1 for r in self.test_results if r.get("success")),
                "failed_tests": sum(1 for r in self.test_results if not r.get("success")),
                "total_raw_serving_options": sum(r.get("serving_options_count", 0) for r in self.test_results)
            },
            "test_results": self.test_results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_summary, f, ensure_ascii=False, indent=2)

        print(f"📄 テスト結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def run_all_tests(self):
        """全テストを実行"""
        try:
            print("🧪 RawServingExtractor コンポーネントテスト開始")
            print("="*60)

            self.setup_driver()

            if not self.login_and_navigate():
                print("❌ ログイン・ナビゲーション失敗")
                return False

            # 各テストを実行
            self.test_modal_state_detection()
            self.test_multiple_foods(3)

            # 結果サマリー
            print(f"\n{'='*60}")
            print("🏁 テスト完了")
            print(f"{'='*60}")

            successful_tests = sum(1 for r in self.test_results if r.get("success"))
            total_tests = len(self.test_results)
            total_options = sum(r.get("serving_options_count", 0) for r in self.test_results)

            print(f"📊 テスト結果: {successful_tests}/{total_tests} 成功")
            print(f"📈 総生serving options数: {total_options}個")

            # 結果保存
            filename = self.save_test_results()
            print(f"✅ 全てのテストが完了しました: {filename}")

            return True

        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


if __name__ == "__main__":
    tester = RawServingExtractorTester()
    tester.run_all_tests()