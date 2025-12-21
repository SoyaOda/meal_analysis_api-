#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
プロンプト一括評価スクリプト

複数のプロンプト × 複数のモデル × 指定回数のテストを一括実行し、
全結果を保存・集計する。

Usage:
    # デフォルト設定で実行
    python test_scripts/batch_evaluate_prompts.py

    # カスタム設定
    python test_scripts/batch_evaluate_prompts.py \
        --prompts prompt1.txt prompt2.txt \
        --models "openrouter:openai/gpt-5.1" "openrouter:google/gemini-3-flash-preview" \
        --runs 5

    # 設定ファイルから実行
    python test_scripts/batch_evaluate_prompts.py --config batch_config.json
"""

import json
import sys
import asyncio
import logging
import aiohttp
import statistics
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import time

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
    mae: float = 0.0
    std: float = 0.0
    median: float = 0.0
    min_error: float = 0.0
    max_error: float = 0.0
    high_error_count: int = 0
    high_error_rate: float = 0.0


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
class PromptModelResult:
    """プロンプト×モデルの結果"""
    prompt_name: str
    model_id: str
    runs: List[RunResult] = field(default_factory=list)
    avg_calorie_mae: float = 0.0
    avg_high_error_rate: float = 0.0
    calorie_cv: float = 0.0  # 変動係数
    consistency_rate: float = 0.0


def load_label_nutrition(label_path: str) -> dict:
    """ラベルから栄養素を集計（元スクリプト準拠）"""
    with open(label_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_calorie = 0.0
    total_protein_g = 0.0
    total_fat_g = 0.0
    total_carbs_g = 0.0

    for dish in data.get("dishes", []):
        # main_food
        main_food = dish.get("main_food")
        if main_food:
            nutrition = main_food.get("nutrition", {})
            total_calorie += nutrition.get("calorie", 0) or 0
            total_protein_g += nutrition.get("protein_g", 0) or 0
            total_fat_g += nutrition.get("fat_g", 0) or 0
            total_carbs_g += nutrition.get("carbs_g", 0) or 0

        # extras
        for extra in dish.get("extras", []):
            nutrition = extra.get("nutrition", {})
            total_calorie += nutrition.get("calorie", 0) or 0
            total_protein_g += nutrition.get("protein_g", 0) or 0
            total_fat_g += nutrition.get("fat_g", 0) or 0
            total_carbs_g += nutrition.get("carbs_g", 0) or 0

    return {
        "calorie": total_calorie,
        "protein_g": total_protein_g,
        "fat_g": total_fat_g,
        "carbohydrate_g": total_carbs_g
    }


async def analyze_image(
    session: aiohttp.ClientSession,
    image_path: Path,
    api_url: str,
    model_id: str,
    prompt_content: Optional[str] = None
) -> Dict[str, Any]:
    """画像を分析"""
    url = f"{api_url}/api/v1/meal-analyses/complete"

    data = aiohttp.FormData()
    data.add_field('image', open(image_path, 'rb'), filename=image_path.name)
    data.add_field('model_id', model_id)
    if prompt_content:
        data.add_field('custom_prompt', prompt_content)

    try:
        async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=120)) as resp:
            if resp.status == 200:
                result = await resp.json()
                return {"success": True, "data": result}
            else:
                error_text = await resp.text()
                return {"success": False, "error": f"HTTP {resp.status}: {error_text[:200]}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def calculate_error(label_val: float, api_val: float) -> float:
    """誤差率を計算"""
    if label_val == 0:
        return 0.0 if api_val == 0 else 100.0
    return abs(api_val - label_val) / label_val * 100


def calculate_stats(errors: List[float]) -> NutritionStats:
    """統計を計算"""
    if not errors:
        return NutritionStats()

    high_errors = [e for e in errors if e >= 30]

    return NutritionStats(
        mae=statistics.mean(errors),
        std=statistics.stdev(errors) if len(errors) > 1 else 0,
        median=statistics.median(errors),
        min_error=min(errors),
        max_error=max(errors),
        high_error_count=len(high_errors),
        high_error_rate=len(high_errors) / len(errors) * 100
    )


async def run_single_evaluation(
    prompt_path: Optional[Path],
    model_id: str,
    run_id: int,
    api_url: str,
    concurrent: int,
    test_images_dir: Path,
    labels_dir: Path,
    num_images: int = 50
) -> RunResult:
    """1回の評価を実行"""
    start_time = time.time()

    # プロンプト読み込み
    prompt_content = None
    if prompt_path and prompt_path.exists():
        prompt_content = prompt_path.read_text(encoding='utf-8')

    # テスト画像一覧（test_food1.jpg ~ test_food50.jpg）
    image_files = []
    for i in range(1, num_images + 1):
        img_path = test_images_dir / f"test_food{i}.jpg"
        if img_path.exists():
            image_files.append((i, img_path))
        else:
            # 代替パス確認
            alt_path = test_images_dir / f"food{i}.jpg"
            if alt_path.exists():
                image_files.append((i, alt_path))

    calorie_errors = []
    protein_errors = []
    fat_errors = []
    carbs_errors = []
    image_results = []
    success_count = 0
    error_count = 0

    semaphore = asyncio.Semaphore(concurrent)

    async def process_image(session: aiohttp.ClientSession, img_idx: int, img_path: Path):
        nonlocal success_count, error_count

        async with semaphore:
            # ラベル読み込み（test_food01.json形式）
            label_path = labels_dir / f"test_food{img_idx:02d}.json"
            if not label_path.exists():
                logger.warning(f"Label not found: {label_path}")
                return None

            label_nutrition = load_label_nutrition(str(label_path))

            # API呼び出し
            result = await analyze_image(session, img_path, api_url, model_id, prompt_content)

            if result["success"]:
                success_count += 1
                api_data = result["data"]

                # 栄養素取得
                api_nutrition = api_data.get("total_nutrition", {})
                api_cal = api_nutrition.get("calories", 0) or 0
                api_protein = api_nutrition.get("protein_g", 0) or 0
                api_fat = api_nutrition.get("fat_g", 0) or 0
                api_carbs = api_nutrition.get("carbohydrate_g", 0) or 0

                # 誤差計算
                cal_err = calculate_error(label_nutrition["calorie"], api_cal)
                prot_err = calculate_error(label_nutrition["protein_g"], api_protein)
                fat_err = calculate_error(label_nutrition["fat_g"], api_fat)
                carb_err = calculate_error(label_nutrition["carbohydrate_g"], api_carbs)

                return {
                    "image": img_path.name,
                    "label_cal": label_nutrition["calorie"],
                    "api_cal": api_cal,
                    "cal_error": cal_err,
                    "prot_error": prot_err,
                    "fat_error": fat_err,
                    "carb_error": carb_err,
                    "success": True
                }
            else:
                error_count += 1
                return {
                    "image": img_path.name,
                    "success": False,
                    "error": result.get("error", "Unknown")
                }

    async with aiohttp.ClientSession() as session:
        tasks = [process_image(session, idx, img) for idx, img in image_files]
        results = await asyncio.gather(*tasks)

    for r in results:
        if r and r.get("success"):
            calorie_errors.append(r["cal_error"])
            protein_errors.append(r["prot_error"])
            fat_errors.append(r["fat_error"])
            carbs_errors.append(r["carb_error"])
            image_results.append(r)
        elif r:
            image_results.append(r)

    elapsed = time.time() - start_time

    return RunResult(
        run_id=run_id,
        timestamp=datetime.now().isoformat(),
        success_count=success_count,
        error_count=error_count,
        calorie_stats=calculate_stats(calorie_errors),
        protein_stats=calculate_stats(protein_errors),
        fat_stats=calculate_stats(fat_errors),
        carbs_stats=calculate_stats(carbs_errors),
        image_results=image_results,
        total_time_seconds=elapsed
    )


async def evaluate_prompt_model(
    prompt_path: Optional[Path],
    model_id: str,
    num_runs: int,
    api_url: str,
    concurrent: int,
    test_images_dir: Path,
    labels_dir: Path
) -> PromptModelResult:
    """プロンプト×モデルの評価"""
    prompt_name = prompt_path.stem if prompt_path else "default"
    logger.info(f"Starting evaluation: {prompt_name} × {model_id} × {num_runs} runs")

    runs = []
    for i in range(num_runs):
        logger.info(f"  Run {i+1}/{num_runs}...")
        run_result = await run_single_evaluation(
            prompt_path, model_id, i+1, api_url, concurrent,
            test_images_dir, labels_dir
        )
        runs.append(run_result)
        logger.info(f"  Run {i+1} complete: MAE={run_result.calorie_stats.mae:.1f}%, "
                   f"30%+={run_result.calorie_stats.high_error_rate:.1f}%")

    # 集計
    maes = [r.calorie_stats.mae for r in runs]
    high_error_rates = [r.calorie_stats.high_error_rate for r in runs]

    avg_mae = statistics.mean(maes) if maes else 0
    avg_high_error = statistics.mean(high_error_rates) if high_error_rates else 0
    cv = (statistics.stdev(maes) / avg_mae * 100) if len(maes) > 1 and avg_mae > 0 else 0

    # 一貫性評価（全ラン間でカロリー誤差10%以内）
    if len(runs) > 1:
        consistent_count = 0
        num_images = len(runs[0].image_results)
        for img_idx in range(num_images):
            cals = []
            for run in runs:
                if img_idx < len(run.image_results) and run.image_results[img_idx].get("success"):
                    cals.append(run.image_results[img_idx].get("api_cal", 0))
            if len(cals) == len(runs) and cals:
                mean_cal = statistics.mean(cals)
                if mean_cal > 0:
                    max_dev = max(abs(c - mean_cal) / mean_cal * 100 for c in cals)
                    if max_dev < 10:
                        consistent_count += 1
        consistency_rate = consistent_count / num_images * 100 if num_images > 0 else 0
    else:
        consistency_rate = 100.0

    return PromptModelResult(
        prompt_name=prompt_name,
        model_id=model_id,
        runs=runs,
        avg_calorie_mae=avg_mae,
        avg_high_error_rate=avg_high_error,
        calorie_cv=cv,
        consistency_rate=consistency_rate
    )


def save_results(results: List[PromptModelResult], output_dir: Path, timestamp: str):
    """結果を保存"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 詳細JSON保存
    json_path = output_dir / f"batch_eval_{timestamp}.json"
    json_data = []
    for r in results:
        item = {
            "prompt_name": r.prompt_name,
            "model_id": r.model_id,
            "avg_calorie_mae": r.avg_calorie_mae,
            "avg_high_error_rate": r.avg_high_error_rate,
            "calorie_cv": r.calorie_cv,
            "consistency_rate": r.consistency_rate,
            "runs": []
        }
        for run in r.runs:
            run_data = {
                "run_id": run.run_id,
                "timestamp": run.timestamp,
                "success_count": run.success_count,
                "error_count": run.error_count,
                "total_time_seconds": run.total_time_seconds,
                "calorie_stats": asdict(run.calorie_stats),
                "protein_stats": asdict(run.protein_stats),
                "fat_stats": asdict(run.fat_stats),
                "carbs_stats": asdict(run.carbs_stats),
                "image_results": run.image_results
            }
            item["runs"].append(run_data)
        json_data.append(item)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # 2. サマリーMarkdown保存
    md_path = output_dir / f"batch_eval_{timestamp}_summary.md"

    lines = [
        "# プロンプト一括評価結果",
        "",
        f"**実行日時**: {timestamp}",
        "",
        "## サマリー",
        "",
        "| プロンプト | モデル | MAE (Cal) | 30%+誤差率 | CV | 一貫性率 |",
        "|-----------|--------|-----------|-----------|-----|---------|"
    ]

    for r in results:
        model_short = r.model_id.split("/")[-1] if "/" in r.model_id else r.model_id
        lines.append(
            f"| {r.prompt_name} | {model_short} | "
            f"{r.avg_calorie_mae:.1f}% | {r.avg_high_error_rate:.1f}% | "
            f"{r.calorie_cv:.1f}% | {r.consistency_rate:.1f}% |"
        )

    lines.extend(["", "## 詳細結果", ""])

    for r in results:
        model_short = r.model_id.split("/")[-1] if "/" in r.model_id else r.model_id
        lines.extend([
            f"### {r.prompt_name} × {model_short}",
            "",
            "| Run | 成功 | 失敗 | MAE (Cal) | 30%+誤差 | 時間(秒) |",
            "|-----|------|------|-----------|----------|----------|"
        ])
        for run in r.runs:
            lines.append(
                f"| {run.run_id} | {run.success_count} | {run.error_count} | "
                f"{run.calorie_stats.mae:.1f}% | {run.calorie_stats.high_error_count}件 | "
                f"{run.total_time_seconds:.1f} |"
            )
        lines.append("")

    # 高誤差ケース集計
    lines.extend(["## 高誤差ケース (30%以上)", "", "| プロンプト | モデル | 画像 | Label Cal | API Cal | 誤差 |",
                  "|-----------|--------|------|-----------|---------|------|"])

    for r in results:
        model_short = r.model_id.split("/")[-1] if "/" in r.model_id else r.model_id
        for run in r.runs:
            for img in run.image_results:
                if img.get("success") and img.get("cal_error", 0) >= 30:
                    err_sign = "+" if img["api_cal"] > img["label_cal"] else "-"
                    lines.append(
                        f"| {r.prompt_name} | {model_short} | {img['image']} | "
                        f"{img['label_cal']:.0f} | {img['api_cal']:.0f} | "
                        f"{err_sign}{img['cal_error']:.1f}% |"
                    )

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logger.info(f"Results saved: {json_path}")
    logger.info(f"Summary saved: {md_path}")

    return json_path, md_path


