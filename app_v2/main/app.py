import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..api.v1.endpoints import meal_analysis
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

# ルートエンドポイント
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "食事分析 API v2.0 - コンポーネント化版",
        "version": "2.0.0",
        "architecture": "Component-based Pipeline",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "version": "v2.0",
        "components": ["Phase1Component", "USDAQueryComponent"]
    }

if __name__ == "__main__":
    import uvicorn
    import os
    # Cloud RunのPORT環境変数を直接使用
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app_v2.main.app:app",
        host="0.0.0.0",
        port=port,
        reload=False
    ) 