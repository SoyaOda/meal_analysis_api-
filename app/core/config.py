from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    API設定クラス
    環境変数から設定値を読み込む
    """
    # Gemini API設定
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"
    
    # API設定
    API_LOG_LEVEL: str = "INFO"
    FASTAPI_ENV: str = "development"
    
    # サーバー設定
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # APIバージョン
    API_VERSION: str = "v1"
    
    # 追加の設定（将来のVertex AI移行用）
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GEMINI_PROJECT_ID: Optional[str] = None
    GEMINI_LOCATION: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    設定インスタンスを取得（キャッシュされる）
    """
    return Settings() 