#!/usr/bin/env python3
"""
栄養検索システム CLI ツール
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from typing import List

# パスの設定
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from core.search_engine import NutritionSearchEngine
from core.models import SearchQuery, BatchSearchQuery


def format_nutrition_info(nutrition):
    """栄養情報をフォーマット"""
    return f"Calories: {nutrition.calories or 0}, Protein: {nutrition.protein or 0}g, Carbs: {(nutrition.carbs or nutrition.carbohydrates or 0)}g, Fat: {nutrition.fat or 0}g"


def display_single_result(response, show_details=False):
    """単一検索結果を表示"""
    print(f"\n🔍 Search: '{response.query}'")
    
    if response.lemmatized_query:
        print(f"   Lemmatized: '{response.lemmatized_query}'")
    
    print(f"   Found: {response.total_found} results in {response.search_time_ms}ms")
    print("-" * 60)
    
    if not response.results:
        print("❌ No results found")
        return
    
    for i, result in enumerate(response.results, 1):
        print(f"{i:2d}. {result.name}")
        print(f"    Match: {result.match_type} | Score: {result.score:.2f} | Source: {result.source_db}")
        
        if show_details:
            print(f"    Nutrition: {format_nutrition_info(result.nutrition)}")
        
        print()


def display_batch_results(response, show_details=False):
    """バッチ検索結果を表示"""
    print(f"\n🎯 Batch Search Results")
    print(f"Total queries: {response.summary['total_queries']}")
    print(f"Successful searches: {response.summary['successful_searches']}")
    print(f"Total results: {response.summary['total_results']}")
    print(f"Match rate: {response.summary['match_rate_percent']:.1f}%")
    print(f"Total time: {response.total_search_time_ms}ms")
    print("=" * 60)
    
    for search_response in response.responses:
        display_single_result(search_response, show_details)


async def search_single(query: str, max_results: int = 10, show_details: bool = False):
    """単一検索実行"""
    engine = NutritionSearchEngine()
    
    search_query = SearchQuery(query=query, max_results=max_results)
    response = await engine.search(search_query)
    
    display_single_result(response, show_details)


async def search_batch(queries: List[str], max_results: int = 5, show_details: bool = False):
    """バッチ検索実行"""
    engine = NutritionSearchEngine()
    
    batch_query = BatchSearchQuery(queries=queries, max_results=max_results)
    response = await engine.batch_search(batch_query)
    
    display_batch_results(response, show_details)


async def interactive_search():
    """インタラクティブ検索モード"""
    engine = NutritionSearchEngine()
    
    print("🔍 Interactive Nutrition Search")
    print("Enter food names to search (type 'quit' to exit)")
    print("Commands: 'batch:<query1>,<query2>,...' for batch search")
    print("-" * 50)
    
    while True:
        try:
            query = input("\nSearch> ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            # バッチ検索
            if query.startswith('batch:'):
                queries = [q.strip() for q in query[6:].split(',')]
                batch_query = BatchSearchQuery(queries=queries, max_results=3)
                response = await engine.batch_search(batch_query)
                display_batch_results(response, show_details=True)
            else:
                # 単一検索
                search_query = SearchQuery(query=query, max_results=5)
                response = await engine.search(search_query)
                display_single_result(response, show_details=True)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(description='栄養検索システム CLI')
    parser.add_argument('query', nargs='?', help='検索クエリ')
    parser.add_argument('--batch', '-b', nargs='+', help='バッチ検索（複数クエリ）')
    parser.add_argument('--max-results', '-n', type=int, default=10, help='最大結果数')
    parser.add_argument('--details', '-d', action='store_true', help='詳細情報を表示')
    parser.add_argument('--interactive', '-i', action='store_true', help='インタラクティブモード')
    parser.add_argument('--json', '-j', action='store_true', help='JSON形式で出力')
    
    args = parser.parse_args()
    
    # 引数チェック
    if not args.query and not args.batch and not args.interactive:
        print("使用例:")
        print("  python cli_search.py 'tomatoes'")
        print("  python cli_search.py --batch 'chicken' 'rice' 'apple'")
        print("  python cli_search.py --interactive")
        sys.exit(1)
    
    # Elasticsearch接続チェック
    from utils.elasticsearch_client import get_elasticsearch_client
    es_client = get_elasticsearch_client()
    
    if not es_client.is_connected():
        print("❌ Elasticsearch not connected!")
        print("💡 Please ensure Elasticsearch is running")
        sys.exit(1)
    
    # 検索実行
    if args.interactive:
        asyncio.run(interactive_search())
    elif args.batch:
        asyncio.run(search_batch(args.batch, args.max_results, args.details))
    else:
        asyncio.run(search_single(args.query, args.max_results, args.details))


if __name__ == '__main__':
    main() 