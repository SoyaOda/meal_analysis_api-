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
    save_results: bool = Form(True),
    save_detailed_logs: bool = Form(True)
):
    """
    完全な食事分析を実行（v2.0 コンポーネント化版）
    
    - Phase 1: Gemini AIによる画像分析
    - USDA Query: 食材のUSDAデータベース照合
    - Phase 2: 計算戦略決定と栄養価精緻化 (TODO)
    - Nutrition Calculation: 最終栄養価計算 (TODO)
    
    Args:
        image: 分析対象の食事画像
        save_results: 結果を保存するかどうか (デフォルト: True)
        save_detailed_logs: 詳細ログを保存するかどうか (デフォルト: True)
    
    Returns:
        完全な分析結果と栄養価計算、詳細ログファイルパス
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
            save_results=save_results,
            save_detailed_logs=save_detailed_logs
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