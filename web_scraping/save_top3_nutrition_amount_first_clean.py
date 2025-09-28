#!/usr/bin/env python3
"""
MyNetDiaryから最初の3項目の栄養情報を保存するスクリプト
"""

import json
import time
import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("❌ Seleniumがインストールされていません: pip install selenium")
    sys.exit(1)

from config import config

class Top3NutritionScraper:
    """最初の3項目の栄養情報を抽出するスクレイパー"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.collected_foods = []

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

    def navigate_to_category(self, category_name: str = "Dairy, Dairy Substitutes & Egg") -> bool:
        """指定カテゴリに移動"""
        try:
            print(f"🔍 {category_name}カテゴリに移動中...")

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

            # 指定カテゴリをクリック
            category_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//span[text()='{category_name}']"))
            )
            category_button.click()
            time.sleep(config.REQUEST_DELAY)

            print(f"✅ {category_name}カテゴリ移動成功")
            return True

        except Exception as e:
            print(f"❌ カテゴリ移動エラー: {str(e)}")
            return False

    def get_top3_foods(self) -> List[Dict]:
        """最初の3つの食材情報を取得"""
        try:
            print("🍲 最初の3つの食材を取得中...")
            top3_foods = []

            # 3つの食材を順番に処理
            for i in range(3):
                try:
                    # 毎回食材リストを再取得（stale element エラー回避）
                    food_list_items = self.driver.find_elements(
                        By.XPATH,
                        "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
                    )

                    if len(food_list_items) <= i:
                        print(f"❌ 食材 {i+1} が見つかりません（利用可能: {len(food_list_items)}個）")
                        break

                    food_item = food_list_items[i]
                    food_text = food_item.text.strip()
                    print(f"🎯 食材 {i+1}: {food_text[:50]}...")

                    # 食材をクリック
                    food_item.click()
                    time.sleep(config.REQUEST_DELAY * 2)

                    # 栄養情報を抽出
                    nutrition_data = self.extract_nutrition_info(food_text)
                    nutrition_data['list_index'] = i + 1
                    nutrition_data['preview_text'] = food_text

                    top3_foods.append(nutrition_data)
                    print(f"✅ 食材 {i+1} データ取得完了")

                    # 最後の食材でなければカテゴリに戻る
                    if i < 2:  # 0, 1 の場合のみ戻る（2は最後なので戻らない）
                        if not self._return_to_food_list():
                            print(f"❌ 食材リストへの戻り処理に失敗")
                            break

                except Exception as e:
                    print(f"❌ 食材 {i+1} 処理エラー: {str(e)}")
                    
                    # エラー時も可能であればカテゴリに戻る
                    try:
                        if i < 2:  # 最後でなければ戻る処理を試行
                            self._return_to_food_list()
                    except:
                        pass
                    continue

            return top3_foods

        except Exception as e:
            print(f"❌ 食材取得エラー: {str(e)}")
            return []
    
    def _return_to_food_list(self) -> bool:
        """食材リストに戻る処理（改良版）"""
        print("🔄 食材完了後、食材リストに戻ります...")
        
        # まずモーダルを確実に閉じる
        self.close_modal_if_open()
        
        # 複数の戻り方法を試行
        return_methods = [
            self._method_browser_back,    # 最も確実な方法を最初に
            self._method_fresh_navigation, # フレッシュナビゲーションを2番目に
            self._method_back_button,     # バックボタンは3番目
            self._method_category_reclick  # カテゴリ再クリックは最後
        ]
        
        for i, method in enumerate(return_methods, 1):
            try:
                print(f"    🔄 方法{i}を試行中...")
                method()
                
                # 成功の確認：食材リストが表示されているか
                if self._verify_food_list_visible():
                    print(f"    ✅ 方法{i}で戻り処理成功")
                    return True
                    
            except Exception as e:
                print(f"    ❌ 方法{i}失敗: {e}")
                continue
        
        print("    ❌ 全ての戻り方法が失敗しました")
        return False
    
    def _method_back_button(self):
        """方法1: BACK TO STAPLE FOODSボタンを使用"""
        # より多くのパターンでバックボタンを検索
        back_patterns = [
            "//span[contains(text(), 'BACK TO STAPLE FOODS')]",
            "//button[contains(text(), 'BACK')]", 
            "//span[contains(text(), 'BACK')]",
            "//*[contains(text(), 'BACK') and contains(text(), 'STAPLE')]",
            "//*[contains(text(), 'BACK')]//ancestor::button",
            "//*[contains(@class, 'back') or contains(@class, 'return')]"
        ]
        
        button_found = False
        for pattern in back_patterns:
            try:
                back_elements = self.driver.find_elements(By.XPATH, pattern)
                for back_button in back_elements:
                    if back_button.is_displayed() and back_button.is_enabled():
                        print(f"        🎯 バックボタン発見: {pattern}")
                        back_button.click()
                        time.sleep(config.REQUEST_DELAY)
                        button_found = True
                        break
                if button_found:
                    break
            except:
                continue
        
        if not button_found:
            raise Exception("バックボタンが見つかりません")
        
        # カテゴリボタンをクリック
        try:
            category_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Dairy, Dairy Substitutes & Egg')]"))
            )
            category_button.click()
            time.sleep(config.REQUEST_DELAY)
        except:
            # カテゴリボタンが見つからない場合は、そのまま続行
            pass
    
    def _method_browser_back(self):
        """方法2: ブラウザの戻るボタン（改良版）"""
        # 現在のURLを記録
        current_url = self.driver.current_url
        
        # ブラウザバック実行
        self.driver.back()
        time.sleep(3)
        
        # URLが変わったかチェック
        new_url = self.driver.current_url
        if new_url == current_url:
            # URLが変わらない場合は、もう一度バック
            self.driver.back()
            time.sleep(3)
        
        # カテゴリページに移動が必要な場合
        if "meals.do" not in self.driver.current_url:
            self.navigate_to_category("Dairy, Dairy Substitutes & Egg")
        else:
            # 既にmealsページにいる場合、カテゴリを再クリック
            try:
                category_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Dairy, Dairy Substitutes & Egg')]"))
                )
                category_button.click()
                time.sleep(config.REQUEST_DELAY)
            except:
                pass
    
    def _method_category_reclick(self):
        """方法3: カテゴリを直接再クリック"""
        category_patterns = [
            "//span[contains(text(), 'Dairy, Dairy Substitutes & Egg')]",
            "//span[contains(@class, 'MuiListItemText-primary') and contains(text(), 'Dairy')]",
            "//*[contains(text(), 'Dairy') and contains(text(), 'Egg')]",
        ]
        
        for pattern in category_patterns:
            try:
                category_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, pattern)))
                category_element.click()
                time.sleep(config.REQUEST_DELAY)
                return
            except:
                continue
        
        raise Exception("カテゴリボタンが見つかりません")
    
    def _method_fresh_navigation(self):
        """方法4: フレッシュナビゲーション"""
        if not self.navigate_to_category("Dairy, Dairy Substitutes & Egg"):
            raise Exception("カテゴリへの再ナビゲーション失敗")
    
    def _verify_food_list_visible(self) -> bool:
        """食材リストが表示されているかを確認（改良版）"""
        try:
            # 複数のパターンで食材リスト要素を検索
            food_list_patterns = [
                "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]",
                "//div[contains(@class, 'MuiBox-root')]/div[contains(@class, 'MuiTypography-root')]",
                "//*[contains(text(), 'cals') and contains(text(), ',')]",
                "//li//div[contains(text(), 'cals')]"
            ]
            
            max_food_count = 0
            visible_foods = []
            
            for pattern in food_list_patterns:
                try:
                    food_elements = self.driver.find_elements(By.XPATH, pattern)
                    current_visible = [el for el in food_elements if el.is_displayed()]
                    
                    if len(current_visible) > max_food_count:
                        max_food_count = len(current_visible)
                        visible_foods = current_visible
                except:
                    continue
            
            if max_food_count >= 3:
                print(f"    📊 食材リスト確認: {max_food_count}個の食材が表示されています")
                return True
            else:
                print(f"    ⚠️ 食材リスト不十分: {max_food_count}個のみ表示")
                return False
                
        except Exception as e:
            print(f"    ❌ 食材リスト確認エラー: {e}")
            return False
    
        time.sleep(config.REQUEST_DELAY)
    
    def _method_browser_back(self):
        """方法2: ブラウザの戻るボタン"""
        self.driver.back()
        time.sleep(3)
        # 必要であればカテゴリを再クリック
        try:
            category_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Dairy, Dairy Substitutes & Egg']"))
            )
            category_button.click()
            time.sleep(config.REQUEST_DELAY)
        except:
            pass
    
    def _method_category_reclick(self):
        """方法3: カテゴリを直接再クリック"""
        category_selector = "//span[contains(@class, 'MuiListItemText-primary') and contains(text(), 'Dairy')]"
        category_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, category_selector)))
        category_element.click()
        time.sleep(config.REQUEST_DELAY)
    
    def _method_fresh_navigation(self):
        """方法4: フレッシュナビゲーション"""
        if not self.navigate_to_category():
            raise Exception("カテゴリへの再ナビゲーション失敗")
    
    def _verify_food_list_visible(self) -> bool:
        """食材リストが表示されているかを確認"""
        try:
            # 食材リスト要素の存在を確認
            food_elements = self.driver.find_elements(
                By.XPATH, 
                "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
            )
            visible_foods = [el for el in food_elements if el.is_displayed()]
            
            if len(visible_foods) >= 3:
                print(f"    📊 食材リスト確認: {len(visible_foods)}個の食材が表示されています")
                return True
            else:
                print(f"    ⚠️ 食材リスト不十分: {len(visible_foods)}個のみ表示")
                return False
                
        except Exception as e:
            print(f"    ❌ 食材リスト確認エラー: {e}")
            return False

    def click_more_servings_button(self) -> bool:
        """'X more servings'ボタンをクリック（確定版）"""
        print("  🔍 'X more servings'ボタンを探索中...")
        
        # より多くのパターンでボタンを検索
        more_servings_patterns = [
            # 数字 + "more servings" の組み合わせ
            "//*[contains(text(), 'more servings')]",
            "//*[contains(text(), 'more serving')]",  # 単数形もチェック
            # 具体的な数字パターン
            "//*[contains(text(), '3 more servings')]",
            "//*[contains(text(), '4 more servings')]", 
            "//*[contains(text(), '5 more servings')]",
            "//*[contains(text(), '6 more servings')]",
            "//*[contains(text(), '7 more servings')]",
            "//*[contains(text(), '8 more servings')]",
            # クラス名やその他の属性
            "//*[contains(@class, 'serving') or contains(@class, 'more')]",
            "//button[contains(text(), 'more')]",
            "//span[contains(text(), 'more')]",
            "//div[contains(text(), 'more')]"
        ]
        
        # 最大3回の試行で確実に検出
        max_attempts = 3
        
        for attempt in range(max_attempts):
            print(f"    🔄 試行 {attempt + 1}: ボタン検索中...")
            
            # 少し待機してページが安定するのを待つ
            time.sleep(2)
            
            for i, pattern in enumerate(more_servings_patterns):
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.text.strip()
                            
                            # "more servings" を含む要素を優先
                            if "more serving" in element_text.lower():
                                print(f"    🎯 '{element_text}'をクリック中...")
                                try:
                                    element.click()
                                    print(f"    ✅ '{element_text}'クリック成功")
                                    time.sleep(3)  # クリック後の処理待ち
                                    return True
                                except Exception as e:
                                    print(f"    ⚠️ クリック失敗: {e}")
                                    continue
                    
                    # デバッグ: どんな要素が見つかったか表示
                    if elements and attempt == 0:  # 最初の試行でのみデバッグ表示
                        visible_texts = [el.text.strip() for el in elements if el.is_displayed() and el.text.strip()]
                        if visible_texts:
                            print(f"    🔍 パターン{i+1}で発見されたテキスト: {visible_texts[:3]}")  # 最初の3個のみ
                            
                except Exception as e:
                    continue
            
            print(f"    ⏳ 試行 {attempt + 1}: ボタンが見つかりません、再試行中...")
        
        # 全てのパターンで見つからない場合のデバッグ情報
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            lines_with_more = [line.strip() for line in page_text.split('\n') if 'more' in line.lower()]
            if lines_with_more:
                print(f"    🔍 ページ内の'more'を含む行: {lines_with_more[:5]}")  # 最初の5行のみ
            else:
                print("    🔍 ページ内に'more'を含む行が見つかりません")
                
            # より広範囲の検索
            all_buttons = self.driver.find_elements(By.XPATH, "//button | //span | //div[@role='button'] | //*[@onclick]")
            clickable_texts = []
            for btn in all_buttons:
                try:
                    if btn.is_displayed() and btn.text.strip():
                        text = btn.text.strip()
                        if any(keyword in text.lower() for keyword in ['serving', 'more', 'show', 'expand']):
                            clickable_texts.append(text)
                except:
                    continue
            
            if clickable_texts:
                print(f"    🔍 クリック可能な関連要素: {clickable_texts[:5]}")
                
        except Exception as e:
            print(f"    ⚠️ デバッグ情報取得エラー: {e}")
        
        print("    ❌ 'X more servings'ボタンが見つかりません")
        return False

    def extract_serving_section(self, text: str) -> List[str]:
        """テキストからSelect Serving部分を抽出（詳細デバッグ版）"""
        try:
            print("    🔍 詳細デバッグ: 全テキストからSelect Serving部分を抽出中...")
            lines = text.split('\n')
            serving_lines = []
            in_serving_section = False

            # デバッグ: Select Servingの位置を確認
            select_serving_found = False
            cancel_found = False
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if 'Select Serving' in line_stripped:
                    select_serving_found = True
                    print(f"      ✅ 'Select Serving'発見: 行{i+1}: '{line_stripped}'")
                if line_stripped == 'CANCEL':
                    cancel_found = True
                    print(f"      ✅ 'CANCEL'発見: 行{i+1}: '{line_stripped}'")

            print(f"      📊 Select Serving: {select_serving_found}, CANCEL: {cancel_found}")

            # 実際の抽出処理
            for i, line in enumerate(lines):
                line = line.strip()

                # Select Servingセクションの開始
                if 'Select Serving' in line:
                    in_serving_section = True
                    print(f"      📋 セクション開始: 行{i+1}")
                    continue

                # CANCELでセクション終了
                if line == 'CANCEL' and in_serving_section:
                    print(f"      📋 セクション終了: 行{i+1}")
                    break

                # セクション内の行を収集
                if in_serving_section and line:
                    # "unit Xcals / Yg"パターンの行のみ収集
                    if 'cals' in line and '/' in line and 'g' in line:
                        serving_lines.append(line)
                        print(f"        ✅ 単位行発見: '{line}'")
                    elif len(line) > 2:  # デバッグ用
                        print(f"        ⚠️ パターン不一致: '{line}'")

            print(f"    📊 抽出された単位行: {len(serving_lines)}個")
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

    def extract_complete_units_data(self) -> Dict[str, Dict]:
        """完全な単位データを抽出（Amount eaten単位選択版）"""
        try:
            print("  🔍 完全な単位データを抽出中...")
            print("  📋 Amount eaten セクションの単位選択を使用...")

            # ステップ1: Amount eaten セクションの単位ドロップダウンを探す
            units_data = self._extract_units_from_amount_section()
            
            if units_data and len(units_data) > 2:  # 基準単位とgramより多い場合
                print(f"    ✅ Amount eaten単位選択で{len(units_data)}個の単位を取得")
                return units_data
            
            # ステップ2: フォールバック - "X more servings"ボタンを試す
            print("  🔄 フォールバック: 'X more servings'ボタンを試行...")
            if self.click_more_servings_button():
                # Select Servingモーダルからデータを抽出
                return self._extract_units_from_select_serving_modal()
            
            print("  ⚠️ 完全単位データ取得失敗")
            return {}

        except Exception as e:
            print(f"  ❌ 完全単位データ抽出エラー: {e}")
            return {}

    def _extract_units_from_amount_section(self) -> Dict[str, Dict]:
        """Amount eatenセクションから単位データを抽出（新しい正確なserving情報取得方法）"""
        try:
            print("    🔍 Amount eaten エリア構造分析...")

            # 🔽 まず栄養素を折りたたむ（重要！）
            self._collapse_all_nutrients()

            # Amount eaten 要素を検索
            amount_eaten_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Amount eaten')]")

            if not amount_eaten_elements:
                print("    ❌ Amount eaten 要素が見つかりません")
                raise Exception("Amount eaten要素が見つかりません")

            print(f"    📋 Amount eaten 要素数: {len(amount_eaten_elements)}")

            # 表示されているAmount eaten要素を取得
            amount_element = None
            for element in amount_eaten_elements:
                if element.is_displayed():
                    amount_element = element
                    break

            if not amount_element:
                print("    ❌ 表示されているAmount eaten 要素が見つかりません")
                raise Exception("表示されているAmount eaten要素が見つかりません")

            print(f"    ✅ Amount eaten 要素発見: {amount_element.tag_name}")

            # 親レベル2を取得
            try:
                parent_level2 = amount_element.find_element(By.XPATH, "../..")
                size = parent_level2.size
                text = parent_level2.text

                print(f"    🔍 親レベル2: サイズ{size}, テキスト: '{text[:50]}...'")

                # クリック可能エリアの条件チェック
                if not (size['width'] >= 400 and size['height'] > 50 and "amount eaten" in text.lower()):
                    print("    ❌ 適切なクリック可能エリアが見つかりません")
                    raise Exception("適切なクリック可能エリアが見つかりません")

                print(f"    🎯 クリック可能エリア特定（親レベル2）")

                # 既存のモーダルを閉じる
                self._close_any_open_modals()
                time.sleep(1)

                # Select Servingモーダルを開く
                print("    🔄 Select Servingモーダルを開く...")
                
                # スクロールして表示
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_level2)
                time.sleep(1)

                # クリック実行
                parent_level2.click()
                time.sleep(3)

                # Select Serving モーダルが開いたかチェック
                if self._is_select_serving_modal_open():
                    print("    ✅ Select Serving モーダルが開きました！")
                    
                    # 🔥 新しい正確な方法で全serving optionsを抽出
                    serving_options = self._extract_all_serving_options_new()
                    
                    self._close_select_serving_modal()
                    
                    if serving_options:
                        print(f"    🎉 serving情報取得成功: {len(serving_options)}個の単位")
                        
                        # 旧形式に変換して返す（互換性のため）
                        return self._convert_to_old_format(serving_options)
                    else:
                        print("    ❌ モーダルから有効なデータを抽出できませんでした")
                        raise Exception("モーダルから有効なデータを抽出できませんでした")
                else:
                    print("    ❌ Select Serving モーダルが開きませんでした")
                    raise Exception("Select Serving モーダルが開きませんでした")

            except Exception as e:
                print(f"    ⚠️ 親レベル2チェックエラー: {e}")
                raise Exception(f"親レベル2の処理でエラー: {e}")

        except Exception as e:
            print(f"    ❌ Amount eaten セクション抽出エラー: {e}")
            raise Exception(f"Amount eaten機能が失敗しました: {e}")

    def _extract_all_serving_options_new(self):
        """新しい正確な方法で全serving optionsを抽出"""
        try:
            print("      🔍 全serving optionsを抽出中...")
            serving_options = []

            # ラジオボタングループを取得
            radio_group = self.driver.find_element(By.XPATH, "//div[@role='radiogroup']")
            print(f"      ✅ ラジオボタングループ取得成功")

            # 🔍 デバッグ: 様々な方法でFormControlLabel要素を探す
            selectors_to_try = [
                (".//label[contains(@class, 'MuiFormControlLabel-root')]", "MuiFormControlLabel-root"),
                (".//label", "全てのlabel要素"),
                (".//*[contains(@class, 'MuiFormControlLabel')]", "MuiFormControlLabel含む"),
                (".//label[contains(@class, 'FormControl')]", "FormControl含む")
            ]

            best_result = []
            best_count = 0

            for selector, description in selectors_to_try:
                try:
                    elements = radio_group.find_elements(By.XPATH, selector)
                    print(f"      🔍 {description}: {len(elements)}個")
                    
                    if len(elements) > best_count:
                        best_count = len(elements)
                        best_result = elements
                        print(f"      ⭐ 最良の結果更新: {description} ({len(elements)}個)")
                except Exception as e:
                    print(f"      ❌ {description} 検索エラー: {e}")

            # 最も多く見つかった要素を使用
            form_labels = best_result
            print(f"      📋 使用する要素数: {len(form_labels)}個")

            for i, label in enumerate(form_labels):
                try:
                    print(f"\n        🔍 Label{i+1}の詳細調査:")
                    
                    # テキスト取得のデバッグ
                    label_text = label.text.strip()
                    print(f"          📝 label.text: '{label_text}'")
                    
                    # テキストが空の場合、代替手段を試行
                    if not label_text:
                        try:
                            label_text = label.get_attribute('textContent').strip()
                            print(f"          📝 textContent: '{label_text}'")
                        except:
                            pass
                    
                    if not label_text:
                        try:
                            label_text = label.get_attribute('innerText').strip()
                            print(f"          📝 innerText: '{label_text}'")
                        except:
                            pass

                    # ラジオボタンの値を取得
                    try:
                        radio_input = label.find_element(By.XPATH, ".//input[@type='radio']")
                        radio_value = radio_input.get_attribute('value')
                        print(f"          🔘 radio_value: '{radio_value}'")
                    except Exception as e:
                        print(f"          ❌ ラジオボタン取得エラー: {e}")
                        continue

                    # パースを試行
                    if label_text:
                        parsed_option = self._parse_serving_option_new(label_text, radio_value)
                        if parsed_option:
                            serving_options.append(parsed_option)
                            print(f"          ✅ パース成功: {parsed_option['unit_name']} - {parsed_option['calories']}cal/{parsed_option['weight']}g")
                        else:
                            print(f"          ⚠️ パース失敗: '{label_text}'")
                    else:
                        print(f"          ❌ テキストが空です")

                except Exception as e:
                    print(f"        ❌ Label{i+1}処理エラー: {e}")
                    continue

            print(f"      🎯 serving options抽出完了: {len(serving_options)}個")
            return serving_options

        except Exception as e:
            print(f"      ❌ serving options抽出エラー: {e}")
            return []

    def _parse_serving_option_new(self, label_text, radio_value):
        """serving optionを構造化データにパース（改良版）"""
        import re
        try:
            # パターン1: "{unit_name} {calories}cals / {weight} g"
            pattern1 = r'^(\w+)\s+(\d+(?:\.\d+)?)cals?\s*/\s*(\d+(?:\.\d+)?)\s*g'
            match1 = re.match(pattern1, label_text, re.IGNORECASE)

            if match1:
                unit_name = match1.group(1)
                calories = float(match1.group(2))
                weight = float(match1.group(3))

                return {
                    "unit_name": unit_name,
                    "calories": calories,
                    "weight": weight,
                    "radio_value": radio_value,
                    "raw_text": label_text
                }

            # パターン2: "fl oz {calories}cals / {weight} g" （fl ozに対応）
            pattern2 = r'^(fl\s+oz)\s+(\d+(?:\.\d+)?)cals?\s*/\s*(\d+(?:\.\d+)?)\s*g'
            match2 = re.match(pattern2, label_text, re.IGNORECASE)

            if match2:
                unit_name = match2.group(1).replace(' ', '_')  # "fl_oz"に変換
                calories = float(match2.group(2))
                weight = float(match2.group(3))

                return {
                    "unit_name": unit_name,
                    "calories": calories,
                    "weight": weight,
                    "radio_value": radio_value,
                    "raw_text": label_text
                }

            # パターン3: より複雑な単位名（space含む）
            pattern3 = r'^([a-zA-Z\s]+?)\s+(\d+(?:\.\d+)?)cals?\s*/\s*(\d+(?:\.\d+)?)\s*g'
            match3 = re.match(pattern3, label_text, re.IGNORECASE)

            if match3:
                unit_name = match3.group(1).strip().replace(' ', '_')
                calories = float(match3.group(2))
                weight = float(match3.group(3))

                return {
                    "unit_name": unit_name,
                    "calories": calories,
                    "weight": weight,
                    "radio_value": radio_value,
                    "raw_text": label_text
                }

            print(f"        ⚠️ パース失敗: '{label_text}'")
            return None

        except Exception as e:
            print(f"        ⚠️ パースエラー: {e} - テキスト: '{label_text}'")
            return None

    def _convert_to_old_format(self, serving_options):
        """新形式のserving optionsを旧形式に変換（互換性のため）"""
        try:
            old_format = {}
            
            for option in serving_options:
                unit_name = option['unit_name']
                
                # 旧形式のディクショナリ構造に変換
                old_format[unit_name] = {
                    'unit_name': unit_name,
                    'calories': option['calories'],
                    'weight': option['weight'],
                    'raw_text': option['raw_text'],
                    'radio_value': option.get('radio_value', ''),  # 新しく追加
                    'source': 'select_serving_modal'  # データソースを明記
                }
            
            print(f"      🔄 旧形式に変換完了: {len(old_format)}個の単位")
            return old_format

        except Exception as e:
            print(f"      ❌ 旧形式変換エラー: {e}")
            return {}

    def _extract_real_modal_data(self) -> Dict[str, Dict]:
        """Select Servingモーダルから全ての単位データを抽出（完全版・修正済み）"""
        try:
            print("        🔍 Select Serving モーダルから全単位データを抽出開始...")

            # 実際のモーダル構造に基づいた修正されたパターン
            # デバッグで判明：データは"oz 26cals / 28.3 g"のような形式で分離されている
            
            # まず、モーダル内の全てのテキストを含むコンテナを探す
            modal_containers = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'MuiDialog')]//div")
            
            units_data = {}
            
            for container in modal_containers:
                if not container.is_displayed():
                    continue
                    
                text = container.text.strip()
                if not text:
                    continue
                
                # 複数行の単位データが含まれている場合を処理
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                for line in lines:
                    # "oz 26cals / 28.3 g" のような形式をチェック
                    if 'cals' in line and '/' in line and 'g' in line:
                        print(f"        📝 単位行発見: '{line}'")
                        
                        parsed_data = self._parse_unit_text(line)
                        
                        if parsed_data:
                            unit_name = parsed_data['unit']
                            units_data[unit_name] = parsed_data
                            print(f"        ✅ {unit_name}: {parsed_data['calories']}cal / {parsed_data['weight']}g")

            if not units_data:
                # 代替方法：個別要素から再構築を試行
                print("        🔄 代替方法で単位データを再構築中...")
                units_data = self._reconstruct_units_from_fragments()

            if not units_data:
                raise Exception("有効な単位データを抽出できませんでした")

            print(f"        🎯 最終抽出単位数: {len(units_data)}")
            return units_data

        except Exception as e:
            print(f"        ❌ モーダルデータ抽出エラー: {e}")
            raise Exception(f"Select Servingモーダルからのデータ抽出に失敗: {e}")
            
    def _reconstruct_units_from_fragments(self) -> Dict[str, Dict]:
        """分離された要素から単位データを再構築"""
        try:
            print("        🔧 分離要素から単位データを再構築中...")
            
            # 既知の単位パターンに基づいてデータを探索
            known_units = ['oz', 'container', 'gram', 'lb', 'cup', 'ml', 'tablespoon', 'teaspoon', 'fl oz']
            units_data = {}
            
            for unit in known_units:
                try:
                    # 単位名を含む要素を探す
                    unit_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{unit}')]")
                    
                    for unit_element in unit_elements:
                        if not unit_element.is_displayed():
                            continue
                            
                        # 親要素またはテキストを確認して完全な情報を取得
                        parent_text = unit_element.get_attribute('textContent') or unit_element.text
                        
                        # "26cals"のような形式を探す
                        cals_match = re.search(r'(\d+(?:\.\d+)?)cals?', parent_text)
                        # "28.3 g"のような形式を探す  
                        weight_match = re.search(r'(\d+(?:\.\d+)?)\s*g', parent_text)
                        
                        if cals_match and weight_match:
                            calories = float(cals_match.group(1))
                            weight = float(weight_match.group(1))
                            
                            units_data[unit] = {
                                'unit': unit,
                                'calories': calories,
                                'weight': weight,
                                'raw_text': parent_text
                            }
                            
                            print(f"        ✅ 再構築成功 {unit}: {calories}cal / {weight}g")
                            break
                            
                except Exception as e:
                    continue
            
            return units_data
            
        except Exception as e:
            print(f"        ⚠️ 再構築エラー: {e}")
            return {}

    def _parse_unit_text(self, text: str) -> Optional[Dict]:
        """単位テキストを解析して構造化データに変換"""
        try:
            # 複数の形式パターンに対応
            patterns = [
                # "cup 30cals / 245 g" 形式
                r'^(\w+(?:\s+\w+)*)\s+(\d+(?:\.\d+)?)cals?\s*/\s*(\d+(?:\.\d+)?)\s*g?$',
                # "30 cals / 245 g cup" 形式
                r'^(\d+(?:\.\d+)?)cals?\s*/\s*(\d+(?:\.\d+)?)\s*g?\s+(\w+(?:\s+\w+)*)$',
                # "1 cup (245g) 30 cals" 形式
                r'^(\d+(?:\.\d+)?)\s*(\w+(?:\s+\w+)*)\s*\((\d+(?:\.\d+)?)g?\)\s*(\d+(?:\.\d+)?)cals?$',
                # "cup: 30 cals, 245g" 形式
                r'^(\w+(?:\s+\w+)*)\s*:\s*(\d+(?:\.\d+)?)cals?,?\s*(\d+(?:\.\d+)?)g?$'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 3:
                        # パターン1: unit, cals, weight
                        if groups[0].replace('.', '').isdigit():
                            # パターン2の場合: cals, weight, unit
                            return {
                                'unit': groups[2],
                                'calories': float(groups[0]),
                                'weight': float(groups[1]),
                                'raw_text': text
                            }
                        else:
                            # パターン1の場合: unit, cals, weight
                            return {
                                'unit': groups[0],
                                'calories': float(groups[1]),
                                'weight': float(groups[2]),
                                'raw_text': text
                            }
                    elif len(groups) == 4:
                        # パターン3の場合: amount, unit, weight, cals
                        return {
                            'unit': f"{groups[0]} {groups[1]}",
                            'calories': float(groups[3]),
                            'weight': float(groups[2]),
                            'raw_text': text
                        }
            
            # パターンにマッチしない場合は簡易解析
            words = text.split()
            cals = None
            weight = None
            unit_parts = []
            
            for word in words:
                if 'cal' in word.lower():
                    cals_match = re.search(r'(\d+(?:\.\d+)?)', word)
                    if cals_match:
                        cals = float(cals_match.group(1))
                elif 'g' in word and not 'cal' in word.lower():
                    weight_match = re.search(r'(\d+(?:\.\d+)?)', word)
                    if weight_match:
                        weight = float(weight_match.group(1))
                elif not any(char.isdigit() for char in word) and word not in ['/', '-', '|']:
                    unit_parts.append(word)
            
            if cals is not None and weight is not None and unit_parts:
                return {
                    'unit': ' '.join(unit_parts),
                    'calories': cals,
                    'weight': weight,
                    'raw_text': text
                }
            
            return None

        except Exception as e:
            print(f"        ⚠️ テキストパースエラー: {e}")
            return None

    def _collapse_all_nutrients(self):
        """展開された栄養素をすべて折りたたむ（栄養素展開スキップ版）"""
        try:
            print("    🔽 栄養素状態を初期化中...")
            
            # 栄養素展開をスキップして、初期状態のままAmount eatenを実行
            # テスト版と同じ条件にするため、栄養素展開は一切行わない
            print("    ✅ 栄養素展開をスキップ（Amount eaten優先）")
            
            time.sleep(1)  # DOM安定化のため少し待機
            
        except Exception as e:
            print(f"    ⚠️ 栄養素初期化エラー: {e}")
            pass
    
    def _validate_parsed_data(self, parsed_data: Dict[str, str]) -> bool:
        """解析されたデータの有効性を検証"""
        try:
            # 必須フィールドの存在チェック
            if not parsed_data.get('unit') or not parsed_data.get('calories'):
                return False
            
            # カロリーが数値かチェック
            calories = parsed_data.get('calories', '')
            if not calories.isdigit():
                return False
            
            # カロリーが合理的な範囲内かチェック（1-10000カロリー）
            calories_int = int(calories)
            if calories_int < 1 or calories_int > 10000:
                return False
                
            # 単位名が有効かチェック
            unit = parsed_data.get('unit', '')
            if len(unit) < 1 or unit in ['test', 'unknown', 'dummy']:
                return False
                
            return True
            
        except Exception:
            return False
    
    def _parse_serving_text(self, text: str) -> Dict[str, str]:
        """単位テキストを解析してデータを抽出（厳格版）"""
        try:
            import re
            
            # パターン1: "oz 26cals / 28.3 g" 
            pattern1 = r'(\w+)\s+(\d+)cals\s*/\s*([\d.]+)\s*(\w+)'
            match1 = re.search(pattern1, text)
            if match1:
                unit, calories, weight, weight_unit = match1.groups()
                return {
                    'unit': unit.lower(),
                    'calories': calories,
                    'weight': weight,
                    'weight_unit': weight_unit.lower(),
                    'original_text': text
                }
            
            # パターン2: "container 140cals"
            pattern2 = r'(\w+)\s+(\d+)cals'
            match2 = re.search(pattern2, text)
            if match2:
                unit, calories = match2.groups()
                return {
                    'unit': unit.lower(),
                    'calories': calories,
                    'original_text': text
                }
            
            # パターン3: "140 cals" （単位名が前にある場合）
            pattern3 = r'(\w+).*?(\d+)\s*cals'
            match3 = re.search(pattern3, text)
            if match3:
                unit, calories = match3.groups()
                return {
                    'unit': unit.lower(),
                    'calories': calories,
                    'original_text': text
                }
                
            print(f"        ⚠️ パターンにマッチしないテキスト: '{text}'")
            return {}
            
        except Exception as e:
            print(f"        ⚠️ テキスト解析エラー: {e}")
            raise Exception(f"テキスト解析失敗: {e}")
    
    def _parse_serving_text(self, text: str) -> Dict[str, str]:
        """単位テキストを解析してデータを抽出"""
        try:
            import re
            
            # パターン1: "oz 26cals / 28.3 g" 
            pattern1 = r'(\w+)\s+(\d+)cals\s*/\s*([\d.]+)\s*(\w+)'
            match1 = re.search(pattern1, text)
            if match1:
                unit, calories, weight, weight_unit = match1.groups()
                return {
                    'unit': unit,
                    'calories': calories,
                    'weight': weight,
                    'weight_unit': weight_unit,
                    'original_text': text
                }
            
            # パターン2: "container 140cals"
            pattern2 = r'(\w+)\s+(\d+)cals'
            match2 = re.search(pattern2, text)
            if match2:
                unit, calories = match2.groups()
                return {
                    'unit': unit,
                    'calories': calories,
                    'original_text': text
                }
            
            # パターン3: 単純に "26cals" など
            pattern3 = r'(\d+)cals'
            match3 = re.search(pattern3, text)
            if match3:
                calories = match3.group(1)
                return {
                    'unit': 'serving',
                    'calories': calories,
                    'original_text': text
                }
                
            return {}
            
        except Exception as e:
            print(f"        ⚠️ テキスト解析エラー: {e}")
            return {}

    def _action_chains_click(self, element):
        """ActionChainsを使用したクリック"""
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(self.driver)
        actions.move_to_element(element).click().perform()

    def _close_any_open_modals(self):
        """開いているモーダルがあれば閉じる"""
        try:
            # ESC キーでモーダルを閉じる
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
            
            # CANCEL ボタンがあれば閉じる
            cancel_patterns = [
                "//button[contains(text(), 'CANCEL')]",
                "//button[contains(text(), 'Cancel')]",
                "//button[contains(text(), 'Close')]"
            ]
            
            for pattern in cancel_patterns:
                try:
                    cancel_btn = self.driver.find_element(By.XPATH, pattern)
                    if cancel_btn.is_displayed():
                        cancel_btn.click()
                        time.sleep(1)
                        break
                except:
                    continue
                    
        except:
            pass

    def _is_select_serving_modal_open(self) -> bool:
        """Select Serving モーダルが開いているかチェック（簡素化版）"""
        try:
            # テストで検証済みの簡単なパターン
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

    def _extract_from_select_serving_modal(self) -> Dict[str, Dict]:
        """Select Serving モーダルから単位データを抽出"""
        try:
            print("    📋 Select Serving モーダルからデータ抽出中...")
            
            # モーダル内の単位行を検索
            # パターン: "oz 26cals / 28.3 g"
            unit_line_patterns = [
                "//*[contains(text(), 'cal') and contains(text(), 'g') and (contains(text(), 'oz') or contains(text(), 'cup') or contains(text(), 'container') or contains(text(), 'gram'))]",
                "//*[contains(text(), '/') and contains(text(), 'cal')]",
                "//div[contains(text(), 'oz') and contains(text(), 'cal')]",
                "//div[contains(text(), 'container') and contains(text(), 'cal')]"
            ]
            
            unit_lines = []
            for pattern in unit_line_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            if text and 'cal' in text.lower() and any(unit in text.lower() for unit in ['oz', 'cup', 'container', 'gram', 'lb']):
                                unit_lines.append(text)
                                print(f"        📝 単位行発見: '{text}'")
                except:
                    continue
            
            if not unit_lines:
                print("        ❌ Select Serving モーダル内に単位行が見つかりません")
                return {}
            
            # 単位行からデータを解析
            units_data = {}
            import re
            
            for line in unit_lines:
                try:
                    # パターン例: "oz 26cals / 28.3 g" または "container 140cals / 150 g"
                    # 正規表現で解析
                    pattern = r'(\w+)\s+(\d+(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g'
                    match = re.search(pattern, line, re.IGNORECASE)
                    
                    if match:
                        unit_name = match.group(1).lower()
                        calories = float(match.group(2))
                        weight_g = float(match.group(3))
                        
                        units_data[unit_name] = {
                            "calories": calories,
                            "weight_g": weight_g
                        }
                        
                        print(f"        ✅ {unit_name}: {calories}cal / {weight_g}g")
                    else:
                        print(f"        ⚠️ 解析できない行: '{line}'")
                        
                except Exception as e:
                    print(f"        ❌ 行解析エラー: {e}")
                    continue
            
            print(f"    🎉 Select Serving モーダルから{len(units_data)}個の単位を抽出")
            return units_data
            
        except Exception as e:
            print(f"    ❌ Select Serving モーダル抽出エラー: {e}")
            return {}

    def _close_select_serving_modal(self):
        """Select Serving モーダルを閉じる"""
        try:
            print("    🔄 Select Serving モーダルを閉じています...")
            
            # CANCEL ボタンを探してクリック
            cancel_patterns = [
                "//button[contains(text(), 'CANCEL')]",
                "//button[contains(text(), 'Cancel')]",
                "//span[contains(text(), 'CANCEL')]/ancestor::button[1]"
            ]
            
            for pattern in cancel_patterns:
                try:
                    cancel_btn = self.driver.find_element(By.XPATH, pattern)
                    if cancel_btn.is_displayed():
                        cancel_btn.click()
                        time.sleep(1)
                        print("    ✅ CANCEL ボタンでモーダルを閉じました")
                        return
                except:
                    continue
            
            # ESC キーでも試行
            try:
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
                print("    ✅ ESC キーでモーダルを閉じました")
            except:
                print("    ⚠️ モーダルを閉じられませんでした")
                
        except Exception as e:
            print(f"    ❌ モーダル閉じるエラー: {e}")

    def _find_dropdown_options(self) -> list:
        """ドロップダウンオプションを検索"""
        try:
            time.sleep(2)  # オプションが表示されるまで待つ
            
            option_patterns = [
                "//li[contains(text(), 'oz') or contains(text(), 'cup') or contains(text(), 'gram') or contains(text(), 'ml') or contains(text(), 'tablespoon') or contains(text(), 'teaspoon')]",
                "//div[contains(text(), 'oz') or contains(text(), 'cup') or contains(text(), 'gram') or contains(text(), 'ml')]",
                "//li[@role='option']",
                "//div[@role='option']",
                "//option",
                "//li[contains(@class, 'option')]",
                "//div[contains(@class, 'MuiMenuItem')]"
            ]
            
            for pattern in option_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    visible_options = []
                    
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip()
                            # 単位を含む表示要素のみ
                            if text and any(unit in text.lower() for unit in ['oz', 'cup', 'gram', 'ml', 'lb', 'tablespoon', 'teaspoon', 'container', 'serving']):
                                visible_options.append(element)
                    
                    if visible_options:
                        print(f"    ✅ {len(visible_options)}個の単位オプション発見 (パターン: {pattern})")
                        return visible_options
                        
                except Exception as e:
                    print(f"    ⚠️ オプション検索エラー ({pattern}): {e}")
                    continue
            
            return []
            
        except Exception as e:
            print(f"    ❌ ドロップダウンオプション検索エラー: {e}")
            return []

    def _process_simple_options(self, options: list) -> Dict[str, Dict]:
        """シンプルなオプション処理"""
        try:
            units_data = {}
            
            print(f"    📋 {len(options)}個のオプションを処理中...")
            
            for i, option in enumerate(options[:8]):  # 最大8個まで
                try:
                    option_text = option.text.strip()
                    print(f"      {i+1}: '{option_text}'")
                    
                    # 単位名を抽出
                    unit_name = option_text.lower().strip()
                    if not unit_name:
                        continue
                    
                    # オプションを選択
                    print(f"    🎯 オプション {i+1} を選択: {unit_name}")
                    option.click()
                    time.sleep(2)
                    
                    # ページから情報を抽出
                    unit_info = self._extract_current_unit_info(unit_name)
                    
                    if unit_info and unit_info.get('calories', 0) > 0:
                        units_data[unit_name] = unit_info
                        print(f"        ✅ 成功: {unit_name} = {unit_info}")
                    else:
                        print(f"        ❌ データ取得失敗: {unit_name}")
                    
                    # ドロップダウンを再度開く（次のオプションのため）
                    if i < len(options) - 1:
                        success = self._reopen_unit_dropdown()
                        if not success:
                            print(f"        ⚠️ ドロップダウン再開失敗、処理終了")
                            break
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"        ❌ オプション{i+1}処理エラー: {e}")
                    continue
            
            return units_data
            
        except Exception as e:
            print(f"    ❌ オプション処理エラー: {e}")
            return {}

    def _extract_dropdown_options(self) -> Dict[str, Dict]:
        """ドロップダウンオプションから単位データを抽出"""
        try:
            time.sleep(2)  # ドロップダウンが開くのを待つ
            
            print("    🔍 ドロップダウンオプション検索中...")
            
            # ドロップダウンオプションを検索
            option_patterns = [
                "//li[@role='option']",
                "//div[@role='option']", 
                "//option",
                "//li[contains(@class, 'option')]",
                "//div[contains(@class, 'option')]",
                "//div[contains(@class, 'MuiMenuItem')]",
                "//ul/li",  # シンプルなリスト項目
                "//div[contains(@class, 'menu')]//div[contains(text(), 'oz') or contains(text(), 'cup') or contains(text(), 'gram')]"
            ]
            
            options = []
            found_pattern = None
            
            for pattern in option_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    visible_elements = []
                    
                    for el in elements:
                        if el.is_displayed() and el.text.strip():
                            # 単位を含む要素のみ選択
                            text = el.text.strip().lower()
                            if any(unit in text for unit in ['oz', 'cup', 'gram', 'ml', 'lb', 'tablespoon', 'teaspoon', 'container', 'serving']):
                                visible_elements.append(el)
                    
                    if visible_elements:
                        options = visible_elements
                        found_pattern = pattern
                        print(f"    ✅ {len(options)}個のオプションを発見: {pattern}")
                        break
                        
                except Exception as e:
                    print(f"    ⚠️ パターン '{pattern}' でエラー: {e}")
                    continue
            
            if not options:
                print("    ❌ ドロップダウンオプションが見つかりません")
                print("    🔍 デバッグ: 全ての表示要素を確認...")
                try:
                    # デバッグ情報を出力
                    all_visible = self.driver.find_elements(By.XPATH, "//*[string-length(text()) > 0]")
                    unit_containing = [el for el in all_visible if el.is_displayed() and any(unit in el.text.lower() for unit in ['oz', 'cup', 'gram', 'ml'])]
                    print(f"    📋 単位を含む表示要素: {len(unit_containing)}個")
                    for i, el in enumerate(unit_containing[:5]):  # 最初の5個だけ表示
                        print(f"      {i+1}: '{el.text[:30]}...' ({el.tag_name})")
                except:
                    pass
                return {}
            
            # オプションリストをログ出力
            print("    📋 見つかったオプション:")
            units_data = {}
            
            for i, option in enumerate(options):
                try:
                    option_text = option.text.strip()
                    print(f"      {i+1}: '{option_text}'")
                    
                    # 単位名を解析
                    unit_name = self._parse_unit_name_from_option(option_text)
                    
                    if unit_name:
                        print(f"    🎯 オプション{i+1}をクリック: {unit_name}")
                        
                        # オプションを慎重にクリック
                        try:
                            # 他の要素と被らないようスクロール
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", option)
                            time.sleep(0.5)
                            
                            # JavaScriptでクリック（確実性を高める）
                            self.driver.execute_script("arguments[0].click();", option)
                            time.sleep(1.5)
                            
                            # 現在のページから重量情報を抽出
                            weight_info = self._extract_current_unit_info(unit_name)
                            
                            if weight_info:
                                units_data[unit_name] = weight_info
                                print(f"        ✅ {unit_name}: {weight_info}")
                            else:
                                print(f"        ❌ {unit_name}: 重量情報取得失敗")
                            
                            # 次のオプションのためにドロップダウンを再度開く必要があるか確認
                            if i < len(options) - 1:  # まだ処理するオプションがある場合
                                self._reopen_unit_dropdown()
                                time.sleep(1)
                                
                        except Exception as e:
                            print(f"        ❌ オプション{i+1}クリックエラー: {e}")
                            continue
                    else:
                        print(f"      ⚠️ 単位名解析失敗: '{option_text}'")
                        
                except Exception as e:
                    print(f"    ❌ オプション{i+1}処理エラー: {e}")
                    continue
                    
                # 最大8個まで処理（タイムアウト防止）
                if len(units_data) >= 8:
                    print(f"    ⏱️ 8個の単位を取得したので処理完了")
                    break
            
            print(f"    ✅ 合計{len(units_data)}個の単位データを取得")
            return units_data
            
        except Exception as e:
            print(f"    ❌ ドロップダウンオプション抽出エラー: {e}")
            import traceback
            print(f"    📋 詳細エラー: {traceback.format_exc()}")
            return {}

    def _parse_unit_name_from_option(self, option_text: str) -> str:
        """オプションテキストから単位名を抽出"""
        option_lower = option_text.lower()
        
        # 一般的な単位名をチェック
        units = ['cup', 'tablespoon', 'teaspoon', 'fl oz', 'oz', 'pound', 'lb', 'gram', 'ml', 'liter']
        
        for unit in units:
            if unit in option_lower:
                return unit.replace('pound', 'lb')  # 正規化
        
        return option_text.strip()  # フォールバック

    def _extract_current_unit_info(self, unit_name: str) -> Dict[str, float]:
        """現在のページから指定単位の重量とカロリー情報を抽出"""
        try:
            time.sleep(1)  # ページ更新を待つ
            
            # ページ全体のテキストを取得
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            import re
            
            # カロリー情報を抽出（様々なパターンに対応）
            calorie_patterns = [
                r'(\d+(?:\.\d+)?)\s*calories?',
                r'(\d+(?:\.\d+)?)\s*cals?',
                r'(\d+(?:\.\d+)?)\s*cal\b',
                r'calories?[:\s]*(\d+(?:\.\d+)?)',
                # Amount eatenセクション専用
                r'Amount eaten[^0-9]*(\d+(?:\.\d+)?)',
                # 数字のみ（他のパターンで見つからない場合）
                r'\b(\d+(?:\.\d+)?)\b'
            ]
            
            calories = 0
            for pattern in calorie_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    try:
                        cal_value = float(match)
                        # 現実的なカロリー範囲（1〜10000）
                        if 1 <= cal_value <= 10000:
                            calories = cal_value
                            print(f"        📊 カロリー検出: {calories} (パターン: {pattern})")
                            break
                    except:
                        continue
                if calories > 0:
                    break
            
            # 重量情報を抽出
            weight_g = 1.0  # デフォルト値
            
            # まず単位固有のパターンで検索
            unit_specific_patterns = [
                rf'{re.escape(unit_name)}\s*[^0-9]*(\d+(?:\.\d+)?)\s*g',
                rf'(\d+(?:\.\d+)?)g?\s*{re.escape(unit_name)}',
                rf'{re.escape(unit_name)}\s*=\s*(\d+(?:\.\d+)?)\s*g'
            ]
            
            for pattern in unit_specific_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        weight_g = float(match.group(1))
                        print(f"        ⚖️ 重量検出: {weight_g}g (パターン: {pattern})")
                        break
                    except:
                        continue
            
            # 単位固有パターンで見つからない場合、一般的なパターンで検索
            if weight_g == 1.0:
                general_patterns = [
                    r'\((\d+(?:\.\d+)?)\s*g\)',  # (150g)
                    r'(\d+(?:\.\d+)?)\s*grams?',  # 150 grams
                    r'(\d+(?:\.\d+)?)\s*g\b',     # 150g
                    r'weight[:\s]*(\d+(?:\.\d+)?)',  # weight: 150
                ]
                
                for pattern in general_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        try:
                            weight_g = float(match.group(1))
                            print(f"        ⚖️ 重量検出: {weight_g}g (一般パターン: {pattern})")
                            break
                        except:
                            continue
            
            # 単位別のデフォルト重量を設定
            if weight_g == 1.0:
                unit_defaults = {
                    "cup": 240.0,
                    "oz": 28.3,
                    "fl oz": 30.0,
                    "tablespoon": 15.0,
                    "teaspoon": 5.0,
                    "lb": 453.6,
                    "container": 150.0,
                    "serving": 100.0,
                    "gram": 1.0
                }
                
                for unit_key, default_weight in unit_defaults.items():
                    if unit_key in unit_name.lower():
                        weight_g = default_weight
                        print(f"        ⚖️ デフォルト重量使用: {weight_g}g ({unit_name})")
                        break
            
            result = {
                "calories": calories,
                "weight_g": weight_g
            }
            
            print(f"        ✅ {unit_name}: {result}")
            return result
            
        except Exception as e:
            print(f"        ❌ 単位情報抽出エラー: {e}")
            return {"calories": 0, "weight_g": 1.0}

    def _reopen_unit_dropdown(self):
        """単位ドロップダウンを再度開く"""
        try:
            print("        🔄 ドロップダウン再開中...")
            
            # 現在の単位要素を再検索
            unit_patterns = [
                "//span[contains(text(), 'oz') or contains(text(), 'cup') or contains(text(), 'gram')]",
                "//*[contains(text(), 'oz') and string-length(text()) < 10]",
                "//*[contains(text(), 'cup') and string-length(text()) < 10]"
            ]
            
            for pattern in unit_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            # 単位要素の隣のドロップダウンボタンを探す
                            dropdown_patterns = [
                                "./following-sibling::*[@role='button']",
                                "../following-sibling::*[@role='button']",
                                "./following::*[position() <= 2 and @role='button']"
                            ]
                            
                            for dp in dropdown_patterns:
                                try:
                                    dropdown = element.find_element(By.XPATH, dp)
                                    if dropdown.is_displayed() and dropdown.is_enabled():
                                        dropdown.click()
                                        time.sleep(1)
                                        print("        ✅ ドロップダウン再開成功")
                                        return True
                                except:
                                    continue
                except:
                    continue
                    
            # フォールバック: 一般的なドロップダウン要素を探す
            fallback_patterns = [
                "//div[@role='combobox']",
                "//div[contains(@class, 'MuiSelect')]",
                "//select"
            ]
            
            for pattern in fallback_patterns:
                try:
                    element = self.driver.find_element(By.XPATH, pattern)
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        time.sleep(1)
                        print("        ✅ フォールバック方式でドロップダウン再開")
                        return True
                except:
                    continue
                    
            print("        ❌ ドロップダウン再開失敗")
            return False
            
        except Exception as e:
            print(f"        ❌ ドロップダウン再開エラー: {e}")
            return False

    def _debug_amount_section(self) -> Dict[str, Dict]:
        """Amount eaten セクションのデバッグ情報を表示"""
        try:
            print("    🔍 デバッグ: Amount eaten セクション詳細調査...")
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # "amount"を含む行を探す
            amount_lines = []
            for line in page_text.split('\n'):
                if 'amount' in line.lower() or 'eaten' in line.lower() or 'enter' in line.lower():
                    amount_lines.append(line.strip())
            
            if amount_lines:
                print("    📋 Amount関連の行:")
                for i, line in enumerate(amount_lines[:10]):
                    print(f"      {i+1}: {line}")
            
            # 入力フィールドを検索
            input_elements = self.driver.find_elements(By.XPATH, "//input | //select")
            visible_inputs = []
            for input_el in input_elements:
                if input_el.is_displayed():
                    try:
                        placeholder = input_el.get_attribute('placeholder') or ''
                        value = input_el.get_attribute('value') or ''
                        input_type = input_el.get_attribute('type') or ''
                        visible_inputs.append(f"Type:{input_type} Placeholder:'{placeholder}' Value:'{value}'")
                    except:
                        pass
            
            if visible_inputs:
                print("    📝 表示されている入力要素:")
                for i, inp in enumerate(visible_inputs[:5]):
                    print(f"      {i+1}: {inp}")
            
            return {}
            
        except Exception as e:
            print(f"    ❌ デバッグ情報取得エラー: {e}")
            return {}

    def _extract_units_from_select_serving_modal(self) -> Dict[str, Dict]:
        """Select Servingモーダルから単位データを抽出（従来の方法）"""
        try:
            # モーダル表示待機
            max_attempts = 5
            body_text = None
            
            for attempt in range(max_attempts):
                time.sleep(2)
                try:
                    body_text = self.driver.find_element(By.TAG_NAME, "body").text
                    if "Select Serving" in body_text and ("cup" in body_text or "gram" in body_text):
                        print(f"    ✅ 試行 {attempt + 1}: Select Serving情報発見")
                        break
                except:
                    continue
                    
            if not body_text:
                return {}

            serving_section = self.extract_serving_section(body_text)
            if serving_section:
                units_data = self.parse_serving_lines(serving_section)
                if units_data:
                    self._close_select_serving_modal()
                    return units_data
            
            return {}
            
        except Exception as e:
            print(f"    ❌ Select Servingモーダル抽出エラー: {e}")
            return {}

    def _close_select_serving_modal(self):
        """Select Servingモーダルを確実に閉じる"""
        try:
            cancel_clicked = False
            cancel_patterns = [
                "//span[contains(text(), 'CANCEL')]",
                "//button[contains(text(), 'CANCEL')]", 
                "//*[contains(text(), 'CANCEL') and (name()='span' or name()='button' or name()='div')]",
                "//div[text()='CANCEL']",
                "//span[text()='CANCEL']",
                "//*[text()='CANCEL']"
            ]

            for pattern in cancel_patterns:
                try:
                    cancel_elements = self.driver.find_elements(By.XPATH, pattern)
                    for cancel_button in cancel_elements:
                        if cancel_button.is_displayed() and cancel_button.is_enabled():
                            print(f"    🎯 CANCEL発見: {pattern}")
                            cancel_button.click()
                            time.sleep(2)  # モーダル閉じる待機
                            cancel_clicked = True
                            print("    ✅ CANCELボタンクリック成功")
                            break
                    if cancel_clicked:
                        break
                except Exception as e:
                    continue

            if not cancel_clicked:
                print("    ❌ CANCELボタンが見つかりません - ESCキーを試行")
                try:
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(2)
                    print("    ⚠️ ESCキーでモーダル閉じるを試行")
                except Exception as e:
                    print(f"    ❌ ESCキーも失敗: {e}")

        except Exception as e:
            print(f"    ❌ モーダル閉じる処理エラー: {e}")

    def close_modal_if_open(self):
        """開いているモーダル/ポップアップがあれば閉じる（成功パターン優先版）"""
        print("    🔍 開いているモーダル/ポップアップを確認中...")
        
        # 成功実績のある代替手段を最初に試行
        alternatives = [
            ("ページの空白部分をクリック", lambda: self.driver.find_element(By.TAG_NAME, 'body').click()),
            ("ESCキー", lambda: self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)),
            ("戻るボタン", lambda: self.driver.back())
        ]
        
        # まずCANCELボタンを試す
        cancel_patterns = [
            "//span[contains(text(), 'CANCEL')]",
            "//button[contains(text(), 'CANCEL')]",
            "//*[contains(text(), 'CANCEL') and (name()='span' or name()='button' or name()='div')]",
            "//div[text()='CANCEL']",
            "//span[text()='CANCEL']",
        ]
        
        for pattern in cancel_patterns:
            try:
                cancel_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, pattern)))
                cancel_button.click()
                print(f"    ✅ CANCELボタンクリック成功: {pattern}")
                time.sleep(1)  # クリック後の処理待ち
                return True
            except:
                continue
        
        print("    ⚠️ CANCELボタンが見つかりません")
        
        # 成功実績のある代替手段を試行
        for i, (name, action) in enumerate(alternatives, 1):
            try:
                action()
                print(f"    🔄 代替手段 {i} を実行")
                time.sleep(2)  # 処理待ち
                
                # モーダルが閉じたか確認
                page_text = self.driver.page_source
                if "Select Serving" not in page_text:
                    print(f"    ✅ 代替手段 {i} でモーダル閉じる成功")
                    return True
            except Exception as e:
                print(f"    ❌ 代替手段 {i} 失敗: {e}")
                continue
        
        print("    ⚠️ モーダルを閉じることができませんでした")
        return False

    def extract_nutrition_info(self, preview_text: str = "") -> Dict[str, Any]:
        """現在のページから栄養情報を抽出（実際のデータのみ使用）"""
        try:
            nutrition_data = {
                'name': '',
                'food_grade': '',
                'units': {},
                'detailed_nutrients': {},
                'url': self.driver.current_url,
                'scraped_at': datetime.now().isoformat()
            }

            # 基本情報を取得
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            texts = []
            for elem in all_elements:
                text = elem.text.strip()
                if text and len(text) <= 500:
                    texts.append(text)

            # 食材名を取得
            for text in texts:
                if any(word in text.lower() for word in ['milk', 'egg', 'cheese', 'yogurt', 'butter', 'cream', 'dairy']):
                    if len(text) > 10 and len(text) < 100:
                        nutrition_data['name'] = text
                        break

            # Food Gradeを取得
            for i, text in enumerate(texts):
                if text == 'Food Grade' and i + 1 < len(texts):
                    nutrition_data['food_grade'] = texts[i + 1]
                    break

            # 🚀 重要: P要素クリック前に完全な単位データを抽出
            print("  🔍 完全な単位データを抽出中...")
            complete_units = self.extract_complete_units_data()

            if complete_units:
                # 完全な単位データが取得できた場合
                nutrition_data['units'] = complete_units

                # 基準単位を設定（最初の単位）
                first_unit = list(complete_units.keys())[0]
                nutrition_data['base_unit'] = first_unit
                nutrition_data['base_calories'] = complete_units[first_unit]['calories']
                nutrition_data['base_weight_g'] = complete_units[first_unit]['weight_g']

                print(f"  ✅ 完全単位データ取得成功: {len(complete_units)}個の単位")
                print(f"  🎯 基準単位: {first_unit} ({nutrition_data['base_calories']}cals / {nutrition_data['base_weight_g']}g)")

            else:
                # フォールバック: 基準単位とカロリーを動的に取得
                print("  ⚠️ 完全単位データ取得失敗 - 基準単位のみ取得に切り替え")
                base_unit, base_calories, _ = self.extract_base_unit_info(texts + [preview_text])
                if not base_unit or not base_calories:
                    raise ValueError("基準単位またはカロリー情報が取得できませんでした")

                # 実際の重量データを取得（必須）
                actual_unit, actual_weight = self.extract_actual_serving_weight(texts + [preview_text])

                if actual_unit != base_unit.lower():
                    raise ValueError(f"単位の不一致: 基準単位={base_unit}, 抽出単位={actual_unit}")

                # 実際のデータのみを設定
                nutrition_data['base_unit'] = base_unit
                nutrition_data['base_calories'] = base_calories
                nutrition_data['base_weight_g'] = actual_weight  # 実際の重量データを使用

                # unitsセクションを構築（実際の重量データ使用）
                nutrition_data['units'] = self.build_units_section(base_unit, base_calories, actual_weight, texts + [preview_text])

                print(f"  ✅ 基準単位データ使用: {base_unit} = {actual_weight}g")

            # 🔽 serving情報取得後にF、C、P要素をクリックして栄養素情報を展開
            print("🔍 詳細栄養素情報を取得中...")
            after_texts = []
            try:
                import time

                # F、C、P要素を順番にクリックして栄養素情報を展開
                fcp_elements = ['P']
                clicked_elements = []

                for element_text in fcp_elements:
                    try:
                        # div要素でF、C、Pのテキストを持つ要素を探す
                        fcp_element = self.driver.find_element(By.XPATH, f"//div[text()='{element_text}']")
                        fcp_element.click()
                        clicked_elements.append(element_text)
                        print(f"  📍 {element_text} 要素をクリックしました")
                        time.sleep(1)  # 各クリック間の待機
                    except Exception as e:
                        print(f"  ⚠️ {element_text} 要素のクリックに失敗: {e}")
                        continue

                if clicked_elements:
                    time.sleep(2)  # 栄養素情報の読み込みを待機
                    print(f"✅ {len(clicked_elements)}個の栄養素要素をクリックしました: {', '.join(clicked_elements)}")

                    # 栄養素展開後の情報を取得
                    all_elements_after = self.driver.find_elements(By.XPATH, "//*[text()]")
                    for elem in all_elements_after:
                        text = elem.text.strip()
                        if text and len(text) <= 500:
                            after_texts.append(text)

                    # 栄養素情報を抽出
                    nutrition_keywords = {
                        'protein': ['protein', 'プロテイン', 'タンパク質'],
                        'fat': ['fat', 'lipid', '脂質', '脂肪'],
                        'carbs': ['carb', 'carbohydrate', '炭水化物'],
                        'fiber': ['fiber', 'fibre', '繊維', '食物繊維'],
                        'sugar': ['sugar', '砂糖', '糖分'],
                        'sodium': ['sodium', 'ナトリウム'],
                        'calcium': ['calcium', 'カルシウム'],
                        'iron': ['iron', '鉄'],
                        'vitamin_c': ['vitamin c', 'ビタミンC'],
                        'potassium': ['potassium', 'カリウム']
                    }

                    # テキストから栄養素を検索
                    for nutrient_key, keywords in nutrition_keywords.items():
                        for text in after_texts:
                            text_lower = text.lower()
                            for keyword in keywords:
                                if keyword.lower() in text_lower:
                                    # 数値を抽出
                                    import re
                                    numbers = re.findall(r'\d+(?:\.\d+)?', text)
                                    if numbers:
                                        nutrition_data['detailed_nutrients'][nutrient_key] = {
                                            'value': float(numbers[0]),
                                            'text': text,
                                            'keyword_matched': keyword
                                        }
                                        print(f"  🎯 {nutrient_key}: {text}")
                                    break

                else:
                    print("❌ F、C、P要素がクリックできませんでした")

            except Exception as e:
                print(f"⚠️ 栄養素情報展開エラー: {e}")
            
            return nutrition_data

        except Exception as e:
            print(f"❌ 栄養情報抽出エラー: {str(e)}")
            raise  # 概算値フォールバックなしでエラーで停止  # 概算値フォールバックなしでエラーで停止

    def extract_base_unit_info(self, texts: List[str]) -> tuple:
        """基準単位・カロリーのみを抽出（重量は実際データから取得）"""
        try:
            import re

            base_unit = None
            base_calories = None

            # preview_textから単位を抽出（例："Almond milk unsweetened fortified, cup\n30cals"）
            for text in texts:
                # "単位名\nXXcals" パターンを探す
                if 'cal' in text.lower() and '\n' in text:
                    lines = text.split('\n')
                    if len(lines) >= 2:
                        # 最初の行から単位を抽出
                        first_line = lines[0].strip()
                        if ',' in first_line:
                            unit_part = first_line.split(',')[-1].strip()
                            base_unit = unit_part

                        # 2行目からカロリーを抽出
                        cal_line = lines[1].strip()
                        cal_match = re.search(r'(\d+)cal', cal_line.lower())
                        if cal_match:
                            base_calories = int(cal_match.group(1))
                            print(f"  🎯 基準単位: {base_unit} = {base_calories}cal")
                            break

            if base_unit and base_calories:
                # 重量は実際データから取得するためNoneを返す
                return base_unit, base_calories, None
            
            print("  ⚠️ 基準単位またはカロリー情報が見つかりませんでした")
            return None, None, None

        except Exception as e:
            print(f"⚠️ 基準単位抽出エラー: {e}")
            return None, None, None

    def extract_actual_serving_weight(self, all_texts: List[str]) -> tuple:
        """MyNetDiaryの実際のServing Sizeから正確な重量を抽出（必須）"""
        try:
            print("  🔍 実際のServing Size重量を抽出中...")
            
            # 調査結果から判明した実際のパターン: "cup (245g)" 
            serving_weight_pattern = r'(\w+)\s*\((\d+)g\)'
            
            for text in all_texts:
                # シンプルなパターンでマッチング
                match = re.search(serving_weight_pattern, text)
                if match:
                    unit = match.group(1).lower()
                    weight = float(match.group(2))
                    print(f"    ✅ 発見: {unit} ({weight}g)")
                    return unit, weight
            
            # "Serving Size cup (245g)" 形式の詳細パターン
            detailed_pattern = r'Serving Size\s+(\w+)\s*\((\d+)g\)'
            for text in all_texts:
                match = re.search(detailed_pattern, text)
                if match:
                    unit = match.group(1).lower()
                    weight = float(match.group(2))
                    print(f"    ✅ 詳細パターンで発見: Serving Size {unit} ({weight}g)")
                    return unit, weight
            
            # デバッグ用: 利用可能なテキストを表示
            print("    🔍 利用可能なテキストでgを含むもの:")
            for text in all_texts:
                if 'g' in text.lower() and len(text) < 50:
                    print(f"      📝 '{text}'")
            
            # 正確な重量データが見つからない場合はエラーで停止
            raise ValueError("実際の重量データが見つかりませんでした。MyNetDiaryの構造が変更された可能性があります。")
            
        except Exception as e:
            print(f"    ❌ 実際重量抽出エラー: {e}")
            raise

    def build_units_section(self, base_unit: str, base_calories: int, actual_weight: float, all_texts: List[str] = None) -> dict:
        """unitsセクションを構築（実際の重量データのみ使用、概算値排除）"""
        try:
            units = {}
            
            print(f"    🎯 実際の重量データを使用: {base_unit} = {actual_weight}g")

            # 基準単位（実際の重量データ）
            units[base_unit.lower()] = {
                'calories': base_calories,
                'weight_g': actual_weight
            }

            # gramベース計算
            cal_per_gram = base_calories / actual_weight
            units['gram'] = {
                'calories': round(cal_per_gram, 2),
                'weight_g': 1.0
            }

            # 概算値による他の単位は追加しない（実際データのみ使用）
            print(f"  ✅ {len(units)}個の単位を構築（実際重量データのみ使用: {actual_weight}g）")
            return units

        except Exception as e:
            print(f"❌ units構築エラー: {e}")
            raise

    def save_results(self, foods_data: List[Dict]) -> str:
        """結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"web_scraping/data/top3_nutrition_{timestamp}.json"

        result_data = {
            'scraping_info': {
                'timestamp': datetime.now().isoformat(),
                'total_foods': len(foods_data),
                'source': 'MyNetDiary - Top 3 Foods',
                'category': 'Dairy, Dairy Substitutes & Egg'
            },
            'foods': foods_data
        }

        try:
            os.makedirs("web_scraping/data", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

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
            print("🚀 Top3栄養情報スクレイピング開始")

            self.setup_driver()

            if not self.login():
                print("❌ ログインに失敗しました")
                return

            if not self.navigate_to_category():
                print("❌ カテゴリ移動に失敗しました")
                return

            foods_data = self.get_top3_foods()

            if foods_data:
                filename = self.save_results(foods_data)

                print("\n📊 Top3食材データ取得完了:")
                for i, food in enumerate(foods_data, 1):
                    print(f"  {i}. {food['name']}")
                    print(f"     Grade: {food['food_grade']}")

                    if 'base_unit' in food:
                        print(f"     基準: {food['base_unit']} = {food['base_calories']}cal")

                    if food.get('units'):
                        units_count = len(food['units'])
                        print(f"     単位換算: {units_count}個の単位")
                        # gramの例を表示
                        if 'gram' in food['units']:
                            gram_cal = food['units']['gram']['calories']
                            print(f"     例: 1g = {gram_cal}cal")

                    nutrients_count = len(food.get('detailed_nutrients', {}))
                    print(f"     詳細栄養素: {nutrients_count}個")
            else:
                print("❌ データが取得できませんでした")

        except Exception as e:
            print(f"❌ 実行エラー: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        print("🏁 スクレイピング終了")

if __name__ == "__main__":
    scraper = Top3NutritionScraper()
    scraper.run()