#!/usr/bin/env python3
"""
全カテゴリ順次収集スクリプト
単一カテゴリ収集スクリプトを使用して全19カテゴリを順次処理
"""

import time
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


class AllCategoriesCollector:
    """全カテゴリ順次収集クラス"""

    def __init__(self):
        # 実際の食材カテゴリ19個
        self.food_categories = [
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

        self.collection_results = []
        self.script_path = Path(__file__).parent / "single_category_collector.py"

    def collect_single_category(self, category_name, retry_count=3):
        """単一カテゴリを収集（リトライ機能付き）"""
        print(f"\n{'='*60}")
        print(f"🎯 カテゴリ収集: {category_name}")
        print(f"{'='*60}")

        for attempt in range(retry_count):
            try:
                if attempt > 0:
                    print(f"🔄 リトライ {attempt}/{retry_count-1}")
                    time.sleep(5)  # リトライ前の待機

                # 単一カテゴリ収集スクリプトを実行
                cmd = [sys.executable, str(self.script_path), category_name]

                print(f"📋 実行コマンド: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10分タイムアウト
                )

                if result.returncode == 0:
                    print(f"✅ {category_name} 収集成功")

                    # 出力からファイル名を抽出
                    output_lines = result.stdout.split('\n')
                    saved_file = None
                    for line in output_lines:
                        if "保存ファイル:" in line:
                            saved_file = line.split("保存ファイル:")[-1].strip()
                            break

                    return {
                        "category": category_name,
                        "success": True,
                        "attempt": attempt + 1,
                        "saved_file": saved_file,
                        "stdout": result.stdout,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    print(f"❌ {category_name} 収集失敗 (終了コード: {result.returncode})")
                    print(f"   stderr: {result.stderr}")

            except subprocess.TimeoutExpired:
                print(f"⏰ {category_name} 収集タイムアウト（10分経過）")
            except Exception as e:
                print(f"💥 {category_name} 収集エラー: {e}")

        # 全リトライ失敗
        return {
            "category": category_name,
            "success": False,
            "attempts": retry_count,
            "error": "All retry attempts failed",
            "timestamp": datetime.now().isoformat()
        }

    def collect_all_categories(self, start_index=0, delay_between_categories=10):
        """全カテゴリを順次収集"""
        print("🚀 全カテゴリ順次収集開始")
        print("="*60)
        print(f"📊 対象カテゴリ: {len(self.food_categories)}個")
        print(f"⏱️ カテゴリ間隔: {delay_between_categories}秒")
        print(f"🎯 開始インデックス: {start_index}")

        target_categories = self.food_categories[start_index:]

        start_time = datetime.now()

        for i, category in enumerate(target_categories):
            category_index = start_index + i + 1

            print(f"\n🔄 進捗: {category_index}/{len(self.food_categories)}")

            # カテゴリ収集実行
            result = self.collect_single_category(category)
            self.collection_results.append(result)

            # 結果表示
            if result["success"]:
                print(f"✅ {category}: 収集成功")
                if result.get("saved_file"):
                    print(f"📁 保存: {result['saved_file']}")
            else:
                print(f"❌ {category}: 収集失敗")

            # 最後のカテゴリ以外は待機
            if i < len(target_categories) - 1:
                print(f"⏳ 次のカテゴリまで{delay_between_categories}秒待機...")
                time.sleep(delay_between_categories)

        end_time = datetime.now()
        duration = end_time - start_time

        # 結果サマリー
        self.print_summary(duration)

        # 結果保存
        summary_file = self.save_collection_summary(start_index)

        return summary_file

    def print_summary(self, duration):
        """収集結果サマリーを表示"""
        successful = [r for r in self.collection_results if r["success"]]
        failed = [r for r in self.collection_results if not r["success"]]

        print(f"\n{'='*60}")
        print("🏁 全カテゴリ収集完了")
        print(f"{'='*60}")
        print(f"⏱️ 総所要時間: {duration}")
        print(f"📊 収集結果: {len(successful)}/{len(self.collection_results)} 成功")
        print(f"✅ 成功: {len(successful)}個")
        print(f"❌ 失敗: {len(failed)}個")

        if successful:
            print(f"\n✅ 成功したカテゴリ:")
            for result in successful:
                print(f"   📂 {result['category']}")

        if failed:
            print(f"\n❌ 失敗したカテゴリ:")
            for result in failed:
                print(f"   💥 {result['category']}")

    def save_collection_summary(self, start_index):
        """収集サマリーを保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"food_catalog_data/collection_summary_{timestamp}.json"

        successful = [r for r in self.collection_results if r["success"]]
        failed = [r for r in self.collection_results if not r["success"]]

        summary_data = {
            "collection_summary": {
                "timestamp": datetime.now().isoformat(),
                "method": "sequential_category_collection",
                "start_index": start_index,
                "total_categories": len(self.food_categories),
                "processed_categories": len(self.collection_results),
                "successful_categories": len(successful),
                "failed_categories": len(failed),
                "success_rate": len(successful) / len(self.collection_results) * 100 if self.collection_results else 0
            },
            "target_categories": self.food_categories,
            "collection_results": self.collection_results,
            "successful_categories": [r["category"] for r in successful],
            "failed_categories": [r["category"] for r in failed]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        print(f"\n📄 収集サマリーを保存: {filename}")
        return filename

    def list_existing_collections(self):
        """既存の収集データを確認"""
        data_dir = Path("food_catalog_data")
        if not data_dir.exists():
            print("📁 food_catalog_data フォルダが見つかりません")
            return

        json_files = list(data_dir.glob("*.json"))

        if not json_files:
            print("📄 既存の収集データがありません")
            return

        print("📋 既存の収集データ:")
        print("="*50)

        category_files = [f for f in json_files if not f.name.startswith("collection_summary")]
        summary_files = [f for f in json_files if f.name.startswith("collection_summary")]

        print(f"📂 カテゴリデータ: {len(category_files)}個")
        for f in sorted(category_files):
            print(f"   📄 {f.name}")

        print(f"\n📊 サマリーファイル: {len(summary_files)}個")
        for f in sorted(summary_files):
            print(f"   📄 {f.name}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="全カテゴリ順次収集スクリプト")
    parser.add_argument("-s", "--start", type=int, default=0,
                       help="開始カテゴリインデックス (0-18)")
    parser.add_argument("-d", "--delay", type=int, default=10,
                       help="カテゴリ間の待機秒数")
    parser.add_argument("-l", "--list", action="store_true",
                       help="既存の収集データを表示")

    args = parser.parse_args()

    collector = AllCategoriesCollector()

    if args.list:
        collector.list_existing_collections()
        return

    # 収集実行
    summary_file = collector.collect_all_categories(args.start, args.delay)

    if summary_file:
        print(f"\n🎉 全カテゴリ収集が完了しました！")
        print(f"📁 サマリー: {summary_file}")
    else:
        print(f"\n💥 全カテゴリ収集でエラーが発生しました。")


if __name__ == "__main__":
    main()