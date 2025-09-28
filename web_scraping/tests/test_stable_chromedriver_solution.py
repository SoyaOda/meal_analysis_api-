#!/usr/bin/env python3
"""
ChromeDriver安定性問題の決定的解決策を実装したテストスクリプト
Chrome 114/115移行期問題、macOSヘッドレスモード対応、新しいSelenium Manager活用
"""

import sys
import time
import json
import os
import psutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.components.stable_multi_food_navigator import StableMultiFoodNavigator
from src.components.comprehensive_food_data_collector import ComprehensiveFoodDataCollector
from config import config


class StableChromeDriverSolution:
    """ChromeDriver安定性問題の決定的解決策を実装"""

    def __init__(self):
        self.test_results = []
        self.food_catalog = None
        self.chrome_process_pids = set()

    def get_system_info(self):
        """システム情報とChrome/ChromeDriverバージョンを確認"""
        print("🔍 システム情報確認中...")

        try:
            # Chromeバージョン確認
            chrome_version = subprocess.run(
                ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                capture_output=True, text=True, timeout=10
            )
            print(f"  🌐 Chrome: {chrome_version.stdout.strip()}")
        except:
            print("  ⚠️ Chrome バージョン確認失敗")

        try:
            # ChromeDriverバージョン確認
            chromedriver_version = subprocess.run(
                ["chromedriver", "--version"],
                capture_output=True, text=True, timeout=10
            )
            print(f"  🚗 ChromeDriver: {chromedriver_version.stdout.strip()}")
        except:
            print("  ⚠️ ChromeDriver バージョン確認失敗")

        print(f"  🖥️ OS: macOS")
        print(f"  🐍 Python: {sys.version}")

    def get_stable_chrome_options(self):
        """Chrome 115+とmacOSヘッドレスモード対応の安定化オプション"""
        chrome_options = Options()

        # === Chrome 115+ 安定化オプション ===
        # 新しいヘッドレスモード（Chrome 115+推奨）
        chrome_options.add_argument("--headless=new")

        # 安定したウィンドウサイズ設定（macOS重要）
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")

        # macOS特有の安定化オプション
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=0")  # 動的ポート割り当て

        # === セッション安定化オプション ===
        # Chrome 114/115移行期対応
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-features=TranslateUI")

        # プロセス分離とクラッシュ防止
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-default-apps")

        # メモリ管理最適化
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")

        # ネットワーク安定化
        chrome_options.add_argument("--aggressive-cache-discard")
        chrome_options.add_argument("--disable-background-networking")

        # 自動化検出回避
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

        # === macOS専用設定 ===
        # 一時ディレクトリをユーザー権限範囲内に設定
        user_home = os.path.expanduser("~")
        temp_profile = f"{user_home}/.chrome_test_profile_{int(time.time())}"
        chrome_options.add_argument(f"--user-data-dir={temp_profile}")

        # ログレベル設定（デバッグ情報削減）
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")

        return chrome_options, temp_profile

    def create_stable_driver_session(self):
        """Chrome 115+ Selenium Manager活用で安定したドライバーセッションを作成"""
        print("🚀 安定化ChromeDriverセッション作成中...")

        # 既存プロセスクリーンアップ
        self.cleanup_chrome_processes()
        time.sleep(1)

        chrome_options, temp_profile = self.get_stable_chrome_options()

        try:
            # === Selenium Manager活用（推奨パターン）===
            # Chrome 115+ではService()を引数なしで呼び出し、
            # Selenium Managerに自動でドライバー管理を委ねる
            service = Service()

            # Chrome for Testing（CfT）対応の最新Selenium実装
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # プロセスID記録
            if hasattr(driver.service, 'process') and driver.service.process:
                chrome_pid = driver.service.process.pid
                self.chrome_process_pids.add(chrome_pid)
                print(f"  📝 ChromeDriverプロセス記録: PID {chrome_pid}")

            # 安定化設定
            driver.implicitly_wait(config.IMPLICIT_WAIT)

            # ページロード戦略設定（macOS安定化）
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                    });
                """
            })

            wait = WebDriverWait(driver, config.TIMEOUT)

            # コンポーネント初期化
            navigator = StableMultiFoodNavigator(driver, wait, config)
            data_collector = ComprehensiveFoodDataCollector(driver, wait, config)

            print("✅ 安定化ChromeDriverセッション作成完了")
            return driver, wait, navigator, data_collector, temp_profile

        except Exception as e:
            print(f"❌ ChromeDriverセッション作成失敗: {e}")
            # 失敗時の一時ディレクトリクリーンアップ
            try:
                if 'temp_profile' in locals() and os.path.exists(temp_profile):
                    import shutil
                    shutil.rmtree(temp_profile)
            except:
                pass
            raise

    def cleanup_chrome_processes(self):
        """強化されたChrome関連プロセスクリーンアップ"""
        print("🧹 Chrome関連プロセス完全クリーンアップ中...")

        # 記録されたPIDを終了
        for pid in self.chrome_process_pids.copy():
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    # 子プロセスも含めて終了
                    children = process.children(recursive=True)
                    for child in children:
                        child.terminate()
                    process.terminate()
                    process.wait(timeout=5)
                self.chrome_process_pids.discard(pid)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied):
                self.chrome_process_pids.discard(pid)

        # 残存Chromeプロセスの強制終了
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = proc.info['name']
                if name and ('chrome' in name.lower() or 'chromedriver' in name.lower()):
                    cmdline = proc.info.get('cmdline', [])
                    # テスト関連のプロセスのみ終了
                    if cmdline and any('test' in str(arg).lower() or 'chrome_test' in str(arg) for arg in cmdline):
                        print(f"  🔪 Chrome残存プロセス終了: PID {proc.info['pid']}")
                        proc.terminate()
                        try:
                            proc.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue

        print("✅ Chrome関連プロセス完全クリーンアップ完了")

    def stable_cleanup_session(self, driver, navigator, temp_profile):
        """安定化されたセッションクリーンアップ"""
        print("🧹 安定化セッションクリーンアップ開始...")

        try:
            # ナビゲーター固有のクリーンアップ
            if navigator:
                try:
                    navigator.cleanup_session()
                except:
                    pass

            # ドライバーの段階的終了
            if driver:
                try:
                    # 全タブを閉じる
                    handles = driver.window_handles
                    for handle in handles:
                        try:
                            driver.switch_to.window(handle)
                            driver.close()
                        except:
                            pass
                except:
                    pass

                try:
                    # ドライバープロセス終了
                    driver.quit()
                except:
                    pass

            # プロセス終了待機
            time.sleep(2)

            # プロセス強制クリーンアップ
            self.cleanup_chrome_processes()

            # 一時ディレクトリクリーンアップ
            try:
                if temp_profile and os.path.exists(temp_profile):
                    import shutil
                    shutil.rmtree(temp_profile)
                    print(f"  🗑️ 一時プロファイル削除: {temp_profile}")
            except Exception as e:
                print(f"  ⚠️ 一時プロファイル削除失敗: {e}")

        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")
            # エラーが発生してもプロセスクリーンアップは実行
            self.cleanup_chrome_processes()

        print("✅ 安定化セッションクリーンアップ完了")

    def load_food_catalog_once(self) -> bool:
        """食材カタログを一度だけ読み込み"""
        if self.food_catalog is not None:
            return True

        print("📁 食材カタログ読み込み...")
        try:
            driver, wait, navigator, data_collector, temp_profile = self.create_stable_driver_session()

            success = navigator.load_food_catalog()
            if success:
                self.food_catalog = navigator.food_catalog
                print(f"✅ 食材カタログ読み込み完了: {len(self.food_catalog)}カテゴリ")

            self.stable_cleanup_session(driver, navigator, temp_profile)
            return success
        except Exception as e:
            print(f"❌ 食材カタログ読み込みエラー: {e}")
            return False

    def select_test_foods(self, count: int = 3) -> List[str]:
        """テスト用食材を選択"""
        print(f"🎯 テスト用食材を選択中（{count}個）...")

        if not self.food_catalog:
            raise Exception("食材カタログが読み込まれていません")

        first_category = list(self.food_catalog.keys())[0]
        category_data = self.food_catalog[first_category]

        print(f"📂 対象カテゴリ: {first_category}")
        print(f"🍽️ カテゴリ内食材数: {len(category_data['foods'])}個")

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

    def collect_single_food_stable(self, food_name: str, sequence: int) -> Dict:
        """安定化ChromeDriverで単一食材のデータを収集"""
        print(f"\n{'='*80}")
        print(f"🔄 安定化ChromeDriver食材データ収集 {sequence}: {food_name[:50]}...")
        print(f"{'='*80}")

        start_time = datetime.now()
        driver = None
        navigator = None
        temp_profile = None

        try:
            # 1. 安定化ドライバーセッション作成
            print("🚀 安定化セッション作成...")
            driver, wait, navigator, data_collector, temp_profile = self.create_stable_driver_session()

            # 2. カタログと検索インデックス再構築
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

            # 5. 包括的データ収集
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
                "stable_driver_success": True,
                "serving_options_count": len(food_data.get("serving_options", [])),
                "nutrition_data_count": len(food_data.get("nutrition_data", {}).get("detailed_nutrients", {})),
                "food_grade": food_data.get("nutrition_data", {}).get("food_grade", ""),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "comprehensive_data": food_data,
                "overall_success": nav_success and food_data.get("collection_success", False)
            }

            if result["overall_success"]:
                print(f"✅ 安定化ChromeDriver収集成功: {duration:.2f}秒")
                print(f"   📋 Serving: {result['serving_options_count']}個")
                print(f"   🥗 栄養素: {result['nutrition_data_count']}種類")
                print(f"   🔄 安定化ドライバー: 成功")
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
                "stable_driver_success": False,
                "error": str(e),
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat(),
                "overall_success": False
            }

            print(f"❌ 安定化ChromeDriverエラー: {e}")
            return result

        finally:
            # 6. 安定化クリーンアップ
            print("🧹 安定化セッションクリーンアップ...")
            self.stable_cleanup_session(driver, navigator, temp_profile)

            # 次の食材のための待機
            print("⏳ 次の食材処理のための安定化待機...")
            time.sleep(3)

    def run_stable_test(self, food_count: int = 3):
        """安定化ChromeDriverテストを実行"""
        try:
            print("🔬 安定化ChromeDriver食材データ収集テスト開始")
            print("="*90)

            # システム情報確認
            self.get_system_info()

            # 1. 食材カタログ読み込み
            if not self.load_food_catalog_once():
                print("❌ カタログ読み込み失敗")
                return False

            # 2. テスト食材選択
            test_foods = self.select_test_foods(food_count)

            # 3. 安定化データ収集実行
            results = []
            for i, food_name in enumerate(test_foods, 1):
                result = self.collect_single_food_stable(food_name, i)
                results.append(result)

            # 4. 結果サマリー表示
            self.print_stable_summary(results)

            # 5. 結果保存
            filename = self.save_stable_results(results)

            overall_successful = [r for r in results if r.get("overall_success")]
            success_rate = len(overall_successful) / len(results) * 100 if results else 0

            print(f"\n🎉 安定化ChromeDriverテスト完了!")
            print(f"✅ 総合成功率: {success_rate:.1f}%")
            print(f"📁 結果ファイル: {filename}")

            return success_rate >= 66.7

        except Exception as e:
            print(f"❌ 安定化ChromeDriverテストエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 最終クリーンアップ
            self.cleanup_chrome_processes()

    def print_stable_summary(self, results: List[Dict]):
        """安定化結果サマリーを表示"""
        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_data = [r for r in results if r.get("data_collection_success")]
        successful_stable = [r for r in results if r.get("stable_driver_success")]
        overall_successful = [r for r in results if r.get("overall_success")]

        print(f"\n{'='*80}")
        print("🏁 安定化ChromeDriver結果サマリー")
        print(f"{'='*80}")
        print(f"📊 総テスト数: {len(results)}個")
        print(f"🧭 ナビゲーション成功: {len(successful_nav)}/{len(results)} ({len(successful_nav)/len(results)*100:.1f}%)")
        print(f"📋 データ収集成功: {len(successful_data)}/{len(results)} ({len(successful_data)/len(results)*100:.1f}%)")
        print(f"🔄 安定化ドライバー成功: {len(successful_stable)}/{len(results)} ({len(successful_stable)/len(results)*100:.1f}%)")
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
            stable_status = "✓" if result.get("stable_driver_success") else "✗"
            duration = result.get("duration_seconds", 0)
            serving_count = result.get("serving_options_count", 0)
            nutrient_count = result.get("nutrition_data_count", 0)

            print(f"  {status} {food_name:<30} N:{nav_status} D:{data_status} S:{stable_status} {duration:5.1f}s S:{serving_count:2d} Nu:{nutrient_count:2d}")

    def save_stable_results(self, results: List[Dict]) -> str:
        """安定化結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/stable_chromedriver_solution_{timestamp}.json"

        Path("data").mkdir(exist_ok=True)

        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_data = [r for r in results if r.get("data_collection_success")]
        successful_stable = [r for r in results if r.get("stable_driver_success")]
        overall_successful = [r for r in results if r.get("overall_success")]

        collection_data = {
            "collection_summary": {
                "timestamp": datetime.now().isoformat(),
                "method": "stable_chromedriver_solution_chrome115_macos_optimized",
                "total_foods": len(results),
                "successful_navigation": len(successful_nav),
                "successful_data_collection": len(successful_data),
                "successful_stable_driver": len(successful_stable),
                "overall_successful": len(overall_successful),
                "navigation_success_rate": len(successful_nav) / len(results) * 100 if results else 0,
                "data_collection_success_rate": len(successful_data) / len(results) * 100 if results else 0,
                "stable_driver_success_rate": len(successful_stable) / len(results) * 100 if results else 0,
                "overall_success_rate": len(overall_successful) / len(results) * 100 if results else 0
            },
            "collection_results": results,
            "stable_solutions": {
                "selenium_manager_integration": "implemented",
                "chrome_115_compatibility": "implemented",
                "macos_headless_optimization": "implemented",
                "session_stability_enhancement": "implemented",
                "process_cleanup_perfection": "implemented"
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(collection_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 安定化結果を保存: {filename}")
        return filename


def main():
    import argparse

    parser = argparse.ArgumentParser(description="安定化ChromeDriver食材データ収集テスト")
    parser.add_argument("-n", "--count", type=int, default=3,
                       help="収集する食材数")

    args = parser.parse_args()

    tester = StableChromeDriverSolution()
    success = tester.run_stable_test(args.count)

    if success:
        print(f"\n🎉 安定化ChromeDriverテストが成功しました！")
        exit(0)
    else:
        print(f"\n💥 安定化ChromeDriverテストが失敗しました。")
        exit(1)


if __name__ == "__main__":
    main()