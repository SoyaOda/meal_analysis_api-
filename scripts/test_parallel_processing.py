#!/usr/bin/env python3
"""
Qwen3ベースRetriever/Reranker並列処理検証テスト

検証項目:
1. バッチEmbedding生成（1回のAPI呼び出しでN個のembedding）
2. 並列Reranker実行（asyncio.gatherで真の並列処理）
3. HTTPコネクションプールの再利用確認
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


# テストクエリ（10件で並列処理の効果を測定）
TEST_QUERIES = [
    "grilled chicken breast",
    "steamed white rice",
    "miso soup with tofu",
    "scrambled eggs",
    "vanilla ice cream",
    "fried salmon fillet",
    "boiled broccoli",
    "caesar salad",
    "orange juice",
    "whole wheat bread",
]


async def test_batch_embedding():
    """バッチEmbedding生成テスト"""
    print("\n" + "=" * 70)
    print("TEST 1: Batch Embedding Generation (Qwen3-Embedding-8B)")
    print("=" * 70)

    from apps.freeform_usda_meal_analysis_api.services.deepinfra_service import DeepInfraService
    from apps.freeform_usda_meal_analysis_api.config.settings import get_settings

    settings = get_settings()
    service = DeepInfraService()
    instruction = settings.DEFAULT_EMBEDDING_INSTRUCTION

    print(f"\nInstruction: {instruction}")
    print(f"Queries: {len(TEST_QUERIES)}")

    # ===== 逐次実行 =====
    print("\n[Sequential Execution]")
    sequential_start = time.time()
    sequential_embeddings = []
    for query in TEST_QUERIES:
        emb = await service.generate_embeddings([query], instruction=instruction)
        sequential_embeddings.append(emb[0])
    sequential_time = time.time() - sequential_start
    print(f"  Sequential time: {sequential_time:.2f}s ({len(TEST_QUERIES)} API calls)")

    # ===== バッチ実行 =====
    print("\n[Batch Execution]")
    batch_start = time.time()
    batch_embeddings = await service.generate_embeddings(
        TEST_QUERIES,
        instruction=instruction
    )
    batch_time = time.time() - batch_start
    print(f"  Batch time: {batch_time:.2f}s (1 API call)")

    # 結果分析
    speedup = sequential_time / batch_time if batch_time > 0 else 0
    is_batch_faster = speedup > 2.0  # バッチは最低でも2倍速いはず

    print(f"\n[Results]")
    print(f"  Sequential: {sequential_time:.2f}s ({len(TEST_QUERIES)} calls)")
    print(f"  Batch:      {batch_time:.2f}s (1 call)")
    print(f"  Speedup:    {speedup:.2f}x")
    print(f"  Embedding dims: {len(batch_embeddings[0])}")

    if is_batch_faster:
        print(f"  BATCH EMBEDDING WORKING")
    else:
        print(f"  WARNING: Batch not significantly faster")

    # Embedding一致確認（同じ結果が返るはず）
    embedding_match = True
    for i, (seq, batch) in enumerate(zip(sequential_embeddings, batch_embeddings)):
        diff = sum(abs(s - b) for s, b in zip(seq, batch))
        if diff > 0.001:  # 浮動小数点誤差を許容
            embedding_match = False
            print(f"  WARNING: Embedding mismatch at index {i}, diff={diff}")

    if embedding_match:
        print(f"  Embedding consistency: OK")

    return is_batch_faster


async def test_parallel_reranker():
    """並列Reranker実行テスト"""
    print("\n" + "=" * 70)
    print("TEST 2: Parallel Reranker Execution (Qwen3-Reranker-8B)")
    print("=" * 70)

    from apps.freeform_usda_meal_analysis_api.services.deepinfra_service import DeepInfraService
    from apps.freeform_usda_meal_analysis_api.config.settings import get_settings

    settings = get_settings()
    service = DeepInfraService()
    instruction = settings.DEFAULT_RERANKER_INSTRUCTION

    print(f"\nInstruction: {instruction[:100]}...")

    # テストケース（各クエリに対して5つの候補）
    test_cases = []
    sample_documents = [
        ["Chicken, broilers or fryers, breast, meat only, cooked, grilled",
         "Chicken, broilers or fryers, breast, meat only, raw",
         "Chicken, broilers or fryers, drumstick, meat only, cooked",
         "Turkey, breast, meat only, cooked, roasted",
         "Duck, meat only, cooked, roasted"],
        ["Rice, white, long-grain, regular, cooked",
         "Rice, white, long-grain, regular, raw",
         "Rice, brown, long-grain, cooked",
         "Rice, fried, meatless",
         "Noodles, egg, cooked"],
        ["Soup, miso, prepared with water",
         "Miso",
         "Tofu, firm",
         "Soup, vegetable beef",
         "Seaweed, wakame, raw"],
        ["Egg, whole, cooked, scrambled",
         "Egg, whole, raw, fresh",
         "Egg, whole, cooked, fried",
         "Egg, whole, cooked, hard-boiled",
         "Egg, white only, raw"],
        ["Ice creams, vanilla",
         "Ice creams, chocolate",
         "Frozen yogurts, vanilla",
         "Milk, whole",
         "Cream, heavy whipping"],
    ]

    for i, query in enumerate(TEST_QUERIES[:5]):
        test_cases.append({
            "query": query,
            "documents": sample_documents[i % len(sample_documents)]
        })

    print(f"Test cases: {len(test_cases)}")

    # ===== 逐次実行 =====
    print("\n[Sequential Execution]")
    sequential_start = time.time()
    sequential_results = []
    for i, case in enumerate(test_cases):
        start = time.time()
        best_idx, scores = await service.rerank(
            query=case["query"],
            documents=case["documents"],
            instruction=instruction
        )
        elapsed = time.time() - start
        sequential_results.append((best_idx, scores, elapsed))
        print(f"  Query {i+1}: {elapsed:.2f}s")
    sequential_time = time.time() - sequential_start
    print(f"  Total: {sequential_time:.2f}s")

    # ===== 並列実行 =====
    print("\n[Parallel Execution]")
    parallel_start = time.time()

    async def rerank_single(case, idx):
        start = time.time()
        result = await service.rerank(
            query=case["query"],
            documents=case["documents"],
            instruction=instruction
        )
        elapsed = time.time() - start
        print(f"  Query {idx+1}: {elapsed:.2f}s (parallel)")
        return result

    tasks = [rerank_single(case, i) for i, case in enumerate(test_cases)]
    parallel_results = await asyncio.gather(*tasks)
    parallel_time = time.time() - parallel_start
    print(f"  Total: {parallel_time:.2f}s")

    # 結果分析
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    is_truly_parallel = speedup > 1.5

    print(f"\n[Results]")
    print(f"  Sequential: {sequential_time:.2f}s")
    print(f"  Parallel:   {parallel_time:.2f}s")
    print(f"  Speedup:    {speedup:.2f}x")

    if is_truly_parallel:
        print(f"  PARALLEL RERANKER WORKING")
    else:
        print(f"  WARNING: Parallelism not effective (speedup < 1.5x)")

    # 結果一致確認
    results_match = True
    for i, ((seq_idx, seq_scores, _), (par_idx, par_scores)) in enumerate(
        zip(sequential_results, parallel_results)
    ):
        if seq_idx != par_idx:
            results_match = False
            print(f"  WARNING: Result mismatch at index {i}")

    if results_match:
        print(f"  Result consistency: OK")

    return is_truly_parallel


async def test_http_connection_pool():
    """HTTPコネクションプール再利用テスト"""
    print("\n" + "=" * 70)
    print("TEST 3: HTTP Connection Pool Reuse")
    print("=" * 70)

    from apps.freeform_usda_meal_analysis_api.core.http_client import get_async_client

    # 同じクライアントインスタンスが返されるか確認
    client1 = get_async_client()
    client2 = get_async_client()
    client3 = get_async_client()

    is_same_instance = (client1 is client2) and (client2 is client3)

    print(f"\n  Client 1 ID: {id(client1)}")
    print(f"  Client 2 ID: {id(client2)}")
    print(f"  Client 3 ID: {id(client3)}")
    print(f"  Same instance: {is_same_instance}")

    if is_same_instance:
        print(f"  HTTP CONNECTION POOL WORKING")
    else:
        print(f"  WARNING: New client created each time (no pooling)")

    return is_same_instance


async def test_full_pipeline_parallel():
    """フルパイプライン並列処理テスト"""
    print("\n" + "=" * 70)
    print("TEST 4: Full Pipeline Parallel Processing")
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

    queries = TEST_QUERIES[:5]  # 5クエリでテスト

    # ===== Phase 1a: バッチEmbedding =====
    print(f"\n[Phase 1a: Batch Embedding for {len(queries)} queries]")
    embed_start = time.time()
    embeddings = await food_search_service.batch_generate_embeddings(queries)
    embed_time = time.time() - embed_start
    print(f"  Time: {embed_time:.2f}s (1 API call for {len(queries)} queries)")

    # ===== Phase 1b: BM25 + FAISS (同期処理) =====
    print(f"\n[Phase 1b: BM25 + FAISS + RRF for {len(queries)} queries]")
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
    candidates_time = time.time() - candidates_start
    print(f"  Time: {candidates_time:.2f}s")

    # ===== Phase 2: 並列Reranker =====
    print(f"\n[Phase 2: Parallel Reranker for {len(queries)} queries]")
    reranker_start = time.time()
    results = await food_search_service.batch_rerank_candidates(
        queries_and_candidates=queries_and_candidates,
        reranker_instruction=settings.DEFAULT_RERANKER_INSTRUCTION,
        top_k=1
    )
    reranker_time = time.time() - reranker_start
    print(f"  Time: {reranker_time:.2f}s")

    # 結果サマリ
    total_time = embed_time + candidates_time + reranker_time
    print(f"\n[Pipeline Summary]")
    print(f"  Phase 1a (Embedding): {embed_time:.2f}s")
    print(f"  Phase 1b (BM25/FAISS): {candidates_time:.2f}s")
    print(f"  Phase 2 (Reranker): {reranker_time:.2f}s")
    print(f"  Total: {total_time:.2f}s for {len(queries)} queries")
    print(f"  Average per query: {total_time/len(queries):.2f}s")

    # 結果表示
    print(f"\n[Results]")
    for query, result in zip(queries, results):
        if result:
            print(f"  {query[:25]:25} -> {result['description'][:40]}...")
        else:
            print(f"  {query[:25]:25} -> NO MATCH")

    # 成功基準: Rerankerが並列で動作している（5クエリで1.5秒未満なら成功）
    is_parallel_working = reranker_time < len(queries) * 0.4  # 1クエリあたり0.4秒未満

    if is_parallel_working:
        print(f"\n  FULL PIPELINE PARALLEL PROCESSING WORKING")
    else:
        print(f"\n  WARNING: Pipeline may not be fully parallel")

    return is_parallel_working


async def main():
    print("\n" + "=" * 70)
    print("Qwen3 Parallel Processing Verification Test")
    print("=" * 70)

    # 環境変数チェック
    api_key = os.getenv("DEEPINFRA_API_KEY")
    if not api_key:
        print("DEEPINFRA_API_KEY not found!")
        return

    print(f"DEEPINFRA_API_KEY: Found")
    print(f"Test queries: {len(TEST_QUERIES)}")

    results = {}

    # Test 1: バッチEmbedding
    try:
        results["batch_embedding"] = await test_batch_embedding()
    except Exception as e:
        print(f"Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results["batch_embedding"] = False

    # Test 2: 並列Reranker
    try:
        results["parallel_reranker"] = await test_parallel_reranker()
    except Exception as e:
        print(f"Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results["parallel_reranker"] = False

    # Test 3: HTTPコネクションプール
    try:
        results["http_pool"] = await test_http_connection_pool()
    except Exception as e:
        print(f"Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        results["http_pool"] = False

    # Test 4: フルパイプライン
    try:
        results["full_pipeline"] = await test_full_pipeline_parallel()
    except Exception as e:
        print(f"Test 4 failed: {e}")
        import traceback
        traceback.print_exc()
        results["full_pipeline"] = False

    # Final Summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    all_passed = all(results.values())
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name:25}: {status}")

    print(f"\n{'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
