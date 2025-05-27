import requests
import sys
import os
import json

def test_health_check():
    """ヘルスチェックエンドポイントのテスト"""
    response = requests.get("http://localhost:8000/health")
    print(f"Health check status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_api_docs():
    """APIドキュメントの確認"""
    response = requests.get("http://localhost:8000/docs")
    print(f"\nAPI docs status: {response.status_code}")
    return response.status_code == 200

def test_meal_analysis_without_image():
    """画像なしでのエラーハンドリングテスト"""
    response = requests.post("http://localhost:8000/api/v1/meal-analyses")
    print(f"\nNo image test status: {response.status_code}")
    if response.status_code == 422:  # FastAPIのバリデーションエラー
        print("Expected validation error received")
        print(f"Response: {response.json()}")
        return True
    return False

def test_meal_analysis_with_image(image_path, description=""):
    """実際の食事画像でのAPIテスト"""
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return False
    
    # APIにリクエスト送信
    with open(image_path, "rb") as f:
        files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
        data = {"text": description} if description else {}
        
        print(f"\nSending image to API: {image_path}")
        if description:
            print(f"With description: {description}")
        
        response = requests.post(
            "http://localhost:8000/api/v1/meal-analyses",
            files=files,
            data=data
        )
    
    print(f"Meal analysis status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("Analysis successful!")
        print(f"Response structure: {list(result.keys())}")
        
        if "dishes" in result:
            print(f"\nNumber of dishes found: {len(result['dishes'])}")
            for i, dish in enumerate(result['dishes'], 1):
                print(f"\n--- Dish {i} ---")
                print(f"  Name: {dish.get('dish_name', 'N/A')}")
                print(f"  Type: {dish.get('type', 'N/A')}")
                print(f"  Quantity: {dish.get('quantity_on_plate', 'N/A')}")
                print(f"  Number of ingredients: {len(dish.get('ingredients', []))}")
                
                if dish.get('ingredients'):
                    print("  Ingredients:")
                    for ingredient in dish['ingredients'][:5]:  # 最初の5つの材料を表示
                        print(f"    - {ingredient.get('ingredient_name', 'N/A')}: {ingredient.get('weight_g', 0)}g")
                    if len(dish.get('ingredients', [])) > 5:
                        print(f"    ... and {len(dish['ingredients']) - 5} more ingredients")
        
        # JSON全体を見やすく表示（デバッグ用）
        print(f"\nFull JSON response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        try:
            error_detail = response.json()
            print(f"Error response: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
        except:
            print(f"Error response text: {response.text}")
    
    return response.status_code == 200

def main():
    """メインテスト実行"""
    print("=== Meal Analysis API Test ===\n")
    
    # 基本的なテスト
    basic_tests = [
        ("Health Check", test_health_check),
        ("API Documentation", test_api_docs),
        ("Error Handling (No Image)", test_meal_analysis_without_image),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in basic_tests:
        print(f"\n--- Testing: {test_name} ---")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    # 実際の画像でのテスト
    print(f"\n\n=== Real Image Analysis Tests ===")
    
    image_tests = [
        ("test_images/food1.jpg", "朝食の画像です"),
        ("test_images/food2.jpg", "昼食の画像です"),
        ("test_images/food3.jpg", "夕食の画像です"),
    ]
    
    for image_path, description in image_tests:
        print(f"\n--- Testing: {image_path} ---")
        try:
            if test_meal_analysis_with_image(image_path, description):
                print(f"✅ Image analysis for {os.path.basename(image_path)} PASSED")
                passed += 1
            else:
                print(f"❌ Image analysis for {os.path.basename(image_path)} FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ Image analysis for {os.path.basename(image_path)} FAILED with exception: {e}")
            print(f"Exception details: {str(e)}")
            failed += 1
    
    print(f"\n\n=== Test Summary ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 