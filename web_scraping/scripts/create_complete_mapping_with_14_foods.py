#!/usr/bin/env python3
"""
complete_food_database.json と stemmed_db を直接マッピングして
14食材も含めた完全なマッピングファイルを作成

処理:
1. complete_food_database.jsonの全食材に対して
2. stemmed_dbから対応する食材を探す（original_nameで一致）
3. マッピングを作成
   - stemmed_id: stemmed_db[id]
   - stemmed_name: stemmed_db[original_name]
   - final_food_id: food_{sequence:04d}
   - final_food_name: complete_db[food_name]

Usage:
    python create_complete_mapping_with_14_foods.py
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def normalize_name(name) -> str:
    """食材名を正規化"""
    if isinstance(name, list):
        name = name[0] if name else ''
    if not isinstance(name, str):
        name = str(name)
    return name.replace('\n', ' ').strip().lower()


def load_complete_db(filepath: Path) -> List[dict]:
    """complete_food_database.jsonを読み込む"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['foods']


def load_stemmed_db(filepath: Path) -> Dict[str, dict]:
    """stemmed DBを読み込み、正規化名でインデックス化"""
    with open(filepath, 'r', encoding='utf-8') as f:
        stemmed_data = json.load(f)

    # 正規化名 -> stemmed entry のマッピング
    stemmed_dict = {}
    for item in stemmed_data:
        original_name = item.get('original_name', '')
        normalized = normalize_name(original_name)
        stemmed_dict[normalized] = item

    return stemmed_dict


def create_mappings(
    complete_foods: List[dict],
    stemmed_dict: Dict[str, dict],
    existing_mappings: List[dict],
    manual_mappings: List[dict]
) -> tuple[List[dict], dict]:
    """マッピングを作成

    既存マッピングをベースに、complete_food_databaseのsequenceを使用したfinal_food_idを付与
    """

    # 既存マッピングから final_food_name -> stemmed_name の逆引きを作成
    final_to_stemmed = {}
    for mapping in existing_mappings:
        final_name_normalized = normalize_name(mapping['final_food_name'])
        final_to_stemmed[final_name_normalized] = mapping

    # 手動マッピングから stemmed_name -> complete_name の辞書を作成
    manual_mapping_dict = {}
    for mapping in manual_mappings:
        stemmed_normalized = normalize_name(mapping['stemmed_name'])
        complete_normalized = normalize_name(mapping['complete_name'])
        manual_mapping_dict[complete_normalized] = {
            'stemmed_name': mapping['stemmed_name'],
            'complete_name': mapping['complete_name']
        }

    mappings = []
    stats = {
        'total_complete_foods': len(complete_foods),
        'mapped_from_existing': 0,
        'mapped_from_manual': 0,
        'mapped_new': 0,
        'unmapped': 0,
        'unmapped_foods': []
    }

    for food in complete_foods:
        food_name = food['food_name']
        sequence = food['sequence']
        normalized_food_name = normalize_name(food_name)

        # 1. 既存マッピングから対応するstemmed_nameを探す
        existing_mapping = final_to_stemmed.get(normalized_food_name)

        if existing_mapping:
            # 既存マッピングをベースに新しいマッピングを作成
            stemmed_name_normalized = normalize_name(existing_mapping['stemmed_name'])
            stemmed_entry = stemmed_dict.get(stemmed_name_normalized)

            if stemmed_entry:
                mapping = {
                    'stemmed_id': str(stemmed_entry['id']),
                    'stemmed_name': stemmed_entry['original_name'],
                    'final_food_id': f"food_{sequence:04d}",
                    'final_food_name': food_name,
                    'sequence': sequence,
                    'category': food['catalog_category']
                }
                mappings.append(mapping)
                stats['mapped_from_existing'] += 1
            else:
                # stemmed_dbに存在しない場合でもマッピング作成
                mapping = {
                    'stemmed_id': existing_mapping['stemmed_id'],
                    'stemmed_name': existing_mapping['stemmed_name'],
                    'final_food_id': f"food_{sequence:04d}",
                    'final_food_name': food_name,
                    'sequence': sequence,
                    'category': food['catalog_category']
                }
                mappings.append(mapping)
                stats['mapped_from_existing'] += 1
        else:
            # 2. 手動マッピングを確認
            manual_entry = manual_mapping_dict.get(normalized_food_name)
            
            if manual_entry:
                # 手動マッピングを使用
                stemmed_name_normalized = normalize_name(manual_entry['stemmed_name'])
                stemmed_entry = stemmed_dict.get(stemmed_name_normalized)
                
                if stemmed_entry:
                    mapping = {
                        'stemmed_id': str(stemmed_entry['id']),
                        'stemmed_name': stemmed_entry['original_name'],
                        'final_food_id': f"food_{sequence:04d}",
                        'final_food_name': food_name,
                        'sequence': sequence,
                        'category': food['catalog_category']
                    }
                    mappings.append(mapping)
                    stats['mapped_from_manual'] += 1
                else:
                    stats['unmapped'] += 1
                    stats['unmapped_foods'].append({
                        'food_name': food_name,
                        'sequence': sequence,
                        'category': food['catalog_category'],
                        'reason': 'manual_mapping_stemmed_not_found'
                    })
            else:
                # 3. 既存マッピングにも手動マッピングにもない
                # stemmed_dbから直接対応を探す（最後の手段）
                stemmed_entry = stemmed_dict.get(normalized_food_name)

                if stemmed_entry:
                    mapping = {
                        'stemmed_id': str(stemmed_entry['id']),
                        'stemmed_name': stemmed_entry['original_name'],
                        'final_food_id': f"food_{sequence:04d}",
                        'final_food_name': food_name,
                        'sequence': sequence,
                        'category': food['catalog_category']
                    }
                    mappings.append(mapping)
                    stats['mapped_new'] += 1
                else:
                    stats['unmapped'] += 1
                    stats['unmapped_foods'].append({
                        'food_name': food_name,
                        'sequence': sequence,
                        'category': food['catalog_category']
                    })

    return mappings, stats


