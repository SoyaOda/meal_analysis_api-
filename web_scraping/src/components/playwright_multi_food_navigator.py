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
        
        # ロガー初期化
        import logging
        self.logger = logging.getLogger(__name__)

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
        """食材名を正規化（改行・余分なスペースを削除）"""
        # 改行文字を空白に置換
        normalized = food_name.replace('\n', ' ').replace('\r', ' ')
        # 複数の連続空白を1つに
        import re
        normalized = re.sub(r'\s+', ' ', normalized)
        # 小文字化＆trim
        return normalized.lower().strip()

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
        """カテゴリを選択（エラー対策強化版）"""
        max_retries = 3
        timeout_ms = 60000  # 30秒→60秒に延長
        
        for attempt in range(max_retries):
            try:
                print(f"📂 カテゴリ選択: {category_name} (試行 {attempt + 1}/{max_retries})")

                # 複数のセレクター戦略を試行
                selectors = [
                    category_xpath,  # 保存されたXPath（優先）
                    f"//span[text()='{category_name}']",  # テキストベース
                    f"//span[contains(text(), '{category_name}')]",  # 部分マッチ
                    f"//*[contains(@class, 'category') and contains(text(), '{category_name}')]"  # クラスベース
                ]
                
                category_element = None
                used_selector = None
                
                for selector in selectors:
                    try:
                        category_element = await self.page.wait_for_selector(selector, timeout=timeout_ms)
                        used_selector = selector
                        break
                    except:
                        continue
                
                if not category_element:
                    if attempt < max_retries - 1:
                        print(f"⚠️ カテゴリ要素が見つかりません。{2}秒後に再試行...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        print(f"❌ カテゴリ選択失敗: {category_name} - 要素が見つかりません")
                        return False

                # スクロールして要素を表示
                await category_element.scroll_into_view_if_needed()
                await asyncio.sleep(1)

                # クリック
                await category_element.click()
                await asyncio.sleep(3.0)  # 待機時間を延長

                print(f"✅ {category_name}カテゴリに移動完了 (使用セレクター: {used_selector})")
                return True

            except Exception as e:
                print(f"⚠️ カテゴリ選択エラー (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"🔄 {3}秒後に再試行...")
                    await asyncio.sleep(3)
                else:
                    print(f"❌ カテゴリ選択最終失敗: {category_name}")
                    return False
        
        return False

    async def _select_food_in_category(self, food_name: str, food_info: dict) -> bool:
        """
        カテゴリ内で特定の食材を選択する（適応的マッチング対応）
        
        カタログとWebページの不一致に対応するため、以下の戦略を使用：
        1. 現在ページの食材を動的に取得
        2. 類似度ベースの最適マッチング
        3. フォールバック戦略による代替選択
        4. 詳細ページ移動の確認
        """
        try:
            # 現在ページの食材を動的に取得
            available_foods = await self._get_current_page_foods()
            
            if not available_foods:
                self.logger.warning(f"ページに食材が見つかりません: カテゴリ内")
                return False
            
            # 最適マッチを検索
            best_match = await self._find_best_food_match(food_name, available_foods)
            
            if not best_match:
                self.logger.warning(f"適合する食材が見つかりません: {food_name}")
                return False
            
            matched_food_name = best_match['name']
            confidence_score = best_match['confidence']  # 'similarity' → 'confidence'に修正
            
            self.logger.info(f"食材マッチング: '{food_name}' → '{matched_food_name}' (信頼度: {confidence_score:.2f})")
            
            # マッチした食材をクリックして詳細ページに移動
            try:
                # elementを直接使用
                if 'element' in best_match:
                    success = await self._click_food_and_verify(matched_food_name, best_match['element'])
                else:
                    # フォールバック: XPathで検索
                    food_element = await self.page.wait_for_selector(
                        f"//a[contains(text(), '{matched_food_name}')]",
                        timeout=30000
                    )
                    success = await self._click_food_and_verify(matched_food_name, food_element)
                
                if success:
                    print(f"✅ 食材選択・詳細ページ移動成功: {matched_food_name}")
                    return True
                else:
                    print(f"❌ 食材詳細ページ移動失敗: {matched_food_name}")
                    return False
                
            except Exception as click_error:
                self.logger.error(f"食材クリックに失敗: {matched_food_name}, エラー: {click_error}")
                return False
                
        except Exception as e:
            self.logger.error(f"食材選択中にエラー: {food_name}, エラー: {e}")
            return False

    async def _verify_food_detail_page(self, food_name: str, timeout: int = 10000) -> bool:
        """
        食材詳細ページに正しく移動したかを確認
        Amount eaten要素やFood Entry要素の存在をチェック
        """
        try:
            # 食材詳細ページの特徴的要素を待機
            indicators = [
                "//div[contains(@class, 'food-entry') or contains(@id, 'food-entry')]",
                "//*[contains(text(), 'Amount eaten')]",
                "//*[contains(text(), 'Serving')]",
                "//*[contains(text(), 'cal/g') or contains(text(), 'calories')]",
                "//input[@type='number']",
                "//input[contains(@placeholder, 'Amount')]"
            ]

            # いずれかの要素が見つかれば詳細ページとみなす
            for selector in indicators:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        print(f"✅ 食材詳細ページ確認成功: {selector}")
                        return True
                except:
                    continue

            # 全ての要素が見つからない場合はページ内容を確認
            page_content = await self.page.content()
            if "Amount eaten" in page_content or "cal/g" in page_content:
                print(f"✅ 食材詳細ページ確認成功: コンテンツ内に詳細情報あり")
                return True

            print(f"❌ 食材詳細ページ未確認: {food_name}")
            return False

        except Exception as e:
            print(f"❌ 食材詳細ページ確認エラー: {e}")
            return False

    async def _click_food_and_verify(self, food_name: str, food_element) -> bool:
        """
        食材をクリックして詳細ページに移動することを確認
        """
        try:
            print(f"🎯 食材クリック試行: {food_name}")

            # 食材をクリック
            await food_element.click()

            # 短時間待機
            await self.page.wait_for_timeout(2000)

            # 詳細ページに移動したかを確認
            if await self._verify_food_detail_page(food_name):
                print(f"✅ 食材詳細ページ移動成功: {food_name}")
                return True
            else:
                print(f"❌ 食材詳細ページ移動失敗: {food_name}")
                # スクリーンショット撮影
                timestamp = datetime.now().strftime("%H%M%S")
                screenshot_path = f"debug/food_click_failure_{timestamp}.png"
                await self.page.screenshot(path=screenshot_path)
                print(f"📸 スクリーンショット保存: {screenshot_path}")
                return False

        except Exception as e:
            print(f"❌ 食材クリック・確認エラー: {e}")
            return False

    async def _get_current_page_foods(self) -> list:
        """現在ページの食材リストを動的に取得"""
        try:
            # 食材リンクを取得（複数のセレクタパターンを試行）
            selectors = [
                "//div[@class='food-list']//a",
                "//a[contains(@href, 'food')]",
                "//td//a[not(contains(@href, 'category'))]",
                "//a[contains(text(), 'cal')]"
            ]
            
            foods = []
            for selector in selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        for element in elements:
                            text = await element.text_content()
                            if text and text.strip():
                                foods.append({
                                    'name': text.strip(),
                                    'element': element
                                })
                        break
                except:
                    continue
            
            # 重複除去
            unique_foods = []
            seen_names = set()
            for food in foods:
                if food['name'] not in seen_names:
                    unique_foods.append(food)
                    seen_names.add(food['name'])
            
            self.logger.info(f"現在ページで {len(unique_foods)} 個の食材を検出")
            return unique_foods
            
        except Exception as e:
            self.logger.error(f"現在ページの食材取得中にエラー: {e}")
            return []

    async def _find_best_food_match(self, target_food: str, available_foods: list) -> dict:
        """最適な食材マッチを検索"""
        if not available_foods:
            return None
        
        best_match = None
        best_score = 0.0
        
        # 完全一致を最優先
        for food in available_foods:
            if food['name'].lower() == target_food.lower():
                return {
                    'name': food['name'],
                    'similarity': 1.0,
                    'element': food['element']
                }
        
        # 類似度ベースマッチング
        for food in available_foods:
            score = self._calculate_food_similarity(target_food, food['name'])
            if score > best_score:
                best_score = score
                best_match = {
                    'name': food['name'],
                    'similarity': score,
                    'element': food['element']
                }
        
        # 最低類似度閾値をチェック
        if best_score >= 0.5:  # 50%以上の類似度が必要
            return best_match
        
        return None

    def _extract_food_keywords(self, food_name: str) -> set:
        """食材名からキーワードを抽出"""
        # 不要な文字を除去
        cleaned = food_name.lower()
        cleaned = cleaned.replace(',', ' ').replace('(', ' ').replace(')', ' ')
        
        # 単語に分割してキーワードセットを作成
        words = cleaned.split()
        keywords = set()
        
        for word in words:
            word = word.strip()
            if word and len(word) > 1:  # 1文字の単語は除外
                keywords.add(word)
        
        return keywords

    def _calculate_food_similarity(self, food1: str, food2: str) -> float:
        """2つの食材名の類似度を計算"""
        keywords1 = self._extract_food_keywords(food1)
        keywords2 = self._extract_food_keywords(food2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Jaccard類似度を計算
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        
        if not union:
            return 0.0
        
        jaccard_score = len(intersection) / len(union)
        
        # 部分文字列マッチングでボーナス
        substring_bonus = 0.0
        if food1.lower() in food2.lower() or food2.lower() in food1.lower():
            substring_bonus = 0.2
        
        return min(1.0, jaccard_score + substring_bonus)

    async def _get_current_page_foods(self) -> list:
        """現在ページの食材リストを動的に取得"""
        try:
            # debug scriptで成功したセレクタを優先使用
            selectors = [
                "//li[contains(@class, 'MuiListItem')]",  # debug scriptで成功
                "//a[contains(@href, 'food')]",
                "//td//a[not(contains(@href, 'category'))]",
                "//a[contains(text(), 'cal')]",
                "//div[@class='food-list']//a"
            ]
            
            foods = []
            for i, selector in enumerate(selectors):
                try:
                    elements = await self.page.query_selector_all(selector)
                    self.logger.info(f"セレクタ {i+1}: '{selector}' → {len(elements)}個の要素")
                    
                    if elements:
                        for element in elements:
                            text = await element.text_content()
                            if text and text.strip():
                                # MuiListItemの場合、リンク要素を探す
                                if 'MuiListItem' in selector:
                                    link_element = await element.query_selector('a')
                                    if link_element:
                                        foods.append({
                                            'text': text.strip(),
                                            'element': link_element  # クリック可能なリンク要素を使用
                                        })
                                    else:
                                        foods.append({
                                            'text': text.strip(),
                                            'element': element
                                        })
                                else:
                                    foods.append({
                                        'text': text.strip(),
                                        'element': element
                                    })
                        
                        self.logger.info(f"セレクタ {i+1}で {len(foods)}個の食材を取得")
                        if foods:  # 食材が見つかったらbreak
                            break
                            
                except Exception as e:
                    self.logger.warning(f"セレクタ {i+1} エラー: {e}")
                    continue
            
            # 重複除去
            unique_foods = []
            seen_texts = set()
            for food in foods:
                if food['text'] not in seen_texts:
                    unique_foods.append(food)
                    seen_texts.add(food['text'])
            
            self.logger.info(f"現在ページで {len(unique_foods)} 個の食材を検出")
            
            # デバッグ: 最初の5個の食材名を表示
            if unique_foods:
                sample_foods = [f['text'] for f in unique_foods[:5]]
                self.logger.info(f"検出された食材例: {sample_foods}")
            else:
                self.logger.warning("食材が全く検出されませんでした")
            
            return unique_foods
            
        except Exception as e:
            self.logger.error(f"現在ページの食材取得中にエラー: {e}")
            return []

    async def _find_best_food_match(self, target_food: str, available_foods: list) -> dict:
        """最適な食材マッチを検索"""
        if not available_foods:
            self.logger.warning("利用可能な食材リストが空です")
            return None
        
        self.logger.info(f"マッチング対象: '{target_food}' (検索候補: {len(available_foods)}個)")
        
        best_match = None
        best_score = 0.0
        
        # 完全一致を最優先
        for food in available_foods:
            if food['text'].lower() == target_food.lower():
                self.logger.info(f"完全一致発見: '{food['text']}'")
                return {
                    'name': food['text'],
                    'confidence': 1.0,
                    'element': food['element']
                }
        
        # 類似度ベースマッチング
        for food in available_foods:
            score = self._calculate_food_similarity(target_food, food['text'])
            self.logger.debug(f"'{food['text']}' → スコア: {score:.2f}")
            
            if score > best_score:
                best_score = score
                best_match = {
                    'name': food['text'],
                    'confidence': score,
                    'element': food['element']
                }
        
        # 最低類似度閾値をチェック
        if best_score >= 0.5:  # 50%以上の類似度が必要
            self.logger.info(f"ベストマッチ: '{best_match['name']}' (スコア: {best_score:.2f})")
            return best_match
        else:
            self.logger.warning(f"十分な類似度のマッチが見つかりません (最高スコア: {best_score:.2f})")
        
        return None

    def _extract_food_keywords(self, food_name: str) -> List[str]:
        """食材名からキーワードを抽出"""
        try:
            # カロリー情報を除去
            clean_name = food_name.replace('\n', ' ')
            clean_name = ' '.join(clean_name.split()[:-1])  # 最後の要素（カロリー）を除去
            
            # 単位・数量を除去
            units_to_remove = ['cup', 'tbsp', 'tsp', 'oz', 'fl oz', 'gram', 'g', 'ml', 'lb', 'piece', 'slice', 'serving']
            words = clean_name.split()
            
            keywords = []
            for word in words:
                word_clean = word.lower().strip(',')
                if word_clean not in units_to_remove and len(word_clean) > 2:
                    keywords.append(word_clean)
            
            return keywords[:3]  # 最初の3つのキーワード
            
        except Exception as e:
            print(f"⚠️ キーワード抽出エラー: {e}")
            return []

    def _calculate_food_similarity(self, target_keywords: List[str], candidate_text: str) -> float:
        """食材の類似度を計算"""
        try:
            if not target_keywords:
                return 0.0
            
            candidate_words = candidate_text.lower().split()
            matches = 0
            
            for keyword in target_keywords:
                # 完全一致
                if keyword in candidate_words:
                    matches += 1
                # 部分一致
                elif any(keyword in word for word in candidate_words):
                    matches += 0.7
                # 類似性チェック（簡易版）
                elif any(abs(len(keyword) - len(word)) <= 2 and 
                        self._simple_similarity(keyword, word) > 0.8 
                        for word in candidate_words):
                    matches += 0.5
            
            return matches / len(target_keywords)
            
        except Exception as e:
            print(f"⚠️ 類似度計算エラー: {e}")
            return 0.0

    def _simple_similarity(self, str1: str, str2: str) -> float:
        """簡易文字列類似度計算"""
        try:
            if len(str1) == 0 or len(str2) == 0:
                return 0.0
            
            # 共通文字数の比率
            common_chars = set(str1) & set(str2)
            total_chars = set(str1) | set(str2)
            
            return len(common_chars) / len(total_chars) if total_chars else 0.0
            
        except:
            return 0.0

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