"""
Meal Analysis API - Main Application
統合アーキテクチャでのmeal_analysis_api専用アプリケーション
"""

import logging
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# PYTHONPATHを設定して共通ライブラリにアクセス
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.meal_analysis_api.endpoints.meal_analysis import router as meal_router
from apps.meal_analysis_api.endpoints.voice_analysis import router as voice_router
from shared.models.phase1_models import RootResponse

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション作成
app = FastAPI(
    title="食事分析 API v2.0",
    description="コンポーネント化された食事分析システム（統合アーキテクチャ版）",
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

# ルーター登録 - app_v2と同じパス構造に
app.include_router(
    meal_router,
    prefix="/api/v1/meal-analyses",
    tags=["Complete Meal Analysis v2.0"]
)

app.include_router(
    voice_router,
    prefix="/api/v1/meal-analyses",
    tags=["Voice Meal Analysis v2.0"]
)

@app.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    """ルートエンドポイント"""
    return RootResponse(
        message="食事分析 API v2.0 - 統合アーキテクチャ版",
        version="2.1.0",
        architecture="Unified Component-based Pipeline",
        docs="/docs"
    )

@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "version": "v2.1",
        "architecture": "unified",
        "components": ["Phase1Component", "Phase1SpeechComponent", "AdvancedNutritionSearchComponent", "NutritionCalculationComponent"]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)