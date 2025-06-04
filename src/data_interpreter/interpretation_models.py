"""
Data Interpreter用のPydanticモデル定義

データ解釈フェーズの入出力構造
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class NutrientValue(BaseModel):
    """栄養素値"""
    amount: float = Field(..., description="栄養素の量")
    unit: str = Field(..., description="単位（例: g, mg, kcal）")
    
    def __str__(self) -> str:
        return f"{self.amount} {self.unit}"


class InterpretedFoodItem(BaseModel):
    """解釈済み食品アイテム"""
    matched_query_term: str = Field(..., description="元のクエリ用語")
    selected_food_description: str = Field(..., description="選択された食品説明")
    db_source_id: Optional[str] = Field(None, description="DB固有ID")
    processed_nutrients: Dict[str, NutrientValue] = Field(..., description="標準化された栄養素")
    
    # 追加メタデータ
    confidence_score: Optional[float] = Field(None, description="選択信頼度")
    food_category: Optional[str] = Field(None, description="食品カテゴリ")
    serving_size_g: Optional[float] = Field(None, description="サービングサイズ（グラム）")
    data_source: Optional[str] = Field(None, description="データソース")


class StructuredNutrientInfo(BaseModel):
    """構造化された栄養情報"""
    interpreted_foods: List[InterpretedFoodItem] = Field(..., description="解釈済み食品リスト")
    interpretation_strategy_used: str = Field(..., description="使用された解釈戦略")
    parsing_errors: Optional[List[str]] = Field(None, description="解釈エラー")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="処理メタデータ")
    
    def get_total_items(self) -> int:
        """解釈済みアイテム数を取得"""
        return len(self.interpreted_foods)
    
    def has_errors(self) -> bool:
        """エラーがあるかチェック"""
        return bool(self.parsing_errors) 