#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
v5_qwen3の実際の重量を正しく取得して分析
JSON構造の違いを考慮した公平な比較
"""

import json
from pathlib import Path
from typing import Dict, Any


def calculate_v5_qwen3_weight(data: Dict[str, Any]) -> int:
    """v5_qwen3特有のJSON構造から重量を正しく取得"""
    total = 0

    # quality_metricsから直接取得（最も正確）
    if "quality_metrics" in data and "total_weight_g" in data["quality_metrics"]:
        return data["quality_metrics"]["total_weight_g"]

    # dishesから計算
    for dish in data.get("dishes", []):
        if dish.get("main_food"):
            main_food = dish["main_food"]
            # weight_derivationから取得
            if "weight_derivation" in main_food:
                total += main_food["weight_derivation"].get("weight_g", 0)
            # 直接weight_gがある場合（フォールバック）
            elif "weight_g" in main_food:
                total += main_food["weight_g"]

        for extra in dish.get("extras", []):
            # extrasは通常のweight_g
            total += extra.get("weight_g", 0)

    return total


def calculate_standard_weight(data: Dict[str, Any]) -> int:
    """標準的なJSON構造から重量を取得"""
    total = 0
    for dish in data.get("dishes", []):
        if dish.get("main_food"):
            total += dish["main_food"].get("weight_g", 0)
        for extra in dish.get("extras", []):
            total += extra.get("weight_g", 0)
    return total


def analyze_all_results():
    """全てのテスト結果を再分析"""

    # 最新の比較結果ファイルを読み込み
    result_file = "test_scripts/output/vlm_problem_images_comparison_20251027_121128.json"

    with open(result_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    print("=" * 80)
    print("📊 v5_qwen3の実際の重量分析（公平な比較）")
    print("=" * 80)
    print()

    # 各画像の結果を分析
    all_weights = {
        "v3_current": [],
        "v4_light": [],
        "v5_qwen3": [],
        "v5_streamlined": []
    }

    label_weights = []

    for image_name, image_data in results.items():
        label_weight = image_data["image_info"]["label_weight"]
        label_weights.append(label_weight)

        print(f"📷 {image_name} (Label: {label_weight}g)")
        print("-" * 40)

        for version in ["v3_current", "v4_light", "v5_qwen3", "v5_streamlined"]:
            if version not in image_data["results"]:
                continue

            result = image_data["results"][version]
            if "error" in result:
                print(f"  {version:15s}: ERROR")
                continue

            # 重量を正しく取得
            if version == "v5_qwen3":
                actual_weight = calculate_v5_qwen3_weight(result["data"])
            elif version == "v5_streamlined" and "total_weight_g" in result["data"]:
                actual_weight = result["data"]["total_weight_g"]
            else:
                actual_weight = calculate_standard_weight(result["data"])

            # テストスクリプトが計算した重量（誤っている可能性）
            reported_weight = result.get("total_weight", 0)

            # 差分を計算
            diff = actual_weight - label_weight
            diff_pct = (diff / label_weight * 100) if label_weight > 0 else 0

            # 記録
            if version in all_weights:
                all_weights[version].append(actual_weight)

            # 表示
            if actual_weight != reported_weight:
                print(f"  {version:15s}: {actual_weight:4d}g (報告値: {reported_weight:4d}g) "
                      f"差: {diff:+4d}g ({diff_pct:+6.1f}%) ⚠️ 修正値")
            else:
                print(f"  {version:15s}: {actual_weight:4d}g "
                      f"差: {diff:+4d}g ({diff_pct:+6.1f}%)")

        print()

    # 統計サマリー
    print("=" * 80)
    print("📈 統計サマリー（修正後）")
    print("=" * 80)
    print()

    print(f"{'Version':<15} | {'平均重量':<8} | {'平均誤差(%)':<12} | {'最小/最大誤差':<20}")
    print("-" * 70)

    for version, weights in all_weights.items():
        if not weights:
            continue

        avg_weight = sum(weights) / len(weights)

        # 誤差を計算
        errors = []
        for i, w in enumerate(weights):
            if i < len(label_weights):
                error = abs(w - label_weights[i]) / label_weights[i] * 100
                errors.append(error)

        if errors:
            avg_error = sum(errors) / len(errors)
            min_error = min(errors)
            max_error = max(errors)

            print(f"{version:<15} | {avg_weight:>8.1f} | {avg_error:>12.1f} | "
                  f"{min_error:>6.1f} / {max_error:>6.1f}")

    print()

    # v5_qwen3の詳細分析
    print("=" * 80)
    print("🔍 v5_qwen3の詳細分析")
    print("=" * 80)
    print()

    for image_name, image_data in results.items():
        if "v5_qwen3" not in image_data["results"]:
            continue

        result = image_data["results"]["v5_qwen3"]
        if "error" in result:
            continue

        data = result["data"]

        print(f"📷 {image_name}")

        # quality_metricsの内容
        if "quality_metrics" in data:
            qm = data["quality_metrics"]
            print(f"  quality_metrics.total_weight_g: {qm.get('total_weight_g', 'N/A')}")

        # 各dishの重量
        for i, dish in enumerate(data.get("dishes", []), 1):
            if dish.get("main_food"):
                mf = dish["main_food"]
                if "weight_derivation" in mf:
                    wd = mf["weight_derivation"]
                    print(f"  Dish {i} main_food:")
                    print(f"    - volume: {wd.get('estimated_volume_cm3', 'N/A')} cm³")
                    print(f"    - density: {wd.get('density_g_cm3', 'N/A')} g/cm³")
                    print(f"    - weight: {wd.get('weight_g', 'N/A')} g")

            for j, extra in enumerate(dish.get("extras", []), 1):
                print(f"  Dish {i} extra {j}: {extra.get('weight_g', 'N/A')} g")

        print()


if __name__ == "__main__":
    analyze_all_results()