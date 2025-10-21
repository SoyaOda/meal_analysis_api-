#!/usr/bin/env python3
"""
extract_food_names.py

USDAデータベースのJSONファイルから食品名を抽出して、
テキストファイルとして保存するスクリプト

Usage:
    python usda_database/scripts/extract_food_names.py
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import ijson  # ストリーミングJSON処理用

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 入力ファイルと出力ファイルのマッピング
FILE_MAPPINGS = {
    "FoodData_Central_branded_food_json_2025-04-24 2.json": {
        "output": "branded_food_names.txt",
        "json_key": "BrandedFoods",
        "description_key": "description",
        "use_streaming": True  # 大きいファイルなのでストリーミング処理
    },
    "FoodData_Central_foundation_food_json_2025-04-24 2.json": {
        "output": "foundation_food_names.txt",
        "json_key": "FoundationFoods",
        "description_key": "description",
        "use_streaming": False
    },
    "FoodData_Central_sr_legacy_food_json_2018-04 2.json": {
        "output": "sr_legacy_food_names.txt",
        "json_key": "SRLegacyFoods",
        "description_key": "description",
        "use_streaming": True  # 大きいファイルなのでストリーミング処理
    },
    "surveyDownload.json": {
        "output": "survey_food_names.txt",
        "json_key": "SurveyFoods",
        "description_key": "description",
        "use_streaming": True
    }
}


def extract_names_streaming(
    json_file: Path,
    json_key: str,
    description_key: str
) -> List[str]:
    """
    ストリーミング方式でJSONファイルから食品名を抽出

    Args:
        json_file: JSONファイルのパス
        json_key: データ配列のキー
        description_key: 食品名のキー

    Returns:
        食品名のリスト
    """
    food_names = []

    print(f"  ストリーミング処理で読み込み中...")

    try:
        with open(json_file, 'rb') as f:
            # ijsonを使用してストリーミング処理
            # 例: "BrandedFoods.item.description" という形式で各要素を読み込む
            prefix = f"{json_key}.item"
            parser = ijson.items(f, prefix)

            count = 0
            for item in parser:
                if isinstance(item, dict) and description_key in item:
                    description = item[description_key]
                    if description and isinstance(description, str):
                        food_names.append(description.strip())
                        count += 1

                        # 進捗表示（10000件ごと）
                        if count % 10000 == 0:
                            print(f"    処理済み: {count:,} 件")

            print(f"    最終件数: {count:,} 件")

    except Exception as e:
        print(f"  ⚠️  ストリーミング処理エラー: {e}")
        # ストリーミング失敗時は通常読み込みにフォールバック
        print(f"  通常読み込みにフォールバック...")
        return extract_names_normal(json_file, json_key, description_key)

    return food_names


def extract_names_normal(
    json_file: Path,
    json_key: str,
    description_key: str
) -> List[str]:
    """
    通常方式でJSONファイルから食品名を抽出

    Args:
        json_file: JSONファイルのパス
        json_key: データ配列のキー
        description_key: 食品名のキー

    Returns:
        食品名のリスト
    """
    food_names = []

    print(f"  通常読み込み中...")

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if json_key not in data:
            print(f"  ⚠️  警告: キー '{json_key}' が見つかりません")
            # キーが見つからない場合、ルート直下の配列をチェック
            if isinstance(data, list):
                print(f"  ルート配列として処理します")
                items = data
            else:
                return food_names
        else:
            items = data[json_key]

        if not isinstance(items, list):
            print(f"  ⚠️  警告: '{json_key}' は配列ではありません")
            return food_names

        for item in items:
            if isinstance(item, dict) and description_key in item:
                description = item[description_key]
                if description and isinstance(description, str):
                    food_names.append(description.strip())

        print(f"    件数: {len(food_names):,} 件")

    except Exception as e:
        print(f"  ❌ エラー: {e}")

    return food_names


def process_file(
    input_file: str,
    config: Dict[str, Any],
    input_dir: Path,
    output_dir: Path
) -> bool:
    """
    単一のJSONファイルを処理

    Args:
        input_file: 入力ファイル名
        config: 設定辞書
        input_dir: 入力ディレクトリ
        output_dir: 出力ディレクトリ

    Returns:
        成功したらTrue
    """
    json_file = input_dir / input_file
    output_file = output_dir / config["output"]

    print(f"\n{'='*80}")
    print(f"処理中: {input_file}")
    print(f"{'='*80}")

    if not json_file.exists():
        print(f"❌ ファイルが存在しません: {json_file}")
        return False

    # ファイルサイズを表示
    file_size_mb = json_file.stat().st_size / (1024 * 1024)
    print(f"ファイルサイズ: {file_size_mb:.1f} MB")

    # 食品名を抽出
    if config.get("use_streaming", False):
        food_names = extract_names_streaming(
            json_file,
            config["json_key"],
            config["description_key"]
        )
    else:
        food_names = extract_names_normal(
            json_file,
            config["json_key"],
            config["description_key"]
        )

    if not food_names:
        print(f"⚠️  警告: 食品名が抽出されませんでした")
        return False

    # 重複を削除してソート
    unique_names = sorted(set(food_names))
    print(f"\n重複削除前: {len(food_names):,} 件")
    print(f"重複削除後: {len(unique_names):,} 件")

    # テキストファイルに保存
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for name in unique_names:
                f.write(f"{name}\n")

        print(f"\n✅ 保存完了: {output_file}")
        print(f"   総件数: {len(unique_names):,} 件")

        # 最初の10件を表示
        print(f"\n   最初の10件:")
        for i, name in enumerate(unique_names[:10], 1):
            print(f"     {i}. {name}")

        return True

    except Exception as e:
        print(f"❌ 保存エラー: {e}")
        return False


def main():
    """メイン処理"""
    print("="*80)
    print("USDA食品名抽出スクリプト")
    print("="*80)
    print()

    # ディレクトリのパス
    input_dir = PROJECT_ROOT / "usda_database"
    output_dir = PROJECT_ROOT / "usda_database" / "names_list"

    # 出力ディレクトリの作成
    output_dir.mkdir(exist_ok=True)

    print(f"入力ディレクトリ: {input_dir}")
    print(f"出力ディレクトリ: {output_dir}")

    # 各ファイルを処理
    results = {}

    for input_file, config in FILE_MAPPINGS.items():
        success = process_file(input_file, config, input_dir, output_dir)
        results[input_file] = success

    # サマリーを表示
    print(f"\n{'='*80}")
    print("処理結果サマリー")
    print(f"{'='*80}\n")

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"総ファイル数: {total_count}")
    print(f"成功: {success_count}")
    print(f"失敗: {total_count - success_count}")
    print()

    for file_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {status}: {file_name}")

    print(f"\n{'='*80}")
    print(f"出力先: {output_dir}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # ijsonがインストールされているか確認
    try:
        import ijson
    except ImportError:
        print("⚠️  警告: ijsonがインストールされていません")
        print("大きなファイルの処理にはijsonのインストールを推奨します:")
        print("  pip install ijson")
        print()
        print("通常読み込みで続行します...")
        print()

        # ijsonなしでも動作するように、すべてのファイルで通常読み込みを使用
        for config in FILE_MAPPINGS.values():
            config["use_streaming"] = False

    main()
