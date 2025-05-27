from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    API設定クラス
    環境変数から設定値を読み込む
    """
    # Vertex AI設定
    GEMINI_PROJECT_ID: str  # GCPプロジェクトID（必須）
    GEMINI_LOCATION: str = "us-central1"  # デフォルトのロケーション
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"
    
    # API設定
    API_LOG_LEVEL: str = "INFO"
    FASTAPI_ENV: str = "development"
    
    # サーバー設定
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # APIバージョン
    API_VERSION: str = "v1"
    
    # Google Cloud認証設定
    # GOOGLE_APPLICATION_CREDENTIALSは通常環境変数で設定するため、ここでは不要
    # gcloud auth application-default login でも可
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    設定インスタンスを取得（キャッシュされる）
    """
    return Settings() 