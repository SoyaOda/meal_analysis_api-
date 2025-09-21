from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import time
import requests
import json
from datetime import datetime

# レスポンスモデルをインポート
from app_v2.models.nutrition_search_models import (
    SuggestionResponse, SuggestionErrorResponse, QueryInfo, Suggestion,
    FoodInfo, NutritionPreview, SearchMetadata, SearchStatus, DebugInfo
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Production Elasticsearch VM configuration
ELASTICSEARCH_URL = "http://35.193.16.212:9200"
INDEX_NAME = "mynetdiary_list_support_db"

def elasticsearch_exact_match_first(query: str, size: int = 10) -> dict:
    """
    実際のElasticsearchインデックス構造に基づくexact match優先検索
    
    インデックス構造:
    - original_name (text) + original_name.keyword (keyword)
    - search_name (text) + search_name.keyword (keyword)  
    - description (text) + description.keyword (keyword)
    """
    
    # Step 1: original_name.keyword での完全一致（大文字小文字区別）
    exact_match_body = {
        "query": {
            "term": {
                "original_name.keyword": query
            }
        },
        "size": 1,
        "_source": ["search_name", "description", "original_name", "nutrition", "processing_method"]
    }
    
    try:
        response = requests.post(
            f"{ELASTICSEARCH_URL}/{INDEX_NAME}/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(exact_match_body),
            timeout=5
        )
        response.raise_for_status()
        exact_result = response.json()
        
        # Exact matchが見つかった場合は決定的に返す
        hits = exact_result.get("hits", {}).get("hits", [])
        if hits:
            hit = hits[0]
            formatted_result = {
                "hits": {
                    "total": {"value": 1},
                    "hits": [{
                        "_score": 999.0,  # 決定的スコア
                        "_source": hit["_source"],
                        "_explanation": "exact_match_original_name_keyword"
                    }]
                },
                "took": exact_result.get("took", 0),
                "_debug_info": {
                    "search_strategy": "exact_match_original_name",
                    "query_matched": query,
                    "matched_original_name": hit["_source"]["original_name"]
                }
            }
            return formatted_result
            
    except Exception as e:
        # Exact match失敗時はフォールバックに進む
        pass
    
    # Step 2: 大文字小文字を区別しないexact match
    case_insensitive_body = {
        "query": {
            "bool": {
                "must": [{
                    "match": {
                        "original_name": {
                            "query": query,
                            "operator": "and",
                            "analyzer": "standard"
                        }
                    }
                }],
                "filter": [{
                    "script": {
                        "script": {
                            "source": "doc['original_name.keyword'].value.toLowerCase() == params.query.toLowerCase()",
                            "params": {
                                "query": query
                            }
                        }
                    }
                }]
            }
        },
        "size": 1,
        "_source": ["search_name", "description", "original_name", "nutrition", "processing_method"]
    }
    
    try:
        response = requests.post(
            f"{ELASTICSEARCH_URL}/{INDEX_NAME}/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(case_insensitive_body),
            timeout=5
        )
        response.raise_for_status()
        exact_result = response.json()
        
        hits = exact_result.get("hits", {}).get("hits", [])
        if hits:
            hit = hits[0]
            formatted_result = {
                "hits": {
                    "total": {"value": 1},
                    "hits": [{
                        "_score": 998.0,  # 決定的スコア（大文字小文字区別なし）
                        "_source": hit["_source"],
                        "_explanation": "exact_match_original_name_case_insensitive"
                    }]
                },
                "took": exact_result.get("took", 0),
                "_debug_info": {
                    "search_strategy": "exact_match_original_name_case_insensitive",
                    "query_matched": query,
                    "matched_original_name": hit["_source"]["original_name"]
                }
            }
            return formatted_result
            
    except Exception as e:
        # Case insensitive exact match失敗時もフォールバックに進む
        pass
    
    # Step 3: すべてのexact match方法が失敗した場合、Tierアルゴリズムにフォールバック
    return elasticsearch_search_optimized_fallback(query, size)

def determine_match_type(query: str, explanation: str, original_name: str, 
                        search_name_list: list, description: str) -> str:
    """
    改善されたマッチタイプ判定ロジック
    
    Args:
        query: 検索クエリ
        explanation: Elasticsearchの_explanationフィールド
        original_name: オリジナル名
        search_name_list: 検索名リスト
        description: 説明文
        
    Returns:
        適切なマッチタイプフラグ
    """
    q_lower = query.lower()
    
    # 1. Exact Match（original_nameで完全一致）の判定
    if explanation == "exact_match_original_name_keyword":
        return "exact_match"
    elif explanation == "exact_match_original_name_case_insensitive":
        return "exact_match"
    
    # 2. original_nameでの直接比較（フォールバック）
    if original_name and original_name.lower() == q_lower:
        return "exact_match"
    
    # 3. Tier 1: search_nameでの完全一致
    for name in search_name_list:
        if name.lower() == q_lower:
            return "tier_1_exact"
    
    # 4. Tier 2: descriptionでの完全一致
    if description and description.lower() == q_lower:
        return "tier_2_description"
    
    # 5. Tier 3: search_nameでのプレフィックスマッチ
    for name in search_name_list:
        if name.lower().startswith(q_lower):
            return "tier_3_phrase"
    
    # 6. Tier 4: descriptionでのプレフィックスマッチ
    if description and description.lower().startswith(q_lower):
        return "tier_4_phrase_desc"
    
    # 7. Tier 5: search_nameでの部分マッチ
    for name in search_name_list:
        if q_lower in name.lower():
            return "tier_5_term"
    
    # 8. Tier 6: descriptionでの部分マッチ
    if description and q_lower in description.lower():
        return "tier_6_multi"
    
    # 9. Tier 7: その他（ファジーマッチ）
    return "tier_7_fuzzy"


def elasticsearch_search_optimized_fallback(query: str, size: int = 10) -> dict:
    """元のTierアルゴリズム（フォールバック用）"""
    
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
        result = response.json()
        
        # フォールバック情報を追加
        if "hits" in result:
            result["_debug_info"] = {
                "search_strategy": "tier_algorithm_fallback",
                "reason": "exact_match_not_found"
            }
        
        return result
    except Exception as e:
        return {"error": str(e)}

def elasticsearch_search_optimized(query: str, size: int = 10) -> dict:
    """
    Exact match優先の検索戦略に移行
    新しいelasticsearch_exact_match_first()を呼び出す
    """
    return elasticsearch_exact_match_first(query, size)

@router.get("/suggest", response_model=SuggestionResponse)
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
            explanation = hit.get("_explanation", "")

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

            # 栄養情報（プレビュー用）- 修正：正しいフィールド名を使用
            nutrition = source.get("nutrition", {})
            nutrition_preview = {
                "calories": nutrition.get("calories", 0),
                "protein": nutrition.get("protein", 0),
                "carbohydrates": nutrition.get("carbs", 0),  # 修正: carbs -> carbohydrates
                "fat": nutrition.get("fat", 0),  # 追加: 脂質も含める
                "per_serving": "100g"
            }

            # 改善されたマッチタイプの判定
            match_type = determine_match_type(q.strip(), explanation, original_name, search_name_list, description)

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
                "elasticsearch_query_used": "exact_match_first_with_7_tier_fallback",
                "tier_scoring": {
                    "exact_match_original_name": 999,
                    "exact_match_case_insensitive": 998,
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

        # Pydanticモデルとして返す
        return SuggestionResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Nutrition suggestion failed: {e}", exc_info=True)
        processing_time = int((time.time() - start_time) * 1000)

        error_response = SuggestionErrorResponse(
            query_info=QueryInfo(
                original_query=q,
                processed_query=q,
                timestamp=datetime.now().isoformat() + "Z"
            ),
            suggestions=[],
            metadata=SearchMetadata(
                total_suggestions=0,
                total_hits=0,
                search_time_ms=0,
                processing_time_ms=processing_time,
                elasticsearch_index=INDEX_NAME
            ),
            status=SearchStatus(
                success=False,
                message=f"Suggestion search failed: {str(e)}"
            )
        )
        return JSONResponse(status_code=500, content=error_response.dict())

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