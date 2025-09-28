#!/usr/bin/env python3
"""
Select Servingモーダルの実態調査スクリプト
モーダル内の構造、要素、データ形式を詳細に分析
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from config import config

class ServingModalInvestigator:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.investigation_data = {
            "timestamp": datetime.now().isoformat(),
            "modal_structure": {},
            "dropdown_options": [],
            "serving_data": [],
            "html_snapshots": {}
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

    def navigate_to_test_food(self):
        """調査用食材に移動（2番目の食材）"""
        print("🔍 調査用食材に移動...")

        # My Foodsページに移動
        my_foods_url = f"{config.BASE_URL}/meals.do#ff"
        self.driver.get(my_foods_url)
        time.sleep(config.REQUEST_DELAY)

        # カテゴリナビゲーション
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

        # 2番目の食材を選択
        food_list_items = self.driver.find_elements(
            By.XPATH,
            "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
        )

        if len(food_list_items) >= 2:
            second_food = food_list_items[1]
            food_name = second_food.text
            print(f"🎯 調査対象食材: {food_name[:50]}...")
            self.investigation_data["food_name"] = food_name
            second_food.click()
            time.sleep(config.REQUEST_DELAY * 2)
            return True
        else:
            print("❌ 調査用食材が見つかりません")
            return False

    def open_serving_modal(self):
        """Select Servingモーダルを開く"""
        try:
            print("🔍 Select Servingモーダルを開く...")

            # Amount eaten要素を検索
            amount_eaten_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Amount eaten')]")

            if not amount_eaten_elements:
                print("❌ Amount eaten要素が見つかりません")
                return False

            # 表示されている要素を取得
            amount_element = None
            for element in amount_eaten_elements:
                if element.is_displayed():
                    amount_element = element
                    break

            if not amount_element:
                print("❌ 表示されているAmount eaten要素が見つかりません")
                return False

            # 親レベル2でクリック
            parent_level2 = amount_element.find_element(By.XPATH, "../..")

            # 既存モーダルを閉じる
            self._close_any_open_modals()
            time.sleep(1)

            # クリック実行
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_level2)
            time.sleep(1)
            parent_level2.click()
            time.sleep(3)

            # モーダルが開いたかチェック
            if self._is_select_serving_modal_open():
                print("✅ Select Servingモーダルが開きました！")
                return True
            else:
                print("❌ Select Servingモーダルが開きませんでした")
                return False

        except Exception as e:
            print(f"❌ モーダルオープンエラー: {e}")
            return False

    def investigate_modal_structure(self):
        """モーダルの構造を詳細調査"""
        print("\n🔍 モーダル構造の詳細調査開始...")

        try:
            # 1. モーダル全体のHTMLを取得
            print("📋 1. モーダル全体のHTML構造を取得...")
            modal_elements = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'modal') or contains(@class, 'Modal') or contains(@class, 'dialog') or contains(@class, 'Dialog')]")

            modal_html = ""
            for i, modal in enumerate(modal_elements):
                if modal.is_displayed():
                    try:
                        html = modal.get_attribute('outerHTML')
                        modal_html = html[:2000]  # 最初の2000文字
                        print(f"  ✅ モーダル{i+1}: {modal.tag_name}, classes: {modal.get_attribute('class')}")
                        break
                    except:
                        continue

            self.investigation_data["html_snapshots"]["modal_html"] = modal_html

            # 2. ドロップダウン要素の調査
            print("📋 2. ドロップダウン要素の調査...")
            dropdown_patterns = [
                "//*[contains(@class, 'select') or contains(@class, 'Select')]",
                "//*[contains(@class, 'dropdown') or contains(@class, 'Dropdown')]",
                "//select",
                "//input[@type='text' and contains(@class, 'select')]"
            ]

            dropdowns_found = []
            for pattern in dropdown_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            dropdown_info = {
                                "tag": element.tag_name,
                                "classes": element.get_attribute('class'),
                                "id": element.get_attribute('id'),
                                "text": element.text[:100],
                                "xpath_pattern": pattern
                            }
                            dropdowns_found.append(dropdown_info)
                            print(f"  🎯 ドロップダウン発見: {element.tag_name} - {element.get_attribute('class')}")
                except:
                    continue

            self.investigation_data["modal_structure"]["dropdowns"] = dropdowns_found

            # 3. serving情報を含む要素の調査
            print("📋 3. serving情報要素の調査...")
            serving_patterns = [
                "//*[contains(text(), 'cal') or contains(text(), 'Cal')]",
                "//*[contains(text(), 'g') or contains(text(), 'gram')]",
                "//*[contains(text(), 'oz')]",
                "//*[contains(text(), 'cup')]",
                "//*[contains(text(), 'ml')]",
                "//*[contains(text(), 'lb')]",
                "//*[contains(text(), 'tbsp') or contains(text(), 'tablespoon')]",
                "//*[contains(text(), 'tsp') or contains(text(), 'teaspoon')]"
            ]

            serving_elements = []
            for pattern in serving_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            element_info = {
                                "tag": element.tag_name,
                                "text": element.text.strip(),
                                "classes": element.get_attribute('class'),
                                "xpath_pattern": pattern,
                                "location": element.location,
                                "size": element.size
                            }
                            serving_elements.append(element_info)
                            print(f"  📊 serving要素: '{element.text.strip()[:50]}...'")
                except:
                    continue

            self.investigation_data["modal_structure"]["serving_elements"] = serving_elements

            # 4. クリック可能要素の調査
            print("📋 4. クリック可能要素の調査...")
            clickable_elements = self.driver.find_elements(By.XPATH, "//*[@onclick or @click or contains(@class, 'click') or contains(@class, 'button') or contains(@class, 'option')]")

            clickable_info = []
            for element in clickable_elements:
                if element.is_displayed():
                    try:
                        info = {
                            "tag": element.tag_name,
                            "text": element.text.strip()[:50],
                            "classes": element.get_attribute('class'),
                            "onclick": element.get_attribute('onclick'),
                            "location": element.location
                        }
                        clickable_info.append(info)
                        print(f"  🔘 クリック可能: {element.tag_name} - '{element.text.strip()[:30]}...'")
                    except:
                        continue

            self.investigation_data["modal_structure"]["clickable_elements"] = clickable_info[:10]  # 最初の10個

            print(f"✅ モーダル構造調査完了: ドロップダウン{len(dropdowns_found)}個, serving要素{len(serving_elements)}個")
            return True

        except Exception as e:
            print(f"❌ モーダル構造調査エラー: {e}")
            return False

    def investigate_dropdown_behavior(self):
        """ドロップダウンの動作を調査"""
        print("\n🔍 ドロップダウン動作調査...")

        try:
            # Material-UIのSelectコンポーネントを探す
            select_patterns = [
                "//div[contains(@class, 'MuiSelect')]",
                "//div[contains(@class, 'select')]//input",
                "//*[@role='button' and contains(@aria-haspopup, 'listbox')]",
                "//*[@role='combobox']"
            ]

            dropdown_found = False
            for pattern in select_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            print(f"  🎯 ドロップダウン候補発見: {element.tag_name} - {element.get_attribute('class')}")

                            # クリックしてオプションを表示
                            try:
                                element.click()
                                time.sleep(2)

                                # オプション要素を探す
                                option_patterns = [
                                    "//li[@role='option']",
                                    "//*[contains(@class, 'option')]",
                                    "//ul//li",
                                    "//*[@role='menuitem']"
                                ]

                                options_found = []
                                for opt_pattern in option_patterns:
                                    try:
                                        option_elements = self.driver.find_elements(By.XPATH, opt_pattern)
                                        for opt in option_elements:
                                            if opt.is_displayed() and opt.text.strip():
                                                option_info = {
                                                    "text": opt.text.strip(),
                                                    "tag": opt.tag_name,
                                                    "classes": opt.get_attribute('class'),
                                                    "value": opt.get_attribute('value') or opt.get_attribute('data-value')
                                                }
                                                options_found.append(option_info)
                                                print(f"    📋 オプション: '{opt.text.strip()}'")
                                    except:
                                        continue

                                self.investigation_data["dropdown_options"] = options_found
                                dropdown_found = True

                                # ESCで閉じる
                                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                                time.sleep(1)
                                break

                            except Exception as e:
                                print(f"    ⚠️ ドロップダウンクリックエラー: {e}")
                                continue

                    if dropdown_found:
                        break

                except:
                    continue

            if not dropdown_found:
                print("  ❌ 操作可能なドロップダウンが見つかりませんでした")

            return dropdown_found

        except Exception as e:
            print(f"❌ ドロップダウン調査エラー: {e}")
            return False

    def test_option_selection(self):
        """オプション選択時のデータ変化を調査"""
        print("\n🔍 オプション選択時のデータ変化調査...")

        try:
            options = self.investigation_data.get("dropdown_options", [])
            if not options:
                print("❌ 調査するオプションがありません")
                return False

            serving_data_samples = []

            # 最初の3つのオプションをテスト
            for i, option in enumerate(options[:3]):
                print(f"  🧪 オプション{i+1}をテスト: '{option['text']}'")

                try:
                    # ドロップダウンを再度開く
                    select_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'MuiSelect')] | //*[@role='button' and contains(@aria-haspopup, 'listbox')]")
                    select_element.click()
                    time.sleep(1)

                    # 該当オプションをクリック
                    option_element = self.driver.find_element(By.XPATH, f"//li[contains(text(), '{option['text']}')]")
                    option_element.click()
                    time.sleep(2)

                    # 選択後のページ内容を取得
                    page_text = self.driver.find_element(By.TAG_NAME, 'body').text

                    # カロリーと重量データを抽出
                    import re
                    cal_matches = re.findall(r'(\d+(?:\.\d+)?)\s*cals?', page_text, re.IGNORECASE)
                    weight_matches = re.findall(r'(\d+(?:\.\d+)?)\s*g(?:\s|$)', page_text)

                    sample_data = {
                        "option_text": option['text'],
                        "calories_found": cal_matches,
                        "weights_found": weight_matches,
                        "selection_index": i
                    }
                    serving_data_samples.append(sample_data)

                    print(f"    📊 結果: カロリー{len(cal_matches)}個, 重量{len(weight_matches)}個")

                except Exception as e:
                    print(f"    ⚠️ オプション{i+1}選択エラー: {e}")
                    continue

            self.investigation_data["serving_data"] = serving_data_samples
            return True

        except Exception as e:
            print(f"❌ オプション選択調査エラー: {e}")
            return False

    def _close_any_open_modals(self):
        """開いているモーダルを閉じる"""
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
        except:
            pass

    def _is_select_serving_modal_open(self):
        """Select Servingモーダルが開いているかチェック"""
        try:
            modal_indicators = [
                "//*[contains(text(), 'Select Serving')]",
                "//*[contains(text(), 'oz') and contains(text(), 'cal')]",
                "//*[contains(text(), 'container') and contains(text(), 'cal')]"
            ]

            for pattern in modal_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            return True
                except:
                    continue
            return False

        except Exception as e:
            print(f"⚠️ モーダル確認エラー: {e}")
            return False

    def save_investigation_results(self):
        """調査結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"serving_modal_investigation_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.investigation_data, f, ensure_ascii=False, indent=2)

        print(f"📄 調査結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def run_investigation(self):
        """調査実行"""
        try:
            print("🔍 Select Servingモーダル実態調査開始")
            print("="*60)

            self.setup_driver()

            if not self.login_to_mynetdiary():
                print("❌ ログインに失敗しました")
                return False

            if not self.navigate_to_test_food():
                print("❌ 調査用食材への移動に失敗")
                return False

            if not self.open_serving_modal():
                print("❌ Select Servingモーダルが開けませんでした")
                return False

            # 詳細調査実行
            print("\n" + "="*60)
            print("📋 詳細調査フェーズ")
            print("="*60)

            self.investigate_modal_structure()
            self.investigate_dropdown_behavior()
            self.test_option_selection()

            # 結果保存
            filename = self.save_investigation_results()

            print("\n" + "="*60)
            print("🏁 調査完了")
            print("="*60)
            print(f"📊 調査結果ファイル: {filename}")
            print(f"🎯 発見されたドロップダウン: {len(self.investigation_data['modal_structure'].get('dropdowns', []))}個")
            print(f"📋 発見されたオプション: {len(self.investigation_data.get('dropdown_options', []))}個")
            print(f"🧪 テストしたserving: {len(self.investigation_data.get('serving_data', []))}個")

            return True

        except Exception as e:
            print(f"❌ 調査実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    investigator = ServingModalInvestigator()
    investigator.run_investigation()