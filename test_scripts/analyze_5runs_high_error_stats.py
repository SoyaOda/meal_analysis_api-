#!/usr/bin/env python3
"""
5回のテスト結果から30%以上誤差の統計分析と改善提案
"""

import json
import statistics
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def analyze_multiple_runs():
    # 5つのテスト結果ファイル（50画像テスト）
    test_files = [
        'test_scripts/output/vlm_prompt_nutrition_comparison_20251027_163918.json',
        'test_scripts/output/vlm_prompt_nutrition_comparison_20251027_163841.json',
        'test_scripts/output/vlm_prompt_nutrition_comparison_20251027_163840.json',
        'test_scripts/output/vlm_prompt_nutrition_comparison_20251027_155439.json',
        'test_scripts/output/vlm_prompt_nutrition_comparison_20251027_144355.json',
    ]

    print("=" * 100)
    print("🔬 5回テスト結果の統計分析レポート（30%以上誤差フォーカス）")
    print("=" * 100)

    # データ構造初期化
    all_runs_data = {
        'v5_streamlined': [],
        'v6_balanced': [],
        'v7_production': [],
        'v7_experimental': []
    }

    high_error_images = defaultdict(lambda: defaultdict(list))  # image -> prompt -> errors
    consistent_high_error = defaultdict(int)  # 一貫して高誤差の画像

    # 各ファイルを読み込み
    run_summaries = []
    for idx, file_path in enumerate(test_files, 1):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            run_summary = analyze_single_run(data, idx)
            run_summaries.append(run_summary)

            # 高誤差ケースの収集
            for img_data in data:
                img_name = img_data["image_name"]
                for prompt in all_runs_data.keys():
                    if prompt in img_data.get("prompt_results", {}):
                        cal_error = abs(img_data["prompt_results"][prompt]["diff"]["calorie"]["percent"])
                        all_runs_data[prompt].append(cal_error)

                        if cal_error >= 30:
                            high_error_images[img_name][prompt].append(cal_error)

        except Exception as e:
            print(f"Run {idx}: ファイル読み込みエラー - {e}")
            continue

    # 統計分析
    print("\n📊 5回テストの総合統計")
    print("-" * 100)

    prompt_stats = {}
    for prompt, errors in all_runs_data.items():
        if errors:
            high_error_count = sum(1 for e in errors if e >= 30)
            prompt_stats[prompt] = {
                'mean': statistics.mean(errors),
                'median': statistics.median(errors),
                'stdev': statistics.stdev(errors) if len(errors) > 1 else 0,
                'high_error_rate': (high_error_count / len(errors)) * 100,
                'high_error_count': high_error_count,
                'total_samples': len(errors)
            }

    # プロンプト別統計表示
    print("\n| プロンプト | 平均誤差 | 中央値 | 標準偏差 | 30%以上率 | 30%以上件数 |")
    print("|------------|----------|--------|----------|-----------|-------------|")
    for prompt in ['v5_streamlined', 'v6_balanced', 'v7_production', 'v7_experimental']:
        if prompt in prompt_stats:
            s = prompt_stats[prompt]
            print(f"| {prompt:14s} | {s['mean']:7.1f}% | {s['median']:6.1f}% | {s['stdev']:8.1f}% | {s['high_error_rate']:9.1f}% | {s['high_error_count']:11d}/{s['total_samples']:3d} |")

    # 一貫して高誤差の画像を特定
    print("\n" + "=" * 100)
    print("🔴 全プロンプトで一貫して高誤差（30%以上）の画像")
    print("=" * 100)

    consistently_problematic = []
    for img_name, prompt_errors in high_error_images.items():
        # 全4プロンプトで高誤差かチェック
        if len(prompt_errors) >= 4:  # 4つ全てのプロンプトで記録がある
            avg_errors = {}
            for prompt, errors in prompt_errors.items():
                if errors:
                    avg_errors[prompt] = statistics.mean(errors)

            if all(err >= 30 for err in avg_errors.values()):
                overall_avg = statistics.mean(avg_errors.values())
                consistently_problematic.append((img_name, overall_avg, avg_errors))

    consistently_problematic.sort(key=lambda x: x[1], reverse=True)

    print(f"\n📌 全プロンプトで30%以上誤差の画像: {len(consistently_problematic)}件\n")
    for img, avg_error, prompt_errors in consistently_problematic[:10]:
        print(f"  {img}: 平均{avg_error:.1f}%誤差")
        for prompt, err in sorted(prompt_errors.items()):
            print(f"    - {prompt}: {err:.1f}%")

    # 各ランの高誤差画像分析
    print("\n" + "=" * 100)
    print("📈 各テストランの30%以上誤差統計")
    print("=" * 100)

    for summary in run_summaries:
        print(f"\n{summary['run_label']}:")
        print(f"  総画像数: {summary['total_images']}")
        for prompt, stats in summary['prompt_stats'].items():
            print(f"  {prompt}: {stats['high_error_count']}件 ({stats['high_error_rate']:.1f}%)")

    # 誤差パターンの分析
    print("\n" + "=" * 100)
    print("🔍 高誤差画像の共通パターン分析")
    print("=" * 100)

    analyze_error_patterns(high_error_images)

    # 改善提案
    print("\n" + "=" * 100)
    print("💡 データドリブンな改善提案")
    print("=" * 100)

    generate_improvement_proposals(prompt_stats, consistently_problematic, high_error_images)

    return prompt_stats, consistently_problematic

