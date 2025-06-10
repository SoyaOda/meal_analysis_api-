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
            self.log_processing_detail("search_method", "elasticsearch_strategic")
            return await self._elasticsearch_strategic_search(input_data, search_terms)
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
    
    async def _elasticsearch_strategic_search(self, input_data: NutritionQueryInput, search_terms: List[str]) -> NutritionQueryOutput:
        """
        戦略的Elasticsearch検索（dish/ingredient別の最適化された検索）
        
        Dish戦略:
        - メイン: EatThisMuch data_type=dish
        - 補助: EatThisMuch data_type=branded (スコアが低い場合)
        
        Ingredient戦略:
        - メイン: EatThisMuch data_type=ingredient  
        - 補助: MyNetDiary, YAZIO, EatThisMuch branded
        
        Args:
            input_data: 入力データ
            search_terms: 検索語彙リスト
            
        Returns:
            NutritionQueryOutput: 戦略的検索結果
        """
        matches = {}
        warnings = []
        errors = []
        successful_matches = 0
        total_searches = len(search_terms)
        
        start_time = datetime.now()
        
        # 各検索語彙について戦略的検索を実行
        for search_index, search_term in enumerate(search_terms):
            self.logger.debug(f"Strategic Elasticsearch search for: {search_term}")
            
            self.log_processing_detail(f"strategic_search_{search_index}_term", search_term)
            
            try:
                # クエリタイプを判定
                query_type = "dish" if search_term in input_data.dish_names else "ingredient"
                self.log_processing_detail(f"search_{search_index}_type", query_type)
                
                # 戦略的検索を実行
                if query_type == "dish":
                    strategic_results = await self._strategic_dish_search(search_term, input_data)
                else:
                    strategic_results = await self._strategic_ingredient_search(search_term, input_data)
                
                if strategic_results:
                    matches[search_term] = strategic_results
                    successful_matches += 1
                    
                    self.log_reasoning(
                        f"strategic_match_{search_index}",
                        f"Found strategic matches for '{search_term}' ({query_type}): {len(strategic_results)} results"
                    )
                else:
                    self.log_reasoning(
                        f"strategic_no_results_{search_index}",
                        f"No strategic results for '{search_term}' ({query_type})"
                    )
                    warnings.append(f"No strategic results found for: {search_term}")
                    
            except Exception as e:
                error_msg = f"Strategic Elasticsearch search error for '{search_term}': {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                
                self.log_reasoning(
                    f"strategic_search_error_{search_index}",
                    f"Strategic Elasticsearch search error for '{search_term}': {str(e)}"
                )
        
        end_time = datetime.now()
        search_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # 戦略的検索サマリーを作成
        total_results = sum(len(result_list) if isinstance(result_list, list) else 1 for result_list in matches.values())
        
        search_summary = {
            "total_searches": total_searches,
            "successful_matches": successful_matches,
            "failed_searches": total_searches - successful_matches,
            "match_rate_percent": round((successful_matches / total_searches) * 100, 1) if total_searches > 0 else 0,
            "search_method": "elasticsearch_strategic",
            "database_source": "elasticsearch_nutrition_db",
            "preferred_source": input_data.preferred_source,
            "search_time_ms": search_time_ms,
            "index_name": self.index_name,
            "total_indexed_documents": await self._get_total_document_count(),
            "strategic_approach": {
                "dish_strategy": "eatthismuch_dish_primary + eatthismuch_branded_fallback",
                "ingredient_strategy": "eatthismuch_ingredient_primary + multi_db_fallback"
            },
            "total_results": total_results
        }
        
        self.log_processing_detail("elasticsearch_strategic_search_summary", search_summary)
        
        result = NutritionQueryOutput(
            matches=matches,
            search_summary=search_summary,
            warnings=warnings if warnings else None,
            errors=errors if errors else None
        )
        
        self.logger.info(f"Strategic Elasticsearch nutrition search completed: {successful_matches}/{total_searches} matches ({result.get_match_rate():.1%}) with {total_results} total results in {search_time_ms}ms")
        
        return result

    async def _strategic_dish_search(self, search_term: str, input_data: NutritionQueryInput) -> List[NutritionMatch]:
        """
        Dish検索戦略を実行
        
        戦略:
        1. EatThisMuch data_type=dish をメイン検索
        2. スコアが低い場合は EatThisMuch data_type=branded を補助検索
        
        Args:
            search_term: 検索語彙
            input_data: 入力データ
            
        Returns:
            List[NutritionMatch]: 戦略的検索結果
        """
        results = []
        MIN_SCORE_THRESHOLD = 20.0  # スコア閾値
        
        self.logger.info(f"Strategic dish search for '{search_term}': EatThisMuch dish -> branded fallback")
        
        # Step 1: EatThisMuch dish をメイン検索
        main_query = self._build_strategic_query(search_term, "eatthismuch", "dish")
        
        try:
            response = self.es_client.search(index=self.index_name, body=main_query)
            hits = response.get('hits', {}).get('hits', [])
            
            if hits:
                best_score = hits[0].get('_score', 0)
                self.logger.info(f"Dish main search: found {len(hits)} results, best score: {best_score}")
                
                if best_score >= MIN_SCORE_THRESHOLD:
                    # 高スコア: メイン結果のみ使用
                    for hit in hits[:self.results_per_db]:
                        match = self._convert_es_hit_to_nutrition_match(hit, search_term)
                        match.search_metadata["strategic_phase"] = "main_dish"
                        match.search_metadata["strategy_type"] = "dish_primary"
                        results.append(match)
                    
                    self.logger.info(f"High score dish results: using {len(results)} main results")
                    return results
                else:
                    # 低スコア: メイン結果を保持して補助検索も実行
                    for hit in hits[:max(1, self.results_per_db // 2)]:
                        match = self._convert_es_hit_to_nutrition_match(hit, search_term)
                        match.search_metadata["strategic_phase"] = "main_dish_low_score"
                        match.search_metadata["strategy_type"] = "dish_primary"
                        results.append(match)
        
        except Exception as e:
            self.logger.error(f"Error in dish main search: {e}")
        
        # Step 2: EatThisMuch branded を補助検索
        fallback_query = self._build_strategic_query(search_term, "eatthismuch", "branded")
        
        try:
            response = self.es_client.search(index=self.index_name, body=fallback_query)
            hits = response.get('hits', {}).get('hits', [])
            
            if hits:
                remaining_slots = self.results_per_db - len(results)
                for hit in hits[:remaining_slots]:
                    match = self._convert_es_hit_to_nutrition_match(hit, search_term)
                    match.search_metadata["strategic_phase"] = "fallback_branded"
                    match.search_metadata["strategy_type"] = "dish_fallback"
                    results.append(match)
                
                self.logger.info(f"Dish fallback search: added {min(len(hits), remaining_slots)} branded results")
        
        except Exception as e:
            self.logger.error(f"Error in dish fallback search: {e}")
        
        # スコア順でソート
        results.sort(key=lambda x: x.score, reverse=True)
        
        self.logger.info(f"Strategic dish search completed: {len(results)} total results")
        return results

    async def _strategic_ingredient_search(self, search_term: str, input_data: NutritionQueryInput) -> List[NutritionMatch]:
        """
        Ingredient検索戦略を実行
        
        戦略:
        1. EatThisMuch data_type=ingredient をメイン検索
        2. MyNetDiary, YAZIO, EatThisMuch branded を補助検索
        
        Args:
            search_term: 検索語彙
            input_data: 入力データ
            
        Returns:
            List[NutritionMatch]: 戦略的検索結果
        """
        results = []
        
        self.logger.info(f"Strategic ingredient search for '{search_term}': EatThisMuch ingredient -> multi-DB fallback")
        
        # Step 1: EatThisMuch ingredient をメイン検索
        main_query = self._build_strategic_query(search_term, "eatthismuch", "ingredient")
        
        try:
            response = self.es_client.search(index=self.index_name, body=main_query)
            hits = response.get('hits', {}).get('hits', [])
            
            if hits:
                # メイン結果を追加（最大半分のスロット使用）
                main_slots = max(1, self.results_per_db // 2)
                for hit in hits[:main_slots]:
                    match = self._convert_es_hit_to_nutrition_match(hit, search_term)
                    match.search_metadata["strategic_phase"] = "main_ingredient"
                    match.search_metadata["strategy_type"] = "ingredient_primary"
                    results.append(match)
                
                self.logger.info(f"Ingredient main search: added {len(results)} primary results")
        
        except Exception as e:
            self.logger.error(f"Error in ingredient main search: {e}")
        
        # Step 2: 補助データベース検索
        fallback_sources = [
            ("mynetdiary", "unified"),
            ("yazio", "unified"), 
            ("eatthismuch", "branded")
        ]
        
        remaining_slots = self.results_per_db - len(results)
        slots_per_source = max(1, remaining_slots // len(fallback_sources))
        
        for db_name, data_type in fallback_sources:
            if remaining_slots <= 0:
                break
                
            try:
                fallback_query = self._build_strategic_query(search_term, db_name, data_type)
                response = self.es_client.search(index=self.index_name, body=fallback_query)
                hits = response.get('hits', {}).get('hits', [])
                
                if hits:
                    current_slots = min(slots_per_source, remaining_slots)
                    for hit in hits[:current_slots]:
                        match = self._convert_es_hit_to_nutrition_match(hit, search_term)
                        match.search_metadata["strategic_phase"] = "fallback_multi_db"
                        match.search_metadata["strategy_type"] = "ingredient_fallback"
                        match.search_metadata["fallback_source"] = f"{db_name}_{data_type}"
                        results.append(match)
                    
                    remaining_slots -= len(hits[:current_slots])
                    self.logger.info(f"Ingredient fallback ({db_name}_{data_type}): added {len(hits[:current_slots])} results")
            
            except Exception as e:
                self.logger.error(f"Error in ingredient fallback search ({db_name}_{data_type}): {e}")
        
        # スコア順でソート
        results.sort(key=lambda x: x.score, reverse=True)
        
        self.logger.info(f"Strategic ingredient search completed: {len(results)} total results")
        return results

    def _build_strategic_query(self, search_term: str, target_db: str, data_type: str) -> Dict[str, Any]:
        """
        戦略的検索用のElasticsearchクエリを構築
        
        Args:
            search_term: 検索語彙
            target_db: ターゲットデータベース
            data_type: データタイプ
            
        Returns:
            Elasticsearchクエリ辞書
        """
        query = {
            "size": self.results_per_db,
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": search_term,
                                "fields": [
                                    "search_name^3",
                                    "description^1"
                                ],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "filter": [
                        {"term": {"source_db": target_db}},
                        {"term": {"data_type": data_type}}
                    ]
                }
            },
            "sort": [
                {"_score": {"order": "desc"}}
            ]
        }
        
        return query
    
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