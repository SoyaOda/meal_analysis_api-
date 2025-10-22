#!/usr/bin/env python
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
    
    # 新方式の栄養データフィールド（default_unit + unit_to_grams方式）
    default_unit: Optional[str] = Field(None, description="デフォルト単位（例: 'cup', 'oz', 'piece'）")
    default_nutrition: Optional[Dict[str, float]] = Field(None, description="1 default_unit当たりの栄養素")
    unit_to_grams: Optional[Dict[str, float]] = Field(None, description="各単位をグラムに変換する係数")
    
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
    """栄養データベース検索入力モデル（構造化入力対応・v3.0粒度制御システム対応）"""
    ingredient_names: List[str] = Field(default_factory=list, description="食材名のリスト")
    dish_names: List[str] = Field(default_factory=list, description="料理名のリスト")
    base_foods: List[Dict[str, Any]] = Field(default_factory=list, description="base_food情報のリスト（v3.0）")
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
        all_terms = list(set(self.ingredient_names + self.dish_names))
        # base_foodsからもitem_nameを追加
        for bf in self.base_foods:
            if bf.get("item_name"):
                all_terms.append(bf["item_name"])
        return list(set(all_terms))
    
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
    
 

# Nutrition Query API用の追加モデル（SuggestionResponse関連）
from typing import List, Optional
from datetime import datetime

class QueryInfo(BaseModel):
    original_query: str = Field(..., description="元の検索クエリ", example="chicken")
    processed_query: str = Field(..., description="処理済みクエリ", example="chicken")
    timestamp: str = Field(..., description="リクエストタイムスタンプ（ISO 8601形式）", example="2025-01-15T10:30:00Z")
    suggestion_type: str = Field(default="autocomplete", description="提案タイプ", example="autocomplete")

class FoodInfo(BaseModel):
    search_name: str = Field(..., description="検索名（簡潔な名称）", example="Chicken breast skinless raw")
    search_name_list: List[str] = Field(..., description="検索名の候補リスト", example=["Chicken breast skinless raw", "Chicken breast meat only raw"])
    description: str = Field(..., description="詳細説明", example="Chicken, broilers or fryers, breast, meat only, raw")
    original_name: str = Field(..., description="オリジナル名（データベース名）", example="Chicken breast skinless raw")
    
    # USDA固有フィールド（オプション）
    ingredient_type: Optional[str] = Field(None, description="食材タイプ（USDA専用: raw/prepared）", example="raw")
    ai_description: Optional[str] = Field(None, description="AI生成の説明文（USDA専用）", example="Chicken breast without skin, raw")
    
    # LLM生成フィールド（オプション）
    brand_name: Optional[str] = Field(None, description="ブランド名（LLM生成）", example="Ritz")
    item_type: Optional[str] = Field(None, description="食材タイプ分類（LLM生成: raw_ingredient/processed_ingredient/prepared_dish）", example="processed_ingredient")

class NutritionPreview(BaseModel):
    calories: float = Field(..., description="カロリー (kcal)", example=165.0)
    protein: float = Field(..., description="タンパク質 (g)", example=31.0)
    carbohydrates: float = Field(..., description="炭水化物 (g)", example=0.0)
    fat: float = Field(..., description="脂質 (g)", example=3.6)
    per_serving: str = Field(default="100g", description="栄養価の基準量", example="100g")

class Suggestion(BaseModel):
    rank: int = Field(..., description="検索結果の順位", example=1)
    suggestion: str = Field(..., description="提案された食品名", example="Chicken breast skinless raw")
    match_type: str = Field(..., description="マッチタイプ（exact_match, tier_1_exact, tier_2_description等）", example="exact_match")
    confidence_score: float = Field(..., description="信頼度スコア (0-100)", example=100.0, ge=0.0, le=100.0)
    food_info: FoodInfo = Field(..., description="食品情報の詳細")
    nutrition_preview: NutritionPreview = Field(..., description="栄養価プレビュー（100gあたり）")
    alternative_names: List[str] = Field(..., description="代替名称リスト", example=["Chicken breast meat only", "Chicken breast"])

    # 新方式の栄養データフィールド（default_unit + unit_to_grams方式）
    default_unit: Optional[str] = Field(None, description="デフォルト単位（例: 'cup', 'oz', 'piece'）", example="oz")
    default_nutrition: Optional[dict] = Field(None, description="1 default_unit当たりの栄養素", example={"calories": 46.9, "protein": 8.8})
    unit_to_grams: Optional[dict] = Field(None, description="各単位をグラムに変換する係数", example={"1 oz": 28.35, "1 lb": 453.59})

class SearchMetadata(BaseModel):
    total_suggestions: int = Field(..., description="提案結果数", example=10)
    total_hits: int = Field(..., description="総ヒット数", example=42)
    search_time_ms: int = Field(..., description="Elasticsearch検索時間 (ms)", example=15)
    processing_time_ms: int = Field(..., description="総処理時間 (ms)", example=23)
    elasticsearch_index: str = Field(..., description="使用されたElasticsearchインデックス", example="mynetdiary_converted_tool_calls_list_stemmed_with_nutrition")

class SearchStatus(BaseModel):
    success: bool = Field(..., description="検索成功フラグ", example=True)
    message: str = Field(..., description="ステータスメッセージ", example="Suggestions generated successfully")

class DebugInfo(BaseModel):
    elasticsearch_query_used: str = Field(..., description="使用されたElasticsearch検索戦略", example="exact_match_only")
    search_strategy_config: Optional[dict] = Field(None, description="検索戦略設定", example={"search_context": "meal_analysis", "exclude_uncooked": True})
    tier_scoring: dict = Field(..., description="Tierスコアリング設定", example={"exact_match_original_name": 999, "tier_1_exact_match": 15})

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

class NutritionHealthCheckResponse(BaseModel):
    """栄養検索APIヘルスチェックレスポンス"""
    status: str = Field(..., description="ヘルス状態 (healthy/unhealthy)", example="healthy")
    service: str = Field(..., description="サービス名", example="nutrition_suggestion_api")
    elasticsearch_index: str = Field(..., description="Elasticsearchインデックス名", example="mynetdiary_converted_tool_calls_list_stemmed_with_nutrition")
    algorithm: str = Field(..., description="検索アルゴリズム", example="7_tier_optimized")
    test_query_success: bool = Field(..., description="テストクエリ成功フラグ", example=True)
