"""
Nutrition Calculator用のPydanticモデル定義

栄養計算フェーズの入出力構造
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..data_interpreter.interpretation_models import InterpretedFoodItem, NutrientValue


class NutrientSummary(BaseModel):
    """栄養素サマリー"""
    total_amount: float = Field(..., description="合計量")
    unit: str = Field(..., description="単位")
    contributing_foods: List[str] = Field(..., description="寄与食品リスト")
    daily_value_percentage: Optional[float] = Field(None, description="1日摂取目標値に対する割合")


class FinalNutritionReport(BaseModel):
    """最終栄養レポート"""
    total_nutrients: Dict[str, NutrientSummary] = Field(..., description="栄養素合計サマリー")
    detailed_items: List[InterpretedFoodItem] = Field(..., description="詳細アイテム別データ")
    
    # レポートメタデータ
    metadata: Dict[str, Any] = Field(..., description="レポートメタデータ")
    total_calories: Optional[float] = Field(None, description="総カロリー")
    total_weight_g: Optional[float] = Field(None, description="総重量（グラム）")
    
    # 統計情報
    nutrition_completeness_score: Optional[float] = Field(None, description="栄養データ完全性スコア")
    macro_breakdown: Optional[Dict[str, float]] = Field(None, description="マクロ栄養素内訳")
    
    class Config:
        json_encoders = {
            # 必要に応じて特別なエンコーダーを追加
        }
    
    def get_summary_text(self) -> str:
        """サマリーテキストを生成"""
        summary_lines = []
        summary_lines.append("=== 栄養レポート ===")
        
        if self.total_calories:
            summary_lines.append(f"総カロリー: {self.total_calories:.1f} kcal")
        
        # 主要栄養素を表示
        major_nutrients = ["PROTEIN", "TOTAL_FAT", "CARBOHYDRATE_BY_DIFFERENCE"]
        for nutrient in major_nutrients:
            if nutrient in self.total_nutrients:
                summary = self.total_nutrients[nutrient]
                summary_lines.append(f"{nutrient}: {summary.total_amount:.1f} {summary.unit}")
        
        summary_lines.append(f"解析食品数: {len(self.detailed_items)}")
        
        return "\n".join(summary_lines) 