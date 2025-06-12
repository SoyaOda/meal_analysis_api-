#!/usr/bin/env python3
"""
見出し語化機能を活用した検索精度向上のテストスクリプト

目的：
- 「tomato」vs「tomatoes」問題の解決検証
- 見出し語化対応検索の効果測定
- スコアリング調整の確認
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
import requests

from app_v2.components.elasticsearch_nutrition_search_component import ElasticsearchNutritionSearchComponent
from app_v2.models.nutrition_search_models import NutritionQueryInput
from app_v2.utils.lemmatization import lemmatize_term, test_lemmatization

# テストケース：問題のあるクエリと期待される改善
TEST_CASES = [
    {
        "query": "tomato",
        "description": "単数形クエリで複数形項目(tomatoes)が上位に来るべき",
        "expected_improvements": ["tomatoes", "tomato"],
        "problematic_results": ["tomato soup", "tomato sauce", "tomato juice"]
    },
    {
        "query": "tomatoes", 
        "description": "複数形クエリはそのまま正常動作するはず",
        "expected_improvements": ["tomatoes"],
        "problematic_results": []
    },
    {
        "query": "potato",
        "description": "単数形クエリで複数形項目(potatoes)が上位に来るべき",
        "expected_improvements": ["potatoes", "potato"],
        "problematic_results": ["potato salad", "potato soup"]
    },
    {
        "query": "apples",
        "description": "複数形クエリで単数形項目(apple)も評価されるべき",
        "expected_improvements": ["apples", "apple"],
        "problematic_results": ["apple juice", "apple pie"]
    },
    {
        "query": "onion",
        "description": "単数形クエリで複数形項目(onions)が上位に来るべき",
        "expected_improvements": ["onions", "onion"],
        "problematic_results": ["onion soup", "onion rings"]
    }
]

async def test_direct_elasticsearch_queries():
    """直接Elasticsearchクエリで現状確認"""
    print("=== 直接Elasticsearch検索での現状確認 ===")
    
    base_url = "http://localhost:9200/nutrition_db/_search"
    
    for test_case in TEST_CASES:
        query = test_case["query"]
        print(f"\n🔍 検索クエリ: '{query}'")
        print(f"📋 説明: {test_case['description']}")
        
        # 標準的な検索クエリ
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["name", "search_name", "description"]
                }
            },
            "size": 10
        }
        
        try:
            response = requests.post(
                base_url,
                headers={"Content-Type": "application/json"},
                json=search_body
            )
            
            if response.status_code == 200:
                result = response.json()
                hits = result.get("hits", {}).get("hits", [])
                
                print(f"📊 検索結果数: {len(hits)}")
                print("🏆 上位5件:")
                
                for i, hit in enumerate(hits[:5]):
                    source = hit["_source"]
                    score = hit["_score"]
                    name = source.get("search_name", "N/A")
                    data_type = source.get("data_type", "N/A")
                    print(f"  {i+1}. {name} (スコア: {score:.2f}, タイプ: {data_type})")
                
            else:
                print(f"❌ 検索エラー: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 検索失敗: {e}")

async def test_lemmatized_component_search():
    """見出し語化コンポーネントでの検索テスト"""
    print("\n\n=== 見出し語化対応コンポーネント検索テスト ===")
    
    # ElasticsearchNutritionSearchComponentを見出し語化対応で初期化
    es_component = ElasticsearchNutritionSearchComponent(
        multi_db_search_mode=False,  # 見出し語化機能を優先
        enable_advanced_features=False,  # 構造化検索は無効
        results_per_db=5
    )
    
    # 見出し語化機能が有効かを確認
    print(f"🔧 見出し語化機能: {'有効' if es_component.enable_lemmatization else '無効'}")
    print(f"🎯 見出し語化完全一致ブースト: {es_component.lemmatized_exact_match_boost}")
    print(f"⚠️ 複合語ペナルティ: {es_component.compound_word_penalty}")
    
    results_comparison = []
    
    for test_case in TEST_CASES:
        query = test_case["query"]
        print(f"\n🔍 見出し語化検索テスト: '{query}'")
        
        # 見出し語化クエリ入力を作成
        query_input = NutritionQueryInput(
            ingredient_names=[query],
            dish_names=[],
            preferred_source="elasticsearch"
        )
        
        try:
            # 見出し語化対応検索を実行
            search_result = await es_component.process(query_input)
            
            matches = search_result.matches.get(query, [])
            search_summary = search_result.search_summary
            
            print(f"📊 検索結果: {len(matches)}件")
            print(f"🎯 検索方法: {search_summary.get('search_method', 'N/A')}")
            print(f"⏱️ 検索時間: {search_summary.get('search_time_ms', 0)}ms")
            
            if matches:
                print("🏆 見出し語化対応上位5件:")
                for i, match in enumerate(matches[:5]):
                    score = match.score
                    name = match.search_name
                    data_type = match.data_type
                    
                    # メタデータの確認
                    metadata = getattr(match, 'search_metadata', {})
                    lemmatized_query = metadata.get('lemmatized_query', 'N/A')
                    lemmatized_db_name = metadata.get('lemmatized_db_name', 'N/A')
                    score_adjustment = metadata.get('score_adjustment_factor', 1.0)
                    
                    print(f"  {i+1}. {name}")
                    print(f"     スコア: {score:.3f} (調整係数: {score_adjustment:.2f})")
                    print(f"     タイプ: {data_type}")
                    print(f"     見出し語化: '{lemmatized_query}' -> '{lemmatized_db_name}'")
                
                # 期待される改善の確認
                top_names = [match.search_name.lower() for match in matches[:3]]
                expected = [exp.lower() for exp in test_case["expected_improvements"]]
                improvements_found = [exp for exp in expected if any(exp in name for name in top_names)]
                
                print(f"✅ 期待された改善: {improvements_found}")
                
                # 結果を保存
                results_comparison.append({
                    "query": query,
                    "description": test_case["description"],
                    "top_results": [(match.search_name, match.score) for match in matches[:5]],
                    "improvements_found": improvements_found,
                    "search_time_ms": search_summary.get('search_time_ms', 0)
                })
            else:
                print("❌ 検索結果なし")
                
        except Exception as e:
            print(f"❌ 見出し語化検索エラー: {e}")
    
    return results_comparison

async def compare_search_methods():
    """検索方法の比較テスト"""
    print("\n\n=== 検索方法比較テスト ===")
    
    # 1. 従来の戦略的検索
    strategic_component = ElasticsearchNutritionSearchComponent(
        multi_db_search_mode=True,
        enable_advanced_features=False,
        results_per_db=5
    )
    strategic_component.enable_lemmatization = False  # 見出し語化を無効
    
    # 2. 見出し語化対応検索
    lemmatized_component = ElasticsearchNutritionSearchComponent(
        multi_db_search_mode=False,
        enable_advanced_features=False,
        results_per_db=5
    )
    
    # 比較対象クエリ
    test_query = "tomato"
    
    print(f"🔍 比較クエリ: '{test_query}'")
    
    query_input = NutritionQueryInput(
        ingredient_names=[test_query],
        dish_names=[],
        preferred_source="elasticsearch"
    )
    
    # 従来検索
    print("\n📊 従来の戦略的検索:")
    try:
        strategic_result = await strategic_component.process(query_input)
        strategic_matches = strategic_result.matches.get(test_query, [])
        print(f"  結果数: {len(strategic_matches)}")
        for i, match in enumerate(strategic_matches[:3]):
            print(f"  {i+1}. {match.search_name} (スコア: {match.score:.3f})")
    except Exception as e:
        print(f"  ❌ エラー: {e}")
    
    # 見出し語化検索
    print("\n📊 見出し語化対応検索:")
    try:
        lemmatized_result = await lemmatized_component.process(query_input)
        lemmatized_matches = lemmatized_result.matches.get(test_query, [])
        print(f"  結果数: {len(lemmatized_matches)}")
        for i, match in enumerate(lemmatized_matches[:3]):
            metadata = getattr(match, 'search_metadata', {})
            adjustment = metadata.get('score_adjustment_factor', 1.0)
            print(f"  {i+1}. {match.search_name} (スコア: {match.score:.3f}, 調整: {adjustment:.2f})")
    except Exception as e:
        print(f"  ❌ エラー: {e}")

def save_test_results(results: List[Dict], filename: str = None):
    """テスト結果を保存"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lemmatization_test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "test_timestamp": datetime.now().isoformat(),
            "test_description": "見出し語化機能を活用した検索精度向上テスト",
            "test_cases": TEST_CASES,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 テスト結果を保存しました: {filename}")

async def main():
    """メインテスト実行"""
    print("🚀 見出し語化機能テスト開始")
    print("=" * 60)
    
    # 1. 見出し語化ライブラリのテスト
    print("📚 見出し語化ライブラリテスト:")
    test_lemmatization()
    
    # 2. 直接Elasticsearch検索での現状確認
    await test_direct_elasticsearch_queries()
    
    # 3. 見出し語化コンポーネント検索テスト
    results = await test_lemmatized_component_search()
    
    # 4. 検索方法の比較
    await compare_search_methods()
    
    # 5. 結果保存
    save_test_results(results)
    
    print("\n✅ 見出し語化機能テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 