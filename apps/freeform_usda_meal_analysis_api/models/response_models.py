"""
Response models for Freeform USDA Meal Analysis API
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, AliasChoices


class HealthCheckResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    model_config = {"protected_namespaces": ()}

    status: str = Field(..., description="ステータス", example="healthy")
    version: str = Field(..., description="APIバージョン", example="1.0.0")
    model_id: str = Field(..., description="使用中のVLMモデルID")
    prompt_file: str = Field(..., description="使用中のプロンプトファイル")


class NutritionInfo(BaseModel):
    """栄養価情報"""
    model_config = {"protected_namespaces": ()}

    calories: float = Field(..., description="カロリー（kcal）", example=156.0)
    protein: float = Field(..., validation_alias=AliasChoices("protein", "protein_g"), description="タンパク質（g）", example=12.0)
    fat: float = Field(..., validation_alias=AliasChoices("fat", "fat_g"), description="脂質（g）", example=10.5)
    carbs: float = Field(..., validation_alias=AliasChoices("carbs", "carbs_g"), description="炭水化物（g）", example=1.1)
    fiber: Optional[float] = Field(None, validation_alias=AliasChoices("fiber", "fiber_g"), description="食物繊維（g）", example=0.0)
    sugar: Optional[float] = Field(None, validation_alias=AliasChoices("sugar", "sugar_g"), description="糖質（g）", example=0.7)
    sodium: Optional[float] = Field(None, validation_alias=AliasChoices("sodium", "sodium_mg"), description="ナトリウム（mg）", example=142.0)


class IngredientDetail(BaseModel):
    """食材詳細情報"""
    model_config = {"protected_namespaces": ()}

    ingredient_name: str = Field(..., description="食材名", example="Egg, whole, raw")
    weight_g: float = Field(..., description="重量（グラム）", example=100.0)
    nutrition_per_100g: NutritionInfo = Field(..., description="100gあたりの栄養情報")
    calculated_nutrition: NutritionInfo = Field(..., description="計算済み栄養情報")
    source_db: str = Field(..., description="データソース", example="usda_fndds")
    fdc_id: Optional[str] = Field(None, description="USDA FDC ID", example="167782")
    calculation_notes: List[str] = Field(
        default_factory=list,
        description="計算に関する注記",
        example=["Scaled from 100g base data using factor 1.000"]
    )
    debug_info: Optional[Dict[str, Any]] = Field(
        None,
        description="デバッグ情報（USDA検索の詳細）",
        example={
            "retriever_candidates": [],  # FAISS検索の候補
            "reranker_results": [],      # リランク結果
            "retry_count": 0              # リトライ回数
        }
    )


class DishDetail(BaseModel):
    """料理詳細情報"""
    model_config = {"protected_namespaces": ()}

    dish_name: str = Field(..., description="料理名", example="Two Large Eggs")
    confidence: float = Field(..., description="識別信頼度", ge=0.0, le=1.0, example=0.95)
    ingredients: List[IngredientDetail] = Field(..., description="食材詳細リスト")
    total_nutrition: NutritionInfo = Field(..., description="料理の総栄養価")
    calculation_metadata: Dict[str, Any] = Field(
        ...,
        description="計算メタデータ",
        example={
            "ingredient_count": 2,
            "total_weight_g": 200.0,
            "calculation_method": "weight_based_scaling"
        }
    )



class UsageInfo(BaseModel):
    """Token使用量とコスト情報"""
    model_config = {"protected_namespaces": ()}

    prompt_tokens: int = Field(..., description="入力トークン数", example=1250)
    completion_tokens: int = Field(..., description="出力トークン数", example=450)
    total_tokens: int = Field(..., description="合計トークン数", example=1700)
    estimated_cost_usd: float = Field(..., description="推定コスト（USD）", example=0.00125)
    model_pricing: Dict[str, Any] = Field(
        ...,
        description="使用したモデルの価格情報",
        example={
            "input_price_per_million": 0.29,
            "output_price_per_million": 0.99
        }
    )
    raw_vlm_output: Optional[str] = Field(
        None,
        description="VLMの生出力（デバッグ用）",
        example="<think>...</think>\n{\"dishes\": ...}"
    )


class AnalysisResponse(BaseModel):
    """分析レスポンス"""
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "analysis_id": "a1b2c3d4",
                "input_type": "image",
                "total_dishes": 2,
                "total_ingredients": 5,
                "processing_time_seconds": 12.34,
                "dishes": [
                    {
                        "dish_name": "Grilled Chicken Breast",
                        "confidence": 0.95,
                        "ingredients": [
                            {
                                "ingredient_name": "Chicken breast, grilled",
                                "weight_g": 150.0,
                                "nutrition_per_100g": {
                                    "calories": 165.0,
                                    "protein": 31.0,
                                    "fat": 3.6,
                                    "carbs": 0.0,
                                    "fiber": 0.0,
                                    "sugar": 0.0,
                                    "sodium": 74.0
                                },
                                "calculated_nutrition": {
                                    "calories": 247.5,
                                    "protein": 46.5,
                                    "fat": 5.4,
                                    "carbs": 0.0,
                                    "fiber": 0.0,
                                    "sugar": 0.0,
                                    "sodium": 111.0
                                },
                                "source_db": "usda_fndds",
                                "fdc_id": "167782",
                                "calculation_notes": ["Scaled from 100g base data using factor 1.500"],
                                "debug_info": {
                                    "retriever_candidates": ["167782", "167783", "167784"],
                                    "reranker_results": ["167782", "167783"],
                                    "retry_count": 0
                                }
                            }
                        ],
                        "total_nutrition": {
                            "calories": 247.5,
                            "protein": 46.5,
                            "fat": 5.4,
                            "carbs": 0.0,
                            "fiber": 0.0,
                            "sugar": 0.0,
                            "sodium": 111.0
                        },
                        "calculation_metadata": {
                            "ingredient_count": 1,
                            "total_weight_g": 150.0,
                            "calculation_method": "weight_based_scaling"
                        }
                    },
                    {
                        "dish_name": "Caesar Salad",
                        "confidence": 0.90,
                        "ingredients": [
                            {
                                "ingredient_name": "Romaine lettuce, raw",
                                "weight_g": 100.0,
                                "nutrition_per_100g": {
                                    "calories": 17.0,
                                    "protein": 1.2,
                                    "fat": 0.3,
                                    "carbs": 3.3,
                                    "fiber": 2.1,
                                    "sugar": 1.2,
                                    "sodium": 8.0
                                },
                                "calculated_nutrition": {
                                    "calories": 17.0,
                                    "protein": 1.2,
                                    "fat": 0.3,
                                    "carbs": 3.3,
                                    "fiber": 2.1,
                                    "sugar": 1.2,
                                    "sodium": 8.0
                                },
                                "source_db": "usda_fndds",
                                "fdc_id": "169248",
                                "calculation_notes": ["Scaled from 100g base data using factor 1.000"]
                            },
                            {
                                "ingredient_name": "Caesar dressing",
                                "weight_g": 30.0,
                                "nutrition_per_100g": {
                                    "calories": 470.0,
                                    "protein": 2.5,
                                    "fat": 48.0,
                                    "carbs": 7.0,
                                    "fiber": 0.0,
                                    "sugar": 5.0,
                                    "sodium": 900.0
                                },
                                "calculated_nutrition": {
                                    "calories": 141.0,
                                    "protein": 0.75,
                                    "fat": 14.4,
                                    "carbs": 2.1,
                                    "fiber": 0.0,
                                    "sugar": 1.5,
                                    "sodium": 270.0
                                },
                                "source_db": "usda_fndds",
                                "fdc_id": "173306",
                                "calculation_notes": ["Scaled from 100g base data using factor 0.300"]
                            },
                            {
                                "ingredient_name": "Parmesan cheese, grated",
                                "weight_g": 10.0,
                                "nutrition_per_100g": {
                                    "calories": 392.0,
                                    "protein": 35.8,
                                    "fat": 25.8,
                                    "carbs": 3.2,
                                    "fiber": 0.0,
                                    "sugar": 0.9,
                                    "sodium": 1529.0
                                },
                                "calculated_nutrition": {
                                    "calories": 39.2,
                                    "protein": 3.58,
                                    "fat": 2.58,
                                    "carbs": 0.32,
                                    "fiber": 0.0,
                                    "sugar": 0.09,
                                    "sodium": 152.9
                                },
                                "source_db": "usda_fndds",
                                "fdc_id": "171287",
                                "calculation_notes": ["Scaled from 100g base data using factor 0.100"]
                            },
                            {
                                "ingredient_name": "Croutons, plain",
                                "weight_g": 15.0,
                                "nutrition_per_100g": {
                                    "calories": 407.0,
                                    "protein": 11.9,
                                    "fat": 6.6,
                                    "carbs": 73.5,
                                    "fiber": 5.0,
                                    "sugar": 5.8,
                                    "sodium": 698.0
                                },
                                "calculated_nutrition": {
                                    "calories": 61.05,
                                    "protein": 1.785,
                                    "fat": 0.99,
                                    "carbs": 11.025,
                                    "fiber": 0.75,
                                    "sugar": 0.87,
                                    "sodium": 104.7
                                },
                                "source_db": "usda_fndds",
                                "fdc_id": "168042",
                                "calculation_notes": ["Scaled from 100g base data using factor 0.150"]
                            }
                        ],
                        "total_nutrition": {
                            "calories": 258.25,
                            "protein": 7.315,
                            "fat": 18.27,
                            "carbs": 16.745,
                            "fiber": 2.85,
                            "sugar": 3.66,
                            "sodium": 535.6
                        },
                        "calculation_metadata": {
                            "ingredient_count": 4,
                            "total_weight_g": 155.0,
                            "calculation_method": "weight_based_scaling"
                        }
                    }
                ],
                "total_nutrition": {
                    "calories": 505.75,
                    "protein": 53.815,
                    "fat": 23.67,
                    "carbs": 16.745,
                    "fiber": 2.85,
                    "sugar": 3.66,
                    "sodium": 646.6
                },
                "ai_model_used": "Qwen/Qwen2-VL-72B-Instruct",
                "prompt_file_used": "freeform_prompt_usda_format_ver_v7_production_20251027.txt",
                "match_rate_percent": 100.0,
                "usage": {
                    "input_tokens": 2500,
                    "thinking_tokens": 3200,
                    "output_tokens": 450,
                    "total_tokens": 6150,
                    "raw_vlm_output": "<think>\nImage shows grilled chicken breast and a Caesar salad...\n</think>\n\n{\n  \"dishes\": [\n    {\"dish_name\": \"Grilled Chicken Breast\", ...}\n  ]\n}",
                    "estimated_cost_usd": 0.0234
                },
                "transcript": None,
                "warnings": []
            }
        }
    }

    analysis_id: str = Field(..., description="分析ID", example="a1b2c3d4")
    input_type: str = Field(..., description="入力タイプ", example="image")

    # 処理サマリー
    total_dishes: int = Field(..., description="検出された料理数", example=3)
    total_ingredients: int = Field(..., description="総食材数", example=9)
    processing_time_seconds: float = Field(..., description="処理時間（秒）", example=15.65)

    # 料理一覧
    dishes: List[DishDetail] = Field(..., description="検出された料理一覧")

    # 総栄養価
    total_nutrition: NutritionInfo = Field(..., description="総栄養価")

    # メタデータ
    ai_model_used: str = Field(
        ...,
        description="使用AIモデル",
        example="Qwen/Qwen2-VL-72B-Instruct"
    )
    prompt_file_used: str = Field(
        ...,
        description="使用プロンプトファイル",
        example="freeform_prompt_usda_format_ver_v7_experimental_20251027.txt"
    )
    match_rate_percent: float = Field(
        ...,
        description="栄養検索マッチ率（%）",
        ge=0.0,
        le=100.0,
        example=100.0
    )

    # Token使用量とコスト情報
    usage: Optional[UsageInfo] = Field(None, description="Token使用量とコスト情報")

    # 音声入力特有
    transcript: Optional[str] = Field(None, description="音声認識テキスト（音声入力時のみ）")

    # 警告メッセージ
    warnings: List[str] = Field(
        default_factory=list,
        description="警告メッセージ",
        example=[]
    )


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    model_config = {"protected_namespaces": ()}

    error: str = Field(..., description="エラータイプ", example="ValidationError")
    message: str = Field(..., description="エラーメッセージ", example="Invalid input format")
    detail: Optional[Dict[str, Any]] = Field(None, description="詳細情報")
    analysis_id: Optional[str] = Field(None, description="分析ID（利用可能な場合）")


# ============================================================
# Retrieval API Response Models
# ============================================================

class FoodItem(BaseModel):
    """食材検索結果アイテム"""
    model_config = {"protected_namespaces": ()}

    fdc_id: str = Field(..., description="USDA FDC ID", example="167782")
    description: str = Field(..., description="食材名", example="Chicken, broilers or fryers, breast, meat only, grilled")
    main_name: str = Field(..., description="主要名称", example="Chicken, broilers or fryers, breast, meat only")
    descriptors: Optional[str] = Field(None, description="調理方法等の記述子", example="grilled")
    source: str = Field(..., description="データソース", example="survey")
    score: float = Field(..., description="類似度スコア", example=0.95)
    nutrition_per_100g: Optional[NutritionInfo] = Field(None, description="100gあたりの栄養情報")


class RetrievalMetadata(BaseModel):
    """検索メタデータ"""
    model_config = {"protected_namespaces": ()}

    total_results: int = Field(..., description="結果数", example=10)
    search_time_ms: int = Field(..., description="検索時間（ミリ秒）", example=250)
    index_type: str = Field(..., description="インデックスタイプ", example="FAISS")
    algorithm: str = Field(..., description="使用アルゴリズム", example="Stage1+Stage2_Rerank")


class RetrievalStatus(BaseModel):
    """検索ステータス"""
    model_config = {"protected_namespaces": ()}

    success: bool = Field(..., description="成功フラグ", example=True)
    message: str = Field(..., description="ステータスメッセージ", example="Search completed successfully")


class RetrievalResponse(BaseModel):
    """食材検索レスポンス"""
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "query": "grilled chicken breast",
                "mode": "hybrid",
                "results": [
                    {
                        "fdc_id": "167782",
                        "description": "Chicken, broilers or fryers, breast, meat only, grilled",
                        "main_name": "Chicken, broilers or fryers, breast, meat only",
                        "descriptors": "grilled",
                        "source": "survey",
                        "score": 0.95,
                        "nutrition_per_100g": {
                            "calories": 165.0,
                            "protein": 31.0,
                            "fat": 3.6,
                            "carbs": 0.0,
                            "fiber": 0.0,
                            "sugar": 0.0,
                            "sodium": 74.0
                        }
                    },
                    {
                        "fdc_id": "171477",
                        "description": "Chicken, broilers or fryers, breast, meat only, cooked, roasted",
                        "main_name": "Chicken, broilers or fryers, breast, meat only",
                        "descriptors": "cooked, roasted",
                        "source": "foundation",
                        "score": 0.89,
                        "nutrition_per_100g": {
                            "calories": 165.0,
                            "protein": 31.0,
                            "fat": 3.6,
                            "carbs": 0.0,
                            "fiber": 0.0,
                            "sugar": 0.0,
                            "sodium": 74.0
                        }
                    }
                ],
                "metadata": {
                    "total_results": 10,
                    "search_time_ms": 250,
                    "index_type": "FAISS",
                    "algorithm": "Stage1+Stage2_Rerank"
                },
                "status": {
                    "success": True,
                    "message": "Search completed successfully"
                }
            }
        }
    }

    query: str = Field(..., description="検索クエリ", example="grilled chicken breast")
    mode: str = Field(..., description="検索モード", example="hybrid")
    results: List[FoodItem] = Field(..., description="検索結果リスト")
    metadata: RetrievalMetadata = Field(..., description="検索メタデータ")
    status: RetrievalStatus = Field(..., description="検索ステータス")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="デバッグ情報（debug=trueの場合のみ）")


# ============================================================
# Metadata Search Response Models
# ============================================================

class MetadataItem(BaseModel):
    """メタデータアイテム"""
    model_config = {"protected_namespaces": ()}

    fdc_id: int = Field(..., description="USDA FDC ID", example=167782)
    description: str = Field(..., description="食材名", example="Chicken, broilers or fryers, breast, meat only, grilled")
    main_name: str = Field(..., description="主要名称", example="Chicken, broilers or fryers, breast, meat only")
    descriptors: Optional[str] = Field(None, description="調理方法等の記述子", example="grilled")
    source: str = Field(..., description="データソース", example="survey")
    nutrition: NutritionInfo = Field(..., description="栄養情報（100gあたり）")
    portions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="ポーション情報",
        example=[
            {"description": "1 breast, bone and skin removed", "gram_weight": 86.0}
        ]
    )


class MetadataSearchResponse(BaseModel):
    """メタデータ検索レスポンス"""
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "query": "chicken breast",
                "results": [
                    {
                        "fdc_id": 167782,
                        "description": "Chicken, broilers or fryers, breast, meat only, grilled",
                        "main_name": "Chicken, broilers or fryers, breast, meat only",
                        "descriptors": "grilled",
                        "source": "survey",
                        "nutrition": {
                            "calories": 165.0,
                            "protein": 31.0,
                            "fat": 3.6,
                            "carbs": 0.0,
                            "fiber": 0.0,
                            "sugar": 0.0,
                            "sodium": 74.0
                        },
                        "portions": [
                            {
                                "description": "1 breast, bone and skin removed",
                                "gram_weight": 86.0
                            }
                        ]
                    }
                ],
                "total": 50,
                "limit": 20,
                "offset": 0,
                "has_more": True
            }
        }
    }

    query: str = Field(..., description="検索クエリ", example="chicken breast")
    results: List[MetadataItem] = Field(..., description="検索結果リスト")
    total: int = Field(..., description="総件数", example=50)
    limit: int = Field(..., description="取得件数制限", example=20)
    offset: int = Field(..., description="オフセット", example=0)
    has_more: bool = Field(..., description="さらに結果があるか", example=True)
