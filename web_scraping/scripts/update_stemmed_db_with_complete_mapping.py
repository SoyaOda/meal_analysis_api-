#!/usr/bin/env python3
"""
complete_mapping_with_14_foods.jsonを使用して、
mynetdiary_converted_tool_calls_list_stemmed.jsonをアップデートする

処理内容:
1. マッピングファイルから1,139件のマッピングを読み込み
2. 各マッピングについて:
   - stemmed_idでstemmed_dbから該当食材を特定
   - sequenceでcomplete_food_databaseから該当食材を特定
   - complete_food_databaseから"serving_info", "nutrition", "serving_conversions"を取得
   - stemmed_dbの該当食材に"update_info"を追加
3. 新しいupdated_mynetdiary_converted_tool_calls_list_stemmed.jsonを作成

Usage:
    python update_stemmed_db_with_complete_mapping.py
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


def load_mapping(filepath: Path) -> List[dict]:
    """マッピングファイルを読み込む"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['mappings']


def load_stemmed_db(filepath: Path) -> List[dict]:
    """stemmed DBを読み込む"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_complete_db(filepath: Path) -> Dict[int, dict]:
    """complete_food_database.jsonを読み込み、sequence -> food のマッピングを作成"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # sequence -> food data のマッピング
    sequence_to_food = {}
    for food in data['foods']:
        sequence_to_food[food['sequence']] = food

    return sequence_to_food


def update_stemmed_db(
    stemmed_data: List[dict],
    mappings: List[dict],
    complete_db: Dict[int, dict]
) -> tuple[List[dict], dict]:
    """stemmed dataを更新"""

    # stemmed_id -> index のマッピングを作成
    id_to_index = {}
    for i, item in enumerate(stemmed_data):
        id_to_index[str(item['id'])] = i

    stats = {
        'total_stemmed_items': len(stemmed_data),
        'total_mappings': len(mappings),
        'successfully_updated': 0,
        'stemmed_not_found': 0,
        'complete_not_found': 0,
        'nutrition_renamed': 0,
        'items_removed': 0,
        'updated_items': [],
        'not_updated_items': [],
        'removed_items': []
    }

    # 全アイテムに対して"nutrition"を"nutrition_per_100g_old"にリネーム
    for item in stemmed_data:
        if 'nutrition' in item:
            item['nutrition_per_100g_old'] = item.pop('nutrition')
            stats['nutrition_renamed'] += 1

    # 更新されたアイテムを追跡
    updated_ids = set()

    for mapping in mappings:
        stemmed_id = mapping['stemmed_id']
        sequence = mapping['sequence']

        # stemmed_dbで該当アイテムを探す
        if stemmed_id not in id_to_index:
            stats['stemmed_not_found'] += 1
            stats['not_updated_items'].append({
                'stemmed_id': stemmed_id,
                'stemmed_name': mapping['stemmed_name'],
                'reason': 'stemmed_not_found'
            })
            continue

        # complete_dbで該当食材を探す
        if sequence not in complete_db:
            stats['complete_not_found'] += 1
            stats['not_updated_items'].append({
                'stemmed_id': stemmed_id,
                'stemmed_name': mapping['stemmed_name'],
                'sequence': sequence,
                'reason': 'complete_not_found'
            })
            continue

        # 更新処理
        idx = id_to_index[stemmed_id]
        complete_food = complete_db[sequence]

        # update_infoを追加
        stemmed_data[idx]['update_info'] = {
            'serving_info': complete_food['serving_info'],
            'nutrition': complete_food['nutrition'],
            'serving_conversions': complete_food['serving_conversions'],
            'matched_food_name': complete_food['food_name'],
            'matched_sequence': sequence,
            'update_timestamp': datetime.now().isoformat()
        }

        stats['successfully_updated'] += 1
        updated_ids.add(stemmed_id)
        stats['updated_items'].append({
            'stemmed_id': stemmed_id,
            'stemmed_name': mapping['stemmed_name'],
            'matched_food': complete_food['food_name']
        })

    # マッピングなしのアイテムを削除
    filtered_data = []
    for item in stemmed_data:
        if str(item['id']) in updated_ids:
            # マッピングありのアイテムのみ保持
            filtered_data.append(item)
        else:
            # マッピングなしのアイテムを削除
            stats['items_removed'] += 1
            stats['removed_items'].append({
                'id': item['id'],
                'original_name': item.get('original_name', 'N/A'),
                'reason': 'no_mapping_found'
            })

    return filtered_data, stats


