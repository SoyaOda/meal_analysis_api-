#!/usr/bin/env python
"""
split_labels.py

label_1_10.jsonを個別の画像ラベルファイルに分割するスクリプト

Usage:
    python test_scripts/split_labels.py
"""

import sys
import json
from pathlib import Path

# プロジェクトルート
project_root = Path(__file__).parent.parent


def split_label_file():
    """label_1_10.jsonを個別ファイルに分割"""

    # 入力ファイル
    input_file = project_root / "test_images" / "images_label" / "label_1_10.json"

    # 出力ディレクトリ
    output_dir = project_root / "test_images" / "images_label"
    output_dir.mkdir(exist_ok=True, parents=True)

    print(f"入力ファイル: {input_file}")
    print(f"出力ディレクトリ: {output_dir}")
    print()

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
                print(f"⚠️  JSON解析エラー: {e}")
                current_json = ""

    print(f"✅ {len(json_objects)}個のJSONオブジェクトを検出")
    print()

    # 各JSONオブジェクトを個別ファイルに保存
    for idx, obj in enumerate(json_objects, start=1):
        output_file = output_dir / f"test_food{idx}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

        # 料理数を取得
        dishes_count = len(obj.get('dishes', []))

        print(f"  {idx}. {output_file.name} -> {dishes_count}個の料理")

    print()
    print("=" * 80)
    print(f"✅ 完了: {len(json_objects)}個のファイルを生成")
    print(f"   出力先: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    split_label_file()
