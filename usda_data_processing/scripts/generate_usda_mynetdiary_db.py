#!/usr/bin/env python3
"""
USDAデータをMyNetDiary互換フォーマットに変換して統合DBを生成

入力:
  - usda_raw_ingredients_search_patterns.json
  - usda_prepared_ingredients_search_patterns.json

出力:
  - usda_data_processing/db/usda_unified_db.json
"""

import json
import time
import re
import nltk
from pathlib import Path
from nltk.stem import PorterStemmer
from typing import Dict, List, Any

# NLTKデータのダウンロード（初回のみ）
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("📥 NLTKデータをダウンロード中...")
    nltk.download('punkt')

# 必要な栄養素IDのマッピング
NUTRIENT_ID_MAPPING = {
    1008: "calorie",       # Energy (kcal)
    1003: "Protein_g",     # Protein (g)
    1004: "Total_Fat_g",   # Total lipid (fat) (g)
    1005: "Total_Carbs_g"  # Carbohydrate, by difference (g)
}


def setup_stemmer():
    """PorterStemmerの初期化"""
    return PorterStemmer()


def clean_and_tokenize_single(text: str) -> List[str]:
    """
    単一テキストのクリーニングとトークン化
    （既存のadd_stemmed_fields.pyから引用）
    """
    if not text:
        return []

    if not isinstance(text, str):
        text = str(text)

    # 小文字に変換
    text = text.lower()

    # 特殊文字を除去（アルファベットとスペースのみ残す）
    text = re.sub(r'[^a-z\s]', ' ', text)

    # 複数のスペースを単一スペースに
    text = re.sub(r'\s+', ' ', text).strip()

    # トークン化
    tokens = text.split()

    return tokens


def stem_single_text(text: str, stemmer: PorterStemmer) -> str:
    """
    単一テキストの語幹化
    （既存のadd_stemmed_fields.pyから引用）
    """
    if not text:
        return ""

    tokens = clean_and_tokenize_single(text)
    stemmed_tokens = [stemmer.stem(token) for token in tokens]

    return ' '.join(stemmed_tokens)


def stem_text_or_list(text, stemmer: PorterStemmer):
    """
    テキストまたはリストの語幹化（型を保持）
    （既存のadd_stemmed_fields.pyから引用）
    """
    if not text:
        return text

    # リスト形式の場合: 各要素を個別に語幹化してリストを返す
    if isinstance(text, list):
        if len(text) == 0:
            return []
        return [stem_single_text(item, stemmer) for item in text]

    # 文字列の場合: 語幹化した文字列を返す
    else:
        return stem_single_text(text, stemmer)


def add_stemmed_fields(item: Dict, stemmer: PorterStemmer) -> Dict:
    """
    search_nameとdescriptionをStemming処理
    """
    return {
        "stemmed_search_name": stem_text_or_list(item['search_name'], stemmer),
        "stemmed_description": stem_text_or_list(item['description'], stemmer)
    }


def extract_nutrition_per_gram(food_nutrients: List[Dict]) -> Dict[str, float]:
    """
    foodNutrientsから4つの栄養素を抽出し、1gあたりに変換

    Args:
        food_nutrients: USDAのfoodNutrients配列（100gあたり）

    Returns:
        1gあたりの栄養情報（4つのみ）
    """
    default_nutrition = {}

    for nutrient_obj in food_nutrients:
        nutrient_id = nutrient_obj['nutrient']['id']
        amount = nutrient_obj.get('amount', 0)

        if nutrient_id in NUTRIENT_ID_MAPPING:
            field_name = NUTRIENT_ID_MAPPING[nutrient_id]
            # 100gあたり → 1gあたりに変換
            per_gram = amount / 100.0
            default_nutrition[field_name] = round(per_gram, 6)

    # 念の為、全ての栄養素が存在することを確認
    for field_name in NUTRIENT_ID_MAPPING.values():
        if field_name not in default_nutrition:
            default_nutrition[field_name] = 0.0
            # print(f"⚠️  警告: {field_name}が見つかりません（0.0を設定）")

    return default_nutrition


def calculate_default_calories(food_nutrients: List[Dict]) -> float:
    """
    default_calories（1gあたり）を計算
    """
    for nutrient_obj in food_nutrients:
        if nutrient_obj['nutrient']['id'] == 1008:  # Energy
            calories_per_100g = nutrient_obj.get('amount', 0)
            return round(calories_per_100g / 100.0, 6)
    return 0.0


def map_basic_fields(item: Dict, ingredient_type: str) -> Dict:
    """基本フィールドをマッピング"""
    return {
        "id": f"usda_{item['foodCode']}",
        "ingredient_type": ingredient_type,  # "raw" または "prepared"
        "original_name": item.get('original_description', item['description']),
        "search_name": item['search_name'],
        "description": item['description'],
        "ai_description": item.get('ai_description'),
        
        # LLMで生成された表示関連フィールド
        "display_name": item.get('display_name'),  # 表示用の名前（例: "Ritz Butter Crackers"）
        "display_variant": item.get('display_variant'),  # バリアント（例: "Sugar-Free", "Fresh"）
        "display_badges": item.get('display_badges', []),  # バッジ（例: ["Diet", "Organic"]）
        
        # LLMで生成された絵文字フィールド
        "category_emoji": item.get('category_emoji'),  # カテゴリの絵文字（例: "🍞"）
        "food_specific_emoji": item.get('food_specific_emoji'),  # 食材固有の絵文字
        
        # LLMで生成された頻度情報
        "consumption_frequency": item.get('consumption_frequency'),  # 消費頻度（common, moderate, rare）
        "frequency_score": item.get('frequency_score'),  # 頻度スコア（1-3）
        
        # カテゴリ情報
        "category": item.get('category'),  # 食材カテゴリ（例: "Yeast breads"）
        
        # LLMで生成された識別情報
        "brand_name": item.get('brand_name'),  # ブランド名（例: "Ritz", "McDonald's"）
        "item_type": item.get('item_type'),  # 食材タイプ（raw_ingredient, processed_ingredient, prepared_dish）

        # メタデータ
        "data_type": "unified",
        "source": "USDA_FNDDS",
        "processing_method": "llm_generated_patterns_v2",
        "conversion_timestamp": time.time(),

        # 単位
        "default_unit": "gram",
        "unit_to_grams": item.get('unit_to_grams', {"gram": 1.0, "oz": 28.35, "lb": 453.6})
    }


