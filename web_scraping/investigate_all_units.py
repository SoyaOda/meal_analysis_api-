#!/usr/bin/env python3
"""
MyNetDiaryで提供される全ての単位と実際重量データを調査するスクリプト
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
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("❌ Seleniumがインストールされていません: pip install selenium")
    sys.exit(1)

from config import config

class AllUnitsInvestigator:
    """全単位調査スクレイパー"""

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

    def navigate_to_food(self, food_name: str = "Almond milk unsweetened fortified") -> bool:
        """特定の食材ページに移動"""
        try:
            print(f"🔍 {food_name}に移動中...")

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
                return False

            # 食材をクリック
            target_food.click()
            time.sleep(config.REQUEST_DELAY)

            print(f"✅ {food_name}に移動完了")
            return True

        except Exception as e:
            print(f"❌ 食材移動エラー: {str(e)}")
            return False

    def investigate_all_units_and_weights(self) -> Dict[str, Any]:
        """全ての単位とその重量データを調査"""
        try:
            investigation_data = {
                'food_name': 'Almond milk unsweetened fortified',
                'investigation_time': datetime.now().isoformat(),
                'units_data': {}
            }

            print("🔍 利用可能な全単位を調査中...")

            # まず単位選択ドロップダウンを探す
            unit_selectors = []

            # 様々な単位選択要素を探す
            possible_selectors = [
                "select",
                "//select[contains(@class, 'unit')]",
                "//div[contains(@class, 'MuiSelect')]",
                "//div[contains(@class, 'select')]",
                "//*[contains(@class, 'unit-selector')]",
                "//*[contains(@class, 'serving-size')]"
            ]

            for selector in possible_selectors:
                try:
                    if selector == "select":
                        elements = self.driver.find_elements(By.TAG_NAME, selector)
                    else:
                        elements = self.driver.find_elements(By.XPATH, selector)

                    if elements:
                        print(f"  📋 発見: {selector} ({len(elements)}個)")
                        unit_selectors.extend(elements)
                except Exception as e:
                    continue

            # 利用可能な単位を取得
            available_units = []

            if unit_selectors:
                print(f"  🎯 {len(unit_selectors)}個の単位選択要素を発見")

                for i, selector_element in enumerate(unit_selectors):
                    try:
                        if selector_element.tag_name == "select":
                            # 標準のselectタグの場合
                            select = Select(selector_element)
                            options = select.options
                            unit_texts = [opt.text.strip() for opt in options if opt.text.strip()]

                            print(f"    Select {i+1}: {unit_texts}")
                            investigation_data['units_data'][f'selector_{i+1}'] = {
                                'type': 'select',
                                'options': unit_texts
                            }

                            available_units.extend(unit_texts)

                            # 各単位を試行して重量データを取得
                            for option in options:
                                if option.text.strip():
                                    unit_name = option.text.strip()
                                    weight_data = self.get_weight_for_unit(select, option, unit_name)
                                    if weight_data:
                                        investigation_data['units_data'][unit_name] = weight_data
                        else:
                            # その他のUI要素の場合
                            text = selector_element.text.strip()
                            if text:
                                print(f"    要素 {i+1}: {text}")
                                investigation_data['units_data'][f'element_{i+1}'] = {
                                    'type': 'other',
                                    'text': text
                                }

                    except Exception as e:
                        print(f"    ⚠️ 要素 {i+1} 処理エラー: {e}")
                        continue

            # "3 more servings" 的なボタンをクリックしてみる
            try:
                more_servings_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'more serving')]")
                for element in more_servings_elements:
                    print(f"  🔍 {element.text}を試行中...")
                    element.click()
                    time.sleep(2)

                    # 追加された単位を取得
                    additional_elements = self.driver.find_elements(By.TAG_NAME, "select")
                    for add_elem in additional_elements:
                        if add_elem not in unit_selectors:
                            select = Select(add_elem)
                            additional_options = [opt.text.strip() for opt in select.options if opt.text.strip()]
                            print(f"    📋 追加単位: {additional_options}")
                            investigation_data['units_data']['additional_units'] = additional_options
                            available_units.extend(additional_options)

            except Exception as e:
                print(f"  ⚠️ 追加単位調査エラー: {e}")

            # F, C, P要素をクリックして栄養情報も取得
            self.expand_nutrition_info()

            # 最終的な全テキスト取得
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            all_texts = [elem.text.strip() for elem in all_elements if elem.text.strip()]

            # 重量関連テキストをフィルタリング
            weight_texts = []
            for text in all_texts:
                if any(pattern in text.lower() for pattern in ['g)', 'gram', 'oz', 'cup', 'ml', 'fl oz', 'weight', 'serving size']):
                    if len(text) < 200:  # 長すぎるテキストは除外
                        weight_texts.append(text)

            investigation_data['weight_related_final_texts'] = weight_texts[:20]  # 最初の20個
            investigation_data['available_units_summary'] = list(set(available_units))

            return investigation_data

        except Exception as e:
            print(f"❌ 全単位調査エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}

    def get_weight_for_unit(self, select_element, option, unit_name: str) -> Dict:
        """指定単位を選択して重量データを取得"""
        try:
            print(f"    🎯 {unit_name}の重量データを取得中...")

            # 単位を選択
            select_element.select_by_visible_text(unit_name)
            time.sleep(2)

            # 重量情報を探す
            weight_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'g') or contains(text(), 'Weight')]")
            weight_info = []

            for elem in weight_elements:
                text = elem.text.strip()
                if 'g' in text and len(text) < 50:
                    weight_info.append(text)

            if weight_info:
                print(f"      ✅ 重量情報: {weight_info[:3]}")
                return {
                    'unit': unit_name,
                    'weight_info': weight_info[:3],
                    'success': True
                }
            else:
                print(f"      ⚠️ 重量情報なし")
                return {
                    'unit': unit_name,
                    'weight_info': [],
                    'success': False
                }

        except Exception as e:
            print(f"      ❌ {unit_name}重量取得エラー: {e}")
            return {
                'unit': unit_name,
                'error': str(e),
                'success': False
            }

    def expand_nutrition_info(self):
        """栄養情報を展開"""
        try:
            print("  🔍 栄養情報を展開中...")

            for letter in ['F', 'C', 'P']:
                try:
                    element = self.driver.find_element(By.XPATH, f"//div[text()='{letter}']")
                    element.click()
                    time.sleep(1)
                    print(f"    ✅ {letter}要素クリック成功")
                except:
                    print(f"    ⚠️ {letter}要素クリック失敗")

        except Exception as e:
            print(f"  ⚠️ 栄養情報展開エラー: {e}")

    def save_investigation_results(self, data: Dict) -> str:
        """調査結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"web_scraping/data/all_units_investigation_{timestamp}.json"

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
            print("🚀 全単位調査開始")

            self.setup_driver()

            if not self.login():
                print("❌ ログインに失敗しました")
                return

            if not self.navigate_to_food():
                print("❌ 食材移動に失敗しました")
                return

            investigation_data = self.investigate_all_units_and_weights()

            if investigation_data:
                filename = self.save_investigation_results(investigation_data)
                print(f"\n📊 調査完了: {filename}")

                # 要約を表示
                if 'available_units_summary' in investigation_data:
                    units = investigation_data['available_units_summary']
                    print(f"\n🎯 発見された単位: {len(units)}個")
                    for unit in units:
                        print(f"  📏 {unit}")
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
    investigator = AllUnitsInvestigator()
    investigator.run()