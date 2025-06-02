from typing import List, Optional, Dict, Literal, Union
from pydantic import BaseModel, Field, field_validator

# --- 共通モデル ---

class CalculatedNutrients(BaseModel):
    """計算済み栄養素モデル"""
    calories_kcal: float = Field(0.0, description="計算された総カロリー (kcal)")
    protein_g: float = Field(0.0, description="計算された総タンパク質 (g)")
    carbohydrates_g: float = Field(0.0, description="計算された総炭水化物 (g)")
    fat_g: float = Field(0.0, description="計算された総脂質 (g)")
    fiber_g: Optional[float] = Field(None, description="計算された総食物繊維 (g)")
    sugars_g: Optional[float] = Field(None, description="計算された総糖質 (g)")
    sodium_mg: Optional[float] = Field(None, description="計算された総ナトリウム (mg)")

class USDANutrient(BaseModel):
    """USDA栄養素情報モデル (USDA Serviceが返す)"""
    name: str = Field(..., description="栄養素名")
    amount: float = Field(..., description="100gまたは100mlあたりの量")
    unit_name: str = Field(..., description="単位名 (例: g, mg, kcal)")
    nutrient_id: Optional[int] = Field(None, description="USDA栄養素ID")
    nutrient_number: Optional[str] = Field(None, description="USDA栄養素番号")

class USDASearchResultItem(BaseModel):
    """USDA検索結果アイテムモデル (USDA Serviceが返す)"""
    fdc_id: int = Field(..., description="USDA FoodData Central ID")
    description: str = Field(..., description="食品の公式名称")
    data_type: Optional[str] = Field(None, description="USDAデータタイプ (例: SR Legacy, Branded)")
    publication_date: Optional[str] = Field(None, description="公開日")
    brand_owner: Optional[str] = Field(None, description="ブランド所有者 (Branded Foodsの場合)")
    brand_name: Optional[str] = Field(None, description="ブランド名")
    subbrand_name: Optional[str] = Field(None, description="サブブランド名")
    gtin_upc: Optional[str] = Field(None, description="GTIN/UPCコード")
    ndb_number: Optional[Union[str, int]] = Field(None, description="NDB番号 (文字列または整数)")
    food_code: Optional[str] = Field(None, description="食品コード")
    score: Optional[float] = Field(None, description="検索結果の関連度スコア")
    ingredients: Optional[str] = Field(None, description="原材料リスト文字列 (Branded食品の場合)")
    ingredients_text: Optional[str] = Field(None, description="原材料リスト文字列 (Branded食品の場合, **Assumption: String**)")
    food_nutrients: List[USDANutrient] = Field(default_factory=list, description="主要な栄養素情報のリスト")
    
    # Enhanced search tracking attributes
    search_tier: Optional[int] = Field(None, description="検索階層 (1=specific, 2=broader, 3=generic)")
    search_query_used: Optional[str] = Field(None, description="実際に使用された検索クエリ")
    search_context: Optional[str] = Field(None, description="検索コンテキスト (branded, ingredient, dish)")
    require_all_words_used: Optional[bool] = Field(None, description="requireAllWordsパラメータが使用されたか")
    data_types_searched: Optional[List[str]] = Field(None, description="検索対象となったデータタイプのリスト")
    
    # Legacy fallback search tracking attributes (for backward compatibility)
    fallback_query_used: Optional[str] = Field(None, description="フォールバック検索で使用されたクエリ（該当する場合）")
    fallback_attempt: Optional[int] = Field(None, description="フォールバック検索の試行回数（該当する場合）")

    @field_validator('ndb_number')
    @classmethod
    def validate_ndb_number(cls, v):
        """ndb_numberを文字列に正規化"""
        if v is not None:
            return str(v)
        return v

# --- Phase 1 Gemini 出力モデル ---

class USDACandidateQuery(BaseModel):
    """Phase 1でGeminiが出力するUSDAクエリ候補"""
    query_term: str = Field(..., description="USDA検索に使用する具体的なクエリ文字列 (英語)")
    granularity_level: Literal["dish", "ingredient", "branded_product"] = Field(..., description="このクエリが対象とする粒度レベル")
    preferred_data_types: Optional[List[Literal["Foundation", "SR Legacy", "Branded"]]] = Field(None, description="推奨USDAデータベースタイプ（優先順）")
    original_term: str = Field("", description="このクエリが由来する元の料理名または食材名")
    reason_for_query: str = Field("", description="このクエリ候補を生成した簡単な理由")

