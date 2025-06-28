#!/usr/bin/env python3
"""
Tool calls版で変換されたMyNetDiaryデータベースからElasticsearchインデックスを作成
検索意図最適化に対応した設定
"""

import json
import sqlite3
from elasticsearch import Elasticsearch
from datetime import datetime

# Elasticsearch設定
ES_HOST = "localhost"
ES_PORT = 9200
INDEX_NAME = "mynetdiary_tool_calls_db"

def create_elasticsearch_index():
    """Elasticsearchインデックスを作成"""
    
    # Elasticsearchクライアント初期化
    es = Elasticsearch([f"http://{ES_HOST}:{ES_PORT}"])
    
    # 既存インデックスを削除
    if es.indices.exists(index=INDEX_NAME):
        print(f"🗑️ Deleting existing index: {INDEX_NAME}")
        es.indices.delete(index=INDEX_NAME)
    
    # インデックス設定（検索意図最適化対応）
    index_settings = {
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
                            "food_synonym_filter",
                            "food_stemmer"
                        ]
                    },
                    "food_exact_analyzer": {
                        "type": "custom", 
                        "tokenizer": "keyword",
                        "filter": ["lowercase"]
                    }
                },
                "filter": {
                    "food_synonym_filter": {
                        "type": "synonym",
                        "synonyms": [
                            "chickpeas,garbanzo beans,garbanzos",
                            "scallions,green onions,spring onions",
                            "cilantro,coriander leaves",
                            "bell pepper,sweet pepper",
                            "zucchini,courgette"
                        ]
                    },
                    "food_stemmer": {
                        "type": "stemmer",
                        "language": "light_english"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "long"},
                "original_name": {
                    "type": "text",
                    "analyzer": "food_name_analyzer",
                    "fields": {
                        "exact": {
                            "type": "text",
                            "analyzer": "food_exact_analyzer"
                        }
                    }
                },
                "search_name": {
                    "type": "text",
                    "analyzer": "food_name_analyzer",
                    "fields": {
                        "exact": {
                            "type": "text", 
                            "analyzer": "food_exact_analyzer"
                        },
                        "lemmatized": {
                            "type": "text",
                            "analyzer": "food_name_analyzer"
                        }
                    }
                },
                "description": {
                    "type": "text",
                    "analyzer": "food_name_analyzer",
                    "fields": {
                        "exact": {
                            "type": "text",
                            "analyzer": "food_exact_analyzer"
                        }
                    }
                },
                "nutrition": {
                    "properties": {
                        "calories": {"type": "float"},
                        "protein": {"type": "float"},
                        "fat": {"type": "float"},
                        "carbs": {"type": "float"}
                    }
                },
                "data_type": {"type": "keyword"},
                "source": {"type": "keyword"},
                "processing_method": {"type": "keyword"},
                "conversion_timestamp": {"type": "date"}
            }
        }
    }
    
    # インデックス作成
    print(f"🔧 Creating index: {INDEX_NAME}")
    es.indices.create(index=INDEX_NAME, body=index_settings)
    print("✅ Index created successfully")
    
    return es

