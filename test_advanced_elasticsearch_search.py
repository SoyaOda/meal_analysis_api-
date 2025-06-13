#!/usr/bin/env python3
"""
Advanced Elasticsearch Search Test v2.0 - Lemmatized Enhanced Search Edition (Multi-Image)

ElasticsearchNutritionSearchComponentの見出し語化対応検索機能をテストするスクリプト
test_images内の全JPG画像を対象とし、Phase1解析結果から抽出したクエリで
見出し語化機能を活用した高精度Elasticsearch検索をテスト
"""

import requests
import json
import time
import os
import glob
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

# Elasticsearch Nutrition Search Component
from app_v2.components.elasticsearch_nutrition_search_component import ElasticsearchNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput

# API設定
BASE_URL = "http://localhost:8000/api/v1"

# テスト画像のパス（全てのfood*.jpgファイル）
test_images_dir = "test_images"
image_files = sorted(glob.glob(os.path.join(test_images_dir, "food*.jpg")))

async def test_single_image_advanced_elasticsearch_search(image_path: str, main_results_dir: str) -> Optional[Dict[str, Any]]:
    """単一画像でAdvanced Elasticsearch戦略的検索をテスト"""
    
    print(f"\n{'='*60}")
    print(f"🖼️  Testing image: {os.path.basename(image_path)}")
    print(f"{'='*60}")
    
    try:
        # 完全分析エンドポイントを呼び出してPhase1結果を取得
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            data = {
                "save_results": True,
                "test_execution": True,  # テスト実行中であることを通知
                "test_results_dir": main_results_dir  # テスト結果ディレクトリを指定
            }
            
            print("Starting complete analysis to get Phase1 results...")
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/meal-analyses/complete", files=files, data=data)
            end_time = time.time()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f}s")
        
        if response.status_code != 200:
            print("❌ Failed to get Phase1 results!")
            print(f"Error: {response.text}")
            return None
        
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
            return None
        
        # ElasticsearchNutritionSearchComponentを見出し語化対応モードで初期化
        print(f"\n🔧 Initializing ElasticsearchNutritionSearchComponent (Lemmatized Enhanced Search Mode)...")
        es_component = ElasticsearchNutritionSearchComponent(
            multi_db_search_mode=False,   # 見出し語化検索を優先（戦略的検索は無効）
            results_per_db=5,             # 各データベースから5つずつ結果を取得
            enable_advanced_features=False # 構造化検索は無効化、見出し語化検索に集中
        )
        
        print(f"✅ Lemmatization features enabled:")
        print(f"   - Lemmatized exact match boost: {es_component.lemmatized_exact_match_boost}")
        print(f"   - Compound word penalty: {es_component.compound_word_penalty}")
        print(f"   - Enable lemmatization: {es_component.enable_lemmatization}")
        
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
        
        # Advanced Elasticsearch見出し語化対応検索を実行
        print(f"\n🔍 Starting Advanced Elasticsearch lemmatized enhanced search...")
        search_start_time = time.time()
        
        search_results = await es_component.execute(nutrition_query_input)
        
        search_end_time = time.time()
        search_time = search_end_time - search_start_time
        
        print(f"✅ Advanced Elasticsearch lemmatized enhanced search completed in {search_time:.3f}s")
        
        # 結果の分析
        matches = search_results.matches
        search_summary = search_results.search_summary
        
        print(f"\n📈 Advanced Elasticsearch Lemmatized Enhanced Search Results Summary:")
        print(f"- Total queries: {search_summary.get('total_searches', 0)}")
        print(f"- Successful matches: {search_summary.get('successful_matches', 0)}")
        print(f"- Failed searches: {search_summary.get('failed_searches', 0)}")
        print(f"- Match rate: {search_summary.get('match_rate_percent', 0):.1f}%")
        print(f"- Search method: {search_summary.get('search_method', 'N/A')}")
        print(f"- Search time: {search_summary.get('search_time_ms', 0)}ms")
        print(f"- Total results: {search_summary.get('total_results', 0)}")
        
        # 見出し語化の効果を表示
        if hasattr(search_results, 'advanced_search_metadata') and search_results.advanced_search_metadata:
            metadata = search_results.advanced_search_metadata
            if 'lemmatization_enabled' in metadata:
                print(f"- Lemmatization enabled: {metadata['lemmatization_enabled']}")
            if 'scoring_parameters' in metadata:
                params = metadata['scoring_parameters']
                print(f"- Exact match boost: {params.get('exact_match_boost', 'N/A')}")
                print(f"- Compound word penalty: {params.get('compound_word_penalty', 'N/A')}")
        
        # 結果を保存
        await save_advanced_elasticsearch_results(
            analysis_id, search_results, all_queries, dish_names, ingredient_names, 
            image_filename=os.path.basename(image_path), main_results_dir=main_results_dir
        )
        
        # この画像の結果をサマリー用に返す
        summary_result = {
            "image_name": os.path.basename(image_path),
            "analysis_id": analysis_id,
            "total_queries": search_summary.get('total_searches', 0),
            "successful_matches": search_summary.get('successful_matches', 0),
            "failed_searches": search_summary.get('failed_searches', 0),
            "match_rate_percent": search_summary.get('match_rate_percent', 0),
            "search_time_ms": search_summary.get('search_time_ms', 0),
            "total_results": search_summary.get('total_results', 0),
            "dish_names": dish_names,
            "ingredient_names": ingredient_names,
            "all_queries": all_queries
        }
        
        # 詳細結果も含めて返す
        detailed_result = {
            "analysis_id": analysis_id,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "image_filename": os.path.basename(image_path),
            "input_queries": {
                "all_queries": all_queries,
                "dish_names": dish_names,
                "ingredient_names": ingredient_names
            },
            "search_summary": search_results.search_summary,
            "matches": {},
            "warnings": search_results.warnings,
            "errors": search_results.errors
        }
        
        # 検索結果を辞書形式に変換
        matches_dict = {}
        for query, match_results in search_results.matches.items():
            if isinstance(match_results, list):
                matches_dict[query] = [
                    {
                        "id": match.id,
                        "search_name": match.search_name,
                        "description": match.description,
                        "data_type": match.data_type,
                        "source": match.source,
                        "nutrition": match.nutrition,
                        "weight": match.weight,
                        "score": match.score,
                        "is_exact_match": match.is_exact_match,
                        "match_details": match.match_details,
                        "search_metadata": match.search_metadata
                    } for match in match_results
                ]
            else:
                matches_dict[query] = {
                    "id": match_results.id,
                    "search_name": match_results.search_name,
                    "description": match_results.description,
                    "data_type": match_results.data_type,
                    "source": match_results.source,
                    "nutrition": match_results.nutrition,
                    "weight": match_results.weight,
                    "score": match_results.score,
                    "is_exact_match": match_results.is_exact_match,
                    "match_details": match_results.match_details,
                    "search_metadata": match_results.search_metadata
                }
        
        return summary_result, detailed_result
        
    except Exception as e:
        print(f"❌ Error testing {os.path.basename(image_path)}: {str(e)}")
        return None

