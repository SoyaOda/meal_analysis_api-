#!/usr/bin/env python3
"""
Select Servingモーダルの内容を詳細調査するデバッグスクリプト
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from config import config

class ModalContentDebugger:
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
        """2番目の食材に移動してAmount eatenをクリック"""
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

    def open_amount_eaten_modal(self):
        """Amount eatenモーダルを開く"""
        try:
            print("🔍 Amount eaten エリア構造分析...")

            # Amount eaten 要素を検索
            amount_eaten_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Amount eaten')]")

            if not amount_eaten_elements:
                print("❌ Amount eaten 要素が見つかりません")
                return False

            # 表示されているAmount eaten要素を取得
            amount_element = None
            for element in amount_eaten_elements:
                if element.is_displayed():
                    amount_element = element
                    break

            if not amount_element:
                print("❌ 表示されているAmount eaten 要素が見つかりません")
                return False

            # 親レベル2を取得してクリック
            parent_level2 = amount_element.find_element(By.XPATH, "../..")
            parent_level2.click()
            time.sleep(3)

            return True

        except Exception as e:
            print(f"❌ Amount eatenモーダル開けませんでした: {e}")
            return False

    def debug_modal_content(self):
        """モーダルの詳細内容を調査"""
        try:
            print("\n🔍 モーダル内容の詳細調査開始...")

            # 1. 全体のHTMLを取得
            print("\n1️⃣ ページ全体のタイトル確認:")
            print(f"   ページタイトル: '{self.driver.title}'")

            # 2. Select Servingというテキストを含む要素を検索
            print("\n2️⃣ 'Select Serving'を含む要素:")
            select_serving_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Select Serving')]")
            for i, element in enumerate(select_serving_elements):
                if element.is_displayed():
                    print(f"   要素{i+1}: '{element.text}' (タグ: {element.tag_name})")

            # 3. モーダル/ダイアログ要素を検索
            print("\n3️⃣ モーダル/ダイアログ構造:")
            modal_selectors = [
                "//div[contains(@class, 'MuiDialog')]",
                "//div[contains(@role, 'dialog')]",
                "//div[contains(@class, 'modal')]",
                "//div[contains(@class, 'popup')]"
            ]

            for selector in modal_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for i, element in enumerate(elements):
                    if element.is_displayed():
                        print(f"   {selector}: 要素{i+1} - '{element.text[:100]}...'")

            # 4. カロリーを含む全ての要素を検索
            print("\n4️⃣ カロリー関連要素:")
            calorie_patterns = [
                "//*[contains(text(), 'cal')]",
                "//*[contains(text(), 'Cal')]",
                "//*[contains(text(), 'cals')]",
                "//*[contains(text(), 'Cals')]"
            ]

            for pattern in calorie_patterns:
                elements = self.driver.find_elements(By.XPATH, pattern)
                print(f"   {pattern}: {len(elements)}個の要素")
                for i, element in enumerate(elements[:5]):  # 最初の5個のみ表示
                    if element.is_displayed():
                        print(f"     要素{i+1}: '{element.text}' (タグ: {element.tag_name})")

            # 5. 単位を含む可能性がある要素を検索
            print("\n5️⃣ 単位関連要素:")
            unit_patterns = [
                "//*[contains(text(), 'cup')]",
                "//*[contains(text(), 'oz')]",
                "//*[contains(text(), 'ml')]",
                "//*[contains(text(), 'gram')]",
                "//*[contains(text(), 'tablespoon')]",
                "//*[contains(text(), 'teaspoon')]",
                "//*[contains(text(), 'lb')]"
            ]

            for pattern in unit_patterns:
                elements = self.driver.find_elements(By.XPATH, pattern)
                if elements:
                    print(f"   {pattern}: {len(elements)}個の要素")
                    for i, element in enumerate(elements[:3]):  # 最初の3個のみ表示
                        if element.is_displayed():
                            print(f"     要素{i+1}: '{element.text}' (タグ: {element.tag_name})")

            # 6. スラッシュ(/)を含む要素を検索
            print("\n6️⃣ スラッシュ(/)を含む要素:")
            slash_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '/')]")
            for i, element in enumerate(slash_elements[:10]):  # 最初の10個のみ表示
                if element.is_displayed():
                    print(f"   要素{i+1}: '{element.text}' (タグ: {element.tag_name})")

            print("\n🎯 調査完了！")

        except Exception as e:
            print(f"❌ モーダル内容調査エラー: {e}")

    def run_debug(self):
        """デバッグ実行"""
        try:
            self.setup_driver()

            if not self.login_to_mynetdiary():
                print("❌ ログインに失敗しました")
                return

            if not self.navigate_to_2nd_food():
                print("❌ ナビゲーションに失敗")
                return

            if self.open_amount_eaten_modal():
                self.debug_modal_content()
            else:
                print("❌ Amount eatenモーダルを開けませんでした")

        except Exception as e:
            print(f"❌ デバッグ実行エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                input("Enter押下でブラウザを閉じます...")  # 手動確認用
                self.driver.quit()

if __name__ == "__main__":
    debugger = ModalContentDebugger()
    debugger.run_debug()