#!/usr/bin/env python
"""
Survey FoodとFoundation Foodを統合
- Survey Foodを優先（1,372個）
- Foundation Foodから重複なし44個を厳選して追加
- 最終統合マッピングを生成
"""

import json
from pathlib import Path
from collections import defaultdict

survey_draft_dir = Path("/Users/odasoya/meal_analysis_api_2/test_scripts/mappings/mappings_draft/survey_food")
foundation_draft_dir = Path("/Users/odasoya/meal_analysis_api_2/test_scripts/mappings/mappings_draft/foundation_food")
output_dir = Path("/Users/odasoya/meal_analysis_api_2/test_scripts/mappings/mappings_final")

def load_all_survey_mappings():
    """全Survey Foodマッピングを読み込み"""
    all_mappings = {}
    for i in range(1, 12):
        json_path = survey_draft_dir / f"usda_food_mappings{i}.json"
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                mappings = json.load(f)
                all_mappings.update(mappings)
    return all_mappings

def load_foundation_mappings():
    """Foundation Food NEW2マッピングを読み込み"""
    json_path = foundation_draft_dir / "usda_food_mappings_new2.json"
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_keywords(display_name):
    """display_nameからキーワードを抽出"""
    name = display_name.lower()
    # 括弧内を除外
    name = name.split('(')[0].strip()
    keywords = set()
    # カンマで分割
    for part in name.split(','):
        part = part.strip()
        if part:
            keywords.add(part)
    # スペースで分割して主要単語も追加
    for word in name.split():
        if len(word) >= 3:  # 3文字以上の単語
            keywords.add(word)
    return keywords

def detect_overlaps(survey_mappings, foundation_mappings):
    """重複を検出して除外すべきFoundationマッピングを特定"""

    survey_keywords = {}
    for key, mapping in survey_mappings.items():
        display_name = mapping.get('display_name', '')
        keywords = extract_keywords(display_name)
        survey_keywords[key] = keywords

    overlapping_foundation_keys = set()

    for f_key, f_mapping in foundation_mappings.items():
        f_name = f_mapping.get('display_name', '')
        f_keywords = extract_keywords(f_name)

        # Survey Foodに類似するものがあるかチェック
        for s_key, s_keywords in survey_keywords.items():
            common = f_keywords & s_keywords
            if common:
                overlap_ratio = len(common) / min(len(f_keywords), len(s_keywords))
                if overlap_ratio > 0.5:  # 50%以上重複
                    overlapping_foundation_keys.add(f_key)
                    break

    return overlapping_foundation_keys

def filter_foundation_mappings(foundation_mappings, overlapping_keys):
    """重複なしのFoundationマッピングを抽出し、さらに厳選"""

    # 重複なしマッピング
    unique_foundation = {k: v for k, v in foundation_mappings.items()
                         if k not in overlapping_keys}

    # 厳選基準: ingredient_only または either で統合数が多いもの
    selected = {}

    for key, mapping in unique_foundation.items():
        display_name = mapping.get('display_name', '')
        role = mapping.get('role', '')
        count = len(mapping.get('all_usda_mappings', []))

        # 優先度の高いカテゴリ
        name_lower = display_name.lower()

        # 必ず追加（ingredient_onlyまたは高統合率）
        priority_add = False

        if role == 'ingredient_only':
            priority_add = True  # ingredient_onlyは全て追加
        elif count >= 3 and role == 'either':
            priority_add = True  # 統合数3以上のeitherも追加

        # 特定カテゴリは除外（Surveyと重複しやすい）
        exclude_categories = [
            'pork', 'beef', 'chicken', 'fish', 'salmon', 'tuna',
            'rice', 'pasta', 'noodle',
            'apple', 'banana', 'orange', 'grape', 'mango'
        ]

        should_exclude = any(cat in name_lower for cat in exclude_categories)

        if priority_add and not should_exclude:
            selected[key] = mapping
        elif not should_exclude and count >= 5:
            # 統合数5以上は強制追加（高価値マッピング）
            selected[key] = mapping

    return selected

