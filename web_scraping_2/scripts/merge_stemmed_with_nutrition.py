#!/usr/bin/env python3
"""
カンマ正規化削除後のall_foods_with_nutrition.jsonを使用して、
mynetdiary_converted_tool_calls_list_stemmed.jsonに栄養情報をマージ

処理内容:
1. stemmed.jsonとall_foods_with_nutrition.jsonをマッピングを使ってマージ
2. default_unit, default_calories, unit_to_grams, default_nutritionを追加
3. default_unitがNoneの食材を除外（Ice cubes, Sea salt）
4. マッピングが見つからない食材を除外

出力:
- db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition.json
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def load_stemmed_db(filepath: Path) -> List[dict]:
    """Stemmed DBを読み込む"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_all_foods_nutrition(filepath: Path) -> Dict[str, dict]:
    """all_foods_with_nutrition.jsonを読み込み、正規化名でインデックス化"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # food_name（正規化）→ food_dataのマッピング
    food_dict = {}
    for food in data['foods']:
        # 正規化: 改行をスペースに、小文字化
        normalized_name = food['food_name'].replace('\n', ' ').strip().lower()
        food_dict[normalized_name] = food

    return food_dict


def load_mapping(filepath: Path) -> Dict[str, str]:
    """マッピングファイルを読み込み、stemmed_name → final_food_nameの辞書を作成"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # stemmed_name（正規化）→ final_food_nameのマッピング
    mapping_dict = {}
    for mapping in data['mappings']:
        stemmed_name = mapping['stemmed_name']
        final_food_name = mapping['final_food_name']

        # 正規化して保存
        normalized_stemmed = normalize_name(stemmed_name)
        mapping_dict[normalized_stemmed] = final_food_name

    return mapping_dict


def normalize_name(name) -> str:
    """食材名を正規化"""
    if isinstance(name, list):
        name = name[0] if name else ''
    if not isinstance(name, str):
        name = str(name)
    return name.replace('\n', ' ').strip().lower()


def merge_nutrition_data(
    stemmed_data: List[dict],
    all_foods_dict: Dict[str, dict],
    mapping_dict: Dict[str, str]
) -> tuple[List[dict], dict]:
    """栄養データをマージ"""

    merged_data = []
    stats = {
        'total_stemmed_items': len(stemmed_data),
        'successfully_merged': 0,
        'excluded_no_default_unit': 0,
        'excluded_no_mapping': 0,
        'excluded_no_nutrition_data': 0,
        'excluded_items': []
    }

    for item in stemmed_data:
        # original_nameを正規化してマッピングを検索
        original_name = item.get('original_name', '')
        normalized_original = normalize_name(original_name)

        # マッピングを使用してfinal_food_nameを取得
        final_food_name = mapping_dict.get(normalized_original)

        if not final_food_name:
            # マッピングが見つからない→除外
            stats['excluded_no_mapping'] += 1
            stats['excluded_items'].append({
                'original_name': original_name,
                'reason': 'no_mapping_found'
            })
            continue

        # final_food_nameから食材名のみを抽出
        # "Beans baked canned plain or vegetarian, cup\n239cals"
        # → "Beans baked canned plain or vegetarian"
        extracted_food_name = final_food_name
        if '\n' in extracted_food_name:
            # 改行の前部分を取得
            extracted_food_name = extracted_food_name.split('\n')[0]
        if ', ' in extracted_food_name:
            # カンマの前部分を取得（食材名のみ）
            extracted_food_name = extracted_food_name.split(', ')[0]

        # 抽出した食材名を正規化してall_foods_dictから検索
        normalized_final = normalize_name(extracted_food_name)
        food_data = all_foods_dict.get(normalized_final)

        if not food_data:
            # 栄養データが見つからない→除外
            stats['excluded_no_nutrition_data'] += 1
            stats['excluded_items'].append({
                'original_name': original_name,
                'final_food_name': final_food_name,
                'reason': 'nutrition_data_not_found'
            })
            continue

        # default_unitがNoneの場合→除外（Ice cubes, Sea salt）
        if food_data.get('default_unit') is None:
            stats['excluded_no_default_unit'] += 1
            stats['excluded_items'].append({
                'original_name': original_name,
                'final_food_name': final_food_name,
                'reason': 'no_default_unit'
            })
            continue

        # マージ成功：栄養データを追加
        merged_item = {
            **item,  # 既存データを保持
            'default_unit': food_data['default_unit'],
            'default_calories': food_data['default_calories'],
            'unit_to_grams': food_data['unit_to_grams'],
            'default_nutrition': food_data['default_nutrition']
        }

        merged_data.append(merged_item)
        stats['successfully_merged'] += 1

    return merged_data, stats


