from typing import List, Optional
from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    """材料情報モデル"""
    ingredient_name: str = Field(..., description="材料の名称")
    weight_g: float = Field(..., description="推定重量（グラム単位）", gt=0)


class Dish(BaseModel):
    """料理情報モデル"""
    dish_name: str = Field(..., description="特定された料理の名称")
    type: str = Field(..., description="料理の種類（例: 主菜, 副菜, スープ）")
    quantity_on_plate: str = Field(..., description="皿の上に載っている料理のおおよその量や個数")
    ingredients: List[Ingredient] = Field(..., description="その料理に含まれる材料のリスト")


class MealAnalysisResponse(BaseModel):
    """食事分析レスポンスモデル"""
    dishes: List[Dish] = Field(..., description="画像から特定された料理のリスト")


class ErrorResponse(BaseModel):
    """エラーレスポンスモデル"""
    error: dict = Field(..., description="エラー情報")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "INVALID_INPUT", 
                    "message": "提供された画像ファイル形式はサポートされていません。"
                }
            }
        } 