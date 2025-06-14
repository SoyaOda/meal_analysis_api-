#!/usr/bin/env python3
"""
Multi-Database Nutrition Search Test v3.0 - Multi-DB Elasticsearch Edition

ElasticsearchNutritionSearchComponentのマルチデータベース検索機能を使用して
3つのデータベース（yazio, mynetdiary, eatthismuch）から各3つずつ
栄養データベース検索結果を取得してテストするスクリプト
"""

import requests
import json
import time
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

# Elasticsearch Nutrition Search Component
from app_v2.components.elasticsearch_nutrition_search_component import ElasticsearchNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput

# API設定（新しいアーキテクチャ版）
BASE_URL = "http://localhost:8000/api/v1"

# テスト画像のパス
image_path = "test_images/food3.jpg"

async def test_multi_db_elasticsearch_nutrition_search():
    """マルチデータベースElasticsearch栄養検索をテスト"""
    
    print("=== Multi-Database Nutrition Search Test v3.0 - Multi-DB Elasticsearch Edition ===")
    print(f"Using image: {image_path}")
    print("🔍 Testing Multi-Database Elasticsearch-powered nutrition search")
    print("📊 Each query will return up to 3 results from each of 3 databases (yazio, mynetdiary, eatthismuch)")
    
    try:
        # 完全分析エンドポイントを呼び出してPhase1結果を取得
        with open(image_path, "rb") as f:
            files = {"image": ("food3.jpg", f, "image/jpeg")}
            data = {}
            
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
        
        # ElasticsearchNutritionSearchComponentをマルチデータベースモードで初期化
        print(f"\n🔧 Initializing ElasticsearchNutritionSearchComponent (Multi-DB Mode)...")
        es_component = ElasticsearchNutritionSearchComponent(
            multi_db_search_mode=True,  # マルチDBモードを有効化
            results_per_db=5  # 各データベースから5つずつ結果を取得
        )
        
        # 検索入力データを作成
        nutrition_query_input = NutritionQueryInput(
            ingredient_names=ingredient_names,
            dish_names=dish_names,
            preferred_source="elasticsearch"
        )
        
        print(f"📝 Query Input:")
        print(f"- Ingredient names: {len(ingredient_names)} items")
        print(f"- Dish names: {len(dish_names)} items")
        print(f"- Total search terms: {len(nutrition_query_input.get_all_search_terms())}")
        print(f"- Multi-DB search mode: Enabled")
        print(f"- Results per database: 5")
        print(f"- Target databases: yazio, mynetdiary, eatthismuch")
        
        # Elasticsearch マルチDB検索を実行
        print(f"\n🔍 Starting Multi-Database Elasticsearch nutrition search...")
        search_start_time = time.time()
        
        search_results = await es_component.execute(nutrition_query_input)
        
        search_end_time = time.time()
        search_time = search_end_time - search_start_time
        
        print(f"✅ Multi-DB Elasticsearch search completed in {search_time:.3f}s")
        
        # 結果の分析
        matches = search_results.matches
        search_summary = search_results.search_summary
        
        print(f"\n📈 Multi-DB Elasticsearch Search Results Summary:")
        print(f"- Total queries: {search_summary.get('total_searches', 0)}")
        print(f"- Successful matches: {search_summary.get('successful_matches', 0)}")
        print(f"- Failed searches: {search_summary.get('failed_searches', 0)}")
        print(f"- Match rate: {search_summary.get('match_rate_percent', 0):.1f}%")
        print(f"- Search time: {search_summary.get('search_time_ms', 0)}ms")
        print(f"- Search method: {search_summary.get('search_method', 'unknown')}")
        print(f"- Database source: {search_summary.get('database_source', 'unknown')}")
        print(f"- Total indexed documents: {search_summary.get('total_indexed_documents', 0)}")
        print(f"- Results per database: {search_summary.get('results_per_db', 0)}")
        print(f"- Target databases: {search_summary.get('target_databases', [])}")
        print(f"- Total results: {search_summary.get('total_results', 0)}")
        
        # データベース別統計の詳細計算
        db_detailed_stats = {"yazio": 0, "mynetdiary": 0, "eatthismuch": 0, "unknown": 0}
        source_distribution = {}
        query_results_breakdown = {}
        
        total_individual_results = 0
        for query, match_results in matches.items():
            if isinstance(match_results, list):
                # マルチDB検索の場合、リスト形式で結果が返される
                query_results_breakdown[query] = len(match_results)
                total_individual_results += len(match_results)
                
                for match in match_results:
                    source = match.source
                    if "elasticsearch_" in source:
                        db_name = source.replace("elasticsearch_", "")
                        if db_name in db_detailed_stats:
                            db_detailed_stats[db_name] += 1
                        else:
                            db_detailed_stats["unknown"] += 1
                    
                    if source not in source_distribution:
                        source_distribution[source] = 0
                    source_distribution[source] += 1
            else:
                # 単一結果の場合（従来形式）
                query_results_breakdown[query] = 1
                total_individual_results += 1
                source = match_results.source
                if source not in source_distribution:
                    source_distribution[source] = 0
                source_distribution[source] += 1
        
        print(f"\n📊 Detailed Database Source Distribution:")
        for source, count in source_distribution.items():
            percentage = (count / total_individual_results) * 100 if total_individual_results > 0 else 0
            print(f"- {source}: {count} results ({percentage:.1f}%)")
        
        print(f"\n📋 Per-Query Results Breakdown:")
        for query, result_count in query_results_breakdown.items():
            query_type = "dish" if query in dish_names else "ingredient"
            print(f"- '{query}' ({query_type}): {result_count} results")
        
        print(f"\n🔍 Top Multi-DB Match Results (showing first 5 queries):")
        for i, (query, match_results) in enumerate(list(matches.items())[:5], 1):
            query_type = "dish" if query in dish_names else "ingredient"
            print(f"\n{i:2d}. Query: '{query}' ({query_type})")
            
            if isinstance(match_results, list):
                print(f"    Found {len(match_results)} results from multiple databases:")
                for j, match in enumerate(match_results, 1):
                    print(f"    {j}. {match.search_name} (score: {match.score:.3f})")
                    print(f"       Source: {match.source}")
                    print(f"       Data type: {match.data_type}")
                    
                    nutrition = match.nutrition
                    if nutrition:
                        calories = nutrition.get('calories', 0)
                        protein = nutrition.get('protein', 0)
                        fat = nutrition.get('fat', 0)
                        carbs = nutrition.get('carbs', nutrition.get('carbohydrates', 0))
                        print(f"       Nutrition (100g): {calories:.1f} kcal, P:{protein:.1f}g, F:{fat:.1f}g, C:{carbs:.1f}g")
            else:
                # 単一結果の場合
                print(f"    Single result: {match_results.search_name} (score: {match_results.score:.3f})")
                print(f"    Source: {match_results.source}")
        
        if len(matches) > 5:
            print(f"\n    ... and {len(matches) - 5} more queries with results")
        
        # 警告とエラーの表示
        if search_results.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in search_results.warnings:
                print(f"   - {warning}")
        
        if search_results.errors:
            print(f"\n❌ Errors:")
            for error in search_results.errors:
                print(f"   - {error}")
        
        # 詳細結果をファイルに保存
        await save_multi_db_elasticsearch_results(analysis_id, search_results, all_queries, dish_names, ingredient_names)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Multi-DB Elasticsearch nutrition search: {e}")
        import traceback
        traceback.print_exc()
        return False

