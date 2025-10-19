from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging
import time
import requests
import json
from datetime import datetime

# レスポンスモデルをインポート
from shared.models.nutrition_search_models import (
    SuggestionResponse, SuggestionErrorResponse, QueryInfo, Suggestion,
    FoodInfo, NutritionPreview, SearchMetadata, SearchStatus, DebugInfo,
    NutritionHealthCheckResponse
)

# USDA専用の設定をインポート
from apps.usda_word_query_api.config import (
    ELASTICSEARCH_URL, USDA_INDEX_NAME, INGREDIENT_TYPES,
    DEFAULT_SEARCH_SIZE, MAX_SEARCH_SIZE, MIN_QUERY_LENGTH
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


def elasticsearch_usda_tier_search(
    query: str,
    size: int = 10,
    ingredient_types: Optional[List[str]] = None
) -> dict:
    """
    USDA専用のTier検索アルゴリズム

    Args:
        query: 検索クエリ
        size: 結果数
        ingredient_types: 食材タイプフィルタ (["raw"], ["prepared"], ["raw", "prepared"], None)
    """

    # クエリを語幹化
    stemmed_query = stem_query(query)
    logger.info(f"USDA STEMMING: '{query}' -> '{stemmed_query}'")

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
        "_source": [
            "id", "ingredient_type", "original_name", "search_name", "description",
            "stemmed_search_name", "stemmed_description", "ai_description",
            "brand_name", "item_type",  # LLMで生成された新しいフィールド
            "default_unit", "default_calories", "default_nutrition", "unit_to_grams",
            "category", "category_emoji", "food_specific_emoji"
        ]
    }

    # ingredient_typeフィルタを追加
    if ingredient_types:
        search_body["query"]["bool"]["filter"] = [
            {"terms": {"ingredient_type": ingredient_types}}
        ]

    try:
        response = requests.post(
            f"{ELASTICSEARCH_URL}/{USDA_INDEX_NAME}/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(search_body),
            timeout=5
        )
        response.raise_for_status()
        result = response.json()

        # デバッグ情報を追加
        if "hits" in result:
            result["_debug_info"] = {
                "search_strategy": "usda_stemmed_tier_algorithm",
                "original_query": query,
                "stemmed_query": stemmed_query,
                "ingredient_types_filter": ingredient_types,
                "reason": "usda_tier_search"
            }

        return result
    except Exception as e:
        logger.error(f"USDA Elasticsearch search failed: {e}")
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

    # 語幹化ベースの判定

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


