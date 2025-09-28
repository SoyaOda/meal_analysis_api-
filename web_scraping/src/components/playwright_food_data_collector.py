#!/usr/bin/env python3
"""
Playwright版の包括的食品データコレクター
ChromeDriverクラッシュ問題を根本的に解決
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from playwright.async_api import Page


class PlaywrightFoodDataCollector:
    """Playwright版の包括的食品データコレクター"""

    def __init__(self, page: Page):
        """
        Args:
            page: Playwright Page instance
        """
        self.page = page

    async def collect_complete_food_data(self, food_name: str) -> Dict[str, Any]:
        """
        指定食材の完全なデータを収集
        処理順序: 栄養素情報 → serving情報（モーダル干渉回避）

        Args:
            food_name: 食材名

        Returns:
            Dict: 包括的な食材データ
        """
        try:
            print(f"📊 包括的データ収集開始: {food_name[:50]}...")

            # 基本情報
            food_data = {
                "food_name": food_name,
                "url": self.page.url,
                "scraped_at": datetime.now().isoformat(),
                "serving_options": [],
                "nutrition_data": {},
                "collection_success": False
            }

            # 1. 栄養素情報収集（先に実行）
            print("🥗 栄養素情報収集中...")
            nutrition_data = await self._extract_nutrition_data()

            # デバッグ: 栄養素データの受け渡し確認
            print(f"🔍 DEBUG: nutrition_data received: {type(nutrition_data)}")
            print(f"🔍 DEBUG: nutrition_data content: {nutrition_data}")

            food_data["nutrition_data"] = nutrition_data

            # 2. Serving情報収集（後に実行）
            print("🍽️ Serving情報収集中...")
            serving_options = await self._extract_serving_options()

            # デバッグ: serving_optionsの受け渡し確認
            print(f"🔍 DEBUG: serving_options received: {type(serving_options)}")
            print(f"🔍 DEBUG: serving_options content: {serving_options}")

            food_data["serving_options"] = serving_options

            # 3. 成功判定（生データベースで判定）
            # 栄養素データの判定（生データ構造に対応）
            nutrition_count = nutrition_data.get("detailed_nutrients", {}).get("total_nutrients_found", 0) if nutrition_data else 0

            # Servingデータの判定（生データ構造に対応）
            serving_count = serving_options.get("total_servings_found", 0) if serving_options else 0

            # デバッグ情報出力
            print(f"📊 収集結果詳細:")
            print(f"   🥗 栄養素: {nutrition_count}種類")
            print(f"   🍽️ Serving: {serving_count}個")
            print(f"   📋 Food Grade: {nutrition_data.get('food_grade', 'なし') if nutrition_data else 'なし'}")

            # より柔軟な成功判定（どちらか一方でも取得できていれば成功）
            success = nutrition_count > 0 or serving_count > 0
            food_data["collection_success"] = success

            # デバッグ: 最終的なfood_dataの構造確認
            print(f"🔍 DEBUG: Final food_data structure before return:")
            print(f"  - food_name: {food_data.get('food_name', 'None')}")
            print(f"  - serving_options keys: {list(serving_options.keys()) if serving_options else 'None'}")
            print(f"  - nutrition_data keys: {list(nutrition_data.keys()) if nutrition_data else 'None'}")
            print(f"  - collection_success: {food_data.get('collection_success', False)}")

            if success:
                print(f"✅ データ収集成功: Serving {serving_count}個, 栄養素 {nutrition_count}種類")
            else:
                print(f"❌ データ収集失敗: Serving {serving_count}個, 栄養素 {nutrition_count}種類")

            return food_data

        except Exception as e:
            print(f"❌ データ収集エラー: {e}")
            import traceback
            traceback.print_exc()
            return {
                "food_name": food_name,
                "error": str(e),
                "collection_success": False,
                "scraped_at": datetime.now().isoformat()
            }

    async def _extract_nutrition_data(self) -> Dict[str, Any]:
        """栄養素情報を抽出"""
        try:
            print("      🔍 栄養素データ抽出中（Playwright版）...")

            # ページが完全に読み込まれるまで待機
            await self.page.wait_for_load_state("networkidle")

            # 詳細栄養素表示のためにPボタンをクリック
            await self._click_P_button()

            # 展開された栄養素データを抽出
            nutrition_data = await self._extract_detailed_nutrients_from_expanded()

            # Food Gradeも抽出
            food_grade = await self._extract_food_grade()
            nutrition_data["food_grade"] = food_grade

            return nutrition_data

        except Exception as e:
            print(f"      ❌ 栄養素データ抽出エラー: {e}")
            return {}

    async def _click_P_button(self) -> bool:
        """Pボタンをクリックして詳細栄養素を展開（Selenium版と同じロジック）"""
        try:
            print("        🔘 Pボタンクリック試行中...")

            # Selenium版と全く同じセレクター：//div[text()='P']
            try:
                p_element = await self.page.query_selector("//div[text()='P']")
                if p_element:
                    is_visible = await p_element.is_visible()
                    if is_visible:
                        await p_element.click()
                        await asyncio.sleep(3)  # Selenium版と同じ待機時間
                        print("        ✅ Pボタンクリック成功")
                        return True
                    else:
                        print("        ❌ Pボタンが表示されていません")
                        return False
                else:
                    print("        ❌ Pボタンが見つかりません")
                    return False
            except Exception as e:
                print(f"        ❌ Pボタンクリックエラー: {e}")
                return False

        except Exception as e:
            print(f"        ❌ Pボタンクリック処理エラー: {e}")
            return False

    async def _extract_detailed_nutrients_from_expanded(self) -> Dict[str, Any]:
        """展開された詳細栄養素データを抽出（Selenium版と同じ：生データ保存のみ）"""
        try:
            print("        📊 展開された栄養素データ抽出中...")

            # Selenium版と同じ：ページ内の全テキスト要素を取得
            all_elements = await self.page.query_selector_all("//*[text()]")
            all_nutrition_texts = []
            
            for elem in all_elements:
                try:
                    text = await elem.text_content()
                    text = text.strip() if text else ""
                    
                    # Selenium版と同じ：200文字以下のテキストのみ、フィルタリングなし
                    if text and len(text) <= 200:
                        all_nutrition_texts.append(text)
                        print(f"          📊 栄養素データ: {text}")

                except Exception as e:
                    continue

            # 生情報として全栄養素データを保存（Selenium版と同じ構造）
            detailed_nutrients = {
                'raw_nutrition_data': all_nutrition_texts,
                'extraction_method': 'raw_data_all_nutrients',
                'total_nutrients_found': len(all_nutrition_texts),
                'extracted_at': datetime.now().isoformat()
            }

            # 各栄養素テキストを個別エントリとしても保存
            for i, nutrition_text in enumerate(all_nutrition_texts, 1):
                detailed_nutrients[f'nutrient_{i:02d}'] = {
                    'raw_text': nutrition_text,
                    'sequence': i,
                    'extracted_at': datetime.now().isoformat()
                }

            print(f"        ✅ 詳細栄養素データ抽出完了: {len(all_nutrition_texts)}個の栄養素情報")

            return {
                'detailed_nutrients': detailed_nutrients,
                'extraction_method': 'playwright_raw_data',
                'total_sections': 1
            }

        except Exception as e:
            print(f"        ❌ 詳細栄養素抽出エラー: {e}")
            return {}

    async def _extract_food_grade(self) -> str:
        """Food Gradeを抽出"""
        try:
            # Food Grade候補テキストを検索
            grade_selectors = [
                "//*[contains(text(), 'Grade:')]",
                "//*[contains(text(), 'grade')]",
                "//*[contains(@class, 'grade')]"
            ]

            for selector in grade_selectors:
                try:
                    grade_element = await self.page.query_selector(selector)
                    if grade_element:
                        grade_text = await grade_element.text_content()
                        grade_text = grade_text.strip() if grade_text else ""

                        import re
                        grade_match = re.search(r'Grade:\s*([A-F][+-]?)', grade_text, re.IGNORECASE)
                        if grade_match:
                            return grade_match.group(1)

                except:
                    continue

            return "N/A"

        except Exception as e:
            print(f"        ⚠️ Food Grade抽出エラー: {e}")
            return "N/A"

    async def _extract_serving_options(self) -> Dict[str, Any]:
        """Serving情報を抽出（Selenium版と同じ：生データ保存のみ）"""
        try:
            print("      🔍 生serving options抽出中（Playwright版）...")

            # Selenium版と同じく、栄養素展開後の状態をリセット - Pボタンを再度クリックして折りたたみ
            print("      📋 栄養素セクションを折りたたみ中...")
            try:
                # Selenium版と同じセレクター：//div[text()='P']
                p_element = await self.page.query_selector("//div[text()='P']")
                if p_element:
                    is_visible = await p_element.is_visible()
                    if is_visible:
                        await p_element.click()
                        await asyncio.sleep(3)  # 安定化のため折りたたみ完了を待機
                        print("      ✅ 栄養素セクション折りたたみ完了")
            except Exception as e:
                print(f"      ⚠️ 栄養素折りたたみ警告: {e}")

            # "Select Serving"モーダルを開く試行
            await self._try_open_serving_modal()

            # モーダル内の全テキストを取得（Selenium版と同じ：フィルタリングなし）
            all_elements = await self.page.query_selector_all("//*[text()]")
            all_serving_texts = []

            for elem in all_elements:
                try:
                    text = await elem.text_content()
                    text = text.strip() if text else ""

                    # Selenium版と同じ：100文字以下のテキストのみ、フィルタリングなし
                    if text and len(text) <= 100:
                        all_serving_texts.append(text)
                        print(f"        📊 Servingデータ: {text}")

                except:
                    continue

            # 生情報として全serving データを保存（Selenium版と同じ構造）
            raw_serving_data = {
                'raw_serving_data': all_serving_texts,
                'extraction_method': 'raw_data_all_servings',
                'total_servings_found': len(all_serving_texts),
                'extracted_at': datetime.now().isoformat()
            }

            # 各serving テキストを個別エントリとしても保存
            for i, serving_text in enumerate(all_serving_texts, 1):
                raw_serving_data[f'serving_{i:02d}'] = {
                    'raw_text': serving_text,
                    'sequence': i,
                    'extracted_at': datetime.now().isoformat()
                }

            print(f"      ✅ 生servingデータ抽出完了: {len(all_serving_texts)}個のserving情報")
            return raw_serving_data

        except Exception as e:
            print(f"      ❌ 生serving options抽出エラー: {e}")
            return {}

    async def _try_open_serving_modal(self) -> bool:
        """Select Servingモーダルを開く試行（Selenium版と同じロジック）"""
        try:
            print("        🔍 Select Servingモーダル開く試行中...")

            # Selenium版と同じく「Amount eaten」要素を探してクリック
            amount_elements = await self.page.query_selector_all("//*[contains(text(), 'Amount eaten')]")

            for element in amount_elements:
                try:
                    is_visible = await element.is_visible()
                    if is_visible:
                        # 親要素レベル2を取得（クリック可能エリア）
                        parent_level2 = await element.query_selector("../..")
                        
                        if parent_level2:
                            # 既存モーダルを閉じる
                            await self._close_any_open_modal_for_serving()

                            # スクロールしてクリック実行
                            await parent_level2.scroll_into_view_if_needed()
                            await asyncio.sleep(1)
                            await parent_level2.click()
                            await asyncio.sleep(3)

                            # モーダルが開いたかチェック
                            if await self._is_modal_open():
                                print("        ✅ Select Servingモーダルが開きました！")
                                return True
                            else:
                                print("        ❌ Select Servingモーダルが開きませんでした")
                                return False

                except Exception as e:
                    print(f"        ⚠️ Amount eaten要素処理エラー: {e}")
                    continue

            print("        ❌ Amount eaten要素が見つかりませんでした")
            return False

        except Exception as e:
            print(f"        ⚠️ Servingモーダル開閉エラー: {e}")
            return False

    async def _close_any_open_modal_for_serving(self) -> bool:
        """serving収集用のモーダル閉じ機能"""
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
            print(f"        ⚠️ モーダル閉じエラー: {e}")
            return False

    async def _is_modal_open(self) -> bool:
        """モーダルが開いているかチェック"""
        try:
            # モーダル関連のセレクターをチェック
            modal_selectors = [
                "//*[@role='dialog']",
                "//div[contains(@class, 'modal')]",
                "//div[contains(@class, 'Modal')]",
                "//*[contains(text(), 'Select Serving')]"
            ]

            for selector in modal_selectors:
                try:
                    modal_element = await self.page.query_selector(selector)
                    if modal_element:
                        is_visible = await modal_element.is_visible()
                        if is_visible:
                            return True
                except:
                    continue

            return False

        except Exception as e:
            print(f"        ⚠️ モーダル状態チェックエラー: {e}")
            return False