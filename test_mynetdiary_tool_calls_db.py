#!/usr/bin/env python3
"""
MyNetDiary Tool Calls DB Test Script

mynetdiary_tool_calls_dbインデックスを使用した完全なクエリテスト
全ての検索結果を詳細に出力
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Any

# Elasticsearch直接アクセス用
ELASTICSEARCH_URL = "http://localhost:9200"
INDEX_NAME = "mynetdiary_tool_calls_db"

def elasticsearch_search(query: str, size: int = 10) -> Dict[str, Any]:
    """Elasticsearchに直接クエリを実行"""
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["search_name^3", "description^2", "original_name"]
            }
        },
        "size": size
    }
    
    try:
        response = requests.post(
            f"{ELASTICSEARCH_URL}/{INDEX_NAME}/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(search_body)
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def format_nutrition_info(nutrition: Dict[str, float]) -> str:
    """栄養情報を見やすい形式でフォーマット"""
    return f"🍽 {nutrition.get('calories', 0):.1f}kcal | 🥩 {nutrition.get('protein', 0):.1f}g | 🍞 {nutrition.get('carbs', 0):.1f}g | 🧈 {nutrition.get('fat', 0):.1f}g"

def test_single_query(query: str, expected_description: str = "") -> Dict[str, Any]:
    """単一クエリのテストを実行"""
    print(f"\n{'='*80}")
    print(f"🔍 クエリ: '{query}'")
    if expected_description:
        print(f"📝 期待する結果: {expected_description}")
    print(f"{'='*80}")
    
    # Elasticsearch検索を実行
    result = elasticsearch_search(query, size=15)
    
    if "error" in result:
        print(f"❌ エラー: {result['error']}")
        return {"query": query, "error": result["error"], "results": []}
    
    hits = result.get("hits", {}).get("hits", [])
    total_hits = result.get("hits", {}).get("total", {}).get("value", 0)
    
    print(f"📊 総検索結果数: {total_hits}")
    print(f"📋 表示結果数: {len(hits)}")
    
    processed_results = []
    
    for i, hit in enumerate(hits, 1):
        source = hit["_source"]
        score = hit["_score"]
        
        search_name = source.get("search_name", "Unknown")
        description = source.get("description", "No description")
        original_name = source.get("original_name", "No original name")
        nutrition = source.get("nutrition", {})
        processing_method = source.get("processing_method", "Unknown")
        
        print(f"\n🏆 結果 #{i} (スコア: {score:.2f})")
        print(f"   🔸 検索名: '{search_name}'")
        print(f"   🔸 説明: '{description}'")
        print(f"   🔸 元の名前: '{original_name}'")
        print(f"   🔸 栄養情報: {format_nutrition_info(nutrition)}")
        print(f"   🔸 処理方法: {processing_method}")
        
        processed_results.append({
            "rank": i,
            "score": score,
            "search_name": search_name,
            "description": description,
            "original_name": original_name,
            "nutrition": nutrition,
            "processing_method": processing_method
        })
    
    return {
        "query": query,
        "total_hits": total_hits,
        "displayed_results": len(hits),
        "results": processed_results
    }

def run_comprehensive_test() -> Dict[str, Any]:
    """包括的なテストを実行"""
    print("🚀 MyNetDiary Tool Calls DB 完全クエリテスト開始")
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️ 対象インデックス: {INDEX_NAME}")
    
    # テストクエリのリスト
    test_queries = [
        # 基本的な食材
        ("beans", "シンプルなbeans検索"),
        ("chicken", "チキン関連の検索"),
        ("tomato", "トマト関連の検索"),
        ("rice", "米関連の検索"),
        
        # 複合語
        ("chicken breast", "チキンブレストの検索"),
        ("brown rice", "玄米の検索"),
        ("black beans", "黒豆の検索"),
        
        # 調理方法込み
        ("fried chicken", "フライドチキンの検索"),
        ("baked potato", "ベイクドポテトの検索"),
        ("steamed broccoli", "蒸しブロッコリーの検索"),
        
        # 大文字小文字テスト
        ("BEANS", "大文字でのbeans検索"),
        ("Chicken", "タイトルケースでのchicken検索"),
        
        # 部分一致テスト
        ("bean", "beanの部分一致検索"),
        ("chick", "chickの部分一致検索"),
        
        # 具体的な料理名
        ("soup", "スープ関連の検索"),
        ("salad", "サラダ関連の検索"),
        ("pasta", "パスタ関連の検索")
    ]
    
    all_results = []
    
    for query, description in test_queries:
        result = test_single_query(query, description)
        all_results.append(result)
    
    # サマリー統計
    print(f"\n{'='*80}")
    print("📊 テスト結果サマリー")
    print(f"{'='*80}")
    
    total_queries = len(all_results)
    queries_with_results = len([r for r in all_results if r.get("total_hits", 0) > 0])
    avg_results_per_query = sum(r.get("total_hits", 0) for r in all_results) / total_queries
    
    print(f"🔢 総クエリ数: {total_queries}")
    print(f"✅ 結果ありクエリ数: {queries_with_results}")
    print(f"❌ 結果なしクエリ数: {total_queries - queries_with_results}")
    print(f"📈 クエリあたり平均結果数: {avg_results_per_query:.1f}")
    
    # 結果をファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"mynetdiary_tool_calls_db_test_results_{timestamp}.json"
    
    test_summary = {
        "timestamp": timestamp,
        "index_name": INDEX_NAME,
        "total_queries": total_queries,
        "queries_with_results": queries_with_results,
        "avg_results_per_query": avg_results_per_query,
        "detailed_results": all_results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 詳細結果を保存: {output_file}")
    
    return test_summary

def check_index_stats():
    """インデックスの統計情報を確認"""
    print(f"\n🗄️ {INDEX_NAME} インデックス統計情報")
    print("="*60)
    
    try:
        # インデックス統計
        stats_response = requests.get(f"{ELASTICSEARCH_URL}/{INDEX_NAME}/_stats")
        stats = stats_response.json()
        
        doc_count = stats.get("_all", {}).get("total", {}).get("docs", {}).get("count", 0)
        index_size = stats.get("_all", {}).get("total", {}).get("store", {}).get("size_in_bytes", 0)
        
        print(f"📄 総ドキュメント数: {doc_count:,}")
        print(f"💽 インデックスサイズ: {index_size / (1024*1024):.2f} MB")
        
        # サンプルデータ
        sample_response = requests.get(f"{ELASTICSEARCH_URL}/{INDEX_NAME}/_search?size=3")
        sample_data = sample_response.json()
        
        print(f"\n📋 サンプルデータ:")
        for i, hit in enumerate(sample_data.get("hits", {}).get("hits", []), 1):
            source = hit["_source"]
            print(f"  {i}. '{source.get('search_name', 'Unknown')}' - {source.get('description', 'No description')}")
            
    except Exception as e:
        print(f"❌ 統計情報取得エラー: {e}")

if __name__ == "__main__":
    print("🔍 MyNetDiary Tool Calls DB テストスイート")
    print("="*80)
    
    # インデックス統計情報
    check_index_stats()
    
    # 包括的テスト実行
    results = run_comprehensive_test()
    
    print(f"\n🎉 テスト完了!")
    print(f"📊 {results['queries_with_results']}/{results['total_queries']} クエリで結果が見つかりました")