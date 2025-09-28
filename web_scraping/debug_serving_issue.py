#!/usr/bin/env python3
"""
デバッグ: FormControlLabelのテキストが空になる問題を調査
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from config import config

def debug_serving_issue():
    print("🔬 Serving情報取得問題のデバッグ")

    # ドライバー設定
    chrome_options = Options()
    if config.HEADLESS:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, config.TIMEOUT)

    try:
        # ログイン & ナビゲーション
        print("🔐 ログイン中...")
        driver.get(config.LOGIN_URL)
        time.sleep(config.REQUEST_DELAY)

        username = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
        password = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        username.send_keys(config.USERNAME)
        password.send_keys(config.PASSWORD)

        login_btn = driver.find_element(By.CSS_SELECTOR, "button[class*='jss15']")
        login_btn.click()
        time.sleep(config.REQUEST_DELAY * 2)

        # カテゴリナビゲーション
        my_foods_url = f"{config.BASE_URL}/meals.do#ff"
        driver.get(my_foods_url)
        time.sleep(config.REQUEST_DELAY)

        my_foods_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@title='My Foods: recent, favorite, custom and recipes']"))
        )
        my_foods_btn.click()
        time.sleep(config.REQUEST_DELAY)

        staple_foods = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Staple Foods']"))
        )
        staple_foods.click()
        time.sleep(config.REQUEST_DELAY)

        category = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Dairy, Dairy Substitutes & Egg']"))
        )
        category.click()
        time.sleep(config.REQUEST_DELAY)

        # 食材選択
        food_items = driver.find_elements(
            By.XPATH,
            "//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItem-button')]"
        )

        if food_items:
            food_name = food_items[0].text
            print(f"📝 食材選択: {food_name[:50]}...")
            food_items[0].click()
            time.sleep(config.REQUEST_DELAY * 2)

            # P要素クリック（メインスクリプトと同じ動作をシミュレート）
            print("📍 P要素をクリック（栄養素展開）...")
            p_elements = driver.find_elements(By.TAG_NAME, "p")
            clickable_p = [p for p in p_elements if p.is_displayed() and p.text.strip()]

            if clickable_p:
                clickable_p[0].click()
                time.sleep(2)
                print("✅ P要素クリック完了")

                # Amount eaten モーダルを開く
                print("\n🔍 Amount eaten モーダルを開く...")
                amount_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Amount eaten')]")

                for element in amount_elements:
                    if element.is_displayed():
                        parent_level2 = element.find_element(By.XPATH, "../..")

                        # モーダルを開く
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", parent_level2)
                        time.sleep(1)
                        parent_level2.click()
                        time.sleep(3)

                        # モーダル内容をデバッグ
                        print("\n🔬 モーダル内容デバッグ...")

                        try:
                            radio_group = driver.find_element(By.XPATH, "//div[@role='radiogroup']")
                            print("✅ ラジオボタングループ発見")

                            form_labels = radio_group.find_elements(By.XPATH, ".//label[contains(@class, 'MuiFormControlLabel-root')]")
                            print(f"📋 FormControlLabel要素数: {len(form_labels)}個")

                            for i, label in enumerate(form_labels):
                                print(f"\n  🔍 Label{i+1}:")

                                # 様々な方法でテキストを取得してみる
                                methods = [
                                    ("label.text", lambda: label.text),
                                    ("label.get_attribute('textContent')", lambda: label.get_attribute('textContent')),
                                    ("label.get_attribute('innerText')", lambda: label.get_attribute('innerText')),
                                ]

                                for method_name, method_func in methods:
                                    try:
                                        result = method_func()
                                        print(f"    {method_name}: '{result}'")
                                    except Exception as e:
                                        print(f"    {method_name}: エラー - {e}")

                                # span要素を探す
                                try:
                                    spans = label.find_elements(By.TAG_NAME, "span")
                                    print(f"    span要素数: {len(spans)}個")

                                    for j, span in enumerate(spans):
                                        span_text = span.text
                                        span_html = span.get_attribute('innerHTML')
                                        print(f"      span{j+1}: text='{span_text}', html='{span_html[:50]}...'")
                                except Exception as e:
                                    print(f"    span検索エラー: {e}")

                                # HTMLを確認
                                try:
                                    html = label.get_attribute('outerHTML')
                                    print(f"    HTML: {html[:150]}...")
                                except Exception as e:
                                    print(f"    HTML取得エラー: {e}")

                        except Exception as e:
                            print(f"❌ ラジオボタングループエラー: {e}")

                        break

    except Exception as e:
        print(f"❌ デバッグエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_serving_issue()