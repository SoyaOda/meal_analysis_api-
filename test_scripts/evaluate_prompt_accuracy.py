#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
プロンプト精度・再現性評価スクリプト

機能:
- 50枚のテスト画像でプロンプトの精度を評価
- 複数回実行による再現性評価
- ラベル（正解データ）との比較
- 詳細な統計指標（MAE, 標準偏差, 中央値, 高誤差率）

Usage:
    # デフォルトプロンプトで1回実行
    python test_scripts/evaluate_prompt_accuracy.py

    # カスタムプロンプトで5回実行（再現性評価）
    python test_scripts/evaluate_prompt_accuracy.py \
      --prompt apps/freeform_usda_meal_analysis_api/prompts/test_prompt_B_decompose.txt \
      --runs 5

    # 特定モデルで評価
    python test_scripts/evaluate_prompt_accuracy.py \
      --model openrouter:google/gemini-2.5-flash-preview \
      --runs 3 \
      --limit 10

Arguments:
    --prompt PROMPT_FILE    プロンプトファイルパス（指定しない場合はAPIデフォルト）
    --model MODEL_ID        VLMモデルID
    --api-url URL           API URL (デフォルト: http://localhost:8006)
    --runs N                実行回数 (デフォルト: 1、再現性評価には3-5推奨)
    --concurrent N          並行リクエスト数 (デフォルト: 3)
    --limit N               処理する画像数 (デフォルト: 50)
"""

import json
import sys
import asyncio
import logging
import aiohttp
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# プロジェクトルート
project_root = Path(__file__).parent.parent


@dataclass
class NutritionStats:
    """栄養素統計"""
    mae: float = 0.0           # 平均絶対誤差
    std: float = 0.0           # 標準偏差
    median: float = 0.0        # 中央値
    min_error: float = 0.0     # 最小誤差
    max_error: float = 0.0     # 最大誤差
    high_error_count: int = 0  # 30%以上誤差件数
    high_error_rate: float = 0.0  # 30%以上誤差率


@dataclass
class RunResult:
    """1回の実行結果"""
    run_id: int
    timestamp: str
    success_count: int
    error_count: int
    calorie_stats: NutritionStats
    protein_stats: NutritionStats
    fat_stats: NutritionStats
    carbs_stats: NutritionStats
    image_results: List[Dict[str, Any]] = field(default_factory=list)
    total_time_seconds: float = 0.0


@dataclass
class ReproducibilityStats:
    """再現性統計"""
    calorie_variance: float = 0.0      # カロリー分散（画像間）
    calorie_cv: float = 0.0            # 変動係数
    consistent_images: int = 0         # 全実行で一貫した結果の画像数
    consistency_rate: float = 0.0      # 一貫性率


def load_label_nutrition(label_path: str) -> dict:
    """ラベルから栄養素を集計"""
    with open(label_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_calorie = 0.0
    total_protein_g = 0.0
    total_fat_g = 0.0
    total_carbs_g = 0.0
    items = []

    for dish in data.get("dishes", []):
        # main_food
        main_food = dish.get("main_food")
        if main_food:
            nutrition = main_food.get("nutrition", {})
            total_calorie += nutrition.get("calorie", 0) or 0
            total_protein_g += nutrition.get("protein_g", 0) or 0
            total_fat_g += nutrition.get("fat_g", 0) or 0
            total_carbs_g += nutrition.get("carbs_g", 0) or 0

            items.append({
                "type": "main_food",
                "search_name": main_food.get("search_name"),
                "weight_g": main_food.get("weight_g"),
                "nutrition": nutrition
            })

        # extras
        for extra in dish.get("extras", []):
            nutrition = extra.get("nutrition", {})
            total_calorie += nutrition.get("calorie", 0) or 0
            total_protein_g += nutrition.get("protein_g", 0) or 0
            total_fat_g += nutrition.get("fat_g", 0) or 0
            total_carbs_g += nutrition.get("carbs_g", 0) or 0

            items.append({
                "type": "extra",
                "search_name": extra.get("search_name"),
                "weight_g": extra.get("weight_g"),
                "nutrition": nutrition
            })

    return {
        "total_calorie": total_calorie,
        "total_protein_g": total_protein_g,
        "total_fat_g": total_fat_g,
        "total_carbs_g": total_carbs_g,
        "items": items
    }


async def call_api(
    session: aiohttp.ClientSession,
    api_url: str,
    image_path: str,
    model_id: Optional[str] = None,
    prompt_path: Optional[str] = None
) -> dict:
    """API呼び出し"""
    endpoint = f"{api_url}/api/v1/meal-analyses/complete"

    with open(image_path, 'rb') as f:
        image_data = f.read()

    data = aiohttp.FormData()
    data.add_field('image', image_data,
                   filename=Path(image_path).name,
                   content_type='image/jpeg')

    if model_id:
        data.add_field('model_id', model_id)

    if prompt_path:
        data.add_field('prompt_path', prompt_path)

    timeout = aiohttp.ClientTimeout(total=300)
    async with session.post(endpoint, data=data, timeout=timeout) as response:
        if response.status != 200:
            error_text = await response.text()
            raise Exception(f"API Error {response.status}: {error_text[:200]}")

        result = await response.json()

        # 栄養素を抽出
        total_nutrition = {
            "calories": 0.0,
            "protein_g": 0.0,
            "fat_g": 0.0,
            "carbs_g": 0.0
        }

        for dish in result.get("dishes", []):
            dish_nutrition = dish.get("total_nutrition", {})
            total_nutrition["calories"] += dish_nutrition.get("calories", 0) or 0
            total_nutrition["protein_g"] += dish_nutrition.get("protein", 0) or 0
            total_nutrition["fat_g"] += dish_nutrition.get("fat", 0) or 0
            total_nutrition["carbs_g"] += dish_nutrition.get("carbs", 0) or 0

        return {
            "total_nutrition": total_nutrition,
            "dishes": result.get("dishes", []),
            "processing_time": result.get("processing_time_seconds", 0),
            "usage": result.get("usage", {})
        }


def calculate_error(label: dict, api_result: dict) -> dict:
    """誤差計算（絶対値ベース）"""
    api_cal = api_result.get('calories', 0) or 0
    label_cal = label['total_calorie']

    diff_cal = api_cal - label_cal
    diff_protein = (api_result.get('protein_g', 0) or 0) - label['total_protein_g']
    diff_fat = (api_result.get('fat_g', 0) or 0) - label['total_fat_g']
    diff_carbs = (api_result.get('carbs_g', 0) or 0) - label['total_carbs_g']

    return {
        "calorie": {
            "diff": diff_cal,
            "abs_diff": abs(diff_cal),
            "percent": (diff_cal / label_cal * 100) if label_cal > 0 else 0,
            "abs_percent": (abs(diff_cal) / label_cal * 100) if label_cal > 0 else 0
        },
        "protein_g": {
            "diff": diff_protein,
            "abs_diff": abs(diff_protein),
            "percent": (diff_protein / label['total_protein_g'] * 100) if label['total_protein_g'] > 0 else 0,
            "abs_percent": (abs(diff_protein) / label['total_protein_g'] * 100) if label['total_protein_g'] > 0 else 0
        },
        "fat_g": {
            "diff": diff_fat,
            "abs_diff": abs(diff_fat),
            "percent": (diff_fat / label['total_fat_g'] * 100) if label['total_fat_g'] > 0 else 0,
            "abs_percent": (abs(diff_fat) / label['total_fat_g'] * 100) if label['total_fat_g'] > 0 else 0
        },
        "carbs_g": {
            "diff": diff_carbs,
            "abs_diff": abs(diff_carbs),
            "percent": (diff_carbs / label['total_carbs_g'] * 100) if label['total_carbs_g'] > 0 else 0,
            "abs_percent": (abs(diff_carbs) / label['total_carbs_g'] * 100) if label['total_carbs_g'] > 0 else 0
        }
    }


def calculate_nutrition_stats(errors: List[float], threshold: float = 30.0) -> NutritionStats:
    """栄養素統計を計算"""
    if not errors:
        return NutritionStats()

    abs_errors = [abs(e) for e in errors]
    high_error_count = sum(1 for e in abs_errors if e >= threshold)

    return NutritionStats(
        mae=statistics.mean(abs_errors),
        std=statistics.stdev(errors) if len(errors) > 1 else 0.0,
        median=statistics.median(abs_errors),
        min_error=min(abs_errors),
        max_error=max(abs_errors),
        high_error_count=high_error_count,
        high_error_rate=high_error_count / len(errors) * 100
    )


async def process_image(
    session: aiohttp.ClientSession,
    api_url: str,
    model_id: Optional[str],
    prompt_path: Optional[str],
    image_index: int,
    semaphore: asyncio.Semaphore
) -> Optional[dict]:
    """1画像を処理"""
    async with semaphore:
        image_name = f"test_food{image_index}.jpg"
        image_path = project_root / f"test_images/images/{image_name}"
        label_path = project_root / f"test_images/images_label_with_nutrition/test_food{image_index:02d}.json"

        try:
            label_nutrition = load_label_nutrition(str(label_path))
            api_result = await call_api(
                session, api_url, str(image_path), model_id, prompt_path
            )
            error = calculate_error(label_nutrition, api_result['total_nutrition'])

            logger.info(
                f"[{image_index:02d}] {image_name}: "
                f"Label {label_nutrition['total_calorie']:.0f} | "
                f"API {api_result['total_nutrition']['calories']:.0f} | "
                f"誤差 {error['calorie']['percent']:+.1f}%"
            )

            return {
                "image_name": image_name,
                "image_index": image_index,
                "label_nutrition": label_nutrition,
                "api_result": api_result,
                "error": error,
                "success": True
            }

        except Exception as e:
            logger.error(f"[{image_index:02d}] {image_name}: エラー - {e}")
            return {
                "image_name": image_name,
                "image_index": image_index,
                "error_message": str(e),
                "success": False
            }


async def run_single_evaluation(
    run_id: int,
    api_url: str,
    model_id: Optional[str],
    prompt_path: Optional[str],
    limit: int,
    concurrent: int
) -> RunResult:
    """1回の評価実行"""
    import time
    start_time = time.time()

    logger.info(f"\n{'='*60}")
    logger.info(f"Run {run_id} 開始")
    logger.info(f"{'='*60}")

    semaphore = asyncio.Semaphore(concurrent)

    async with aiohttp.ClientSession() as session:
        tasks = [
            process_image(session, api_url, model_id, prompt_path, i, semaphore)
            for i in range(1, limit + 1)
        ]
        results = await asyncio.gather(*tasks)

    # 成功/失敗を分離
    success_results = [r for r in results if r and r.get('success')]
    error_results = [r for r in results if r and not r.get('success')]

    # 統計計算
    cal_errors = [r['error']['calorie']['percent'] for r in success_results]
    protein_errors = [r['error']['protein_g']['percent'] for r in success_results]
    fat_errors = [r['error']['fat_g']['percent'] for r in success_results]
    carbs_errors = [r['error']['carbs_g']['percent'] for r in success_results]

    elapsed_time = time.time() - start_time

    return RunResult(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        success_count=len(success_results),
        error_count=len(error_results),
        calorie_stats=calculate_nutrition_stats(cal_errors),
        protein_stats=calculate_nutrition_stats(protein_errors),
        fat_stats=calculate_nutrition_stats(fat_errors),
        carbs_stats=calculate_nutrition_stats(carbs_errors),
        image_results=success_results,
        total_time_seconds=elapsed_time
    )


def calculate_reproducibility(runs: List[RunResult]) -> ReproducibilityStats:
    """再現性統計を計算"""
    if len(runs) < 2:
        return ReproducibilityStats()

    # 画像ごとのカロリー結果を収集
    image_calories: Dict[str, List[float]] = {}

    for run in runs:
        for img_result in run.image_results:
            img_name = img_result['image_name']
            cal = img_result['api_result']['total_nutrition']['calories']
            if img_name not in image_calories:
                image_calories[img_name] = []
            image_calories[img_name].append(cal)

    # 各画像のカロリー分散を計算
    variances = []
    consistent_count = 0

    for img_name, calories in image_calories.items():
        if len(calories) >= 2:
            var = statistics.variance(calories)
            variances.append(var)
            # 標準偏差が平均の5%以内なら一貫性あり
            mean_cal = statistics.mean(calories)
            std_cal = statistics.stdev(calories)
            if mean_cal > 0 and (std_cal / mean_cal) < 0.05:
                consistent_count += 1

    avg_variance = statistics.mean(variances) if variances else 0

    # 全画像の平均カロリーから変動係数を計算
    all_means = [statistics.mean(cals) for cals in image_calories.values() if len(cals) >= 2]
    overall_mean = statistics.mean(all_means) if all_means else 0
    cv = (avg_variance ** 0.5 / overall_mean * 100) if overall_mean > 0 else 0

    return ReproducibilityStats(
        calorie_variance=avg_variance,
        calorie_cv=cv,
        consistent_images=consistent_count,
        consistency_rate=(consistent_count / len(image_calories) * 100) if image_calories else 0
    )


def generate_report(
    runs: List[RunResult],
    reproducibility: ReproducibilityStats,
    config: dict,
    output_path: str
):
    """Markdownレポート生成"""
    md = []
    md.append("# プロンプト精度・再現性評価レポート\n")
    md.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 設定情報
    md.append("## 評価設定\n")
    md.append(f"| 項目 | 値 |")
    md.append(f"|------|-----|")
    md.append(f"| プロンプト | `{config.get('prompt_path', 'デフォルト')}` |")
    md.append(f"| モデル | `{config.get('model_id', 'デフォルト')}` |")
    md.append(f"| 実行回数 | {len(runs)} |")
    md.append(f"| 画像数 | {config.get('limit', 50)} |")
    md.append("")

    # サマリー統計（全実行の平均）
    md.append("## 精度サマリー\n")

    if runs:
        avg_mae_cal = statistics.mean([r.calorie_stats.mae for r in runs])
        avg_mae_protein = statistics.mean([r.protein_stats.mae for r in runs])
        avg_mae_fat = statistics.mean([r.fat_stats.mae for r in runs])
        avg_mae_carbs = statistics.mean([r.carbs_stats.mae for r in runs])

        avg_high_error = statistics.mean([r.calorie_stats.high_error_rate for r in runs])

        md.append("### 平均絶対誤差 (MAE)\n")
        md.append("| 栄養素 | MAE (%) | 30%以上誤差率 |")
        md.append("|--------|---------|---------------|")
        md.append(f"| カロリー | {avg_mae_cal:.1f}% | {avg_high_error:.1f}% |")
        md.append(f"| タンパク質 | {avg_mae_protein:.1f}% | - |")
        md.append(f"| 脂質 | {avg_mae_fat:.1f}% | - |")
        md.append(f"| 炭水化物 | {avg_mae_carbs:.1f}% | - |")
        md.append("")

    # 再現性統計（複数実行の場合）
    if len(runs) >= 2:
        md.append("## 再現性評価\n")
        md.append(f"| 指標 | 値 |")
        md.append(f"|------|-----|")
        md.append(f"| カロリー分散（画像間平均） | {reproducibility.calorie_variance:.1f} |")
        md.append(f"| 変動係数 (CV) | {reproducibility.calorie_cv:.1f}% |")
        md.append(f"| 一貫性のある画像数 | {reproducibility.consistent_images}/{len(runs[0].image_results) if runs else 0} |")
        md.append(f"| 一貫性率 | {reproducibility.consistency_rate:.1f}% |")
        md.append("")

    # 各実行の詳細
    md.append("## 実行別詳細\n")

    for run in runs:
        md.append(f"### Run {run.run_id}\n")
        md.append(f"- 成功: {run.success_count}, 失敗: {run.error_count}")
        md.append(f"- 処理時間: {run.total_time_seconds:.1f}秒")
        md.append("")

        md.append("| 栄養素 | MAE | 標準偏差 | 中央値 | 最小 | 最大 | 30%以上 |")
        md.append("|--------|-----|----------|--------|------|------|---------|")

        for name, stats in [
            ("カロリー", run.calorie_stats),
            ("タンパク質", run.protein_stats),
            ("脂質", run.fat_stats),
            ("炭水化物", run.carbs_stats)
        ]:
            md.append(
                f"| {name} | {stats.mae:.1f}% | {stats.std:.1f}% | "
                f"{stats.median:.1f}% | {stats.min_error:.1f}% | "
                f"{stats.max_error:.1f}% | {stats.high_error_count}件 |"
            )
        md.append("")

    # 高誤差ケース一覧
    if runs:
        md.append("## 高誤差ケース (カロリー誤差 >= 30%)\n")

        high_error_cases = []
        for run in runs:
            for img in run.image_results:
                abs_err = abs(img['error']['calorie']['percent'])
                if abs_err >= 30:
                    high_error_cases.append({
                        "run_id": run.run_id,
                        "image": img['image_name'],
                        "label_cal": img['label_nutrition']['total_calorie'],
                        "api_cal": img['api_result']['total_nutrition']['calories'],
                        "error_pct": img['error']['calorie']['percent']
                    })

        if high_error_cases:
            md.append("| Run | 画像 | Label Cal | API Cal | 誤差 |")
            md.append("|-----|------|-----------|---------|------|")
            for case in sorted(high_error_cases, key=lambda x: abs(x['error_pct']), reverse=True)[:20]:
                md.append(
                    f"| {case['run_id']} | {case['image']} | "
                    f"{case['label_cal']:.0f} | {case['api_cal']:.0f} | "
                    f"{case['error_pct']:+.1f}% |"
                )
        else:
            md.append("高誤差ケースはありません。\n")

    # ファイル出力
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    logger.info(f"レポート生成: {output_path}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="プロンプト精度・再現性評価"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="プロンプトファイルパス"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="VLMモデルID"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8006",
        help="API URL"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="実行回数（再現性評価には3-5推奨）"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=3,
        help="並行リクエスト数"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="処理する画像数"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("プロンプト精度・再現性評価")
    print("=" * 70)
    print(f"プロンプト: {args.prompt or 'デフォルト'}")
    print(f"モデル: {args.model or 'デフォルト'}")
    print(f"実行回数: {args.runs}")
    print(f"画像数: {args.limit}")
    print(f"並行数: {args.concurrent}")
    print("=" * 70)
    print()

    # 複数回実行
    all_runs: List[RunResult] = []

    for run_id in range(1, args.runs + 1):
        run_result = await run_single_evaluation(
            run_id=run_id,
            api_url=args.api_url,
            model_id=args.model,
            prompt_path=args.prompt,
            limit=args.limit,
            concurrent=args.concurrent
        )
        all_runs.append(run_result)

        # Run結果サマリー表示
        print(f"\n[Run {run_id}] 完了: "
              f"成功={run_result.success_count}, "
              f"MAE={run_result.calorie_stats.mae:.1f}%, "
              f"30%以上={run_result.calorie_stats.high_error_count}件")

    # 再現性統計
    reproducibility = calculate_reproducibility(all_runs)

    # 最終サマリー表示
    print("\n" + "=" * 70)
    print("最終結果")
    print("=" * 70)

    if all_runs:
        avg_mae = statistics.mean([r.calorie_stats.mae for r in all_runs])
        avg_high_error = statistics.mean([r.calorie_stats.high_error_rate for r in all_runs])

        print(f"平均MAE (カロリー): {avg_mae:.1f}%")
        print(f"平均30%以上誤差率: {avg_high_error:.1f}%")

        if len(all_runs) >= 2:
            print(f"再現性 (一貫性率): {reproducibility.consistency_rate:.1f}%")

    # レポート・JSON出力
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_name = Path(args.prompt).stem if args.prompt else "default"

    output_dir = project_root / "test_scripts/output"
    output_dir.mkdir(exist_ok=True)

    md_path = output_dir / f"prompt_eval_{prompt_name}_{timestamp}.md"
    json_path = output_dir / f"prompt_eval_{prompt_name}_{timestamp}.json"

    config = {
        "prompt_path": args.prompt,
        "model_id": args.model,
        "api_url": args.api_url,
        "runs": args.runs,
        "limit": args.limit,
        "concurrent": args.concurrent
    }

    generate_report(all_runs, reproducibility, config, str(md_path))

    # JSON保存
    json_data = {
        "config": config,
        "runs": [asdict(r) for r in all_runs],
        "reproducibility": asdict(reproducibility)
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nMarkdownレポート: {md_path}")
    print(f"JSON詳細: {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
