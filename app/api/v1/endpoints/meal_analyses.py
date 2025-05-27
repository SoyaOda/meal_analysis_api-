from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from typing import Annotated, Optional
import logging

from ....services.gemini_service import GeminiMealAnalyzer
from ..schemas.meal import MealAnalysisResponse, ErrorResponse
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
    response_model=MealAnalysisResponse,
    summary="Analyze meal image",
    description="Upload a meal image to identify dishes, types, quantities, and ingredients using AI analysis."
)
async def analyze_meal(
    image: Annotated[UploadFile, File(description="Meal image file to analyze.")],
    settings: Annotated[Settings, Depends(get_settings)],
    gemini_service: Annotated[GeminiMealAnalyzer, Depends(get_gemini_analyzer)],
    optional_text: Annotated[Optional[str], Form(description="Optional additional information about the meal.")] = None
):
    """
    Analyze uploaded meal image and return structured dish information.
    
    Args:
        image: Uploaded image file
        optional_text: Optional user context (not used in current implementation)
        
    Returns:
        MealAnalysisResponse: Structured analysis including dishes and ingredients
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
        logger.info(f"Starting meal analysis for image: {image.filename}, size: {len(image_bytes)} bytes")
        
        # Geminiサービスを使用して画像を分析
        analysis_result = await gemini_service.analyze_image_and_text(
            image_bytes=image_bytes,
            image_mime_type=image.content_type,
            optional_text=optional_text
        )
        
        logger.info(f"Meal analysis completed successfully for image: {image.filename}")
        
        # Pydanticモデルでバリデーション
        response = MealAnalysisResponse(**analysis_result)
        return response
        
    except RuntimeError as e:
        # Geminiサービスからの具体的なエラー
        logger.error(f"Error during meal analysis: {e}")
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