from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .phase2_models import RefinedDish


class CalculatedNutrients(BaseModel):
    """計算済み栄養素モデル"""
    calories_kcal: float = Field(0.0, description="計算された総カロリー (kcal)")
    protein_g: float = Field(0.0, description="計算された総タンパク質 (g)")
    carbohydrates_g: float = Field(0.0, description="計算された総炭水化物 (g)")
    fat_g: float = Field(0.0, description="計算された総脂質 (g)")
    fiber_g: Optional[float] = Field(None, description="計算された総食物繊維 (g)")
    sodium_mg: Optional[float] = Field(None, description="計算された総ナトリウム (mg)")

    def to_dict(self) -> Dict[str, float]:
        """辞書形式で栄養素データを取得"""
        return {
            "calories_kcal": self.calories_kcal,
            "protein_g": self.protein_g,
            "carbohydrates_g": self.carbohydrates_g,
            "fat_g": self.fat_g,
            "fiber_g": self.fiber_g or 0.0,
            "sodium_mg": self.sodium_mg or 0.0
        }

    def add(self, other: 'CalculatedNutrients') -> 'CalculatedNutrients':
        """他の栄養素と合計する"""
        return CalculatedNutrients(
            calories_kcal=self.calories_kcal + other.calories_kcal,
            protein_g=self.protein_g + other.protein_g,
            carbohydrates_g=self.carbohydrates_g + other.carbohydrates_g,
            fat_g=self.fat_g + other.fat_g,
            fiber_g=(self.fiber_g or 0.0) + (other.fiber_g or 0.0),
            sodium_mg=(self.sodium_mg or 0.0) + (other.sodium_mg or 0.0)
        )


class EnrichedRefinedDish(BaseModel):
    """栄養価が計算された料理モデル"""
    # Phase2の情報を継承
    dish_name: str = Field(..., description="料理名")
    type: str = Field(..., description="料理の種類")
    quantity_on_plate: str = Field(..., description="皿の上の量")
    calculation_strategy: str = Field(..., description="計算戦略")
    
    # 計算された栄養価情報
    dish_total_actual_nutrients: CalculatedNutrients = Field(..., description="この料理の合計栄養素")
    ingredient_nutrients: Optional[List[Dict]] = Field(None, description="各食材の栄養価詳細")
    calculation_details: Optional[Dict] = Field(None, description="計算の詳細情報")


class TotalNutrients(CalculatedNutrients):
    """食事全体の栄養素モデル（CalculatedNutrientsを拡張）"""
    dish_count: int = Field(0, description="料理の数")
    ingredient_count: int = Field(0, description="総食材数")
    calculation_summary: Optional[Dict[str, int]] = Field(None, description="計算サマリー")


class NutritionInput(BaseModel):
    """栄養計算コンポーネントの入力モデル"""
    refined_dishes: List[RefinedDish] = Field(..., description="Phase2で精緻化された料理のリスト")
    calculation_options: Optional[Dict] = Field(None, description="計算オプション")


class NutritionOutput(BaseModel):
    """栄養計算コンポーネントの出力モデル"""
    enriched_dishes: List[EnrichedRefinedDish] = Field(..., description="栄養価が計算された料理のリスト")
    total_meal_nutrients: TotalNutrients = Field(..., description="食事全体の栄養価")
    calculation_summary: Dict[str, Any] = Field(default_factory=dict, description="計算サマリー")
    warnings: Optional[List[str]] = Field(None, description="処理中の警告メッセージ")
    errors: Optional[List[str]] = Field(None, description="処理中のエラーメッセージ")

    def get_total_calories(self) -> float:
        """総カロリーを取得"""
        return self.total_meal_nutrients.calories_kcal

    def get_dishes_by_strategy(self, strategy: str) -> List[EnrichedRefinedDish]:
        """指定された計算戦略の料理を取得"""
        return [dish for dish in self.enriched_dishes if dish.calculation_strategy == strategy] 