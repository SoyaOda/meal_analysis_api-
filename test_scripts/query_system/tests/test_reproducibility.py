#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
検索結果の再現性テスト

同じクエリを5回実行して、結果が一致するか確認
"""

import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline


def run_single_search(pipeline, query_main, query_desc, run_number):
    """1回の検索を実行"""
    result = pipeline.search(
        query_main=query_main,
        query_descriptors=query_desc,
        return_top_k=5,
        return_candidates=True
    )

    candidates = result['stage1_candidates']
    top_k = result['top_k']

    return {
        'run': run_number,
        'stage1_top5_fdcs': [c['fdc_id'] for c in candidates[:5]],
        'stage1_top5_scores': [c['score'] for c in candidates[:5]],
        'stage2_top5_fdcs': [t['fdc_id'] for t in top_k[:5]],
        'stage2_top5_scores': [t['rerank_score'] for t in top_k[:5]],
        'best_match_fdc': result['best_match']['fdc_id'],
        'best_match_score': result['best_match']['rerank_score']
    }


def main():
    """再現性テスト"""

    print("=" * 80)
    print("検索結果の再現性テスト")
    print("=" * 80)

    # Initialize pipeline
    index_dir = project_root / "data"
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=40
    )

    # Test query
    query_main = "prosciutto"
    query_desc = "sliced"

    print(f"\nQuery: {query_main} | {query_desc}")
    print(f"Stage1 top_k: 40")
    print(f"実行回数: 5回")
    print("-" * 80)

    # Run 5 times
    results = []
    for i in range(1, 6):
        print(f"\n🔄 Run {i}/5...", flush=True)
        result = run_single_search(pipeline, query_main, query_desc, i)
        results.append(result)
        time.sleep(0.5)  # APIレート制限回避

    # Compare results
    print("\n" + "=" * 80)
    print("再現性チェック")
    print("=" * 80)

    # Stage 1: Top 5 FDC IDs
    print("\n【Stage 1: Top 5 FDC IDs】")
    print("-" * 80)

    baseline = results[0]['stage1_top5_fdcs']
    all_match = True

    for i, r in enumerate(results, 1):
        fdcs = r['stage1_top5_fdcs']
        match = fdcs == baseline
        symbol = "✅" if match else "❌"
        print(f"{symbol} Run {i}: {fdcs}")
        if not match:
            all_match = False

    if all_match:
        print(f"\n✅ Stage 1の順位は完全に一致（再現性あり）")
    else:
        print(f"\n❌ Stage 1の順位が異なる（再現性なし）")

    # Stage 1: Scores
    print("\n【Stage 1: Top 5 Scores】")
    print("-" * 80)

    baseline_scores = results[0]['stage1_top5_scores']
    scores_match = True

    for i, r in enumerate(results, 1):
        scores = r['stage1_top5_scores']
        # 浮動小数点の誤差を考慮（1e-6以下は同一とみなす）
        match = all(abs(s1 - s2) < 1e-6 for s1, s2 in zip(scores, baseline_scores))
        symbol = "✅" if match else "❌"
        scores_str = ", ".join([f"{s:.6f}" for s in scores])
        print(f"{symbol} Run {i}: [{scores_str}]")
        if not match:
            scores_match = False

    if scores_match:
        print(f"\n✅ Stage 1のスコアは一致（誤差1e-6以内）")
    else:
        print(f"\n❌ Stage 1のスコアが異なる")

    # Stage 2: Top 5 FDC IDs
    print("\n【Stage 2 (Reranker): Top 5 FDC IDs】")
    print("-" * 80)

    baseline_stage2 = results[0]['stage2_top5_fdcs']
    stage2_match = True

    for i, r in enumerate(results, 1):
        fdcs = r['stage2_top5_fdcs']
        match = fdcs == baseline_stage2
        symbol = "✅" if match else "❌"
        print(f"{symbol} Run {i}: {fdcs}")
        if not match:
            stage2_match = False

    if stage2_match:
        print(f"\n✅ Stage 2の順位は完全に一致（再現性あり）")
    else:
        print(f"\n❌ Stage 2の順位が異なる（再現性なし）")

    # Stage 2: Scores
    print("\n【Stage 2 (Reranker): Top 5 Rerank Scores】")
    print("-" * 80)

    baseline_rerank_scores = results[0]['stage2_top5_scores']
    rerank_scores_match = True

    for i, r in enumerate(results, 1):
        scores = r['stage2_top5_scores']
        # Rerankerスコアは誤差が大きい可能性があるので1e-4で比較
        match = all(abs(s1 - s2) < 1e-4 for s1, s2 in zip(scores, baseline_rerank_scores))
        symbol = "✅" if match else "❌"
        scores_str = ", ".join([f"{s:.6f}" for s in scores])
        print(f"{symbol} Run {i}: [{scores_str}]")
        if not match:
            rerank_scores_match = False

    if rerank_scores_match:
        print(f"\n✅ Rerankerスコアは一致（誤差1e-4以内）")
    else:
        print(f"\n❌ Rerankerスコアが異なる")

    # Best match
    print("\n【Best Match】")
    print("-" * 80)

    baseline_best = results[0]['best_match_fdc']
    best_match = True

    for i, r in enumerate(results, 1):
        fdc = r['best_match_fdc']
        score = r['best_match_score']
        match = fdc == baseline_best
        symbol = "✅" if match else "❌"
        print(f"{symbol} Run {i}: FDC {fdc}, Score {score:.6f}")
        if not match:
            best_match = False

    if best_match:
        print(f"\n✅ Best matchは一致（再現性あり）")
    else:
        print(f"\n❌ Best matchが異なる（再現性なし）")

    # Final conclusion
    print("\n" + "=" * 80)
    print("総合結論")
    print("=" * 80)

    if all_match and stage2_match and best_match:
        print(f"\n✅ 完全な再現性あり")
        print(f"   - Stage 1の順位: 一致")
        print(f"   - Stage 2の順位: 一致")
        print(f"   - Best match: 一致")
        print(f"\n→ システムは決定的（ランダム要素なし）")
    else:
        print(f"\n❌ 再現性に問題あり")

        if not all_match:
            print(f"   - Stage 1の順位: 不一致 ❌")
            print(f"     → Embedding API または FAISS に非決定性")
        else:
            print(f"   - Stage 1の順位: 一致 ✅")

        if not stage2_match:
            print(f"   - Stage 2の順位: 不一致 ❌")
            print(f"     → Reranker API に非決定性")
        else:
            print(f"   - Stage 2の順位: 一致 ✅")

        if not best_match:
            print(f"   - Best match: 不一致 ❌")
        else:
            print(f"   - Best match: 一致 ✅")

        print(f"\n→ システムにランダム要素が存在する可能性")

    # Additional analysis
    if not all_match or not scores_match:
        print(f"\n" + "=" * 80)
        print("Stage 1 非決定性の詳細分析")
        print("=" * 80)

        print(f"\n考えられる原因:")
        print(f"  1. Embedding API (DeepInfra) が毎回異なるベクトルを返す")
        print(f"  2. FAISSの浮動小数点演算の非決定性")
        print(f"  3. Two-stream weighted search の実装問題")

        print(f"\n影響:")
        print(f"  - 順位の揺らぎ → 境界付近（40位前後）で不安定")
        print(f"  - prosciuttoケースは40位ギリギリ → 実行ごとに入ったり外れたり")

        print(f"\n対策:")
        print(f"  1. Stage1 top_kを大きめに設定（40 → 60-80）")
        print(f"  2. BM25+Embeddingで確実性を向上")
        print(f"  3. Embedding APIのキャッシング検討")


if __name__ == "__main__":
    main()
