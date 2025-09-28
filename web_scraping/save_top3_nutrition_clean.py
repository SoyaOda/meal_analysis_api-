#!/usr/bin/env python3
"""
MyNetDiary Top3食材の栄養情報を抽出するスクリプト（栄養素展開スキップ版）
テストで成功した条件に合わせて栄養素展開を一切行わずAmount eaten機能を実行
"""

import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from config import config

class Top3NutritionScraperClean:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.collected_foods = []

    def setup_driver(self):
        """ChromeDriverを設定"""
        print("🚀 ChromeDriverを起動中...")
        chrome_options = Options()
        if config.HEADLESS:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)

    def login(self):
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
        """Dairy, Dairy Substitutes & Eggカテゴリに移動"""
        print("🔍 カテゴリナビゲーション...")

        my_foods_url = f"{config.BASE_URL}/meals.do#ff"
        self.driver.get(my_foods_url)
        time.sleep(config.REQUEST_DELAY)

        my_foods_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
        )
        my_foods_button.click()
        time.sleep(config.REQUEST_DELAY)

        staple_foods_item = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
        )
        staple_foods_item.click()
        time.sleep(config.REQUEST_DELAY)

        category_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Dairy, Dairy Substitutes & Egg']"))
        )
        category_button.click()
        time.sleep(config.REQUEST_DELAY)

        print("✅ カテゴリナビゲーション完了")
        return True

    def get_top3_foods(self):
        """Top3食材の情報を取得"""
        print("\n🍽️ Top3食材の栄養情報を取得開始...")

        for food_index in range(3):
            food_number = food_index + 1
            print(f"\n{'='*60}")
            print(f"🥗 食材 {food_number} の処理開始")
            print(f"{'='*60}")

            try:
                food_list_items = self.driver.find_elements(
                    By.XPATH,
                    "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
                )

                if len(food_list_items) <= food_index:
                    print(f"❌ 食材 {food_number} が見つかりません")
                    continue

                food_item = food_list_items[food_index]
                food_name = food_item.text
                print(f"🎯 食材 {food_number}: {food_name[:50]}...")

                food_item.click()
                time.sleep(config.REQUEST_DELAY * 2)

                # 栄養素展開を一切行わず、直接Amount eaten機能を実行
                print("🔍 Amount eaten機能による単位データ抽出を実行...")
                units_data = self._extract_units_from_amount_section()

                if units_data:
                    print(f"✅ 食材 {food_number}: 単位データ抽出成功 - {len(units_data)}個の単位")
                    for unit in units_data:
                        print(f"  📊 {unit['unit_name']}: {unit['calories']}cal, {unit['weight']}g")
                else:
                    print(f"❌ 食材 {food_number}: 単位データ抽出失敗")
                    units_data = []

                # 食材データを保存
                food_data = {
                    "food_index": food_number,
                    "food_name": food_name.strip(),
                    "units_data": units_data,
                    "timestamp": datetime.now().isoformat()
                }

                self.collected_foods.append(food_data)

                # 次の食材のために戻る（最後の食材以外）
                if food_index < 2:
                    print(f"🔄 食材リストに戻る...")
                    self.driver.back()
                    time.sleep(3)

            except Exception as e:
                print(f"❌ 食材 {food_number} 処理エラー: {e}")
                continue

        print(f"\n🏁 Top3食材処理完了: {len(self.collected_foods)}個の食材データを収集")

    def _extract_units_from_amount_section(self):
        """Amount eaten機能を使用して単位データを抽出（栄養素展開スキップ版）"""
        try:
            print("    🔍 Amount eaten エリア構造分析...")

            # Amount eaten 要素を検索
            amount_eaten_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Amount eaten')]")

            if not amount_eaten_elements:
                print("    ❌ Amount eaten 要素が見つかりません")
                return []

            print(f"    📋 Amount eaten 要素数: {len(amount_eaten_elements)}個")

            # 表示されているAmount eaten要素を取得
            amount_element = None
            for element in amount_eaten_elements:
                if element.is_displayed():
                    amount_element = element
                    break

            if not amount_element:
                print("    ❌ 表示されているAmount eaten 要素が見つかりません")
                return []

            print(f"    ✅ Amount eaten 要素発見: {amount_element.tag_name}")

            # テストで成功した親レベル2を取得
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

                    # テストで成功した通常クリックを実行
                    print("    🔄 通常クリックでSelect Servingモーダルを開く...")

                    # スクロールして表示
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_level2)
                    time.sleep(1)

                    # 通常クリック実行
                    parent_level2.click()
                    time.sleep(3)

                    # Select Serving モーダルが開いたかチェック
                    if self._is_select_serving_modal_open():
                        print("    ✅ Select Serving モーダルが開きました！")
                        units_data = self._extract_real_modal_data()
                        self._close_select_serving_modal()
                        return units_data
                    else:
                        print("    ❌ Select Serving モーダルが開きませんでした")
                        return []
                else:
                    print("    ❌ 適切なクリック可能エリアが見つかりません")
                    return []

            except Exception as e:
                print(f"    ⚠️ 親レベル2チェックエラー: {e}")
                return []

        except Exception as e:
            print(f"    ❌ Amount eaten テストエラー: {e}")
            return []

    def _extract_real_modal_data(self):
        """実際のSelect Servingモーダルからデータを抽出"""
        try:
            print("      🔍 実際のモーダルデータを抽出中...")
            units_data = []

            # デバッグ用のモーダル内容確認
            modal_content = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'cal')]")
            print(f"      📋 カロリー要素数: {len(modal_content)}個")

            # 実際のモーダル構造に対応したパターン
            serving_patterns = [
                "//*[contains(text(), 'oz') and contains(text(), 'cal')]",
                "//*[contains(text(), 'container') and contains(text(), 'cal')]",
                "//*[contains(text(), 'gram') and contains(text(), 'cal')]",
                "//*[contains(text(), 'lb') and contains(text(), 'cal')]",
                "//*[contains(text(), 'cup') and contains(text(), 'cal')]",
                "//*[contains(text(), 'tbsp') and contains(text(), 'cal')]",
                "//*[contains(text(), 'tsp') and contains(text(), 'cal')]"
            ]

            for pattern in serving_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            element_text = element.text.strip()
                            if element_text and 'cal' in element_text.lower():
                                parsed_data = self._parse_unit_text(element_text)
                                if parsed_data:
                                    units_data.append(parsed_data)
                                    print(f"        ✅ 単位データ: {parsed_data['unit_name']} - {parsed_data['calories']}cal - {parsed_data['weight']}g")
                except Exception as e:
                    print(f"        ⚠️ パターン{pattern}処理エラー: {e}")
                    continue

            if not units_data:
                print("      ⚠️ 標準パターンで単位が見つかりません。フラグメント再構築を試行...")
                units_data = self._reconstruct_units_from_fragments()

            print(f"      🎯 抽出完了: {len(units_data)}個の単位データ")
            return units_data

        except Exception as e:
            print(f"      ❌ モーダルデータ抽出エラー: {e}")
            return []

    def _reconstruct_units_from_fragments(self):
        """フラグメント化されたデータから単位情報を再構築"""
        try:
            print("        🔧 フラグメント再構築開始...")
            units_data = []

            # より幅広いテキスト要素を検索
            all_text_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'cal') or contains(text(), 'g')]")

            for element in all_text_elements:
                if element.is_displayed():
                    text = element.text.strip()
                    if text and ('cal' in text.lower() or 'g' in text.lower()):
                        # 隣接要素も含めて単位情報を構築
                        try:
                            parent = element.find_element(By.XPATH, "..")
                            parent_text = parent.text.strip()
                            if parent_text:
                                parsed_data = self._parse_unit_text(parent_text)
                                if parsed_data and not any(u['unit_name'] == parsed_data['unit_name'] for u in units_data):
                                    units_data.append(parsed_data)
                                    print(f"          🔧 再構築: {parsed_data['unit_name']} - {parsed_data['calories']}cal - {parsed_data['weight']}g")
                        except:
                            continue

            print(f"        ✅ フラグメント再構築完了: {len(units_data)}個")
            return units_data

        except Exception as e:
            print(f"        ❌ フラグメント再構築エラー: {e}")
            return []

    def _parse_unit_text(self, text):
        """単位テキストをパースして構造化データに変換"""
        import re

        try:
            text = text.strip()
            if not text:
                return None

            # パターン1: "oz 26cals / 28.3 g" 形式
            pattern1 = r'(\w+)\s+(\d+(?:\.\d+)?)cals?\s*/\s*(\d+(?:\.\d+)?)\s*g'
            match1 = re.search(pattern1, text, re.IGNORECASE)
            if match1:
                unit_name = match1.group(1)
                calories = float(match1.group(2))
                weight = float(match1.group(3))

                return {
                    'unit_name': unit_name,
                    'calories': calories,
                    'weight': weight,
                    'raw_text': text
                }

            # パターン2: "container 140cals / 150 g" 形式
            pattern2 = r'(\w+)\s+(\d+(?:\.\d+)?)cals?\s*/\s*(\d+(?:\.\d+)?)\s*g'
            match2 = re.search(pattern2, text, re.IGNORECASE)
            if match2:
                unit_name = match2.group(1)
                calories = float(match2.group(2))
                weight = float(match2.group(3))

                return {
                    'unit_name': unit_name,
                    'calories': calories,
                    'weight': weight,
                    'raw_text': text
                }

            # パターン3: より柔軟なパターン
            cal_match = re.search(r'(\d+(?:\.\d+)?)\s*cals?', text, re.IGNORECASE)
            weight_match = re.search(r'(\d+(?:\.\d+)?)\s*g', text, re.IGNORECASE)
            unit_match = re.search(r'^(\w+)', text)

            if cal_match and weight_match and unit_match:
                return {
                    'unit_name': unit_match.group(1),
                    'calories': float(cal_match.group(1)),
                    'weight': float(weight_match.group(1)),
                    'raw_text': text
                }

            return None

        except Exception as e:
            print(f"          ⚠️ テキストパースエラー: {e} - テキスト: '{text}'")
            return None

    def _close_any_open_modals(self):
        """開いているモーダルがあれば閉じる"""
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass

    def _is_select_serving_modal_open(self):
        """Select Serving モーダルが開いているかチェック"""
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
            print("        ✅ Select Serving モーダルを閉じました")
        except:
            pass

    def save_results(self):
        """結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nutrition_data_clean_{timestamp}.json"

        output_data = {
            "extraction_info": {
                "timestamp": datetime.now().isoformat(),
                "total_foods_processed": len(self.collected_foods),
                "method": "amount_eaten_clean_no_nutrition_expansion"
            },
            "foods": self.collected_foods
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"📄 結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def run(self):
        """メイン実行フロー"""
        try:
            self.setup_driver()

            if not self.login():
                print("❌ ログインに失敗しました")
                return False

            if not self.navigate_to_category():
                print("❌ カテゴリナビゲーションに失敗")
                return False

            self.get_top3_foods()

            # 結果サマリー
            print(f"\n{'='*60}")
            print("🏁 MyNetDiary Top3食材抽出完了")
            print(f"{'='*60}")
            print(f"📊 処理済み食材数: {len(self.collected_foods)}")

            for i, food in enumerate(self.collected_foods, 1):
                units_count = len(food.get('units_data', []))
                print(f"   食材{i}: {food['food_name'][:30]}... ({units_count}個の単位)")

            filename = self.save_results()
            print(f"✅ 全ての処理が完了しました: {filename}")

            return True

        except Exception as e:
            print(f"❌ 実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    scraper = Top3NutritionScraperClean()
    scraper.run()