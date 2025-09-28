#!/usr/bin/env python3
"""
安定的マルチ食材ナビゲーションテストスクリプト
一度ログインしたら複数の食材ページに順次移動してserving情報を抽出
"""

import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# プロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.components.stable_multi_food_navigator import StableMultiFoodNavigator
from src.components.raw_serving_extractor import RawServingExtractor
from src.components.modal_handler import ModalHandler
from config import config


class StableMultiNavigatorTester:
    """安定的マルチナビゲーションテストクラス"""

    def __init__(self):
        self.driver = None
        self.wait = None
        self.multi_navigator = None
        self.serving_extractor = None
        self.modal_handler = None
        self.test_results = []

    def setup_driver(self):
        """ChromeDriverを設定"""
        print("🚀 ChromeDriverを起動中...")
        chrome_options = Options()
        # ヘッドレスモードを無効化（テスト観察のため）
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(f"--user-agent={config.USER_AGENT}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(config.IMPLICIT_WAIT)
        self.wait = WebDriverWait(self.driver, config.TIMEOUT)

        # コンポーネントを初期化
        self.multi_navigator = StableMultiFoodNavigator(self.driver, self.wait, config)
        self.serving_extractor = RawServingExtractor(self.driver)
        self.modal_handler = ModalHandler(self.driver)

        print("✅ ChromeDriver起動完了")

    def select_test_foods(self, count: int = 5) -> List[str]:
        """
        テスト用食材を選択

        Args:
            count: 選択する食材数

        Returns:
            List[str]: 選択された食材名のリスト
        """
        print(f"🎯 テスト用食材を選択中（{count}個）...")

        # カタログから多様なカテゴリの食材を選択
        selected_foods = []

        # 各カテゴリから1つずつ選択
        categories_used = []
        for normalized_name, food_info in self.multi_navigator.food_index.items():
            category = food_info["category"]
            if category not in categories_used:
                selected_foods.append(food_info["original_name"])
                categories_used.append(category)
                if len(selected_foods) >= count:
                    break

        # 足りない場合はランダムに追加
        if len(selected_foods) < count:
            all_foods = list(self.multi_navigator.food_index.values())
            additional_foods = random.sample(all_foods, min(count - len(selected_foods), len(all_foods)))
            for food_info in additional_foods:
                if food_info["original_name"] not in selected_foods:
                    selected_foods.append(food_info["original_name"])

        print(f"✅ テスト食材選択完了:")
        for i, food_name in enumerate(selected_foods, 1):
            food_info = self.multi_navigator.find_food_by_name(food_name)
            category = food_info["category"] if food_info else "不明"
            print(f"   {i}. {food_name[:50]}... ({category})")

        return selected_foods[:count]

    def extract_serving_info(self, food_name: str) -> Dict:
        """
        現在の食材ページからserving情報を抽出

        Args:
            food_name: 食材名

        Returns:
            Dict: serving抽出結果
        """
        try:
            print(f"📊 serving情報抽出: {food_name[:30]}...")

            # Select Servingモーダルを開く
            modal_opened = self.modal_handler.open_serving_modal()
            if not modal_opened:
                return {
                    "success": False,
                    "error": "モーダルが開けませんでした",
                    "serving_options": []
                }

            # serving情報を抽出
            serving_options = self.serving_extractor.extract_raw_serving_options()

            # モーダルを閉じる
            self.modal_handler.close_modal()

            result = {
                "success": len(serving_options) > 0,
                "serving_options_count": len(serving_options),
                "serving_options": serving_options
            }

            if serving_options:
                print(f"✅ serving抽出成功: {len(serving_options)}個のオプション")
                for i, option in enumerate(serving_options[:3], 1):  # 最初の3個表示
                    print(f"  {i}. {option['raw_text']}")
                if len(serving_options) > 3:
                    print(f"  ... 他 {len(serving_options) - 3}個")
            else:
                print("❌ serving抽出失敗")

            return result

        except Exception as e:
            print(f"❌ serving抽出エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "serving_options": []
            }

    def test_multi_navigation_with_serving(self, food_names: List[str]) -> List[Dict]:
        """
        マルチナビゲーション + serving抽出の統合テスト

        Args:
            food_names: テストする食材名のリスト

        Returns:
            List[Dict]: 各食材のテスト結果
        """
        print(f"🧪 マルチナビゲーション + serving抽出テスト開始")
        print(f"📊 対象食材数: {len(food_names)}個")

        test_results = []

        for i, food_name in enumerate(food_names, 1):
            print(f"\n{'='*70}")
            print(f"🔄 食材テスト {i}/{len(food_names)}: {food_name[:40]}...")
            print(f"{'='*70}")

            start_time = datetime.now()

            try:
                # 1. 食材に移動
                nav_success = self.multi_navigator.navigate_to_food_stable(food_name)

                # 2. serving情報抽出（移動が成功した場合のみ）
                serving_result = {"success": False, "serving_options": []}
                if nav_success:
                    serving_result = self.extract_serving_info(food_name)

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # 結果をまとめる
                result = {
                    "sequence": i,
                    "food_name": food_name,
                    "navigation_success": nav_success,
                    "serving_extraction_success": serving_result.get("success", False),
                    "serving_options_count": len(serving_result.get("serving_options", [])),
                    "serving_options": serving_result.get("serving_options", []),
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "overall_success": nav_success and serving_result.get("success", False)
                }

                if result["overall_success"]:
                    print(f"✅ 統合テスト成功: {duration:.2f}秒")
                else:
                    print(f"❌ 統合テスト失敗")

                test_results.append(result)

                # 次の食材のための待機
                if i < len(food_names):
                    time.sleep(3)

            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                result = {
                    "sequence": i,
                    "food_name": food_name,
                    "navigation_success": False,
                    "serving_extraction_success": False,
                    "error": str(e),
                    "duration_seconds": duration,
                    "timestamp": datetime.now().isoformat(),
                    "overall_success": False
                }

                print(f"❌ 統合テストエラー: {e}")
                test_results.append(result)

        return test_results

    def print_test_summary(self, results: List[Dict]):
        """テスト結果サマリーを表示"""
        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_serving = [r for r in results if r.get("serving_extraction_success")]
        overall_successful = [r for r in results if r.get("overall_success")]

        print(f"\n{'='*70}")
        print("🏁 マルチナビゲーション統合テスト結果")
        print(f"{'='*70}")
        print(f"📊 総テスト数: {len(results)}個")
        print(f"🧭 ナビゲーション成功: {len(successful_nav)}/{len(results)} ({len(successful_nav)/len(results)*100:.1f}%)")
        print(f"📋 serving抽出成功: {len(successful_serving)}/{len(results)} ({len(successful_serving)/len(results)*100:.1f}%)")
        print(f"✅ 統合成功: {len(overall_successful)}/{len(results)} ({len(overall_successful)/len(results)*100:.1f}%)")

        if overall_successful:
            durations = [r["duration_seconds"] for r in overall_successful]
            total_serving_options = sum(r.get("serving_options_count", 0) for r in overall_successful)

            print(f"⏱️ 平均処理時間: {sum(durations)/len(durations):.2f}秒")
            print(f"📈 総serving options数: {total_serving_options}個")
            print(f"📊 平均serving options/食材: {total_serving_options/len(overall_successful):.1f}個")

        print(f"\n📋 個別結果:")
        for result in results:
            status = "✅" if result.get("overall_success") else "❌"
            food_name = result["food_name"][:25] + "..." if len(result["food_name"]) > 25 else result["food_name"]
            nav_status = "✓" if result.get("navigation_success") else "✗"
            serving_status = "✓" if result.get("serving_extraction_success") else "✗"
            duration = result.get("duration_seconds", 0)
            serving_count = result.get("serving_options_count", 0)

            print(f"  {status} {food_name:<30} Nav:{nav_status} Srv:{serving_status} {duration:5.1f}s {serving_count:2d}opts")

    def save_test_results(self, results: List[Dict]) -> str:
        """テスト結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"food_catalog_data/stable_multi_navigation_test_{timestamp}.json"

        # 統計情報を計算
        successful_nav = [r for r in results if r.get("navigation_success")]
        successful_serving = [r for r in results if r.get("serving_extraction_success")]
        overall_successful = [r for r in results if r.get("overall_success")]

        test_data = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "method": "stable_multi_navigation_with_serving",
                "total_tests": len(results),
                "successful_navigation": len(successful_nav),
                "successful_serving_extraction": len(successful_serving),
                "overall_successful": len(overall_successful),
                "navigation_success_rate": len(successful_nav) / len(results) * 100 if results else 0,
                "serving_success_rate": len(successful_serving) / len(results) * 100 if results else 0,
                "overall_success_rate": len(overall_successful) / len(results) * 100 if results else 0
            },
            "test_results": results,
            "statistics": {
                "total_serving_options": sum(r.get("serving_options_count", 0) for r in results),
                "avg_serving_options_per_food": sum(r.get("serving_options_count", 0) for r in overall_successful) / len(overall_successful) if overall_successful else 0
            }
        }

        # 統計情報を追加計算
        if overall_successful:
            durations = [r["duration_seconds"] for r in overall_successful]
            test_data["statistics"].update({
                "avg_duration_seconds": sum(durations) / len(durations),
                "min_duration_seconds": min(durations),
                "max_duration_seconds": max(durations)
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 テスト結果を保存: {filename}")
        return filename

    def cleanup(self):
        """リソースクリーンアップ"""
        if self.multi_navigator:
            self.multi_navigator.cleanup_session()
        if self.driver:
            self.driver.quit()

    def run_comprehensive_test(self, food_count: int = 5):
        """包括的テストを実行"""
        try:
            print("🧪 安定的マルチナビゲーション包括的テスト開始")
            print("="*80)

            self.setup_driver()

            # 1. カタログ読み込み
            print("📁 食材カタログ読み込み...")
            if not self.multi_navigator.load_food_catalog():
                print("❌ カタログ読み込み失敗")
                return False

            # 2. セッション初期化（ログイン）
            print("🔐 セッション初期化...")
            if not self.multi_navigator.initialize_session():
                print("❌ セッション初期化失敗")
                return False

            # 3. テスト食材選択
            test_foods = self.select_test_foods(food_count)

            # 4. マルチナビゲーション + serving抽出テスト
            results = self.test_multi_navigation_with_serving(test_foods)

            # 5. 結果サマリー表示
            self.print_test_summary(results)

            # 6. 結果保存
            filename = self.save_test_results(results)

            overall_successful = [r for r in results if r.get("overall_success")]
            success_rate = len(overall_successful) / len(results) * 100 if results else 0

            print(f"\n🎉 包括的テスト完了!")
            print(f"✅ 総合成功率: {success_rate:.1f}%")
            print(f"📁 結果ファイル: {filename}")

            return success_rate > 50  # 50%以上の成功率で成功とみなす

        except Exception as e:
            print(f"❌ 包括的テストエラー: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="安定的マルチナビゲーションテスト")
    parser.add_argument("-n", "--count", type=int, default=5,
                       help="テストする食材数")

    args = parser.parse_args()

    tester = StableMultiNavigatorTester()
    success = tester.run_comprehensive_test(args.count)

    if success:
        print(f"\n🎉 安定的マルチナビゲーションテストが成功しました！")
        exit(0)
    else:
        print(f"\n💥 安定的マルチナビゲーションテストが失敗しました。")
        exit(1)


if __name__ == "__main__":
    main()