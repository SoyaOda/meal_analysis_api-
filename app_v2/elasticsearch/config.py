"""
Elasticsearch設定管理
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class ElasticsearchConfig(BaseSettings):
    """Elasticsearch設定クラス"""
    
    # 接続設定
    host: str = "localhost"
    port: int = 9200
    scheme: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None
    
    # インデックス設定
    food_nutrition_index: str = "food_nutrition_v2"
    
    # 検索設定
    default_search_size: int = 10
    max_search_size: int = 100
    
    # タイムアウト設定
    timeout: int = 30
    max_retries: int = 3
    
    # セマンティック検索設定
    enable_semantic_search: bool = True  # 仕様書に基づき有効化（実装は段階的）
    semantic_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    class Config:
        env_prefix = "ELASTICSEARCH_"
        env_file = ".env"

    @property
    def connection_url(self) -> str:
        """Elasticsearch接続URLを生成"""
        auth_part = ""
        if self.username and self.password:
            auth_part = f"{self.username}:{self.password}@"
        
        return f"{self.scheme}://{auth_part}{self.host}:{self.port}"

    @property
    def connection_config(self) -> dict:
        """Elasticsearchクライアント接続設定を生成"""
        config = {
            "hosts": [{"host": self.host, "port": self.port, "scheme": self.scheme}],
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }
        
        if self.username and self.password:
            config["http_auth"] = (self.username, self.password)
            
        return config


# グローバル設定インスタンス
es_config = ElasticsearchConfig() 