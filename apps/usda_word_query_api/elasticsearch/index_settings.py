"""
Elasticsearch Index Settings for USDA Unified Database
USDA統合DBのElasticsearchインデックス設定
"""

from apps.usda_word_query_api.config import USDA_INDEX_NAME

# アナライザー設定（語幹化用）
USDA_INDEX_SETTINGS = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "stemmed_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "porter_stem"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            # 基本フィールド
            "id": {
                "type": "keyword"
            },
            "ingredient_type": {
                "type": "keyword"  # "raw" or "prepared"
            },

            # 検索用フィールド（元データ）
            "original_name": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "exact": {"type": "keyword", "normalizer": "lowercase_normalizer"}
                }
            },
            "search_name": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "description": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },

            # 語幹化フィールド（検索最適化）
            "stemmed_search_name": {
                "type": "text",
                "analyzer": "stemmed_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "stemmed_description": {
                "type": "text",
                "analyzer": "stemmed_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },

            # AI生成フィールド（オプション）
            "ai_description": {
                "type": "text"
            },

            # LLMで生成された新しいフィールド
            "brand_name": {
                "type": "keyword"  # ブランド名（例: "Ritz", "McDonald's"）
            },
            "item_type": {
                "type": "keyword"  # 食材タイプ（raw_ingredient, processed_ingredient, prepared_dish）
            },

            # 栄養情報
            "default_unit": {
                "type": "keyword"
            },
            "default_calories": {
                "type": "float"
            },
            "default_nutrition": {
                "type": "object",
                "properties": {
                    "calorie": {"type": "float"},
                    "Protein_g": {"type": "float"},
                    "Total_Fat_g": {"type": "float"},
                    "Total_Carbs_g": {"type": "float"}
                }
            },
            "unit_to_grams": {
                "type": "object",
                "enabled": True
            },

            # メタデータ
            "source": {
                "type": "keyword"
            },
            "data_type": {
                "type": "keyword"
            },
            "processing_method": {
                "type": "keyword"
            },
            "conversion_timestamp": {
                "type": "float"
            },

            # カテゴリ情報（元のUSDAデータから）
            "category": {
                "type": "keyword"
            },
            "category_emoji": {
                "type": "keyword"
            },
            "food_specific_emoji": {
                "type": "keyword"
            }
        }
    }
}

# Normalizerの設定を追加（lowercase_normalizer）
USDA_INDEX_SETTINGS["settings"]["analysis"]["normalizer"] = {
    "lowercase_normalizer": {
        "type": "custom",
        "filter": ["lowercase"]
    }
}


def get_index_settings():
    """インデックス設定を取得"""
    return USDA_INDEX_SETTINGS


def get_index_name():
    """インデックス名を取得"""
    return USDA_INDEX_NAME