def save_merged_db(data: List[dict], filepath: Path):
    """マージされたDBを保存"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_merge_report(stats: dict, filepath: Path):
    """マージレポートを保存"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'statistics': stats,
        'summary': {
            'total_items': stats['total_stemmed_items'],
            'successfully_merged': stats['successfully_merged'],
            'merge_rate': f"{stats['successfully_merged'] / stats['total_stemmed_items'] * 100:.2f}%",
            'excluded_no_default_unit': stats['excluded_no_default_unit'],
            'excluded_no_mapping': stats['excluded_no_mapping'],
            'excluded_no_nutrition_data': stats['excluded_no_nutrition_data'],
            'total_excluded': len(stats['excluded_items'])
        }
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def print_summary(stats: dict):
    """サマリーを表示"""
    print("=" * 80)
    print("Stemmed DB栄養情報マージレポート")
    print("=" * 80)
    print(f"\n【統計】")
    print(f"元のStemmed DBアイテム数: {stats['total_stemmed_items']:,}")
    print(f"マージ成功: {stats['successfully_merged']:,} ({stats['successfully_merged'] / stats['total_stemmed_items'] * 100:.1f}%)")
    print(f"\n【除外】")
    print(f"default_unitなし: {stats['excluded_no_default_unit']}件")
    print(f"マッピングなし: {stats['excluded_no_mapping']}件")
    print(f"栄養データなし: {stats['excluded_no_nutrition_data']}件")
    print(f"合計除外: {len(stats['excluded_items'])}件")

    if stats['excluded_items']:
        print(f"\n【除外されたアイテム（最初の10件）】")
        for i, item in enumerate(stats['excluded_items'][:10], 1):
            print(f"{i}. {item['original_name']}")
            print(f"   理由: {item['reason']}")
            if 'final_food_name' in item:
                print(f"   Final name: {item['final_food_name']}")

        if len(stats['excluded_items']) > 10:
            print(f"... 他 {len(stats['excluded_items']) - 10} 件")


def main():
    """メイン処理"""
    # ファイルパス
    base_dir = Path('/Users/odasoya/meal_analysis_api_2')
    stemmed_db_file = base_dir / 'db' / 'mynetdiary_converted_tool_calls_list_stemmed.json'
    all_foods_file = base_dir / 'web_scraping_2' / 'output' / 'all_foods_with_nutrition.json'
    mapping_file = base_dir / 'web_scraping' / 'processed_data' / 'complete_mapping_with_14_foods.json'
    output_file = base_dir / 'db' / 'mynetdiary_converted_tool_calls_list_stemmed_with_nutrition.json'
    report_file = base_dir / 'db' / 'stemmed_nutrition_merge_report.json'

    print("【1. データ読み込み中】")
    stemmed_data = load_stemmed_db(stemmed_db_file)
    print(f"✓ Stemmed DB: {len(stemmed_data)} アイテム")

    all_foods_dict = load_all_foods_nutrition(all_foods_file)
    print(f"✓ All Foods Nutrition: {len(all_foods_dict)} 食材")

    mapping_dict = load_mapping(mapping_file)
    print(f"✓ マッピング: {len(mapping_dict)} エントリ")

    print("\n【2. 栄養データマージ中】")
    merged_data, stats = merge_nutrition_data(stemmed_data, all_foods_dict, mapping_dict)
    print(f"✓ マージ完了")

    print("\n【3. ファイル保存中】")
    save_merged_db(merged_data, output_file)
    print(f"✓ マージDB保存: {output_file}")

    save_merge_report(stats, report_file)
    print(f"✓ レポート保存: {report_file}")

    print("\n")
    print_summary(stats)

    print(f"\n✅ 完了！")
    print(f"最終アイテム数: {len(merged_data):,}件")


if __name__ == '__main__':
    main()