class Phase1Ingredient(BaseModel):
    """Phase 1 材料モデル"""
    ingredient_name: str = Field(..., description="材料の名称 (英語)")
    state: Optional[Literal["raw", "cooked", "fried", "baked", "processed", "dry", "unknown"]] = Field("unknown", description="材料の調理・加工状態")

class Phase1Dish(BaseModel):
    """Phase 1 料理モデル"""
    dish_name: str = Field(..., description="特定された料理の名称 (英語)")
    type: str = Field(..., description="料理の種類（例: Main course, Side dish）")
    quantity_on_plate: str = Field(..., description="皿の上の量や個数")
    ingredients: List[Phase1Ingredient] = Field(..., description="含まれる材料のリスト")
    # NEW: Phase 1でクエリ候補を出力
    usda_query_candidates: List[USDACandidateQuery] = Field(..., description="この料理/食材に関連するUSDAクエリ候補リスト")

class Phase1AnalysisResponse(BaseModel):
    """Phase 1 食事分析レスポンスモデル"""
    dishes: List[Phase1Dish] = Field(..., description="画像から特定された料理のリスト")

# --- Phase 2 Gemini 出力モデル (Gemini向けスキーマ) ---

class RefinedIngredientGeminiOutput(BaseModel):
    """Phase 2 Gemini出力用 - 材料モデル"""
    ingredient_name: str = Field(..., description="材料の名称 (英語)。Phase 1から引き継ぎ、必要なら修正。")
    estimated_weight_g: Optional[float] = Field(None, description="画像から推定された材料の重量 (g)。ingredient_level計算の場合に設定。")
    fdc_id: Optional[int] = Field(None, description="選択されたFDC ID。ingredient_levelの場合、またはdish_levelのFallback時に設定。")
    usda_source_description: Optional[str] = Field(None, description="選択されたFDC IDの公式名称。")
    reason_for_choice: Optional[str] = Field(None, description="このFDC IDを選択した理由、または選択しなかった理由。")

class RefinedDishGeminiOutput(BaseModel):
    """Phase 2 Gemini出力用 - 料理モデル"""
    dish_name: str = Field(..., description="料理の名称 (英語)。Phase 1から引き継ぎ、必要なら修正。")
    calculation_strategy: Literal["dish_level", "ingredient_level"] = Field(..., description="写真と検索結果に基づいて決定された最終計算戦略")
    reason_for_strategy: str = Field(..., description="この計算戦略を選択した理由。写真の複雑さと検索結果の質を考慮。")
    estimated_dish_weight_g: Optional[float] = Field(None, description="画像から推定された料理全体の重量 (g)。dish_level計算の場合に設定。")
    fdc_id: Optional[int] = Field(None, description="選択されたFDC ID。dish_levelの場合に設定。")
    usda_source_description: Optional[str] = Field(None, description="選択されたFDC IDの公式名称。")
    reason_for_choice: Optional[str] = Field(None, description="このFDC IDを選択した理由、または選択しなかった理由。")
    ingredients: List[RefinedIngredientGeminiOutput] = Field(..., description="材料リスト")

class Phase2GeminiResponse(BaseModel):
    """Phase 2 Gemini出力用 - 全体モデル"""
    dishes: List[RefinedDishGeminiOutput] = Field(..., description="精緻化された料理リスト。")

# --- Phase 2 API 出力モデル (最終レスポンス) ---

class RefinedIngredientResponse(BaseModel):
    """Phase 2 API出力用 - 材料モデル"""
    ingredient_name: str
    weight_g: float
    fdc_id: Optional[int]
    usda_source_description: Optional[str]
    reason_for_choice: Optional[str] # From Gemini
    key_nutrients_per_100g: Optional[Dict[str, float]] # From USDA Service
    actual_nutrients: Optional[CalculatedNutrients] # From Nutrition Calculation

