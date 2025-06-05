import requests
import json
import asyncio
from pathlib import Path

# API設定
BASE_URL = "http://localhost:8000/api/v1"

# テスト画像のパス
image_path = "test_images/food3.jpg"

def test_complete_analysis():
    """完全分析エンドポイントをテスト"""
    
    print("=== Complete Meal Analysis Test ===")
    print(f"Using image: {image_path}")
    
    try:
        # 完全分析エンドポイントを呼び出し
        with open(image_path, "rb") as f:
            files = {"image": ("food3.jpg", f, "image/jpeg")}
            data = {"save_results": True}  # 結果を保存
            
            print("Starting complete analysis pipeline...")
            response = requests.post(f"{BASE_URL}/meal-analyses/complete", files=files, data=data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Complete analysis successful!")
            
            # 分析ID
            analysis_id = result.get("analysis_id")
            print(f"Analysis ID: {analysis_id}")
            
            # 処理サマリー
            summary = result.get("processing_summary", {})
            print(f"\n📊 Processing Summary:")
            print(f"- Total dishes: {summary.get('total_dishes')}")
            print(f"- Total ingredients: {summary.get('total_ingredients')}")
            print(f"- USDA match rate: {summary.get('usda_match_rate')}")
            print(f"- Total calories: {summary.get('total_calories')} kcal")
            print(f"- Pipeline status: {summary.get('pipeline_status')}")
            
            # 保存先
            saved_to = result.get("saved_to")
            if saved_to:
                print(f"- Results saved to: {saved_to}")
            
            # 最終栄養価結果
            final_nutrition = result.get("final_nutrition_result", {})
            total_nutrients = final_nutrition.get("total_meal_nutrients", {})
            
            print(f"\n🍽 Final Meal Nutrition:")
            print(f"- Calories: {total_nutrients.get('calories_kcal', 0):.2f} kcal")
            print(f"- Protein: {total_nutrients.get('protein_g', 0):.2f} g")
            print(f"- Carbohydrates: {total_nutrients.get('carbohydrates_g', 0):.2f} g")
            print(f"- Fat: {total_nutrients.get('fat_g', 0):.2f} g")
            
            # 各フェーズの結果数
            phase1_dishes = len(result.get("phase1_result", {}).get("dishes", []))
            phase2_dishes = len(result.get("phase2_result", {}).get("dishes", []))
            final_dishes = len(final_nutrition.get("dishes", []))
            
            print(f"\n📈 Pipeline Progress:")
            print(f"- Phase 1 dishes: {phase1_dishes}")
            print(f"- Phase 2 dishes: {phase2_dishes}")
            print(f"- Final dishes: {final_dishes}")
            print(f"- USDA matches: {result.get('usda_matches_count', 0)}")
            
            return True, analysis_id
            
        else:
            print("❌ Complete analysis failed!")
            print(f"Error: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error during complete analysis: {e}")
        return False, None

def test_list_results():
    """保存された結果の一覧を取得"""
    
    print("\n=== List Saved Results ===")
    
    try:
        response = requests.get(f"{BASE_URL}/meal-analyses/results")
        
        if response.status_code == 200:
            results = response.json()
            total = results.get("total_results", 0)
            print(f"📁 Total saved results: {total}")
            
            if total > 0:
                print("\nRecent results:")
                for i, result in enumerate(results.get("results", [])[:5]):  # 最新5件
                    print(f"{i+1}. {result.get('filename')}")
                    print(f"   ID: {result.get('analysis_id')}")
                    print(f"   Time: {result.get('timestamp')}")
                    summary = result.get('summary', {})
                    print(f"   Calories: {summary.get('total_calories', 0)} kcal")
                    print()
            
        else:
            print(f"❌ Failed to list results: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error listing results: {e}")

def test_get_specific_result(analysis_id):
    """特定の分析結果を取得"""
    
    if not analysis_id:
        return
        
    print(f"\n=== Get Specific Result: {analysis_id} ===")
    
    try:
        response = requests.get(f"{BASE_URL}/meal-analyses/results/{analysis_id}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Retrieved result for analysis ID: {analysis_id}")
            
            # メタデータ
            metadata = result.get("metadata", {})
            print(f"Timestamp: {metadata.get('timestamp')}")
            print(f"Pipeline: {metadata.get('processing_pipeline')}")
            
            # 処理サマリー
            summary = result.get("processing_summary", {})
            print(f"Status: {summary.get('pipeline_status')}")
            print(f"Total calories: {summary.get('total_calories')} kcal")
            
        else:
            print(f"❌ Failed to get result: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting specific result: {e}")

if __name__ == "__main__":
    print("Testing Complete Meal Analysis Pipeline")
    print("=" * 50)
    
    # 完全分析のテスト
    success, analysis_id = test_complete_analysis()
    
    if success:
        # 結果一覧のテスト
        test_list_results()
        
        # 特定結果取得のテスト
        test_get_specific_result(analysis_id)
        
        print("\n🎉 All tests completed!")
    else:
        print("\n💥 Complete analysis test failed!") 