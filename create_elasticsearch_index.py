#!/usr/bin/env python3
"""
Elasticsearch Index Creation Script with Lemmatization Support

現状のJSONデータベースからElasticsearchインデックスを作成する（見出し語化対応版）
"""

import json
import os
from elasticsearch import Elasticsearch
from typing import Dict, List, Any
import time

# 見出し語化機能をインポート
try:
    from app_v2.utils.lemmatization import lemmatize_term
    LEMMATIZATION_AVAILABLE = True
    print("✅ 見出し語化機能が利用可能です")
except ImportError as e:
    print(f"⚠️ 見出し語化機能をインポートできません: {e}")
    print("   基本機能のみで実行します")
    LEMMATIZATION_AVAILABLE = False
    
    # フォールバック関数
    def lemmatize_term(term: str) -> str:
        return term.lower() if term else ""


def create_index_mapping() -> Dict[str, Any]:
    """Elasticsearchインデックスのマッピングを定義"""
    return {
        "mappings": {
            "properties": {
                "id": {
                    "type": "keyword"
                },
                "search_name": {
                    "type": "text",
                    "analyzer": "standard",
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
                    "analyzer": "standard",
                    "fields": {
                        "exact": {
                            "type": "keyword"
                        }
                    }
                },
                "description": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "data_type": {
                    "type": "keyword"
                },
                "nutrition": {
                    "type": "object",
                    "properties": {
                        "calories": {"type": "float"},
                        "protein": {"type": "float"},
                        "fat": {"type": "float"},
                        "carbs": {"type": "float"},
                        "carbohydrates": {"type": "float"},
                        "fiber": {"type": "float"},
                        "sugar": {"type": "float"},
                        "sodium": {"type": "float"}
                    }
                },
                "weight": {
                    "type": "float"
                },
                "source_db": {
                    "type": "keyword"
                }
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "food_analyzer": {
                        "type": "standard",
                        "stopwords": "_none_"
                    }
                }
            }
        }
    }


def load_json_databases() -> Dict[str, List[Dict[str, Any]]]:
    """JSONデータベースファイルを読み込み"""
    databases = {}
    
    db_configs = {
        "yazio": "db/yazio_db.json",
        "mynetdiary": "db/mynetdiary_db.json", 
        "eatthismuch": "db/eatthismuch_db.json"
    }
    
    for db_name, file_path in db_configs.items():
        try:
            if os.path.exists(file_path):
                print(f"Loading {db_name} from {file_path}...")
                with open(file_path, 'r', encoding='utf-8') as f:
                    database = json.load(f)
                    databases[db_name] = database
                    print(f"✅ Loaded {db_name}: {len(database)} items")
            else:
                print(f"⚠️  File not found: {file_path}")
                databases[db_name] = []
        except Exception as e:
            print(f"❌ Error loading {db_name}: {e}")
            databases[db_name] = []
    
    return databases


def prepare_document(item: Dict[str, Any], source_db: str) -> Dict[str, Any]:
    """ドキュメントをElasticsearch用に準備（見出し語化対応）"""
    search_name = item.get("search_name", "")
    
    # 見出し語化されたsearch_nameを生成
    search_name_lemmatized = ""
    if search_name and LEMMATIZATION_AVAILABLE:
        try:
            search_name_lemmatized = lemmatize_term(search_name)
        except Exception as e:
            print(f"⚠️ 見出し語化エラー for '{search_name}': {e}")
            search_name_lemmatized = search_name.lower()
    else:
        search_name_lemmatized = search_name.lower()
    
    doc = {
        "id": item.get("id", 0),
        "search_name": search_name,
        "search_name_lemmatized": search_name_lemmatized,
        "description": item.get("description"),
        "data_type": item.get("data_type", "unknown"),
        "nutrition": item.get("nutrition", {}),
        "weight": item.get("weight"),
        "source_db": source_db
    }
    
    # 空の値を除去
    return {k: v for k, v in doc.items() if v is not None}


