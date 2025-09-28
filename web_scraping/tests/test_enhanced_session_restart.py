#!/usr/bin/env python3
"""
強化版セッション再開アプローチによる食材データ収集テストスクリプト
ChromeDriverメモリリーク対策とプロセス完全クリーンアップを実装
"""

import sys
import time
import json
import os
import psutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.components.stable_multi_food_navigator import StableMultiFoodNavigator
from src.components.comprehensive_food_data_collector import ComprehensiveFoodDataCollector
from config import config


class EnhancedSessionRestartTester:
    """強化版セッション再開アプローチによる食材データ収集テストクラス"""

    def __init__(self):
        self.test_results = []
        self.food_catalog = None
        self.chrome_process_pids = set()

    def get_enhanced_chrome_options(self):
        """メモリリーク対策を含む強化されたChromeオプション"""
        chrome_options = Options()

        # 基本オプション
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

        # メモリリーク対策オプション（重要）
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-features=TranslateUI")
        chrome_options.add_argument("--disable-ipc-flooding-protection")

        # プロセス分離とメモリ管理
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")

        # 一時ディレクトリ管理
        chrome_options.add_argument("--user-data-dir=/tmp/chrome_test_profile")
        chrome_options.add_argument("--data-path=/tmp/chrome_test_data")
        chrome_options.add_argument("--disk-cache-dir=/tmp/chrome_cache")

        # 安定性向上
        chrome_options.add_argument("--no-sandbox")  # 必要な場合のみ
        chrome_options.add_argument("--disable-dev-shm-usage")  # メモリリーク注意

        return chrome_options

    def cleanup_chrome_processes(self):
        """Chrome関連プロセスを強制終了"""
        print("🧹 Chrome関連プロセスのクリーンアップ中...")

        # 記録されたPIDを終了
        for pid in self.chrome_process_pids.copy():
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    process.terminate()
                    process.wait(timeout=5)
                self.chrome_process_pids.discard(pid)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                self.chrome_process_pids.discard(pid)

        # 残存Chromeプロセスの検索と終了
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and ('chrome' in proc.info['name'].lower() or
                                        'chromedriver' in proc.info['name'].lower()):
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('test' in arg for arg in cmdline):
                        print(f"  🔪 Chrome残存プロセス終了: PID {proc.info['pid']}")
                        proc.terminate()
                        proc.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue

        # 一時ディレクトリのクリーンアップ
        import shutil
        temp_dirs = ["/tmp/chrome_test_profile", "/tmp/chrome_test_data", "/tmp/chrome_cache"]
        for temp_dir in temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    print(f"  🗑️ 一時ディレクトリ削除: {temp_dir}")
            except Exception as e:
                print(f"  ⚠️ 一時ディレクトリ削除失敗: {temp_dir} - {e}")

    def create_enhanced_session(self):
        """強化版ブラウザセッションを作成"""
        print("🚀 強化版ブラウザセッション作成中...")

        # 事前クリーンアップ
        self.cleanup_chrome_processes()
        time.sleep(2)  # プロセス終了待機

        chrome_options = self.get_enhanced_chrome_options()

        # ChromeDriverサービス設定（macOS対応）
        service = Service()

        driver = webdriver.Chrome(service=service, options=chrome_options)

        # プロセスIDを記録
        try:
            chrome_pid = driver.service.process.pid
            self.chrome_process_pids.add(chrome_pid)
            print(f"  📝 ChromeDriverプロセス記録: PID {chrome_pid}")
        except:
            pass

        driver.implicitly_wait(config.IMPLICIT_WAIT)
        wait = WebDriverWait(driver, config.TIMEOUT)

        # コンポーネントを初期化
        navigator = StableMultiFoodNavigator(driver, wait, config)
        data_collector = ComprehensiveFoodDataCollector(driver, wait, config)

        print("✅ 強化版ブラウザセッション作成完了")
        return driver, wait, navigator, data_collector

    def enhanced_cleanup_session(self, driver, navigator):
        """強化版セッションクリーンアップ"""
        print("🧹 強化版セッションクリーンアップ開始...")

        try:
            # ナビゲーター固有のクリーンアップ
            if navigator:
                navigator.cleanup_session()

            # ドライバーの段階的終了
            if driver:
                try:
                    # 全てのウィンドウを閉じる
                    for handle in driver.window_handles:
                        driver.switch_to.window(handle)
                        driver.close()
                except:
                    pass

                # ドライバーを完全終了
                driver.quit()

            # プロセス終了待機
            time.sleep(1)

            # 強制プロセスクリーンアップ
            self.cleanup_chrome_processes()

        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")
            # エラーが発生してもプロセスクリーンアップは実行
            self.cleanup_chrome_processes()

        print("✅ 強化版セッションクリーンアップ完了")

    def load_food_catalog_once(self) -> bool:
        """食材カタログを一度だけ読み込み"""
        if self.food_catalog is not None:
            return True

        print("📁 食材カタログ読み込み...")
        driver, wait, navigator, data_collector = self.create_enhanced_session()

        try:
            success = navigator.load_food_catalog()
            if success:
                self.food_catalog = navigator.food_catalog
                print(f"✅ 食材カタログ読み込み完了: {len(self.food_catalog)}カテゴリ")

            self.enhanced_cleanup_session(driver, navigator)
            return success
        except Exception as e:
            print(f"❌ 食材カタログ読み込みエラー: {e}")
            self.enhanced_cleanup_session(driver, navigator)
            return False

    def select_test_foods(self, count: int = 3) -> List[str]:
        """テスト用食材を選択"""
        print(f"🎯 テスト用食材を選択中（{count}個）...")

        if not self.food_catalog:
            raise Exception("食材カタログが読み込まれていません")

        # 最初のカテゴリから食材を取得
        first_category = list(self.food_catalog.keys())[0]
        category_data = self.food_catalog[first_category]

        print(f"📂 対象カテゴリ: {first_category}")
        print(f"🍽️ カテゴリ内食材数: {len(category_data['foods'])}個")

        # 最初のN個の食材を選択
        selected_foods = []
        foods = category_data['foods']

        for i in range(min(count, len(foods))):
            food_name = foods[i]['food_name']
            selected_foods.append(food_name)

        print(f"✅ テスト食材選択完了:")
        for i, food_name in enumerate(selected_foods, 1):
            display_name = food_name.replace('\n', ' ')
            print(f"   {i}. {display_name[:50]}...")

        return selected_foods

    def collect_single_food_enhanced(self, food_name: str, sequence: int) -> Dict:
        """強化版セッション再開アプローチで単一食材のデータを収集"""
        print(f"\n{'='*80}")
        print(f"🔄 強化版セッション再開アプローチ食材データ収集 {sequence}: {food_name[:50]}...")
        print(f"{'='*80}")

        start_time = datetime.now()
        driver = None
        navigator = None

        try:
            # 1. 新しい強化版ブラウザセッションを作成
            print("🚀 強化版セッション作成...")
            driver, wait, navigator, data_collector = self.create_enhanced_session()

            # 2. カタログと検索インデックスを再構築
            navigator.food_catalog = self.food_catalog
            print("📁 食材カタログ再設定完了")

            print("🔍 検索インデックス再構築中...")
            navigator.food_index = {}
            for category_name, category_data in self.food_catalog.items():
                for food in category_data['foods']:
                    normalized_name = navigator._normalize_food_name(food['food_name'])
                    navigator.food_index[normalized_name] = {
                        "original_name": food['food_name'],
                        "category": category_name,
                        "navigation_info": food
                    }
            print(f"✅ 検索インデックス構築完了: {len(navigator.food_index)}個の食材")

            # 3. セッション初期化（ログイン）
            print("🔐 セッション初期化...")
            if not navigator.initialize_session():
                raise Exception("セッション初期化失敗")

            # 4. 食材ページに移動
            print("🧭 食材ページに移動中...")
            nav_success = navigator.navigate_to_food_stable(food_name)

            if not nav_success:
                raise Exception("食材ナビゲーション失敗")

            # 5. 包括的データ収集（serving + 栄養素）
            print("📊 包括的データ収集実行...")
            food_data = data_collector.collect_complete_food_data(food_name)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # 結果をまとめる
            result = {
                "sequence": sequence,
                "food_name": food_name,
                "navigation_success": nav_success,
                "data_collection_success": food_data.get("collection_success", False),
                "enhanced_session_success": True,
                "serving_options_count": len(food_data.get("serving_options", [])),
                "nutrition_data_count": len(food_data.get("nutrition_data", {}).get("detailed_nutrients", {})),
                "food_grade": food_data.get("nutrition_data", {}).get("food_grade", ""),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "comprehensive_data": food_data,
                "overall_success": nav_success and food_data.get("collection_success", False)
            }

            if result["overall_success"]:
                print(f"✅ 強化版セッション再開アプローチ収集成功: {duration:.2f}秒")
                print(f"   📋 Serving: {result['serving_options_count']}個")
                print(f"   🥗 栄養素: {result['nutrition_data_count']}種類")
                print(f"   🔄 強化版セッション: 成功")
            else:
                print(f"❌ データ収集失敗")

            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "sequence": sequence,
                "food_name": food_name,
                "navigation_success": False,
                "data_collection_success": False,
                "enhanced_session_success": False,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "overall_success": False
            }

            print(f"❌ 強化版セッション再開アプローチエラー: {e}")
            return result

        finally:
            # 6. 強化版セッションクリーンアップ
            print("🧹 強化版セッションクリーンアップ...")
            self.enhanced_cleanup_session(driver, navigator)

            # 次の食材のための待機
            print("⏳ 次の食材処理のための安定化待機...")
            time.sleep(5)  # 強化版では待機時間を増加

    def run_enhanced_test(self, food_count: int = 3):
        """強化版セッション再開アプローチテストを実行"""
        try:
            print("🔬 強化版セッション再開アプローチ食材データ収集テスト開始")
            print("="*90)

            # 1. 食材カタログ読み込み
            if not self.load_food_catalog_once():
                print("❌ カタログ読み込み失敗")
                return False

            # 2. テスト食材選択
            test_foods = self.select_test_foods(food_count)

            # 3. 強化版データ収集実行
            results = []
            for i, food_name in enumerate(test_foods, 1):
                result = self.collect_single_food_enhanced(food_name, i)
                results.append(result)

            # 4. 結果サマリー表示
            self.print_enhanced_summary(results)

            # 5. 結果保存
            filename = self.save_enhanced_results(results)

            overall_successful = [r for r in results if r.get("overall_success")]
            success_rate = len(overall_successful) / len(results) * 100 if results else 0

            print(f"\n🎉 強化版セッション再開アプローチテスト完了!")
            print(f"✅ 総合成功率: {success_rate:.1f}%")
            print(f"📁 結果ファイル: {filename}")

            return success_rate >= 66.7  # 2/3以上の成功率で成功とみなす

        except Exception as e:
            print(f"❌ 強化版セッション再開アプローチテストエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 最終クリーンアップ
            self.cleanup_chrome_processes()

    def print_enhanced_summary(self, results: List[Dict]):
        """強化版結果サマリーを表示"""
        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_data = [r for r in results if r.get("data_collection_success")]
        successful_enhanced = [r for r in results if r.get("enhanced_session_success")]
        overall_successful = [r for r in results if r.get("overall_success")]

        print(f"\n{'='*80}")
        print("🏁 強化版セッション再開アプローチ結果サマリー")
        print(f"{'='*80}")
        print(f"📊 総テスト数: {len(results)}個")
        print(f"🧭 ナビゲーション成功: {len(successful_nav)}/{len(results)} ({len(successful_nav)/len(results)*100:.1f}%)")
        print(f"📋 データ収集成功: {len(successful_data)}/{len(results)} ({len(successful_data)/len(results)*100:.1f}%)")
        print(f"🔄 強化版セッション成功: {len(successful_enhanced)}/{len(results)} ({len(successful_enhanced)/len(results)*100:.1f}%)")
        print(f"✅ 総合成功: {len(overall_successful)}/{len(results)} ({len(overall_successful)/len(results)*100:.1f}%)")

        if overall_successful:
            durations = [r["duration_seconds"] for r in overall_successful]
            total_serving = sum(r.get("serving_options_count", 0) for r in overall_successful)
            total_nutrients = sum(r.get("nutrition_data_count", 0) for r in overall_successful)

            print(f"⏱️ 平均処理時間: {sum(durations)/len(durations):.2f}秒")
            print(f"📈 総serving options数: {total_serving}個")
            print(f"🥗 総栄養素数: {total_nutrients}種類")

        print(f"\n📋 個別結果:")
        for result in results:
            status = "✅" if result.get("overall_success") else "❌"
            food_name = result["food_name"][:25] + "..." if len(result["food_name"]) > 25 else result["food_name"]
            nav_status = "✓" if result.get("navigation_success") else "✗"
            data_status = "✓" if result.get("data_collection_success") else "✗"
            enhanced_status = "✓" if result.get("enhanced_session_success") else "✗"
            duration = result.get("duration_seconds", 0)
            serving_count = result.get("serving_options_count", 0)
            nutrient_count = result.get("nutrition_data_count", 0)

            print(f"  {status} {food_name:<30} N:{nav_status} D:{data_status} E:{enhanced_status} {duration:5.1f}s S:{serving_count:2d} Nu:{nutrient_count:2d}")

    def save_enhanced_results(self, results: List[Dict]) -> str:
        """強化版収集結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/enhanced_session_restart_{timestamp}.json"

        # dataディレクトリ作成
        Path("data").mkdir(exist_ok=True)

        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_data = [r for r in results if r.get("data_collection_success")]
        successful_enhanced = [r for r in results if r.get("enhanced_session_success")]
        overall_successful = [r for r in results if r.get("overall_success")]

        collection_data = {
            "collection_summary": {
                "timestamp": datetime.now().isoformat(),
                "method": "enhanced_session_restart_with_memory_leak_prevention",
                "total_foods": len(results),
                "successful_navigation": len(successful_nav),
                "successful_data_collection": len(successful_data),
                "successful_enhanced_session": len(successful_enhanced),
                "overall_successful": len(overall_successful),
                "navigation_success_rate": len(successful_nav) / len(results) * 100 if results else 0,
                "data_collection_success_rate": len(successful_data) / len(results) * 100 if results else 0,
                "enhanced_session_success_rate": len(successful_enhanced) / len(results) * 100 if results else 0,
                "overall_success_rate": len(overall_successful) / len(results) * 100 if results else 0
            },
            "collection_results": results,
            "enhancements": {
                "memory_leak_prevention": "implemented",
                "process_force_cleanup": "implemented",
                "temp_directory_management": "implemented",
                "chrome_options_optimized": "implemented"
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 強化版収集結果を保存: {filename}")
        return filename


def main():
    import argparse

    parser = argparse.ArgumentParser(description="強化版セッション再開アプローチ食材データ収集テスト")
    parser.add_argument("-n", "--count", type=int, default=3,
                       help="収集する食材数")

    args = parser.parse_args()

    tester = EnhancedSessionRestartTester()
    success = tester.run_enhanced_test(args.count)

    if success:
        print(f"\n🎉 強化版セッション再開アプローチテストが成功しました！")
        exit(0)
    else:
        print(f"\n💥 強化版セッション再開アプローチテストが失敗しました。")
        exit(1)


if __name__ == "__main__":
    main()