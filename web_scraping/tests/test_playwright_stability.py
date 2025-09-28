#!/usr/bin/env python3
"""
Playwright版の安定性テストスクリプト
ChromeDriverクラッシュ問題の根本的解決を検証
"""

import sys
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.components.playwright_multi_food_navigator import PlaywrightMultiFoodNavigator
from src.components.playwright_food_data_collector import PlaywrightFoodDataCollector


class PlaywrightStabilityTest:
    """Playwright版の安定性テスト"""

    def __init__(self):
        self.test_result = None
        self.navigator = PlaywrightMultiFoodNavigator()

    async def test_single_food_stability(self) -> Dict[str, Any]:
        """1つの食品でPlaywright安定性をテスト"""
        print("🧪 Playwright安定性テスト開始（1食品）...")

        try:
            # セッション初期化
            print("🚀 Playwrightセッション初期化中...")
            init_success = await self.navigator.initialize_session()
            if not init_success:
                raise Exception("Playwrightセッション初期化失敗")

            # 食材カタログ読み込み
            print("📁 食材カタログ読み込み...")
            catalog_success = await self.navigator.load_food_catalog()
            if not catalog_success:
                raise Exception("食材カタログ読み込み失敗")

            # 最初のカテゴリから1つの食品を選択
            first_category = list(self.navigator.food_catalog.keys())[0]
            first_food = self.navigator.food_catalog[first_category]['foods'][0]

            print(f"🎯 テスト対象食品: {first_food}")

            # 食品を選択してページに移動
            print("🔍 食品選択とページ移動中...")
            navigation_success = await self.navigator.navigate_to_food_stable(first_food['food_name'])
            if not navigation_success:
                raise Exception("食品ページへの移動に失敗")

            # データコレクター初期化
            data_collector = PlaywrightFoodDataCollector(self.navigator.page)

            # 食品データ収集
            start_time = asyncio.get_event_loop().time()

            food_result = await data_collector.collect_complete_food_data(
                food_name=first_food['food_name']
            )

            collection_time = asyncio.get_event_loop().time() - start_time

            # 結果評価
            is_success = (
                food_result and
                food_result.get('collection_success', False) and
                food_result.get('nutrition_data') and
                food_result.get('serving_options')
            )

            self.test_result = {
                'food_name': first_food['food_name'],
                'category': first_category,
                'success': is_success,
                'collection_time': round(collection_time, 1),
                'nutrition_available': bool(food_result.get('nutrition_data')),
                'serving_available': bool(food_result.get('serving_options')),
                'nutrition_count': food_result.get('nutrition_data', {}).get('detailed_nutrients', {}).get('total_nutrients_found', 0) if food_result.get('nutrition_data') else 0,
                'serving_count': food_result.get('serving_options', {}).get('total_servings_found', 0) if food_result.get('serving_options') else 0,
                'browser_type': 'playwright-chromium',
                'completed_at': datetime.now().isoformat()
            }

            if is_success:
                print(f"✅ Playwright安定性テスト成功!")
                print(f"  📊 栄養データ: {self.test_result['nutrition_count']}件")
                print(f"  🥄 サービングデータ: {self.test_result['serving_count']}件")
                print(f"  ⏱️ 処理時間: {self.test_result['collection_time']}秒")
            else:
                print(f"❌ Playwright安定性テスト失敗")

        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            self.test_result = {
                'success': False,
                'error': str(e),
                'browser_type': 'playwright-chromium',
                'completed_at': datetime.now().isoformat()
            }

        finally:
            # クリーンアップ
            await self.navigator.cleanup_session()

        return self.test_result

    def save_results(self):
        """テスト結果を保存"""
        if self.test_result:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/playwright_stability_test_{timestamp}.json"

            os.makedirs("data", exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_result, f, ensure_ascii=False, indent=2)

            print(f"💾 テスト結果保存: {filename}")


async def main():
    """メイン実行"""
    print("🔬 Playwright安定性テスト開始")
    print("=" * 50)

    tester = PlaywrightStabilityTest()

    try:
        # テスト実行
        result = await tester.test_single_food_stability()

        # 結果保存
        tester.save_results()

        # 結果表示
        print("\n📋 テスト結果サマリー:")
        print("=" * 30)
        if result['success']:
            print(f"✅ ステータス: 成功")
            print(f"🍽️ 食品: {result['food_name']}")
            print(f"📂 カテゴリ: {result['category']}")
            print(f"⏱️ 処理時間: {result['collection_time']}秒")
            print(f"📊 栄養データ: {result['nutrition_count']}件")
            print(f"🥄 サービングデータ: {result['serving_count']}件")
            print(f"🌐 ブラウザ: {result['browser_type']}")
        else:
            print(f"❌ ステータス: 失敗")
            if 'error' in result:
                print(f"🚨 エラー: {result['error']}")
            print(f"🌐 ブラウザ: {result.get('browser_type', 'unknown')}")

        print(f"🕐 完了時刻: {result['completed_at']}")

        return 0 if result['success'] else 1

    except Exception as e:
        print(f"❌ テスト実行中にエラー: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())