#!/usr/bin/env python3
"""
Word Query System vs Direct Elasticsearch Comparison Test

test_mynetdiary_tool_calls_db.pyで使用したクエリを
Word Query Systemでテストして結果を比較
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Any

# API URLs
WORD_QUERY_API = "http://localhost:5001/api/search"
ELASTICSEARCH_URL = "http://localhost:9200"
TOOL_CALLS_INDEX = "mynetdiary_tool_calls_db"

def test_word_query_system(query: str) -> Dict[str, Any]:
    """Word Query System API経由でテスト"""
    try:
        response = requests.post(
            WORD_QUERY_API,
            headers={"Content-Type": "application/json"},
            json={"query": query, "max_results": 10},
            timeout=10
        )
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_direct_elasticsearch(query: str) -> Dict[str, Any]:
    """直接Elasticsearch経由でテスト（tool_calls_db使用）"""
    search_body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["search_name^3", "description^2", "original_name"]
            }
        },
        "size": 10
    }
    
    try:
        response = requests.post(
            f"{ELASTICSEARCH_URL}/{TOOL_CALLS_INDEX}/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(search_body),
            timeout=10
        )
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def format_nutrition_simple(nutrition: Dict[str, float]) -> str:
    """簡潔な栄養情報フォーマット"""
    cal = nutrition.get('calories', 0)
    protein = nutrition.get('protein', 0)
    carbs = nutrition.get('carbs', nutrition.get('carbohydrates', 0))
    fat = nutrition.get('fat', 0)
    return f"{cal:.1f}kcal|P{protein:.1f}g|C{carbs:.1f}g|F{fat:.1f}g"

def compare_single_query(query: str) -> Dict[str, Any]:
    """単一クエリで両システムを比較"""
    print(f"\n{'='*80}")
    print(f"🔍 Query: '{query}'")
    print(f"{'='*80}")
    
    # Word Query System
    print(f"\n🌟 Word Query System (mynetdiary_list_support_db):")
    word_result = test_word_query_system(query)
    
    if not word_result["success"]:
        print(f"❌ Error: {word_result['error']}")
        word_results = []
        word_total = 0
    else:
        word_data = word_result["data"]
        word_results = word_data.get("results", [])
        word_total = word_data.get("total_found", 0)
        print(f"📊 Found: {word_total} results, showing: {len(word_results)}")
        
        for i, result in enumerate(word_results[:5], 1):
            nutrition = result.get("nutrition", {})
            match_type = result.get("match_type", "unknown")
            score = result.get("score", 0)
            name = result.get("name", "Unknown")
            desc = result.get("description", "")
            print(f"  {i}. [{match_type}] {name} ({score:.2f}) - {format_nutrition_simple(nutrition)}")
            if desc:
                print(f"      Description: {desc}")
    
    # Direct Elasticsearch
    print(f"\n🗄️ Direct Elasticsearch (mynetdiary_tool_calls_db):")
    es_result = test_direct_elasticsearch(query)
    
    if not es_result["success"]:
        print(f"❌ Error: {es_result['error']}")
        es_results = []
        es_total = 0
    else:
        es_data = es_result["data"]
        hits = es_data.get("hits", {}).get("hits", [])
        es_total = es_data.get("hits", {}).get("total", {}).get("value", 0)
        print(f"📊 Found: {es_total} results, showing: {len(hits)}")
        
        es_results = []
        for i, hit in enumerate(hits[:5], 1):
            source = hit["_source"]
            score = hit["_score"]
            search_name = source.get("search_name", "Unknown")
            description = source.get("description", "")
            nutrition = source.get("nutrition", {})
            print(f"  {i}. [direct] {search_name} ({score:.2f}) - {format_nutrition_simple(nutrition)}")
            if description:
                print(f"      Description: {description}")
            es_results.append(source)
    
    return {
        "query": query,
        "word_query": {
            "success": word_result["success"],
            "total": word_total,
            "results": word_results[:5]
        },
        "elasticsearch": {
            "success": es_result["success"], 
            "total": es_total,
            "results": es_results[:5]
        }
    }

def run_comparison_test():
    """包括的比較テスト実行"""
    print("🚀 Word Query System vs Direct Elasticsearch Comparison")
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌟 Word Query System: {WORD_QUERY_API}")
    print(f"🗄️ Direct Elasticsearch: {ELASTICSEARCH_URL}/{TOOL_CALLS_INDEX}")
    
    # test_mynetdiary_tool_calls_db.pyと同じクエリを使用
    test_queries = [
        "beans",
        "chicken", 
        "tomato",
        "rice",
        "chicken breast",
        "brown rice",
        "black beans",
        "fried chicken",
        "baked potato",
        "steamed broccoli",
        "BEANS",
        "Chicken",
        "bean",
        "chick",
        "soup",
        "salad",
        "pasta"
    ]
    
    all_comparisons = []
    
    for query in test_queries:
        comparison = compare_single_query(query)
        all_comparisons.append(comparison)
    
    # サマリー統計
    print(f"\n{'='*80}")
    print("📊 Comparison Summary")
    print(f"{'='*80}")
    
    total_queries = len(all_comparisons)
    word_success = len([c for c in all_comparisons if c["word_query"]["success"] and c["word_query"]["total"] > 0])
    es_success = len([c for c in all_comparisons if c["elasticsearch"]["success"] and c["elasticsearch"]["total"] > 0])
    
    word_avg = sum(c["word_query"]["total"] for c in all_comparisons if c["word_query"]["success"]) / total_queries
    es_avg = sum(c["elasticsearch"]["total"] for c in all_comparisons if c["elasticsearch"]["success"]) / total_queries
    
    print(f"🔢 Total Queries: {total_queries}")
    print(f"🌟 Word Query Success: {word_success}/{total_queries} ({word_success/total_queries*100:.1f}%)")
    print(f"🗄️ Elasticsearch Success: {es_success}/{total_queries} ({es_success/total_queries*100:.1f}%)")
    print(f"📈 Word Query Avg Results: {word_avg:.1f}")
    print(f"📈 Elasticsearch Avg Results: {es_avg:.1f}")
    
    # 詳細な違いの分析
    print(f"\n🔍 Key Differences Analysis:")
    different_results = 0
    for comp in all_comparisons:
        if (comp["word_query"]["success"] and comp["elasticsearch"]["success"] and
            comp["word_query"]["total"] != comp["elasticsearch"]["total"]):
            different_results += 1
    
    print(f"📊 Queries with different result counts: {different_results}/{total_queries}")
    
    # 結果をファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"word_query_vs_elasticsearch_comparison_{timestamp}.json"
    
    comparison_summary = {
        "timestamp": timestamp,
        "total_queries": total_queries,
        "word_query_success_rate": word_success/total_queries,
        "elasticsearch_success_rate": es_success/total_queries,
        "word_query_avg_results": word_avg,
        "elasticsearch_avg_results": es_avg,
        "detailed_comparisons": all_comparisons
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 詳細結果を保存: {output_file}")
    
    return comparison_summary

if __name__ == "__main__":
    print("🔍 Word Query System Comparison Test")
    print("="*80)
    
    # システム接続チェック
    print("🔧 Connection Check:")
    try:
        word_check = requests.get("http://localhost:5001/health", timeout=5)
        print(f"✅ Word Query System: {word_check.status_code}")
    except:
        print("❌ Word Query System: Not accessible")
    
    try:
        es_check = requests.get(f"{ELASTICSEARCH_URL}/_cluster/health", timeout=5)
        print(f"✅ Elasticsearch: {es_check.status_code}")
    except:
        print("❌ Elasticsearch: Not accessible")
    
    # 比較テスト実行
    results = run_comparison_test()
    
    print(f"\n🎉 Comparison Test Complete!")
    print(f"📊 Word Query: {results['word_query_success_rate']*100:.1f}% success")
    print(f"📊 Elasticsearch: {results['elasticsearch_success_rate']*100:.1f}% success")