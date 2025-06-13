#!/usr/bin/env python3
"""
Final Exact Match Integration Test

完全一致判定機能が正しく統合され、JSONアウトプットに含まれることを確認するテスト
"""

import json
import asyncio
from app_v2.components.elasticsearch_nutrition_search_component import ElasticsearchNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput

async def test_exact_match_integration():
    """完全一致判定機能の統合テスト"""
    print("🔍 完全一致判定機能の統合テストを開始...")
    
    # Elasticsearchコンポーネントを初期化
    es_component = ElasticsearchNutritionSearchComponent(
        elasticsearch_url="http://localhost:9200",
        enable_advanced_features=True
    )
    
    # テスト用の検索クエリ
    test_queries = [
        "chicken",         # 完全一致する可能性が高い
        "tomato",          # 単複形の違いがある可能性
        "PARMESAN CHEESE", # 大文字小文字の違い
    ]
    
    for query in test_queries:
        print(f"\n📝 テスト中: '{query}'")
        
        # 検索入力を作成
        search_input = NutritionQueryInput(
            ingredient_names=[query],
            search_strategy="basic"
        )
        
        # 検索を実行
        result = await es_component.process(search_input)
        
        # 結果を確認
        if query in result.matches:
            matches = result.matches[query]
            if isinstance(matches, list) and matches:
                first_match = matches[0]
                print(f"   ✅ 検索成功: {len(matches)} 件の結果")
                print(f"   🔎 1番目の結果: {first_match.search_name}")
                print(f"   📊 完全一致: {first_match.is_exact_match}")
                print(f"   📋 マッチング詳細: {json.dumps(first_match.match_details, indent=2, ensure_ascii=False)}")
                
                # JSONシリアライゼーションのテスト
                match_json = first_match.model_dump()
                print(f"   🔧 JSONに含まれる is_exact_match: {'is_exact_match' in match_json}")
                print(f"   🔧 JSONに含まれる match_details: {'match_details' in match_json}")
                
                if 'is_exact_match' in match_json and 'match_details' in match_json:
                    print(f"   ✅ JSONシリアライゼーション正常")
                else:
                    print(f"   ❌ JSONシリアライゼーション不正常")
            else:
                print(f"   ❌ 検索結果なし")
        else:
            print(f"   ❌ 検索失敗")
    
    print("\n🎯 完全一致判定機能の統合テスト完了!")

if __name__ == "__main__":
    asyncio.run(test_exact_match_integration()) 