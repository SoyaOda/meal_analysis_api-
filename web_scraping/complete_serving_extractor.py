#!/usr/bin/env python3
"""
Complete Serving情報抽出スクリプト
判明した構造に基づいて網羅的にserving情報を取得
"""

import time
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from config import config

class CompleteServingExtractor:
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

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)

    def login_and_navigate(self):
        """ログイン & カテゴリナビゲーション"""
        print("🔐 MyNetDiaryにログイン...")
        self.driver.get(config.LOGIN_URL)
        time.sleep(config.REQUEST_DELAY)

        username = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
        password = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        username.send_keys(config.USERNAME)
        password.send_keys(config.PASSWORD)

        login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='jss15']")
        login_btn.click()
        time.sleep(config.REQUEST_DELAY * 2)

        # カテゴリナビゲーション
        my_foods_url = f"{config.BASE_URL}/meals.do#ff"
        self.driver.get(my_foods_url)
        time.sleep(config.REQUEST_DELAY)

        my_foods_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
        )
        my_foods_btn.click()
        time.sleep(config.REQUEST_DELAY)

        staple_foods = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
        )
        staple_foods.click()
        time.sleep(config.REQUEST_DELAY)

        category = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Dairy, Dairy Substitutes & Egg']"))
        )
        category.click()
        time.sleep(config.REQUEST_DELAY)

        print("✅ ログイン & ナビゲーション完了")
        return True

    def extract_top3_foods_complete_serving(self):
        """Top3食材の完全serving情報を抽出"""
        print("\n🍽️ Top3食材の完全serving情報を抽出開始...")

        for food_index in range(3):
            food_number = food_index + 1
            print(f"\n{'='*60}")
            print(f"🥗 食材 {food_number} の処理開始")
            print(f"{'='*60}")

            try:
                # 食材リストを取得
                food_list_items = self.driver.find_elements(
                    By.XPATH,
                    "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
                )

                if len(food_list_items) <= food_index:
                    print(f"❌ 食材 {food_number} が見つかりません")
                    continue

                food_item = food_list_items[food_index]
                food_name = food_item.text.strip()
                print(f"🎯 食材 {food_number}: {food_name[:50]}...")

                # 食材をクリック
                food_item.click()
                time.sleep(config.REQUEST_DELAY * 2)

                # 完全serving情報を抽出
                serving_data = self._extract_complete_serving_data()

                if serving_data:
                    print(f"✅ 食材 {food_number}: serving情報取得成功 - {len(serving_data)}個のオプション")
                    for option in serving_data:
                        print(f"  📊 {option['unit_name']}: {option['calories']}cal / {option['weight']}g")
                else:
                    print(f"❌ 食材 {food_number}: serving情報取得失敗")
                    serving_data = []

                # 食材データを保存
                food_data = {
                    "food_index": food_number,
                    "food_name": food_name,
                    "serving_options": serving_data,
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

    def _extract_complete_serving_data(self):
        """完全serving情報を抽出（判明した構造に基づく）"""
        try:
            print("    🔍 Select Servingモーダルを開く...")

            # Amount eaten要素を検索してクリック
            amount_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Amount eaten')]")

            for element in amount_elements:
                if element.is_displayed():
                    parent_level2 = element.find_element(By.XPATH, "../..")

                    # 既存モーダルを閉じる
                    try:
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(1)
                    except:
                        pass

                    # クリック実行
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_level2)
                    time.sleep(1)
                    parent_level2.click()
                    time.sleep(3)

                    # モーダルが開いたかチェック
                    if self._is_select_serving_modal_open():
                        print("    ✅ Select Servingモーダルが開きました！")

                        # 完全serving情報を抽出
                        serving_options = self._extract_all_serving_options()

                        # モーダルを閉じる
                        self._close_modal()

                        return serving_options
                    else:
                        print("    ❌ Select Servingモーダルが開きませんでした")
                        return []

            print("    ❌ Amount eaten要素が見つかりませんでした")
            return []

        except Exception as e:
            print(f"    ❌ serving情報抽出エラー: {e}")
            return []

    def _extract_all_serving_options(self):
        """全てのserving optionsを抽出"""
        try:
            print("      🔍 全serving optionsを抽出中...")
            serving_options = []

            # ラジオボタングループを取得
            radio_group = self.driver.find_element(By.XPATH, "//div[@role='radiogroup']")

            # FormControlLabel要素を取得（各serving option）
            form_labels = radio_group.find_elements(By.XPATH, ".//label[contains(@class, 'MuiFormControlLabel-root')]")
            print(f"      📋 発見されたoptions: {len(form_labels)}個")

            for i, label in enumerate(form_labels):
                try:
                    # ラジオボタンの値を取得
                    radio_input = label.find_element(By.XPATH, ".//input[@type='radio']")
                    radio_value = radio_input.get_attribute('value')

                    # ラベルテキストを取得
                    label_span = label.find_element(By.XPATH, ".//span[contains(@class, 'MuiFormControlLabel-label')]")
                    label_text = label_span.text.strip()

                    # 構造化データにパース
                    parsed_option = self._parse_serving_option(label_text, radio_value)

                    if parsed_option:
                        serving_options.append(parsed_option)
                        print(f"        ✅ Option{i+1}: {parsed_option['unit_name']} - {parsed_option['calories']}cal/{parsed_option['weight']}g")

                except Exception as e:
                    print(f"        ⚠️ Option{i+1}解析エラー: {e}")
                    continue

            print(f"      🎯 serving options抽出完了: {len(serving_options)}個")
            return serving_options

        except Exception as e:
            print(f"      ❌ serving options抽出エラー: {e}")
            return []

    def _parse_serving_option(self, label_text, radio_value):
        """serving optionを構造化データにパース"""
        try:
            # パターン: "{unit_name} {calories}cals / {weight} g"
            pattern = r'^(\w+)\s+(\d+(?:\.\d+)?)cals?\s*/\s*(\d+(?:\.\d+)?)\s*g'
            match = re.match(pattern, label_text, re.IGNORECASE)

            if match:
                unit_name = match.group(1)
                calories = float(match.group(2))
                weight = float(match.group(3))

                return {
                    "unit_name": unit_name,
                    "calories": calories,
                    "weight": weight,
                    "radio_value": radio_value,
                    "raw_text": label_text
                }
            else:
                print(f"        ⚠️ パース失敗: '{label_text}'")
                return None

        except Exception as e:
            print(f"        ⚠️ パースエラー: {e} - テキスト: '{label_text}'")
            return None

    def _is_select_serving_modal_open(self):
        """Select Servingモーダルが開いているかチェック"""
        try:
            modal_indicators = [
                "//*[contains(text(), 'Select Serving')]",
                "//div[@role='radiogroup']"
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

    def _close_modal(self):
        """モーダルを閉じる"""
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass

    def save_results(self):
        """結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # test_resultsフォルダに保存
        results_dir = "test_results"
        filename = f"{results_dir}/complete_serving_data_{timestamp}.json"

        output_data = {
            "extraction_info": {
                "timestamp": datetime.now().isoformat(),
                "total_foods_processed": len(self.collected_foods),
                "method": "complete_serving_extraction",
                "description": "網羅的serving情報取得（ラジオボタン構造解析版）",
                "data_structure": "生データ形式で商材固有のserving情報を完全保存"
            },
            "foods": self.collected_foods,
            "metadata": {
                "source_platform": "MyNetDiary",
                "category": "Dairy, Dairy Substitutes & Egg",
                "extraction_method": "selenium_radio_button_analysis",
                "data_quality": "raw_complete_serving_options"
            }
        }

        # サマリー統計を追加
        total_options = sum(len(food.get('serving_options', [])) for food in self.collected_foods)
        output_data["extraction_info"]["total_serving_options"] = total_options

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"📄 結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def run_complete_extraction(self):
        """完全抽出実行"""
        try:
            print("🏁 Complete Serving情報抽出開始")
            print("="*60)

            self.setup_driver()

            if not self.login_and_navigate():
                print("❌ ログイン・ナビゲーション失敗")
                return False

            # Top3食材の完全serving情報を抽出
            self.extract_top3_foods_complete_serving()

            # 結果サマリー
            print(f"\n{'='*60}")
            print("🏁 Complete Serving情報抽出完了")
            print(f"{'='*60}")
            print(f"📊 処理済み食材数: {len(self.collected_foods)}")

            total_options = 0
            for i, food in enumerate(self.collected_foods, 1):
                options_count = len(food.get('serving_options', []))
                total_options += options_count
                print(f"   食材{i}: {food['food_name'][:30]}... ({options_count}個のserving)")

            print(f"📈 総serving options数: {total_options}個")

            # 結果保存
            filename = self.save_results()
            print(f"✅ 全ての処理が完了しました: {filename}")

            return True

        except Exception as e:
            print(f"❌ 完全抽出エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    extractor = CompleteServingExtractor()
    extractor.run_complete_extraction()