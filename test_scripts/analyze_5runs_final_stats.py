#!/usr/bin/env python3
"""
5回テスト結果の最終統計分析
"""

import json
import statistics
from pathlib import Path
from collections import defaultdict
import argparse
import sys

def analyze_final_results(log_dir):
    """指定ディレクトリから5ランの結果を分析"""

    print("=" * 100)
    print("📊 6プロンプト × 50画像 × 5ラン 最終統計分析")
    print("=" * 100)

    # 結果ファイルを収集
    json_files = list(Path(log_dir).glob("run_*_results.json"))

    if not json_files:
        print(f"❌ エラー: {log_dir} に結果ファイルが見つかりません")
        return

    print(f"\n📁 分析対象: {len(json_files)}ファイル")

    # データ収集
    prompt_all_errors = defaultdict(list)  # prompt -> all errors
    prompt_high_errors = defaultdict(int)  # prompt -> count of 30%+ errors
    image_errors = defaultdict(lambda: defaultdict(list))  # image -> prompt -> errors

    total_tests = 0

    # 各ファイルを処理
    for file_idx, json_file in enumerate(sorted(json_files), 1):
        print(f"\nRun {file_idx}: {json_file.name}")

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            for img_data in data:
                img_name = img_data.get("image_name")

                for prompt_name, result in img_data.get("prompt_results", {}).items():
                    if "diff" in result and "calorie" in result["diff"]:
                        cal_error = abs(result["diff"]["calorie"]["percent"])
                        prompt_all_errors[prompt_name].append(cal_error)
                        image_errors[img_name][prompt_name].append(cal_error)
                        total_tests += 1

                        if cal_error >= 30:
                            prompt_high_errors[prompt_name] += 1

        except Exception as e:
            print(f"  ⚠️ エラー: {e}")
            continue

    print(f"\n総テスト数: {total_tests}")

    # プロンプト別統計
    print("\n" + "=" * 100)
    print("📈 プロンプト別パフォーマンス（5ラン合計）")
    print("=" * 100)

    prompt_stats = []
    for prompt_name in ['v6_corrected', 'v6_balanced', 'v7_experimental',
                       'v5_streamlined', 'v7_production', 'v6_enhanced']:
        if prompt_name in prompt_all_errors:
            errors = prompt_all_errors[prompt_name]
            if errors:
                high_count = prompt_high_errors[prompt_name]
                stats = {
                    'prompt': prompt_name,
                    'mean': statistics.mean(errors),
                    'median': statistics.median(errors),
                    'stdev': statistics.stdev(errors) if len(errors) > 1 else 0,
                    'min': min(errors),
                    'max': max(errors),
                    'high_count': high_count,
                    'high_rate': (high_count / len(errors)) * 100,
                    'total': len(errors)
                }
                prompt_stats.append(stats)

    # 30%以上誤差率でソート
    prompt_stats.sort(key=lambda x: x['high_rate'])

    print("\n| プロンプト | サンプル数 | 平均誤差 | 中央値 | 標準偏差 | 最小/最大 | 30%以上誤差 | 30%以上率 |")
    print("|------------|-----------|----------|--------|----------|-----------|------------|-----------|")

    for stats in prompt_stats:
        print(f"| {stats['prompt']:18s} | {stats['total']:9d} | {stats['mean']:7.1f}% | {stats['median']:6.1f}% | "
              f"{stats['stdev']:8.1f}% | {stats['min']:.0f}/{stats['max']:.0f}% | {stats['high_count']:10d} | {stats['high_rate']:9.1f}% |")

    # 最良プロンプトと最悪プロンプト
    if prompt_stats:
        best = prompt_stats[0]
        worst = prompt_stats[-1]

        print("\n" + "=" * 100)
        print("🏆 パフォーマンスサマリー")
        print("=" * 100)

        print(f"\n✅ ベストプロンプト: {best['prompt']}")
        print(f"   - 30%以上誤差率: {best['high_rate']:.1f}%")
        print(f"   - 平均誤差: {best['mean']:.1f}%")
        print(f"   - 中央値: {best['median']:.1f}%")

        print(f"\n❌ ワーストプロンプト: {worst['prompt']}")
        print(f"   - 30%以上誤差率: {worst['high_rate']:.1f}%")
        print(f"   - 平均誤差: {worst['mean']:.1f}%")
        print(f"   - 中央値: {worst['median']:.1f}%")

    # 問題画像の特定
    print("\n" + "=" * 100)
    print("🔴 一貫して高誤差の画像")
    print("=" * 100)

    problem_images = []
    for img_name, prompt_errors in image_errors.items():
        # 各プロンプトでの平均誤差を計算
        avg_by_prompt = {}
        for prompt, errors in prompt_errors.items():
            if errors:
                avg_by_prompt[prompt] = statistics.mean(errors)

        # 3つ以上のプロンプトで30%以上
        high_error_prompts = sum(1 for err in avg_by_prompt.values() if err >= 30)
        if high_error_prompts >= 3:
            overall_avg = statistics.mean(avg_by_prompt.values())
            problem_images.append({
                'image': img_name,
                'avg_error': overall_avg,
                'high_error_prompts': high_error_prompts,
                'details': avg_by_prompt
            })

    problem_images.sort(key=lambda x: x['avg_error'], reverse=True)

    print(f"\n3つ以上のプロンプトで30%超誤差: {len(problem_images)}件")

    for idx, img in enumerate(problem_images[:10], 1):
        print(f"\n{idx}. {img['image']}: 平均{img['avg_error']:.1f}%誤差 ({img['high_error_prompts']}プロンプトで30%超)")
        for prompt, err in sorted(img['details'].items(), key=lambda x: x[1], reverse=True):
            print(f"    {prompt}: {err:.1f}%")

    # 改善推奨
    print("\n" + "=" * 100)
    print("💡 最終推奨事項")
    print("=" * 100)

    if prompt_stats:
        print(f"\n1. **プロンプト選択**: {prompt_stats[0]['prompt']}を採用（30%以上誤差率{prompt_stats[0]['high_rate']:.1f}%）")

        if len(prompt_stats) > 1:
            print(f"2. **アンサンブル候補**: {prompt_stats[0]['prompt']} + {prompt_stats[1]['prompt']}")

        print(f"3. **要改善画像数**: {len(problem_images)}件を特別処理")

        # 改善効果の推定
        current_rate = statistics.mean([s['high_rate'] for s in prompt_stats])
        print(f"\n現在の平均30%以上誤差率: {current_rate:.1f}%")
        print(f"ベストプロンプト採用で: {prompt_stats[0]['high_rate']:.1f}%に改善")
        print(f"削減率: {(current_rate - prompt_stats[0]['high_rate']):.1f}%ポイント")

    return prompt_stats, problem_images

def main():
    parser = argparse.ArgumentParser(description='5ラン結果の統計分析')
    parser.add_argument('--log_dir', required=True, help='ログディレクトリのパス')
    args = parser.parse_args()

    if not Path(args.log_dir).exists():
        print(f"❌ エラー: ディレクトリ {args.log_dir} が存在しません")
        sys.exit(1)

    analyze_final_results(args.log_dir)

if __name__ == "__main__":
    main()