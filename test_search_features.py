#!/usr/bin/env python3
"""
検索機能詳細テスト
現在の検索システムがどの要素を考慮しているかを確認
"""

import asyncio
from app_v2.elasticsearch.search_service import food_search_service, SearchQuery, NutritionTarget
from app_v2.elasticsearch.client import es_client

async def test_search_features():
    """検索機能の詳細をテスト"""
    
    print("=== 🔍 検索機能詳細テスト ===\n")
    
    # 1. 基本検索（人気度ブースティングのみ）
    print("1. 基本検索テスト (人気度ブースティング)")
    query = SearchQuery(elasticsearch_query_terms='chicken')
    results = await food_search_service.search_foods(query, size=5)
    
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r.food_name[:50]}")
        print(f"     スコア: {r.score:.4f} | 人気度: {r.num_favorites} | タイプ: {r.data_type}")
        print(f"     カロリー: {r.nutrition.get('calories', 0):.1f}kcal/100g")
    
    print()
    
    # 2. 栄養プロファイル類似性を含む検索
    print("2. 栄養プロファイル類似性テスト")
    nutrition_target = NutritionTarget(
        calories=200.0,
        protein_g=25.0,
        fat_total_g=8.0,
        carbohydrate_by_difference_g=0.5
    )
    
    query_with_nutrition = SearchQuery(
        elasticsearch_query_terms='chicken',
        target_nutrition_vector=nutrition_target
    )
    
    results_with_nutrition = await food_search_service.search_foods(
        query_with_nutrition, 
        size=5,
        enable_nutritional_similarity=True
    )
    
    for i, r in enumerate(results_with_nutrition, 1):
        print(f"  {i}. {r.food_name[:50]}")
        print(f"     スコア: {r.score:.4f} | 人気度: {r.num_favorites}")
        print(f"     栄養: {r.nutrition.get('calories', 0):.1f}kcal, "
              f"{r.nutrition.get('protein_g', 0):.1f}g protein, "
              f"{r.nutrition.get('fat_total_g', 0):.1f}g fat")
        
        # 目標栄養プロファイルとの差を計算
        cal_diff = abs(r.nutrition.get('calories', 0) - 200.0)
        pro_diff = abs(r.nutrition.get('protein_g', 0) - 25.0)
        print(f"     目標との差: カロリー{cal_diff:.1f}, タンパク質{pro_diff:.1f}g")
    
    print()
    
    # 3. タイプフィルタリングテスト
    print("3. タイプフィルタリングテスト (食材のみ)")
    results_ingredient_only = await food_search_service.search_foods(
        query, 
        size=5,
        data_type_filter=["ingredient", "branded"]
    )
    
    for i, r in enumerate(results_ingredient_only, 1):
        print(f"  {i}. {r.food_name[:50]}")
        print(f"     タイプ: {r.data_type} | スコア: {r.score:.4f} | 人気度: {r.num_favorites}")
    
    print()
    
    # 4. 検索システムの構成要素まとめ
    print("=== 🎯 検索システム構成要素まとめ ===")
    print("✅ 考慮される要素:")
    print("  1. BM25F語彙的マッチング (基本スコア)")
    print("  2. 人気度ブースティング (num_favorites)")
    print("     - 1000+お気に入り: 1.2倍ブースト")
    print("     - 100+お気に入り: 1.1倍ブースト") 
    print("     - 10+お気に入り: 1.05倍ブースト")
    print("  3. 栄養プロファイル類似性 (オプション)")
    print("     - カロリー、タンパク質、脂質、炭水化物の類似度")
    print("     - 正規化・重み付けによる距離計算")
    print("  4. タイプベースフィルタリング")
    print("     - ingredient/dish/branded による絞り込み")
    print("  5. カスタムアナライザー")
    print("     - ステミング、同義語展開、ファジー検索")
    print("     - 音声類似検索 (低ブースト)")
    
    print("\n❌ 現在無効化されている要素:")
    print("  - function_score (デバッグのため一時的に無効)")
    print("  - セマンティック埋め込みベクトル類似性")

if __name__ == "__main__":
    asyncio.run(test_search_features()) 