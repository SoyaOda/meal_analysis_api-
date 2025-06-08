#!/usr/bin/env python3
"""
Elasticsearch v2.0 統合テスト

build_nutrition_db_v2.py → Elasticsearch indexing → search_service.py の完全パイプラインテスト
"""

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path

# app_v2の検索サービスをインポート
try:
    from app_v2.elasticsearch.search_service import food_search_service, SearchQuery, NutritionTarget
    from app_v2.elasticsearch.client import es_client
    from app_v2.elasticsearch.config import es_config
    ELASTICSEARCH_V2_AVAILABLE = True
    print("✅ app_v2 Elasticsearch services imported successfully")
except ImportError as e:
    ELASTICSEARCH_V2_AVAILABLE = False
    print(f"❌ app_v2 Elasticsearch services not available: {e}")

async def check_elasticsearch_connection():
    """Elasticsearchへの接続確認"""
    print("\n=== Elasticsearch Connection Test ===")
    
    if not ELASTICSEARCH_V2_AVAILABLE:
        print("❌ Elasticsearch services not available")
        return False
    
    try:
        # クラスター情報取得
        cluster_info = await es_client.get_cluster_info()
        
        if cluster_info:
            print("✅ Elasticsearch cluster connection successful")
            print(f"- Cluster name: {cluster_info.get('cluster_name', 'unknown')}")
            print(f"- Version: {cluster_info.get('version', {}).get('number', 'unknown')}")
            return True
        else:
            print("❌ Failed to get cluster info")
            return False
            
    except Exception as e:
        print(f"❌ Elasticsearch connection failed: {e}")
        return False

async def check_food_nutrition_index():
    """food_nutrition_v2インデックスの状態確認"""
    print(f"\n=== Index Status Check: {es_config.food_nutrition_index} ===")
    
    if not ELASTICSEARCH_V2_AVAILABLE:
        print("❌ Elasticsearch services not available")
        return False, 0
    
    try:
        # インデックス存在確認
        index_exists = await es_client.index_exists(es_config.food_nutrition_index)
        
        if not index_exists:
            print(f"❌ Index '{es_config.food_nutrition_index}' does not exist")
            print("💡 Run the indexing process first")
            return False, 0
        
        print(f"✅ Index '{es_config.food_nutrition_index}' exists")
        
        # インデックス統計取得
        stats = await es_client.get_index_stats(es_config.food_nutrition_index)
        
        if stats:
            doc_count = stats.get('total', {}).get('docs', {}).get('count', 0)
            store_size = stats.get('total', {}).get('store', {}).get('size_in_bytes', 0)
            store_size_mb = store_size / (1024 * 1024)
            
            print(f"📊 Index Statistics:")
            print(f"- Document count: {doc_count:,}")
            print(f"- Store size: {store_size_mb:.2f} MB")
            
            return True, doc_count
        else:
            print("⚠️ Could not retrieve index statistics")
            return True, 0
            
    except Exception as e:
        print(f"❌ Error checking index: {e}")
        return False, 0

def check_nutrition_db_v2_files():
    """nutrition_db_v2ディレクトリのファイル確認"""
    print("\n=== Nutrition DB v2.0 Files Check ===")
    
    db_path = Path("nutrition_db_v2")
    
    if not db_path.exists():
        print(f"❌ Directory '{db_path}' does not exist")
        print("💡 Run 'python build_nutrition_db_v2.py' first")
        return False, {}
    
    print(f"✅ Directory '{db_path}' exists")
    
    # 期待されるファイル
    expected_files = [
        "dish_db_v2.json",
        "ingredient_db_v2.json", 
        "branded_db_v2.json",
        "unified_nutrition_db_v2.json"
    ]
    
    file_stats = {}
    
    for filename in expected_files:
        file_path = db_path / filename
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_stats[filename] = len(data)
                    print(f"✅ {filename}: {len(data):,} items")
            except Exception as e:
                print(f"❌ {filename}: Error reading - {e}")
                file_stats[filename] = 0
        else:
            print(f"❌ {filename}: Not found")
            file_stats[filename] = 0
    
    total_items = sum(file_stats.values())
    print(f"\n📊 Total items in v2 database: {total_items:,}")
    
    return total_items > 0, file_stats

def run_nutrition_db_v2_build():
    """nutrition_db_v2の構築を実行"""
    print("\n=== Building Nutrition DB v2.0 ===")
    
    try:
        print("🏗️ Running build_nutrition_db_v2.py...")
        result = subprocess.run(
            ["python", "build_nutrition_db_v2.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5分タイムアウト
        )
        
        if result.returncode == 0:
            print("✅ Nutrition DB v2.0 build completed successfully")
            print("📋 Build output:")
            print(result.stdout)
            return True
        else:
            print("❌ Nutrition DB v2.0 build failed")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Nutrition DB v2.0 build timed out")
        return False
    except Exception as e:
        print(f"❌ Error running build: {e}")
        return False

async def run_basic_search_tests():
    """基本的な検索テストを実行"""
    print("\n=== Basic Search Tests ===")
    
    if not ELASTICSEARCH_V2_AVAILABLE:
        print("❌ Elasticsearch services not available")
        return False
    
    # テストクエリ
    test_queries = ["potato", "apple", "chicken", "rice"]
    
    all_passed = True
    
    for query_term in test_queries:
        print(f"\n🔍 Testing search: '{query_term}'")
        
        try:
            query = SearchQuery(elasticsearch_query_terms=query_term)
            results = await food_search_service.search_foods(query, size=3)
            
            if results:
                print(f"✅ Found {len(results)} results")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result.food_name} | Score: {result.score:.2f}")
                    if result.description:
                        print(f"     Description: {result.description}")
            else:
                print(f"❌ No results found for '{query_term}'")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Search failed for '{query_term}': {e}")
            all_passed = False
    
    return all_passed

