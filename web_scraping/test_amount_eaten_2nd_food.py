#!/usr/bin/env python3
"""
2番目の食材（Almond yogurt plain）でAmount eatenエリアテスト専用スクリプト
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from config import config

class AmountEatenTester:
    def __init__(self):
        self.driver = None
        self.wait = None

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

        # 元のスクリプトと同じセレクターを使用
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

    def navigate_to_2nd_food(self):
        """2番目の食材（Almond yogurt plain）に移動（メインスクリプトと同じ方法）"""
        print("🔍 Dairy, Dairy Substitutes & Eggカテゴリに移動中...")

        try:
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

            # Dairy, Dairy Substitutes & Eggカテゴリをクリック
            category_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Dairy, Dairy Substitutes & Egg']"))
            )
            category_button.click()
            time.sleep(config.REQUEST_DELAY)

            print("🍲 2番目の食材（Almond yogurt plain）を取得中...")

            # 食材リストを取得（メインスクリプトと同じセレクター）
            food_list_items = self.driver.find_elements(
                By.XPATH,
                "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
            )

            print(f"発見した食材数: {len(food_list_items)}")

            if len(food_list_items) < 2:
                print("❌ 2番目の食材が見つかりません")
                return False

            # 最初の3つの食材を表示
            for i in range(min(3, len(food_list_items))):
                food_text = food_list_items[i].text.strip()
                print(f"  食材 {i+1}: {food_text[:50]}...")

            second_food = food_list_items[1]  # 2番目の食材
            food_name = second_food.text
            print(f"🎯 2番目の食材を選択: {food_name[:50]}...")

            # 2番目の食材をクリック
            second_food.click()
            time.sleep(config.REQUEST_DELAY * 2)

            # 栄養素を展開
            self.expand_nutrients()

            return True

        except Exception as e:
            print(f"❌ ナビゲーションエラー: {e}")
            return False

    def expand_nutrients(self):
        """栄養素を展開"""
        print("🔍 詳細栄養素情報を取得中...")

        try:
            # F, C, P 要素をクリック
            for letter in ['F', 'C', 'P']:
                try:
                    element = self.driver.find_element(By.XPATH, f"//div[text()='{letter}']")
                    element.click()
                    time.sleep(1)
                    print(f"  📍 {letter} 要素をクリックしました")
                except:
                    print(f"  ⚠️ {letter} 要素が見つかりません")

            time.sleep(2)
            print("✅ 栄養素展開完了")

        except Exception as e:
            print(f"❌ 栄養素展開エラー: {e}")

    def test_amount_eaten_area(self):
        """Amount eaten エリアの詳細テスト"""
        print("\n" + "="*60)
        print("🧪 Amount eaten エリア詳細テスト開始")
        print("="*60)

        # Step 1: Amount eaten エリアの基本調査
        self.analyze_amount_eaten_structure()

        # Step 2: 単位行の詳細調査
        self.analyze_unit_lines()

        # Step 3: クリック可能エリアの特定
        clickable_areas = self.find_clickable_areas()

        # Step 4: 各クリック可能エリアをテスト
        self.test_clickable_areas(clickable_areas)

    def analyze_amount_eaten_structure(self):
        """Amount eaten エリアの構造分析"""
        print("\n📋 Step 1: Amount eaten エリア構造分析")

        try:
            # Amount eaten 要素を検索
            amount_eaten_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Amount eaten')]")

            print(f"Amount eaten 要素数: {len(amount_eaten_elements)}")

            for i, element in enumerate(amount_eaten_elements):
                if element.is_displayed():
                    print(f"\n📍 Amount eaten 要素 {i+1}:")
                    print(f"  タグ: {element.tag_name}")
                    print(f"  テキスト: '{element.text}'")
                    print(f"  位置: {element.location}")
                    print(f"  サイズ: {element.size}")

                    # 親要素の調査
                    for level in range(1, 4):
                        try:
                            parent = element.find_element(By.XPATH, f"{'../' * level}.")
                            print(f"  親レベル{level}: {parent.tag_name} - '{parent.text[:50]}...'")
                            print(f"    位置: {parent.location}, サイズ: {parent.size}")
                        except:
                            break

        except Exception as e:
            print(f"❌ 構造分析エラー: {e}")

    def analyze_unit_lines(self):
        """単位行の詳細分析"""
        print("\n📋 Step 2: 単位行詳細分析")

        # 各単位パターンを検索
        unit_patterns = [
            ("container", "//div[contains(text(), 'container')]"),
            ("oz", "//div[contains(text(), 'oz')]"),
            ("cup", "//div[contains(text(), 'cup')]"),
            ("gram", "//div[contains(text(), 'gram')]"),
            ("数字+単位", "//*[text()[matches(., '^\\d+\\s+(container|oz|cup|gram|ml)$')]]")
        ]

        for unit_name, pattern in unit_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, pattern)
                print(f"\n🔍 {unit_name} パターン: {len(elements)}個発見")

                for j, element in enumerate(elements[:3]):  # 最初の3個だけ表示
                    if element.is_displayed():
                        print(f"  {j+1}: '{element.text}' ({element.tag_name})")
                        print(f"      位置: {element.location}, サイズ: {element.size}")

            except Exception as e:
                print(f"  ❌ {unit_name} 検索エラー: {e}")

    def find_clickable_areas(self):
        """クリック可能エリアの特定"""
        print("\n📋 Step 3: クリック可能エリア特定")

        clickable_areas = []

        # パターン1: Amount eaten 周辺の大きな要素
        try:
            amount_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Amount eaten')]")
            for element in amount_elements:
                if element.is_displayed():
                    # 親コンテナを段階的にチェック
                    for level in range(1, 4):
                        try:
                            parent = element.find_element(By.XPATH, f"{'../' * level}.")
                            size = parent.size
                            if size['width'] > 100 and size['height'] > 30:
                                clickable_areas.append({
                                    'element': parent,
                                    'name': f'Amount eaten 親レベル{level}',
                                    'text': parent.text[:50],
                                    'size': size,
                                    'location': parent.location
                                })
                        except:
                            break
        except Exception as e:
            print(f"❌ Amount eaten エリア検索エラー: {e}")

        # パターン2: 単位を含む行の親要素
        try:
            unit_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'container') or contains(text(), 'oz')]")
            for element in unit_elements:
                if element.is_displayed() and element.text.strip():
                    # 親要素をチェック
                    try:
                        parent = element.find_element(By.XPATH, "..")
                        size = parent.size
                        if size['width'] > 80 and size['height'] > 20:
                            clickable_areas.append({
                                'element': parent,
                                'name': f'単位行親: {element.text}',
                                'text': parent.text[:50],
                                'size': size,
                                'location': parent.location
                            })
                    except:
                        pass
        except Exception as e:
            print(f"❌ 単位行検索エラー: {e}")

        print(f"🎯 クリック可能候補エリア: {len(clickable_areas)}個発見")
        for i, area in enumerate(clickable_areas):
            print(f"  {i+1}: {area['name']} - サイズ{area['size']} - '{area['text'][:30]}...'")

        return clickable_areas

    def test_clickable_areas(self, clickable_areas):
        """各クリック可能エリアをテスト"""
        print("\n📋 Step 4: クリック可能エリアテスト")

        for i, area in enumerate(clickable_areas):
            print(f"\n🧪 テスト {i+1}: {area['name']}")

            # 複数のクリック方法をテスト
            click_methods = [
                ("JavaScript", lambda el: self.driver.execute_script("arguments[0].click();", el)),
                ("通常クリック", lambda el: el.click()),
                ("ActionChains", lambda el: ActionChains(self.driver).move_to_element(el).click().perform())
            ]

            for method_name, click_func in click_methods:
                try:
                    print(f"  🔄 {method_name}でクリック中...")

                    # スクロールして表示
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", area['element'])
                    time.sleep(1)

                    # クリック実行
                    click_func(area['element'])
                    time.sleep(3)

                    # Select Serving モーダルが開いたかチェック
                    if self.check_select_serving_modal():
                        print(f"    ✅ {method_name} 成功! Select Serving モーダルが開きました")
                        self.close_modal()
                        return True
                    else:
                        print(f"    ❌ {method_name} 失敗: モーダルが開きませんでした")

                except Exception as e:
                    print(f"    ❌ {method_name} エラー: {e}")

        print("❌ 全てのクリック方法が失敗しました")
        return False

    def check_select_serving_modal(self):
        """Select Serving モーダルが開いているかチェック"""
        try:
            # Select Serving モーダルの特徴的な要素を探す
            modal_indicators = [
                "//*[contains(text(), 'Select Serving')]",
                "//*[contains(text(), 'oz') and contains(text(), 'cal') and contains(text(), 'g')]",
                "//div[contains(@class, 'MuiDialog')]"
            ]

            for pattern in modal_indicators:
                elements = self.driver.find_elements(By.XPATH, pattern)
                for element in elements:
                    if element.is_displayed():
                        print(f"        🎯 モーダル確認: '{element.text[:30]}...'")
                        return True
            return False

        except Exception as e:
            print(f"        ⚠️ モーダル確認エラー: {e}")
            return False

    def close_modal(self):
        """モーダルを閉じる"""
        try:
            # ESC キー
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)

            # CANCEL ボタン
            cancel_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'CANCEL')]")
            for btn in cancel_buttons:
                if btn.is_displayed():
                    btn.click()
                    time.sleep(1)
                    break
        except:
            pass

    def run_test(self):
        """テスト実行"""
        try:
            self.setup_driver()

            if not self.login_to_mynetdiary():
                print("❌ ログインに失敗しました")
                return

            if self.navigate_to_2nd_food():
                self.test_amount_eaten_area()
            else:
                print("❌ 2番目の食材への移動に失敗")

        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                # input("📋 ブラウザを確認してからEnterを押してください...")
                time.sleep(5)  # 一時的に5秒待機
                self.driver.quit()

if __name__ == "__main__":
    tester = AmountEatenTester()
    tester.run_test()