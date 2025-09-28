#!/usr/bin/env python3
"""
ナビゲーション管理コンポーネント
MyNetDiaryサイト内の遷移処理を管理
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Optional


class NavigationManager:
    """MyNetDiaryサイト内のナビゲーションを管理するコンポーネント"""

    def __init__(self, driver, wait: Optional[WebDriverWait] = None, config=None):
        """
        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
            config: 設定オブジェクト
        """
        self.driver = driver
        self.wait = wait or WebDriverWait(driver, 10)
        self.config = config

    def login_and_navigate_to_category(self, category_name: str = "Dairy, Dairy Substitutes & Egg") -> bool:
        """
        ログインして指定カテゴリまでナビゲーション

        Args:
            category_name: 移動先カテゴリ名

        Returns:
            bool: ナビゲーション成功かどうか
        """
        try:
            print("🔐 MyNetDiaryにログイン...")

            # ログインページに移動
            self.driver.get(self.config.LOGIN_URL)
            time.sleep(self.config.REQUEST_DELAY)

            # ログイン処理
            username = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            password = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            username.send_keys(self.config.USERNAME)
            password.send_keys(self.config.PASSWORD)

            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='jss15']")
            login_btn.click()
            time.sleep(self.config.REQUEST_DELAY * 2)

            # カテゴリナビゲーション
            my_foods_url = f"{self.config.BASE_URL}/meals.do#ff"
            self.driver.get(my_foods_url)
            time.sleep(self.config.REQUEST_DELAY)

            # My Foods ボタンクリック
            my_foods_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
            )
            my_foods_btn.click()
            time.sleep(self.config.REQUEST_DELAY)

            # Staple Foods クリック
            staple_foods = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
            )
            staple_foods.click()
            time.sleep(self.config.REQUEST_DELAY)

            # 指定カテゴリクリック
            category = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//span[text()='{category_name}']"))
            )
            category.click()
            time.sleep(self.config.REQUEST_DELAY)

            print("✅ ログイン & ナビゲーション完了")
            return True

        except Exception as e:
            print(f"❌ ログイン・ナビゲーションエラー: {e}")
            return False

    def return_to_food_list(self, category_name: str = "Dairy, Dairy Substitutes & Egg") -> bool:
        """
        食材リストに戻る処理（複数の方法を試行）

        Args:
            category_name: 戻り先カテゴリ名

        Returns:
            bool: 戻り処理成功かどうか
        """
        print("🔄 食材リストに戻る...")

        # 複数の戻り方法を試行
        return_methods = [
            lambda: self._method_browser_back(category_name),
            lambda: self._method_fresh_navigation(category_name),
            lambda: self._method_category_reclick(category_name)
        ]

        for i, method in enumerate(return_methods, 1):
            try:
                print(f"    🔄 方法{i}を試行中...")
                method()

                # 成功の確認：食材リストが表示されているか
                if self.verify_food_list_visible():
                    print(f"    ✅ 方法{i}で戻り処理成功")
                    return True

            except Exception as e:
                print(f"    ❌ 方法{i}失敗: {e}")
                continue

        print("    ❌ 全ての戻り方法が失敗しました")
        return False

    def _method_browser_back(self, category_name: str):
        """方法1: ブラウザの戻るボタン"""
        self.driver.back()
        time.sleep(3)

        # 必要であればカテゴリを再クリック
        try:
            category_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//span[text()='{category_name}']"))
            )
            category_button.click()
            time.sleep(self.config.REQUEST_DELAY)
        except:
            pass

    def _method_fresh_navigation(self, category_name: str):
        """方法2: フレッシュナビゲーション"""
        my_foods_url = f"{self.config.BASE_URL}/meals.do#ff"
        self.driver.get(my_foods_url)
        time.sleep(self.config.REQUEST_DELAY)

        # カテゴリまで再ナビゲーション
        try:
            my_foods_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
            )
            my_foods_btn.click()
            time.sleep(self.config.REQUEST_DELAY)

            staple_foods = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
            )
            staple_foods.click()
            time.sleep(self.config.REQUEST_DELAY)

            category = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//span[text()='{category_name}']"))
            )
            category.click()
            time.sleep(self.config.REQUEST_DELAY)
        except Exception as e:
            print(f"        ⚠️ フレッシュナビゲーション失敗: {e}")

    def _method_category_reclick(self, category_name: str):
        """方法3: カテゴリ再クリック"""
        try:
            category_button = self.driver.find_element(By.XPATH, f"//span[text()='{category_name}']")
            category_button.click()
            time.sleep(self.config.REQUEST_DELAY)
        except Exception as e:
            print(f"        ⚠️ カテゴリ再クリック失敗: {e}")

    def verify_food_list_visible(self, min_foods: int = 3) -> bool:
        """
        食材リストが表示されているかを確認

        Args:
            min_foods: 最低限必要な食材数

        Returns:
            bool: 食材リストが正常に表示されているか
        """
        try:
            # 食材リスト要素の存在を確認
            food_elements = self.driver.find_elements(
                By.XPATH,
                "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
            )
            visible_foods = [el for el in food_elements if el.is_displayed()]

            if len(visible_foods) >= min_foods:
                print(f"    📊 食材リスト確認: {len(visible_foods)}個の食材が表示されています")
                return True
            else:
                print(f"    ⚠️ 食材リスト不十分: {len(visible_foods)}個のみ表示（最低{min_foods}個必要）")
                return False

        except Exception as e:
            print(f"    ❌ 食材リスト確認エラー: {e}")
            return False

    def get_food_list_items(self):
        """
        現在の食材リストアイテムを取得

        Returns:
            list: 食材要素のリスト
        """
        return self.driver.find_elements(
            By.XPATH,
            "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
        )