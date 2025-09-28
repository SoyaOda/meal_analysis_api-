#!/usr/bin/env python3
"""
MyNetDiaryの全カテゴリと各カテゴリ内の食材を発見・保存するスクリプト
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

class CategoryFoodDiscoverer:
    """カテゴリと食材を発見するスクレイパー"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.categories_data = {}

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

    def navigate_to_staple_foods(self) -> bool:
        """Staple Foodsメニューに移動"""
        try:
            print("🔍 Staple Foodsメニューに移動中...")

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

            print("✅ Staple Foodsメニュー移動成功")
            return True

        except Exception as e:
            print(f"❌ Staple Foodsメニュー移動エラー: {str(e)}")
            return False

    def discover_categories(self) -> List[str]:
        """利用可能なカテゴリを発見"""
        try:
            print("🔍 利用可能なカテゴリを発見中...")

            # 正確なクラス名でカテゴリリストを取得
            category_elements = self.driver.find_elements(
                By.XPATH,
                "//span[contains(@class, 'MuiListItemText-primary')]"
            )

            categories = []
            # 既知のカテゴリ名のリスト（デバッグで発見済み）
            known_categories = [
                "Beans & Peas", "Beverages", "Breads & Rolls", "Cheese",
                "Condiments, Dressings & Sauces", "Dairy, Dairy Substitutes & Egg",
                "Fats & Oils", "Fish & Seafood", "Fruit - canned, dried, or juice",
                "Fruit - raw or frozen", "Grains & Grain Products", "Meats",
                "Nuts & Seeds", "Poultry", "Spices & Herbs", "Stocks and Gravy",
                "Sweets & Sweeteners", "Vegetables - canned, dried, or juice",
                "Vegetables - raw, frozen, or cooked"
            ]

            for element in category_elements:
                text = element.text.strip()
                if text in known_categories:
                    categories.append(text)
                    print(f"  📁 発見: {text}")

            print(f"✅ {len(categories)}個のカテゴリを発見")
            return categories

        except Exception as e:
            print(f"❌ カテゴリ発見エラー: {str(e)}")
            return []

    def get_foods_in_category(self, category_name: str) -> List[str]:
        """指定カテゴリ内の食材リストを取得"""
        try:
            print(f"🍲 {category_name}カテゴリの食材を取得中...")

            # カテゴリをクリック
            category_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//span[text()='{category_name}']"))
            )
            category_button.click()
            time.sleep(config.REQUEST_DELAY)

            # 食材リストを取得
            food_elements = self.driver.find_elements(
                By.XPATH,
                "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
            )

            foods = []
            for element in food_elements:
                food_text = element.text.strip()
                if food_text and len(food_text) > 5:  # 短すぎるテキストは除外
                    foods.append(food_text)

            print(f"  ✅ {len(foods)}個の食材を発見")
            return foods[:10]  # 最初の10個のみ取得（時間短縮のため）

        except Exception as e:
            print(f"❌ {category_name}の食材取得エラー: {str(e)}")
            return []

    def discover_all_categories_and_foods(self) -> Dict[str, Any]:
        """全カテゴリと食材を発見"""
        try:
            # Staple Foodsに移動
            if not self.navigate_to_staple_foods():
                return {}

            # カテゴリを発見
            categories = self.discover_categories()

            all_data = {
                'discovery_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_categories': len(categories),
                    'source': 'MyNetDiary - Staple Foods'
                },
                'categories': {}
            }

            # 各カテゴリの食材を取得
            for category in categories:
                try:
                    # Staple Foodsに戻る
                    if not self.navigate_to_staple_foods():
                        continue

                    foods = self.get_foods_in_category(category)
                    all_data['categories'][category] = {
                        'food_count': len(foods),
                        'foods': foods
                    }

                except Exception as e:
                    print(f"⚠️ {category}処理エラー: {e}")
                    all_data['categories'][category] = {
                        'food_count': 0,
                        'foods': [],
                        'error': str(e)
                    }

            return all_data

        except Exception as e:
            print(f"❌ 全体発見エラー: {str(e)}")
            return {}

    def save_results(self, data: Dict) -> str:
        """結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"web_scraping/data/categories_foods_discovery_{timestamp}.json"

        try:
            os.makedirs("web_scraping/data", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"💾 結果を保存しました: {filename}")
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
            print("🚀 カテゴリ・食材発見開始")

            self.setup_driver()

            if not self.login():
                print("❌ ログインに失敗しました")
                return

            data = self.discover_all_categories_and_foods()

            if data:
                filename = self.save_results(data)

                print(f"\n📊 発見結果:")
                print(f"  カテゴリ数: {data['discovery_info']['total_categories']}")
                for category, info in data['categories'].items():
                    print(f"  📁 {category}: {info['food_count']}個の食材")
                    if info['foods']:
                        print(f"     例: {', '.join(info['foods'][:3])}...")
            else:
                print("❌ データが取得できませんでした")

        except Exception as e:
            print(f"❌ 実行エラー: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        print("🏁 発見終了")

if __name__ == "__main__":
    discoverer = CategoryFoodDiscoverer()
    discoverer.run()