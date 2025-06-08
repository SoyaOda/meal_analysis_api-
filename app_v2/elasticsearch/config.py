"""
Elasticsearch設定管理
"""
import os
from typing import Optional, Dict
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
    
    # 🎯 検索パラメータ設定（実験結果に基づく最適化設定）
    # Function Score重み設定
    enable_popularity_boost: bool = False  # 人気度ブーストを有効化するか
    popularity_boost_weight: float = 0.0  # 人気度ブーストの重み（0.0で無効化）
    
    enable_nutritional_similarity: bool = False  # 栄養プロファイル類似性を有効化するか
    nutritional_similarity_weight: float = 0.0  # 栄養プロファイル類似性の重み（0.0で無効化）
    
    enable_semantic_similarity: bool = False  # セマンティック類似性を有効化するか
    semantic_similarity_weight: float = 0.0  # セマンティック類似性の重み（0.0で無効化）
    
    # 栄養素重み設定（均等分割基準値）
    nutrition_weight_calories: float = 0.1  # カロリー重み（実験最適値）
    nutrition_weight_protein: float = 0.1   # タンパク質重み（実験最適値）
    nutrition_weight_fat: float = 0.1       # 脂質重み（実験最適値）
    nutrition_weight_carbs: float = 0.1     # 炭水化物重み（実験最適値）
    
    # 栄養素正規化係数設定
    nutrition_norm_calories: float = 200.0      # カロリー正規化係数（100gあたり100-300kcalの範囲）
    nutrition_norm_protein: float = 20.0        # タンパク質正規化係数（100gあたり10-30gの範囲）
    nutrition_norm_fat: float = 20.0            # 脂質正規化係数（100gあたり10-30gの範囲）
    nutrition_norm_carbs: float = 50.0          # 炭水化物正規化係数（100gあたり25-75gの範囲）
    nutrition_norm_fiber: float = 10.0          # 食物繊維正規化係数
    nutrition_norm_sodium: float = 500.0        # ナトリウム正規化係数
    
    # 語彙的検索フィールドブースト設定
    field_boost_food_name: float = 3.0           # food_nameフィールドのブースト値
    field_boost_description: float = 1.5         # descriptionフィールドのブースト値
    field_boost_brand_name: float = 1.2          # brand_nameフィールドのブースト値
    field_boost_ingredients: float = 1.0         # ingredientsフィールドのブースト値
    field_boost_phonetic: float = 0.5            # 音声類似フィールドのブースト値
    
    # フレーズマッチングブースト設定
    phrase_match_boost: float = 2.0              # フレーズ一致時のブースト値
    
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
    
    def get_nutrition_weights(self) -> Dict[str, float]:
        """栄養素重み辞書を取得"""
        return {
            "calories": self.nutrition_weight_calories,
            "protein_g": self.nutrition_weight_protein,
            "fat_total_g": self.nutrition_weight_fat,
            "carbohydrate_by_difference_g": self.nutrition_weight_carbs
        }
    
    def get_nutrition_normalization_factors(self) -> Dict[str, float]:
        """栄養素正規化係数辞書を取得"""
        return {
            "calories": self.nutrition_norm_calories,
            "protein_g": self.nutrition_norm_protein,
            "fat_total_g": self.nutrition_norm_fat,
            "carbohydrate_by_difference_g": self.nutrition_norm_carbs,
            "fiber_total_dietary_g": self.nutrition_norm_fiber,
            "sodium_mg": self.nutrition_norm_sodium
        }
    
    def get_field_boosts(self) -> Dict[str, float]:
        """フィールドブースト設定辞書を取得"""
        return {
            "food_name": self.field_boost_food_name,
            "description": self.field_boost_description,
            "brand_name": self.field_boost_brand_name,
            "ingredients_text": self.field_boost_ingredients,
            "food_name.phonetic": self.field_boost_phonetic
        }


# グローバル設定インスタンス
es_config = ElasticsearchConfig() 