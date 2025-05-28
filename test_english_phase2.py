import requests
import json
import asyncio
import httpx

# API設定
BASE_URL = "http://localhost:8000/api/v1"

# テスト画像のパス（英語の食材名を含む画像を使用）
image_path = "test_images/food3.jpg"

async def run_phase1_and_phase2():
    """フェーズ1→フェーズ2の流れをテスト"""
    
    print("=== Phase 1: Initial Analysis ===")
    
    # フェーズ1: 画像分析
    with open(image_path, "rb") as f:
        files = {"image": ("food3.jpg", f, "image/jpeg")}
        response = requests.post(f"{BASE_URL}/meal-analyses", files=files)
    
    if response.status_code != 200:
        print(f"Phase 1 failed: {response.status_code}")
        print(response.text)
        return
    
    phase1_result = response.json()
    print("Phase 1 successful!")
    print(json.dumps(phase1_result, indent=2))
    
    # 食材名を表示（英語になっているはず）
    print("\nDetected ingredients:")
    for dish in phase1_result.get("dishes", []):
        print(f"  Dish: {dish['dish_name']}")
        for ingredient in dish.get("ingredients", []):
            print(f"    - {ingredient['ingredient_name']}: {ingredient['weight_g']}g")
    
    print("\n=== Phase 2: USDA Refinement ===")
    
    # フェーズ2: USDA精緻化
    with open(image_path, "rb") as f:
        files = {
            "image": ("food3.jpg", f, "image/jpeg"),
            "initial_analysis_data": (None, json.dumps(phase1_result), "application/json")
        }
        response = requests.post(f"{BASE_URL}/meal-analyses/refine", files=files)
    
    print(f"Phase 2 status: {response.status_code}")
    
    if response.status_code == 200:
        phase2_result = response.json()
        print("Phase 2 successful!")
        print(json.dumps(phase2_result, indent=2))
        
        # USDA FDC IDを表示
        print("\nUSDA matches:")
        for dish in phase2_result.get("dishes", []):
            print(f"  Dish: {dish['dish_name']}")
            for ingredient in dish.get("ingredients", []):
                if ingredient.get("fdc_id"):
                    print(f"    - {ingredient['ingredient_name']}: FDC ID {ingredient['fdc_id']} ({ingredient.get('usda_source_description', 'N/A')})")
                else:
                    print(f"    - {ingredient['ingredient_name']}: No USDA match")
                    
                # 栄養素情報を表示
                nutrients = ingredient.get("key_nutrients_per_100g", {})
                if nutrients:
                    print(f"      Nutrients per 100g: {nutrients}")
    else:
        print("Phase 2 failed!")
        print(response.text)

if __name__ == "__main__":
    print("Testing Meal Analysis API (English version)")
    print(f"Using image: {image_path}")
    asyncio.run(run_phase1_and_phase2()) 