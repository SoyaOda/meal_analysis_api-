"""
Freeform USDA Meal Analysis API

FastAPI application for analyzing meals using USDA FNDDS database
with customizable VLM models and prompts.
"""
import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import health, analysis, retrieval, metadata, voice, streaming
from .admin import admin_router
from .models.response_models import RootResponse
from .services.analytics import init_analytics, get_analytics

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 設定読み込み
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # Startup
    logger.info("=" * 60)
    logger.info(f"{settings.API_TITLE} v{settings.API_VERSION}")
    logger.info("=" * 60)

    # FAISSデータはDockerイメージに含まれている（ローカル環境と同じ）
    logger.info(f"Default VLM Model: {settings.DEFAULT_VLM_MODEL_ID}")
    logger.info(f"Default Prompt: {settings.DEFAULT_PROMPT_FILE}")
    logger.info(f"USDA Index Directory: {settings.USDA_INDEX_DIR}")
    logger.info("=" * 60)
    
    # Cloud Run最適化: バックグラウンドでインデックスをロード
    import asyncio
    from .core import startup_optimizer
    
    logger.info("🚀 Starting with Lazy Loading - indexes will be loaded on first request")
    
    # バックグラウンドでインデックスをプリロード開始（オプション）
    # 起動時間を最優先する場合はコメントアウト
    if settings.PRELOAD_INDEXES_ON_STARTUP:
        logger.info("📦 Starting background index preloading...")
        asyncio.create_task(startup_optimizer.lazy_load_indexes())
    
    # ハイブリッドサーチエンジンの初期化（軽量なので即座に実行）
    hybrid_engine = None
    try:
        from .services.hybrid_search import HybridSearchEngine
        hybrid_engine = HybridSearchEngine(
            index_dir=settings.USDA_INDEX_DIR,
            bm25_weight=settings.DEFAULT_BM25_WEIGHT,
            vector_weight=settings.DEFAULT_VECTOR_WEIGHT,
            rrf_k=settings.DEFAULT_RRF_K
        )
        logger.info("✅ Hybrid search engine initialized")
    except Exception as e:
        logger.warning(f"⚠️ Hybrid search engine initialization failed: {e}")
        logger.warning("   Hybrid mode will not be available")

    # パイプライン初期化（Lazy Loading対応）
    try:
        analysis.initialize_pipeline(
            hybrid_engine=hybrid_engine,
            use_lazy_loading=True  # Lazy Loadingを有効化
        )
    except Exception as e:
        logger.error(f"Failed to initialize pipeline during startup: {e}")
        raise

    # Retrieval router に search_service を設定
    from .routers import retrieval
    retrieval.set_search_service(analysis._pipeline.food_search_service)
    logger.info("✅ Retrieval router initialized with search service")

    # Retrieval routerにhybrid_engineも設定
    if hybrid_engine:
        retrieval.set_hybrid_search_engine(hybrid_engine)
        logger.info("✅ Retrieval router initialized with hybrid search engine")

    # Voice router に pipeline を設定
    from .routers import voice
    voice.set_pipeline(analysis._pipeline)
    logger.info("✅ Voice router initialized with pipeline")

    # Search Analytics初期化（BigQueryログ記録）
    analytics = None
    try:
        analytics = await init_analytics(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            enabled=os.environ.get("SEARCH_ANALYTICS_ENABLED", "true").lower() == "true"
        )
        logger.info("✅ Search Analytics initialized")
    except Exception as e:
        logger.warning(f"⚠️ Search Analytics initialization failed: {e}")
        logger.warning("   Search analytics logging will be disabled")

    # startup_optimizerのロード状態は、実際のロード後に更新される
    # ここではすぐに"ready"とマークしない（Lazy Loadingのため）
    logger.info("✅ Application initialized - ready to accept requests")

    yield  # アプリケーション実行中

    # Shutdown
    logger.info("Shutting down Freeform USDA Meal Analysis API...")

    # グローバルHTTPクライアントのクローズ
    from .core.http_client import close_async_client
    await close_async_client()
    logger.info("✅ HTTP client closed")

    # Search Analyticsの停止（残りのログをフラッシュ）
    analytics = get_analytics()
    if analytics:
        await analytics.stop()
        logger.info("✅ Search Analytics stopped")


# FastAPIアプリケーション作成
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Root",
            "description": "ルートエンドポイント - API情報とエンドポイント一覧を取得"
        },
        {
            "name": "Health",
            "description": "ヘルスチェック - サービス稼働状態確認（Cloud Run用 liveness/readiness probe）"
        },
        {
            "name": "Analysis",
            "description": "食事分析（メイン機能） - 画像から食事を分析し栄養価を計算。Match rate: 平均95%以上"
        },
        {
            "name": "Voice Analysis",
            "description": "音声入力分析 - 音声から食事を分析し栄養価を計算。Whisper STT + LLM + USDA検索"
        },
        {
            "name": "Streaming",
            "description": "SSEストリーミング - リアルタイム進捗表示付きの食事分析。プログレスバー実装に最適"
        },
        {
            "name": "Retrieval",
            "description": "食材検索 - USDA DBから類似食材を検索。Fast（高速180ms）/ Accurate（高精度800ms）/ Hybrid（最高精度、BM25+Vector）"
        },
        {
            "name": "Metadata",
            "description": "メタデータ配信 - USDA食材の詳細情報（13,564件）。フロントエンド向け、gzip圧縮推奨（8.4MB→0.7MB）"
        },
        {
            "name": "Admin",
            "description": "管理パネル - API設定の動的変更（VLM、検索、Reranker）。Firestoreで永続化、TTLキャッシュ対応"
        }
    ]
)

# CORS設定（環境に応じて制限）
if settings.ALLOWED_ORIGINS == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"CORS origins: {cors_origins}")

# ルーター登録
app.include_router(health.router)
app.include_router(analysis.router)
app.include_router(voice.router)  # Voice analysis router
app.include_router(streaming.router)  # SSE streaming router
app.include_router(retrieval.router, prefix="/api/v1", tags=["Retrieval"])
app.include_router(metadata.router, tags=["Metadata"])
app.include_router(admin_router)  # Admin Panel（/admin）


@app.get("/", response_model=RootResponse, tags=["Root"])
async def root():
    """
    ルートエンドポイント - API情報取得

    ## 概要
    APIの基本情報、利用可能なエンドポイント、デフォルト設定を取得します。

    Returns:
        RootResponse: API情報
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
            "analysis_stream": "/api/v1/meal-analyses/stream",
            "voice": "/api/v1/meal-analyses/voice",
            "voice_stream": "/api/v1/meal-analyses/voice/stream",
            "retrieval": "/api/v1/retrieve",
            "admin": "/admin",
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
        app,  # appオブジェクトを直接渡す（パッケージ構造に依存しない）
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )
