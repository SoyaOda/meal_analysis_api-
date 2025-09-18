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
    
    # 完全一致判定（新機能）
    is_exact_match: bool = Field(default=False, description="柔軟な完全一致かどうか（大文字小文字、語形変化、単複、所有格、語順の違いを許容）")
    match_details: Dict[str, Any] = Field(default_factory=dict, description="マッチング詳細情報")
    
    # 検索に関するメタデータ
    search_metadata: Optional[Dict[str, Any]] = Field(None, description="検索に関するメタデータ")
    
    class Config:
        # デフォルト値でもJSONシリアライゼーションに含める
        fields = {
            "is_exact_match": {"alias": "is_exact_match"},
            "match_details": {"alias": "match_details"}
        }


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

    def get_match_rate(self) -> float:
        """照合成功率を計算"""
        total_searches = self.search_summary.get("total_searches", 0)
        successful_matches = self.search_summary.get("successful_matches", 0)
        if total_searches == 0:
            return 0.0
        return successful_matches / total_searches

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


# Word Query API専用レスポンスモデル
class QueryInfo(BaseModel):
    """検索クエリ情報"""
    original_query: str = Field(..., description="元の検索クエリ", example="chicken")
    processed_query: str = Field(..., description="処理後検索クエリ", example="chicken") 
    timestamp: str = Field(..., description="処理時刻（ISO 8601 UTC形式）", example="2025-09-18T07:42:15.123456Z")
    suggestion_type: str = Field(default="autocomplete", description="提案タイプ", example="autocomplete")


class FoodInfo(BaseModel):
    """食材詳細情報"""
    search_name: str = Field(..., description="検索名", example="chicken breast")
    search_name_list: List[str] = Field(..., description="検索名リスト", example=["chicken breast", "chicken breast fillet"])
    description: Optional[str] = Field(None, description="食材説明", example="boneless, skinless, raw")
    original_name: str = Field(..., description="元の食材名", example="Chicken breast boneless skinless raw")


class NutritionPreview(BaseModel):
    """栄養プレビュー"""
    calories: float = Field(..., description="カロリー（kcal）", example=165.0)
    protein: float = Field(..., description="タンパク質（g）", example=31.0)
    carbohydrates: float = Field(..., description="炭水化物（g）", example=0.0)
    fat: float = Field(..., description="脂質（g）", example=3.6)
    per_serving: str = Field(default="100g", description="基準量", example="100g")


class Suggestion(BaseModel):
    """検索候補"""
    rank: int = Field(..., description="順位", example=1)
    suggestion: str = Field(..., description="提案食材名", example="chicken breast")
    match_type: str = Field(..., description="マッチタイプ", example="exact_match")
    confidence_score: float = Field(..., description="信頼度スコア（0-100）", example=95.8)
    food_info: FoodInfo = Field(..., description="食材詳細情報")
    nutrition_preview: NutritionPreview = Field(..., description="栄養プレビュー")
    alternative_names: List[str] = Field(..., description="代替名リスト", example=["chicken breast fillet", "chicken breast meat"])


class SearchMetadata(BaseModel):
    """検索メタデータ"""
    total_suggestions: int = Field(..., description="総提案数", example=10)
    total_hits: int = Field(..., description="総ヒット数", example=25)
    search_time_ms: int = Field(..., description="検索時間（ミリ秒）", example=350)
    processing_time_ms: int = Field(..., description="処理時間（ミリ秒）", example=385)
    elasticsearch_index: str = Field(..., description="使用インデックス", example="mynetdiary_list_support_db")


class SearchStatus(BaseModel):
    """検索ステータス"""
    success: bool = Field(..., description="成功フラグ", example=True)
    message: str = Field(..., description="ステータスメッセージ", example="Suggestions generated successfully")


class DebugInfo(BaseModel):
    """デバッグ情報（debug=true時）"""
    elasticsearch_query_used: str = Field(..., description="使用されたElasticsearchクエリタイプ")
    tier_scoring: Dict[str, int] = Field(..., description="Tier検索スコア設定")


class SuggestionResponse(BaseModel):
    """Word Query API レスポンスモデル"""
    query_info: QueryInfo = Field(..., description="検索クエリ情報")
    suggestions: List[Suggestion] = Field(..., description="検索候補リスト")
    metadata: SearchMetadata = Field(..., description="検索メタデータ")
    status: SearchStatus = Field(..., description="検索ステータス")
    debug_info: Optional[DebugInfo] = Field(None, description="デバッグ情報（debug=true時のみ）")


class SuggestionErrorResponse(BaseModel):
    """Word Query API エラーレスポンスモデル"""
    query_info: QueryInfo = Field(..., description="検索クエリ情報")
    suggestions: List[Suggestion] = Field(default_factory=list, description="空の検索候補リスト")
    metadata: SearchMetadata = Field(..., description="検索メタデータ")
    status: SearchStatus = Field(..., description="検索ステータス")
