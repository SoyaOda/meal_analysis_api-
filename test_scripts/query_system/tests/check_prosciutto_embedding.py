#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ham, prosciuttoの実際のEmbeddingスコアを確認

なぜ40位圏外なのか？
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline


def main():
    """Ham, prosciuttoの実際のスコアを確認"""

    print("=" * 80)
    print("Ham, prosciutto の実際のEmbeddingスコアを確認")
    print("=" * 80)

    # Initialize pipeline
    index_dir = project_root / "data"
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=100  # 100まで取得して確認
    )

    # Search for prosciutto
    query_main = "prosciutto"
    query_desc = "sliced"

    print(f"\nQuery: {query_main} | {query_desc}")
    print("-" * 80)

    # Get top 100 candidates
    result = pipeline.search(
        query_main=query_main,
        query_descriptors=query_desc,
        return_top_k=10,
        return_candidates=True
    )

    candidates = result['stage1_candidates']
    correct_item_fdc = 2705879  # Ham, prosciutto

    # Find Ham, prosciutto
    print(f"\nStage 1: 上位100件の候補を確認")
    print("=" * 80)

    found = False
    rank = None
    score = None

    for i, cand in enumerate(candidates, 1):
        if cand['fdc_id'] == correct_item_fdc:
            found = True
            rank = i
            score = cand['score']
            print(f"\n✅ 見つかりました！")
            print(f"   順位: {i}位")
            print(f"   Embeddingスコア: {score:.6f}")
            print(f"   項目: {cand['description']}")
            print(f"   Main: {cand['main_name']} | Desc: {cand['descriptors']}")
            break

    if not found:
        print(f"\n❌ 上位100件にも含まれていません")
        print(f"   「Ham, prosciutto」のEmbeddingスコアは非常に低い")

    # Show top 50 for analysis
    print(f"\n" + "=" * 80)
    print(f"Top 50 候補のスコア分布")
    print("=" * 80)

    print(f"\n{'順位':<4} {'スコア':<10} {'項目':<50}")
    print("-" * 80)

    for i, cand in enumerate(candidates[:50], 1):
        marker = "✅" if cand['fdc_id'] == correct_item_fdc else "  "
        print(f"{marker} {i:<2} {cand['score']:.6f}   {cand['description'][:50]}")

    # Score distribution analysis
    print(f"\n" + "=" * 80)
    print(f"スコア分布の分析")
    print("=" * 80)

    top10_min = candidates[9]['score'] if len(candidates) >= 10 else 0
    top20_min = candidates[19]['score'] if len(candidates) >= 20 else 0
    top40_min = candidates[39]['score'] if len(candidates) >= 40 else 0
    top100_min = candidates[99]['score'] if len(candidates) >= 100 else 0

    print(f"\nTop 10の最低スコア: {top10_min:.6f}")
    print(f"Top 20の最低スコア: {top20_min:.6f}")
    print(f"Top 40の最低スコア: {top40_min:.6f}")
    print(f"Top 100の最低スコア: {top100_min:.6f}")

    if found:
        print(f"\nHam, prosciuttoのスコア: {score:.6f}")
        print(f"  Top 40との差: {score - top40_min:.6f}")
        print(f"  Top 100との差: {score - top100_min:.6f}")

    # Analysis
    print(f"\n" + "=" * 80)
    print(f"分析")
    print("=" * 80)

    if found and rank <= 100:
        print(f"\n【状況】")
        print(f"  Ham, prosciutto: {rank}位 (スコア: {score:.6f})")
        print(f"  Top 40ライン: {top40_min:.6f}")
        print(f"  差分: {abs(score - top40_min):.6f}")

        if rank > 40:
            print(f"\n【問題】")
            print(f"  わずか{abs(score - top40_min):.6f}の差で40位圏外")
            print(f"  → Stage1のtop_kを少し増やすだけで解決可能")
            print(f"\n【推奨】")
            print(f"  Stage1 top_k: 40 → {max(60, rank + 10)} に増やす")
            print(f"  コスト増加: {((max(60, rank + 10) - 40) / 40 * 100):.0f}%")
    else:
        print(f"\n【深刻な問題】")
        print(f"  Ham, prosciuttoは上位100件にも入っていない")
        print(f"  Embeddingの根本的な問題の可能性")
        print(f"\n【原因候補】")
        print(f"  1. 'Ham, prosciutto'の記述形式の問題")
        print(f"     'Ham'が前 → 'prosciutto'の重みが低い")
        print(f"  2. Embedding modelの語彙不足")
        print(f"     'prosciutto'を適切に認識できていない")
        print(f"  3. データベース構築時のembeddingエラー")

    print(f"\n" + "=" * 80)
    print(f"BM25+Embeddingの必要性")
    print("=" * 80)

    if found and rank > 40 and rank <= 100:
        print(f"\n【短期対策】")
        print(f"  Stage1 top_k増加でも解決可能")
        print(f"  40 → 60-100")
        print(f"\n【長期対策】")
        print(f"  BM25+Embeddingハイブリッドで確実に解決")
        print(f"  'prosciutto'を含む項目に高スコア保証")
    else:
        print(f"\n【必須対策】")
        print(f"  BM25+Embeddingハイブリッドが必須")
        print(f"  top_k増加だけでは不十分")
        print(f"  BM25でexact matchを保証する必要あり")


if __name__ == "__main__":
    main()
