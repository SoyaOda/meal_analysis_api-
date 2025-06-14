#!/usr/bin/env python3
"""
Advanced Elasticsearch Strategic Search Test - Standalone Edition v3.0
APIサーバーを使わずに直接MealAnalysisPipelineでfood1.jpgを分析し、
test_advanced_elasticsearch_search.pyと同様のAdvanced Elasticsearch戦略的検索を実行します。
"""

import asyncio
import os
import sys
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app_v2.pipeline import MealAnalysisPipeline
from app_v2.components.elasticsearch_nutrition_search_component import ElasticsearchNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def setup_environment():
    """環境変数の設定"""
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/Users/odasoya/meal_analysis_api_2/service-account-key.json")
    os.environ.setdefault("GEMINI_PROJECT_ID", "recording-diet-ai-3e7cf")
    os.environ.setdefault("GEMINI_LOCATION", "us-central1")
    os.environ.setdefault("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")


def get_image_mime_type(file_path: str) -> str:
    """ファイル拡張子からMIMEタイプを推定"""
    ext = Path(file_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


async def analyze_food1_image_with_detailed_search():
    """food1.jpgの分析を実行し、詳細な検索結果分析も行う"""
    
    # 画像ファイルのパス
    image_path = "test_images/food1.jpg"
    
    # 画像ファイルの存在確認
    if not os.path.exists(image_path):
        print(f"❌ エラー: 画像ファイルが見つかりません: {image_path}")
        return None
    
    # 画像データの読み込み
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    image_mime_type = get_image_mime_type(image_path)
    
    print(f"🚀 Advanced Elasticsearch Strategic Search Test (Standalone) 開始")
    print(f"📁 分析対象: {image_path}")
    print(f"📊 画像サイズ: {len(image_bytes):,} bytes")
    print(f"🔍 MIMEタイプ: {image_mime_type}")
    print(f"🔧 検索方法: Advanced Elasticsearch Strategic Search (APIサーバー不要)")
    print("=" * 60)
    
    # 結果保存用ディレクトリを作成（test_advanced_elasticsearch_search.pyと同様の構造）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    main_results_dir = f"analysis_results/elasticsearch_test_{timestamp}"
    os.makedirs(main_results_dir, exist_ok=True)
    
    # 完全分析結果保存用サブディレクトリを作成
    api_calls_dir = f"{main_results_dir}/api_calls"
    os.makedirs(api_calls_dir, exist_ok=True)
    
    print(f"📁 メイン結果保存ディレクトリ: {main_results_dir}")
    print(f"📁 完全分析結果保存ディレクトリ: {api_calls_dir}")
    
    # パイプラインの初期化（Elasticsearch検索を使用）
    pipeline = MealAnalysisPipeline(
        use_elasticsearch_search=True,
        use_local_nutrition_search=False
    )
    
    try:
        # Step 1: 完全分析実行
        print(f"\n🔄 Step 1: 完全食事分析実行中...")
        analysis_start_time = time.time()
        
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            save_detailed_logs=False
        )
        
        analysis_end_time = time.time()
        analysis_time = analysis_end_time - analysis_start_time
        
        print(f"✅ 完全分析が完了しました！ ({analysis_time:.2f}秒)")
        
        # 基本結果の表示
        print_basic_analysis_summary(result)
        
        # Step 2: Phase1結果から検索クエリを抽出
        print(f"\n🔄 Step 2: Phase1結果から検索クエリを抽出中...")
        
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
        
        print(f"📊 抽出された検索クエリ:")
        print(f"   - 料理名: {len(dish_names)}個")
        print(f"   - 食材名: {len(ingredient_names)}個")
        print(f"   - 総クエリ数: {len(all_queries)}個")
        
        if len(all_queries) == 0:
            print("❌ Phase1結果から検索クエリを抽出できませんでした！")
            return None
        
        # Step 3: Advanced Elasticsearch戦略的検索実行
        print(f"\n🔄 Step 3: Advanced Elasticsearch戦略的検索実行中...")
        
        # ElasticsearchNutritionSearchComponentを見出し語化対応モードで初期化
        es_component = ElasticsearchNutritionSearchComponent(
            strategic_search_mode=False,   # 統合検索モード（全データベース統合での見出し語化検索）
            results_per_db=5,             # 各データベースから5つずつ結果を取得
            enable_advanced_features=False # 構造化検索は無効化、見出し語化検索に集中
        )
        
        print(f"✅ Elasticsearch検索コンポーネント初期化完了:")
        print(f"   - 見出し語化完全一致ブースト: {es_component.lemmatized_exact_match_boost}")
        print(f"   - 複合語ペナルティ: {es_component.compound_word_penalty}")
        print(f"   - 見出し語化有効: {es_component.enable_lemmatization}")
        
        # 検索入力データを作成
        nutrition_query_input = NutritionQueryInput(
            ingredient_names=ingredient_names,
            dish_names=dish_names,
            preferred_source="elasticsearch"
        )
        
        print(f"📝 検索入力データ:")
        print(f"   - 食材名: {len(ingredient_names)}個")
        print(f"   - 料理名: {len(dish_names)}個")
        print(f"   - 総検索語数: {len(nutrition_query_input.get_all_search_terms())}個")
        
        # 詳細Elasticsearch検索を実行
        search_start_time = time.time()
        
        search_results = await es_component.execute(nutrition_query_input)
        
        search_end_time = time.time()
        search_time = search_end_time - search_start_time
        
        print(f"✅ Advanced Elasticsearch戦略的検索完了 ({search_time:.3f}秒)")
        
        # Step 4: 戦略的検索結果の分析と表示
        print(f"\n🔄 Step 4: 戦略的検索結果分析中...")
        
        search_summary = search_results.search_summary
        
        print(f"\n📈 Advanced Elasticsearch戦略的検索結果サマリー:")
        print(f"   - 総検索数: {search_summary.get('total_searches', 0)}")
        print(f"   - 成功マッチ: {search_summary.get('successful_matches', 0)}")
        print(f"   - 失敗検索: {search_summary.get('failed_searches', 0)}")
        print(f"   - マッチ率: {search_summary.get('match_rate_percent', 0):.1f}%")
        print(f"   - 検索方法: {search_summary.get('search_method', 'N/A')}")
        print(f"   - 検索時間: {search_summary.get('search_time_ms', 0)}ms")
        print(f"   - 総結果数: {search_summary.get('total_results', 0)}")
        
        # 見出し語化の効果を表示
        if hasattr(search_results, 'advanced_search_metadata') and search_results.advanced_search_metadata:
            metadata = search_results.advanced_search_metadata
            if 'lemmatization_enabled' in metadata:
                print(f"   - 見出し語化有効: {metadata['lemmatization_enabled']}")
            if 'scoring_parameters' in metadata:
                params = metadata['scoring_parameters']
                print(f"   - 完全一致ブースト: {params.get('exact_match_boost', 'N/A')}")
                print(f"   - 複合語ペナルティ: {params.get('compound_word_penalty', 'N/A')}")
        
        # Step 5: 結果保存（test_advanced_elasticsearch_search.pyと同様の構造）
        print(f"\n🔄 Step 5: 戦略的検索結果保存中...")
        
        analysis_id = result.get("analysis_id", "unknown")
        
        # 完全分析結果を保存（スタンドアロン実行結果）
        await save_api_call_results(
            analysis_id=analysis_id,
            complete_analysis_result=result,
            image_filename=os.path.basename(image_path),
            api_calls_dir=api_calls_dir,
            analysis_time=analysis_time
        )
        
        # 戦略的検索結果を保存（test_advanced_elasticsearch_search.pyと同様）
        await save_advanced_elasticsearch_results(
            analysis_id=analysis_id,
            search_results=search_results,
            all_queries=all_queries,
            dish_names=dish_names,
            ingredient_names=ingredient_names,
            image_filename=os.path.basename(image_path),
            main_results_dir=main_results_dir
        )
        
        # 包括的結果を保存
        await save_comprehensive_results(
            analysis_id=analysis_id,
            complete_analysis_result=result,
            search_results=search_results,
            all_queries=all_queries,
            dish_names=dish_names,
            ingredient_names=ingredient_names,
            image_filename=os.path.basename(image_path),
            main_results_dir=main_results_dir,
            analysis_time=analysis_time,
            search_time=search_time
        )
        
        print(f"✅ 戦略的検索結果保存完了！")
        
        # 最終サマリー表示
        print_detailed_analysis_summary(result, search_results, analysis_time, search_time)
        
        return {
            "complete_analysis": result,
            "detailed_search": search_results,
            "analysis_time": analysis_time,
            "search_time": search_time,
            "saved_to": main_results_dir,
            "api_calls_dir": api_calls_dir
        }
        
    except Exception as e:
        print(f"❌ 分析中にエラーが発生しました: {e}")
        logger.error(f"分析エラー: {e}", exc_info=True)
        return None


