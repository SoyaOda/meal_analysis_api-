#!/usr/bin/env python3
"""
create_ai_review_document.py

VLMテスト結果を外部AIレビュー用のフォーマットに整形して出力するスクリプト

Usage:
    python test_scripts/create_ai_review_document.py
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# プロンプト生成関数をインポート
sys.path.insert(0, str(Path(__file__).parent))
from generate_complete_prompt import generate_vlm_prompt


def load_json_results(output_dir: Path) -> Dict[str, Any]:
    """
    outputディレクトリからVLMテスト結果のJSONファイルを読み込む

    Args:
        output_dir: 出力ディレクトリのパス

    Returns:
        モデル名をキー、結果を値とする辞書
    """
    results = {}

    # vlm_test_results_*.jsonファイルを検索
    json_files = list(output_dir.glob("vlm_test_results_*.json"))

    for json_file in json_files:
        print(f"読み込み中: {json_file.name}")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # ファイル名からモデル名を抽出
        # vlm_test_results_[モデル名]_[タイムスタンプ].json
        filename_parts = json_file.stem.split('_')
        # vlm_test_results_ を除いて、最後のタイムスタンプも除く
        model_name = '_'.join(filename_parts[3:-1]) if len(filename_parts) > 4 else filename_parts[3]

        # メタデータからモデルIDを取得（より正確）
        if 'test_metadata' in data and 'model_id' in data['test_metadata']:
            model_name = data['test_metadata']['model_id']

        results[model_name] = data

    return results


def format_image_results(results: Dict[str, Any]) -> str:
    """
    各画像の結果をフォーマット

    Args:
        results: VLMテスト結果

    Returns:
        フォーマットされた文字列
    """
    formatted_results = []

    # モデルごとに結果を整理
    for model_name, data in results.items():
        formatted_results.append(f"\n### モデル: {model_name}\n")

        if 'test_metadata' in data:
            metadata = data['test_metadata']
            formatted_results.append(f"- テスト日時: {metadata.get('timestamp', 'N/A')}")
            formatted_results.append(f"- 成功: {metadata.get('successful', 0)}/{metadata.get('total_images', 0)}画像")
            formatted_results.append(f"- 失敗: {metadata.get('failed', 0)}画像\n")

        # 各画像の結果
        if 'results' in data:
            for idx, image_result in enumerate(data['results'], 1):
                formatted_results.append(f"\n#### 画像{idx}: {image_result.get('image_file', 'N/A')}")

                if image_result.get('success', False):
                    formatted_results.append("- ステータス: ✅ 成功")

                    if 'vlm_response' in image_result and image_result['vlm_response']:
                        formatted_results.append("- VLMレスポンス:")
                        formatted_results.append("```json")
                        formatted_results.append(json.dumps(image_result['vlm_response'],
                                                           indent=2,
                                                           ensure_ascii=False))
                        formatted_results.append("```")
                else:
                    formatted_results.append("- ステータス: ❌ 失敗")
                    if 'error' in image_result:
                        formatted_results.append(f"- エラー: {image_result['error']}")

    return '\n'.join(formatted_results)


def create_review_document(prompt: str, results: Dict[str, Any]) -> str:
    """
    外部AIレビュー用のドキュメントを作成

    Args:
        prompt: VLMプロンプト
        results: VLMテスト結果

    Returns:
        レビュー用ドキュメント
    """
    document = []

    # ヘッダー
    document.append("# VLM食品認識テスト結果レビュー依頼")
    document.append(f"\n生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
    document.append("=" * 80)

    # 概要
    document.append("\n## 概要\n")
    document.append("現状下記の様なプロンプトで添付の5つの画像を3つのVLMで分析したのでそのresultを示す。")
    document.append("徹底レビューして、食品名リストの絞り込み、プロンプト、VLMモデルどの部分をどう修正すると良いと思う？\n")

    # プロンプトセクション
    document.append("=" * 80)
    document.append("\n## [プロンプト]\n")
    document.append("```")
    document.append(prompt)
    document.append("```\n")

    # 結果セクション
    document.append("=" * 80)
    document.append("\n## [Results]\n")

    # テストした画像の情報
    test_images = set()
    for model_name, data in results.items():
        if 'results' in data:
            for image_result in data['results']:
                test_images.add(image_result.get('image_file', 'Unknown'))

    document.append(f"### テスト画像: {len(test_images)}枚")
    for img in sorted(test_images):
        document.append(f"- {img}")

    document.append(f"\n### テストモデル: {len(results)}種類")
    for model in results.keys():
        document.append(f"- {model}")

    # 詳細結果
    document.append("\n" + "=" * 80)
    document.append("\n## 詳細結果")
    document.append(format_image_results(results))

    # レビュー依頼
    document.append("\n" + "=" * 80)
    document.append("\n## レビュー観点\n")
    document.append("以下の観点でレビューをお願いします：\n")
    document.append("1. **食品名リストの最適化**")
    document.append("   - 不要な重複項目の特定")
    document.append("   - 誤認を招く類似項目の統合提案")
    document.append("   - 追加すべき重要な食品名\n")

    document.append("2. **プロンプトの改善**")
    document.append("   - 曖昧な指示の明確化")
    document.append("   - ルールの優先順位の調整")
    document.append("   - エラーを減らすための追加ルール")
    document.append("   - 具体例でなく、より本質的・一般的な指示への修正（過学習的になあらない様にするため）\n")

    document.append("3. **VLMモデルの評価**")
    document.append("   - 各モデルの強み・弱みの分析")
    document.append("   - 最適なモデルの推奨")
    document.append("   - モデル固有の問題点\n")

    document.append("4. **共通エラーパターン**")
    document.append("   - 頻繁に発生する誤認識")
    document.append("   - weight推定の精度問題")
    document.append("   - analysis_methodの選択ミス\n")

    return '\n'.join(document)


def main():
    """メイン処理"""
    print("=" * 80)
    print("外部AIレビュー用ドキュメント生成")
    print("=" * 80)
    print()

    # 1. プロンプトを生成
    print("1. プロンプトを生成中...")
    food_names_list_path = project_root / "test_scripts" / "food_names_list" / "food_names_list.txt"

    if not food_names_list_path.exists():
        print(f"❌ エラー: {food_names_list_path} が存在しません")
        sys.exit(1)

    with open(food_names_list_path, 'r', encoding='utf-8') as f:
        food_names_list = f.read()

    prompt = generate_vlm_prompt(food_names_list)
    print(f"   ✅ プロンプト生成完了: {len(prompt):,}文字")

    # 2. VLMテスト結果を読み込み
    print("\n2. VLMテスト結果を読み込み中...")
    output_dir = project_root / "test_scripts" / "output"

    if not output_dir.exists():
        print(f"❌ エラー: {output_dir} が存在しません")
        sys.exit(1)

    results = load_json_results(output_dir)
    print(f"   ✅ {len(results)}個のモデル結果を読み込みました")

    if not results:
        print("⚠️  警告: VLMテスト結果が見つかりませんでした")
        print("   test_vlm_all_images.pyを先に実行してください")
        sys.exit(1)

    # 3. レビュードキュメントを作成
    print("\n3. レビュードキュメントを作成中...")
    document = create_review_document(prompt, results)
    print(f"   ✅ ドキュメント生成完了: {len(document):,}文字")

    # 4. ファイルに保存
    print("\n4. ファイルに保存中...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"ai_review_document_{timestamp}.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(document)

    print(f"   ✅ 保存完了: {output_file}")

    # 5. テキストファイルも生成（コピペ用）
    txt_output_file = output_dir / f"ai_review_document_{timestamp}.txt"
    with open(txt_output_file, 'w', encoding='utf-8') as f:
        f.write(document)

    print(f"   ✅ テキスト版も保存: {txt_output_file}")

    print("\n" + "=" * 80)
    print("✨ 外部AIレビュー用ドキュメントの生成が完了しました！")
    print("=" * 80)
    print()
    print("次のステップ:")
    print(f"1. {output_file} を開く")
    print("2. 内容をコピーして外部AIに貼り付ける")
    print("3. フィードバックを受け取る")
    print("4. 改善案を実装する")
    print()


if __name__ == "__main__":
    main()