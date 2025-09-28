#!/usr/bin/env python3
"""
「3 more servings」クリック後の完全な単位データを抽出するスクリプト
"""

import json
import time
import sys
import os
import re
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
    from selenium.webdriver.common.action_chains import ActionChains
except ImportError:
    print("❌ Seleniumがインストールされていません: pip install selenium")
    sys.exit(1)

from config import config

class CompleteUnitsExtractor:
    """完全な単位データ抽出スクレイパー"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.actions = None

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
        self.actions = ActionChains(self.driver)
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

    def extract_complete_units_data(self) -> Dict[str, Any]:
        """完全な単位データを抽出"""
        try:
            result_data = {
                'food_name': 'Almond milk unsweetened fortified',
                'extraction_time': datetime.now().isoformat(),
                'units': {},
                'detailed_nutrients': {},
                'extraction_successful': False
            }

            print("🔍 完全な単位データを抽出中...")

            # ステップ1: 「X more servings」ボタンをクリック（Xは任意の数字）
            print("  📋 ステップ1: 'X more servings'ボタンをクリック")
            more_servings_patterns = [
                "//*[contains(text(), 'more serving')]",
                "//*[contains(text(), 'more Serving')]"
            ]

            more_servings_clicked = False
            for pattern in more_servings_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        try:
                            element_text = element.text.strip()

                            # "数字 more serving" のパターンに一致するかチェック
                            if re.match(r'^\d+\s+more\s+serving', element_text.lower()):
                                print(f"    🎯 '{element_text}'をクリック中...")
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                time.sleep(1)
                                element.click()
                                time.sleep(3)
                                more_servings_clicked = True
                                print(f"    ✅ '{element_text}'クリック成功")
                                break
                            else:
                                print(f"    ⚠️ パターン不一致: '{element_text}'")
                        except Exception as e:
                            print(f"    ⚠️ 要素処理エラー: {e}")
                            continue
                    if more_servings_clicked:
                        break
                except Exception as e:
                    print(f"    ⚠️ パターン検索エラー: {e}")
                    continue

            if not more_servings_clicked:
                print("    ❌ 'X more servings'ボタンが見つかりません")
                return result_data

            # ステップ2: 全テキストを取得してSelect Serving情報を解析
            print("  📋 ステップ2: Select Serving情報を解析")
            body_text = self.driver.find_element(By.TAG_NAME, "body").text

            # 「Select Serving」から「CANCEL」までの部分を抽出
            serving_section = self.extract_serving_section(body_text)
            units_data = {}  # 変数を初期化

            if serving_section:
                print("    ✅ Select Serving情報発見:")
                for line in serving_section:
                    print(f"      {line}")

                # 各単位の情報を解析
                units_data = self.parse_serving_lines(serving_section)
                result_data['units'] = units_data

                if units_data:
                    print(f"    📊 {len(units_data)}個の単位データを抽出")
                    result_data['extraction_successful'] = True
            else:
                print("    ⚠️ Select Serving情報が見つかりません")

            # ステップ3: F, C, P要素をクリックして栄養情報を取得
            print("  📋 ステップ3: 栄養情報を取得")
            self.expand_nutrition_info()

            # 栄養情報を抽出
            detailed_nutrients = self.extract_detailed_nutrients()
            result_data['detailed_nutrients'] = detailed_nutrients

            # ステップ4: 基準単位を特定
            print("  📋 ステップ4: 基準単位を特定")
            if units_data:
                # 最も重量の重い単位を基準として設定（通常は最初に表示される単位）
                first_unit = list(units_data.keys())[0]
                result_data['base_unit'] = first_unit
                result_data['base_calories'] = units_data[first_unit]['calories']
                result_data['base_weight_g'] = units_data[first_unit]['weight_g']

                print(f"    ✅ 基準単位: {first_unit} ({result_data['base_calories']}cals / {result_data['base_weight_g']}g)")

            return result_data

        except Exception as e:
            print(f"❌ データ抽出エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'extraction_time': datetime.now().isoformat(),
                'extraction_successful': False
            }

    def extract_serving_section(self, text: str) -> List[str]:
        """テキストからSelect Serving部分を抽出"""
        try:
            lines = text.split('\n')
            serving_lines = []
            in_serving_section = False

            for line in lines:
                line = line.strip()

                # Select Servingセクションの開始
                if 'Select Serving' in line:
                    in_serving_section = True
                    continue

                # CANCELでセクション終了
                if line == 'CANCEL' and in_serving_section:
                    break

                # セクション内の行を収集
                if in_serving_section and line:
                    # "unit Xcals / Yg"パターンの行のみ収集
                    if 'cals' in line and '/' in line and 'g' in line:
                        serving_lines.append(line)

            return serving_lines

        except Exception as e:
            print(f"  ⚠️ Select Serving部分抽出エラー: {e}")
            return []

    def parse_serving_lines(self, lines: List[str]) -> Dict[str, Dict]:
        """サービング行を解析して単位データを構築"""
        try:
            units_data = {}

            for line in lines:
                # "cup 30cals / 245 g"のようなパターンを解析
                match = re.match(r'^(\w+(?:\s+\w+)*)\s+(\d+)cals\s+/\s+([\d.]+)\s*g$', line.strip())

                if match:
                    unit = match.group(1).strip()
                    calories = int(match.group(2))
                    weight_g = float(match.group(3))

                    units_data[unit] = {
                        'calories': calories,
                        'weight_g': weight_g
                    }

                    print(f"      ✅ {unit}: {calories}cals / {weight_g}g")
                else:
                    print(f"      ⚠️ 解析失敗: {line}")

            return units_data

        except Exception as e:
            print(f"  ⚠️ サービング行解析エラー: {e}")
            return {}

    def expand_nutrition_info(self):
        """栄養情報を展開"""
        try:
            print("    🔍 栄養情報を展開中...")

            for letter in ['F', 'C', 'P']:
                try:
                    element = self.driver.find_element(By.XPATH, f"//div[text()='{letter}']")
                    element.click()
                    time.sleep(1)
                    print(f"      ✅ {letter}要素クリック成功")
                except:
                    print(f"      ⚠️ {letter}要素クリック失敗")

        except Exception as e:
            print(f"    ⚠️ 栄養情報展開エラー: {e}")

    def extract_detailed_nutrients(self) -> Dict:
        """詳細栄養情報を抽出"""
        try:
            print("    🔍 詳細栄養情報を抽出中...")

            # 栄養素キーワードマッピング
            nutrient_keywords = {
                'protein': ['protein'],
                'fat': ['fat'],
                'carbs': ['carb', 'carbs'],
                'fiber': ['fiber', 'fibre'],
                'sugar': ['sugar'],
                'sodium': ['sodium'],
                'calcium': ['calcium'],
                'iron': ['iron'],
                'potassium': ['potassium'],
                'vitamin_c': ['vitamin c']
            }

            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            lines = body_text.split('\n')

            detailed_nutrients = {}

            for nutrient_key, keywords in nutrient_keywords.items():
                for line in lines:
                    line_lower = line.lower().strip()

                    for keyword in keywords:
                        if keyword in line_lower and any(char.isdigit() for char in line):
                            # 数値を抽出
                            numbers = re.findall(r'\d+(?:\.\d+)?', line)
                            if numbers:
                                try:
                                    value = float(numbers[0])
                                    detailed_nutrients[nutrient_key] = {
                                        'value': value,
                                        'text': line.strip(),
                                        'keyword_matched': keyword
                                    }
                                    print(f"      ✅ {nutrient_key}: {value} ({line.strip()[:50]})")
                                    break
                                except:
                                    continue

                    if nutrient_key in detailed_nutrients:
                        break

            return detailed_nutrients

        except Exception as e:
            print(f"    ⚠️ 詳細栄養情報抽出エラー: {e}")
            return {}

    def save_extraction_results(self, data: Dict) -> str:
        """抽出結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"web_scraping/data/complete_units_extraction_{timestamp}.json"

        try:
            os.makedirs("web_scraping/data", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"💾 抽出結果を保存しました: {filename}")
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
            print("🚀 完全単位データ抽出開始")

            self.setup_driver()

            if not self.login():
                print("❌ ログインに失敗しました")
                return

            if not self.navigate_to_food():
                print("❌ 食材移動に失敗しました")
                return

            extraction_data = self.extract_complete_units_data()

            if extraction_data and extraction_data.get('extraction_successful'):
                filename = self.save_extraction_results(extraction_data)
                print(f"\n📊 完全単位データ抽出完了: {filename}")

                # 結果要約を表示
                units = extraction_data.get('units', {})
                nutrients = extraction_data.get('detailed_nutrients', {})

                print(f"\n🎯 抽出要約:")
                print(f"  📏 単位データ: {len(units)}個")
                for unit, data in units.items():
                    print(f"    - {unit}: {data['calories']}cals / {data['weight_g']}g")

                print(f"  🥗 栄養データ: {len(nutrients)}個")
                for nutrient, data in nutrients.items():
                    print(f"    - {nutrient}: {data['value']}{data.get('unit', '')}")

                if extraction_data.get('base_unit'):
                    print(f"  🎯 基準単位: {extraction_data['base_unit']}")

            else:
                print("❌ 完全単位データの抽出に失敗しました")

        except Exception as e:
            print(f"❌ 実行エラー: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        print("🏁 完全単位データ抽出終了")

if __name__ == "__main__":
    extractor = CompleteUnitsExtractor()
    extractor.run()