from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from .api.v1.endpoints import meal_analyses, meal_analyses_refine, meal_analyses_complete
from .core.config import get_settings

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,  # 一時的にDEBUGレベルに変更
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# 設定の取得
settings = get_settings()

# FastAPIアプリケーションの作成
app = FastAPI(
    title="食事分析API (Meal Analysis API)",
    description="食事の画像とテキストを分析し、料理と材料を特定するAPI。USDAデータベースとの連携により栄養価計算の精度を向上。",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORSミドルウェアの設定（開発環境用）
if settings.FASTAPI_ENV == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 本番環境では適切に制限する
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ルートパスのエンドポイント
@app.get("/")
async def root():
    """APIのルートエンドポイント"""
    return {
        "message": "食事分析API (Meal Analysis API)",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """APIのヘルスチェック"""
    return {
        "status": "healthy",
        "service": "meal-analysis-api"
    }

# v1 APIルーターの登録
app.include_router(
    meal_analyses.router,
    prefix=f"/api/{settings.API_VERSION}/meal-analyses",
    tags=["Meal Analysis"]
)

# v1 API フェーズ2ルーターの登録（/refineエンドポイント）
app.include_router(
    meal_analyses_refine.router,
    prefix=f"/api/{settings.API_VERSION}/meal-analyses",
    tags=["Meal Analysis"]
)

# v1 API完全分析ルーターの登録（全フェーズ統合）
app.include_router(
    meal_analyses_complete.router,
    prefix=f"/api/{settings.API_VERSION}/meal-analyses",
    tags=["Complete Meal Analysis"]
)

# スタートアップイベント
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("Meal Analysis API starting up...")
    logger.info(f"Environment: {settings.FASTAPI_ENV}")
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Gemini Model: {settings.GEMINI_MODEL_NAME}")
    logger.info("Phase 2 features with USDA integration enabled")

# シャットダウンイベント
@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    logger.info("Meal Analysis API shutting down...")

# グローバルエラーハンドラー
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """予期しないエラーのハンドリング"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "内部サーバーエラーが発生しました。"
            }
        }
    ) 

# メイン実行部分
if __name__ == "__main__":
    import uvicorn
    import os
    
    # 環境変数の設定（必要に応じて）
    os.environ.setdefault("USDA_API_KEY", "vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg")
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/Users/odasoya/meal_analysis_api /service-account-key.json")
    os.environ.setdefault("GEMINI_PROJECT_ID", "recording-diet-ai-3e7cf")
    os.environ.setdefault("GEMINI_LOCATION", "us-central1")
    os.environ.setdefault("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")
    
    # サーバー起動
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    ) 