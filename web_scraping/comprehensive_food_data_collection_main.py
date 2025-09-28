#!/usr/bin/env python3
"""
食材カタログデータを統合した網羅的食材データ収集メインスクリプト
全てのカテゴリの全ての食材に対してPlaywright版包括的データ収集を実行
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
tests_dir = current_dir / "tests"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(tests_dir))

from components.playwright_multi_food_navigator import PlaywrightMultiFoodNavigator
from components.playwright_food_data_collector import PlaywrightFoodDataCollector


class ComprehensiveFoodDataCollectionMain:
    """全食材対象の網羅的データ収集メインクラス"""

    def __init__(self):
        self.navigator = None
        self.data_collector = None
        self.food_catalog = {}
        self.all_foods = []

    def load_all_food_catalog_data(self, catalog_dir: str = "food_catalog_data") -> bool:
        """全てのカテゴリファイルから食材カタログデータを統合"""
        try:
            print("📁 全食材カタログデータを統合中...")

            catalog_path = Path(catalog_dir)
            if not catalog_path.exists():
                print(f"❌ カタログディレクトリが見つかりません: {catalog_dir}")
                return False

            json_files = list(catalog_path.glob("*.json"))
            if not json_files:
                print("❌ カタログファイルが見つかりません")
                return False

            total_categories = 0
            total_foods = 0
            category_summary = {}

            for file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    category_data = data['category_data']
                    category_name = category_data['name']
                    foods = category_data['foods']

                    # 重複カテゴリのチェック（最新のタイムスタンプを優先）
                    if category_name in self.food_catalog:
                        existing_timestamp = self.food_catalog[category_name].get('timestamp', '')
                        new_timestamp = data['collection_info'].get('timestamp', '')

                        if new_timestamp > existing_timestamp:
                            print(f"  🔄 {category_name}: 更新版を使用 ({len(foods)}食材)")
                            self.food_catalog[category_name] = {
                                'category_info': {
                                    'name': category_name,
                                    'xpath': category_data['xpath']
                                },
                                'foods': foods,
                                'timestamp': new_timestamp,
                                'food_count': len(foods)
                            }
                        else:
                            print(f"  ⏭️ {category_name}: 既存版を維持 ({len(self.food_catalog[category_name]['foods'])}食材)")
                            continue
                    else:
                        self.food_catalog[category_name] = {
                            'category_info': {
                                'name': category_name,
                                'xpath': category_data['xpath']
                            },
                            'foods': foods,
                            'timestamp': data['collection_info'].get('timestamp', ''),
                            'food_count': len(foods)
                        }

                    category_summary[category_name] = len(foods)
                    total_foods += len(foods)
                    total_categories += 1

                except Exception as e:
                    print(f"⚠️ ファイル処理エラー: {file_path.name} - {e}")
                    continue

            # 全食材リストを作成
            self.all_foods = []
            for category_name, category_data in self.food_catalog.items():
                for food in category_data['foods']:
                    food_info = {
                        'food_name': food['food_name'],
                        'category': category_name,
                        'navigation_info': food
                    }
                    self.all_foods.append(food_info)

            print(f"✅ 食材カタログ統合完了:")
            print(f"   📂 カテゴリ数: {len(self.food_catalog)}個")
            print(f"   🍽️ 総食材数: {len(self.all_foods)}個")

            # カテゴリ別食材数表示
            print(f"\n📊 カテゴリ別食材数:")
            for category, count in sorted(category_summary.items()):
                print(f"   {category}: {count}個")

            return len(self.all_foods) > 0

        except Exception as e:
            print(f"❌ 食材カタログ統合エラー: {e}")
            return False

    async def initialize_session(self) -> bool:
        """Playwrightセッションを初期化"""
        try:
            print("🚀 Playwright版網羅的データ収集セッション初期化中...")

            self.navigator = PlaywrightMultiFoodNavigator()

            # ナビゲーターのfood_catalogとfood_indexを設定
            self.navigator.food_catalog = self.food_catalog
            self.navigator._build_food_index()

            session_success = await self.navigator.initialize_session()

            if not session_success:
                print("❌ セッション初期化失敗")
                return False

            # データコレクターを初期化
            self.data_collector = PlaywrightFoodDataCollector(self.navigator.page)

            print("✅ Playwright版網羅的データ収集セッション初期化完了")
            return True

        except Exception as e:
            print(f"❌ セッション初期化エラー: {e}")
            return False

    def select_foods_for_collection(self, mode: str = "all", limit: int = None, category: str = None) -> List[str]:
        """収集対象食材を選択"""
        try:
            print(f"🎯 収集対象食材選択中 (モード: {mode})...")

            if mode == "all":
                selected_foods = [food['food_name'] for food in self.all_foods]
                if limit:
                    selected_foods = selected_foods[:limit]

            elif mode == "category" and category:
                if category in self.food_catalog:
                    selected_foods = [food['food_name'] for food in self.food_catalog[category]['foods']]
                    if limit:
                        selected_foods = selected_foods[:limit]
                else:
                    print(f"❌ カテゴリが見つかりません: {category}")
                    return []

            elif mode == "sample":
                # 各カテゴリから少数をサンプリング
                selected_foods = []
                sample_per_category = limit // len(self.food_catalog) if limit else 2

                for category_name, category_data in self.food_catalog.items():
                    category_foods = [food['food_name'] for food in category_data['foods'][:sample_per_category]]
                    selected_foods.extend(category_foods)

                if limit:
                    selected_foods = selected_foods[:limit]

            else:
                print(f"❌ 無効なモード: {mode}")
                return []

            print(f"✅ 選択完了: {len(selected_foods)}個の食材")
            return selected_foods

        except Exception as e:
            print(f"❌ 食材選択エラー: {e}")
            return []

    async def collect_food_data_comprehensive(self, food_names: List[str]) -> List[Dict]:
        """包括的食材データ収集"""
        print(f"🔬 網羅的包括的データ収集開始")
        print(f"📊 対象食材数: {len(food_names)}個")
        print(f"🎯 ワークフロー: 食材→serving→栄養素→FOODタブリセット→次の食材")

        results = []
        failed_foods = []

        for i, food_name in enumerate(food_names, 1):
            print(f"\n{'='*100}")
            print(f"🔄 網羅的データ収集 {i}/{len(food_names)}: {food_name[:50]}...")
            print(f"{'='*100}")

            start_time = datetime.now()

            try:
                # カタログ情報を取得
                catalog_info = self._get_food_catalog_info(food_name)

                # 1. 食材ページに移動
                print("🥘 食材ページに移動中...")
                nav_success = await self.navigator.navigate_to_food_stable(food_name)

                if not nav_success:
                    print(f"❌ 食材移動失敗: {food_name}")
                    failed_foods.append(food_name)
                    results.append({
                        "sequence": i,
                        "food_name": food_name,
                        "catalog_category": catalog_info.get("category", "unknown"),
                        "catalog_food_name": catalog_info.get("original_name", food_name),
                        "navigation_success": False,
                        "data_collection_success": False,
                        "reset_success": False,
                        "error": "食材ナビゲーション失敗",
                        "timestamp": datetime.now().isoformat()
                    })

                    # 失敗時でも少し待機
                    await asyncio.sleep(2)
                    continue

                # 2. 包括的データ収集（serving + 栄養素）
                print("📊 包括的データ収集実行...")
                food_data = await self.data_collector.collect_complete_food_data(food_name)

                # 3. FOODタブ経由リセット
                print("🔄 FOODタブ経由リセット実行...")
                reset_success = await self.navigator.reset_to_food_base_via_food_tab()

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # 結果をまとめる
                result = {
                    "sequence": i,
                    "food_name": food_name,
                    "catalog_category": catalog_info.get("category", "unknown"),
                    "catalog_food_name": catalog_info.get("original_name", food_name),
                    "navigation_success": nav_success,
                    "data_collection_success": food_data.get("collection_success", False),
                    "reset_success": reset_success,
                    "serving_options_count": len(food_data.get("serving_options", [])),
                    "nutrition_data_count": len(food_data.get("nutrition_data", {}).get("detailed_nutrients", {})),
                    "food_grade": food_data.get("nutrition_data", {}).get("food_grade", ""),
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "comprehensive_data": food_data,
                    "overall_success": nav_success and food_data.get("collection_success", False) and reset_success
                }

                if result["overall_success"]:
                    print(f"✅ 網羅的データ収集成功: {duration:.2f}秒")
                    print(f"   📂 カテゴリ: {catalog_info.get('category', 'unknown')}")
                    print(f"   📋 Serving: {result['serving_options_count']}個")
                    print(f"   🥗 栄養素: {result['nutrition_data_count']}種類")
                    print(f"   🔄 リセット: {'成功' if reset_success else '失敗'}")
                else:
                    print(f"❌ データ収集失敗")

                results.append(result)

                # 進行状況表示
                successful_count = sum(1 for r in results if r.get("overall_success", False))
                print(f"📈 進行状況: {i}/{len(food_names)} (成功: {successful_count}個, 失敗: {len(failed_foods)}個)")

                # 4. 次の食材のための安定化待機（最後の食材以外）
                if i < len(food_names):
                    print("⏳ 次の食材処理のための安定化待機...")
                    await asyncio.sleep(3)

            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                catalog_info = self._get_food_catalog_info(food_name)
                failed_foods.append(food_name)

                result = {
                    "sequence": i,
                    "food_name": food_name,
                    "catalog_category": catalog_info.get("category", "unknown"),
                    "catalog_food_name": catalog_info.get("original_name", food_name),
                    "navigation_success": False,
                    "data_collection_success": False,
                    "reset_success": False,
                    "error": str(e),
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "overall_success": False
                }

                print(f"❌ 網羅的データ収集エラー: {e}")
                results.append(result)

        print(f"\n🏁 網羅的データ収集完了!")
        print(f"📊 総処理数: {len(results)}個")
        print(f"✅ 成功: {sum(1 for r in results if r.get('overall_success', False))}個")
        print(f"❌ 失敗: {len(failed_foods)}個")

        return results

    def _get_food_catalog_info(self, food_name: str) -> Dict[str, str]:
        """食材のカタログ情報を取得"""
        try:
            # 全食材から検索
            for food in self.all_foods:
                if food['food_name'] == food_name:
                    return {
                        "category": food.get("category", "unknown"),
                        "original_name": food.get("food_name", food_name)
                    }

            return {
                "category": "unknown",
                "original_name": food_name
            }
        except Exception as e:
            print(f"⚠️ カタログ情報取得エラー: {e}")
            return {
                "category": "unknown",
                "original_name": food_name
            }

    def save_comprehensive_results(self, results: List[Dict], mode: str = "all") -> str:
        """包括的収集結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/comprehensive_food_collection_{mode}_{timestamp}.json"

        # dataディレクトリ作成
        Path("data").mkdir(exist_ok=True)

        # 統計情報を計算
        successful = [r for r in results if r.get("overall_success")]

        collection_data = {
            "collection_summary": {
                "timestamp": datetime.now().isoformat(),
                "method": "comprehensive_food_collection_main",
                "collection_mode": mode,
                "browser_type": "playwright-chromium",
                "total_foods": len(results),
                "successful": len(successful),
                "failed": len(results) - len(successful),
                "success_rate": len(successful) / len(results) * 100 if results else 0,
                "total_categories": len(set(r.get("catalog_category", "unknown") for r in results)),
                "average_duration": sum(r.get("duration_seconds", 0) for r in successful) / len(successful) if successful else 0
            },
            "collection_results": results,
            "food_catalog_summary": {
                "total_categories": len(self.food_catalog),
                "total_foods_in_catalog": len(self.all_foods),
                "categories": {name: data['food_count'] for name, data in self.food_catalog.items()}
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 網羅的収集結果を保存: {filename}")
        return filename

    async def cleanup(self):
        """リソースクリーンアップ"""
        if self.navigator:
            await self.navigator.cleanup_session()

    async def run_comprehensive_collection(self, mode: str = "sample", limit: int = 10, category: str = None):
        """網羅的食材データ収集を実行"""
        try:
            print("🚀 網羅的食材データ収集システム開始")
            print("="*120)

            # 1. 食材カタログデータ統合
            if not self.load_all_food_catalog_data():
                print("❌ 食材カタログデータ統合失敗")
                return False

            # 2. セッション初期化
            if not await self.initialize_session():
                print("❌ セッション初期化失敗")
                return False

            # 3. 収集対象食材選択
            selected_foods = self.select_foods_for_collection(mode=mode, limit=limit, category=category)
            if not selected_foods:
                print("❌ 収集対象食材が選択されませんでした")
                return False

            # 4. 包括的データ収集実行
            results = await self.collect_food_data_comprehensive(selected_foods)

            # 5. 結果保存
            filename = self.save_comprehensive_results(results, mode=mode)

            successful = [r for r in results if r.get("overall_success")]
            success_rate = len(successful) / len(results) * 100 if results else 0

            print(f"\n🎉 網羅的食材データ収集完了!")
            print(f"✅ 成功率: {success_rate:.1f}%")
            print(f"📁 結果ファイル: {filename}")

            return success_rate >= 50  # 50%以上の成功率で成功とみなす

        except Exception as e:
            print(f"❌ 網羅的データ収集システムエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.cleanup()


async def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description='網羅的食材データ収集')
    parser.add_argument('--mode', choices=['all', 'sample', 'category'], default='all',
                      help='収集モード (default: all)')
    parser.add_argument('--limit', type=int, default=None,
                      help='収集する食材数の上限 (default: 制限なし)')
    parser.add_argument('--category', type=str,
                      help='カテゴリモード時の対象カテゴリ名')

    args = parser.parse_args()

    print(f"🚀 網羅的食材データ収集開始")
    print(f"   モード: {args.mode}")
    if args.limit:
        print(f"   上限: {args.limit}個")
    else:
        print(f"   上限: 制限なし（全食材）")
    if args.category:
        print(f"   カテゴリ: {args.category}")

    collector = ComprehensiveFoodDataCollectionMain()
    success = await collector.run_comprehensive_collection(
        mode=args.mode,
        limit=args.limit,
        category=args.category
    )

    if success:
        print("🎉 実行成功！")
        return 0
    else:
        print("❌ 実行失敗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)