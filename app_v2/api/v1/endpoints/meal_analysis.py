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
    test_results_dir: Optional[str] = Form(None)
):
    """
    完全な食事分析を実行（v2.0 コンポーネント化版）
    
    - Phase 1: Deep Infra Gemma 3による画像分析
    - Nutrition Search: 食材の栄養データベース照合（5階層ファジーマッチング）
    - Nutrition Calculation: 最終栄養価計算
    
    Args:
        image: 分析対象の食事画像
        save_detailed_logs: 分析ログを保存するかどうか (デフォルト: True)
    
    Returns:
        完全な分析結果と栄養価計算、分析ログファイルパス
    """
    
    try:
        # 画像の検証
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="アップロードされたファイルは画像である必要があります")
        
        # 画像データの読み込み
        image_data = await image.read()
        logger.info(f"Starting complete meal analysis pipeline v2.0 (detailed_logs: {save_detailed_logs})")
        
        # パイプラインの実行
        pipeline = MealAnalysisPipeline()
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_data,
            image_mime_type=image.content_type,
            save_detailed_logs=save_detailed_logs,
            test_execution=test_execution,
            test_results_dir=test_results_dir
        )
        
        logger.info(f"Complete analysis pipeline v2.0 finished successfully")
        
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