class RefinedDishResponse(BaseModel):
    """Phase 2 API出力用 - 料理モデル"""
    dish_name: str
    type: str # From Phase 1
    quantity_on_plate: str # From Phase 1
    estimated_total_dish_weight_g: Optional[float] = Field(None, description="Phase1で推定された料理全体の重量（グラム）")
    actual_weight_used_for_calculation_g: Optional[float] = Field(None, description="栄養計算で実際に使用された重量（グラム）")
    weight_calculation_method: Optional[str] = Field(None, description="重量計算方法の説明")
    calculation_strategy: Literal["dish_level", "ingredient_level"] # From Gemini
    reason_for_strategy: Optional[str] # From Gemini
    fdc_id: Optional[int] # From Gemini (dish_level)
    usda_source_description: Optional[str] # From Gemini (dish_level)
    reason_for_choice: Optional[str] # From Gemini (dish_level)
    key_nutrients_per_100g: Optional[Dict[str, float]] # From USDA Service (dish_level)
    ingredients: List[RefinedIngredientResponse]
    dish_total_actual_nutrients: Optional[CalculatedNutrients] # From Nutrition Calculation

class MealAnalysisRefinementResponse(BaseModel):
    """Phase 2 食事分析精緻化レスポンスモデル"""
    dishes: List[RefinedDishResponse]
    total_meal_nutrients: Optional[CalculatedNutrients]
    warnings: Optional[List[str]] = Field(None, description="処理中に発生した警告メッセージ。")
    errors: Optional[List[str]] = Field(None, description="処理中に発生したエラーメッセージ。")

# --- 後方互換性のために既存モデルも保持 ---

class Ingredient(BaseModel):
    """材料情報モデル (既存API用)"""
    ingredient_name: str = Field(..., description="材料の名称")
    weight_g: float = Field(..., description="推定重量（グラム単位）", ge=0.1)

class Dish(BaseModel):
    """料理情報モデル (既存API用)"""
    dish_name: str = Field(..., description="特定された料理の名称")
    type: str = Field(..., description="料理の種類（例: 主菜, 副菜, スープ）")
    quantity_on_plate: str = Field(..., description="皿の上に載っている料理のおおよその量や個数")
    ingredients: List[Ingredient] = Field(..., description="その料理に含まれる材料のリスト")

class MealAnalysisResponse(BaseModel):
    """食事分析レスポンスモデル (既存API用)"""
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

# --- 後方互換性のエイリアス ---
InitialAnalysisIngredient = Ingredient  
InitialAnalysisDish = Dish  
InitialAnalysisData = MealAnalysisResponse  

# --- RefinedIngredient/RefinedDish は RefinedIngredientResponse/RefinedDishResponse へのエイリアス ---
RefinedIngredient = RefinedIngredientResponse
RefinedDish = RefinedDishResponse

# --- Gemini向けJSONスキーマ定義 (手動で修正) ---

# Phase 1 Schema - 手動で定義してGemini API互換にする
PHASE_1_GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "dishes": {
            "type": "array",
            "description": "画像から特定された料理のリスト",
            "items": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "特定された料理の名称 (英語)"},
                    "type": {"type": "string", "description": "料理の種類（例: Main course, Side dish）"},
                    "quantity_on_plate": {"type": "string", "description": "皿の上の量や個数"},
                    "ingredients": {
                        "type": "array",
                        "description": "含まれる材料のリスト",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "材料の名称 (英語)"},
                                "state": {
                                    "type": "string",
                                    "enum": ["raw", "cooked", "fried", "baked", "processed", "dry", "unknown"],
                                    "description": "材料の調理・加工状態"
                                }
                            },
                            "required": ["ingredient_name", "state"]
                        }
                    },
                    "usda_query_candidates": {
                        "type": "array",
                        "description": "この料理/食材に関連するUSDAクエリ候補リスト",
                        "items": {
                            "type": "object",
                            "properties": {
                                "query_term": {"type": "string", "description": "USDA検索に使用する具体的なクエリ文字列 (英語)"},
                                "granularity_level": {
                                    "type": "string",
                                    "enum": ["dish", "ingredient", "branded_product"],
                                    "description": "このクエリが対象とする粒度レベル"
                                },
                                "preferred_data_types": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["Foundation", "SR Legacy", "Branded"]
                                    },
                                    "description": "推奨USDAデータベースタイプ（優先順）"
                                },
                                "original_term": {"type": "string", "description": "このクエリが由来する元の料理名または食材名"},
                                "reason_for_query": {"type": "string", "description": "このクエリ候補を生成した簡単な理由"}
                            },
                            "required": ["query_term", "granularity_level", "original_term", "reason_for_query"]
                        }
                    }
                },
                "required": ["dish_name", "type", "quantity_on_plate", "ingredients", "usda_query_candidates"]
            }
        }
    },
    "required": ["dishes"]
}

