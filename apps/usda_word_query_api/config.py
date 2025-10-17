"""
USDA Word Query API Configuration
USDA専用栄養検索API設定ファイル（word_query_apiのUSDA版）
"""

import os

# Elasticsearch Configuration
ELASTICSEARCH_URL = os.environ.get("ELASTICSEARCH_URL", "http://35.193.16.212:9200")
USDA_INDEX_NAME = "usda_unified_nutrition_db"

# API Configuration
API_TITLE = "USDA Word Query API"
API_DESCRIPTION = "USDA FNDDS統合データベース栄養検索API（word_query_apiのUSDA版）"
API_VERSION = "1.0.0"
DEFAULT_PORT = 8004

# Search Configuration
DEFAULT_SEARCH_SIZE = 10
MAX_SEARCH_SIZE = 50
MIN_QUERY_LENGTH = 2

# USDA-specific settings
INGREDIENT_TYPES = ["raw", "prepared"]  # 許可されるingredient_type

# Stemming Configuration (MyNetDiaryと同じ設定)
ENABLE_STEMMING = True
