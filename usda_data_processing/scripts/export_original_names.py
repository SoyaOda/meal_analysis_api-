#!/usr/bin/env python
"""
surveyDownload.jsonから食品名を元データの順番で抽出してMDファイルに保存

出力:
1. usda_composite_dishes_original.md - 複合料理（inputFoods >= 2）
2. usda_single_ingredients_original.md - 単一食材（inputFoods == 1）
"""

import json
from pathlib import Path
from datetime import datetime


def load_survey_data(file_path: str) -> list:
    """surveyDownload.jsonを読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('SurveyFoods', [])


def export_to_markdown(foods: list, output_path: str, title: str, description: str, start_number: int = 1) -> int:
    """
    食品リストをMarkdownファイルに出力

    Args:
        foods: 食品リスト
        output_path: 出力ファイルパス
        title: ファイルのタイトル
        description: 説明文
        start_number: 開始番号（デフォルト: 1）

    Returns:
        最後に使用した番号
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # ヘッダー
        f.write(f"# {title}\n\n")
        f.write(f"> {description}\n\n")
        f.write(f"**Source**: `usda_database/surveyDownload.json`  \n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Total Items**: {len(foods)}\n\n")
        if start_number > 1:
            f.write(f"**Number Range**: {start_number} - {start_number + len(foods) - 1}\n\n")
        f.write("---\n\n")

        # 食品リスト
        for i, food in enumerate(foods, start_number):
            food_description = food.get('description', 'Unknown')
            f.write(f"{i}. {food_description}\n")

    return start_number + len(foods) - 1


def main():
    """メイン実行"""
    # パス設定
    base_dir = Path("/Users/odasoya/meal_analysis_api_2")
    survey_json_path = base_dir / "usda_database" / "surveyDownload.json"
    output_dir = base_dir / "usda_data_processing" / "display_name_generation"

    # 出力ファイルパス
    composite_output = output_dir / "original_name.txt"
    single_output = output_dir / "original_name_single_ingredients.txt"

    print("📂 surveyDownload.json読み込み中...")
    foods = load_survey_data(str(survey_json_path))
    print(f"✅ 総食品数: {len(foods)}件\n")

    # 食品を分類（元データの順番を保持）
    composite_dishes = []
    single_ingredients = []

    for food in foods:
        input_foods = food.get('inputFoods', [])
        input_count = len(input_foods)

        if input_count >= 2:
            composite_dishes.append(food)
        elif input_count == 1:
            single_ingredients.append(food)
        # input_count == 0 は除外（Human milk）

    print(f"📊 分類結果:")
    print(f"   - 単一食材（inputFoods == 1）: {len(single_ingredients)}件")
    print(f"   - 複合料理（inputFoods >= 2）: {len(composite_dishes)}件")
    print(f"   - 除外（inputFoods == 0）: {len(foods) - len(composite_dishes) - len(single_ingredients)}件\n")

    # 単一食材の出力（番号1から開始）
    print("📝 単一食材リスト生成中...")
    last_number = export_to_markdown(
        single_ingredients,
        str(single_output),
        "USDA FNDDS - Single Ingredients (Original Names)",
        "単一食材（調理済み + 基本食材）の元データ名リスト（元データの順番を保持）",
        start_number=1
    )
    print(f"✅ 生成完了: {single_output}")
    print(f"   - ファイルサイズ: {single_output.stat().st_size / 1024:.1f} KB")
    print(f"   - 番号範囲: 1 - {last_number}\n")

    # 複合料理の出力（単一食材の続きから開始）
    print(f"📝 複合料理リスト生成中（番号{last_number + 1}から開始）...")
    final_number = export_to_markdown(
        composite_dishes,
        str(composite_output),
        "USDA FNDDS - Composite Dishes (Original Names)",
        "複合料理の元データ名リスト（元データの順番を保持）",
        start_number=last_number + 1
    )
    print(f"✅ 生成完了: {composite_output}")
    print(f"   - ファイルサイズ: {composite_output.stat().st_size / 1024:.1f} KB")
    print(f"   - 番号範囲: {last_number + 1} - {final_number}\n")

    print("=" * 80)
    print("✨ 処理完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
