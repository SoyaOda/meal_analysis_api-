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
    summary="食事画像の分析",
    description="送信された食事画像（およびオプションのテキスト）を分析し、料理と材料の構造化JSONを返します。",
    responses={
        400: {
            "description": "不正なリクエスト",
            "model": ErrorResponse
        },
        500: {
            "description": "内部サーバーエラー",
            "model": ErrorResponse
        }
    }
)
async def create_meal_analysis(
    image: Annotated[UploadFile, File(description="食事の画像ファイル。")],
    text: Annotated[Optional[str], Form(description="食事に関するオプションのテキスト記述。")] = None,
    analyzer: Annotated[GeminiMealAnalyzer, Depends(get_gemini_analyzer)] = None
):
    """
    食事画像を分析して、料理と材料の情報を返すエンドポイント
    
    - **image**: 分析対象の食事画像（JPEG, PNG, WEBP等）
    - **text**: 画像に関する補足情報（オプション）
    
    Returns:
        料理と材料の詳細情報を含むJSON
    """
    # 画像ファイルの検証
    if not image.content_type or not image.content_type.startswith("image/"):
        logger.warning(f"Invalid image file type: {image.content_type}")
        raise HTTPException(
            status_code=400, 
            detail={
                "error": {
                    "code": "INVALID_IMAGE_FORMAT",
                    "message": "無効な画像ファイル形式です。画像（例: JPEG, PNG）をアップロードしてください。"
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
        analysis_result = await analyzer.analyze_image_and_text(
            image_bytes=image_bytes,
            image_mime_type=image.content_type,
            optional_text=text
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
                    "message": f"食事分析処理中にエラーが発生しました: {str(e)}"
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