from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache


from pydantic import Field

class Settings(BaseSettings):
    """
    API設定クラス
    環境変数から設定値を読み込む
    """
    # Deep Infra設定
    DEEPINFRA_API_KEY: Optional[str] = None  # Deep Infra APIキー
    DEEPINFRA_MODEL_ID: str = "google/gemma-3-27b-it"  # Deep Infraモデル識別子
    DEEPINFRA_BASE_URL: str = "https://api.deepinfra.com/v1/openai"  # OpenAI互換エンドポイント
    
    # 栄養データベース検索設定
    USE_ELASTICSEARCH_SEARCH: bool = True  # Elasticsearch栄養データベース検索を使用するかどうか
    USE_LOCAL_NUTRITION_SEARCH: bool = False  # ローカル栄養データベース検索を使用するかどうか（レガシー）
    NUTRITION_DB_EXPERIMENT_PATH: Optional[str] = None  # nutrition_db_experimentへのパス（自動検出する場合はNone）
    
    # Elasticsearch設定
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index_name: str = "nutrition_fuzzy_search"
    elasticsearch_timeout: int = 30
    
    # ファジーマッチング設定
    fuzzy_search_enabled: bool = True  # ファジーマッチング機能を有効にするかどうか
    jaro_winkler_threshold: float = 0.85  # Jaro-Winkler類似度の閾値
    fuzzy_min_score_tier3: float = 5.0  # Tier 3の最小スコア閾値
    fuzzy_max_candidates: int = 5  # Tier 4で取得する最大候補数
    
    # キャッシュ設定
    CACHE_TYPE: str = "simple"  # "simple", "redis", "memcached"
    CACHE_REDIS_URL: Optional[str] = None  # Redisを使用する場合のURL
    NUTRITION_CACHE_TTL_SECONDS: int = 3600  # 栄養データベースレスポンスのキャッシュ有効期間（1時間）
    
    # API設定
    API_LOG_LEVEL: str = "INFO"
    FASTAPI_ENV: str = "development"
    
    # サーバー設定（Cloud Run対応）
    HOST: str = "0.0.0.0"
    PORT: int = Field(default=8000, env="PORT")  # Cloud RunのPORT環境変数に対応
    
    # APIバージョン
    API_VERSION: str = "v1"
    
    # 結果保存設定
    RESULTS_DIR: str = "analysis_results"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 追加の環境変数を無視  # 追加の環境変数を無視


@lru_cache()
def get_settings() -> Settings:
    """
    設定インスタンスを取得（キャッシュされる）
    """
    return Settings() 