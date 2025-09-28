#!/usr/bin/env python3
"""
MyNetDiaryのページ構造をデバッグするスクリプト
"""

import json
import time
import sys
import os
from datetime import datetime

# パス設定
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("❌ Seleniumがインストールされていません: pip install selenium")
    sys.exit(1)

from config import config

class PageStructureDebugger:
    """ページ構造をデバッグするクラス"""

    def __init__(self):
        self.driver = None
        self.wait = None

    def setup_driver(self) -> webdriver.Chrome:
        """Chrome WebDriverのセットアップ"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_path):
            chrome_options.binary_location = chrome_path

        print("🚀 ChromeDriverを起動中...")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)
        return self.driver

    def login(self) -> bool:
        """MyNetDiaryにログイン"""
        try:
            print("🔐 MyNetDiaryにログイン中...")
            self.driver.get(config.LOGIN_URL)
            time.sleep(config.REQUEST_DELAY)

            username_element = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            password_element = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            username_element.send_keys(config.USERNAME)
            password_element.send_keys(config.PASSWORD)

            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[class*='jss15']")
            login_button.click()
            time.sleep(config.REQUEST_DELAY * 2)

            current_url = self.driver.current_url
            if "login" not in current_url.lower() and "logon" not in current_url.lower():
                print("✅ ログイン成功！")
                return True
            else:
                print("❌ ログイン失敗")
                return False

        except Exception as e:
            print(f"❌ ログインエラー: {str(e)}")
            return False

    def debug_staple_foods_structure(self):
        """Staple Foodsページの構造をデバッグ"""
        try:
            print("🔍 Staple Foodsページに移動してデバッグ...")

            # My Foodsページに移動
            my_foods_url = f"{config.BASE_URL}/meals.do#ff"
            self.driver.get(my_foods_url)
            time.sleep(config.REQUEST_DELAY)

            # My Foodsボタンをクリック
            my_foods_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
            )
            my_foods_button.click()
            time.sleep(config.REQUEST_DELAY)

            # Staple Foodsメニューアイテムをクリック
            staple_foods_item = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
            )
            staple_foods_item.click()
            time.sleep(config.REQUEST_DELAY)

            print("✅ Staple Foodsページに到達")

            # 全てのテキスト要素を取得
            print("\n📄 ページ内の全テキスト要素:")
            all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
            texts = []
            for elem in all_elements:
                text = elem.text.strip()
                tag = elem.tag_name
                classes = elem.get_attribute("class") or ""
                if text and len(text) <= 100:
                    entry = {
                        'text': text,
                        'tag': tag,
                        'class': classes
                    }
                    texts.append(entry)
                    print(f"  📝 {tag}.{classes}: {text}")

            # spanタグの要素のみを詳細に調査
            print("\n🔍 span要素の詳細:")
            span_elements = self.driver.find_elements(By.TAG_NAME, "span")
            for span in span_elements:
                text = span.text.strip()
                classes = span.get_attribute("class") or ""
                if text and len(text) < 50:
                    print(f"  📌 span.{classes}: '{text}'")

            # 結果を保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"web_scraping/data/page_debug_{timestamp}.json"

            debug_data = {
                'debug_info': {
                    'timestamp': datetime.now().isoformat(),
                    'url': self.driver.current_url,
                    'total_elements': len(texts)
                },
                'all_texts': texts
            }

            os.makedirs("web_scraping/data", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)

            print(f"\n💾 デバッグ結果を保存: {filename}")

            # Beans & Peas が見つかるかテスト
            print("\n🧪 'Beans & Peas' の存在確認:")
            beans_elements = self.driver.find_elements(By.XPATH, "//span[text()='Beans & Peas']")
            if beans_elements:
                print("  ✅ 'Beans & Peas' が見つかりました！")
                for elem in beans_elements:
                    print(f"     クラス: {elem.get_attribute('class')}")
                    print(f"     親要素: {elem.find_element(By.XPATH, '..').tag_name}")
            else:
                print("  ❌ 'Beans & Peas' が見つかりませんでした")

        except Exception as e:
            print(f"❌ デバッグエラー: {str(e)}")
            import traceback
            traceback.print_exc()

    def cleanup(self):
        """リソースをクリーンアップ"""
        if self.driver:
            print("🔄 WebDriverをクリーンアップ中...")
            self.driver.quit()

    def run(self):
        """メイン実行"""
        try:
            print("🚀 ページ構造デバッグ開始")

            self.setup_driver()

            if not self.login():
                print("❌ ログインに失敗しました")
                return

            self.debug_staple_foods_structure()

        except Exception as e:
            print(f"❌ 実行エラー: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

        print("🏁 デバッグ終了")

if __name__ == "__main__":
    debugger = PageStructureDebugger()
    debugger.run()