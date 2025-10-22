#!/usr/bin/env python
"""
base_1からbase_6のマッピングファイル内の名前がsurveyDownload.jsonに存在するか検証
"""

import json
from pathlib import Path
from collections import defaultdict

# パス設定
project_root = Path(__file__).parent.parent
survey_json_path = project_root / "usda_database" / "surveyDownload.json"

def load_survey_database():
    """surveyDownload.jsonから食品名を抽出"""
    print(f"📚 surveyDownload.jsonを読み込み中...")

    if not survey_json_path.exists():
        print(f"❌ ファイルが見つかりません: {survey_json_path}")
        return None

    with open(survey_json_path, 'r', encoding='utf-8') as f:
        survey_data = json.load(f)

    # 食品名を収集
    food_names = set()

    # surveyDownload.jsonの構造を確認
    if isinstance(survey_data, dict):
        if 'SurveyFoods' in survey_data:
            foods = survey_data['SurveyFoods']
        elif 'foods' in survey_data:
            foods = survey_data['foods']
        else:
            # トップレベルが食品データの場合
            foods = survey_data.values() if isinstance(survey_data, dict) else survey_data
    else:
        foods = survey_data

    # 食品名を抽出
    for food in foods:
        if isinstance(food, dict):
            # 可能な名前フィールドをチェック
            if 'description' in food:
                food_names.add(food['description'])
            if 'foodDescription' in food:
                food_names.add(food['foodDescription'])
            if 'name' in food:
                food_names.add(food['name'])
            if 'fdcDescription' in food:
                food_names.add(food['fdcDescription'])

    print(f"✅ {len(food_names):,} 個の食品名を読み込みました")
    return food_names

def validate_base_file(file_path, survey_names):
    """base_*.jsonファイル内の名前を検証"""

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # マッピング構造を確認
    if isinstance(data, dict):
        # mappings フィールドがある場合
        if 'mappings' in data:
            mappings = data['mappings']
        else:
            mappings = data
    else:
        print(f"⚠️  {file_path.name}: 予期しない構造")
        return None

    # 検証結果
    results = {
        'total': 0,
        'found': 0,
        'not_found': [],
        'names_checked': []
    }

    # 各マッピングの名前をチェック
    for key, mapping in mappings.items():
        # デフォルトのUSDA名を確認
        if 'default_usda' in mapping and mapping['default_usda']:
            name = mapping['default_usda'].get('name')
            if name:
                results['total'] += 1
                results['names_checked'].append(name)
                if name in survey_names:
                    results['found'] += 1
                else:
                    results['not_found'].append({
                        'key': key,
                        'name': name,
                        'field': 'default_usda'
                    })

        # all_usda_mappings内の名前も確認
        if 'all_usda_mappings' in mapping:
            for item in mapping['all_usda_mappings']:
                if 'name' in item:
                    name = item['name']
                    results['total'] += 1
                    results['names_checked'].append(name)
                    if name in survey_names:
                        results['found'] += 1
                    else:
                        results['not_found'].append({
                            'key': key,
                            'name': name,
                            'field': 'all_usda_mappings'
                        })

    return results

def main():
    print("="*80)
    print("base_1〜base_6のsurveyDownload.json検証")
    print("="*80)
    print()

    # surveyDownload.jsonを読み込み
    survey_names = load_survey_database()

    if not survey_names:
        print("❌ surveyDownload.jsonの読み込みに失敗しました")
        return

    print()

    # 各base_*.jsonファイルを検証
    mappings_dir = Path(__file__).parent / "mappings"

    # 全体の統計
    total_stats = {
        'files': 0,
        'total_names': 0,
        'found_names': 0,
        'not_found_names': 0,
        'all_not_found': []
    }

    # base_1からbase_6まで検証
    for i in range(1, 7):
        file_path = mappings_dir / f"base_{i}.json"

        if not file_path.exists():
            print(f"⚠️  {file_path.name} が見つかりません")
            continue

        print(f"\n📋 検証中: {file_path.name}")
        print("-"*40)

        results = validate_base_file(file_path, survey_names)

        if results:
            total_stats['files'] += 1
            total_stats['total_names'] += results['total']
            total_stats['found_names'] += results['found']
            total_stats['not_found_names'] += len(results['not_found'])

            # ファイルごとの結果表示
            percentage = (results['found'] / results['total'] * 100) if results['total'] > 0 else 0
            print(f"  検証項目数: {results['total']}")
            print(f"  ✅ 存在: {results['found']} ({percentage:.1f}%)")

            if results['not_found']:
                print(f"  ❌ 存在しない: {len(results['not_found'])} 件")

                # 最初の5件を表示
                for item in results['not_found'][:5]:
                    print(f"     - {item['key']}: \"{item['name']}\" ({item['field']})")

                if len(results['not_found']) > 5:
                    print(f"     ... 他 {len(results['not_found']) - 5} 件")

                # 全体リストに追加
                for item in results['not_found']:
                    item['file'] = file_path.name
                    total_stats['all_not_found'].append(item)

    # 総合結果
    print("\n" + "="*80)
    print("📊 総合結果")
    print("="*80)

    print(f"  検証ファイル数: {total_stats['files']}")
    print(f"  総検証項目数: {total_stats['total_names']}")
    print(f"  ✅ 存在: {total_stats['found_names']} ({total_stats['found_names']/total_stats['total_names']*100:.1f}%)")
    print(f"  ❌ 存在しない: {total_stats['not_found_names']} ({total_stats['not_found_names']/total_stats['total_names']*100:.1f}%)")

    if total_stats['all_not_found']:
        # ユニークな名前を集計
        unique_names = {}
        for item in total_stats['all_not_found']:
            if item['name'] not in unique_names:
                unique_names[item['name']] = []
            unique_names[item['name']].append(f"{item['file']}:{item['key']}")

        print(f"\n  ユニークな存在しない名前: {len(unique_names)} 件")

        # 頻出する存在しない名前を表示
        sorted_names = sorted(unique_names.items(), key=lambda x: len(x[1]), reverse=True)

        print("\n  頻出する存在しない名前（上位10件）:")
        for name, locations in sorted_names[:10]:
            print(f"    \"{name}\" ({len(locations)} 箇所)")
            for loc in locations[:3]:
                print(f"      - {loc}")
            if len(locations) > 3:
                print(f"      ... 他 {len(locations) - 3} 箇所")

    # 結論
    print("\n" + "="*80)
    if total_stats['not_found_names'] == 0:
        print("✅ すべての名前がsurveyDownload.jsonに存在します！")
    else:
        print(f"❌ {total_stats['not_found_names']} 件の名前がsurveyDownload.jsonに存在しません。")
        print("   マッピングファイルの修正が必要です。")
    print("="*80)

    # エラー詳細をファイルに保存
    if total_stats['all_not_found']:
        error_file = mappings_dir / "base_files_validation_errors.json"
        error_data = {
            'summary': total_stats,
            'not_found_items': total_stats['all_not_found'],
            'unique_names': {name: locs for name, locs in unique_names.items()}
        }

        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, ensure_ascii=False, indent=2)

        print(f"\n📝 エラー詳細を保存: {error_file}")

if __name__ == "__main__":
    main()