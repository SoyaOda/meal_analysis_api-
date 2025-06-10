#!/usr/bin/env python3
"""
Elasticsearch Nutrition Search Component

現状のqueryシステムをElasticsearchで高速化する新しいコンポーネント
Elasticsearch専用でフォールバック機能なし
"""

import os
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import BaseComponent
from ..models.nutrition_search_models import (
    NutritionQueryInput, NutritionQueryOutput, NutritionMatch
)
from ..config import get_settings

# Elasticsearchクライアント
try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False


class ElasticsearchNutritionSearchComponent(BaseComponent[NutritionQueryInput, NutritionQueryOutput]):
    """
    Elasticsearch専用栄養データベース検索コンポーネント
    
    現状のマルチデータベース検索システムをElasticsearchで高速化します。
    Elasticsearch専用でフォールバック機能は提供しません。
    """
    
    def __init__(self, elasticsearch_url: str = "http://localhost:9200", multi_db_search_mode: bool = False, results_per_db: int = 3):
        super().__init__("ElasticsearchNutritionSearchComponent")
        
        self.elasticsearch_url = elasticsearch_url
        self.es_client = None
        self.index_name = "nutrition_db"
        self.multi_db_search_mode = multi_db_search_mode
        self.results_per_db = results_per_db
        self.target_databases = ["yazio", "mynetdiary", "eatthismuch"]
        
        # Elasticsearchクライアントの初期化
        self._initialize_elasticsearch()
        
        self.logger.info(f"ElasticsearchNutritionSearchComponent initialized")
        self.logger.info(f"Elasticsearch available: {ELASTICSEARCH_AVAILABLE}")
        self.logger.info(f"ES client connected: {self.es_client is not None}")
        self.logger.info(f"Multi-DB search mode: {self.multi_db_search_mode}")
        self.logger.info(f"Results per database: {self.results_per_db}")
        
    def _initialize_elasticsearch(self):
        """Elasticsearchクライアントを初期化"""
        if not ELASTICSEARCH_AVAILABLE:
            self.logger.error("Elasticsearch library not available. Please install: pip install elasticsearch")
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
                    self.logger.error(f"Index '{self.index_name}' does not exist. Please run create_elasticsearch_index.py first.")
                    self.es_client = None
            else:
                self.logger.error("Elasticsearch ping failed. Please ensure Elasticsearch is running.")
                self.es_client = None
                
        except Exception as e:
            self.logger.error(f"Failed to connect to Elasticsearch: {e}")
            self.es_client = None
    
    async def process(self, input_data: NutritionQueryInput) -> NutritionQueryOutput:
        """
        Elasticsearch検索の主処理
        
        Args:
            input_data: NutritionQueryInput
            
        Returns:
            NutritionQueryOutput: Elasticsearch検索結果
            
        Raises:
            RuntimeError: Elasticsearchが利用できない場合
        """
        # Elasticsearch利用可能性チェック
        if not ELASTICSEARCH_AVAILABLE:
            error_msg = "Elasticsearch library not available. Please install: pip install elasticsearch"
            self.logger.error(error_msg)
            return NutritionQueryOutput(
                matches={},
                search_summary={
                    "total_searches": 0,
                    "successful_matches": 0,
                    "failed_searches": 0,
                    "match_rate_percent": 0,
                    "search_method": "elasticsearch_unavailable",
                    "search_time_ms": 0
                },
                errors=[error_msg]
            )
        
        if not self.es_client:
            error_msg = "Elasticsearch client not initialized. Please check connection and index availability."
            self.logger.error(error_msg)
            return NutritionQueryOutput(
                matches={},
                search_summary={
                    "total_searches": 0,
                    "successful_matches": 0,
                    "failed_searches": 0,
                    "match_rate_percent": 0,
                    "search_method": "elasticsearch_connection_failed",
                    "search_time_ms": 0
                },
                errors=[error_msg]
            )
        
        search_terms = input_data.get_all_search_terms()
        self.logger.info(f"Starting Elasticsearch nutrition search for {len(search_terms)} terms")
        
        # 検索対象の詳細をログに記録
        self.log_processing_detail("search_terms", search_terms)
        self.log_processing_detail("ingredient_names", input_data.ingredient_names)
        self.log_processing_detail("dish_names", input_data.dish_names)
        self.log_processing_detail("total_search_terms", len(search_terms))
        self.log_processing_detail("multi_db_search_mode", self.multi_db_search_mode)
        self.log_processing_detail("results_per_db", self.results_per_db)
        
        if self.multi_db_search_mode:
            self.log_processing_detail("search_method", "elasticsearch_multi_db")
            return await self._elasticsearch_multi_db_search(input_data, search_terms)
        else:
            self.log_processing_detail("search_method", "elasticsearch_single")
            return await self._elasticsearch_search(input_data, search_terms)
    
    async def _elasticsearch_search(self, input_data: NutritionQueryInput, search_terms: List[str]) -> NutritionQueryOutput:
        """
        Elasticsearchを使用した単一結果検索（従来の方式）
        
        Args:
            input_data: 入力データ
            search_terms: 検索語彙リスト
            
        Returns:
            NutritionQueryOutput: Elasticsearch検索結果
        """
        matches = {}
        warnings = []
        errors = []
        successful_matches = 0
        total_searches = len(search_terms)
        
        start_time = datetime.now()
        
        # 各検索語彙についてElasticsearch検索を実行
        for search_index, search_term in enumerate(search_terms):
            self.logger.debug(f"Elasticsearch search for: {search_term}")
            
            self.log_processing_detail(f"es_search_{search_index}_term", search_term)
            
            try:
                # Elasticsearchクエリの構築
                es_query = self._build_elasticsearch_query(search_term, input_data)
                
                # 検索実行
                response = self.es_client.search(
                    index=self.index_name,
                    body=es_query
                )
                
                # 結果処理
                hits = response.get('hits', {}).get('hits', [])
                
                if hits:
                    # 最良のマッチを選択
                    best_hit = hits[0]
                    source = best_hit['_source']
                    score = best_hit['_score']
                    
                    match_result = self._convert_es_hit_to_nutrition_match(best_hit, search_term)
                    matches[search_term] = match_result
                    successful_matches += 1
                    
                    self.log_reasoning(
                        f"es_match_{search_index}",
                        f"Found Elasticsearch match for '{search_term}': {source.get('search_name', 'N/A')} (score: {score:.3f}, db: {source.get('source_db', 'N/A')})"
                    )
                    
                    self.logger.debug(f"ES match for '{search_term}': {source.get('search_name', 'N/A')} from {source.get('source_db', 'N/A')}")
                else:
                    self.log_reasoning(
                        f"es_no_match_{search_index}",
                        f"No Elasticsearch match found for '{search_term}'"
                    )
                    warnings.append(f"No Elasticsearch match found for: {search_term}")
                    
            except Exception as e:
                error_msg = f"Elasticsearch search error for '{search_term}': {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                
                self.log_reasoning(
                    f"es_search_error_{search_index}",
                    f"Elasticsearch search error for '{search_term}': {str(e)}"
                )
        
        end_time = datetime.now()
        search_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # 検索サマリーを作成
        search_summary = {
            "total_searches": total_searches,
            "successful_matches": successful_matches,
            "failed_searches": total_searches - successful_matches,
            "match_rate_percent": round((successful_matches / total_searches) * 100, 1) if total_searches > 0 else 0,
            "search_method": "elasticsearch",
            "database_source": "elasticsearch_nutrition_db",
            "preferred_source": input_data.preferred_source,
            "search_time_ms": search_time_ms,
            "index_name": self.index_name,
            "total_indexed_documents": await self._get_total_document_count()
        }
        
        self.log_processing_detail("elasticsearch_search_summary", search_summary)
        
        result = NutritionQueryOutput(
            matches=matches,
            search_summary=search_summary,
            warnings=warnings if warnings else None,
            errors=errors if errors else None
        )
        
        self.logger.info(f"Elasticsearch nutrition search completed: {successful_matches}/{total_searches} matches ({result.get_match_rate():.1%}) in {search_time_ms}ms")
        
        return result
    
    async def _elasticsearch_multi_db_search(self, input_data: NutritionQueryInput, search_terms: List[str]) -> NutritionQueryOutput:
        """
        Elasticsearchを使用したマルチデータベース検索（各DBから複数結果を取得）
        
        Args:
            input_data: 入力データ
            search_terms: 検索語彙リスト
            
        Returns:
            NutritionQueryOutput: Elasticsearch検索結果（各DBから複数結果）
        """
        matches = {}
        warnings = []
        errors = []
        successful_matches = 0
        total_searches = len(search_terms)
        
        start_time = datetime.now()
        
        # 各検索語彙についてマルチDB検索を実行
        for search_index, search_term in enumerate(search_terms):
            self.logger.debug(f"Multi-DB Elasticsearch search for: {search_term}")
            
            self.log_processing_detail(f"multi_db_search_{search_index}_term", search_term)
            
            try:
                # 各データベースから結果を取得
                db_results = await self._search_all_databases(search_term, input_data)
                
                if db_results:
                    # 各データベースからの結果を統合
                    consolidated_results = self._consolidate_multi_db_results(db_results, search_term)
                    
                    if consolidated_results:
                        matches[search_term] = consolidated_results
                        successful_matches += 1
                        
                        self.log_reasoning(
                            f"multi_db_match_{search_index}",
                            f"Found multi-DB matches for '{search_term}': {len(consolidated_results)} total results from {len(db_results)} databases"
                        )
                    else:
                        self.log_reasoning(
                            f"multi_db_no_results_{search_index}",
                            f"No consolidated results for '{search_term}'"
                        )
                        warnings.append(f"No multi-DB results found for: {search_term}")
                else:
                    self.log_reasoning(
                        f"multi_db_no_match_{search_index}",
                        f"No multi-DB match found for '{search_term}'"
                    )
                    warnings.append(f"No multi-DB match found for: {search_term}")
                    
            except Exception as e:
                error_msg = f"Multi-DB Elasticsearch search error for '{search_term}': {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                
                self.log_reasoning(
                    f"multi_db_search_error_{search_index}",
                    f"Multi-DB Elasticsearch search error for '{search_term}': {str(e)}"
                )
        
        end_time = datetime.now()
        search_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # マルチDB検索サマリーを作成
        total_results = sum(len(result_list) if isinstance(result_list, list) else 1 for result_list in matches.values())
        
        search_summary = {
            "total_searches": total_searches,
            "successful_matches": successful_matches,
            "failed_searches": total_searches - successful_matches,
            "match_rate_percent": round((successful_matches / total_searches) * 100, 1) if total_searches > 0 else 0,
            "search_method": "elasticsearch_multi_db",
            "database_source": "elasticsearch_nutrition_db",
            "preferred_source": input_data.preferred_source,
            "search_time_ms": search_time_ms,
            "index_name": self.index_name,
            "total_indexed_documents": await self._get_total_document_count(),
            "results_per_db": self.results_per_db,
            "target_databases": self.target_databases,
            "total_results": total_results
        }
        
        self.log_processing_detail("elasticsearch_multi_db_search_summary", search_summary)
        
        result = NutritionQueryOutput(
            matches=matches,
            search_summary=search_summary,
            warnings=warnings if warnings else None,
            errors=errors if errors else None
        )
        
        self.logger.info(f"Multi-DB Elasticsearch nutrition search completed: {successful_matches}/{total_searches} matches ({result.get_match_rate():.1%}) with {total_results} total results in {search_time_ms}ms")
        
        return result
    
    async def _search_all_databases(self, search_term: str, input_data: NutritionQueryInput) -> Dict[str, List[Dict]]:
        """
        各データベースから検索結果を取得
        
        Args:
            search_term: 検索語彙
            input_data: 入力データ
            
        Returns:
            Dict[str, List[Dict]]: データベース名をキーとした検索結果辞書
        """
        db_results = {}
        
        self.logger.info(f"Starting multi-database search for '{search_term}' across {len(self.target_databases)} databases")
        
        for db_name in self.target_databases:
            self.logger.info(f"Searching in database: {db_name}")
            try:
                # データベース固有のクエリを構築
                es_query = self._build_multi_db_elasticsearch_query(search_term, input_data, db_name)
                self.logger.debug(f"Query for {db_name}: {es_query}")
                
                # 検索実行
                response = self.es_client.search(
                    index=self.index_name,
                    body=es_query
                )
                
                hits = response.get('hits', {}).get('hits', [])
                if hits:
                    db_results[db_name] = hits[:self.results_per_db]  # 指定された件数まで取得
                    self.logger.info(f"Found {len(hits)} results in {db_name} for '{search_term}', storing {len(db_results[db_name])}")
                else:
                    self.logger.info(f"No results in {db_name} for '{search_term}'")
                    
            except Exception as e:
                self.logger.error(f"Error searching {db_name} for '{search_term}': {e}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        self.logger.info(f"Multi-database search completed. Found results in {len(db_results)} databases: {list(db_results.keys())}")
        return db_results
    
    def _consolidate_multi_db_results(self, db_results: Dict[str, List[Dict]], search_term: str) -> List[NutritionMatch]:
        """
        各データベースからの検索結果を統合
        
        Args:
            db_results: データベース別検索結果
            search_term: 検索語彙
            
        Returns:
            List[NutritionMatch]: 統合された結果リスト
        """
        consolidated = []
        
        for db_name, hits in db_results.items():
            for hit in hits:
                match = self._convert_es_hit_to_nutrition_match(hit, search_term)
                # データベース名を明示的にメタデータに追加
                match.search_metadata["source_database"] = db_name
                match.search_metadata["multi_db_search"] = True
                consolidated.append(match)
        
        # スコア順でソート
        consolidated.sort(key=lambda x: x.score, reverse=True)
        
        return consolidated
    
    async def _get_total_document_count(self) -> int:
        """インデックス内の総ドキュメント数を取得"""
        try:
            stats = self.es_client.indices.stats(index=self.index_name)
            return stats["indices"][self.index_name]["total"]["docs"]["count"]
        except Exception as e:
            self.logger.warning(f"Failed to get document count: {e}")
            return 0
    
    def _build_elasticsearch_query(self, search_term: str, input_data: NutritionQueryInput) -> Dict[str, Any]:
        """
        Elasticsearch検索クエリを構築
        
        Args:
            search_term: 検索語彙
            input_data: 入力データ（検索タイプ判定用）
            
        Returns:
            Elasticsearchクエリ辞書
        """
        # 基本的なmulti_matchクエリ
        base_query = {
            "multi_match": {
                "query": search_term,
                "fields": [
                    "search_name^3",  # 検索名に高い重み
                    "search_name.exact^5"  # 完全一致に最高の重み
                ],
                "type": "best_fields",
                "fuzziness": "AUTO",
                "operator": "OR"
            }
        }
        
        # データタイプとソースデータベースフィルタ
        filters = []
        
        # dish_namesに含まれる場合は料理データを優先
        if search_term in input_data.dish_names:
            filters.append({"term": {"data_type": "dish"}})
        # ingredient_namesに含まれる場合は食材データを優先
        elif search_term in input_data.ingredient_names:
            filters.append({"term": {"data_type": "ingredient"}})
        
        # 優先ソースの設定
        if input_data.preferred_source and input_data.preferred_source != "elasticsearch":
            source_mapping = {
                "yazio": "yazio",
                "mynetdiary": "mynetdiary", 
                "eatthismuch": "eatthismuch"
            }
            if input_data.preferred_source in source_mapping:
                filters.append({"term": {"source_db": source_mapping[input_data.preferred_source]}})
        
        # フィルタがある場合はboolクエリでラップ
        if filters:
            query = {
                "bool": {
                    "must": [base_query],
                    "should": filters,  # shouldで優先度付け
                    "boost": 1.2
                }
            }
        else:
            query = base_query
        
        return {
            "query": query,
            "size": 5,  # 上位5件を取得
            "_source": ["data_type", "id", "search_name", "nutrition", "weight", "source_db", "description"]
        }
    
    def _build_multi_db_elasticsearch_query(self, search_term: str, input_data: NutritionQueryInput, target_db: str) -> Dict[str, Any]:
        """
        特定データベース向けElasticsearch検索クエリを構築
        
        Args:
            search_term: 検索語彙
            input_data: 入力データ
            target_db: 対象データベース名
            
        Returns:
            Elasticsearchクエリ辞書
        """
        # 基本的なmulti_matchクエリ
        base_query = {
            "multi_match": {
                "query": search_term,
                "fields": [
                    "search_name^3",
                    "search_name.exact^5"
                ],
                "type": "best_fields",
                "fuzziness": "AUTO",
                "operator": "OR"
            }
        }
        
        # 必須フィルタ：指定されたデータベースのみ
        # data_typeフィルタは削除して、全てのタイプから検索
        filters = [{"term": {"source_db": target_db}}]
        
        query = {
            "bool": {
                "must": [base_query] + filters
            }
        }
        
        return {
            "query": query,
            "size": self.results_per_db,  # データベースあたりの取得件数
            "_source": ["data_type", "id", "search_name", "nutrition", "weight", "source_db", "description"]
        }
    
    def _convert_es_hit_to_nutrition_match(self, hit: Dict[str, Any], search_term: str) -> NutritionMatch:
        """
        ElasticsearchヒットをNutritionMatchに変換
        
        Args:
            hit: Elasticsearchヒット
            search_term: 検索語彙
            
        Returns:
            NutritionMatch
        """
        source = hit['_source']
        score = hit['_score']
        
        # ソースデータベース情報を含める
        source_db = source.get('source_db', 'unknown')
        final_source = f"elasticsearch_{source_db}"
        
        return NutritionMatch(
            id=source.get('id', 0),
            search_name=source.get('search_name', search_term),
            description=source.get('description'),
            data_type=source.get('data_type', 'unknown'),
            source=final_source,
            nutrition=source.get('nutrition', {}),
            weight=source.get('weight'),
            score=score,
            search_metadata={
                "search_term": search_term,
                "elasticsearch_score": score,
                "search_method": "elasticsearch_multi_db" if self.multi_db_search_mode else "elasticsearch",
                "source_database": source_db,
                "index_name": self.index_name
            }
        ) 