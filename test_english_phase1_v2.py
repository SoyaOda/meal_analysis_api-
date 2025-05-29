#!/usr/bin/env python3
"""
Phase 1 Analysis Test Script (v2.1) - USDAクエリ候補を含む新しい出力をテスト
"""

import requests
import json
import sys
import time
from pathlib import Path

# API設定
BASE_URL = "http://localhost:8000"
MEAL_ANALYSES_ENDPOINT = f"{BASE_URL}/api/v1/meal-analyses/"

def test_phase1_analysis_v2():
    """Phase 1の新しい仕様（v2.1）をテスト"""
    
    # テスト画像を探す
    test_image_paths = [
        "test_images/food1.jpg",  # 存在することを確認済み
        "test_images/food2.jpg",
        "test_images/food3.jpg",
        "tests/assets/test_meal.jpg",
        "test_meal.jpg", 
        "sample_meal.jpg",
        # 他の一般的な場所も試す
        Path.home() / "Downloads" / "meal.jpg",
        Path.cwd() / "meal.jpg"
    ]
    
    test_image_path = None
    for path in test_image_paths:
        if Path(path).exists():
            test_image_path = Path(path)
            break
    
    if not test_image_path:
        print("❌ Test image not found. Please place a meal image in one of these locations:")
        for path in test_image_paths:
            print(f"   - {path}")
        return False
    
    print(f"📷 Using test image: {test_image_path}")
    
    # API リクエスト
    try:
        print("🚀 Sending Phase 1 analysis request...")
        start_time = time.time()
        
        with open(test_image_path, 'rb') as image_file:
            files = {
                'image': ('test_meal.jpg', image_file, 'image/jpeg')
            }
            data = {
                'optional_text': 'This is a test meal for Phase 1 analysis with USDA query candidates.'
            }
            
            response = requests.post(
                MEAL_ANALYSES_ENDPOINT,
                files=files,
                data=data,
                timeout=60
            )
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  Request completed in {elapsed_time:.2f} seconds")
        
        # レスポンス確認
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error response: {response.text}")
            return False
        
        # JSON パース
        result = response.json()
        
        # 結果の表示と検証
        print("\n" + "="*80)
        print("📋 PHASE 1 ANALYSIS RESULTS (v2.1)")
        print("="*80)
        
        # 基本構造の確認
        if 'dishes' not in result:
            print("❌ Missing 'dishes' field in response")
            return False
        
        dishes = result['dishes']
        print(f"🍽️  Found {len(dishes)} dishes")
        
        # 各料理の詳細表示
        for i, dish in enumerate(dishes, 1):
            print(f"\n📌 DISH {i}: {dish.get('dish_name', 'Unknown')}")
            print(f"   Type: {dish.get('type', 'N/A')}")
            print(f"   Quantity: {dish.get('quantity_on_plate', 'N/A')}")
            
            # 材料リスト
            ingredients = dish.get('ingredients', [])
            print(f"   🥗 Ingredients ({len(ingredients)}):")
            for ing in ingredients:
                print(f"      - {ing.get('ingredient_name', 'Unknown')}: {ing.get('weight_g', 0)}g")
            
            # NEW: USDAクエリ候補の確認 (v2.1の重要な新機能)
            usda_candidates = dish.get('usda_query_candidates', [])
            print(f"   🔍 USDA Query Candidates ({len(usda_candidates)}):")
            
            if not usda_candidates:
                print("      ❌ No USDA query candidates found - this is a problem for v2.1!")
                return False
            
            for j, candidate in enumerate(usda_candidates, 1):
                print(f"      {j}. Query: '{candidate.get('query_term', 'N/A')}'")
                print(f"         Granularity: {candidate.get('granularity_level', 'N/A')}")
                print(f"         Original: {candidate.get('original_term', 'N/A')}")
                print(f"         Reason: {candidate.get('reason_for_query', 'N/A')}")
        
        # v2.1 仕様の検証
        print(f"\n🔍 V2.1 SPECIFICATION VALIDATION:")
        
        validation_passed = True
        
        # 1. 全ての料理にUSDAクエリ候補があるか
        for dish in dishes:
            if not dish.get('usda_query_candidates'):
                print(f"   ❌ Dish '{dish.get('dish_name')}' has no USDA query candidates")
                validation_passed = False
            else:
                print(f"   ✅ Dish '{dish.get('dish_name')}' has {len(dish.get('usda_query_candidates'))} USDA query candidates")
        
        # 2. クエリ候補の粒度レベルが適切か
        granularity_levels = set()
        for dish in dishes:
            for candidate in dish.get('usda_query_candidates', []):
                level = candidate.get('granularity_level')
                if level in ['dish', 'ingredient', 'branded_product']:
                    granularity_levels.add(level)
                else:
                    print(f"   ❌ Invalid granularity level: {level}")
                    validation_passed = False
        
        print(f"   📊 Granularity levels found: {list(granularity_levels)}")
        
        # 3. 理由付けがあるか
        reasoning_count = 0
        total_candidates = 0
        for dish in dishes:
            for candidate in dish.get('usda_query_candidates', []):
                total_candidates += 1
                if candidate.get('reason_for_query'):
                    reasoning_count += 1
        
        reasoning_percentage = (reasoning_count / total_candidates * 100) if total_candidates > 0 else 0
        print(f"   📝 Query reasoning coverage: {reasoning_percentage:.1f}% ({reasoning_count}/{total_candidates})")
        
        if reasoning_percentage < 80:
            print(f"   ⚠️  Low reasoning coverage - should be > 80%")
            validation_passed = False
        
        # 結果保存
        output_file = "phase1_analysis_result_v2.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Full result saved to: {output_file}")
        
        # 最終判定
        if validation_passed:
            print(f"\n✅ Phase 1 v2.1 test PASSED!")
            print("   - All dishes have USDA query candidates")
            print("   - Granularity levels are valid") 
            print("   - Reasoning coverage is sufficient")
            return True
        else:
            print(f"\n❌ Phase 1 v2.1 test FAILED!")
            print("   Please check the validation errors above.")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("🧪 Phase 1 Analysis Test (v2.1) - USDA Query Candidates")
    print("-" * 60)
    
    # ヘルスチェック
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print("❌ Server health check failed")
            return 1
    except:
        print("❌ Cannot connect to server. Is it running on http://localhost:8000?")
        return 1
    
    # Phase 1テスト実行
    if test_phase1_analysis_v2():
        print("\n🎉 All tests passed! Ready for Phase 2 integration.")
        return 0
    else:
        print("\n💥 Tests failed! Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 