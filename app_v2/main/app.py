import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..api.v1.endpoints import nutrition_search
from ..config import get_settings

# 環境変数の設定（既存のappと同じ）
os.environ.setdefault("USDA_API_KEY", "vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg")
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/Users/odasoya/meal_analysis_api /service-account-key.json")
os.environ.setdefault("GEMINI_PROJECT_ID", "recording-diet-ai-3e7cf")
os.environ.setdefault("GEMINI_LOCATION", "us-central1")
os.environ.setdefault("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# FastAPIアプリの作成
app = FastAPI(
    title="Word Query API v2.0",
    description="栄養検索・食材照合専用システム",
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
    nutrition_search.router,
    prefix="/api/v1/nutrition",
    tags=["Nutrition Search & Suggestions"]
)

# ルートエンドポイント
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Word Query API v2.0 - 栄養検索専用版",
        "version": "2.0.0",
        "architecture": "Nutrition Search Service",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "version": "v2.0",
        "components": ["ElasticsearchComponent", "MyNetDiaryNutritionSearchComponent"]
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