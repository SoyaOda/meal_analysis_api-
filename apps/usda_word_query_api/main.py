"""
USDA Word Query API - Main Application
USDA FNDDS統合データベース栄養検索API専用アプリケーション（word_query_apiのUSDA版）
"""

import logging
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# PYTHONPATHを設定して共通ライブラリにアクセス
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.usda_word_query_api.endpoints.usda_search import router as usda_router
from apps.usda_word_query_api.config import API_TITLE, API_DESCRIPTION, API_VERSION, DEFAULT_PORT

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション作成
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(
    usda_router,
    prefix="/api/v1/usda",
    tags=["usda-search"]
)

# word_query_api互換性のため、同じルーターを/api/v1/nutritionでも提供（リダイレクトなし）
app.include_router(
    usda_router,
    prefix="/api/v1/nutrition",
    tags=["nutrition-search-compat"],
    include_in_schema=False
)

@app.get("/", tags=["root"])
async def root():
    """ルートエンドポイント"""
    return {
        "message": "USDA Word Query API",
        "version": API_VERSION,
        "status": "healthy",
        "data_source": "USDA FNDDS",
        "total_items": 1542,
        "endpoints": {
            "docs": "/docs",
            "usda_search": "/api/v1/usda/suggest",
            "usda_stats": "/api/v1/usda/stats",
            "health": "/api/v1/usda/suggest/health"
        }
    }

@app.get("/health", tags=["health"])
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "api": "usda-word-query",
        "version": API_VERSION,
        "architecture": "unified",
        "data_source": "USDA_FNDDS"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    logger.info(f"Starting USDA Word Query API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)