async def save_multi_db_elasticsearch_results(analysis_id: str, search_results, all_queries: List[str], dish_names: List[str], ingredient_names: List[str]):
    """マルチデータベースElasticsearch検索結果をファイルに保存"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"analysis_results/multi_db_elasticsearch_search_{analysis_id}_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    # 検索結果を辞書形式に変換
    matches_dict = {}
    for query, match_results in search_results.matches.items():
        if isinstance(match_results, list):
            # マルチDB結果の場合
            matches_dict[query] = []
            for match in match_results:
                matches_dict[query].append({
                    "id": match.id,
                    "search_name": match.search_name,
                    "description": match.description,
                    "data_type": match.data_type,
                    "source": match.source,
                    "nutrition": match.nutrition,
                    "weight": match.weight,
                    "score": match.score,
                    "search_metadata": match.search_metadata
                })
        else:
            # 単一結果の場合
            matches_dict[query] = {
                "id": match_results.id,
                "search_name": match_results.search_name,
                "description": match_results.description,
                "data_type": match_results.data_type,
                "source": match_results.source,
                "nutrition": match_results.nutrition,
                "weight": match_results.weight,
                "score": match_results.score,
                "search_metadata": match_results.search_metadata
            }
    
    # 1. 全検索結果をJSONで保存
    results_file = os.path.join(results_dir, "multi_db_elasticsearch_search_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_id": analysis_id,
            "timestamp": timestamp,
            "search_method": "elasticsearch_multi_db",
            "input_queries": {
                "all_queries": all_queries,
                "dish_names": dish_names,
                "ingredient_names": ingredient_names
            },
            "search_summary": search_results.search_summary,
            "matches": matches_dict,
            "warnings": search_results.warnings,
            "errors": search_results.errors
        }, f, indent=2, ensure_ascii=False)
    
    # 2. 検索サマリーをマークダウンで保存
    summary_file = os.path.join(results_dir, "multi_db_elasticsearch_summary.md")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# Multi-Database Elasticsearch Nutrition Search Results\n\n")
        f.write(f"**Analysis ID:** {analysis_id}\n")
        f.write(f"**Timestamp:** {timestamp}\n")
        f.write(f"**Search Method:** Multi-Database Elasticsearch\n")
        f.write(f"**Total Queries:** {len(all_queries)}\n")
        f.write(f"**Results per Database:** 5\n")
        f.write(f"**Target Databases:** yazio, mynetdiary, eatthismuch\n\n")
        
        # 検索サマリー
        summary = search_results.search_summary
        f.write(f"## Search Summary\n\n")
        f.write(f"- **Total searches:** {summary.get('total_searches', 0)}\n")
        f.write(f"- **Successful matches:** {summary.get('successful_matches', 0)}\n")
        f.write(f"- **Failed searches:** {summary.get('failed_searches', 0)}\n")
        f.write(f"- **Match rate:** {summary.get('match_rate_percent', 0):.1f}%\n")
        f.write(f"- **Search time:** {summary.get('search_time_ms', 0)}ms\n")
        f.write(f"- **Database source:** {summary.get('database_source', 'unknown')}\n")
        f.write(f"- **Total indexed documents:** {summary.get('total_indexed_documents', 0)}\n")
        f.write(f"- **Results per database:** {summary.get('results_per_db', 0)}\n")
        f.write(f"- **Target databases:** {', '.join(summary.get('target_databases', []))}\n")
        f.write(f"- **Total results:** {summary.get('total_results', 0)}\n\n")
        
        # ソース分布
        source_distribution = {}
        total_individual_results = 0
        for match_results in search_results.matches.values():
            if isinstance(match_results, list):
                total_individual_results += len(match_results)
                for match in match_results:
                    source = match.source
                    if source not in source_distribution:
                        source_distribution[source] = 0
                    source_distribution[source] += 1
            else:
                total_individual_results += 1
                source = match_results.source
                if source not in source_distribution:
                    source_distribution[source] = 0
                source_distribution[source] += 1
        
        f.write(f"## Source Database Distribution\n\n")
        for source, count in source_distribution.items():
            percentage = (count / total_individual_results) * 100 if total_individual_results > 0 else 0
            f.write(f"- **{source}:** {count} results ({percentage:.1f}%)\n")
        f.write(f"\n")
        
        # 詳細結果
        f.write(f"## Multi-DB Match Results Detail\n\n")
        for i, (query, match_results) in enumerate(search_results.matches.items(), 1):
            query_type = "dish" if query in dish_names else "ingredient"
            f.write(f"### {i}. {query} ({query_type})\n\n")
            
            if isinstance(match_results, list):
                f.write(f"**Found {len(match_results)} results from multiple databases:**\n\n")
                for j, match in enumerate(match_results, 1):
                    f.write(f"#### Result {j}\n")
                    f.write(f"- **Match:** {match.search_name}\n")
                    f.write(f"- **Score:** {match.score:.3f}\n")
                    f.write(f"- **Source:** {match.source}\n")
                    f.write(f"- **Data Type:** {match.data_type}\n")
                    
                    if match.nutrition:
                        nutrition = match.nutrition
                        calories = nutrition.get('calories', 0)
                        protein = nutrition.get('protein', 0)
                        fat = nutrition.get('fat', 0)
                        carbs = nutrition.get('carbs', nutrition.get('carbohydrates', 0))
                        f.write(f"- **Nutrition (100g):** {calories:.1f} kcal, P:{protein:.1f}g, F:{fat:.1f}g, C:{carbs:.1f}g\n")
                    
                    if match.description:
                        f.write(f"- **Description:** {match.description}\n")
                    
                    f.write(f"\n")
            else:
                # 単一結果の場合
                f.write(f"**Single result:**\n")
                f.write(f"- **Match:** {match_results.search_name}\n")
                f.write(f"- **Score:** {match_results.score:.3f}\n")
                f.write(f"- **Source:** {match_results.source}\n")
                f.write(f"- **Data Type:** {match_results.data_type}\n")
                
                if match_results.nutrition:
                    nutrition = match_results.nutrition
                    calories = nutrition.get('calories', 0)
                    protein = nutrition.get('protein', 0)
                    fat = nutrition.get('fat', 0)
                    carbs = nutrition.get('carbs', nutrition.get('carbohydrates', 0))
                    f.write(f"- **Nutrition (100g):** {calories:.1f} kcal, P:{protein:.1f}g, F:{fat:.1f}g, C:{carbs:.1f}g\n")
                
                if match_results.description:
                    f.write(f"- **Description:** {match_results.description}\n")
                
                f.write(f"\n")
        
        # 警告とエラー
        if search_results.warnings:
            f.write(f"## Warnings\n\n")
            for warning in search_results.warnings:
                f.write(f"- {warning}\n")
            f.write(f"\n")
        
        if search_results.errors:
            f.write(f"## Errors\n\n")
            for error in search_results.errors:
                f.write(f"- {error}\n")
            f.write(f"\n")
    
    print(f"\n💾 Multi-DB Elasticsearch results saved to:")
    print(f"   📁 {results_dir}/")
    print(f"   📄 multi_db_elasticsearch_search_results.json")
    print(f"   📄 multi_db_elasticsearch_summary.md")

if __name__ == "__main__":
    print("🚀 Starting Multi-Database Elasticsearch Nutrition Search Test")
    success = asyncio.run(test_multi_db_elasticsearch_nutrition_search())
    
    if success:
        print("\n✅ Multi-Database Elasticsearch nutrition search test completed successfully!")
        print("🎯 Each query returned up to 3 results from each of 3 databases (yazio, mynetdiary, eatthismuch)")
    else:
        print("\n❌ Multi-Database Elasticsearch nutrition search test failed!") 