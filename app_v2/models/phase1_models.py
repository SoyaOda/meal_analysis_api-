from typing import List, Optional
from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    """食材情報モデル"""
    ingredient_name: str = Field(..., description="食材の名称")
    weight_g: float = Field(..., description="推定重量（グラム単位）", gt=0)


class Dish(BaseModel):
    """料理情報モデル"""
    dish_name: str = Field(..., description="特定された料理の名称")
    type: str = Field(..., description="料理の種類（例: 主菜, 副菜, スープ）")
    quantity_on_plate: str = Field(..., description="皿の上に載っている料理のおおよその量や個数")
    ingredients: List[Ingredient] = Field(..., description="その料理に含まれる食材のリスト")


class Phase1Input(BaseModel):
    """Phase1コンポーネントの入力モデル"""
    image_bytes: bytes = Field(..., description="画像データ（バイト形式）")
    image_mime_type: str = Field(..., description="画像のMIMEタイプ")
    optional_text: Optional[str] = Field(None, description="オプションのテキスト情報")

    class Config:
        arbitrary_types_allowed = True


class Phase1Output(BaseModel):
    """Phase1コンポーネントの出力モデル"""
    dishes: List[Dish] = Field(..., description="画像から特定された料理のリスト")
    analysis_confidence: Optional[float] = Field(None, description="分析の信頼度 (0-1)")
    warnings: Optional[List[str]] = Field(None, description="処理中の警告メッセージ")

    def get_all_ingredient_names(self) -> List[str]:
        """全ての食材名のリストを取得"""
        ingredient_names = []
        for dish in self.dishes:
            for ingredient in dish.ingredients:
                ingredient_names.append(ingredient.ingredient_name)
        return ingredient_names

    def get_all_dish_names(self) -> List[str]:
        """全ての料理名のリストを取得"""
        return [dish.dish_name for dish in self.dishes] 