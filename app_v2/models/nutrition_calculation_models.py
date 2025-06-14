#!/usr/bin/env python3
"""
Nutrition Calculation Models

栄養計算フェーズで使用するモデル定義
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class NutritionInfo(BaseModel):
    """栄養情報モデル（実際の重量ベース）"""
    calories: float = Field(..., description="カロリー (kcal)")
    protein: float = Field(..., description="タンパク質 (g)")
    fat: float = Field(..., description="脂質 (g)")
    carbs: float = Field(..., description="炭水化物 (g)")
    fiber: Optional[float] = Field(None, description="食物繊維 (g)")
    sugar: Optional[float] = Field(None, description="糖質 (g)")
    sodium: Optional[float] = Field(None, description="ナトリウム (mg)")
    
    def __add__(self, other: 'NutritionInfo') -> 'NutritionInfo':
        """栄養情報の加算"""
        return NutritionInfo(
            calories=self.calories + other.calories,
            protein=self.protein + other.protein,
            fat=self.fat + other.fat,
            carbs=self.carbs + other.carbs,
            fiber=(self.fiber or 0) + (other.fiber or 0) if self.fiber is not None or other.fiber is not None else None,
            sugar=(self.sugar or 0) + (other.sugar or 0) if self.sugar is not None or other.sugar is not None else None,
            sodium=(self.sodium or 0) + (other.sodium or 0) if self.sodium is not None or other.sodium is not None else None
        )


class IngredientNutrition(BaseModel):
    """食材レベルの栄養計算結果"""
    ingredient_name: str = Field(..., description="食材名")
    weight_g: float = Field(..., description="重量 (g)")
    nutrition_per_100g: Dict[str, float] = Field(..., description="100gあたりの栄養情報（データベースから）")
    calculated_nutrition: NutritionInfo = Field(..., description="実際の重量に基づく栄養情報")
    source_db: str = Field(..., description="栄養データのソースデータベース")
    calculation_notes: List[str] = Field(default_factory=list, description="計算に関する注記")


class DishNutrition(BaseModel):
    """料理レベルの栄養計算結果"""
    dish_name: str = Field(..., description="料理名")
    confidence: float = Field(..., description="料理特定の信頼度")
    ingredients: List[IngredientNutrition] = Field(..., description="含まれる食材の栄養情報")
    total_nutrition: NutritionInfo = Field(..., description="料理全体の栄養情報")
    calculation_metadata: Dict[str, Any] = Field(default_factory=dict, description="計算メタデータ")


class MealNutrition(BaseModel):
    """食事全体の栄養計算結果"""
    dishes: List[DishNutrition] = Field(..., description="料理別の栄養情報")
    total_nutrition: NutritionInfo = Field(..., description="食事全体の栄養情報")
    calculation_summary: Dict[str, Any] = Field(default_factory=dict, description="計算サマリー")
    warnings: List[str] = Field(default_factory=list, description="計算時の警告")


class NutritionCalculationInput(BaseModel):
    """栄養計算コンポーネントの入力"""
    phase1_result: Any = Field(..., description="Phase1の結果（Phase1Output）")
    nutrition_search_result: Any = Field(..., description="栄養検索の結果（NutritionQueryOutput）")


class NutritionCalculationOutput(BaseModel):
    """栄養計算コンポーネントの出力"""
    meal_nutrition: MealNutrition = Field(..., description="食事全体の栄養計算結果")
    calculation_metadata: Dict[str, Any] = Field(default_factory=dict, description="計算プロセスのメタデータ")
    processing_time_ms: int = Field(..., description="処理時間（ミリ秒）") 