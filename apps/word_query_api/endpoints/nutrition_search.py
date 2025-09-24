from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import time
import requests
import json
from datetime import datetime

# レスポンスモデルをインポート
from shared.models.nutrition_search_models import (
    SuggestionResponse, SuggestionErrorResponse, QueryInfo, Suggestion,
    FoodInfo, NutritionPreview, SearchMetadata, SearchStatus, DebugInfo
)

logger = logging.getLogger(__name__)
# NLTK stemming functionality
import nltk
from nltk.stem import PorterStemmer
import re

# Initialize Porter Stemmer
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt')

stemmer = PorterStemmer()

def stem_query(query: str) -> str:
    """クエリを語幹化して返す"""
    if not query:
        return ""
    
    # 小文字に変換
    query = query.lower()
    
    # 特殊文字を除去（アルファベットとスペースのみ残す）
    query = re.sub(r'[^a-z\s]', ' ', query)
    
    # 複数のスペースを単一スペースに
    query = re.sub(r'\s+', ' ', query).strip()
    
    # トークン化と語幹化
    tokens = query.split()
    stemmed_tokens = [stemmer.stem(token) for token in tokens]
    
    return ' '.join(stemmed_tokens)

router = APIRouter()

# Production Elasticsearch VM configuration
ELASTICSEARCH_URL = "http://35.193.16.212:9200"
INDEX_NAME = "mynetdiary_converted_tool_calls_list_stemmed"

