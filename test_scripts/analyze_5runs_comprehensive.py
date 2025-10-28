#!/usr/bin/env python3
"""
5回のテスト結果から30%以上誤差の包括的統計分析
"""

import json
import statistics
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def analyze_all_runs():
    # 5つのテスト結果ファイル（50画像テスト）
    test_files = [
        'test_scripts/output/vlm_prompt_nutrition_comparison_20251027_163918.json',
        'test_scripts/output/vlm_prompt_nutrition_comparison_20251027_163841.json',
        'test_scripts/output/vlm_prompt_nutrition_comparison_20251027_163840.json',
        'test_scripts/output/vlm_prompt_nutrition_comparison_20251027_155439.json',
        'test_scripts/output/vlm_prompt_nutrition_comparison_20251027_144355.json',
    ]

    print("=" * 100)
    print("🔬 5回×50画像テストの包括的分析レポート（30%以上誤差フォーカス）")
    print("=" * 100)

    # データ収集
    all_results = defaultdict(lambda: defaultdict(list))  # prompt -> image -> errors
    run_summaries = []
    image_error_counts = defaultdict(lambda: defaultdict(int))  # image -> prompt -> count

    # 各テストファイルを読み込み
    for run_idx, file_path in enumerate(test_files, 1):
        print(f"\n📁 Run {run_idx}: {file_path.split('/')[-1]}")

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            run_stats = {
                'run_num': run_idx,
                'total_images': len(data),
                'prompts_stats': {}
            }

            # 各画像のデータを処理
            for img_data in data:
                img_name = img_data.get("image_name", "unknown")

                # prompt_resultsから各プロンプトの結果を取得
                if "prompt_results" in img_data:
                    for prompt_name, prompt_result in img_data["prompt_results"].items():
                        if "diff" in prompt_result and "calorie" in prompt_result["diff"]:
                            cal_error = abs(prompt_result["diff"]["calorie"]["percent"])
                            all_results[prompt_name][img_name].append(cal_error)

                            if cal_error >= 30:
                                image_error_counts[img_name][prompt_name] += 1

                            # 統計収集
                            if prompt_name not in run_stats['prompts_stats']:
                                run_stats['prompts_stats'][prompt_name] = {
                                    'errors': [],
                                    'high_error_count': 0
                                }

                            run_stats['prompts_stats'][prompt_name]['errors'].append(cal_error)
                            if cal_error >= 30:
                                run_stats['prompts_stats'][prompt_name]['high_error_count'] += 1

            # 各プロンプトの平均を計算
            for prompt, stats in run_stats['prompts_stats'].items():
                if stats['errors']:
                    stats['mean_error'] = statistics.mean(stats['errors'])
                    stats['high_error_rate'] = (stats['high_error_count'] / len(stats['errors'])) * 100
                    print(f"  {prompt}: {stats['high_error_count']}件/{len(stats['errors'])}件 (30%以上: {stats['high_error_rate']:.1f}%)")

            run_summaries.append(run_stats)

        except Exception as e:
            print(f"  ⚠️ エラー: {e}")
            continue

    # 全体統計
    print("\n" + "=" * 100)
    print("📊 5回テスト合計統計（延べ250画像分）")
    print("=" * 100)

    # プロンプト別の統計
    prompt_overall_stats = {}
    for prompt_name in all_results.keys():
        all_errors = []
        high_error_count = 0

        for img_errors in all_results[prompt_name].values():
            all_errors.extend(img_errors)
            high_error_count += sum(1 for e in img_errors if e >= 30)

        if all_errors:
            prompt_overall_stats[prompt_name] = {
                'total_samples': len(all_errors),
                'mean': statistics.mean(all_errors),
                'median': statistics.median(all_errors),
                'stdev': statistics.stdev(all_errors) if len(all_errors) > 1 else 0,
                'high_error_count': high_error_count,
                'high_error_rate': (high_error_count / len(all_errors)) * 100
            }

    # ソート（30%以上誤差率の低い順）
    sorted_prompts = sorted(prompt_overall_stats.items(),
                           key=lambda x: x[1]['high_error_rate'])

    print("\n| プロンプト | テスト数 | 平均誤差 | 中央値 | 標準偏差 | 30%以上件数 | 30%以上率 |")
    print("|------------|----------|----------|--------|----------|-------------|-----------|")
    for prompt, stats in sorted_prompts:
        print(f"| {prompt:18s} | {stats['total_samples']:8d} | {stats['mean']:7.1f}% | {stats['median']:6.1f}% | {stats['stdev']:8.1f}% | {stats['high_error_count']:11d} | {stats['high_error_rate']:9.1f}% |")

    # 一貫して高誤差の画像を特定
    print("\n" + "=" * 100)
    print("🔴 複数回のテストで高誤差（30%以上）を記録した画像")
    print("=" * 100)

    problem_images = []
    for img_name, prompt_errors in image_error_counts.items():
        total_high_error_count = sum(prompt_errors.values())
        if total_high_error_count >= 3:  # 3回以上高誤差
            avg_errors = {}
            for prompt in prompt_errors.keys():
                if prompt in all_results and img_name in all_results[prompt]:
                    avg_errors[prompt] = statistics.mean(all_results[prompt][img_name])

            if avg_errors:
                overall_avg = statistics.mean(avg_errors.values())
                problem_images.append({
                    'image': img_name,
                    'avg_error': overall_avg,
                    'high_error_count': total_high_error_count,
                    'prompt_errors': avg_errors
                })

    problem_images.sort(key=lambda x: x['avg_error'], reverse=True)

    print(f"\n📌 3回以上30%超誤差を記録した画像: {len(problem_images)}件")
    for idx, img_info in enumerate(problem_images[:15], 1):
        print(f"\n{idx}. {img_info['image']}: 平均{img_info['avg_error']:.1f}%誤差 (高誤差{img_info['high_error_count']}回)")
        for prompt, err in sorted(img_info['prompt_errors'].items()):
            print(f"    {prompt}: {err:.1f}%")

    # 改善提案
    print("\n" + "=" * 100)
    print("💡 統計に基づく改善提案")
    print("=" * 100)

    print("\n### 1. プロンプト選択戦略")
    print("-" * 80)

    best = sorted_prompts[0] if sorted_prompts else None
    if best:
        print(f"✅ ベスト: {best[0]}")
        print(f"   30%以上誤差率: {best[1]['high_error_rate']:.1f}%")
        print(f"   平均誤差: {best[1]['mean']:.1f}%")

    if len(sorted_prompts) > 1:
        second = sorted_prompts[1]
        print(f"\n🥈 次点: {second[0]}")
        print(f"   30%以上誤差率: {second[1]['high_error_rate']:.1f}%")
        print(f"   平均誤差: {second[1]['mean']:.1f}%")

    print("\n### 2. 問題画像への対処")
    print("-" * 80)

    if problem_images:
        # カテゴリ分析
        categories = {'1-10': 0, '11-20': 0, '21-30': 0, '31-40': 0, '41-50': 0}
        for img_info in problem_images:
            try:
                num = int(img_info['image'].replace('test_food', '').replace('.jpg', ''))
                if num <= 10: categories['1-10'] += 1
                elif num <= 20: categories['11-20'] += 1
                elif num <= 30: categories['21-30'] += 1
                elif num <= 40: categories['31-40'] += 1
                else: categories['41-50'] += 1
            except:
                pass

        print("\n問題画像の分布:")
        for cat, count in categories.items():
            if count > 0:
                print(f"  test_food{cat}: {count}件")

        print(f"\n最も問題のある画像Top5:")
        for img_info in problem_images[:5]:
            print(f"  - {img_info['image']}: 平均{img_info['avg_error']:.1f}%誤差")

    print("\n### 3. 実装アクションプラン")
    print("-" * 80)

    print("\n**Phase 1: 即座に実装可能（1週間）**")
    print("```python")
    print("# 1. 問題画像の特別処理")
    print(f"PROBLEM_IMAGES = {[img['image'] for img in problem_images[:10]]}")
    print("")
    print("# 2. ベストプロンプトの採用")
    if best:
        print(f"DEFAULT_PROMPT = '{best[0]}'")
    print("")
    print("# 3. 動的補正係数")
    print("CORRECTION_FACTORS = {")
    for img_info in problem_images[:5]:
        factor = 1.0 / (1.0 + img_info['avg_error'] / 100)
        print(f"    '{img_info['image']}': {factor:.2f},")
    print("}")
    print("```")

    print("\n**Phase 2: 短期改善（2週間）**")
    print("- アンサンブル手法の実装（上位2プロンプトの平均）")
    print("- カテゴリ別の専用処理")
    print("- 信頼度スコアによるフィルタリング")

    print("\n**Phase 3: 中期改善（1ヶ月）**")
    print("- 問題画像の詳細分析と再アノテーション")
    print("- プロンプトの根本的な再設計")
    print("- 機械学習による補正モデルの開発")

    # 期待効果
    print("\n### 4. 期待される改善効果")
    print("-" * 80)

    if prompt_overall_stats:
        current_avg = statistics.mean([s['high_error_rate'] for s in prompt_overall_stats.values()])
        print(f"\n現状: 平均{current_avg:.1f}%の画像で30%以上誤差")
        print(f"目標: {(current_avg * 0.5):.1f}%に削減（50%改善）")
        print(f"削減数: 約{int(current_avg * 0.5 * 2.5)}件/250件")

    return prompt_overall_stats, problem_images

if __name__ == "__main__":
    stats, problems = analyze_all_runs()