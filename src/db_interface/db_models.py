"""
DB Interface用のPydanticモデル定義

データベースクエリと結果の構造
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class IdentifiedItemForDB(BaseModel):
    """DB検索用の食品アイテム（循環インポート回避）"""
    name: str = Field(..., description="食品アイテム名")
    quantity_estimate: Optional[str] = Field(None, description="推定量")
    attributes: Optional[Dict[str, Any]] = Field(None, description="属性情報")
    weight_g: Optional[float] = Field(None, description="推定重量（グラム）")
    state: Optional[str] = Field(None, description="調理状態")


class QueryParameters(BaseModel):
    """データベースクエリパラメータ"""
    items_to_query: List[IdentifiedItemForDB] = Field(..., description="検索対象アイテム")
    query_strategy_id: Optional[str] = Field("default_usda_food_search", description="クエリ戦略ID")
    db_specific_options: Optional[Dict[str, Any]] = Field(None, description="DB固有オプション")
    max_results_per_item: Optional[int] = Field(5, description="アイテムあたり最大結果数")


class RawFoodData(BaseModel):
    """データベースから取得した生の食品データ"""
    food_description: str = Field(..., description="食品説明")
    nutrients: Dict[str, Any] = Field(..., description="栄養素データ（DB固有形式）")
    db_source_id: Optional[str] = Field(None, description="DB固有ID（FDC IDなど）")
    matched_query_term: str = Field(..., description="対応するクエリ用語")
    confidence_score: Optional[float] = Field(None, description="マッチング信頼度")
    
    # USDA固有フィールド
    food_category: Optional[str] = Field(None, description="食品カテゴリ")
    brand_owner: Optional[str] = Field(None, description="ブランド所有者")
    data_type: Optional[str] = Field(None, description="データタイプ")
    publication_date: Optional[str] = Field(None, description="公開日")


class RawDBResult(BaseModel):
    """データベース検索結果"""
    query_params_used: QueryParameters = Field(..., description="使用されたクエリパラメータ")
    retrieved_foods: List[RawFoodData] = Field(..., description="取得された食品データリスト")
    source_db_name: str = Field(..., description="ソースデータベース名")
    query_timestamp: Optional[str] = Field(None, description="クエリ実行時刻")
    total_results_found: Optional[int] = Field(None, description="見つかった結果総数")
    errors: Optional[List[str]] = Field(None, description="エラーメッセージリスト")
    
    class Config:
        json_encoders = {
            # 必要に応じて特別なエンコーダーを追加
        } 