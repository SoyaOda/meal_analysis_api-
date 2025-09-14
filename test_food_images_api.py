#!/usr/bin/env python3
"""
Food2-5画像のCloud Run API詳細テスト
"""
import json
import time
import requests
from pathlib import Path
import hashlib

def get_image_hash(image_path):
    """画像のSHA256ハッシュを取得"""
    with open(image_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def test_api_image(image_path, image_name, api_url):
    """Cloud Run APIで単一画像をテスト"""
    print(f"\n🔍 {image_name} Cloud Run APIテスト")
    
    # 画像ハッシュ確認
    image_hash = get_image_hash(image_path)
    print(f"📄 Hash: {image_hash}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            
            start_time = time.time()
            response = requests.post(api_url, files=files, timeout=60)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                dishes = result.get('dishes', [])
                total_dishes = len(dishes)
                total_calories = sum(dish.get('total_calories', 0) for dish in dishes)
                total_ingredients = sum(len(dish.get('ingredients', [])) for dish in dishes)
                
                print(f"✅ 処理時間: {processing_time:.1f}秒")
                print(f"🍽️ 料理数: {total_dishes}")
                print(f"📊 総カロリー: {total_calories:.1f} kcal")
                print(f"🥬 総食材数: {total_ingredients}")
                
                # 料理詳細
                print("📝 料理詳細:")
                for i, dish in enumerate(dishes, 1):
                    dish_name = dish.get('name', '不明')
                    dish_calories = dish.get('total_calories', 0)
                    ingredients = dish.get('ingredients', [])
                    print(f"   {i}. {dish_name}: {dish_calories:.1f} kcal ({len(ingredients)}食材)")
                    
                    # 食材詳細
                    for ing in ingredients:
                        ing_name = ing.get('name', '不明')
                        ing_weight = ing.get('weight', 0)
                        ing_calories = ing.get('calories', 0)
                        print(f"      - {ing_name} ({ing_weight}g): {ing_calories:.1f} kcal")
                
                return {
                    "image_name": image_name,
                    "image_hash": image_hash,
                    "total_dishes": total_dishes,
                    "total_calories": total_calories,
                    "total_ingredients": total_ingredients,
                    "processing_time": processing_time,
                    "dishes": dishes
                }
            else:
                print(f"❌ APIエラー: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return None
                
    except Exception as e:
        print(f"❌ {image_name} APIエラー: {str(e)}")
        return None

def main():
    """メイン処理"""
    print("🚀 Food2-5 Cloud Run API詳細テスト")
    print("=" * 60)
    
    api_url = "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/complete"
    
    # テスト対象画像
    test_images = [
        ("test_images/food2.jpg", "food2"),
        ("test_images/food3.jpg", "food3"),
        ("test_images/food4.jpg", "food4"),
        ("test_images/food5.jpg", "food5")
    ]
    
    results = []
    
    for image_path, image_name in test_images:
        result = test_api_image(image_path, image_name, api_url)
        if result:
            results.append(result)
    
    # 結果サマリー
    print(f"\n📊 Cloud Run APIテスト結果サマリー")
    print("=" * 50)
    for result in results:
        print(f"{result['image_name']}: {result['total_calories']:.1f} kcal ({result['total_dishes']}料理, {result['total_ingredients']}食材)")
    
    # JSON保存
    with open("cloud_food2_5_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 結果保存: cloud_food2_5_results.json")

if __name__ == "__main__":
    main()