async def test_advanced_elasticsearch_search():
    """全画像でAdvanced Elasticsearch戦略的検索をテスト"""
    
    print("🚀 Starting Advanced Elasticsearch Strategic Search Test (Multi-Image)")
    print("=== Advanced Elasticsearch Search Test v1.0 - Strategic Search Edition ===")
    print(f"📁 Testing {len(image_files)} images: {[os.path.basename(f) for f in image_files]}")
    print("🔍 Testing Advanced Elasticsearch strategic search (dish/ingredient optimization)")
    print("📊 Strategic database targeting: EatThisMuch dishes/ingredients + fallback optimization")
    
    if not image_files:
        print("❌ No food*.jpg images found in test_images directory!")
        return False
    
    # 実行用のメインディレクトリを作成
    main_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_results_dir = f"analysis_results/elasticsearch_test_{main_timestamp}"
    os.makedirs(main_results_dir, exist_ok=True)
    print(f"📁 Created main results directory: {main_results_dir}")
    
    # 全体のサマリー用変数
    all_results = []
    all_detailed_results = []  # 詳細検索結果を保存
    total_queries = 0
    total_successful = 0
    total_failed = 0
    total_search_time = 0
    total_results_count = 0
    
    # 各画像でテストを実行
    for image_path in image_files:
        result = await test_single_image_advanced_elasticsearch_search(image_path, main_results_dir)
        if result:
            summary_result, detailed_result = result
            all_results.append(summary_result)
            all_detailed_results.append(detailed_result)
            
            total_queries += summary_result["total_queries"]
            total_successful += summary_result["successful_matches"]
            total_failed += summary_result["failed_searches"]
            total_search_time += summary_result["search_time_ms"]
            total_results_count += summary_result["total_results"]
    
    # 全体のサマリーを表示
    print(f"\n{'='*80}")
    print(f"🎯 OVERALL MULTI-IMAGE TEST SUMMARY")
    print(f"{'='*80}")
    print(f"📊 Images tested: {len(all_results)}/{len(image_files)}")
    print(f"📈 Overall Statistics:")
    print(f"   - Total queries across all images: {total_queries}")
    print(f"   - Total successful matches: {total_successful}")
    print(f"   - Total failed searches: {total_failed}")
    print(f"   - Overall match rate: {(total_successful/total_queries*100) if total_queries > 0 else 0:.1f}%")
    print(f"   - Total search time: {total_search_time}ms")
    print(f"   - Average search time per image: {total_search_time/len(all_results) if all_results else 0:.1f}ms")
    print(f"   - Total results found: {total_results_count}")
    print(f"   - Average results per image: {total_results_count/len(all_results) if all_results else 0:.1f}")
    
    print(f"\n📋 Per-Image Results Breakdown:")
    for i, result in enumerate(all_results, 1):
        print(f"   {i}. {result['image_name']}:")
        print(f"      - Queries: {result['total_queries']} | Matches: {result['successful_matches']} | Success: {result['match_rate_percent']:.1f}%")
        print(f"      - Time: {result['search_time_ms']}ms | Results: {result['total_results']}")
        print(f"      - Dishes: {len(result['dish_names'])} | Ingredients: {len(result['ingredient_names'])}")
    
    # 集約結果を保存（詳細結果も含める）
    await save_multi_image_summary(all_results, total_queries, total_successful, total_failed, total_search_time, total_results_count, all_detailed_results, main_results_dir)
    
    print(f"\n✅ Multi-image Advanced Elasticsearch strategic search test completed!")
    print(f"🎯 Overall success rate: {(total_successful/total_queries*100) if total_queries > 0 else 0:.1f}%")
    
    return len(all_results) > 0

