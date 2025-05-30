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
        require_all_words: bool = False,  # 新機能: 精度向上のオプション
        brand_owner_filter: Optional[str] = None  # 新機能: ブランド特定検索
    ) -> List[USDASearchResultItem]:
        """
        USDA FoodData Central APIで食品を検索し、詳細な情報を返す (v2.1仕様)
        改善提案に基づいて検索精度とブランド対応を強化
        
        Args:
            query: 検索クエリ文字列
            data_types: データタイプのリスト（例: ["Foundation", "SR Legacy", "Branded"]）
            page_size: 1ページあたりの結果数
            page_number: 取得するページ番号
            sort_by: ソートキー
            sort_order: ソート順（"asc" または "desc"）
            require_all_words: 検索クエリの全単語を含む結果のみ取得（精度向上）
            brand_owner_filter: 特定ブランドオーナーでの検索強化
            
        Returns:
            USDASearchResultItemのリスト（新しいPydanticモデル）
        """
        params = {
            "api_key": self.api_key,
            "pageSize": page_size,
            "pageNumber": page_number,
            "sortBy": sort_by,
            "sortOrder": sort_order
        }
        
        # ブランドフィルターが指定された場合、クエリを強化
        if brand_owner_filter:
            # ブランド名をクエリに含めてBranded Foodsを優先検索
            enhanced_query = f"{brand_owner_filter} {query}"
            params["query"] = enhanced_query
            logger.info(f"Enhanced query with brand filter: '{enhanced_query}'")
            
            # Branded Foodsを優先するよう data_types を調整
            if not data_types:
                data_types = ["Branded", "FNDDS", "Foundation", "SR Legacy"]
            elif "Branded" not in data_types:
                data_types = ["Branded"] + data_types
        else:
            params["query"] = query
        
        if data_types:
            # データタイプをカンマ区切り文字列として渡す
            params["dataType"] = ",".join(data_types)
        
        # 精度向上オプション
        if require_all_words:
            params["requireAllWords"] = "true"
            logger.debug(f"Using require_all_words=true for enhanced precision")
        
        try:
            context = f"USDA API enhanced search (brand:{brand_owner_filter}, precise:{require_all_words})"
            logger.info(f"USDA API enhanced search: query='{params['query']}', page_size={page_size}")
            
            response = await self._make_request_with_retry(
                method="GET",
                url=f"{self.base_url}/foods/search",
                params=params,
                context=context
            )
            
            if response:
                data = response.json()
                
                results = []
                for food_data in data.get("foods", [])[:page_size]:
                    # ブランドフィルターが指定されている場合、後処理でさらなるフィルタリング
                    if brand_owner_filter:
                        food_brand = food_data.get("brandOwner", "").lower()
                        if brand_owner_filter.lower() not in food_brand:
                            # ブランドが一致しない場合はスキップ（ただし、多少の柔軟性は保持）
                            if food_data.get("dataType") == "Branded":
                                continue
                    
                    nutrients_extracted = self._extract_key_nutrients(food_data.get("foodNutrients", []))
                    
                    results.append(USDASearchResultItem(
                        fdc_id=food_data.get("fdcId"),
                        description=food_data.get("description"),
                        data_type=food_data.get("dataType"),
                        brand_owner=food_data.get("brandOwner"),
                        ingredients_text=food_data.get("ingredients"),
                        food_nutrients=nutrients_extracted,
                        score=food_data.get("score")
                    ))
                
                logger.info(f"USDA API enhanced search returned {len(results)} results for query '{params['query']}'")
                
                # ブランドフィルターが指定された場合のログ強化
                if brand_owner_filter:
                    branded_count = sum(1 for r in results if r.data_type == "Branded")
                    logger.info(f"Brand-filtered search: {branded_count}/{len(results)} results are Branded Foods")
                
                return results
            
        except Exception as e:
            logger.error(f"Unexpected error in USDAService.search_foods_rich: {str(e)}")
            raise RuntimeError(f"Unexpected error in USDA service: {str(e)}") from e
    
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
            "format": "full",
            # 主要栄養素のみ取得
            "nutrients": ",".join(self.key_nutrient_numbers)
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
            "208": "calories_kcal",      # Energy
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


@lru_cache()
def get_usda_service():
    """USDAServiceのシングルトンインスタンスを取得"""
    return USDAService() 