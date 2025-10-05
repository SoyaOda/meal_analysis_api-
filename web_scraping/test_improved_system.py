#!/usr/bin/env python3
"""
改善されたサービング抽出システムのテスト
Cornstarchで実際のデータ収集を実行
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

async def test_improved_system():
    """改善されたシステムのテスト"""
    print("🧪 改善されたサービング抽出システムテスト")
    print("=" * 60)

    navigator = PlaywrightMultiFoodNavigator()

    try:
        # セッション初期化
        print("🚀 セッション初期化中...")
        await navigator.initialize_session()
        await navigator.load_food_catalog()

        collector = PlaywrightFoodDataCollector(navigator.page)

        target_food = "Cornstarch, cup\n488cals"
        print(f"🎯 対象食材: {repr(target_food)}")

        # ナビゲーション
        print("\n🧭 ナビゲーション実行中...")
        nav_success = await navigator.navigate_to_food_stable(target_food)
        print(f"ナビゲーション: {'✅成功' if nav_success else '❌失敗'}")

        if nav_success:
            # 改善されたデータ収集を実行
            print("\n📊 改善されたデータ収集実行中...")
            food_data = await collector.collect_complete_food_data(target_food)

            print(f"\n📋 収集結果:")
            print(f"  全体成功: {food_data.get('collection_success', False)}")

            serving_options = food_data.get('serving_options', {})
            print(f"  サービングデータ数: {len(serving_options.get('raw_serving_data', []))}")

            # 改善されたサービング情報をチェック
            improved_servings = serving_options.get('improved_servings', [])
            print(f"  改善されたサービング数: {len(improved_servings)}")

            if improved_servings:
                print("\n🎯 改善されたサービング情報:")
                for i, serving in enumerate(improved_servings, 1):
                    print(f"    {i}. {serving.get('display_text', 'N/A')} (出典: {serving.get('source', 'N/A')})")

                # 結果の判定
                success = len(improved_servings) >= 3
                print(f"\n🏆 テスト結果: {'✅成功' if success else '❌失敗'}")
                print(f"期待: 3個以上のサービングオプション")
                print(f"実際: {len(improved_servings)}個のサービングオプション")

                # 結果を保存
                test_result = {
                    "target_food": target_food,
                    "navigation_success": nav_success,
                    "collection_success": food_data.get('collection_success', False),
                    "total_raw_serving_data": len(serving_options.get('raw_serving_data', [])),
                    "improved_servings_count": len(improved_servings),
                    "improved_servings": improved_servings,
                    "test_success": success,
                    "timestamp": datetime.now().isoformat()
                }

                output_file = f"improved_system_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(test_result, f, ensure_ascii=False, indent=2)

                print(f"\n📄 結果保存: {output_file}")
                return success

            else:
                print("❌ 改善されたサービング情報が生成されませんでした")
                return False

        else:
            print("❌ ナビゲーション失敗")
            return False

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        print(f"詳細: {traceback.format_exc()}")
        return False
    finally:
        await navigator.cleanup_session()

if __name__ == "__main__":
    success = asyncio.run(test_improved_system())
    print(f"\n🎯 最終結果: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)