def elasticsearch_exact_match_first(query: str, size: int = 10) -> dict:
    """
    実際のElasticsearchインデックス構造に基づくexact match優先検索
    
    インデックス構造:
    - original_name (text) + original_name.keyword (keyword)
    - search_name (text) + search_name.keyword (keyword)  
    - description (text) + description.keyword (keyword)
    """
    
    import time
    start_time = time.time()
    
    # Step 1: original_name.exact での完全一致（小文字化）
    step1_start = time.time()
    exact_match_body = {
        "query": {
            "term": {
                "original_name.exact": query.lower()
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
        step1_time = int((time.time() - step1_start) * 1000)
        
        # Exact matchが見つかった場合は決定的に返す
        hits = exact_result.get("hits", {}).get("hits", [])
        if hits:
            logger.info(f"PERFORMANCE: Step1 exact match found in {step1_time}ms for query: {query}")
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
        else:
            logger.info(f"PERFORMANCE: Step1 exact match not found in {step1_time}ms for query: {query}")
            
    except Exception as e:
        step1_time = int((time.time() - step1_start) * 1000)
        logger.error(f"PERFORMANCE: Step1 exact match failed in {step1_time}ms for query: {query}, error: {e}")
        # Exact match失敗時はフォールバックに進む
        pass

    # Step 2: Exact match失敗時、直接Tierアルゴリズムにフォールバック
    step2_start = time.time()
    logger.info(f"PERFORMANCE: Falling back to Tier algorithm for query: {query}")
    
    result = elasticsearch_search_optimized_fallback(query, size)
    
    step2_time = int((time.time() - step2_start) * 1000)
    total_time = int((time.time() - start_time) * 1000)
    
    logger.info(f"PERFORMANCE: Tier fallback completed in {step2_time}ms, total time: {total_time}ms for query: {query}")
    
    return result

def elasticsearch_exact_match_only(query: str, size: int = 10, exclude_uncooked: bool = False) -> dict:
    """
    Exact Matchのみ実行（フォールバックなし）
    
    Args:
        query: 検索クエリ
        size: 結果数
        exclude_uncooked: uncookedを含む食材を除外
    """
    
    import time
    start_time = time.time()
    
    exact_match_body = {
        "query": {
            "bool": {
                "must": [{
                    "term": {
                        "original_name.exact": query.lower()
                    }
                }]
            }
        },
        "size": size,
        "_source": ["search_name", "description", "original_name", "nutrition", "processing_method"]
    }
    
    # uncookedを除外する場合
    if exclude_uncooked:
        exact_match_body["query"]["bool"]["must_not"] = [{
            "wildcard": {
                "original_name": "*uncooked*"
            }
        }]
    
    try:
        response = requests.post(
            f"{ELASTICSEARCH_URL}/{INDEX_NAME}/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(exact_match_body),
            timeout=5
        )
        response.raise_for_status()
        exact_result = response.json()
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Exact matchが見つかった場合
        hits = exact_result.get("hits", {}).get("hits", [])
        if hits:
            logger.info(f"PERFORMANCE: Exact match found in {processing_time}ms for query: {query}")
            # ヒットしたアイテムに決定的スコアを設定
            for hit in hits:
                hit["_score"] = 999.0
                hit["_explanation"] = "exact_match_original_name_keyword"
            
            exact_result["_debug_info"] = {
                "search_strategy": "exact_match_only",
                "query_matched": query,
                "exclude_uncooked": exclude_uncooked
            }
        else:
            logger.info(f"PERFORMANCE: Exact match not found in {processing_time}ms for query: {query}")
            # マッチしなかった場合は空の結果を返す
            exact_result = {
                "hits": {
                    "total": {"value": 0},
                    "hits": []
                },
                "took": exact_result.get("took", 0),
                "_debug_info": {
                    "search_strategy": "exact_match_only",
                    "query_matched": query,
                    "exclude_uncooked": exclude_uncooked,
                    "reason": "no_exact_match_found"
                }
            }
        
        return exact_result
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"PERFORMANCE: Exact match failed in {processing_time}ms for query: {query}, error: {e}")
        return {"error": str(e)}


def determine_match_type(query: str, explanation: str, original_name: str, 
                        search_name_list: list, description: str) -> str:
    """
    語幹化フィールドに対応したマッチタイプ判定ロジック
    
    Args:
        query: 検索クエリ
        explanation: Elasticsearchの_explanationフィールド
        original_name: オリジナル名
        search_name_list: 検索名リスト（元のsearch_name）
        description: 説明文（元のdescription）
        
    Returns:
        適切なマッチタイプフラグ
    """
    q_lower = query.lower()
    stemmed_query = stem_query(query)
    
    # 1. Exact Match（original_nameで完全一致）の判定
    if explanation == "exact_match_original_name_keyword":
        return "exact_match"
    
    # 2. original_nameでの直接比較（フォールバック）
    if original_name and original_name.lower() == q_lower:
        return "exact_match"
    
    # 語幹化ベースの判定（元のフィールドとの比較ではなく、語幹化クエリベース）
    
    # 3. Tier 1: stemmed_search_nameでの完全一致
    for name in search_name_list:
        stemmed_name = stem_query(name) if name else ""
        if stemmed_name == stemmed_query:
            return "tier_1_exact"
    
    # 4. Tier 2: stemmed_descriptionでの完全一致
    if description:
        stemmed_desc = stem_query(description)
        if stemmed_desc == stemmed_query:
            return "tier_2_description"
    
    # 5. Tier 3: stemmed_search_nameでのプレフィックスマッチ
    for name in search_name_list:
        stemmed_name = stem_query(name) if name else ""
        if stemmed_name.startswith(stemmed_query):
            return "tier_3_phrase"
    
    # 6. Tier 4: stemmed_descriptionでのプレフィックスマッチ
    if description:
        stemmed_desc = stem_query(description)
        if stemmed_desc.startswith(stemmed_query):
            return "tier_4_phrase_desc"
    
    # 7. Tier 5: stemmed_search_nameでの部分マッチ
    for name in search_name_list:
        stemmed_name = stem_query(name) if name else ""
        if stemmed_query in stemmed_name:
            return "tier_5_term"
    
    # 8. Tier 6: stemmed_descriptionでの部分マッチ
    if description:
        stemmed_desc = stem_query(description)
        if stemmed_query in stemmed_desc:
            return "tier_6_multi"
    
    # 9. Tier 7: その他（ファジーマッチ）
    return "tier_7_fuzzy"


def elasticsearch_search_optimized_fallback(query: str, size: int = 10, exclude_uncooked: bool = False) -> dict:
    """語幹化フィールドを使用するTierアルゴリズム"""
    
    # クエリを語幹化
    stemmed_query = stem_query(query)
    logger.info(f"STEMMING: '{query}' -> '{stemmed_query}'")
    
    search_body = {
        "query": {
            "bool": {
                "should": [
                    # Tier 1: Exact Match (stemmed_search_name) - Score: 15+
                    {"match_phrase": {"stemmed_search_name": {"query": stemmed_query, "boost": 15}}},

                    # Tier 2: Exact Match (stemmed_description) - Score: 12+
                    {"match_phrase": {"stemmed_description": {"query": stemmed_query, "boost": 12}}},

                    # Tier 3: Phrase Match (stemmed_search_name) - Score: 10+
                    {"match": {"stemmed_search_name": {"query": stemmed_query, "boost": 10}}},

                    # Tier 4: Phrase Match (stemmed_description) - Score: 8+
                    {"match": {"stemmed_description": {"query": stemmed_query, "boost": 8}}},

                    # Tier 5: Term Match (stemmed_search_name.keyword) - Score: 6+
                    {"term": {"stemmed_search_name.keyword": {"value": stemmed_query, "boost": 6}}},

                    # Tier 6: Multi-field match - Score: 4+
                    {"multi_match": {
                        "query": stemmed_query,
                        "fields": ["stemmed_search_name^3", "stemmed_description^2", "original_name"],
                        "boost": 4
                    }},

                    # Tier 7: Fuzzy Match (stemmed_search_name) - Score: 2+
                    {"fuzzy": {"stemmed_search_name": {"value": stemmed_query, "boost": 2}}}
                ]
            }
        },
        "size": size,
        "_source": ["search_name", "stemmed_search_name", "description", "stemmed_description", "original_name", "nutrition", "processing_method"]
    }

    # uncookedを除外する場合
    if exclude_uncooked:
        search_body["query"]["bool"]["must_not"] = [{
            "wildcard": {
                "original_name": "*uncooked*"
            }
        }]

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
                "search_strategy": "stemmed_tier_algorithm",
                "original_query": query,
                "stemmed_query": stemmed_query,
                "exclude_uncooked": exclude_uncooked,
                "reason": "tier_search_requested"
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
    debug: bool = Query(False, description="デバッグ情報を含めるか"),
    search_context: str = Query("meal_analysis", description="検索コンテキスト: meal_analysis（exact match）| word_search（tier検索）"),
    exclude_uncooked: bool = Query(False, description="uncookedを含む食材を除外")
):
    """
    栄養データベース検索予測API

    用途別検索戦略による高精度検索予測

    Args:
        q: 検索クエリ（例: "chick", "tom", "brown r"）
        limit: 返す提案数（デフォルト: 10件、最大: 50件）
        debug: デバッグ情報を含めるかどうか
        search_context: 検索コンテキスト
            - "meal_analysis": 食事分析用（exact match優先、uncookedデフォルト除外）
            - "word_search": ワード検索用（tier検索、全候補表示）
        exclude_uncooked: uncookedを含む食材を除外するか

    Returns:
        検索予測結果のJSON
    """

    start_time = time.time()

    try:
        # search_contextに基づくデフォルト設定
        if search_context == "meal_analysis" and exclude_uncooked is False:
            # meal_analysis時はデフォルトでuncooked除外
            exclude_uncooked = True

        logger.info(f"Nutrition suggestion request: query='{q}', limit={limit}, context={search_context}, exclude_uncooked={exclude_uncooked}")

        # バリデーション
        if len(q.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 2 characters long"
            )

        # search_contextに基づく検索戦略選択
        es_start_time = time.time()
        
        if search_context == "word_search":
            # ワード検索：Tier検索のみ
            logger.info(f"PERFORMANCE: Using Tier search for word_search context: {q}")
            result = elasticsearch_search_optimized_fallback(q.strip(), size=limit, exclude_uncooked=exclude_uncooked)
            search_strategy = "tier_search_only"
            elasticsearch_query_used = "stemmed_tier_algorithm"
        else:
            # meal_analysis（デフォルト）：Exact Matchのみ
            logger.info(f"PERFORMANCE: Using Exact Match for meal_analysis context: {q}")
            result = elasticsearch_exact_match_only(q.strip(), size=limit, exclude_uncooked=exclude_uncooked)
            search_strategy = "exact_match_only"
            elasticsearch_query_used = "exact_match_original_name_only"
        
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

            # 栄養情報（プレビュー用）
            nutrition = source.get("nutrition", {})
            nutrition_preview = {
                "calories": nutrition.get("calories", 0),
                "protein": nutrition.get("protein", 0),
                "carbohydrates": nutrition.get("carbs", 0),
                "fat": nutrition.get("fat", 0),
                "per_serving": "100g"
            }

            # マッチタイプの判定
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
                "elasticsearch_query_used": elasticsearch_query_used,
                "search_strategy_config": {
                    "search_context": search_context,
                    "exclude_uncooked": exclude_uncooked
                },
                "tier_scoring": {
                    "exact_match_original_name": 999,
                    "tier_1_exact_match": 15,
                    "tier_2_exact_description": 12,
                    "tier_3_phrase_match": 10,
                    "tier_4_phrase_description": 8,
                    "tier_5_term_match": 6,
                    "tier_6_multi_field": 4,
                    "tier_7_fuzzy_match": 2
                }
            }

        logger.info(f"Suggestion completed: {len(suggestions)} results in {processing_time}ms using {search_strategy}")

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