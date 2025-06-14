#!/usr/bin/env python3
"""
Local Nutrition Search System Test v2.0

nutrition_db_experimentで実装したローカル検索システムと統合したシステムをテスト
"""

import requests
import json
import time
import os
from datetime import datetime

# API設定（新しいアーキテクチャ版）
BASE_URL = "http://localhost:8000/api/v1"

# テスト画像のパス
image_path = "test_images/food3.jpg"

def test_local_nutrition_search_complete_analysis():
    """ローカル栄養データベース検索を使用した完全分析をテスト"""
    
    print("=== Local Nutrition Search Complete Analysis Test v2.0 ===")
    print(f"Using image: {image_path}")
    print("🔍 Testing nutrition_db_experiment integration")
    
    try:
        # 完全分析エンドポイントを呼び出し
        with open(image_path, "rb") as f:
            files = {"image": ("food3.jpg", f, "image/jpeg")}
            data = {}  # 結果を保存
            
            print("Starting complete analysis with local nutrition search...")
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/meal-analyses/complete", files=files, data=data)
            end_time = time.time()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Local nutrition search analysis successful!")
            
            # 分析ID
            analysis_id = result.get("analysis_id")
            print(f"Analysis ID: {analysis_id}")
            
            # メタデータ（検索方法の確認）
            metadata = result.get("metadata", {})
            print(f"\n📊 Pipeline Info:")
            print(f"- Version: {metadata.get('pipeline_version')}")
            print(f"- Components: {', '.join(metadata.get('components_used', []))}")
            print(f"- Nutrition Search Method: {metadata.get('nutrition_search_method')}")
            print(f"- Timestamp: {metadata.get('timestamp')}")
            
            # 処理サマリー
            summary = result.get("processing_summary", {})
            print(f"\n📈 Processing Summary:")
            print(f"- Total dishes: {summary.get('total_dishes')}")
            print(f"- Total ingredients: {summary.get('total_ingredients')}")
            print(f"- Search method: {summary.get('search_method')}")
            
            # ローカル検索結果
            nutrition_search_result = result.get("nutrition_search_result", {})
            print(f"\n🔍 Local Nutrition Search Results:")
            print(f"- Matches found: {nutrition_search_result.get('matches_count', 0)}")
            print(f"- Match rate: {nutrition_search_result.get('match_rate', 0):.1%}")
            print(f"- Search method: {nutrition_search_result.get('search_method', 'unknown')}")
            
            search_summary = nutrition_search_result.get('search_summary', {})
            if search_summary:
                print(f"- Database source: {search_summary.get('database_source', 'unknown')}")
                print(f"- Total searches: {search_summary.get('total_searches', 0)}")
                print(f"- Successful matches: {search_summary.get('successful_matches', 0)}")
                print(f"- Failed searches: {search_summary.get('failed_searches', 0)}")
            
            # Phase1 結果
            phase1_result = result.get("phase1_result", {})
            phase1_dishes = len(phase1_result.get("dishes", []))
            print(f"\n🔍 Phase1 Results:")
            print(f"- Detected dishes: {phase1_dishes}")
            
            if phase1_dishes > 0:
                print("- Dish details:")
                for i, dish in enumerate(phase1_result.get("dishes", [])[:3], 1):  # 最初の3料理のみ表示
                    print(f"  {i}. {dish.get('dish_name', 'Unknown')}")
                    ingredients = dish.get('ingredients', [])
                    print(f"     Ingredients ({len(ingredients)}): {', '.join([ing.get('ingredient_name', 'Unknown') for ing in ingredients[:5]])}")
                    if len(ingredients) > 5:
                        print(f"     ... and {len(ingredients) - 5} more")
            
            # 最終栄養価結果（暫定）
            final_nutrition = result.get("final_nutrition_result", {})
            total_nutrients = final_nutrition.get("total_meal_nutrients", {})
            
            print(f"\n🍽 Final Meal Nutrition (Preliminary):")
            print(f"- Calories: {total_nutrients.get('calories_kcal', 0):.2f} kcal")
            print(f"- Protein: {total_nutrients.get('protein_g', 0):.2f} g")
            print(f"- Carbohydrates: {total_nutrients.get('carbohydrates_g', 0):.2f} g")
            print(f"- Fat: {total_nutrients.get('fat_g', 0):.2f} g")
            
            # 保存された詳細ログファイル
            analysis_folder = result.get("analysis_folder")
            saved_files = result.get("saved_files", {})
            
            if analysis_folder:
                print(f"\n📁 Analysis Folder:")
                print(f"- Path: {analysis_folder}")
                print(f"- Contains organized phase-by-phase results")
            
            if saved_files:
                print(f"\n💾 Saved Files by Phase ({len(saved_files)} total):")
                
                # Phase1 files
                phase1_files = [k for k in saved_files.keys() if k.startswith('phase1_')]
                if phase1_files:
                    print("  📊 Phase1 (Image Analysis):")
                    for file_key in phase1_files:
                        print(f"    - {file_key}: {saved_files[file_key]}")
                
                # Local search files  
                search_files = [k for k in saved_files.keys() if 'nutrition_search' in k or 'local' in k.lower()]
                if search_files:
                    print("  🔍 Local Nutrition Search:")
                    for file_key in search_files:
                        print(f"    - {file_key}: {saved_files[file_key]}")
                
                # Pipeline files
                pipeline_files = [k for k in saved_files.keys() if k in ['pipeline_summary', 'complete_log']]
                if pipeline_files:
                    print("  📋 Pipeline Summary:")
                    for file_key in pipeline_files:
                        print(f"    - {file_key}: {saved_files[file_key]}")
            
            return True, analysis_id
            
        else:
            print("❌ Local nutrition search analysis failed!")
            print(f"Error: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error during local nutrition search analysis: {e}")
        return False, None

