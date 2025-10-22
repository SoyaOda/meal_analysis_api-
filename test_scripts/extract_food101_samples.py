#!/usr/bin/env python
"""
extract_food101_samples.py

Food-101データセットの各カテゴリからランダムに1枚の画像を抽出し、
test_images/food101/フォルダに保存するスクリプト

Usage:
    python test_scripts/extract_food101_samples.py
"""

import os
import random
import shutil
from pathlib import Path
from typing import List

# プロジェクトルート
project_root = Path(__file__).parent.parent

# Food-101データセットのパス
FOOD101_TRAIN_DIR = project_root / "dataset" / "food-101" / "train"

# 出力先ディレクトリ
OUTPUT_DIR = project_root / "test_scripts" / "test_images" / "food101"


def get_all_categories(train_dir: Path) -> List[str]:
    """
    訓練データディレクトリから全カテゴリを取得

    Args:
        train_dir: 訓練データディレクトリ

    Returns:
        カテゴリ名のリスト
    """
    categories = []

    if not train_dir.exists():
        print(f"❌ エラー: {train_dir} が存在しません")
        return categories

    for item in sorted(train_dir.iterdir()):
        if item.is_dir():
            categories.append(item.name)

    return categories


def extract_random_image(category: str, train_dir: Path, output_dir: Path) -> bool:
    """
    指定されたカテゴリからランダムに1枚の画像を抽出して保存

    Args:
        category: カテゴリ名
        train_dir: 訓練データディレクトリ
        output_dir: 出力先ディレクトリ

    Returns:
        成功したらTrue
    """
    category_dir = train_dir / category

    # カテゴリディレクトリ内の画像ファイルを取得
    image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    images = [
        f for f in category_dir.iterdir()
        if f.is_file() and f.suffix in image_extensions
    ]

    if not images:
        print(f"⚠️  警告: {category} に画像が見つかりませんでした")
        return False

    # ランダムに1枚選択
    selected_image = random.choice(images)

    # 出力ファイル名（カテゴリ名 + 元の拡張子）
    output_file = output_dir / f"{category}{selected_image.suffix}"

    # 画像をコピー
    try:
        shutil.copy2(selected_image, output_file)
        print(f"✅ {category:40s} -> {output_file.name}")
        return True
    except Exception as e:
        print(f"❌ エラー: {category} のコピーに失敗: {e}")
        return False


def main():
    """メイン処理"""
    print("="*80)
    print("Food-101 画像サンプル抽出スクリプト")
    print("="*80)
    print()

    # 訓練データディレクトリの確認
    if not FOOD101_TRAIN_DIR.exists():
        print(f"❌ エラー: Food-101訓練データが見つかりません: {FOOD101_TRAIN_DIR}")
        print()
        print("次のコマンドでFood-101データセットをダウンロードしてください：")
        print("  # Kaggleからダウンロード")
        print("  kaggle datasets download -d kmader/food41")
        print("  # または公式サイトから")
        print("  wget http://data.vision.ee.ethz.ch/cvl/food-101.tar.gz")
        return

    print(f"訓練データディレクトリ: {FOOD101_TRAIN_DIR}")

    # 出力ディレクトリの作成
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"出力先ディレクトリ: {OUTPUT_DIR}")
    print()

    # 全カテゴリを取得
    categories = get_all_categories(FOOD101_TRAIN_DIR)

    if not categories:
        print("❌ カテゴリが見つかりませんでした")
        return

    print(f"カテゴリ数: {len(categories)}")
    print()

    # ランダムシードを固定（再現性のため）
    random.seed(42)

    # 各カテゴリから画像を抽出
    success_count = 0
    failed_count = 0

    print("画像抽出中...")
    print("-"*80)

    for category in categories:
        if extract_random_image(category, FOOD101_TRAIN_DIR, OUTPUT_DIR):
            success_count += 1
        else:
            failed_count += 1

    # サマリーを表示
    print("-"*80)
    print()
    print(f"✅ 抽出完了!")
    print(f"  成功: {success_count} 件")
    print(f"  失敗: {failed_count} 件")
    print(f"  合計: {success_count + failed_count} 件")
    print()
    print(f"📁 画像の保存先: {OUTPUT_DIR}")
    print()

    # 抽出された画像のリストを表示（最初の10件）
    extracted_images = sorted(OUTPUT_DIR.glob("*.*"))
    if extracted_images:
        print(f"抽出された画像の例（最初の10件）:")
        for img in extracted_images[:10]:
            file_size = img.stat().st_size / 1024  # KB
            print(f"  - {img.name:50s} ({file_size:7.1f} KB)")

        if len(extracted_images) > 10:
            print(f"  ... 他 {len(extracted_images) - 10} 件")


if __name__ == "__main__":
    main()
