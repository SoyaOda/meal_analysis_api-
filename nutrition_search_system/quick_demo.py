#!/usr/bin/env python3
"""
栄養検索システム クイックデモ
高度な検索機能をシンプルに体験できるデモスクリプト
"""

import sys
import asyncio
from pathlib import Path

# パスの設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core.search_engine import NutritionSearchEngine
from core.models import SearchQuery, BatchSearchQuery


def print_banner():
    """バナー表示"""
    print("🔍" + "=" * 58 + "🔍")
    print("🔍  Nutrition Search System - Quick Demo            🔍")
    print("🔍  高度なElasticsearch検索システムのデモンストレーション 🔍")
    print("🔍" + "=" * 58 + "🔍")
    print()


async def demo_single_search():
    """単一検索デモ"""
    print("📍 1. 単一検索デモ - 'tomatoes' で検索")
    print("-" * 50)
    
    engine = NutritionSearchEngine()
    query = SearchQuery(query="tomatoes", max_results=5)
    result = await engine.search(query)
    
    print(f"🔍 Query: '{result.query}'")
    if result.lemmatized_query:
        print(f"   Lemmatized: '{result.lemmatized_query}'")
    print(f"   Results: {result.total_found} found in {result.search_time_ms}ms")
    print()
    
    for i, item in enumerate(result.results, 1):
        print(f"{i}. {item.name}")
        print(f"   Match: {item.match_type} | Score: {item.score:.2f} | Source: {item.source_db}")
        nutrition = item.nutrition
        print(f"   Nutrition: {nutrition.calories or 0} cal, {nutrition.protein or 0}g protein, {(nutrition.carbs or nutrition.carbohydrates or 0)}g carbs")
        print()


async def demo_batch_search():
    """バッチ検索デモ"""
    print("📍 2. バッチ検索デモ - 複数の食材を同時検索")
    print("-" * 50)
    
    engine = NutritionSearchEngine()
    queries = ["chicken breast", "brown rice", "apple"]
    batch_query = BatchSearchQuery(queries=queries, max_results=3)
    result = await engine.batch_search(batch_query)
    
    print(f"🎯 Batch Search Results:")
    print(f"   Queries: {result.summary['total_queries']}")
    print(f"   Successful: {result.summary['successful_searches']}")
    print(f"   Total Results: {result.summary['total_results']}")
    print(f"   Match Rate: {result.summary['match_rate_percent']:.1f}%")
    print(f"   Total Time: {result.total_search_time_ms}ms")
    print()
    
    for search_result in result.responses:
        print(f"🔍 '{search_result.query}' → {len(search_result.results)} results")
        for item in search_result.results[:2]:  # 上位2件のみ表示
            print(f"   • {item.name} ({item.match_type}, score: {item.score:.2f})")
        print()


async def demo_lemmatization():
    """見出し語化デモ"""
    print("📍 3. 見出し語化機能デモ - 語の変化形に対応")
    print("-" * 50)
    
    engine = NutritionSearchEngine()
    
    # 複数形で検索
    test_queries = [
        ("tomatoes", "複数形 → 単数形"),
        ("apples", "複数形 → 単数形"),
        ("eggs", "複数形 → 単数形")
    ]
    
    for query_text, description in test_queries:
        query = SearchQuery(query=query_text, max_results=3)
        result = await engine.search(query)
        
        print(f"🔍 '{query_text}' ({description})")
        if result.lemmatized_query and result.lemmatized_query != query_text:
            print(f"   Lemmatized: '{result.lemmatized_query}'")
        print(f"   Found: {result.total_found} results")
        
        if result.results:
            best_match = result.results[0]
            print(f"   Best Match: {best_match.name} ({best_match.match_type})")
        print()


async def demo_advanced_features():
    """高度な機能デモ"""
    print("📍 4. 高度な検索機能デモ")
    print("-" * 50)
    
    engine = NutritionSearchEngine()
    
    # フィルタリング例
    query = SearchQuery(
        query="chicken",
        max_results=10,
        source_db_filter=["yazio"],  # YAZIOデータベースのみ
        min_score=1.0  # 最小スコア
    )
    
    result = await engine.search(query)
    print(f"🔍 Filtered Search: 'chicken' (YAZIO only, min_score=1.0)")
    print(f"   Results: {result.total_found} found")
    print(f"   Sources: {set(item.source_db for item in result.results)}")
    print()
    
    # 統計情報
    stats = engine.get_stats()
    print("📊 Engine Statistics:")
    print(f"   Total searches performed: {stats['total_searches']}")
    print(f"   Average response time: {stats['average_response_time_ms']:.1f}ms")
    print(f"   Database documents: {stats['total_documents']:,}")
    print()


async def main():
    """メインデモ実行"""
    print_banner()
    
    # Elasticsearch接続チェック
    from utils.elasticsearch_client import get_elasticsearch_client
    es_client = get_elasticsearch_client()
    
    if not es_client.is_connected():
        print("❌ Elasticsearch not connected!")
        print("💡 Please start Elasticsearch first:")
        print("   ../elasticsearch-8.10.4/bin/elasticsearch")
        return 1
    
    total_docs = es_client.get_total_documents()
    print(f"✅ Connected to Elasticsearch ({total_docs:,} documents available)")
    print()
    
    try:
        # デモ実行
        await demo_single_search()
        await demo_batch_search()
        await demo_lemmatization()
        await demo_advanced_features()
        
        print("🎉" + "=" * 58 + "🎉")
        print("🎉  Demo Complete! システムは正常に動作しています      🎉")
        print("🎉" + "=" * 58 + "🎉")
        print()
        print("次のステップ:")
        print("• Web Demo: python start_demo.py --mode flask")
        print("• API Server: python start_demo.py --mode fastapi")
        print("• CLI Tool: python cli_search.py --interactive")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 