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
    
    # Step 1: original_name.keyword での完全一致（大文字小文字区別）
    step1_start = time.time()
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
    
    # Step 2: 大文字小文字を区別しないexact match
    step2_start = time.time()
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
        step2_time = int((time.time() - step2_start) * 1000)
        
        hits = exact_result.get("hits", {}).get("hits", [])
        if hits:
            logger.info(f"PERFORMANCE: Step2 case-insensitive match found in {step2_time}ms for query: {query}")
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
        else:
            logger.info(f"PERFORMANCE: Step2 case-insensitive match not found in {step2_time}ms for query: {query}")
            
    except Exception as e:
        step2_time = int((time.time() - step2_start) * 1000)
        logger.error(f"PERFORMANCE: Step2 case-insensitive match failed in {step2_time}ms for query: {query}, error: {e}")
        # Case insensitive exact match失敗時もフォールバックに進む
        pass
    
    # Step 3: すべてのexact match方法が失敗した場合、Tierアルゴリズムにフォールバック
    step3_start = time.time()
    logger.info(f"PERFORMANCE: Falling back to Tier algorithm for query: {query}")
    
    result = elasticsearch_search_optimized_fallback(query, size)
    
    step3_time = int((time.time() - step3_start) * 1000)
    total_time = int((time.time() - start_time) * 1000)
    
    logger.info(f"PERFORMANCE: Tier fallback completed in {step3_time}ms, total time: {total_time}ms for query: {query}")
    
    return result

def elasticsearch_exact_match_first_configurable(query: str, size: int = 10, skip_case_insensitive: bool = False) -> dict:
    """
    設定可能なexact match検索
    
    Args:
        query: 検索クエリ
        size: 結果数
        skip_case_insensitive: case-insensitive検索をスキップするかどうか
    """
    
    import time
    start_time = time.time()
    
    # Step 1: original_name.keyword での完全一致（大文字小文字区別）
    step1_start = time.time()
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
    
    # Step 2: 大文字小文字を区別しないexact match（スキップ可能）
    if not skip_case_insensitive:
        step2_start = time.time()
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
            step2_time = int((time.time() - step2_start) * 1000)
            
            hits = exact_result.get("hits", {}).get("hits", [])
            if hits:
                logger.info(f"PERFORMANCE: Step2 case-insensitive match found in {step2_time}ms for query: {query}")
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
            else:
                logger.info(f"PERFORMANCE: Step2 case-insensitive match not found in {step2_time}ms for query: {query}")
                
        except Exception as e:
            step2_time = int((time.time() - step2_start) * 1000)
            logger.error(f"PERFORMANCE: Step2 case-insensitive match failed in {step2_time}ms for query: {query}, error: {e}")
            # Case insensitive exact match失敗時もフォールバックに進む
            pass
    else:
        logger.info(f"PERFORMANCE: Skipping case-insensitive match for query: {query}")
    
    # Step 3: すべてのexact match方法が失敗した場合、Tierアルゴリズムにフォールバック
    step3_start = time.time()
    logger.info(f"PERFORMANCE: Falling back to Tier algorithm for query: {query}")
    
    result = elasticsearch_search_optimized_fallback(query, size)
    
    step3_time = int((time.time() - step3_start) * 1000)
    total_time = int((time.time() - start_time) * 1000)
    
    logger.info(f"PERFORMANCE: Tier fallback completed in {step3_time}ms, total time: {total_time}ms for query: {query}")
    
    return result

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
    elif explanation == "exact_match_original_name_case_insensitive":
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


def elasticsearch_search_optimized_fallback(query: str, size: int = 10) -> dict:
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
    debug: bool = Query(False, description="デバッグ情報を含めるか"),
    skip_exact_match: bool = Query(False, description="exact match検索をスキップしてTier検索を直接実行"),
    skip_case_insensitive: bool = Query(False, description="case-insensitive検索をスキップ")
):
    """
    栄養データベース検索予測API

    成功している7段階Tierシステムを使用した高精度検索予測

    Args:
        q: 検索クエリ（例: "chick", "tom", "brown r"）
        limit: 返す提案数（デフォルト: 10件、最大: 50件）
        debug: デバッグ情報を含めるかどうか
        skip_exact_match: exact match検索をスキップしてTier検索を直接実行
        skip_case_insensitive: case-insensitive検索をスキップ

    Returns:
        検索予測結果のJSON
    """

    start_time = time.time()

    try:
        logger.info(f"Nutrition suggestion request: query='{q}', limit={limit}, skip_exact={skip_exact_match}, skip_case_insensitive={skip_case_insensitive}")

        # バリデーション
        if len(q.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="Query must be at least 2 characters long"
            )

        # 高速パス: Tier検索直行
        if skip_exact_match:
            logger.info(f"PERFORMANCE: Skipping exact match, going directly to Tier algorithm for query: {q}")
            es_start_time = time.time()
            result = elasticsearch_search_optimized_fallback(q.strip(), size=limit)
            es_time = int((time.time() - es_start_time) * 1000)
        else:
            # 通常パス: exact match優先検索
            es_start_time = time.time()
            result = elasticsearch_exact_match_first_configurable(q.strip(), size=limit, skip_case_insensitive=skip_case_insensitive)
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
                "elasticsearch_query_used": "exact_match_first_with_7_tier_fallback" if not skip_exact_match else "direct_tier_fallback",
                "search_strategy_config": {
                    "skip_exact_match": skip_exact_match,
                    "skip_case_insensitive": skip_case_insensitive
                },
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