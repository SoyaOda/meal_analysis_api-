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
from elasticsearch import Elasticsearch

from ..components.base import BaseComponent
from ..models.nutrition_search_models import NutritionQueryInput, NutritionQueryOutput, NutritionMatch
from ..config.settings import get_settings
from ..utils.mynetdiary_utils import validate_ingredient_against_mynetdiary

import logging
logger = logging.getLogger(__name__)

# Production Elasticsearch VM configuration (from query_api_deploy branch)
ELASTICSEARCH_URL = "http://35.193.16.212:9200"
INDEX_NAME = "mynetdiary_list_support_db"
API_BASE_URL = "https://meal-analysis-api-v2-1077966746907.us-central1.run.app"

class AdvancedNutritionSearchComponent(BaseComponent[NutritionQueryInput, NutritionQueryOutput]):
    """
    Advanced Nutrition Search Component with Multi-tier Performance Strategy

    Performance routing based on query count:
    - ≤5 queries: Parallel API search
    - 6-15 queries: Batched API search
    - 16+ queries: Direct Elasticsearch batch search

    Features:
    - 7-tier search strategy from query_api_deploy branch
    - Alternative name support (chickpeas ↔ garbanzo beans)
    - Detailed debug logging for each phase
    - Error tolerance with graceful degradation
    """

    def __init__(self,
                 api_base_url: str = API_BASE_URL,
                 elasticsearch_url: str = ELASTICSEARCH_URL):
        super().__init__("AdvancedNutritionSearchComponent")

        self.api_base_url = api_base_url
        self.elasticsearch_url = elasticsearch_url

        # Initialize Elasticsearch client for direct search
        try:
            self.es_client = Elasticsearch([elasticsearch_url])
            if self.es_client.ping():
                self.logger.info(f"✅ Elasticsearch connected: {elasticsearch_url}")
            else:
                self.logger.error(f"❌ Elasticsearch ping failed: {elasticsearch_url}")
                raise ConnectionError(f"Cannot connect to Elasticsearch at {elasticsearch_url}")
        except Exception as e:
            self.logger.error(f"❌ Elasticsearch initialization failed: {e}")
            raise RuntimeError(f"Elasticsearch initialization failed: {e}") from e

    async def process(self, input_data: NutritionQueryInput) -> NutritionQueryOutput:
        """
        Main processing with intelligent routing based on query count
        """
        start_time = time.time()

        search_terms = input_data.get_all_search_terms()
        query_count = len(search_terms)

        self.log_processing_detail("input_query_count", query_count)
        self.log_processing_detail("search_terms", search_terms)

        # Intelligent routing based on query count
        if query_count <= 5:
            strategy = "parallel_api"
            results = await self._parallel_api_search(search_terms, input_data)
        elif query_count <= 15:
            strategy = "batched_api"
            results = await self._batched_api_search(search_terms, input_data, batch_size=5)
        else:
            strategy = "elasticsearch_batch"
            results = await self._elasticsearch_batch_search(search_terms, input_data)

        processing_time = int((time.time() - start_time) * 1000)

        # Add strategy information to results
        if results.search_summary:
            results.search_summary["performance_strategy"] = strategy
            results.search_summary["total_processing_time_ms"] = processing_time

        self.log_processing_detail("selected_strategy", strategy)
        self.log_processing_detail("total_processing_time_ms", processing_time)
        self.log_reasoning("strategy_selection",
                          f"Selected '{strategy}' for {query_count} queries, "
                          f"completed in {processing_time}ms")

        self.logger.info(f"🚀 Advanced search completed: {query_count} queries using '{strategy}' in {processing_time}ms")

        return results

    async def _parallel_api_search(self, search_terms: List[str],
                                 input_data: NutritionQueryInput) -> NutritionQueryOutput:
        """
        Parallel API search for ≤5 queries
        """
        self.log_processing_detail("api_search_method", "parallel")

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
            "parallel_api", errors
        )

    async def _batched_api_search(self, search_terms: List[str],
                                input_data: NutritionQueryInput,
                                batch_size: int = 5) -> NutritionQueryOutput:
        """
        Batched API search for 6-15 queries
        """
        self.log_processing_detail("api_search_method", "batched")
        self.log_processing_detail("batch_size", batch_size)

        start_time = time.time()
        matches = {}
        errors = []
        successful_matches = 0

        # Split into batches
        batches = [search_terms[i:i+batch_size] for i in range(0, len(search_terms), batch_size)]
        self.log_processing_detail("batch_count", len(batches))

        for batch_index, batch in enumerate(batches):
            batch_start = time.time()

            async with httpx.AsyncClient(timeout=30.0) as client:
                tasks = [self._single_api_request(client, term) for term in batch]
                batch_responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Process batch results
            for term, response in zip(batch, batch_responses):
                if isinstance(response, Exception):
                    error_msg = f"API request failed for '{term}': {str(response)}"
                    errors.append(error_msg)
                elif response and response.get("suggestions"):
                    matches[term] = self._convert_api_suggestions_to_matches(
                        response["suggestions"], term
                    )
                    successful_matches += 1

            batch_time = int((time.time() - batch_start) * 1000)
            self.log_processing_detail(f"batch_{batch_index}_time_ms", batch_time)

            # Small delay between batches to avoid overwhelming API
            await asyncio.sleep(0.05)

        total_time = int((time.time() - start_time) * 1000)

        return self._build_nutrition_query_output(
            matches, successful_matches, len(search_terms), total_time,
            "batched_api", errors
        )

    async def _elasticsearch_batch_search(self, search_terms: List[str],
                                        input_data: NutritionQueryInput) -> NutritionQueryOutput:
        """
        Direct Elasticsearch batch search for 16+ queries using msearch
        """
        if not self.es_client:
            raise RuntimeError("Elasticsearch client is not available for batch search")

        self.log_processing_detail("search_method", "elasticsearch_batch")

        start_time = time.time()
        matches = {}
        errors = []
        successful_matches = 0

        # Build multi-search request body
        search_body = []
        for term in search_terms:
            # Index specification
            search_body.append({"index": INDEX_NAME})

            # Query using 7-tier strategy from query_api_deploy
            search_body.append({
                "query": {
                    "bool": {
                        "should": [
                            # Tier 1: Exact Match (search_name array elements) - Score: 15+
                            {"match_phrase": {"search_name": {"query": term, "boost": 15}}},

                            # Tier 2: Exact Match (description) - Score: 12+
                            {"match_phrase": {"description": {"query": term, "boost": 12}}},

                            # Tier 3: Phrase Match (search_name array elements) - Score: 10+
                            {"match": {"search_name": {"query": term, "boost": 10}}},

                            # Tier 4: Phrase Match (description) - Score: 8+
                            {"match": {"description": {"query": term, "boost": 8}}},

                            # Tier 5: Term Match (complete match of search_name elements) - Score: 6+
                            {"term": {"search_name.keyword": {"value": term, "boost": 6}}},

                            # Tier 6: Multi-field match - Score: 4+
                            {"multi_match": {
                                "query": term,
                                "fields": ["search_name^3", "description^2", "original_name"],
                                "boost": 4
                            }},

                            # Tier 7: Fuzzy Match (search_name array elements) - Score: 2+
                            {"fuzzy": {"search_name": {"value": term, "boost": 2}}}
                        ]
                    }
                },
                "size": 5,
                "_source": ["search_name", "description", "original_name", "nutrition", "processing_method"]
            })

        try:
            # Execute multi-search
            response = self.es_client.msearch(body=search_body)

            # Process each response
            for i, (term, result) in enumerate(zip(search_terms, response["responses"])):
                if "error" in result:
                    error_msg = f"ES search failed for '{term}': {result['error']}"
                    errors.append(error_msg)
                else:
                    hits = result.get("hits", {}).get("hits", [])
                    if hits:
                        matches[term] = self._convert_es_hits_to_matches(hits, term)
                        successful_matches += 1

                        self.log_processing_detail(f"es_result_{i}", {
                            "term": term,
                            "hit_count": len(hits),
                            "top_score": hits[0]["_score"] if hits else 0
                        })

        except Exception as e:
            self.logger.error(f"Elasticsearch batch search failed: {e}")
            raise RuntimeError(f"Elasticsearch batch search failed and fallback is disabled: {e}") from e

        es_time = int((time.time() - start_time) * 1000)

        return self._build_nutrition_query_output(
            matches, successful_matches, len(search_terms), es_time,
            "elasticsearch_batch", errors
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
                    "search_method": "api"
                }
            )
            matches.append(match)

        return matches

    def _convert_es_hits_to_matches(self, hits: List[Dict],
                                  search_term: str) -> List[NutritionMatch]:
        """Convert Elasticsearch hits to NutritionMatch objects"""
        matches = []
        for hit in hits:
            source = hit["_source"]

            # Handle search_name array properly
            search_name_raw = source.get("search_name", ["Unknown"])
            if isinstance(search_name_raw, list) and len(search_name_raw) > 0:
                display_name = search_name_raw[0]
                search_name_str = search_name_raw[0]
            else:
                display_name = search_name_raw if search_name_raw else "Unknown"
                search_name_str = search_name_raw if search_name_raw else "Unknown"

            match = NutritionMatch(
                id=hit.get("_id", "unknown"),
                name=display_name,
                search_name=search_name_str,
                description=source.get("description", ""),
                data_type="elasticsearch_result",
                source_db="mynetdiary_direct",
                nutrition=source.get("nutrition", {}),
                weight=100,  # Default weight
                score=hit["_score"],
                search_metadata={
                    "search_term": search_term,
                    "elasticsearch_score": hit["_score"],
                    "original_name": source.get("original_name", ""),
                    "processing_method": source.get("processing_method", ""),
                    "search_method": "elasticsearch_direct"
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
            "advanced_search_enabled": True,
            "alternative_name_support": True,
            "performance_tier": method
        }

        return NutritionQueryOutput(
            matches=matches,
            search_summary=search_summary,
            errors=errors if errors else None
        )