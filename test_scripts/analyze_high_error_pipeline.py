#!/usr/bin/env python
"""
30%以上のカロリー誤差がある画像の詳細Pipeline分析スクリプト

全プロンプトで30%以上誤差がある画像を優先的に分析し、
VLM出力→クエリ→検索→栄養素計算の各段階での問題を特定する。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

def load_test_results(json_path: str) -> List[Dict]:
    """テスト結果JSONを読み込む（画像リスト形式）"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_error(predicted: float, labeled: float) -> float:
    """誤差率を計算"""
    if labeled == 0:
        return 0.0
    return ((predicted - labeled) / labeled) * 100

def identify_high_error_images(results: List[Dict], threshold: float = 30.0) -> Dict[str, List[Dict]]:
    """30%以上の誤差がある画像を特定

    Args:
        results: 画像ごとの結果リスト
        threshold: 誤差率の閾値（デフォルト30%）

    Returns:
        画像名をキーとした高誤差プロンプトのリスト
    """
    high_error_images = defaultdict(list)

    for image_data in results:
        image_name = image_data['image_name']
        label_nutrition = image_data['label_nutrition']
        label_cal = label_nutrition['total_calorie']

        # 各プロンプトの結果を確認
        for prompt_name, prompt_result in image_data.get('prompt_results', {}).items():
            pred_cal = prompt_result['total_nutrition']['calories']
            error_pct = prompt_result['diff']['calorie']['percent']

            if abs(error_pct) >= threshold:
                high_error_images[image_name].append({
                    'prompt': prompt_name,
                    'error': error_pct,
                    'predicted': pred_cal,
                    'labeled': label_cal
                })

    return high_error_images

def analyze_pipeline_for_image(image_name: str, prompt_name: str, results: List[Dict]) -> Dict[str, Any]:
    """特定の画像とプロンプトについてPipelineを詳細分析

    Args:
        image_name: 画像ファイル名
        prompt_name: プロンプト名
        results: 全画像の結果リスト

    Returns:
        分析結果の辞書
    """
    # 該当画像のデータを探す
    image_data = None
    for img in results:
        if img['image_name'] == image_name:
            image_data = img
            break

    if not image_data:
        return {'error': f'Image {image_name} not found'}

    label_nutrition = image_data['label_nutrition']
    prompt_result = image_data['prompt_results'][prompt_name]

    analysis = {
        'image_name': image_name,
        'prompt': prompt_name,
        'label_nutrition': label_nutrition,
        'predicted_nutrition': prompt_result['total_nutrition'],
        'diff': prompt_result['diff'],
        'label_items': label_nutrition.get('items', []),
        'label_total_weight': sum(item['weight_g'] for item in label_nutrition.get('items', []))
    }

    return analysis

