#!/usr/bin/env python3
"""
Select Servingモーダルの深度分析スクリプト
HTMLソースとラジオボタン構造を詳細解析
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
from selenium.webdriver.common.action_chains import ActionChains
from config import config

class DeepServingAnalyzer:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.analysis_data = {
            "timestamp": datetime.now().isoformat(),
            "serving_options": [],
            "radio_buttons": [],
            "detailed_structure": {},
            "html_fragments": {}
        }

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
        """ログインして調査対象に移動"""
        print("🔐 ログイン & ナビゲーション...")

        # ログイン
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

        # 2番目の食材を選択
        food_items = self.driver.find_elements(
            By.XPATH,
            "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
        )

        if len(food_items) >= 2:
            food_items[1].click()
            time.sleep(config.REQUEST_DELAY * 2)
            return True
        return False

    def open_serving_modal(self):
        """Select Servingモーダルを開く"""
        print("🔍 Select Servingモーダルを開く...")

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

                # モーダル確認
                modal_indicators = [
                    "//*[contains(text(), 'Select Serving')]",
                    "//*[contains(text(), 'oz') and contains(text(), 'cal')]"
                ]

                for pattern in modal_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, pattern)
                        if any(el.is_displayed() for el in elements):
                            print("✅ Select Servingモーダルが開きました！")
                            return True
                    except:
                        continue

        print("❌ Select Servingモーダルが開けませんでした")
        return False

    def analyze_radio_button_structure(self):
        """ラジオボタン構造の深度分析"""
        print("\n🔍 ラジオボタン構造の深度分析...")

        try:
            # ラジオボタングループを検索
            radio_group = self.driver.find_element(By.XPATH, "//div[@role='radiogroup']")
            print("✅ ラジオボタングループを発見")

            # FormControlLabel要素を検索（これが各serving option）
            form_labels = radio_group.find_elements(By.XPATH, ".//label[contains(@class, 'MuiFormControlLabel-root')]")
            print(f"📋 FormControlLabel要素数: {len(form_labels)}個")

            serving_options = []

            for i, label in enumerate(form_labels):
                try:
                    print(f"\n  🔍 オプション{i+1}を分析中...")

                    # ラジオボタンのinput要素
                    radio_input = label.find_element(By.XPATH, ".//input[@type='radio']")
                    radio_value = radio_input.get_attribute('value')
                    is_checked = radio_input.get_attribute('checked') is not None

                    print(f"    📋 ラジオボタン値: {radio_value}, 選択状態: {is_checked}")

                    # ラベルテキスト内容を詳細解析
                    label_span = label.find_element(By.XPATH, ".//span[contains(@class, 'MuiFormControlLabel-label')]")
                    label_html = label_span.get_attribute('innerHTML')
                    label_text = label_span.text

                    print(f"    📝 ラベルテキスト: '{label_text[:100]}...'")

                    # HTMLから詳細情報を抽出
                    detailed_info = self._parse_label_content(label_html, label_text)

                    option_data = {
                        "index": i + 1,
                        "radio_value": radio_value,
                        "is_selected": is_checked,
                        "label_text": label_text,
                        "label_html": label_html[:500],  # 最初の500文字
                        "parsed_info": detailed_info
                    }

                    serving_options.append(option_data)

                    # 詳細情報をログ出力
                    if detailed_info:
                        print(f"    📊 解析結果:")
                        for key, value in detailed_info.items():
                            print(f"      {key}: {value}")

                except Exception as e:
                    print(f"    ⚠️ オプション{i+1}解析エラー: {e}")
                    continue

            self.analysis_data["serving_options"] = serving_options
            print(f"\n✅ ラジオボタン分析完了: {len(serving_options)}個のオプション")
            return True

        except Exception as e:
            print(f"❌ ラジオボタン分析エラー: {e}")
            return False

    def _parse_label_content(self, html_content, text_content):
        """ラベル内容を詳細パース"""
        try:
            parsed_info = {}

            # テキストからの情報抽出
            lines = text_content.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]

            if non_empty_lines:
                parsed_info["first_line"] = non_empty_lines[0]
                if len(non_empty_lines) > 1:
                    parsed_info["additional_lines"] = non_empty_lines[1:]

            # カロリー情報の抽出
            cal_pattern = r'(\d+(?:\.\d+)?)\s*cals?'
            cal_matches = re.findall(cal_pattern, text_content, re.IGNORECASE)
            if cal_matches:
                parsed_info["calories"] = cal_matches

            # 重量情報の抽出
            weight_patterns = [
                r'(\d+(?:\.\d+)?)\s*g(?:\s|$|\.)',
                r'(\d+(?:\.\d+)?)\s*gram',
                r'(\d+(?:\.\d+)?)\s*oz',
                r'(\d+(?:\.\d+)?)\s*lb'
            ]

            for pattern in weight_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    parsed_info["weights"] = matches

            # 単位名の抽出
            unit_patterns = [
                r'\b(oz|gram|g|lb|cup|ml|fl\s*oz|tbsp|tsp|tablespoon|teaspoon)\b'
            ]

            for pattern in unit_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    parsed_info["units"] = list(set(matches))  # 重複除去

            # HTMLから span 要素内の値を抽出
            span_pattern = r'<span[^>]*>([^<]+)</span>'
            span_matches = re.findall(span_pattern, html_content)
            if span_matches:
                parsed_info["span_values"] = span_matches

            return parsed_info

        except Exception as e:
            print(f"      ⚠️ ラベル解析エラー: {e}")
            return {}

    def test_option_selection(self):
        """各オプションを選択してデータ変化をテスト"""
        print("\n🧪 オプション選択テスト...")

        serving_options = self.analysis_data.get("serving_options", [])
        if not serving_options:
            print("❌ テストするオプションがありません")
            return False

        selection_results = []

        # 最初の3つのオプションをテスト
        for option in serving_options[:3]:
            try:
                print(f"\n  🎯 オプション{option['index']}を選択テスト...")
                print(f"    値: {option['radio_value']}")

                # ラジオボタンを探してクリック
                radio_xpath = f"//input[@type='radio' and @value='{option['radio_value']}']"
                radio_element = self.driver.find_element(By.XPATH, radio_xpath)

                # ラジオボタンの親のlabel要素をクリック
                label_element = radio_element.find_element(By.XPATH, "../../../..")
                label_element.click()
                time.sleep(2)

                # 選択後のページ状態を取得
                page_body = self.driver.find_element(By.TAG_NAME, 'body')
                page_text = page_body.text

                # データ変化を解析
                cal_matches = re.findall(r'(\d+(?:\.\d+)?)\s*cals?', page_text, re.IGNORECASE)
                weight_matches = re.findall(r'(\d+(?:\.\d+)?)\s*g(?:\s|$)', page_text)

                selection_result = {
                    "option_index": option['index'],
                    "option_value": option['radio_value'],
                    "calories_found": cal_matches[:5],  # 最初の5個
                    "weights_found": weight_matches[:5],  # 最初の5個
                    "was_selected": True
                }

                selection_results.append(selection_result)
                print(f"    📊 選択後: カロリー{len(cal_matches)}個, 重量{len(weight_matches)}個発見")

            except Exception as e:
                print(f"    ⚠️ オプション{option['index']}選択エラー: {e}")
                continue

        self.analysis_data["selection_results"] = selection_results
        return True

    def extract_complete_modal_html(self):
        """モーダル全体のHTMLを完全抽出"""
        print("\n📋 モーダル完全HTML抽出...")

        try:
            # モーダルダイアログを取得
            modal_dialog = self.driver.find_element(By.XPATH, "//div[@role='dialog']")
            complete_html = modal_dialog.get_attribute('outerHTML')

            # HTMLを解析しやすいように保存
            self.analysis_data["html_fragments"]["complete_modal"] = complete_html

            # ラジオボタンセクションのHTMLも個別取得
            radio_group = self.driver.find_element(By.XPATH, "//div[@role='radiogroup']")
            radio_html = radio_group.get_attribute('outerHTML')
            self.analysis_data["html_fragments"]["radio_group"] = radio_html

            print("✅ 完全HTML抽出完了")
            return True

        except Exception as e:
            print(f"❌ HTML抽出エラー: {e}")
            return False

    def save_analysis_results(self):
        """分析結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"deep_serving_analysis_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_data, f, ensure_ascii=False, indent=2)

        print(f"📄 分析結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def run_deep_analysis(self):
        """深度分析実行"""
        try:
            print("🔬 Select Serving深度分析開始")
            print("="*60)

            self.setup_driver()

            if not self.login_and_navigate():
                print("❌ ログイン・ナビゲーション失敗")
                return False

            if not self.open_serving_modal():
                print("❌ モーダルオープン失敗")
                return False

            # 深度分析実行
            self.analyze_radio_button_structure()
            self.test_option_selection()
            self.extract_complete_modal_html()

            # 結果保存
            filename = self.save_analysis_results()

            print("\n" + "="*60)
            print("🏁 深度分析完了")
            print("="*60)
            print(f"📊 分析結果ファイル: {filename}")
            print(f"🎯 serving オプション数: {len(self.analysis_data.get('serving_options', []))}個")
            print(f"🧪 選択テスト数: {len(self.analysis_data.get('selection_results', []))}個")

            return True

        except Exception as e:
            print(f"❌ 深度分析エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    analyzer = DeepServingAnalyzer()
    analyzer.run_deep_analysis()