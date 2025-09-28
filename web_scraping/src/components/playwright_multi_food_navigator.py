#!/usr/bin/env python3
"""
Playwright版の安定したマルチ食品ナビゲーター
ChromeDriverの安定性問題を根本的に解決
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from pathlib import Path


class PlaywrightMultiFoodNavigator:
    """Playwright版の安定したマルチ食品ナビゲーター"""

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.food_catalog: Dict[str, Any] = {}
        self.food_index: Dict[str, Any] = {}
        self.current_session_active = False

        # MyNetDiary設定
        self.BASE_URL = "https://www.mynetdiary.com"
        self.LOGIN_URL = f"{self.BASE_URL}/logonPage.do"
        self.FOOD_BASE_URL = f"{self.BASE_URL}/food.do"

        # 認証情報（Selenium版と同じ）
        self.username = "odssuu@gmail.com"
        self.password = "hojihoji2025"

    async def initialize_session(self) -> bool:
        """
        Playwrightセッションを初期化

        Returns:
            bool: 初期化成功可否
        """
        try:
            print("🚀 Playwrightセッション初期化中...")

            self.playwright = await async_playwright().start()

            # Chrome設定（Playwrightで最適化）
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-background-timer-throttling",
                    "--disable-renderer-backgrounding",
                    "--disable-features=TranslateUI"
                ]
            )

            # コンテキスト作成（独立したセッション）
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )

            # ページ作成
            self.page = await self.context.new_page()

            # ページ設定
            self.page.set_default_timeout(30000)

            # MyNetDiaryログイン
            await self._login_to_mynetdiary()

            self.current_session_active = True
            print("✅ Playwrightセッション初期化完了")
            return True

        except Exception as e:
            print(f"❌ Playwrightセッション初期化エラー: {e}")
            await self.cleanup_session()
            return False

    async def _login_to_mynetdiary(self) -> bool:
        """MyNetDiaryにログイン"""
        try:
            print("🔐 MyNetDiaryログイン中...")

            # ログインページに移動
            await self.page.goto(self.LOGIN_URL)
            await asyncio.sleep(1.0)  # REQUEST_DELAY相当

            # Selenium版と全く同じセレクターを使用
            # ユーザー名入力
            await self.page.fill("input[type='text']", self.username)
            print("✅ ユーザー名入力完了")

            # パスワード入力
            await self.page.fill("input[type='password']", self.password)
            print("✅ パスワード入力完了")

            # ログインボタンクリック（Selenium版と同じ）
            await self.page.click("button[class*='jss15']")
            await asyncio.sleep(2.0)  # REQUEST_DELAY * 2相当
            print("✅ ログインボタンクリック完了")

            # Selenium版と同じく、ログインボタンクリック後は成功と判定
            # （ログイン後のページ確認は行わない）
            print("✅ MyNetDiaryログイン完了")
            return True

        except Exception as e:
            print(f"❌ ログインエラー: {e}")
            return False

    async def load_food_catalog(self, catalog_dir: str = "food_catalog_data") -> bool:
        """
        保存済み食材カタログを読み込み

        Args:
            catalog_dir: カタログデータディレクトリ

        Returns:
            bool: 読み込み成功フラグ
        """
        try:
            print("📁 食材カタログを読み込み中...")

            from pathlib import Path
            import json

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

    async def _extract_foods_from_category(self, category_name: str) -> List[Dict[str, Any]]:
        """カテゴリから食材リストを抽出"""
        foods = []

        try:
            # 食材リスト要素を取得
            food_elements = await self.page.query_selector_all(
                "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
            )

            for i, element in enumerate(food_elements):
                try:
                    food_text = await element.text_content()
                    food_text = food_text.strip()

                    if food_text:
                        food_info = {
                            'food_name': food_text,
                            'category': category_name,
                            'page_number': 1,  # 現在ページ番号
                            'position_in_page': i + 1,
                            'collected_at': datetime.now().isoformat()
                        }
                        foods.append(food_info)

                except Exception as e:
                    print(f"    ⚠️ 食材要素処理エラー: {e}")
                    continue

        except Exception as e:
            print(f"  ⚠️ 食材リスト抽出エラー: {e}")

        return foods

    def _build_food_index(self):
        """食材検索インデックスを構築"""
        index = {}

        for category, cat_data in self.food_catalog.items():
            for food in cat_data['foods']:
                food_name = food['food_name']
                normalized_name = self._normalize_food_name(food_name)
                index[normalized_name] = food

        self.food_index = index

    def _normalize_food_name(self, food_name: str) -> str:
        """食材名を正規化"""
        return food_name.lower().strip()

    async def navigate_to_food_stable(self, food_name: str) -> bool:
        """
        指定食材に安定的に移動

        Args:
            food_name: 食材名

        Returns:
            bool: 移動成功可否
        """
        try:
            print(f"🎯 食材に移動中: {food_name[:50]}...")

            # 食材をカタログから検索
            normalized_name = self._normalize_food_name(food_name)

            if normalized_name not in self.food_index:
                print(f"❌ 食材が見つかりません: {food_name}")
                return False

            food_info = self.food_index[normalized_name]
            category = food_info['category']

            print(f"📂 カテゴリ: {category}")

            # 食材ベース画面に移動
            await self._navigate_to_food_base()

            # カテゴリ情報を取得
            category_info = self.food_catalog[category]["category_info"]
            category_xpath = category_info["xpath"]

            # カテゴリを選択
            await self._select_category(category, category_xpath)

            # 食材情報を取得
            food_info = self.food_index[normalized_name]["navigation_info"]

            # 食材を選択
            success = await self._select_food_in_category(food_name, food_info)

            if success:
                print(f"✅ 食材移動成功: {food_name}")
                return True
            else:
                print(f"❌ 食材移動失敗: {food_name}")
                return False

        except Exception as e:
            print(f"❌ 食材移動エラー: {e}")
            return False

    async def _navigate_to_food_base(self) -> bool:
        """
        安定的な食材ベース画面への移動
        Selenium版と同じロジック: FOOD タブ → My Foods → Staple Foods の順で移動
        モーダル干渉を回避するための強化版
        """
        try:
            print("🧭 食材ベース画面に移動中...")

            # 0. 開いているモーダルがあれば閉じる
            await self._close_any_open_modals()

            # 1. FOODタブをクリック（メイン画面に確実に戻るため）
            food_tab_clicked = False
            for attempt in range(3):
                try:
                    print(f"🎯 FOODタブクリック試行 {attempt + 1}/3")

                    # モーダルを再度チェック
                    await self._close_any_open_modals()

                    # Selenium版と同じセレクター
                    food_tab = await self.page.query_selector("//span[text()='FOOD' or text()='Food']")
                    if food_tab:
                        # JavaScript評価でクリック（Selenium版と同様）
                        await self.page.evaluate("(element) => element.click()", food_tab)
                        await asyncio.sleep(2.0)  # REQUEST_DELAY * 2相当

                        print("✅ FOODタブクリック完了")
                        food_tab_clicked = True
                        break

                except Exception as e:
                    print(f"⚠️ FOODタブクリック試行{attempt + 1}失敗: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2)
                    else:
                        print("❌ FOODタブクリック最終的に失敗、URL直接移動を試行")

            # 2. My Foods画面に移動（FOODタブがだめでも直接移動）
            my_foods_url = f"{self.BASE_URL}/meals.do#ff"
            await self.page.goto(my_foods_url)
            await asyncio.sleep(2.0)  # REQUEST_DELAY * 2相当
            print("🔄 My Foods画面に直接移動")

            # 3. My Foods ボタンクリック
            my_foods_btn = await self.page.wait_for_selector("//button[@title='My Foods: recent, favorite, custom and recipes']")
            await my_foods_btn.click()
            await asyncio.sleep(1.0)  # REQUEST_DELAY相当

            # 4. Staple Foodsをクリック
            staple_foods = await self.page.wait_for_selector("//span[text()='Staple Foods']")
            await staple_foods.click()
            await asyncio.sleep(1.0)  # REQUEST_DELAY相当

            print("✅ 食材ベース画面への移動完了")
            return True

        except Exception as e:
            print(f"❌ 食材ベース画面移動エラー: {e}")
            return False

    async def _select_category(self, category_name: str, category_xpath: str) -> bool:
        """カテゴリを選択（Selenium版と同じロジック）"""
        try:
            print(f"📂 カテゴリ選択: {category_name}")

            # Selenium版と同じく、保存されたXPathを使用
            category_element = await self.page.wait_for_selector(category_xpath)

            # スクロールして要素を表示
            await category_element.scroll_into_view_if_needed()
            await asyncio.sleep(1)

            # クリック
            await category_element.click()
            await asyncio.sleep(2.0)  # REQUEST_DELAY * 2相当

            print(f"✅ {category_name}カテゴリに移動完了")
            return True

        except Exception as e:
            print(f"❌ カテゴリ選択エラー: {e}")
            return False

    async def _select_food_in_category(self, food_name: str, food_info: dict) -> bool:
        """カテゴリ内で食材を選択（テキストマッチング優先で堅牢性向上）"""
        try:
            print(f"🍽️ 食材選択: {food_name}")

            # ページ移動（必要に応じて）
            target_page = food_info["page_number"]
            current_page = 1

            if target_page > 1:
                print(f"📄 ページ{target_page}に移動中...")

                while current_page < target_page:
                    # 次ページボタンを探してクリック
                    next_buttons = await self.page.query_selector_all(
                        "//button[contains(@aria-label, 'next') or contains(text(), 'Next')]"
                    )

                    clicked = False
                    for button in next_buttons:
                        try:
                            is_enabled = await button.is_enabled()
                            is_visible = await button.is_visible()

                            if is_enabled and is_visible:
                                await button.scroll_into_view_if_needed()
                                await asyncio.sleep(1)
                                await button.click()
                                await asyncio.sleep(2.0)  # REQUEST_DELAY * 2相当
                                clicked = True
                                break
                        except:
                            continue

                    if not clicked:
                        raise Exception(f"ページ{target_page}への移動失敗")

                    current_page += 1

            # 食材をクリック（改善：テキストマッチング優先）
            print(f"🥗 食材をクリック: {food_name}")

            # 方法1: テキストマッチングで直接検索
            food_name_short = food_name.split()[0] if food_name else ""  # 最初の単語を取得
            
            text_selectors = [
                f"//*[contains(text(), '{food_name_short}')]",
                f"//div[contains(text(), '{food_name_short}')]",
                f"//li[contains(text(), '{food_name_short}')]"
            ]
            
            food_element = None
            for selector in text_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for elem in elements:
                        text_content = await elem.text_content()
                        if text_content and food_name_short.lower() in text_content.lower():
                            # クリック可能な要素かチェック
                            clickable_elem = elem
                            try:
                                # より具体的なクリック可能要素を探す
                                parent = await elem.query_selector("..")
                                if parent:
                                    clickable_elem = parent
                            except:
                                pass
                            
                            food_element = clickable_elem
                            print(f"✅ テキストマッチングで食材発見: {text_content[:50]}...")
                            break
                    if food_element:
                        break
                except:
                    continue

            # 方法2: 位置ベースでフォールバック（元のロジック）
            if not food_element:
                print(f"⚠️ テキストマッチング失敗、位置ベース試行（位置: {food_info['position_in_page']}）")
                
                food_xpath = food_info.get("xpath", "")
                try:
                    if food_xpath:
                        food_element = await self.page.wait_for_selector(food_xpath, timeout=5000)
                    else:
                        # 代替XPath
                        alternative_xpath = f"//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')][{food_info['position_in_page']}]"
                        food_element = await self.page.wait_for_selector(alternative_xpath, timeout=5000)
                except:
                    pass

            if not food_element:
                print(f"❌ 食材要素が見つかりません: {food_name}")
                return False

            # クリック実行
            await food_element.scroll_into_view_if_needed()
            await asyncio.sleep(1)
            await food_element.click()
            await asyncio.sleep(2.0)  # REQUEST_DELAY * 2相当

            print(f"✅ {food_name} への移動完了")
            return True

        except Exception as e:
            print(f"❌ 食材選択エラー: {e}")
            return False

    async def _close_any_open_modals(self) -> bool:
        """開いているモーダルを閉じる"""
        try:
            # ESCキーでモーダルを閉じる
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

            # 明示的なクローズボタンも試行
            close_selectors = [
                "//button[contains(@class, 'close')]",
                "//button[contains(text(), 'Close')]",
                "//button[contains(@aria-label, 'close')]",
                "//*[@role='dialog']//button"
            ]

            for selector in close_selectors:
                try:
                    close_button = await self.page.query_selector(selector)
                    if close_button:
                        await close_button.click()
                        await asyncio.sleep(0.3)
                except:
                    continue

            return True

        except Exception as e:
            print(f"⚠️ モーダル閉じエラー: {e}")
            return False

    async def reset_to_food_base_via_food_tab(self) -> bool:
        """
        FOODタブ経由で食材ベース状態にリセット
        栄養素を閉じずに効率的にリセット
        
        Returns:
            bool: リセット成功フラグ
        """
        try:
            print("🔄 FOODタブ経由でベース状態にリセット中...")

            # 1. ESCキーでモーダルを閉じる
            await self._close_any_open_modals()

            # 2. FOODタブをクリック
            food_tab_clicked = False
            for attempt in range(3):
                try:
                    print(f"🎯 FOODタブクリック試行 {attempt + 1}/3")
                    
                    food_tab = await self.page.wait_for_selector("//span[text()='FOOD' or text()='Food']", timeout=10000)
                    
                    # JavaScript評価でクリック（Selenium版と同様）
                    await self.page.evaluate("(element) => element.click()", food_tab)
                    await asyncio.sleep(2)
                    
                    print("✅ FOODタブクリック完了")
                    food_tab_clicked = True
                    break
                    
                except Exception as e:
                    print(f"⚠️ FOODタブクリック試行{attempt + 1}失敗: {e}")
                    if attempt < 2:
                        await asyncio.sleep(1)

            if not food_tab_clicked:
                print("❌ FOODタブクリック失敗")
                return False

            # 3. My Foods画面に移動（食材ベース確保）
            my_foods_url = f"{self.BASE_URL}/meals.do#ff"
            await self.page.goto(my_foods_url)
            await asyncio.sleep(2)
            print("🔄 My Foods画面に移動完了")

            # 4. Staple Foodsアクセス可能性確認
            try:
                my_foods_btn = await self.page.wait_for_selector(
                    "//button[@title='My Foods: recent, favorite, custom and recipes']", 
                    timeout=10000
                )
                is_displayed = await my_foods_btn.is_visible()
                if is_displayed:
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

    async def get_navigation_stats(self) -> Dict[str, Any]:
        """ナビゲーション統計を取得"""
        return {
            'total_categories': len(self.food_catalog),
            'total_foods': sum(cat['food_count'] for cat in self.food_catalog.values()),
            'indexed_foods': len(self.food_index),
            'session_active': self.current_session_active,
            'browser_type': 'playwright-chromium'
        }

    async def cleanup_session(self):
        """セッションクリーンアップ"""
        try:
            print("🧹 Playwrightセッションクリーンアップ中...")

            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
                self.playwright = None

            self.current_session_active = False
            print("✅ Playwrightセッションクリーンアップ完了")

        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")