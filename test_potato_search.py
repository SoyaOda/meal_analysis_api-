#!/usr/bin/env python3
"""
Potato検索問題分析スクリプト

eatthismuchの期待結果と現在の結果を比較して問題点を特定
"""

import asyncio
from app_v2.elasticsearch.search_service import food_search_service, SearchQuery, NutritionTarget

async def analyze_potato_search_problem():
    """potato検索の問題を分析"""
    
    print("🥔 Potato検索問題分析")
    print("="*70)
    
    # 1. 現在の検索結果
    print("1. 現在の検索結果 (純粋語彙的検索):")
    print("-"*50)
    
    query = SearchQuery(elasticsearch_query_terms='potato')
    results = await food_search_service.search_foods(query, size=10)
    
    for i, r in enumerate(results, 1):
        print(f"{i:2}. {r.food_name[:45]:45} | Score: {r.score:.3f}")
        print(f"    {r.nutrition.get('calories', 0):3.0f}kcal, {r.nutrition.get('carbohydrate_by_difference_g', 0):2.0f}g carbs, {r.nutrition.get('fat_total_g', 0):3.1f}g fat, {r.nutrition.get('protein_g', 0):2.0f}g protein")
        print(f"    Type: {r.data_type}, Favorites: {r.num_favorites}")
        if r.description:
            print(f"    Desc: {r.description[:60]}")
        print()
    
    # 2. eatthismuchの期待結果との比較
    print("\n2. eatthismuch期待結果との比較:")
    print("-"*50)
    
    expected_results = [
        {"name": "Potato - Flesh and skin, raw", "calories": 284, "carbs": 64, "fat": 0.3, "protein": 7},
        {"name": "Red potatoes - Flesh and skin, raw", "calories": 119, "carbs": 27, "fat": 0.2, "protein": 3},
        {"name": "Russet potatoes - Flesh and skin, raw", "calories": 292, "carbs": 67, "fat": 0.3, "protein": 8},
        {"name": "White potatoes - Flesh and skin, raw", "calories": 255, "carbs": 58, "fat": 0.4, "protein": 6},
        {"name": "Baked potato - Flesh and skin, without salt", "calories": 161, "carbs": 37, "fat": 0.2, "protein": 4}
    ]
    
    print("期待される上位結果:")
    for i, expected in enumerate(expected_results, 1):
        print(f"{i}. {expected['name']}")
        print(f"   {expected['calories']}kcal, {expected['carbs']}g carbs, {expected['fat']}g fat, {expected['protein']}g protein")
    
    # 3. 問題点分析
    print("\n3. 問題点分析:")
    print("-"*50)
    
    # 生ポテトの検索結果を確認
    raw_potato_found = False
    processed_potato_count = 0
    
    for r in results[:5]:  # 上位5件をチェック
        food_name_lower = r.food_name.lower()
        
        if "raw" in food_name_lower or ("flesh" in food_name_lower and "skin" in food_name_lower):
            raw_potato_found = True
            print(f"✅ 生ポテト発見: {r.food_name}")
        
        if any(processed in food_name_lower for processed in ["fried", "mashed", "baked", "boiled", "hash"]):
            processed_potato_count += 1
            print(f"⚠️ 加工ポテト上位: {r.food_name}")
    
    print(f"\n📊 分析結果:")
    print(f"- 上位5件中の生ポテト: {'あり' if raw_potato_found else 'なし'}")
    print(f"- 上位5件中の加工ポテト: {processed_potato_count}件")
    
    # 4. データタイプ別検索テスト
    print("\n4. データタイプ別検索テスト:")
    print("-"*50)
    
    # ingredient のみで検索
    print("Ingredient のみで検索:")
    ingredient_results = await food_search_service.search_foods(
        query, size=5, data_type_filter=["ingredient"]
    )
    
    for i, r in enumerate(ingredient_results, 1):
        print(f"{i}. {r.food_name[:40]:40} | {r.nutrition.get('calories', 0):3.0f}kcal")
    
    print("\nDish のみで検索:")
    dish_results = await food_search_service.search_foods(
        query, size=5, data_type_filter=["dish"]
    )
    
    for i, r in enumerate(dish_results, 1):
        print(f"{i}. {r.food_name[:40]:40} | {r.nutrition.get('calories', 0):3.0f}kcal")
    
    # 5. 栄養プロファイル類似性テスト
    print("\n5. 栄養プロファイル類似性テスト:")
    print("-"*50)
    
    # 生ポテトの典型的な栄養プロファイル
    raw_potato_nutrition = NutritionTarget(
        calories=280.0,  # eatthismuchの生ポテト平均
        protein_g=7.0,
        fat_total_g=0.3,
        carbohydrate_by_difference_g=64.0
    )
    
    query_with_nutrition = SearchQuery(
        elasticsearch_query_terms='potato',
        target_nutrition_vector=raw_potato_nutrition
    )
    
    nutrition_results = await food_search_service.search_foods(
        query_with_nutrition, 
        size=5,
        enable_nutritional_similarity=True
    )
    
    print("栄養プロファイル類似性を考慮した結果:")
    for i, r in enumerate(nutrition_results, 1):
        cal_diff = abs(r.nutrition.get('calories', 0) - 280.0)
        fat_diff = abs(r.nutrition.get('fat_total_g', 0) - 0.3)
        print(f"{i}. {r.food_name[:40]:40} | Score: {r.score:.3f}")
        print(f"   {r.nutrition.get('calories', 0):3.0f}kcal (diff: {cal_diff:3.0f}), {r.nutrition.get('fat_total_g', 0):3.1f}g fat (diff: {fat_diff:3.1f})")
    
    # 6. 推奨改善策
    print("\n6. 推奨改善策:")
    print("-"*50)
    print("現在の問題:")
    print("- Function Scoreが無効化されているため、栄養プロファイル類似性が働いていない")
    print("- 純粋なBM25F語彙的マッチングでは、生vs加工の区別ができない")
    print("- 人気度ブースティングも無効化されている")
    
    print("\n改善案:")
    print("1. Function Scoreを再有効化して栄養プロファイル類似性を活用")
    print("2. 'raw', 'fresh', 'flesh and skin'などのキーワードにブーストを追加")
    print("3. 'fried', 'mashed', 'processed'などの加工キーワードにペナルティ")
    print("4. データタイプ 'ingredient' に軽いブーストを追加")

if __name__ == "__main__":
    asyncio.run(analyze_potato_search_problem()) 