def convert_to_mynetdiary_format(usda_item: Dict, stemmer: PorterStemmer, ingredient_type: str) -> Dict:
    """
    USDAアイテムをMyNetDiary互換フォーマットに変換

    Args:
        usda_item: USDAの検索パターンアイテム
        stemmer: PorterStemmerインスタンス
        ingredient_type: "raw" または "prepared"

    Returns:
        MyNetDiary互換フォーマットの辞書
    """
    # 基本フィールド
    result = map_basic_fields(usda_item, ingredient_type)

    # default_calories（1gあたり）
    result['default_calories'] = calculate_default_calories(usda_item.get('foodNutrients', []))

    # default_nutrition（1gあたり、4つのみ）
    result['default_nutrition'] = extract_nutrition_per_gram(usda_item.get('foodNutrients', []))

    # Stemming処理
    stemmed = add_stemmed_fields(usda_item, stemmer)
    result.update(stemmed)

    return result


def main():
    """メイン処理"""

    print("="*80)
    print("🔄 USDA → MyNetDiary互換フォーマット変換")
    print("="*80)
    print()

    # パス設定
    base_dir = Path("/Users/odasoya/meal_analysis_api_2/usda_data_processing")
    input_dir = base_dir / "output"
    output_dir = base_dir / "db"

    # 出力ディレクトリを作成
    output_dir.mkdir(exist_ok=True)
    print(f"📁 出力ディレクトリ: {output_dir}")
    print()

    # Stemmerの初期化
    print("🔧 Stemmerを初期化中...")
    stemmer = setup_stemmer()
    print("   ✅ 初期化完了")
    print()

    # 入力ファイル
    input_files = [
        {
            "path": input_dir / "usda_raw_ingredients_search_patterns.json",
            "type": "raw",
            "name": "生食材"
        },
        {
            "path": input_dir / "usda_prepared_ingredients_search_patterns.json",
            "type": "prepared",
            "name": "準備済み食材"
        }
    ]

    all_items = []
    total_count = 0

    # 各ファイルを処理
    for file_info in input_files:
        file_path = file_info['path']
        ingredient_type = file_info['type']
        display_name = file_info['name']

        if not file_path.exists():
            print(f"⚠️  スキップ: {file_path.name} が見つかりません")
            continue

        print(f"📖 処理中: {display_name} ({file_path.name})")

        # データ読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = data.get('items', [])
        print(f"   読み込み: {len(items)}件")

        # 各アイテムを変換
        converted_items = []
        for item in items:
            converted = convert_to_mynetdiary_format(item, stemmer, ingredient_type)
            converted_items.append(converted)

        all_items.extend(converted_items)
        total_count += len(converted_items)

        print(f"   ✅ 変換完了: {len(converted_items)}件")
        print()

    # 統合DBを保存
    output_file = output_dir / "usda_unified_db.json"

    print(f"💾 統合DB保存中: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)

    print(f"   ✅ 保存完了: {len(all_items)}件")
    print()

    # 統計情報
    print("="*80)
    print("📊 統計情報")
    print("="*80)

    raw_count = sum(1 for item in all_items if item['ingredient_type'] == 'raw')
    prepared_count = sum(1 for item in all_items if item['ingredient_type'] == 'prepared')

    print(f"\n総アイテム数: {len(all_items)}件")
    print(f"  - 生食材: {raw_count}件")
    print(f"  - 準備済み: {prepared_count}件")

    # サンプル表示
    print("\n" + "="*80)
    print("📝 変換結果サンプル")
    print("="*80)

    if all_items:
        sample = all_items[0]
        print(f"\n🔍 サンプル: {sample['original_name']}")
        print(f"   ID: {sample['id']}")
        print(f"   タイプ: {sample['ingredient_type']}")
        print(f"   search_name: {sample['search_name'][:3]}...")
        print(f"   stemmed_search_name: {sample['stemmed_search_name'][:3]}...")
        print(f"   default_unit: {sample['default_unit']}")
        print(f"   default_calories: {sample['default_calories']}")
        print(f"   default_nutrition:")
        for key, value in sample['default_nutrition'].items():
            print(f"      {key}: {value}")
        print(f"   unit_to_grams: {len(sample['unit_to_grams'])}個の単位")

    print("\n" + "="*80)
    print("🎉 処理完了！")
    print("="*80)
    print(f"\n出力ファイル: {output_file}")
    print(f"総件数: {len(all_items)}件")
    print()


if __name__ == "__main__":
    main()
