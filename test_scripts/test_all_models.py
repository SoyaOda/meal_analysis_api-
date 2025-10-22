#!/usr/bin/env python
"""
test_all_models.py

models_to_test.txtファイルに列挙されたすべてのモデルで
test_vlm_all_images.pyを順番に実行するスクリプト

Usage:
    python test_scripts/test_all_models.py [--models-file FILE] [--skip-existing]

Arguments:
    --models-file FILE  モデルリストファイル (デフォルト: models_to_test.txt)
    --skip-existing     既に結果が存在するモデルはスキップする
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_models_list(models_file_path: Path) -> List[str]:
    """
    モデルリストファイルを読み込む

    Args:
        models_file_path: モデルリストファイルのパス

    Returns:
        モデルIDのリスト
    """
    models = []

    with open(models_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 空行とコメント行をスキップ
            if line and not line.startswith('#'):
                models.append(line)

    return models


def check_existing_result(model_id: str, output_dir: Path) -> bool:
    """
    指定されたモデルの結果が既に存在するか確認

    Args:
        model_id: モデルID
        output_dir: 出力ディレクトリ

    Returns:
        結果が存在する場合はTrue
    """
    model_name_safe = model_id.replace("/", "_").replace(":", "_")
    pattern = f"vlm_test_results_{model_name_safe}_*.json"

    existing_files = list(output_dir.glob(pattern))
    return len(existing_files) > 0


def run_test_for_model(model_id: str, test_script_path: Path, output_dir: Path) -> Dict[str, Any]:
    """
    単一のモデルでテストを実行

    Args:
        model_id: モデルID
        test_script_path: test_vlm_all_images.pyのパス
        output_dir: 出力ディレクトリ

    Returns:
        実行結果の辞書
    """
    result = {
        "model_id": model_id,
        "status": "pending",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "duration_seconds": None,
        "output_file": None,
        "error": None
    }

    try:
        # コマンドを構築
        cmd = [
            sys.executable,  # 現在のPythonインタープリタを使用
            str(test_script_path),
            "--model", model_id
        ]

        # 環境変数を設定
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        # プロセスを実行
        print(f"実行コマンド: {' '.join(cmd)}")

        start_time = datetime.now()
        process = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10分のタイムアウト
        )
        end_time = datetime.now()

        result["end_time"] = end_time.isoformat()
        result["duration_seconds"] = (end_time - start_time).total_seconds()

        if process.returncode == 0:
            result["status"] = "success"

            # 出力ファイルを探す
            model_name_safe = model_id.replace("/", "_").replace(":", "_")
            pattern = f"vlm_test_results_{model_name_safe}_*.json"
            output_files = sorted(output_dir.glob(pattern))

            if output_files:
                result["output_file"] = str(output_files[-1])  # 最新のファイル

            # 標準出力から成功/失敗の統計を抽出
            if "サマリー:" in process.stdout:
                lines = process.stdout.split('\n')
                for i, line in enumerate(lines):
                    if "サマリー:" in line:
                        # 次の数行を取得
                        for j in range(i+1, min(i+5, len(lines))):
                            if "成功:" in lines[j]:
                                result["successful_images"] = lines[j].split("成功:")[1].strip()
                            elif "失敗:" in lines[j]:
                                result["failed_images"] = lines[j].split("失敗:")[1].strip()
        else:
            result["status"] = "failed"
            result["error"] = f"Process exited with code {process.returncode}"
            if process.stderr:
                result["error"] += f"\nStderr: {process.stderr}"

    except subprocess.TimeoutExpired:
        result["status"] = "timeout"
        result["error"] = "Test exceeded 10 minutes timeout"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def print_summary(results: List[Dict[str, Any]]):
    """
    実行結果のサマリーを表示

    Args:
        results: 各モデルの実行結果のリスト
    """
    print("\n" + "="*80)
    print("実行結果サマリー")
    print("="*80)

    total = len(results)
    successful = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    timeout = sum(1 for r in results if r["status"] == "timeout")
    error = sum(1 for r in results if r["status"] == "error")

    print(f"\n総モデル数: {total}")
    print(f"  ✅ 成功: {successful}")
    print(f"  ❌ 失敗: {failed}")
    print(f"  ⏱️  タイムアウト: {timeout}")
    print(f"  🔥 エラー: {error}")

    print("\n詳細:")
    for i, result in enumerate(results, 1):
        status_icon = {
            "success": "✅",
            "failed": "❌",
            "timeout": "⏱️",
            "error": "🔥"
        }.get(result["status"], "❓")

        print(f"\n{i}. {result['model_id']}")
        print(f"   ステータス: {status_icon} {result['status']}")

        if result["duration_seconds"]:
            print(f"   実行時間: {result['duration_seconds']:.1f}秒")

        if result["status"] == "success":
            if "successful_images" in result:
                print(f"   画像結果: {result.get('successful_images', 'N/A')}")
            if result["output_file"]:
                print(f"   出力ファイル: {Path(result['output_file']).name}")
        elif result["error"]:
            error_lines = result["error"].split('\n')
            print(f"   エラー: {error_lines[0]}")
            if len(error_lines) > 1:
                print(f"           {error_lines[1][:60]}...")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="models_to_test.txtに列挙されたすべてのモデルでVLMテストを実行"
    )
    parser.add_argument(
        "--models-file",
        type=str,
        default="models_to_test.txt",
        help="モデルリストファイル (デフォルト: models_to_test.txt)"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="既に結果が存在するモデルはスキップする"
    )

    args = parser.parse_args()

    print("="*80)
    print("複数モデルVLMテスト実行スクリプト")
    print("="*80)
    print()

    # パスを設定
    test_scripts_dir = project_root / "test_scripts"
    models_file_path = test_scripts_dir / args.models_file
    test_script_path = test_scripts_dir / "test_vlm_all_images.py"
    output_dir = test_scripts_dir / "output"

    # ファイルの存在確認
    if not models_file_path.exists():
        print(f"❌ エラー: {models_file_path} が存在しません")
        sys.exit(1)

    if not test_script_path.exists():
        print(f"❌ エラー: {test_script_path} が存在しません")
        sys.exit(1)

    # モデルリストを読み込み
    print(f"モデルリストを読み込み中: {models_file_path}")
    models = load_models_list(models_file_path)

    if not models:
        print("⚠️  警告: 有効なモデルが見つかりませんでした")
        sys.exit(0)

    print(f"検出されたモデル数: {len(models)}")
    for i, model_id in enumerate(models, 1):
        print(f"  {i}. {model_id}")

    print()

    # 出力ディレクトリを作成
    output_dir.mkdir(exist_ok=True)

    # 各モデルでテストを実行
    results = []

    for i, model_id in enumerate(models, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{len(models)}] モデル: {model_id}")
        print(f"{'='*80}")

        # 既存結果のチェック
        if args.skip_existing and check_existing_result(model_id, output_dir):
            print(f"⏭️  スキップ: 既に結果が存在します")
            results.append({
                "model_id": model_id,
                "status": "skipped",
                "error": "Already has result"
            })
            continue

        print(f"テストを開始します...")
        result = run_test_for_model(model_id, test_script_path, output_dir)
        results.append(result)

        if result["status"] == "success":
            print(f"✅ 成功 (実行時間: {result['duration_seconds']:.1f}秒)")
        else:
            print(f"❌ {result['status']}: {result.get('error', 'Unknown error')}")

    # サマリーを表示
    print_summary(results)

    # 結果をJSONファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = output_dir / f"all_models_test_summary_{timestamp}.json"

    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "models_file": args.models_file,
                "total_models": len(models),
                "skip_existing": args.skip_existing
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📄 サマリーファイル: {summary_file}")
    print("\n✨ すべてのテストが完了しました!")


if __name__ == "__main__":
    main()