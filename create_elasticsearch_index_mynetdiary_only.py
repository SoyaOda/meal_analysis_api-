#!/usr/bin/env python3
"""
MyNetDiary専用 Elasticsearch Index Creation Script

新しく修正されたMyNetDiaryデータベース（mynetdiary_final_complete.json）のみから
Elasticsearchインデックスを作成する
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
    """Elasticsearchインデックスのマッピングを定義（高度なテキストマッチング対応）"""
    return {
        "mappings": {
            "properties": {
                "id": {
                    "type": "keyword"
                },
                "search_name": {
                    "type": "text",
                    "analyzer": "meal_text_analyzer",  # カスタムアナライザーを使用
                    "search_analyzer": "meal_search_analyzer",  # 検索時は同義語フィルター付き
                    "fields": {
                        "exact": {
                            "type": "keyword"
                        },
                        "suggest": {
                            "type": "completion"
                        },
                        "standard": {
                            "type": "text",
                            "analyzer": "standard"
                        }
                    }
                },
                "search_name_lemmatized": {
                    "type": "text",
                    "analyzer": "meal_text_analyzer",
                    "search_analyzer": "meal_search_analyzer",
                    "fields": {
                        "exact": {
                            "type": "keyword"
                        }
                    }
                },
                "description": {
                    "type": "text",
                    "analyzer": "meal_text_analyzer",
                    "search_analyzer": "meal_search_analyzer"
                },
                "original_name": {
                    "type": "text",
                    "analyzer": "meal_text_analyzer",
                    "search_analyzer": "meal_search_analyzer",
                    "fields": {
                        "exact": {
                            "type": "keyword"
                        }
                    }
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
                },
                "processing_method": {
                    "type": "keyword"
                },
                "attempts": {
                    "type": "integer"
                }
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "char_filter": {
                    "punctuation_normalizer": {
                        "type": "mapping",
                        "mappings": [
                            "&=> and ",
                            ",=> ",
                            ".=> ",
                            "!=> ",
                            "?=> ",
                            ";=> ",
                            ":=> "
                        ]
                    }
                },
                "filter": {
                    "english_possessive_stemmer": {
                        "type": "stemmer",
                        "language": "possessive_english"
                    },
                    "english_stemmer": {
                        "type": "stemmer",
                        "language": "english"
                    },
                    "english_stopwords": {
                        "type": "stop",
                        "stopwords": [
                            "a", "an", "and", "are", "as", "at", "be", "but", "by",
                            "for", "if", "in", "into", "is", "it", "no", "not", "of",
                            "on", "or", "such", "that", "the", "their", "then", "there",
                            "these", "they", "this", "to", "was", "will", "with"
                        ]
                    },
                    "meal_synonym_filter": {
                        "type": "synonym_graph",
                        "synonyms": [
                            "chicken,poultry",
                            "beef,cow meat",
                            "pork,pig meat",
                            "fish,seafood",
                            "potato,potatoes",
                            "tomato,tomatoes",
                            "apple,apples",
                            "banana,bananas",
                            "orange,oranges",
                            "bread,toast",
                            "rice,grain",
                            "pasta,noodles,spaghetti,macaroni",
                            "salad,greens",
                            "soup,broth",
                            "milk,dairy",
                            "cheese,dairy",
                            "egg,eggs",
                            "oil,fat",
                            "butter,margarine",
                            "salt,sodium",
                            "pepper,spice",
                            "sugar,sweetener",
                            "onion,onions",
                            "garlic,seasoning",
                            "carrot,carrots",
                            "broccoli,vegetable",
                            "spinach,leafy green",
                            "lettuce,leafy green",
                            "ground beef,minced meat",
                            "french fries,fries,chips",
                            "ice cream,dessert",
                            "chocolate,cocoa",
                            "coffee,beverage",
                            "tea,beverage",
                            "water,beverage",
                            "juice,beverage"
                        ],
                        "updateable": True
                    },
                    "shingle_filter": {
                        "type": "shingle",
                        "min_shingle_size": 2,
                        "max_shingle_size": 3,
                        "output_unigrams": True
                    }
                },
                "analyzer": {
                    "meal_text_analyzer": {
                        "tokenizer": "standard",
                        "char_filter": ["punctuation_normalizer"],
                        "filter": [
                            "lowercase",
                            "english_possessive_stemmer",
                            "english_stopwords",
                            "english_stemmer"
                        ]
                    },
                    "meal_search_analyzer": {
                        "tokenizer": "standard",
                        "char_filter": ["punctuation_normalizer"],
                        "filter": [
                            "lowercase",
                            "english_possessive_stemmer",
                            "english_stopwords",
                            "meal_synonym_filter",
                            "english_stemmer"
                        ]
                    }
                }
            }
        }
    }


def load_mynetdiary_database() -> List[Dict[str, Any]]:
    """新しいMyNetDiaryデータベースを読み込み"""
    db_file = "db/mynetdiary_final_complete.json"
    
    if not os.path.exists(db_file):
        print(f"❌ Database file not found: {db_file}")
        return []
    
    try:
        print(f"Loading MyNetDiary database from {db_file}...")
        with open(db_file, 'r', encoding='utf-8') as f:
            database = json.load(f)
            print(f"✅ Loaded MyNetDiary: {len(database)} items")
            return database
    except Exception as e:
        print(f"❌ Error loading MyNetDiary database: {e}")
        return []


def prepare_document(item: Dict[str, Any]) -> Dict[str, Any]:
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
        "original_name": item.get("original_name"),
        "data_type": item.get("data_type", "unified_fixed"),
        "nutrition": item.get("nutrition", {}),
        "weight": item.get("weight"),
        "source_db": "mynetdiary_fixed",
        "processing_method": item.get("processing_method", ""),
        "attempts": item.get("attempts", 1)
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
                    "_id": f"mynetdiary_fixed_{doc['id']}"
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
    print("=== MyNetDiary専用 Elasticsearch Index Creation ===")
    
    # Elasticsearchクライアントの初期化
    print("\n1. Connecting to Elasticsearch...")
    es_client = Elasticsearch(["http://localhost:9200"])
    
    if not es_client.ping():
        print("❌ Cannot connect to Elasticsearch. Make sure it's running on localhost:9200")
        return False
    
    print("✅ Connected to Elasticsearch")
    
    # インデックス名
    index_name = "mynetdiary_fixed_db"
    
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
    
    # MyNetDiaryデータベースの読み込み
    print("\n4. Loading MyNetDiary database...")
    database = load_mynetdiary_database()
    
    if not database:
        print("❌ No data to index")
        return False
    
    # ドキュメントの準備
    print("\n5. Preparing documents for indexing...")
    all_documents = []
    
    for item in database:
        if "search_name" in item:  # 有効なアイテムのみ
            doc = prepare_document(item)
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
    print("\n8. Testing sample searches...")
    
    # 標準検索テスト
    test_queries = [
        "chicken",
        "tomatoes",
        "beans",
        "beef ribeye"
    ]
    
    for query in test_queries:
        print(f"\n   Testing search for '{query}':")
        
        # 検索クエリ
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "search_name^3",
                        "search_name_lemmatized^2", 
                        "description^1",
                        "original_name^1"
                    ],
                    "type": "best_fields"
                }
            },
            "size": 3
        }
        
        try:
            response = es_client.search(index=index_name, body=search_query)
            hits = response["hits"]["hits"]
            
            print(f"     Found {len(hits)} results:")
            for hit in hits:
                source = hit["_source"]
                print(f"     - {source['search_name']} ({source.get('description', 'N/A')}) score: {hit['_score']:.2f}")
                
        except Exception as e:
            print(f"     ❌ Search error: {e}")
    
    print(f"\n✅ MyNetDiary専用インデックス作成完了!")
    print(f"   インデックス名: {index_name}")
    print(f"   総ドキュメント数: {doc_count}")
    
    return True


if __name__ == "__main__":
    main() 