def print_basic_analysis_summary(result: dict):
    """基本分析結果のサマリーを表示"""
    if not result or 'error' in result:
        print(f"❌ エラー: {result.get('error', '不明なエラー')}")
        return
    
    print(f"\n📋 基本分析結果サマリー (ID: {result.get('analysis_id', 'N/A')})")
    print("-" * 40)
    
    # Phase1結果
    phase1 = result.get('phase1_result', {})
    dishes = phase1.get('dishes', [])
    detected_items = phase1.get('detected_food_items', [])
    
    print(f"🍽️  検出された料理: {len(dishes)}個")
    for i, dish in enumerate(dishes, 1):
        confidence = dish.get('confidence', 0)
        print(f"   {i}. {dish.get('dish_name', 'N/A')} (信頼度: {confidence:.2f})")
    
    print(f"\n🥕 検出された食材: {len(detected_items)}個")
    for i, item in enumerate(detected_items, 1):
        confidence = item.get('confidence', 0)
        print(f"   {i}. {item.get('item_name', 'N/A')} (信頼度: {confidence:.2f})")
    
    # 栄養検索結果
    nutrition_search = result.get('nutrition_search_result', {})
    match_rate = nutrition_search.get('match_rate', 0)
    matches_count = nutrition_search.get('matches_count', 0)
    
    print(f"\n🔍 基本栄養データベース照合結果:")
    print(f"   - マッチ件数: {matches_count}件")
    print(f"   - 成功率: {match_rate:.1%}")
    print(f"   - 検索方法: {nutrition_search.get('search_summary', {}).get('search_method', 'elasticsearch')}")


