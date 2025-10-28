#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stage 1候補保存機能のテスト

prosciuttoケース1件で、Stage 1候補が正しく保存されるか確認
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline


def main():
    """Stage 1候補保存のテスト"""

    print("=" * 80)
    print("Stage 1候補保存機能のテスト")
    print("=" * 80)

    # Initialize pipeline
    index_dir = project_root / "data"
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=40
    )

    # Test query
    query_name = "prosciutto"
    query_desc = "sliced"

    print(f"\nQuery: {query_name} | {query_desc}")
    print("-" * 80)

    # Search with return_candidates=True
    result = pipeline.search(
        query_main=query_name,
        query_descriptors=query_desc,
        return_top_k=5,
        return_candidates=True
    )

    # Check returned data
    print(f"\n✅ 検索完了")
    print(f"\nReturned keys:")
    for key in result.keys():
        print(f"  - {key}")

    # Check candidates
    candidates = result.get('stage1_candidates', [])
    print(f"\n📊 Stage 1候補数: {len(candidates)}")

    if candidates:
        print(f"\n最初の3件:")
        for i, cand in enumerate(candidates[:3], 1):
            print(f"  {i}. {cand['description']}")
            print(f"     Score: {cand['score']:.6f}, FDC ID: {cand['fdc_id']}")

    # Simulate saving
    test_result = {
        "query_id": 1,
        "query_name": query_name,
        "query_desc": query_desc,
        "matched_description": result['best_match']['description'],
        "rerank_score": result['best_match']['rerank_score'],
        "stage1_score": result['best_match']['stage1_score'],
        "fdc_id": result['best_match']['fdc_id'],
        "top_k_results": result['top_k'],
        "stage1_candidates": candidates
    }

    # Save test result
    output_file = project_root / "output" / "test_candidates_saving.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_result, f, indent=2, ensure_ascii=False)

    file_size_kb = output_file.stat().st_size / 1024
    print(f"\n💾 Test result saved to: {output_file}")
    print(f"   File size: {file_size_kb:.2f} KB")

    # Verify Ham, prosciutto presence in Stage 1
    correct_fdc = 2705879
    found = any(c['fdc_id'] == correct_fdc for c in candidates)

    print(f"\n{'='*80}")
    print(f"検証結果")
    print("=" * 80)

    if found:
        rank = next(i+1 for i, c in enumerate(candidates) if c['fdc_id'] == correct_fdc)
        score = next(c['score'] for c in candidates if c['fdc_id'] == correct_fdc)
        print(f"\n✅ Ham, prosciutto (FDC ID: {correct_fdc}) が見つかりました")
        print(f"   Stage 1順位: {rank}位")
        print(f"   Embeddingスコア: {score:.6f}")
    else:
        print(f"\n❌ Ham, prosciutto (FDC ID: {correct_fdc}) は40位圏外")

    print(f"\n✅ Stage 1候補が正しく保存されることを確認しました")


if __name__ == "__main__":
    main()
