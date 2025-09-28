#!/usr/bin/env python3
"""
簡素化されたAmount eaten機能テスト
修正されたロジックの動作確認用
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

class SimplifiedAmountEatenTester:
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

    def navigate_to_2nd_food(self):
        """2番目の食材に移動"""
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

        # 2番目の食材をクリック
        food_list_items = self.driver.find_elements(
            By.XPATH,
            "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
        )

        if len(food_list_items) >= 2:
            second_food = food_list_items[1]
            food_name = second_food.text
            print(f"🎯 2番目の食材を選択: {food_name[:50]}...")
            second_food.click()
            time.sleep(config.REQUEST_DELAY * 2)
            return True
        else:
            print("❌ 2番目の食材が見つかりません")
            return False

    def test_simplified_amount_eaten(self):
        """簡素化されたAmount eaten機能をテスト（修正版ロジック）"""
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

            # 修正版ロジック: 親レベル2を直接使用
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

                    # 修正版: まず通常クリックのみ試行
                    print("    🔄 通常クリックでSelect Servingモーダルを開く...")

                    # スクロールして表示
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_level2)
                    time.sleep(1)

                    # 通常クリック実行
                    parent_level2.click()
                    time.sleep(3)

                    # Select Serving モーダルが開いたかチェック
                    if self._is_select_serving_modal_open():
                        print("    ✅ 通常クリックでSelect Serving モーダルが開きました！")
                        print("    🎉 修正版Amount eaten機能成功！")
                        self._close_select_serving_modal()
                        return True
                    else:
                        print("    ❌ 通常クリック: Select Serving モーダルが開きませんでした")
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
        """簡素化テスト実行"""
        try:
            self.setup_driver()

            if not self.login_to_mynetdiary():
                print("❌ ログインに失敗しました")
                return

            if self.navigate_to_2nd_food():
                result = self.test_simplified_amount_eaten()
                if result:
                    print("🎉 簡素化テスト成功！修正されたAmount eaten機能が動作しています")
                else:
                    print("❌ 簡素化テスト失敗")
            else:
                print("❌ ナビゲーションに失敗")

        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    tester = SimplifiedAmountEatenTester()
    tester.run_test()