#!/usr/bin/env python3
"""
Comprehensive Nutrition Search Systems Test Script

READMEで紹介されている両方の検索システムをテスト:
1. MyNetDiary System (mynetdiary_list_support_db & mynetdiary_tool_calls_db)
2. Multi-Database System (usda_food_db)

test_mynetdiary_tool_calls_db.py と同様の詳細なテスト出力を提供
"""

import requests
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

# Elasticsearch直接アクセス用
ELASTICSEARCH_URL = "http://localhost:9200"

# テスト対象のインデックス（READMEから）
INDICES = {
    "mynetdiary_list_support": "mynetdiary_list_support_db",
    "mynetdiary_tool_calls": "mynetdiary_tool_calls_db",
    "usda_food": "usda_food_db",
    "mynetdiary_fixed": "mynetdiary_fixed_db"
}

def check_elasticsearch_connection() -> bool:
    """Elasticsearchの接続を確認"""
    try:
        response = requests.get(ELASTICSEARCH_URL)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Elasticsearch接続エラー: {e}")
        return False

def get_available_indices() -> List[str]:
    """使用可能なインデックスを取得"""
    try:
        response = requests.get(f"{ELASTICSEARCH_URL}/_cat/indices?format=json")
        if response.status_code == 200:
            indices_data = response.json()
            return [idx["index"] for idx in indices_data if not idx["index"].startswith(".")]
        return []
    except Exception as e:
        print(f"❌ インデックス一覧取得エラー: {e}")
        return []

