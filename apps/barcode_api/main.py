#!/usr/bin/env python3
"""
バーコード検索APIメインアプリケーション

FoodData Central (FDC) データベースを使用したバーコード検索API
"""

import logging
import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.barcode import router as barcode_router

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('barcode_api.log')
    ]
)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション作成
app = FastAPI(
    title="バーコード検索API",
    description="FoodData Central (FDC) データベースを使用したバーコード検索API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(barcode_router)


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("バーコード検索API起動中...")

    # データベース接続確認
    try:
        from .services.fdc_service import FDCDatabaseService
        fdc_service = FDCDatabaseService()

        if fdc_service.health_check():
            stats = fdc_service.get_database_stats()
            logger.info("FDCデータベース接続成功")
            logger.info(f"データベース統計: {stats}")
        else:
            logger.error("FDCデータベース接続失敗")

    except Exception as e:
        logger.error(f"起動時データベース確認エラー: {e}")

    logger.info("バーコード検索API起動完了")


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    logger.info("バーコード検索API終了")


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "service": "バーコード検索API",
        "version": "1.0.0",
        "description": "FoodData Central (FDC) データベースを使用したバーコード検索API",
        "endpoints": {
            "barcode_lookup": "/api/v1/barcode/lookup",
            "health_check": "/api/v1/barcode/health",
            "database_stats": "/api/v1/barcode/stats",
            "api_docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def app_health():
    """アプリケーション全体のヘルスチェック"""
    try:
        from .services.fdc_service import FDCDatabaseService
        fdc_service = FDCDatabaseService()
        db_healthy = fdc_service.health_check()

        return {
            "status": "healthy" if db_healthy else "degraded",
            "application": "running",
            "database": "connected" if db_healthy else "disconnected",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "application": "running",
                "database": "error",
                "error": str(e),
                "version": "1.0.0"
            }
        )


# 例外ハンドラー
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404エラーハンドラー"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error_code": "NOT_FOUND",
            "error_message": "リクエストされたリソースが見つかりません",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500エラーハンドラー"""
    logger.error(f"内部サーバーエラー: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "error_message": "内部サーバーエラーが発生しました"
        }
    )


if __name__ == "__main__":
    import uvicorn

    # 環境変数からポート番号を取得（デフォルト: 8003）
    port = int(os.getenv("PORT", "8003"))

    logger.info(f"バーコード検索APIをポート {port} で起動中...")

    uvicorn.run(
        "apps.barcode_api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # 開発時のみ
        log_level="info"
    )