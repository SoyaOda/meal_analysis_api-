from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, field_validator

from .phase1_models import Ingredient
from .nutrition_search_models import NutritionQueryOutput


class RefinedIngredient(BaseModel):
    """栄養データベース情報で精緻化された食材モデル"""
    ingredient_name: str = Field(..., description="食材の名称（精緻化後）")
    weight_g: float = Field(..., description="食材の推定重量（グラム単位、Phase1由来）", gt=0)
    nutrition_id: Optional[str] = Field(None, description="対応する栄養データベース食品ID (食材レベルの場合)")
    nutrition_source_description: Optional[str] = Field(None, description="選択された栄養データベース食品の名称 (食材レベルの場合)")
    key_nutrients_per_100g: Optional[Dict[str, float]] = Field(
        None,
        description="選択された食品の主要栄養素（100gあたり）。キーは'calories_kcal', 'protein_g', 'carbohydrates_g', 'fat_g'。",
    )

    @field_validator('key_nutrients_per_100g')
    def check_ingredient_nutrients_values(cls, v):
        if v is not None:
            for key, value in v.items():
                if value is None:
                    v[key] = 0.0
        return v


class RefinedDish(BaseModel):
    """栄養データベース情報で精緻化された料理モデル"""
    dish_name: str = Field(..., description="特定された料理の名称（精緻化後）")
    type: str = Field(..., description="料理の種類（例: 主菜, 副菜, スープ）")
    quantity_on_plate: str = Field(..., description="皿の上に載っている料理のおおよその量や個数")
    
    calculation_strategy: Optional[Literal["dish_level", "ingredient_level"]] = Field(
        None, 
        description="この料理の栄養計算方針 (Geminiが決定)"
    )
    
    # dish_level計算時に使用されるフィールド
    nutrition_id: Optional[str] = Field(None, description="料理全体の栄養データベースID (dish_level計算時)")
    nutrition_source_description: Optional[str] = Field(None, description="料理全体の栄養データベース名称 (dish_level計算時)")
    key_nutrients_per_100g: Optional[Dict[str, float]] = Field(
        None,
        description="料理全体の100gあたり主要栄養素 (dish_level計算時)。キーは'calories_kcal', 'protein_g', 'carbohydrates_g', 'fat_g'。",
    )

    ingredients: List[RefinedIngredient] = Field(default_factory=list, description="この料理に含まれる食材のリスト")

    @field_validator('key_nutrients_per_100g')
    def check_dish_nutrients_values(cls, v):
        if v is not None:
            for key, value in v.items():
                if value is None:
                    v[key] = 0.0
        return v


class Phase2Input(BaseModel):
    """Phase2コンポーネントの入力モデル"""
    image_bytes: bytes = Field(..., description="画像データ（バイト形式）")
    image_mime_type: str = Field(..., description="画像のMIMEタイプ")
    phase1_result: 'Phase1Output' = Field(..., description="Phase1の出力結果")
    nutrition_matches: NutritionQueryOutput = Field(..., description="栄養データベース照合結果")

    class Config:
        arbitrary_types_allowed = True


class Phase2Output(BaseModel):
    """Phase2コンポーネントの出力モデル"""
    refined_dishes: List[RefinedDish] = Field(..., description="精緻化された料理のリスト")
    strategy_summary: Dict[str, int] = Field(default_factory=dict, description="計算戦略のサマリー")
    warnings: Optional[List[str]] = Field(None, description="処理中の警告メッセージ")
    errors: Optional[List[str]] = Field(None, description="処理中のエラーメッセージ")

    def get_dishes_by_strategy(self, strategy: str) -> List[RefinedDish]:
        """指定された戦略の料理リストを取得"""
        return [dish for dish in self.refined_dishes if dish.calculation_strategy == strategy]

# 循環インポートを避けるため、ここで型を更新
from .phase1_models import Phase1Output
Phase2Input.model_rebuild() 