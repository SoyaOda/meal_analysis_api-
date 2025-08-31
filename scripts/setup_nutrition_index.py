#!/usr/bin/env python3
"""
Elasticsearch栄養データベースインデックスセットアップスクリプト
"""

import os
import sys
import json
import logging
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_nutrition_index(es_client, index_name="nutrition_db"):
    """栄養データベース用インデックス作成"""
    
    # インデックス設定
    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "food_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "stop",
                            "snowball"
                        ]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "name": {
                    "type": "text",
                    "analyzer": "food_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        },
                        "suggest": {
                            "type": "completion"
                        }
                    }
                },
                "brand": {
                    "type": "text",
                    "analyzer": "food_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "category": {
                    "type": "keyword"
                },
                "database": {
                    "type": "keyword"
                },
                "nutrition": {
                    "properties": {
                        "calories": {"type": "float"},
                        "protein": {"type": "float"},
                        "carbs": {"type": "float"},
                        "fat": {"type": "float"},
                        "fiber": {"type": "float"},
                        "sugar": {"type": "float"},
                        "sodium": {"type": "float"}
                    }
                },
                "ingredients": {
                    "type": "text",
                    "analyzer": "food_analyzer"
                },
                "preparation": {
                    "type": "text",
                    "analyzer": "food_analyzer"
                },
                "serving_size": {
                    "type": "text"
                },
                "created_at": {
                    "type": "date"
                }
            }
        }
    }
    
    try:
        # 既存インデックスチェック
        if es_client.indices.exists(index=index_name):
            logger.info(f"インデックス '{index_name}' は既に存在します")
            return True
        
        # インデックス作成
        es_client.indices.create(index=index_name, body=index_settings)
        logger.info(f"✅ インデックス '{index_name}' を作成しました")
        return True
        
    except RequestError as e:
        logger.error(f"❌ インデックス作成エラー: {e}")
        return False

def add_sample_data(es_client, index_name="nutrition_db"):
    """サンプル栄養データ追加"""
    
    sample_foods = [
        {
            "name": "白米",
            "brand": "",
            "category": "主食",
            "database": "sample",
            "nutrition": {
                "calories": 168,
                "protein": 2.5,
                "carbs": 37.1,
                "fat": 0.3,
                "fiber": 0.3,
                "sugar": 0.1,
                "sodium": 1
            },
            "ingredients": "米",
            "preparation": "炊飯",
            "serving_size": "100g",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "name": "鶏むね肉",
            "brand": "",
            "category": "肉類",
            "database": "sample",
            "nutrition": {
                "calories": 108,
                "protein": 22.3,
                "carbs": 0,
                "fat": 1.5,
                "fiber": 0,
                "sugar": 0,
                "sodium": 39
            },
            "ingredients": "鶏肉",
            "preparation": "生",
            "serving_size": "100g",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "name": "トマト",
            "brand": "",
            "category": "野菜",
            "database": "sample",
            "nutrition": {
                "calories": 19,
                "protein": 0.7,
                "carbs": 4.7,
                "fat": 0.1,
                "fiber": 1.0,
                "sugar": 2.6,
                "sodium": 3
            },
            "ingredients": "トマト",
            "preparation": "生",
            "serving_size": "100g",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
    
    try:
        # サンプルデータインサート
        for i, food in enumerate(sample_foods):
            es_client.index(
                index=index_name,
                id=f"sample_{i+1}",
                body=food
            )
        
        # インデックス更新
        es_client.indices.refresh(index=index_name)
        
        logger.info(f"✅ {len(sample_foods)}件のサンプルデータを追加しました")
        return True
        
    except Exception as e:
        logger.error(f"❌ サンプルデータ追加エラー: {e}")
        return False

def test_search(es_client, index_name="nutrition_db"):
    """検索テスト"""
    
    try:
        # 基本検索テスト
        query = {
            "query": {
                "match": {
                    "name": "米"
                }
            }
        }
        
        result = es_client.search(index=index_name, body=query)
        hits = result['hits']['total']['value']
        
        logger.info(f"✅ 検索テスト成功: '米' の検索で {hits} 件ヒット")
        
        # 結果表示
        for hit in result['hits']['hits']:
            food = hit['_source']
            logger.info(f"  - {food['name']} ({food['nutrition']['calories']}kcal)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 検索テストエラー: {e}")
        return False

def main():
    """メイン処理"""
    
    # Elasticsearch接続設定
    if len(sys.argv) > 1:
        es_host = sys.argv[1]
    else:
        es_host = input("Elasticsearch URL を入力してください (例: http://10.128.0.2:9200): ")
    
    if not es_host.startswith('http'):
        es_host = f"http://{es_host}"
    
    if not es_host.endswith(':9200'):
        es_host = f"{es_host}:9200"
    
    logger.info(f"🔗 Elasticsearch接続先: {es_host}")
    
    try:
        # Elasticsearch クライアント作成
        es_client = Elasticsearch([es_host], timeout=30)
        
        # 接続テスト
        if not es_client.ping():
            logger.error("❌ Elasticsearch接続に失敗しました")
            return False
        
        logger.info("✅ Elasticsearch接続成功")
        
        # インデックス作成
        if not create_nutrition_index(es_client):
            return False
        
        # サンプルデータ追加
        if not add_sample_data(es_client):
            return False
        
        # 検索テスト
        if not test_search(es_client):
            return False
        
        logger.info("")
        logger.info("🎉 Elasticsearch栄養データベースセットアップ完了!")
        logger.info(f"📍 Elasticsearch URL: {es_host}")
        logger.info("📝 Cloud Run環境変数に以下を設定してください:")
        logger.info(f"   ELASTIC_HOST={es_host}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ セットアップエラー: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)