#!/usr/bin/env python
"""
マッピングファイル内のすべてのUSDA名がデータベースに存在するか検証
"""

import json
import argparse
import re
from pathlib import Path
from collections import defaultdict

# パス設定
project_root = Path(__file__).parent.parent
usda_names_dir = project_root / "usda_database" / "names_list"

def load_usda_database():
    """すべてのUSDAデータベースファイルを読み込み（番号を除外）"""
    db_files = {
        'survey_fndds': 'survey_food_names.txt',
        'sr_legacy': 'sr_legacy_food_names.txt',
        'foundation': 'foundation_food_names.txt',
        'branded': 'branded_food_names.txt'
    }

    all_items = {}
    for db_name, file_name in db_files.items():
        db_path = usda_names_dir / file_name
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                items = []
                for line in f:
                    line = line.strip()
                    if line:
                        # 行頭の番号とドットを除去（例: "123. Food name" -> "Food name"）
                        match = re.match(r'^\d+\.\s+(.+)$', line)
                        if match:
                            food_name = match.group(1)
                            items.append(food_name)
                            if food_name not in all_items:
                                all_items[food_name] = db_name
                        else:
                            # 番号がない場合はそのまま使用
                            items.append(line)
                            if line not in all_items:
                                all_items[line] = db_name

                print(f"✅ {db_name}: {len(items):,} 項目を読み込み")
        else:
            print(f"⚠️  {db_name}: ファイルが見つかりません")

    return all_items

def validate_mapping_file(mapping_file, usda_items):
    """マッピングファイル内のUSDA名を検証"""

    # マッピングファイルを読み込み
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mappings = json.load(f)

    print(f"\n📋 マッピングファイル: {mapping_file}")
    print(f"   総マッピング数: {len(mappings)}")

    # 検証結果を格納
    validation_results = {
        'total_mappings': len(mappings),
        'valid_defaults': 0,
        'invalid_defaults': [],
        'valid_all_mappings': 0,
        'invalid_all_mappings': [],
        'database_mismatch': []
    }

    # 各マッピングを検証
    for food_id, mapping in mappings.items():
        display_name = mapping.get('display_name', food_id)

        # デフォルトUSDAを検証
        default_usda = mapping.get('default_usda')
        if default_usda:
            name = default_usda['name']
            expected_db = default_usda['database']

            if name in usda_items:
                actual_db = usda_items[name]
                validation_results['valid_defaults'] += 1

                # データベース名が一致しているか確認
                if expected_db != actual_db:
                    validation_results['database_mismatch'].append({
                        'display_name': display_name,
                        'usda_name': name,
                        'expected_db': expected_db,
                        'actual_db': actual_db
                    })
            else:
                validation_results['invalid_defaults'].append({
                    'display_name': display_name,
                    'usda_name': name,
                    'expected_db': expected_db
                })

        # all_usda_mappingsを検証
        all_mappings = mapping.get('all_usda_mappings', [])
        for item in all_mappings:
            name = item['name']
            expected_db = item['database']

            if name in usda_items:
                actual_db = usda_items[name]
                validation_results['valid_all_mappings'] += 1

                # データベース名が一致しているか確認
                if expected_db != actual_db:
                    validation_results['database_mismatch'].append({
                        'display_name': display_name,
                        'usda_name': name,
                        'expected_db': expected_db,
                        'actual_db': actual_db
                    })
            else:
                validation_results['invalid_all_mappings'].append({
                    'display_name': display_name,
                    'usda_name': name,
                    'expected_db': expected_db
                })

    return validation_results

