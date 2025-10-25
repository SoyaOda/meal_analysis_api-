#!/usr/bin/env python
"""
generate_freeform_prompt.py

Freeformプロンプト（食品リスト不要版）を生成するスクリプト
prompt_base/freeform_prompt.txt を読み込んで output/ に保存します

Usage:
    python test_scripts/generate_freeform_prompt.py
"""

import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_vlm_prompt() -> str:
    """
    VLMに送信する自由生成版プロンプトを生成（食品リスト不要）
    prompt_base/freeform_prompt.txt から読み込みます

    Returns:
        str: 完全なプロンプト
    """
    # prompt_base/freeform_prompt.txtを読み込み
    prompt_base_path = project_root / "test_scripts" / "prompt_base" / "freeform_prompt.txt"

    if not prompt_base_path.exists():
        raise FileNotFoundError(f"プロンプトベースファイルが見つかりません: {prompt_base_path}")

    with open(prompt_base_path, 'r', encoding='utf-8') as f:
        prompt = f.read()

    return prompt


def main():
    """メイン処理"""
    print("="*80)
    print("自由生成版プロンプト生成スクリプト")
    print("="*80)
    print()

    # プロンプトベースファイルパス
    prompt_base_path = project_root / "test_scripts" / "prompt_base" / "freeform_prompt.txt"
    print(f"プロンプトベースファイル: {prompt_base_path}")

    # プロンプトを生成（prompt_base/から読み込み）
    print("プロンプトを生成中...")
    try:
        prompt = generate_vlm_prompt()
    except FileNotFoundError as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)

    # プロンプトの文字数を計算
    prompt_length = len(prompt)
    prompt_lines = prompt.count('\n') + 1

    print(f"✅ プロンプト生成完了: {prompt_length:,} 文字")
    print()

    # 出力ファイルパス
    output_file = project_root / "test_scripts/output/freeform_prompt.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # ファイルに保存
    print(f"プロンプトを保存中: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f"✅ 保存完了!")
    print()

    print("="*80)
    print(f"自由生成版プロンプト: {output_file}")
    print(f"文字数: {prompt_length:,}")
    print(f"行数: {prompt_lines}")
    print("="*80)


if __name__ == "__main__":
    main()