@router.get("/suggest", response_model=SuggestionResponse)
async def suggest_usda_foods(
    q: str = Query(..., min_length=MIN_QUERY_LENGTH, description="検索クエリ（最小2文字）"),
    limit: int = Query(DEFAULT_SEARCH_SIZE, ge=1, le=MAX_SEARCH_SIZE, description="提案数（1-50件）"),
    debug: bool = Query(False, description="デバッグ情報を含めるか"),
    ingredient_type: Optional[str] = Query(None, description="食材タイプフィルタ: raw | prepared | all")
):
    """
    USDAデータベース検索予測API

    USDA FNDDS統合データベースからの高精度検索予測

    Args:
        q: 検索クエリ（例: "chicken", "rice", "bread"）
        limit: 返す提案数（デフォルト: 10件、最大: 50件）
        debug: デバッグ情報を含めるかどうか
        ingredient_type: 食材タイプフィルタ
            - "raw": 生食材のみ
            - "prepared": 準備済み食材のみ
            - "all" or None: 両方

    Returns:
        検索予測結果のJSON
    """

    start_time = time.time()

    try:
        logger.info(f"USDA suggestion request: query='{q}', limit={limit}, ingredient_type={ingredient_type}")

        # バリデーション
        if len(q.strip()) < MIN_QUERY_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Query must be at least {MIN_QUERY_LENGTH} characters long"
            )

        # ingredient_typeフィルタの設定
        ingredient_types_filter = None
        if ingredient_type and ingredient_type != "all":
            if ingredient_type in INGREDIENT_TYPES:
                ingredient_types_filter = [ingredient_type]
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid ingredient_type. Must be one of: {', '.join(INGREDIENT_TYPES + ['all'])}"
                )

        # Elasticsearch検索実行
        es_start_time = time.time()
        result = elasticsearch_usda_tier_search(
            q.strip(),
            size=limit,
            ingredient_types=ingredient_types_filter
        )
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
            if isinstance(search_name_array, list) and len(search_name_array) > 0:
                search_name = search_name_array[0]
                search_name_list = search_name_array
            else:
                search_name = search_name_array if search_name_array else "Unknown"
                search_name_list = [search_name] if search_name else ["Unknown"]

            description = source.get("description", "")
            original_name = source.get("original_name", "")

            # USDA固有フィールド
            ingredient_type_value = source.get("ingredient_type", "unknown")
            ai_description = source.get("ai_description")

            # 栄養情報（USDA形式: default_nutrition）
            default_nutrition = source.get("default_nutrition", {})

            # プレビュー用に変換（1gあたり → 100gあたり）
            nutrition_preview = {
                "calories": round(default_nutrition.get("calorie", 0) * 100, 2),
                "protein": round(default_nutrition.get("Protein_g", 0) * 100, 2),
                "carbohydrates": round(default_nutrition.get("Total_Carbs_g", 0) * 100, 2),
                "fat": round(default_nutrition.get("Total_Fat_g", 0) * 100, 2),
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
                    "original_name": original_name,
                    "ingredient_type": ingredient_type_value,  # USDA固有（raw/prepared）
                    "ai_description": ai_description,  # USDA固有
                    "brand_name": source.get("brand_name"),  # LLMで生成されたブランド名
                    "item_type": source.get("item_type")  # LLMで生成された食材タイプ（raw_ingredient/processed_ingredient/prepared_dish）
                },
                "nutrition_preview": nutrition_preview,
                "alternative_names": [name for name in search_name_list if name != search_name][:3],

                # USDA形式の栄養データフィールド（1gあたり）
                "default_unit": source.get("default_unit"),
                "default_calories": source.get("default_calories"),
                "default_nutrition": default_nutrition,
                "unit_to_grams": source.get("unit_to_grams"),

                # カテゴリ情報
                "category": source.get("category"),
                "category_emoji": source.get("category_emoji"),
                "food_specific_emoji": source.get("food_specific_emoji")
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
                "elasticsearch_index": USDA_INDEX_NAME
            },
            "status": {
                "success": True,
                "message": "USDA suggestions generated successfully"
            }
        }

        # デバッグ情報追加
        if debug:
            response_data["debug_info"] = {
                "elasticsearch_query_used": "usda_stemmed_tier_algorithm",
                "search_strategy_config": {
                    "ingredient_type_filter": ingredient_type,
                    "ingredient_types_applied": ingredient_types_filter
                },
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

        logger.info(f"USDA suggestion completed: {len(suggestions)} results in {processing_time}ms")

        # Pydanticモデルとして返す
        return SuggestionResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"USDA suggestion failed: {e}", exc_info=True)
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
                elasticsearch_index=USDA_INDEX_NAME
            ),
            status=SearchStatus(
                success=False,
                message=f"USDA suggestion search failed: {str(e)}"
            )
        )
        return JSONResponse(status_code=500, content=error_response.dict())


@router.get("/suggest/health", response_model=NutritionHealthCheckResponse)
async def usda_suggestion_health_check():
    """USDA検索予測APIのヘルスチェック"""
    try:
        # 簡単なテストクエリ
        test_result = elasticsearch_usda_tier_search("test", size=1)

        return NutritionHealthCheckResponse(
            status="healthy" if "error" not in test_result else "unhealthy",
            service="usda_suggestion_api",
            elasticsearch_index=USDA_INDEX_NAME,
            algorithm="usda_7_tier_optimized",
            test_query_success="error" not in test_result
        )

    except Exception as e:
        logger.error(f"USDA health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


@router.get("/stats")
async def get_usda_stats():
    """USDA統合データベースの統計情報を取得"""
    try:
        # インデックスの統計情報を取得
        count_response = requests.get(
            f"{ELASTICSEARCH_URL}/{USDA_INDEX_NAME}/_count",
            timeout=5
        )
        count_response.raise_for_status()
        count_result = count_response.json()
        doc_count = count_result.get("count", 0)

        # ingredient_type別の集計
        agg_body = {
            "size": 0,
            "aggs": {
                "by_ingredient_type": {
                    "terms": {"field": "ingredient_type", "size": 10}
                }
            }
        }

        agg_response = requests.post(
            f"{ELASTICSEARCH_URL}/{USDA_INDEX_NAME}/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(agg_body),
            timeout=5
        )
        agg_response.raise_for_status()
        agg_result = agg_response.json()

        buckets = agg_result.get("aggregations", {}).get("by_ingredient_type", {}).get("buckets", [])
        ingredient_type_stats = {bucket["key"]: bucket["doc_count"] for bucket in buckets}

        return {
            "status": "success",
            "index_name": USDA_INDEX_NAME,
            "total_documents": doc_count,
            "ingredient_type_breakdown": ingredient_type_stats,
            "timestamp": datetime.now().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve stats: {str(e)}"
        )
