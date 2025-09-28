#!/usr/bin/env python3
"""
簡単なテスト用スクリプト
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def test_simple_scraping():
    """簡単なテスト"""
    print("🚀 簡単なテスト開始")

    try:
        # Chrome設定（ヘッドレスモード）
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        print("🔍 ChromeDriver起動中...")
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)

        print("🌐 MyNetDiaryにアクセス...")
        driver.get("https://www.mynetdiary.com")

        print(f"✅ ページタイトル: {driver.title}")
        print("✅ 基本テスト成功")

        driver.quit()
        print("🏁 テスト完了")

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_scraping()