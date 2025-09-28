#!/usr/bin/env python3
"""
食材カタログ管理コンポーネント
全カテゴリの食材リストを収集・管理し、任意の食材への直接遷移を可能にする
"""

import time
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, List, Optional, Tuple


class FoodCatalogManager:
    """食材カタログの収集・管理・検索を行うコンポーネント"""

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
        self.categories = []

    def discover_all_categories(self) -> List[Dict]:
        """
        全カテゴリを発見して収集

        Returns:
            List[Dict]: カテゴリ情報のリスト
        """
        try:
            print("🔍 全カテゴリを発見中...")

            # My Foods画面に移動
            my_foods_url = f"{self.config.BASE_URL}/meals.do#ff"
            self.driver.get(my_foods_url)
            time.sleep(self.config.REQUEST_DELAY)

            # My Foods ボタンクリック
            my_foods_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
            )
            my_foods_btn.click()
            time.sleep(self.config.REQUEST_DELAY)

            categories = []

            # メインカテゴリを発見
            main_categories = [
                "Staple Foods",
                "Recipes",
                "My Custom Foods"
            ]

            for main_category in main_categories:
                try:
                    print(f"  📂 {main_category}カテゴリを調査中...")

                    # メインカテゴリをクリック
                    main_cat_element = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, f"//span[text()='{main_category}']"))
                    )
                    main_cat_element.click()
                    time.sleep(self.config.REQUEST_DELAY)

                    # サブカテゴリを発見
                    if main_category == "Staple Foods":
                        sub_categories = self._discover_staple_food_subcategories()
                        categories.extend(sub_categories)

                except Exception as e:
                    print(f"    ⚠️ {main_category}カテゴリエラー: {e}")
                    continue

            self.categories = categories
            print(f"✅ カテゴリ発見完了: {len(categories)}個")
            return categories

        except Exception as e:
            print(f"❌ カテゴリ発見エラー: {e}")
            return []

    def _discover_staple_food_subcategories(self) -> List[Dict]:
        """Staple Foodsのサブカテゴリを発見"""
        try:
            subcategories = []

            # サブカテゴリ要素を取得
            subcat_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'MuiList')]//span[contains(@class, 'MuiListItemText')]"
            )

            for element in subcat_elements:
                try:
                    category_name = element.text.strip()
                    if category_name and len(category_name) > 2:  # 有効なカテゴリ名
                        subcategory = {
                            "main_category": "Staple Foods",
                            "sub_category": category_name,
                            "xpath": f"//span[text()='{category_name}']",
                            "discovered_at": datetime.now().isoformat()
                        }
                        subcategories.append(subcategory)
                        print(f"    📋 発見: {category_name}")

                except Exception as e:
                    print(f"    ⚠️ サブカテゴリ要素エラー: {e}")
                    continue

            return subcategories

        except Exception as e:
            print(f"    ❌ サブカテゴリ発見エラー: {e}")
            return []

    def collect_all_foods_from_category(self, category: Dict) -> List[Dict]:
        """
        指定カテゴリから全食材を収集

        Args:
            category: カテゴリ情報

        Returns:
            List[Dict]: 食材情報のリスト
        """
        try:
            print(f"🥗 {category['sub_category']}から食材収集中...")

            # カテゴリに移動
            success = self._navigate_to_category(category)
            if not success:
                return []

            foods = []
            page_num = 1
            max_pages = 50  # 安全装置

            while page_num <= max_pages:
                print(f"  📄 ページ{page_num}を処理中...")

                # 現在ページの食材を取得
                page_foods = self._extract_foods_from_current_page(category, page_num)
                if not page_foods:
                    print(f"  ✅ ページ{page_num}: 食材なし（収集完了）")
                    break

                foods.extend(page_foods)
                print(f"  ✅ ページ{page_num}: {len(page_foods)}個の食材を収集")

                # 次のページがあるかチェック
                if not self._has_next_page():
                    print(f"  🏁 最終ページ{page_num}に到達")
                    break

                # 次のページに移動
                if not self._go_to_next_page():
                    print(f"  ❌ 次のページへの移動失敗")
                    break

                page_num += 1

            print(f"✅ {category['sub_category']}: 総{len(foods)}個の食材を収集")
            return foods

        except Exception as e:
            print(f"❌ 食材収集エラー: {e}")
            return []

    def _navigate_to_category(self, category: Dict) -> bool:
        """指定カテゴリに移動"""
        try:
            # Staple Foodsをクリック
            staple_foods = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
            )
            staple_foods.click()
            time.sleep(self.config.REQUEST_DELAY)

            # サブカテゴリをクリック
            sub_category = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, category['xpath']))
            )
            sub_category.click()
            time.sleep(self.config.REQUEST_DELAY)

            return True

        except Exception as e:
            print(f"    ❌ カテゴリ移動エラー: {e}")
            return False

    def _extract_foods_from_current_page(self, category: Dict, page_num: int) -> List[Dict]:
        """現在ページから食材を抽出"""
        try:
            # 食材要素を取得
            food_elements = self.driver.find_elements(
                By.XPATH,
                "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
            )

            foods = []
            for i, element in enumerate(food_elements):
                try:
                    food_text = element.text.strip()
                    if food_text:
                        food_info = {
                            "food_name": food_text,
                            "category": category['sub_category'],
                            "main_category": category['main_category'],
                            "page_number": page_num,
                            "position_in_page": i + 1,
                            "xpath": f"//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')][{i + 1}]",
                            "collected_at": datetime.now().isoformat()
                        }
                        foods.append(food_info)

                except Exception as e:
                    print(f"      ⚠️ 食材{i+1}抽出エラー: {e}")
                    continue

            return foods

        except Exception as e:
            print(f"    ❌ ページ食材抽出エラー: {e}")
            return []

    def _has_next_page(self) -> bool:
        """次のページがあるかチェック"""
        try:
            # ページネーション要素を探す
            next_buttons = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@aria-label, 'next') or contains(text(), 'Next') or contains(text(), '次')]"
            )

            for button in next_buttons:
                if button.is_enabled() and button.is_displayed():
                    return True

            return False

        except Exception as e:
            print(f"      ⚠️ 次ページチェックエラー: {e}")
            return False

    def _go_to_next_page(self) -> bool:
        """次のページに移動"""
        try:
            # 次ページボタンをクリック
            next_buttons = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@aria-label, 'next') or contains(text(), 'Next') or contains(text(), '次')]"
            )

            for button in next_buttons:
                if button.is_enabled() and button.is_displayed():
                    button.click()
                    time.sleep(self.config.REQUEST_DELAY)
                    return True

            return False

        except Exception as e:
            print(f"      ❌ 次ページ移動エラー: {e}")
            return False

    def build_complete_catalog(self) -> Dict:
        """全カテゴリの完全カタログを構築"""
        try:
            print("🏗️ 完全食材カタログを構築中...")

            # カテゴリを発見
            categories = self.discover_all_categories()
            if not categories:
                print("❌ カテゴリ発見失敗")
                return {}

            catalog = {
                "catalog_info": {
                    "created_at": datetime.now().isoformat(),
                    "total_categories": len(categories),
                    "collection_method": "comprehensive_catalog_builder"
                },
                "categories": {},
                "food_index": {},  # 食材名 -> 詳細情報のインデックス
                "statistics": {}
            }

            total_foods = 0

            # 各カテゴリから食材を収集
            for category in categories:
                try:
                    foods = self.collect_all_foods_from_category(category)
                    category_name = category['sub_category']

                    catalog["categories"][category_name] = {
                        "category_info": category,
                        "foods": foods,
                        "food_count": len(foods)
                    }

                    # 食材インデックスを構築
                    for food in foods:
                        food_key = self._normalize_food_name(food['food_name'])
                        catalog["food_index"][food_key] = {
                            "original_name": food['food_name'],
                            "category": category_name,
                            "navigation_info": food
                        }

                    total_foods += len(foods)
                    print(f"✅ {category_name}: {len(foods)}個登録完了")

                except Exception as e:
                    print(f"❌ {category.get('sub_category', 'unknown')}カテゴリ処理エラー: {e}")
                    continue

            # 統計情報
            catalog["statistics"] = {
                "total_foods": total_foods,
                "total_categories": len(catalog["categories"]),
                "avg_foods_per_category": total_foods / max(len(catalog["categories"]), 1)
            }

            self.food_catalog = catalog
            print(f"🎉 完全カタログ構築完了: {total_foods}個の食材、{len(categories)}カテゴリ")
            return catalog

        except Exception as e:
            print(f"❌ カタログ構築エラー: {e}")
            return {}

    def _normalize_food_name(self, food_name: str) -> str:
        """食材名を正規化（検索用）"""
        return food_name.lower().strip().replace('\n', ' ')

    def find_food_by_name(self, search_name: str) -> Optional[Dict]:
        """食材名で検索"""
        normalized_search = self._normalize_food_name(search_name)
        return self.food_catalog.get("food_index", {}).get(normalized_search)

    def navigate_to_food(self, food_name: str) -> bool:
        """指定食材のページに直接移動"""
        try:
            food_info = self.find_food_by_name(food_name)
            if not food_info:
                print(f"❌ 食材が見つかりません: {food_name}")
                return False

            nav_info = food_info["navigation_info"]
            category_name = food_info["category"]

            print(f"🎯 {food_name} に移動中（カテゴリ: {category_name}）...")

            # カテゴリに移動
            category_info = None
            for cat in self.categories:
                if cat['sub_category'] == category_name:
                    category_info = cat
                    break

            if not category_info:
                print(f"❌ カテゴリ情報が見つかりません: {category_name}")
                return False

            # カテゴリページに移動
            success = self._navigate_to_category(category_info)
            if not success:
                return False

            # 該当ページに移動
            target_page = nav_info["page_number"]
            current_page = 1

            while current_page < target_page:
                if not self._go_to_next_page():
                    print(f"❌ ページ{target_page}への移動失敗")
                    return False
                current_page += 1

            # 食材をクリック
            food_xpath = nav_info["xpath"]
            food_element = self.driver.find_element(By.XPATH, food_xpath)
            food_element.click()
            time.sleep(self.config.REQUEST_DELAY)

            print(f"✅ {food_name} ページに移動完了")
            return True

        except Exception as e:
            print(f"❌ 食材移動エラー: {e}")
            return False

    def save_catalog(self, filename: str = None) -> str:
        """カタログをファイルに保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results/food_catalog_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.food_catalog, f, ensure_ascii=False, indent=2)

        print(f"📄 食材カタログを保存: {filename}")
        return filename

    def load_catalog(self, filename: str) -> bool:
        """カタログをファイルから読み込み"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.food_catalog = json.load(f)

            print(f"📄 食材カタログを読み込み: {filename}")
            print(f"📊 統計: {self.food_catalog.get('statistics', {})}")
            return True

        except Exception as e:
            print(f"❌ カタログ読み込みエラー: {e}")
            return False