async def save_advanced_elasticsearch_results(analysis_id: str, search_results, all_queries: List[str], dish_names: List[str], ingredient_names: List[str], image_filename: str, main_results_dir: str):
    """Advanced Elasticsearch戦略的検索結果をファイルに保存"""
    
    # メインディレクトリ内にサブディレクトリを作成
    image_base = os.path.splitext(image_filename)[0]  # food1, food2, etc.
    results_dir = f"{main_results_dir}/{image_base}"
    os.makedirs(results_dir, exist_ok=True)
    
    # 検索結果を辞書形式に変換
    matches_dict = {}
    for query, match_results in search_results.matches.items():
        if isinstance(match_results, list):
            matches_dict[query] = [
                {
                    "id": match.id,
                    "search_name": match.search_name,
                    "description": match.description,
                    "data_type": match.data_type,
                    "source": match.source,
                    "nutrition": match.nutrition,
                    "weight": match.weight,
                    "score": match.score,
                    "is_exact_match": match.is_exact_match,
                    "match_details": match.match_details,
                    "search_metadata": match.search_metadata
                } for match in match_results
            ]
        else:
            matches_dict[query] = {
                "id": match_results.id,
                "search_name": match_results.search_name,
                "description": match_results.description,
                "data_type": match_results.data_type,
                "source": match_results.source,
                "nutrition": match_results.nutrition,
                "weight": match_results.weight,
                "score": match_results.score,
                "is_exact_match": match_results.is_exact_match,
                "match_details": match_results.match_details,
                "search_metadata": match_results.search_metadata
            }
    
    # 1. 全検索結果をJSONで保存
    results_file = os.path.join(results_dir, "advanced_elasticsearch_search_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "analysis_id": analysis_id,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "image_filename": image_filename,
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
        f.write(f"**Image:** {image_filename}\n")
        f.write(f"**Timestamp:** {datetime.now().strftime('%Y%m%d_%H%M%S')}\n")
        f.write(f"**Search Method:** Advanced Elasticsearch Strategic Search\n")
        f.write(f"**Total Queries:** {len(all_queries)}\n\n")
        
        # 検索サマリー
        summary = search_results.search_summary
        f.write(f"## Search Summary\n\n")
        f.write(f"- **Total searches:** {summary.get('total_searches', 0)}\n")
        f.write(f"- **Successful matches:** {summary.get('successful_matches', 0)}\n")
        f.write(f"- **Failed searches:** {summary.get('failed_searches', 0)}\n")
        f.write(f"- **Match rate:** {summary.get('match_rate_percent', 0):.1f}%\n")
        f.write(f"- **Search time:** {summary.get('search_time_ms', 0)}ms\n")
        f.write(f"- **Total results:** {summary.get('total_results', 0)}\n\n")
    
    print(f"   💾 Results saved: {results_dir}/")

async def save_multi_image_summary(all_results: List[Dict[str, Any]], total_queries: int, total_successful: int, total_failed: int, total_search_time: int, total_results_count: int, detailed_results: List[Dict[str, Any]], main_results_dir: str):
    """マルチ画像テストの全体サマリーと詳細結果を1つのファイルに保存"""
    
    # メインディレクトリに直接保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. 全体サマリーと詳細結果をJSONで保存
    comprehensive_file = os.path.join(main_results_dir, "comprehensive_multi_image_results.json")
    with open(comprehensive_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "test_type": "comprehensive_multi_image_advanced_elasticsearch_strategic",
            "overall_summary": {
                "images_tested": len(all_results),
                "total_queries": total_queries,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "overall_match_rate_percent": (total_successful/total_queries*100) if total_queries > 0 else 0,
                "total_search_time_ms": total_search_time,
                "average_search_time_per_image_ms": total_search_time/len(all_results) if all_results else 0,
                "total_results_found": total_results_count,
                "average_results_per_image": total_results_count/len(all_results) if all_results else 0
            },
            "per_image_summary": all_results,
            "detailed_search_results": detailed_results or []
        }, f, indent=2, ensure_ascii=False)
    
    # 2. 包括的マークダウンレポートを保存
    comprehensive_md_file = os.path.join(main_results_dir, "comprehensive_multi_image_results.md")
    with open(comprehensive_md_file, 'w', encoding='utf-8') as f:
        f.write(f"# Comprehensive Multi-Image Advanced Elasticsearch Strategic Search Results\n\n")
        f.write(f"**Test Date:** {timestamp}\n")
        f.write(f"**Test Type:** Comprehensive Multi-Image Advanced Elasticsearch Strategic Search\n")
        f.write(f"**Images Tested:** {len(all_results)}\n\n")
        
        # 全体パフォーマンス
        f.write(f"## Overall Performance Summary\n\n")
        f.write(f"- **Total Queries:** {total_queries}\n")
        f.write(f"- **Successful Matches:** {total_successful}\n")
        f.write(f"- **Failed Searches:** {total_failed}\n")
        f.write(f"- **Overall Success Rate:** {(total_successful/total_queries*100) if total_queries > 0 else 0:.1f}%\n")
        f.write(f"- **Total Search Time:** {total_search_time}ms\n")
        f.write(f"- **Average Time per Image:** {total_search_time/len(all_results) if all_results else 0:.1f}ms\n")
        f.write(f"- **Total Results Found:** {total_results_count}\n")
        f.write(f"- **Average Results per Image:** {total_results_count/len(all_results) if all_results else 0:.1f}\n\n")
        
        # パフォーマンス比較表
        f.write(f"## Performance Comparison Table\n\n")
        f.write(f"| Image | Queries | Matches | Success % | Time (ms) | Results | Dishes | Ingredients |\n")
        f.write(f"|-------|---------|---------|-----------|-----------|---------|--------|-------------|\n")
        for result in all_results:
            f.write(f"| {result['image_name']} | {result['total_queries']} | {result['successful_matches']} | {result['match_rate_percent']:.1f}% | {result['search_time_ms']} | {result['total_results']} | {len(result['dish_names'])} | {len(result['ingredient_names'])} |\n")
        
        f.write(f"\n**Average Performance:** {(total_successful/total_queries*100) if total_queries > 0 else 0:.1f}% success rate, {total_search_time/len(all_results) if all_results else 0:.1f}ms per image\n\n")
        
        # 各画像の詳細結果
        if detailed_results:
            f.write(f"## Detailed Search Results by Image\n\n")
            
            for i, detail in enumerate(detailed_results):
                image_info = all_results[i]
                f.write(f"### {i+1}. {image_info['image_name']}\n\n")
                f.write(f"- **Analysis ID:** {image_info['analysis_id']}\n")
                f.write(f"- **Success Rate:** {image_info['match_rate_percent']:.1f}% ({image_info['successful_matches']}/{image_info['total_queries']})\n")
                f.write(f"- **Search Time:** {image_info['search_time_ms']}ms\n")
                f.write(f"- **Total Results:** {image_info['total_results']}\n\n")
                
                # 検出された料理と材料
                f.write(f"#### Detected Items\n\n")
                if image_info['dish_names']:
                    f.write(f"**Dishes ({len(image_info['dish_names'])}):** {', '.join(image_info['dish_names'])}\n\n")
                if image_info['ingredient_names']:
                    f.write(f"**Ingredients ({len(image_info['ingredient_names'])}):** {', '.join(image_info['ingredient_names'])}\n\n")
                
                # 検索結果詳細
                f.write(f"#### Search Results Detail\n\n")
                matches = detail.get('matches', {})
                dish_names = image_info['dish_names']
                
                # 料理結果を先に表示
                dish_results = {k: v for k, v in matches.items() if k in dish_names}
                ingredient_results = {k: v for k, v in matches.items() if k not in dish_names}
                
                if dish_results:
                    f.write(f"##### Dish Search Results\n\n")
                    for j, (query, match_results) in enumerate(dish_results.items(), 1):
                        f.write(f"**{j}. {query} (dish)**\n\n")
                        if isinstance(match_results, list):
                            f.write(f"Found {len(match_results)} results:\n\n")
                            for k, match in enumerate(match_results[:3], 1):  # 上位3件のみ表示
                                f.write(f"   {k}. **{match.get('search_name', 'Unknown')}** (score: {match.get('score', 0):.2f})\n")
                                f.write(f"      - Source: {match.get('source', 'Unknown')}\n")
                                f.write(f"      - Data Type: {match.get('data_type', 'Unknown')}\n")
                                if match.get('nutrition'):
                                    nutrition = match['nutrition']
                                    calories = nutrition.get('calories', 0)
                                    protein = nutrition.get('protein', 0)
                                    fat = nutrition.get('fat', 0)
                                    carbs = nutrition.get('carbs', nutrition.get('carbohydrates', 0))
                                    f.write(f"      - Nutrition (100g): {calories:.1f} kcal, P:{protein:.1f}g, F:{fat:.1f}g, C:{carbs:.1f}g\n")
                                f.write(f"\n")
                            if len(match_results) > 3:
                                f.write(f"   ... and {len(match_results) - 3} more results\n\n")
                        f.write(f"\n")
                
                if ingredient_results:
                    f.write(f"##### Ingredient Search Results\n\n")
                    for j, (query, match_results) in enumerate(ingredient_results.items(), 1):
                        f.write(f"**{j}. {query} (ingredient)**\n\n")
                        if isinstance(match_results, list):
                            f.write(f"Found {len(match_results)} results:\n\n")
                            for k, match in enumerate(match_results[:2], 1):  # 上位2件のみ表示
                                f.write(f"   {k}. **{match.get('search_name', 'Unknown')}** (score: {match.get('score', 0):.2f})\n")
                                f.write(f"      - Source: {match.get('source', 'Unknown')}\n")
                                f.write(f"      - Data Type: {match.get('data_type', 'Unknown')}\n")
                                if match.get('nutrition'):
                                    nutrition = match['nutrition']
                                    calories = nutrition.get('calories', 0)
                                    protein = nutrition.get('protein', 0)
                                    fat = nutrition.get('fat', 0)
                                    carbs = nutrition.get('carbs', nutrition.get('carbohydrates', 0))
                                    f.write(f"      - Nutrition (100g): {calories:.1f} kcal, P:{protein:.1f}g, F:{fat:.1f}g, C:{carbs:.1f}g\n")
                                f.write(f"\n")
                            if len(match_results) > 2:
                                f.write(f"   ... and {len(match_results) - 2} more results\n\n")
                        f.write(f"\n")
                
                f.write(f"---\n\n")
        
        # 戦略的検索統計（全画像統合）
        if detailed_results:
            f.write(f"## Strategic Search Statistics (All Images)\n\n")
            
            # データベース分布統計
            total_db_stats = {"elasticsearch_eatthismuch": 0, "elasticsearch_yazio": 0, "elasticsearch_mynetdiary": 0}
            strategy_stats = {"dish_primary": 0, "dish_fallback": 0, "ingredient_primary": 0, "ingredient_fallback": 0}
            total_individual_results = 0
            
            for detail in detailed_results:
                matches = detail.get('matches', {})
                dish_names = set(detail.get('input_queries', {}).get('dish_names', []))
                
                for query, match_results in matches.items():
                    if isinstance(match_results, list):
                        total_individual_results += len(match_results)
                        for match in match_results:
                            source = match.get('source', '')
                            if source in total_db_stats:
                                total_db_stats[source] += 1
                            
                            # 戦略統計
                            metadata = match.get('search_metadata', {})
                            strategy_type = metadata.get('strategy_type', '')
                            if strategy_type in strategy_stats:
                                strategy_stats[strategy_type] += 1
            
            f.write(f"### Database Distribution\n\n")
            for db, count in total_db_stats.items():
                if count > 0:
                    percentage = (count / total_individual_results) * 100 if total_individual_results > 0 else 0
                    db_name = db.replace('elasticsearch_', '').title()
                    f.write(f"- **{db_name}:** {count} results ({percentage:.1f}%)\n")
            
            f.write(f"\n### Strategy Distribution\n\n")
            total_strategy_results = sum(strategy_stats.values())
            for strategy, count in strategy_stats.items():
                if count > 0:
                    percentage = (count / total_strategy_results) * 100 if total_strategy_results > 0 else 0
                    strategy_name = strategy.replace('_', ' ').title()
                    f.write(f"- **{strategy_name}:** {count} results ({percentage:.1f}%)\n")
    
    print(f"\n📊 Comprehensive multi-image results saved to:")
    print(f"   📁 {main_results_dir}/")
    print(f"   📄 comprehensive_multi_image_results.json")
    print(f"   📄 comprehensive_multi_image_results.md")

if __name__ == "__main__":
    print("🚀 Starting Advanced Elasticsearch Strategic Search Test")
    success = asyncio.run(test_advanced_elasticsearch_search())
    
    if success:
        print("\n✅ Advanced Elasticsearch strategic search test completed successfully!")
        print("🎯 Strategic search optimization: dish/ingredient targeting with fallback strategies")
    else:
        print("\n❌ Advanced Elasticsearch strategic search test failed!") 