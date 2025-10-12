#!/usr/bin/env python3
"""
mynetdiary_converted_tool_calls_list_stemmed.jsonをアップデートして、
complete_food_database.jsonの詳細情報を統合する

処理内容:
1. "nutrition" を "nutrition_per_100g_old" にリネーム
2. マッピングを使用して対応する食材を見つける
3. complete_food_database.jsonから"serving_info", "nutrition", "serving_conversions"を
   "update_info"として追加

Usage:
    python update_stemmed_db_with_complete_data.py
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def load_stemmed_db(filepath: Path) -> List[dict]:
    """stemmed DBを読み込む"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_mappings(filepath: Path) -> Dict[str, str]:
    """マッピングを読み込み、stemmed_name -> final_food_name の辞書を作成"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # stemmed_name (正規化) -> final_food_name のマッピング
    mapping_dict = {}
    for mapping in data['mappings']:
        stemmed_name = mapping['stemmed_name']
        final_food_name = mapping['final_food_name']
        # 正規化して保存
        normalized_stemmed = normalize_food_name(stemmed_name)
        mapping_dict[normalized_stemmed] = final_food_name

    return mapping_dict


def load_complete_db(filepath: Path) -> Dict[str, dict]:
    """complete_food_database.jsonを読み込み、food_name -> food_data の辞書を作成"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # food_name -> food_data のマッピング
    # 正規化された名前もキーとして保存
    db_dict = {}
    for food in data['foods']:
        food_name = food['food_name']
        # 改行をスペースに置換して正規化
        normalized_name = food_name.replace('\n', ' ').strip().lower()

        db_dict[normalized_name] = {
            'original_name': food_name,
            'serving_info': food['serving_info'],
            'nutrition': food['nutrition'],
            'serving_conversions': food['serving_conversions'],
            'data_sources': food.get('data_sources', {})
        }

    return db_dict


def normalize_food_name(name) -> str:
    """食材名を正規化

    nameがリストの場合は最初の要素を使用
    """
    if isinstance(name, list):
        name = name[0] if name else ''
    if not isinstance(name, str):
        name = str(name)
    return name.replace('\n', ' ').strip().lower()


def update_stemmed_data(
    stemmed_data: List[dict],
    mappings: Dict[str, str],
    complete_db: Dict[str, dict]
) -> tuple[List[dict], dict]:
    """stemmed dataを更新"""

    updated_data = []
    stats = {
        'total_items': len(stemmed_data),
        'updated_with_complete_info': 0,
        'mapping_found': 0,
        'complete_data_found': 0,
        'no_mapping': 0,
        'no_complete_data': 0,
        'missing_items': []
    }

    for item in stemmed_data:
        # 1. "nutrition" を "nutrition_per_100g_old" にリネーム
        if 'nutrition' in item:
            item['nutrition_per_100g_old'] = item.pop('nutrition')

        # 2. マッピングを使用してfinal_food_nameを取得（original_nameを使用）
        original_name = item.get('original_name', '')
        normalized_original_name = normalize_food_name(original_name)
        final_food_name = mappings.get(normalized_original_name)

        if final_food_name:
            stats['mapping_found'] += 1

            # 3. complete_dbから対応する食材情報を取得
            normalized_final_name = normalize_food_name(final_food_name)
            complete_info = complete_db.get(normalized_final_name)

            if complete_info:
                stats['complete_data_found'] += 1
                stats['updated_with_complete_info'] += 1

                # 4. update_infoを追加
                item['update_info'] = {
                    'serving_info': complete_info['serving_info'],
                    'nutrition': complete_info['nutrition'],
                    'serving_conversions': complete_info['serving_conversions'],
                    'data_sources': complete_info['data_sources'],
                    'matched_food_name': complete_info['original_name'],
                    'update_timestamp': datetime.now().isoformat()
                }
            else:
                stats['no_complete_data'] += 1
                stats['missing_items'].append({
                    'original_name': original_name,
                    'final_food_name': final_food_name,
                    'reason': 'complete_data_not_found'
                })
                # update_infoなしでマッピング情報のみ記録
                item['update_info'] = {
                    'matched_food_name': final_food_name,
                    'status': 'complete_data_not_found',
                    'update_timestamp': datetime.now().isoformat()
                }
        else:
            stats['no_mapping'] += 1
            stats['missing_items'].append({
                'original_name': original_name,
                'reason': 'no_mapping_found'
            })
            # update_infoにステータスのみ記録
            item['update_info'] = {
                'status': 'no_mapping_found',
                'update_timestamp': datetime.now().isoformat()
            }

        updated_data.append(item)

    return updated_data, stats


