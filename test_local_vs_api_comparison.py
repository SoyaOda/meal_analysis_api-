#!/usr/bin/env python3
"""
ローカルElasticsearchとCloud Run APIの比較テストスクリプト

test_mynetdiary_list_support_optimized.pyと同じテストケースを使用して、
ローカルの直接Elasticsearch検索結果とCloud Run APIの結果を比較します。
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Any
import time

# ローカルElasticsearch設定
LOCAL_ELASTICSEARCH_URL = "http://35.193.16.212:9200"
LOCAL_INDEX_NAME = "mynetdiary_list_support_db"

# Cloud Run API設定
API_BASE_URL = "https://meal-analysis-api-v2-1077966746907.us-central1.run.app"

def elasticsearch_search_local(query: str, size: int = 10) -> Dict[str, Any]:
    """ローカルElasticsearchへの直接検索（元のロジック）"""

    search_body = {
        "query": {
            "bool": {
                "should": [
                    # Tier 1: Exact Match (search_name配列要素) - Score: 15+
                    {"match_phrase": {"search_name": {"query": query, "boost": 15}}},

                    # Tier 2: Exact Match (description) - Score: 12+
                    {"match_phrase": {"description": {"query": query, "boost": 12}}},

                    # Tier 3: Phrase Match (search_name配列要素) - Score: 10+
                    {"match": {"search_name": {"query": query, "boost": 10}}},

                    # Tier 4: Phrase Match (description) - Score: 8+
                    {"match": {"description": {"query": query, "boost": 8}}},

                    # Tier 5: Term Match (search_name要素の完全一致) - Score: 6+
                    {"term": {"search_name.keyword": {"value": query, "boost": 6}}},

                    # Tier 6: Multi-field match - Score: 4+
                    {"multi_match": {
                        "query": query,
                        "fields": ["search_name^3", "description^2", "original_name"],
                        "boost": 4
                    }},

                    # Tier 7: Fuzzy Match (search_name配列要素) - Score: 2+
                    {"fuzzy": {"search_name": {"value": query, "boost": 2}}}
                ]
            }
        },
        "size": size,
        "_source": ["search_name", "description", "original_name", "nutrition", "processing_method"]
    }

    try:
        start_time = time.time()
        response = requests.post(
            f"{LOCAL_ELASTICSEARCH_URL}/{LOCAL_INDEX_NAME}/_search",
            headers={"Content-Type": "application/json"},
            data=json.dumps(search_body),
            timeout=10
        )
        response_time = int((time.time() - start_time) * 1000)

        if response.status_code == 200:
            result = response.json()
            result['response_time_ms'] = response_time
            return result
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}", "response_time_ms": response_time}
    except Exception as e:
        return {"error": str(e), "response_time_ms": 0}

def api_search(query: str, size: int = 10) -> Dict[str, Any]:
    """Cloud Run APIを通じた検索"""

    try:
        start_time = time.time()
        response = requests.get(
            f"{API_BASE_URL}/api/v1/nutrition/suggest",
            params={
                "q": query,
                "limit": size,
                "debug": "false"
            },
            timeout=10
        )
        response_time = int((time.time() - start_time) * 1000)

        if response.status_code == 200:
            result = response.json()
            result['api_response_time_ms'] = response_time
            return result
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}", "api_response_time_ms": response_time}
    except Exception as e:
        return {"error": str(e), "api_response_time_ms": 0}

def compare_results(query: str, expected_alternatives: List[str], size: int = 10) -> Dict[str, Any]:
    """ローカルとAPIの結果を比較"""

    print(f"\n{'='*80}")
    print(f"🔍 比較テスト: '{query}'")
    print(f"📝 期待する代替名: {', '.join(expected_alternatives)}")
    print(f"{'='*80}")

    # ローカル検索実行
    print("🏠 ローカルElasticsearch検索中...")
    local_result = elasticsearch_search_local(query, size)

    # API検索実行
    print("☁️ Cloud Run API検索中...")
    api_result = api_search(query, size)

    # 結果の比較分析
    comparison = {
        "query": query,
        "expected_alternatives": expected_alternatives,
        "local_result": local_result,
        "api_result": api_result,
        "comparison_analysis": {}
    }

    # ローカル結果の処理
    if "error" not in local_result:
        local_hits = local_result.get("hits", {}).get("hits", [])
        local_total = local_result.get("hits", {}).get("total", {}).get("value", 0)
        local_time = local_result.get("response_time_ms", 0)

        print(f"🏠 ローカル結果: {len(local_hits)}件 (総数: {local_total}) - {local_time}ms")

        for i, hit in enumerate(local_hits[:3], 1):
            source = hit["_source"]
            score = hit["_score"]
            search_name = source.get("search_name", ["Unknown"])
            name = search_name[0] if isinstance(search_name, list) else search_name
            description = source.get("description", "")
            print(f"   {i}. {name} (スコア: {score:.2f}) - {description}")
    else:
        print(f"🏠 ローカルエラー: {local_result['error']}")
        local_hits = []
        local_total = 0
        local_time = local_result.get("response_time_ms", 0)

    # API結果の処理
    if "error" not in api_result:
        api_suggestions = api_result.get("suggestions", [])
        api_metadata = api_result.get("metadata", {})
        api_total = api_metadata.get("total_hits", 0)
        api_time = api_result.get("api_response_time_ms", 0)
        search_time = api_metadata.get("search_time_ms", 0)

        print(f"☁️ API結果: {len(api_suggestions)}件 (総数: {api_total}) - {api_time}ms (検索: {search_time}ms)")

        for i, suggestion in enumerate(api_suggestions[:3], 1):
            name = suggestion.get("suggestion", "Unknown")
            confidence = suggestion.get("confidence_score", 0)
            alt_names = suggestion.get("alternative_names", [])
            alt_text = f" (代替: {alt_names[:2]})" if alt_names else ""
            print(f"   {i}. {name} (信頼度: {confidence}%){alt_text}")
    else:
        print(f"☁️ APIエラー: {api_result['error']}")
        api_suggestions = []
        api_total = 0
        api_time = api_result.get("api_response_time_ms", 0)
        search_time = 0

    # 代替名マッチング分析
    local_alt_matches = 0
    api_alt_matches = 0

    if local_hits:
        for hit in local_hits:
            source = hit["_source"]
            search_name = source.get("search_name", [])
            names_to_check = search_name if isinstance(search_name, list) else [search_name]

            for name in names_to_check:
                if any(alt.lower() in name.lower() for alt in expected_alternatives):
                    local_alt_matches += 1
                    break

    if api_suggestions:
        for suggestion in api_suggestions:
            food_info = suggestion.get("food_info", {})
            search_name_list = food_info.get("search_name_list", [])
            alt_names = suggestion.get("alternative_names", [])

            # 両方がリストであることを保証
            if isinstance(search_name_list, str):
                search_name_list = [search_name_list]
            if isinstance(alt_names, str):
                alt_names = [alt_names]

            all_names = search_name_list + alt_names

            if any(alt.lower() in ' '.join(all_names).lower() for alt in expected_alternatives):
                api_alt_matches += 1

    # 比較分析結果
    comparison["comparison_analysis"] = {
        "local_results_count": len(local_hits),
        "api_results_count": len(api_suggestions),
        "local_total_hits": local_total,
        "api_total_hits": api_total,
        "local_response_time_ms": local_time,
        "api_response_time_ms": api_time,
        "api_search_time_ms": search_time,
        "local_alternative_matches": local_alt_matches,
        "api_alternative_matches": api_alt_matches,
        "results_match": len(local_hits) == len(api_suggestions),
        "alternative_detection_match": local_alt_matches == api_alt_matches
    }

    # 比較サマリー表示
    print(f"\n📊 比較分析:")
    print(f"   📈 結果数: ローカル {len(local_hits)} vs API {len(api_suggestions)}")
    print(f"   ⏱️ 応答時間: ローカル {local_time}ms vs API {api_time}ms")
    print(f"   🎯 代替名マッチ: ローカル {local_alt_matches} vs API {api_alt_matches}")

    if len(local_hits) == len(api_suggestions):
        print(f"   ✅ 結果数一致")
    else:
        print(f"   ⚠️ 結果数不一致")

    if local_alt_matches == api_alt_matches:
        print(f"   ✅ 代替名検出一致")
    else:
        print(f"   ⚠️ 代替名検出不一致")

    return comparison

def run_comparison_test() -> Dict[str, Any]:
    """test_mynetdiary_list_support_optimized.pyと同じテストケースで比較実行"""

    print("🚀 ローカル vs API 比較テスト開始")
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🏠 ローカルElasticsearch: {LOCAL_ELASTICSEARCH_URL}/{LOCAL_INDEX_NAME}")
    print(f"☁️ Cloud Run API: {API_BASE_URL}")

    # test_mynetdiary_list_support_optimized.pyと同じテストケース
    test_cases = [
        # チックピー/ガルバンゾ豆テスト
        ("chickpeas", ["chickpea", "garbanzo", "garbanzo beans"]),
        ("garbanzo beans", ["chickpea", "chickpeas", "garbanzo"]),
        ("garbanzo", ["chickpea", "chickpeas", "garbanzo beans"]),

        # 具体的な食材での精度テスト
        ("tomato", ["tomato", "tomatoes"]),
        ("tomatoes", ["tomato"]),
        ("chicken breast", ["chicken", "breast"]),
        ("brown rice", ["rice", "brown"]),

        # 部分一致テスト
        ("beans", ["black beans", "kidney beans", "fava beans", "garbanzo beans"]),
        ("rice", ["brown rice", "white rice", "rice flour"]),
    ]

    all_comparisons = []

    for query, expected_alternatives in test_cases:
        comparison = compare_results(query, expected_alternatives, size=10)
        all_comparisons.append(comparison)

    # 全体サマリー
    print(f"\n{'='*80}")
    print("📊 全体比較サマリー")
    print(f"{'='*80}")

    total_tests = len(all_comparisons)
    results_match_count = len([c for c in all_comparisons if c["comparison_analysis"]["results_match"]])
    alt_match_count = len([c for c in all_comparisons if c["comparison_analysis"]["alternative_detection_match"]])

    # 平均応答時間
    local_times = [c["comparison_analysis"]["local_response_time_ms"] for c in all_comparisons
                   if "error" not in c["local_result"]]
    api_times = [c["comparison_analysis"]["api_response_time_ms"] for c in all_comparisons
                 if "error" not in c["api_result"]]

    avg_local_time = sum(local_times) / len(local_times) if local_times else 0
    avg_api_time = sum(api_times) / len(api_times) if api_times else 0

    print(f"🔢 総テスト数: {total_tests}")
    print(f"✅ 結果数一致: {results_match_count}/{total_tests} ({(results_match_count/total_tests)*100:.1f}%)")
    print(f"🎯 代替名検出一致: {alt_match_count}/{total_tests} ({(alt_match_count/total_tests)*100:.1f}%)")
    print(f"⏱️ 平均応答時間:")
    print(f"   🏠 ローカル: {avg_local_time:.1f}ms")
    print(f"   ☁️ API: {avg_api_time:.1f}ms")

    if avg_api_time > 0 and avg_local_time > 0:
        speed_ratio = avg_api_time / avg_local_time
        print(f"   📈 API/ローカル比: {speed_ratio:.2f}x")

    # 結果をファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"local_vs_api_comparison_{timestamp}.json"

    summary = {
        "timestamp": timestamp,
        "test_summary": {
            "total_tests": total_tests,
            "results_match_count": results_match_count,
            "alternative_match_count": alt_match_count,
            "results_match_rate": (results_match_count/total_tests)*100,
            "alternative_match_rate": (alt_match_count/total_tests)*100,
            "avg_local_response_time_ms": avg_local_time,
            "avg_api_response_time_ms": avg_api_time,
            "api_speed_ratio": avg_api_time / avg_local_time if avg_local_time > 0 else None
        },
        "local_elasticsearch_url": LOCAL_ELASTICSEARCH_URL,
        "api_base_url": API_BASE_URL,
        "detailed_comparisons": all_comparisons
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n💾 詳細結果を保存: {output_file}")

    return summary

if __name__ == "__main__":
    print("🔍 ローカル vs API 比較テストスイート")
    print("=" * 80)
    print("🎯 test_mynetdiary_list_support_optimized.pyと同じテストケースで比較")
    print("🏠 ローカル直接Elasticsearch vs ☁️ Cloud Run API")
    print("=" * 80)

    # 比較テスト実行
    results = run_comparison_test()

    print(f"\n🎉 比較テスト完了!")
    print(f"📊 結果一致率: {results['test_summary']['results_match_rate']:.1f}%")
    print(f"🎯 代替名検出一致率: {results['test_summary']['alternative_match_rate']:.1f}%")
    if results['test_summary']['api_speed_ratio']:
        print(f"⚡ API速度比: {results['test_summary']['api_speed_ratio']:.2f}x")