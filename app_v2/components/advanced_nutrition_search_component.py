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

from ..components.base import BaseComponent
from ..models.nutrition_search_models import NutritionQueryInput, NutritionQueryOutput, NutritionMatch
from ..config.settings import get_settings
from ..utils.mynetdiary_utils import validate_ingredient_against_mynetdiary

import logging
logger = logging.getLogger(__name__)

# Word Query API configuration
API_BASE_URL = "https://meal-analysis-api-v2-1077966746907.us-central1.run.app"

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
        Main processing using deployed Word Query API
        """
        start_time = time.time()

        search_terms = input_data.get_all_search_terms()
        query_count = len(search_terms)

        self.log_processing_detail("input_query_count", query_count)
        self.log_processing_detail("search_terms", search_terms)

        # Use API for all queries (simplified approach)
        results = await self._api_search(search_terms, input_data)

        processing_time = int((time.time() - start_time) * 1000)

        # Add processing information to results
        if results.search_summary:
            results.search_summary["total_processing_time_ms"] = processing_time

        self.log_processing_detail("total_processing_time_ms", processing_time)
        self.log_reasoning("search_completion",
                          f"Completed {query_count} queries using Word Query API in {processing_time}ms")

        self.logger.info(f"🚀 Word Query API search completed: {query_count} queries in {processing_time}ms")

        return results

    async def _api_search(self, search_terms: List[str],
                         input_data: NutritionQueryInput) -> NutritionQueryOutput:
        """
        API search using deployed Word Query API
        """
        self.log_processing_detail("search_method", "word_query_api")

        start_time = time.time()
        matches = {}
        errors = []
        successful_matches = 0

        # Create parallel API requests
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []
            for term in search_terms:
                task = self._single_api_request(client, term)
                tasks.append(task)

            # Execute all requests in parallel
            api_responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, (term, response) in enumerate(zip(search_terms, api_responses)):
            if isinstance(response, Exception):
                error_msg = f"API request failed for '{term}': {str(response)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
            elif response and response.get("suggestions"):
                # Convert API response to NutritionMatch
                matches[term] = self._convert_api_suggestions_to_matches(
                    response["suggestions"], term
                )
                successful_matches += 1

                self.log_processing_detail(f"api_response_{i}", {
                    "term": term,
                    "suggestion_count": len(response["suggestions"]),
                    "processing_time_ms": response.get("metadata", {}).get("processing_time_ms", 0)
                })
            else:
                self.logger.warning(f"No results for '{term}'")

        api_time = int((time.time() - start_time) * 1000)

        return self._build_nutrition_query_output(
            matches, successful_matches, len(search_terms), api_time,
            "word_query_api", errors
        )

    async def _single_api_request(self, client: httpx.AsyncClient, term: str) -> Dict[str, Any]:
        """Single API request with error handling"""
        try:
            response = await client.get(
                f"{self.api_base_url}/api/v1/nutrition/suggest",
                params={"q": term, "limit": 5, "debug": "false"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"API request failed for '{term}': {e}")
            raise

    def _convert_api_suggestions_to_matches(self, suggestions: List[Dict],
                                          search_term: str) -> List[NutritionMatch]:
        """Convert API suggestions to NutritionMatch objects"""
        matches = []
        for suggestion in suggestions:
            food_info = suggestion.get("food_info", {})
            nutrition_preview = suggestion.get("nutrition_preview", {})

            match = NutritionMatch(
                id=f"api_{suggestion.get('rank', 1)}",
                name=suggestion.get("suggestion", "Unknown"),
                search_name=food_info.get("search_name", "Unknown"),
                description=food_info.get("description", ""),
                data_type="api_result",
                source_db="mynetdiary_api",
                nutrition={
                    "calories": nutrition_preview.get("calories", 0),
                    "protein": nutrition_preview.get("protein", 0)
                },
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
                                    total_searches: int,
                                    search_time_ms: int,
                                    method: str,
                                    errors: List[str]) -> NutritionQueryOutput:
        """Build standardized NutritionQueryOutput"""

        total_results = sum(len(result_list) if isinstance(result_list, list) else 1
                           for result_list in matches.values())
        match_rate = (successful_matches / total_searches * 100) if total_searches > 0 else 0

        search_summary = {
            "total_searches": total_searches,
            "successful_matches": successful_matches,
            "failed_searches": total_searches - successful_matches,
            "match_rate_percent": round(match_rate, 1),
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