def print_detailed_analysis_summary(complete_result: dict, search_results, analysis_time: float, search_time: float):
    """Advanced Elasticsearch戦略的検索結果の最終サマリーを表示"""
    
    print(f"\n{'='*80}")
    print(f"🎯 Advanced Elasticsearch Strategic Search Test 完了サマリー")
    print(f"{'='*80}")
    
    analysis_id = complete_result.get('analysis_id', 'N/A')
    print(f"📋 分析ID: {analysis_id}")
    
    # 処理時間サマリー
    print(f"\n⏱️  処理時間サマリー:")
    print(f"   - 完全分析時間: {analysis_time:.2f}秒")
    print(f"   - 戦略的検索時間: {search_time:.3f}秒")
    print(f"   - 総処理時間: {analysis_time + search_time:.2f}秒")
    
    # 戦略的検索結果サマリー
    search_summary = search_results.search_summary
    print(f"\n🔍 戦略的検索結果サマリー:")
    print(f"   - 総検索数: {search_summary.get('total_searches', 0)}")
    print(f"   - 成功マッチ: {search_summary.get('successful_matches', 0)}")
    print(f"   - マッチ率: {search_summary.get('match_rate_percent', 0):.1f}%")
    print(f"   - 総結果数: {search_summary.get('total_results', 0)}")
    
    # 栄養価計算は未実装（Phase2とNutritionCalculationComponentで実装予定）
    
    print(f"\n✅ Advanced Elasticsearch Strategic Search Test 完了！")
    print(f"🎯 総合成功率: {search_summary.get('match_rate_percent', 0):.1f}%")


