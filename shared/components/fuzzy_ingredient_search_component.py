"""
高度なファジーマッチングシステム - 食材検索コンポーネント

5階層の検索カスケードを実装:
Tier 1: 完全一致検索 (Case-Insensitive)
Tier 2: 正規化一致検索
Tier 3: 高信頼性ファジー検索 (Elasticsearch)
Tier 4: 高度なセマンティック・構造検索 (Elasticsearch)
Tier 5: アプリケーションレベルでの再ランキング (Jaro-Winkler)
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from elasticsearch import Elasticsearch
from rapidfuzz.distance import JaroWinkler

from .base import BaseComponent
from ..models.nutrition_search_models import NutritionQueryOutput, NutritionMatch
from ..config.settings import get_settings

# ロギング設定
logger = logging.getLogger(__name__)

class FuzzyIngredientSearchComponent(BaseComponent):
    """高度なファジーマッチングによる食材検索コンポーネント"""
    
    def __init__(self):
        super().__init__("FuzzyIngredientSearchComponent")
        self.settings = get_settings()
        self.es_client = None
        self._initialize_elasticsearch()
    
    def _initialize_elasticsearch(self):
        """Elasticsearchクライアントを初期化"""
        try:
            self.es_client = Elasticsearch(
                hosts=[self.settings.elasticsearch_url],
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            # 接続テスト
            if self.es_client.ping():
                logger.info("✅ Elasticsearch接続成功")
            else:
                logger.error("❌ Elasticsearch接続失敗")
                self.es_client = None
        except Exception as e:
            logger.error(f"❌ Elasticsearch初期化エラー: {e}")
            self.es_client = None
    
    def normalize_and_sort_string(self, query_string: str) -> str:
        """Tier 2のための正規化処理"""
        if not query_string:
            return ""
        
        # 小文字化、句読点除去、単語のアルファベット順ソート
        cleaned_string = re.sub(r'[^\w\s]', '', query_string.lower())
        sorted_words = sorted(cleaned_string.split())
        return " ".join(sorted_words)
    
    def _tier1_exact_match(self, query_string: str) -> Optional[Dict[str, Any]]:
        """Tier 1: 完全一致検索 (Case-Insensitive)"""
        if not self.es_client:
            return None
        
        try:
            query = {
                "query": {
                    "term": {
                        "search_name.exact": query_string
                    }
                },
                "size": 1
            }
            
            response = self.es_client.search(
                index=self.settings.elasticsearch_index_name,
                body=query
            )
            
            if response['hits']['hits']:
                hit = response['hits']['hits'][0]
                logger.info(f"Tier 1 完全一致: '{query_string}' -> {hit['_source']['search_name']}")
                return hit['_source']
                
        except Exception as e:
            logger.error(f"Tier 1 検索エラー: {e}")
        
        return None
    
    def _tier2_normalized_match(self, query_string: str) -> Optional[Dict[str, Any]]:
        """Tier 2: 正規化一致検索"""
        if not self.es_client:
            return None
        
        normalized_query = self.normalize_and_sort_string(query_string)
        if not normalized_query:
            return None
        
        try:
            # 正規化されたフィールドでの検索
            query = {
                "query": {
                    "match": {
                        "search_name_normalized": {
                            "query": normalized_query,
                            "operator": "and"
                        }
                    }
                },
                "size": 1
            }
            
            response = self.es_client.search(
                index=self.settings.elasticsearch_index_name,
                body=query
            )
            
            if response['hits']['hits']:
                hit = response['hits']['hits'][0]
                logger.info(f"Tier 2 正規化一致: '{query_string}' -> {hit['_source']['search_name']}")
                return hit['_source']
                
        except Exception as e:
            logger.error(f"Tier 2 検索エラー: {e}")
        
        return None
    
    def _tier3_high_confidence_fuzzy(self, query_string: str) -> Optional[Dict[str, Any]]:
        """Tier 3: 高信頼性ファジー検索"""
        if not self.es_client:
            return None
        
        try:
            query = {
                "min_score": 5.0,
                "query": {
                    "multi_match": {
                        "query": query_string,
                        "fields": ["search_name"],
                        "type": "best_fields",
                        "fuzziness": "AUTO",
                        "prefix_length": 2,
                        "max_expansions": 10
                    }
                },
                "size": 1
            }
            
            response = self.es_client.search(
                index=self.settings.elasticsearch_index_name,
                body=query
            )
            
            if response['hits']['hits']:
                hit = response['hits']['hits'][0]
                score = hit['_score']
                logger.info(f"Tier 3 高信頼性ファジー: '{query_string}' -> {hit['_source']['search_name']} (score: {score:.2f})")
                return hit['_source']
                
        except Exception as e:
            logger.error(f"Tier 3 検索エラー: {e}")
        
        return None
    
    def _tier4_advanced_semantic_search(self, query_string: str) -> List[Dict[str, Any]]:
        """Tier 4: 高度なセマンティック・構造検索"""
        if not self.es_client:
            return []
        
        try:
            query = {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": query_string,
                                    "fields": ["search_name^3", "description"],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO:4,7",
                                    "prefix_length": 1,
                                    "boost": 3
                                }
                            },
                            {
                                "match": {
                                    "search_name.edge_ngram": {
                                        "query": query_string,
                                        "boost": 1
                                    }
                                }
                            },
                            {
                                "match": {
                                    "search_name_normalized": {
                                        "query": self.normalize_and_sort_string(query_string),
                                        "boost": 5
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": 5
            }
            
            response = self.es_client.search(
                index=self.settings.elasticsearch_index_name,
                body=query
            )
            
            candidates = []
            for hit in response['hits']['hits']:
                candidates.append(hit['_source'])
                logger.info(f"Tier 4 候補: {hit['_source']['search_name']} (score: {hit['_score']:.2f})")
            
            return candidates
            
        except Exception as e:
            logger.error(f"Tier 4 検索エラー: {e}")
            return []
    
    def _tier5_jaro_winkler_rerank(self, query_string: str, candidates: List[Dict[str, Any]], threshold: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Tier 5: Jaro-Winkler再ランキング"""
        if not candidates:
            return None
        
        best_match = None
        highest_score = 0.0
        
        for candidate in candidates:
            candidate_name = candidate.get('search_name', '')
            if not candidate_name:
                continue
            
            # Jaro-Winklerスコアを計算（距離を類似度に変換）
            distance = JaroWinkler.distance(query_string.lower(), candidate_name.lower())
            score = 1.0 - distance
            
            logger.info(f"Jaro-Winkler: '{query_string}' vs '{candidate_name}' = {score:.4f}")
            
            if score > highest_score:
                highest_score = score
                best_match = candidate
        
        # 閾値が指定されていない場合は設定から取得
        if threshold is None:
            threshold = self.settings.jaro_winkler_threshold
        
        if highest_score >= threshold:
            logger.info(f"Tier 5 最終一致: {best_match['search_name']} (score: {highest_score:.4f})")
            return best_match
        else:
            logger.warning(f"Tier 5: 最高スコア {highest_score:.4f} < 閾値 {threshold}")
            return None
    
    def find_ingredient(self, query_string: str, disambiguate: bool = False) -> Dict[str, Any]:
        """
        5階層の検索カスケードを実行して食材を特定するオーケストレータ関数
        
        Args:
            query_string: 検索クエリ文字列
            disambiguate: 曖昧性がある場合に複数候補を返すかどうか
            
        Returns:
            検索結果辞書
        """
        logger.info(f"🔍 食材検索開始: '{query_string}'")
        
        if not query_string or not query_string.strip():
            return {
                "status": "error",
                "message": "検索クエリが空です",
                "tier": 0
            }
        
        query_string = query_string.strip()
        
        # Tier 1: 完全一致検索
        result = self._tier1_exact_match(query_string)
        if result:
            return {
                "status": "success",
                "tier": 1,
                "data": result,
                "confidence": "exact"
            }
        
        # Tier 2: 正規化一致検索
        result = self._tier2_normalized_match(query_string)
        if result:
            return {
                "status": "success", 
                "tier": 2,
                "data": result,
                "confidence": "normalized"
            }
        
        # Tier 3: 高信頼性ファジー検索
        result = self._tier3_high_confidence_fuzzy(query_string)
        if result:
            return {
                "status": "success",
                "tier": 3,
                "data": result,
                "confidence": "high_fuzzy"
            }
        
        # Tier 4: 高度なセマンティック・構造検索
        candidates = self._tier4_advanced_semantic_search(query_string)
        if not candidates:
            logger.warning(f"❌ 全階層で一致なし: '{query_string}'")
            return {
                "status": "error",
                "message": f"No exact match found for ingredient '{query_string}'",
                "tier": 4
            }
        
        # Tier 5: Jaro-Winkler再ランキング
        final_match = self._tier5_jaro_winkler_rerank(query_string, candidates)
        if final_match:
            return {
                "status": "success",
                "tier": 5,
                "data": final_match,
                "confidence": "semantic_match"
            }
        
        # 曖昧性処理
        if disambiguate and candidates:
            return {
                "status": "ambiguous",
                "tier": 5,
                "candidates": candidates[:3],  # 上位3候補
                "message": f"Multiple potential matches found for '{query_string}'"
            }
        
        # 全階層で失敗
        logger.error(f"❌ CRITICAL: No exact match found for ingredient '{query_string}' after all tiers.")
        return {
            "status": "error",
            "message": f"No exact match found for ingredient '{query_string}'",
            "tier": 5
        }
    
    async def process(self, input_data: List[Dict[str, Any]]) -> NutritionQueryOutput:
        """BaseComponentの抽象メソッド実装"""
        return await self.execute_search(input_data)
    
    async def execute_search(self, detected_items: List[Dict[str, Any]], **kwargs) -> NutritionQueryOutput:
        """BaseComponentインターフェースの実装"""
        matches = {}
        successful_matches = 0
        
        for item in detected_items:
            ingredient_name = item.get('name', '')
            if not ingredient_name:
                continue
            
            # ファジーマッチング検索を実行
            search_result = self.find_ingredient(
                ingredient_name, 
                disambiguate=kwargs.get('disambiguate', False)
            )
            
            if search_result['status'] == 'success':
                nutrition_match = NutritionMatch(
                    id=search_result['data'].get('id', 0),
                    name=search_result['data']['search_name'],
                    search_name=search_result['data']['search_name'],
                    description=search_result['data'].get('description'),
                    data_type=search_result['data'].get('data_type', 'unknown'),
                    source_db=search_result['data'].get('source_db', 'unknown'),
                    nutrition=search_result['data'].get('nutrition', {}),
                    weight=search_result['data'].get('weight'),
                    search_metadata={
                        'tier': search_result['tier'],
                        'confidence_level': search_result['confidence']
                    }
                )
                matches[ingredient_name] = nutrition_match
                successful_matches += 1
            else:
                # エラーの場合もログに記録
                logger.warning(f"検索失敗: {ingredient_name} - {search_result.get('message', 'Unknown error')}")
        
        return NutritionQueryOutput(
            matches=matches,
            search_summary={
                'total_searches': len(detected_items),
                'successful_matches': successful_matches,
                'search_method': 'fuzzy_multi_tier_cascade',
                'component': 'FuzzyIngredientSearchComponent'
            }
        ) 