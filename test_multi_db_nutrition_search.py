#!/usr/bin/env python3
"""
Multi-Database Nutrition Search Test v1.0

dbフォルダ内の3種類のデータベース（yazio、mynetdiary、eatthismuch）を対象に、
1つのqueryにつき各dbから上位3つの結果を取得するテストスクリプト
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import math

# API設定（新しいアーキテクチャ版）
BASE_URL = "http://localhost:8000/api/v1"

# テスト画像のパス
image_path = "test_images/food3.jpg"

# dbフォルダ内のデータベース
DB_CONFIGS = {
    "yazio": {
        "file_path": "db/yazio_db.json",
        "source": "YAZIO"
    },
    "mynetdiary": {
        "file_path": "db/mynetdiary_db.json", 
        "source": "MyNetDiary"
    },
    "eatthismuch": {
        "file_path": "db/eatthismuch_db.json",
        "source": "EatThisMuch"
    }
}

class MultiDbNutritionSearcher:
    """複数データベースから栄養情報を検索するクラス"""
    
    def __init__(self):
        self.databases = {}
        self.load_databases()
    
    def load_databases(self):
        """3つのデータベースを読み込み"""
        print("🔄 Loading databases...")
        
        for db_name, config in DB_CONFIGS.items():
            try:
                print(f"   Loading {db_name}...")
                with open(config["file_path"], 'r', encoding='utf-8') as f:
                    database = json.load(f)
                    self.databases[db_name] = {
                        "data": database,
                        "source": config["source"],
                        "count": len(database)
                    }
                    print(f"   ✅ {db_name}: {len(database)} items loaded")
            except Exception as e:
                print(f"   ❌ Failed to load {db_name}: {e}")
                self.databases[db_name] = {
                    "data": [],
                    "source": config["source"],
                    "count": 0
                }
        
        total_items = sum(db["count"] for db in self.databases.values())
        print(f"✅ Total items loaded: {total_items}")
    
    def search_single_database(self, query: str, db_name: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """単一データベースから検索"""
        if db_name not in self.databases:
            return []
        
        database = self.databases[db_name]["data"]
        query_lower = query.lower()
        scored_results = []
        
        for item in database:
            if 'search_name' not in item:
                continue
            
            item_name = item['search_name'].lower()
            score = self.calculate_match_score(query_lower, item_name)
            
            if score > 0.1:  # 最低閾値
                result = item.copy()
                result['_match_score'] = score
                result['_query'] = query
                result['_db_name'] = db_name
                scored_results.append(result)
        
        # スコアでソートして上位k件を返す
        scored_results.sort(key=lambda x: x['_match_score'], reverse=True)
        return scored_results[:top_k]
    
    def calculate_match_score(self, query: str, item_name: str) -> float:
        """マッチスコアを計算"""
        if query == item_name:
            return 1.0  # 完全一致
        elif query in item_name:
            if item_name.startswith(query):
                return 0.9  # 前方一致
            elif item_name.endswith(query):
                return 0.8  # 後方一致
            else:
                return 0.7  # 中間一致
        elif item_name in query:
            return 0.6  # 逆部分一致
        else:
            # 単語レベルの一致
            query_words = set(query.split())
            item_words = set(item_name.split())
            common_words = query_words & item_words
            if common_words:
                return len(common_words) / max(len(query_words), len(item_words)) * 0.5
        
        return 0.0
    
    def search_all_databases(self, query: str, top_k_per_db: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """全データベースから検索"""
        results = {}
        
        for db_name in self.databases.keys():
            db_results = self.search_single_database(query, db_name, top_k_per_db)
            results[db_name] = db_results
        
        return results
    
    def search_multiple_queries(self, queries: List[str], top_k_per_db: int = 3) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """複数のクエリについて全データベースから検索"""
        all_results = {}
        
        for query in queries:
            all_results[query] = self.search_all_databases(query, top_k_per_db)
        
        return all_results

def test_multi_db_nutrition_search():
    """マルチデータベース栄養検索をテスト"""
    
    print("=== Multi-Database Nutrition Search Test v1.0 ===")
    print(f"Using image: {image_path}")
    print("🔍 Testing search across 3 databases: YAZIO, MyNetDiary, EatThisMuch")
    
    try:
        # 完全分析エンドポイントを呼び出してPhase1結果を取得
        with open(image_path, "rb") as f:
            files = {"image": ("food3.jpg", f, "image/jpeg")}
            data = {"save_results": True}
            
            print("Starting complete analysis to get Phase1 results...")
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/meal-analyses/complete", files=files, data=data)
            end_time = time.time()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f}s")
        
        if response.status_code != 200:
            print("❌ Failed to get Phase1 results!")
            print(f"Error: {response.text}")
            return False
        
        result = response.json()
        analysis_id = result.get("analysis_id")
        print(f"Analysis ID: {analysis_id}")
        
        # Phase1結果から検索クエリを抽出
        phase1_result = result.get("phase1_result", {})
        dishes = phase1_result.get("dishes", [])
        
        all_queries = []
        dish_names = []
        ingredient_names = []
        
        for dish in dishes:
            dish_name = dish.get("dish_name")
            if dish_name:
                dish_names.append(dish_name)
                all_queries.append(dish_name)
            
            ingredients = dish.get("ingredients", [])
            for ingredient in ingredients:
                ingredient_name = ingredient.get("ingredient_name")
                if ingredient_name:
                    ingredient_names.append(ingredient_name)
                    all_queries.append(ingredient_name)
        
        # 重複を除去
        all_queries = list(set(all_queries))
        dish_names = list(set(dish_names))
        ingredient_names = list(set(ingredient_names))
        
        print(f"\n📊 Extracted Search Queries:")
        print(f"- Total dishes: {len(dish_names)}")
        print(f"- Total ingredients: {len(ingredient_names)}")
        print(f"- Total unique queries: {len(all_queries)}")
        
        if len(all_queries) == 0:
            print("❌ No search queries extracted from Phase1 results!")
            return False
        
        # マルチデータベース検索システムを初期化
        searcher = MultiDbNutritionSearcher()
        
        # 全クエリについてマルチデータベース検索を実行
        print(f"\n🔍 Starting multi-database search for {len(all_queries)} queries...")
        search_start_time = time.time()
        
        search_results = searcher.search_multiple_queries(all_queries, top_k_per_db=3)
        
        search_end_time = time.time()
        search_time = search_end_time - search_start_time
        
        print(f"✅ Multi-database search completed in {search_time:.2f}s")
        
        # 結果の分析
        total_matches = 0
        db_stats = {db_name: {"matches": 0, "queries_with_results": 0} for db_name in DB_CONFIGS.keys()}
        
        query_results_summary = []
        
        for query, db_results in search_results.items():
            query_summary = {
                "query": query,
                "type": "dish" if query in dish_names else "ingredient",
                "results_per_db": {}
            }
            
            for db_name, results in db_results.items():
                num_results = len(results)
                query_summary["results_per_db"][db_name] = num_results
                
                if num_results > 0:
                    db_stats[db_name]["queries_with_results"] += 1
                    db_stats[db_name]["matches"] += num_results
                    total_matches += num_results
            
            query_results_summary.append(query_summary)
        
        # 結果の表示
        print(f"\n📈 Multi-Database Search Results Summary:")
        print(f"- Total queries: {len(all_queries)}")
        print(f"- Total matches found: {total_matches}")
        print(f"- Average matches per query: {total_matches / len(all_queries):.1f}")
        print(f"- Search time: {search_time:.2f}s")
        print(f"- Average time per query: {search_time / len(all_queries):.3f}s")
        
        print(f"\n📊 Database Statistics:")
        for db_name, stats in db_stats.items():
            db_info = searcher.databases[db_name]
            coverage = (stats["queries_with_results"] / len(all_queries)) * 100
            print(f"- {db_name} ({db_info['source']}):")
            print(f"  Database size: {db_info['count']} items")
            print(f"  Queries with results: {stats['queries_with_results']}/{len(all_queries)} ({coverage:.1f}%)")
            print(f"  Total matches: {stats['matches']}")
            print(f"  Avg matches per successful query: {stats['matches'] / max(stats['queries_with_results'], 1):.1f}")
        
        print(f"\n🔍 Detailed Query Results:")
        for i, query_summary in enumerate(query_results_summary[:10], 1):  # 最初の10件のみ表示
            query = query_summary["query"]
            query_type = query_summary["type"]
            results_per_db = query_summary["results_per_db"]
            
            print(f"{i:2d}. '{query}' ({query_type})")
            
            for db_name, count in results_per_db.items():
                if count > 0:
                    # 上位結果の詳細を表示
                    top_result = search_results[query][db_name][0]
                    print(f"    {db_name}: {count} matches")
                    print(f"      Best: '{top_result['search_name']}' (score: {top_result['_match_score']:.3f})")
                    nutrition = top_result.get('nutrition', {})
                    if nutrition:
                        calories = nutrition.get('calories', 0)
                        protein = nutrition.get('protein', 0)
                        print(f"      Nutrition: {calories:.1f} kcal, {protein:.1f}g protein")
                else:
                    print(f"    {db_name}: No matches")
        
        if len(query_results_summary) > 10:
            print(f"    ... and {len(query_results_summary) - 10} more queries")
        
        # 詳細結果をファイルに保存
        save_detailed_results(analysis_id, search_results, query_results_summary, db_stats, searcher.databases)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during multi-database nutrition search: {e}")
        import traceback
        traceback.print_exc()
        return False

def save_detailed_results(analysis_id: str, search_results: Dict, query_summary: List, db_stats: Dict, db_info: Dict):
    """詳細な検索結果をファイルに保存"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"analysis_results/multi_db_search_{analysis_id}_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. 全検索結果をJSONで保存
    results_file = os.path.join(results_dir, "complete_search_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_id": analysis_id,
            "timestamp": timestamp,
            "search_results": search_results,
            "summary": {
                "total_queries": len(search_results),
                "database_stats": db_stats,
                "database_info": {db_name: {"count": info["count"], "source": info["source"]} 
                                for db_name, info in db_info.items()}
            }
        }, f, indent=2, ensure_ascii=False)
    
    # 2. 検索サマリーをマークダウンで保存
    summary_file = os.path.join(results_dir, "search_summary.md")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# Multi-Database Nutrition Search Results\n\n")
        f.write(f"**Analysis ID:** {analysis_id}\n")
        f.write(f"**Timestamp:** {timestamp}\n")
        f.write(f"**Total Queries:** {len(search_results)}\n\n")
        
        f.write(f"## Database Statistics\n\n")
        for db_name, stats in db_stats.items():
            db_inf = db_info[db_name]
            coverage = (stats["queries_with_results"] / len(search_results)) * 100
            f.write(f"### {db_name} ({db_inf['source']})\n")
            f.write(f"- Database size: {db_inf['count']} items\n")
            f.write(f"- Query coverage: {stats['queries_with_results']}/{len(search_results)} ({coverage:.1f}%)\n")
            f.write(f"- Total matches: {stats['matches']}\n")
            f.write(f"- Avg matches per successful query: {stats['matches'] / max(stats['queries_with_results'], 1):.1f}\n\n")
        
        f.write(f"## Query Results Detail\n\n")
        for i, query_summary in enumerate(query_summary, 1):
            query = query_summary["query"]
            query_type = query_summary["type"]
            results_per_db = query_summary["results_per_db"]
            
            f.write(f"### {i}. {query} ({query_type})\n")
            
            for db_name, count in results_per_db.items():
                if count > 0:
                    f.write(f"- **{db_name}**: {count} matches\n")
                    # 上位3件の詳細
                    for j, result in enumerate(search_results[query][db_name][:3], 1):
                        f.write(f"  {j}. {result['search_name']} (score: {result['_match_score']:.3f})\n")
                        nutrition = result.get('nutrition', {})
                        if nutrition:
                            calories = nutrition.get('calories', 0)
                            protein = nutrition.get('protein', 0)
                            fat = nutrition.get('fat', 0)
                            carbs = nutrition.get('carbs', 0)
                            f.write(f"     Nutrition (100g): {calories:.1f} kcal, P:{protein:.1f}g, F:{fat:.1f}g, C:{carbs:.1f}g\n")
                else:
                    f.write(f"- **{db_name}**: No matches\n")
            f.write(f"\n")
    
    print(f"\n💾 Detailed results saved to:")
    print(f"   📁 {results_dir}/")
    print(f"   📄 complete_search_results.json")
    print(f"   📄 search_summary.md")

if __name__ == "__main__":
    print("🚀 Starting Multi-Database Nutrition Search Test")
    success = test_multi_db_nutrition_search()
    
    if success:
        print("\n✅ Multi-database nutrition search test completed successfully!")
    else:
        print("\n❌ Multi-database nutrition search test failed!") 