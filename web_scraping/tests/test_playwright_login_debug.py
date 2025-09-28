#!/usr/bin/env python3
"""
Playwright版のログインデバッグテスト
MyNetDiaryログイン処理の問題を詳しく調査
"""

import asyncio
import traceback
from playwright.async_api import async_playwright


async def debug_mynetdiary_login():
    """MyNetDiaryログインのデバッグテスト"""
    print("🔍 MyNetDiaryログインデバッグテスト開始...")

    playwright = None
    browser = None
    context = None
    page = None

    try:
        # Playwright起動
        print("1. Playwright起動中...")
        playwright = await async_playwright().start()
        print("✅ Playwright起動成功")

        # ブラウザ起動
        print("2. ブラウザ起動中...")
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu"
            ]
        )
        print("✅ ブラウザ起動成功")

        # コンテキスト作成
        print("3. コンテキスト作成中...")
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        print("✅ コンテキスト作成成功")

        # ページ作成
        print("4. ページ作成中...")
        page = await context.new_page()
        page.set_default_timeout(30000)
        print("✅ ページ作成成功")

        # MyNetDiaryログインページに移動
        login_url = "https://www.mynetdiary.com/logonPage.do"
        print(f"5. ログインページに移動中: {login_url}")
        await page.goto(login_url)
        await page.wait_for_load_state("networkidle")
        print("✅ ログインページ移動成功")

        # 現在のURL確認
        current_url = page.url
        print(f"📍 現在のURL: {current_url}")

        # ページタイトル確認
        title = await page.title()
        print(f"📄 ページタイトル: {title}")

        # フォーム要素の存在確認
        print("6. フォーム要素確認中...")
        username_field = await page.query_selector('#username-or-email')
        password_field = await page.query_selector('#password')
        submit_button = await page.query_selector('button[class*="jss"]')

        print(f"  👤 ユーザー名フィールド: {'存在' if username_field else '見つからない'}")
        print(f"  🔒 パスワードフィールド: {'存在' if password_field else '見つからない'}")
        print(f"  🔘 ログインボタン: {'存在' if submit_button else '見つからない'}")

        if not username_field or not password_field or not submit_button:
            print("❌ 必要なフォーム要素が見つかりません")

            # ページ内容をデバッグ
            print("🔍 ページ内容をデバッグ中...")
            all_inputs = await page.query_selector_all('input')
            print(f"  入力フィールド数: {len(all_inputs)}")

            for i, input_elem in enumerate(all_inputs):
                input_type = await input_elem.get_attribute('type')
                input_name = await input_elem.get_attribute('name')
                input_id = await input_elem.get_attribute('id')
                input_class = await input_elem.get_attribute('class')
                input_placeholder = await input_elem.get_attribute('placeholder')
                input_value = await input_elem.get_attribute('value')
                print(f"    入力{i+1}: type={input_type}, name={input_name}, id={input_id}, class={input_class}, placeholder={input_placeholder}, value={input_value}")

            return False

        # ログイン情報入力
        print("7. ログイン情報入力中...")
        username = "odssuu@gmail.com"
        password = "hojihoji2025"

        await page.fill('#username-or-email', username)
        print("✅ ユーザー名入力完了")

        await page.fill('#password', password)
        print("✅ パスワード入力完了")

        # ログインボタンクリック
        print("8. ログインボタンクリック中...")
        await page.click('button[class*="jss"]')
        await page.wait_for_load_state("networkidle")
        print("✅ ログインボタンクリック完了")

        # ログイン後のURL確認
        final_url = page.url
        print(f"📍 ログイン後URL: {final_url}")

        # ログイン成功判定
        if "food.do" in final_url or "home.do" in final_url:
            print("🎉 ログイン成功！")
            return True
        else:
            print(f"❌ ログイン失敗: 期待されるURLではありません")

            # エラーメッセージ確認
            error_elements = await page.query_selector_all('//*[contains(text(), "error") or contains(text(), "invalid") or contains(text(), "incorrect")]')
            if error_elements:
                print("🚨 エラーメッセージ:")
                for elem in error_elements:
                    error_text = await elem.text_content()
                    print(f"  - {error_text}")

            return False

    except Exception as e:
        print(f"❌ ログインデバッグエラー: {e}")
        print("🔍 詳細なエラー情報:")
        traceback.print_exc()
        return False

    finally:
        # クリーンアップ
        print("9. クリーンアップ中...")
        if page:
            await page.close()
        if context:
            await context.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()
        print("✅ クリーンアップ完了")


async def main():
    """メイン実行"""
    success = await debug_mynetdiary_login()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)