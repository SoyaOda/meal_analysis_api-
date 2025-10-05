#!/usr/bin/env python3
"""
食材カタログデータを統合した網羅的食材データ収集メインスクリプト
全てのカテゴリの全ての食材に対してPlaywright版包括的データ収集を実行
"""

import asyncio
import json
import logging
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


def setup_logging(log_level: str = "INFO") -> str:
    """
    リアルタイムログ機能を設定

    Args:
        log_level: ログレベル ("DEBUG", "INFO", "WARNING", "ERROR")

    Returns:
        str: 作成されたログファイルのパス
    """
    # logsディレクトリを作成
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # ログファイル名生成（タイムスタンプ付き）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"comprehensive_collection_{timestamp}.log"
    log_filepath = logs_dir / log_filename

    # ログレベル設定
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # ログフォーマット設定
    log_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 既存のハンドラーをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # ファイルハンドラー（リアルタイム書き込み）
    file_handler = logging.FileHandler(log_filepath, mode='w', encoding='utf-8')
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(log_format)
    file_handler.flush = lambda: file_handler.stream.flush()  # 強制フラッシュ

    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(log_format)

    # ハンドラーを追加
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # 初期ログメッセージ
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("📝 網羅的食材データ収集 - ログセッション開始")
    logger.info(f"📂 ログファイル: {log_filepath}")
    logger.info(f"🔧 ログレベル: {log_level}")
    logger.info("="*80)

    return str(log_filepath)