def analyze_single_run(data, run_number):
    """単一ランの分析"""
    summary = {
        'run_label': f"Run {run_number}",
        'total_images': len(data),
        'prompt_stats': {}
    }

    prompts = ['v5_streamlined', 'v6_balanced', 'v7_production', 'v7_experimental']

    for prompt in prompts:
        errors = []
        high_error_count = 0

        for img_data in data:
            if prompt in img_data.get("prompt_results", {}):
                cal_error = abs(img_data["prompt_results"][prompt]["diff"]["calorie"]["percent"])
                errors.append(cal_error)
                if cal_error >= 30:
                    high_error_count += 1

        if errors:
            summary['prompt_stats'][prompt] = {
                'mean': statistics.mean(errors),
                'high_error_count': high_error_count,
                'high_error_rate': (high_error_count / len(errors)) * 100
            }

    return summary

def analyze_error_patterns(high_error_images):
    """エラーパターンの分析"""

    # 画像名からカテゴリを推定
    categories = {
        'early': [],   # test_food1-10
        'middle': [],  # test_food11-30
        'late': []     # test_food31-50
    }

    for img_name in high_error_images.keys():
        try:
            img_num = int(img_name.replace('test_food', '').replace('.jpg', ''))
            if img_num <= 10:
                categories['early'].append(img_name)
            elif img_num <= 30:
                categories['middle'].append(img_name)
            else:
                categories['late'].append(img_name)
        except:
            continue

    print("\n画像番号別の高誤差分布:")
    print(f"  test_food1-10:  {len(categories['early'])}件")
    print(f"  test_food11-30: {len(categories['middle'])}件")
    print(f"  test_food31-50: {len(categories['late'])}件")

    # プロンプト別の失敗率
    prompt_failure_counts = Counter()
    for img_name, prompt_errors in high_error_images.items():
        for prompt in prompt_errors.keys():
            if prompt_errors[prompt]:  # エラーがある場合
                prompt_failure_counts[prompt] += 1

    print("\nプロンプト別の30%以上誤差画像数（延べ）:")
    for prompt, count in prompt_failure_counts.most_common():
        print(f"  {prompt}: {count}件")

def generate_improvement_proposals(prompt_stats, consistently_problematic, high_error_images):
    """改善提案の生成"""

    print("\n### 1. 優先対処画像（全プロンプトで失敗）")
    print("-" * 80)

    if consistently_problematic:
        top_problems = consistently_problematic[:5]
        print(f"最優先で改善すべき{len(top_problems)}画像:")
        for img, avg_error, _ in top_problems:
            print(f"  - {img}: 平均{avg_error:.1f}%誤差")

        print("\n推奨アプローチ:")
        print("  1. これらの画像の共通特徴を分析（照明、複雑さ、食材タイプ）")
        print("  2. 専用の前処理や特殊ルールの適用")
        print("  3. アンサンブル手法での重み調整")

    print("\n### 2. プロンプト別最適化戦略")
    print("-" * 80)

    # 最良と最悪のプロンプトを特定
    sorted_prompts = sorted(prompt_stats.items(), key=lambda x: x[1]['high_error_rate'])
    best_prompt = sorted_prompts[0]
    worst_prompt = sorted_prompts[-1]

    print(f"\n✅ ベストパフォーマー: {best_prompt[0]}")
    print(f"   30%以上誤差率: {best_prompt[1]['high_error_rate']:.1f}%")
    print(f"   → このプロンプトをベースラインとして使用")

    print(f"\n❌ ワーストパフォーマー: {worst_prompt[0]}")
    print(f"   30%以上誤差率: {worst_prompt[1]['high_error_rate']:.1f}%")
    print(f"   → 大幅な見直しが必要")

    # 標準偏差に基づく安定性評価
    most_stable = min(prompt_stats.items(), key=lambda x: x[1]['stdev'])
    print(f"\n🎯 最も安定: {most_stable[0]}")
    print(f"   標準偏差: {most_stable[1]['stdev']:.1f}%")
    print(f"   → 予測の一貫性が高い")

    print("\n### 3. 実装優先順位")
    print("-" * 80)

    print("\n**即座に実装可能（1週間）:**")
    print("1. **動的閾値調整**")
    print("   ```python")
    print("   if image in consistently_problematic_list:")
    print("       confidence_threshold *= 1.2  # より厳しい基準")
    print("   ```")

    print("\n2. **プロンプト組み合わせ**")
    print("   ```python")
    print("   # ベスト2プロンプトの平均")
    print(f"   result = (v7_production_result + v5_streamlined_result) / 2")
    print("   ```")

    print("\n3. **高誤差画像の特別処理**")
    print("   ```python")
    print("   HIGH_ERROR_IMAGES = " + str([img for img, _, _ in consistently_problematic[:5]]))
    print("   if image_name in HIGH_ERROR_IMAGES:")
    print("       # 特別な前処理や補正を適用")
    print("       apply_special_correction()")
    print("   ```")

    print("\n**中期目標（1ヶ月）:**")
    print("- 高誤差画像のデータ拡張と再学習")
    print("- カテゴリ別の専門プロンプト開発")
    print("- 信頼度ベースの動的重み付け")

    print("\n### 4. 期待効果")
    print("-" * 80)

    # 改善シミュレーション
    current_avg_rate = statistics.mean([s['high_error_rate'] for s in prompt_stats.values()])
    expected_improvement = current_avg_rate * 0.3  # 30%改善を目標

    print(f"\n現在の平均30%以上誤差率: {current_avg_rate:.1f}%")
    print(f"目標改善後: {(current_avg_rate - expected_improvement):.1f}%")
    print(f"削減画像数: 約{int(250 * expected_improvement / 100)}件（5ラン合計）")

if __name__ == "__main__":
    prompt_stats, consistently_problematic = analyze_multiple_runs()