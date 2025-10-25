#!/usr/bin/env python3
"""
test_vlm_usda_matching_full.py

VLM出力（freeform_usda形式）からUSDA統合データベースへの完全マッチングテスト
全50画像を処理し、詳細な統計を出力

Usage:
    python test_scripts/test_vlm_usda_matching_full.py [--score-threshold SCORE]
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import nltk
from nltk.stem import PorterStemmer

# Porter Stemmer初期化
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt')

stemmer = PorterStemmer()


def normalize_text(text: str) -> str:
    """テキストを正規化"""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def stem_text(text: str) -> str:
    """テキストを語幹化"""
    normalized = normalize_text(text)
    if not normalized:
        return ""
    tokens = normalized.split()
    stemmed_tokens = [stemmer.stem(token) for token in tokens]
    return ' '.join(stemmed_tokens)


def parse_usda_name(usda_name: str) -> Tuple[str, str]:
    """USDA名から search_name と description を抽出"""
    if '. ' in usda_name:
        parts = usda_name.split('. ', 1)
        name_part = parts[1] if len(parts) > 1 else usda_name
    else:
        name_part = usda_name

    components = [c.strip() for c in name_part.split(',')]
    search_name = components[0] if components else ""
    description = ', '.join(components[1:]) if len(components) > 1 else ""

    return search_name, description


def build_usda_index(usda_data: Dict) -> List[Dict]:
    """USDAデータからインデックスを構築"""
    index = []

    for key, item in usda_data.items():
        if 'default_usda' not in item:
            continue

        usda_name = item['default_usda'].get('name', '')
        search_name, description = parse_usda_name(usda_name)

        normalized_search = normalize_text(search_name)
        stemmed_search = stem_text(search_name)
        normalized_desc = normalize_text(description)
        stemmed_desc = stem_text(description)

        index.append({
            'key': key,
            'display_name': item.get('display_name', ''),
            'role': item.get('role', ''),
            'original_name': usda_name,
            'search_name': search_name,
            'description': description,
            'normalized_search': normalized_search,
            'stemmed_search': stemmed_search,
            'normalized_desc': normalized_desc,
            'stemmed_desc': stemmed_desc,
            'full_normalized': normalize_text(f"{search_name} {description}"),
            'full_stemmed': stem_text(f"{search_name} {description}")
        })

    return index


def match_vlm_to_usda(
    vlm_search_name: str,
    vlm_description: Optional[str],
    usda_index: List[Dict]
) -> List[Tuple[Dict, str, float]]:
    """VLMの search_name と description を USDA データベースにマッチング"""
    matches = []

    vlm_full = f"{vlm_search_name} {vlm_description or ''}".strip()
    vlm_normalized = normalize_text(vlm_full)
    vlm_stemmed = stem_text(vlm_full)
    vlm_search_normalized = normalize_text(vlm_search_name)
    vlm_search_stemmed = stem_text(vlm_search_name)

    for usda_item in usda_index:
        score = 0
        match_type = ""

        # 1. 完全一致（search_name + description）
        if vlm_normalized == usda_item['full_normalized']:
            score = 100
            match_type = "exact_full"

        # 2. 完全一致（search_name のみ）
        elif vlm_search_normalized == usda_item['normalized_search']:
            score = 95
            match_type = "exact_search"

        # 3. 語幹化後の完全一致（search_name + description）
        elif vlm_stemmed == usda_item['full_stemmed']:
            score = 90
            match_type = "stemmed_full"

        # 4. 語幹化後の完全一致（search_name のみ）
        elif vlm_search_stemmed == usda_item['stemmed_search']:
            score = 85
            match_type = "stemmed_search"

        # 5. search_name が USDA の search_name に含まれる
        elif vlm_search_normalized in usda_item['normalized_search']:
            score = 70
            match_type = "search_substring"

        # 6. USDA の search_name が VLM の search_name に含まれる
        elif usda_item['normalized_search'] in vlm_search_normalized:
            score = 65
            match_type = "usda_in_vlm"

        # 7. 語幹化後の部分一致（search_name）
        elif vlm_search_stemmed in usda_item['stemmed_search'] or \
             usda_item['stemmed_search'] in vlm_search_stemmed:
            score = 60
            match_type = "stemmed_substring"

        # 8. description のマッチング
        if vlm_description and usda_item['description']:
            vlm_desc_normalized = normalize_text(vlm_description)
            if vlm_desc_normalized == usda_item['normalized_desc']:
                score += 15
                match_type += "+exact_desc"
            elif vlm_desc_normalized in usda_item['normalized_desc'] or \
                 usda_item['normalized_desc'] in vlm_desc_normalized:
                score += 10
                match_type += "+partial_desc"

        if score > 0:
            matches.append((usda_item, match_type, score))

    matches.sort(key=lambda x: x[2], reverse=True)
    return matches


def test_vlm_usda_matching_full(score_threshold: int = 70):
    """メイン処理"""
    print("=" * 80)
    print("VLM → USDA 完全マッチングテスト")
    print(f"スコア閾値: {score_threshold}")
    print("=" * 80)
    print()

    # ファイルパス
    project_root = Path(__file__).parent.parent
    vlm_file = project_root / "test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json"
    usda_file = project_root / "test_scripts/mappings/mappings_final/usda_food_mappings_unified.json"

    # データ読み込み
    with open(vlm_file, 'r', encoding='utf-8') as f:
        vlm_data = json.load(f)

    with open(usda_file, 'r', encoding='utf-8') as f:
        usda_data = json.load(f)

    print(f"VLM結果: {vlm_data['test_metadata']['total_images']}画像")
    print(f"USDAデータ: {len(usda_data)}アイテム")
    print()

    # USDAインデックス構築
    usda_index = build_usda_index(usda_data)
    print(f"USDAインデックス: {len(usda_index)}アイテム")
    print()

    # マッチング統計
    stats = defaultdict(int)
    total_items = 0
    matched_items = 0
    high_quality_matches = 0  # スコア90以上
    medium_quality_matches = 0  # スコア70-89
    low_quality_matches = 0  # スコア70未満
    failed_matches = []

    # 全画像を処理
    for result_idx, result in enumerate(vlm_data['results'], 1):
        if not result.get('vlm_response') or 'dishes' not in result['vlm_response']:
            continue

        dishes = result['vlm_response']['dishes']

        for dish_idx, dish in enumerate(dishes, 1):
            # main_food を処理
            if dish.get('main_food'):
                main_food = dish['main_food']
                search_name = main_food.get('search_name', '')
                description = main_food.get('description')

                total_items += 1
                matches = match_vlm_to_usda(search_name, description, usda_index)

                if matches and matches[0][2] >= score_threshold:
                    matched_items += 1
                    top_match = matches[0]
                    stats[top_match[1]] += 1

                    # 品質分類
                    if top_match[2] >= 90:
                        high_quality_matches += 1
                    elif top_match[2] >= 70:
                        medium_quality_matches += 1
                else:
                    # マッチ失敗
                    top_match = matches[0] if matches else None
                    failed_matches.append({
                        'image': result['image_file'],
                        'type': 'main_food',
                        'vlm_name': search_name,
                        'vlm_desc': description,
                        'top_match': top_match[0]['display_name'] if top_match else None,
                        'score': top_match[2] if top_match else 0
                    })

            # extras を処理
            if dish.get('extras'):
                for extra in dish['extras']:
                    search_name = extra.get('search_name', '')
                    description = extra.get('description')

                    total_items += 1
                    matches = match_vlm_to_usda(search_name, description, usda_index)

                    if matches and matches[0][2] >= score_threshold:
                        matched_items += 1
                        top_match = matches[0]
                        stats[top_match[1]] += 1

                        if top_match[2] >= 90:
                            high_quality_matches += 1
                        elif top_match[2] >= 70:
                            medium_quality_matches += 1
                    else:
                        top_match = matches[0] if matches else None
                        failed_matches.append({
                            'image': result['image_file'],
                            'type': 'extra',
                            'vlm_name': search_name,
                            'vlm_desc': description,
                            'top_match': top_match[0]['display_name'] if top_match else None,
                            'score': top_match[2] if top_match else 0
                        })

    # サマリー
    print()
    print("=" * 80)
    print("マッチング統計サマリー")
    print("=" * 80)
    print(f"総アイテム数: {total_items}")
    print(f"マッチ成功: {matched_items} ({matched_items/total_items*100:.1f}%)")
    print(f"マッチ失敗: {total_items - matched_items} ({(total_items-matched_items)/total_items*100:.1f}%)")
    print()
    print("品質別マッチング:")
    print(f"  高品質 (スコア90+): {high_quality_matches} ({high_quality_matches/total_items*100:.1f}%)")
    print(f"  中品質 (スコア70-89): {medium_quality_matches} ({medium_quality_matches/total_items*100:.1f}%)")
    print(f"  低品質 (スコア<70): {total_items - matched_items} ({(total_items-matched_items)/total_items*100:.1f}%)")
    print()
    print("マッチタイプ別:")
    for match_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {match_type}: {count}件 ({count/matched_items*100:.1f}%)")

    # 失敗ケースの分析
    if failed_matches:
        print()
        print("=" * 80)
        print(f"マッチ失敗ケース (上位20件)")
        print("=" * 80)
        for idx, failure in enumerate(failed_matches[:20], 1):
            print(f"{idx}. VLM: {failure['vlm_name']}")
            if failure['vlm_desc']:
                print(f"   Description: {failure['vlm_desc']}")
            if failure['top_match']:
                print(f"   最良候補: {failure['top_match']} (score={failure['score']})")
            else:
                print(f"   候補なし")
            print(f"   画像: {failure['image']}")
            print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VLM-USDA完全マッチングテスト")
    parser.add_argument(
        "--score-threshold",
        type=int,
        default=70,
        help="マッチング成功とみなす最小スコア (デフォルト: 70)"
    )
    args = parser.parse_args()

    test_vlm_usda_matching_full(score_threshold=args.score_threshold)
