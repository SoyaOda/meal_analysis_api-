#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prosciuttoケースの最終デバッグ

実際の評価と同じ条件（top_k=40）で、Stage 1とStage 2の両方を確認
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline


def main():
    """実際の評価条件でprosciuttoをデバッグ"""

    print("=" * 80)
    print("Prosciutto 最終デバッグ（実際の評価条件: top_k=40）")
    print("=" * 80)

    # Initialize pipeline (same as actual evaluation)
    index_dir = project_root / "data"
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=40  # 実際の評価と同じ
    )

    # Query (same as actual evaluation)
    query_main = "prosciutto"
    query_desc = "sliced"

    print(f"\nQuery: {query_main} | {query_desc}")
    print(f"Stage1 top_k: 40 (実際の評価と同じ)")
    print("-" * 80)

    # Get full results with candidates
    result = pipeline.search(
        query_main=query_main,
        query_descriptors=query_desc,
        return_top_k=10,
        return_candidates=True  # Stage 1候補も取得
    )

    candidates = result['stage1_candidates']
    correct_item_fdc = 2705879  # Ham, prosciutto

    # Check Stage 1
    print(f"\n{'='*80}")
    print(f"Stage 1: 候補取得（top_k=40）")
    print("=" * 80)

    found_in_stage1 = False
    stage1_rank = None
    stage1_score = None

    for i, cand in enumerate(candidates, 1):
        if cand['fdc_id'] == correct_item_fdc:
            found_in_stage1 = True
            stage1_rank = i
            stage1_score = cand['score']
            break

    if found_in_stage1:
        print(f"\n✅ Stage 1で{stage1_rank}位に取得されました")
        print(f"   Ham, prosciutto")
        print(f"   Embeddingスコア: {stage1_score:.6f}")
    else:
        print(f"\n❌ Stage 1の上位40件に含まれていません")

    # Show top 10 from Stage 1
    print(f"\n{'='*80}")
    print(f"Stage 1 Top 10")
    print("=" * 80)
    print(f"\n{'順位':<4} {'スコア':<10} {'項目':<50}")
    print("-" * 80)

    for i, cand in enumerate(candidates[:10], 1):
        marker = "✅" if cand['fdc_id'] == correct_item_fdc else "  "
        print(f"{marker} {i:<2} {cand['score']:.6f}   {cand['description'][:50]}")

    # Check Stage 2
    print(f"\n{'='*80}")
    print(f"Stage 2: Reranker結果")
    print("=" * 80)

    found_in_stage2 = False
    stage2_rank = None
    stage2_score = None

    for i, item in enumerate(result['top_k'], 1):
        if item['fdc_id'] == correct_item_fdc:
            found_in_stage2 = True
            stage2_rank = i
            stage2_score = item['rerank_score']
            break

    if found_in_stage2:
        print(f"\n✅ Stage 2で{stage2_rank}位になりました")
        print(f"   Ham, prosciutto")
        print(f"   Rerankスコア: {stage2_score:.6f}")
    else:
        print(f"\n❌ Stage 2のTop 10に含まれていません")

    # Show top 10 from Stage 2
    print(f"\n{'='*80}")
    print(f"Stage 2 Top 10")
    print("=" * 80)
    print(f"\n{'順位':<4} {'Rerank':<10} {'Stage1':<10} {'項目':<40}")
    print("-" * 80)

    for i, item in enumerate(result['top_k'], 1):
        marker = "✅" if item['fdc_id'] == correct_item_fdc else "  "
        print(f"{marker} {i:<2} {item['rerank_score']:.6f}   {item['stage1_score']:.6f}   {item['description'][:40]}")

    # Final analysis
    print(f"\n{'='*80}")
    print(f"最終分析")
    print("=" * 80)

    if found_in_stage1:
        print(f"\n【Stage 1】")
        print(f"  ✅ Ham, prosciutto: {stage1_rank}位 (スコア: {stage1_score:.6f})")
        print(f"  → Stage 1は正しく機能している")

        if found_in_stage2:
            print(f"\n【Stage 2】")
            print(f"  ✅ Ham, prosciutto: {stage2_rank}位 (スコア: {stage2_score:.6f})")
            if stage2_rank == 1:
                print(f"  → Stage 2も正しく機能している")
            else:
                print(f"  ⚠️  Stage 2で順位が下がった ({stage1_rank}位 → {stage2_rank}位)")
                print(f"  → Rerankerの問題")
        else:
            print(f"\n【Stage 2】")
            print(f"  ❌ Top 10圏外")
            print(f"  → Rerankerが「Ham, prosciutto」を低く評価")
            print(f"  → Rerankerの深刻な問題")
    else:
        print(f"\n【Stage 1】")
        print(f"  ❌ Ham, prosciutto: 40位圏外")
        print(f"  → Stage 1 (Embedding検索)の問題")
        print(f"\n【対策】")
        print(f"  1. BM25+Embeddingハイブリッド検索")
        print(f"  2. Stage1 top_k増加 (40 → 60-100)")
        print(f"  3. クエリ拡張（同義語辞書）")

    # Show best match
    best = result['best_match']
    print(f"\n{'='*80}")
    print(f"実際にマッチした項目")
    print("=" * 80)
    print(f"\n  {best['description']}")
    print(f"  FDC ID: {best['fdc_id']}")
    print(f"  Rerank Score: {best['rerank_score']:.6f}")
    print(f"  Stage1 Score: {best['stage1_score']:.6f}")

    print(f"\n{'='*80}")
    print(f"結論")
    print("=" * 80)

    if not found_in_stage1:
        print(f"\n根本原因: Embedding検索の限界")
        print(f"  'prosciutto'を含む項目が上位40件に入らない")
        print(f"\n推奨対策: BM25+Embeddingハイブリッド検索 ⭐⭐⭐⭐⭐")
        print(f"  BM25で'prosciutto'を含む項目に高スコアを保証")
    elif not found_in_stage2 or (found_in_stage2 and stage2_rank > 1):
        print(f"\n根本原因: Rerankerの問題")
        print(f"  Stage 1で正しく取得されているが、Rerankerで低評価")
        print(f"\n推奨対策: Rerankerのチューニング ⭐⭐⭐⭐⭐")
        print(f"  1. Task instructionの改善")
        print(f"  2. クエリテンプレートの最適化")
        print(f"  3. Reranker modelの変更検討")


if __name__ == "__main__":
    main()
