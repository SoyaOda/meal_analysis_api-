from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field, field_validator


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


# 計算済み栄養素情報を格納する共通モデル
class CalculatedNutrients(BaseModel):
    """計算済み栄養素モデル"""
    calories_kcal: float = Field(0.0, description="計算された総カロリー (kcal)")
    protein_g: float = Field(0.0, description="計算された総タンパク質 (g)")
    carbohydrates_g: float = Field(0.0, description="計算された総炭水化物 (g)")
    fat_g: float = Field(0.0, description="計算された総脂質 (g)")

    class Config:
        json_schema_extra = {
            "example": {
                "calories_kcal": 82.5,
                "protein_g": 15.5,
                "carbohydrates_g": 0.0,
                "fat_g": 1.8
            }
        }


# フェーズ2のレスポンススキーマ
class RefinedIngredient(BaseModel):
    """USDA情報で精緻化された材料モデル"""
    ingredient_name: str = Field(..., description="材料の名称（精緻化後）")
    weight_g: float = Field(..., description="材料の推定重量（グラム単位、フェーズ1由来）", gt=0)  # この重量はフェーズ1から引き継がれる
    fdc_id: Optional[int] = Field(None, description="対応するUSDA食品のFDC ID (食材レベルの場合)")
    usda_source_description: Optional[str] = Field(None, description="選択されたUSDA食品の公式名称 (食材レベルの場合)")
    key_nutrients_per_100g: Optional[Dict[str, float]] = Field(
        None,
        description="選択されたUSDA食品の主要栄養素（100gあたり）。キーは'calories_kcal', 'protein_g', 'carbohydrates_g', 'fat_g'。",
    )
    actual_nutrients: Optional[CalculatedNutrients] = Field(
        None,
        description="この食材の推定重量と100gあたりの栄養素に基づいて計算された実際の栄養素量。"
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
    
    calculation_strategy: Optional[Literal["dish_level", "ingredient_level"]] = Field(  # NEW FIELD
        None, 
        description="この料理の栄養計算方針 (Geminiが決定)"
    )
    
    # dish_level計算時に使用されるフィールド
    fdc_id: Optional[int] = Field(None, description="料理全体のFDC ID (dish_level計算時)")
    usda_source_description: Optional[str] = Field(None, description="料理全体のUSDA公式名称 (dish_level計算時)")
    key_nutrients_per_100g: Optional[Dict[str, float]] = Field(  # この料理全体の100gあたり栄養素 (dish_level計算時)
        None,
        description="料理全体の100gあたり主要栄養素 (dish_level計算時)。キーは'calories_kcal', 'protein_g', 'carbohydrates_g', 'fat_g'。",
    )

    ingredients: List[RefinedIngredient] = Field(default_factory=list, description="この料理に含まれる材料のリスト。calculation_strategyが'dish_level'の場合、これらの材料のactual_nutrientsは計算されないことがある。")
    
    dish_total_actual_nutrients: Optional[CalculatedNutrients] = Field(  # dish_levelの場合は料理全体の計算結果、ingredient_levelの場合は材料の集計結果
        None,
        description="この料理の合計栄養素。calculation_strategyに基づき計算される。"
    )

    @field_validator('key_nutrients_per_100g')
    def check_dish_nutrients_values(cls, v):
        if v is not None:
            for key, value in v.items():
                if value is None:
                    v[key] = 0.0
        return v


class MealAnalysisRefinementResponse(BaseModel):
    """フェーズ2食事分析精緻化レスポンスモデル"""
    dishes: List[RefinedDish] = Field(..., description="USDA情報で精緻化・栄養計算された料理のリスト")
    total_meal_nutrients: Optional[CalculatedNutrients] = Field(
        None,
        description="食事全体の全ての料理の栄養素を集計した合計値。"
    )
    warnings: Optional[List[str]] = Field(None, description="処理中に発生した警告メッセージのリスト。")
    errors: Optional[List[str]] = Field(None, description="処理中に発生したエラーメッセージのリスト。")


# Gemini向けのJSONスキーマ定義 (REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA) の更新
REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "dishes": {
            "type": "array",
            "description": "画像から特定・精緻化された料理/食品アイテムのリスト。",
            "items": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "特定された料理/食品アイテムの名称。"},
                    "type": {"type": "string", "description": "料理の種類（例: 主菜, 副菜, 単品食品）。"},
                    "quantity_on_plate": {"type": "string", "description": "皿の上の量。"},
                    "calculation_strategy": {  # NEW: Geminiに出力させる
                        "type": "string",
                        "enum": ["dish_level", "ingredient_level"],
                        "description": "このアイテムの栄養計算方針。"
                    },
                    "fdc_id": {  # NEW: dish_levelの場合のFDC ID
                        "type": ["integer", "null"],
                        "description": "calculation_strategyが'dish_level'の場合、この料理/食品アイテム全体のFDC ID。それ以外はnull。"
                    },
                    "usda_source_description": {  # NEW: dish_levelの場合の説明
                        "type": ["string", "null"],
                        "description": "calculation_strategyが'dish_level'の場合、この料理/食品アイテム全体のUSDA公式名称。それ以外はnull。"
                    },
                    "ingredients": {
                        "type": "array",
                        "description": "この料理/食品アイテムに含まれると推定される材料のリスト。calculation_strategyが'ingredient_level'の場合、各材料にfdc_idとusda_source_descriptionが必要。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "材料の名称。"},
                                # weight_g はフェーズ1から引き継がれるため、Geminiは出力不要
                                "fdc_id": {
                                    "type": ["integer", "null"],
                                    "description": "calculation_strategyが'ingredient_level'の場合、この材料のFDC ID。それ以外はnullまたは省略可。"
                                },
                                "usda_source_description": {
                                    "type": ["string", "null"],
                                    "description": "calculation_strategyが'ingredient_level'の場合、この材料のUSDA公式名称。それ以外はnullまたは省略可。"
                                }
                            },
                            "required": ["ingredient_name"]  # 状況に応じてfdc_id, usda_source_descriptionも必須
                        }
                    }
                },
                "required": ["dish_name", "type", "quantity_on_plate", "calculation_strategy", "ingredients"]
            }
        }
    },
    "required": ["dishes"]
} 