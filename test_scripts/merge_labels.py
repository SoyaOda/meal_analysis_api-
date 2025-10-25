#!/usr/bin/env python3
"""
画像ラベルファイルを1つにまとめるスクリプト
test_images/images_label内の全JSONファイルをファイル名込みで統合
"""
import json
from pathlib import Path
from datetime import datetime

LABEL_DIR = Path("/Users/odasoya/meal_analysis_api_2/test_images/images_label")

def merge_labels():
    """全ラベルファイルを1つにまとめる"""
    print("📁 ラベルファイルを読み込み中...")

    # test_food*.jsonファイルを取得してソート
    label_files = sorted(LABEL_DIR.glob("test_food*.json"))

    if not label_files:
        print("❌ ラベルファイルが見つかりません")
        return

    print(f"✅ {len(label_files)}個のファイルを発見")

    # 統合データを作成
    merged_data = {
        "created_at": datetime.now().isoformat(),
        "total_images": len(label_files),
        "labels": []
    }

    # 各ラベルファイルを読み込み
    for label_file in label_files:
        image_num = label_file.stem.replace("test_food", "")
        image_filename = f"test_food{image_num}.jpg"

        with open(label_file, 'r', encoding='utf-8') as f:
            label_data = json.load(f)

        # ファイル名を含めて統合
        entry = {
            "image_file": image_filename,
            "image_number": int(image_num),
            "label": label_data
        }

        merged_data["labels"].append(entry)
        print(f"  - {image_filename}: {len(label_data.get('dishes', []))}品")

    # 保存
    output_file = LABEL_DIR / "all_labels.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)

    print()
    print(f"✅ 統合完了: {output_file}")
    print(f"📊 総画像数: {len(label_files)}")

    # 総料理数を計算
    total_dishes = sum(len(entry["label"].get("dishes", [])) for entry in merged_data["labels"])
    print(f"📊 総料理数: {total_dishes}")

def main():
    print("="*80)
    print("🤖 ラベルファイル統合スクリプト")
    print("="*80)
    print()

    merge_labels()

    print()
    print("="*80)
    print("✅ 完了")
    print("="*80)

if __name__ == "__main__":
    main()
