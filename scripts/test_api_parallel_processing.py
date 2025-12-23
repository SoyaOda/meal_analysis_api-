#!/usr/bin/env python3
"""
APIエンドポイント並列処理検証テスト

実際のAPIエンドポイントを呼び出して、
Hybrid Search (Embedding + BM25/FAISS + Reranker) の
並列処理が正しく動作しているか検証する。

テスト方法:
1. ローカルでAPIサーバーを起動
2. このスクリプトを実行
3. サーバーログで並列処理のタイミングを確認
"""
import asyncio
import sys
import os
import time
import json
import base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


# テスト用のシンプルな画像（1x1ピクセルの白いJPEG）
# 実際のVLM解析は行われないが、パイプラインの動作確認には十分
MINIMAL_JPEG = bytes([
    0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
    0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
    0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
    0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
    0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
    0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
    0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
    0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
    0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
    0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
    0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
    0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
    0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
    0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
    0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
    0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
    0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
    0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
    0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
    0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
    0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
    0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
    0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
    0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
    0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
    0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
    0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xDB, 0x20, 0xA8, 0xF1, 0x45, 0x00,
    0x14, 0x50, 0x01, 0x45, 0x14, 0x00, 0xFF, 0xD9
])


async def test_pipeline_directly():
    """パイプラインを直接テストして並列処理を検証"""
    print("\n" + "=" * 70)
    print("TEST: Direct Pipeline Parallel Processing Verification")
    print("=" * 70)

    from apps.freeform_usda_meal_analysis_api.services.pipeline import MealAnalysisPipeline
    from apps.freeform_usda_meal_analysis_api.services.hybrid_search import HybridSearchEngine
    from apps.freeform_usda_meal_analysis_api.config.settings import get_settings

    settings = get_settings()

    # パイプライン初期化
    print("\nInitializing pipeline...")
    hybrid_engine = HybridSearchEngine(index_dir=settings.USDA_INDEX_DIR)
    pipeline = MealAnalysisPipeline(
        vlm_model_id=settings.DEFAULT_VLM_MODEL_ID,
        vlm_prompt_file=settings.get_prompt_path(),
        index_dir=settings.USDA_INDEX_DIR,
        usda_metadata_file=settings.USDA_METADATA_FILE,
        stage1_top_k=settings.DEFAULT_STAGE1_TOP_K,
        device=settings.DEFAULT_DEVICE,
        hybrid_engine=hybrid_engine,
        use_lazy_loading=False
    )
    print("Pipeline initialized")

    # テスト用のクエリを直接作成（VLMをスキップ）
    test_queries = [
        {"search_name": "grilled chicken breast", "description": "grilled chicken", "weight_g": 150, "dish_index": 0, "is_main_food": True},
        {"search_name": "steamed white rice", "description": "white rice", "weight_g": 200, "dish_index": 1, "is_main_food": True},
        {"search_name": "miso soup", "description": "miso soup", "weight_g": 250, "dish_index": 2, "is_main_food": True},
        {"search_name": "scrambled eggs", "description": "eggs", "weight_g": 100, "dish_index": 3, "is_main_food": True},
        {"search_name": "vanilla ice cream", "description": "ice cream", "weight_g": 80, "dish_index": 4, "is_main_food": True},
        {"search_name": "grilled salmon", "description": "salmon", "weight_g": 120, "dish_index": 5, "is_main_food": True},
        {"search_name": "caesar salad", "description": "salad", "weight_g": 150, "dish_index": 6, "is_main_food": True},
        {"search_name": "orange juice", "description": "juice", "weight_g": 200, "dish_index": 7, "is_main_food": True},
    ]

    print(f"\nTest queries: {len(test_queries)}")
    for q in test_queries:
        print(f"  - {q['search_name']}")

    # ===== 並列検索テスト =====
    print("\n" + "-" * 50)
    print("Testing _parallel_search() method...")
    print("-" * 50)

    parallel_start = time.time()
    parallel_results = await pipeline._parallel_search(
        queries=test_queries,
        include_debug_info=False
    )
    parallel_time = time.time() - parallel_start

    print(f"\nParallel search completed in {parallel_time:.2f}s")
    print(f"Results: {len(parallel_results)}")

    # 結果表示
    for i, (query, result) in enumerate(zip(test_queries, parallel_results)):
        if result:
            print(f"  [{i+1}] {query['search_name'][:25]:25} -> {result['description'][:40]}...")
        else:
            print(f"  [{i+1}] {query['search_name'][:25]:25} -> NO MATCH")

    # ===== 逐次検索テスト（比較用） =====
    print("\n" + "-" * 50)
    print("Testing _sequential_search() method (for comparison)...")
    print("-" * 50)

    sequential_start = time.time()
    sequential_results = await pipeline._sequential_search(
        queries=test_queries,
        include_debug_info=False
    )
    sequential_time = time.time() - sequential_start

    print(f"\nSequential search completed in {sequential_time:.2f}s")

    # ===== 結果分析 =====
    print("\n" + "=" * 70)
    print("RESULTS ANALYSIS")
    print("=" * 70)

    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    avg_parallel = parallel_time / len(test_queries)
    avg_sequential = sequential_time / len(test_queries)

    print(f"\n  Queries:     {len(test_queries)}")
    print(f"  Parallel:    {parallel_time:.2f}s (avg: {avg_parallel:.2f}s/query)")
    print(f"  Sequential:  {sequential_time:.2f}s (avg: {avg_sequential:.2f}s/query)")
    print(f"  Speedup:     {speedup:.2f}x")

    # 並列処理の判定
    # 並列処理が効いていれば、8クエリでも単一クエリ+αの時間で終わるはず
    is_parallel_working = speedup > 1.5

    if is_parallel_working:
        print(f"\n  PARALLEL PROCESSING CONFIRMED")
        print(f"  (Speedup {speedup:.2f}x > 1.5x threshold)")
    else:
        print(f"\n  WARNING: Parallel processing may not be effective")
        print(f"  (Speedup {speedup:.2f}x <= 1.5x threshold)")

    # 結果の一致確認
    results_match = True
    for i, (par, seq) in enumerate(zip(parallel_results, sequential_results)):
        if par and seq:
            if par.get("fdc_id") != seq.get("fdc_id"):
                results_match = False
                print(f"\n  WARNING: Result mismatch at index {i}")
                print(f"    Parallel: {par.get('description', 'N/A')[:50]}")
                print(f"    Sequential: {seq.get('description', 'N/A')[:50]}")

    if results_match:
        print(f"\n  Result consistency: OK")

    return is_parallel_working, speedup


