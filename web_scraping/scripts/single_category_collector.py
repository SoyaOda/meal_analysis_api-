#!/usr/bin/env python3
"""
単一カテゴリ食材収集スクリプト (完成版)
安定性を重視し、1カテゴリずつ確実に収集する
"""

import time
import json
import sys
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import config


class SingleCategoryCollector:
    """単一カテゴリ専用収集クラス"""

    def __init__(self):
        self.driver = None
        self.wait = None

        # 実際の食材カテゴリ19個
        self.food_categories = [
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

        # ヘッドレスモードを無効化（安定性のため）
        # chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)

        print("✅ ChromeDriver起動完了")

    def login_and_navigate(self):
        """ログイン & 基本ナビゲーション"""
        print("🔐 MyNetDiaryにログイン中...")

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

            # Staple Foodsをクリック
            staple_foods = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
            )
            staple_foods.click()
            time.sleep(config.REQUEST_DELAY)

            print("✅ ログイン & ナビゲーション完了")
            return True

        except Exception as e:
            print(f"❌ ログイン・ナビゲーションエラー: {e}")
            return False

    def collect_category_foods(self, category_name):
        """指定カテゴリの食材を収集"""
        print(f"\n🥗 {category_name} の食材収集開始")
        print("="*60)

        try:
            # カテゴリに移動
            category_xpath = f"//span[text()='{category_name}']"

            # カテゴリ要素を探して移動
            category_element = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, category_xpath))
            )

            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", category_element)
            time.sleep(2)
            category_element.click()
            time.sleep(config.REQUEST_DELAY * 2)

            print(f"✅ {category_name} カテゴリに移動完了")

            # 食材データを収集
            foods = []
            page_num = 1
            max_pages = 20  # 安全装置
            max_foods = 500  # カテゴリあたりの最大食材数

            while page_num <= max_pages and len(foods) < max_foods:
                print(f"  📄 ページ {page_num} を処理中...")

                try:
                    # 食材要素を取得
                    food_elements = self.driver.find_elements(
                        By.XPATH,
                        "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
                    )

                    if not food_elements:
                        print(f"  ✅ ページ{page_num}: 食材なし（収集完了）")
                        break

                    page_foods = 0
                    for i, element in enumerate(food_elements):
                        if len(foods) >= max_foods:
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

                    # 次のページがあるかチェック
                    try:
                        next_buttons = self.driver.find_elements(
                            By.XPATH,
                            "//button[contains(@aria-label, 'next') or contains(text(), 'Next') or contains(@aria-label, 'Go to next page')]"
                        )

                        has_next = False
                        for button in next_buttons:
                            try:
                                if button.is_enabled() and button.is_displayed():
                                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                                    time.sleep(1)
                                    button.click()
                                    time.sleep(config.REQUEST_DELAY * 2)
                                    has_next = True
                                    break
                            except Exception as btn_e:
                                print(f"      ⚠️ ボタンクリックエラー: {btn_e}")
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

            print(f"✅ {category_name}: 総{len(foods)}個の食材を収集完了")
            return foods

        except Exception as e:
            print(f"❌ {category_name} 食材収集エラー: {e}")
            return []

    def save_category_data(self, category_name, foods):
        """カテゴリデータを保存"""
        # ファイル名を安全に作成
        safe_category_name = category_name.replace(" & ", "_and_").replace(" - ", "_").replace(", ", "_").replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"food_catalog_data/{safe_category_name}_{timestamp}.json"

        data = {
            "collection_info": {
                "category_name": category_name,
                "timestamp": datetime.now().isoformat(),
                "total_foods": len(foods),
                "method": "single_category_collection",
                "collector_version": "1.0"
            },
            "category_data": {
                "name": category_name,
                "xpath": f"//span[text()='{category_name}']",
                "foods": foods
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"📄 {category_name} データを保存: {filename}")
        return filename

    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()

    def collect_single_category(self, category_name):
        """単一カテゴリ収集の完全実行"""
        try:
            print(f"🎯 単一カテゴリ収集: {category_name}")
            print("="*60)

            self.setup_driver()

            if not self.login_and_navigate():
                print("❌ ログイン・ナビゲーション失敗")
                return None

            # 食材収集
            foods = self.collect_category_foods(category_name)

            if foods:
                # データ保存
                filename = self.save_category_data(category_name, foods)
                print(f"\n✅ {category_name} 収集完了: {len(foods)}個の食材")
                print(f"📁 保存ファイル: {filename}")
                return filename
            else:
                print(f"\n❌ {category_name} 収集失敗")
                return None

        except Exception as e:
            print(f"❌ 単一カテゴリ収集エラー: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.cleanup()

    def list_available_categories(self):
        """利用可能なカテゴリを表示"""
        print("📋 利用可能な食材カテゴリ (19個):")
        print("="*50)
        for i, category in enumerate(self.food_categories, 1):
            print(f"  {i:2d}. {category}")
        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="単一カテゴリ食材収集スクリプト")
    parser.add_argument("category", nargs='?', help="収集するカテゴリ名")
    parser.add_argument("-l", "--list", action="store_true", help="利用可能なカテゴリを表示")
    parser.add_argument("-i", "--index", type=int, help="カテゴリ番号で指定 (1-19)")

    args = parser.parse_args()

    collector = SingleCategoryCollector()

    if args.list:
        collector.list_available_categories()
        return

    # カテゴリ決定
    category_name = None

    if args.index:
        if 1 <= args.index <= len(collector.food_categories):
            category_name = collector.food_categories[args.index - 1]
        else:
            print(f"❌ 無効なカテゴリ番号: {args.index} (1-{len(collector.food_categories)}の範囲で指定)")
            return
    elif args.category:
        if args.category in collector.food_categories:
            category_name = args.category
        else:
            print(f"❌ 無効なカテゴリ名: {args.category}")
            print("利用可能なカテゴリを確認するには: python scripts/single_category_collector.py -l")
            return
    else:
        # インタラクティブ選択
        collector.list_available_categories()
        try:
            choice = int(input("収集するカテゴリ番号を入力 (1-19): "))
            if 1 <= choice <= len(collector.food_categories):
                category_name = collector.food_categories[choice - 1]
            else:
                print(f"❌ 無効な番号: {choice}")
                return
        except ValueError:
            print("❌ 無効な入力")
            return

    # 収集実行
    if category_name:
        result = collector.collect_single_category(category_name)
        if result:
            print(f"\n🎉 {category_name} の収集が正常に完了しました！")
            print(f"📁 保存先: {result}")
        else:
            print(f"\n💥 {category_name} の収集に失敗しました。")


if __name__ == "__main__":
    main()