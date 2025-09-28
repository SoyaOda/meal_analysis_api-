#!/usr/bin/env python3
"""
安定的マルチ食材ナビゲーションコンポーネント
一度ログインしたら再ログインせずに複数の食材ページへ安定的に遷移
FOODタブ経由の確実なナビゲーションパスを実装
"""

import time
import json
from pathlib import Path
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, List, Optional, Tuple


class StableMultiFoodNavigator:
    """安定的マルチ食材ナビゲーションクラス"""

    def __init__(self, driver, wait: Optional[WebDriverWait] = None, config=None):
        """
        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
            config: 設定オブジェクト
        """
        self.driver = driver
        self.wait = wait or WebDriverWait(driver, 10)
        self.config = config
        self.food_catalog = {}
        self.food_index = {}
        self.current_session_active = False

    def load_food_catalog(self, catalog_dir: str = "food_catalog_data") -> bool:
        """
        保存済み食材カタログを読み込み

        Args:
            catalog_dir: カタログデータディレクトリ

        Returns:
            bool: 読み込み成功フラグ
        """
        try:
            print("📁 食材カタログを読み込み中...")

            data_dir = Path(catalog_dir)
            if not data_dir.exists():
                print(f"❌ カタログディレクトリが見つかりません: {catalog_dir}")
                return False

            json_files = [f for f in data_dir.glob("*.json")
                         if not f.name.startswith(("collection_summary", "navigation_test"))]

            if not json_files:
                print("❌ カタログデータが見つかりません")
                return False

            total_foods = 0
            for file in json_files:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    category_name = data['category_data']['name']
                    foods = data['category_data']['foods']

                    self.food_catalog[category_name] = {
                        "category_info": {
                            "name": category_name,
                            "xpath": data['category_data']['xpath']
                        },
                        "foods": foods
                    }

                    # 食材検索インデックスを構築
                    for food in foods:
                        normalized_name = self._normalize_food_name(food['food_name'])
                        self.food_index[normalized_name] = {
                            "original_name": food['food_name'],
                            "category": category_name,
                            "navigation_info": food
                        }

                    total_foods += len(foods)

                except Exception as e:
                    print(f"⚠️ ファイル読み込みエラー: {file.name} - {e}")
                    continue

            print(f"✅ カタログ読み込み完了:")
            print(f"   📂 カテゴリ数: {len(self.food_catalog)}個")
            print(f"   🍽️ 総食材数: {total_foods}個")
            print(f"   🔍 検索インデックス: {len(self.food_index)}個")

            return len(self.food_catalog) > 0

        except Exception as e:
            print(f"❌ カタログ読み込みエラー: {e}")
            return False

    def _normalize_food_name(self, food_name: str) -> str:
        """食材名を正規化（検索用）"""
        return food_name.lower().strip().replace('\n', ' ')

    def find_food_by_name(self, search_name: str) -> Optional[Dict]:
        """
        食材名で検索

        Args:
            search_name: 検索する食材名

        Returns:
            Optional[Dict]: 食材情報（見つからない場合はNone）
        """
        normalized_search = self._normalize_food_name(search_name)
        return self.food_index.get(normalized_search)

    def search_foods_partial(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        部分一致で食材を検索

        Args:
            query: 検索クエリ
            max_results: 最大結果数

        Returns:
            List[Dict]: 一致した食材のリスト
        """
        normalized_query = query.lower().strip()
        matches = []

        for normalized_name, food_info in self.food_index.items():
            if normalized_query in normalized_name:
                matches.append(food_info)
                if len(matches) >= max_results:
                    break

        return matches

    def initialize_session(self) -> bool:
        """
        初回ログイン & セッション初期化

        Returns:
            bool: 初期化成功フラグ
        """
        try:
            print("🔐 MyNetDiaryセッション初期化中...")

            # ログイン
            self.driver.get(self.config.LOGIN_URL)
            time.sleep(self.config.REQUEST_DELAY)

            username = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            password = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            username.send_keys(self.config.USERNAME)
            password.send_keys(self.config.PASSWORD)

            login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='jss15']")
            login_btn.click()
            time.sleep(self.config.REQUEST_DELAY * 2)

            print("✅ ログイン完了")
            self.current_session_active = True
            return True

        except Exception as e:
            print(f"❌ セッション初期化エラー: {e}")
            self.current_session_active = False
            return False

    def navigate_to_food_base_stable(self) -> bool:
        """
        安定的な食材ベース画面への移動
        FOODタブ → My Foods → Staple Foods の順で移動
        モーダル干渉を回避するための強化版

        Returns:
            bool: 移動成功フラグ
        """
        try:
            print("🧭 食材ベース画面に移動中...")

            # 0. 開いているモーダルがあれば閉じる
            self._close_any_open_modals()

            # 1. FOODタブをクリック（メイン画面に確実に戻るため）
            food_tab_clicked = False
            for attempt in range(3):
                try:
                    print(f"🎯 FOODタブクリック試行 {attempt + 1}/3")
                    
                    # モーダルを再度チェック
                    self._close_any_open_modals()
                    
                    food_tab = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//span[text()='FOOD' or text()='Food']"))
                    )
                    
                    # JavaScriptクリックで確実にクリック
                    self.driver.execute_script("arguments[0].click();", food_tab)
                    time.sleep(self.config.REQUEST_DELAY * 2)
                    
                    print("✅ FOODタブクリック完了")
                    food_tab_clicked = True
                    break
                    
                except Exception as e:
                    print(f"⚠️ FOODタブクリック試行{attempt + 1}失敗: {e}")
                    if attempt < 2:
                        time.sleep(2)
                    else:
                        print("❌ FOODタブクリック最終的に失敗、URL直接移動を試行")

            # 2. My Foods画面に移動（FOODタブがだめでも直接移動）
            my_foods_url = f"{self.config.BASE_URL}/meals.do#ff"
            self.driver.get(my_foods_url)
            time.sleep(self.config.REQUEST_DELAY * 2)
            print("🔄 My Foods画面に直接移動")

            # 3. My Foods ボタンクリック
            my_foods_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
            )
            my_foods_btn.click()
            time.sleep(self.config.REQUEST_DELAY)

            # 4. Staple Foodsをクリック
            staple_foods = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
            )
            staple_foods.click()
            time.sleep(self.config.REQUEST_DELAY)

            print("✅ 食材ベース画面への移動完了")
            return True

        except Exception as e:
            print(f"❌ 食材ベース画面移動エラー: {e}")
            return False

    def navigate_to_food_stable(self, food_name: str) -> bool:
        """
        指定食材に安定的にナビゲーション

        Args:
            food_name: 移動する食材名

        Returns:
            bool: ナビゲーション成功フラグ
        """
        try:
            print(f"🎯 食材に移動中: {food_name[:50]}...")

            # 1. 食材を検索
            food_info = self.find_food_by_name(food_name)
            if not food_info:
                print(f"❌ 食材が見つかりません: {food_name}")
                return False

            category_name = food_info["category"]
            nav_info = food_info["navigation_info"]

            print(f"📂 カテゴリ: {category_name}")

            # 2. 食材ベース画面に移動（毎回安定的に）
            if not self.navigate_to_food_base_stable():
                return False

            # 3. カテゴリに移動
            category_info = self.food_catalog[category_name]["category_info"]
            category_xpath = category_info["xpath"]

            category_element = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, category_xpath))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", category_element)
            time.sleep(1)
            category_element.click()
            time.sleep(self.config.REQUEST_DELAY * 2)

            print(f"✅ {category_name}カテゴリに移動完了")

            # 4. ページ移動（必要に応じて）
            target_page = nav_info["page_number"]
            current_page = 1

            if target_page > 1:
                print(f"📄 ページ{target_page}に移動中...")

                while current_page < target_page:
                    next_buttons = self.driver.find_elements(
                        By.XPATH,
                        "//button[contains(@aria-label, 'next') or contains(text(), 'Next')]"
                    )

                    clicked = False
                    for button in next_buttons:
                        try:
                            if button.is_enabled() and button.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                                time.sleep(1)
                                button.click()
                                time.sleep(self.config.REQUEST_DELAY * 2)
                                clicked = True
                                break
                        except:
                            continue

                    if not clicked:
                        raise Exception(f"ページ{target_page}への移動失敗")

                    current_page += 1

            # 5. 食材をクリック
            print(f"🥗 食材をクリック（位置: {nav_info['position_in_page']}）")

            food_xpath = nav_info["xpath"]
            try:
                food_element = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, food_xpath))
                )
            except:
                # XPathが見つからない場合、位置ベースで再試行
                alternative_xpath = f"//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')][{nav_info['position_in_page']}]"
                food_element = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, alternative_xpath))
                )

            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", food_element)
            time.sleep(1)
            food_element.click()
            time.sleep(self.config.REQUEST_DELAY * 2)

            print(f"✅ {food_name} への移動完了")
            return True

        except Exception as e:
            print(f"❌ 食材ナビゲーションエラー: {e}")
            return False

    def navigate_to_multiple_foods(self, food_names: List[str]) -> List[Dict]:
        """
        複数の食材に順次ナビゲーション

        Args:
            food_names: 移動する食材名のリスト

        Returns:
            List[Dict]: 各食材のナビゲーション結果
        """
        results = []

        if not self.current_session_active:
            print("❌ セッションが初期化されていません")
            return results

        print(f"🚀 マルチ食材ナビゲーション開始: {len(food_names)}個の食材")

        for i, food_name in enumerate(food_names, 1):
            print(f"\n{'='*60}")
            print(f"🔄 食材 {i}/{len(food_names)}: {food_name[:50]}...")
            print(f"{'='*60}")

            start_time = datetime.now()

            try:
                # 食材に移動
                success = self.navigate_to_food_stable(food_name)

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                result = {
                    "food_name": food_name,
                    "navigation_success": success,
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "sequence": i
                }

                if success:
                    print(f"✅ 食材 {i} 移動成功: {duration:.2f}秒")
                else:
                    print(f"❌ 食材 {i} 移動失敗")

                results.append(result)

                # 次の食材のための短い待機
                if i < len(food_names):
                    time.sleep(2)

            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                result = {
                    "food_name": food_name,
                    "navigation_success": False,
                    "error": str(e),
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "sequence": i
                }

                print(f"❌ 食材 {i} エラー: {e}")
                results.append(result)

        return results

    def get_navigation_stats(self, results: List[Dict]) -> Dict:
        """
        ナビゲーション結果の統計を取得

        Args:
            results: ナビゲーション結果のリスト

        Returns:
            Dict: 統計情報
        """
        if not results:
            return {}

        successful = [r for r in results if r.get("navigation_success")]
        failed = [r for r in results if not r.get("navigation_success")]

        stats = {
            "total_foods": len(results),
            "successful_navigations": len(successful),
            "failed_navigations": len(failed),
            "success_rate": len(successful) / len(results) * 100 if results else 0
        }

        if successful:
            durations = [r["duration_seconds"] for r in successful]
            stats.update({
                "avg_duration_seconds": sum(durations) / len(durations),
                "min_duration_seconds": min(durations),
                "max_duration_seconds": max(durations)
            })

        return stats

    def cleanup_session(self):
        """セッションをクリーンアップ"""
        self.current_session_active = False
        print("🧹 セッションクリーンアップ完了")

    def _close_any_open_modals(self):
        """開いているSelect Servingモーダルなどを閉じる"""
        try:
            # ESCキーでSelect Servingモーダルを閉じる（複数回試行）
            for i in range(3):
                from selenium.webdriver.common.keys import Keys
                from selenium.webdriver.common.action_chains import ActionChains
                
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(0.5)
                
            print("🔐 モーダル閉じ完了（ESCキー使用）")
            
        except Exception as e:
            print(f"⚠️ モーダル閉じ処理でエラー: {e}")

    def reset_to_food_base_via_food_tab(self) -> bool:
        """
        FOODタブ経由で食材ベース状態にリセット
        栄養素を閉じずに効率的にリセット
        
        Returns:
            bool: リセット成功フラグ
        """
        try:
            print("🔄 FOODタブ経由でベース状態にリセット中...")

            # 1. ESCキーでモーダルを閉じる
            self._close_any_open_modals()

            # 2. FOODタブをクリック
            food_tab_clicked = False
            for attempt in range(3):
                try:
                    print(f"🎯 FOODタブクリック試行 {attempt + 1}/3")
                    
                    food_tab = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//span[text()='FOOD' or text()='Food']"))
                    )
                    
                    # JavaScriptクリックで確実にクリック
                    self.driver.execute_script("arguments[0].click();", food_tab)
                    time.sleep(2)
                    
                    print("✅ FOODタブクリック完了")
                    food_tab_clicked = True
                    break
                    
                except Exception as e:
                    print(f"⚠️ FOODタブクリック試行{attempt + 1}失敗: {e}")
                    if attempt < 2:
                        time.sleep(1)

            if not food_tab_clicked:
                print("❌ FOODタブクリック失敗")
                return False

            # 3. My Foods画面に移動（食材ベース確保）
            my_foods_url = f"{self.config.BASE_URL}/meals.do#ff"
            self.driver.get(my_foods_url)
            time.sleep(2)
            print("🔄 My Foods画面に移動完了")

            # 4. Staple Foodsアクセス可能性確認
            try:
                my_foods_btn = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
                )
                if my_foods_btn.is_displayed():
                    print("✅ 食材ベース状態リセット成功")
                    return True
                else:
                    print("❌ 食材ベースアクセス不可")
                    return False
            except:
                print("❌ 食材ベース確認失敗")
                return False

        except Exception as e:
            print(f"❌ FOODタブリセットエラー: {e}")
            return False
