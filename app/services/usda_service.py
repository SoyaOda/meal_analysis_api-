# app/services/usda_service.py
import httpx
import json
import logging
from typing import List, Optional, Dict, Any
from functools import lru_cache

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class USDANutrient:
    """USDA栄養素情報を表すクラス"""
    def __init__(self, name: str, amount: float, unit_name: str, 
                 nutrient_id: Optional[int] = None, 
                 nutrient_number: Optional[str] = None):
        self.name = name
        self.amount = amount
        self.unit_name = unit_name
        self.nutrient_id = nutrient_id
        self.nutrient_number = nutrient_number


class USDASearchResultItem:
    """USDA検索結果アイテムを表すクラス"""
    def __init__(self, fdc_id: int, description: str, 
                 data_type: Optional[str] = None,
                 brand_owner: Optional[str] = None,
                 ingredients_text: Optional[str] = None,
                 food_nutrients: List[USDANutrient] = None,
                 score: Optional[float] = None):
        self.fdc_id = fdc_id
        self.description = description
        self.data_type = data_type
        self.brand_owner = brand_owner
        self.ingredients_text = ingredients_text
        self.food_nutrients = food_nutrients or []
        self.score = score


class USDAService:
    """USDA FoodData Central APIとの通信を管理するサービスクラス"""
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.USDA_API_KEY
        self.base_url = settings.USDA_API_BASE_URL
        self.timeout = settings.USDA_API_TIMEOUT
        self.key_nutrient_numbers = settings.USDA_KEY_NUTRIENT_NUMBERS
        
        if not self.api_key:
            logger.error("USDA_API_KEY is not configured.")
            raise ValueError("USDA API key not configured.")
        
        # httpx.AsyncClientの設定
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={"X-Api-Key": self.api_key}
        )
    
    async def search_foods(
        self,
        query: str,
        data_types: Optional[List[str]] = None,
        page_size: int = 5,
        page_number: int = 1,
        sort_by: str = "score",
        sort_order: str = "desc"
    ) -> List[USDASearchResultItem]:
        """
        USDA FoodData Central APIで食品を検索
        
        Args:
            query: 検索クエリ文字列
            data_types: データタイプのリスト（例: ["Foundation", "SR Legacy", "Branded"]）
            page_size: 1ページあたりの結果数
            page_number: 取得するページ番号
            sort_by: ソートキー
            sort_order: ソート順（"asc" または "desc"）
            
        Returns:
            USDASearchResultItemのリスト
        """
        params = {
            "query": query,
            "api_key": self.api_key,
            "pageSize": page_size,
            "pageNumber": page_number,
            "sortBy": sort_by,
            "sortOrder": sort_order
        }
        
        if data_types:
            # データタイプをカンマ区切り文字列として渡す
            params["dataType"] = ",".join(data_types)
        
        try:
            logger.info(f"USDA API search: query='{query}', page_size={page_size}")
            response = await self.client.get(f"{self.base_url}/foods/search", params=params)
            
            # レートリミット情報のログ
            if "X-RateLimit-Remaining" in response.headers:
                logger.info(f"USDA API Rate Limit Remaining: {response.headers.get('X-RateLimit-Remaining')}")
            
            response.raise_for_status()
            data = response.json()
            
            results = []
            for food_data in data.get("foods", [])[:page_size]:
                nutrients_extracted = self._extract_nutrients(food_data.get("foodNutrients", []))
                
                results.append(USDASearchResultItem(
                    fdc_id=food_data.get("fdcId"),
                    description=food_data.get("description"),
                    data_type=food_data.get("dataType"),
                    brand_owner=food_data.get("brandOwner"),
                    ingredients_text=food_data.get("ingredients"),
                    food_nutrients=nutrients_extracted,
                    score=food_data.get("score")
                ))
            
            logger.info(f"USDA API search returned {len(results)} results for query '{query}'")
            return results
            
        except httpx.HTTPStatusError as e:
            logger.error(f"USDA API HTTP error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 429:
                raise RuntimeError(f"USDA API rate limit exceeded. Detail: {e.response.text}") from e
            raise RuntimeError(f"USDA API error: {e.response.status_code} - {e.response.text}") from e
        except httpx.RequestError as e:
            logger.error(f"USDA API request failed: {str(e)}")
            raise RuntimeError(f"USDA API request failed: {str(e)}") from e
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error(f"USDA API response parsing error: {str(e)}")
            raise RuntimeError(f"USDA API response parsing error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error in USDAService.search_foods: {str(e)}")
            raise RuntimeError(f"Unexpected error in USDA service: {str(e)}") from e
    
    def _extract_nutrients(self, food_nutrients: List[Dict[str, Any]]) -> List[USDANutrient]:
        """
        foodNutrientsデータから主要栄養素を抽出
        
        Args:
            food_nutrients: USDA APIから返される栄養素データのリスト
            
        Returns:
            USDANutrientのリスト
        """
        nutrients_extracted = []
        
        for nutrient_entry in food_nutrients:
            # 栄養素情報の抽出（データ構造はフォーマットによって異なる）
            nutrient_detail = nutrient_entry.get("nutrient", {})
            amount = nutrient_entry.get("amount")
            
            # Branded Foodsのabridgedフォーマットへの対応
            if not nutrient_detail and "nutrientId" in nutrient_entry:
                nutrient_id = nutrient_entry.get("nutrientId")
                name = nutrient_entry.get("nutrientName")
                number = nutrient_entry.get("nutrientNumber")
                unit_name = nutrient_entry.get("unitName")
                amount = nutrient_entry.get("value")  # Branded abridgedでは"value"
            else:
                # SR Legacy, Foundation, または full Branded
                nutrient_id = nutrient_detail.get("id")
                name = nutrient_detail.get("name")
                number = nutrient_detail.get("number")
                unit_name = nutrient_detail.get("unitName")
            
            # 主要栄養素のみを抽出
            if number and str(number) in self.key_nutrient_numbers:
                if name and amount is not None and unit_name:
                    nutrients_extracted.append(USDANutrient(
                        name=name,
                        amount=float(amount),
                        unit_name=unit_name,
                        nutrient_id=int(nutrient_id) if nutrient_id else None,
                        nutrient_number=str(number) if number else None
                    ))
        
        return nutrients_extracted
    
    async def get_food_details(
        self, 
        fdc_id: int, 
        format: str = "full",
        target_nutrient_numbers: Optional[List[str]] = None
    ) -> Optional[USDASearchResultItem]:
        """
        特定のFDC IDの食品詳細情報を取得
        
        Args:
            fdc_id: 食品のFDC ID
            format: レスポンス形式（"abridged" または "full"）
            target_nutrient_numbers: 取得する栄養素番号のリスト
            
        Returns:
            USDASearchResultItem または None
        """
        params = {
            "api_key": self.api_key,
            "format": format
        }
        
        if target_nutrient_numbers:
            params["nutrients"] = ",".join(target_nutrient_numbers)
        
        try:
            logger.info(f"USDA API get food details: fdc_id={fdc_id}")
            response = await self.client.get(f"{self.base_url}/food/{fdc_id}", params=params)
            response.raise_for_status()
            
            food_data = response.json()
            nutrients_extracted = self._extract_nutrients(food_data.get("foodNutrients", []))
            
            return USDASearchResultItem(
                fdc_id=food_data.get("fdcId"),
                description=food_data.get("description"),
                data_type=food_data.get("dataType"),
                brand_owner=food_data.get("brandOwner"),
                ingredients_text=food_data.get("ingredients"),
                food_nutrients=nutrients_extracted
            )
            
        except Exception as e:
            logger.error(f"Error fetching food details for FDC ID {fdc_id}: {str(e)}")
            return None
    
    async def close_client(self):
        """HTTPクライアントをクローズ"""
        await self.client.aclose()


# FastAPIの依存性注入用関数
async def get_usda_service():
    """
    USDAServiceのインスタンスを提供する依存性注入関数
    """
    service = USDAService()
    try:
        yield service
    finally:
        await service.close_client() 