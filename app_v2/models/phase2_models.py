from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, field_validator

from .phase1_models import Ingredient
from .usda_models import USDAQueryOutput


class RefinedIngredient(BaseModel):
    """USDA情報で精緻化された食材モデル"""
    ingredient_name: str = Field(..., description="食材の名称（精緻化後）")
    weight_g: float = Field(..., description="食材の推定重量（グラム単位、Phase1由来）", gt=0)
    fdc_id: Optional[int] = Field(None, description="対応するUSDA食品のFDC ID (食材レベルの場合)")
    usda_source_description: Optional[str] = Field(None, description="選択されたUSDA食品の公式名称 (食材レベルの場合)")
    key_nutrients_per_100g: Optional[Dict[str, float]] = Field(
        None,
        description="選択されたUSDA食品の主要栄養素（100gあたり）。キーは'calories_kcal', 'protein_g', 'carbohydrates_g', 'fat_g'。",
    )

    @field_validator('key_nutrients_per_100g')
    def check_ingredient_nutrients_values(cls, v):
        if v is not None:
            for key, value in v.items():
                if value is None:
                    v[key] = 0.0
        return v


class RefinedDish(BaseModel):
    """USDA情報で精緻化された料理モデル"""
    dish_name: str = Field(..., description="特定された料理の名称（精緻化後）")
    type: str = Field(..., description="料理の種類（例: 主菜, 副菜, スープ）")
    quantity_on_plate: str = Field(..., description="皿の上に載っている料理のおおよその量や個数")
    
    calculation_strategy: Optional[Literal["dish_level", "ingredient_level"]] = Field(
        None, 
        description="この料理の栄養計算方針 (Geminiが決定)"
    )
    
    # dish_level計算時に使用されるフィールド
    fdc_id: Optional[int] = Field(None, description="料理全体のFDC ID (dish_level計算時)")
    usda_source_description: Optional[str] = Field(None, description="料理全体のUSDA公式名称 (dish_level計算時)")
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
    usda_matches: USDAQueryOutput = Field(..., description="USDA照合結果")

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