#!/usr/bin/env python3
"""
Cornstarch serving情報取得の簡易テスト
"""
import sys
import os
import asyncio
import json
from pathlib import Path
from datetime import datetime

current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from components.playwright_multi_food_navigator import PlaywrightMultiFoodNavigator
from components.playwright_food_data_collector import PlaywrightFoodDataCollector

async def main():
    print("🧪 Cornstarch Serving情報取得テスト")
    print("=" * 60)

    navigator = None

    try:
        # ナビゲーターの初期化
        navigator = PlaywrightMultiFoodNavigator()
        await navigator.initialize_session()
        await navigator.load_food_catalog()

        # データコレクターの初期化
        data_collector = PlaywrightFoodDataCollector(navigator.page)

        # Cornstarchにナビゲート
        target_name = "Cornstarch, cup\n488cals"
        print(f"\n🎯 ターゲット: {repr(target_name)}")

        success = await navigator.navigate_to_food_stable(target_name)

        if not success:
            print("❌ ナビゲーション失敗")
            return False

        print("✅ ナビゲーション成功")

        # Serving情報のみ収集（軽量化）
        print("\n📡 Serving情報収集中...")

        # 「X more servings」リンクをクリックして全serving表示
        print("\n🔍 'more servings'リンクを探す...")
        try:
            # すべての<a>タグと<button>タグを取得
            all_clickable = await navigator.page.query_selector_all("a, button")

            clicked = False
            for elem in all_clickable:
                try:
                    text = await elem.inner_text()
                    if 'more' in text.lower() and 'serving' in text.lower():
                        print(f"  ✅ リンク発見: '{text.strip()}'")
                        await elem.click()
                        await asyncio.sleep(2)
                        clicked = True
                        break
                except:
                    continue

            if clicked:
                print("  ✅ 全serving情報を展開")
            else:
                print("  ℹ️ 'more servings'リンクなし（全て表示済み）")
        except Exception as e:
            print(f"  ⚠️ リンククリックエラー: {e}")

        # スクリーンショット保存
        screenshot_file = f"debug/cornstarch_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await navigator.page.screenshot(path=screenshot_file)
        print(f"📸 スクリーンショット保存: {screenshot_file}")

        # ページのHTMLを直接確認
        page_content = await navigator.page.content()

        # Serving情報を抽出
        print("\n🔍 Serving情報を抽出...")
        print(f"  ページ内容の長さ: {len(page_content)} bytes")

        # 画面に表示されているserving要素を直接取得
        print("\n  📋 ページ上のserving要素を取得...")
        serving_buttons = await navigator.page.query_selector_all("button, div, span")

        serving_info = []
        for elem in serving_buttons:
            try:
                text = await elem.inner_text()
                # "cup", "tablespoon" などの単位を含むテキストを探す
                if any(unit in text.lower() for unit in ['cup', 'tablespoon', 'teaspoon', 'gram', 'ml', 'oz', 'lb', 'fl oz']):
                    if len(text) < 50:  # 短いテキストのみ（ノイズ除去）
                        serving_info.append(text.strip())
            except:
                continue

        if serving_info:
            print(f"  ✅ Serving要素: {len(serving_info)}個発見")
            for i, info in enumerate(serving_info):  # 全て表示
                print(f"    [{i}] {info}")

        # HTMLからパターンマッチングでも抽出
        import re

        # パターン: "unit XXXcals / YY g"
        pattern = r'(\w+(?:\s+\w+)?)\s+(\d+)cals?\s*/\s*([\d.]+)\s*g'
        matches = re.findall(pattern, page_content, re.IGNORECASE)

        print(f"\n  🔍 正規表現マッチング...")
        if 'Select Serving' in page_content or 'select serving' in page_content.lower():
            print("  ✅ Select Servingセクション発見")

            if matches:
                print(f"  📋 Serving情報: {len(matches)}個見つかりました")
                for i, (unit, cals, grams) in enumerate(matches[:20]):
                    print(f"    [{i}] {unit} {cals}cals / {grams} g")

                # 結果を保存
                result = {
                    "food_name": "Cornstarch, cup 488cals",
                    "serving_count": len(matches),
                    "servings": [
                        {"unit": unit, "calories": cals, "grams": grams}
                        for unit, cals, grams in matches
                    ]
                }

                output_file = f"debug/cornstarch_serving_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                print(f"\n📄 結果保存: {output_file}")
                return len(matches) > 0
            else:
                print("  ❌ serving形式のデータが見つかりません")

                # HTMLの一部を保存してデバッグ
                html_file = f"debug/cornstarch_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(page_content)
                print(f"  📄 HTMLを保存: {html_file}")
                return False
        else:
            print("  ❌ Select Servingセクションが見つかりません")
            return False

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if navigator:
            await navigator.cleanup_session()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