async def test_parallel_with_timing_logs():
    """タイミングログ付き並列処理テスト"""
    print("\n" + "=" * 70)
    print("TEST: Parallel Processing with Detailed Timing")
    print("=" * 70)

    from apps.freeform_usda_meal_analysis_api.services.food_search_service import USDAFoodSearchService
    from apps.freeform_usda_meal_analysis_api.services.hybrid_search import HybridSearchEngine
    from apps.freeform_usda_meal_analysis_api.config.settings import get_settings

    settings = get_settings()

    # サービス初期化
    print("\nInitializing services...")
    hybrid_engine = HybridSearchEngine(index_dir=settings.USDA_INDEX_DIR)
    food_search_service = USDAFoodSearchService(
        index_dir=settings.USDA_INDEX_DIR,
        hybrid_engine=hybrid_engine,
        use_lazy_loading=False
    )
    print("Services initialized")

    # テストクエリ
    queries = [
        "grilled chicken breast",
        "steamed white rice",
        "miso soup with tofu",
        "scrambled eggs",
        "vanilla ice cream",
        "grilled salmon fillet",
        "caesar salad",
        "fresh orange juice",
    ]

    print(f"\nTest queries: {len(queries)}")

    # ===== Phase 1a: バッチEmbedding =====
    print("\n[Phase 1a: Batch Embedding Generation]")
    embed_start = time.time()
    embeddings = await food_search_service.batch_generate_embeddings(queries)
    embed_time = time.time() - embed_start
    print(f"  Time: {embed_time:.2f}s for {len(queries)} queries (1 API call)")
    print(f"  Embedding dimensions: {len(embeddings[0])}")

    # ===== Phase 1b: BM25 + FAISS + RRF =====
    print("\n[Phase 1b: BM25 + FAISS + RRF Fusion]")
    candidates_start = time.time()
    queries_and_candidates = []
    for i, query in enumerate(queries):
        candidates = food_search_service.get_candidates_only_sync(
            query=query,
            query_embedding=embeddings[i],
            stage1_top_k=50
        )
        queries_and_candidates.append({
            "query": query,
            "candidates": candidates
        })
        print(f"  {query[:25]:25}: {len(candidates)} candidates")
    candidates_time = time.time() - candidates_start
    print(f"  Total time: {candidates_time:.2f}s")

    # ===== Phase 2: 並列Reranker =====
    print("\n[Phase 2: Parallel Reranker Execution]")
    reranker_start = time.time()

    # 各Reranker呼び出しの開始・終了時刻を記録
    reranker_timings = []

    async def rerank_with_timing(idx, query, candidates):
        start = time.time()
        result = await food_search_service.hybrid_engine.apply_reranker_batch(
            queries_and_candidates=[{"query": query, "candidates": candidates}],
            reranker_service=food_search_service.searcher.reranker_service,
            reranker_instruction=settings.DEFAULT_RERANKER_INSTRUCTION,
            top_k=1
        )
        end = time.time()
        reranker_timings.append({
            "idx": idx,
            "query": query[:25],
            "start": start - reranker_start,
            "end": end - reranker_start,
            "duration": end - start
        })
        return result[0] if result else None

    # 並列実行
    tasks = [
        rerank_with_timing(i, item["query"], item["candidates"])
        for i, item in enumerate(queries_and_candidates)
    ]
    results = await asyncio.gather(*tasks)
    reranker_time = time.time() - reranker_start

    print(f"  Total time: {reranker_time:.2f}s")

    # タイミング分析
    print("\n[Reranker Timing Analysis]")
    print(f"  {'Query':<25} {'Start':>8} {'End':>8} {'Duration':>10}")
    print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*10}")

    # 開始時刻でソート
    reranker_timings.sort(key=lambda x: x["start"])
    for t in reranker_timings:
        print(f"  {t['query']:<25} {t['start']:>7.2f}s {t['end']:>7.2f}s {t['duration']:>9.2f}s")

    # 並列度を計算
    # 全てのタスクが同時に開始していれば並列
    start_times = [t["start"] for t in reranker_timings]
    start_range = max(start_times) - min(start_times)

    print(f"\n  Start time range: {start_range:.3f}s")
    if start_range < 0.5:
        print(f"  TRULY PARALLEL (all tasks started within 0.5s)")
    else:
        print(f"  WARNING: Tasks may be sequential (start range > 0.5s)")

    # 合計
    total_time = embed_time + candidates_time + reranker_time
    print("\n" + "=" * 70)
    print("TIMING SUMMARY")
    print("=" * 70)
    print(f"  Phase 1a (Embedding):   {embed_time:.2f}s")
    print(f"  Phase 1b (BM25/FAISS):  {candidates_time:.2f}s")
    print(f"  Phase 2 (Reranker):     {reranker_time:.2f}s")
    print(f"  Total:                  {total_time:.2f}s for {len(queries)} queries")
    print(f"  Average per query:      {total_time/len(queries):.2f}s")

    # 結果表示
    print("\n[Search Results]")
    for query, result in zip(queries, results):
        if result:
            print(f"  {query[:25]:25} -> {result['description'][:40]}...")
        else:
            print(f"  {query[:25]:25} -> NO MATCH")

    return start_range < 0.5


