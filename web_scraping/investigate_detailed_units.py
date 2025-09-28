#!/usr/bin/env python3
"""
MyNetDiaryで「3 more servings」をクリックして詳細な単位情報を取得するスクリプト
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
    from selenium.webdriver.common.action_chains import ActionChains
except ImportError:
    print("❌ Seleniumがインストールされていません: pip install selenium")
    sys.exit(1)

from config import config

class DetailedUnitsInvestigator:
    """詳細単位調査スクレイパー"""

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

    def investigate_detailed_serving_options(self) -> Dict[str, Any]:
        """詳細なサービング選択オプションを調査"""
        try:
            investigation_data = {
                'food_name': 'Almond milk unsweetened fortified',
                'investigation_time': datetime.now().isoformat(),
                'step_by_step_process': [],
                'serving_options_found': {},
                'more_servings_clicked': False,
                'final_serving_data': {}
            }

            print("🔍 詳細なサービング選択オプションを調査中...")

            # ステップ1: 初期の表示を確認
            print("  📋 ステップ1: 初期表示の確認")
            initial_text = self.driver.find_element(By.TAG_NAME, "body").text
            investigation_data['step_by_step_process'].append({
                'step': 1,
                'description': '初期表示確認',
                'content': initial_text[:500]  # 最初の500文字
            })

            # ステップ2: Select Servingエリアを探す
            print("  📋 ステップ2: Select Servingエリアの探索")
            serving_selectors = []

            # 様々なパターンでSelect Serving要素を探す
            serving_patterns = [
                "//div[contains(text(), 'Select Serving')]",
                "//span[contains(text(), 'Select Serving')]",
                "//label[contains(text(), 'Select Serving')]",
                "//*[contains(text(), 'serving') and contains(@class, 'select')]",
                "//*[contains(@class, 'serving-selector')]",
                "//select",
                "//div[contains(@class, 'MuiSelect')]"
            ]

            for pattern in serving_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    if elements:
                        print(f"    ✅ 発見: {pattern} ({len(elements)}個)")
                        for i, elem in enumerate(elements):
                            try:
                                print(f"      要素{i+1}: {elem.text[:100]}")
                                serving_selectors.append(elem)
                            except:
                                print(f"      要素{i+1}: テキスト取得不可")
                except Exception as e:
                    continue

            investigation_data['step_by_step_process'].append({
                'step': 2,
                'description': 'Select Servingエリア探索',
                'found_elements': len(serving_selectors)
            })

            # ステップ3: "3 more servings"ボタンを探してクリック
            print("  📋 ステップ3: '3 more servings'ボタンの探索とクリック")
            more_servings_patterns = [
                "//*[contains(text(), 'more serving')]",
                "//*[contains(text(), 'more Serving')]",
                "//*[contains(text(), '3 more')]",
                "//button[contains(text(), 'more')]",
                "//span[contains(text(), 'more')]",
                "//div[contains(text(), 'more')]"
            ]

            more_servings_clicked = False
            for pattern in more_servings_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        try:
                            print(f"    🎯 発見: '{element.text}' - クリック試行")

                            # スクロールして要素を表示
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)

                            # クリック試行
                            element.click()
                            time.sleep(3)  # より長く待機
                            more_servings_clicked = True

                            investigation_data['more_servings_clicked'] = True
                            investigation_data['step_by_step_process'].append({
                                'step': 3,
                                'description': 'more servingsボタンクリック成功',
                                'clicked_text': element.text
                            })

                            print(f"    ✅ '{element.text}'クリック成功")
                            break
                        except Exception as e:
                            print(f"    ⚠️ クリック失敗: {e}")
                            continue

                    if more_servings_clicked:
                        break
                except Exception as e:
                    continue

            # ステップ4: クリック後の状態を調査
            if more_servings_clicked:
                print("  📋 ステップ4: クリック後の詳細情報取得")
                time.sleep(2)

                # 現在のページの全テキストを取得
                current_text = self.driver.find_element(By.TAG_NAME, "body").text
                investigation_data['step_by_step_process'].append({
                    'step': 4,
                    'description': 'クリック後の全テキスト',
                    'content': current_text[:1000]  # 最初の1000文字
                })

                # Select要素を再度探索
                print("    🔍 Select要素の再探索...")
                new_selects = self.driver.find_elements(By.TAG_NAME, "select")
                for i, select in enumerate(new_selects):
                    try:
                        select_obj = Select(select)
                        options = [opt.text.strip() for opt in select_obj.options if opt.text.strip()]
                        print(f"      Select{i+1}: {options}")

                        investigation_data['serving_options_found'][f'select_{i+1}'] = options

                        # 各オプションをクリックして詳細情報を取得
                        for option_text in options:
                            if option_text and option_text != "Select Serving":
                                try:
                                    print(f"        📊 {option_text}を選択中...")
                                    select_obj.select_by_visible_text(option_text)
                                    time.sleep(2)

                                    # 選択後のテキストを取得
                                    current_serving_text = self.driver.find_element(By.TAG_NAME, "body").text

                                    # カロリーと重量情報を抽出
                                    serving_info = self.extract_serving_info(current_serving_text, option_text)
                                    if serving_info:
                                        investigation_data['final_serving_data'][option_text] = serving_info
                                        print(f"          ✅ {option_text}: {serving_info}")

                                except Exception as e:
                                    print(f"          ⚠️ {option_text}選択エラー: {e}")
                                    continue
                    except Exception as e:
                        print(f"      Select{i+1}処理エラー: {e}")
                        continue

            # ステップ5: 最終結果まとめ
            investigation_data['summary'] = {
                'more_servings_clicked': more_servings_clicked,
                'total_serving_options': len(investigation_data['final_serving_data']),
                'serving_options_list': list(investigation_data['final_serving_data'].keys())
            }

            return investigation_data

        except Exception as e:
            print(f"❌ 詳細調査エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'investigation_time': datetime.now().isoformat()
            }

    def extract_serving_info(self, text: str, unit: str) -> Dict:
        """テキストからサービング情報を抽出"""
        try:
            lines = text.split('\n')

            # カロリー情報を探す
            calories = None
            weight = None

            for line in lines:
                line = line.strip()

                # "30cals / 245 g"のようなパターンを探す
                if 'cals' in line and '/' in line and 'g' in line:
                    parts = line.split('/')
                    if len(parts) == 2:
                        # カロリー部分
                        cal_part = parts[0].strip()
                        if 'cals' in cal_part:
                            try:
                                calories = int(cal_part.replace('cals', '').strip())
                            except:
                                pass

                        # 重量部分
                        weight_part = parts[1].strip()
                        if 'g' in weight_part:
                            try:
                                weight = float(weight_part.replace('g', '').strip())
                            except:
                                pass

                # "cup 30cals / 245 g"のような行を探す
                if unit.lower() in line.lower() and 'cals' in line and 'g' in line:
                    print(f"          📊 マッチした行: {line}")
                    # さらに詳細な解析を実行
                    parts = line.split()
                    for part in parts:
                        if 'cals' in part:
                            try:
                                calories = int(part.replace('cals', '').strip())
                            except:
                                pass
                        if part.endswith('g') and part[:-1].replace('.', '').isdigit():
                            try:
                                weight = float(part[:-1])
                            except:
                                pass

            if calories is not None and weight is not None:
                return {
                    'calories': calories,
                    'weight_g': weight,
                    'extraction_success': True
                }
            else:
                return {
                    'calories': None,
                    'weight_g': None,
                    'extraction_success': False,
                    'raw_text_sample': text[:200]
                }

        except Exception as e:
            return {
                'error': str(e),
                'extraction_success': False
            }

    def save_investigation_results(self, data: Dict) -> str:
        """調査結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"web_scraping/data/detailed_units_investigation_{timestamp}.json"

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
            print("🚀 詳細単位調査開始")

            self.setup_driver()

            if not self.login():
                print("❌ ログインに失敗しました")
                return

            if not self.navigate_to_food():
                print("❌ 食材移動に失敗しました")
                return

            investigation_data = self.investigate_detailed_serving_options()

            if investigation_data:
                filename = self.save_investigation_results(investigation_data)
                print(f"\n📊 詳細調査完了: {filename}")

                # 要約を表示
                if 'summary' in investigation_data:
                    summary = investigation_data['summary']
                    print(f"\n🎯 調査要約:")
                    print(f"  📋 more servingsクリック: {summary.get('more_servings_clicked', False)}")
                    print(f"  📋 発見されたサービング選択肢: {summary.get('total_serving_options', 0)}個")

                    if summary.get('serving_options_list'):
                        print(f"  📋 サービング選択肢:")
                        for option in summary['serving_options_list']:
                            info = investigation_data['final_serving_data'].get(option, {})
                            if info.get('extraction_success'):
                                print(f"    - {option}: {info['calories']}cals / {info['weight_g']}g")
                            else:
                                print(f"    - {option}: 詳細情報取得失敗")
            else:
                print("❌ 調査データが取得できませんでした")

        except Exception as e:
            print(f"❌ 実行エラー: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        print("🏁 詳細調査終了")

if __name__ == "__main__":
    investigator = DetailedUnitsInvestigator()
    investigator.run()