def bulk_index_documents(es_client: Elasticsearch, index_name: str, documents: List[Dict[str, Any]], batch_size: int = 1000):
    """バルクインデックスでドキュメントを追加"""
    total_docs = len(documents)
    indexed_count = 0
    
    print(f"📥 Indexing {total_docs} documents in batches of {batch_size}...")
    
    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]
        
        # バルクリクエストの構築
        bulk_body = []
        for doc in batch:
            bulk_body.append({
                "index": {
                    "_index": index_name,
                    "_id": f"{doc['source_db']}_{doc['id']}"
                }
            })
            bulk_body.append(doc)
        
        try:
            response = es_client.bulk(body=bulk_body)
            
            # エラーチェック
            if response.get("errors"):
                error_count = sum(1 for item in response["items"] if "error" in item.get("index", {}))
                print(f"⚠️  Batch {i//batch_size + 1}: {error_count} errors in batch")
            
            indexed_count += len(batch)
            print(f"   Progress: {indexed_count}/{total_docs} ({indexed_count/total_docs*100:.1f}%)")
            
        except Exception as e:
            print(f"❌ Error indexing batch {i//batch_size + 1}: {e}")
    
    print(f"✅ Indexing completed: {indexed_count} documents")


def main():
    """メイン処理"""
    print("=== Elasticsearch Index Creation ===")
    
    # Elasticsearchクライアントの初期化
    print("\n1. Connecting to Elasticsearch...")
    es_client = Elasticsearch(["http://localhost:9200"])
    
    if not es_client.ping():
        print("❌ Cannot connect to Elasticsearch. Make sure it's running on localhost:9200")
        return False
    
    print("✅ Connected to Elasticsearch")
    
    # インデックス名
    index_name = "nutrition_db"
    
    # 既存インデックスの削除（必要に応じて）
    print(f"\n2. Checking existing index '{index_name}'...")
    if es_client.indices.exists(index=index_name):
        print(f"   Index '{index_name}' already exists. Deleting...")
        es_client.indices.delete(index=index_name)
        print("   ✅ Deleted existing index")
    
    # インデックスの作成
    print(f"\n3. Creating index '{index_name}'...")
    mapping = create_index_mapping()
    es_client.indices.create(index=index_name, body=mapping)
    print("✅ Index created with mapping")
    
    # JSONデータベースの読み込み
    print("\n4. Loading JSON databases...")
    databases = load_json_databases()
    
    # ドキュメントの準備
    print("\n5. Preparing documents for indexing...")
    all_documents = []
    
    for db_name, items in databases.items():
        print(f"   Processing {db_name}: {len(items)} items")
        for item in items:
            if "search_name" in item:  # 有効なアイテムのみ
                doc = prepare_document(item, db_name)
                all_documents.append(doc)
    
    print(f"✅ Prepared {len(all_documents)} documents for indexing")
    
    # バルクインデックス
    print("\n6. Bulk indexing documents...")
    start_time = time.time()
    bulk_index_documents(es_client, index_name, all_documents)
    end_time = time.time()
    
    print(f"✅ Indexing completed in {end_time - start_time:.2f} seconds")
    
    # インデックス統計の表示
    print("\n7. Index statistics...")
    stats = es_client.indices.stats(index=index_name)
    doc_count = stats["indices"][index_name]["total"]["docs"]["count"]
    index_size = stats["indices"][index_name]["total"]["store"]["size_in_bytes"]
    
    print(f"   Total documents: {doc_count}")
    print(f"   Index size: {index_size / 1024 / 1024:.2f} MB")
    
    # サンプル検索テスト（見出し語化対応）
    print("\n8. Testing sample search...")
    
    # 従来の検索
    test_query_standard = {
        "query": {
            "multi_match": {
                "query": "chicken",
                "fields": ["search_name", "search_name.exact"]
            }
        },
        "size": 3
    }
    
    response = es_client.search(index=index_name, body=test_query_standard)
    hits = response["hits"]["hits"]
    
    print(f"   Standard search for 'chicken': {len(hits)} results")
    for hit in hits:
        source = hit["_source"]
        print(f"   - {source['search_name']} ({source['source_db']}) score: {hit['_score']:.2f}")
    
    # 見出し語化検索テスト
    print("\n   Testing lemmatized search...")
    test_query_lemmatized = {
        "query": {
            "multi_match": {
                "query": "tomatoes",
                "fields": ["search_name", "search_name_lemmatized"]
            }
        },
        "size": 5
    }
    
    response_lem = es_client.search(index=index_name, body=test_query_lemmatized)
    hits_lem = response_lem["hits"]["hits"]
    
    print(f"   Lemmatized search for 'tomatoes': {len(hits_lem)} results")
    for hit in hits_lem:
        source = hit["_source"]
        lemmatized = source.get('search_name_lemmatized', 'N/A')
        print(f"   - {source['search_name']} -> {lemmatized} ({source['source_db']}) score: {hit['_score']:.2f}")
    
    print(f"\n🎉 Elasticsearch index '{index_name}' successfully created!")
    print(f"   Ready for high-speed nutrition search")
    
    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Index creation completed successfully!")
    else:
        print("\n❌ Index creation failed!") 