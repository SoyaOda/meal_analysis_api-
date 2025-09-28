#!/usr/bin/env python3
"""
モーダル操作コンポーネント
Select Servingモーダルの開閉処理を管理
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from typing import Optional


class ModalHandler:
    """Select Servingモーダルの開閉を管理するコンポーネント"""

    def __init__(self, driver):
        """
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver

    def open_serving_modal(self, timeout: int = 10) -> bool:
        """
        Amount eaten要素をクリックしてSelect Servingモーダルを開く

        Args:
            timeout: タイムアウト秒数

        Returns:
            bool: モーダルが開けたかどうか
        """
        try:
            print("    🔄 Select Servingモーダルを開く...")

            # Amount eaten要素を検索してクリック
            amount_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Amount eaten')]")

            for element in amount_elements:
                if element.is_displayed():
                    # 親要素レベル2を取得（クリック可能エリア）
                    parent_level2 = element.find_element(By.XPATH, "../..")

                    # 既存モーダルを閉じる
                    self._close_any_open_modal()

                    # スクロールしてクリック実行
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                        parent_level2
                    )
                    time.sleep(1)
                    parent_level2.click()
                    time.sleep(3)

                    # モーダルが開いたかチェック
                    if self._is_modal_open():
                        print("    ✅ Select Servingモーダルが開きました！")
                        return True
                    else:
                        print("    ❌ Select Servingモーダルが開きませんでした")
                        return False

            print("    ❌ Amount eaten要素が見つかりませんでした")
            return False

        except Exception as e:
            print(f"    ❌ モーダルオープンエラー: {e}")
            return False

    def close_modal(self) -> bool:
        """
        Select Servingモーダルを閉じる（ESCキー使用）

        Returns:
            bool: モーダルが閉じられたかどうか
        """
        try:
            # ESCキーでモーダルを閉じる（確実・シンプル）
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
            print("    ✅ ESCキーでモーダル閉じる完了")
            return True

        except Exception as e:
            print(f"    ❌ モーダル閉じるエラー: {e}")
            return False

    def _close_any_open_modal(self):
        """既存のモーダル/ポップアップを閉じる"""
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass

    def _is_modal_open(self) -> bool:
        """Select Servingモーダルが開いているかチェック"""
        try:
            modal_indicators = [
                "//*[contains(text(), 'Select Serving')]",
                "//div[@role='radiogroup']",
                "//*[contains(text(), 'oz') and contains(text(), 'cal')]"
            ]

            for pattern in modal_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    if any(el.is_displayed() for el in elements):
                        return True
                except:
                    continue
            return False

        except Exception as e:
            print(f"        ⚠️ モーダル確認エラー: {e}")
            return False