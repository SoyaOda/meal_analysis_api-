import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..api.v1.endpoints import meal_analysis, voice_analysis
from ..config import get_settings
from ..models.meal_analysis_models import RootResponse

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# FastAPIアプリの作成
app = FastAPI(
    title="食事分析 API v2.0",
    description="コンポーネント化された食事分析システム",
    version="2.0.0",
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

# ルーターの登録
app.include_router(
    meal_analysis.router,
    prefix="/api/v1/meal-analyses",
    tags=["Complete Meal Analysis v2.0"]
)

# 音声分析ルーターの登録
app.include_router(
    voice_analysis.router,
    prefix="/api/v1/meal-analyses",
    tags=["Voice Meal Analysis v2.0"]
)

# ルートエンドポイント
@app.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    """ルートエンドポイント"""
    return RootResponse(
        message="食事分析 API v2.0 - コンポーネント化版",
        version="2.0.0",
        architecture="Component-based Pipeline",
        docs="/docs"
    )

@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "version": "v2.0",
        "components": ["Phase1Component", "Phase1SpeechComponent", "AdvancedNutritionSearchComponent", "NutritionCalculationComponent"]
    }

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app_v2.main.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    ) 