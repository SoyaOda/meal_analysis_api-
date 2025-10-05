#!/usr/bin/env python3
"""
Cornstarchナビゲーション専用デバッグスクリプト
PDCA: 食材ページへのナビゲーション方法を改善
"""
import sys
import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# パスの設定
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from components.playwright_multi_food_navigator import PlaywrightMultiFoodNavigator
from components.playwright_food_data_collector import PlaywrightFoodDataCollector

def setup_logging():
    """ログの設定"""
    log_dir = current_dir / "debug"
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"cornstarch_debug_{timestamp}.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)

async def debug_food_catalog(navigator):
    """食材カタログの内容をデバッグ"""
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("🔍 食材カタログの調査")
    logger.info("=" * 60)

    # カタログ読み込み
    await navigator.load_food_catalog()

    # Cornstarchを含む食材を検索
    target = "Cornstarch"
    matching_foods = []

    # food_catalog構造: {category: {"category_info": {...}, "foods": [...]}}
    for category, category_data in navigator.food_catalog.items():
        foods = category_data.get("foods", [])
        for food in foods:
            food_name = food.get('food_name', food) if isinstance(food, dict) else food
            if target.lower() in food_name.lower():
                matching_foods.append({
                    "category": category,
                    "name": food_name,
                    "repr": repr(food_name),
                    "food_data": food
                })

    logger.info(f"\n'{target}'を含む食材: {len(matching_foods)}個")
    for i, item in enumerate(matching_foods):
        logger.info(f"  [{i}] カテゴリ: {item['category']}")
        logger.info(f"      名前: {item['name']}")
        logger.info(f"      repr: {item['repr']}")
        logger.info("")

    return matching_foods

async def debug_page_elements(navigator):
    """ページ上の食材要素をデバッグ"""
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("🔍 ページ上の食材要素を調査")
    logger.info("=" * 60)

    # ページ上のすべての食材要素を取得
    try:
        # food-items コンテナを探す
        food_items = await navigator.page.query_selector_all('[class*="food-item"]')
        logger.info(f"food-item要素: {len(food_items)}個")

        # 各要素のテキストを確認
        cornstarch_candidates = []
        for i, item in enumerate(food_items[:50]):  # 最初の50個のみ
            text = await item.inner_text()
            if "cornstarch" in text.lower():
                cornstarch_candidates.append({
                    "index": i,
                    "text": text,
                    "repr": repr(text)
                })

        logger.info(f"\nCornstarchを含む要素: {len(cornstarch_candidates)}個")
        for candidate in cornstarch_candidates:
            logger.info(f"  [{candidate['index']}]")
            logger.info(f"    テキスト: {candidate['text']}")
            logger.info(f"    repr: {candidate['repr']}")
            logger.info("")

        return cornstarch_candidates

    except Exception as e:
        logger.error(f"ページ要素取得エラー: {e}")
        return []

async def test_navigation_method_1(navigator, target_name):
    """方法1: 完全一致検索"""
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("📍 方法1: 完全一致検索")
    logger.info("=" * 60)

    try:
        success = await navigator.navigate_to_food_stable(target_name)
        logger.info(f"結果: {'✅ 成功' if success else '❌ 失敗'}")
        return success
    except Exception as e:
        logger.error(f"エラー: {e}")
        return False

async def test_navigation_method_2(navigator, target_name):
    """方法2: 改行文字を削除して検索"""
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("📍 方法2: 改行文字を削除")
    logger.info("=" * 60)

    # 改行を削除
    normalized_name = target_name.replace('\n', ' ')
    logger.info(f"正規化後: {repr(normalized_name)}")

    try:
        success = await navigator.navigate_to_food_stable(normalized_name)
        logger.info(f"結果: {'✅ 成功' if success else '❌ 失敗'}")
        return success
    except Exception as e:
        logger.error(f"エラー: {e}")
        return False

