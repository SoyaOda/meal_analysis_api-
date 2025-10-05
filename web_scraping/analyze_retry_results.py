#!/usr/bin/env python3
"""
リトライ完了後の失敗食材データ状態調査スクリプト
"""

import json
import sys
import os
from datetime import datetime

def analyze_retry_results():
    """リトライ結果の分析"""
    print("🔍 リトライ結果分析開始")
    print("=" * 60)

    # 元の失敗分析結果を読み込み
    print("📄 元の失敗分析結果を読み込み中...")

    # 失敗分析ファイルを探す
    failure_files = [f for f in os.listdir('processed_data') if f.startswith('failure_analysis_')]
    if not failure_files:
        print("❌ 失敗分析ファイルが見つかりません")
        return False

    latest_failure_file = sorted(failure_files)[-1]
    failure_path = f"processed_data/{latest_failure_file}"

    print(f"📂 失敗分析ファイル: {latest_failure_file}")

    with open(failure_path, 'r', encoding='utf-8') as f:
        failure_data = json.load(f)

    # 失敗した48食材のリスト
    failed_foods = failure_data["failure_reasons"]["insufficient_serving"]
    print(f"🎯 調査対象: {len(failed_foods)}個の失敗食材")

    # 新しい収集結果を読み込み
    print("\n📄 新しい収集結果を読み込み中...")
    new_result_file = "data/comprehensive_food_collection_all_20251001_124446.json"

    if not os.path.exists(new_result_file):
        print(f"❌ 新しい結果ファイルが見つかりません: {new_result_file}")
        return False

    with open(new_result_file, 'r', encoding='utf-8') as f:
        new_data = json.load(f)

    collection_results = new_data.get("collection_results", [])
    print(f"📊 新しい収集結果: {len(collection_results)}個の食材")

    # 失敗食材の状態を調査
    print("\n🔍 失敗食材の状態調査:")
    print("-" * 60)

    recovery_stats = {
        "total_failed_foods": len(failed_foods),
        "found_in_new_data": 0,
        "successful_recovery": 0,
        "still_failed": 0,
        "not_found": 0,
        "detailed_results": []
    }

    # 食材名をキーとした辞書を作成（高速検索用）
    new_data_dict = {}
    for result in collection_results:
        food_name = result.get("food_name", "").replace('\n', ' ').strip()
        new_data_dict[food_name] = result

    for i, failed_food in enumerate(failed_foods, 1):
        print(f"\n[{i:2d}/{len(failed_foods)}] {failed_food}")

        # 新しいデータで検索
        if failed_food in new_data_dict:
            recovery_stats["found_in_new_data"] += 1
            result = new_data_dict[failed_food]

            # 成功状態をチェック
            data_success = result.get("data_collection_success", False)
            nav_success = result.get("navigation_success", False)
            overall_success = result.get("overall_success", False)

            if overall_success and data_success:
                recovery_stats["successful_recovery"] += 1
                serving_count = result.get("serving_options_count", 0)
                nutrition_count = result.get("nutrition_data_count", 0)

                print(f"  ✅ 回復成功")
                print(f"     📊 Serving: {serving_count}個")
                print(f"     🥗 栄養素: {nutrition_count}個")
                print(f"     🎯 Navigation: {nav_success}")
                print(f"     📡 Data Collection: {data_success}")

                # 詳細データ確認
                comprehensive_data = result.get("comprehensive_data", {})
                if comprehensive_data:
                    serving_data = comprehensive_data.get("serving_options", {}).get("raw_serving_data", [])
                    nutrition_data = comprehensive_data.get("nutrition_data", {}).get("detailed_nutrients", {}).get("raw_nutrition_data", [])

                    print(f"     🔍 Raw Serving: {len(serving_data)}個")
                    print(f"     🔍 Raw Nutrition: {len(nutrition_data)}個")

                recovery_stats["detailed_results"].append({
                    "food_name": failed_food,
                    "status": "recovered",
                    "serving_count": serving_count,
                    "nutrition_count": nutrition_count,
                    "raw_serving_count": len(serving_data) if comprehensive_data else 0,
                    "raw_nutrition_count": len(nutrition_data) if comprehensive_data else 0
                })

            else:
                recovery_stats["still_failed"] += 1
                print(f"  ❌ まだ失敗")
                print(f"     🎯 Navigation: {nav_success}")
                print(f"     📡 Data Collection: {data_success}")
                print(f"     🏆 Overall: {overall_success}")

                if result.get("error"):
                    print(f"     ⚠️ エラー: {result['error']}")

                recovery_stats["detailed_results"].append({
                    "food_name": failed_food,
                    "status": "still_failed",
                    "navigation_success": nav_success,
                    "data_collection_success": data_success,
                    "error": result.get("error", "")
                })
        else:
            recovery_stats["not_found"] += 1
            print(f"  ❓ 新しいデータに見つかりません")

            recovery_stats["detailed_results"].append({
                "food_name": failed_food,
                "status": "not_found"
            })

    # 統計サマリー
    print("\n" + "=" * 60)
    print("📊 回復統計サマリー")
    print("=" * 60)

    total = recovery_stats["total_failed_foods"]
    found = recovery_stats["found_in_new_data"]
    recovered = recovery_stats["successful_recovery"]
    still_failed = recovery_stats["still_failed"]
    not_found = recovery_stats["not_found"]

    print(f"🎯 調査対象食材: {total}個")
    print(f"📂 新データで発見: {found}個 ({found/total*100:.1f}%)")
    print(f"✅ 回復成功: {recovered}個 ({recovered/total*100:.1f}%)")
    print(f"❌ まだ失敗: {still_failed}個 ({still_failed/total*100:.1f}%)")
    print(f"❓ 見つからず: {not_found}個 ({not_found/total*100:.1f}%)")

    # 回復率計算
    if found > 0:
        recovery_rate = recovered / found * 100
        print(f"🏆 回復率: {recovery_rate:.1f}% ({recovered}/{found})")

    # 詳細結果を保存
    output_file = f"retry_recovery_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recovery_stats, f, ensure_ascii=False, indent=2)

    print(f"\n📄 詳細結果保存: {output_file}")

    # 成功判定
    if recovered >= total * 0.8:  # 80%以上回復で成功
        print("\n🎉 回復成功！大部分の食材が正常にデータ取得されました")
        return True
    else:
        print(f"\n⚠️ 回復不完全：まだ{total - recovered}個の食材に問題があります")
        return False

if __name__ == "__main__":
    success = analyze_retry_results()
    sys.exit(0 if success else 1)