# Phase 2 Schema - 手動で定義してGemini API互換にする
PHASE_2_GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "dishes": {
            "type": "array",
            "description": "精緻化された料理リスト",
            "items": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "料理の名称 (英語)。Phase 1から引き継ぎ、必要なら修正。"},
                    "calculation_strategy": {
                        "type": "string",
                        "enum": ["dish_level", "ingredient_level"],
                        "description": "写真と検索結果に基づいて決定された最終計算戦略"
                    },
                    "reason_for_strategy": {"type": "string", "description": "この計算戦略を選択した理由。写真の複雑さと検索結果の質を考慮。"},
                    "estimated_dish_weight_g": {"type": "number", "description": "画像から推定された料理全体の重量 (g)。dish_level計算の場合に設定。"},
                    "fdc_id": {"type": "integer", "description": "dish_levelの場合に選択されたFDC ID"},
                    "usda_source_description": {"type": "string", "description": "dish_levelの場合に選択されたFDC IDの公式名称"},
                    "reason_for_choice": {"type": "string", "description": "dish_levelの場合、このFDC IDを選択した理由"},
                    "ingredients": {
                        "type": "array",
                        "description": "材料リスト。各材料についてFDC IDと選択理由を記述",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "材料の名称 (英語)。Phase 1から引き継ぎ、必要なら修正"},
                                "estimated_weight_g": {"type": "number", "description": "画像から推定された材料の重量 (g)。ingredient_level計算の場合に設定。"},
                                "fdc_id": {"type": "integer", "description": "選択されたFDC ID。ingredient_levelの場合、またはdish_levelのFallback時に設定"},
                                "usda_source_description": {"type": "string", "description": "選択されたFDC IDの公式名称"},
                                "reason_for_choice": {"type": "string", "description": "このFDC IDを選択した理由、または選択しなかった理由"}
                            },
                            "required": ["ingredient_name"]
                        }
                    }
                },
                "required": ["dish_name", "calculation_strategy", "reason_for_strategy", "ingredients"]
            }
        }
    },
    "required": ["dishes"]
}

# 後方互換性のために既存スキーマも保持
MEAL_ANALYSIS_GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "dishes": {
            "type": "array",
            "description": "画像から特定された料理のリスト。",
            "items": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "特定された料理の名称。"},
                    "type": {"type": "string", "description": "料理の種類（例: 主菜, 副菜, スープ, デザート）。"},
                    "quantity_on_plate": {"type": "string", "description": "皿の上に載っている料理のおおよその量や個数（例: '1杯', '2切れ', '約200g'）。"},
                    "ingredients": {
                        "type": "array",
                        "description": "この料理に含まれると推定される材料のリスト。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "材料の名称。"},
                                "weight_g": {"type": "number", "description": "その材料の推定重量（グラム単位）。"}
                            },
                            "required": ["ingredient_name", "weight_g"]
                        }
                    },
                    "usda_query_candidates": {
                        "type": "array",
                        "description": "この料理/食材に関連するUSDAクエリ候補リスト。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "query_term": {"type": "string", "description": "USDA検索に使用する具体的なクエリ文字列 (英語)"},
                                "granularity_level": {
                                    "type": "string", 
                                    "enum": ["dish", "ingredient", "branded_product"],
                                    "description": "このクエリが対象とする粒度レベル"
                                },
                                "original_term": {"type": "string", "description": "このクエリが由来する元の料理名または食材名"},
                                "reason_for_query": {"type": "string", "description": "このクエリ候補を生成した簡単な理由"}
                            },
                            "required": ["query_term", "granularity_level"]
                        }
                    }
                },
                "required": ["dish_name", "type", "quantity_on_plate", "ingredients", "usda_query_candidates"]
            }
        }
    },
    "required": ["dishes"]
}

REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA = PHASE_2_GEMINI_SCHEMA 