def merge_mappings():
    """マッピングを統合"""

    print("="*80)
    print("Survey Food + Foundation Food 統合処理")
    print("="*80)
    print()

    # 1. Survey Foodを読み込み
    print("📊 1. Survey Foodマッピング読み込み")
    print("-"*80)
    survey_mappings = load_all_survey_mappings()
    survey_foods = sum(len(m.get('all_usda_mappings', [])) for m in survey_mappings.values())
    print(f"  読み込み完了: {len(survey_mappings)}個のマッピング")
    print(f"  総食品数: {survey_foods}個")
    print(f"  統合率: {survey_foods/len(survey_mappings):.2f}")
    print()

    # 2. Foundation Foodを読み込み
    print("📊 2. Foundation Food NEW2マッピング読み込み")
    print("-"*80)
    foundation_mappings = load_foundation_mappings()
    foundation_foods = sum(len(m.get('all_usda_mappings', [])) for m in foundation_mappings.values())
    print(f"  読み込み完了: {len(foundation_mappings)}個のマッピング")
    print(f"  総食品数: {foundation_foods}個")
    print(f"  統合率: {foundation_foods/len(foundation_mappings):.2f}")
    print()

    # 3. 重複検出
    print("🔍 3. 重複検出")
    print("-"*80)
    overlapping_keys = detect_overlaps(survey_mappings, foundation_mappings)
    print(f"  重複検出: {len(overlapping_keys)}個のFoundationマッピングが重複")
    print(f"  重複なし: {len(foundation_mappings) - len(overlapping_keys)}個")
    print()

    # 4. Foundation厳選
    print("✅ 4. Foundation厳選（ingredient_only優先）")
    print("-"*80)
    selected_foundation = filter_foundation_mappings(foundation_mappings, overlapping_keys)
    selected_foods = sum(len(m.get('all_usda_mappings', [])) for m in selected_foundation.values())
    print(f"  厳選後: {len(selected_foundation)}個のマッピング")
    print(f"  総食品数: {selected_foods}個")
    print()

    # 厳選されたマッピングの詳細表示
    print("  【厳選されたFoundationマッピング】")
    print()

    # roleごとに分類
    by_role = defaultdict(list)
    for key, mapping in selected_foundation.items():
        role = mapping.get('role', 'unknown')
        count = len(mapping.get('all_usda_mappings', []))
        by_role[role].append({
            'key': key,
            'display_name': mapping.get('display_name', ''),
            'count': count
        })

    for role in ['ingredient_only', 'either', 'is_base']:
        if role in by_role:
            items = sorted(by_role[role], key=lambda x: x['count'], reverse=True)
            print(f"  [{role.upper()}] ({len(items)}個)")
            for item in items:
                print(f"    - {item['display_name']:45s} ({item['count']:2d}個統合)")
            print()

    # 5. 統合
    print("🔗 5. 統合実行")
    print("-"*80)

    final_mappings = {}

    # Survey Foodを追加
    final_mappings.update(survey_mappings)
    print(f"  Survey追加: {len(survey_mappings)}個")

    # Foundationを追加（キー重複チェック）
    foundation_added = 0
    foundation_skipped = 0

    for key, mapping in selected_foundation.items():
        if key in final_mappings:
            # キー重複の場合は接頭辞を付ける
            new_key = f"foundation_{key}"
            final_mappings[new_key] = mapping
            foundation_added += 1
            print(f"  ⚠️ キー重複: {key} → {new_key}")
        else:
            final_mappings[key] = mapping
            foundation_added += 1

    print(f"  Foundation追加: {foundation_added}個")
    print()

    # 6. 統計情報
    print("📈 6. 統合後の統計")
    print("-"*80)

    total_mappings = len(final_mappings)
    total_foods = sum(len(m.get('all_usda_mappings', [])) for m in final_mappings.values())
    avg_consolidation = total_foods / total_mappings

    # roleの分布
    role_dist = defaultdict(int)
    for mapping in final_mappings.values():
        role = mapping.get('role', 'unknown')
        role_dist[role] += 1

    print(f"  総マッピング数: {total_mappings}個")
    print(f"  総食品数: {total_foods}個")
    print(f"  統合率: {avg_consolidation:.2f}食品/マッピング")
    print()

    print("  Role分布:")
    for role in ['is_base', 'either', 'ingredient_only', 'sauce_only', 'unknown']:
        if role in role_dist:
            percentage = role_dist[role] / total_mappings * 100
            print(f"    {role:20s}: {role_dist[role]:4d}個 ({percentage:5.1f}%)")
    print()

    # 7. ファイル出力
    print("💾 7. ファイル出力")
    print("-"*80)

    output_dir.mkdir(parents=True, exist_ok=True)

    # JSONファイル
    output_json = output_dir / "usda_food_mappings_unified.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(final_mappings, f, ensure_ascii=False, indent=2)

    print(f"  ✅ {output_json}")
    print(f"     {total_mappings}個のマッピング, {total_foods}個の食品")
    print()

    # 統計レポート
    report_path = output_dir / "merge_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("Survey Food + Foundation Food 統合レポート\n")
        f.write("="*80 + "\n\n")

        f.write("【構成】\n")
        f.write(f"  Survey Food:     {len(survey_mappings):4d}個のマッピング ({survey_foods:5d}食品)\n")
        f.write(f"  Foundation Food: {foundation_added:4d}個のマッピング ({selected_foods:5d}食品)\n")
        f.write(f"  合計:            {total_mappings:4d}個のマッピング ({total_foods:5d}食品)\n\n")

        f.write("【統計】\n")
        f.write(f"  統合率: {avg_consolidation:.2f}食品/マッピング\n\n")

        f.write("【Role分布】\n")
        for role in ['is_base', 'either', 'ingredient_only', 'sauce_only', 'unknown']:
            if role in role_dist:
                percentage = role_dist[role] / total_mappings * 100
                f.write(f"  {role:20s}: {role_dist[role]:4d}個 ({percentage:5.1f}%)\n")
        f.write("\n")

        f.write("【Foundationから追加されたマッピング】\n\n")
        for role in ['ingredient_only', 'either', 'is_base']:
            if role in by_role:
                f.write(f"[{role.upper()}]\n")
                items = sorted(by_role[role], key=lambda x: x['count'], reverse=True)
                for item in items:
                    f.write(f"  - {item['display_name']:45s} ({item['count']:2d}個統合)\n")
                f.write("\n")

    print(f"  ✅ {report_path}")
    print()

    # 8. 検証
    print("✅ 8. 検証")
    print("-"*80)

    # キーの重複チェック
    all_keys = list(final_mappings.keys())
    unique_keys = set(all_keys)

    if len(all_keys) == len(unique_keys):
        print("  ✅ キーの重複なし")
    else:
        print(f"  ❌ キーの重複あり: {len(all_keys) - len(unique_keys)}件")

    # all_usda_mappingsの形式チェック
    invalid_count = 0
    for key, mapping in final_mappings.items():
        all_usda = mapping.get('all_usda_mappings', [])
        if not isinstance(all_usda, list):
            invalid_count += 1
        elif all_usda and not isinstance(all_usda[0], str):
            invalid_count += 1

    if invalid_count == 0:
        print("  ✅ all_usda_mappings形式チェック: 全て正常")
    else:
        print(f"  ❌ all_usda_mappings形式エラー: {invalid_count}件")

    print()
    print("="*80)
    print("💡 統合完了")
    print("="*80)
    print()
    print(f"最終マッピング: {output_json}")
    print(f"  - {total_mappings}個のマッピング")
    print(f"  - {total_foods}個の食品")
    print(f"  - 統合率 {avg_consolidation:.2f}")
    print()
    print("="*80)

if __name__ == "__main__":
    merge_mappings()
