#!/usr/bin/env python
"""
split_all_labels.py

すべてのlabel_*.jsonファイルを個別の画像ラベルファイルに分割するスクリプト

Usage:
    python test_scripts/split_all_labels.py
"""

import sys
import json
from pathlib import Path
import re

# プロジェクトルート
project_root = Path(__file__).parent.parent


def parse_range_from_filename(filename: str):
    """
    ファイル名から範囲を抽出

    例: "label_11_20.json" -> (11, 20)
    """
    match = re.search(r'label_(\d+)_(\d+)\.json', filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def split_label_file(input_file: Path, start_idx: int):
    """
    label_*.jsonファイルを個別ファイルに分割

    Args:
        input_file: 入力ファイルのパス
        start_idx: 開始インデックス（例: label_11_20.json なら 11）
    """
    # 出力ディレクトリ
    output_dir = input_file.parent

    print(f"処理中: {input_file.name}")

    # ファイルを読み込み
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # JSONオブジェクトを分割（改行で区切られている）
    json_objects = []
    current_json = ""
    brace_count = 0

    for line in content.split('\n'):
        if not line.strip():
            continue

        current_json += line + '\n'

        # 中括弧のカウント
        for char in line:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1

        # 完全なJSONオブジェクトが完成した
        if brace_count == 0 and current_json.strip():
            try:
                obj = json.loads(current_json)
                json_objects.append(obj)
                current_json = ""
            except json.JSONDecodeError as e:
                print(f"  ⚠️  JSON解析エラー: {e}")
                current_json = ""

    print(f"  検出: {len(json_objects)}個のJSONオブジェクト")

    # 各JSONオブジェクトを個別ファイルに保存
    saved_count = 0
    for idx, obj in enumerate(json_objects):
        file_idx = start_idx + idx
        output_file = output_dir / f"test_food{file_idx}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

        # 料理数を取得
        dishes_count = len(obj.get('dishes', []))
        print(f"    {file_idx}. {output_file.name} -> {dishes_count}個の料理")
        saved_count += 1

    return saved_count


def main():
    """メイン処理"""
    print("=" * 80)
    print("すべてのlabel_*.jsonファイルを分割")
    print("=" * 80)
    print()

    # ラベルディレクトリ
    label_dir = project_root / "test_images" / "images_label"

    if not label_dir.exists():
        print(f"❌ エラー: {label_dir} が存在しません")
        sys.exit(1)

    # すべてのlabel_*.jsonファイルを取得
    label_files = sorted(label_dir.glob("label_*.json"))

    if not label_files:
        print(f"⚠️  警告: {label_dir} に label_*.json ファイルが見つかりませんでした")
        sys.exit(0)

    print(f"検出されたラベルファイル: {len(label_files)}件")
    for f in label_files:
        start, end = parse_range_from_filename(f.name)
        if start and end:
            print(f"  - {f.name} (test_food{start} ~ test_food{end})")
        else:
            print(f"  - {f.name}")
    print()

    # 各ファイルを処理
    total_saved = 0
    for label_file in label_files:
        start_idx, _ = parse_range_from_filename(label_file.name)

        if start_idx is None:
            print(f"⚠️  スキップ: {label_file.name} (範囲を抽出できませんでした)")
            continue

        saved = split_label_file(label_file, start_idx)
        total_saved += saved
        print()

    print("=" * 80)
    print(f"✅ 完了: 合計 {total_saved}個のファイルを生成")
    print(f"   出力先: {label_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
