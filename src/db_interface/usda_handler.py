"""
USDA Database Handler

USDAデータベースに特化したハンドラー実装
既存のUSDAサービスロジックをカプセル化
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_handler import DBHandler
from .db_models import QueryParameters, RawDBResult, RawFoodData, IdentifiedItemForDB
from ..common.exceptions import DatabaseConnectionError, DatabaseQueryError

logger = logging.getLogger(__name__)


class USDADatabaseHandler(DBHandler):
    """USDA FoodData Central API ハンドラー"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        USDA設定で初期化
        
        Args:
            config: USDA API設定（API_KEY、BASE_URLなど）
        """
        super().__init__(config)
        self.api_key = config.get("USDA_API_KEY")
        self.base_url = config.get("USDA_API_BASE_URL", "https://api.nal.usda.gov/fdc/v1")
        self.timeout = config.get("TIMEOUT_SECONDS", 30)
        self.client: Optional[httpx.AsyncClient] = None
        
        # プロンプト設定
        self.prompts_config = config.get("PROMPTS", {})
        
        if not self.api_key:
            logger.warning("USDA API key not provided. Some functions may not work.")
        
        logger.info(f"USDADatabaseHandler initialized. Base URL: {self.base_url}")
    
    async def connect(self):
        """HTTP クライアント初期化"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)
            logger.info("USDA HTTP client initialized")
    
    async def disconnect(self):
        """HTTP クライアント終了"""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.info("USDA HTTP client closed")
    
    def is_connected(self) -> bool:
        """接続状態確認"""
        return self.client is not None and not self.client.is_closed
    
    async def fetch_nutrition_data(self, params: QueryParameters) -> RawDBResult:
        """
        USDA FoodData Central から栄養データを取得
        
        Args:
            params: クエリパラメータ
            
        Returns:
            RawDBResult: USDA検索結果
        """
        if not self.is_connected():
            await self.connect()
        
        all_retrieved_foods: List[RawFoodData] = []
        errors: List[str] = []
        total_results = 0
        
        for item in params.items_to_query:
            try:
                # USDAクエリ候補がattributesに含まれている場合はそれを使用
                query_candidates = []
                if item.attributes and 'usda_query_candidates' in item.attributes:
                    query_candidates = item.attributes['usda_query_candidates']
                
                if not query_candidates:
                    # プロンプトテンプレートからクエリを生成
                    query_term = self._build_usda_query(item, params.query_strategy_id)
                    query_candidates = [query_term]
                
                # 各クエリ候補で検索
                item_results = []
                for query_term in query_candidates[:3]:  # 最大3つのクエリ候補を試す
                    results = await self._search_usda_api(query_term, params.max_results_per_item)
                    
                    if results:
                        for food_data in results:
                            food_data.matched_query_term = item.name  # 元のアイテム名を保持
                        item_results.extend(results)
                        break  # 結果が見つかったら次のクエリは試さない
                
                if item_results:
                    all_retrieved_foods.extend(item_results)
                    total_results += len(item_results)
                else:
                    errors.append(f"No USDA results found for '{item.name}'")
                    
            except Exception as e:
                error_msg = f"Error querying USDA for '{item.name}': {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return RawDBResult(
            query_params_used=params,
            retrieved_foods=all_retrieved_foods,
            source_db_name="USDA_FDC",
            query_timestamp=datetime.utcnow().isoformat() + "Z",
            total_results_found=total_results,
            errors=errors if errors else None
        )
    
    def _build_usda_query(self, item: IdentifiedItemForDB, strategy_id: Optional[str]) -> str:
        """
        プロンプトテンプレートからUSDAクエリを構築
        
        Args:
            item: 検索対象アイテム
            strategy_id: 戦略ID
            
        Returns:
            str: 構築されたクエリ文字列
        """
        # デフォルトは食品名そのまま
        prompt_template = self.prompts_config.get(strategy_id, "{food_name}")
        
        # テンプレート変数の置換
        replacements = {
            "food_name": item.name,
            "state": item.state or "prepared",
            "quantity": item.quantity_estimate or "",
        }
        
        # attributesから追加情報を取得
        if item.attributes:
            replacements.update({
                "cooking_method": item.attributes.get("cooking_method", ""),
                "brand": item.attributes.get("brand", ""),
                "type": item.attributes.get("type", "")
            })
        
        try:
            query_term = prompt_template.format(**replacements)
        except KeyError as e:
            logger.warning(f"Template variable not found: {e}. Using food name only.")
            query_term = item.name
        
        return query_term.strip()
    
    async def _search_usda_api(self, query_term: str, max_results: int = 5) -> List[RawFoodData]:
        """
        USDA API検索を実行
        
        Args:
            query_term: 検索クエリ
            max_results: 最大結果数
            
        Returns:
            List[RawFoodData]: 検索結果リスト
        """
        try:
            search_params = {
                "query": query_term,
                "api_key": self.api_key,
                "pageSize": max_results,
                "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"],  # 信頼性の高いデータタイプを優先
                "sortBy": "dataType.keyword",
                "sortOrder": "asc"
            }
            
            response = await self.client.get(
                f"{self.base_url}/foods/search",
                params=search_params
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if data.get("foods"):
                for food_entry in data["foods"]:
                    # 栄養素データを辞書形式に変換
                    nutrients_dict = {}
                    for nutrient in food_entry.get("foodNutrients", []):
                        nutrient_name = nutrient.get("nutrientName", "")
                        nutrient_value = nutrient.get("value", 0)
                        nutrient_unit = nutrient.get("unitName", "")
                        
                        if nutrient_name and nutrient_value is not None:
                            nutrients_dict[nutrient_name] = {
                                "value": nutrient_value,
                                "unit": nutrient_unit,
                                "nutrient_id": nutrient.get("nutrientId")
                            }
                    
                    raw_food = RawFoodData(
                        food_description=food_entry.get("description", "N/A"),
                        nutrients=nutrients_dict,
                        db_source_id=str(food_entry.get("fdcId", "")),
                        matched_query_term=query_term,
                        food_category=food_entry.get("foodCategory", ""),
                        brand_owner=food_entry.get("brandOwner", ""),
                        data_type=food_entry.get("dataType", ""),
                        publication_date=food_entry.get("publishedDate", "")
                    )
                    results.append(raw_food)
            
            logger.info(f"USDA search for '{query_term}' returned {len(results)} results")
            return results
            
        except httpx.HTTPStatusError as e:
            error_msg = f"USDA API HTTP error for '{query_term}': {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise DatabaseQueryError(error_msg) from e
        
        except httpx.RequestError as e:
            error_msg = f"USDA API request error for '{query_term}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseConnectionError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Unexpected error during USDA search for '{query_term}': {str(e)}"
            logger.error(error_msg)
            raise DatabaseQueryError(error_msg) from e 