async def main():
    parser = argparse.ArgumentParser(description="プロンプト一括評価")
    parser.add_argument("--prompts", nargs="+", help="プロンプトファイルパス（複数可）")
    parser.add_argument("--models", nargs="+", help="モデルID（複数可）")
    parser.add_argument("--runs", type=int, default=3, help="各組み合わせの実行回数")
    parser.add_argument("--api-url", default="http://localhost:8006", help="API URL")
    parser.add_argument("--concurrent", type=int, default=5, help="並行リクエスト数")
    parser.add_argument("--config", help="設定JSONファイル")
    parser.add_argument("--output-dir", default="test_scripts/output", help="出力ディレクトリ")

    args = parser.parse_args()

    # 設定読み込み
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
        prompts = config.get("prompts", [])
        models = config.get("models", [])
        num_runs = config.get("runs", 3)
    else:
        prompts = args.prompts or [
            "apps/freeform_usda_meal_analysis_api/prompts/freeform_prompt_usda_format_ver_v7_production_20251027.txt",
            "apps/freeform_usda_meal_analysis_api/prompts/test_prompt_D_improved.txt",
            "apps/freeform_usda_meal_analysis_api/prompts/test_prompt_E_refined.txt",
            "apps/freeform_usda_meal_analysis_api/prompts/test_prompt_F_hybrid.txt",
        ]
        models = args.models or [
            "openrouter:openai/gpt-5.1",
            "openrouter:google/gemini-3-flash-preview"
        ]
        num_runs = args.runs

    # パス設定
    test_images_dir = project_root / "test_images" / "images"
    labels_dir = project_root / "test_images" / "images_label_with_nutrition"
    output_dir = project_root / args.output_dir

    # 全組み合わせ評価
    total_combos = len(prompts) * len(models)
    logger.info(f"=== Batch Evaluation Start ===")
    logger.info(f"Prompts: {len(prompts)}, Models: {len(models)}, Runs: {num_runs}")
    logger.info(f"Total combinations: {total_combos}, Total runs: {total_combos * num_runs}")

    results = []
    combo_idx = 0

    for prompt_file in prompts:
        prompt_path = project_root / prompt_file if prompt_file else None

        for model_id in models:
            combo_idx += 1
            logger.info(f"\n[{combo_idx}/{total_combos}] Evaluating...")

            result = await evaluate_prompt_model(
                prompt_path, model_id, num_runs,
                args.api_url, args.concurrent,
                test_images_dir, labels_dir
            )
            results.append(result)

            logger.info(f"  → Avg MAE: {result.avg_calorie_mae:.1f}%, "
                       f"30%+: {result.avg_high_error_rate:.1f}%, "
                       f"CV: {result.calorie_cv:.1f}%")

    # 結果保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path, md_path = save_results(results, output_dir, timestamp)

    # 最終サマリー表示
    print("\n" + "="*60)
    print("=== BATCH EVALUATION COMPLETE ===")
    print("="*60)
    print(f"\n{'Prompt':<30} {'Model':<15} {'MAE':>8} {'30%+':>8} {'CV':>8}")
    print("-"*75)

    for r in results:
        model_short = r.model_id.split("/")[-1][:12]
        print(f"{r.prompt_name:<30} {model_short:<15} "
              f"{r.avg_calorie_mae:>7.1f}% {r.avg_high_error_rate:>7.1f}% "
              f"{r.calorie_cv:>7.1f}%")

    print(f"\nResults: {json_path}")
    print(f"Summary: {md_path}")


if __name__ == "__main__":
    asyncio.run(main())