def save_updated_db(data: List[dict], filepath: Path):
    """更新されたDBを保存"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_update_report(stats: dict, filepath: Path):
    """更新レポートを保存"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'statistics': {
            'total_stemmed_items': stats['total_stemmed_items'],
            'total_mappings': stats['total_mappings'],
            'successfully_updated': stats['successfully_updated'],
            'stemmed_not_found': stats['stemmed_not_found'],
            'complete_not_found': stats['complete_not_found'],
            'update_rate': f"{stats['successfully_updated'] / stats['total_stemmed_items'] * 100:.2f}%"
        },
        'not_updated_items': stats['not_updated_items'][:20]  # 最初の20件のみ
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def print_summary(stats: dict):
    """サマリーを出力"""
    print("=" * 80)
    print("Stemmed DB更新レポート（complete_mapping_with_14_foods使用）")
    print("=" * 80)
    print(f"\n【統計】")
    print(f"元のstemmed_db総アイテム数: {stats['total_stemmed_items']:,}")
    print(f"nutritionフィールドをリネーム: {stats['nutrition_renamed']:,}")
    print(f"マッピング数: {stats['total_mappings']:,}")
    print(f"更新成功: {stats['successfully_updated']:,}")
    print(f"削除されたアイテム: {stats['items_removed']:,}")
    print(f"最終アイテム数: {stats['successfully_updated']:,}")
    print(f"stemmed_db未発見: {stats['stemmed_not_found']:,}")
    print(f"complete_db未発見: {stats['complete_not_found']:,}")

    if stats['removed_items']:
        print(f"\n【削除されたアイテム】")
        for i, item in enumerate(stats['removed_items'], 1):
            print(f"{i}. {item['original_name']}")
            print(f"   ID: {item['id']}")
            print(f"   理由: {item['reason']}")

    if stats['not_updated_items']:
        print(f"\n【更新されなかったアイテム（最初の10件）】")
        for i, item in enumerate(stats['not_updated_items'][:10], 1):
            print(f"{i}. Stemmed Name: {item.get('stemmed_name', 'N/A')}")
            print(f"   Stemmed ID: {item.get('stemmed_id', 'N/A')}")
            print(f"   理由: {item.get('reason', 'N/A')}")

        if len(stats['not_updated_items']) > 10:
            print(f"... 他 {len(stats['not_updated_items']) - 10} 件")


def verify_update_info_coverage(updated_data: List[dict]) -> dict:
    """update_infoの網羅性を検証"""
    verification = {
        'total_items': len(updated_data),
        'with_full_update_info': 0,
        'with_no_mapping_status': 0,
        'missing_update_info': 0,
        'sample_full_update': None
    }

    for item in updated_data:
        if 'update_info' in item:
            if 'serving_info' in item['update_info']:
                verification['with_full_update_info'] += 1
                if not verification['sample_full_update']:
                    verification['sample_full_update'] = {
                        'id': item['id'],
                        'original_name': item.get('original_name', 'N/A'),
                        'update_info_keys': list(item['update_info'].keys())
                    }
            elif 'status' in item['update_info'] and item['update_info']['status'] == 'no_mapping_found':
                verification['with_no_mapping_status'] += 1
        else:
            verification['missing_update_info'] += 1

    return verification


def print_verification(verification: dict):
    """検証結果を出力"""
    print("\n" + "=" * 80)
    print("update_info網羅性検証")
    print("=" * 80)
    print(f"総アイテム数: {verification['total_items']:,}")
    print(f"完全なupdate_info: {verification['with_full_update_info']:,} ({verification['with_full_update_info'] / verification['total_items'] * 100:.1f}%)")
    print(f"マッピングなし(削除済み): {verification['with_no_mapping_status']:,}")
    print(f"update_info欠落: {verification['missing_update_info']:,}")

    if verification['sample_full_update']:
        print(f"\n【完全なupdate_infoのサンプル】")
        sample = verification['sample_full_update']
        print(f"ID: {sample['id']}")
        print(f"Name: {sample['original_name']}")
        print(f"Update Info Keys: {', '.join(sample['update_info_keys'])}")

    # 結論
    print(f"\n【結論】")
    if verification['with_full_update_info'] == verification['total_items'] and verification['with_no_mapping_status'] == 0:
        print("✅ 全てのアイテムが完全なupdate_infoを持っています！")
        print(f"   - 完全な情報: {verification['with_full_update_info']:,}件")
        print(f"   - マッピングなしアイテムは削除されました")
    else:
        print(f"⚠️ 想定外の状態です")
        if verification['with_no_mapping_status'] > 0:
            print(f"   - マッピングなしアイテムが残っています: {verification['with_no_mapping_status']:,}件")
        if verification['missing_update_info'] > 0:
            print(f"   - update_infoが欠落: {verification['missing_update_info']:,}件")


def main():
    # ファイルパス
    base_dir = Path('/Users/odasoya/meal_analysis_api_2')
    stemmed_db_file = base_dir / 'db' / 'mynetdiary_converted_tool_calls_list_stemmed.json'
    mapping_file = base_dir / 'web_scraping' / 'processed_data' / 'complete_mapping_with_14_foods.json'
    complete_db_file = base_dir / 'web_scraping' / 'important_data' / 'complete_food_database.json'
    output_file = base_dir / 'db' / 'updated_mynetdiary_converted_tool_calls_list_stemmed.json'
    report_file = base_dir / 'db' / 'stemmed_db_complete_mapping_update_report.json'

    print("【1. データ読み込み中】")
    stemmed_data = load_stemmed_db(stemmed_db_file)
    print(f"✓ Stemmed DB: {len(stemmed_data)} アイテム")

    mappings = load_mapping(mapping_file)
    print(f"✓ マッピング: {len(mappings)} エントリ")

    complete_db = load_complete_db(complete_db_file)
    print(f"✓ Complete DB: {len(complete_db)} 食材（sequence indexed）")

    print("\n【2. データ更新中】")
    updated_data, stats = update_stemmed_db(stemmed_data, mappings, complete_db)
    print(f"✓ 更新完了")

    print("\n【3. update_info網羅性検証中】")
    verification = verify_update_info_coverage(updated_data)
    print(f"✓ 検証完了")

    print("\n【4. ファイル保存中】")
    save_updated_db(updated_data, output_file)
    print(f"✓ 更新DB保存: {output_file}")

    save_update_report(stats, report_file)
    print(f"✓ レポート保存: {report_file}")

    print("\n")
    print_summary(stats)
    print_verification(verification)

    print(f"\n完了！")


if __name__ == '__main__':
    main()
