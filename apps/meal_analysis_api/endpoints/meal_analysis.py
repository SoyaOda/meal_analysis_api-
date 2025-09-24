from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from shared.pipeline import MealAnalysisPipeline
from apps.meal_analysis_api.models.meal_analysis_models import (
    SimplifiedCompleteAnalysisResponse,
    HealthCheckResponse,
    PipelineInfoResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/complete", response_model=SimplifiedCompleteAnalysisResponse)
async def complete_meal_analysis(
    image: UploadFile = File(...),
    save_detailed_logs: bool = Form(True),
    test_execution: bool = Form(False),
    test_results_dir: Optional[str] = Form(None),
    ai_model_id: Optional[str] = Form(None),
    optional_text: Optional[str] = Form(None),
    temperature: Optional[float] = Form(0.0),
    seed: Optional[int] = Form(123456)
) -> SimplifiedCompleteAnalysisResponse:
    """
    完全な食事分析を実行（v2.0 コンポーネント化版）
    
    - Phase 1: Deep Infra画像分析（モデル選択可能）
    - Nutrition Search: 食材の栄養データベース照合（5階層ファジーマッチング）
    - Nutrition Calculation: 最終栄養価計算
    
    Args:
        image: 分析対象の食事画像
        save_detailed_logs: 分析ログを保存するかどうか (デフォルト: True)
        test_execution: テスト実行モード (デフォルト: False)
        test_results_dir: テスト結果保存先ディレクトリ (テスト実行時のみ)
        ai_model_id: 使用する画像分析モデルID (オプション)
                 指定可能: "Qwen/Qwen2.5-VL-32B-Instruct", "google/gemma-3-27b-it", 
                          "meta-llama/Llama-3.2-90B-Vision-Instruct"
                 未指定: 設定ファイルのデフォルトモデルを使用
        optional_text: 追加のテキスト情報 (英語想定) - 画像と併せて分析に使用
                      例: "This is homemade low-sodium pasta", "Restaurant meal with extra vegetables"
        temperature: AI推論のランダム性制御 (0.0-1.0, デフォルト: 0.0 - 決定的)
        seed: 再現性のためのシード値 (デフォルト: 123456)
    
    Returns:
        完全な分析結果と栄養価計算、分析ログファイルパス
    """
    
    try:
        # モデル検証
        from shared.config.settings import get_settings
        settings = get_settings()

        if ai_model_id and not settings.validate_model_id(ai_model_id):
            available_models = ", ".join(settings.SUPPORTED_VISION_MODELS)
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported ai_model_id: {ai_model_id}. Available models: {available_models}"
            )

        # temperatureパラメータの範囲検証
        if temperature is not None and (temperature < 0.0 or temperature > 1.0):
            raise HTTPException(
                status_code=400,
                detail="temperature must be between 0.0 and 1.0"
            )
        
        # 画像の検証
        if image.content_type and not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="アップロードされたファイルは画像である必要があります")
        
        # 画像データの読み込み
        image_data = await image.read()
        
        # モデル情報をログに出力
        effective_model = ai_model_id or settings.DEEPINFRA_MODEL_ID
        model_config = settings.get_model_config(effective_model)
        
        # ログ出力（パラメータ情報を含む）
        log_info = f"Starting complete meal analysis pipeline v2.0 (model: {effective_model}, detailed_logs: {save_detailed_logs}, temperature: {temperature}, seed: {seed}"
        if optional_text:
            log_info += f", optional_text: '{optional_text[:50]}{'...' if len(optional_text) > 50 else ''}'"
        log_info += ")"
        logger.info(log_info)
        
        if model_config:
            logger.info(f"Model characteristics: {model_config}")
        
        # パイプラインの実行（全パラメータ付き）
        pipeline = MealAnalysisPipeline(model_id=ai_model_id)
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_data,
            image_mime_type=image.content_type or 'image/jpeg',  # Default to image/jpeg if None
            optional_text=optional_text,
            temperature=temperature,  # NEW: Temperature parameter
            seed=seed,  # NEW: Seed parameter
            save_detailed_logs=save_detailed_logs,
            test_execution=test_execution,
            test_results_dir=test_results_dir
        )
        
        # 使用されたモデル情報を結果に追加
        result["model_used"] = effective_model
        if model_config:
            result["model_config"] = model_config
        
        # optional_text情報も結果に含める
        if optional_text:
            result["optional_text_used"] = optional_text
        
        logger.info(f"Complete analysis pipeline v2.0 finished successfully with model: {effective_model}")
        
        # Convert complex result to simplified model
        simplified_response = _convert_to_simplified_response(result)
        return simplified_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Complete analysis failed: {str(e)}"
        )


