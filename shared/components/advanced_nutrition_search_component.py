"""
Advanced Nutrition Search Component with Multi-tier Performance Strategy

Combines API-based search and direct Elasticsearch for optimal performance
with 20+ word queries. Includes detailed debug logging for each phase.
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from shared.components.base import BaseComponent
from shared.models.nutrition_search_models import NutritionQueryInput, NutritionQueryOutput, NutritionMatch
from shared.config.settings import get_settings
from shared.utils.mynetdiary_utils import validate_ingredient_against_mynetdiary

import logging
import os
logger = logging.getLogger(__name__)

# Word Query API configuration
# Default: Production deployed API with stemming functionality
# Override with WORD_QUERY_API_URL environment variable for local development
API_BASE_URL = os.environ.get(
    "WORD_QUERY_API_URL",
    "https://word-query-api-1077966746907.us-central1.run.app"
)

class AdvancedNutritionSearchComponent(BaseComponent[NutritionQueryInput, NutritionQueryOutput]):
    """
    Advanced Nutrition Search Component using deployed Word Query API

    Always uses the deployed Word Query API with:
    - 7-tier search strategy 
    - Alternative name support (chickpeas ↔ garbanzo beans)
    - Detailed debug logging for each phase
    - Error tolerance with graceful degradation
    """

    def __init__(self, api_base_url: str = API_BASE_URL):
        super().__init__("AdvancedNutritionSearchComponent")
        self.api_base_url = api_base_url
        self.logger.info(f"✅ AdvancedNutritionSearchComponent initialized with API: {api_base_url}")

    async def process(self, input_data: NutritionQueryInput) -> NutritionQueryOutput:
        """
        Word Query API強制使用 - fallback一切なし
        料理名は栄養計算から除外
        """
        start_time = time.time()

        # 食材名のみでWord Query APIを使用（料理名は除外）
        search_terms = input_data.ingredient_names  # dish_namesを含めない
        query_count = len(search_terms)

        if query_count == 0:
            raise ValueError("No ingredient names provided. ingredient_names is empty.")

        self.log_processing_detail("input_query_count", query_count)
        self.log_processing_detail("search_terms", search_terms)
        self.log_processing_detail("excluded_dish_names", input_data.dish_names)  # 除外された料理名をログ出力
        self.log_processing_detail("word_query_api_url", self.api_base_url)

        # Word Query API接続テスト
        await self._validate_word_query_api_connection()

        # Word Query API強制使用 - エラー時は即停止
        results = await self._word_query_api_only_search(search_terms, input_data)

        processing_time = int((time.time() - start_time) * 1000)

        # Add processing information to results
        if results.search_summary:
            results.search_summary["total_processing_time_ms"] = processing_time
            results.search_summary["api_url_used"] = self.api_base_url

        self.log_processing_detail("total_processing_time_ms", processing_time)
        self.log_reasoning("search_completion",
                          f"Completed {query_count} ingredient queries using ONLY Word Query API in {processing_time}ms (dish names excluded from nutrition search)")

        self.logger.info(f"🚀 Word Query API ONLY search completed: {query_count} ingredient queries in {processing_time}ms (dish names excluded)")

        return results

    async def _validate_word_query_api_connection(self):
        """Word Query API接続確認 - 失敗時は即エラー"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_base_url}/health")
                if response.status_code != 200:
                    raise ConnectionError(f"Word Query API health check failed: {response.status_code}")
                self.logger.info(f"✅ Word Query API connection validated: {self.api_base_url}")
        except Exception as e:
            error_msg = f"❌ Word Query API connection failed: {self.api_base_url} - {str(e)}"
            self.logger.error(error_msg)
            raise ConnectionError(error_msg) from e

    async def _word_query_api_only_search(self, search_terms: List[str],
                                        input_data: NutritionQueryInput) -> NutritionQueryOutput:
        """
        Word Query API専用検索 - エラー時は即座に例外発生
        料理名はexact match rate計算から除外
        """
        self.log_processing_detail("search_method", "word_query_api_only")

        start_time = time.time()
        matches = {}
        successful_matches = 0
        exact_matches = 0
        tier_1_exact_matches = 0
        
        # 食材名のみでexact match rateを計算（料理名は除外）
        ingredient_count = len(input_data.ingredient_names)

        # Create parallel API requests
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                tasks = []
                for term in search_terms:
                    task = self._single_api_request_strict(client, term)
                    tasks.append(task)

                # Execute all requests in parallel
                api_responses = await asyncio.gather(*tasks)  # return_exceptions=Falseで例外は即座に伝播

        except Exception as e:
            error_msg = f"Word Query API batch request failed: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        # Process results - すべて成功している前提
        for i, (term, response) in enumerate(zip(search_terms, api_responses)):
            if not response or not response.get("suggestions"):
                error_msg = f"Word Query API returned no suggestions for '{term}'"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            # Convert API response to NutritionMatch
            match_list = self._convert_api_suggestions_to_matches(
                response["suggestions"], term
            )
            matches[term] = match_list
            successful_matches += 1

            # Check match quality for the top result - 食材名のみをexact match rate計算に含める
            if match_list and term in input_data.ingredient_names:
                top_match = match_list[0]
                match_type = top_match.search_metadata.get("match_type", "unknown")

                if match_type == "exact_match":
                    exact_matches += 1
                elif match_type == "tier_1_exact":
                    tier_1_exact_matches += 1

            self.log_processing_detail(f"api_response_{i}", {
                "term": term,
                "is_ingredient": term in input_data.ingredient_names,
                "is_dish": term in input_data.dish_names,
                "suggestion_count": len(response["suggestions"]),
                "top_match_type": match_list[0].search_metadata.get("match_type", "unknown") if match_list else "none",
                "processing_time_ms": response.get("metadata", {}).get("processing_time_ms", 0)
            })

        api_time = int((time.time() - start_time) * 1000)

        return self._build_nutrition_query_output(
            matches, successful_matches, exact_matches, tier_1_exact_matches,
            ingredient_count, api_time, "word_query_api", []
        )

    async def _single_api_request_strict(self, client: httpx.AsyncClient, term: str) -> Dict[str, Any]:
        """厳密なAPI リクエスト - エラー時は即座に例外発生"""
        try:
            response = await client.get(
                f"{self.api_base_url}/api/v1/nutrition/suggest",
                params={
                    "q": term, 
                    "limit": 5, 
                    "debug": "false",
                    "search_context": "meal_analysis",
                    "exclude_uncooked": "true"
                }
            )
            response.raise_for_status()

            result = response.json()

            # レスポンス形式チェック
            if not isinstance(result, dict) or "suggestions" not in result:
                raise ValueError(f"Invalid response format from Word Query API for term '{term}'")

            return result

        except httpx.TimeoutException as e:
            error_msg = f"Word Query API timeout for '{term}': {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except httpx.HTTPStatusError as e:
            error_msg = f"Word Query API HTTP error for '{term}': {e.response.status_code}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Word Query API request failed for '{term}': {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _convert_api_suggestions_to_matches(self, suggestions: List[Dict],
                                          search_term: str) -> List[NutritionMatch]:
        """Convert API suggestions to NutritionMatch objects"""
        matches = []
        for suggestion in suggestions:
            food_info = suggestion.get("food_info", {})
            nutrition_preview = suggestion.get("nutrition_preview", {})

            # 必須の栄養価データを取得し、不足している場合はエラー
            required_nutrients = ["calories", "protein", "fat", "carbohydrates"]
            nutrition_data = {}
            
            for nutrient in required_nutrients:
                if nutrient not in nutrition_preview:
                    raise ValueError(f"Missing required nutrition data '{nutrient}' for ingredient '{search_term}'")
                nutrition_data[nutrient] = nutrition_preview[nutrient]
                
            # carbsキーも追加（標準化）
            nutrition_data["carbs"] = nutrition_data["carbohydrates"]

            match = NutritionMatch(
                id=f"api_{suggestion.get('rank', 1)}",
                name=suggestion.get("suggestion", "Unknown"),
                search_name=food_info.get("search_name", "Unknown"),
                description=food_info.get("description", ""),
                data_type="api_result",
                source_db="mynetdiary_api",
                nutrition=nutrition_data,
                weight=100,  # Default weight
                score=suggestion.get("confidence_score", 0),
                search_metadata={
                    "search_term": search_term,
                    "api_rank": suggestion.get("rank", 1),
                    "match_type": suggestion.get("match_type", "unknown"),
                    "confidence_score": suggestion.get("confidence_score", 0),
                    "alternative_names": suggestion.get("alternative_names", []),
                    "search_method": "word_query_api"
                }
            )
            matches.append(match)

        return matches

    def _build_nutrition_query_output(self, matches: Dict[str, Any],
                                    successful_matches: int,
                                    exact_matches: int,
                                    tier_1_exact_matches: int,
                                    total_searches: int,
                                    search_time_ms: int,
                                    method: str,
                                    errors: List[str]) -> NutritionQueryOutput:
        """Build standardized NutritionQueryOutput with detailed match statistics"""

        total_results = sum(len(result_list) if isinstance(result_list, list) else 1
                           for result_list in matches.values())
        
        # DEBUG: ログで実際の値を確認
        self.logger.info(f"DEBUG EXACT MATCH CALCULATION:")
        self.logger.info(f"  total_searches: {total_searches} (type: {type(total_searches)})")
        self.logger.info(f"  exact_matches: {exact_matches} (type: {type(exact_matches)})")
        self.logger.info(f"  tier_1_exact_matches: {tier_1_exact_matches} (type: {type(tier_1_exact_matches)})")
        self.logger.info(f"  successful_matches: {successful_matches} (type: {type(successful_matches)})")
        
        # Calculate various match rates
        api_response_rate = (successful_matches / total_searches * 100) if total_searches > 0 else 0
        exact_match_rate = (exact_matches / total_searches * 100) if total_searches > 0 else 0
        high_quality_match_rate = ((exact_matches + tier_1_exact_matches) / total_searches * 100) if total_searches > 0 else 0

        # DEBUG: 計算結果もログ出力
        self.logger.info(f"  api_response_rate: {api_response_rate}")
        self.logger.info(f"  exact_match_rate: {exact_match_rate}")
        self.logger.info(f"  high_quality_match_rate: {high_quality_match_rate}")

        search_summary = {
            "total_searches": total_searches,
            "successful_matches": successful_matches,
            "exact_matches": exact_matches,
            "tier_1_exact_matches": tier_1_exact_matches,
            "failed_searches": total_searches - successful_matches,
            
            # Renamed for clarity
            "api_response_rate_percent": round(api_response_rate, 1),
            "exact_match_rate_percent": round(exact_match_rate, 1),
            "high_quality_match_rate_percent": round(high_quality_match_rate, 1),
            
            "search_method": method,
            "search_time_ms": search_time_ms,
            "total_results": total_results,
            "word_query_api_enabled": True,
            "alternative_name_support": True,
            "seven_tier_search": True
        }

        return NutritionQueryOutput(
            matches=matches,
            search_summary=search_summary,
            errors=errors if errors else None
        )