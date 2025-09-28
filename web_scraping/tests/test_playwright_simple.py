#!/usr/bin/env python3
"""
簡単なPlaywrightテスト
基本的な動作確認用
"""

import asyncio
from playwright.async_api import async_playwright


async def simple_playwright_test():
    """シンプルなPlaywrightテスト"""
    print("🧪 簡単なPlaywrightテスト開始...")

    try:
        # Playwright起動
        playwright = await async_playwright().start()
        print("✅ Playwright起動成功")

        # ブラウザ起動
        browser = await playwright.chromium.launch(headless=True)
        print("✅ ブラウザ起動成功")

        # コンテキスト作成
        context = await browser.new_context()
        print("✅ コンテキスト作成成功")

        # ページ作成
        page = await context.new_page()
        print("✅ ページ作成成功")

        # 簡単なページに移動
        await page.goto("https://httpbin.org/get")
        print("✅ ページ移動成功")

        # タイトル取得
        title = await page.title()
        print(f"✅ ページタイトル: {title}")

        # クリーンアップ
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()
        print("✅ クリーンアップ完了")

        print("🎉 Playwrightテスト成功！")
        return True

    except Exception as e:
        print(f"❌ Playwrightテストエラー: {e}")
        return False


async def main():
    """メイン実行"""
    success = await simple_playwright_test()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)