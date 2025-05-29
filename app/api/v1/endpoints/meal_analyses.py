from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from typing import Annotated, Optional
import logging

from ....services.gemini_service import GeminiMealAnalyzer
from ..schemas.meal import Phase1AnalysisResponse, MealAnalysisResponse, ErrorResponse
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
    "/",
    response_model=Phase1AnalysisResponse,
    summary="Analyze meal image (Phase 1 - v2.1)",
    description="v2.1: 食事画像を分析して料理・食材を特定し、USDAクエリ候補を生成。Phase 2でより精度の高い栄養計算を可能にする。"
)
async def analyze_meal(
    image: Annotated[UploadFile, File(description="Meal image file to analyze.")],
    settings: Annotated[Settings, Depends(get_settings)],
    gemini_service: Annotated[GeminiMealAnalyzer, Depends(get_gemini_analyzer)],
    optional_text: Annotated[Optional[str], Form(description="Optional additional information about the meal.")] = None
):
    """
    v2.1仕様：食事画像分析エンドポイント（Phase 1）
    
    処理内容:
    1. 画像から料理・食材を特定
    2. 各料理に対してUSDAクエリ候補を複数粒度で生成
    3. 重量推定と理由を含む構造化されたデータを返す
    
    Args:
        image: アップロードされた画像ファイル
        optional_text: オプションの補助情報
        
    Returns:
        Phase1AnalysisResponse: USDAクエリ候補を含む構造化された分析結果
    """
    # Validate image file
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_IMAGE_FORMAT",
                    "message": "Invalid image file format. Please upload an image (e.g., JPEG, PNG)."
                }
            }
        )
    
    # サポートされている画像形式の確認
    supported_formats = ["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"]
    if image.content_type not in supported_formats:
        logger.warning(f"Unsupported image format: {image.content_type}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "UNSUPPORTED_IMAGE_FORMAT",
                    "message": f"サポートされていない画像形式です。サポート形式: {', '.join(supported_formats)}"
                }
            }
        )
    
    # 画像サイズの制限（例: 10MB）
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    image_bytes = await image.read()
    
    if len(image_bytes) > MAX_FILE_SIZE:
        logger.warning(f"Image file too large: {len(image_bytes)} bytes")
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"画像ファイルサイズが大きすぎます。最大サイズ: {MAX_FILE_SIZE // (1024 * 1024)}MB"
                }
            }
        )
    
    if len(image_bytes) == 0:
        logger.warning("Empty image file uploaded")
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "EMPTY_FILE",
                    "message": "空の画像ファイルです。"
                }
            }
        )
    
    try:
        logger.info(f"Starting Phase 1 meal analysis for image: {image.filename}, size: {len(image_bytes)} bytes")
        
        # 新しいPhase 1メソッドを使用
        analysis_result = await gemini_service.analyze_image_phase1(
            image_bytes=image_bytes,
            image_mime_type=image.content_type,
            optional_text=optional_text
        )
        
        logger.info(f"Phase 1 meal analysis completed successfully for image: {image.filename}")
        
        # Pydanticモデルでバリデーション
        response = Phase1AnalysisResponse(**analysis_result)
        return response
        
    except RuntimeError as e:
        # Geminiサービスからの具体的なエラー
        logger.error(f"Error during Phase 1 meal analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "ANALYSIS_ERROR",
                    "message": f"Failed to analyze meal image: {str(e)}"
                }
            }
        )
    except Exception as e:
        # その他の予期せぬエラー
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "予期せぬエラーが発生しました。"
                }
            }
        )


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