def _convert_to_simplified_response(result: dict) -> SimplifiedCompleteAnalysisResponse:
    """Convert complex API result to simplified response model"""
    from apps.meal_analysis_api.models.meal_analysis_models import SimplifiedCompleteAnalysisResponse, DishSummary, SimplifiedNutritionInfo, IngredientSummary

    # Extract dishes information（実際のレスポンス構造に合わせて修正）
    dishes = []
    phase1_result = result.get("phase1_result", {})
    final_nutrition_result = result.get("final_nutrition_result", {})

    for dish_data in phase1_result.get("dishes", []):
        # Find corresponding nutrition data
        dish_nutrition = None
        for nutrition_dish in final_nutrition_result.get("dishes", []):
            if nutrition_dish.get("dish_name") == dish_data.get("dish_name"):
                dish_nutrition = nutrition_dish
                break

        # Extract ingredients with full details（実際の構造に合わせて）
        ingredients = []
        for ingredient_data in dish_data.get("ingredients", []):
            # Find corresponding nutrition calculation for this ingredient
            nutrition_ingredient = None
            if dish_nutrition:
                for nutr_ing in dish_nutrition.get("ingredients", []):
                    if nutr_ing.get("ingredient_name") == ingredient_data.get("ingredient_name"):
                        nutrition_ingredient = nutr_ing
                        break

            if nutrition_ingredient:
                ingredients.append(IngredientSummary(
                    ingredient_name=nutrition_ingredient.get("ingredient_name", "Unknown"),
                    weight_g=nutrition_ingredient.get("weight_g", 0.0),
                    nutrition_per_100g=nutrition_ingredient.get("nutrition_per_100g", {}),
                    calculated_nutrition=nutrition_ingredient.get("calculated_nutrition", {}),
                    source_db=nutrition_ingredient.get("source_db", "unknown"),
                    calculation_notes=nutrition_ingredient.get("calculation_notes", [])
                ))
            else:
                # Fallback to basic data
                ingredients.append(IngredientSummary(
                    ingredient_name=ingredient_data.get("ingredient_name", "Unknown"),
                    weight_g=ingredient_data.get("weight_g", 0.0),
                    nutrition_per_100g={},
                    calculated_nutrition={"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "fiber": None, "sugar": None, "sodium": None},
                    source_db="unknown",
                    calculation_notes=[]
                ))

        # Build dish summary with full nutrition and metadata
        total_nutrition = {}
        calculation_metadata = {}
        if dish_nutrition:
            total_nutrition = dish_nutrition.get("total_nutrition", {})
            calculation_metadata = dish_nutrition.get("calculation_metadata", {})

        dishes.append(DishSummary(
            dish_name=dish_data.get("dish_name", "Unknown"),
            confidence=dish_data.get("confidence", 0.0),
            ingredients=ingredients,
            total_nutrition=total_nutrition,
            calculation_metadata=calculation_metadata
        ))
    
    # Extract total nutrition
    total_nutrition_data = final_nutrition_result.get("total_nutrition", {})
    total_nutrition = SimplifiedNutritionInfo(
        calories=total_nutrition_data.get("calories", 0.0),
        protein=total_nutrition_data.get("protein", 0.0),
        fat=total_nutrition_data.get("fat", 0.0),
        carbs=total_nutrition_data.get("carbs", 0.0)
    )
    
    # Extract search match rate
    nutrition_search_result = result.get("nutrition_search_result", {})
    match_rate = nutrition_search_result.get("match_rate", 0.0) * 100.0  # Convert to percentage
    
    # Extract processing time
    processing_summary = result.get("processing_summary", {})
    processing_time = processing_summary.get("processing_time_seconds", 0.0)
    
    return SimplifiedCompleteAnalysisResponse(
        analysis_id=result.get("analysis_id", "unknown"),
        input_type="image",  # 画像分析特有のフィールド
        total_dishes=len(dishes),
        total_ingredients=processing_summary.get("total_ingredients", 0),
        processing_time_seconds=processing_time,
        dishes=dishes,
        total_nutrition=total_nutrition,
        ai_model_used=result.get("model_used", "unknown"),
        match_rate_percent=match_rate
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """ヘルスチェック"""
    return HealthCheckResponse(
        status="healthy", 
        version="v2.0", 
        components=["Phase1Component", "AdvancedNutritionSearchComponent", "NutritionCalculationComponent"]
    )


@router.get("/pipeline-info", response_model=PipelineInfoResponse)
async def get_pipeline_info() -> PipelineInfoResponse:
    """パイプライン情報の取得"""
    pipeline = MealAnalysisPipeline()
    info = pipeline.get_pipeline_info()
    return PipelineInfoResponse(**info) 