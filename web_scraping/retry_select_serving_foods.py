#!/usr/bin/env python3
"""
Select Serving不在の63食材のServing options情報を再取得
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from src.components.playwright_multi_food_navigator import PlaywrightMultiFoodNavigator
from src.components.playwright_food_data_collector import PlaywrightFoodDataCollector


async def main():
    # ログファイル設定
    log_file = Path('important_data/retry_select_serving_log.txt')

    def log_print(message):
        """コンソールとログファイルの両方に出力"""
        print(message)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(message + '\n')

    # ログファイル初期化
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"=== Select Serving再収集ログ ===\n")
        f.write(f"開始時刻: {datetime.now().isoformat()}\n\n")

    log_print("🔄 Select Serving不在食材の再収集")
    log_print("=" * 80)

    # データ読み込み
    data_file = Path('important_data/complete_scraping_data_1188_foods.json')
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = data['collection_results']

    # Select Serving不在の食材を抽出
    failed_foods = []
    for i, item in enumerate(results, 1):
        comp_data = item.get('comprehensive_data', {})
        serving_options = comp_data.get('serving_options', {})
        raw_serving_data = serving_options.get('raw_serving_data', [])

        if 'Select Serving' not in raw_serving_data:
            failed_foods.append({
                'sequence': i,
                'food_name': item.get('food_name', ''),
                'catalog_category': item.get('catalog_category', ''),
                'original_item': item
            })

    log_print(f"対象食材数: {len(failed_foods)}個")
    log_print("")

    # 全63食材を処理
    log_print(f"📝 全{len(failed_foods)}食材を再収集します")
    log_print("")

    # Playwrightセッション初期化
    navigator = PlaywrightMultiFoodNavigator()
    await navigator.initialize_session()

    data_collector = PlaywrightFoodDataCollector(navigator.page)

    # カタログ読み込み
    log_print("📚 カタログ読み込み中...")
    await navigator.load_food_catalog()
    log_print("✅ カタログ読み込み完了")
    log_print("")

    # 再収集結果
    retry_results = []

    for i, food_item in enumerate(failed_foods, 1):
        food_name = food_item['food_name']
        category = food_item['catalog_category']

        log_print(f"🔍 {i}/{len(failed_foods)}: {food_name}")
        log_print(f"   カテゴリ: {category}")

        try:
            # 食材ページに移動
            log_print("   → 食材ページへ移動中...")
            nav_success = await navigator.navigate_to_food_stable(food_name)

            if not nav_success:
                log_print("   ❌ ナビゲーション失敗")
                retry_results.append({
                    'food_name': food_name,
                    'navigation_success': False,
                    'data_collection_success': False
                })
                continue

            log_print("   ✅ ナビゲーション成功")

            # 包括的データ収集
            log_print("   → データ収集中...")
            food_data = await data_collector.collect_complete_food_data(food_name)

            if food_data:
                log_print("   ✅ データ収集成功")

                # Serving options確認
                serving_options = food_data.get('serving_options', {})
                raw_serving_data = serving_options.get('raw_serving_data', [])

                if 'Select Serving' in raw_serving_data:
                    log_print("   🎉 'Select Serving'発見！")
                else:
                    log_print("   ⚠️  'Select Serving'なし")

                retry_results.append({
                    'food_name': food_name,
                    'navigation_success': True,
                    'data_collection_success': True,
                    'comprehensive_data': food_data,
                    'has_select_serving': 'Select Serving' in raw_serving_data
                })
            else:
                log_print("   ❌ データ収集失敗")
                retry_results.append({
                    'food_name': food_name,
                    'navigation_success': True,
                    'data_collection_success': False
                })

            # FOODタブ経由リセット
            log_print("   → リセット中...")
            await navigator.reset_to_food_base_via_food_tab()
            log_print("   ✅ リセット完了")

        except Exception as e:
            log_print(f"   ❌ エラー: {e}")
            retry_results.append({
                'food_name': food_name,
                'error': str(e)
            })

        log_print("")

    # セッション終了
    await navigator.cleanup_session()

    # 結果保存
    output_data = {
        'retry_summary': {
            'timestamp': datetime.now().isoformat(),
            'total_retry': len(retry_results),
            'successful': sum(1 for r in retry_results if r.get('data_collection_success')),
            'failed': sum(1 for r in retry_results if not r.get('data_collection_success'))
        },
        'retry_results': retry_results
    }

    output_file = Path('important_data/retry_select_serving_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    log_print("=" * 80)
    log_print("📊 実行結果")
    log_print("=" * 80)
    log_print(f"再収集試行: {len(retry_results)}個")
    log_print(f"成功: {sum(1 for r in retry_results if r.get('data_collection_success'))}個")
    log_print(f"失敗: {sum(1 for r in retry_results if not r.get('data_collection_success'))}個")
    log_print("")
    log_print(f"💾 結果保存: {output_file}")
    log_print(f"📝 ログ保存: {log_file}")


if __name__ == "__main__":
    asyncio.run(main())
