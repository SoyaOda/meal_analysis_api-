# app/services/usda_service.py
import httpx
import json
import logging
import asyncio
import time
from typing import List, Optional, Dict, Any
from functools import lru_cache

from ..core.config import get_settings
from ..api.v1.schemas.meal import USDANutrient, USDASearchResultItem

logger = logging.getLogger(__name__)


class USDAService:
    """USDA FoodData Central APIとの通信を管理するサービスクラス"""
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.USDA_API_KEY
        self.base_url = settings.USDA_API_BASE_URL
        self.timeout = settings.USDA_API_TIMEOUT
        self.max_retries = settings.USDA_API_MAX_RETRIES
        self.retry_delay = settings.USDA_API_RETRY_DELAY
        self.retry_backoff = settings.USDA_API_RETRY_BACKOFF
        self.key_nutrient_numbers = settings.USDA_KEY_NUTRIENT_NUMBERS
        
        if not self.api_key:
            logger.error("USDA_API_KEY is not configured.")
            raise ValueError("USDA API key not configured.")
        
        # httpx.AsyncClientの設定
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"X-Api-Key": self.api_key}
        )
    
    async def _make_request_with_retry(
        self, 
        method: str, 
        url: str, 
        params: Optional[Dict[str, Any]] = None,
        context: str = "API request"
    ) -> Optional[httpx.Response]:
        """
        リトライ機構付きHTTPリクエスト
        
        Args:
            method: HTTPメソッド（'GET', 'POST'など）
            url: リクエストURL
            params: クエリパラメータ
            context: ログ用のコンテキスト情報
            
        Returns:
            httpx.Response or None（全てのリトライが失敗した場合）
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # 初回 + リトライ回数
            try:
                if attempt > 0:
                    # リトライの場合は待機
                    delay = self.retry_delay * (self.retry_backoff ** (attempt - 1))
                    logger.info(f"Retrying {context} (attempt {attempt + 1}/{self.max_retries + 1}) after {delay:.1f}s delay...")
                    await asyncio.sleep(delay)
                
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1}/{self.max_retries + 1})")
                start_time = time.time()
                
                response = await self.client.request(method, url, params=params)
                
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                if "X-RateLimit-Remaining" in response.headers:
                    logger.debug(f"USDA API Rate Limit Remaining: {response.headers.get('X-RateLimit-Remaining')}")
                
                response.raise_for_status()
                
                if attempt > 0:
                    logger.info(f"{context} succeeded on attempt {attempt + 1} after {duration_ms:.1f}ms")
                else:
                    logger.debug(f"{context} succeeded on first attempt in {duration_ms:.1f}ms")
                
                return response
                
            except httpx.TimeoutException as e:
                last_exception = e
                logger.warning(f"{context} timed out on attempt {attempt + 1}/{self.max_retries + 1}: {str(e)}")
                if attempt == self.max_retries:
                    logger.error(f"{context} failed after {self.max_retries + 1} attempts due to timeout")
                    break
                    
            except httpx.HTTPStatusError as e:
                # 404やクライアントエラー（4xx）はリトライしない
                if 400 <= e.response.status_code < 500:
                    logger.warning(f"{context} failed with client error {e.response.status_code}, not retrying")
                    last_exception = e
                    break
                # サーバーエラー（5xx）はリトライする
                elif e.response.status_code >= 500:
                    last_exception = e
                    logger.warning(f"{context} failed with server error {e.response.status_code} on attempt {attempt + 1}/{self.max_retries + 1}")
                    if attempt == self.max_retries:
                        logger.error(f"{context} failed after {self.max_retries + 1} attempts due to server errors")
                        break
                else:
                    # その他のHTTPエラー
                    logger.error(f"{context} failed with HTTP error {e.response.status_code}: {e.response.text}")
                    last_exception = e
                    break
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"{context} failed with exception on attempt {attempt + 1}/{self.max_retries + 1}: {str(e)}")
                if attempt == self.max_retries:
                    logger.error(f"{context} failed after {self.max_retries + 1} attempts due to: {str(e)}")
                    break
        
        # すべてのリトライが失敗した場合
        logger.error(f"{context} ultimately failed after {self.max_retries + 1} attempts. Last error: {last_exception}")
        return None
    
    async def search_foods_rich(
        self,
        query: str,
        data_types: Optional[List[str]] = None,
        page_size: int = 10,
        page_number: int = 1,
        sort_by: str = "score",
        sort_order: str = "desc",
        require_all_words: bool = False,
        brand_owner_filter: Optional[str] = None,
        search_context: Optional[str] = None
    ) -> List[USDASearchResultItem]:
        """
        Enhanced USDA FoodData Central API food search with tiered search capabilities
        
        Args:
            query: 検索クエリ
            data_types: 検索対象データタイプのリスト（例：["Branded", "SR Legacy"]）
            page_size: 結果の最大件数
            page_number: ページ番号  
            sort_by: ソート基準
            sort_order: ソート順序
            require_all_words: 全ての単語を必須とするか
            brand_owner_filter: ブランドオーナーフィルタ
            search_context: 検索コンテキスト（"branded", "ingredient", "dish"）
            
        Returns:
            List[USDASearchResultItem]: 検索結果のリスト
        """
        if not query.strip():
            return []

        try:
            # Build query parameters
            params = {
                "query": query,
                "pageSize": min(page_size, 200),  # API limit
                "pageNumber": page_number,
                "sortBy": sort_by,
                "sortOrder": sort_order,
                "requireAllWords": require_all_words
            }

            # Add data types if specified
            if data_types:
                # Convert list to comma-separated string as expected by USDA API
                params["dataType"] = ",".join(data_types)
            
            # Add brand owner filter if specified
            if brand_owner_filter:
                params["brandOwner"] = brand_owner_filter

            # Log the search attempt
            logger.info(f"USDA API search: query='{query}', data_types={data_types}, "
                       f"require_all_words={require_all_words}, brand_owner='{brand_owner_filter}', "
                       f"context='{search_context}'")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/foods/search",
                    params=params,
                    headers={"X-Api-Key": self.api_key}
                )
                response.raise_for_status()
                
                data = response.json()
                foods = data.get("foods", [])
                
                # Process and enhance results
                results = []
                for food_item in foods:
                    result = USDASearchResultItem(
                        fdc_id=food_item.get("fdcId"),
                        description=food_item.get("description", ""),
                        data_type=food_item.get("dataType"),
                        publication_date=food_item.get("publishedDate"),
                        brand_owner=food_item.get("brandOwner"),
                        brand_name=food_item.get("brandName"),
                        subbrand_name=food_item.get("subbrandName"),
                        gtin_upc=food_item.get("gtinUpc"),
                        ndb_number=food_item.get("ndbNumber"),
                        food_code=food_item.get("foodCode"),
                        score=food_item.get("score", 0.0),
                        ingredients=food_item.get("ingredients")
                    )
                    
                    # Add search metadata for tracking
                    result.search_context = search_context
                    result.require_all_words_used = require_all_words
                    result.data_types_searched = data_types
                    
                    results.append(result)

                logger.info(f"USDA API response: {len(results)} results returned "
                           f"(query: '{query}', context: '{search_context}')")
                return results

        except httpx.HTTPStatusError as e:
            logger.error(f"USDA API HTTP error for query '{query}': {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            logger.error(f"USDA API request error for query '{query}': {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in USDA search for query '{query}': {str(e)}")
            return []
    
    def _extract_key_nutrients(self, food_nutrients: List[Dict[str, Any]]) -> List[USDANutrient]:
        """
        foodNutrientsデータから主要栄養素を抽出 (新しいPydanticモデル使用)
        """
        # 主要栄養素 (configから取得) のみを抽出する
        nutrients_extracted = []
        key_numbers = self.key_nutrient_numbers # Settings から取得

        for nutrient_entry in food_nutrients:
            nutrient_detail = nutrient_entry.get("nutrient", {})
            amount = nutrient_entry.get("amount")

            if not nutrient_detail and "nutrientId" in nutrient_entry: # Branded abridged
                number = nutrient_entry.get("nutrientNumber")
                name = nutrient_entry.get("nutrientName")
                unit_name = nutrient_entry.get("unitName")
                amount = nutrient_entry.get("value")
                nutrient_id = nutrient_entry.get("nutrientId")
            else: # Standard
                number = nutrient_detail.get("number")
                name = nutrient_detail.get("name")
                unit_name = nutrient_detail.get("unitName")
                nutrient_id = nutrient_detail.get("id")

            if number and str(number) in key_numbers:
                if name and amount is not None and unit_name:
                    nutrients_extracted.append(USDANutrient(
                        name=name,
                        amount=float(amount),
                        unit_name=unit_name,
                        nutrient_id=int(nutrient_id) if nutrient_id else None,
                        nutrient_number=str(number) if number else None
                    ))
        return nutrients_extracted

    async def get_food_details(self, fdc_id: int) -> Optional[USDASearchResultItem]:
        """
        特定のFDC IDの食品詳細情報を取得 (新しいPydanticモデル使用)
        """
        params = {
            "api_key": self.api_key,
            "format": "full"  # ingredients も確実に取得するために format="full" を使用
        }
        
        try:
            logger.info(f"Getting USDA food details for FDC ID: {fdc_id}")
            response = await self._make_request_with_retry(
                method="GET",
                url=f"{self.base_url}/food/{fdc_id}",
                params=params,
                context="Getting USDA food details"
            )
            
            if response:
                food_data = response.json()
                
                # _extract_key_nutrients を使用して栄養素をパース
                nutrients_extracted = self._extract_key_nutrients(food_data.get("foodNutrients", []))
                
                return USDASearchResultItem(
                    fdc_id=food_data.get("fdcId"),
                    description=food_data.get("description"),
                    data_type=food_data.get("dataType"),
                    brand_owner=food_data.get("brandOwner"),
                    ingredients_text=food_data.get("ingredients"),
                    food_nutrients=nutrients_extracted,
                    score=None  # 詳細取得時はスコアなし
                )
            
        except Exception as e:
            logger.error(f"Error getting food details for FDC ID {fdc_id}: {str(e)}")
            raise RuntimeError(f"Error getting food details: {str(e)}") from e

    async def get_food_details_for_nutrition(self, fdc_id: int) -> Optional[Dict[str, float]]:
        """
        栄養計算用の食品詳細情報を取得 (既存ロジックを維持・確認)
        """
        params = {
            "api_key": self.api_key,
            "format": "full"
            # Remove nutrient filter to get all nutrients including 957, 958
            # "nutrients": ",".join(self.key_nutrient_numbers)
        }
        
        try:
            logger.debug(f"Getting nutrition data for FDC ID: {fdc_id}")
            response = await self._make_request_with_retry(
                method="GET",
                url=f"{self.base_url}/food/{fdc_id}",
                params=params,
                context="Getting nutrition data"
            )
            
            if response:
                food_data = response.json()
                
                return self._parse_nutrients_for_calculation(food_data)
            
        except Exception as e:
            logger.error(f"Error getting nutrition data for FDC ID {fdc_id}: {str(e)}")
            return None

    def _parse_nutrients_for_calculation(self, food_data_raw: dict) -> Dict[str, float]:
        """
        USDA APIレスポンスから栄養計算用の栄養素辞書を作成
        """
        nutrients_dict = {}
        food_nutrients = food_data_raw.get("foodNutrients", [])
        
        # 栄養素番号と標準名の対応表
        nutrient_map = {
            "208": "calories_kcal",      # Energy (older format)
            "957": "calories_kcal",      # Energy (Atwater General Factors) - Foundation data
            "958": "calories_kcal",      # Energy (Atwater Specific Factors) - Foundation data  
            "203": "protein_g",          # Protein  
            "205": "carbohydrates_g",    # Carbohydrate
            "204": "fat_g",              # Total lipid (fat)
            "291": "fiber_g",            # Fiber, total dietary
            "269": "sugars_g",           # Sugars, total
            "307": "sodium_mg"           # Sodium
        }
        
        for nutrient_entry in food_nutrients:
            nutrient_detail = nutrient_entry.get("nutrient", {})
            amount = nutrient_entry.get("amount")
            
            # データ構造の違いに対応
            if not nutrient_detail and "nutrientId" in nutrient_entry:
                # Branded Foods abridged format
                number = nutrient_entry.get("nutrientNumber")
                amount = nutrient_entry.get("value")
            else:
                # Standard format
                number = nutrient_detail.get("number")
            
            if number and str(number) in nutrient_map and amount is not None:
                standard_name = nutrient_map[str(number)]
                # For calories, prefer Atwater Specific Factors (958) over General Factors (957) over legacy (208)
                if standard_name == "calories_kcal":
                    if "calories_kcal" not in nutrients_dict or str(number) == "958":
                        nutrients_dict[standard_name] = float(amount)
                    elif str(number) == "957" and "calories_kcal" in nutrients_dict:
                        # Only replace if current value is from legacy 208
                        current_from_legacy = True  # We can't track source easily, so prefer 957 over existing
                        nutrients_dict[standard_name] = float(amount)
                else:
                    nutrients_dict[standard_name] = float(amount)
        
        logger.debug(f"Parsed nutrients for calculation: {nutrients_dict}")
        return nutrients_dict

    # 後方互換性のために既存メソッドも保持
    async def search_foods(
        self,
        query: str,
        data_types: Optional[List[str]] = None,
        page_size: int = 5,
        page_number: int = 1,
        sort_by: str = "score",
        sort_order: str = "desc"
    ) -> List:
        """
        後方互換性のための既存search_foodsメソッド
        """
        # 新しいsearch_foods_richを呼び出して、古い形式に変換
        rich_results = await self.search_foods_rich(
            query=query,
            data_types=data_types,
            page_size=page_size,
            page_number=page_number,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # 後方互換性のために古いUSDASearchResultItemクラス形式に変換
        # （実際の実装では、必要に応じてレガシークラスを保持する）
        return rich_results
    
    async def close_client(self):
        """HTTPクライアントのクリーンアップ"""
        if self.client:
            await self.client.aclose()

    async def search_foods_with_fallback(
        self,
        query_candidates: List[str],
        search_context: str = "ingredient",
        max_results: int = 5
    ) -> List[USDASearchResultItem]:
        """
        Multiple query candidates with intelligent fallback searching
        
        Args:
            query_candidates: List of query terms to try in order of preference
            search_context: Search context for optimization
            max_results: Maximum results to return
        """
        all_results = []
        
        for i, query in enumerate(query_candidates):
            try:
                results = await self.search_foods_rich(
                    query=query,
                    page_size=max_results,
                    search_context=search_context
                )
                
                if results:
                    logger.info(f"Fallback search #{i+1} successful with query '{query}': {len(results)} results")
                    # Add query source info to results
                    for result in results:
                        result.fallback_query_used = query
                        result.fallback_attempt = i + 1
                    all_results.extend(results)
                    
                    # Stop after first successful search unless we need more results
                    if len(all_results) >= max_results:
                        break
                else:
                    logger.info(f"Fallback search #{i+1} returned no results for query '{query}'")
                    
            except Exception as e:
                logger.warning(f"Fallback search #{i+1} failed for query '{query}': {str(e)}")
                continue
        
        # Remove duplicates and limit results
        unique_results = []
        seen_fdc_ids = set()
        
        for result in all_results:
            if result.fdc_id not in seen_fdc_ids:
                unique_results.append(result)
                seen_fdc_ids.add(result.fdc_id)
                if len(unique_results) >= max_results:
                    break
        
        logger.info(f"Fallback search completed: {len(unique_results)} unique results from {len(query_candidates)} queries")
        return unique_results

    async def execute_tiered_usda_search(
        self,
        phase1_candidate: 'USDACandidateQuery',
        phase1_ingredient_details: Optional['Phase1Ingredient'] = None,  # NEW: Phase1の食材詳細情報
        brand_context: Optional[str] = None,
        max_results_cap: int = 15
    ) -> List[USDASearchResultItem]:
        """
        Enhanced tiered USDA search strategy with 5-tier approach (Tier 0-4)
        Utilizes Phase 1 state and preparation_method for precise cooking state matching
        
        Args:
            phase1_candidate: Query candidate from Phase 1 with metadata
            phase1_ingredient_details: Phase1Ingredient containing state & preparation_method (NEW)
            brand_context: Detected brand context (e.g., "La Madeleine")
            max_results_cap: Maximum total results to return
            
        Returns:
            List of deduplicated USDASearchResultItem results from all tiers
        """
        all_found_results_map: Dict[int, USDASearchResultItem] = {}  # FDC IDで重複排除
        attempted_queries = set()
        tier_results_count = {}  # Track results per tier
        RESULTS_PER_TIER = 3  # Reduced to allow for more tiers
        
        logger.info(f"Starting enhanced tiered USDA search for: {phase1_candidate.query_term} "
                   f"(granularity: {phase1_candidate.granularity_level})")
        
        if phase1_ingredient_details:
            logger.info(f"Phase1 ingredient details: state={phase1_ingredient_details.state}, "
                       f"prep_method={phase1_ingredient_details.preparation_method}")

        # Tier 0: Complete State/Prep Match (NEW - highest precision)
        if (phase1_ingredient_details and 
            phase1_ingredient_details.state != "unknown" and 
            phase1_ingredient_details.preparation_method != "unknown"):
            
            query_t0 = f"{phase1_candidate.query_term}, {phase1_ingredient_details.state}, {phase1_ingredient_details.preparation_method}"
            if query_t0 not in attempted_queries:
                data_types_t0 = ["SR Legacy", "Foundation"]  # High-quality databases for precise matches
                logger.info(f"Tier 0 (Complete State/Prep Match): query='{query_t0}'")
                
                try:
                    results_t0 = await self.search_foods_rich(
                        query=query_t0,
                        data_types=data_types_t0,
                        page_size=RESULTS_PER_TIER,
                        require_all_words=True,
                        search_context="complete_state_match"
                    )
                    
                    tier_results_count[0] = len(results_t0)
                    for res in results_t0:
                        if res.fdc_id not in all_found_results_map:
                            all_found_results_map[res.fdc_id] = res
                            res.search_tier = 0
                            res.search_query_used = query_t0
                            
                    attempted_queries.add(query_t0)
                    logger.info(f"Tier 0 completed: {len(results_t0)} results found")
                        
                except Exception as e:
                    logger.warning(f"Tier 0 search failed for '{query_t0}': {str(e)}")

        # Tier 1: State Match (NEW - state only, no specific prep method)
        if (phase1_ingredient_details and 
            phase1_ingredient_details.state != "unknown"):
            
            query_t1 = f"{phase1_candidate.query_term}, {phase1_ingredient_details.state}"
            if query_t1 not in attempted_queries:
                data_types_t1 = ["SR Legacy", "Foundation"]
                logger.info(f"Tier 1 (State Match): query='{query_t1}'")
                
                try:
                    results_t1 = await self.search_foods_rich(
                        query=query_t1,
                        data_types=data_types_t1,
                        page_size=RESULTS_PER_TIER,
                        require_all_words=True,
                        search_context="state_match"
                    )
                    
                    tier_results_count[1] = len(results_t1)
                    for res in results_t1:
                        if res.fdc_id not in all_found_results_map:
                            all_found_results_map[res.fdc_id] = res
                            res.search_tier = 1
                            res.search_query_used = query_t1
                            
                    attempted_queries.add(query_t1)
                    logger.info(f"Tier 1 completed: {len(results_t1)} results found")
                        
                except Exception as e:
                    logger.warning(f"Tier 1 search failed for '{query_t1}': {str(e)}")

        # Tier 2: Original Phase 1 Query (enhanced from previous Tier 1)
        query_term_t2 = phase1_candidate.query_term
        if query_term_t2 not in attempted_queries:
            # Use Phase1 preferred_data_types if available
            if hasattr(phase1_candidate, 'preferred_data_types') and phase1_candidate.preferred_data_types:
                data_types_t2 = phase1_candidate.preferred_data_types
                search_context_t2 = phase1_candidate.granularity_level
                brand_owner_t2 = brand_context if "Branded" in data_types_t2 else None
                require_all_words_t2 = True
                logger.info(f"Tier 2 (Phase1 Guided): query='{query_term_t2}', data_types={data_types_t2}")
            else:
                # Dynamic dataType selection based on granularity and cooking state
                is_cooked_query = any(term in query_term_t2.lower() for term in ["cooked", "prepared", "grilled", "fried", "baked", "boiled", "steamed"])
                is_raw_query = "raw" in query_term_t2.lower()
                
                if phase1_candidate.granularity_level == "dish":
                    data_types_t2 = ["SR Legacy", "Branded"]
                    search_context_t2 = "dish"
                    brand_owner_t2 = brand_context
                    require_all_words_t2 = True
                elif phase1_candidate.granularity_level == "ingredient":
                    if is_raw_query:
                        data_types_t2 = ["Foundation", "SR Legacy"]
                        search_context_t2 = "raw_ingredient"
                    elif is_cooked_query:
                        data_types_t2 = ["SR Legacy", "Foundation"]
                        search_context_t2 = "cooked_ingredient"
                    else:
                        data_types_t2 = ["Foundation", "SR Legacy"]
                        search_context_t2 = "ingredient"
                    brand_owner_t2 = None
                    require_all_words_t2 = True
                elif phase1_candidate.granularity_level == "branded_product":
                    data_types_t2 = ["Branded"]
                    search_context_t2 = "branded_product"
                    brand_owner_t2 = brand_context
                    require_all_words_t2 = True
                else:
                    data_types_t2 = ["SR Legacy", "Foundation", "Branded"]
                    search_context_t2 = "general"
                    brand_owner_t2 = brand_context
                    require_all_words_t2 = False

            try:
                results_t2 = await self.search_foods_rich(
                    query=query_term_t2,
                    data_types=data_types_t2,
                    page_size=RESULTS_PER_TIER,
                    require_all_words=require_all_words_t2,
                    brand_owner_filter=brand_owner_t2,
                    search_context=search_context_t2
                )
                
                tier_results_count[2] = len(results_t2)
                for res in results_t2:
                    if res.fdc_id not in all_found_results_map:
                        all_found_results_map[res.fdc_id] = res
                        res.search_tier = 2
                        res.search_query_used = query_term_t2
                        
                attempted_queries.add(query_term_t2)
                logger.info(f"Tier 2 completed: {len(results_t2)} results found")
                    
            except Exception as e:
                logger.warning(f"Tier 2 search failed for '{query_term_t2}': {str(e)}")

        # Tier 3: Simplified Query (enhanced from previous Tier 2)
        query_term_t3 = self._simplify_query_term(query_term_t2)
        
        if query_term_t3 and query_term_t3 != query_term_t2 and query_term_t3 not in attempted_queries:
            data_types_t3 = ["SR Legacy", "Branded", "Foundation"]
            require_all_words_t3 = False
            
            logger.info(f"Tier 3 (Simplified): query='{query_term_t3}', require_all_words=False")
            
            try:
                results_t3 = await self.search_foods_rich(
                    query=query_term_t3,
                    data_types=data_types_t3,
                    page_size=RESULTS_PER_TIER,
                    require_all_words=require_all_words_t3,
                    search_context="simplified"
                )
                
                tier_results_count[3] = len(results_t3)
                for res in results_t3:
                    if res.fdc_id not in all_found_results_map:
                        all_found_results_map[res.fdc_id] = res
                        res.search_tier = 3
                        res.search_query_used = query_term_t3
                        
                attempted_queries.add(query_term_t3)
                logger.info(f"Tier 3 completed: {len(results_t3)} new results found")
                
            except Exception as e:
                logger.warning(f"Tier 3 search failed for '{query_term_t3}': {str(e)}")

        # Tier 4: Base/Raw Form Query (NEW - for conversion purposes)
        if (phase1_ingredient_details and 
            phase1_ingredient_details.state == "cooked"):
            
            # Construct raw/base form query
            raw_query_term = self._construct_raw_form_query(phase1_candidate.query_term, phase1_ingredient_details)
            
            if raw_query_term and raw_query_term not in attempted_queries:
                data_types_t4 = ["Foundation", "SR Legacy"]  # Focus on base ingredient databases
                logger.info(f"Tier 4 (Base/Raw Form - for conversion): query='{raw_query_term}'")
                
                try:
                    results_t4 = await self.search_foods_rich(
                        query=raw_query_term,
                        data_types=data_types_t4,
                        page_size=RESULTS_PER_TIER,
                        require_all_words=False,
                        search_context="raw_for_conversion"
                    )
                    
                    tier_results_count[4] = len(results_t4)
                    for res in results_t4:
                        if res.fdc_id not in all_found_results_map:
                            all_found_results_map[res.fdc_id] = res
                            res.search_tier = 4
                            res.search_query_used = raw_query_term
                            # Flag for conversion requirement
                            res.requires_cooking_conversion = True
                            
                    attempted_queries.add(raw_query_term)
                    logger.info(f"Tier 4 completed: {len(results_t4)} base form results found")
                        
                except Exception as e:
                    logger.warning(f"Tier 4 search failed for '{raw_query_term}': {str(e)}")

        final_results = list(all_found_results_map.values())
        final_results = self._sort_and_limit_results(final_results, max_results_cap)
        
        logger.info(f"Enhanced tiered search completed: {len(final_results)} total unique results from {len(attempted_queries)} queries")
        logger.info(f"Results per tier: {tier_results_count}")
        return final_results

    def _extract_brand_from_query(self, query_term: str) -> Optional[str]:
        """Extract potential brand name from query term"""
        known_brands = ["La Madeleine", "McDonald's", "Subway", "Panera", "Starbucks"]
        query_lower = query_term.lower()
        
        for brand in known_brands:
            if brand.lower() in query_lower:
                return brand
        
        # Generic brand extraction - first 1-2 words if they look like brand names
        words = query_term.split()
        if len(words) >= 2 and words[0][0].isupper():
            # Check if first word(s) might be brand name
            if len(words[0]) > 2 and not words[0].lower() in ["the", "a", "an"]:
                return words[0] if len(words) == 2 else f"{words[0]} {words[1]}"
        
        return None

    def _simplify_query_term(self, query_term: str) -> str:
        """
        Simplify query term by mechanically removing rightmost comma-separated component
        Simple hierarchical strategy: "A, B, C" → "A, B" → "A"
        """
        # Handle comma-separated format - simply remove rightmost component
        if ',' in query_term:
            parts = [part.strip() for part in query_term.split(',')]
            if len(parts) > 1:
                # Remove rightmost component: "Meatloaf, prepared, cooked" → "Meatloaf, prepared"
                return ", ".join(parts[:-1])
            else:
                return query_term
        
        # Handle space-separated format (fallback) - remove last word
        words = query_term.split()
        if len(words) > 1:
            return " ".join(words[:-1])
        
        return query_term

    def _generalize_query_term(self, phase1_candidate: 'USDACandidateQuery') -> str:
        """
        Generate the most generic term by extracting leftmost comma-separated component
        Simple rule: "A, B, C" → "A" (core food category)
        """
        query_term = phase1_candidate.query_term
        
        # Extract core category from comma-separated format
        if ',' in query_term:
            # Return the first part (core category) from "Category, Type, Method"
            core_category = query_term.split(',')[0].strip()
            return core_category
        
        # Handle space-separated format (fallback) - return first word
        words = query_term.split()
        if words:
            return words[0]
        
        return query_term

    def _sort_and_limit_results(self, results: List[USDASearchResultItem], max_results: int) -> List[USDASearchResultItem]:
        """Sort results by quality and limit to max_results"""
        def get_sort_key(item: USDASearchResultItem):
            # Primary sort: data type priority
            datatype_priority = self._get_datatype_priority(item.data_type)
            # Secondary sort: score (higher is better)
            score = item.score or 0
            # Tertiary sort: tier (lower tier = earlier, better)
            tier = getattr(item, 'search_tier', 999)
            
            return (-datatype_priority, -score, tier)
        
        results.sort(key=get_sort_key)
        return results[:max_results]

    def _get_datatype_priority(self, data_type: Optional[str]) -> int:
        """Get priority score for USDA data type"""
        if data_type == "SR Legacy": 
            return 4  # Highest priority for prepared dishes
        elif data_type == "Foundation": 
            return 3  # High priority for basic ingredients
        elif data_type == "Branded": 
            return 2  # Medium priority for commercial products
        else: 
            return 1  # Lowest priority for unknown types

    def organize_results_by_tier(self, results: List[USDASearchResultItem]) -> Dict[int, List[USDASearchResultItem]]:
        """
        Organize search results by tier for structured Phase2 analysis
        
        Args:
            results: List of search results from tiered search
            
        Returns:
            Dict mapping tier number to list of results for that tier
        """
        tier_organized = {}
        
        for result in results:
            tier = getattr(result, 'search_tier', 0)
            if tier not in tier_organized:
                tier_organized[tier] = []
            tier_organized[tier].append(result)
        
        return tier_organized

    def format_tier_results_for_prompt(self, results: List[USDASearchResultItem]) -> str:
        """
        Format tiered search results for Phase2 prompt inclusion
        
        Args:
            results: List of search results from tiered search
            
        Returns:
            Formatted string for prompt inclusion
        """
        if not results:
            return "No USDA search results available."
        
        tier_organized = self.organize_results_by_tier(results)
        formatted_sections = []
        
        for tier in sorted(tier_organized.keys()):
            tier_results = tier_organized[tier]
            if not tier_results:
                continue
                
            # Get query used for this tier
            query_used = getattr(tier_results[0], 'search_query_used', 'N/A')
            
            # Format tier header
            tier_section = f"**TIER {tier} RESULTS** (Query: '{query_used}'):\n"
            
            # Format each result in this tier
            for i, result in enumerate(tier_results, 1):
                combo_indicator = ""
                if any(combo in result.description.lower() for combo in ["with", "&", "and", "meal", "dinner", "plate", "combo"]):
                    combo_indicator = " [COMBO MEAL]"
                
                tier_section += (
                    f"{i}. FDC {result.fdc_id}: {result.description}{combo_indicator}\n"
                    f"   Type: {result.data_type}, Score: {result.score:.1f}\n"
                )
            
            formatted_sections.append(tier_section)
        
        return "\n".join(formatted_sections)

    def _construct_raw_form_query(self, original_query: str, phase1_ingredient: 'Phase1Ingredient') -> Optional[str]:
        """
        Construct a raw/base form query for cooked ingredients to enable cooking conversion
        
        Args:
            original_query: Original query term from Phase 1
            phase1_ingredient: Phase1Ingredient with state and preparation_method info
            
        Returns:
            Raw form query string or None if construction not applicable
        """
        if phase1_ingredient.state != "cooked":
            return None
            
        # Remove cooking-related terms and replace with "raw" or "dry"
        query_lower = original_query.lower()
        
        # Common cooked state patterns to replace
        cooked_patterns = [
            ("cooked", "raw"),
            ("prepared", "raw"), 
            ("grilled", "raw"),
            ("fried", "raw"),
            ("baked", "raw"),
            ("roasted", "raw"),
            ("boiled", "raw"),
            ("steamed", "raw"),
            ("sauteed", "raw"),
            ("stewed", "raw"),
            ("microwaved", "raw")
        ]
        
        raw_query = original_query
        
        # Apply pattern replacements
        for cooked_term, raw_term in cooked_patterns:
            if cooked_term in query_lower:
                # Case-sensitive replacement to maintain original formatting
                import re
                pattern = re.compile(re.escape(cooked_term), re.IGNORECASE)
                raw_query = pattern.sub(raw_term, raw_query)
                logger.debug(f"Raw form construction: '{original_query}' -> '{raw_query}' (replaced {cooked_term})")
                return raw_query
        
        # If no direct pattern match, try intelligent construction based on ingredient type
        words = original_query.split(', ')
        if len(words) >= 1:
            base_ingredient = words[0]  # e.g., "Chicken breast" from "Chicken breast, grilled"
            
            # Special cases for common ingredient categories
            if any(meat in base_ingredient.lower() for meat in ["chicken", "beef", "pork", "turkey", "fish", "salmon", "tuna"]):
                raw_query = f"{base_ingredient}, raw"
            elif any(pasta in base_ingredient.lower() for pasta in ["pasta", "noodles", "macaroni", "spaghetti", "penne"]):
                raw_query = f"{base_ingredient}, dry"  # Pasta is typically dry in base form
            elif any(grain in base_ingredient.lower() for grain in ["rice", "quinoa", "barley", "oats"]):
                raw_query = f"{base_ingredient}, dry"  # Grains are typically dry in base form
            elif any(veg in base_ingredient.lower() for veg in ["potato", "carrot", "broccoli", "spinach", "onion"]):
                raw_query = f"{base_ingredient}, raw"
            else:
                # Generic fallback
                raw_query = f"{base_ingredient}, raw"
            
            logger.debug(f"Raw form construction (intelligent): '{original_query}' -> '{raw_query}' (category-based)")
            return raw_query
        
        logger.debug(f"Raw form construction failed for: '{original_query}'")
        return None


@lru_cache()
def get_usda_service():
    """USDAServiceのシングルトンインスタンスを取得"""
    return USDAService() 