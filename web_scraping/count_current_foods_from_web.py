#!/usr/bin/env python3
"""
MyNetDiary Webサイトから現在の食材数をリアルタイムでカウント
既存のPlaywrightナビゲーターを使用してリアルタイムデータを取得
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# パス設定
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from components.playwright_multi_food_navigator import PlaywrightMultiFoodNavigator


class CurrentFoodCounter:
    """現在のWeb食材数カウンタークラス"""

    def __init__(self):
        self.navigator = None
        self.category_counts = {}
        self.total_foods = 0

    async def initialize_session(self) -> bool:
        """Playwrightセッションを初期化"""
        try:
            print("🚀 MyNetDiary現在食材数カウント開始")
            print("="*60)

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

    async def count_foods_in_category(self, category_name: str) -> int:
        """指定カテゴリの食材数をカウント"""
        try:
            print(f"\n📂 カテゴリカウント中: {category_name}")

            # カテゴリページに移動
            await self.navigator.page.goto("https://www.mynetdiary.com/food")
            await asyncio.sleep(2)

            # My Foodsをクリック
            await self.navigator.page.click("//span[text()='My Foods']")
            await asyncio.sleep(2)

            # Staple Foodsをクリック
            await self.navigator.page.click("//span[text()='Staple Foods']")
            await asyncio.sleep(3)

            # 対象カテゴリをクリック
            category_xpath = f"//span[text()='{category_name}']"
            try:
                await self.navigator.page.click(category_xpath)
                await asyncio.sleep(3)

                # 全ページを巡回して食材数をカウント
                total_count = 0
                page_num = 1

                while True:
                    print(f"   📄 ページ {page_num} をスキャン中...")

                    # 現在ページの食材リスト要素を取得
                    food_items = await self.navigator.page.locator("//li[contains(@class, 'MuiListItem-container')]//div[contains(@class, 'MuiListItemText-primary')]").all()

                    current_page_count = len(food_items)
                    total_count += current_page_count

                    print(f"   📊 ページ {page_num}: {current_page_count}食材")

                    if current_page_count == 0:
                        break

                    # 次ページボタンをチェック
                    try:
                        next_button = await self.navigator.page.locator("//button[@aria-label='Go to next page']").first
                        if await next_button.is_enabled():
                            await next_button.click()
                            await asyncio.sleep(2)
                            page_num += 1
                        else:
                            break
                    except:
                        # 次ページボタンがない場合は終了
                        break

                print(f"✅ {category_name}: {total_count}食材")
                return total_count

            except Exception as e:
                print(f"❌ カテゴリアクセスエラー ({category_name}): {e}")
                return 0

        except Exception as e:
            print(f"❌ カテゴリカウントエラー ({category_name}): {e}")
            return 0

    async def count_all_categories(self) -> Dict[str, int]:
        """全カテゴリの食材数をカウント"""

        # スクリプトで定義されている19カテゴリ
        categories = [
            "Beans & Peas",
            "Beverages",
            "Breads & Rolls",
            "Cheese",
            "Condiments, Dressings & Sauces",
            "Dairy, Dairy Substitutes & Egg",
            "Fats & Oils",
            "Fish & Seafood",
            "Fruit - canned, dried, or juice",
            "Fruit - raw or frozen",
            "Grains & Grain Products",
            "Meats",
            "Nuts & Seeds",
            "Poultry",
            "Spices & Herbs",
            "Stocks and Gravy",
            "Sweets & Sweeteners",
            "Vegetables - canned, dried, or juice",
            "Vegetables - raw, frozen, or cooked"
        ]

        print(f"🎯 対象カテゴリ: {len(categories)}個")

        results = {}

        for i, category in enumerate(categories, 1):
            print(f"\n🔄 進行状況: {i}/{len(categories)}")

            count = await self.count_foods_in_category(category)
            results[category] = count
            self.total_foods += count

            # カテゴリ間の待機
            if i < len(categories):
                print("⏳ 次のカテゴリまで3秒待機...")
                await asyncio.sleep(3)

        return results

    def print_results(self, results: Dict[str, int]):
        """結果を表示"""
        print(f"\n{'='*80}")
        print("🏁 MyNetDiary現在食材数カウント完了")
        print(f"{'='*80}")
        print(f"📅 スキャン日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 カテゴリ数: {len(results)}個")
        print(f"🍽️ 総食材数: {self.total_foods}個")
        print(f"📈 平均食材数/カテゴリ: {self.total_foods/len(results):.1f}個")

        print(f"\n📋 カテゴリ別食材数:")
        print("-" * 60)

        # 食材数の多い順にソート
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        for category, count in sorted_results:
            print(f"{category:<40}: {count:>3}食材")

        print("-" * 60)
        print(f"{'合計':<40}: {self.total_foods:>3}食材")

    def save_results(self, results: Dict[str, int]) -> str:
        """結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/current_food_count_from_web_{timestamp}.json"

        # dataディレクトリ作成
        Path("data").mkdir(exist_ok=True)

        data = {
            "scan_info": {
                "timestamp": datetime.now().isoformat(),
                "method": "direct_web_scraping",
                "source": "MyNetDiary website",
                "total_categories": len(results),
                "total_foods": self.total_foods
            },
            "category_counts": results,
            "sorted_by_count": sorted(results.items(), key=lambda x: x[1], reverse=True)
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 結果を保存: {filename}")
        return filename

    async def cleanup(self):
        """リソースクリーンアップ"""
        if self.navigator:
            await self.navigator.cleanup_session()

    async def run_count(self):
        """食材数カウント実行"""
        try:
            # 1. セッション初期化
            if not await self.initialize_session():
                return False

            # 2. 全カテゴリの食材数カウント
            results = await self.count_all_categories()

            # 3. 結果表示
            self.print_results(results)

            # 4. 結果保存
            filename = self.save_results(results)

            return True

        except Exception as e:
            print(f"❌ 食材数カウントエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.cleanup()


async def main():
    """メイン実行"""
    print("🔍 MyNetDiary現在食材数をWebから直接カウント")

    counter = CurrentFoodCounter()
    success = await counter.run_count()

    if success:
        print("\n🎉 カウント成功！")
        return 0
    else:
        print("\n❌ カウント失敗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)