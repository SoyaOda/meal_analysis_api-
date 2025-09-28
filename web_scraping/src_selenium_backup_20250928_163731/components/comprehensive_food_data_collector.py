#!/usr/bin/env python3
"""
包括的食材データ収集コンポーネント
serving情報 + 栄養素情報を統合的に収集
"""

import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC


class ComprehensiveFoodDataCollector:
    """包括的食材データ収集クラス"""

    def __init__(self, driver, wait, config):
        """
        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
            config: 設定オブジェクト
        """
        self.driver = driver
        self.wait = wait
        self.config = config
        
        # 既存の成功コンポーネントを使用
        from .raw_serving_extractor import RawServingExtractor
        from .modal_handler import ModalHandler
        
        self.raw_serving_extractor = RawServingExtractor(driver)
        self.modal_handler = ModalHandler(driver)

    def collect_complete_food_data(self, food_name: str) -> Dict[str, Any]:
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
                "url": self.driver.current_url,
                "scraped_at": datetime.now().isoformat(),
                "serving_options": [],
                "nutrition_data": {},
                "collection_success": False
            }

            # 1. 栄養素情報収集（先に実行）
            print("🥗 栄養素情報収集中...")
            nutrition_data = self._extract_nutrition_data()
            
            # デバッグ: 栄養素データの受け渡し確認
            print(f"🔍 DEBUG: nutrition_data received: {type(nutrition_data)}")
            print(f"🔍 DEBUG: nutrition_data content: {nutrition_data}")
            
            food_data["nutrition_data"] = nutrition_data

            # 2. Serving情報収集（後に実行）
            print("🍽️ Serving情報収集中...")
            serving_options = self._extract_serving_options()
            
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

    def _extract_serving_options(self) -> Dict[str, Any]:
        """Serving情報を抽出（完全生データ保存方式）"""
        try:
            print("    🔄 Select Servingモーダルを開く...")
            
            # 栄養素展開後の状態をリセット - Pボタンを再度クリックして折りたたみ
            print("    📋 栄養素セクションを折りたたみ中...")
            try:
                p_element = self.driver.find_element(By.XPATH, "//div[text()='P']")
                if p_element.is_displayed():
                    p_element.click()
                    time.sleep(3)  # 安定化のため折りたたみ完了を待機
                    print("    ✅ 栄養素セクション折りたたみ完了")
            except Exception as e:
                print(f"    ⚠️ 栄養素折りたたみ警告: {e}")
            
            # 既存の成功コンポーネントを使用
            modal_opened = self.modal_handler.open_serving_modal()
            if not modal_opened:
                print("    ❌ モーダルが開けませんでした")
                return {}

            print("    ✅ Select Servingモーダルが開きました！")
            
            # 修正: 生データ保存方式のコンポーネントで情報を抽出
            serving_data = self.raw_serving_extractor.extract_raw_serving_options()
            
            # デバッグ: 実際の返り値を確認
            print(f"    🔍 DEBUG: serving_data type: {type(serving_data)}")
            print(f"    🔍 DEBUG: serving_data keys: {list(serving_data.keys()) if serving_data else 'None'}")
            if serving_data and 'total_servings_found' in serving_data:
                print(f"    🔍 DEBUG: Total servings found: {serving_data['total_servings_found']}")

            # モーダルを閉じる
            self.modal_handler.close_modal()

            total_servings = serving_data.get('total_servings_found', 0) if serving_data else 0
            print(f"    🎯 serving情報抽出完了: {total_servings}個")
            return serving_data

        except Exception as e:
            print(f"❌ Serving情報抽出エラー: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _extract_nutrition_data(self) -> Dict[str, Any]:
        """栄養素情報を抽出（Pボタンクリック方式）"""
        try:
            print("  🔍 栄養素データ抽出開始...")

            nutrition_data = {
                'food_grade': '',
                'detailed_nutrients': {},
                'extraction_method': 'P_button_expansion'
            }

            # 1. Food Grade取得
            nutrition_data['food_grade'] = self._extract_food_grade()
            print(f"  🔍 DEBUG: Food Grade: {nutrition_data['food_grade']}")

            # 2. Pボタンをクリックして栄養素情報を展開
            if self._click_P_button():
                print("  ✅ Pボタンクリック成功、栄養素情報展開")
                
                # 3. 展開された栄養素情報を取得
                detailed_nutrients = self._extract_detailed_nutrients_from_expanded()
                
                # デバッグ: 実際の返り値を確認
                print(f"  🔍 DEBUG: detailed_nutrients type: {type(detailed_nutrients)}")
                print(f"  🔍 DEBUG: detailed_nutrients keys: {list(detailed_nutrients.keys()) if detailed_nutrients else 'None'}")
                print(f"  🔍 DEBUG: detailed_nutrients length: {len(detailed_nutrients) if detailed_nutrients else 'None'}")
                
                nutrition_data['detailed_nutrients'] = detailed_nutrients
                
                print(f"  📊 栄養素データ取得完了: {len(detailed_nutrients)}種類")
            else:
                print("  ❌ Pボタンクリック失敗")

            # デバッグ: 最終的なnutrition_dataを確認
            print(f"  🔍 DEBUG: Final nutrition_data structure:")
            print(f"    - food_grade: {nutrition_data.get('food_grade', 'None')}")
            print(f"    - detailed_nutrients count: {len(nutrition_data.get('detailed_nutrients', {}))}")
            print(f"    - extraction_method: {nutrition_data.get('extraction_method', 'None')}")

            return nutrition_data

        except Exception as e:
            print(f"❌ 栄養素データ抽出エラー: {e}")
            import traceback
            traceback.print_exc()
            return {}


    def _extract_food_grade(self) -> str:
        """Food Gradeを抽出"""
        try:
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            texts = [elem.text.strip() for elem in all_elements if elem.text.strip()]

            for i, text in enumerate(texts):
                if text == 'Food Grade' and i + 1 < len(texts):
                    food_grade = texts[i + 1]
                    print(f"  📋 Food Grade: {food_grade}")
                    return food_grade

            print("  ⚠️ Food Grade情報が見つかりません")
            return ""

        except Exception as e:
            print(f"  ❌ Food Grade抽出エラー: {e}")
            return ""

    def _click_P_button(self) -> bool:
        """Pボタンをクリックして栄養素情報を展開"""
        try:
            print("  🎯 Pボタンを探してクリック中...")

            # Pボタンを探す（参考ファイルのロジック使用）
            p_element = self.driver.find_element(By.XPATH, "//div[text()='P']")
            
            if p_element.is_displayed():
                p_element.click()
                time.sleep(3)  # 安定化のため栄養素情報の展開を待機
                print("  ✅ Pボタンクリック完了")
                return True
            else:
                print("  ❌ Pボタンが表示されていません")
                return False

        except Exception as e:
            print(f"  ❌ Pボタンクリックエラー: {e}")
            return False

    def _extract_detailed_nutrients_from_expanded(self) -> Dict[str, Any]:
        """展開された栄養素情報から詳細データを抽出（生情報として全て保存）"""
        try:
            print("  🔍 展開された栄養素情報から詳細データ抽出中...")

            # 栄養素展開後の全テキストを取得
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            all_nutrition_texts = []
            
            for elem in all_elements:
                text = elem.text.strip()
                if text and len(text) <= 200:  # 長すぎるテキストは除外
                    # 栄養素らしいテキストを検出（数値+単位を含む）
                    import re
                    if re.search(r'\d+(?:\.\d+)?\s*(g|mg|µg|mcg|IU|%)', text, re.IGNORECASE):
                        all_nutrition_texts.append(text)
                        print(f"    📊 栄養素データ: {text}")

            # 生情報として全栄養素データを保存
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

            print(f"  ✅ 生栄養素データ抽出完了: {len(all_nutrition_texts)}個の栄養素情報")
            return detailed_nutrients

        except Exception as e:
            print(f"  ❌ 詳細栄養素抽出エラー: {e}")
            return {}

    def _extract_units_from_amount_section(self) -> Dict[str, Dict]:
        """Amount eatenセクションから単位データを抽出"""
        try:
            print("  🔍 Amount eaten セクションから単位データ抽出...")

            # 栄養素を折りたたむ
            self._collapse_all_nutrients()

            # Amount eaten要素を探す
            amount_elements = self.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'Amount eaten')]"
            )

            if not amount_elements:
                print("  ⚠️ Amount eaten要素が見つかりません")
                return {}

            # 単位データの辞書
            units_data = {}

            # 基本的な単位情報を抽出（簡易版）
            # ここは複雑なロジックなので、まずは基本的な実装
            print("  📋 基本単位情報を抽出（簡易版）")

            return units_data

        except Exception as e:
            print(f"  ❌ Amount eaten単位抽出エラー: {e}")
            return {}

    def _extract_units_via_select_serving(self) -> Dict[str, Dict]:
        """Select ServingモーダルからフォールバックでUnitsデータ取得"""
        try:
            print("  🔄 Select Servingモーダルから単位データ取得...")

            # モーダルを開く
            if self._open_serving_modal():
                # serving optionsから単位データを構築
                serving_options = self._extract_raw_serving_options()
                units_data = {}

                for option in serving_options:
                    # 簡易パース（カロリーと重量を抽出）
                    raw_text = option['raw_text']

                    # パターン解析（例: "cup 30cals / 245 g"）
                    if 'cals' in raw_text and 'g' in raw_text:
                        parts = raw_text.split()
                        unit_name = parts[0] if parts else 'unknown'

                        # カロリー抽出
                        cal_part = [p for p in parts if 'cals' in p]
                        calories = 0
                        if cal_part:
                            calories = int(''.join(filter(str.isdigit, cal_part[0])))

                        # 重量抽出
                        weight_g = 0
                        if '/' in raw_text:
                            weight_part = raw_text.split('/')[-1].strip()
                            weight_g = float(''.join(filter(lambda x: x.isdigit() or x == '.', weight_part)))

                        units_data[unit_name] = {
                            'calories': calories,
                            'weight_g': weight_g,
                            'source': 'select_serving_modal'
                        }

                # モーダルを閉じる
                self._close_modal_with_esc()

                print(f"  ✅ {len(units_data)}個の単位データを取得")
                return units_data

            return {}

        except Exception as e:
            print(f"  ❌ Select Serving単位抽出エラー: {e}")
            return {}

    def _collapse_all_nutrients(self):
        """全ての栄養素セクションを折りたたみ"""
        try:
            print("  🔽 栄養素セクションを折りたたみ中...")

            # 展開されている栄養素セクションを探す
            expand_buttons = self.driver.find_elements(
                By.XPATH, "//button[contains(@aria-expanded, 'true')]"
            )

            for button in expand_buttons:
                try:
                    if button.is_displayed():
                        button.click()
                        time.sleep(0.5)
                except:
                    continue

            print("  ✅ 栄養素折りたたみ完了")

        except Exception as e:
            print(f"  ⚠️ 栄養素折りたたみエラー: {e}")

    def _extract_detailed_nutrients(self) -> Dict[str, Any]:
        """詳細栄養素情報を抽出（簡易版）"""
        try:
            print("  🔍 詳細栄養素抽出（簡易版）...")

            # ページから栄養素テキストを抽出
            all_text = self.driver.find_element(By.TAG_NAME, "body").text

            # 基本的な栄養素パターンを探す
            nutrients = {}

            # カロリー
            if 'calories' in all_text.lower() or 'cals' in all_text.lower():
                nutrients['energy'] = 'found'

            # タンパク質
            if 'protein' in all_text.lower():
                nutrients['protein'] = 'found'

            # 炭水化物
            if 'carbohydrate' in all_text.lower() or 'carbs' in all_text.lower():
                nutrients['carbohydrate'] = 'found'

            # 脂質
            if 'fat' in all_text.lower():
                nutrients['fat'] = 'found'

            print(f"  📊 基本栄養素検出: {len(nutrients)}種類")
            return nutrients

        except Exception as e:
            print(f"  ❌ 詳細栄養素抽出エラー: {e}")
            return {}