#!/usr/bin/env python3
"""
失敗食材の単体テスト用スクリプト
Cornstarch, cup 488cals の収集をテストして不具合を再現
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

def setup_logging():
    """ログの設定"""
    log_dir = os.path.join(current_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'single_food_test_{timestamp}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)

async def test_single_food_collection():
    """単一食材のデータ収集テスト"""
    logger = setup_logging()

    # テスト対象の食材
    test_food_name = "Cornstarch, cup 488cals"

    logger.info(f"🧪 単体テスト開始: {test_food_name}")

    try:
        # ナビゲーターの初期化
        navigator = PlaywrightMultiFoodNavigator()

        # セッション初期化
        logger.info("🚀 セッション初期化中...")
        await navigator.initialize_session()

        # コレクターの初期化（navigatorのpageを使用）
        data_collector = PlaywrightFoodDataCollector(navigator.page)

        # 食材カタログ読み込み
        logger.info("📚 食材カタログ読み込み中...")
        await navigator.load_food_catalog()

        # 1. ナビゲーションテスト
        logger.info("🎯 食材ナビゲーションテスト開始...")
        nav_success = await navigator.navigate_to_food_stable(test_food_name)

        logger.info(f"  - Navigation Success: {nav_success}")

        if not nav_success:
            logger.error("❌ ナビゲーションに失敗しました")
            result = {
                "test_food": test_food_name,
                "navigation_success": False,
                "data_collection_success": False,
                "error": "食材ナビゲーション失敗",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 2. データ収集テスト
            logger.info("📡 データ収集テスト開始...")
            food_data = await data_collector.collect_complete_food_data(test_food_name)

            # 3. リセットテスト
            logger.info("🔄 リセットテスト開始...")
            reset_success = await navigator.reset_to_food_base_via_food_tab()

            # 結果の分析
            logger.info("📊 収集結果の分析:")
            logger.info(f"  - Navigation Success: {nav_success}")
            logger.info(f"  - Data Collection Success: {food_data.get('collection_success', False)}")
            logger.info(f"  - Reset Success: {reset_success}")

            # comprehensive_dataの詳細分析
            if food_data.get('collection_success', False):
                serving_data = food_data.get('serving_options', {}).get('raw_serving_data', [])
                nutrition_data = food_data.get('nutrition_data', {}).get('detailed_nutrients', {}).get('raw_nutrition_data', [])

                logger.info(f"  - Serving Data Count: {len(serving_data)}")
                logger.info(f"  - Nutrition Data Count: {len(nutrition_data)}")

                if serving_data:
                    logger.info("  - Sample Serving Data:")
                    for i, item in enumerate(serving_data[:10]):
                        logger.info(f"    [{i}]: {str(item)[:100]}...")

                if nutrition_data:
                    logger.info("  - Sample Nutrition Data:")
                    for i, item in enumerate(nutrition_data[:10]):
                        logger.info(f"    [{i}]: {str(item)[:100]}...")
            else:
                logger.warning("  - データ収集に失敗しました")

            result = {
                "test_food": test_food_name,
                "navigation_success": nav_success,
                "data_collection_success": food_data.get('collection_success', False),
                "reset_success": reset_success,
                "serving_data_count": len(food_data.get('serving_options', {}).get('raw_serving_data', [])),
                "nutrition_data_count": len(food_data.get('nutrition_data', {}).get('detailed_nutrients', {}).get('raw_nutrition_data', [])),
                "comprehensive_data": food_data,
                "timestamp": datetime.now().isoformat()
            }

        # 結果を保存
        output_file = f"single_food_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 結果保存: {output_file}")

        # 不具合の判定
        if not result.get('data_collection_success', False):
            logger.error("❌ 不具合再現: データ収集に失敗しました")
            return False
        else:
            logger.info("✅ 成功: データ収集が成功しました")
            return True

    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {str(e)}")
        import traceback
        logger.error(f"詳細エラー: {traceback.format_exc()}")
        return False
    finally:
        # ナビゲーターのクリーンアップ
        try:
            await navigator.cleanup_session()
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_single_food_collection())
    sys.exit(0 if success else 1)