def generate_pipeline_report(results: List[Dict], output_path: str):
    """詳細なPipelineレポートを生成

    Args:
        results: 全画像の結果リスト
        output_path: レポート出力先パス
    """
    high_error_images = identify_high_error_images(results, threshold=30.0)

    # 全プロンプトで失敗している画像を特定
    critical_images = {
        img_name: errors
        for img_name, errors in high_error_images.items()
        if len(errors) >= 3  # 全3プロンプトで失敗
    }

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

    report_lines = []
    report_lines.append("# 30%以上カロリー誤差の詳細Pipeline分析レポート")
    report_lines.append("")
    report_lines.append(f"**生成日時**: {timestamp}")
    report_lines.append(f"**テスト画像総数**: {len(results)}")
    report_lines.append("")

    # サマリー
    report_lines.append("## 📊 高誤差画像サマリー")
    report_lines.append("")
    report_lines.append(f"- **30%以上誤差の画像総数**: {len(high_error_images)}")
    report_lines.append(f"- **全3プロンプトで30%以上誤差**: {len(critical_images)}件")
    report_lines.append("")

    # プロンプト別の高誤差件数
    prompt_error_counts = defaultdict(int)
    for errors in high_error_images.values():
        for error_data in errors:
            prompt_error_counts[error_data['prompt']] += 1

    report_lines.append("### プロンプト別30%以上誤差件数")
    report_lines.append("")
    for prompt, count in sorted(prompt_error_counts.items()):
        report_lines.append(f"- **{prompt}**: {count}件")
    report_lines.append("")

    # 全プロンプトで失敗している画像の詳細分析
    if critical_images:
        report_lines.append("## 🔴 Critical: 全プロンプトで30%以上誤差の画像")
        report_lines.append("")

        for img_name in sorted(critical_images.keys()):
            errors = critical_images[img_name]
            report_lines.append(f"### 画像: {img_name}")
            report_lines.append("")

            # エラー率の比較
            report_lines.append("#### 各プロンプトのエラー率")
            report_lines.append("")
            report_lines.append("| プロンプト | 予測カロリー | ラベルカロリー | 誤差率 |")
            report_lines.append("|-----------|------------|-------------|--------|")

            for error_data in sorted(errors, key=lambda x: x['prompt']):
                report_lines.append(
                    f"| {error_data['prompt']} | "
                    f"{error_data['predicted']:.1f} kcal | "
                    f"{error_data['labeled']:.1f} kcal | "
                    f"{error_data['error']:+.1f}% |"
                )

            report_lines.append("")

            # 各プロンプトのPipeline詳細分析
            for error_data in sorted(errors, key=lambda x: x['prompt']):
                prompt_name = error_data['prompt']
                analysis = analyze_pipeline_for_image(img_name, prompt_name, results)

                report_lines.append(f"#### Pipeline分析: {prompt_name}")
                report_lines.append("")

                # ラベルアイテム（正解データ）
                report_lines.append("**ラベルアイテム（正解データ）:**")
                report_lines.append("")

                if not analysis.get('label_items'):
                    report_lines.append("⚠️ **ラベルアイテムがありません**")
                else:
                    for i, item in enumerate(analysis['label_items'], 1):
                        report_lines.append(
                            f"{i}. **{item['type']}**: {item['search_name']} - "
                            f"{item['weight_g']}g "
                            f"(Cal: {item['nutrition']['calorie']:.1f}, "
                            f"Pro: {item['nutrition']['protein_g']:.1f}g, "
                            f"Fat: {item['nutrition']['fat_g']:.1f}g, "
                            f"Carbs: {item['nutrition']['carbs_g']:.1f}g)"
                        )

                report_lines.append("")
                report_lines.append(f"**ラベル総重量**: {analysis['label_total_weight']}g")
                report_lines.append("")

                # 栄養素比較
                report_lines.append("**栄養素比較:**")
                report_lines.append("")
                report_lines.append("| 栄養素 | 予測値 | ラベル値 | 誤差 |")
                report_lines.append("|--------|--------|----------|------|")

                nutrient_mapping = {
                    'calories': ('total_calorie', 'calorie'),
                    'protein_g': ('total_protein_g', 'protein_g'),
                    'fat_g': ('total_fat_g', 'fat_g'),
                    'carbs_g': ('total_carbs_g', 'carbs_g')
                }

                for pred_key, (label_key, diff_key) in nutrient_mapping.items():
                    pred = analysis['predicted_nutrition'].get(pred_key, 0)
                    label = analysis['label_nutrition'].get(label_key, 0)
                    error_pct = analysis['diff'].get(diff_key, {}).get('percent', 0)

                    report_lines.append(
                        f"| {pred_key} | {pred:.1f} | {label:.1f} | {error_pct:+.1f}% |"
                    )

                report_lines.append("")
                report_lines.append("---")
                report_lines.append("")

            report_lines.append("")

    # 2プロンプトで失敗している画像
    two_prompt_errors = {
        img_name: errors
        for img_name, errors in high_error_images.items()
        if len(errors) == 2
    }

    if two_prompt_errors:
        report_lines.append("## 🟡 2プロンプトで30%以上誤差の画像")
        report_lines.append("")

        for img_name in sorted(two_prompt_errors.keys()):
            errors = two_prompt_errors[img_name]
            prompts = [e['prompt'] for e in errors]
            error_avg = sum(abs(e['error']) for e in errors) / len(errors)

            report_lines.append(
                f"- **{img_name}**: {', '.join(prompts)} "
                f"(平均誤差: {error_avg:.1f}%)"
            )

        report_lines.append("")

    # 1プロンプトのみで失敗している画像
    single_prompt_errors = {
        img_name: errors
        for img_name, errors in high_error_images.items()
        if len(errors) == 1
    }

    if single_prompt_errors:
        report_lines.append("## 🟢 1プロンプトのみ30%以上誤差の画像")
        report_lines.append("")

        by_prompt = defaultdict(list)
        for img_name, errors in single_prompt_errors.items():
            prompt = errors[0]['prompt']
            error = errors[0]['error']
            by_prompt[prompt].append((img_name, error))

        for prompt in sorted(by_prompt.keys()):
            images = by_prompt[prompt]
            report_lines.append(f"### {prompt}: {len(images)}件")
            report_lines.append("")

            for img_name, error in sorted(images, key=lambda x: -abs(x[1])):
                report_lines.append(f"- **{img_name}**: {error:+.1f}%")

            report_lines.append("")

    # レポートを保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"✅ レポート生成完了: {output_path}")
    print(f"\n📊 サマリー:")
    print(f"  - 30%以上誤差の画像総数: {len(high_error_images)}")
    print(f"  - 全3プロンプトで失敗: {len(critical_images)}件")
    print(f"  - 2プロンプトで失敗: {len(two_prompt_errors)}件")
    print(f"  - 1プロンプトのみ失敗: {len(single_prompt_errors)}件")

def main():
    # 最新の結果ファイルを使用
    results_dir = Path(__file__).parent / 'output'
    json_file = results_dir / 'vlm_prompt_nutrition_comparison_20251027_144355.json'

    if not json_file.exists():
        print(f"❌ 結果ファイルが見つかりません: {json_file}")
        sys.exit(1)

    print(f"📖 結果ファイル読み込み中: {json_file}")
    results = load_test_results(str(json_file))

    # レポート生成
    output_file = results_dir / 'pipeline_detailed_analysis_20251027.md'
    generate_pipeline_report(results, str(output_file))

if __name__ == '__main__':
    main()