class ComprehensiveFoodDataCollectionMain:
    """全食材対象の網羅的データ収集メインクラス"""

    def __init__(self):
        self.navigator = None
        self.data_collector = None

    

    async def initialize_session(self) -> bool:
        """Playwrightセッションを初期化"""
        try:
            print("🚀 Playwright版網羅的データ収集セッション初期化中...")

            self.navigator = PlaywrightMultiFoodNavigator()

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

    def _select_foods_from_navigator(self, mode: str = "all", limit: int = None, category: str = None) -> List[str]:
        """失敗食材リストから収集対象食材を選択"""
        try:
            print(f"🎯 失敗食材リストから収集対象を選択中...")

            # 失敗食材リストファイルを読み込み
            failed_foods_file = Path("data/failed_foods_list.json")
            
            if not failed_foods_file.exists():
                print(f"❌ 失敗食材リストファイルが見つかりません: {failed_foods_file}")
                return []
            
            with open(failed_foods_file, 'r', encoding='utf-8') as f:
                failed_data = json.load(f)
            
            selected_foods = failed_data['failed_foods']
            
            print(f"✅ 失敗食材リスト読み込み完了: {len(selected_foods)}個")
            
            # limit が指定されている場合は制限
            if limit:
                selected_foods = selected_foods[:limit]
                print(f"   🔢 制限適用: {len(selected_foods)}個")
            
            print(f"\n📋 処理対象食材:")
            for i, food in enumerate(selected_foods[:10]):
                print(f"   {i+1}. {food}")
            if len(selected_foods) > 10:
                print(f"   ... 他 {len(selected_foods) - 10}個")
            
            return selected_foods

        except Exception as e:
            print(f"❌ 失敗食材リスト読み込みエラー: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def collect_food_data_comprehensive(self, food_names: List[str], save_interval: int = 10, existing_results: List[Dict] = None) -> List[Dict]:
        """包括的食材データ収集（中断再開対応）"""
        print(f"🔬 網羅的包括的データ収集開始")
        print(f"📊 対象食材数: {len(food_names)}個")
        print(f"🎯 ワークフロー: 食材→serving→栄養素→FOODタブリセット→次の食材")
        print(f"💾 中間保存間隔: {save_interval}食材ごと")

        # 既存結果があれば継続、なければ新規開始
        results = existing_results if existing_results else []
        failed_foods = []
        start_index = len(results)  # 既存結果の数から再開位置を決定

        if start_index > 0:
            print(f"🔄 再開モード: {start_index}食材目から継続")

        for i, food_name in enumerate(food_names, start_index + 1):
            print(f"\n{'='*100}")
            print(f"🔄 網羅的データ収集 {i}/{len(food_names) + start_index}: {food_name[:50]}...")
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
                print(f"📈 進行状況: {i}/{len(food_names) + start_index} (成功: {successful_count}個, 失敗: {len(failed_foods)}個)")

                # 中間保存（指定間隔ごと）
                if len(results) % save_interval == 0:
                    print(f"💾 中間保存実行 ({len(results)}食材処理完了)...")
                    mode = "all"  # デフォルトモード、実際は呼び出し元から渡す
                    self.save_intermediate_results(results, mode, len(results))

                # 4. 次の食材のための安定化待機（最後の食材以外）
                if i < len(food_names) + start_index:
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
            # navigator.food_catalogから検索
            for category_name, category_data in self.navigator.food_catalog.items():
                for food in category_data['foods']:
                    if food['food_name'] == food_name:
                        return {
                            "category": category_name,
                            "original_name": food['food_name']
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

    def find_latest_incomplete_file(self, data_dir: str = "data") -> str:
        """最新の未完了結果ファイルを検出"""
        try:
            data_path = Path(data_dir)
            if not data_path.exists():
                return None
            
            # comprehensive_food_collection_*.jsonファイルを検索
            json_files = list(data_path.glob("comprehensive_food_collection_*.json"))
            if not json_files:
                return None
            
            # 最新のファイルを選択（タイムスタンプ順）
            json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for file_path in json_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 収集が完了していないファイルかチェック
                    results = data.get('collection_results', [])
                    if not results:
                        continue
                    
                    # 全ての食材が処理済みかチェック
                    total_foods = data.get('collection_summary', {}).get('total_foods', 0)
                    successful = data.get('collection_summary', {}).get('successful', 0)
                    
                    # 完了していない、または成功率が100%未満の場合
                    if len(results) < total_foods or successful < len(results):
                        print(f"📄 未完了ファイル検出: {file_path.name}")
                        print(f"   進行状況: {len(results)}/{total_foods}食材")
                        return str(file_path)
                
                except Exception as e:
                    print(f"⚠️ ファイル検査エラー: {file_path.name} - {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ 未完了ファイル検出エラー: {e}")
            return None
    
    def load_existing_results(self, resume_file: str) -> Dict[str, Any]:
        """既存の結果ファイルを読み込み"""
        try:
            print(f"📖 既存結果ファイル読み込み: {resume_file}")
            
            with open(resume_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            results = existing_data.get('collection_results', [])
            print(f"✅ 既存結果読み込み完了: {len(results)}食材の記録")
            
            return existing_data
            
        except Exception as e:
            print(f"❌ 既存結果読み込みエラー: {e}")
            return {}
    
    def extract_completed_foods(self, existing_results: List[Dict]) -> set:
        """処理済み食材を抽出"""
        completed_foods = set()
        
        for result in existing_results:
            # data_collection_successがTrueの食材を処理済みとみなす
            # overall_successは古いフィールド名なので、両方をチェック
            is_completed = (result.get("data_collection_success", False) or 
                          result.get("overall_success", False))
            
            if is_completed:
                completed_foods.add(result.get("food_name", ""))
        
        print(f"📋 処理済み食材: {len(completed_foods)}個")
        return completed_foods

    def extract_failed_foods(self, existing_results: List[Dict]) -> List[str]:
        """失敗した食材を抽出（再実行対象）"""
        failed_foods = []
        
        for result in existing_results:
            # data_collection_successがFalseまたはoverall_successがFalseの食材を失敗とみなす
            is_failed = (not result.get("data_collection_success", True) or 
                        not result.get("overall_success", True))
            
            if is_failed:
                food_name = result.get("food_name", "")
                if food_name:
                    failed_foods.append(food_name)
        
        print(f"❌ 失敗食材（再実行対象）: {len(failed_foods)}個")
        return failed_foods
    
    def filter_remaining_foods(self, all_foods: List[str], completed_foods: set) -> List[str]:
        """未処理の食材をフィルタ"""
        remaining_foods = [food for food in all_foods if food not in completed_foods]
        
        print(f"🎯 残り処理対象: {len(remaining_foods)}個")
        if len(remaining_foods) < len(all_foods):
            print(f"⏭️ スキップ済み: {len(all_foods) - len(remaining_foods)}個")
        
        return remaining_foods
    
    def save_intermediate_results(self, results: List[Dict], mode: str, sequence: int) -> str:
        """中間結果を保存"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/comprehensive_food_collection_{mode}_{timestamp}_intermediate_{sequence}.json"
            
            # dataディレクトリ作成
            Path("data").mkdir(exist_ok=True)
            
            # 統計情報を計算
            successful = [r for r in results if r.get("overall_success")]
            
            # navigator.food_catalogから総食材数を計算
            total_foods_in_catalog = sum(len(category_data['foods']) for category_data in self.navigator.food_catalog.values())
            
            collection_data = {
                "collection_summary": {
                    "timestamp": datetime.now().isoformat(),
                    "method": "comprehensive_food_collection_main_with_resume",
                    "collection_mode": mode,
                    "browser_type": "playwright-chromium",
                    "total_foods": len(results),
                    "successful": len(successful),
                    "failed": len(results) - len(successful),
                    "success_rate": len(successful) / len(results) * 100 if results else 0,
                    "total_categories": len(set(r.get("catalog_category", "unknown") for r in results)),
                    "average_duration": sum(r.get("duration_seconds", 0) for r in successful) / len(successful) if successful else 0,
                    "is_intermediate": True,
                    "sequence": sequence
                },
                "collection_results": results,
                "food_catalog_summary": {
                    "total_categories": len(self.navigator.food_catalog),
                    "total_foods_in_catalog": total_foods_in_catalog,
                    "categories": {name: len(data['foods']) for name, data in self.navigator.food_catalog.items()}
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(collection_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 中間結果保存: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 中間結果保存エラー: {e}")
            return ""

    def save_comprehensive_results(self, results: List[Dict], mode: str = "all") -> str:
        """包括的収集結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/comprehensive_food_collection_{mode}_{timestamp}.json"

        # dataディレクトリ作成
        Path("data").mkdir(exist_ok=True)

        # 統計情報を計算
        successful = [r for r in results if r.get("overall_success")]

        # navigator.food_catalogから総食材数を計算
        total_foods_in_catalog = sum(len(category_data['foods']) for category_data in self.navigator.food_catalog.values())

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
                "total_categories": len(self.navigator.food_catalog),
                "total_foods_in_catalog": total_foods_in_catalog,
                "categories": {name: len(data['foods']) for name, data in self.navigator.food_catalog.items()}
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

    async def run_comprehensive_collection(self, mode: str = "sample", limit: int = 10, category: str = None, 
                                          auto_resume: bool = False, resume_file: str = None, save_interval: int = 10):
        """失敗食材リトライ専用の収集実行"""
        try:
            print("🚀 失敗食材リトライシステム開始")
            print("="*120)

            # 1. セッション初期化（先に実行）
            if not await self.initialize_session():
                print("❌ セッション初期化失敗")
                return False

            # 2. 食材カタログ読み込み（安定版を使用）
            print("📁 食材カタログ読み込み...")
            if not await self.navigator.load_food_catalog():
                print("❌ カタログ読み込み失敗")
                return False

            # 3. 失敗食材リストから収集対象を選択（auto-resumeは無視）
            all_selected_foods = self._select_foods_from_navigator(mode=mode, limit=limit, category=category)
            if not all_selected_foods:
                print("❌ 収集対象食材が選択されませんでした")
                return False

            # 4. 既存結果の確認（リトライ専用なので新規実行）
            existing_results = []
            print(f"\n🆕 新規実行: {len(all_selected_foods)}食材をリトライ")

            # 5. 包括的データ収集実行
            print(f"\n🔬 データ収集開始:")
            print(f"   📊 処理対象: {len(all_selected_foods)}食材")
            print(f"   💾 保存間隔: {save_interval}食材ごと")
            
            results = await self.collect_food_data_comprehensive(
                all_selected_foods, 
                save_interval=save_interval, 
                existing_results=existing_results
            )

            # 6. 最終結果保存（専用ファイル名）
            output_dir = Path("data")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = output_dir / f"retry_failed_foods_{timestamp}.json"
            
            output_data = {
                "collection_summary": {
                    "collection_mode": "retry_failed_foods",
                    "total_foods": len(results),
                    "successful_foods": len([r for r in results if r.get("overall_success")]),
                    "failed_foods": len([r for r in results if not r.get("overall_success")]),
                    "collection_timestamp": timestamp
                },
                "collection_results": results
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)

            successful = [r for r in results if r.get("overall_success")]
            failed = [r for r in results if not r.get("overall_success")]
            success_rate = len(successful) / len(results) * 100 if results else 0

            print(f"\n🎉 失敗食材リトライ完了!")
            print(f"✅ 成功率: {success_rate:.1f}%")
            print(f"✅ 成功: {len(successful)}個")
            print(f"❌ 失敗: {len(failed)}個")
            print(f"📁 結果ファイル: {filename}")
            
            if failed:
                print(f"\n⚠️ まだ失敗している食材:")
                for i, r in enumerate(failed[:10]):
                    print(f"   {i+1}. {r.get('food_name', 'Unknown')}")
                if len(failed) > 10:
                    print(f"   ... 他 {len(failed) - 10}個")

            return success_rate >= 50  # 50%以上の成功率で成功とみなす

        except Exception as e:
            print(f"❌ リトライシステムエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.cleanup()


async def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description='網羅的食材データ収集（中断再開対応）')
    parser.add_argument('--mode', choices=['all', 'sample', 'category'], default='all',
                      help='収集モード (default: all)')
    parser.add_argument('--limit', type=int, default=None,
                      help='収集する食材数の上限 (default: 制限なし)')
    parser.add_argument('--category', type=str,
                      help='カテゴリモード時の対象カテゴリ名')
    
    # 中断再開オプション
    parser.add_argument('--auto-resume', action='store_true',
                      help='自動的に最新の未完了ファイルから再開')
    parser.add_argument('--resume-file', type=str,
                      help='指定したファイルから再開（ファイルパス）')
    parser.add_argument('--save-interval', type=int, default=10,
                      help='中間保存の間隔（食材数、default: 10）')
    
    # ログ設定オプション
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                      default='INFO', help='ログレベル (default: INFO)')

    args = parser.parse_args()

    # ログ設定を最初に実行
    log_filepath = setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info(f"🚀 網羅的食材データ収集開始")
    logger.info(f"   モード: {args.mode}")
    if args.limit:
        logger.info(f"   上限: {args.limit}個")
    else:
        logger.info(f"   上限: 制限なし（全食材）")
    if args.category:
        logger.info(f"   カテゴリ: {args.category}")
    
    # 再開オプション表示
    if args.auto_resume:
        logger.info(f"   🔄 自動再開: 有効")
    elif args.resume_file:
        logger.info(f"   📄 再開ファイル: {args.resume_file}")
    else:
        logger.info(f"   🆕 新規実行")
    
    logger.info(f"   💾 中間保存間隔: {args.save_interval}食材ごと")
    logger.info(f"   📝 ログファイル: {log_filepath}")

    # 従来のprint文もそのまま残す（コンソール表示用）
    print(f"🚀 網羅的食材データ収集開始")
    print(f"   モード: {args.mode}")
    if args.limit:
        print(f"   上限: {args.limit}個")
    else:
        print(f"   上限: 制限なし（全食材）")
    if args.category:
        print(f"   カテゴリ: {args.category}")
    
    # 再開オプション表示
    if args.auto_resume:
        print(f"   🔄 自動再開: 有効")
    elif args.resume_file:
        print(f"   📄 再開ファイル: {args.resume_file}")
    else:
        print(f"   🆕 新規実行")
    
    print(f"   💾 中間保存間隔: {args.save_interval}食材ごと")

    collector = ComprehensiveFoodDataCollectionMain()
    success = await collector.run_comprehensive_collection(
        mode=args.mode,
        limit=args.limit,
        category=args.category,
        auto_resume=args.auto_resume,
        resume_file=args.resume_file,
        save_interval=args.save_interval
    )

    if success:
        logger.info("🎉 実行成功！")
        print("🎉 実行成功！")
        return 0
    else:
        logger.error("❌ 実行失敗")
        print("❌ 実行失敗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)