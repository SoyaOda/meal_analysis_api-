#!/usr/bin/env python3
"""
実際の食材カテゴリ19個の安定的な食材収集スクリプト
ChromeDriverエラーを回避し、確実に各カテゴリの食材を収集
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from config import config


class StableFoodCategoryCollector:
    """安定的な食材カテゴリ収集クラス"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.collected_data = {
            "categories": [],
            "foods_by_category": {}
        }

        # 実際の食材カテゴリのみ（19個）
        self.target_food_categories = [
            "Beans & Peas",
            "Beverages",
            "Breads & Rolls",
            "Cheese",
            "Condiments, Dressings & Sauces",
            "Dairy, Dairy Substitutes & Egg",
            "Fats & Oils",
            "Fish & Seafood",
            "Fruit - canned, dried, or juice",
            "Fruit - raw or frozen",
            "Grains & Grain Products",
            "Meats",
            "Nuts & Seeds",
            "Poultry",
            "Spices & Herbs",
            "Stocks and Gravy",
            "Sweets & Sweeteners",
            "Vegetables - canned, dried, or juice",
            "Vegetables - raw, frozen, or cooked"
        ]

    def setup_driver(self):
        """ChromeDriverを設定"""
        print("🚀 ChromeDriverを起動中...")
        chrome_options = Options()
        if config.HEADLESS:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

        # 安定性のためのオプション追加
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)

    def login_and_navigate_to_my_foods(self):
        """ログイン & My Foods画面に移動"""
        print("🔐 ログイン & My Foods画面に移動中...")

        try:
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

        except Exception as e:
            print(f"❌ ログイン・ナビゲーションエラー: {e}")
            return False

    def navigate_to_staple_foods(self):
        """Staple Foodsに移動"""
        try:
            staple_foods = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
            )
            staple_foods.click()
            time.sleep(config.REQUEST_DELAY)
            return True
        except Exception as e:
            print(f"❌ Staple Foods移動エラー: {e}")
            return False

    def collect_foods_from_category_safe(self, category_name):
        """安全な食材収集（エラー回避機能付き）"""
        print(f"\n🥗 {category_name}から食材収集中...")

        try:
            # カテゴリをクリック
            category_xpath = f"//span[text()='{category_name}']"

            # 要素が見つかるまで待機
            category_element = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, category_xpath))
            )

            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", category_element)
            time.sleep(1)
            category_element.click()
            time.sleep(config.REQUEST_DELAY * 2)

            foods = []
            page_num = 1
            max_pages = 5  # 安全装置
            max_foods_per_category = 100  # カテゴリあたりの最大食材数

            while page_num <= max_pages and len(foods) < max_foods_per_category:
                print(f"  📄 ページ{page_num}を処理中...")

                try:
                    # 食材要素を取得（短いタイムアウト）
                    self.driver.implicitly_wait(2)
                    food_elements = self.driver.find_elements(
                        By.XPATH,
                        "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
                    )
                    self.driver.implicitly_wait(config.IMPLICIT_WAIT)

                    if not food_elements:
                        print(f"  ✅ ページ{page_num}: 食材なし（収集完了）")
                        break

                    page_foods = 0
                    for i, element in enumerate(food_elements):
                        if len(foods) >= max_foods_per_category:
                            break

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
                                page_foods += 1

                        except Exception as e:
                            print(f"      ⚠️ 食材{i+1}抽出エラー（スキップ）: {e}")
                            continue

                    print(f"  ✅ ページ{page_num}: {page_foods}個の食材を処理")

                    # 次のページがあるかチェック（エラー回避）
                    try:
                        self.driver.implicitly_wait(1)
                        next_buttons = self.driver.find_elements(
                            By.XPATH,
                            "//button[contains(@aria-label, 'next') or contains(text(), 'Next')]"
                        )
                        self.driver.implicitly_wait(config.IMPLICIT_WAIT)

                        has_next = False
                        for button in next_buttons:
                            try:
                                if button.is_enabled() and button.is_displayed():
                                    button.click()
                                    time.sleep(config.REQUEST_DELAY)
                                    has_next = True
                                    break
                            except:
                                continue

                        if not has_next:
                            print(f"  🏁 最終ページ{page_num}に到達")
                            break

                    except Exception as e:
                        print(f"  ⚠️ ページネーションエラー（終了）: {e}")
                        break

                    page_num += 1

                except Exception as e:
                    print(f"  ❌ ページ{page_num}処理エラー: {e}")
                    break

            print(f"✅ {category_name}: 総{len(foods)}個の食材を収集")
            return foods

        except Exception as e:
            print(f"❌ {category_name}食材収集エラー: {e}")
            return []

    def collect_all_food_categories(self, start_index=0, max_categories=None):
        """全食材カテゴリを順次収集"""
        if max_categories is None:
            target_categories = self.target_food_categories[start_index:]
        else:
            target_categories = self.target_food_categories[start_index:start_index + max_categories]

        print(f"\n🎯 対象カテゴリ: {len(target_categories)}個")
        for i, cat in enumerate(target_categories, start_index + 1):
            print(f"  {i:2d}. {cat}")

        successful_collections = 0
        total_foods = 0

        for i, category_name in enumerate(target_categories):
            print(f"\n{'='*60}")
            print(f"📂 カテゴリ {start_index + i + 1}/{len(self.target_food_categories)}: {category_name}")
            print(f"{'='*60}")

            try:
                # Staple Foodsに戻る
                if not self.navigate_to_staple_foods():
                    print(f"❌ Staple Foods移動失敗 - {category_name}をスキップ")
                    continue

                # 食材収集
                foods = self.collect_foods_from_category_safe(category_name)

                if foods:
                    self.collected_data["foods_by_category"][category_name] = foods
                    successful_collections += 1
                    total_foods += len(foods)
                    print(f"✅ {category_name}: {len(foods)}個収集成功")
                else:
                    print(f"❌ {category_name}: 収集失敗")

                # カテゴリ間の待機
                time.sleep(2)

            except Exception as e:
                print(f"❌ カテゴリ {category_name} 処理エラー: {e}")
                continue

        print(f"\n🏁 収集完了:")
        print(f"   ✅ 成功カテゴリ: {successful_collections}/{len(target_categories)}")
        print(f"   🍽️ 総食材数: {total_foods}個")

        return successful_collections > 0

    def save_results(self, filename=None):
        """結果を保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results/food_categories_stable_{timestamp}.json"

        # 統計情報を追加
        total_foods = sum(len(foods) for foods in self.collected_data["foods_by_category"].values())
        successful_categories = len(self.collected_data["foods_by_category"])

        output_data = {
            "collection_info": {
                "timestamp": datetime.now().isoformat(),
                "method": "stable_food_category_collection",
                "target_categories": len(self.target_food_categories),
                "successful_categories": successful_categories,
                "total_foods": total_foods,
                "description": "実際の食材カテゴリ19個の安定収集"
            },
            "target_food_categories": self.target_food_categories,
            "foods_by_category": self.collected_data["foods_by_category"],
            "category_statistics": {
                cat: len(foods) for cat, foods in self.collected_data["foods_by_category"].items()
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 結果を保存: {filename}")
        print(f"📊 統計:")
        print(f"   📂 対象カテゴリ数: {len(self.target_food_categories)}個")
        print(f"   ✅ 成功カテゴリ数: {successful_categories}個")
        print(f"   🍽️ 総食材数: {total_foods}個")

        # カテゴリ別詳細
        print(f"\n📋 カテゴリ別詳細:")
        for cat, foods in self.collected_data["foods_by_category"].items():
            print(f"   {cat}: {len(foods)}個")

        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def run_stable_collection(self, start_index=0, max_categories=5):
        """安定収集を実行"""
        try:
            print("📋 実際の食材カテゴリ安定収集開始")
            print("="*60)

            self.setup_driver()

            if not self.login_and_navigate_to_my_foods():
                print("❌ ログイン・ナビゲーション失敗")
                return False

            # 食材カテゴリを順次収集
            success = self.collect_all_food_categories(start_index, max_categories)

            if success:
                # 結果保存
                filename = self.save_results()
                print(f"✅ 安定収集が完了しました: {filename}")
            else:
                print("❌ 収集に失敗しました")

            return success

        except Exception as e:
            print(f"❌ 安定収集エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="実際の食材カテゴリ安定収集")
    parser.add_argument("-s", "--start", type=int, default=0,
                       help="開始カテゴリインデックス (0-18)")
    parser.add_argument("-n", "--max-categories", type=int, default=5,
                       help="最大収集カテゴリ数")

    args = parser.parse_args()

    collector = StableFoodCategoryCollector()
    success = collector.run_stable_collection(args.start, args.max_categories)

    if success:
        print("\n✅ 実際の食材カテゴリ安定収集が正常に完了しました！")
        exit(0)
    else:
        print("\n❌ 実際の食材カテゴリ安定収集に失敗しました。")
        exit(1)