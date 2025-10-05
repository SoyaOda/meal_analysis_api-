#!/usr/bin/env python3
"""
失敗食材（Kosher salt）のserving情報取得テスト
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
    print("🧪 Kosher salt Serving情報取得テスト（直接パターンマッチ版）")
    print("=" * 60)

    navigator = None

    try:
        # ナビゲーターの初期化
        navigator = PlaywrightMultiFoodNavigator()
        await navigator.initialize_session()
        await navigator.load_food_catalog()

        # データコレクターの初期化
        data_collector = PlaywrightFoodDataCollector(navigator.page)

        # Kosher saltにナビゲート
        target_name = "Kosher salt, tsp\n0cals"
        print(f"\n🎯 ターゲット: {repr(target_name)}")

        success = await navigator.navigate_to_food_stable(target_name)

        if not success:
            print("❌ ナビゲーション失敗")
            return False

        print("✅ ナビゲーション成功")

        # 修正版のserving情報収集を実行
        print("\n📡 修正版serving情報収集中...")
        serving_data = await data_collector._extract_serving_options()

        print(f"\n📊 収集結果:")
        print(f"   総要素数: {serving_data.get('total_servings_found', 0)}")
        print(f"   改善版serving数: {len(serving_data.get('improved_servings', []))}")

        print(f"\n🔍 Raw serving data（最初の30個）:")
        raw_data = serving_data.get('raw_serving_data', [])
        for i, text in enumerate(raw_data[:30], 1):
            print(f"   [{i}] {text}")

        print(f"\n✅ Improved servings:")
        improved = serving_data.get('improved_servings', [])
        for i, serving in enumerate(improved, 1):
            print(f"   [{i}] {serving}")

        # 結果を保存
        output_file = f"debug/kosher_salt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serving_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 結果保存: {output_file}")

        return len(improved) > 0

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
