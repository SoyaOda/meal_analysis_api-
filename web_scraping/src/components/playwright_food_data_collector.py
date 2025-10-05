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


import re

class PlaywrightFoodDataCollector:
    """Playwright版の包括的食品データコレクター"""

    def __init__(self, page: Page):
        """
        Args:
            page: Playwright Page instance
        """
        self.page = page

    def _is_valid_nutrition_data(self, nutrition_data: Dict[str, Any]) -> bool:
        """栄養データが有効かチェック（UIノイズでないか）"""
        if not nutrition_data or not isinstance(nutrition_data, dict):
            return False

        # raw_nutrition_dataをチェック
        raw_data = nutrition_data.get("raw_nutrition_data", [])
        if not raw_data or len(raw_data) < 5:
            return False

        # 有効な栄養素パターン（より厳格に）
        valid_nutrition_patterns = [
            r"Total Fat \d+\.?\d*g",
            r"Saturated Fat \d+\.?\d*g", 
            r"Trans Fat \d+\.?\d*g",
            r"Cholesterol \d+\.?\d*mg",
            r"Sodium \d+\.?\d*mg",
            r"Total Carbohydrate \d+\.?\d*g",
            r"Dietary Fiber \d+\.?\d*g",
            r"Total Sugars \d+\.?\d*g",
            r"Protein \d+\.?\d*g",
            r"Vitamin [A-Z] \d+\.?\d*",
            r"Calcium \d+\.?\d*mg",
            r"Iron \d+\.?\d*mg",
            r"\d+\.?\d* cal/g",
            r"\d+\.?\d* calories",
        ]

        # 無効データ指標（大幅に拡張）
        invalid_indicators = [
            # UIナビゲーション要素
            r"Meals", r"Dashboard", r"Plan", r"Food", r"Exercise",
            r"Today", r"Calorie Budget", r"Eaten", r"Left",
            r"Settings", r"Profile", r"Reports", r"Goals",
            
            # JavaScript/CSS関連
            r"var \w+ = ", r"\.Mui\w+-\w+-\d+", r"function\s*\(",
            r"MuiInputBase-input", r"jss\d+", r"makeStyles",
            r"\.css\-\w+", r"\.emotion\-\w+",
            
            # 法的・規約関連
            r"Privacy Policy", r"Terms of Service", r"Garmin linking",
            r"Legal", r"Copyright", r"All rights reserved",
            
            # 日付・時刻要素
            r"Sep \d+, \d+", r"September \d+", r"datePicke",
            r"chartStartDate", r"copyFoodEntry",
            
            # 一般的なノイズ要素
            r"^$", r"^\s+$", r"undefined", r"null", r"NaN",
            r"^[,\.\-\s]+$", r"^\d+$"  # 数字のみや記号のみ
        ]

        valid_count = 0
        invalid_count = 0
        total_items = len(raw_data)

        for item in raw_data:
            if isinstance(item, str):
                item_stripped = item.strip()
                if not item_stripped:  # 空文字列は無効
                    invalid_count += 1
                    continue
                
                # 有効な栄養素パターンをチェック
                found_valid = False
                for pattern in valid_nutrition_patterns:
                    if re.search(pattern, item_stripped, re.IGNORECASE):
                        valid_count += 1
                        found_valid = True
                        break
                
                # 無効データ指標をチェック（有効パターンが見つからなかった場合のみ）
                if not found_valid:
                    for pattern in invalid_indicators:
                        if re.search(pattern, item_stripped):
                            invalid_count += 1
                            break

        # より厳格な判定基準
        has_enough_nutrition = valid_count >= 8  # 最低8個の有効な栄養素
        invalid_ratio = invalid_count / total_items if total_items > 0 else 1
        has_low_noise = invalid_ratio < 0.2  # 無効データ比率20%未満
        has_minimal_total = total_items >= 10  # 最低10個のデータ項目

        print(f"🔍 栄養データ検証: 有効{valid_count}個, 無効{invalid_count}個, 比率{invalid_ratio:.2f}, 総数{total_items}")
        
        return has_enough_nutrition and has_low_noise and has_minimal_total

    def _is_valid_serving_data(self, serving_data: Dict[str, Any]) -> bool:
        """サービングデータが有効かチェック（UIノイズでないか）"""
        if not serving_data or not isinstance(serving_data, dict):
            return False

        raw_data = serving_data.get("raw_serving_data", [])
        if not raw_data or len(raw_data) < 3:
            return False

        # 有効なサービング形式パターン（より厳格に）
        valid_serving_patterns = [
            r"\d+\.?\d*\s*(cup|cups)\b",
            r"\d+\.?\d*\s*(oz|ounce|ounces)\b", 
            r"\d+\.?\d*\s*(g|gram|grams)\b",
            r"\d+\.?\d*\s*(ml|milliliter|milliliters)\b",
            r"\d+\.?\d*\s*(tsp|teaspoon|teaspoons)\b",
            r"\d+\.?\d*\s*(tbsp|tablespoon|tablespoons)\b",
            r"\d+\.?\d*\s*(piece|pieces)\b",
            r"\d+\.?\d*\s*(slice|slices)\b",
            r"\d+\.?\d*\s*(serving|servings)\b",
            r"\d+\.?\d*\s*(lb|pound|pounds)\b",
            r"\d+\.?\d*\s*(kg|kilogram|kilograms)\b",
            # 実際のMyNetDiaryで見つかったパターンを追加
            r"^(cup|tablespoon|teaspoon|gram|ml)$",  # 単位のみ
            r"^\d+\.\d+\s*more\s*servings$",         # "3 more servings"
            r"^Weight$",                             # "Weight" ラベル
            r"^\d+$",                               # 数値のみ（重量値など）
        ]

        # 無効データ指標（大幅に拡張）
        invalid_indicators = [
            # UIナビゲーション要素
            r"Meals", r"Dashboard", r"Plan", r"Food", r"Exercise",
            r"Today", r"Calorie Budget", r"Eaten", r"Left",
            r"Settings", r"Profile", r"Reports", r"Goals",
            
            # JavaScript/CSS関連
            r"var \w+ = ", r"\.Mui\w+-\w+-\d+", r"function\s*\(",
            r"MuiInputBase-input", r"jss\d+", r"makeStyles",
            r"\.css\-\w+", r"\.emotion\-\w+",
            
            # 法的・規約関連
            r"Privacy Policy", r"Terms of Service", r"Garmin linking",
            r"Legal", r"Copyright", r"All rights reserved",
            
            # 日付・時刻要素
            r"Sep \d+, \d+", r"September \d+", r"datePicke",
            r"chartStartDate", r"copyFoodEntry",
            
            # 一般的なノイズ要素
            r"^$", r"^\s+$", r"undefined", r"null", r"NaN",
            r"^[,\.\-\s]+$",  # 記号のみ
            
            # サービング特有のノイズ
            r"Enter eaten amount like", r"Enter staple food name",
            r"meal-select", r"LOG FOOD TO", r"BACK TO STAPLE FOODS",
            r"Hide Nutrients", r"Show all nutrients"
        ]

        valid_count = 0
        invalid_count = 0
        total_items = len(raw_data)

        for item in raw_data:
            if isinstance(item, str):
                item_stripped = item.strip()
                if not item_stripped:  # 空文字列は無効
                    invalid_count += 1
                    continue
                
                # 有効なサービング形式をチェック
                found_valid = False
                for pattern in valid_serving_patterns:
                    if re.search(pattern, item_stripped, re.IGNORECASE):
                        valid_count += 1
                        found_valid = True
                        break
                
                # 無効データ指標をチェック（有効パターンが見つからなかった場合のみ）
                if not found_valid:
                    for pattern in invalid_indicators:
                        if re.search(pattern, item_stripped):
                            invalid_count += 1
                            break

        # 現実的な判定基準に修正
        has_enough_servings = valid_count >= 3  # 最低3個の有効なサービング（5→3に緩和）
        invalid_ratio = invalid_count / total_items if total_items > 0 else 1
        has_low_noise = invalid_ratio < 0.7  # 無効データ比率70%未満（30%→70%に大幅緩和）
        has_minimal_total = total_items >= 5  # 最低5個のデータ項目（8→5に緩和）

        print(f"🔍 サービングデータ検証: 有効{valid_count}個, 無効{invalid_count}個, 比率{invalid_ratio:.2f}, 総数{total_items}")
        
        return has_enough_servings and has_low_noise and has_minimal_total

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

            # 3. データ品質チェック（UIノイズ検出）
            nutrition_valid = self._is_valid_nutrition_data(nutrition_data)
            serving_valid = self._is_valid_serving_data(serving_options)

            # 基本的な数量チェック
            nutrition_count = nutrition_data.get("detailed_nutrients", {}).get("total_nutrients_found", 0) if nutrition_data else 0
            serving_count = serving_options.get("total_servings_found", 0) if serving_options else 0

            # デバッグ情報出力
            print(f"📊 収集結果詳細:")
            print(f"   🥗 栄養素: {nutrition_count}種類 (品質: {'✅' if nutrition_valid else '❌'})")
            print(f"   🍽️ Serving: {serving_count}個 (品質: {'✅' if serving_valid else '❌'})")
            print(f"   📋 Food Grade: {nutrition_data.get('food_grade', 'なし') if nutrition_data else 'なし'}")

            # 厳格な成功判定（数量AND品質）
            success = (nutrition_count > 0 and nutrition_valid) or (serving_count > 0 and serving_valid)
            food_data["collection_success"] = success

            # 品質チェック結果を記録
            food_data["data_quality_check"] = {
                "nutrition_valid": nutrition_valid,
                "serving_valid": serving_valid,
                "quality_checked_at": datetime.now().isoformat()
            }

            # デバッグ: 最終的なfood_dataの構造確認
            print(f"🔍 DEBUG: Final food_data structure before return:")
            print(f"  - food_name: {food_data.get('food_name', 'None')}")
            print(f"  - serving_options keys: {list(serving_options.keys()) if serving_options else 'None'}")
            print(f"  - nutrition_data keys: {list(nutrition_data.keys()) if nutrition_data else 'None'}")
            print(f"  - collection_success: {food_data.get('collection_success', False)}")

            if success:
                print(f"✅ データ収集成功: Serving {serving_count}個 (品質: {'✅' if serving_valid else '❌'}), 栄養素 {nutrition_count}種類 (品質: {'✅' if nutrition_valid else '❌'})")
            else:
                if nutrition_count > 0 or serving_count > 0:
                    print(f"❌ データ収集失敗（品質不良）: Serving {serving_count}個 (品質: {'✅' if serving_valid else '❌'}), 栄養素 {nutrition_count}種類 (品質: {'✅' if nutrition_valid else '❌'})")
                else:
                    print(f"❌ データ収集失敗（データなし）: Serving {serving_count}個, 栄養素 {nutrition_count}種類")

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
        """Serving情報を抽出（改善版：ページ上のserving要素を直接取得）"""
        try:
            print("      🔍 改善版serving options抽出中（Playwright版）...")

            # 栄養素展開後の状態をリセット - Pボタンを再度クリックして折りたたみ
            print("      📋 栄養素セクションを折りたたみ中...")
            try:
                p_element = await self.page.query_selector("//div[text()='P']")
                if p_element:
                    is_visible = await p_element.is_visible()
                    if is_visible:
                        await p_element.click()
                        await asyncio.sleep(2)
                        print("      ✅ 栄養素セクション折りたたみ完了")
            except Exception as e:
                print(f"      ⚠️ 栄養素折りたたみ警告: {e}")

            # 「X more servings」リンクをクリックして全serving展開
            print("      🔍 'more servings'リンクを探してクリック...")
            try:
                all_clickable = await self.page.query_selector_all("a, button")
                
                clicked = False
                for elem in all_clickable:
                    try:
                        text = await elem.inner_text()
                        if 'more' in text.lower() and 'serving' in text.lower():
                            print(f"        ✅ リンク発見: '{text.strip()}'")
                            await elem.click()
                            await asyncio.sleep(3)  # 展開完了を待つ
                            clicked = True
                            break
                    except:
                        continue
                
                if clicked:
                    print("        ✅ 全serving情報を展開")
                else:
                    print("        ℹ️ 'more servings'リンクなし（全て表示済み）")
            except Exception as e:
                print(f"        ⚠️ リンククリックエラー: {e}")

            # ページ上のserving要素を取得（改善版）
            print("      📊 ページ上のserving要素を取得中...")
            
            # serving情報を含む要素を直接取得
            # パターン: "cup 488cals / 128 g" のような形式
            all_elements = await self.page.query_selector_all("button, div, span")
            
            all_serving_texts = []
            seen_texts = set()
            
            for elem in all_elements:
                try:
                    # 可視性チェック
                    is_visible = await elem.is_visible()
                    if not is_visible:
                        continue
                    
                    text = await elem.inner_text()
                    text = text.strip() if text else ""
                    
                    # serving情報のフィルター
                    # - 100文字以下
                    # - 既出でない  
                    # - 単位とカロリー/グラム情報を含む
                    if text and len(text) <= 100 and text not in seen_texts:
                        # "cup 488cals / 128 g" のようなパターンを検出
                        text_lower = text.lower()
                        
                        # 単位キーワード
                        unit_keywords = ['cup', 'tablespoon', 'tbsp', 'teaspoon', 'tsp',
                                       'gram', 'g', 'ml', 'oz', 'ounce', 'fl oz', 'lb',
                                       'serving', 'piece', 'slice']
                        
                        has_unit = any(keyword in text_lower for keyword in unit_keywords)
                        has_cals = 'cal' in text_lower
                        has_grams = ' g' in text_lower or '/g' in text_lower or text_lower.endswith('g')
                        has_number = any(char.isdigit() for char in text)
                        
                        # "cup 488cals / 128 g" のような完全な形式
                        # または "cup", "tablespoon" などの単位のみ
                        is_complete_serving = has_unit and has_cals and has_grams and has_number
                        is_unit_only = has_unit and len(text) < 20 and not has_cals
                        
                        if is_complete_serving or is_unit_only:
                            all_serving_texts.append(text)
                            seen_texts.add(text)
                except:
                    continue

            print(f"      📊 生データ収集完了: {len(all_serving_texts)}個の要素")
            
            # デバッグ用：最初の30個を表示
            print(f"      🔍 最初の30個のserving要素:")
            for i, text in enumerate(all_serving_texts[:30], 1):
                print(f"        [{i}] {text}")

            # 改善されたサービング抽出ロジックを適用
            print("      🧠 改善された抽出ロジック実行中...")
            improved_servings = self._extract_improved_serving_info(all_serving_texts)
            print(f"      ✅ 改善された抽出完了: {len(improved_servings)}個")

            # 生情報として全serving データを保存
            raw_serving_data = {
                'raw_serving_data': all_serving_texts,
                'extraction_method': 'page_based_serving_extraction',
                'total_servings_found': len(all_serving_texts),
                'improved_servings': improved_servings,
                'extracted_at': datetime.now().isoformat()
            }

            # 各serving テキストを個別エントリとしても保存
            for i, serving_text in enumerate(all_serving_texts, 1):
                raw_serving_data[f'serving_{i:03d}'] = serving_text

            print(f"      ✅ 改善版serving抽出完了: 生データ{len(all_serving_texts)}個 → 構造化{len(improved_servings)}個")
            return raw_serving_data

        except Exception as e:
            print(f"      ❌ 改善版serving options抽出エラー: {e}")
            import traceback
            print(f"      🔍 詳細エラー: {traceback.format_exc()}")
            return {}

    def _extract_improved_serving_info(self, raw_data: List[str]) -> List[Dict[str, Any]]:
        """改善されたサービング情報抽出（直接パターンマッチを優先）"""
        
        print(f"      🔬 改善版抽出開始: 生データ{len(raw_data)}個")
        
        # 1. まず直接パターンマッチを試行（最優先）
        direct_servings = self._extract_direct_serving_patterns(raw_data)
        print(f"      📋 直接パターンマッチ: {len(direct_servings)}個")
        
        if len(direct_servings) > 0:
            # 直接パターンで取得できた場合はそれを使用
            for i, serving in enumerate(direct_servings, 1):
                print(f"        {i}. {serving.get('display_text', 'N/A')}")
            return direct_servings
        
        # 2. 直接パターンで取得できない場合は従来の方法
        print(f"      ℹ️ 直接パターンなし、従来方式を適用")
        
        unit_keywords = [
            'cup', 'tablespoon', 'tbsp', 'teaspoon', 'tsp',
            'gram', 'g', 'ml', 'oz', 'ounce', 'serving',
            'piece', 'slice', 'medium', 'large', 'small'
        ]

        # 基本情報の抽出
        serving_size_info = self._extract_serving_size_info_from_raw(raw_data)
        print(f"      📏 基本情報: {serving_size_info}")
        
        # Amount eaten ドロップダウン情報の抽出
        dropdown_units = self._extract_dropdown_units_from_raw(raw_data, unit_keywords)
        print(f"      📋 ドロップダウン単位: {dropdown_units}")
        
        # 重量・カロリー情報の抽出
        weight_calorie_info = self._extract_weight_calorie_info_from_raw(raw_data)
        print(f"      ⚖️ 重量・カロリー: {weight_calorie_info}")
        
        # 組み合わせてサービング情報を構築
        serving_options = self._build_serving_options_from_data(
            serving_size_info, dropdown_units, weight_calorie_info
        )
        
        print(f"      🎯 構築結果: {len(serving_options)}個のサービング")
        for i, option in enumerate(serving_options, 1):
            print(f"        {i}. {option.get('display_text', 'N/A')}")

        return serving_options

    def _extract_serving_size_info_from_raw(self, raw_data: List[str]) -> Dict[str, Any]:
        """基本のServing Size情報を抽出"""
        serving_info = {}
        data_str = ' '.join(raw_data)

        # "Serving Size cup (128g)" パターンを探す
        import re
        serving_size_pattern = r'Serving Size\s+([a-zA-Z\s]+?)\s*\((\d+(?:\.\d+)?)g?\)'
        match = re.search(serving_size_pattern, data_str)

        if match:
            unit = match.group(1).strip()
            weight = float(match.group(2))
            serving_info = {
                'base_unit': unit,
                'base_weight_g': weight,
                'pattern': 'serving_size'
            }

        return serving_info

    def _extract_dropdown_units_from_raw(self, raw_data: List[str], unit_keywords: List[str]) -> List[str]:
        """Amount eaten ドロップダウンの単位を抽出"""
        dropdown_units = []
        found_amount_eaten = False
        collection_window = 0

        for i, item in enumerate(raw_data):
            item_str = str(item).strip().lower()

            # Amount eaten の発見
            if 'amount eaten' in item_str:
                found_amount_eaten = True
                collection_window = 0
                continue

            # Amount eaten の後で単位語を探す（10要素以内）
            if found_amount_eaten:
                collection_window += 1

                # 単位語の判定
                for unit in unit_keywords:
                    if unit.lower() == item_str:
                        dropdown_units.append(item_str)
                        break

                # "3 more servings" のような終了パターン
                if 'more serving' in item_str:
                    break

                # 10個以上離れたら終了
                if collection_window > 10:
                    break

        return dropdown_units

    def _extract_weight_calorie_info_from_raw(self, raw_data: List[str]) -> Dict[str, Any]:
        """重量とカロリー情報を抽出"""
        info = {}
        data_str = ' '.join(raw_data)

        import re
        # "488 cals" パターン
        calorie_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*cals?'
        calorie_matches = re.findall(calorie_pattern, data_str)

        # "Weight 128 g" パターン
        weight_pattern = r'Weight\s+(\d+(?:\.\d+)?)\s*g'
        weight_match = re.search(weight_pattern, data_str)

        if calorie_matches:
            # 最初の（通常は主要な）カロリー値を使用
            main_calories = float(calorie_matches[0].replace(',', ''))
            info['main_calories'] = main_calories

        if weight_match:
            main_weight = float(weight_match.group(1))
            info['main_weight_g'] = main_weight

            # カロリー密度を計算
            if 'main_calories' in info:
                info['calories_per_gram'] = info['main_calories'] / main_weight

        return info

    def _extract_direct_serving_patterns(self, raw_data: List[str]) -> List[Dict[str, Any]]:
        """Raw dataから直接 'unit Xcals / Yg' パターンを抽出"""
        import re
        
        servings = []
        
        # パターン: "tsp 0cals / 3.2 g" または "cup 488cals / 128 g"
        pattern = r'([a-zA-Z\s\.]+?)\s+(\d+(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g'
        
        for text in raw_data:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                unit = match.group(1).strip()
                calories = float(match.group(2))
                grams = float(match.group(3))
                
                # 有効な単位かチェック
                unit_clean = unit.lower()
                valid_units = ['cup', 'tablespoon', 'tbsp', 'teaspoon', 'tsp', 
                              'gram', 'g', 'ml', 'oz', 'ounce', 'fl oz', 'lb',
                              'serving', 'piece', 'slice']
                
                if any(valid in unit_clean for valid in valid_units):
                    calories_per_gram = calories / grams if grams > 0 else 0
                    
                    servings.append({
                        'unit': unit_clean.replace('.', '').strip(),
                        'calories_per_unit': calories,
                        'grams_per_unit': grams,
                        'conversion_factor': grams,
                        'calories_per_gram': round(calories_per_gram, 4),
                        'display_text': f"1 {unit_clean} ({grams}g) = {calories} kcal",
                        'source': 'direct_pattern_match'
                    })
        
        # 重複削除（同じ単位は最初のものを保持）
        unique_servings = []
        seen_units = set()
        for serving in servings:
            unit_key = serving['unit'].lower()
            if unit_key not in seen_units:
                seen_units.add(unit_key)
                unique_servings.append(serving)
        
        return unique_servings

    def _build_serving_options_from_data(self, serving_size_info: Dict, dropdown_units: List[str],
                                       weight_calorie_info: Dict) -> List[Dict[str, Any]]:
        """サービング情報を組み合わせて構築"""
        serving_options = []

        # 基本情報があるかチェック
        if not weight_calorie_info.get('calories_per_gram'):
            return serving_options

        base_unit = serving_size_info.get('base_unit', 'cup')
        base_weight = serving_size_info.get('base_weight_g', 128)
        base_calories = weight_calorie_info.get('main_calories', 488)
        calories_per_gram = weight_calorie_info['calories_per_gram']

        # 1. 基本単位を追加
        serving_options.append({
            'unit': base_unit,
            'calories_per_unit': base_calories,
            'grams_per_unit': base_weight,
            'conversion_factor': base_weight,
            'calories_per_gram': round(calories_per_gram, 4),
            'display_text': f"1 {base_unit} ({base_weight}g) = {base_calories} kcal",
            'source': 'serving_size_info'
        })

        # 2. 標準変換単位を追加
        unit_conversions = {
            'tablespoon': 8,      # 1 tablespoon ≈ 8g (flour)
            'tbsp': 8,
            'teaspoon': 2.7,      # 1 teaspoon ≈ 2.7g (flour)
            'tsp': 2.7,
            'gram': 1,
            'g': 1,
            'ml': 0.5,            # cornstarch density ≈ 0.5g/ml
            'oz': 28.3,           # 1 oz = 28.3g
            'ounce': 28.3
        }

        # ドロップダウンから見つかった単位で標準変換を適用
        for unit in dropdown_units:
            unit_clean = unit.lower().strip()
            if unit_clean in unit_conversions and unit_clean != base_unit.lower():
                unit_weight = unit_conversions[unit_clean]
                unit_calories = round(unit_weight * calories_per_gram, 1)

                serving_options.append({
                    'unit': unit_clean,
                    'calories_per_unit': unit_calories,
                    'grams_per_unit': unit_weight,
                    'conversion_factor': unit_weight,
                    'calories_per_gram': round(calories_per_gram, 4),
                    'display_text': f"1 {unit_clean} ({unit_weight}g) = {unit_calories} kcal",
                    'source': 'standard_conversion'
                })

        # 3. 重複削除とソート
        unique_options = []
        seen_units = set()

        for option in serving_options:
            unit_key = option['unit'].lower()
            if unit_key not in seen_units:
                seen_units.add(unit_key)
                unique_options.append(option)

        # gram を最初に、その後アルファベット順
        def sort_key(option):
            unit = option['unit'].lower()
            if unit in ['gram', 'g']:
                return '0_gram'
            return f'1_{unit}'

        unique_options.sort(key=sort_key)

        return unique_options

    async def _try_open_serving_modal(self) -> bool:
        """Select Servingモーダルを開く試行（複数セレクタ対応版）"""
        try:
            print("        🔍 Select Servingモーダル開く試行中...")

            # 複数のセレクタパターンを試行（優先度順）
            # デバッグで動作確認済みセレクタを最優先に配置
            selectors_to_try = [
                # 1. デバッグで動作確認済み（最優先）
                "//*[contains(text(), 'Amount')]/..//input",
                "//*[contains(text(), 'eaten')]/..//input",
                
                # 2. Amount eaten テキストベース（従来）
                "//*[contains(text(), 'Amount eaten')]",
                
                # 3. placeholder属性ベース（推奨）
                "//input[@placeholder='Amount eaten']",
                "//input[contains(@placeholder, 'Amount')]",
                
                # 4. MUI/React系セレクタ
                "//input[contains(@class, 'MuiInputBase-input')]",
                "//div[contains(@class, 'MuiTextField-root')]//input",
                
                # 5. フォーム系セレクタ
                "//input[@type='number']",
                "//input[@name='amount']",
                "//input[contains(@id, 'amount')]",
                
                # 6. 汎用入力フィールド
                "//input[@type='text']",
                "//input[not(@type)]"
            ]

            for i, selector in enumerate(selectors_to_try):
                try:
                    print(f"        🎯 セレクタ {i+1}/{len(selectors_to_try)}: {selector}")
                    
                    elements = await self.page.query_selector_all(selector)
                    if not elements:
                        print(f"        ❌ 要素なし")
                        continue
                    
                    print(f"        ✅ {len(elements)}個の要素を発見")
                    
                    for j, element in enumerate(elements):
                        try:
                            is_visible = await element.is_visible()
                            is_enabled = await element.is_enabled()
                            
                            if not (is_visible and is_enabled):
                                print(f"        ⚠️ 要素{j+1}: 不可視または無効")
                                continue
                            
                            print(f"        🎯 要素{j+1}で試行: 可視={is_visible}, 有効={is_enabled}")
                            
                            # 要素の属性情報を取得（デバッグ用）
                            placeholder = await element.get_attribute('placeholder') or ''
                            element_type = await element.get_attribute('type') or ''
                            print(f"          📋 属性: placeholder='{placeholder}', type='{element_type}'")
                            
                            # 既存モーダルを閉じる
                            await self._close_any_open_modal_for_serving()

                            # アプローチ1: 直接クリック
                            try:
                                await element.scroll_into_view_if_needed()
                                await asyncio.sleep(1)
                                await element.click()
                                await asyncio.sleep(2)
                                
                                if await self._is_modal_open():
                                    print(f"        ✅ 成功! セレクタ{i+1}・要素{j+1}で直接クリック")
                                    return True
                            except Exception as click_error:
                                print(f"          ❌ 直接クリック失敗: {click_error}")

                            # アプローチ2: 親要素経由（Selenium版互換）
                            try:
                                parent_level2 = await element.query_selector("../..")
                                if parent_level2:
                                    await parent_level2.scroll_into_view_if_needed()
                                    await asyncio.sleep(1)
                                    await parent_level2.click()
                                    await asyncio.sleep(2)
                                    
                                    if await self._is_modal_open():
                                        print(f"        ✅ 成功! セレクタ{i+1}・要素{j+1}で親要素クリック")
                                        return True
                            except Exception as parent_error:
                                print(f"          ❌ 親要素クリック失敗: {parent_error}")
                            
                            # アプローチ3: フォーカス+エンター
                            try:
                                await element.focus()
                                await asyncio.sleep(0.5)
                                await self.page.keyboard.press("Enter")
                                await asyncio.sleep(2)
                                
                                if await self._is_modal_open():
                                    print(f"        ✅ 成功! セレクタ{i+1}・要素{j+1}でフォーカス+エンター")
                                    return True
                            except Exception as focus_error:
                                print(f"          ❌ フォーカス+エンター失敗: {focus_error}")

                        except Exception as element_error:
                            print(f"        ⚠️ 要素{j+1}処理エラー: {element_error}")
                            continue

                except Exception as selector_error:
                    print(f"        ❌ セレクタ{i+1}エラー: {selector_error}")
                    continue

            print("        ❌ 全てのセレクタでAmount eaten要素が見つかりませんでした")
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