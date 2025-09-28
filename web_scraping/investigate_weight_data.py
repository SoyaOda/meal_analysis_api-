#!/usr/bin/env python3
"""
MyNetDiaryページから実際の重量データを調査するスクリプト
単位セクションで使用している概算値が元データと一致しているかを確認
"""

import json
import time
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("❌ Seleniumがインストールされていません: pip install selenium")
    sys.exit(1)

from config import config

class WeightDataInvestigator:
    """重量データ調査スクレイパー"""

    def __init__(self):
        self.driver = None
        self.wait = None

    def setup_driver(self) -> webdriver.Chrome:
        """Chrome WebDriverのセットアップ"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Mac用のChrome実行パスを設定
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_path):
            chrome_options.binary_location = chrome_path

        print("🚀 ChromeDriverを起動中...")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)
        return self.driver

    def login(self) -> bool:
        """MyNetDiaryにログイン"""
        try:
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

        except Exception as e:
            print(f"❌ ログインエラー: {str(e)}")
            return False

    def investigate_weight_display(self, food_name: str = "Almond milk unsweetened fortified") -> dict:
        """特定の食材で重量表示を詳細調査"""
        try:
            print(f"🔍 {food_name}の重量表示を調査中...")

            # Dairy, Dairy Substitutes & Eggカテゴリに移動
            category_name = "Dairy, Dairy Substitutes & Egg"
            staple_foods_url = f"{config.BASE_URL}/meals.do#ff"
            self.driver.get(staple_foods_url)
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

            # カテゴリをクリック
            category_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//span[text()='{category_name}']"))
            )
            category_button.click()
            time.sleep(config.REQUEST_DELAY)

            # 指定の食材を検索してクリック
            food_elements = self.driver.find_elements(
                By.XPATH,
                "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
            )

            target_food = None
            for element in food_elements:
                if food_name.lower() in element.text.lower():
                    target_food = element
                    break

            if not target_food:
                print(f"❌ {food_name}が見つかりません")
                return {}

            # 食材をクリック
            target_food.click()
            time.sleep(config.REQUEST_DELAY)

            investigation_data = {
                'food_name': food_name,
                'investigation_time': datetime.now().isoformat(),
                'weight_information': {}
            }

            # 基本情報を取得
            try:
                all_text_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
                all_texts = [elem.text.strip() for elem in all_text_elements if elem.text.strip()]

                print("📝 ページ内の全テキスト要素:")
                weight_related_texts = []
                for text in all_texts:
                    if any(unit in text.lower() for unit in ['cup', 'gram', 'tablespoon', 'teaspoon', 'oz', 'container', 'serving']):
                        weight_related_texts.append(text)
                        print(f"  🏷️ {text}")

                investigation_data['weight_information']['all_weight_related_texts'] = weight_related_texts

            except Exception as e:
                print(f"⚠️ テキスト要素取得エラー: {e}")

            # 単位選択要素を探す
            try:
                print("\n🔍 単位選択要素を探索中...")

                # セレクトボックスを探す
                select_elements = self.driver.find_elements(By.TAG_NAME, "select")
                print(f"  📋 select要素数: {len(select_elements)}")

                for i, select in enumerate(select_elements):
                    try:
                        options = select.find_elements(By.TAG_NAME, "option")
                        if options:
                            option_texts = [opt.text.strip() for opt in options if opt.text.strip()]
                            print(f"    Select {i+1}: {option_texts}")
                            investigation_data['weight_information'][f'select_options_{i+1}'] = option_texts
                    except Exception as e:
                        print(f"    Select {i+1} エラー: {e}")

                # Material-UI系のドロップダウンを探す
                mui_selects = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'MuiSelect-root') or contains(@class, 'MuiFormControl-root')]")
                print(f"  🎯 MUI select要素数: {len(mui_selects)}")

                # ボタン系の単位選択を探す
                unit_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'cup') or contains(text(), 'gram') or contains(text(), 'oz')]")
                if unit_buttons:
                    button_texts = [btn.text.strip() for btn in unit_buttons]
                    print(f"  🔘 単位関連ボタン: {button_texts}")
                    investigation_data['weight_information']['unit_buttons'] = button_texts

            except Exception as e:
                print(f"⚠️ 単位選択要素探索エラー: {e}")

            # F, C, P要素をクリックして栄養情報を展開
            try:
                print("\n🔍 F, C, P要素をクリックして詳細表示...")

                for letter in ['F', 'C', 'P']:
                    try:
                        element = self.driver.find_element(By.XPATH, f"//div[text()='{letter}']")
                        element.click()
                        time.sleep(1)
                        print(f"  ✅ {letter}要素クリック成功")
                    except:
                        print(f"  ⚠️ {letter}要素が見つからないかクリックできません")

                time.sleep(config.REQUEST_DELAY)

            except Exception as e:
                print(f"⚠️ F, C, P要素クリックエラー: {e}")

            # 展開後の詳細情報を取得
            try:
                print("\n📊 展開後の詳細情報を取得...")

                # 栄養素関連のテキストを再取得
                all_text_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
                expanded_texts = [elem.text.strip() for elem in all_text_elements if elem.text.strip()]

                nutrient_texts = []
                unit_weight_texts = []
                for text in expanded_texts:
                    if any(nutrient in text.lower() for nutrient in ['protein', 'fat', 'carb', 'fiber', 'sugar', 'sodium', 'calcium', 'iron']):
                        nutrient_texts.append(text)
                    elif any(pattern in text.lower() for pattern in ['g)', 'mg)', 'cal']):
                        unit_weight_texts.append(text)

                investigation_data['weight_information']['expanded_nutrient_texts'] = nutrient_texts[:10]  # 最初の10個
                investigation_data['weight_information']['expanded_unit_weight_texts'] = unit_weight_texts[:10]  # 最初の10個

                print(f"  🧪 栄養素テキスト例: {nutrient_texts[:3]}")
                print(f"  ⚖️ 単位・重量テキスト例: {unit_weight_texts[:3]}")

            except Exception as e:
                print(f"⚠️ 展開後情報取得エラー: {e}")

            return investigation_data

        except Exception as e:
            print(f"❌ 重量表示調査エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}

    def save_investigation_results(self, data: Dict) -> str:
        """調査結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"web_scraping/data/weight_investigation_{timestamp}.json"

        try:
            os.makedirs("web_scraping/data", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"💾 調査結果を保存しました: {filename}")
            return filename

        except Exception as e:
            print(f"❌ 保存エラー: {str(e)}")
            return ""

    def cleanup(self):
        """リソースをクリーンアップ"""
        if self.driver:
            print("🔄 WebDriverをクリーンアップ中...")
            self.driver.quit()

    def run(self):
        """メイン実行"""
        try:
            print("🚀 重量データ調査開始")

            self.setup_driver()

            if not self.login():
                print("❌ ログインに失敗しました")
                return

            # アーモンドミルクで調査
            investigation_data = self.investigate_weight_display("Almond milk unsweetened fortified")

            if investigation_data:
                filename = self.save_investigation_results(investigation_data)
                print(f"\n📊 調査完了: {filename}")
            else:
                print("❌ 調査データが取得できませんでした")

        except Exception as e:
            print(f"❌ 実行エラー: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        print("🏁 調査終了")

if __name__ == "__main__":
    investigator = WeightDataInvestigator()
    investigator.run()