def save_updated_db(data: List[dict], filepath: Path):
    """更新されたDBを保存"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_update_report(stats: dict, filepath: Path):
    """更新レポートを保存"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'statistics': stats,
        'summary': {
            'total_items': stats['total_items'],
            'successfully_updated': stats['updated_with_complete_info'],
            'update_rate': f"{stats['updated_with_complete_info'] / stats['total_items'] * 100:.2f}%",
            'mapping_found': stats['mapping_found'],
            'complete_data_found': stats['complete_data_found'],
            'missing_mappings': stats['no_mapping'],
            'missing_complete_data': stats['no_complete_data']
        }
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def print_summary(stats: dict):
    """サマリーを出力"""
    print("=" * 80)
    print("Stemmed DB更新レポート")
    print("=" * 80)
    print(f"\n【統計】")
    print(f"総アイテム数: {stats['total_items']:,}")
    print(f"完全情報で更新: {stats['updated_with_complete_info']:,} ({stats['updated_with_complete_info'] / stats['total_items'] * 100:.1f}%)")
    print(f"マッピング発見: {stats['mapping_found']:,}")
    print(f"完全データ発見: {stats['complete_data_found']:,}")
    print(f"マッピング未発見: {stats['no_mapping']:,}")
    print(f"完全データ未発見: {stats['no_complete_data']:,}")

    if stats['missing_items']:
        print(f"\n【未更新アイテム（最初の10件）】")
        for i, item in enumerate(stats['missing_items'][:10], 1):
            original = item.get('original_name', 'N/A')
            print(f"{i}. Original: {original[:60] if len(original) > 60 else original}")
            print(f"   理由: {item['reason']}")
            if 'final_food_name' in item:
                final = item['final_food_name']
                print(f"   Final name: {final[:60] if len(final) > 60 else final}")

        if len(stats['missing_items']) > 10:
            print(f"... 他 {len(stats['missing_items']) - 10} 件")


def main():
    # ファイルパス
    base_dir = Path('/Users/odasoya/meal_analysis_api_2')
    stemmed_db_file = base_dir / 'db' / 'mynetdiary_converted_tool_calls_list_stemmed.json'
    mapping_file = base_dir / 'web_scraping' / 'processed_data' / 'complete_1to1_mappings.json'
    complete_db_file = base_dir / 'web_scraping' / 'important_data' / 'complete_food_database.json'
    output_file = base_dir / 'db' / 'updated_mynetdiary_converted_tool_calls_list_stemmed.json'
    report_file = base_dir / 'db' / 'stemmed_db_update_report.json'

    print("【1. データ読み込み中】")
    stemmed_data = load_stemmed_db(stemmed_db_file)
    print(f"✓ Stemmed DB: {len(stemmed_data)} アイテム")

    mappings = load_mappings(mapping_file)
    print(f"✓ マッピング: {len(mappings)} エントリ")

    complete_db = load_complete_db(complete_db_file)
    print(f"✓ Complete DB: {len(complete_db)} 食材")

    print("\n【2. データ更新中】")
    updated_data, stats = update_stemmed_data(stemmed_data, mappings, complete_db)
    print(f"✓ 更新完了")

    print("\n【3. ファイル保存中】")
    save_updated_db(updated_data, output_file)
    print(f"✓ 更新DB保存: {output_file}")

    save_update_report(stats, report_file)
    print(f"✓ レポート保存: {report_file}")

    print("\n")
    print_summary(stats)

    print(f"\n完了！")


if __name__ == '__main__':
    main()