async def test_navigation_method_3(navigator, page):
    """方法3: 直接クリック（XPath使用）"""
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("📍 方法3: XPathで直接検索＆クリック")
    logger.info("=" * 60)

    try:
        # Cornstarchを含むテキストを持つ要素を検索
        # 複数のパターンを試す
        patterns = [
            "//div[contains(text(), 'Cornstarch')]",
            "//span[contains(text(), 'Cornstarch')]",
            "//*[contains(text(), 'Cornstarch')]",
            "//*[contains(., 'Cornstarch') and contains(., '488')]",
        ]

        for pattern in patterns:
            logger.info(f"  試行中: {pattern}")
            elements = await page.query_selector_all(f"xpath={pattern}")
            logger.info(f"    見つかった要素: {len(elements)}個")

            if elements:
                for i, elem in enumerate(elements[:3]):
                    text = await elem.inner_text()
                    logger.info(f"    [{i}] {repr(text[:100])}")

                # 最初の要素をクリック
                logger.info(f"  最初の要素をクリック...")
                await elements[0].click()
                await asyncio.sleep(2)

                # 成功判定
                url = page.url
                logger.info(f"  現在のURL: {url}")

                if "food" in url.lower():
                    logger.info("結果: ✅ 成功（食材ページに到達）")
                    return True

        logger.info("結果: ❌ 失敗（要素が見つからない）")
        return False

    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_data_collection(navigator, data_collector):
    """データ収集をテスト"""
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("📡 データ収集テスト")
    logger.info("=" * 60)

    try:
        # 現在のページからデータを収集
        food_data = await data_collector.collect_complete_food_data("Cornstarch, cup 488cals")

        if food_data.get('collection_success'):
            serving_count = len(food_data.get('serving_options', {}).get('raw_serving_data', []))
            nutrition_count = len(food_data.get('nutrition_data', {}).get('detailed_nutrients', {}).get('raw_nutrition_data', []))

            logger.info(f"✅ データ収集成功")
            logger.info(f"  Serving: {serving_count}個")
            logger.info(f"  Nutrition: {nutrition_count}個")

            # Servingデータのサンプルを表示
            if serving_count > 0:
                serving_data = food_data['serving_options']['raw_serving_data']
                logger.info("\n  Serving サンプル（最初の20個）:")
                for i, item in enumerate(serving_data[:20]):
                    logger.info(f"    [{i}] {item}")

            return True
        else:
            logger.error("❌ データ収集失敗")
            return False

    except Exception as e:
        logger.error(f"エラー: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """メイン処理"""
    logger = setup_logging()

    logger.info("🧪 Cornstarch ナビゲーションデバッグ開始")
    logger.info("=" * 60)

    navigator = None

    try:
        # ナビゲーターの初期化
        navigator = PlaywrightMultiFoodNavigator()
        await navigator.initialize_session()

        # データコレクターの初期化
        data_collector = PlaywrightFoodDataCollector(navigator.page)

        # Phase 1: 食材カタログの調査
        logger.info("\n📚 Phase 1: 食材カタログ調査")
        matching_foods = await debug_food_catalog(navigator)

        if not matching_foods:
            logger.error("❌ カタログにCornstarchが見つかりません")
            return False

        target_name = matching_foods[0]['name']
        logger.info(f"\n🎯 ターゲット食材: {repr(target_name)}")

        # Phase 2: ページ要素の調査
        logger.info("\n📄 Phase 2: ページ要素調査")
        page_candidates = await debug_page_elements(navigator)

        # Phase 3: ナビゲーション方法のテスト
        logger.info("\n🧭 Phase 3: ナビゲーション方法テスト")

        # 方法1
        await navigator.reset_to_food_base_via_food_tab()
        await asyncio.sleep(1)
        success_1 = await test_navigation_method_1(navigator, target_name)

        # 方法2
        if not success_1:
            await navigator.reset_to_food_base_via_food_tab()
            await asyncio.sleep(1)
            success_2 = await test_navigation_method_2(navigator, target_name)
        else:
            success_2 = False

        # 方法3
        if not success_1 and not success_2:
            await navigator.reset_to_food_base_via_food_tab()
            await asyncio.sleep(1)
            success_3 = await test_navigation_method_3(navigator, navigator.page)
        else:
            success_3 = False

        # Phase 4: データ収集テスト
        if success_1 or success_2 or success_3:
            logger.info("\n📊 Phase 4: データ収集テスト")
            success_data = await test_data_collection(navigator, data_collector)

            if success_data:
                logger.info("\n🎉 完全成功！Serving情報取得完了")
                return True

        logger.error("\n❌ すべての方法が失敗")
        return False

    except Exception as e:
        logger.error(f"❌ エラー発生: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    finally:
        if navigator:
            await navigator.cleanup_session()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
