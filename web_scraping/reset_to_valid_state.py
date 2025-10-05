#!/usr/bin/env python3
"""
MyNetDiary収集データを有効な状態にリセットするスクリプト
品質チェッカーで修正されたファイルをベースとして、resume機能で再実行可能な状態にする
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class DataStateReset:
    """データ状態リセッター"""

    def __init__(self):
        self.data_dir = Path("data")

    def find_best_reference_file(self) -> Path:
        """最適な参照ファイルを見つける"""
        json_files = list(self.data_dir.glob("comprehensive_food_collection_all_*.json"))

        if not json_files:
            raise FileNotFoundError("参照ファイルが見つかりません")

        # 品質修正済みファイルを探す
        corrected_files = []
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                summary = data.get("collection_summary", {})
                if summary.get("quality_corrected"):
                    corrected_files.append((file_path, summary))
            except:
                continue

        if corrected_files:
            # 最新の品質修正済みファイルを選択
            best_file = max(corrected_files, key=lambda x: x[1].get("correction_timestamp", ""))
            return best_file[0]
        else:
            # 品質修正済みがない場合は最新ファイル
            return max(json_files, key=lambda f: f.stat().st_mtime)

    def analyze_current_state(self, file_path: Path) -> Dict[str, Any]:
        """現在の状態を分析"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        collection_results = data.get("collection_results", [])
        summary = data.get("collection_summary", {})

        analysis = {
            "file_path": str(file_path),
            "total_foods": len(collection_results),
            "original_successful": summary.get("successful", 0),
            "original_failed": summary.get("failed", 0),
            "quality_corrected": summary.get("quality_corrected", False),
            "corrections_made": summary.get("corrections_made", 0),
            "failed_items": [],
            "needs_retry": []
        }

        # 失敗したアイテムとリトライが必要なアイテムを特定
        for item in collection_results:
            if not item.get("data_collection_success"):
                failed_item = {
                    "sequence": item.get("sequence"),
                    "food_name": item.get("food_name"),
                    "category": item.get("catalog_category"),
                    "reason": item.get("data_quality_issue", "Unknown failure")
                }
                analysis["failed_items"].append(failed_item)

                # resume機能で再実行可能なアイテムかチェック
                if not item.get("error") and item.get("navigation_success"):
                    analysis["needs_retry"].append(failed_item)

        return analysis

    def create_resume_file(self, source_file: Path, target_name: str = None) -> Path:
        """resume機能用のファイルを作成"""
        if not target_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_name = f"comprehensive_food_collection_resume_{timestamp}.json"

        target_path = self.data_dir / target_name

        with open(source_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # resume用にサマリーを調整
        if "collection_summary" in data:
            summary = data["collection_summary"]
            summary["method"] = "comprehensive_food_collection_main_with_resume"
            summary["reset_for_resume"] = True
            summary["reset_timestamp"] = datetime.now().isoformat()
            summary["source_file"] = str(source_file.name)

        # バックアップとして保存
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return target_path

    def generate_retry_statistics(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """リトライ統計を生成"""
        failed_by_category = {}
        retry_by_category = {}

        for item in analysis["failed_items"]:
            category = item["category"]
            failed_by_category[category] = failed_by_category.get(category, 0) + 1

        for item in analysis["needs_retry"]:
            category = item["category"]
            retry_by_category[category] = retry_by_category.get(category, 0) + 1

        return {
            "total_failed": len(analysis["failed_items"]),
            "total_retry_candidates": len(analysis["needs_retry"]),
            "retry_rate": len(analysis["needs_retry"]) / len(analysis["failed_items"]) if analysis["failed_items"] else 0,
            "failed_by_category": failed_by_category,
            "retry_by_category": retry_by_category
        }

    def create_retry_instructions(self, analysis: Dict[str, Any]) -> str:
        """リトライ実行手順を生成"""
        stats = self.generate_retry_statistics(analysis)

        instructions = f"""
# MyNetDiary データ収集 Resume 実行手順

## 現在の状態
- 総食材数: {analysis['total_foods']}
- 元の成功数: {analysis['original_successful']}
- 元の失敗数: {analysis['original_failed']}
- 品質修正による追加失敗: {analysis['corrections_made']}
- 現在の失敗数: {len(analysis['failed_items'])}
- リトライ候補: {stats['total_retry_candidates']}

## カテゴリ別失敗統計
"""

        for category, count in stats["failed_by_category"].items():
            retry_count = stats["retry_by_category"].get(category, 0)
            instructions += f"- {category}: {count}件失敗 (リトライ候補: {retry_count}件)\n"

        instructions += f"""
## Resume実行コマンド

```bash
# web_scrapingディレクトリに移動
cd /Users/odasoya/meal_analysis_api_2/web_scraping

# Resume機能で失敗したアイテムを再実行
python src/main_comprehensive_food_collection.py --mode resume --input {analysis['file_path'].split('/')[-1]}
```

## 期待される結果
- {stats['total_retry_candidates']}件の食材の再収集を試行
- 品質チェック機能により、UIノイズは自動的に失敗として判定
- 有効な栄養データが取得できた場合のみ成功として記録

## 注意事項
1. 新しい品質チェック機能により、無効データは自動的に失敗として判定されます
2. Amount eaten要素の検出問題は複数のセレクタで対応済みです
3. 結果は新しいファイルに保存され、元ファイルは保持されます

"""
        return instructions


def main():
    """メイン実行関数"""
    print("🔄 MyNetDiary データ状態リセッター開始")
    print("="*80)

    resetter = DataStateReset()

    try:
        # 1. 最適な参照ファイルを見つける
        print("📁 最適な参照ファイルを検索中...")
        reference_file = resetter.find_best_reference_file()
        print(f"✅ 参照ファイル特定: {reference_file.name}")

        # 2. 現在の状態を分析
        print("\n📊 現在の状態を分析中...")
        analysis = resetter.analyze_current_state(reference_file)

        print(f"📈 分析結果:")
        print(f"   総食材数: {analysis['total_foods']}")
        print(f"   元の成功数: {analysis['original_successful']}")
        print(f"   現在の失敗数: {len(analysis['failed_items'])}")
        print(f"   リトライ候補: {len(analysis['needs_retry'])}")
        print(f"   品質修正済み: {'✅' if analysis['quality_corrected'] else '❌'}")

        # 3. Resume用ファイル作成
        print(f"\n🔧 Resume用ファイルを作成中...")
        resume_file = resetter.create_resume_file(reference_file)
        print(f"✅ Resume用ファイル作成: {resume_file.name}")

        # 4. リトライ統計生成
        stats = resetter.generate_retry_statistics(analysis)
        print(f"\n📊 リトライ統計:")
        print(f"   リトライ率: {stats['retry_rate']:.1%}")
        print(f"   失敗カテゴリ数: {len(stats['failed_by_category'])}")

        # 5. 実行手順生成
        instructions = resetter.create_retry_instructions(analysis)

        instructions_file = Path("resume_instructions.md")
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)

        print(f"✅ 実行手順作成: {instructions_file.name}")

        print(f"\n🎯 次のステップ:")
        print(f"   1. {resume_file.name} を使用してresume実行")
        print(f"   2. 品質チェック機能により無効データは自動的に失敗判定")
        print(f"   3. {stats['total_retry_candidates']}件の食材の再収集を試行")
        print(f"   4. 詳細手順: {instructions_file.name} を参照")

        return True

    except Exception as e:
        print(f"❌ リセット処理エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)