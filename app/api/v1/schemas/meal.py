from typing import List, Optional, Dict
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


# ========== フェーズ2用モデル ==========

# フェーズ1の出力を表すモデル（initial_analysis_data用）
InitialAnalysisIngredient = Ingredient  # フェーズ1と同じ構造
InitialAnalysisDish = Dish  # フェーズ1と同じ構造
InitialAnalysisData = MealAnalysisResponse  # フェーズ1と同じ構造


# USDA検索結果を表すモデル
class USDANutrient(BaseModel):
    """USDA栄養素情報モデル"""
    name: str = Field(..., description="栄養素名")
    amount: float = Field(..., description="100gまたは100mlあたりの量")
    unit_name: str = Field(..., description="単位名 (例: g, mg, kcal)")
    nutrient_id: Optional[int] = Field(None, description="USDA栄養素ID")
    nutrient_number: Optional[str] = Field(None, description="USDA栄養素番号")


class USDASearchResultItem(BaseModel):
    """USDA検索結果アイテムモデル"""
    fdc_id: int = Field(..., description="USDA FoodData Central ID")
    description: str = Field(..., description="食品の公式名称")
    data_type: Optional[str] = Field(None, description="USDAデータタイプ (例: SR Legacy, Branded)")
    brand_owner: Optional[str] = Field(None, description="ブランド所有者 (Branded Foodsの場合)")
    ingredients_text: Optional[str] = Field(None, description="原材料リスト文字列 (Branded Foodsの場合)")
    food_nutrients: List[USDANutrient] = Field(default_factory=list, description="主要な栄養素情報のリスト")
    score: Optional[float] = Field(None, description="検索結果の関連度スコア")


# フェーズ2のレスポンススキーマ
class RefinedIngredient(BaseModel):
    """USDA情報で精緻化された材料モデル"""
    ingredient_name: str = Field(..., description="材料の名称（精緻化後）")
    weight_g: float = Field(..., description="材料の推定重量（グラム単位）", gt=0)
    fdc_id: Optional[int] = Field(None, description="対応するUSDA食品のFDC ID")
    usda_source_description: Optional[str] = Field(None, description="選択されたUSDA食品の公式名称")
    key_nutrients_per_100g: Optional[Dict[str, float]] = Field(
        None, 
        description="選択されたUSDA食品の主要栄養素（100gあたり）",
        json_schema_extra={
            "example": {
                "calories_kcal": 165,
                "protein_g": 31.0,
                "fat_g": 3.6,
                "carbohydrate_g": 0.0
            }
        }
    )


class RefinedDish(BaseModel):
    """USDA情報で精緻化された料理モデル"""
    dish_name: str = Field(..., description="特定された料理の名称（精緻化後）")
    type: str = Field(..., description="料理の種類（例: 主菜, 副菜, スープ）")
    quantity_on_plate: str = Field(..., description="皿の上に載っている料理のおおよその量や個数")
    ingredients: List[RefinedIngredient] = Field(..., description="精緻化された材料のリスト")


class MealAnalysisRefinementResponse(BaseModel):
    """フェーズ2食事分析精緻化レスポンスモデル"""
    dishes: List[RefinedDish] = Field(..., description="USDA情報で精緻化された料理のリスト")


# Gemini向けのJSONスキーマ定義
REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "dishes": {
            "type": "array",
            "description": "画像から特定・精緻化された料理のリスト。",
            "items": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "特定された料理の名称。"},
                    "type": {"type": "string", "description": "料理の種類（例: 主菜, 副菜）。"},
                    "quantity_on_plate": {"type": "string", "description": "皿の上の量。"},
                    "ingredients": {
                        "type": "array",
                        "description": "この料理に含まれると推定される材料のリスト（USDA情報で精緻化）。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "材料の名称（USDA情報に基づき精緻化される可能性あり）。"},
                                "weight_g": {"type": "number", "description": "その材料の推定重量（グラム単位）。"},
                                "fdc_id": {"type": ["integer", "null"], "description": "選択されたUSDA食品のFDC ID。該当なしの場合はnull。"},
                                "usda_source_description": {"type": ["string", "null"], "description": "選択されたUSDA食品の公式名称。"}
                            },
                            "required": ["ingredient_name", "weight_g"]
                        }
                    }
                },
                "required": ["dish_name", "type", "quantity_on_plate", "ingredients"]
            }
        }
    },
    "required": ["dishes"]
} 