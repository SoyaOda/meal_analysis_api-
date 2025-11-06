"""
Health check router for Cloud Run deployment
"""
import os
from fastapi import APIRouter, Response, status as http_status
from ..models.response_models import HealthCheckResponse
from ..config import get_settings
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class ReadinessResponse(BaseModel):
    """Readiness check response model"""
    status: str
    service: str
    indexes_loaded: bool
    message: str


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    ヘルスチェックエンドポイント（Liveness Check）
    Cloud Runのliveness probeで使用

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


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check(response: Response):
    """
    Readiness check for Cloud Run
    インデックスがロードされているか確認してサービスの準備状態を返す

    Returns:
        ReadinessResponse: サービスの準備状態
    """
    from ..core.startup_optimizer import startup_optimizer

    # Check if indexes are loaded
    indexes_loaded = startup_optimizer.is_loaded

    if indexes_loaded:
        return ReadinessResponse(
            status="ready",
            service="freeform-usda-meal-analysis-api",
            indexes_loaded=True,
            message="Service is ready to accept requests"
        )
    else:
        # Service is not ready yet
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="not_ready",
            service="freeform-usda-meal-analysis-api",
            indexes_loaded=False,
            message="Indexes are not loaded yet. Service is initializing."
        )
