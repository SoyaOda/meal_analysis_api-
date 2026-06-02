"""
Health check router for Cloud Run deployment
"""

import logging

from fastapi import APIRouter, Response, status as http_status
from ..models.response_models import HealthCheckResponse
from ..config import get_settings
from ..admin.config_manager import get_config_manager
from pydantic import BaseModel

logger = logging.getLogger(__name__)

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
        HealthCheckResponse: APIのステータス情報（ConfigManagerから動的取得）
    """
    settings = get_settings()
    config_manager = get_config_manager()
    config = config_manager.get_config()

    # 配信中の設定とコード既定の乖離（eval=v11b / prod=v7 のような構造的ドリフト）を検出
    drift = config_manager.detect_config_drift()
    if drift["drift"]:
        logger.warning(
            "Config drift detected (served config differs from code defaults): %s",
            drift["fields"],
        )

    return HealthCheckResponse(
        status="healthy",
        version=settings.API_VERSION,  # 静的バージョン情報はsettingsから
        model_id=config.vlm.model_id,  # 動的設定はConfigManagerから
        prompt_file=config.vlm.prompt_file,  # 動的設定はConfigManagerから
        config_drift=drift["drift"],
        config_drift_fields=drift["fields"] or None,
        prompt_text_override_active=config.vlm.prompt_text is not None,
        schema_version=getattr(config, "schema_version", None),
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
            message="Service is ready to accept requests",
        )
    else:
        # Service is not ready yet
        response.status_code = http_status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(
            status="not_ready",
            service="freeform-usda-meal-analysis-api",
            indexes_loaded=False,
            message="Indexes are not loaded yet. Service is initializing.",
        )
