#!/usr/bin/env python3
"""
メインスクリプトのナビゲーション機能をテスト
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from config import config

class MainNavigationTester:
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

    def test_food_navigation_cycle(self):
        """食材ナビゲーションサイクルをテスト"""
        print("\n🧪 食材ナビゲーションサイクルテスト開始")

        results = []

        for i in range(3):
            print(f"\n{'='*40}")
            print(f"🎯 食材 {i+1} ナビゲーションテスト")
            print(f"{'='*40}")

            # 食材リストを取得
            food_list_items = self.driver.find_elements(
                By.XPATH,
                "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
            )

            print(f"利用可能な食材数: {len(food_list_items)}")

            if len(food_list_items) <= i:
                print(f"❌ 食材 {i+1} が見つかりません")
                results.append(False)
                break

            # 食材をクリック
            food_item = food_list_items[i]
            food_name = food_item.text
            print(f"🎯 食材クリック: {food_name[:50]}...")
            food_item.click()
            time.sleep(config.REQUEST_DELAY * 2)

            # 最後の食材でなければ戻る処理をテスト
            if i < 2:
                print("🔄 食材リストに戻る処理をテスト...")

                # 簡単な戻り方法：ブラウザバック
                self.driver.back()
                time.sleep(3)

                # 食材リストが再表示されているか確認
                new_food_list = self.driver.find_elements(
                    By.XPATH,
                    "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
                )

                if len(new_food_list) > 0:
                    print(f"✅ 戻り処理成功！食材リスト: {len(new_food_list)}個確認")
                    results.append(True)
                else:
                    print("❌ 戻り処理失敗：食材リストが空")
                    results.append(False)
                    break
            else:
                print("📝 最後の食材のため戻り処理スキップ")
                results.append(True)

        return results

    def run_test(self):
        """ナビゲーションテスト実行"""
        try:
            self.setup_driver()

            if not self.login_to_mynetdiary():
                print("❌ ログインに失敗しました")
                return

            if not self.navigate_to_category():
                print("❌ カテゴリナビゲーションに失敗")
                return

            results = self.test_food_navigation_cycle()

            # 結果サマリー
            print(f"\n{'='*60}")
            print("🏁 ナビゲーションテスト結果サマリー")
            print(f"{'='*60}")

            success_count = sum(results)
            for i, result in enumerate(results):
                status = "✅ 成功" if result else "❌ 失敗"
                print(f"食材 {i+1} ナビゲーション: {status}")

            print(f"\n成功率: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")

            if success_count == len(results):
                print("🎉 全てのナビゲーションが正常動作！")
            elif success_count > 0:
                print(f"⚠️ 一部ナビゲーションで問題")
            else:
                print("❌ 全てのナビゲーションで失敗")

        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    tester = MainNavigationTester()
    tester.run_test()