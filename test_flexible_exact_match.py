#!/usr/bin/env python3
"""
Flexible Exact Match Test Script

柔軟な完全一致判定機能をテストするスクリプト
以下の差異を許容する一致判定をテスト：
- 大文字小文字
- ing, edのあるなし (語形変化)
- 単数形、複数形
- "'s"や","のあるなし (所有格、句読点)
- wordの順序の違い
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any

# テキストマッチング機能をインポート
try:
    from app_v2.utils.text_matching import (
        is_flexible_exact_match, 
        analyze_text_matching,
        get_text_matcher
    )
    TEXT_MATCHING_AVAILABLE = True
    print("✅ テキストマッチング機能が利用可能です")
except ImportError as e:
    print(f"❌ テキストマッチング機能をインポートできません: {e}")
    TEXT_MATCHING_AVAILABLE = False


def create_test_cases() -> List[Dict[str, Any]]:
    """テストケースを作成"""
    test_cases = [
        # 大文字小文字のテスト
        {
            "category": "大文字小文字",
            "query": "chicken breast",
            "targets": [
                "Chicken Breast",
                "CHICKEN BREAST", 
                "chicken breast",
                "Chicken breast",
                "CHICKEN breast"
            ],
            "expected_matches": 5
        },
        
        # 語形変化のテスト (ing, ed)
        {
            "category": "語形変化 (ing, ed)",
            "query": "fried chicken",
            "targets": [
                "Fried Chicken",
                "Frying Chicken",
                "Fry Chicken",
                "Fried Chickens"
            ],
            "expected_matches": 4
        },
        
        # 単数形・複数形のテスト
        {
            "category": "単数形・複数形",
            "query": "apple",
            "targets": [
                "Apple",
                "Apples",
                "apple",
                "apples",
                "Green Apple",
                "Green Apples"
            ],
            "expected_matches": 4  # Green Apple/Applesは部分一致
        },
        
        # 所有格・句読点のテスト
        {
            "category": "所有格・句読点",
            "query": "mcdonald's burger",
            "targets": [
                "McDonald's Burger",
                "McDonalds Burger",
                "McDonald Burger",
                "McDonald's, Burger",
                "McDonald burger"
            ],
            "expected_matches": 5
        },
        
        # 語順の違いのテスト
        {
            "category": "語順の違い",
            "query": "tomato soup",
            "targets": [
                "Tomato Soup",
                "Soup Tomato",
                "Soup, Tomato",
                "Fresh Tomato Soup",
                "Tomato & Basil Soup"
            ],
            "expected_matches": 3  # Fresh/Basilが含まれるものは部分一致
        },
        
        # 複合テスト
        {
            "category": "複合テスト",
            "query": "grilled chicken's breast",
            "targets": [
                "Grilled Chicken Breast",
                "Grilled Chickens Breast",
                "Chicken Breast, Grilled",
                "Breast of Grilled Chicken",
                "GRILLED CHICKEN'S BREAST"
            ],
            "expected_matches": 5
        },
        
        # 食品固有のテスト
        {
            "category": "食品固有",
            "query": "french fries",
            "targets": [
                "French Fries",
                "French fries",
                "Fries, French",
                "Fried French Potatoes",
                "Potato Fries"
            ],
            "expected_matches": 3  # Potato系は別物として扱う
        }
    ]
    
    return test_cases


def run_single_test_case(test_case: Dict[str, Any]) -> Dict[str, Any]:
    """単一のテストケースを実行"""
    if not TEXT_MATCHING_AVAILABLE:
        return {
            "error": "テキストマッチング機能が利用できません",
            "category": test_case["category"]
        }
    
    query = test_case["query"]
    targets = test_case["targets"]
    expected_matches = test_case["expected_matches"]
    
    print(f"\n🧪 テストカテゴリ: {test_case['category']}")
    print(f"   クエリ: '{query}'")
    
    # バッチ分析を実行
    analysis_result = analyze_text_matching(query, targets)
    
    exact_matches = analysis_result["exact_matches"]
    partial_matches = analysis_result["partial_matches"]
    exact_match_count = len(exact_matches)
    
    print(f"   期待された完全一致数: {expected_matches}")
    print(f"   実際の完全一致数: {exact_match_count}")
    
    # 個別結果の表示
    for i, target in enumerate(targets, 1):
        matcher = get_text_matcher()
        is_match, details = matcher.is_flexible_exact_match(query, target)
        
        status = "✅ 完全一致" if is_match else "❌ 一致なし"
        match_type = details.get("match_type", "unknown")
        similarity_score = details.get("similarity_score", 0.0)
        
        print(f"   {i}. '{target}' -> {status} ({match_type}, score: {similarity_score:.2f})")
    
    # 結果の評価
    success = exact_match_count >= (expected_matches * 0.8)  # 80%以上の正解率
    result_status = "✅ 成功" if success else "❌ 失敗"
    
    print(f"   結果: {result_status}")
    
    return {
        "category": test_case["category"],
        "query": query,
        "targets": targets,
        "expected_matches": expected_matches,
        "actual_matches": exact_match_count,
        "exact_matches": exact_matches,
        "partial_matches": partial_matches,
        "success": success,
        "match_rate": exact_match_count / len(targets) if targets else 0.0
    }


def run_all_tests() -> Dict[str, Any]:
    """全テストを実行"""
    print("🚀 柔軟な完全一致判定テストを開始")
    print("=" * 60)
    
    if not TEXT_MATCHING_AVAILABLE:
        print("❌ テキストマッチング機能が利用できません")
        return {"error": "TEXT_MATCHING_NOT_AVAILABLE"}
    
    test_cases = create_test_cases()
    results = []
    
    total_tests = len(test_cases)
    successful_tests = 0
    
    for test_case in test_cases:
        result = run_single_test_case(test_case)
        results.append(result)
        
        if result.get("success", False):
            successful_tests += 1
    
    # 全体結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    print(f"総テスト数: {total_tests}")
    print(f"成功テスト数: {successful_tests}")
    print(f"成功率: {successful_tests/total_tests*100:.1f}%")
    
    # カテゴリ別結果
    print(f"\n📋 カテゴリ別結果:")
    for result in results:
        if "error" not in result:
            status = "✅" if result["success"] else "❌"
            match_rate = result["match_rate"] * 100
            print(f"   {status} {result['category']}: {result['actual_matches']}/{len(result['targets'])} ({match_rate:.1f}%)")
    
    # 完全なテスト結果をファイルに保存
    test_results = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "summary": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "text_matching_available": TEXT_MATCHING_AVAILABLE
        },
        "detailed_results": results
    }
    
    output_file = f"flexible_exact_match_test_results_{test_results['timestamp']}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 詳細結果を保存: {output_file}")
    
    return test_results


def demo_advanced_matching():
    """高度なマッチング機能のデモ"""
    if not TEXT_MATCHING_AVAILABLE:
        print("❌ テキストマッチング機能が利用できません")
        return
    
    print("\n🎯 高度なマッチング機能デモ")
    print("=" * 40)
    
    demo_cases = [
        ("chicken", "grilled chicken breast"),
        ("apple pie", "homemade apple pies"),
        ("beef steak", "steak of beef"),
        ("potato", "mashed potatoes"),
        ("fish", "fried fish fillet")
    ]
    
    matcher = get_text_matcher()
    
    for query, target in demo_cases:
        is_match, details = matcher.is_flexible_exact_match(
            query, target, similarity_threshold=0.7
        )
        
        print(f"\nクエリ: '{query}' vs '{target}'")
        print(f"結果: {'✅ 一致' if is_match else '❌ 不一致'}")
        print(f"タイプ: {details.get('match_type', 'unknown')}")
        print(f"スコア: {details.get('similarity_score', 0.0):.3f}")
        
        if 'query_tokens' in details:
            print(f"クエリトークン: {details['query_tokens']}")
            print(f"ターゲットトークン: {details['target_tokens']}")


def main():
    """メイン関数"""
    print("🔍 柔軟な完全一致判定テストスイート")
    print("大文字小文字、語形変化、単複、所有格、語順の違いを許容する一致判定をテスト")
    
    # 基本テスト実行
    test_results = run_all_tests()
    
    # 高度なマッチング機能のデモ
    demo_advanced_matching()
    
    print("\n🎉 テスト完了!")
    return test_results


if __name__ == "__main__":
    main() 