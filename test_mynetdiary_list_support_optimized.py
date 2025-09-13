#!/usr/bin/env python3
"""
MyNetDiary List Support DB Optimized Test Script

search_name_list配列フィールドに最適化された7段階検索戦略のテスト
代替名検索の効果を重点的に検証
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Any

# Elasticsearch直接アクセス用
ELASTICSEARCH_URL = "http://localhost:9200"
INDEX_NAME = "mynetdiary_list_support_db"

def elasticsearch_search_optimized(query: str, size: int = 10) -> Dict[str, Any]:
    """search_name_list配列に最適化された7段階検索戦略"""

    search_body = {
        "query": {
            "bool": {
                "should": [
                    # Tier 1: Exact Match (search_name_list配列要素) - Score: 15+
                    {"match_phrase": {"search_name_list": {"query": query, "boost": 15}}},
                    # Tier 1b: Exact Match (search_name文字列) - Score: 15+ (fallback)
                    {"match_phrase": {"search_name": {"query": query, "boost": 15}}},

                    # Tier 2: Exact Match (description) - Score: 12+
                    {"match_phrase": {"description": {"query": query, "boost": 12}}},

                    # Tier 3: Phrase Match (search_name_list配列要素) - Score: 10+
                    {"match": {"search_name_list": {"query": query, "boost": 10}}},
                    # Tier 3b: Phrase Match (search_name文字列) - Score: 10+ (fallback)
                    {"match": {"search_name": {"query": query, "boost": 10}}},

                    # Tier 4: Phrase Match (description) - Score: 8+
                    {"match": {"description": {"query": query, "boost": 8}}},

                    # Tier 5: Term Match (search_name_list要素の完全一致) - Score: 6+
                    {"term": {"search_name_list.keyword": {"value": query, "boost": 6}}},
                    # Tier 5b: Term Match (search_name文字列の完全一致) - Score: 6+ (fallback)
                    {"term": {"search_name.keyword": {"value": query, "boost": 6}}},

                    # Tier 6: Multi-field match (配列と文字列両対応) - Score: 4+
                    {"multi_match": {
                        "query": query,
                        "fields": ["search_name_list^3", "search_name^3", "description^2", "original_name"],
                        "boost": 4
                    }},

                    # Tier 7: Fuzzy Match (search_name_list配列要素) - Score: 2+
                    {"fuzzy": {"search_name_list": {"value": query, "boost": 2}}},
                    # Tier 7b: Fuzzy Match (search_name文字列) - Score: 2+ (fallback)
                    {"fuzzy": {"search_name": {"value": query, "boost": 2}}}
                ]
            }
        },
        "size": size,
        "_source": ["search_name", "search_name_list", "description", "original_name", "nutrition", "processing_method"]
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

def test_alternative_names_query(query: str, expected_alternatives: List[str]) -> Dict[str, Any]:
    """代替名検索の効果をテスト"""
    print(f"\n{'='*80}")
    print(f"🔍 代替名テスト: '{query}'")
    print(f"📝 期待する代替名: {', '.join(expected_alternatives)}")
    print(f"{'='*80}")

    result = elasticsearch_search_optimized(query, size=15)

    if "error" in result:
        print(f"❌ エラー: {result['error']}")
        return {"query": query, "error": result["error"], "results": []}

    hits = result.get("hits", {}).get("hits", [])
    total_hits = result.get("hits", {}).get("total", {}).get("value", 0)

    print(f"📊 総検索結果数: {total_hits}")
    print(f"📋 表示結果数: {len(hits)}")

    processed_results = []
    alternative_matches = []

    for i, hit in enumerate(hits, 1):
        source = hit["_source"]
        score = hit["_score"]

        search_name = source.get("search_name", "Unknown")
        search_name_list = source.get("search_name_list", [])
        description = source.get("description", "No description")
        original_name = source.get("original_name", "No original name")
        nutrition = source.get("nutrition", {})
        processing_method = source.get("processing_method", "Unknown")

        # 代替名マッチングをチェック
        is_alternative_match = any(alt.lower() in ' '.join(search_name_list).lower() for alt in expected_alternatives)
        if is_alternative_match:
            alternative_matches.append(i)

        print(f"\n🏆 結果 #{i} (スコア: {score:.2f}) {'🎯' if is_alternative_match else ''}")
        print(f"   🔸 検索名: '{search_name}'")
        print(f"   🔸 検索名リスト: {search_name_list}")
        print(f"   🔸 説明: '{description}'")
        print(f"   🔸 元の名前: '{original_name}'")
        print(f"   🔸 栄養情報: {format_nutrition_info(nutrition)}")
        print(f"   🔸 処理方法: {processing_method}")

        processed_results.append({
            "rank": i,
            "score": score,
            "search_name": search_name,
            "search_name_list": search_name_list,
            "description": description,
            "original_name": original_name,
            "nutrition": nutrition,
            "processing_method": processing_method,
            "is_alternative_match": is_alternative_match
        })

    # 代替名マッチング効果の分析
    print(f"\n📈 代替名マッチング分析:")
    print(f"   🎯 代替名マッチした結果: {len(alternative_matches)} / {len(hits)}")
    if alternative_matches:
        print(f"   📍 マッチした順位: {', '.join(f'#{pos}' for pos in alternative_matches)}")
        top_alt_rank = min(alternative_matches)
        print(f"   🥇 最高順位の代替名マッチ: #{top_alt_rank}")

    return {
        "query": query,
        "expected_alternatives": expected_alternatives,
        "total_hits": total_hits,
        "displayed_results": len(hits),
        "alternative_matches_count": len(alternative_matches),
        "alternative_matches_ranks": alternative_matches,
        "results": processed_results
    }

def run_alternative_names_test() -> Dict[str, Any]:
    """代替名に特化したテストを実行"""
    print("🚀 MyNetDiary List Support DB 代替名最適化テスト開始")
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️ 対象インデックス: {INDEX_NAME}")

    # 代替名テストケース（READMEで言及されている代替名）
    alternative_test_cases = [
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

    all_results = []

    for query, expected_alternatives in alternative_test_cases:
        result = test_alternative_names_query(query, expected_alternatives)
        all_results.append(result)

    # 代替名検索効果のサマリー
    print(f"\n{'='*80}")
    print("📊 代替名検索効果サマリー")
    print(f"{'='*80}")

    total_tests = len(all_results)
    successful_alternative_searches = len([r for r in all_results if r.get("alternative_matches_count", 0) > 0])

    print(f"🔢 総テスト数: {total_tests}")
    print(f"✅ 代替名マッチ成功: {successful_alternative_searches}")
    print(f"❌ 代替名マッチ失敗: {total_tests - successful_alternative_searches}")
    print(f"📈 代替名検索成功率: {(successful_alternative_searches/total_tests)*100:.1f}%")

    # 詳細統計
    all_alternative_matches = [r.get("alternative_matches_count", 0) for r in all_results]
    avg_alternative_matches = sum(all_alternative_matches) / len(all_alternative_matches)

    print(f"🎯 平均代替名マッチ数: {avg_alternative_matches:.1f}")

    # トップ順位での代替名マッチ分析
    top_rank_matches = [min(r.get("alternative_matches_ranks", [999])) for r in all_results if r.get("alternative_matches_ranks")]
    if top_rank_matches:
        avg_top_rank = sum(top_rank_matches) / len(top_rank_matches)
        print(f"🥇 代替名マッチ平均最高順位: {avg_top_rank:.1f}")

    # 結果をファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"mynetdiary_list_support_alternative_names_test_{timestamp}.json"

    test_summary = {
        "timestamp": timestamp,
        "index_name": INDEX_NAME,
        "test_type": "alternative_names_optimization",
        "total_tests": total_tests,
        "successful_alternative_searches": successful_alternative_searches,
        "success_rate_percent": (successful_alternative_searches/total_tests)*100,
        "avg_alternative_matches": avg_alternative_matches,
        "avg_top_rank": sum(top_rank_matches) / len(top_rank_matches) if top_rank_matches else None,
        "detailed_results": all_results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_summary, f, ensure_ascii=False, indent=2)

    print(f"\n💾 詳細結果を保存: {output_file}")

    return test_summary

if __name__ == "__main__":
    print("🔍 MyNetDiary List Support DB 代替名最適化テストスイート")
    print("="*80)
    print("🎯 search_name_list配列フィールド活用による代替名検索改善テスト")
    print("📖 READMEの7段階検索戦略 + 配列形式対応")
    print("="*80)

    # 代替名最適化テスト実行
    results = run_alternative_names_test()

    print(f"\n🎉 代替名最適化テスト完了!")
    print(f"📊 成功率: {results['success_rate_percent']:.1f}%")
    if results.get('avg_top_rank'):
        print(f"🥇 平均最高順位: {results['avg_top_rank']:.1f}")