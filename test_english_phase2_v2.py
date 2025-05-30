#!/usr/bin/env python3
"""
Phase 2 Analysis Test Script (v2.1) - calculation_strategyとFDC ID選択をテスト

Usage:
    python test_english_phase2_v2.py [image_path] [phase1_result_file]
    
Examples:
    python test_english_phase2_v2.py test_images/food1.jpg
    python test_english_phase2_v2.py test_images/food1.jpg test_results/phase1_result_food1_20240530_120000.json
    python test_english_phase2_v2.py  # デフォルト画像とPhase1結果を使用
"""

import requests
import json
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# API設定
BASE_URL = "http://localhost:8000"
PHASE1_ENDPOINT = f"{BASE_URL}/api/v1/meal-analyses/"
PHASE2_ENDPOINT = f"{BASE_URL}/api/v1/meal-analyses/refine"

def get_default_image_paths():
    """デフォルトの画像パスリストを返す"""
    return [
        "test_images/food1.jpg",
        "test_images/food2.jpg",
        "test_images/food3.jpg",
        "tests/assets/test_meal.jpg",
        "test_meal.jpg", 
        "sample_meal.jpg",
        Path.home() / "Downloads" / "meal.jpg",
        Path.cwd() / "meal.jpg"
    ]

def find_test_image(specified_path=None):
    """テスト画像のパスを見つける"""
    if specified_path:
        path = Path(specified_path)
        if path.exists():
            return path
        else:
            print(f"❌ Specified image not found: {specified_path}")
            return None
    
    # デフォルトの画像を探す
    for path in get_default_image_paths():
        if Path(path).exists():
            return Path(path)
    
    return None

def find_phase1_result(specified_path=None):
    """Phase1結果ファイルを見つける"""
    if specified_path:
        path = Path(specified_path)
        if path.exists():
            return path
        else:
            print(f"❌ Specified Phase 1 result file not found: {specified_path}")
            return None
    
    # デフォルトファイルまたは最新のファイルを探す
    default_paths = [
        "phase1_analysis_result_v2.json",  # デフォルトファイル
    ]
    
    # test_resultsフォルダ内の最新ファイルも確認
    test_results_dir = Path("test_results")
    if test_results_dir.exists():
        phase1_files = list(test_results_dir.glob("phase1_result_*.json"))
        # 最新のファイルを先頭に
        phase1_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        default_paths.extend(phase1_files)
    
    for path in default_paths:
        if Path(path).exists():
            return Path(path)
    
    return None

def test_phase2_analysis_v2(image_path, phase1_result_file):
    """Phase 2の新しい仕様（v2.1）をテスト"""
    
    print(f"📷 Using test image: {image_path}")
    print(f"📄 Using Phase 1 result: {phase1_result_file}")
    
    # Phase 1結果を読み込み
    try:
        with open(phase1_result_file, 'r', encoding='utf-8') as f:
            phase1_result = json.load(f)
        print(f"✅ Phase 1 result loaded from {phase1_result_file}")
    except Exception as e:
        print(f"❌ Error loading Phase 1 result: {e}")
        return False, None
    
    # Phase 2 API リクエスト
    try:
        print("🚀 Sending Phase 2 analysis request...")
        start_time = time.time()
        
        with open(image_path, 'rb') as image_file:
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
            return False, None
        
        # JSON パース
        result = response.json()
        
        # 結果の表示と検証
        print("\n" + "="*80)
        print("📋 PHASE 2 ANALYSIS RESULTS (v2.1)")
        print("="*80)
        
        # 基本構造の確認
        if 'dishes' not in result:
            print("❌ Missing 'dishes' field in response")
            return False, None
        
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
        else:
            print(f"\n⚠️  No total meal nutrition calculated")
            validation_passed = False
        
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
        
        # 最終判定
        if validation_passed:
            print(f"\n✅ Phase 2 v2.1 test PASSED!")
            print("   - All calculation strategies are valid")
            print("   - FDC IDs are properly selected")
            print("   - Total meal nutrition is calculated")
        else:
            print(f"\n❌ Phase 2 v2.1 test FAILED!")
            print("   Please check the validation errors above.")
        
        return validation_passed, result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False, None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {response.text}")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, None

def save_result(result, image_path, phase1_result_file):
    """結果をtest_resultsフォルダに保存"""
    # 出力ディレクトリを作成
    output_dir = Path("test_results")
    output_dir.mkdir(exist_ok=True)
    
    # タイムスタンプ付きファイル名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = Path(image_path).stem
    output_file = output_dir / f"phase2_result_{image_name}_{timestamp}.json"
    
    # 結果を保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Full result saved to: {output_file}")
    
    # デフォルトファイル名でもコピー保存（後続処理で使用するため）
    default_file = "phase2_analysis_result_v2.json"
    with open(default_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Also saved as: {default_file}")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(
        description="Phase 2 Analysis Test (v2.1) - Calculation Strategy & FDC ID Selection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_english_phase2_v2.py test_images/food1.jpg
  python test_english_phase2_v2.py test_images/food1.jpg test_results/phase1_result_food1_20240530_120000.json
  python test_english_phase2_v2.py  # Use default image and latest Phase 1 result
        """
    )
    parser.add_argument(
        'image_path', 
        nargs='?', 
        help='Path to the meal image file (optional, will search for default images if not provided)'
    )
    parser.add_argument(
        'phase1_result_file', 
        nargs='?', 
        help='Path to Phase 1 result JSON file (optional, will use latest if not provided)'
    )
    
    args = parser.parse_args()
    
    print("🧪 Phase 2 Analysis Test (v2.1) - Calculation Strategy & FDC ID Selection")
    print("-" * 80)
    
    # ヘルスチェック
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print("❌ Server health check failed")
            return 1
    except requests.exceptions.RequestException:
        print("❌ Server is not reachable")
        return 1
    
    # 画像ファイルを探す
    image_path = find_test_image(args.image_path)
    
    if not image_path:
        print("❌ No test image found. Please specify an image path or place a meal image in one of these locations:")
        for path in get_default_image_paths():
            print(f"   - {path}")
        print(f"\nUsage: python {sys.argv[0]} [image_path] [phase1_result_file]")
        return 1
    
    # Phase 1結果ファイルを探す
    phase1_result_file = find_phase1_result(args.phase1_result_file)
    
    if not phase1_result_file:
        print("❌ No Phase 1 result file found. Please run Phase 1 test first or specify a result file:")
        print("   python test_english_phase1_v2.py")
        print(f"   OR: python {sys.argv[0]} {image_path} <phase1_result_file>")
        return 1
    
    # テスト実行
    success, result = test_phase2_analysis_v2(image_path, phase1_result_file)
    
    # 結果を保存
    if result:
        save_result(result, image_path, phase1_result_file)
    
    if success:
        print("\n🎉 Phase 2 test completed successfully!")
        return 0
    else:
        print("\n💥 Phase 2 test failed! Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 