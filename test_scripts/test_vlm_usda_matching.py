#!/usr/bin/env python3
"""
test_vlm_usda_matching.py

VLM出力（freeform_usda形式）からUSDA統合データベースへのマッチングテスト

Usage:
    python test_scripts/test_vlm_usda_matching.py
"""

import json
import re
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
    # 小文字化
    text = text.lower()
    # 特殊文字を除去（アルファベットとスペースのみ）
    text = re.sub(r'[^a-z\s]', ' ', text)
    # 複数スペースを単一スペースに
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
    """
    USDA名から search_name と description を抽出

    形式: "Num. search_name, description1, description2"

    Returns:
        (search_name, description)
    """
    # "Num. " を除去
    if '. ' in usda_name:
        parts = usda_name.split('. ', 1)
        name_part = parts[1] if len(parts) > 1 else usda_name
    else:
        name_part = usda_name

    # コンマで分割
    components = [c.strip() for c in name_part.split(',')]
    search_name = components[0] if components else ""
    description = ', '.join(components[1:]) if len(components) > 1 else ""

    return search_name, description


def build_usda_index(usda_data: Dict) -> List[Dict]:
    """
    USDAデータからインデックスを構築

    Returns:
        各アイテムの情報を含む辞書のリスト
    """
    index = []

    for key, item in usda_data.items():
        if 'default_usda' not in item:
            continue

        usda_name = item['default_usda'].get('name', '')
        search_name, description = parse_usda_name(usda_name)

        # 正規化と語幹化
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
    """
    VLMの search_name と description を USDA データベースにマッチング

    Returns:
        (usda_item, match_type, score) のリスト（スコア降順）
    """
    matches = []

    # VLMクエリの正規化と語幹化
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

    # スコア降順でソート
    matches.sort(key=lambda x: x[2], reverse=True)

    return matches


def test_vlm_usda_matching():
    """メイン処理"""
    print("=" * 80)
    print("VLM → USDA マッチングテスト")
    print("=" * 80)
    print()

    # ファイルパス
    project_root = Path(__file__).parent.parent
    vlm_file = project_root / "test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json"
    usda_file = project_root / "test_scripts/mappings/mappings_final/usda_food_mappings_unified.json"

    # データ読み込み
    print("データ読み込み中...")
    with open(vlm_file, 'r', encoding='utf-8') as f:
        vlm_data = json.load(f)

    with open(usda_file, 'r', encoding='utf-8') as f:
        usda_data = json.load(f)

    print(f"VLM結果: {vlm_data['test_metadata']['total_images']}画像")
    print(f"USDAデータ: {len(usda_data)}アイテム")
    print()

    # USDAインデックス構築
    print("USDAインデックス構築中...")
    usda_index = build_usda_index(usda_data)
    print(f"インデックス完了: {len(usda_index)}アイテム")
    print()

    # マッチング統計
    stats = defaultdict(int)
    total_items = 0
    matched_items = 0

    # 各画像の結果を処理
    for result_idx, result in enumerate(vlm_data['results'][:5], 1):  # 最初の5画像のみテスト
        if not result.get('vlm_response') or 'dishes' not in result['vlm_response']:
            continue

        print("=" * 80)
        print(f"画像 {result_idx}: {result['image_file']}")
        print("=" * 80)

        dishes = result['vlm_response']['dishes']

        for dish_idx, dish in enumerate(dishes, 1):
            print(f"\nDish {dish_idx}:")

            # main_food を処理
            if dish.get('main_food'):
                main_food = dish['main_food']
                search_name = main_food.get('search_name', '')
                description = main_food.get('description')

                print(f"  main_food: {search_name}")
                if description:
                    print(f"    description: {description}")

                total_items += 1
                matches = match_vlm_to_usda(search_name, description, usda_index)

                if matches:
                    matched_items += 1
                    top_match = matches[0]
                    stats[top_match[1]] += 1

                    print(f"  ✅ マッチ: {top_match[0]['display_name']}")
                    print(f"     タイプ: {top_match[1]}, スコア: {top_match[2]}")
                    print(f"     USDA: {top_match[0]['original_name']}")

                    # 上位3件を表示
                    if len(matches) > 1:
                        print(f"  その他の候補:")
                        for match in matches[1:3]:
                            print(f"    - {match[0]['display_name']} ({match[1]}, score={match[2]})")
                else:
                    print(f"  ❌ マッチなし")

            # extras を処理
            if dish.get('extras'):
                for extra_idx, extra in enumerate(dish['extras'], 1):
                    search_name = extra.get('search_name', '')
                    description = extra.get('description')

                    print(f"  extra {extra_idx}: {search_name}")
                    if description:
                        print(f"    description: {description}")

                    total_items += 1
                    matches = match_vlm_to_usda(search_name, description, usda_index)

                    if matches:
                        matched_items += 1
                        top_match = matches[0]
                        stats[top_match[1]] += 1

                        print(f"  ✅ マッチ: {top_match[0]['display_name']}")
                        print(f"     タイプ: {top_match[1]}, スコア: {top_match[2]}")
                    else:
                        print(f"  ❌ マッチなし")

    # サマリー
    print()
    print("=" * 80)
    print("マッチング統計")
    print("=" * 80)
    print(f"総アイテム数: {total_items}")
    print(f"マッチ成功: {matched_items} ({matched_items/total_items*100:.1f}%)")
    print(f"マッチ失敗: {total_items - matched_items} ({(total_items-matched_items)/total_items*100:.1f}%)")
    print()
    print("マッチタイプ別:")
    for match_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {match_type}: {count}件")


if __name__ == "__main__":
    test_vlm_usda_matching()
