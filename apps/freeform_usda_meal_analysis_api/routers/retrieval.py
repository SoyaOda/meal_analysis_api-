#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
USDA Food Retrieval API Router
FAISS検索エンドポイント（fastモードとaccurateモード）
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
import logging
import time
from datetime import datetime

from ..models.response_models import (
    RetrievalResponse,
    RetrievalMetadata,
    RetrievalStatus,
    RetrievalHealthResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

# USDAFoodSearchServiceはmain.pyで初期化されたものをグローバルに保持
_search_service = None
_hybrid_search_engine = None


def set_search_service(service):
    """検索サービスを設定"""
    global _search_service
    _search_service = service


def set_hybrid_search_engine(engine):
    """ハイブリッドサーチエンジンを設定"""
    global _hybrid_search_engine
    _hybrid_search_engine = engine


@router.get("/retrieve", response_model=RetrievalResponse)
async def retrieve_foods(
    q: str = Query(..., min_length=1, description="検索クエリ"),
    mode: str = Query("hybrid", description="検索モード: fast (FAISS only) | accurate (FAISS + Rerank) | hybrid (BM25 + FAISS) | hybrid_reranker (BM25 + FAISS + Rerank)"),
    top_k: int = Query(10, ge=1, le=50, description="返却結果数（1-50）"),
    offset: int = Query(0, ge=0, le=500, description="オフセット（スキップする結果数、ページネーション用）"),
    include_nutrition: bool = Query(True, description="栄養情報を含めるか"),
    debug: bool = Query(False, description="デバッグ情報を含めるか")
) -> RetrievalResponse:
    """
    USDA食材検索API（FAISS検索）

    Args:
        q: 検索クエリ（例: "chicken breast grilled"）
        mode: "fast" (FAISS検索のみ、高速) or "accurate" (FAISS + Reranking、高精度) or "hybrid" (BM25 + FAISS、最高精度) or "hybrid_reranker" (BM25 + FAISS + Reranking、最高精度)
        top_k: 返却する結果数
        offset: オフセット（ページネーション用、スキップする結果数）
        include_nutrition: 栄養情報を含めるか
        debug: デバッグ情報を含めるか

    Returns:
        検索結果のJSON（metadata.has_moreでさらに結果があるか確認可能）
    """

    if not _search_service:
        raise HTTPException(
            status_code=503,
            detail="Search service not initialized"
        )

    start_time = time.time()

    try:
        logger.info(f"🔍 Retrieval request: query='{q}', mode={mode}, top_k={top_k}")

        # モード検証
        if mode not in ["fast", "accurate", "hybrid", "hybrid_reranker"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid mode. Must be 'fast', 'accurate', 'hybrid', or 'hybrid_reranker'"
            )

        # ページネーション用に多めに取得（offset + top_k + 1件で、has_moreを判定）
        internal_top_k = offset + top_k + 1

        # 検索実行
        if mode == "fast":
            # Fast mode: FAISS検索のみ（Stage 1）
            result = await _search_fast_mode(q, internal_top_k)
        elif mode == "hybrid":
            # Hybrid mode: BM25 + FAISS（RRF融合）
            result = await _search_hybrid_mode(q, internal_top_k)
        elif mode == "hybrid_reranker":
            # Hybrid + Reranker mode: BM25 + FAISS（RRF融合）+ Reranking
            result = await _search_hybrid_reranker_mode(q, internal_top_k)
        else:
            # Accurate mode: FAISS + Reranking（Stage 1 + 2）
            result = await _search_accurate_mode(q, internal_top_k)

        # ページネーション適用（offsetからtop_k件を取得）
        all_results = result.get("results", [])
        total_available = len(all_results)
        has_more = total_available > offset + top_k
        paginated_results = all_results[offset:offset + top_k]
        result["results"] = paginated_results

        # 栄養情報フィルタ
        if not include_nutrition:
            for item in result.get("results", []):
                item.pop("nutrition_per_100g", None)

        # 処理時間計算
        processing_time_ms = int((time.time() - start_time) * 1000)

        # レスポンス構築
        response = RetrievalResponse(
            query=q,
            mode=mode,
            results=result.get("results", []),
            metadata=RetrievalMetadata(
                total_results=len(result.get("results", [])),
                search_time_ms=processing_time_ms,
                index_type="FAISS",
                algorithm="Stage1" if mode == "fast" else "Stage1+Stage2_Rerank",
                offset=offset,
                has_more=has_more,
                total_available=total_available if total_available > 0 else None
            ),
            status=RetrievalStatus(
                success=True,
                message="Search completed successfully"
            ),
            debug_info=result.get("debug_info") if debug else None
        )

        logger.info(f"✅ Retrieval completed: {len(result.get('results', []))} results in {processing_time_ms}ms")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Retrieval error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


async def _search_fast_mode(query: str, top_k: int) -> Dict[str, Any]:
    """
    Fast mode: FAISS検索のみ（Stage 1）

    SimplifiedUSDASearcherの内部処理を直接使用して
    Stage 1のみ実行（Rerankingスキップ）
    """
    import numpy as np

    # Lazy Loading対応：初回アクセス時にインデックスをロード
    await _search_service._ensure_searcher_loaded()
    
    searcher = _search_service.searcher

    # Embedding生成
    embeddings = await searcher.embedding_service.generate_embeddings([query])
    query_vector = np.array(embeddings[0]).astype('float32').reshape(1, -1)

    # FAISS検索
    distances, indices = searcher.index_full.search(query_vector, top_k)

    # 結果を整形
    results = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx < len(searcher.items):
            item = searcher.items[idx]

            # 栄養情報（既に100gあたりのデータ）
            nutrition = item.get("nutrition", {})
            nutrition_per_100g = {
                "calories": round(nutrition.get("calories", 0), 1),
                "protein": round(nutrition.get("protein_g", 0), 1),
                "fat": round(nutrition.get("fat_g", 0), 1),
                "carbs": round(nutrition.get("carbs_g", 0), 1)
            }

            results.append({
                "fdc_id": str(item.get("fdc_id")),
                "description": item.get("description", ""),
                "main_name": item.get("main_name", ""),
                "descriptors": item.get("descriptors", ""),
                "source": item.get("source", "unknown"),
                "score": float(dist),
                "nutrition_per_100g": nutrition_per_100g
            })

    return {
        "results": results,
        "debug_info": {
            "mode": "fast",
            "stage1_candidates": len(results),
            "reranking_applied": False
        }
    }


async def _search_accurate_mode(query: str, top_k: int) -> Dict[str, Any]:
    """
    Accurate mode: FAISS + Reranking（Stage 1 + 2）

    SimplifiedUSDASearcherの完全な検索パイプラインを使用
    """
    # Lazy Loading対応：初回アクセス時にインデックスをロード
    await _search_service._ensure_searcher_loaded()

    # USDAFoodSearchServiceのsearch_batchメソッドを使用
    # （内部でSimplifiedUSDASearcher.searchを呼ぶ）
    result = await _search_service.searcher.search_async(
        query_main=query,
        query_descriptors="",
        return_top_k=top_k
    )

    # 結果を整形
    results = []
    for candidate in result.get("all_candidates", []):
        # メタデータから栄養情報を取得
        fdc_id = candidate.get("fdc_id")
        item = next((i for i in _search_service.searcher.items if i.get("fdc_id") == fdc_id), None)

        nutrition_per_100g = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
        if item:
            nutrition = item.get("nutrition", {})
            nutrition_per_100g = {
                "calories": round(nutrition.get("calories", 0), 1),
                "protein": round(nutrition.get("protein_g", 0), 1),
                "fat": round(nutrition.get("fat_g", 0), 1),
                "carbs": round(nutrition.get("carbs_g", 0), 1)
            }

        results.append({
            "fdc_id": str(candidate.get("fdc_id")),
            "description": candidate.get("description", ""),
            "main_name": candidate.get("main_name", ""),
            "descriptors": candidate.get("descriptors", ""),
            "source": candidate.get("source", "unknown"),
            "score": candidate.get("rerank_score", 0),
            "nutrition_per_100g": nutrition_per_100g
        })

    return {
        "results": results,
        "debug_info": {
            "mode": "accurate",
            "stage1_candidates": 40,  # デフォルト
            "reranking_applied": True
        }
    }


async def _search_hybrid_mode(query: str, top_k: int) -> Dict[str, Any]:
    """
    Hybrid mode: BM25 + FAISS（RRF融合）

    HybridSearchEngineを使用してBM25とVectorを組み合わせた検索を実行
    """
    if not _hybrid_search_engine:
        raise HTTPException(
            status_code=503,
            detail="Hybrid search engine not initialized"
        )

    # Lazy Loading対応：初回アクセス時にインデックスをロード
    await _search_service._ensure_searcher_loaded()
    
    searcher = _search_service.searcher

    # ハイブリッドサーチ実行
    candidates = await _hybrid_search_engine.search_hybrid(
        query=query,
        faiss_index=searcher.index_full,
        embedding_service=searcher.embedding_service,
        items=searcher.items,
        top_k=top_k,
        stage1_top_k=100  # Stage1で取得する候補数
    )

    # 結果を整形
    results = []
    for candidate in candidates:
        # メタデータから栄養情報を取得
        fdc_id = candidate.get("fdc_id")
        item = next((i for i in searcher.items if i.get("fdc_id") == fdc_id), None)

        nutrition_per_100g = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
        if item:
            nutrition = item.get("nutrition", {})
            nutrition_per_100g = {
                "calories": round(nutrition.get("calories", 0), 1),
                "protein": round(nutrition.get("protein_g", 0), 1),
                "fat": round(nutrition.get("fat_g", 0), 1),
                "carbs": round(nutrition.get("carbs_g", 0), 1)
            }

        results.append({
            "fdc_id": str(candidate.get("fdc_id")),
            "description": candidate.get("description", ""),
            "main_name": candidate.get("main_name", ""),
            "descriptors": candidate.get("descriptors", ""),
            "source": candidate.get("source", "unknown"),
            "score": candidate.get("hybrid_score", 0),
            "nutrition_per_100g": nutrition_per_100g
        })

    return {
        "results": results,
        "debug_info": {
            "mode": "hybrid",
            "algorithm": "BM25+Vector_RRF",
            "bm25_weight": _hybrid_search_engine.bm25_weight,
            "vector_weight": _hybrid_search_engine.vector_weight,
            "rrf_k": _hybrid_search_engine.rrf_k
        }
    }



async def _search_hybrid_reranker_mode(query: str, top_k: int) -> Dict[str, Any]:
    """
    Hybrid + Reranker mode: BM25 + FAISS（RRF融合） + Reranking

    HybridSearchEngineを使用してBM25とVectorを組み合わせた検索を実行し、
    さらにRerankerで精度を向上
    """
    if not _hybrid_search_engine:
        raise HTTPException(
            status_code=503,
            detail="Hybrid search engine not initialized"
        )

    # Lazy Loading対応：初回アクセス時にインデックスをロード
    await _search_service._ensure_searcher_loaded()
    
    searcher = _search_service.searcher

    # ハイブリッド + リランキング検索実行
    search_result = await _hybrid_search_engine.search_hybrid_with_reranker(
        query=query,
        faiss_index=searcher.index_full,
        embedding_service=searcher.embedding_service,
        reranker_service=searcher.reranker_service,
        items=searcher.items,
        top_k=top_k,
        stage1_top_k=100  # Stage1で取得する候補数
    )

    # search_hybrid_with_rerankerは {"results": [...], "debug_info": {...}} を返す
    candidates = search_result.get("results", [])

    # 結果を整形
    results = []
    for candidate in candidates:
        # メタデータから栄養情報を取得
        fdc_id = candidate.get("fdc_id")
        item = next((i for i in searcher.items if i.get("fdc_id") == fdc_id), None)

        nutrition_per_100g = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
        if item:
            nutrition = item.get("nutrition", {})
            nutrition_per_100g = {
                "calories": round(nutrition.get("calories", 0), 1),
                "protein": round(nutrition.get("protein_g", 0), 1),
                "fat": round(nutrition.get("fat_g", 0), 1),
                "carbs": round(nutrition.get("carbs_g", 0), 1)
            }

        results.append({
            "fdc_id": str(candidate.get("fdc_id")),
            "description": candidate.get("description", ""),
            "main_name": candidate.get("main_name", ""),
            "descriptors": candidate.get("descriptors", ""),
            "source": candidate.get("source", "unknown"),
            "score": candidate.get("rerank_score", 0),  # Rerankスコアを使用
            "nutrition_per_100g": nutrition_per_100g
        })

    return {
        "results": results,
        "debug_info": {
            "mode": "hybrid_reranker",
            "algorithm": "BM25+Vector_RRF+Reranker",
            "bm25_weight": _hybrid_search_engine.bm25_weight,
            "vector_weight": _hybrid_search_engine.vector_weight,
            "rrf_k": _hybrid_search_engine.rrf_k,
            "reranking_applied": True
        }
    }


@router.get("/retrieve/health", response_model=RetrievalHealthResponse)
async def retrieval_health_check():
    """
    Retrieval APIヘルスチェック

    ## 概要
    Retrieval APIの状態、利用可能な検索モード、インデックスの初期化状態を確認します。

    Returns:
        RetrievalHealthResponse: Retrieval APIの状態情報
    """
    if not _search_service:
        raise HTTPException(
            status_code=503,
            detail="Search service not initialized"
        )

    return {
        "status": "healthy",
        "service": "usda_retrieval_api",
        "index_type": "FAISS",
        "modes": ["fast", "accurate", "hybrid"],
        "searcher_initialized": _search_service.searcher is not None,
        "hybrid_search_enabled": _hybrid_search_engine is not None
    }
