#!/usr/bin/env python3
"""
Food2-5画像の詳細比較テスト
"""
import os
import sys
import asyncio
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """環境変数の設定"""
    load_dotenv()
    
    if not os.environ.get("DEEPINFRA_API_KEY"):
        print("❌ DEEPINFRA_API_KEY が設定されていません")
        sys.exit(1)
    
    os.environ.setdefault("USE_ELASTICSEARCH_SEARCH", "false")

async def test_single_image(image_path, image_name):
    """単一画像の分析テスト"""
    from app_v2.pipeline.orchestrator import MealAnalysisPipeline
    
    if not os.path.exists(image_path):
        print(f"❌ テスト画像が見つかりません: {image_path}")
        return None
    
    print(f"\n🔍 {image_name} Local環境テスト")
    
    try:
        pipeline = MealAnalysisPipeline()
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        start_time = time.time()
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type="image/jpeg",
            optional_text=""
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        final_result = result.get("final_nutrition_result", {})
        total_dishes = len(final_result.get("dishes", []))
        total_calories = final_result.get("total_nutrition", {}).get("calories", 0)
        total_ingredients = sum(len(dish.get("ingredients", [])) for dish in final_result.get("dishes", []))
        
        print(f"✅ 処理時間: {processing_time:.1f}秒")
        print(f"🍽️ 料理数: {total_dishes}")
        print(f"📊 総カロリー: {total_calories:.1f} kcal")
        print(f"🥬 総食材数: {total_ingredients}")
        
        # 料理詳細
        print("📝 料理詳細:")
        for i, dish in enumerate(final_result.get("dishes", []), 1):
            dish_name = dish.get("dish_name", "不明")
            dish_calories = dish.get("total_nutrition", {}).get("calories", 0)
            ingredient_count = len(dish.get("ingredients", []))
            print(f"   {i}. {dish_name}: {dish_calories:.1f} kcal ({ingredient_count}食材)")
            
            # 食材詳細
            for ing in dish.get("ingredients", []):
                ing_name = ing.get("name", "不明")
                ing_weight = ing.get("weight", 0)
                ing_calories = ing.get("nutrition", {}).get("calories", 0)
                print(f"      - {ing_name} ({ing_weight}g): {ing_calories:.1f} kcal")
        
        return {
            "image_name": image_name,
            "total_dishes": total_dishes,
            "total_calories": total_calories,
            "total_ingredients": total_ingredients,
            "processing_time": processing_time,
            "dishes": final_result.get("dishes", [])
        }
        
    except Exception as e:
        print(f"❌ {image_name} 分析エラー: {str(e)}")
        return None

async def main():
    """メイン処理"""
    print("🚀 Food2-5 Local環境詳細テスト")
    print("=" * 60)
    
    setup_environment()
    
    # テスト対象画像
    test_images = [
        ("test_images/food2.jpg", "food2"),
        ("test_images/food3.jpg", "food3"),
        ("test_images/food4.jpg", "food4"),
        ("test_images/food5.jpg", "food5")
    ]
    
    results = []
    
    for image_path, image_name in test_images:
        result = await test_single_image(image_path, image_name)
        if result:
            results.append(result)
    
    # 結果サマリー
    print(f"\n📊 Local環境テスト結果サマリー")
    print("=" * 50)
    for result in results:
        print(f"{result['image_name']}: {result['total_calories']:.1f} kcal ({result['total_dishes']}料理, {result['total_ingredients']}食材)")
    
    # JSON保存
    with open("local_food2_5_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 結果保存: local_food2_5_results.json")

if __name__ == "__main__":
    asyncio.run(main())
