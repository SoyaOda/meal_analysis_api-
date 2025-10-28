#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Two-stream searchのデバッグ

Ham, prosciuttoがmain/full検索でそれぞれ何位なのかを確認
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.index.searcher import IndexSearcher


def main():
    """Two-stream searchの動作を詳細に確認"""

    print("=" * 80)
    print("Two-Stream Search デバッグ")
    print("=" * 80)

    # Initialize searcher
    index_dir = project_root / "data"
    searcher = IndexSearcher(
        index_dir=str(index_dir),
        device="cpu",
        weight_main=0.6,
        weight_full=0.4
    )

    # Query
    query_main = "prosciutto"
    query_descriptors = "sliced"

    print(f"\nQuery: {query_main} | {query_descriptors}")
    print(f"Weights: main={searcher.weight_main}, full={searcher.weight_full}")
    print("-" * 80)

    # Build query texts
    from src.preprocessing.text_normalizer import build_main_only_text, build_full_text, normalize_text
    import numpy as np

    text_main = normalize_text(build_main_only_text(query_main))
    text_full = normalize_text(build_full_text(query_main, query_descriptors))

    print(f"\nQuery texts:")
    print(f"  Main-only: '{text_main}'")
    print(f"  Full:      '{text_full}'")

    # Encode queries
    emb_main = searcher.embedding_model.encode(text_main, batch_size=1, show_progress_bar=False)
    emb_full = searcher.embedding_model.encode(text_full, batch_size=1, show_progress_bar=False)

    # Normalize
    emb_main = emb_main / np.linalg.norm(emb_main, axis=1, keepdims=True)
    emb_full = emb_full / np.linalg.norm(emb_full, axis=1, keepdims=True)

    # Search with k=100 to find Ham, prosciutto
    k_search = 100

    scores_main, indices_main = searcher.index_main.search(emb_main, k_search)
    scores_full, indices_full = searcher.index_full.search(emb_full, k_search)

    # Find Ham, prosciutto
    correct_fdc = 2705879

    # Find in metadata
    correct_idx = None
    for i, item in enumerate(searcher.items):
        if item.get('fdc_id') == correct_fdc:
            correct_idx = i
            break

    print(f"\n{'='*80}")
    print(f"Ham, prosciutto の検索結果")
    print("=" * 80)

    if correct_idx is None:
        print(f"\n❌ Ham, prosciutto (FDC {correct_fdc}) がmetadataに見つかりません")
        return

    print(f"\nDatabase index: {correct_idx}")
    print(f"Description: {searcher.items[correct_idx]['description']}")

    # Check main search
    main_rank = None
    main_score = None

    for i, idx in enumerate(indices_main[0], 1):
        if idx == correct_idx:
            main_rank = i
            main_score = scores_main[0][i-1]
            break

    if main_rank:
        print(f"\n✅ Main-only検索: {main_rank}位 (スコア: {main_score:.6f})")
    else:
        print(f"\n❌ Main-only検索: 100位圏外")

    # Check full search
    full_rank = None
    full_score = None

    for i, idx in enumerate(indices_full[0], 1):
        if idx == correct_idx:
            full_rank = i
            full_score = scores_full[0][i-1]
            break

    if full_rank:
        print(f"✅ Full検索: {full_rank}位 (スコア: {full_score:.6f})")
    else:
        print(f"❌ Full検索: 100位圏外")

    # Calculate combined score
    if main_score is not None and full_score is not None:
        combined_score = searcher.weight_main * main_score + searcher.weight_full * full_score
        print(f"\n📊 Combined score: {combined_score:.6f}")
        print(f"   = {searcher.weight_main} × {main_score:.6f} + {searcher.weight_full} × {full_score:.6f}")
    elif main_score is not None:
        combined_score = searcher.weight_main * main_score
        print(f"\n📊 Combined score: {combined_score:.6f} (main-only)")
    elif full_score is not None:
        combined_score = searcher.weight_full * full_score
        print(f"\n📊 Combined score: {combined_score:.6f} (full-only)")
    else:
        print(f"\n❌ Combined scoreを計算できません（両方とも100位圏外）")
        return

    # Show top 10 from each search
    print(f"\n{'='*80}")
    print(f"Main-only検索 Top 10")
    print("=" * 80)

    for i in range(10):
        idx = indices_main[0][i]
        score = scores_main[0][i]
        item = searcher.items[idx]
        marker = "✅" if idx == correct_idx else "  "
        print(f"{marker} {i+1}. {item['description'][:50]:50} {score:.6f}")

    print(f"\n{'='*80}")
    print(f"Full検索 Top 10")
    print("=" * 80)

    for i in range(10):
        idx = indices_full[0][i]
        score = scores_full[0][i]
        item = searcher.items[idx]
        marker = "✅" if idx == correct_idx else "  "
        print(f"{marker} {i+1}. {item['description'][:50]:50} {score:.6f}")

    # Test with different top_k values
    print(f"\n{'='*80}")
    print(f"Different top_k values")
    print("=" * 80)

    for top_k in [40, 60, 80, 100]:
        result = searcher.search(
            query_main=query_main,
            query_descriptors=query_descriptors,
            top_k=top_k
        )

        found = any(c['fdc_id'] == correct_fdc for c in result)
        k_search_used = min(top_k * 2, searcher.index_main.ntotal)

        if found:
            rank = next(i+1 for i, c in enumerate(result) if c['fdc_id'] == correct_fdc)
            score = next(c['score'] for c in result if c['fdc_id'] == correct_fdc)
            print(f"  top_k={top_k:3} (k_search={k_search_used:3}): ✅ {rank}位 (score: {score:.6f})")
        else:
            print(f"  top_k={top_k:3} (k_search={k_search_used:3}): ❌ 圏外")

    print(f"\n{'='*80}")
    print(f"結論")
    print("=" * 80)

    print(f"\nHam, prosciutto の検索状況:")
    if main_rank:
        print(f"  Main-only: {main_rank}位 / {k_search}")
    else:
        print(f"  Main-only: 100位圏外")

    if full_rank:
        print(f"  Full:      {full_rank}位 / {k_search}")
    else:
        print(f"  Full:      100位圏外")

    print(f"\ntop_k=40の場合:")
    print(f"  k_search = 80")
    if main_rank and main_rank <= 80:
        print(f"  Main-only検索で取得される: ✅ ({main_rank}位 <= 80)")
    else:
        print(f"  Main-only検索で取得されない: ❌ ({main_rank if main_rank else '100+'}位 > 80)")

    if full_rank and full_rank <= 80:
        print(f"  Full検索で取得される: ✅ ({full_rank}位 <= 80)")
    else:
        print(f"  Full検索で取得されない: ❌ ({full_rank if full_rank else '100+'}位 > 80)")


if __name__ == "__main__":
    main()
