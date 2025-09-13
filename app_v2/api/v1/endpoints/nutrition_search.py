from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import time
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Production Elasticsearch VM configuration
ELASTICSEARCH_URL = "http://35.193.16.212:9200"
INDEX_NAME = "mynetdiary_list_support_db"

def elasticsearch_search_optimized(query: str, size: int = 10) -> dict:
    """成功している7段階検索戦略（test_mynetdiary_list_support_optimized.pyから）"""

    search_body = {
        "query": {
            "bool": {
                "should": [
                    # Tier 1: Exact Match (search_name配列要素) - Score: 15+
                    {"match_phrase": {"search_name": {"query": query, "boost": 15}}},

                    # Tier 2: Exact Match (description) - Score: 12+
                    {"match_phrase": {"description": {"query": query, "boost": 12}}},

                    # Tier 3: Phrase Match (search_name配列要素) - Score: 10+
                    {"match": {"search_name": {"query": query, "boost": 10}}},

                    # Tier 4: Phrase Match (description) - Score: 8+
                    {"match": {"description": {"query": query, "boost": 8}}},

                    # Tier 5: Term Match (search_name要素の完全一致) - Score: 6+
                    {"term": {"search_name.keyword": {"value": query, "boost": 6}}},

                    # Tier 6: Multi-field match - Score: 4+
                    {"multi_match": {
                        "query": query,
                        "fields": ["search_name^3", "description^2", "original_name"],
                        "boost": 4
                    }},

                    # Tier 7: Fuzzy Match (search_name配列要素) - Score: 2+
                    {"fuzzy": {"search_name": {"value": query, "boost": 2}}}
                ]
            }
        },
        "size": size,
        "_source": ["search_name", "description", "original_name", "nutrition", "processing_method"]
    }

    try:
        response = requests.post(
            f"{ELASTICSEARCH_URL}/{INDEX_NAME}/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(search_body),
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@router.get("/suggest")
async def suggest_foods(
    q: str = Query(..., min_length=2, description="検索クエリ（最小2文字）"),
    limit: int = Query(10, ge=1, le=50, description="提案数（1-50件）"),
    debug: bool = Query(False, description="デバッグ情報を含めるか")
):
    """
    栄養データベース検索予測API

    成功している7段階Tierシステムを使用した高精度検索予測

    Args:
        q: 検索クエリ（例: "chick", "tom", "brown r"）
        limit: 返す提案数（デフォルト: 10件、最大: 50件）
        debug: デバッグ情報を含めるかどうか

    Returns:
        検索予測結果のJSON
    """

    start_time = time.time()

    try:
        logger.info(f"Nutrition suggestion request: query='{q}', limit={limit}")

        # バリデーション
        if len(q.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 2 characters long"
            )

        # Elasticsearch検索実行
        es_start_time = time.time()
        result = elasticsearch_search_optimized(q.strip(), size=limit)
        es_time = int((time.time() - es_start_time) * 1000)

        if "error" in result:
            raise Exception(f"Elasticsearch error: {result['error']}")

        # 結果処理
        hits = result.get("hits", {}).get("hits", [])
        total_hits = result.get("hits", {}).get("total", {}).get("value", 0)

        suggestions = []
        for i, hit in enumerate(hits, 1):
            source = hit["_source"]
            score = hit["_score"]

            # 基本情報
            search_name_array = source.get("search_name", ["Unknown"])
            # search_nameが配列の場合は最初の要素、文字列の場合はそのまま使用
            if isinstance(search_name_array, list) and len(search_name_array) > 0:
                search_name = search_name_array[0]
                search_name_list = search_name_array
            else:
                search_name = search_name_array if search_name_array else "Unknown"
                search_name_list = [search_name] if search_name else ["Unknown"]
            description = source.get("description", "")
            original_name = source.get("original_name", "")

            # 栄養情報（プレビュー用）
            nutrition = source.get("nutrition", {})
            nutrition_preview = {
                "calories": nutrition.get("calories", 0),
                "protein": nutrition.get("protein", 0),
                "per_serving": "100g"
            }

            # マッチタイプの判定
            match_type = "fuzzy_match"
            q_lower = q.lower()
            for name in search_name_list:
                if name.lower() == q_lower:
                    match_type = "exact_match"
                    break
                elif name.lower().startswith(q_lower):
                    match_type = "prefix_match"
                elif q_lower in name.lower():
                    match_type = "partial_match"

            # 信頼度スコア（0-100）
            confidence_score = min(100, (score / 15) * 100)

            suggestion = {
                "rank": i,
                "suggestion": search_name,
                "match_type": match_type,
                "confidence_score": round(confidence_score, 1),
                "food_info": {
                    "search_name": search_name,
                    "search_name_list": search_name_list,
                    "description": description,
                    "original_name": original_name
                },
                "nutrition_preview": nutrition_preview,
                "alternative_names": [name for name in search_name_list if name != search_name][:3]
            }

            suggestions.append(suggestion)

        # レスポンス構築
        processing_time = int((time.time() - start_time) * 1000)
        response_data = {
            "query_info": {
                "original_query": q,
                "processed_query": q.strip(),
                "timestamp": datetime.now().isoformat() + "Z",
                "suggestion_type": "autocomplete"
            },
            "suggestions": suggestions,
            "metadata": {
                "total_suggestions": len(suggestions),
                "total_hits": total_hits,
                "search_time_ms": es_time,
                "processing_time_ms": processing_time,
                "elasticsearch_index": INDEX_NAME
            },
            "status": {
                "success": True,
                "message": "Suggestions generated successfully"
            }
        }

        # デバッグ情報追加
        if debug:
            response_data["debug_info"] = {
                "elasticsearch_query_used": "7_tier_optimized_search_name_list",
                "tier_scoring": {
                    "tier_1_exact_match": 15,
                    "tier_2_exact_description": 12,
                    "tier_3_phrase_match": 10,
                    "tier_4_phrase_description": 8,
                    "tier_5_term_match": 6,
                    "tier_6_multi_field": 4,
                    "tier_7_fuzzy_match": 2
                }
            }

        logger.info(f"Suggestion completed: {len(suggestions)} results in {processing_time}ms")

        return JSONResponse(
            status_code=200,
            content=response_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Nutrition suggestion failed: {e}", exc_info=True)
        processing_time = int((time.time() - start_time) * 1000)

        return JSONResponse(
            status_code=500,
            content={
                "query_info": {
                    "original_query": q,
                    "timestamp": datetime.now().isoformat() + "Z"
                },
                "suggestions": [],
                "metadata": {
                    "total_suggestions": 0,
                    "processing_time_ms": processing_time
                },
                "status": {
                    "success": False,
                    "message": f"Suggestion search failed: {str(e)}"
                }
            }
        )

@router.get("/suggest/health")
async def suggestion_health_check():
    """検索予測APIのヘルスチェック"""
    try:
        # 簡単なテストクエリ
        test_result = elasticsearch_search_optimized("test", size=1)

        return {
            "status": "healthy" if "error" not in test_result else "unhealthy",
            "service": "nutrition_suggestion_api",
            "elasticsearch_index": INDEX_NAME,
            "algorithm": "7_tier_optimized",
            "test_query_success": "error" not in test_result
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )