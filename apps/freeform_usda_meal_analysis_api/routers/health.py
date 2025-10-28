"""
Health check router
"""
from fastapi import APIRouter
from ..models.response_models import HealthCheckResponse
from ..config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    ヘルスチェックエンドポイント

    Returns:
        HealthCheckResponse: APIのステータス情報
    """
    settings = get_settings()

    return HealthCheckResponse(
        status="healthy",
        version=settings.API_VERSION,
        model_id=settings.DEFAULT_VLM_MODEL_ID,
        prompt_file=settings.DEFAULT_PROMPT_FILE
    )
