#!/usr/bin/env python3
"""
高度なファジーマッチング用Elasticsearch Index Creation Script

仕様書に従った多層型検索カスケード用のインデックス設定:
- マルチフィールドマッピング
- カスタムアナライザー (normalized_sorted, edge_ngram)
- ファジー検索最適化
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


def create_fuzzy_index_mapping() -> Dict[str, Any]:
    """ファジーマッチング用Elasticsearchインデックスのマッピングを定義"""
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "standard_analyzer_with_synonyms": {
                        "type": "standard",
                        "stopwords": "_none_"
                    },
                    "normalized_sorted_analyzer": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "asciifolding",
                            "sort_tokens_filter"
                        ]
                    },
                    "edge_ngram_analyzer": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "asciifolding",
                            "edge_ngram_filter"
                        ]
                    }
                },
                "filter": {
                    "sort_tokens_filter": {
                        "type": "fingerprint",
                        "separator": " "
                    },
                    "edge_ngram_filter": {
                        "type": "edge_ngram",
                        "min_gram": 2,
                        "max_gram": 15
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {
                    "type": "keyword"
                },
                "search_name": {
                    "type": "text",
                    "analyzer": "standard_analyzer_with_synonyms",
                    "fields": {
                        "exact": {
                            "type": "keyword"
                        },
                        "normalized_sorted": {
                            "type": "text",
                            "analyzer": "normalized_sorted_analyzer"
                        },
                        "edge_ngram": {
                            "type": "text",
                            "analyzer": "edge_ngram_analyzer"
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
                "search_name_normalized": {
                    "type": "text",
                    "analyzer": "normalized_sorted_analyzer",
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
        }
    }


def normalize_and_sort_string(query_string: str) -> str:
    """正規化処理: 小文字化、句読点除去、単語のアルファベット順ソート"""
    if not query_string:
        return ""
    
    import re
    cleaned_string = re.sub(r'[^\w\s]', '', query_string.lower())
    sorted_words = sorted(cleaned_string.split())
    return " ".join(sorted_words)


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


def prepare_fuzzy_document(item: Dict[str, Any], source_db: str) -> Dict[str, Any]:
    """ファジーマッチング用ドキュメントをElasticsearch用に準備"""
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
    
    # 正規化されたsearch_nameを生成
    search_name_normalized = normalize_and_sort_string(search_name)
    
    doc = {
        "id": item.get("id", 0),
        "search_name": search_name,
        "search_name_lemmatized": search_name_lemmatized,
        "search_name_normalized": search_name_normalized,
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


def test_fuzzy_search_queries(es_client: Elasticsearch, index_name: str):
    """ファジーマッチング機能のテスト"""
    print("\n🧪 ファジーマッチング機能テスト")
    print("=" * 50)
    
    test_queries = [
        "Onion raw",
        "raw onion", 
        "onio raw",  # タイポ
        "Tortilla white flour",
        "white flour tortilla",  # 順序違い
        "tomat",  # 部分一致
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        
        # Tier 3相当のクエリ
        search_query = {
            "min_score": 3.0,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["search_name"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "prefix_length": 1,
                    "max_expansions": 10
                }
            },
            "size": 3
        }
        
        try:
            response = es_client.search(index=index_name, body=search_query)
            hits = response['hits']['hits']
            
            if hits:
                print(f"   ✅ Found {len(hits)} matches:")
                for hit in hits:
                    print(f"      - {hit['_source']['search_name']} (score: {hit['_score']:.2f})")
            else:
                print("   ❌ No matches found")
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")


def main():
    """メイン処理"""
    print("=== 高度なファジーマッチング用Elasticsearch Index Creation ===")
    
    # Elasticsearchに接続
    try:
        es_client = Elasticsearch(
            hosts=["http://localhost:9200"],
            timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        if not es_client.ping():
            print("❌ Elasticsearchに接続できません")
            return
        
        print("✅ Elasticsearch接続成功")
        
    except Exception as e:
        print(f"❌ Elasticsearch接続エラー: {e}")
        return
    
    index_name = "nutrition_fuzzy_search"
    
    # 既存のインデックスを削除
    if es_client.indices.exists(index=index_name):
        print(f"🗑️  既存のインデックス '{index_name}' を削除中...")
        es_client.indices.delete(index=index_name)
    
    # 新しいインデックスを作成
    print(f"🏗️  新しいインデックス '{index_name}' を作成中...")
    mapping = create_fuzzy_index_mapping()
    es_client.indices.create(index=index_name, body=mapping)
    print("✅ インデックス作成完了")
    
    # データベースを読み込み
    print("\n📚 データベース読み込み中...")
    databases = load_json_databases()
    
    # ドキュメントを準備
    print("\n📝 ドキュメント準備中...")
    all_documents = []
    
    for db_name, items in databases.items():
        for item in items:
            doc = prepare_fuzzy_document(item, db_name)
            all_documents.append(doc)
    
    print(f"✅ 準備完了: {len(all_documents)} documents")
    
    # バルクインデックス
    if all_documents:
        bulk_index_documents(es_client, index_name, all_documents)
        
        # インデックスをリフレッシュ
        print("🔄 インデックスをリフレッシュ中...")
        es_client.indices.refresh(index=index_name)
        
        # 統計情報を表示
        stats = es_client.indices.stats(index=index_name)
        doc_count = stats['indices'][index_name]['total']['docs']['count']
        print(f"📊 インデックス統計: {doc_count} documents indexed")
        
        # ファジーマッチング機能をテスト
        test_fuzzy_search_queries(es_client, index_name)
        
    else:
        print("⚠️  インデックスするドキュメントがありません")
    
    print("\n✅ ファジーマッチング用インデックス作成完了!")


if __name__ == "__main__":
    main() 