#!/usr/bin/env python3
"""
ElasticsearchVM用の3つのデータベース統合インデックス作成スクリプト
ローカルと同様の栄養データベース検索を実現
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any, Optional
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 見出し語化の依存関係チェック
LEMMATIZATION_AVAILABLE = False
try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    LEMMATIZATION_AVAILABLE = True
    logger.info("✅ NLTK lemmatization available")
    
    # 必要なNLTKデータの確認
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/wordnet')
    except LookupError:
        logger.warning("⚠️ NLTK data missing, downloading...")
        nltk.download('punkt')
        nltk.download('wordnet')
        nltk.download('omw-1.4')
        
except ImportError:
    logger.warning("⚠️ NLTK not available, lemmatization disabled")

def lemmatize_term(term: str) -> str:
    """単語の見出し語化"""
    if not LEMMATIZATION_AVAILABLE:
        return term.lower()
    
    try:
        lemmatizer = WordNetLemmatizer()
        tokens = word_tokenize(term.lower())
        lemmatized = [lemmatizer.lemmatize(token) for token in tokens]
        return " ".join(lemmatized)
    except Exception as e:
        logger.warning(f"Lemmatization failed for '{term}': {e}")
        return term.lower()

def create_index_mapping() -> Dict[str, Any]:
    """Elasticsearchインデックスマッピング定義"""
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "food_name_analyzer": {
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
                "search_name": {
                    "type": "text",
                    "analyzer": "food_name_analyzer",
                    "fields": {
                        "exact": {
                            "type": "keyword"
                        },
                        "suggest": {
                            "type": "completion"
                        }
                    }
                },
                "search_name_lemmatized": {
                    "type": "text",
                    "analyzer": "food_name_analyzer"
                },
                "brand": {
                    "type": "text",
                    "analyzer": "food_name_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "category": {
                    "type": "keyword"
                },
                "source_db": {
                    "type": "keyword"
                },
                "data_type": {
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
                        "sodium": {"type": "float"},
                        "cholesterol": {"type": "float"},
                        "saturated_fat": {"type": "float"},
                        "trans_fat": {"type": "float"},
                        "potassium": {"type": "float"},
                        "calcium": {"type": "float"},
                        "iron": {"type": "float"},
                        "vitamin_a": {"type": "float"},
                        "vitamin_c": {"type": "float"}
                    }
                },
                "ingredients": {
                    "type": "text",
                    "analyzer": "food_name_analyzer"
                },
                "preparation": {
                    "type": "text",
                    "analyzer": "food_name_analyzer"
                },
                "serving_size": {
                    "type": "text"
                },
                "serving_unit": {
                    "type": "keyword"
                },
                "created_at": {
                    "type": "date"
                }
            }
        }
    }

def create_sample_nutrition_databases() -> Dict[str, List[Dict[str, Any]]]:
    """ローカルと同様の3つのデータベースのサンプルデータ作成"""
    
    # YAZIO データベース (1,825項目相当のサンプル)
    yazio_samples = [
        {
            "search_name": "白米",
            "brand": "",
            "category": "主食",
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
            "serving_unit": "g"
        },
        {
            "search_name": "玄米",
            "brand": "",
            "category": "主食",
            "nutrition": {
                "calories": 165,
                "protein": 2.8,
                "carbs": 35.6,
                "fat": 1.0,
                "fiber": 1.4,
                "sugar": 0.4,
                "sodium": 1
            },
            "ingredients": "玄米",
            "preparation": "炊飯",
            "serving_size": "100g",
            "serving_unit": "g"
        },
        {
            "search_name": "食パン",
            "brand": "YAZIO",
            "category": "パン類",
            "nutrition": {
                "calories": 264,
                "protein": 9.0,
                "carbs": 47.0,
                "fat": 4.4,
                "fiber": 2.3,
                "sugar": 3.0,
                "sodium": 500
            },
            "ingredients": "小麦粉、イースト、塩、砂糖",
            "preparation": "焼成",
            "serving_size": "100g",
            "serving_unit": "g"
        }
    ]
    
    # MyNetDiary データベース (1,142項目相当のサンプル)
    mynetdiary_samples = [
        {
            "search_name": "鶏むね肉",
            "brand": "",
            "category": "肉類",
            "nutrition": {
                "calories": 108,
                "protein": 22.3,
                "carbs": 0,
                "fat": 1.5,
                "fiber": 0,
                "sugar": 0,
                "sodium": 39,
                "cholesterol": 58
            },
            "ingredients": "鶏肉",
            "preparation": "生",
            "serving_size": "100g",
            "serving_unit": "g"
        },
        {
            "search_name": "鶏もも肉",
            "brand": "",
            "category": "肉類",
            "nutrition": {
                "calories": 200,
                "protein": 16.2,
                "carbs": 0,
                "fat": 14.2,
                "fiber": 0,
                "sugar": 0,
                "sodium": 98,
                "cholesterol": 89
            },
            "ingredients": "鶏肉",
            "preparation": "生",
            "serving_size": "100g",
            "serving_unit": "g"
        },
        {
            "search_name": "豚ロース",
            "brand": "MyNetDiary",
            "category": "肉類",
            "nutrition": {
                "calories": 263,
                "protein": 19.3,
                "carbs": 0.2,
                "fat": 19.2,
                "fiber": 0,
                "sugar": 0,
                "sodium": 59,
                "cholesterol": 69
            },
            "ingredients": "豚肉",
            "preparation": "生",
            "serving_size": "100g",
            "serving_unit": "g"
        }
    ]
    
    # EatThisMuch データベース (8,878項目相当のサンプル)
    eatthismuch_samples = [
        {
            "search_name": "トマト",
            "brand": "",
            "category": "野菜",
            "nutrition": {
                "calories": 19,
                "protein": 0.7,
                "carbs": 4.7,
                "fat": 0.1,
                "fiber": 1.0,
                "sugar": 2.6,
                "sodium": 3,
                "potassium": 237,
                "vitamin_c": 21.0,
                "vitamin_a": 449
            },
            "ingredients": "トマト",
            "preparation": "生",
            "serving_size": "100g",
            "serving_unit": "g"
        },
        {
            "search_name": "きゅうり",
            "brand": "",
            "category": "野菜",
            "nutrition": {
                "calories": 14,
                "protein": 0.7,
                "carbs": 3.6,
                "fat": 0.1,
                "fiber": 0.5,
                "sugar": 1.7,
                "sodium": 2,
                "potassium": 147,
                "vitamin_c": 2.8
            },
            "ingredients": "きゅうり",
            "preparation": "生",
            "serving_size": "100g",
            "serving_unit": "g"
        },
        {
            "search_name": "バナナ",
            "brand": "EatThisMuch",
            "category": "果物",
            "nutrition": {
                "calories": 89,
                "protein": 1.1,
                "carbs": 22.8,
                "fat": 0.3,
                "fiber": 2.6,
                "sugar": 12.2,
                "sodium": 1,
                "potassium": 358,
                "vitamin_c": 8.7,
                "vitamin_a": 64
            },
            "ingredients": "バナナ",
            "preparation": "生",
            "serving_size": "100g",
            "serving_unit": "g"
        },
        {
            "search_name": "アボカド",
            "brand": "",
            "category": "果物",
            "nutrition": {
                "calories": 160,
                "protein": 2.0,
                "carbs": 8.5,
                "fat": 14.7,
                "fiber": 6.7,
                "sugar": 0.7,
                "sodium": 7,
                "potassium": 485
            },
            "ingredients": "アボカド",
            "preparation": "生",
            "serving_size": "100g",
            "serving_unit": "g"
        },
        {
            "search_name": "鮭",
            "brand": "",
            "category": "魚類",
            "nutrition": {
                "calories": 208,
                "protein": 25.4,
                "carbs": 0,
                "fat": 12.4,
                "fiber": 0,
                "sugar": 0,
                "sodium": 59,
                "cholesterol": 55
            },
            "ingredients": "鮭",
            "preparation": "生",
            "serving_size": "100g",
            "serving_unit": "g"
        }
    ]
    
    return {
        "yazio": yazio_samples,
        "mynetdiary": mynetdiary_samples,
        "eatthismuch": eatthismuch_samples
    }

def prepare_document(item: Dict[str, Any], db_name: str) -> Dict[str, Any]:
    """ドキュメントをElasticsearch用に準備"""
    doc = {
        "search_name": item["search_name"],
        "search_name_lemmatized": lemmatize_term(item["search_name"]),
        "brand": item.get("brand", ""),
        "category": item.get("category", ""),
        "source_db": db_name,
        "data_type": "food",
        "nutrition": item.get("nutrition", {}),
        "ingredients": item.get("ingredients", ""),
        "preparation": item.get("preparation", ""),
        "serving_size": item.get("serving_size", "100g"),
        "serving_unit": item.get("serving_unit", "g"),
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    # 検索用のサジェスト設定
    if "search_name" in doc:
        doc["search_name"] = {
            "input": doc["search_name"],
            "suggest": doc["search_name"]
        }
    
    return doc

def bulk_index_documents(es_client: Elasticsearch, index_name: str, documents: List[Dict[str, Any]], batch_size: int = 100):
    """バルクインデックス処理"""
    from elasticsearch.helpers import bulk
    
    def doc_generator():
        for i, doc in enumerate(documents):
            yield {
                "_index": index_name,
                "_id": f"{doc['source_db']}_{i}",
                "_source": doc
            }
    
    try:
        success, failed = bulk(es_client, doc_generator(), chunk_size=batch_size)
        logger.info(f"✅ Successfully indexed: {success} documents")
        if failed:
            logger.warning(f"⚠️ Failed to index: {len(failed)} documents")
            for failure in failed[:5]:  # 最初の5つの失敗のみ表示
                logger.warning(f"   Failed: {failure}")
        
        return success
    except Exception as e:
        logger.error(f"❌ Bulk indexing failed: {e}")
        return 0

def test_multi_database_search(es_client: Elasticsearch, index_name: str):
    """複数データベース検索テスト"""
    logger.info("🔍 Testing multi-database search...")
    
    test_queries = [
        {"term": "鶏", "description": "鶏肉検索 (MyNetDiary)"},
        {"term": "トマト", "description": "野菜検索 (EatThisMuch)"},
        {"term": "米", "description": "主食検索 (YAZIO)"},
        {"term": "バナナ", "description": "果物検索 (EatThisMuch)"}
    ]
    
    for query_info in test_queries:
        term = query_info["term"]
        desc = query_info["description"]
        
        query = {
            "query": {
                "multi_match": {
                    "query": term,
                    "fields": ["search_name", "search_name_lemmatized"],
                    "type": "best_fields"
                }
            },
            "size": 3
        }
        
        try:
            response = es_client.search(index=index_name, body=query)
            hits = response["hits"]["hits"]
            
            logger.info(f"   {desc}: {len(hits)} results")
            for hit in hits:
                source = hit["_source"]
                logger.info(f"     - {source['search_name']} ({source['source_db']}) score: {hit['_score']:.2f}")
        except Exception as e:
            logger.error(f"   ❌ Search failed for '{term}': {e}")

def main():
    """メイン処理"""
    logger.info("=== Elasticsearch Multi-Database Index Creation for VM ===")
    
    # コマンドライン引数からElasticsearch URLを取得
    if len(sys.argv) > 1:
        es_host = sys.argv[1]
    else:
        es_host = input("Elasticsearch URL を入力してください (例: http://10.128.0.2:9200): ")
    
    if not es_host.startswith('http'):
        es_host = f"http://{es_host}"
    
    if not es_host.endswith(':9200'):
        es_host = f"{es_host}:9200"
    
    logger.info(f"🔗 Connecting to Elasticsearch: {es_host}")
    
    try:
        # Elasticsearch クライアント作成
        es_client = Elasticsearch([es_host], timeout=30)
        
        # 接続テスト
        if not es_client.ping():
            logger.error("❌ Cannot connect to Elasticsearch")
            return False
        
        logger.info("✅ Connected to Elasticsearch")
        
        # インデックス名
        index_name = "nutrition_db"
        
        # 既存インデックスの削除
        if es_client.indices.exists(index=index_name):
            logger.info(f"Deleting existing index '{index_name}'...")
            es_client.indices.delete(index=index_name)
            logger.info("✅ Deleted existing index")
        
        # インデックス作成
        logger.info(f"Creating index '{index_name}'...")
        mapping = create_index_mapping()
        es_client.indices.create(index=index_name, body=mapping)
        logger.info("✅ Index created with mapping")
        
        # サンプルデータベース作成
        logger.info("Creating sample nutrition databases...")
        databases = create_sample_nutrition_databases()
        
        # ドキュメント準備
        logger.info("Preparing documents for indexing...")
        all_documents = []
        
        for db_name, items in databases.items():
            logger.info(f"   Processing {db_name}: {len(items)} items")
            for item in items:
                doc = prepare_document(item, db_name)
                all_documents.append(doc)
        
        logger.info(f"✅ Prepared {len(all_documents)} documents for indexing")
        
        # バルクインデックス
        logger.info("Bulk indexing documents...")
        start_time = time.time()
        indexed_count = bulk_index_documents(es_client, index_name, all_documents)
        end_time = time.time()
        
        logger.info(f"✅ Indexing completed in {end_time - start_time:.2f} seconds")
        
        # インデックス統計
        logger.info("Index statistics...")
        es_client.indices.refresh(index=index_name)
        stats = es_client.indices.stats(index=index_name)
        doc_count = stats["indices"][index_name]["total"]["docs"]["count"]
        index_size = stats["indices"][index_name]["total"]["store"]["size_in_bytes"]
        
        logger.info(f"   Total documents: {doc_count}")
        logger.info(f"   Index size: {index_size / 1024:.2f} KB")
        
        # 複数データベース検索テスト
        test_multi_database_search(es_client, index_name)
        
        logger.info("")
        logger.info("🎉 Elasticsearch multi-database index successfully created!")
        logger.info("📊 Database distribution:")
        logger.info("   - yazio: 3 items (主食、パン類)")
        logger.info("   - mynetdiary: 3 items (肉類)")
        logger.info("   - eatthismuch: 5 items (野菜、果物、魚類)")
        logger.info("")
        logger.info("📝 Cloud Run環境変数設定:")
        logger.info(f"   ELASTIC_HOST={es_host}")
        logger.info("   ELASTIC_INDEX=nutrition_db")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)