async def main():
    print("\n" + "=" * 70)
    print("API Endpoint Parallel Processing Verification")
    print("=" * 70)

    # 環境変数チェック
    api_key = os.getenv("DEEPINFRA_API_KEY")
    if not api_key:
        print("DEEPINFRA_API_KEY not found!")
        return

    print(f"DEEPINFRA_API_KEY: Found")

    results = {}

    # Test 1: パイプライン直接テスト
    try:
        is_parallel, speedup = await test_pipeline_directly()
        results["pipeline_parallel"] = is_parallel
        results["speedup"] = speedup
    except Exception as e:
        print(f"\nTest 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results["pipeline_parallel"] = False
        results["speedup"] = 0

    # Test 2: 詳細タイミングテスト
    try:
        is_truly_parallel = await test_parallel_with_timing_logs()
        results["truly_parallel"] = is_truly_parallel
    except Exception as e:
        print(f"\nTest 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results["truly_parallel"] = False

    # Final Summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    all_passed = results.get("pipeline_parallel", False) and results.get("truly_parallel", False)

    print(f"\n  Pipeline Parallel Search: {'PASS' if results.get('pipeline_parallel') else 'FAIL'}")
    print(f"  Speedup: {results.get('speedup', 0):.2f}x")
    print(f"  Truly Parallel Execution: {'PASS' if results.get('truly_parallel') else 'FAIL'}")

    print(f"\n{'ALL TESTS PASSED - PARALLEL PROCESSING CONFIRMED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