def test_pipeline_info_local():
    """ローカル検索パイプライン情報をテスト"""
    print("\n=== Local Nutrition Search Pipeline Info ===")
    
    try:
        response = requests.get(f"{BASE_URL}/meal-analyses/pipeline-info")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Pipeline info retrieved!")
            print(f"Pipeline ID: {result.get('pipeline_id')}")
            print(f"Version: {result.get('version')}")
            print(f"Nutrition Search Method: {result.get('nutrition_search_method')}")
            
            components = result.get('components', [])
            print(f"\n🔧 Components ({len(components)}):")
            for i, comp in enumerate(components, 1):
                print(f"  {i}. {comp.get('component_name')} ({comp.get('component_type')})")
                print(f"     Executions: {comp.get('execution_count')}")
        else:
            print(f"❌ Pipeline info failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting pipeline info: {e}")

def test_nutrition_db_experiment_availability():
    """nutrition_db_experimentの利用可能性をテスト"""
    print("\n=== Nutrition DB Experiment Availability Test ===")
    
    try:
        # nutrition_db_experimentディレクトリの存在確認
        nutrition_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nutrition_db_experiment")
        
        print(f"🔍 Checking nutrition_db_experiment path: {nutrition_db_path}")
        
        if os.path.exists(nutrition_db_path):
            print("✅ nutrition_db_experiment directory found")
            
            # データベースファイルの存在確認（正しいパスに修正）
            db_files = [
                "nutrition_db/dish_db.json",
                "nutrition_db/ingredient_db.json", 
                "nutrition_db/branded_db.json",
                "nutrition_db/unified_nutrition_db.json"
            ]
            
            print("📊 Database Files:")
            for db_file in db_files:
                full_path = os.path.join(nutrition_db_path, db_file)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            # 大きなファイルの場合は一部だけ読み込み
                            if os.path.getsize(full_path) > 10 * 1024 * 1024:  # 10MB以上
                                f.seek(0)
                                first_chunk = f.read(1024)
                                if first_chunk.strip().startswith('['):
                                    # JSONファイルサイズから推定アイテム数を計算
                                    file_size_mb = os.path.getsize(full_path) / (1024 * 1024)
                                    estimated_items = int(file_size_mb * 1000)  # 大まかな推定
                                    print(f"  ✅ {db_file}: ~{estimated_items} items (file size: {file_size_mb:.1f}MB)")
                                else:
                                    print(f"  ✅ {db_file}: Large file ({file_size_mb:.1f}MB)")
                            else:
                                data = json.load(f)
                                print(f"  ✅ {db_file}: {len(data)} items")
                    except Exception as e:
                        print(f"  ❌ {db_file}: Error reading - {e}")
                else:
                    print(f"  ❌ {db_file}: Not found")
            
            # 検索コンポーネントのインポート確認
            print("🔧 Search Components:")
            
            search_service_path = os.path.join(nutrition_db_path, "search_service")
            if os.path.exists(search_service_path):
                print(f"  ✅ search_service directory found: {search_service_path}")
                
                # 主要ファイルの存在確認
                component_files = [
                    "nlp/query_preprocessor.py",
                    "api/search_handler.py", 
                    "api/query_builder.py"
                ]
                
                for comp_file in component_files:
                    full_path = os.path.join(search_service_path, comp_file)
                    if os.path.exists(full_path):
                        print(f"    ✅ {comp_file}")
                    else:
                        print(f"    ❌ {comp_file}: Not found")
            else:
                print(f"  ❌ search_service directory not found")
                
        else:
            print("❌ nutrition_db_experiment directory not found")
            print("💡 Please ensure nutrition_db_experiment is in the same directory as this script")
            
    except Exception as e:
        print(f"❌ Error checking nutrition_db_experiment: {e}")

def compare_search_methods():
    """ローカル検索と他の検索方法の比較テスト"""
    print("\n=== Search Methods Comparison ===")
    print("🔬 This would compare local search vs other search methods")
    print("📝 TODO: Implement when multiple methods are available")

if __name__ == "__main__":
    print("Testing Local Nutrition Search Integration v2.0")
    print("=" * 70)
    
    # nutrition_db_experimentの利用可能性チェック
    test_nutrition_db_experiment_availability()
    
    # パイプライン情報
    test_pipeline_info_local()
    
    # ローカル栄養検索を使った完全分析のテスト
    success, analysis_id = test_local_nutrition_search_complete_analysis()
    
    if success:
        print("\n🎉 Local nutrition search integration test completed successfully!")
        print("🚀 nutrition_db_experiment search system is working with the meal analysis pipeline!")
        print(f"📋 Analysis ID: {analysis_id}")
    else:
        print("\n💥 Local nutrition search integration test failed!")
        print("🔧 Check the local search system setup and logs.")
        
    # 比較テスト（将来実装予定）
    compare_search_methods() 