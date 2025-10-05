#!/usr/bin/env python3
"""
単一食材のナビゲーション問題を詳細デバッグするスクリプト
失敗食材: "Water, cup 0cals" (Beverages)を対象に徹底分析
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# パス設定
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from components.playwright_multi_food_navigator import PlaywrightMultiFoodNavigator


class SingleFoodNavigationDebugger:
    """単一食材ナビゲーション詳細デバッガー"""

    def __init__(self):
        self.navigator = None
        self.debug_logs = []
        self.page_screenshots = []

    async def initialize_session(self) -> bool:
        """デバッグ用セッション初期化"""
        try:
            print("🔍 ナビゲーションデバッグセッション開始")
            print("="*80)

            self.navigator = PlaywrightMultiFoodNavigator()
            session_success = await self.navigator.initialize_session()

            if not session_success:
                print("❌ セッション初期化失敗")
                return False

            print("✅ セッション初期化完了")
            return True

        except Exception as e:
            print(f"❌ セッション初期化エラー: {e}")
            return False

    async def load_food_catalog_debug(self) -> bool:
        """食材カタログ読み込み（デバッグ付き）"""
        try:
            print("\n📁 食材カタログ読み込み（デバッグモード）...")

            if not await self.navigator.load_food_catalog():
                print("❌ カタログ読み込み失敗")
                return False

            print("✅ カタログ読み込み完了")
            print(f"   📂 カテゴリ数: {len(self.navigator.food_catalog)}個")

            # Beveragesカテゴリの詳細確認
            if "Beverages" in self.navigator.food_catalog:
                beverages = self.navigator.food_catalog["Beverages"]
                print(f"   🥤 Beveragesカテゴリ: {len(beverages['foods'])}個の食材")

                # Water関連食材を検索
                water_foods = [food for food in beverages['foods']
                             if 'water' in food['food_name'].lower()]
                print(f"   💧 Water関連食材: {len(water_foods)}個")
                for water_food in water_foods[:5]:
                    print(f"      - {water_food['food_name']}")

            return True

        except Exception as e:
            print(f"❌ カタログ読み込みエラー: {e}")
            return False

    async def debug_page_state(self, step_name: str) -> Dict[str, Any]:
        """現在のページ状態を詳細記録"""
        try:
            page_info = {
                "step": step_name,
                "timestamp": datetime.now().isoformat(),
                "url": self.navigator.page.url,
                "title": await self.navigator.page.title(),
                "visible_elements": [],
                "categories_found": [],
                "food_items_found": [],
                "modals_detected": [],
                "error_messages": []
            }

            # 画面スクリーンショット撮影
            screenshot_path = f"debug/screenshot_{step_name}_{datetime.now().strftime('%H%M%S')}.png"
            Path("debug").mkdir(exist_ok=True)
            await self.navigator.page.screenshot(path=screenshot_path)
            page_info["screenshot"] = screenshot_path
            print(f"   📸 スクリーンショット保存: {screenshot_path}")

            # カテゴリ要素の検索
            try:
                category_elements = await self.navigator.page.query_selector_all("//span[contains(@class, 'MuiTypography')]")
                category_texts = []
                for elem in category_elements[:20]:  # 最初の20個
                    text = await elem.text_content()
                    if text and len(text.strip()) > 0:
                        category_texts.append(text.strip())
                page_info["categories_found"] = category_texts
                print(f"   📂 カテゴリ要素発見: {len(category_texts)}個")
            except Exception as e:
                page_info["categories_found"] = [f"エラー: {e}"]

            # 食材リスト要素の検索
            try:
                food_elements = await self.navigator.page.query_selector_all("//li[contains(@class, 'MuiListItem')]")
                food_texts = []
                for elem in food_elements[:10]:  # 最初の10個
                    text = await elem.text_content()
                    if text and len(text.strip()) > 0:
                        food_texts.append(text.strip())
                page_info["food_items_found"] = food_texts
                print(f"   🍽️ 食材要素発見: {len(food_texts)}個")
            except Exception as e:
                page_info["food_items_found"] = [f"エラー: {e}"]

            # モーダル・ダイアログの検出
            try:
                modal_selectors = [
                    "//div[contains(@class, 'MuiDialog')]",
                    "//div[contains(@class, 'modal')]",
                    "//div[contains(@class, 'overlay')]",
                    "//div[contains(@role, 'dialog')]"
                ]
                for selector in modal_selectors:
                    modals = await self.navigator.page.query_selector_all(selector)
                    if modals:
                        page_info["modals_detected"].append(f"{selector}: {len(modals)}個")
            except Exception as e:
                page_info["modals_detected"] = [f"エラー: {e}"]

            # エラーメッセージの検出
            try:
                error_selectors = [
                    "//div[contains(@class, 'error')]",
                    "//div[contains(@class, 'warning')]",
                    "//*[contains(text(), 'error') or contains(text(), 'Error')]"
                ]
                for selector in error_selectors:
                    errors = await self.navigator.page.query_selector_all(selector)
                    if errors:
                        for error in errors:
                            text = await error.text_content()
                            if text:
                                page_info["error_messages"].append(text.strip())
            except Exception as e:
                page_info["error_messages"] = [f"エラー: {e}"]

            self.debug_logs.append(page_info)
            return page_info

        except Exception as e:
            print(f"❌ ページ状態デバッグエラー: {e}")
            return {"error": str(e)}

    async def test_water_navigation_detailed(self) -> bool:
        """Water食材のナビゲーションを詳細テスト"""
        target_food = "Water, cup\n0cals"

        try:
            print(f"\n🎯 ターゲット食材詳細テスト: {target_food}")
            print("-" * 80)

            # Step 1: 初期状態の記録
            await self.debug_page_state("01_initial_state")

            # Step 2: 食材ベース画面への移動
            print("\n🧭 食材ベース画面に移動中...")
            base_success = await self.navigator._navigate_to_food_base()
            await self.debug_page_state("02_after_base_navigation")

            if not base_success:
                print("❌ 食材ベース画面移動失敗")
                return False
            print("✅ 食材ベース画面移動成功")

            # Step 3: Beveragesカテゴリ選択
            print("\n📂 Beveragesカテゴリ選択中...")
            beverages_info = self.navigator.food_catalog["Beverages"]
            category_xpath = beverages_info['category_info']['xpath']

            print(f"   使用するXPath: {category_xpath}")
            category_success = await self.navigator._select_category("Beverages", category_xpath)
            await self.debug_page_state("03_after_category_selection")

            if not category_success:
                print("❌ Beveragesカテゴリ選択失敗")
                # 代替セレクター試行
                print("🔄 代替セレクター試行中...")
                await self.try_alternative_category_selectors("Beverages")
                await self.debug_page_state("03b_after_alternative_category")
                return False
            print("✅ Beveragesカテゴリ選択成功")

            # Step 4: Water食材を検索
            print(f"\n🔍 {target_food} を検索中...")

            # 現在ページの全食材リストを取得
            food_elements = await self.navigator.page.query_selector_all("//li[contains(@class, 'MuiListItem')]")
            print(f"   ページ上の食材要素数: {len(food_elements)}個")

            # 各食材要素のテキストを確認
            found_foods = []
            water_candidates = []

            for i, elem in enumerate(food_elements[:50]):  # 最初の50個をチェック
                try:
                    text = await elem.text_content()
                    if text:
                        text = text.strip()
                        found_foods.append(f"{i+1}: {text}")

                        # Water関連食材をチェック
                        if 'water' in text.lower():
                            water_candidates.append((i, text, elem))
                            print(f"   💧 Water候補発見 {i+1}: {text}")

                        # 完全一致チェック
                        if text == target_food or text == "Water, cup\n0cals":
                            print(f"   🎯 ターゲット完全一致発見 {i+1}: {text}")
                            water_candidates.append((i, text, elem))

                except Exception as e:
                    found_foods.append(f"{i+1}: エラー - {e}")

            await self.debug_page_state("04_after_food_search")

            # 検索結果をログに記録
            search_results = {
                "target_food": target_food,
                "total_elements": len(food_elements),
                "water_candidates": len(water_candidates),
                "found_foods_sample": found_foods[:20]  # 最初の20個
            }

            print(f"\n📊 検索結果:")
            print(f"   対象食材: {target_food}")
            print(f"   総要素数: {len(food_elements)}個")
            print(f"   Water候補: {len(water_candidates)}個")

            if water_candidates:
                print(f"   候補詳細:")
                for idx, text, elem in water_candidates:
                    print(f"     {idx+1}: {text}")

                # 最初の候補をクリック試行
                print(f"\n🖱️ 最初のWater候補をクリック試行...")
                try:
                    target_elem = water_candidates[0][2]
                    await target_elem.scroll_into_view_if_needed()
                    await asyncio.sleep(1)
                    await target_elem.click()
                    await asyncio.sleep(2)

                    await self.debug_page_state("05_after_food_click")
                    print("✅ 食材クリック成功")
                    return True

                except Exception as e:
                    print(f"❌ 食材クリック失敗: {e}")
                    await self.debug_page_state("05_after_food_click_failed")
                    return False
            else:
                print("❌ Water食材が見つかりません")

                # デバッグ用: 見つかった食材をすべて表示
                print("\n📋 見つかった食材（サンプル）:")
                for food in found_foods[:10]:
                    print(f"     {food}")

                return False

        except Exception as e:
            print(f"❌ Water食材ナビゲーションテストエラー: {e}")
            await self.debug_page_state("error_state")
            import traceback
            traceback.print_exc()
            return False

    async def try_alternative_category_selectors(self, category_name: str):
        """代替カテゴリセレクター試行"""
        alternative_selectors = [
            f"//span[text()='{category_name}']",
            f"//span[contains(text(), '{category_name}')]",
            f"//*[contains(@class, 'category') and contains(text(), '{category_name}')]",
            f"//div[contains(text(), '{category_name}')]",
            f"//li[contains(text(), '{category_name}')]"
        ]

        print(f"   🔄 代替セレクター試行 ({len(alternative_selectors)}個):")
        for i, selector in enumerate(alternative_selectors):
            try:
                print(f"     {i+1}. {selector}")
                elements = await self.navigator.page.query_selector_all(selector)
                if elements:
                    print(f"        ✅ 発見: {len(elements)}個の要素")
                    # 最初の要素をクリック試行
                    try:
                        await elements[0].click()
                        await asyncio.sleep(2)
                        print(f"        ✅ クリック成功")
                        return True
                    except Exception as click_e:
                        print(f"        ❌ クリック失敗: {click_e}")
                else:
                    print(f"        ❌ 要素なし")
            except Exception as e:
                print(f"        ❌ セレクターエラー: {e}")

        return False

    def save_debug_results(self) -> str:
        """デバッグ結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debug/navigation_debug_water_{timestamp}.json"

        Path("debug").mkdir(exist_ok=True)

        debug_data = {
            "test_info": {
                "target_food": "Water, cup 0cals",
                "category": "Beverages",
                "timestamp": datetime.now().isoformat(),
                "test_purpose": "ナビゲーション失敗原因の詳細分析"
            },
            "debug_logs": self.debug_logs,
            "screenshots": self.page_screenshots
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 デバッグ結果保存: {filename}")
        return filename

    async def cleanup(self):
        """リソースクリーンアップ"""
        if self.navigator:
            await self.navigator.cleanup_session()

    async def run_debug_test(self):
        """デバッグテスト実行"""
        try:
            # 1. セッション初期化
            if not await self.initialize_session():
                return False

            # 2. 食材カタログ読み込み
            if not await self.load_food_catalog_debug():
                return False

            # 3. Water食材ナビゲーションテスト
            success = await self.test_water_navigation_detailed()

            # 4. 結果保存
            self.save_debug_results()

            print(f"\n{'='*80}")
            print("🏁 ナビゲーションデバッグテスト完了")
            print(f"{'='*80}")
            print(f"🎯 テスト結果: {'✅ 成功' if success else '❌ 失敗'}")
            print(f"📊 記録されたデバッグログ: {len(self.debug_logs)}個")

            return success

        except Exception as e:
            print(f"❌ デバッグテスト実行エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.cleanup()


async def main():
    """メイン実行"""
    print("🔍 単一食材ナビゲーション詳細デバッグテスト")
    print("対象食材: Water, cup 0cals (Beverages)")

    debugger = SingleFoodNavigationDebugger()
    success = await debugger.run_debug_test()

    if success:
        print("\n🎉 デバッグテスト成功！")
        print("   ナビゲーション問題が特定され、解決策を検証できました。")
        return 0
    else:
        print("\n❌ デバッグテスト失敗")
        print("   詳細なログが保存されました。分析して対策を検討します。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)