def print_results(results):
    """検証結果を表示"""
    print("\n" + "="*80)
    print("検証結果サマリー")
    print("="*80)

    # デフォルトUSDAの検証結果
    print(f"\n【デフォルトUSDA】")
    print(f"  ✅ 有効: {results['valid_defaults']}/{results['total_mappings']}")

    if results['invalid_defaults']:
        print(f"  ❌ 無効: {len(results['invalid_defaults'])} 件")
        print("\n  存在しないUSDA名:")
        for item in results['invalid_defaults'][:10]:  # 最初の10件を表示
            print(f"    - {item['display_name']}: \"{item['usda_name']}\" ({item['expected_db']})")
        if len(results['invalid_defaults']) > 10:
            print(f"    ... 他 {len(results['invalid_defaults']) - 10} 件")

    # 全マッピングの検証結果
    print(f"\n【全USDAマッピング】")
    print(f"  ✅ 有効: {results['valid_all_mappings']} 項目")

    if results['invalid_all_mappings']:
        print(f"  ❌ 無効: {len(results['invalid_all_mappings'])} 件")

        # display_name別に集計
        by_display = defaultdict(list)
        for item in results['invalid_all_mappings']:
            by_display[item['display_name']].append(item['usda_name'])

        print("\n  存在しないUSDA名（食品別）:")
        count = 0
        for display_name, names in by_display.items():
            if count >= 5:  # 最初の5食品のみ表示
                remaining = len(by_display) - 5
                if remaining > 0:
                    print(f"    ... 他 {remaining} 食品")
                break

            print(f"    {display_name}:")
            for i, name in enumerate(names):
                if i >= 3:  # 各食品で最初の3件のみ表示
                    if len(names) > 3:
                        print(f"      ... 他 {len(names) - 3} 件")
                    break
                print(f"      - \"{name}\"")
            count += 1

    # データベース不一致
    if results['database_mismatch']:
        print(f"\n【データベース不一致】")
        print(f"  ⚠️  {len(results['database_mismatch'])} 件")

        # display_name別に集計
        by_display = defaultdict(list)
        for item in results['database_mismatch']:
            by_display[item['display_name']].append(item)

        print("\n  データベース名が異なる項目:")
        count = 0
        for display_name, items in by_display.items():
            if count >= 5:  # 最初の5食品のみ表示
                break

            print(f"    {display_name}:")
            for i, item in enumerate(items):
                if i >= 2:  # 各食品で最初の2件のみ表示
                    break
                print(f"      - \"{item['usda_name']}\"")
                print(f"        期待: {item['expected_db']} → 実際: {item['actual_db']}")
            count += 1

    # 総合判定
    print("\n" + "="*80)
    if not results['invalid_defaults'] and not results['invalid_all_mappings']:
        print("✅ すべてのUSDA名がデータベースに存在します！")
    else:
        print("❌ 一部のUSDA名がデータベースに存在しません。")
        print("   マッピングファイルの修正が必要です。")

    if results['database_mismatch']:
        print("⚠️  データベース名の不一致があります。")
        print("   正確性のため、データベース名を修正することを推奨します。")

    print("="*80)

def main():
    parser = argparse.ArgumentParser(description='マッピングファイル内のUSDA名を検証')
    parser.add_argument(
        '--mapping',
        type=str,
        default='mappings/food_name_mappings.json',
        help='検証するマッピングファイル（デフォルト: mappings/food_name_mappings.json）'
    )

    args = parser.parse_args()

    # マッピングファイルのパスを解決
    mapping_path = Path(args.mapping)
    if not mapping_path.is_absolute():
        mapping_path = Path(__file__).parent / mapping_path

    if not mapping_path.exists():
        print(f"❌ マッピングファイルが見つかりません: {mapping_path}")
        return

    print("="*80)
    print("USDAマッピング検証スクリプト")
    print("="*80)
    print()

    # USDAデータベースを読み込み
    print("📚 USDAデータベースを読み込み中...")
    usda_items = load_usda_database()
    print(f"\n✅ 総USDA項目数: {len(usda_items):,}")

    # マッピングファイルを検証
    results = validate_mapping_file(mapping_path, usda_items)

    # 結果を表示
    print_results(results)

    # エラー詳細をファイルに保存（オプション）
    if results['invalid_defaults'] or results['invalid_all_mappings']:
        error_file = mapping_path.parent / f"{mapping_path.stem}_validation_errors.json"
        error_data = {
            'invalid_defaults': results['invalid_defaults'],
            'invalid_all_mappings': results['invalid_all_mappings'],
            'database_mismatch': results['database_mismatch']
        }

        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)

        print(f"\n📝 エラー詳細を保存: {error_file}")

    # デバッグ用：最初の無効な項目を検索
    if results['invalid_defaults'] and len(results['invalid_defaults']) > 0:
        first_invalid = results['invalid_defaults'][0]
        print(f"\n🔍 デバッグ: 最初の無効な項目を検索")
        print(f"   探している名前: \"{first_invalid['usda_name']}\"")

        # 部分一致で検索
        found_similar = []
        for item_name in usda_items.keys():
            if first_invalid['usda_name'].lower() in item_name.lower():
                found_similar.append(item_name)

        if found_similar:
            print(f"   類似する項目が見つかりました:")
            for name in found_similar[:5]:
                print(f"     - \"{name}\"")
        else:
            print(f"   類似する項目は見つかりませんでした")

if __name__ == "__main__":
    main()