async def save_api_call_results(
    analysis_id: str,
    complete_analysis_result: dict,
    image_filename: str,
    api_calls_dir: str,
    analysis_time: float
):
    """完全分析結果を保存（スタンドアロン実行結果）"""
    
    # 完全分析結果用のサブディレクトリを作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    api_analysis_dir = f"{api_calls_dir}/api_analysis_{timestamp}"
    os.makedirs(api_analysis_dir, exist_ok=True)
    
    # 完全分析結果をJSONで保存
    api_result_file = f"{api_analysis_dir}/meal_analysis_{analysis_id}.json"
    with open(api_result_file, 'w', encoding='utf-8') as f:
        json.dump(complete_analysis_result, f, indent=2, ensure_ascii=False)
    
    print(f"   💾 完全分析結果保存: {api_analysis_dir}/")


async def save_advanced_elasticsearch_results(
    analysis_id: str,
    search_results,
    all_queries: List[str],
    dish_names: List[str],
    ingredient_names: List[str],
    image_filename: str,
    main_results_dir: str
):
    """Advanced Elasticsearch戦略的検索結果をファイルに保存（test_advanced_elasticsearch_search.pyと同様）"""
    
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
    
    print(f"   💾 検索結果保存: {results_dir}/")


async def save_comprehensive_results(
    analysis_id: str,
    complete_analysis_result: dict,
    search_results,
    all_queries: List[str],
    dish_names: List[str],
    ingredient_names: List[str],
    image_filename: str,
    main_results_dir: str,
    analysis_time: float,
    search_time: float
):
    """包括的結果をマークダウンで保存（test_advanced_elasticsearch_search.pyと同様）"""
    
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
                "search_metadata": match_results.search_metadata
            }
    
    # 包括的結果をマークダウンで保存
    comprehensive_md_file = os.path.join(main_results_dir, "comprehensive_multi_image_results.md")
    with open(comprehensive_md_file, 'w', encoding='utf-8') as f:
        f.write(f"# Comprehensive Multi-Image Advanced Elasticsearch Strategic Search Results\n\n")
        f.write(f"**Test Type:** Standalone Advanced Elasticsearch Strategic Search\n")
        f.write(f"**Timestamp:** {datetime.now().strftime('%Y%m%d_%H%M%S')}\n")
        f.write(f"**Images Tested:** 1 ({image_filename})\n\n")
        
        # 全体サマリー
        f.write(f"## Overall Summary\n\n")
        f.write(f"- **Images tested:** 1/1\n")
        f.write(f"- **Total queries:** {len(all_queries)}\n")
        f.write(f"- **Total successful matches:** {search_results.search_summary.get('successful_matches', 0)}\n")
        f.write(f"- **Total failed searches:** {search_results.search_summary.get('failed_searches', 0)}\n")
        f.write(f"- **Overall match rate:** {search_results.search_summary.get('match_rate_percent', 0):.1f}%\n")
        f.write(f"- **Total search time:** {search_results.search_summary.get('search_time_ms', 0)}ms\n")
        f.write(f"- **Total results found:** {search_results.search_summary.get('total_results', 0)}\n")
        f.write(f"- **Complete analysis time:** {analysis_time:.2f}s\n")
        f.write(f"- **Detailed search time:** {search_time:.3f}s\n\n")
        
        # 画像別結果
        f.write(f"## Per-Image Results Breakdown\n\n")
        f.write(f"### {image_filename}\n\n")
        f.write(f"- **Queries:** {len(all_queries)} | **Matches:** {search_results.search_summary.get('successful_matches', 0)} | **Success:** {search_results.search_summary.get('match_rate_percent', 0):.1f}%\n")
        f.write(f"- **Time:** {search_results.search_summary.get('search_time_ms', 0)}ms | **Results:** {search_results.search_summary.get('total_results', 0)}\n")
        f.write(f"- **Dishes:** {len(dish_names)} | **Ingredients:** {len(ingredient_names)}\n\n")
        
        # 検出されたアイテム
        f.write(f"## Detected Items\n\n")
        f.write(f"**Dishes ({len(dish_names)}):** {', '.join(dish_names)}\n\n")
        f.write(f"**Ingredients ({len(ingredient_names)}):** {', '.join(ingredient_names)}\n\n")
        
        # 詳細検索結果
        f.write(f"## Detailed Search Results\n\n")
        
        # 料理検索結果
        f.write(f"### Dish Search Results\n\n")
        for dish_name in dish_names:
            if dish_name in matches_dict:
                matches = matches_dict[dish_name]
                if isinstance(matches, list) and len(matches) > 0:
                    f.write(f"**{dish_name} (Dish)**\n\n")
                    f.write(f"Found {len(matches)} results:\n\n")
                    for i, match in enumerate(matches, 1):
                        f.write(f"   {i}. **{match['search_name']}** (Score: {match['score']:.2f})\n")
                        f.write(f"      - Source: {match['source']}\n")
                        f.write(f"      - Data Type: {match['data_type']}\n")
                        if match['nutrition']:
                            nutrition = match['nutrition']
                            f.write(f"      - Nutrition (100g): {nutrition.get('calories_kcal', 0):.1f} kcal, ")
                            f.write(f"P:{nutrition.get('protein_g', 0):.1f}g, ")
                            f.write(f"F:{nutrition.get('fat_g', 0):.1f}g, ")
                            f.write(f"C:{nutrition.get('carbohydrates_g', 0):.1f}g\n")
                        f.write(f"\n")
                    f.write(f"\n")
        
        # 食材検索結果
        f.write(f"### Ingredient Search Results\n\n")
        for ingredient_name in ingredient_names:
            if ingredient_name in matches_dict:
                matches = matches_dict[ingredient_name]
                if isinstance(matches, list) and len(matches) > 0:
                    f.write(f"**{ingredient_name} (Ingredient)**\n\n")
                    f.write(f"Found {len(matches)} results:\n\n")
                    for i, match in enumerate(matches, 1):
                        f.write(f"   {i}. **{match['search_name']}** (Score: {match['score']:.2f})\n")
                        f.write(f"      - Source: {match['source']}\n")
                        f.write(f"      - Data Type: {match['data_type']}\n")
                        if match['nutrition']:
                            nutrition = match['nutrition']
                            f.write(f"      - Nutrition (100g): {nutrition.get('calories_kcal', 0):.1f} kcal, ")
                            f.write(f"P:{nutrition.get('protein_g', 0):.1f}g, ")
                            f.write(f"F:{nutrition.get('fat_g', 0):.1f}g, ")
                            f.write(f"C:{nutrition.get('carbohydrates_g', 0):.1f}g\n")
                        f.write(f"\n")
                    f.write(f"\n")
    
    print(f"   💾 包括的結果保存: {main_results_dir}/comprehensive_multi_image_results.md")


def main():
    """メイン関数"""
    print("🚀 Advanced Elasticsearch Strategic Search Test - Standalone Edition v3.0")
    print("📝 APIサーバー不要の直接パイプライン実行 + Advanced Elasticsearch戦略的検索")
    print()
    
    # 環境設定
    setup_environment()
    
    try:
        # Advanced Elasticsearch戦略的検索実行
        result = asyncio.run(analyze_food1_image_with_detailed_search())
        
        if result:
            print("✅ Advanced Elasticsearch戦略的検索テスト成功！")
            print(f"💾 メイン結果保存先: {result['saved_to']}")
            print(f"💾 完全分析結果保存先: {result['api_calls_dir']}")
            return 0
        else:
            print("❌ Advanced Elasticsearch戦略的検索テスト失敗")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ ユーザーによって中断されました")
        return 1
    except Exception as e:
        print(f"❌ 実行中にエラーが発生しました: {e}")
        logger.error(f"メイン実行エラー: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 