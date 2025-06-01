from typing import Optional, List
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
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash-preview-05-20"
    
    # USDA API設定
    USDA_API_KEY: str  # USDA FoodData Central APIキー（必須）
    USDA_API_BASE_URL: str = "https://api.nal.usda.gov/fdc/v1"
    USDA_API_TIMEOUT: float = 15.0  # APIタイムアウト秒数（FDC ID 746952のような遅いレスポンスに対応）
    USDA_API_MAX_RETRIES: int = 3  # 最大リトライ回数
    USDA_API_RETRY_DELAY: float = 1.0  # 初回リトライ前の待機時間（秒）
    USDA_API_RETRY_BACKOFF: float = 2.0  # リトライ間隔の倍率（exponential backoff）
    USDA_SEARCH_CANDIDATES_LIMIT: int = 5  # 1回の検索で取得する最大候補数
    # 主要栄養素番号（カンマ区切り文字列として環境変数から読み込む）
    USDA_KEY_NUTRIENT_NUMBERS_STR: str = "208,203,204,205,291,269,307"
    # 208: Energy (kcal), 203: Protein, 204: Total lipid (fat), 
    # 205: Carbohydrate, 291: Fiber, 269: Total sugars, 307: Sodium
    
    @property
    def USDA_KEY_NUTRIENT_NUMBERS(self) -> List[str]:
        """主要栄養素番号のリストを返す"""
        return self.USDA_KEY_NUTRIENT_NUMBERS_STR.split(",")
    
    # キャッシュ設定
    CACHE_TYPE: str = "simple"  # "simple", "redis", "memcached"
    CACHE_REDIS_URL: Optional[str] = None  # Redisを使用する場合のURL
    USDA_CACHE_TTL_SECONDS: int = 3600  # USDAレスポンスのキャッシュ有効期間（1時間）
    
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