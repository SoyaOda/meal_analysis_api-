#!/usr/bin/env python3
"""
クイックサービングデバッグ - Cornstarchのサービング情報取得に特化
"""

import sys
import os
import logging
import asyncio
import json
from datetime import datetime

# パスの設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from components.playwright_multi_food_navigator import PlaywrightMultiFoodNavigator
from components.playwright_food_data_collector import PlaywrightFoodDataCollector

async def quick_debug():
    """クイックデバッグ実行"""
    print("🔬 クイックサービングデバッグ開始")

    navigator = PlaywrightMultiFoodNavigator()

    try:
        # セッション初期化
        await navigator.initialize_session()
        await navigator.load_food_catalog()

        collector = PlaywrightFoodDataCollector(navigator.page)

        target_food = "Cornstarch, cup\n488cals"
        print(f"🎯 対象食材: {repr(target_food)}")

        # ナビゲーション
        print("🧭 ナビゲーション実行中...")
        nav_success = await navigator.navigate_to_food_stable(target_food)
        print(f"ナビゲーション: {'✅成功' if nav_success else '❌失敗'}")

        if nav_success:
            page = navigator.page

            # 1. Amount eaten ボタンの確認
            print("\n🔍 Amount eaten ボタン確認...")
            amount_eaten_elements = await page.locator('text="Amount eaten"').all()
            print(f"Amount eaten ボタン数: {len(amount_eaten_elements)}")

            # 2. Select Serving 要素の確認
            print("\n🔍 Select Serving 確認...")
            select_serving_elements = await page.locator('text="Select Serving"').all()
            print(f"Select Serving要素数: {len(select_serving_elements)}")

            # 3. テーブル構造の確認
            print("\n🔍 テーブル構造確認...")
            table_elements = await page.locator('table').all()
            print(f"テーブル数: {len(table_elements)}")

            if table_elements:
                # 最初のテーブルの内容を取得
                table_text = await table_elements[0].text_content()
                print(f"最初のテーブル内容 (最初の200文字):")
                print(table_text[:200] if table_text else "テキストなし")

            # 4. カロリー情報の検索
            print("\n🔍 カロリー情報検索...")
            calorie_pattern = ':text-matches("\\d+\\s*cals?")'
            calorie_elements = await page.locator(calorie_pattern).all()
            print(f"カロリー要素数: {len(calorie_elements)}")

            for i, elem in enumerate(calorie_elements[:5]):
                text = await elem.text_content()
                print(f"  カロリー{i+1}: {text}")

            # 5. 重量情報の検索
            print("\n🔍 重量情報検索...")
            weight_pattern = ':text-matches("\\d+\\.?\\d*\\s*g")'
            weight_elements = await page.locator(weight_pattern).all()
            print(f"重量要素数: {len(weight_elements)}")

            for i, elem in enumerate(weight_elements[:5]):
                text = await elem.text_content()
                print(f"  重量{i+1}: {text}")

            # 6. 実際のデータ収集を試行
            print("\n📊 実際のデータ収集試行...")
            food_data = await collector.collect_complete_food_data(target_food)

            serving_data = food_data.get('serving_options', {}).get('raw_serving_data', [])
            nutrition_data = food_data.get('nutrition_data', {}).get('detailed_nutrients', {}).get('raw_nutrition_data', [])

            print(f"収集成功: {food_data.get('collection_success', False)}")
            print(f"サービングデータ数: {len(serving_data)}")
            print(f"栄養データ数: {len(nutrition_data)}")

            # サンプルデータ表示
            print("\n📝 サービングデータサンプル:")
            for i, item in enumerate(serving_data[:10]):
                print(f"  {i+1}: {str(item)[:80]}...")

            # 7. 改善された抽出を試行
            print("\n🔧 改善された抽出試行...")

            # Select Serving テーブルから直接抽出
            select_serving_text = ""
            if select_serving_elements:
                # Select Serving 周辺のコンテキストを取得
                parent = page.locator('text="Select Serving"').locator('..')
                select_serving_text = await parent.text_content()
                print(f"Select Serving周辺テキスト (最初の500文字):")
                print(select_serving_text[:500] if select_serving_text else "テキストなし")

            # 成功判定
            valid_serving_found = False
            if select_serving_text:
                # "unit Xcals / Y g" パターンを探す
                import re
                serving_pattern = r'([a-zA-Z\s]+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g'
                matches = re.findall(serving_pattern, select_serving_text)

                print(f"\n🎯 発見されたサービングパターン: {len(matches)}個")
                for match in matches[:5]:
                    unit, calories, grams = match
                    print(f"  {unit.strip()}: {calories}cals / {grams}g")
                    valid_serving_found = True

            print(f"\n🏆 最終結果: {'✅成功' if valid_serving_found else '❌失敗'}")

            # 結果保存
            result = {
                "target_food": target_food,
                "navigation_success": nav_success,
                "elements_found": {
                    "amount_eaten": len(amount_eaten_elements),
                    "select_serving": len(select_serving_elements),
                    "tables": len(table_elements),
                    "calories": len(calorie_elements),
                    "weights": len(weight_elements)
                },
                "collection_success": food_data.get('collection_success', False),
                "raw_data_counts": {
                    "serving": len(serving_data),
                    "nutrition": len(nutrition_data)
                },
                "valid_serving_found": valid_serving_found,
                "select_serving_text": select_serving_text[:1000] if select_serving_text else "",
                "timestamp": datetime.now().isoformat()
            }

            output_file = f"quick_debug_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"\n📄 結果保存: {output_file}")
            return valid_serving_found

        else:
            print("❌ ナビゲーション失敗")
            return False

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")
        return False
    finally:
        await navigator.cleanup_session()

if __name__ == "__main__":
    success = asyncio.run(quick_debug())
    print(f"\n🎯 結果: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)