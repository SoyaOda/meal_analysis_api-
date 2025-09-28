#!/usr/bin/env python3
"""
Staple Foodsカテゴリ情報・食材情報のみを取得するスクリプト
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from src.components.navigation_manager import NavigationManager
from config import config


class StapleFoodsInfoCollector:
    """Staple Foods情報収集クラス"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.navigation_manager = None
        self.collected_data = {
            "categories": [],
            "foods_by_category": {}
        }

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

        # NavigationManagerを初期化
        self.navigation_manager = NavigationManager(self.driver, self.wait, config)

    def login_and_navigate_to_my_foods(self):
        """ログイン & My Foods画面に移動"""
        print("🔐 ログイン & My Foods画面に移動中...")

        # ログイン
        self.driver.get(config.LOGIN_URL)
        time.sleep(config.REQUEST_DELAY)

        username = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
        password = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        username.send_keys(config.USERNAME)
        password.send_keys(config.PASSWORD)

        login_btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='jss15']")
        login_btn.click()
        time.sleep(config.REQUEST_DELAY * 2)

        # My Foods画面に移動
        my_foods_url = f"{config.BASE_URL}/meals.do#ff"
        self.driver.get(my_foods_url)
        time.sleep(config.REQUEST_DELAY)

        # My Foods ボタンクリック
        my_foods_btn = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
        )
        my_foods_btn.click()
        time.sleep(config.REQUEST_DELAY)

        print("✅ My Foods画面への移動完了")
        return True

    def discover_staple_foods_categories(self):
        """Staple Foodsのサブカテゴリを発見"""
        print("\n📂 Staple Foodsカテゴリ発見中...")

        try:
            # Staple Foodsをクリック
            staple_foods = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
            )
            staple_foods.click()
            time.sleep(config.REQUEST_DELAY)

            categories = []

            # サブカテゴリ要素を取得
            subcat_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'MuiList')]//span[contains(@class, 'MuiListItemText')]"
            )

            print(f"📋 発見された要素数: {len(subcat_elements)}個")

            for i, element in enumerate(subcat_elements):
                try:
                    category_name = element.text.strip()
                    if category_name and len(category_name) > 2:  # 有効なカテゴリ名
                        category_info = {
                            "index": i + 1,
                            "category_name": category_name,
                            "xpath": f"//span[text()='{category_name}']",
                            "discovered_at": datetime.now().isoformat()
                        }
                        categories.append(category_info)
                        print(f"  {i+1:2d}. {category_name}")

                except Exception as e:
                    print(f"    ⚠️ 要素{i+1}処理エラー: {e}")
                    continue

            self.collected_data["categories"] = categories
            print(f"✅ Staple Foodsサブカテゴリ発見完了: {len(categories)}個")
            return categories

        except Exception as e:
            print(f"❌ サブカテゴリ発見エラー: {e}")
            return []

    def collect_foods_from_category(self, category_info):
        """指定カテゴリから食材を収集"""
        category_name = category_info["category_name"]
        print(f"\n🥗 {category_name}から食材収集中...")

        try:
            # カテゴリをクリック
            category_xpath = category_info["xpath"]
            category_element = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, category_xpath))
            )
            category_element.click()
            time.sleep(config.REQUEST_DELAY)

            foods = []
            page_num = 1
            max_pages = 10  # 安全装置（テスト用に制限）

            while page_num <= max_pages:
                print(f"  📄 ページ{page_num}を処理中...")

                # 現在ページの食材を取得
                food_elements = self.driver.find_elements(
                    By.XPATH,
                    "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
                )

                if not food_elements:
                    print(f"  ✅ ページ{page_num}: 食材なし（収集完了）")
                    break

                for i, element in enumerate(food_elements):
                    try:
                        food_text = element.text.strip()
                        if food_text:
                            food_info = {
                                "food_name": food_text,
                                "category": category_name,
                                "page_number": page_num,
                                "position_in_page": i + 1,
                                "xpath": f"//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')][{i + 1}]",
                                "collected_at": datetime.now().isoformat()
                            }
                            foods.append(food_info)

                    except Exception as e:
                        print(f"      ⚠️ 食材{i+1}抽出エラー: {e}")
                        continue

                print(f"  ✅ ページ{page_num}: {len(food_elements)}個の食材を処理")

                # 次のページがあるかチェック
                next_buttons = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(@aria-label, 'next') or contains(text(), 'Next') or contains(text(), '次')]"
                )

                has_next = False
                for button in next_buttons:
                    if button.is_enabled() and button.is_displayed():
                        button.click()
                        time.sleep(config.REQUEST_DELAY)
                        has_next = True
                        break

                if not has_next:
                    print(f"  🏁 最終ページ{page_num}に到達")
                    break

                page_num += 1

            print(f"✅ {category_name}: 総{len(foods)}個の食材を収集")
            return foods

        except Exception as e:
            print(f"❌ {category_name}食材収集エラー: {e}")
            return []

    def collect_target_categories_foods(self, target_categories=None):
        """指定カテゴリの食材を収集"""
        if target_categories is None:
            # デフォルトで最初の3カテゴリ
            target_categories = 3

        categories = self.collected_data.get("categories", [])

        if isinstance(target_categories, int):
            target_list = categories[:target_categories]
        else:
            # カテゴリ名のリストが指定された場合
            target_list = [cat for cat in categories if cat["category_name"] in target_categories]

        print(f"\n🎯 対象カテゴリ: {len(target_list)}個")
        for cat in target_list:
            print(f"  - {cat['category_name']}")

        for category_info in target_list:
            category_name = category_info["category_name"]

            # Staple Foodsに戻る
            staple_foods = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
            )
            staple_foods.click()
            time.sleep(config.REQUEST_DELAY)

            # 食材収集
            foods = self.collect_foods_from_category(category_info)
            self.collected_data["foods_by_category"][category_name] = foods

    def save_results(self, filename=None):
        """結果を保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results/staple_foods_info_{timestamp}.json"

        # 統計情報を追加
        total_foods = sum(len(foods) for foods in self.collected_data["foods_by_category"].values())

        output_data = {
            "collection_info": {
                "timestamp": datetime.now().isoformat(),
                "total_categories": len(self.collected_data["categories"]),
                "collected_categories": len(self.collected_data["foods_by_category"]),
                "total_foods": total_foods,
                "method": "staple_foods_info_collection"
            },
            "categories": self.collected_data["categories"],
            "foods_by_category": self.collected_data["foods_by_category"]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 結果を保存: {filename}")
        print(f"📊 統計:")
        print(f"   📂 総カテゴリ数: {len(self.collected_data['categories'])}個")
        print(f"   🥗 収集カテゴリ数: {len(self.collected_data['foods_by_category'])}個")
        print(f"   🍽️ 総食材数: {total_foods}個")

        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def run_info_collection(self, target_categories=3):
        """情報収集を実行"""
        try:
            print("📋 Staple Foods情報収集開始")
            print("="*60)

            self.setup_driver()

            if not self.login_and_navigate_to_my_foods():
                print("❌ ログイン・ナビゲーション失敗")
                return False

            # 1. カテゴリ発見
            categories = self.discover_staple_foods_categories()
            if not categories:
                print("❌ カテゴリ発見失敗")
                return False

            # 2. 指定カテゴリの食材収集
            self.collect_target_categories_foods(target_categories)

            # 3. 結果保存
            filename = self.save_results()
            print(f"✅ 情報収集が完了しました: {filename}")

            return True

        except Exception as e:
            print(f"❌ 情報収集エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Staple Foods情報収集")
    parser.add_argument("-n", "--num-categories", type=int, default=3,
                       help="収集するカテゴリ数 (デフォルト: 3)")
    parser.add_argument("--categories", nargs='+',
                       help="収集する特定カテゴリ名のリスト")

    args = parser.parse_args()

    collector = StapleFoodsInfoCollector()

    target = args.categories if args.categories else args.num_categories
    success = collector.run_info_collection(target)

    if success:
        print("\n✅ Staple Foods情報収集が正常に完了しました！")
        exit(0)
    else:
        print("\n❌ Staple Foods情報収集に失敗しました。")
        exit(1)