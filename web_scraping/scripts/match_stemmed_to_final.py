#!/usr/bin/env python3
"""
db/mynetdiary_converted_tool_calls_list_stemmed.jsonと
processed_data/all_foods_final_1152.jsonの対応を確認するスクリプト
"""

import json
import re
from pathlib import Path
from difflib import SequenceMatcher


def normalize_for_matching(name: str) -> str:
    """マッチング用に食材名を正規化"""
    # 小文字化
    normalized = name.lower().strip()

    # カロリー情報を削除
    normalized = re.sub(r'\s+\d+cals?$', '', normalized)

    # 改行削除
    normalized = normalized.replace('\n', ' ')

    # 連続スペースを1つに
    normalized = re.sub(r'\s+', ' ', normalized)

    return normalized


def extract_key_words(text: str) -> set:
    """テキストからキーワードを抽出"""
    # 小文字化して単語分割
    words = text.lower().split()

    # ストップワードを除外
    stop_words = {'with', 'without', 'or', 'and', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for'}

    return {w for w in words if w not in stop_words and len(w) > 2}


def calculate_match_score(stemmed_food: dict, final_food: dict) -> dict:
    """
    2つの食材のマッチスコアを計算

    マッチング基準:
    1. original_nameの類似度
    2. キーワードの重複度
    3. カテゴリの一致（あれば）
    """
    stemmed_name = stemmed_food['original_name']
    final_name = final_food['food_name']

    # 正規化
    norm_stemmed = normalize_for_matching(stemmed_name)
    norm_final = normalize_for_matching(final_name)

    # 1. 完全一致チェック
    if norm_stemmed == norm_final:
        return {
            'score': 1.0,
            'match_type': 'exact',
            'details': 'Complete match'
        }

    # 2. 文字列類似度
    similarity = SequenceMatcher(None, norm_stemmed, norm_final).ratio()

    # 3. キーワード一致度
    stemmed_keywords = extract_key_words(norm_stemmed)
    final_keywords = extract_key_words(norm_final)

    if stemmed_keywords and final_keywords:
        keyword_overlap = len(stemmed_keywords & final_keywords) / len(stemmed_keywords | final_keywords)
    else:
        keyword_overlap = 0

    # 総合スコア（類似度70% + キーワード30%）
    total_score = similarity * 0.7 + keyword_overlap * 0.3

    return {
        'score': total_score,
        'match_type': 'partial' if total_score > 0.6 else 'weak',
        'details': {
            'similarity': similarity,
            'keyword_overlap': keyword_overlap,
            'stemmed_keywords': list(stemmed_keywords),
            'final_keywords': list(final_keywords),
            'common_keywords': list(stemmed_keywords & final_keywords)
        }
    }


def main():
    print("🔍 Stemmed Database → Final JSON 対応確認システム")
    print("=" * 80)

    # ファイル読み込み
    stemmed_file = Path('/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed.json')
    final_file = Path('processed_data/all_foods_final_1152.json')

    with open(stemmed_file, 'r', encoding='utf-8') as f:
        stemmed_data = json.load(f)

    with open(final_file, 'r', encoding='utf-8') as f:
        final_data = json.load(f)

    final_foods = final_data['foods']

    print(f"📋 Stemmed Database: {len(stemmed_data)}個")
    print(f"📋 Final JSON: {len(final_foods)}個")

    # 対応チェック
    print(f"\n🔍 対応チェック実行中...")
    print("=" * 80)

    matches = []
    exact_matches = 0
    partial_matches = 0
    weak_matches = 0
    no_matches = 0

    for stemmed_food in stemmed_data:
        best_match = None
        best_score = 0

        # 全ての最終食材と比較
        for final_food in final_foods:
            match_result = calculate_match_score(stemmed_food, final_food)

            if match_result['score'] > best_score:
                best_score = match_result['score']
                best_match = {
                    'stemmed_food': stemmed_food,
                    'final_food': final_food,
                    'match_info': match_result
                }

        # マッチ分類
        if best_score >= 0.95:
            exact_matches += 1
            match_category = 'exact'
        elif best_score >= 0.6:
            partial_matches += 1
            match_category = 'partial'
        elif best_score >= 0.3:
            weak_matches += 1
            match_category = 'weak'
        else:
            no_matches += 1
            match_category = 'none'

        matches.append({
            **best_match,
            'category': match_category
        })

    # 結果表示
    print(f"\n📊 マッチング結果:")
    print(f"   ✅ 完全一致: {exact_matches}個 ({exact_matches/len(stemmed_data)*100:.1f}%)")
    print(f"   🔶 部分一致: {partial_matches}個 ({partial_matches/len(stemmed_data)*100:.1f}%)")
    print(f"   ⚠️  弱い一致: {weak_matches}個 ({weak_matches/len(stemmed_data)*100:.1f}%)")
    print(f"   ❌ 未一致: {no_matches}個 ({no_matches/len(stemmed_data)*100:.1f}%)")

    # サンプル表示
    print(f"\n📋 完全一致サンプル（最初の5個）:")
    exact_samples = [m for m in matches if m['category'] == 'exact'][:5]
    for i, match in enumerate(exact_samples, 1):
        print(f"\n{i}. Stemmed: {match['stemmed_food']['original_name']}")
        print(f"   Final: {match['final_food']['food_name']}")
        print(f"   スコア: {match['match_info']['score']:.3f}")

    print(f"\n📋 部分一致サンプル（最初の5個）:")
    partial_samples = [m for m in matches if m['category'] == 'partial'][:5]
    for i, match in enumerate(partial_samples, 1):
        print(f"\n{i}. Stemmed: {match['stemmed_food']['original_name']}")
        print(f"   Final: {match['final_food']['food_name']}")
        print(f"   スコア: {match['match_info']['score']:.3f}")
        if 'common_keywords' in match['match_info']['details']:
            print(f"   共通キーワード: {', '.join(match['match_info']['details']['common_keywords'])}")

    print(f"\n📋 未一致サンプル（最初の10個）:")
    no_match_samples = [m for m in matches if m['category'] == 'none'][:10]
    for i, match in enumerate(no_match_samples, 1):
        print(f"\n{i}. Stemmed: {match['stemmed_food']['original_name']}")
        print(f"   最も近い候補: {match['final_food']['food_name']}")
        print(f"   スコア: {match['match_info']['score']:.3f}")

    # レポート保存
    output_file = 'processed_data/stemmed_to_final_correspondence.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_stemmed_foods': len(stemmed_data),
                'total_final_foods': len(final_foods),
                'exact_matches': exact_matches,
                'partial_matches': partial_matches,
                'weak_matches': weak_matches,
                'no_matches': no_matches,
                'match_rate': (exact_matches + partial_matches) / len(stemmed_data) * 100
            },
            'matches': matches
        }, f, ensure_ascii=False, indent=2)

    print(f"\n" + "=" * 80)
    print(f"💾 詳細レポート保存: {output_file}")
    print(f"\n📈 総合一致率: {(exact_matches + partial_matches) / len(stemmed_data) * 100:.1f}%")
    print(f"   （完全一致 + 部分一致）")


if __name__ == "__main__":
    main()
