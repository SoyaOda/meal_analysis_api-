"""
Freeform USDA Meal Analysis API

FastAPI application for analyzing meals using USDA FNDDS database
with customizable VLM models and prompts.
"""
import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import health, analysis

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 設定読み込み
settings = get_settings()

# FastAPIアプリケーション作成
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(health.router)
app.include_router(analysis.router)


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("=" * 60)
    logger.info(f"{settings.API_TITLE} v{settings.API_VERSION}")
    logger.info("=" * 60)
    logger.info(f"Default VLM Model: {settings.DEFAULT_VLM_MODEL_ID}")
    logger.info(f"Default Prompt: {settings.DEFAULT_PROMPT_FILE}")
    logger.info(f"USDA Index Directory: {settings.USDA_INDEX_DIR}")
    logger.info("=" * 60)

    # パイプライン初期化
    try:
        analysis.initialize_pipeline()
    except Exception as e:
        logger.error(f"Failed to initialize pipeline during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    logger.info("Shutting down Freeform USDA Meal Analysis API...")


@app.get("/")
async def root():
    """
    ルートエンドポイント

    Returns:
        dict: API情報
    """
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "endpoints": {
            "health": "/health",
            "analysis": "/api/v1/meal-analyses",
        },
        "default_config": {
            "model": settings.DEFAULT_VLM_MODEL_ID,
            "prompt": settings.DEFAULT_PROMPT_FILE,
            "search": {
                "mode": "full_index_only",
                "stage1_top_k": settings.DEFAULT_STAGE1_TOP_K,
            }
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8006"))
    logger.info(f"Starting server on port {port}...")

    uvicorn.run(
        "apps.freeform_usda_meal_analysis_api.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )
