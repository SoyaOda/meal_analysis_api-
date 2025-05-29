#!/usr/bin/env python3
"""
Phase 2 Analysis Test Script (v2.1) - calculation_strategyとFDC ID選択をテスト
"""

import requests
import json
import sys
import time
from pathlib import Path

# API設定
BASE_URL = "http://localhost:8000"
PHASE1_ENDPOINT = f"{BASE_URL}/api/v1/meal-analyses/"
PHASE2_ENDPOINT = f"{BASE_URL}/api/v1/meal-analyses/refine"

def test_phase2_analysis_v2():
    """Phase 2の新しい仕様（v2.1）をテスト"""
    
    # 1. Phase 1結果ファイルの確認
    phase1_result_file = "phase1_analysis_result_v2.json"
    if not Path(phase1_result_file).exists():
        print(f"❌ Phase 1 result file not found: {phase1_result_file}")
        print("   Please run test_english_phase1_v2.py first")
        return False
    
    # Phase 1結果を読み込み
    try:
        with open(phase1_result_file, 'r', encoding='utf-8') as f:
            phase1_result = json.load(f)
        print(f"✅ Phase 1 result loaded from {phase1_result_file}")
    except Exception as e:
        print(f"❌ Error loading Phase 1 result: {e}")
        return False
    
    # 2. テスト画像の確認
    test_image_paths = [
        "test_images/food1.jpg",
        "test_images/food2.jpg",
        "test_images/food3.jpg",
    ]
    
    test_image_path = None
    for path in test_image_paths:
        if Path(path).exists():
            test_image_path = Path(path)
            break
    
    if not test_image_path:
        print("❌ Test image not found")
        return False
    
    print(f"📷 Using test image: {test_image_path}")
    
    # 3. Phase 2 API リクエスト
    try:
        print("🚀 Sending Phase 2 analysis request...")
        start_time = time.time()
        
        with open(test_image_path, 'rb') as image_file:
            files = {
                'image': ('test_meal.jpg', image_file, 'image/jpeg')
            }
            data = {
                'phase1_analysis_json': json.dumps(phase1_result, ensure_ascii=False)
            }
            
            response = requests.post(
                PHASE2_ENDPOINT,
                files=files,
                data=data,
                timeout=120  # Phase 2は時間がかかる可能性
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
        print("📋 PHASE 2 ANALYSIS RESULTS (v2.1)")
        print("="*80)
        
        # 基本構造の確認
        if 'dishes' not in result:
            print("❌ Missing 'dishes' field in response")
            return False
        
        dishes = result['dishes']
        print(f"🍽️  Found {len(dishes)} dishes")
        
        # 各料理の詳細表示と検証
        validation_passed = True
        strategy_counts = {"dish_level": 0, "ingredient_level": 0}
        total_fdc_ids_selected = 0
        
        for i, dish in enumerate(dishes, 1):
            print(f"\n📌 DISH {i}: {dish.get('dish_name', 'Unknown')}")
            print(f"   Type: {dish.get('type', 'N/A')}")
            
            # NEW v2.1: calculation_strategy の確認
            strategy = dish.get('calculation_strategy')
            print(f"   🎯 Calculation Strategy: {strategy}")
            
            if strategy not in ['dish_level', 'ingredient_level']:
                print(f"      ❌ Invalid calculation strategy: {strategy}")
                validation_passed = False
            else:
                strategy_counts[strategy] += 1
                print(f"   📝 Strategy Reason: {dish.get('reason_for_strategy', 'N/A')}")
            
            # FDC ID情報の確認
            dish_fdc_id = dish.get('fdc_id')
            if strategy == 'dish_level':
                if dish_fdc_id:
                    print(f"   🏷️  Dish FDC ID: {dish_fdc_id}")
                    print(f"   📄 USDA Source: {dish.get('usda_source_description', 'N/A')}")
                    print(f"   💭 Choice Reason: {dish.get('reason_for_choice', 'N/A')}")
                    total_fdc_ids_selected += 1
                else:
                    print(f"      ⚠️  No FDC ID for dish-level strategy")
            
            # 材料の詳細
            ingredients = dish.get('ingredients', [])
            print(f"   🥗 Ingredients ({len(ingredients)}):")
            
            for ing in ingredients:
                ing_name = ing.get('ingredient_name', 'Unknown')
                weight = ing.get('weight_g', 0)
                ing_fdc_id = ing.get('fdc_id')
                
                print(f"      - {ing_name}: {weight}g", end="")
                if ing_fdc_id:
                    print(f" [FDC ID: {ing_fdc_id}]")
                    total_fdc_ids_selected += 1
                    if ing.get('reason_for_choice'):
                        print(f"        Reason: {ing.get('reason_for_choice')}")
                else:
                    print(f" [No FDC ID]")
            
            # 栄養素情報の確認
            nutrients = dish.get('dish_total_actual_nutrients')
            if nutrients:
                print(f"   🧮 Nutrition (Total): {nutrients.get('calories_kcal', 0):.1f} kcal, "
                      f"{nutrients.get('protein_g', 0):.1f}g protein, "
                      f"{nutrients.get('carbohydrates_g', 0):.1f}g carbs, "
                      f"{nutrients.get('fat_g', 0):.1f}g fat")
            else:
                print(f"   ⚠️  No nutritional data calculated")
        
        # 食事全体の栄養
        total_nutrients = result.get('total_meal_nutrients')
        if total_nutrients:
            print(f"\n🍽️  MEAL TOTAL NUTRITION:")
            print(f"   Energy: {total_nutrients.get('calories_kcal', 0):.1f} kcal")
            print(f"   Protein: {total_nutrients.get('protein_g', 0):.1f}g")
            print(f"   Carbohydrates: {total_nutrients.get('carbohydrates_g', 0):.1f}g")
            print(f"   Fat: {total_nutrients.get('fat_g', 0):.1f}g")
            if total_nutrients.get('fiber_g'):
                print(f"   Fiber: {total_nutrients.get('fiber_g', 0):.1f}g")
            if total_nutrients.get('sodium_mg'):
                print(f"   Sodium: {total_nutrients.get('sodium_mg', 0):.1f}mg")
        
        # v2.1 仕様の検証
        print(f"\n🔍 V2.1 SPECIFICATION VALIDATION:")
        print(f"   📊 Strategy Distribution:")
        print(f"      - Dish Level: {strategy_counts['dish_level']} dishes")
        print(f"      - Ingredient Level: {strategy_counts['ingredient_level']} dishes") 
        print(f"   🏷️  Total FDC IDs Selected: {total_fdc_ids_selected}")
        
        # 警告とエラーの確認
        warnings = result.get('warnings', [])
        errors = result.get('errors', [])
        
        if warnings:
            print(f"   ⚠️  Warnings ({len(warnings)}):")
            for warning in warnings:
                print(f"      - {warning}")
        
        if errors:
            print(f"   ❌ Errors ({len(errors)}):")
            for error in errors:
                print(f"      - {error}")
            validation_passed = False
        
        # 結果保存
        output_file = "phase2_analysis_result_v2.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Full result saved to: {output_file}")
        
        # 最終判定
        success_criteria = [
            len(dishes) > 0,
            all(d.get('calculation_strategy') in ['dish_level', 'ingredient_level'] for d in dishes),
            total_fdc_ids_selected > 0,
            total_nutrients is not None,
            not errors  # エラーがないこと
        ]
        
        if all(success_criteria) and validation_passed:
            print(f"\n✅ Phase 2 v2.1 test PASSED!")
            print("   - All dishes have valid calculation strategies")
            print("   - FDC IDs were successfully selected")
            print("   - Nutritional calculations completed")
            print("   - No critical errors")
            return True
        else:
            print(f"\n❌ Phase 2 v2.1 test FAILED!")
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
    print("🧪 Phase 2 Analysis Test (v2.1) - Strategy & FDC ID Selection")
    print("-" * 70)
    
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
    
    # Phase 2テスト実行
    if test_phase2_analysis_v2():
        print("\n🎉 Phase 2 test passed! v2.1 implementation is working correctly.")
        return 0
    else:
        print("\n💥 Phase 2 test failed! Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 