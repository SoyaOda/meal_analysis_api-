"""
MyNetDiary専用栄養データベース検索コンポーネント
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from .base import BaseComponent
from ..models.nutrition_search_models import NutritionQueryInput, NutritionQueryOutput, NutritionMatch
from ..utils.mynetdiary_utils import validate_ingredient_against_mynetdiary

# Elasticsearchの可用性チェック
try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    Elasticsearch = None

class MyNetDiaryNutritionSearchComponent(BaseComponent[NutritionQueryInput, NutritionQueryOutput]):
    """
    MyNetDiary専用栄養データベース検索コンポーネント
    
    特徴:
    - ingredientに対しては完全一致の1つの項目のみを取得
    - 複数項目や0件の場合はエラーで全体の解析を停止
    - dishに対しては従来通りの検索を実行
    """
    
    def __init__(
        self, 
        elasticsearch_url: str = "http://localhost:9200",
        results_per_db: int = 3
    ):
        """
        MyNetDiaryNutritionSearchComponentの初期化
        
        Args:
            elasticsearch_url: ElasticsearchのURL
            results_per_db: データベースあたりの結果数（dishの場合）
        """
        super().__init__("MyNetDiaryNutritionSearchComponent")
        self.elasticsearch_url = elasticsearch_url
        self.results_per_db = results_per_db
        
        # インデックス名
        self.index_name = "nutrition_db"
        
        # Elasticsearchクライアントの初期化
        self.es_client = None
        self._initialize_elasticsearch()

    def _initialize_elasticsearch(self):
        """Elasticsearchクライアントを初期化"""
        if not ELASTICSEARCH_AVAILABLE:
            self.logger.error("Elasticsearch library not available")
            return
        
        try:
            self.es_client = Elasticsearch([self.elasticsearch_url])
            
            # 接続テスト
            if self.es_client.ping():
                self.logger.info(f"Successfully connected to Elasticsearch at {self.elasticsearch_url}")
                
                # インデックス存在確認
                if self.es_client.indices.exists(index=self.index_name):
                    self.logger.info(f"Index '{self.index_name}' exists and ready")
                else:
                    self.logger.error(f"Index '{self.index_name}' does not exist")
            else:
                self.logger.error(f"Failed to connect to Elasticsearch at {self.elasticsearch_url}")
                self.es_client = None
                
        except Exception as e:
            self.logger.error(f"Error initializing Elasticsearch: {e}")
            self.es_client = None

    async def process(self, input_data: NutritionQueryInput) -> NutritionQueryOutput:
        """
        MyNetDiary専用検索の主処理
        
        Args:
            input_data: NutritionQueryInput
            
        Returns:
            NutritionQueryOutput: MyNetDiary専用検索結果
            
        Raises:
            RuntimeError: Elasticsearchが利用できない場合、またはingredient検索で複数/0件の場合
        """
        # Elasticsearch利用可能性チェック
        if not ELASTICSEARCH_AVAILABLE or not self.es_client:
            raise RuntimeError("Elasticsearch not available for MyNetDiary search")
        
        start_time = datetime.now()
        
        search_terms = input_data.get_all_search_terms()
        self.logger.info(f"Starting MyNetDiary specialized search for {len(search_terms)} terms")
        
        matches = {}
        successful_matches = 0
        total_searches = len(search_terms)
        errors = []
        
        # 各検索語彙について処理
        for search_index, search_term in enumerate(search_terms):
            try:
                # ingredientかdishかを判定
                if search_term in input_data.ingredient_names:
                    # ingredient検索: 厳密な1件マッチング
                    result = await self._strict_ingredient_search(search_term)
                    if result:
                        matches[search_term] = result
                        successful_matches += 1
                        self.logger.info(f"Strict ingredient match for '{search_term}': {result.name}")
                    else:
                        # ingredient検索で結果がない場合はエラーで停止
                        error_msg = f"CRITICAL: No exact match found for ingredient '{search_term}' in MyNetDiary database"
                        self.logger.error(error_msg)
                        raise RuntimeError(error_msg)
                        
                elif search_term in input_data.dish_names:
                    # dish検索: 従来通りの検索
                    results = await self._flexible_dish_search(search_term)
                    if results:
                        matches[search_term] = results
                        successful_matches += 1
                        self.logger.info(f"Dish search for '{search_term}': {len(results)} results")
                    else:
                        self.logger.warning(f"No dish results found for '{search_term}'")
                        
            except Exception as e:
                error_msg = f"MyNetDiary search error for '{search_term}': {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                # ingredient検索のエラーの場合は全体を停止
                if search_term in input_data.ingredient_names:
                    raise RuntimeError(error_msg)
        
        # 結果の構築
        end_time = datetime.now()
        search_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        total_results = sum(len(result_list) if isinstance(result_list, list) else 1 for result_list in matches.values())
        match_rate = (successful_matches / total_searches * 100) if total_searches > 0 else 0
        
        search_summary = {
            "total_searches": total_searches,
            "successful_matches": successful_matches,
            "failed_searches": total_searches - successful_matches,
            "match_rate_percent": round(match_rate, 1),
            "search_method": "mynetdiary_specialized",
            "search_time_ms": search_time_ms,
            "total_results": total_results,
            "ingredient_strict_matching": True,
            "dish_flexible_matching": True
        }
        
        result = NutritionQueryOutput(
            matches=matches,
            search_summary=search_summary,
            errors=errors if errors else None
        )
        
        self.logger.info(f"MyNetDiary specialized search completed: {successful_matches}/{total_searches} matches in {search_time_ms}ms")
        
        return result

    async def _strict_ingredient_search(self, ingredient_name: str) -> Optional[NutritionMatch]:
        """
        ingredient用の厳密検索（完全一致の1件のみ）
        
        Args:
            ingredient_name: 検索する食材名
            
        Returns:
            NutritionMatch: 完全一致の1件、または None
            
        Raises:
            RuntimeError: 複数件マッチした場合
        """
        # まずMyNetDiaryリストに含まれているかチェック
        if not validate_ingredient_against_mynetdiary(ingredient_name):
            self.logger.error(f"Ingredient '{ingredient_name}' not found in MyNetDiary list")
            return None
        
        # MyNetDiaryデータベースから完全一致検索
        query = {
            "size": 10,  # 複数件チェック用
            "query": {
                "bool": {
                    "must": [
                        {"term": {"search_name.exact": ingredient_name}},
                        {"term": {"source_db": "mynetdiary"}}
                    ]
                }
            }
        }
        
        try:
            response = self.es_client.search(index=self.index_name, body=query)
            hits = response.get('hits', {}).get('hits', [])
            
            if len(hits) == 0:
                self.logger.error(f"No exact match found for ingredient '{ingredient_name}' in MyNetDiary database")
                return None
            elif len(hits) > 1:
                # 複数件マッチした場合はエラー
                hit_names = [hit['_source'].get('search_name', 'N/A') for hit in hits]
                error_msg = f"Multiple matches found for ingredient '{ingredient_name}': {hit_names}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            else:
                # 正確に1件マッチした場合
                hit = hits[0]
                match = self._convert_es_hit_to_nutrition_match(hit, ingredient_name)
                match.search_metadata["search_type"] = "strict_ingredient"
                match.search_metadata["validation_passed"] = True
                return match
                
        except Exception as e:
            self.logger.error(f"Error in strict ingredient search for '{ingredient_name}': {e}")
            raise

    async def _flexible_dish_search(self, dish_name: str) -> List[NutritionMatch]:
        """
        dish用の柔軟検索（従来通り）
        
        Args:
            dish_name: 検索する料理名
            
        Returns:
            List[NutritionMatch]: 検索結果のリスト
        """
        # 複数データベースから検索
        query = {
            "size": self.results_per_db,
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": dish_name,
                                "fields": [
                                    "search_name^3",
                                    "description^1"
                                ],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "should": [
                        {"term": {"data_type": "dish"}},
                        {"term": {"data_type": "branded"}}
                    ]
                }
            },
            "sort": [
                {"_score": {"order": "desc"}}
            ]
        }
        
        try:
            response = self.es_client.search(index=self.index_name, body=query)
            hits = response.get('hits', {}).get('hits', [])
            
            results = []
            for hit in hits:
                match = self._convert_es_hit_to_nutrition_match(hit, dish_name)
                match.search_metadata["search_type"] = "flexible_dish"
                results.append(match)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in flexible dish search for '{dish_name}': {e}")
            return []

    def _convert_es_hit_to_nutrition_match(self, hit: Dict[str, Any], search_term: str) -> NutritionMatch:
        """ElasticsearchのhitをNutritionMatchに変換"""
        source = hit['_source']
        score = hit['_score']
        
        return NutritionMatch(
            id=source.get('id', hit.get('_id', 'unknown')),
            name=source.get('search_name', 'Unknown'),
            search_name=source.get('search_name', 'Unknown'),
            description=source.get('description'),
            data_type=source.get('data_type', 'unknown'),
            source_db=source.get('source_db', 'unknown'),
            nutrition=source.get('nutrition', {}),
            weight=source.get('weight', 100),
            score=score,
            search_metadata={
                "search_term": search_term,
                "elasticsearch_score": score,
                "search_method": "mynetdiary_specialized",
                "source_database": source.get('source_db', 'unknown'),
                "index_name": self.index_name,
                "data_type": source.get('data_type', 'unknown')
            }
        ) 