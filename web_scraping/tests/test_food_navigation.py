#!/usr/bin/env python3
"""
食材ナビゲーションテストスクリプト
保存済みカテゴリ情報を使用して任意の食材ページに遷移テスト
"""

import time
import json
import sys
import random
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import config
from src.components.raw_serving_extractor import RawServingExtractor
from src.components.modal_handler import ModalHandler


class FoodNavigationTester:
    """食材ナビゲーションテストクラス"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.raw_serving_extractor = None
        self.modal_handler = None
        self.food_catalog = {}
        self.test_results = []

    def setup_driver(self):
        """ChromeDriverを設定"""
        print("🚀 ChromeDriverを起動中...")
        chrome_options = Options()
        # ヘッドレスモードを無効化（テスト観察のため）
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)

        # コンポーネントを初期化
        self.raw_serving_extractor = RawServingExtractor(self.driver)
        self.modal_handler = ModalHandler(self.driver)

        print("✅ ChromeDriver起動完了")

    def load_food_catalog(self):
        """保存済み食材カタログを読み込み"""
        print("📁 保存済み食材カタログを読み込み中...")

        data_dir = Path("food_catalog_data")
        json_files = [f for f in data_dir.glob("*.json") if not f.name.startswith("collection_summary")]

        if not json_files:
            print("❌ 保存済みカタログデータが見つかりません")
            return False

        total_foods = 0
        for file in json_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                category_name = data['category_data']['name']
                foods = data['category_data']['foods']

                self.food_catalog[category_name] = {
                    "category_info": {
                        "name": category_name,
                        "xpath": data['category_data']['xpath']
                    },
                    "foods": foods
                }

                total_foods += len(foods)

            except Exception as e:
                print(f"⚠️ ファイル読み込みエラー: {file.name} - {e}")
                continue

        print(f"✅ カタログ読み込み完了:")
        print(f"   📂 カテゴリ数: {len(self.food_catalog)}個")
        print(f"   🍽️ 総食材数: {total_foods}個")

        return len(self.food_catalog) > 0

    def login_and_navigate_to_my_foods(self):
        """ログイン & My Foods画面に移動"""
        print("🔐 MyNetDiaryにログイン中...")

        try:
            # ログイン
            self.driver.get(config.LOGIN_URL)
            time.sleep(config.REQUEST_DELAY)

            username = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            password = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            username.send_keys(config.USERNAME)
            password.send_keys(config.PASSWORD)

            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='jss15']")
            login_btn.click()
            time.sleep(config.REQUEST_DELAY * 2)

            # My Foods画面に移動
            my_foods_url = f"{config.BASE_URL}/meals.do#ff"
            self.driver.get(my_foods_url)
            time.sleep(config.REQUEST_DELAY)

            # My Foods ボタンクリック
            my_foods_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
            )
            my_foods_btn.click()
            time.sleep(config.REQUEST_DELAY)

            # Staple Foodsをクリック
            staple_foods = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
            )
            staple_foods.click()
            time.sleep(config.REQUEST_DELAY)

            print("✅ ログイン & ナビゲーション完了")
            return True

        except Exception as e:
            print(f"❌ ログイン・ナビゲーションエラー: {e}")
            return False

    def navigate_to_food(self, category_name, food_info):
        """指定食材に直接ナビゲーション"""
        print(f"\n🎯 食材ナビゲーション: {food_info['food_name'][:50]}...")

        try:
            # 1. カテゴリに移動
            category_info = self.food_catalog[category_name]["category_info"]
            category_xpath = category_info["xpath"]

            print(f"📂 ステップ1: {category_name}カテゴリに移動")

            category_element = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, category_xpath))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", category_element)
            time.sleep(1)
            category_element.click()
            time.sleep(config.REQUEST_DELAY * 2)

            print(f"✅ {category_name}カテゴリに移動完了")

            # 2. ページに移動（必要に応じて）
            target_page = food_info["page_number"]
            current_page = 1

            if target_page > 1:
                print(f"📄 ステップ2: ページ{target_page}に移動")

                while current_page < target_page:
                    # 次のページボタンを探してクリック
                    next_buttons = self.driver.find_elements(
                        By.XPATH,
                        "//button[contains(@aria-label, 'next') or contains(text(), 'Next') or contains(@aria-label, 'Go to next page')]"
                    )

                    clicked = False
                    for button in next_buttons:
                        try:
                            if button.is_enabled() and button.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                                time.sleep(1)
                                button.click()
                                time.sleep(config.REQUEST_DELAY * 2)
                                clicked = True
                                break
                        except:
                            continue

                    if not clicked:
                        raise Exception(f"ページ{target_page}への移動失敗")

                    current_page += 1

                print(f"✅ ページ{target_page}に移動完了")

            # 3. 食材をクリック
            print(f"🥗 ステップ3: 食材をクリック（位置: {food_info['position_in_page']}）")

            food_xpath = food_info["xpath"]
            try:
                food_element = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, food_xpath))
                )
            except:
                # XPathが見つからない場合、位置ベースで再試行
                alternative_xpath = f"//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')][{food_info['position_in_page']}]"
                food_element = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, alternative_xpath))
                )

            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", food_element)
            time.sleep(1)
            food_element.click()
            time.sleep(config.REQUEST_DELAY * 2)

            print(f"✅ 食材クリック完了")

            return True

        except Exception as e:
            print(f"❌ 食材ナビゲーションエラー: {e}")
            return False

    def test_serving_extraction(self, food_info):
        """serving情報抽出テスト"""
        print(f"📊 serving情報抽出テスト")

        try:
            # Select Servingモーダルを開く
            modal_opened = self.modal_handler.open_serving_modal()
            if not modal_opened:
                print("❌ Select Servingモーダルが開けませんでした")
                return []

            print("✅ Select Servingモーダル開放成功")

            # serving情報を抽出
            serving_options = self.raw_serving_extractor.extract_raw_serving_options()

            # モーダルを閉じる
            self.modal_handler.close_modal()

            if serving_options:
                print(f"✅ serving情報抽出成功: {len(serving_options)}個のオプション")
                for i, option in enumerate(serving_options, 1):
                    print(f"  {i}. {option['raw_text']}")
            else:
                print("❌ serving情報抽出失敗")

            return serving_options

        except Exception as e:
            print(f"❌ serving情報抽出エラー: {e}")
            return []

    def test_food_navigation_complete(self, category_name, food_info):
        """完全な食材ナビゲーションテスト"""
        test_name = f"{category_name}_{food_info['position_in_page']}"
        print(f"\n{'='*80}")
        print(f"🧪 完全ナビゲーションテスト: {test_name}")
        print(f"{'='*80}")

        start_time = datetime.now()

        try:
            # 1. 食材に移動
            nav_success = self.navigate_to_food(category_name, food_info)

            if not nav_success:
                raise Exception("食材ナビゲーション失敗")

            # 2. serving情報抽出
            serving_options = self.test_serving_extraction(food_info)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 結果記録
            result = {
                "test_name": test_name,
                "category": category_name,
                "food_name": food_info["food_name"],
                "navigation_success": nav_success,
                "serving_extraction_success": len(serving_options) > 0,
                "serving_options_count": len(serving_options),
                "serving_options": serving_options,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }

            success = nav_success and len(serving_options) > 0

            if success:
                print(f"✅ 完全テスト成功: {duration:.2f}秒")
            else:
                print(f"❌ 完全テスト失敗")

            self.test_results.append(result)
            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "test_name": test_name,
                "category": category_name,
                "food_name": food_info.get("food_name", "unknown"),
                "navigation_success": False,
                "serving_extraction_success": False,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }

            print(f"❌ 完全テストエラー: {e}")
            self.test_results.append(result)
            return result

    def select_random_foods(self, count=5):
        """ランダムな食材を選択"""
        all_foods = []

        for category_name, category_data in self.food_catalog.items():
            for food in category_data["foods"]:
                all_foods.append((category_name, food))

        if len(all_foods) < count:
            count = len(all_foods)

        selected = random.sample(all_foods, count)
        return selected

    def run_navigation_tests(self, test_count=3):
        """ナビゲーションテストを実行"""
        try:
            print("🧪 食材ナビゲーションテスト開始")
            print("="*80)

            self.setup_driver()

            # カタログ読み込み
            if not self.load_food_catalog():
                return False

            # ログイン
            if not self.login_and_navigate_to_my_foods():
                return False

            # テスト対象食材を選択
            selected_foods = self.select_random_foods(test_count)

            print(f"\n🎯 テスト対象食材 ({len(selected_foods)}個):")
            for i, (category, food) in enumerate(selected_foods, 1):
                print(f"  {i}. {food['food_name'][:50]}... ({category})")

            # 各食材をテスト
            for i, (category_name, food_info) in enumerate(selected_foods, 1):
                print(f"\n🔄 テスト {i}/{len(selected_foods)}")

                # 完全ナビゲーションテスト
                result = self.test_food_navigation_complete(category_name, food_info)

                # Staple Foodsに戻る（次のテストのため）
                if i < len(selected_foods):
                    print("🔄 Staple Foodsに戻る...")
                    try:
                        staple_foods = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
                        )
                        staple_foods.click()
                        time.sleep(config.REQUEST_DELAY)
                    except:
                        print("⚠️ Staple Foods復帰に失敗（継続）")

                time.sleep(2)  # テスト間の待機

            # 結果サマリー
            self.print_test_summary()

            # 結果保存
            summary_file = self.save_test_results()

            return True

        except Exception as e:
            print(f"❌ ナビゲーションテストエラー: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()

    def print_test_summary(self):
        """テスト結果サマリーを表示"""
        successful_nav = [r for r in self.test_results if r.get("navigation_success")]
        successful_serving = [r for r in self.test_results if r.get("serving_extraction_success")]
        fully_successful = [r for r in self.test_results if r.get("navigation_success") and r.get("serving_extraction_success")]

        print(f"\n{'='*80}")
        print("🏁 ナビゲーションテスト結果サマリー")
        print(f"{'='*80}")
        print(f"📊 総テスト数: {len(self.test_results)}個")
        print(f"🧭 ナビゲーション成功: {len(successful_nav)}/{len(self.test_results)}")
        print(f"📋 serving抽出成功: {len(successful_serving)}/{len(self.test_results)}")
        print(f"✅ 完全成功: {len(fully_successful)}/{len(self.test_results)}")

        if fully_successful:
            avg_duration = sum(r["duration_seconds"] for r in fully_successful) / len(fully_successful)
            print(f"⏱️ 平均所要時間: {avg_duration:.2f}秒")

        print(f"\n📋 個別結果:")
        for result in self.test_results:
            status = "✅" if result.get("navigation_success") and result.get("serving_extraction_success") else "❌"
            food_name = result["food_name"][:30]
            category = result["category"]
            duration = result.get("duration_seconds", 0)
            print(f"  {status} {food_name}... ({category}) - {duration:.2f}s")

    def save_test_results(self):
        """テスト結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"food_catalog_data/navigation_test_results_{timestamp}.json"

        test_data = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "method": "food_navigation_test",
                "total_tests": len(self.test_results),
                "successful_navigation": sum(1 for r in self.test_results if r.get("navigation_success")),
                "successful_serving_extraction": sum(1 for r in self.test_results if r.get("serving_extraction_success")),
                "fully_successful": sum(1 for r in self.test_results if r.get("navigation_success") and r.get("serving_extraction_success"))
            },
            "test_results": self.test_results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 テスト結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="食材ナビゲーションテスト")
    parser.add_argument("-n", "--count", type=int, default=3,
                       help="テストする食材数")

    args = parser.parse_args()

    tester = FoodNavigationTester()
    success = tester.run_navigation_tests(args.count)

    if success:
        print(f"\n🎉 食材ナビゲーションテストが完了しました！")
    else:
        print(f"\n💥 食材ナビゲーションテストに失敗しました。")


if __name__ == "__main__":
    main()