def save_mappings(mappings: List[dict], stats: dict, output_file: Path):
    """マッピングファイルを保存"""
    
    total_mapped = stats['mapped_from_existing'] + stats['mapped_from_manual'] + stats['mapped_new']
    
    output = {
        'total_mappings': len(mappings),
        'timestamp': datetime.now().isoformat(),
        'description': 'complete_food_database.json と stemmed_db の完全マッピング（13食材含む）',
        'sources': {
            'complete_food_database': 'web_scraping/important_data/complete_food_database.json',
            'stemmed_db': 'db/mynetdiary_converted_tool_calls_list_stemmed.json',
            'manual_mappings': 'web_scraping/processed_data/manual_mapping_14_foods.json'
        },
        'statistics': {
            'total_complete_foods': stats['total_complete_foods'],
            'successfully_mapped': total_mapped,
            'mapped_from_existing': stats['mapped_from_existing'],
            'mapped_from_manual': stats['mapped_from_manual'],
            'mapped_new': stats['mapped_new'],
            'unmapped': stats['unmapped'],
            'mapping_rate': f"{total_mapped / stats['total_complete_foods'] * 100:.2f}%"
        },
        'unmapped_foods': stats['unmapped_foods'],
        'mappings': mappings
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def print_summary(stats: dict, mappings: List[dict]):
    """サマリーを出力"""
    print("=" * 80)
    print("完全マッピング作成レポート")
    print("=" * 80)
    print(f"\n【統計】")
    print(f"complete_food_database総食材数: {stats['total_complete_foods']:,}")
    print(f"既存マッピングから: {stats['mapped_from_existing']:,}")
    print(f"手動マッピングから: {stats['mapped_from_manual']:,}")
    print(f"新規マッピング: {stats['mapped_new']:,}")
    total_mapped = stats['mapped_from_existing'] + stats['mapped_from_manual'] + stats['mapped_new']
    print(f"マッピング成功合計: {total_mapped:,} ({total_mapped / stats['total_complete_foods'] * 100:.1f}%)")
    print(f"マッピング未成功: {stats['unmapped']:,}")

    if stats['unmapped_foods']:
        print(f"\n【マッピング未成功の食材（最初の10件）】")
        for i, food in enumerate(stats['unmapped_foods'][:10], 1):
            name = food['food_name']
            truncated = name[:60] + "..." if len(name) > 60 else name
            print(f"{i}. {truncated}")
            print(f"   Sequence: {food['sequence']}, Category: {food['category']}")

        if len(stats['unmapped_foods']) > 10:
            print(f"... 他 {len(stats['unmapped_foods']) - 10} 件")

    # 既存マッピングと比較
    print(f"\n【比較】")
    print(f"既存マッピング（complete_1to1_mappings.json）: 1,126")
    print(f"新マッピング: {len(mappings):,}")
    print(f"増加数: {len(mappings) - 1126:,}")


def main():
    # ファイルパス
    base_dir = Path('/Users/odasoya/meal_analysis_api_2')
    complete_db_file = base_dir / 'web_scraping' / 'important_data' / 'complete_food_database.json'
    stemmed_db_file = base_dir / 'db' / 'mynetdiary_converted_tool_calls_list_stemmed.json'
    existing_mapping_file = base_dir / 'web_scraping' / 'processed_data' / 'complete_1to1_mappings.json'
    manual_mapping_file = base_dir / 'web_scraping' / 'processed_data' / 'manual_mapping_14_foods.json'
    output_file = base_dir / 'web_scraping' / 'processed_data' / 'complete_mapping_with_14_foods.json'

    print("【1. データ読み込み中】")
    complete_foods = load_complete_db(complete_db_file)
    print(f"✓ complete_food_database: {len(complete_foods)} 食材")

    stemmed_dict = load_stemmed_db(stemmed_db_file)
    print(f"✓ stemmed_db: {len(stemmed_dict)} 食材（正規化済み）")

    with open(existing_mapping_file, 'r', encoding='utf-8') as f:
        existing_data = json.load(f)
    existing_mappings = existing_data['mappings']
    print(f"✓ 既存マッピング: {len(existing_mappings)} エントリ")

    with open(manual_mapping_file, 'r', encoding='utf-8') as f:
        manual_data = json.load(f)
    manual_mappings = manual_data['manual_mappings']
    print(f"✓ 手動マッピング: {len(manual_mappings)} エントリ")

    print("\n【2. マッピング作成中】")
    mappings, stats = create_mappings(complete_foods, stemmed_dict, existing_mappings, manual_mappings)
    print(f"✓ マッピング作成完了: {len(mappings)} エントリ")

    print("\n【3. ファイル保存中】")
    save_mappings(mappings, stats, output_file)
    print(f"✓ 保存完了: {output_file}")

    print("\n")
    print_summary(stats, mappings)

    print(f"\n完了！")


if __name__ == '__main__':
    main()
