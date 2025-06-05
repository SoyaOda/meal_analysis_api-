import requests
import json
import time

# API設定（新しいアーキテクチャ版）
BASE_URL = "http://localhost:8000/api/v1"

# テスト画像のパス
image_path = "test_images/food3.jpg"

def test_complete_analysis_v2():
    """完全分析エンドポイント v2.0 をテスト"""
    
    print("=== Complete Meal Analysis Test v2.0 (Component-based) ===")
    print(f"Using image: {image_path}")
    
    try:
        # 完全分析エンドポイントを呼び出し
        with open(image_path, "rb") as f:
            files = {"image": ("food3.jpg", f, "image/jpeg")}
            data = {"save_results": True}  # 結果を保存
            
            print("Starting complete analysis pipeline v2.0...")
            response = requests.post(f"{BASE_URL}/meal-analyses/complete", files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Complete analysis v2.0 successful!")
            
            # 分析ID
            analysis_id = result.get("analysis_id")
            print(f"Analysis ID: {analysis_id}")
            
            # メタデータ
            metadata = result.get("metadata", {})
            print(f"\n📊 Pipeline Info:")
            print(f"- Version: {metadata.get('pipeline_version')}")
            print(f"- Components: {', '.join(metadata.get('components_used', []))}")
            print(f"- Timestamp: {metadata.get('timestamp')}")
            
            # 処理サマリー
            summary = result.get("processing_summary", {})
            print(f"\n📈 Processing Summary:")
            print(f"- Total dishes: {summary.get('total_dishes')}")
            print(f"- Total ingredients: {summary.get('total_ingredients')}")
            print(f"- USDA match rate: {summary.get('usda_match_rate')}")
            print(f"- Total calories: {summary.get('total_calories')} kcal")
            print(f"- Pipeline status: {summary.get('pipeline_status')}")
            print(f"- Processing time: {summary.get('processing_time_seconds', 0):.2f}s")
            
            # Phase1 結果
            phase1_result = result.get("phase1_result", {})
            phase1_dishes = len(phase1_result.get("dishes", []))
            print(f"\n🔍 Phase1 Results:")
            print(f"- Detected dishes: {phase1_dishes}")
            
            # USDA 結果
            usda_result = result.get("usda_result", {})
            print(f"\n🔍 USDA Query Results:")
            print(f"- Matches found: {usda_result.get('matches_count', 0)}")
            print(f"- Match rate: {usda_result.get('match_rate', 0):.1%}")
            
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
                
                # USDA files  
                usda_files = [k for k in saved_files.keys() if k.startswith('usda_')]
                if usda_files:
                    print("  🔍 USDA Query:")
                    for file_key in usda_files:
                        print(f"    - {file_key}: {saved_files[file_key]}")
                
                # Phase2 files
                phase2_files = [k for k in saved_files.keys() if k.startswith('phase2_')]
                if phase2_files:
                    print("  ⚙️ Phase2 (Strategy):")
                    for file_key in phase2_files:
                        print(f"    - {file_key}: {saved_files[file_key]}")
                
                # Nutrition files
                nutrition_files = [k for k in saved_files.keys() if k.startswith('nutrition_')]
                if nutrition_files:
                    print("  🧮 Nutrition Calculation:")
                    for file_key in nutrition_files:
                        print(f"    - {file_key}: {saved_files[file_key]}")
                
                # Pipeline files
                pipeline_files = [k for k in saved_files.keys() if k in ['pipeline_summary', 'complete_log']]
                if pipeline_files:
                    print("  📋 Pipeline Summary:")
                    for file_key in pipeline_files:
                        print(f"    - {file_key}: {saved_files[file_key]}")
            
            # Legacy compatibility
            if result.get("legacy_saved_to"):
                print(f"\n💾 Legacy Result File:")
                print(f"- Path: {result.get('legacy_saved_to')}")
            
            return True, analysis_id
            
        else:
            print("❌ Complete analysis v2.0 failed!")
            print(f"Error: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error during complete analysis v2.0: {e}")
        return False, None

def test_health_check():
    """ヘルスチェックをテスト"""
    print("\n=== Health Check v2.0 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/meal-analyses/health")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Health check successful!")
            print(f"Status: {result.get('status')}")
            print(f"Version: {result.get('version')}")
            print(f"Message: {result.get('message')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during health check: {e}")

def test_pipeline_info():
    """パイプライン情報をテスト"""
    print("\n=== Pipeline Info v2.0 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/meal-analyses/pipeline-info")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Pipeline info retrieved!")
            print(f"Pipeline ID: {result.get('pipeline_id')}")
            print(f"Version: {result.get('version')}")
            
            components = result.get('components', [])
            print(f"\n🔧 Components ({len(components)}):")
            for i, comp in enumerate(components, 1):
                print(f"  {i}. {comp.get('component_name')} ({comp.get('component_type')})")
                print(f"     Executions: {comp.get('execution_count')}")
        else:
            print(f"❌ Pipeline info failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting pipeline info: {e}")

if __name__ == "__main__":
    print("Testing Complete Meal Analysis Pipeline v2.0 (Component-based)")
    print("=" * 70)
    
    # ヘルスチェック
    test_health_check()
    
    # パイプライン情報
    test_pipeline_info()
    
    # 完全分析のテスト
    success, analysis_id = test_complete_analysis_v2()
    
    if success:
        print("\n🎉 All v2.0 tests completed successfully!")
        print("🚀 New component-based architecture is working!")
    else:
        print("\n💥 v2.0 tests failed!")
        print("🔧 Check the component-based pipeline setup.") 