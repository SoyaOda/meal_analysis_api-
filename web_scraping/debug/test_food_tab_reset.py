#!/usr/bin/env python3
"""
FOODタブ初期状態復帰テスト・デバッグスクリプト
栄養素展開→FOODタブクリック→状態確認のサイクルを詳細に観察
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.components.stable_multi_food_navigator import StableMultiFoodNavigator
from config import config


class FoodTabResetDebugger:
    """FOODタブ初期状態復帰デバッガー"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.navigator = None
        self.debug_log = []

    def setup_driver(self):
        """ChromeDriverを設定"""
        print("🚀 デバッグ用ChromeDriverを起動中...")
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)

        # ナビゲーターを初期化
        self.navigator = StableMultiFoodNavigator(self.driver, self.wait, config)

        print("✅ デバッグ用ChromeDriver起動完了")

    def log_debug(self, message: str, details: dict = None):
        """デバッグログを記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "url": self.driver.current_url,
            "page_title": self.driver.title,
            "details": details or {}
        }
        self.debug_log.append(log_entry)
        print(f"🔍 {message}")
        if details:
            for key, value in details.items():
                print(f"   📋 {key}: {value}")

    def capture_page_state(self, state_name: str) -> dict:
        """現在のページ状態をキャプチャ"""
        try:
            page_state = {
                "url": self.driver.current_url,
                "title": self.driver.title,
                "visible_elements": [],
                "nutrition_elements": [],
                "modal_elements": []
            }

            # 主要な可視要素を収集
            visible_elements = self.driver.find_elements(By.XPATH, "//*[text() and string-length(normalize-space(text())) > 0]")
            page_state["visible_elements"] = [elem.text.strip()[:50] for elem in visible_elements[:20] if elem.is_displayed()]

            # 栄養素関連要素を確認
            nutrition_keywords = ["protein", "fat", "carb", "fiber", "vitamin", "calcium", "iron", "sodium", "P"]
            for keyword in nutrition_keywords:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                if elements:
                    page_state["nutrition_elements"].append(f"{keyword}: {len(elements)} found")

            # モーダル要素を確認
            modals = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'MuiDialog-root')]")
            page_state["modal_elements"] = [f"Modal {i+1}: visible={modal.is_displayed()}" for i, modal in enumerate(modals)]

            self.log_debug(f"ページ状態キャプチャ: {state_name}", page_state)
            return page_state

        except Exception as e:
            self.log_debug(f"ページ状態キャプチャエラー: {e}")
            return {}

    def test_food_tab_reset_cycle(self, food_name: str = "Anchovy canned, oz, boneless\n60cals"):
        """
        FOODタブ初期状態復帰サイクルをテスト

        Args:
            food_name: テスト対象の食材名
        """
        try:
            print(f"\n{'='*80}")
            print(f"🧪 FOODタブ初期状態復帰サイクルテスト開始")
            print(f"🎯 対象食材: {food_name[:50]}...")
            print(f"{'='*80}")

            # Step 1: 初期状態をキャプチャ
            initial_state = self.capture_page_state("初期状態")

            # Step 2: 食材に移動
            print("\n🧭 食材ページに移動...")
            nav_success = self.navigator.navigate_to_food_stable(food_name)
            if not nav_success:
                self.log_debug("❌ 食材移動失敗")
                return False

            food_page_state = self.capture_page_state("食材ページ到着")

            # Step 3: Pボタンをクリックして栄養素展開
            print("\n🎯 Pボタンをクリックして栄養素展開...")
            p_success = self._click_P_button_debug()
            if p_success:
                nutrition_expanded_state = self.capture_page_state("栄養素展開後")
            else:
                self.log_debug("⚠️ Pボタンクリック失敗、続行")

            # Step 4: FOODタブをクリック（初期状態復帰試行）
            print("\n🔄 FOODタブクリックで初期状態復帰試行...")
            food_tab_success = self._click_food_tab_debug()

            if food_tab_success:
                # 少し待機してから状態確認
                time.sleep(3)
                reset_state = self.capture_page_state("FOODタブクリック後")

                # Step 5: 初期状態との比較
                self._compare_states(initial_state, reset_state)

                # Step 6: Staple Foodsアクセス可能性確認
                staple_foods_accessible = self._check_staple_foods_accessibility()

                return staple_foods_accessible
            else:
                self.log_debug("❌ FOODタブクリック失敗")
                return False

        except Exception as e:
            self.log_debug(f"❌ FOODタブ復帰サイクルテストエラー: {e}")
            return False

    def _click_P_button_debug(self) -> bool:
        """Pボタンをクリック（デバッグ版）"""
        try:
            print("  🎯 Pボタンを探してクリック中...")

            # Pボタンを探す
            p_elements = self.driver.find_elements(By.XPATH, "//div[text()='P']")
            self.log_debug(f"Pボタン検索結果", {"found_count": len(p_elements)})

            for i, p_element in enumerate(p_elements):
                try:
                    if p_element.is_displayed():
                        self.log_debug(f"Pボタン {i+1} をクリック試行")
                        p_element.click()
                        time.sleep(2)
                        self.log_debug("✅ Pボタンクリック完了")
                        return True
                except Exception as e:
                    self.log_debug(f"Pボタン {i+1} クリック失敗: {e}")
                    continue

            self.log_debug("❌ クリック可能なPボタンが見つかりません")
            return False

        except Exception as e:
            self.log_debug(f"❌ Pボタンクリックエラー: {e}")
            return False

    def _click_food_tab_debug(self) -> bool:
        """FOODタブをクリック（デバッグ版）"""
        try:
            print("  🔄 FOODタブクリック中...")

            # FOODタブを探す
            food_tab_selectors = [
                "//span[text()='FOOD' or text()='Food']",
                "//a[contains(text(), 'FOOD')]",
                "//button[contains(text(), 'FOOD')]",
                "//*[contains(@class, 'food') or contains(@id, 'food')]"
            ]

            for selector in food_tab_selectors:
                try:
                    food_elements = self.driver.find_elements(By.XPATH, selector)
                    self.log_debug(f"FOODタブ検索: {selector}", {"found_count": len(food_elements)})

                    for i, food_element in enumerate(food_elements):
                        try:
                            if food_element.is_displayed():
                                self.log_debug(f"FOODタブ {i+1} をクリック試行")

                                # スクロールしてクリック
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", food_element)
                                time.sleep(1)

                                # JavaScriptクリック
                                self.driver.execute_script("arguments[0].click();", food_element)
                                time.sleep(2)

                                self.log_debug("✅ FOODタブクリック完了")
                                return True

                        except Exception as e:
                            self.log_debug(f"FOODタブ {i+1} クリック失敗: {e}")
                            continue

                except Exception as e:
                    self.log_debug(f"FOODタブ検索エラー ({selector}): {e}")
                    continue

            self.log_debug("❌ クリック可能なFOODタブが見つかりません")
            return False

        except Exception as e:
            self.log_debug(f"❌ FOODタブクリックエラー: {e}")
            return False

    def _compare_states(self, initial_state: dict, reset_state: dict):
        """初期状態と復帰後状態を比較"""
        print("\n📊 状態比較分析...")

        comparison = {
            "url_match": initial_state.get("url") == reset_state.get("url"),
            "title_match": initial_state.get("title") == reset_state.get("title"),
            "nutrition_elements_cleared": len(reset_state.get("nutrition_elements", [])) < len(initial_state.get("nutrition_elements", [])),
            "modal_elements_cleared": all("visible=False" in modal for modal in reset_state.get("modal_elements", []))
        }

        self.log_debug("状態比較結果", comparison)

        if all(comparison.values()):
            print("✅ 初期状態への復帰成功")
            return True
        else:
            print("❌ 初期状態への復帰に問題")
            return False

    def _check_staple_foods_accessibility(self) -> bool:
        """Staple Foodsアクセス可能性確認"""
        try:
            print("  🔍 Staple Foodsアクセス可能性確認...")

            # My Foods画面に移動
            my_foods_url = f"{config.BASE_URL}/meals.do#ff"
            self.driver.get(my_foods_url)
            time.sleep(2)

            # My Foodsボタンが見つかるか確認
            my_foods_btn = self.driver.find_elements(
                By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"
            )

            if my_foods_btn and my_foods_btn[0].is_displayed():
                self.log_debug("✅ Staple Foodsアクセス可能")
                return True
            else:
                self.log_debug("❌ Staple Foodsアクセス不可")
                return False

        except Exception as e:
            self.log_debug(f"❌ Staple Foodsアクセス確認エラー: {e}")
            return False

    def save_debug_log(self) -> str:
        """デバッグログを保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debug/food_tab_reset_debug_{timestamp}.json"

        # ディレクトリ作成
        Path("debug").mkdir(exist_ok=True)

        debug_data = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "test_type": "food_tab_reset_debug",
                "total_log_entries": len(self.debug_log)
            },
            "debug_log": self.debug_log
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 デバッグログを保存: {filename}")
        return filename

    def cleanup(self):
        """リソースクリーンアップ"""
        if self.navigator:
            self.navigator.cleanup_session()
        if self.driver:
            self.driver.quit()

    def run_food_tab_reset_debug(self):
        """FOODタブ初期状態復帰デバッグを実行"""
        try:
            print("🔍 FOODタブ初期状態復帰デバッグ開始")
            print("="*90)

            self.setup_driver()

            # 1. カタログ読み込み
            if not self.navigator.load_food_catalog():
                print("❌ カタログ読み込み失敗")
                return False

            # 2. セッション初期化
            if not self.navigator.initialize_session():
                print("❌ セッション初期化失敗")
                return False

            # 3. FOODタブ復帰サイクルテスト
            success = self.test_food_tab_reset_cycle()

            # 4. ログ保存
            log_file = self.save_debug_log()

            print(f"\n🎉 FOODタブ復帰デバッグ完了!")
            print(f"✅ 復帰成功: {'Yes' if success else 'No'}")
            print(f"📁 デバッグログ: {log_file}")

            return success

        except Exception as e:
            print(f"❌ デバッグ実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


def main():
    debugger = FoodTabResetDebugger()
    success = debugger.run_food_tab_reset_debug()

    if success:
        print(f"\n🎉 FOODタブ初期状態復帰が正常に動作しました！")
    else:
        print(f"\n💥 FOODタブ初期状態復帰に問題があります。")


if __name__ == "__main__":
    main()