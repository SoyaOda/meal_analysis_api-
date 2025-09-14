from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from ....pipeline import MealAnalysisPipeline

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/complete")
async def complete_meal_analysis(
    image: UploadFile = File(...),
    save_detailed_logs: bool = Form(True),
    test_execution: bool = Form(False),
    test_results_dir: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    optional_text: Optional[str] = Form(None)
):
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
        model_id: 使用する画像分析モデルID (オプション)
                 指定可能: "Qwen/Qwen2.5-VL-32B-Instruct", "google/gemma-3-27b-it", 
                          "meta-llama/Llama-3.2-90B-Vision-Instruct"
                 未指定: 設定ファイルのデフォルトモデルを使用
        optional_text: 追加のテキスト情報 (英語想定) - 画像と併せて分析に使用
                      例: "This is homemade low-sodium pasta", "Restaurant meal with extra vegetables"
    
    Returns:
        完全な分析結果と栄養価計算、分析ログファイルパス
    """
    
    try:
        # モデル検証
        from app_v2.config.settings import get_settings
        settings = get_settings()
        
        if model_id and not settings.validate_model_id(model_id):
            available_models = ", ".join(settings.SUPPORTED_VISION_MODELS)
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported model_id: {model_id}. Available models: {available_models}"
            )
        
        # 画像の検証
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="アップロードされたファイルは画像である必要があります")
        
        # 画像データの読み込み
        image_data = await image.read()
        
        # モデル情報をログに出力
        effective_model = model_id or settings.DEEPINFRA_MODEL_ID
        model_config = settings.get_model_config(effective_model)
        
        # ログ出力（optional_text情報を含む）
        log_info = f"Starting complete meal analysis pipeline v2.0 (model: {effective_model}, detailed_logs: {save_detailed_logs}"
        if optional_text:
            log_info += f", optional_text: '{optional_text[:50]}{'...' if len(optional_text) > 50 else ''}'"
        log_info += ")"
        logger.info(log_info)
        
        if model_config:
            logger.info(f"Model characteristics: {model_config}")
        
        # パイプラインの実行（model_id + optional_text付き）
        pipeline = MealAnalysisPipeline(model_id=model_id)
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_data,
            image_mime_type=image.content_type,
            optional_text=optional_text,  # NEW: Optional text parameter
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
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Complete analysis failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "version": "v2.0", "message": "食事分析API v2.0 - コンポーネント化版"}


@router.get("/pipeline-info")
async def get_pipeline_info():
    """パイプライン情報の取得"""
    pipeline = MealAnalysisPipeline()
    return pipeline.get_pipeline_info() 