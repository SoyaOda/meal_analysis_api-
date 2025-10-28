#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prosciuttoケースのデバッグ

正しい項目「Ham, prosciutto」がデータベースに存在するのに、
なぜ「Ham luncheon meat, loaf type」がマッチしたのかを調査
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline


def main():
    """Prosciuttoのマッチング過程を詳細にデバッグ"""

    print("=" * 80)
    print("Prosciutto マッチングデバッグ")
    print("=" * 80)

    # Initialize pipeline
    index_dir = project_root / "data"
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=40
    )

    # Search for prosciutto
    query_main = "prosciutto"
    query_desc = "sliced"

    print(f"\nQuery: {query_main} | {query_desc}")
    print("-" * 80)

    # Get full results with candidates
    result = pipeline.search(
        query_main=query_main,
        query_descriptors=query_desc,
        return_top_k=10,
        return_candidates=True
    )

    # Check if correct item is in Stage 1 candidates
    candidates = result['stage1_candidates']
    correct_item_fdc = 2705879  # Ham, prosciutto

    print(f"\nStage 1: 候補取得状況 (Top {len(candidates)})")
    print("=" * 80)

    correct_item_found = False
    correct_item_rank = None

    for i, cand in enumerate(candidates, 1):
        if cand['fdc_id'] == correct_item_fdc:
            correct_item_found = True
            correct_item_rank = i
            print(f"\n✅ 正しい項目が{i}位で取得されました!")
            print(f"   {cand['description']}")
            print(f"   Stage1 Score: {cand['score']:.4f}")
            print(f"   Main: {cand['main_name']} | Desc: {cand['descriptors']}")
            break

    if not correct_item_found:
        print(f"\n❌ 正しい項目「Ham, prosciutto」(FDC ID: {correct_item_fdc})は")
        print(f"   Stage 1の上位{len(candidates)}件に含まれていませんでした。")
        print(f"\n   これはStage 1 (Embedding検索)の問題です。")

    # Show top 10 candidates
    print(f"\n" + "-" * 80)
    print(f"Stage 1 Top 10 候補:")
    print("-" * 80)

    for i, cand in enumerate(candidates[:10], 1):
        marker = "✅" if cand['fdc_id'] == correct_item_fdc else "  "
        print(f"{marker} {i}. {cand['description']}")
        print(f"     Stage1 Score: {cand['score']:.4f}")
        print(f"     Main: {cand['main_name']} | Desc: {cand['descriptors']}")
        print(f"     FDC ID: {cand['fdc_id']}")
        print()

    # Show Stage 2 results
    print("=" * 80)
    print("Stage 2: Reranker結果 (Top 10)")
    print("=" * 80)

    for i, item in enumerate(result['top_k'], 1):
        marker = "✅" if item['fdc_id'] == correct_item_fdc else "  "
        print(f"{marker} {i}. {item['description']}")
        print(f"     Rerank Score: {item['rerank_score']:.4f}")
        print(f"     Stage1 Score: {item['stage1_score']:.4f}")
        print(f"     Main: {item['main_name']} | Desc: {item['descriptors']}")
        print(f"     FDC ID: {item['fdc_id']}")
        print()

    # Analysis
    print("=" * 80)
    print("分析結果")
    print("=" * 80)

    if not correct_item_found:
        print(f"\n❌ 問題: Stage 1 (Embedding検索)で正しい項目が取得できていない")
        print(f"\n原因候補:")
        print(f"  1. Embedding modelが「prosciutto」を認識できていない")
        print(f"  2. 「Ham, prosciutto」のembedding vectorが適切でない")
        print(f"  3. Stage1のtop_k=40では不十分（より多くの候補が必要）")
        print(f"\n対策:")
        print(f"  1. Stage1のtop_kを増やす (40 → 100)")
        print(f"  2. クエリの正規化を改善")
        print(f"  3. データベースのembeddingを再生成")
    else:
        print(f"\n✅ Stage 1で正しい項目が{correct_item_rank}位で取得されています")
        print(f"\n問題: Stage 2 (Reranker)で正しい項目が1位にならない")
        print(f"\n対策:")
        print(f"  1. Rerankerのtask instructionを改善")
        print(f"  2. クエリテンプレートの改善")


if __name__ == "__main__":
    main()