def elasticsearch_search(index_name: str, query: str, size: int = 10) -> Dict[str, Any]:
    """Elasticsearchに直接クエリを実行"""

    # インデックスごとに最適化されたクエリ構成
    if "mynetdiary" in index_name:
        # MyNetDiaryシステム用（READMEの7段階検索戦略 + search_name_list配列対応）
        search_body = {
            "query": {
                "bool": {
                    "should": [
                        # 1. Exact Match (search_name_list配列要素) - Score: 15+
                        {"match_phrase": {"search_name_list": {"query": query, "boost": 15}}},
                        # 1b. Exact Match (search_name文字列) - Score: 15+ (fallback)
                        {"match_phrase": {"search_name": {"query": query, "boost": 15}}},

                        # 2. Exact Match (description) - Score: 12+
                        {"match_phrase": {"description": {"query": query, "boost": 12}}},

                        # 3. Phrase Match (search_name_list配列要素) - Score: 10+
                        {"match": {"search_name_list": {"query": query, "boost": 10}}},
                        # 3b. Phrase Match (search_name文字列) - Score: 10+ (fallback)
                        {"match": {"search_name": {"query": query, "boost": 10}}},

                        # 4. Phrase Match (description) - Score: 8+
                        {"match": {"description": {"query": query, "boost": 8}}},

                        # 5. Term Match (search_name_list要素の完全一致) - Score: 6+
                        {"term": {"search_name_list.keyword": {"value": query.lower(), "boost": 6}}},
                        # 5b. Term Match (search_name文字列の完全一致) - Score: 6+ (fallback)
                        {"term": {"search_name.keyword": {"value": query.lower(), "boost": 6}}},

                        # 6. Multi-field match (配列と文字列両対応) - Score: 4+
                        {"multi_match": {
                            "query": query,
                            "fields": ["search_name_list^3", "search_name^3", "description^2", "original_name"],
                            "boost": 4
                        }},

                        # 7. Fuzzy Match (search_name_list配列要素) - Score: 2+
                        {"fuzzy": {"search_name_list": {"value": query, "boost": 2}}},
                        # 7b. Fuzzy Match (search_name文字列) - Score: 2+ (fallback)
                        {"fuzzy": {"search_name": {"value": query, "boost": 2}}}
                    ]
                }
            },
            "size": size
        }
    else:
        # 基本的なマルチマッチクエリ（Multi-DBシステム用）
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "description^2", "category", "ingredients"]
                }
            },
            "size": size
        }

    try:
        response = requests.post(
            f"{ELASTICSEARCH_URL}/{index_name}/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(search_body)
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def format_nutrition_info(nutrition: Dict[str, Any]) -> str:
    """栄養情報を見やすい形式でフォーマット"""
    if not nutrition:
        return "栄養情報なし"

    # MyNetDiary形式
    if "calories" in nutrition:
        return f"🍽 {nutrition.get('calories', 0):.1f}kcal | 🥩 {nutrition.get('protein', 0):.1f}g | 🍞 {nutrition.get('carbs', 0):.1f}g | 🧈 {nutrition.get('fat', 0):.1f}g"

    # USDA形式（異なるフィールド名の可能性）
    elif "energy" in nutrition:
        return f"🍽 {nutrition.get('energy', 0):.1f}kcal | 🥩 {nutrition.get('protein', 0):.1f}g | 🍞 {nutrition.get('carbohydrate', 0):.1f}g | 🧈 {nutrition.get('fat', 0):.1f}g"

    # その他の形式
    else:
        key_nutrients = ["calories", "energy", "protein", "carbs", "carbohydrate", "fat", "fiber", "sodium"]
        found_nutrients = [f"{k}: {v}" for k, v in nutrition.items() if k in key_nutrients and v]
        return " | ".join(found_nutrients) if found_nutrients else "栄養情報形式不明"

def get_index_stats(index_name: str) -> Dict[str, Any]:
    """インデックスの統計情報を取得"""
    try:
        stats_response = requests.get(f"{ELASTICSEARCH_URL}/{index_name}/_stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            doc_count = stats.get("_all", {}).get("total", {}).get("docs", {}).get("count", 0)
            index_size = stats.get("_all", {}).get("total", {}).get("store", {}).get("size_in_bytes", 0)
            return {
                "doc_count": doc_count,
                "size_mb": round(index_size / (1024*1024), 2),
                "exists": True
            }
        else:
            return {"exists": False, "error": f"HTTP {stats_response.status_code}"}
    except Exception as e:
        return {"exists": False, "error": str(e)}

def test_single_query_on_index(index_name: str, query: str, expected_description: str = "") -> Dict[str, Any]:
    """単一インデックスで単一クエリのテストを実行"""
    print(f"\n{'─'*60}")
    print(f"🔍 インデックス: {index_name} | クエリ: '{query}'")
    if expected_description:
        print(f"📝 期待する結果: {expected_description}")

    # インデックスが存在するかチェック
    stats = get_index_stats(index_name)
    if not stats["exists"]:
        print(f"❌ インデックス '{index_name}' が存在しません: {stats.get('error', 'Unknown error')}")
        return {
            "index": index_name,
            "query": query,
            "exists": False,
            "error": stats.get("error", "Index not found"),
            "results": []
        }

    print(f"📊 インデックス統計: {stats['doc_count']:,} documents, {stats['size_mb']} MB")

    # Elasticsearch検索を実行
    result = elasticsearch_search(index_name, query, size=10)

    if "error" in result:
        print(f"❌ 検索エラー: {result['error']}")
        return {
            "index": index_name,
            "query": query,
            "exists": True,
            "error": result["error"],
            "results": []
        }

    hits = result.get("hits", {}).get("hits", [])
    total_hits = result.get("hits", {}).get("total", {}).get("value", 0)

    print(f"📋 検索結果: {total_hits} 件中 {len(hits)} 件表示")

    processed_results = []

    for i, hit in enumerate(hits, 1):
        source = hit["_source"]
        score = hit["_score"]

        # インデックスタイプに応じてフィールドを動的に取得
        if "mynetdiary" in index_name:
            name = source.get("search_name", source.get("name", "Unknown"))
            description = source.get("description", "No description")
            original_name = source.get("original_name", "")
            nutrition = source.get("nutrition", {})
            processing_method = source.get("processing_method", "Unknown")

            print(f"   🏆 #{i} (スコア: {score:.2f})")
            print(f"      🔸 検索名: '{name}'")
            print(f"      🔸 説明: '{description}'")
            if original_name:
                print(f"      🔸 元の名前: '{original_name}'")
            print(f"      🔸 栄養情報: {format_nutrition_info(nutrition)}")
            print(f"      🔸 処理方法: {processing_method}")

        else:
            # Multi-DBシステム用
            name = source.get("name", source.get("food_name", "Unknown"))
            description = source.get("description", source.get("category", "No description"))
            nutrition = source.get("nutrition", source.get("nutrients", {}))
            category = source.get("category", "")

            print(f"   🏆 #{i} (スコア: {score:.2f})")
            print(f"      🔸 名前: '{name}'")
            print(f"      🔸 説明: '{description}'")
            if category:
                print(f"      🔸 カテゴリ: '{category}'")
            print(f"      🔸 栄養情報: {format_nutrition_info(nutrition)}")

        processed_results.append({
            "rank": i,
            "score": score,
            "name": name,
            "description": description,
            "source": source  # 完全なソースデータも保存
        })

    return {
        "index": index_name,
        "query": query,
        "exists": True,
        "total_hits": total_hits,
        "displayed_results": len(hits),
        "results": processed_results
    }

def run_comprehensive_test() -> Dict[str, Any]:
    """すべてのシステムで包括的なテストを実行"""
    print("🚀 包括的な栄養検索システムテスト開始")
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Elasticsearch接続チェック
    if not check_elasticsearch_connection():
        return {"error": "Elasticsearch connection failed"}

    # 使用可能なインデックスを確認
    available_indices = get_available_indices()
    print(f"📋 利用可能なインデックス: {', '.join(available_indices)}")

    # テスト対象インデックスをフィルタ
    test_indices = {}
    for name, index_name in INDICES.items():
        if index_name in available_indices:
            test_indices[name] = index_name
            print(f"✅ テスト対象: {name} ({index_name})")
        else:
            print(f"❌ 利用不可: {name} ({index_name})")

    if not test_indices:
        print("❌ テスト可能なインデックスがありません")
        return {"error": "No testable indices found"}

    # READMEに基づいたテストクエリ（改良版）
    test_queries = [
        # 基本的な食材（READMEの例から）
        ("tomato", "トマト関連 - READMEの主要例"),
        ("chicken", "チキン関連 - READMEの主要例"),
        ("rice", "米関連 - READMEの主要例"),
        ("beans", "豆類関連 - READMEの主要例"),

        # 具体的な製品（READMEの例から）
        ("tomato powder", "トマトパウダー - 具体的検索例"),
        ("chicken breast", "チキンブレスト - 具体的検索例"),
        ("brown rice", "玄米 - 具体的検索例"),

        # 代替名のテスト（READMEで言及）
        ("chickpeas", "ひよこ豆 - 代替名テスト用"),
        ("garbanzo beans", "ガルバンゾ豆 - chickpeasの代替名"),

        # 複雑なクエリ（READMEで言及）
        ("stewed tomatoes", "煮込みトマト - 複雑クエリ例"),
        ("lean ground beef", "赤身ひき肉 - 複雑クエリ例"),

        # 一般的な検索（READMEの検索戦略テスト用）
        ("soup", "スープ - 一般的カテゴリ"),
        ("salad", "サラダ - 一般的カテゴリ"),
        ("pasta", "パスタ - 一般的カテゴリ"),

        # 大文字小文字・部分一致テスト
        ("TOMATO", "大文字でのトマト検索"),
        ("chick", "部分一致テスト")
    ]

    all_results = {}

    # 各インデックスでテストを実行
    for index_type, index_name in test_indices.items():
        print(f"\n{'='*80}")
        print(f"🗄️ インデックステスト: {index_type} ({index_name})")
        print(f"{'='*80}")

        index_results = []

        for query, description in test_queries:
            result = test_single_query_on_index(index_name, query, description)
            index_results.append(result)

        all_results[index_type] = {
            "index_name": index_name,
            "total_queries": len(test_queries),
            "queries_with_results": len([r for r in index_results if r.get("total_hits", 0) > 0]),
            "avg_results_per_query": sum(r.get("total_hits", 0) for r in index_results) / len(test_queries),
            "detailed_results": index_results
        }

    # 比較サマリー
    print(f"\n{'='*80}")
    print("📊 システム間比較サマリー")
    print(f"{'='*80}")

    for index_type, stats in all_results.items():
        if "error" not in stats:
            print(f"\n🔍 {index_type} ({stats['index_name']}):")
            print(f"   ✅ 結果ありクエリ: {stats['queries_with_results']}/{stats['total_queries']}")
            print(f"   📈 平均結果数: {stats['avg_results_per_query']:.1f}")

            # 上位結果の品質チェック
            top_results_with_good_scores = 0
            for result in stats['detailed_results']:
                if result.get('results') and len(result['results']) > 0:
                    if result['results'][0].get('score', 0) >= 5.0:  # 高スコア閾値
                        top_results_with_good_scores += 1

            print(f"   🎯 高品質結果クエリ: {top_results_with_good_scores}/{stats['total_queries']}")

    # 結果をファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"nutrition_search_systems_test_results_{timestamp}.json"

    test_summary = {
        "timestamp": timestamp,
        "tested_indices": test_indices,
        "total_queries_per_index": len(test_queries),
        "systems_comparison": all_results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_summary, f, ensure_ascii=False, indent=2)

    print(f"\n💾 詳細結果を保存: {output_file}")

    return test_summary

def check_all_indices_stats():
    """全インデックスの統計情報を確認"""
    print(f"\n🗄️ 全インデックス統計情報")
    print("="*80)

    available_indices = get_available_indices()

    for index_name in available_indices:
        if any(target in index_name for target in ["mynetdiary", "usda", "food"]):
            stats = get_index_stats(index_name)
            if stats["exists"]:
                print(f"📊 {index_name}: {stats['doc_count']:,} docs, {stats['size_mb']} MB")
            else:
                print(f"❌ {index_name}: {stats.get('error', 'Error')}")

if __name__ == "__main__":
    print("🔍 包括的栄養検索システムテストスイート")
    print("="*80)
    print("📖 READMEに基づいた MyNetDiary & Multi-Database システムテスト")
    print("🎯 test_mynetdiary_tool_calls_db.py と同様の詳細出力")
    print("="*80)

    # 全インデックス統計情報
    check_all_indices_stats()

    # 包括的テスト実行
    results = run_comprehensive_test()

    if "error" not in results:
        successful_systems = len([s for s in results["systems_comparison"].values() if "error" not in s])
        total_systems = len(results["systems_comparison"])
        print(f"\n🎉 テスト完了!")
        print(f"📊 {successful_systems}/{total_systems} システムでテスト成功")

        # 推奨システムの特定（READMEに基づく）
        if "mynetdiary_list_support" in results["systems_comparison"]:
            mynet_stats = results["systems_comparison"]["mynetdiary_list_support"]
            if "error" not in mynet_stats:
                print(f"🥇 推奨システム (MyNetDiary): {mynet_stats['queries_with_results']}/{mynet_stats['total_queries']} クエリで結果")
    else:
        print(f"\n❌ テスト失敗: {results['error']}")