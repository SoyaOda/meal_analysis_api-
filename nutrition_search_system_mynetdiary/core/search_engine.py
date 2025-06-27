"""
栄養検索エンジン - 7段階検索戦略と見出し語化機能
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from .models import SearchQuery, SearchResponse, SearchResult, NutritionInfo, BatchSearchQuery, BatchSearchResponse
from utils.lemmatization import lemmatize_term, create_lemmatized_query_variations
from utils.elasticsearch_client import get_elasticsearch_client

logger = logging.getLogger(__name__)


class NutritionSearchEngine:
    """栄養データベース検索エンジン"""
    
    def __init__(self):
        self.es_client = get_elasticsearch_client()
        
        # 検索パラメータ
        self.lemmatized_exact_match_boost = 2.0
        self.compound_word_penalty = 0.8
        self.enable_lemmatization = True
        
        # 統計
        self.total_searches = 0
        self.total_response_time = 0
        
        logger.info("🔍 NutritionSearchEngine initialized")
    
    async def search(self, query: SearchQuery) -> SearchResponse:
        """単一検索実行"""
        start_time = datetime.now()
        
        if not self.es_client.is_connected():
            return SearchResponse(
                query=query.query,
                results=[],
                total_found=0,
                search_time_ms=0,
                lemmatized_query=None
            )
        
        # 見出し語化処理
        lemmatized_query = lemmatize_term(query.query) if self.enable_lemmatization else query.query
        
        # 7段階検索クエリ構築
        es_query = self._build_advanced_search_query(query.query, lemmatized_query, query.max_results)
        
        # Elasticsearch検索実行
        response = await self.es_client.search(es_query)
        
        # 結果変換
        results = []
        if response and response.get('hits', {}).get('hits'):
            results = self._convert_es_results(response['hits']['hits'], query.query, lemmatized_query)
            
            # スコアフィルタリング
            results = [r for r in results if r.score >= query.min_score]
            
            # ソースDBフィルタリング
            if query.source_db_filter:
                results = [r for r in results if r.source_db in query.source_db_filter]
        
        # 統計更新
        end_time = datetime.now()
        search_time_ms = int((end_time - start_time).total_seconds() * 1000)
        self.total_searches += 1
        self.total_response_time += search_time_ms
        
        return SearchResponse(
            query=query.query,
            results=results,
            total_found=len(results),
            search_time_ms=search_time_ms,
            lemmatized_query=lemmatized_query if lemmatized_query != query.query else None
        )
    
    async def batch_search(self, batch_query: BatchSearchQuery) -> BatchSearchResponse:
        """バッチ検索実行"""
        start_time = datetime.now()
        
        # 並列検索実行
        search_tasks = []
        for query_text in batch_query.queries:
            search_query = SearchQuery(
                query=query_text,
                max_results=batch_query.max_results
            )
            search_tasks.append(self.search(search_query))
        
        responses = await asyncio.gather(*search_tasks)
        
        # 統計情報作成
        end_time = datetime.now()
        total_search_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        total_results = sum(len(r.results) for r in responses)
        successful_searches = sum(1 for r in responses if len(r.results) > 0)
        
        summary = {
            "total_queries": len(batch_query.queries),
            "successful_searches": successful_searches,
            "total_results": total_results,
            "average_results_per_query": total_results / len(batch_query.queries) if batch_query.queries else 0,
            "match_rate_percent": (successful_searches / len(batch_query.queries) * 100) if batch_query.queries else 0
        }
        
        return BatchSearchResponse(
            queries=batch_query.queries,
            responses=responses,
            total_search_time_ms=total_search_time_ms,
            summary=summary
        )
    
    def _build_advanced_search_query(self, original_term: str, lemmatized_term: str, max_results: int) -> Dict[str, Any]:
        """7段階検索戦略のElasticsearchクエリ構築"""
        
        bool_query = {
            "bool": {
                "should": [
                    # 1. 見出し語化完全一致（最高ブースト）
                    {
                        "match": {
                            "search_name_lemmatized.exact": {
                                "query": lemmatized_term,
                                "boost": self.lemmatized_exact_match_boost * 3.0
                            }
                        }
                    },
                    # 2. 見出し語化一致（高ブースト）
                    {
                        "match": {
                            "search_name_lemmatized": {
                                "query": lemmatized_term,
                                "boost": self.lemmatized_exact_match_boost * 2.0
                            }
                        }
                    },
                    # 3. 元の語での完全一致
                    {
                        "match": {
                            "search_name.exact": {
                                "query": original_term,
                                "boost": 1.8
                            }
                        }
                    },
                    # 4. 元の語での一致
                    {
                        "match": {
                            "search_name": {
                                "query": original_term,
                                "boost": 1.5
                            }
                        }
                    },
                    # 5. 見出し語化部分一致
                    {
                        "match_phrase": {
                            "search_name_lemmatized": {
                                "query": lemmatized_term,
                                "boost": self.lemmatized_exact_match_boost
                            }
                        }
                    },
                    # 6. 元の語での部分一致
                    {
                        "match_phrase": {
                            "search_name": {
                                "query": original_term,
                                "boost": 1.0
                            }
                        }
                    },
                    # 7. あいまい検索（typo対応）
                    {
                        "fuzzy": {
                            "search_name_lemmatized": {
                                "value": lemmatized_term,
                                "fuzziness": "AUTO",
                                "boost": 0.5
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }
        
        return {
            "query": bool_query,
            "size": max_results * 2,  # スコア調整後に絞り込むため多めに取得
            "_source": ["id", "search_name", "description", "data_type", "nutrition", "source_db"]
        }
    
    def _convert_es_results(self, es_hits: List[Dict[str, Any]], original_term: str, lemmatized_term: str) -> List[SearchResult]:
        """Elasticsearch結果をSearchResultに変換"""
        results = []
        
        for hit in es_hits:
            source = hit['_source']
            
            # 栄養情報変換
            nutrition_data = source.get('nutrition', {})
            nutrition = NutritionInfo(**nutrition_data)
            
            # マッチタイプ判定
            match_type = self._determine_match_type(
                source.get('search_name', ''),
                source.get('search_name_lemmatized', ''),
                original_term,
                lemmatized_term
            )
            
            # スコア調整
            adjusted_score = self._calculate_adjusted_score(
                hit['_score'],
                original_term,
                lemmatized_term,
                source.get('search_name', ''),
                source.get('search_name_lemmatized', ''),
                match_type
            )
            
            result = SearchResult(
                id=str(source.get('id', '')),
                name=source.get('search_name', ''),
                description=source.get('description', ''),
                nutrition=nutrition,
                source_db=source.get('source_db', ''),
                score=adjusted_score,
                match_type=match_type
            )
            
            results.append(result)
        
        # スコア順でソート
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def _determine_match_type(self, db_name: str, db_name_lemmatized: str, original_term: str, lemmatized_term: str) -> str:
        """マッチタイプを判定"""
        db_name_lower = db_name.lower()
        db_lemmatized_lower = db_name_lemmatized.lower()
        original_lower = original_term.lower()
        lemmatized_lower = lemmatized_term.lower()
        
        if db_name_lower == original_lower or db_lemmatized_lower == lemmatized_lower:
            return "exact"
        elif db_lemmatized_lower == lemmatized_lower:
            return "lemmatized"
        elif original_lower in db_name_lower or lemmatized_lower in db_lemmatized_lower:
            return "partial"
        else:
            return "fuzzy"
    
    def _calculate_adjusted_score(
        self, 
        base_score: float, 
        original_term: str, 
        lemmatized_term: str, 
        db_name: str, 
        db_name_lemmatized: str, 
        match_type: str
    ) -> float:
        """スコア調整計算"""
        
        # ベーススコア調整
        if match_type == "exact":
            adjustment = self.lemmatized_exact_match_boost
        elif match_type == "lemmatized":
            adjustment = self.lemmatized_exact_match_boost * 0.9
        elif match_type == "partial":
            adjustment = 0.8
        else:  # fuzzy
            adjustment = 0.5
        
        # 複合語ペナルティ
        if len(original_term.split()) > 1:
            adjustment *= self.compound_word_penalty
        
        return base_score * adjustment
    
    def get_stats(self) -> Dict[str, Any]:
        """検索統計取得"""
        avg_response_time = (self.total_response_time / self.total_searches) if self.total_searches > 0 else 0
        
        return {
            "total_searches": self.total_searches,
            "average_response_time_ms": avg_response_time,
            "total_documents": self.es_client.get_total_documents(),
            "elasticsearch_health": self.es_client.get_index_stats()
        } 