async def run_two_stage_search_validation():
    """段階的検索戦略の動作確認"""
    print("\n=== Two-Stage Search Strategy Validation ===")
    
    if not ELASTICSEARCH_V2_AVAILABLE:
        print("❌ Elasticsearch services not available")
        return False
    
    # potatoクエリで詳細検証
    query = SearchQuery(elasticsearch_query_terms="potato")
    results = await food_search_service.search_foods(query, size=10)
    
    if not results:
        print("❌ No results for potato search")
        return False
    
    print("Top 10 results for 'potato':")
    
    raw_ingredient_rank = None
    
    for i, result in enumerate(results, 1):
        # food_nameにpotatoが含まれ、descriptionにrawが含まれるかチェック
        name_match = "potato" in result.food_name.lower()
        raw_indicator = any(keyword in (result.description or '').lower() 
                           for keyword in ['raw', 'flesh', 'skin'])
        
        status = ""
        if name_match and raw_indicator:
            status = "✅ IDEAL"
            if raw_ingredient_rank is None:
                raw_ingredient_rank = i
        elif name_match:
            status = "✅ GOOD"
        else:
            status = "❌ POOR"
        
        print(f"{i:2}. {status} {result.food_name}")
        if result.description:
            print(f"    Description: {result.description}")
        print(f"    Score: {result.score:.2f} | Type: {result.data_type}")
    
    # 評価
    if raw_ingredient_rank is not None:
        print(f"\n📊 Evaluation:")
        print(f"✅ Raw potato ingredient found at rank #{raw_ingredient_rank}")
        if raw_ingredient_rank <= 3:
            print("🎯 EXCELLENT: Raw ingredient in top 3")
            return True
        elif raw_ingredient_rank <= 5:
            print("🎯 GOOD: Raw ingredient in top 5")
            return True
        else:
            print("🎯 FAIR: Raw ingredient found but not in top 5")
            return False
    else:
        print("❌ No raw potato ingredient found in top 10")
        return False

async def main():
    """メイン統合テスト"""
    print("🎯 Elasticsearch v2.0 Integration Test")
    print("=" * 60)
    
    # 1. nutrition_db_v2ファイル確認
    db_files_exist, file_stats = check_nutrition_db_v2_files()
    
    if not db_files_exist:
        print("\n🏗️ Building nutrition database v2.0...")
        build_success = run_nutrition_db_v2_build()
        
        if not build_success:
            print("❌ Cannot proceed without nutrition database")
            return False
            
        # 再確認
        db_files_exist, file_stats = check_nutrition_db_v2_files()
        
        if not db_files_exist:
            print("❌ Database build completed but files not found")
            return False
    
    # 2. Elasticsearch接続確認
    connection_ok = await check_elasticsearch_connection()
    
    if not connection_ok:
        print("❌ Cannot proceed without Elasticsearch connection")
        return False
    
    # 3. インデックス確認
    index_ok, doc_count = await check_food_nutrition_index()
    
    if not index_ok or doc_count == 0:
        print(f"\n💡 Index not ready. Expected documents: {sum(file_stats.values()):,}")
        print("💡 You may need to run the indexing process")
        print("💡 Check if elasticsearch indexing script exists and run it")
        # インデックスがない場合でも基本テストは続行
    
    # 4. 基本検索テスト
    if index_ok and doc_count > 0:
        basic_tests_passed = await run_basic_search_tests()
        
        if basic_tests_passed:
            print("\n✅ Basic search tests passed")
        else:
            print("\n❌ Some basic search tests failed")
        
        # 5. 段階的検索戦略テスト
        two_stage_passed = await run_two_stage_search_validation()
        
        if two_stage_passed:
            print("\n✅ Two-stage search strategy working correctly")
        else:
            print("\n❌ Two-stage search strategy needs improvement")
        
        # 総合評価
        overall_success = basic_tests_passed and two_stage_passed
        
        print(f"\n🏆 Integration Test Results:")
        print(f"- Database files: {'✅' if db_files_exist else '❌'}")
        print(f"- Elasticsearch connection: {'✅' if connection_ok else '❌'}")
        print(f"- Index ready: {'✅' if index_ok and doc_count > 0 else '❌'}")
        print(f"- Basic search: {'✅' if basic_tests_passed else '❌'}")
        print(f"- Two-stage strategy: {'✅' if two_stage_passed else '❌'}")
        print(f"\n🎯 Overall Status: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")
        
        return overall_success
    else:
        print(f"\n⚠️ Elasticsearch index not ready for testing")
        print(f"- Database files available: {'✅' if db_files_exist else '❌'}")
        print(f"- Connection: {'✅' if connection_ok else '❌'}")
        print(f"- Index needs to be created and populated")
        return False

if __name__ == "__main__":
    asyncio.run(main()) 