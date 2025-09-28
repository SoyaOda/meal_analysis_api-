#!/usr/bin/env python3
"""
改善されたAmount eaten機能をテスト
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from config import config

class ImprovedAmountEatenTester:
    def __init__(self):
        self.driver = None
        self.wait = None

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

    def login_to_mynetdiary(self):
        """MyNetDiaryにログイン"""
        print("🔐 MyNetDiaryにログイン中...")
        self.driver.get(config.LOGIN_URL)
        time.sleep(config.REQUEST_DELAY)

        username_element = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
        password_element = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")

        username_element.send_keys(config.USERNAME)
        password_element.send_keys(config.PASSWORD)

        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[class*='jss15']")
        login_button.click()
        time.sleep(config.REQUEST_DELAY * 2)

        current_url = self.driver.current_url
        if "login" not in current_url.lower() and "logon" not in current_url.lower():
            print("✅ ログイン成功！")
            return True
        else:
            print("❌ ログイン失敗")
            return False

    def navigate_to_category(self):
        """カテゴリページに移動"""
        print("🔍 カテゴリナビゲーション...")

        # My Foodsページに移動
        my_foods_url = f"{config.BASE_URL}/meals.do#ff"
        self.driver.get(my_foods_url)
        time.sleep(config.REQUEST_DELAY)

        # My Foodsボタンをクリック
        my_foods_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
        )
        my_foods_button.click()
        time.sleep(config.REQUEST_DELAY)

        # Staple Foodsメニューアイテムをクリック
        staple_foods_item = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
        )
        staple_foods_item.click()
        time.sleep(config.REQUEST_DELAY)

        # Dairy, Dairy Substitutes & Eggカテゴリをクリック
        category_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Dairy, Dairy Substitutes & Egg']"))
        )
        category_button.click()
        time.sleep(config.REQUEST_DELAY)

        return True

    def test_food_by_index(self, food_index):
        """指定インデックスの食材でAmount eaten機能をテスト"""
        print(f"\n{'='*60}")
        print(f"🧪 食材 {food_index + 1} のAmount eaten改善版テスト")
        print(f"{'='*60}")

        try:
            # 食材リストを取得
            food_list_items = self.driver.find_elements(
                By.XPATH,
                "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
            )

            if len(food_list_items) <= food_index:
                print(f"❌ 食材 {food_index + 1} が見つかりません")
                return False

            food_item = food_list_items[food_index]
            food_name = food_item.text
            print(f"🎯 食材 {food_index + 1}: {food_name[:50]}...")

            # 食材をクリック
            food_item.click()
            time.sleep(config.REQUEST_DELAY * 2)

            # 栄養素を展開
            self.expand_nutrients()

            # 改善されたAmount eaten機能をテスト
            result = self.test_improved_amount_eaten()

            return result

        except Exception as e:
            print(f"❌ 食材 {food_index + 1} テストエラー: {e}")
            return False

    def expand_nutrients(self):
        """栄養素を展開"""
        try:
            for letter in ['F', 'C', 'P']:
                try:
                    element = self.driver.find_element(By.XPATH, f"//div[text()='{letter}']")
                    element.click()
                    time.sleep(1)
                    print(f"  📍 {letter} 要素をクリックしました")
                except:
                    print(f"  ⚠️ {letter} 要素が見つかりません")
        except:
            pass

    def test_improved_amount_eaten(self):
        """改善されたAmount eaten機能をテスト"""
        try:
            print("    🔍 Amount eaten エリア構造分析...")

            # Amount eaten 要素を検索
            amount_eaten_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Amount eaten')]")

            if not amount_eaten_elements:
                print("    ❌ Amount eaten 要素が見つかりません")
                return False

            print(f"    📋 Amount eaten 要素数: {len(amount_eaten_elements)}")

            # 表示されているAmount eaten要素を取得
            amount_element = None
            for element in amount_eaten_elements:
                if element.is_displayed():
                    amount_element = element
                    break

            if not amount_element:
                print("    ❌ 表示されているAmount eaten 要素が見つかりません")
                return False

            print(f"    ✅ Amount eaten 要素発見: {amount_element.tag_name}")

            # 親レベル2（テストで成功したエリア）を取得
            try:
                parent_level2 = amount_element.find_element(By.XPATH, "../..")
                size = parent_level2.size
                text = parent_level2.text

                print(f"    🔍 親レベル2: サイズ{size}, テキスト: '{text[:50]}...'")

                # テストで成功した条件をチェック（幅400px以上）
                if (size['width'] >= 400 and size['height'] > 50 and
                    "amount eaten" in text.lower()):

                    print(f"    🎯 クリック可能エリア特定（親レベル2）")

                    # 既存のモーダルを閉じる
                    self._close_any_open_modals()
                    time.sleep(1)

                    # 複数のクリック方法を試行（改善版）
                    click_methods = [
                        ("通常クリック", lambda: parent_level2.click()),
                        ("JavaScriptクリック", lambda: self.driver.execute_script("arguments[0].click();", parent_level2)),
                        ("ActionChainsクリック", lambda: self._action_chains_click(parent_level2))
                    ]

                    for method_name, click_func in click_methods:
                        try:
                            print(f"    🔄 {method_name}でSelect Servingモーダルを開く...")

                            # スクロールして表示
                            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_level2)
                            time.sleep(1)

                            # クリック実行
                            click_func()
                            time.sleep(3)

                            # Select Serving モーダルが開いたかチェック
                            if self._is_select_serving_modal_open():
                                print(f"    ✅ {method_name}でSelect Serving モーダルが開きました！")
                                self._close_select_serving_modal()
                                return True
                            else:
                                print(f"    ❌ {method_name}: Select Serving モーダルが開きませんでした")

                        except Exception as e:
                            print(f"    ❌ {method_name}エラー: {e}")
                            continue

                    return False
                else:
                    print("    ❌ 適切なクリック可能エリアが見つかりません")
                    return False

            except Exception as e:
                print(f"    ⚠️ 親レベル2チェックエラー: {e}")
                return False

        except Exception as e:
            print(f"    ❌ Amount eaten テストエラー: {e}")
            return False

    def _action_chains_click(self, element):
        """ActionChainsを使用したクリック"""
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click().perform()

    def _close_any_open_modals(self):
        """開いているモーダルがあれば閉じる"""
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass

    def _is_select_serving_modal_open(self):
        """Select Serving モーダルが開いているかチェック（簡素化版）"""
        try:
            # テストで検証済みの簡単なパターン
            modal_indicators = [
                "//*[contains(text(), 'Select Serving')]",
                "//*[contains(text(), 'oz') and contains(text(), 'cals')]",
                "//*[contains(text(), 'container') and contains(text(), 'cals')]"
            ]

            for pattern in modal_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            print(f"        ✅ Select Serving モーダル確認: '{element.text[:30]}...'")
                            return True
                except:
                    continue

            return False

        except Exception as e:
            print(f"        ⚠️ モーダル確認エラー: {e}")
            return False

    def _close_select_serving_modal(self):
        """Select Serving モーダルを閉じる"""
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass

    def run_test(self):
        """改善版テスト実行"""
        try:
            self.setup_driver()

            if not self.login_to_mynetdiary():
                print("❌ ログインに失敗しました")
                return

            if not self.navigate_to_category():
                print("❌ カテゴリナビゲーションに失敗")
                return

            # 3つの食材をテスト
            results = []
            for i in range(3):
                result = self.test_food_by_index(i)
                results.append(result)

                # 次の食材のためにカテゴリに戻る（最後の食材以外）
                if i < 2:
                    self.driver.back()
                    time.sleep(3)

            # 結果サマリー
            print(f"\n{'='*60}")
            print("🏁 改善版Amount eaten機能テスト結果")
            print(f"{'='*60}")

            success_count = sum(results)
            for i, result in enumerate(results):
                status = "✅ 成功" if result else "❌ 失敗"
                print(f"食材 {i+1}: {status}")

            print(f"\n成功率: {success_count}/3 ({success_count/3*100:.1f}%)")

            if success_count == 3:
                print("🎉 全ての食材でAmount eaten機能が正常動作！")
            elif success_count > 0:
                print(f"⚠️ 一部の食材で動作。改善効果確認")
            else:
                print("❌ 全ての食材で失敗")

        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    tester = ImprovedAmountEatenTester()
    tester.run_test()