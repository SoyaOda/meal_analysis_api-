#!/usr/bin/env python3
"""
Advanced Elasticsearch Search Test v1.0 - Strategic Search Edition

ElasticsearchNutritionSearchComponentの戦略的検索機能をテストするスクリプト
JPG画像を入力し、Phase1解析結果から抽出したクエリで
高度なElasticsearch検索戦略（dish/ingredient戦略的検索）をテスト
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

# API設定
BASE_URL = "http://localhost:8000/api/v1"

# テスト画像のパス
image_path = "test_images/food3.jpg"

async def test_advanced_elasticsearch_search():
    """Advanced Elasticsearch戦略的検索をテスト"""
    
    print("=== Advanced Elasticsearch Search Test v1.0 - Strategic Search Edition ===")
    print(f"Using image: {image_path}")
    print("🔍 Testing Advanced Elasticsearch strategic search (dish/ingredient optimization)")
    print("📊 Strategic database targeting: EatThisMuch dishes/ingredients + fallback optimization")
    
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
        
        print(f"\n📊 Extracted Search Queries from Phase1:")
        print(f"- Total dishes: {len(dish_names)}")
        print(f"- Total ingredients: {len(ingredient_names)}")
        print(f"- Total unique queries: {len(all_queries)}")
        
        if len(all_queries) == 0:
            print("❌ No search queries extracted from Phase1 results!")
            return False
        
        # ElasticsearchNutritionSearchComponentを戦略的検索モードで初期化
        print(f"\n🔧 Initializing ElasticsearchNutritionSearchComponent (Strategic Search Mode)...")
        es_component = ElasticsearchNutritionSearchComponent(
            multi_db_search_mode=True,    # 戦略的検索モードを有効化
            results_per_db=5,             # 各データベースから5つずつ結果を取得
            enable_advanced_features=False # 仕様書通りの戦略的検索を実行するため無効化
        )
        
        # 検索入力データを作成
        nutrition_query_input = NutritionQueryInput(
            ingredient_names=ingredient_names,
            dish_names=dish_names,
            preferred_source="elasticsearch"
        )
        
        print(f"📝 Strategic Query Input:")
        print(f"- Ingredient names: {len(ingredient_names)} items")
        print(f"- Dish names: {len(dish_names)} items")
        print(f"- Total search terms: {len(nutrition_query_input.get_all_search_terms())}")
        print(f"- Strategic search mode: Enabled")
        print(f"- Dish strategy: EatThisMuch data_type=dish (primary) → data_type=branded (fallback)")
        print(f"- Ingredient strategy: EatThisMuch data_type=ingredient (primary) → MyNetDiary/YAZIO/branded (fallback)")
        print(f"- Min score threshold: 20.0")
        
        # Advanced Elasticsearch戦略検索を実行
        print(f"\n🔍 Starting Advanced Elasticsearch strategic search...")
        search_start_time = time.time()
        
        search_results = await es_component.execute(nutrition_query_input)
        
        search_end_time = time.time()
        search_time = search_end_time - search_start_time
        
        print(f"✅ Advanced Elasticsearch strategic search completed in {search_time:.3f}s")
        
        # 結果の分析
        matches = search_results.matches
        search_summary = search_results.search_summary
        
        print(f"\n📈 Advanced Elasticsearch Strategic Search Results Summary:")
        print(f"- Total queries: {search_summary.get('total_searches', 0)}")
        print(f"- Successful matches: {search_summary.get('successful_matches', 0)}")
        print(f"- Failed searches: {search_summary.get('failed_searches', 0)}")
        print(f"- Match rate: {search_summary.get('match_rate_percent', 0):.1f}%")
        print(f"- Search time: {search_summary.get('search_time_ms', 0)}ms")
        print(f"- Search method: {search_summary.get('search_method', 'unknown')}")
        print(f"- Database source: {search_summary.get('database_source', 'unknown')}")
        print(f"- Total indexed documents: {search_summary.get('total_indexed_documents', 0)}")
        print(f"- Results per database: {search_summary.get('results_per_db', 0)}")
        print(f"- Strategic mode: {search_summary.get('strategic_mode', False)}")
        print(f"- Total results: {search_summary.get('total_results', 0)}")
        
        # データベース別統計の詳細計算
        db_detailed_stats = {"yazio": 0, "mynetdiary": 0, "eatthismuch": 0, "unknown": 0}
        source_distribution = {}
        query_results_breakdown = {}
        strategy_breakdown = {"dish_primary": 0, "dish_fallback": 0, "ingredient_primary": 0, "ingredient_fallback": 0}
        
        total_individual_results = 0
        for query, match_results in matches.items():
            if isinstance(match_results, list):
                # マルチ結果の場合
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
                    
                    # 戦略的検索の統計
                    query_type = "dish" if query in dish_names else "ingredient"
                    metadata = match.search_metadata or {}
                    search_strategy = metadata.get('search_strategy', 'unknown')
                    if query_type == "dish":
                        if "primary" in search_strategy:
                            strategy_breakdown["dish_primary"] += 1
                        elif "fallback" in search_strategy:
                            strategy_breakdown["dish_fallback"] += 1
                    else:
                        if "primary" in search_strategy:
                            strategy_breakdown["ingredient_primary"] += 1
                        elif "fallback" in search_strategy:
                            strategy_breakdown["ingredient_fallback"] += 1
            else:
                # 単一結果の場合
                query_results_breakdown[query] = 1
                total_individual_results += 1
                source = match_results.source
                if source not in source_distribution:
                    source_distribution[source] = 0
                source_distribution[source] += 1
                
                # 戦略的検索の統計
                query_type = "dish" if query in dish_names else "ingredient"
                metadata = match_results.search_metadata or {}
                search_strategy = metadata.get('search_strategy', 'unknown')
                if query_type == "dish":
                    if "primary" in search_strategy:
                        strategy_breakdown["dish_primary"] += 1
                    elif "fallback" in search_strategy:
                        strategy_breakdown["dish_fallback"] += 1
                else:
                    if "primary" in search_strategy:
                        strategy_breakdown["ingredient_primary"] += 1
                    elif "fallback" in search_strategy:
                        strategy_breakdown["ingredient_fallback"] += 1
        
        print(f"\n📊 Strategic Search Database Distribution:")
        for source, count in source_distribution.items():
            percentage = (count / total_individual_results) * 100 if total_individual_results > 0 else 0
            print(f"- {source}: {count} results ({percentage:.1f}%)")
        
        print(f"\n🎯 Strategic Search Strategy Breakdown:")
        total_strategy_results = sum(strategy_breakdown.values())
        for strategy, count in strategy_breakdown.items():
            if count > 0:
                percentage = (count / total_strategy_results) * 100 if total_strategy_results > 0 else 0
                print(f"- {strategy}: {count} results ({percentage:.1f}%)")
        
        print(f"\n📋 Per-Query Strategic Results Breakdown:")
        for query, result_count in query_results_breakdown.items():
            query_type = "dish" if query in dish_names else "ingredient"
            print(f"- '{query}' ({query_type}): {result_count} results")
        
        print(f"\n🔍 Top Strategic Search Results (showing first 5 queries):")
        for i, (query, match_results) in enumerate(list(matches.items())[:5], 1):
            query_type = "dish" if query in dish_names else "ingredient"
            print(f"\n{i:2d}. Query: '{query}' ({query_type})")
            
            if isinstance(match_results, list):
                print(f"    Found {len(match_results)} strategic results:")
                for j, match in enumerate(match_results, 1):
                    metadata = match.search_metadata or {}
                    search_strategy = metadata.get('strategy_type', 'unknown')
                    print(f"    {j}. {match.search_name} (score: {match.score:.3f})")
                    print(f"       Source: {match.source}")
                    print(f"       Data type: {match.data_type}")
                    print(f"       Strategy: {search_strategy}")
                    
                    nutrition = match.nutrition
                    if nutrition:
                        calories = nutrition.get('calories', 0)
                        protein = nutrition.get('protein', 0)
                        fat = nutrition.get('fat', 0)
                        carbs = nutrition.get('carbs', nutrition.get('carbohydrates', 0))
                        print(f"       Nutrition (100g): {calories:.1f} kcal, P:{protein:.1f}g, F:{fat:.1f}g, C:{carbs:.1f}g")
            else:
                # 単一結果の場合
                metadata = match_results.search_metadata or {}
                search_strategy = metadata.get('strategy_type', 'unknown')
                print(f"    Strategic result: {match_results.search_name} (score: {match_results.score:.3f})")
                print(f"    Source: {match_results.source}")
                print(f"    Strategy: {search_strategy}")
        
        if len(matches) > 5:
            print(f"\n    ... and {len(matches) - 5} more queries with strategic results")
        
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
        await save_advanced_elasticsearch_results(analysis_id, search_results, all_queries, dish_names, ingredient_names)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Advanced Elasticsearch strategic search: {e}")
        import traceback
        traceback.print_exc()
        return False

async def save_advanced_elasticsearch_results(analysis_id: str, search_results, all_queries: List[str], dish_names: List[str], ingredient_names: List[str]):
    """Advanced Elasticsearch戦略的検索結果をファイルに保存"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"analysis_results/advanced_elasticsearch_search_{analysis_id}_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    # 検索結果を辞書形式に変換
    matches_dict = {}
    for query, match_results in search_results.matches.items():
        if isinstance(match_results, list):
            # マルチ結果の場合
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
    results_file = os.path.join(results_dir, "advanced_elasticsearch_search_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_id": analysis_id,
            "timestamp": timestamp,
            "search_method": "elasticsearch_strategic",
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
    summary_file = os.path.join(results_dir, "advanced_elasticsearch_summary.md")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# Advanced Elasticsearch Strategic Search Results\n\n")
        f.write(f"**Analysis ID:** {analysis_id}\n")
        f.write(f"**Timestamp:** {timestamp}\n")
        f.write(f"**Search Method:** Advanced Elasticsearch Strategic Search\n")
        f.write(f"**Total Queries:** {len(all_queries)}\n")
        f.write(f"**Strategic Mode:** Enabled\n")
        f.write(f"**Dish Strategy:** EatThisMuch data_type=dish (primary) → data_type=branded (fallback)\n")
        f.write(f"**Ingredient Strategy:** EatThisMuch data_type=ingredient (primary) → MyNetDiary/YAZIO/branded (fallback)\n")
        f.write(f"**Min Score Threshold:** 20.0\n\n")
        
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
        f.write(f"- **Strategic mode:** {summary.get('strategic_mode', False)}\n")
        f.write(f"- **Total results:** {summary.get('total_results', 0)}\n\n")
        
        # ソース分布と戦略統計
        source_distribution = {}
        strategy_breakdown = {"dish_primary": 0, "dish_fallback": 0, "ingredient_primary": 0, "ingredient_fallback": 0}
        total_individual_results = 0
        
        for query, match_results in search_results.matches.items():
            if isinstance(match_results, list):
                total_individual_results += len(match_results)
                for match in match_results:
                    source = match.source
                    if source not in source_distribution:
                        source_distribution[source] = 0
                    source_distribution[source] += 1
                    
                    # 戦略統計
                    query_type = "dish" if query in dish_names else "ingredient"
                    metadata = match.search_metadata or {}
                    search_strategy = metadata.get('strategy_type', 'unknown')
                    if query_type == "dish":
                        if "primary" in search_strategy:
                            strategy_breakdown["dish_primary"] += 1
                        elif "fallback" in search_strategy:
                            strategy_breakdown["dish_fallback"] += 1
                    else:
                        if "primary" in search_strategy:
                            strategy_breakdown["ingredient_primary"] += 1
                        elif "fallback" in search_strategy:
                            strategy_breakdown["ingredient_fallback"] += 1
            else:
                total_individual_results += 1
                source = match_results.source
                if source not in source_distribution:
                    source_distribution[source] = 0
                source_distribution[source] += 1
                
                # 戦略統計
                query_type = "dish" if query in dish_names else "ingredient"
                metadata = match_results.search_metadata or {}
                search_strategy = metadata.get('strategy_type', 'unknown')
                if query_type == "dish":
                    if "primary" in search_strategy:
                        strategy_breakdown["dish_primary"] += 1
                    elif "fallback" in search_strategy:
                        strategy_breakdown["dish_fallback"] += 1
                else:
                    if "primary" in search_strategy:
                        strategy_breakdown["ingredient_primary"] += 1
                    elif "fallback" in search_strategy:
                        strategy_breakdown["ingredient_fallback"] += 1
        
        f.write(f"## Source Database Distribution\n\n")
        for source, count in source_distribution.items():
            percentage = (count / total_individual_results) * 100 if total_individual_results > 0 else 0
            f.write(f"- **{source}:** {count} results ({percentage:.1f}%)\n")
        f.write(f"\n")
        
        f.write(f"## Strategic Search Strategy Breakdown\n\n")
        total_strategy_results = sum(strategy_breakdown.values())
        for strategy, count in strategy_breakdown.items():
            if count > 0:
                percentage = (count / total_strategy_results) * 100 if total_strategy_results > 0 else 0
                f.write(f"- **{strategy}:** {count} results ({percentage:.1f}%)\n")
        f.write(f"\n")
        
        # 詳細結果
        f.write(f"## Strategic Search Results Detail\n\n")
        for i, (query, match_results) in enumerate(search_results.matches.items(), 1):
            query_type = "dish" if query in dish_names else "ingredient"
            f.write(f"### {i}. {query} ({query_type})\n\n")
            
            if isinstance(match_results, list):
                f.write(f"**Found {len(match_results)} strategic results:**\n\n")
                for j, match in enumerate(match_results, 1):
                    metadata = match.search_metadata or {}
                    search_strategy = metadata.get('search_strategy', 'unknown')
                    f.write(f"#### Strategic Result {j}\n")
                    f.write(f"- **Match:** {match.search_name}\n")
                    f.write(f"- **Score:** {match.score:.3f}\n")
                    f.write(f"- **Source:** {match.source}\n")
                    f.write(f"- **Data Type:** {match.data_type}\n")
                    f.write(f"- **Strategy:** {search_strategy}\n")
                    
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
                metadata = match_results.search_metadata or {}
                search_strategy = metadata.get('search_strategy', 'unknown')
                f.write(f"**Strategic result:**\n")
                f.write(f"- **Match:** {match_results.search_name}\n")
                f.write(f"- **Score:** {match_results.score:.3f}\n")
                f.write(f"- **Source:** {match_results.source}\n")
                f.write(f"- **Data Type:** {match_results.data_type}\n")
                f.write(f"- **Strategy:** {search_strategy}\n")
                
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
    
    print(f"\n💾 Advanced Elasticsearch strategic search results saved to:")
    print(f"   📁 {results_dir}/")
    print(f"   📄 advanced_elasticsearch_search_results.json")
    print(f"   📄 advanced_elasticsearch_summary.md")

if __name__ == "__main__":
    print("🚀 Starting Advanced Elasticsearch Strategic Search Test")
    success = asyncio.run(test_advanced_elasticsearch_search())
    
    if success:
        print("\n✅ Advanced Elasticsearch strategic search test completed successfully!")
        print("🎯 Strategic search optimization: dish/ingredient targeting with fallback strategies")
    else:
        print("\n❌ Advanced Elasticsearch strategic search test failed!") 