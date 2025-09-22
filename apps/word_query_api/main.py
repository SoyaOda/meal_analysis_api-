"""
Nutrition Query API - Main Application
統合アーキテクチャでのnutrition_query_api専用アプリケーション
"""

import logging
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# PYTHONPATHを設定して共通ライブラリにアクセス
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.word_query_api.endpoints.nutrition_search import router as nutrition_router

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション作成
app = FastAPI(
    title="Nutrition Query API",
    description="栄養データベース検索API（統合アーキテクチャ版）",
    version="2.1.0",
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
    nutrition_router,
    prefix="/api/v1/nutrition",
    tags=["nutrition-search"]
)

@app.get("/", tags=["root"])
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Nutrition Query API - 統合アーキテクチャ版",
        "version": "2.1.0",
        "status": "healthy",
        "endpoints": {
            "docs": "/docs",
            "nutrition_search": "/api/v1/nutrition/"
        }
    }

@app.get("/health", tags=["health"])
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "api": "nutrition-query",
        "version": "2.1.0",
        "architecture": "unified"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)