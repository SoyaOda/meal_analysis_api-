#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
USDA Food Retrieval API Router
FAISS検索エンドポイント（fastモードとaccurateモード）
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any, Tuple
import logging
import time
import hashlib
from datetime import datetime
from collections import OrderedDict
from threading import Lock

from ..models.response_models import (
    RetrievalResponse,
    RetrievalMetadata,
    RetrievalStatus,
    RetrievalHealthResponse
)
from ..services.portions_normalizer import normalize_portions_for_food
from ..services.analytics import get_analytics
from dataclasses import asdict
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================
# Response Cache with TTL
# ============================================================
class TTLCache:
    """Thread-safe LRU cache with TTL (Time To Live)"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """
        Args:
            max_size: Maximum number of cached items
            ttl_seconds: Time to live in seconds (default: 5 minutes)
        """
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _make_key(self, query: str, mode: str, top_k: int, offset: int) -> str:
        """Generate cache key from search parameters"""
        key_str = f"{query.lower().strip()}:{mode}:{top_k}:{offset}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, query: str, mode: str, top_k: int, offset: int) -> Optional[Dict]:
        """Get cached result if exists and not expired"""
        key = self._make_key(query, mode, top_k, offset)
        with self._lock:
            if key in self._cache:
                result, timestamp = self._cache[key]
                if time.time() - timestamp < self._ttl:
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return result
                else:
                    # Expired, remove
                    del self._cache[key]
            self._misses += 1
            return None

    def set(self, query: str, mode: str, top_k: int, offset: int, result: Dict):
        """Cache a search result"""
        key = self._make_key(query, mode, top_k, offset)
        with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = (result, time.time())

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics"""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / total, 3) if total > 0 else 0,
                "ttl_seconds": self._ttl
            }


# Global cache instance (100 items, 5 minute TTL)
_response_cache = TTLCache(max_size=100, ttl_seconds=300)

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
    include_units: bool = Query(False, description="利用可能な単位リストを含めるか（正規化済み）"),
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
        include_units: 利用可能な単位リストを含めるか（正規化済み、g/cup/oz等）
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

        # 短いクエリの最適化: 3文字未満のクエリではBM25スコアが0になりやすいため
        # hybrid/hybrid_rerankerモードの場合はfast（FAISS only）に自動切り替え
        original_mode = mode
        query_length = len(q.strip())
        if query_length < 3 and mode in ["hybrid", "hybrid_reranker"]:
            logger.info(f"🔄 Short query optimization: switching from '{mode}' to 'fast' for query='{q}' (length={query_length})")
            mode = "fast"

        # キャッシュチェック（include_nutritionとinclude_unitsはポストプロセスなので基本パラメータでキャッシュ）
        cached_result = _response_cache.get(q, mode, top_k, offset)
        if cached_result is not None:
            logger.info(f"✅ Cache hit for query='{q}'")
            # キャッシュされた結果を使用（ポストプロセスは適用済み）
            processing_time_ms = int((time.time() - start_time) * 1000)
            response = RetrievalResponse(
                query=q,
                mode=mode,
                results=cached_result["results"],
                metadata=RetrievalMetadata(
                    total_results=len(cached_result["results"]),
                    search_time_ms=processing_time_ms,
                    index_type="FAISS",
                    algorithm=cached_result.get("algorithm", "cached"),
                    offset=offset,
                    has_more=cached_result.get("has_more", False),
                    total_available=cached_result.get("total_available")
                ),
                status=RetrievalStatus(
                    success=True,
                    message="Search completed successfully (cached)"
                ),
                debug_info=None
            )

            # キャッシュヒットの検索ログを記録
            analytics = get_analytics()
            if analytics:
                try:
                    await analytics.log_search(
                        query=q,
                        results_count=len(cached_result["results"]),
                        mode=mode,
                        latency_ms=processing_time_ms,
                        offset=offset,
                        top_k=top_k,
                        cache_hit=True
                    )
                except Exception as log_err:
                    logger.warning(f"Failed to log search analytics: {log_err}")

            return response

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

        # 単位情報を追加（include_units=trueの場合）
        if include_units:
            # Lazy Loading対応：searcherのitemsから各食品のportions情報を取得
            searcher = _search_service.searcher
            for item in result.get("results", []):
                fdc_id = item.get("fdc_id")
                # items内から該当する食品を検索
                food_item = next(
                    (i for i in searcher.items if str(i.get("fdc_id")) == str(fdc_id)),
                    None
                )
                if food_item:
                    portions = food_item.get("portions", [])
                    normalized_units = normalize_portions_for_food(portions, include_gram=True)
                    item["available_units"] = [asdict(u) for u in normalized_units]
                else:
                    # 見つからない場合はgのみ
                    item["available_units"] = [
                        {"name": "g", "abbreviation": "g", "grams_per_unit": 1.0, "original_description": "gram (base unit)", "is_base_unit": True}
                    ]

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

        # キャッシュに保存（ポストプロセス適用後の結果を保存）
        cache_data = {
            "results": result.get("results", []),
            "algorithm": "Stage1" if mode == "fast" else "Stage1+Stage2_Rerank",
            "has_more": has_more,
            "total_available": total_available if total_available > 0 else None
        }
        _response_cache.set(q, mode, top_k, offset, cache_data)

        # 検索ログを記録（非同期、ノンブロッキング）
        analytics = get_analytics()
        if analytics:
            try:
                await analytics.log_search(
                    query=q,
                    results_count=len(result.get("results", [])),
                    mode=mode,
                    latency_ms=processing_time_ms,
                    offset=offset,
                    top_k=top_k,
                    cache_hit=False
                )
            except Exception as log_err:
                logger.warning(f"Failed to log search analytics: {log_err}")

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


class SelectionLogRequest(BaseModel):
    """選択ログリクエスト"""
    query: str
    fdc_id: str
    food_name: str
    result_position: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class SelectionLogResponse(BaseModel):
    """選択ログレスポンス"""
    success: bool
    message: str


@router.post("/retrieve/selection", response_model=SelectionLogResponse)
async def log_food_selection(request: SelectionLogRequest) -> SelectionLogResponse:
    """
    食品選択イベントをログに記録

    ## 概要
    ユーザーが検索結果から食品を選択した際にこのエンドポイントを呼び出すことで、
    検索精度向上のためのデータを収集します。

    Args:
        request: 選択情報（検索クエリ、選択したFDC ID、食品名、結果位置等）

    Returns:
        SelectionLogResponse: ログ記録の成否
    """
    analytics = get_analytics()
    if not analytics:
        logger.warning("Analytics not initialized, selection not logged")
        return SelectionLogResponse(
            success=False,
            message="Analytics not available"
        )

    try:
        await analytics.log_selection(
            query=request.query,
            selected_fdc_id=request.fdc_id,
            selected_food_name=request.food_name,
            result_position=request.result_position,
            user_id=request.user_id,
            session_id=request.session_id
        )
        logger.info(f"📊 Selection logged: query='{request.query}', fdc_id={request.fdc_id}, position={request.result_position}")
        return SelectionLogResponse(
            success=True,
            message="Selection logged successfully"
        )
    except Exception as e:
        logger.error(f"Failed to log selection: {e}")
        return SelectionLogResponse(
            success=False,
            message=f"Failed to log selection: {str(e)}"
        )


@router.get("/retrieve/cache/stats")
async def cache_stats():
    """
    キャッシュ統計情報を取得

    ## 概要
    レスポンスキャッシュのヒット率、サイズ、TTLなどの統計情報を返します。

    Returns:
        キャッシュ統計情報
    """
    return _response_cache.stats()


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
