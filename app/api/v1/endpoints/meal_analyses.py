from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from typing import Annotated, Optional
import logging
import time  # 実行時間測定のため

from ....services.gemini_service import GeminiMealAnalyzer
from ..schemas.meal import Phase1AnalysisResponse, MealAnalysisResponse, ErrorResponse
from ....services.logging_service import get_meal_analysis_logger, ProcessingPhase, LogLevel
from ....core.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Geminiサービスインスタンスのキャッシュ
_gemini_analyzer = None


async def get_gemini_analyzer(settings: Annotated[Settings, Depends(get_settings)]) -> GeminiMealAnalyzer:
    """
    Geminiサービスインスタンスを取得（シングルトン）
    """
    global _gemini_analyzer
    if _gemini_analyzer is None:
        _gemini_analyzer = GeminiMealAnalyzer(
            project_id=settings.GEMINI_PROJECT_ID,
            location=settings.GEMINI_LOCATION,
            model_name=settings.GEMINI_MODEL_NAME
        )
    return _gemini_analyzer


@router.post(
    "",
    response_model=Phase1AnalysisResponse,
    summary="Analyze Meal Image (Phase 1 v2.1)",
    description="v2.1: 食事画像を分析し、料理・食材識別とUSDAクエリ候補生成を行います。"
)
async def analyze_meal_v2_1(
    settings: Annotated[Settings, Depends(get_settings)],
    image: Annotated[UploadFile, File(description="Meal image file.")],
    optional_text: Annotated[Optional[str], None] = None
):
    """
    v2.1仕様：食事画像の基本分析
    
    処理フロー:
    1. 画像の基本バリデーション
    2. Gemini AI による食事分析（Phase 1）
    3. USDAクエリ候補の生成
    4. 結果返却
    """
    # ログサービス初期化
    meal_logger = get_meal_analysis_logger()
    session_id = meal_logger.start_session(
        endpoint="/api/v1/meal-analyses",
        image_filename=getattr(image, 'filename', None),
        image_size_bytes=None  # 後で設定
    )
    
    start_time = time.time()
    
    try:
        # 1. Image validation
        meal_logger.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.REQUEST_RECEIVED,
            message="Starting Phase 1 meal analysis"
        )
        
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid image file format.")
        
        try:
            image_bytes = await image.read()
            # Update image size in session
            if session_id in meal_logger.active_sessions:
                meal_logger.active_sessions[session_id].image_size_bytes = len(image_bytes)
            
            # File size check (e.g., 10MB)
            if len(image_bytes) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Image file size too large (max 10MB).")
        except Exception as e:
            logger.error(f"Error reading image file: {e}")
            meal_logger.log_error(
                session_id=session_id,
                phase=ProcessingPhase.REQUEST_RECEIVED,
                error_message="Failed to read image file",
                error_details=str(e)
            )
            raise HTTPException(status_code=400, detail="Failed to read image file.")

        # 2. Geminiサービスインスタンス取得
        gemini_service = await get_gemini_analyzer(settings)

        # 3. Call Gemini service (Phase 1)
        meal_logger.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.PHASE1_START,
            message="Starting Gemini Phase 1 analysis"
        )
        
        phase1_start_time = time.time()
        try:
            result = await gemini_service.analyze_image_phase1(
                image_bytes=image_bytes,
                image_mime_type=image.content_type,
                optional_text=optional_text
            )
            phase1_duration = (time.time() - phase1_start_time) * 1000
            
            # Phase 1結果をログに記録
            dishes_count = len(result.get('dishes', []))
            usda_queries_count = sum(
                len(dish.get('usda_query_candidates', [])) 
                for dish in result.get('dishes', [])
            )
            
            meal_logger.update_phase1_results(
                session_id=session_id,
                duration_ms=phase1_duration,
                dishes_count=dishes_count,
                usda_queries_count=usda_queries_count,
                phase1_output=result
            )
            
        except Exception as e:
            meal_logger.log_error(
                session_id=session_id,
                phase=ProcessingPhase.PHASE1_START,
                error_message="Gemini Phase 1 analysis failed",
                error_details=str(e)
            )
            raise HTTPException(status_code=503, detail=f"Gemini API error: {e}")

        # 4. レスポンス作成とセッション終了
        response = Phase1AnalysisResponse(**result)
        
        meal_logger.end_session(
            session_id=session_id,
            warnings=None,
            errors=None
        )
        
        return response
        
    except Exception as e:
        # 予期しないエラーのログ記録
        meal_logger.log_error(
            session_id=session_id,
            phase=ProcessingPhase.ERROR_OCCURRED,
            error_message="Unexpected error during Phase 1 processing",
            error_details=str(e)
        )
        
        # セッション終了（エラー時）
        meal_logger.end_session(
            session_id=session_id,
            warnings=None,
            errors=[str(e)]
        )
        
        raise


# 後方互換性のため、古いエンドポイントも維持
@router.post(
    "/legacy",
    response_model=MealAnalysisResponse,
    summary="Legacy Meal Analysis (v1.0 compatibility)",
    description="後方互換性のための旧バージョンエンドポイント。新しい機能にはメインエンドポイント `/` を使用してください。"
)
async def analyze_meal_legacy(
    image: Annotated[UploadFile, File(description="Meal image file to analyze.")],
    settings: Annotated[Settings, Depends(get_settings)],
    gemini_service: Annotated[GeminiMealAnalyzer, Depends(get_gemini_analyzer)],
    optional_text: Annotated[Optional[str], Form(description="Optional additional information about the meal.")] = None
):
    """
    後方互換性のための旧フォーマット
    """
    # 同じ検証を実行
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file format.")
    
    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large.")
    
    try:
        # 旧メソッドを使用（存在する場合）
        analysis_result = await gemini_service.analyze_image_and_text(
            image_bytes=image_bytes,
            image_mime_type=image.content_type,
            optional_text=optional_text
        )
        
        response = MealAnalysisResponse(**analysis_result)
        return response
        
    except Exception as e:
        logger.error(f"Legacy analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 