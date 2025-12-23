#!/usr/bin/env python3
"""
Pipeline Instruction Test - DeepInfra Reranker

パイプライン全体のDeepInfra instruction対応を検証するテスト。
Phase 1a: バッチEmbedding生成（instruction付き）
Phase 1b: BM25 + FAISS + RRF融合
Phase 2: 並列Reranker実行（instruction付き）
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


# テストクエリ（VLMが出力するような食品クエリ）
TEST_QUERIES = [
    "grilled chicken breast",
    "steamed white rice",
    "miso soup",
    "scrambled eggs",
    "vanilla ice cream",
]


async def test_embedding_with_instruction():
    """Embedding生成のinstruction対応テスト"""
    print("\n" + "="*60)
    print("📍 TEST 1: Embedding with Instruction")
    print("="*60)

    from apps.freeform_usda_meal_analysis_api.services.deepinfra_service import DeepInfraService
    from apps.freeform_usda_meal_analysis_api.config.settings import get_settings

    settings = get_settings()
    service = DeepInfraService()

    instruction = settings.DEFAULT_EMBEDDING_INSTRUCTION
    print(f"\n📝 Instruction: {instruction}")

    # 単一テストクエリ
    test_query = "grilled chicken breast"

    # instruction付きでembedding生成
    print(f"\n🔄 Generating embedding for: '{test_query}'")
    start = time.time()
    embeddings = await service.generate_embeddings(
        texts=[test_query],
        instruction=instruction
    )
    elapsed = time.time() - start

    print(f"✅ Embedding generated: {len(embeddings[0])} dimensions in {elapsed:.2f}s")
    print(f"   First 5 values: {embeddings[0][:5]}")

    return True


async def test_reranker_with_instruction():
    """Rerankerのinstruction対応テスト"""
    print("\n" + "="*60)
    print("📍 TEST 2: Reranker with Instruction")
    print("="*60)

    from apps.freeform_usda_meal_analysis_api.services.deepinfra_service import DeepInfraService
    from apps.freeform_usda_meal_analysis_api.config.settings import get_settings

    settings = get_settings()
    service = DeepInfraService()

    instruction = settings.DEFAULT_RERANKER_INSTRUCTION
    print(f"\n📝 Instruction: {instruction[:100]}...")

    # テストケース
    query = "grilled chicken breast"
    documents = [
        "Chicken, broilers or fryers, breast, meat only, cooked, grilled",
        "Chicken, broilers or fryers, breast, meat only, raw",
        "Chicken, broilers or fryers, breast, meat and skin, cooked, roasted",
        "Chicken, broilers or fryers, drumstick, meat only, cooked, grilled",
        "Turkey, breast, meat only, cooked, roasted",
    ]

    print(f"\n🔄 Reranking for query: '{query}'")
    print(f"   Candidates: {len(documents)}")

    start = time.time()
    best_idx, scores = await service.rerank(
        query=query,
        documents=documents,
        instruction=instruction
    )
    elapsed = time.time() - start

    print(f"\n✅ Reranking complete in {elapsed:.2f}s")
    print(f"   Best match [{best_idx}]: {documents[best_idx]}")
    print(f"   Score: {scores[best_idx]:.4f}")
    print(f"\n   All scores:")
    for i, (doc, score) in enumerate(zip(documents, scores)):
        marker = "👑" if i == best_idx else "  "
        print(f"   {marker} [{i}] {score:.4f} - {doc[:50]}...")

    # 検証: "grilled"が含まれるアイテムが最高スコアになるはず
    expected_idx = 0  # "Chicken, broilers or fryers, breast, meat only, cooked, grilled"
    is_correct = best_idx == expected_idx
    print(f"\n{'✅' if is_correct else '❌'} Expected best match: [{expected_idx}]")

    return is_correct


async def test_parallel_reranker():
    """並列Reranker実行のテスト"""
    print("\n" + "="*60)
    print("📍 TEST 3: Parallel Reranker Execution")
    print("="*60)

    from apps.freeform_usda_meal_analysis_api.services.deepinfra_service import DeepInfraService
    from apps.freeform_usda_meal_analysis_api.config.settings import get_settings

    settings = get_settings()
    service = DeepInfraService()
    instruction = settings.DEFAULT_RERANKER_INSTRUCTION

    # 複数クエリを準備
    test_cases = [
        {
            "query": "grilled chicken breast",
            "documents": [
                "Chicken, broilers or fryers, breast, meat only, cooked, grilled",
                "Chicken, broilers or fryers, breast, meat only, raw",
                "Chicken, broilers or fryers, drumstick, meat only, cooked, grilled",
            ],
            "expected_idx": 0
        },
        {
            "query": "scrambled eggs",
            "documents": [
                "Egg, whole, raw, fresh",
                "Egg, whole, cooked, scrambled",
                "Egg, whole, cooked, fried",
            ],
            "expected_idx": 1
        },
        {
            "query": "steamed white rice",
            "documents": [
                "Rice, white, long-grain, regular, cooked",
                "Rice, white, long-grain, regular, raw, unenriched",
                "Rice, fried, meatless",
            ],
            "expected_idx": 0
        },
        {
            "query": "miso soup",
            "documents": [
                "Soup, miso, prepared with water",
                "Miso",
                "Soup, vegetable beef, canned, prepared with equal volume water",
            ],
            "expected_idx": 0
        },
        {
            "query": "vanilla ice cream",
            "documents": [
                "Ice creams, vanilla",
                "Ice creams, chocolate",
                "Frozen yogurts, vanilla, soft-serve",
            ],
            "expected_idx": 0
        },
    ]

    # ===== 逐次実行 =====
    print(f"\n📊 Sequential execution ({len(test_cases)} queries)...")
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
        print(f"   Query {i+1} ({case['query'][:20]}...): {elapsed:.2f}s")
    sequential_total = time.time() - sequential_start
    print(f"   Total: {sequential_total:.2f}s")

    # ===== 並列実行 =====
    print(f"\n📊 Parallel execution ({len(test_cases)} queries)...")
    parallel_start = time.time()

    async def rerank_single(case):
        return await service.rerank(
            query=case["query"],
            documents=case["documents"],
            instruction=instruction
        )

    tasks = [rerank_single(case) for case in test_cases]
    parallel_results = await asyncio.gather(*tasks)
    parallel_total = time.time() - parallel_start
    print(f"   Total: {parallel_total:.2f}s")

    # 結果分析
    speedup = sequential_total / parallel_total if parallel_total > 0 else 0
    is_truly_parallel = speedup > 1.5

    print(f"\n📈 Results:")
    print(f"   Sequential: {sequential_total:.2f}s")
    print(f"   Parallel:   {parallel_total:.2f}s")
    print(f"   Speedup:    {speedup:.2f}x")

    if is_truly_parallel:
        print(f"   ✅ TRUE PARALLEL EXECUTION CONFIRMED")
    else:
        print(f"   ⚠️  SEQUENTIAL-LIKE (speedup < 1.5x)")

    # 精度チェック
    correct = 0
    for i, ((best_idx, scores), case) in enumerate(zip(parallel_results, test_cases)):
        is_correct = best_idx == case["expected_idx"]
        if is_correct:
            correct += 1
        status = "✅" if is_correct else "❌"
        print(f"   {status} {case['query'][:25]:25} -> [{best_idx}] {case['documents'][best_idx][:30]}...")

    accuracy = correct / len(test_cases) * 100
    print(f"\n📊 Accuracy: {correct}/{len(test_cases)} ({accuracy:.1f}%)")

    return is_truly_parallel and accuracy >= 80


async def test_full_pipeline():
    """フルパイプラインテスト（2フェーズ最適化）"""
    print("\n" + "="*60)
    print("📍 TEST 4: Full Pipeline with 2-Phase Optimization")
    print("="*60)

    from apps.freeform_usda_meal_analysis_api.services.food_search_service import USDAFoodSearchService
    from apps.freeform_usda_meal_analysis_api.services.hybrid_search import HybridSearchEngine
    from apps.freeform_usda_meal_analysis_api.config.settings import get_settings

    settings = get_settings()

    # HybridSearchEngineとUSDAFoodSearchServiceを初期化
    print("\n🔄 Initializing services...")
    hybrid_engine = HybridSearchEngine(
        index_dir=settings.USDA_INDEX_DIR
    )

    food_search_service = USDAFoodSearchService(
        index_dir=settings.USDA_INDEX_DIR,
        hybrid_engine=hybrid_engine,
        use_lazy_loading=False  # テスト用に同期ロード
    )

    print("✅ Services initialized")

    # Phase 1a: バッチEmbedding生成
    print(f"\n🔄 Phase 1a: Batch embedding generation for {len(TEST_QUERIES)} queries...")
    embed_start = time.time()
    embeddings = await food_search_service.batch_generate_embeddings(TEST_QUERIES)
    embed_time = time.time() - embed_start
    print(f"✅ Embedding completed in {embed_time:.2f}s")

    # Phase 1b: BM25 + FAISS + RRF融合（候補取得のみ）
    print(f"\n🔄 Phase 1b: BM25 + FAISS + RRF fusion...")
    candidates_start = time.time()
    queries_and_candidates = []
    for i, query in enumerate(TEST_QUERIES):
        candidates = food_search_service.get_candidates_only_sync(
            query=query,
            query_embedding=embeddings[i],
            stage1_top_k=50
        )
        queries_and_candidates.append({
            "query": query,
            "candidates": candidates
        })
        print(f"   {query}: {len(candidates)} candidates")
    candidates_time = time.time() - candidates_start
    print(f"✅ BM25/FAISS/RRF completed in {candidates_time:.2f}s")

    # Phase 2: 並列Reranker実行
    print(f"\n🔄 Phase 2: Parallel reranker...")
    reranker_start = time.time()
    reranked_results = await food_search_service.batch_rerank_candidates(
        queries_and_candidates=queries_and_candidates,
        reranker_instruction=settings.DEFAULT_RERANKER_INSTRUCTION,
        top_k=1
    )
    reranker_time = time.time() - reranker_start
    print(f"✅ Reranker completed in {reranker_time:.2f}s")

    # 結果表示
    total_time = embed_time + candidates_time + reranker_time
    print(f"\n📊 Total pipeline time: {total_time:.2f}s")
    print(f"   - Embedding: {embed_time:.2f}s")
    print(f"   - BM25/FAISS/RRF: {candidates_time:.2f}s")
    print(f"   - Reranker: {reranker_time:.2f}s")

    print(f"\n📋 Results:")
    for query, result in zip(TEST_QUERIES, reranked_results):
        if result:
            print(f"   {query:25} -> {result['description'][:40]}... (score: {result.get('rerank_score', 0):.4f})")
        else:
            print(f"   {query:25} -> NO MATCH")

    return True


async def main():
    print("\n" + "="*70)
    print("🔬 Pipeline Instruction Test - DeepInfra Reranker")
    print("="*70)

    # 環境変数チェック
    api_key = os.getenv("DEEPINFRA_API_KEY")
    if not api_key:
        print("❌ DEEPINFRA_API_KEY not found!")
        return
    print(f"✅ DEEPINFRA_API_KEY: Found")

    results = {}

    # Test 1: Embedding with Instruction
    try:
        results["embedding"] = await test_embedding_with_instruction()
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        results["embedding"] = False

    # Test 2: Reranker with Instruction
    try:
        results["reranker"] = await test_reranker_with_instruction()
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        results["reranker"] = False

    # Test 3: Parallel Reranker
    try:
        results["parallel"] = await test_parallel_reranker()
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
        results["parallel"] = False

    # Test 4: Full Pipeline
    try:
        results["pipeline"] = await test_full_pipeline()
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
        import traceback
        traceback.print_exc()
        results["pipeline"] = False

    # Final Summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)

    all_passed = all(results.values())
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name:20}: {status}")

    print(f"\n{'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
