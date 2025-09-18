"""
Simplified Pydantic models for Meal Analysis API responses
Based on actual API response structure analysis
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# SIMPLIFIED MODELS FOR ACTUAL API STRUCTURE
# ============================================================================

class SimplifiedNutritionInfo(BaseModel):
    """簡略化された栄養価情報（実際に使用される項目のみ）"""
    calories: float = Field(..., description="カロリー（kcal）", example=766.48)
    protein: float = Field(..., description="タンパク質（g）", example=26.25)
    fat: float = Field(default=0.0, description="脂質（g）", example=30.45)
    carbs: float = Field(default=0.0, description="炭水化物（g）", example=45.2)


class IngredientSummary(BaseModel):
    """食材概要情報"""
    name: str = Field(..., description="食材名", example="lettuce romaine raw")
    weight_g: float = Field(..., description="重量（グラム）", example=150.0)
    calories: float = Field(..., description="カロリー（kcal）", example=25.5)


class DishSummary(BaseModel):
    """料理概要情報"""
    dish_name: str = Field(..., description="料理名", example="Caesar Salad")
    confidence: float = Field(..., description="識別信頼度", example=0.95)
    ingredient_count: int = Field(..., description="食材数", example=4)
    ingredients: List[IngredientSummary] = Field(..., description="食材詳細リスト")
    total_calories: float = Field(..., description="料理の総カロリー（kcal）", example=310.07)


class SimplifiedCompleteAnalysisResponse(BaseModel):
    """簡略化された完全分析レスポンス"""
    analysis_id: str = Field(..., description="分析ID", example="cc6aac84")

    # 処理サマリー（重要情報のみ）
    total_dishes: int = Field(..., description="検出された料理数", example=3)
    total_ingredients: int = Field(..., description="総食材数", example=9)
    processing_time_seconds: float = Field(..., description="処理時間（秒）", example=15.65)

    # 料理一覧（簡略化）
    dishes: List[DishSummary] = Field(..., description="検出された料理一覧")

    # 総栄養価（実際に使用される部分のみ）
    total_nutrition: SimplifiedNutritionInfo = Field(..., description="総栄養価")

    # デバッグ・メタデータ（重要な部分のみ）
    model_used: str = Field(..., description="使用AIモデル", example="google/gemma-3-27b-it")
    match_rate_percent: float = Field(..., description="栄養検索マッチ率（%）", example=100.0)
    search_method: str = Field(..., description="検索方法", example="elasticsearch")


# ============================================================================
# EXISTING MODELS FOR OTHER ENDPOINTS (SIMPLIFIED)
# ============================================================================


class HealthCheckResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str = Field(..., description="ステータス", example="healthy")
    version: str = Field(..., description="バージョン", example="v2.0")
    components: List[str] = Field(..., description="利用可能なコンポーネント",
                                example=["Phase1Component", "AdvancedNutritionSearchComponent", "NutritionCalculationComponent"])


class ComponentInfo(BaseModel):
    """コンポーネント情報"""
    component_name: str = Field(..., description="コンポーネント名", example="Phase1Component")
    component_type: str = Field(..., description="コンポーネントタイプ", example="analysis")
    execution_count: int = Field(..., description="実行回数", example=0)


class PipelineInfoResponse(BaseModel):
    """パイプライン情報レスポンス"""
    pipeline_id: str = Field(..., description="パイプラインID", example="59284cf2")
    version: str = Field(..., description="バージョン", example="v2.0")
    nutrition_search_method: str = Field(..., description="栄養検索方法", example="elasticsearch")
    components: List[ComponentInfo] = Field(..., description="コンポーネント詳細情報")


class RootResponse(BaseModel):
    """ルートエンドポイントレスポンス"""
    message: str = Field(..., description="メッセージ", example="食事分析 API v2.0 - コンポーネント化版")
    version: str = Field(..., description="バージョン", example="2.0.0")
    architecture: str = Field(..., description="アーキテクチャ", example="Component-based Pipeline")
    docs: str = Field(..., description="ドキュメントURL", example="/docs")