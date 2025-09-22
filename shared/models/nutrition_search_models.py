#!/usr/bin/env python3
"""
Nutrition Search Models

ローカル栄養データベース検索で使用する純粋なローカル形式のモデル（構造化入力対応）
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


class NutritionMatch(BaseModel):
    """栄養データベース照合結果モデル（純粋なローカル形式）"""
    id: Union[int, str] = Field(..., description="食品ID（ローカルID）")
    name: str = Field(..., description="食品名")  # search_nameから変更
    search_name: str = Field(..., description="検索名（簡潔な名称）")
    description: Optional[str] = Field(None, description="詳細説明")
    data_type: str = Field(..., description="データタイプ (dish, ingredient, branded)")
    source_db: str = Field(..., description="ソースデータベース（yazio, mynetdiary, eatthismuch）")
    source: str = Field(default="local_database", description="データソース（'local_database'）")
    
    # ローカルDBの生の栄養データ（100gあたり正規化済み）
    nutrition: Dict[str, float] = Field(default_factory=dict, description="ローカルDBの栄養データ（100gあたり）")
    weight: Optional[float] = Field(None, description="元データの重量（g）")
    
    # 検索スコア
    score: Optional[float] = Field(None, description="検索結果の関連度スコア")
    
    # 検索に関するメタデータ
    search_metadata: Optional[Dict[str, Any]] = Field(None, description="検索に関するメタデータ")

    model_config = {"protected_namespaces": ()}


class AdvancedSearchOptions(BaseModel):
    """高度な検索オプション"""
    enable_fuzzy_matching: bool = Field(default=True, description="ファジーマッチングを有効にする")
    enable_two_stage_search: bool = Field(default=True, description="二段階検索を有効にする")
    primary_term_boost: float = Field(default=3.0, description="プライマリ用語のブースト値")
    brand_boost: float = Field(default=2.5, description="ブランド情報のブースト値")
    ingredient_boost: float = Field(default=1.5, description="材料情報のブースト値")
    preparation_boost: float = Field(default=1.2, description="調理法情報のブースト値")
    jaro_winkler_threshold: float = Field(default=0.8, description="Jaro-Winkler類似度の閾値")
    levenshtein_threshold: float = Field(default=0.7, description="Levenshtein類似度の閾値")
    first_stage_size: int = Field(default=50, description="第一段階で取得する候補数")
    final_result_size: int = Field(default=10, description="最終結果数")

    model_config = {"protected_namespaces": ()}


class NutritionQueryInput(BaseModel):
    """栄養データベース検索入力モデル（構造化入力対応）"""
    ingredient_names: List[str] = Field(default_factory=list, description="食材名のリスト")
    dish_names: List[str] = Field(default_factory=list, description="料理名のリスト")
    search_options: Optional[Dict[str, Any]] = Field(None, description="検索オプション")
    preferred_source: str = Field(default="local_database", description="優先データソース")
    
    # 構造化データのサポート
    structured_analysis: Optional[Dict[str, Any]] = Field(None, description="Phase1からの構造化分析データ")
    phase1_output: Optional[Any] = Field(None, description="Phase1Outputオブジェクト（構造化データ含む）")
    
    # 高度な検索オプション
    advanced_search_options: Optional[AdvancedSearchOptions] = Field(None, description="高度な検索オプション")
    
    # 検索戦略
    search_strategy: str = Field(default="basic", description="検索戦略（basic, strategic, advanced_structured）")

    model_config = {"protected_namespaces": ()}

    def get_all_search_terms(self) -> List[str]:
        """全ての検索語彙を取得"""
        return list(set(self.ingredient_names + self.dish_names))
    
    def get_structured_search_terms(self) -> Optional[Dict[str, Any]]:
        """構造化された検索用語を取得"""
        if self.phase1_output and hasattr(self.phase1_output, 'get_structured_search_terms'):
            return self.phase1_output.get_structured_search_terms()
        elif self.structured_analysis:
            return self.structured_analysis
        else:
            return None
    
    def get_primary_search_terms(self) -> List[str]:
        """プライマリ検索用語を取得（高信頼度アイテム）"""
        if self.phase1_output and hasattr(self.phase1_output, 'get_primary_search_terms'):
            return self.phase1_output.get_primary_search_terms()
        else:
            return self.get_all_search_terms()
    
    def has_structured_data(self) -> bool:
        """構造化データが利用可能かチェック"""
        return (
            self.structured_analysis is not None or
            (self.phase1_output and hasattr(self.phase1_output, 'detected_food_items'))
        )
    
    def is_advanced_search_enabled(self) -> bool:
        """高度な検索が有効かチェック"""
        return (
            self.search_strategy in ["advanced_structured", "strategic"] or
            self.has_structured_data()
        )


class NutritionQueryOutput(BaseModel):
    """栄養データベース検索結果モデル（構造化出力対応）"""
    # マルチデータベース検索対応：単一結果またはリスト結果を受け入れる
    matches: Dict[str, Union[NutritionMatch, List[NutritionMatch]]] = Field(
        default_factory=dict, 
        description="検索語彙と対応する照合結果のマッピング（単一結果またはマルチDB結果リスト）"
    )
    search_summary: Dict[str, Any] = Field(
        default_factory=dict, 
        description="検索結果のサマリー情報（柔軟な型対応）"
    )
    warnings: Optional[List[str]] = Field(None, description="警告メッセージのリスト")
    errors: Optional[List[str]] = Field(None, description="エラーメッセージのリスト")
    
    # 高度な検索結果のメタデータ
    advanced_search_metadata: Optional[Dict[str, Any]] = Field(None, description="高度な検索のメタデータ")

    model_config = {"protected_namespaces": ()}

    def get_match_rate(self) -> float:
        """Exact Match率を計算"""
        return self.search_summary.get("exact_match_rate_percent", 0.0) / 100.0

    def get_total_matches(self) -> int:
        """総照合件数を取得（マルチDB検索対応）"""
        total = 0
        for match_result in self.matches.values():
            if isinstance(match_result, list):
                total += len(match_result)
            else:
                total += 1
        return total
    
    def get_total_individual_results(self) -> int:
        """個別結果の総数を取得（マルチDB検索用）"""
        return self.get_total_matches()
    
    def has_errors(self) -> bool:
        """エラーが存在するかチェック"""
        return self.errors is not None and len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """警告が存在するかチェック"""
        return self.warnings is not None and len(self.warnings) > 0
    
    def get_search_method(self) -> str:
        """使用された検索方法を取得"""
        return self.search_summary.get("search_method", "unknown")
    
    def is_advanced_search_result(self) -> bool:
        """高度な検索の結果かチェック"""
        search_method = self.get_search_method()
        return search_method in [
            "advanced_structured_elasticsearch", 
            "elasticsearch_strategic",
            "two_stage_search"
        ] 

# Nutrition Query API用の追加モデル（SuggestionResponse関連）
from typing import List, Optional
from datetime import datetime

class QueryInfo(BaseModel):
    original_query: str
    processed_query: str
    timestamp: str
    suggestion_type: str = "autocomplete"

class FoodInfo(BaseModel):
    search_name: str
    search_name_list: List[str]
    description: str
    original_name: str

class NutritionPreview(BaseModel):
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    per_serving: str = "100g"

class Suggestion(BaseModel):
    rank: int
    suggestion: str
    match_type: str
    confidence_score: float
    food_info: FoodInfo
    nutrition_preview: NutritionPreview
    alternative_names: List[str]

class SearchMetadata(BaseModel):
    total_suggestions: int
    total_hits: int
    search_time_ms: int
    processing_time_ms: int
    elasticsearch_index: str

class SearchStatus(BaseModel):
    success: bool
    message: str

class DebugInfo(BaseModel):
    elasticsearch_query_used: str
    tier_scoring: dict

class SuggestionResponse(BaseModel):
    query_info: QueryInfo
    suggestions: List[Suggestion]
    metadata: SearchMetadata
    status: SearchStatus
    debug_info: Optional[DebugInfo] = None

class SuggestionErrorResponse(BaseModel):
    query_info: QueryInfo
    suggestions: List[Suggestion]
    metadata: SearchMetadata
    status: SearchStatus
