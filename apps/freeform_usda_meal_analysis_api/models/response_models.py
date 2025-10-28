"""
Response models for Freeform USDA Meal Analysis API
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


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
    protein: float = Field(..., description="タンパク質（g）", example=12.0)
    fat: float = Field(..., description="脂質（g）", example=10.5)
    carbs: float = Field(..., description="炭水化物（g）", example=1.1)
    fiber: Optional[float] = Field(None, description="食物繊維（g）", example=0.0)
    sugar: Optional[float] = Field(None, description="糖質（g）", example=0.7)
    sodium: Optional[float] = Field(None, description="ナトリウム（mg）", example=142.0)


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


class AnalysisResponse(BaseModel):
    """分析レスポンス"""
    model_config = {"protected_namespaces": ()}

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
