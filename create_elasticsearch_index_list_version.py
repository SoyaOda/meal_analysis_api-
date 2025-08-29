#!/usr/bin/env python3
"""
MyNetDiary リスト形式対応 Elasticsearch インデックス作成スクリプト

search_nameがリスト形式と文字列形式の両方に対応し、
リスト内の各項目を独立して検索対象にできるElasticsearchインデックスを作成。
"""

import json
import sqlite3
import time
from datetime import datetime
from elasticsearch import Elasticsearch
from typing import Dict, Any, List, Union

# 設定
INDEX_NAME = "mynetdiary_list_support_db"
ELASTICSEARCH_HOST = "http://localhost:9200"

def create_elasticsearch_index():
    """リスト形式対応のElasticsearchインデックスを作成"""
    
    # Elasticsearch接続
    es = Elasticsearch([ELASTICSEARCH_HOST])
    
    # 既存インデックス削除
    if es.indices.exists(index=INDEX_NAME):
        print(f"🗑️ Deleting existing index: {INDEX_NAME}")
        es.indices.delete(index=INDEX_NAME)
    
    # インデックス設定とマッピング
    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "tokenizer": {
                    "food_name_tokenizer": {
                        "type": "standard",
                        "max_token_length": 50
                    }
                },
                "filter": {
                    "food_name_stemmer": {
                        "type": "stemmer",
                        "language": "english"
                    },
                    "food_name_stop": {
                        "type": "stop",
                        "stopwords": ["and", "or", "with", "without", "in", "on", "at", "by"]
                    }
                },
                "analyzer": {
                    "food_name_analyzer": {
                        "type": "custom",
                        "tokenizer": "food_name_tokenizer",
                        "filter": ["lowercase", "food_name_stop", "food_name_stemmer"]
                    },
                    "food_exact_analyzer": {
                        "type": "custom",
                        "tokenizer": "keyword",
                        "filter": ["lowercase"]
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
                "search_name_list": {
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
                "search_name_type": {"type": "keyword"},
                "alternative_names_count": {"type": "integer"},
                "original_search_name": {"type": "text"},
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
                "conversion_timestamp": {"type": "date"},
                "list_conversion_timestamp": {"type": "date"}
            }
        }
    }
    
    # インデックス作成
    print(f"🔧 Creating index: {INDEX_NAME}")
    es.indices.create(index=INDEX_NAME, body=index_settings)
    print("✅ Index created successfully")
    
    return es

def process_search_name_field(search_name: Union[str, List[str]]) -> Dict[str, Any]:
    """search_nameフィールドを処理してElasticsearch用の形式に変換"""
    
    if isinstance(search_name, list):
        # リスト形式の場合
        return {
            "search_name": " ".join(search_name),  # 検索用に結合
            "search_name_list": search_name,       # 個別項目用
            "search_name_type": "list",
            "alternative_names_count": len(search_name)
        }
    else:
        # 文字列形式の場合
        return {
            "search_name": search_name,
            "search_name_list": [search_name],     # 統一的に扱うためリスト化
            "search_name_type": "string", 
            "alternative_names_count": 1
        }

