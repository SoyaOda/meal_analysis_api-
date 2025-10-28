#!/usr/bin/env python3
"""Analyze v7_experimental test results"""

import json

# Load JSON data
with open('test_scripts/output/vlm_prompt_nutrition_comparison_20251027_153511.json', 'r') as f:
    data = json.load(f)

print("=" * 80)
print("📊 v6_balanced vs v7_experimental 比較結果 (3画像)")
print("=" * 80)

# 各プロンプトの誤差を集計
results = {"v6_balanced": [], "v7_experimental": []}

for img in data:
    img_name = img["image_name"]
    for prompt in ["v6_balanced", "v7_experimental"]:
        if prompt in img["prompt_results"]:
            diff = img["prompt_results"][prompt]["diff"]
            cal_err = abs(diff["calorie"]["percent"])
            results[prompt].append({
                "image": img_name,
                "cal_error": cal_err,
                "protein_error": abs(diff["protein_g"]["percent"]),
                "fat_error": abs(diff["fat_g"]["percent"]),
                "carbs_error": abs(diff["carbs_g"]["percent"])
            })

# 平均誤差を計算
for prompt in ["v6_balanced", "v7_experimental"]:
    errors = results[prompt]
    avg_cal = sum(e["cal_error"] for e in errors) / len(errors)
    avg_prot = sum(e["protein_error"] for e in errors) / len(errors)
    avg_fat = sum(e["fat_error"] for e in errors) / len(errors)
    avg_carbs = sum(e["carbs_error"] for e in errors) / len(errors)
    high_error = sum(1 for e in errors if e["cal_error"] >= 30)

    print(f"\n{prompt}:")
    print(f"  平均カロリー誤差: {avg_cal:.1f}%")
    print(f"  平均タンパク質誤差: {avg_prot:.1f}%")
    print(f"  平均脂質誤差: {avg_fat:.1f}%")
    print(f"  平均炭水化物誤差: {avg_carbs:.1f}%")
    print(f"  30%以上誤差件数: {high_error}件")

# 各画像の詳細比較
print("\n" + "=" * 80)
print("画像別詳細比較:")
print("=" * 80)

for img in data:
    img_name = img["image_name"]
    print(f"\n📷 {img_name}")

    label = img["label_nutrition"]
    print(f"  ラベル: Cal={label['total_calorie']:.0f}, P={label['total_protein_g']:.1f}g, F={label['total_fat_g']:.1f}g, C={label['total_carbs_g']:.1f}g")

    for prompt in ["v6_balanced", "v7_experimental"]:
        if prompt in img["prompt_results"]:
            diff = img["prompt_results"][prompt]["diff"]
            total = img["prompt_results"][prompt]["total_nutrition"]

            cal_err = diff["calorie"]["percent"]
            prot_err = diff["protein_g"]["percent"]
            fat_err = diff["fat_g"]["percent"]
            carbs_err = diff["carbs_g"]["percent"]

            print(f"  {prompt}:")
            print(f"    予測: Cal={total['calories']:.0f} ({cal_err:+.1f}%), P={total['protein_g']:.1f}g ({prot_err:+.1f}%), F={total['fat_g']:.1f}g ({fat_err:+.1f}%), C={total['carbs_g']:.1f}g ({carbs_err:+.1f}%)")

print("\n" + "=" * 80)
print("🎯 結論:")
print("=" * 80)

v6_avg = sum(e["cal_error"] for e in results["v6_balanced"]) / len(results["v6_balanced"])
v7_avg = sum(e["cal_error"] for e in results["v7_experimental"]) / len(results["v7_experimental"])

if v7_avg < v6_avg:
    improvement = v6_avg - v7_avg
    print(f"✅ v7_experimental が v6_balanced より {improvement:.1f}% 改善")
else:
    degradation = v7_avg - v6_avg
    print(f"⚠️  v7_experimental が v6_balanced より {degradation:.1f}% 悪化")
    print(f"   → Component-based計算が期待通りに機能していない可能性")

print("=" * 80)