def load_and_index_data(es):
    """変換済みデータをロードしてインデックス"""
    
    # JSONファイルからデータロード
    print("📂 Loading converted data...")
    with open('db/mynetdiary_converted_tool_calls.json', 'r', encoding='utf-8') as f:
        converted_data = json.load(f)
    
    print(f"✅ Loaded {len(converted_data)} items")
    
    # SQLiteデータベースに保存（検索システム用）
    print("💾 Creating SQLite database...")
    conn = sqlite3.connect('db/mynetdiary_tool_calls.db')
    cursor = conn.cursor()
    
    # テーブル作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nutrition_data (
            id INTEGER PRIMARY KEY,
            original_name TEXT NOT NULL,
            search_name TEXT NOT NULL,
            description TEXT,
            calories REAL,
            protein REAL,
            fat REAL,
            carbs REAL,
            data_type TEXT,
            source_db TEXT,
            processing_method TEXT,
            conversion_timestamp REAL
        )
    ''')
    
    # データ挿入とElasticsearchインデックス
    print("📤 Indexing data to Elasticsearch and SQLite...")
    indexed_count = 0
    batch_size = 100
    batch = []
    
    for item in converted_data:
        # Elasticsearch用ドキュメント準備
        doc = {
            "id": item["id"],
            "original_name": item["original_name"],
            "search_name": item["search_name"],
            "description": item["description"],
            "nutrition": item["nutrition"],
            "data_type": item["data_type"],
            "source": item["source"],
            "processing_method": item["processing_method"],
            "conversion_timestamp": datetime.fromtimestamp(item["conversion_timestamp"])
        }
        
        batch.append({
            "_index": INDEX_NAME,
            "_id": item["id"],
            "_source": doc
        })
        
        # SQLiteに挿入
        nutrition = item["nutrition"]
        cursor.execute('''
            INSERT OR REPLACE INTO nutrition_data 
            (id, original_name, search_name, description, calories, protein, fat, carbs, 
             data_type, source_db, processing_method, conversion_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item["id"],
            item["original_name"],
            item["search_name"],
            item["description"],
            nutrition.get("calories", 0),
            nutrition.get("protein", 0),
            nutrition.get("fat", 0),
            nutrition.get("carbs", 0),
            item["data_type"],
            item["source"],
            item["processing_method"],
            item["conversion_timestamp"]
        ))
        
        # バッチでElasticsearchに送信
        if len(batch) >= batch_size:
            from elasticsearch.helpers import bulk
            try:
                success, failed = bulk(es, batch, stats_only=True)
                indexed_count += success
                if failed > 0:
                    print(f"   ⚠️ {failed} documents failed in this batch")
                print(f"   📊 Progress: {indexed_count}/{len(converted_data)} ({indexed_count/len(converted_data)*100:.1f}%)")
            except Exception as e:
                print(f"   ❌ Batch error: {e}")
                # 個別に処理してみる
                for doc in batch:
                    try:
                        es.index(index=INDEX_NAME, id=doc["_id"], body=doc["_source"])
                        indexed_count += 1
                    except Exception as doc_error:
                        print(f"   🔴 Failed to index document {doc['_id']}: {doc_error}")
            batch = []
    
    # 残りのバッチを処理
    if batch:
        from elasticsearch.helpers import bulk
        try:
            success, failed = bulk(es, batch, stats_only=True)
            indexed_count += success
            if failed > 0:
                print(f"   ⚠️ {failed} documents failed in final batch")
        except Exception as e:
            print(f"   ❌ Final batch error: {e}")
            # 個別に処理してみる
            for doc in batch:
                try:
                    es.index(index=INDEX_NAME, id=doc["_id"], body=doc["_source"])
                    indexed_count += 1
                except Exception as doc_error:
                    print(f"   🔴 Failed to index document {doc['_id']}: {doc_error}")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully indexed {indexed_count} documents")
    print(f"💾 SQLite database saved: db/mynetdiary_tool_calls.db")
    
    return indexed_count

def test_search_functionality(es):
    """検索機能をテスト"""
    
    print("\n🔍 Testing search functionality...")
    
    test_queries = [
        "tomato",           # 一般検索（野菜のトマト）
        "tomato powder",    # 特定製品検索
        "coffee",           # 一般検索（基本コーヒー）
        "coffee powder",    # 特定製品検索
        "chicken breast",   # 肉類検索
        "beans"            # 豆類検索
    ]
    
    for query in test_queries:
        print(f"\n🔎 Testing query: '{query}'")
        
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["search_name^3", "description^1", "original_name^2"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "size": 5
        }
        
        result = es.search(index=INDEX_NAME, body=search_body)
        
        for i, hit in enumerate(result['hits']['hits'], 1):
            source = hit['_source']
            score = hit['_score']
            print(f"   {i}. [{score:.2f}] {source['search_name']} | {source['description']}")
            print(f"      Original: {source['original_name']}")

def main():
    """メイン処理"""
    
    print("🚀 MyNetDiary Tool Calls版 Elasticsearch インデックス作成")
    print("=" * 70)
    
    try:
        # Elasticsearchインデックス作成
        es = create_elasticsearch_index()
        
        # データロードとインデックス
        indexed_count = load_and_index_data(es)
        
        # 検索機能テスト
        test_search_functionality(es)
        
        print(f"\n🎉 完了! {indexed_count}件のデータがインデックスされました")
        print(f"📊 インデックス名: {INDEX_NAME}")
        print("🔍 検索意図最適化により、一般検索と特定製品検索が適切に分離されます")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 