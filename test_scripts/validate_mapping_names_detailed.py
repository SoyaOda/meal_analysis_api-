#!/usr/bin/env python
"""
マッピングファイル内のすべてのUSDA名がデータベースに存在するか詳細検証
all_usda_mappings内のすべての項目も検証
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
    """マッピングファイル内のUSDA名を詳細検証"""

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
        'total_all_mappings': 0,  # 全all_usda_mappings内の総項目数
        'valid_all_mappings': 0,
        'invalid_all_mappings': [],
        'database_mismatch': [],
        'all_mappings_stats': {}  # 各食品のall_usda_mappings統計
    }

    # 各マッピングを検証
    for food_id, mapping in mappings.items():
        display_name = mapping.get('display_name', food_id)

        # all_usda_mappings統計を初期化
        all_mappings_count = 0
        valid_mappings_count = 0
        invalid_mappings_list = []

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
                        'actual_db': actual_db,
                        'type': 'default'
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

            all_mappings_count += 1
            validation_results['total_all_mappings'] += 1

            if name in usda_items:
                actual_db = usda_items[name]
                validation_results['valid_all_mappings'] += 1
                valid_mappings_count += 1

                # データベース名が一致しているか確認
                if expected_db != actual_db:
                    validation_results['database_mismatch'].append({
                        'display_name': display_name,
                        'usda_name': name,
                        'expected_db': expected_db,
                        'actual_db': actual_db,
                        'type': 'all_mappings'
                    })
            else:
                validation_results['invalid_all_mappings'].append({
                    'display_name': display_name,
                    'usda_name': name,
                    'expected_db': expected_db
                })
                invalid_mappings_list.append(name)

        # 各食品の統計を保存
        validation_results['all_mappings_stats'][display_name] = {
            'total': all_mappings_count,
            'valid': valid_mappings_count,
            'invalid': len(invalid_mappings_list),
            'invalid_names': invalid_mappings_list
        }

    return validation_results

def print_detailed_results(results):
    """詳細な検証結果を表示"""
    print("\n" + "="*80)
    print("検証結果サマリー")
    print("="*80)

    # デフォルトUSDAの検証結果
    print(f"\n【デフォルトUSDA】")
    print(f"  ✅ 有効: {results['valid_defaults']}/{results['total_mappings']} ({results['valid_defaults']/results['total_mappings']*100:.1f}%)")

    if results['invalid_defaults']:
        print(f"  ❌ 無効: {len(results['invalid_defaults'])} 件")
        print("\n  存在しないデフォルトUSDA名:")
        for item in results['invalid_defaults'][:5]:  # 最初の5件を表示
            print(f"    - {item['display_name']}: \"{item['usda_name']}\" ({item['expected_db']})")
        if len(results['invalid_defaults']) > 5:
            print(f"    ... 他 {len(results['invalid_defaults']) - 5} 件")

    # all_usda_mappingsの詳細統計
    print(f"\n【all_usda_mappings詳細統計】")
    print(f"  📊 総項目数: {results['total_all_mappings']}")
    print(f"  ✅ 有効: {results['valid_all_mappings']} ({results['valid_all_mappings']/results['total_all_mappings']*100:.1f}%)")

    invalid_count = results['total_all_mappings'] - results['valid_all_mappings']
    if invalid_count > 0:
        print(f"  ❌ 無効: {invalid_count} ({invalid_count/results['total_all_mappings']*100:.1f}%)")

    # 問題のある食品を表示
    problem_foods = []
    for display_name, stats in results['all_mappings_stats'].items():
        if stats['invalid'] > 0:
            problem_foods.append((display_name, stats))

    if problem_foods:
        print(f"\n  問題のある食品 ({len(problem_foods)} 件):")
        for display_name, stats in sorted(problem_foods, key=lambda x: x[1]['invalid'], reverse=True)[:10]:
            print(f"    {display_name}:")
            print(f"      総数: {stats['total']}, 有効: {stats['valid']}, 無効: {stats['invalid']}")
            if stats['invalid_names']:
                for name in stats['invalid_names'][:3]:
                    print(f"        ❌ \"{name}\"")
                if len(stats['invalid_names']) > 3:
                    print(f"        ... 他 {len(stats['invalid_names']) - 3} 件")

    # 全体の無効な項目リスト（重複除去）
    if results['invalid_all_mappings']:
        unique_invalid = {}
        for item in results['invalid_all_mappings']:
            if item['usda_name'] not in unique_invalid:
                unique_invalid[item['usda_name']] = []
            unique_invalid[item['usda_name']].append(item['display_name'])

        print(f"\n  ユニークな無効USDA名 ({len(unique_invalid)} 件):")
        for i, (usda_name, foods) in enumerate(list(unique_invalid.items())[:5]):
            print(f"    {i+1}. \"{usda_name}\"")
            print(f"       使用している食品: {', '.join(foods[:3])}")
            if len(foods) > 3:
                print(f"       ... 他 {len(foods) - 3} 食品")

    # データベース不一致
    if results['database_mismatch']:
        print(f"\n【データベース不一致】")
        print(f"  ⚠️  {len(results['database_mismatch'])} 件")

        # タイプ別に集計
        default_mismatch = [x for x in results['database_mismatch'] if x['type'] == 'default']
        all_mappings_mismatch = [x for x in results['database_mismatch'] if x['type'] == 'all_mappings']

        if default_mismatch:
            print(f"\n  デフォルトUSDAの不一致: {len(default_mismatch)} 件")
            for item in default_mismatch[:3]:
                print(f"    - {item['display_name']}: \"{item['usda_name']}\"")
                print(f"      期待: {item['expected_db']} → 実際: {item['actual_db']}")

        if all_mappings_mismatch:
            print(f"\n  all_usda_mappingsの不一致: {len(all_mappings_mismatch)} 件")
            for item in all_mappings_mismatch[:3]:
                print(f"    - {item['display_name']}: \"{item['usda_name']}\"")
                print(f"      期待: {item['expected_db']} → 実際: {item['actual_db']}")

    # 総合判定
    print("\n" + "="*80)

    total_items = results['total_mappings'] + results['total_all_mappings']
    valid_items = results['valid_defaults'] + results['valid_all_mappings']

    print(f"📊 総合統計:")
    print(f"   検証項目総数: {total_items}")
    print(f"   有効項目数: {valid_items} ({valid_items/total_items*100:.1f}%)")

    if not results['invalid_defaults'] and invalid_count == 0:
        print("\n✅ すべてのUSDA名がデータベースに存在します！")
    else:
        print(f"\n❌ {len(results['invalid_defaults']) + invalid_count} 件のUSDA名がデータベースに存在しません。")
        print("   マッピングファイルの修正が必要です。")

    if results['database_mismatch']:
        print("\n⚠️  データベース名の不一致があります。")
        print("   正確性のため、データベース名を修正することを推奨します。")

    print("="*80)

def main():
    parser = argparse.ArgumentParser(description='マッピングファイル内のUSDA名を詳細検証')
    parser.add_argument(
        '--mapping',
        type=str,
        required=True,
        help='検証するマッピングファイル'
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
    print("USDAマッピング詳細検証スクリプト")
    print("="*80)
    print()

    # USDAデータベースを読み込み
    print("📚 USDAデータベースを読み込み中...")
    usda_items = load_usda_database()
    print(f"\n✅ 総USDA項目数: {len(usda_items):,}")

    # マッピングファイルを検証
    results = validate_mapping_file(mapping_path, usda_items)

    # 結果を表示
    print_detailed_results(results)

    # エラー詳細をファイルに保存
    if results['invalid_defaults'] or results['invalid_all_mappings']:
        error_file = mapping_path.parent / f"{mapping_path.stem}_detailed_validation_errors.json"
        error_data = {
            'summary': {
                'total_mappings': results['total_mappings'],
                'valid_defaults': results['valid_defaults'],
                'invalid_defaults_count': len(results['invalid_defaults']),
                'total_all_mappings': results['total_all_mappings'],
                'valid_all_mappings': results['valid_all_mappings'],
                'invalid_all_mappings_count': len(results['invalid_all_mappings'])
            },
            'invalid_defaults': results['invalid_defaults'],
            'invalid_all_mappings': results['invalid_all_mappings'],
            'database_mismatch': results['database_mismatch'],
            'all_mappings_stats': results['all_mappings_stats']
        }

        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)

        print(f"\n📝 詳細エラーレポートを保存: {error_file}")

if __name__ == "__main__":
    main()