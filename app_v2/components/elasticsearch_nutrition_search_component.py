#!/usr/bin/env python3
"""
Elasticsearch Nutrition Search Component

高度なクエリ戦略対応版：構造化入力、bool query、function_score、文字列類似度、二段階検索
"""

import os
import json
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from .base import BaseComponent
from ..models.nutrition_search_models import (
    NutritionQueryInput, NutritionQueryOutput, NutritionMatch
)
from ..models.phase1_models import Phase1Output, DetectedFoodItem, FoodAttribute, AttributeType
from ..config import get_settings

# 文字列類似度アルゴリズム
try:
    from rapidfuzz.distance import JaroWinkler, Levenshtein
    from rapidfuzz.fuzz import ratio, partial_ratio
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

# Elasticsearchクライアント
try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False


class ElasticsearchNutritionSearchComponent(BaseComponent[NutritionQueryInput, NutritionQueryOutput]):
    """
    Elasticsearch栄養データベース検索コンポーネント（高度なクエリ戦略対応）
    
    構造化入力対応、bool query、function_score、文字列類似度、二段階検索を実装
    """
    
    def __init__(
        self, 
        elasticsearch_url: str = "http://localhost:9200", 
        multi_db_search_mode: bool = False, 
        results_per_db: int = 3,
        enable_advanced_features: bool = True
    ):
        super().__init__("ElasticsearchNutritionSearchComponent")
        
        self.elasticsearch_url = elasticsearch_url
        self.es_client = None
        self.index_name = "nutrition_db"
        self.multi_db_search_mode = multi_db_search_mode
        self.results_per_db = results_per_db
        self.target_databases = ["yazio", "mynetdiary", "eatthismuch"]
        
        # 高度な機能フラグ
        self.enable_advanced_features = enable_advanced_features
        self.enable_fuzzy_matching = RAPIDFUZZ_AVAILABLE and enable_advanced_features
        self.enable_two_stage_search = enable_advanced_features
        
        # 二段階検索のパラメータ
        self.first_stage_size = 50  # 第一段階で取得する候補数
        self.final_result_size = 10  # 最終的な結果数
        
        # ブースティングとスコアリングのパラメータ
        self.primary_term_boost = 3.0
        self.brand_boost = 2.5
        self.ingredient_boost = 1.5
        self.preparation_boost = 1.2
        self.jaro_winkler_threshold = 0.8
        self.levenshtein_threshold = 0.7
        
        # Elasticsearchクライアントの初期化
        self._initialize_elasticsearch()
        
        self.logger.info(f"ElasticsearchNutritionSearchComponent initialized")
        self.logger.info(f"Advanced features enabled: {self.enable_advanced_features}")
        self.logger.info(f"Fuzzy matching available: {self.enable_fuzzy_matching}")
        self.logger.info(f"Two-stage search enabled: {self.enable_two_stage_search}")
        
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
        高度なElasticsearch検索の主処理
        
        Args:
            input_data: NutritionQueryInput (構造化入力対応)
            
        Returns:
            NutritionQueryOutput: 高度なElasticsearch検索結果
            
        Raises:
            RuntimeError: Elasticsearchが利用できない場合
        """
        # Elasticsearch利用可能性チェック
        if not ELASTICSEARCH_AVAILABLE or not self.es_client:
            return self._create_error_response("Elasticsearch not available")
        
        start_time = datetime.now()
        
        # 構造化入力の検出と処理
        structured_data = self._extract_structured_data(input_data)
        search_terms = input_data.get_all_search_terms()
        
        self.logger.info(f"Starting advanced Elasticsearch search for {len(search_terms)} terms")
        self.log_processing_detail("structured_data_available", structured_data is not None)
        self.log_processing_detail("search_terms", search_terms)
        self.log_processing_detail("advanced_features_enabled", self.enable_advanced_features)
        
        if self.enable_advanced_features and structured_data:
            # 構造化データを使用した高度な検索
            return await self._advanced_structured_search(input_data, structured_data, search_terms, start_time)
        elif self.multi_db_search_mode:
            # 従来の戦略的検索
            return await self._elasticsearch_strategic_search(input_data, search_terms)
        else:
            # 基本検索
            return await self._elasticsearch_search(input_data, search_terms)
    
    def _extract_structured_data(self, input_data: NutritionQueryInput) -> Optional[Dict[str, Any]]:
        """入力データから構造化データを抽出"""
        # NutritionQueryInputが構造化データを含んでいるかチェック
        if hasattr(input_data, 'structured_analysis') and input_data.structured_analysis:
            return input_data.structured_analysis
        
        # 代替: Phase1Outputから構造化データを抽出
        if hasattr(input_data, 'phase1_output') and input_data.phase1_output:
            phase1_output = input_data.phase1_output
            if hasattr(phase1_output, 'get_structured_search_terms'):
                return phase1_output.get_structured_search_terms()
        
        return None
    
    async def _advanced_structured_search(
        self, 
        input_data: NutritionQueryInput, 
        structured_data: Dict[str, Any], 
        search_terms: List[str],
        start_time: datetime
    ) -> NutritionQueryOutput:
        """構造化データを使用した高度な検索"""
        self.log_processing_detail("search_method", "advanced_structured")
        
        matches = {}
        successful_matches = 0
        total_searches = len(search_terms)
        
        # 高信頼度アイテムの処理
        high_confidence_items = structured_data.get('high_confidence_items', [])
        medium_confidence_items = structured_data.get('medium_confidence_items', [])
        brands = structured_data.get('brands', [])
        ingredients = structured_data.get('ingredients', [])
        cooking_methods = structured_data.get('cooking_methods', [])
        negative_cues = structured_data.get('negative_cues', [])
        
        self.log_processing_detail("high_confidence_items_count", len(high_confidence_items))
        self.log_processing_detail("brands_detected", brands)
        self.log_processing_detail("negative_cues", negative_cues)
        
        # 各検索語彙に対して高度な検索を実行
        for search_index, search_term in enumerate(search_terms):
            try:
                # 構造化データを使用したクエリ構築
                advanced_query = self._build_advanced_structured_query(
                    search_term, 
                    structured_data, 
                    input_data
                )
                
                if self.enable_two_stage_search:
                    # 二段階検索
                    nutrition_matches = await self._two_stage_search(
                        advanced_query, 
                        search_term, 
                        structured_data
                    )
                else:
                    # 単段階高度検索
                    nutrition_matches = await self._single_stage_advanced_search(
                        advanced_query, 
                        search_term
                    )
                
                if nutrition_matches:
                    matches[search_term] = nutrition_matches[0]  # ベストマッチを選択
                    successful_matches += 1
                    
                    self.log_reasoning(
                        f"advanced_match_{search_index}",
                        f"Advanced structured match for '{search_term}': {nutrition_matches[0].name} "
                        f"(score: {nutrition_matches[0].score:.3f}, db: {nutrition_matches[0].source_db})"
                    )
                
            except Exception as e:
                self.logger.error(f"Advanced search failed for '{search_term}': {e}")
                continue
        
        # 結果の統計処理
        search_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        match_rate = (successful_matches / total_searches * 100) if total_searches > 0 else 0
        
        return NutritionQueryOutput(
            matches=matches,
            search_summary={
                "total_searches": total_searches,
                "successful_matches": successful_matches,
                "failed_searches": total_searches - successful_matches,
                "match_rate_percent": round(match_rate, 1),
                "search_method": "advanced_structured_elasticsearch",
                "search_time_ms": search_time_ms,
                "high_confidence_items": len(high_confidence_items),
                "brands_used": len(brands),
                "negative_cues_applied": len(negative_cues),
                "fuzzy_matching_enabled": self.enable_fuzzy_matching,
                "two_stage_search_enabled": self.enable_two_stage_search
            },
            errors=[]
        )
    
    def _build_advanced_structured_query(
        self, 
        search_term: str, 
        structured_data: Dict[str, Any], 
        input_data: NutritionQueryInput
    ) -> Dict[str, Any]:
        """構造化データを使用した高度なElasticsearchクエリを構築"""
        
        # 構造化データから関連情報を抽出
        high_confidence_items = structured_data.get('high_confidence_items', [])
        brands = structured_data.get('brands', [])
        ingredients = structured_data.get('ingredients', [])
        cooking_methods = structured_data.get('cooking_methods', [])
        negative_cues = structured_data.get('negative_cues', [])
        
        # 現在の検索語句が高信頼度アイテムに含まれるかチェック
        is_high_confidence = any(
            item.item_name.lower() == search_term.lower() 
            for item in high_confidence_items 
            if hasattr(item, 'item_name')
        )
        
        # Bool クエリの構築
        bool_query = {
            "bool": {
                "must": [],
                "should": [],
                "must_not": []
            }
        }
        
        # Must句: 高信頼度の場合は必須条件として使用
        if is_high_confidence:
            bool_query["bool"]["must"].append({
                "match_phrase": {
                    "search_name": {
                        "query": search_term,
                        "boost": self.primary_term_boost
                    }
                }
            })
        else:
            # 中・低信頼度の場合はshouldで柔軟に
            bool_query["bool"]["should"].append({
                "match_phrase": {
                    "search_name": {
                        "query": search_term,
                        "boost": self.primary_term_boost,
                        "slop": 1  # 単語間の距離を1つまで許可
                    }
                }
            })
            
            # 代替マッチングオプション
            bool_query["bool"]["should"].append({
                "match": {
                    "search_name": {
                        "query": search_term,
                        "boost": self.primary_term_boost * 0.8
                    }
                }
            })
        
        # Should句: ブランド情報によるブースト
        for brand in brands:
            if brand:
                bool_query["bool"]["should"].append({
                    "match": {
                        "search_name": {
                            "query": brand,
                            "boost": self.brand_boost
                        }
                    }
                })
        
        # Should句: 材料情報によるブースト
        for ingredient in ingredients:
            if ingredient:
                bool_query["bool"]["should"].append({
                    "match": {
                        "search_name": {
                            "query": ingredient,
                            "boost": self.ingredient_boost
                        }
                    }
                })
        
        # Should句: 調理法情報によるブースト
        for cooking_method in cooking_methods:
            if cooking_method:
                bool_query["bool"]["should"].append({
                    "multi_match": {
                        "query": cooking_method,
                        "fields": ["search_name", "source_description"],
                        "boost": self.preparation_boost
                    }
                })
        
        # Must_not句: ネガティブキュー（除外条件）
        for negative_cue in negative_cues:
            if negative_cue:
                bool_query["bool"]["must_not"].append({
                    "match": {
                        "search_name": negative_cue
                    }
                })
        
        # Function_score クエリでラップ（文字列類似度適用）
        # Painlessスクリプトの問題のため、RapidFuzzベースの二段階検索を使用
        if False:  # self.enable_fuzzy_matching:
            try:
                query = {
                    "function_score": {
                        "query": bool_query,
                        "functions": [
                            {
                                "script_score": {
                                    "script": {
                                        "source": self._get_similarity_script(),
                                        "params": {
                                            "search_term": search_term
                                        }
                                    }
                                }
                            }
                        ],
                        "score_mode": "max",
                        "boost_mode": "multiply"
                    }
                }
            except Exception as script_error:
                # スクリプトエラーの場合はbool queryにフォールバック
                self.logger.warning(f"Script score error, falling back to bool query: {script_error}")
                query = bool_query
        else:
            query = bool_query
        
        return {
            "query": query,
            "size": self.first_stage_size if self.enable_two_stage_search else self.final_result_size,
            "_source": True,
            "sort": [
                {"_score": {"order": "desc"}}
            ]
        }
    
    def _get_similarity_script(self) -> str:
        """文字列類似度計算用のPainlessスクリプト（シンプル版）"""
        return """
        if (doc['search_name.keyword'].size() == 0) {
            return _score;
        }
        String dbName = doc['search_name.keyword'].value;
        String searchTerm = params.search_term;
        
        if (dbName == null || searchTerm == null) {
            return _score;
        }
        
        String dbLower = dbName.toLowerCase();
        String searchLower = searchTerm.toLowerCase();
        
        // 完全一致
        if (dbLower.equals(searchLower)) {
            return _score * 2.0;
        }
        
        // 部分一致
        if (dbLower.contains(searchLower) || searchLower.contains(dbLower)) {
            return _score * 1.5;
        }
        
        return _score;
        """
    
    async def _two_stage_search(
        self, 
        first_stage_query: Dict[str, Any], 
        search_term: str, 
        structured_data: Dict[str, Any]
    ) -> List[NutritionMatch]:
        """二段階検索の実行"""
        
        # 第一段階: 広めに候補を取得
        response = self.es_client.search(
            index=self.index_name,
            body=first_stage_query
        )
        
        first_stage_hits = response.get('hits', {}).get('hits', [])
        self.log_processing_detail("first_stage_hits_count", len(first_stage_hits))
        
        if not first_stage_hits:
            return []
        
        # 第二段階: 詳細な再ランキング
        candidates = []
        for hit in first_stage_hits:
            nutrition_match = self._convert_es_hit_to_nutrition_match(hit, search_term)
            
            # 詳細な類似度スコアを計算（RapidFuzzを使用）
            if self.enable_fuzzy_matching:
                enhanced_score = self._calculate_enhanced_similarity_score(
                    nutrition_match, 
                    search_term, 
                    structured_data
                )
                nutrition_match.score = enhanced_score
            
            candidates.append(nutrition_match)
        
        # スコア順でソート
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        # 上位結果を返す
        final_results = candidates[:self.final_result_size]
        
        self.log_processing_detail("second_stage_results_count", len(final_results))
        if final_results:
            self.log_processing_detail("top_result_score", final_results[0].score)
        
        return final_results
    
    def _calculate_enhanced_similarity_score(
        self, 
        nutrition_match: NutritionMatch, 
        search_term: str, 
        structured_data: Dict[str, Any]
    ) -> float:
        """RapidFuzzを使用した詳細な類似度スコア計算"""
        if not RAPIDFUZZ_AVAILABLE:
            return nutrition_match.score
        
        base_score = nutrition_match.score
        db_name = nutrition_match.name.lower()
        search_lower = search_term.lower()
        
        # Jaro-Winkler 類似度
        jaro_winkler_score = JaroWinkler.similarity(db_name, search_lower)
        
        # Levenshtein 類似度（正規化）
        levenshtein_score = 1.0 - (Levenshtein.distance(db_name, search_lower) / max(len(db_name), len(search_lower)))
        
        # FuzzyWuzzy Ratio
        fuzzy_ratio = ratio(db_name, search_lower) / 100.0
        
        # FuzzyWuzzy Partial Ratio
        partial_ratio_score = partial_ratio(db_name, search_lower) / 100.0
        
        # 重み付き組み合わせ
        similarity_boost = (
            jaro_winkler_score * 0.4 +
            levenshtein_score * 0.3 +
            fuzzy_ratio * 0.2 +
            partial_ratio_score * 0.1
        )
        
        # ブランド一致ボーナス
        brands = structured_data.get('brands', [])
        brand_bonus = 0.0
        for brand in brands:
            if brand and brand.lower() in db_name:
                brand_bonus = 0.3
                break
        
        # 最終スコア計算
        enhanced_score = base_score * (1.0 + similarity_boost + brand_bonus)
        
        return enhanced_score
    
    async def _single_stage_advanced_search(
        self, 
        advanced_query: Dict[str, Any], 
        search_term: str
    ) -> List[NutritionMatch]:
        """単段階高度検索の実行"""
        
        response = self.es_client.search(
            index=self.index_name,
            body=advanced_query
        )
        
        hits = response.get('hits', {}).get('hits', [])
        
        results = []
        for hit in hits:
            nutrition_match = self._convert_es_hit_to_nutrition_match(hit, search_term)
            results.append(nutrition_match)
        
        return results
    
    def _create_error_response(self, error_message: str) -> NutritionQueryOutput:
        """エラーレスポンスを作成"""
        return NutritionQueryOutput(
            matches={},
            search_summary={
                "total_searches": 0,
                "successful_matches": 0,
                "failed_searches": 0,
                "match_rate_percent": 0,
                "search_method": "error",
                "search_time_ms": 0
            },
            errors=[error_message]
        )

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
        
        # ソースデータベース情報を取得
        source_db = source.get('source_db', 'unknown')
        search_name = source.get('search_name', search_term)
        final_source = f"elasticsearch_{source_db}"
        
        return NutritionMatch(
            id=source.get('id', 0),
            name=search_name,  # 必須フィールド追加
            search_name=search_name,
            description=source.get('description'),
            data_type=source.get('data_type', 'unknown'),
            source_db=source_db,  # 必須フィールド追加
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