def load_and_index_data(es):
    """リスト形式データをロードしてインデックス"""
    
    # JSONファイルからデータロード
    print("📂 Loading list format data...")
    with open('db/mynetdiary_converted_tool_calls_list.json', 'r', encoding='utf-8') as f:
        converted_data = json.load(f)
    
    print(f"✅ Loaded {len(converted_data)} items")
    
    # 統計情報
    list_entries = sum(1 for item in converted_data if isinstance(item.get('search_name'), list))
    string_entries = len(converted_data) - list_entries
    
    print(f"📊 Data distribution:")
    print(f"   📝 List format entries: {list_entries}")
    print(f"   📄 String format entries: {string_entries}")
    
    # SQLiteデータベースに保存（検索システム用）
    print("💾 Creating SQLite database...")
    conn = sqlite3.connect('db/mynetdiary_list_support.db')
    cursor = conn.cursor()
    
    # テーブル作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nutrition_data (
            id TEXT PRIMARY KEY,
            original_name TEXT NOT NULL,
            search_name TEXT NOT NULL,
            search_name_list TEXT,
            search_name_type TEXT,
            alternative_names_count INTEGER,
            original_search_name TEXT,
            description TEXT,
            calories REAL,
            protein REAL,
            fat REAL,
            carbs REAL,
            data_type TEXT,
            source_db TEXT,
            processing_method TEXT,
            conversion_timestamp REAL,
            list_conversion_timestamp REAL
        )
    ''')
    
    # データ挿入とElasticsearchインデックス
    print("📤 Indexing data to Elasticsearch and SQLite...")
    indexed_count = 0
    batch_size = 100
    batch = []
    
    for item in converted_data:
        # search_nameフィールドを処理
        search_name_data = process_search_name_field(item.get('search_name', ''))
        
        # Elasticsearch用ドキュメント準備
        doc = {
            "id": item["id"],
            "original_name": item["original_name"],
            "description": item.get("description", ""),
            "nutrition": item["nutrition"],
            "data_type": item["data_type"],
            "source": item["source"],
            "processing_method": item["processing_method"],
            "conversion_timestamp": datetime.fromtimestamp(item["conversion_timestamp"])
        }
        
        # search_name関連フィールドを追加
        doc.update(search_name_data)
        
        # リスト変換のタイムスタンプがある場合は追加
        if "list_conversion_timestamp" in item:
            doc["list_conversion_timestamp"] = datetime.fromtimestamp(item["list_conversion_timestamp"])
        
        # 元のsearch_nameを保存（リスト形式の場合）
        if "original_search_name" in item:
            doc["original_search_name"] = item["original_search_name"]
        
        batch.append({
            "_index": INDEX_NAME,
            "_id": item["id"],
            "_source": doc
        })
        
        # SQLiteに挿入
        nutrition = item["nutrition"]
        cursor.execute('''
            INSERT OR REPLACE INTO nutrition_data 
            (id, original_name, search_name, search_name_list, search_name_type, 
             alternative_names_count, original_search_name, description, 
             calories, protein, fat, carbs, data_type, source_db, processing_method, 
             conversion_timestamp, list_conversion_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(item["id"]),
            item["original_name"],
            doc["search_name"],
            json.dumps(doc["search_name_list"]),
            doc["search_name_type"],
            doc["alternative_names_count"],
            doc.get("original_search_name"),
            item.get("description", ""),
            nutrition.get("calories", 0),
            nutrition.get("protein", 0),
            nutrition.get("fat", 0),
            nutrition.get("carbs", 0),
            item["data_type"],
            item["source"],
            item["processing_method"],
            item["conversion_timestamp"],
            item.get("list_conversion_timestamp")
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
    print(f"💾 SQLite database saved: db/mynetdiary_list_support.db")
    
    return indexed_count

def test_list_search_functionality(es):
    """リスト対応検索機能をテスト"""
    
    print("\n🔍 Testing list-aware search functionality...")
    
    test_queries = [
        "chickpeas",        # リスト項目の1つ目
        "garbanzo beans",   # リスト項目の2つ目  
        "cannellini",       # リスト項目の1つ目
        "white kidney beans", # リスト項目の2つ目
        "tomato",           # 一般検索
        "coffee powder",    # 特定製品検索
    ]
    
    for query in test_queries:
        print(f"\n🔎 Testing query: '{query}'")
        
        # 両方のフィールドを検索対象に
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        # 統合されたsearch_nameフィールド検索
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["search_name^3", "search_name.exact^4"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        },
                        # 個別のリスト項目検索
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["search_name_list^5", "search_name_list.exact^6"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            },
            "size": 5
        }
        
        result = es.search(index=INDEX_NAME, body=search_body)
        
        for i, hit in enumerate(result['hits']['hits'], 1):
            source = hit['_source']
            score = hit['_score']
            search_name_type = source.get('search_name_type', 'unknown')
            
            if search_name_type == 'list':
                # リスト形式の場合
                alt_count = source.get('alternative_names_count', 0)
                original_search = source.get('original_search_name', 'N/A')
                search_names = source.get('search_name_list', [])
                print(f"   {i}. [{score:.2f}] {search_names} (List: {alt_count} names)")
                print(f"      Original: {source['original_name']}")
                print(f"      From: {original_search}")
            else:
                # 文字列形式の場合
                print(f"   {i}. [{score:.2f}] {source['search_name']} | {source.get('description', '')}")
                print(f"      Original: {source['original_name']}")

def main():
    """メイン処理"""
    
    print("🚀 MyNetDiary リスト形式対応 Elasticsearch インデックス作成")
    print("=" * 70)
    
    try:
        # Elasticsearchインデックス作成
        es = create_elasticsearch_index()
        
        # データロードとインデックス
        indexed_count = load_and_index_data(es)
        
        # 検索機能テスト
        test_list_search_functionality(es)
        
        print(f"\n🎉 完了! {indexed_count}件のデータがインデックスされました")
        print(f"📊 インデックス名: {INDEX_NAME}")
        print(f"🔍 リスト形式対応: search_nameリスト内の各項目が独立して検索可能")
        print(f"💡 アルゴリズム: リスト内で最高スコアの項目がそのエントリのスコア")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 