#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDCA Evaluation Cycle Runner

パイプライン全フェーズを評価し、ボトルネックを特定するPDCAサイクルツール。

フェーズ:
  Phase 1 (VLM): 食材認識・重量推定の品質
  Phase 2 (Matching): USDA検索+Rerankerのマッチ品質
  Phase 3 (Nutrition): エンドツーエンドのカロリー・栄養素精度

Usage:
    python test_scripts/pdca/run_pdca_cycle.py
    python test_scripts/pdca/run_pdca_cycle.py --config test_scripts/pdca/config.yaml
    python test_scripts/pdca/run_pdca_cycle.py --models gemma4-26b --limit 10
"""

import json
import sys
import asyncio
import logging
import argparse
import statistics
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

import aiohttp
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ========== Data Models ==========


@dataclass
class VLMPhaseMetrics:
    """Phase 1: VLM認識品質"""
    total_items: int = 0
    matched_items: int = 0          # ラベルと一致した食材数
    extra_items: int = 0            # ラベルにない食材（ハルシネーション）
    missed_items: int = 0           # VLMが見逃した食材
    food_precision: float = 0.0     # matched / (matched + extra)
    food_recall: float = 0.0        # matched / (matched + missed)
    food_f1: float = 0.0
    weight_errors: List[float] = field(default_factory=list)  # 重量誤差(%)
    weight_mape: float = 0.0
    critical_misidentifications: List[Dict] = field(default_factory=list)


@dataclass
class MatchingPhaseMetrics:
    """Phase 2: USDA検索+Reranker品質"""
    total_queries: int = 0
    correct_matches: int = 0        # 適切なUSDA食品にマッチ
    wrong_matches: int = 0          # 明らかに間違ったマッチ
    acceptable_matches: int = 0     # 類似だが完全一致ではない
    match_accuracy: float = 0.0
    wrong_match_details: List[Dict] = field(default_factory=list)


@dataclass
class NutritionPhaseMetrics:
    """Phase 3: 栄養素精度"""
    calorie_mae: float = 0.0
    calorie_mape: float = 0.0
    protein_mae: float = 0.0
    fat_mae: float = 0.0
    carbs_mae: float = 0.0
    high_error_count: int = 0
    high_error_rate: float = 0.0
    high_error_cases: List[Dict] = field(default_factory=list)
    per_image_errors: List[Dict] = field(default_factory=list)


@dataclass
class PDCACycleResult:
    """1回のPDCAサイクル結果"""
    timestamp: str = ""
    model_id: str = ""
    model_label: str = ""
    prompt_file: str = ""
    prompt_label: str = ""
    success_count: int = 0
    error_count: int = 0
    total_time_seconds: float = 0.0
    vlm: VLMPhaseMetrics = field(default_factory=VLMPhaseMetrics)
    matching: MatchingPhaseMetrics = field(default_factory=MatchingPhaseMetrics)
    nutrition: NutritionPhaseMetrics = field(default_factory=NutritionPhaseMetrics)
    bottleneck: str = ""            # 最大のボトルネックフェーズ
    recommendations: List[str] = field(default_factory=list)


# ========== Label Loading ==========


def load_label(label_path: str) -> Dict:
    """ラベルファイルを読み込み、食材リストと栄養素を返す"""
    with open(label_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    foods = []
    total_cal = 0.0
    total_protein = 0.0
    total_fat = 0.0
    total_carbs = 0.0

    for dish in data.get("dishes", []):
        main_food = dish.get("main_food")
        if main_food:
            nut = main_food.get("nutrition", {})
            foods.append({
                "search_name": main_food["search_name"].lower(),
                "weight_g": main_food.get("weight_g", 0),
                "type": "main_food",
            })
            total_cal += nut.get("calorie", 0) or 0
            total_protein += nut.get("protein_g", 0) or 0
            total_fat += nut.get("fat_g", 0) or 0
            total_carbs += nut.get("carbs_g", 0) or 0

        for extra in dish.get("extras", []):
            nut = extra.get("nutrition", {})
            foods.append({
                "search_name": extra["search_name"].lower(),
                "weight_g": extra.get("weight_g", 0),
                "type": "extra",
            })
            total_cal += nut.get("calorie", 0) or 0
            total_protein += nut.get("protein_g", 0) or 0
            total_fat += nut.get("fat_g", 0) or 0
            total_carbs += nut.get("carbs_g", 0) or 0

    return {
        "foods": foods,
        "total_calorie": total_cal,
        "total_protein_g": total_protein,
        "total_fat_g": total_fat,
        "total_carbs_g": total_carbs,
    }


# ========== API Call ==========


async def call_api(
    session: aiohttp.ClientSession,
    api_url: str,
    image_path: str,
    model_id: str,
    prompt_path: Optional[str],
    use_vlm_cache: bool,
    debug: bool,
    reranker_model: Optional[str] = None,
    reranker_instruction: Optional[str] = None,
    prompt_text: Optional[str] = None,
) -> Dict:
    """APIを呼び出し、全フェーズのデータを取得"""
    endpoint = f"{api_url}/api/v1/meal-analyses/complete"

    with open(image_path, "rb") as f:
        image_data = f.read()

    data = aiohttp.FormData()
    data.add_field("image", image_data, filename=Path(image_path).name, content_type="image/jpeg")
    data.add_field("model_id", model_id)
    data.add_field("use_vlm_cache", str(use_vlm_cache).lower())
    data.add_field("debug", str(debug).lower())

    if prompt_path:
        data.add_field("prompt_path", prompt_path)

    if prompt_text:
        data.add_field("prompt_text", prompt_text)

    if reranker_model:
        data.add_field("reranker_model", reranker_model)

    if reranker_instruction:
        data.add_field("reranker_instruction", reranker_instruction)

    timeout = aiohttp.ClientTimeout(total=300)
    async with session.post(endpoint, data=data, timeout=timeout) as response:
        if response.status != 200:
            error_text = await response.text()
            raise Exception(f"API Error {response.status}: {error_text[:300]}")
        return await response.json()


# ========== Phase Evaluators ==========


def normalize_food_name(name: str) -> str:
    """食材名を正規化してマッチングしやすくする"""
    name = name.lower().strip()
    # USDA修飾子を除去
    for pattern in [
        r"\(includes foods for usda.*?\)",
        r", raw$", r", cooked$", r", fresh$",
        r", boiled.*$", r", grilled.*$", r", roasted.*$",
        r", baked.*$",
    ]:
        name = re.sub(pattern, "", name)
    # カンマ以降を除去（大分類のみ比較）
    parts = name.split(",")
    return parts[0].strip()


def foods_match(label_name: str, api_name: str) -> str:
    """2つの食材名の一致度を判定: exact/partial/wrong"""
    ln = normalize_food_name(label_name)
    an = normalize_food_name(api_name)

    # 完全一致
    if ln == an:
        return "exact"

    # 部分一致（主要単語が含まれる）
    ln_words = set(ln.split())
    an_words = set(an.split())
    overlap = ln_words & an_words
    if overlap and len(overlap) >= max(1, len(ln_words) // 2):
        return "partial"

    # カテゴリレベルマッチ（肉→肉、野菜→野菜 等）
    meat_words = {"beef", "chicken", "pork", "lamb", "steak", "meat", "ham", "prosciutto"}
    veg_words = {"broccoli", "asparagus", "spinach", "lettuce", "cabbage", "kale", "greens", "salad"}
    pasta_words = {"pasta", "penne", "spaghetti", "macaroni", "noodle", "couscous", "rice"}
    potato_words = {"potato", "potatoes", "rosti", "fries"}
    fruit_words = {"tomato", "tomatoes", "avocado", "cucumber", "pepper", "peppers"}

    categories = [meat_words, veg_words, pasta_words, potato_words, fruit_words]
    for cat in categories:
        if (ln_words & cat) and (an_words & cat):
            return "partial"

    return "wrong"


def evaluate_vlm_phase(label: Dict, api_result: Dict) -> Dict:
    """Phase 1: VLMの食材認識・重量推定を評価"""
    label_foods = label["foods"]

    # API結果から食材を抽出
    api_foods = []
    for dish in api_result.get("dishes", []):
        for ing in dish.get("ingredients", []):
            api_foods.append({
                "vlm_query": (ing.get("vlm_query") or "").lower(),
                "matched_name": (ing.get("ingredient_name") or ing.get("matched_db_description") or "").lower(),
                "weight_g": ing.get("weight_g", 0),
            })

    # 食材マッチング（greedy best-match）
    matched = 0
    missed = 0
    weight_errors = []
    details = []
    used_api_indices = set()

    for lf in label_foods:
        best_match = None
        best_score = "wrong"
        best_idx = -1

        for i, af in enumerate(api_foods):
            if i in used_api_indices:
                continue
            vlm_match = foods_match(lf["search_name"], af["vlm_query"])
            if vlm_match == "exact":
                best_match = af
                best_score = "exact"
                best_idx = i
                break
            elif vlm_match == "partial" and best_score != "exact":
                best_match = af
                best_score = "partial"
                best_idx = i

        if best_match and best_score in ("exact", "partial"):
            matched += 1
            used_api_indices.add(best_idx)
            # 重量誤差
            if lf["weight_g"] > 0:
                w_err = abs(best_match["weight_g"] - lf["weight_g"]) / lf["weight_g"] * 100
                weight_errors.append(w_err)
            details.append({
                "label": lf["search_name"],
                "vlm": best_match["vlm_query"],
                "match": best_score,
                "label_weight": lf["weight_g"],
                "vlm_weight": best_match["weight_g"],
            })
        else:
            missed += 1
            details.append({
                "label": lf["search_name"],
                "vlm": None,
                "match": "missed",
            })

    extra = len(api_foods) - len(used_api_indices)

    precision = matched / (matched + extra) if (matched + extra) > 0 else 0
    recall = matched / (matched + missed) if (matched + missed) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "matched": matched,
        "missed": missed,
        "extra": extra,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "weight_errors": weight_errors,
        "details": details,
    }


def evaluate_matching_phase(label: Dict, api_result: Dict) -> Dict:
    """Phase 2: USDA検索+Rerankerの品質を評価"""
    label_foods = label["foods"]
    correct = 0
    wrong = 0
    acceptable = 0
    wrong_details = []

    api_foods = []
    for dish in api_result.get("dishes", []):
        for ing in dish.get("ingredients", []):
            api_foods.append({
                "vlm_query": (ing.get("vlm_query") or "").lower(),
                "matched_name": (ing.get("ingredient_name") or ing.get("matched_db_description") or "").lower(),
                "weight_g": ing.get("weight_g", 0),
            })

    used_indices = set()

    for lf in label_foods:
        # VLMが認識した食材に対応するAPI結果を見つける
        best_idx = -1
        best_vlm_match = "wrong"
        for i, af in enumerate(api_foods):
            if i in used_indices:
                continue
            m = foods_match(lf["search_name"], af["vlm_query"])
            if m in ("exact", "partial"):
                best_idx = i
                best_vlm_match = m
                if m == "exact":
                    break

        if best_idx < 0:
            continue  # VLMが認識しなかった食材はスキップ

        used_indices.add(best_idx)
        af = api_foods[best_idx]

        # VLMクエリ → USDAマッチの品質を評価
        usda_match = foods_match(lf["search_name"], af["matched_name"])
        if usda_match == "exact":
            correct += 1
        elif usda_match == "partial":
            acceptable += 1
        else:
            wrong += 1
            wrong_details.append({
                "label": lf["search_name"],
                "vlm_query": af["vlm_query"],
                "usda_matched": af["matched_name"],
                "issue": "vlm_query→USDA matching failure",
            })

    total = correct + acceptable + wrong
    accuracy = (correct + acceptable) / total if total > 0 else 0

    return {
        "correct": correct,
        "acceptable": acceptable,
        "wrong": wrong,
        "total": total,
        "accuracy": accuracy,
        "wrong_details": wrong_details,
    }


def evaluate_nutrition_phase(label: Dict, api_result: Dict, threshold: float) -> Dict:
    """Phase 3: エンドツーエンドの栄養素精度"""
    # API結果から合計栄養素を計算
    api_cal = 0.0
    api_protein = 0.0
    api_fat = 0.0
    api_carbs = 0.0

    for dish in api_result.get("dishes", []):
        tn = dish.get("total_nutrition", {})
        api_cal += tn.get("calories", 0) or 0
        api_protein += tn.get("protein", 0) or 0
        api_fat += tn.get("fat", 0) or 0
        api_carbs += tn.get("carbs", 0) or 0

    label_cal = label["total_calorie"]
    cal_err_pct = abs(api_cal - label_cal) / label_cal * 100 if label_cal > 0 else 0
    cal_signed_pct = (api_cal - label_cal) / label_cal * 100 if label_cal > 0 else 0

    prot_err = abs(api_protein - label["total_protein_g"]) / label["total_protein_g"] * 100 if label["total_protein_g"] > 0 else 0
    fat_err = abs(api_fat - label["total_fat_g"]) / label["total_fat_g"] * 100 if label["total_fat_g"] > 0 else 0
    carbs_err = abs(api_carbs - label["total_carbs_g"]) / label["total_carbs_g"] * 100 if label["total_carbs_g"] > 0 else 0

    return {
        "calorie_error_pct": cal_err_pct,
        "calorie_signed_pct": cal_signed_pct,
        "protein_error_pct": prot_err,
        "fat_error_pct": fat_err,
        "carbs_error_pct": carbs_err,
        "label_cal": label_cal,
        "api_cal": api_cal,
        "is_high_error": cal_err_pct >= threshold,
    }


# ========== Bottleneck Analysis ==========


def identify_bottleneck(vlm: VLMPhaseMetrics, matching: MatchingPhaseMetrics, nutrition: NutritionPhaseMetrics) -> tuple:
    """ボトルネックフェーズとレコメンデーションを特定"""
    bottleneck = ""
    recommendations = []

    # スコア計算（0-100、低いほど問題）
    vlm_score = vlm.food_f1 * 100
    match_score = matching.match_accuracy * 100
    nut_score = max(0, 100 - nutrition.calorie_mae)

    scores = {
        "vlm": vlm_score,
        "matching": match_score,
        "nutrition": nut_score,
    }

    bottleneck = min(scores, key=scores.get)

    if vlm_score < 70:
        recommendations.append(f"[VLM] 食材認識F1が{vlm.food_f1:.2f}と低い。プロンプトのDETECTION PRIORITYセクション強化を検討")
    if vlm.weight_mape > 30:
        recommendations.append(f"[VLM] 重量推定MAPE {vlm.weight_mape:.1f}%。PORTION ANCHORSの調整を検討")
    if vlm.critical_misidentifications:
        recommendations.append(f"[VLM] {len(vlm.critical_misidentifications)}件のクリティカル誤認識あり。VLMモデル変更またはプロンプト改良が必要")

    if matching.wrong_matches > 3:
        recommendations.append(f"[Matching] {matching.wrong_matches}件のUSDA誤マッチ。Rerankerモデルの上位互換(4B→8B)または食品ドメインembeddingの検討")
    if matching.match_accuracy < 0.7:
        recommendations.append(f"[Matching] マッチ精度{matching.match_accuracy:.1%}。BM25/Vectorの重み調整やUSDAインデックス拡充を検討")

    if nutrition.calorie_mae > 20:
        recommendations.append(f"[Nutrition] カロリーMAE {nutrition.calorie_mae:.1f}%。高誤差ケースの共通パターンを分析し、プロンプトに反映")
    if nutrition.high_error_rate > 15:
        recommendations.append(f"[Nutrition] 30%以上誤差率{nutrition.high_error_rate:.1f}%。外れ値ケースの根本原因分析が必要")

    if not recommendations:
        recommendations.append("全フェーズが目標値を達成。次のPDCAサイクルでは目標値の引き上げを検討")

    return bottleneck, recommendations


# ========== Main Pipeline ==========


async def evaluate_single_image(
    session: aiohttp.ClientSession,
    api_url: str,
    model_id: str,
    prompt_path: Optional[str],
    image_idx: int,
    config: Dict,
    semaphore: asyncio.Semaphore,
    reranker_model: Optional[str] = None,
    reranker_instruction: Optional[str] = None,
    prompt_text: Optional[str] = None,
) -> Optional[Dict]:
    """1画像のフェーズ別評価"""
    async with semaphore:
        image_path = PROJECT_ROOT / f"test_images/images/test_food{image_idx}.jpg"
        label_path = PROJECT_ROOT / f"test_images/images_label_with_nutrition/test_food{image_idx:02d}.json"

        if not image_path.exists() or not label_path.exists():
            return None

        try:
            label = load_label(str(label_path))
            api_result = await call_api(
                session, api_url, str(image_path),
                model_id, prompt_path,
                config["evaluation"]["use_vlm_cache"],
                config["evaluation"]["debug"],
                reranker_model=reranker_model,
                reranker_instruction=reranker_instruction,
                prompt_text=prompt_text,
            )

            threshold = config["evaluation"]["calorie_high_error_threshold"]

            vlm_eval = evaluate_vlm_phase(label, api_result)
            matching_eval = evaluate_matching_phase(label, api_result)
            nutrition_eval = evaluate_nutrition_phase(label, api_result, threshold)

            logger.info(
                f"[{image_idx:02d}] Cal:{nutrition_eval['label_cal']:.0f}→{nutrition_eval['api_cal']:.0f} "
                f"({nutrition_eval['calorie_signed_pct']:+.1f}%) | "
                f"VLM F1:{vlm_eval['f1']:.2f} | Match:{matching_eval['accuracy']:.2f}"
            )

            return {
                "image_idx": image_idx,
                "image_name": f"test_food{image_idx}.jpg",
                "success": True,
                "vlm": vlm_eval,
                "matching": matching_eval,
                "nutrition": nutrition_eval,
                "api_result": api_result,
            }

        except Exception as e:
            logger.error(f"[{image_idx:02d}] Error: {e}")
            return {
                "image_idx": image_idx,
                "image_name": f"test_food{image_idx}.jpg",
                "success": False,
                "error": str(e),
            }


async def run_pdca_cycle(
    model_label: str,
    model_id: str,
    prompt_label: str,
    prompt_file: Optional[str],
    config: Dict,
    limit: int,
    reranker_model: Optional[str] = None,
    reranker_instruction: Optional[str] = None,
    prompt_text: Optional[str] = None,
) -> PDCACycleResult:
    """1モデル×1プロンプトのPDCAサイクル実行"""
    import time
    start = time.time()

    logger.info(f"\n{'='*60}")
    logger.info(f"PDCA Cycle: {model_label} × {prompt_label}")
    if reranker_model:
        logger.info(f"Reranker: {reranker_model}")
    logger.info(f"{'='*60}")

    api_url = config["api"]["url"]
    concurrent = config["api"]["concurrent"]
    semaphore = asyncio.Semaphore(concurrent)

    async with aiohttp.ClientSession() as session:
        tasks = [
            evaluate_single_image(session, api_url, model_id, prompt_file, i, config, semaphore,
                                  reranker_model=reranker_model,
                                  reranker_instruction=reranker_instruction,
                                  prompt_text=prompt_text)
            for i in range(1, limit + 1)
        ]
        results = await asyncio.gather(*tasks)

    success_results = [r for r in results if r and r.get("success")]
    error_results = [r for r in results if r and not r.get("success")]

    # Phase 1: VLM集計
    all_matched = sum(r["vlm"]["matched"] for r in success_results)
    all_missed = sum(r["vlm"]["missed"] for r in success_results)
    all_extra = sum(r["vlm"]["extra"] for r in success_results)
    all_weight_errors = []
    all_critical = []
    for r in success_results:
        all_weight_errors.extend(r["vlm"]["weight_errors"])
        for d in r["vlm"]["details"]:
            if d["match"] == "missed":
                all_critical.append({"image": r["image_name"], **d})

    vlm_precision = all_matched / (all_matched + all_extra) if (all_matched + all_extra) > 0 else 0
    vlm_recall = all_matched / (all_matched + all_missed) if (all_matched + all_missed) > 0 else 0
    vlm_f1 = 2 * vlm_precision * vlm_recall / (vlm_precision + vlm_recall) if (vlm_precision + vlm_recall) > 0 else 0

    vlm_metrics = VLMPhaseMetrics(
        total_items=all_matched + all_missed,
        matched_items=all_matched,
        extra_items=all_extra,
        missed_items=all_missed,
        food_precision=vlm_precision,
        food_recall=vlm_recall,
        food_f1=vlm_f1,
        weight_errors=all_weight_errors,
        weight_mape=statistics.mean(all_weight_errors) if all_weight_errors else 0,
        critical_misidentifications=all_critical[:10],
    )

    # Phase 2: Matching集計
    total_correct = sum(r["matching"]["correct"] for r in success_results)
    total_acceptable = sum(r["matching"]["acceptable"] for r in success_results)
    total_wrong = sum(r["matching"]["wrong"] for r in success_results)
    total_queries = total_correct + total_acceptable + total_wrong
    all_wrong_details = []
    for r in success_results:
        for d in r["matching"]["wrong_details"]:
            all_wrong_details.append({"image": r["image_name"], **d})

    matching_metrics = MatchingPhaseMetrics(
        total_queries=total_queries,
        correct_matches=total_correct,
        wrong_matches=total_wrong,
        acceptable_matches=total_acceptable,
        match_accuracy=(total_correct + total_acceptable) / total_queries if total_queries > 0 else 0,
        wrong_match_details=all_wrong_details[:20],
    )

    # Phase 3: Nutrition集計
    cal_errors = [r["nutrition"]["calorie_error_pct"] for r in success_results]
    prot_errors = [r["nutrition"]["protein_error_pct"] for r in success_results]
    fat_errors = [r["nutrition"]["fat_error_pct"] for r in success_results]
    carbs_errors = [r["nutrition"]["carbs_error_pct"] for r in success_results]
    high_error_cases = [
        {"image": r["image_name"], **r["nutrition"]}
        for r in success_results if r["nutrition"]["is_high_error"]
    ]

    nutrition_metrics = NutritionPhaseMetrics(
        calorie_mae=statistics.mean(cal_errors) if cal_errors else 0,
        calorie_mape=statistics.mean(cal_errors) if cal_errors else 0,
        protein_mae=statistics.mean(prot_errors) if prot_errors else 0,
        fat_mae=statistics.mean(fat_errors) if fat_errors else 0,
        carbs_mae=statistics.mean(carbs_errors) if carbs_errors else 0,
        high_error_count=len(high_error_cases),
        high_error_rate=len(high_error_cases) / len(success_results) * 100 if success_results else 0,
        high_error_cases=sorted(high_error_cases, key=lambda x: x["calorie_error_pct"], reverse=True)[:10],
    )

    # Bottleneck分析
    bottleneck, recommendations = identify_bottleneck(vlm_metrics, matching_metrics, nutrition_metrics)

    elapsed = time.time() - start

    return PDCACycleResult(
        timestamp=datetime.now().isoformat(),
        model_id=model_id,
        model_label=model_label,
        prompt_file=prompt_file or "default",
        prompt_label=prompt_label,
        success_count=len(success_results),
        error_count=len(error_results),
        total_time_seconds=elapsed,
        vlm=vlm_metrics,
        matching=matching_metrics,
        nutrition=nutrition_metrics,
        bottleneck=bottleneck,
        recommendations=recommendations,
    )


# ========== Report Generation ==========


def generate_report(results: List[PDCACycleResult], config: Dict, output_dir: Path) -> Path:
    """PDCAレポート（Markdown）を生成"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = output_dir / f"pdca_report_{timestamp}.md"

    targets = config.get("targets", {})

    lines = [
        "# PDCA Evaluation Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Images**: {config['dataset']['num_images']}",
        f"**Cache**: {'disabled' if not config['evaluation']['use_vlm_cache'] else 'enabled'}",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Model | Prompt | VLM F1 | Match Acc | Cal MAE | 30%+ Err | Bottleneck |",
        "|-------|--------|--------|-----------|---------|----------|------------|",
    ]

    for r in results:
        lines.append(
            f"| {r.model_label} | {r.prompt_label} | "
            f"{r.vlm.food_f1:.2f} | {r.matching.match_accuracy:.1%} | "
            f"{r.nutrition.calorie_mae:.1f}% | {r.nutrition.high_error_count}件 ({r.nutrition.high_error_rate:.1f}%) | "
            f"**{r.bottleneck}** |"
        )

    lines.extend(["", "---", ""])

    # フェーズ別詳細
    for r in results:
        lines.extend([
            f"## {r.model_label} x {r.prompt_label}",
            "",
            f"Success: {r.success_count}/{r.success_count + r.error_count} | "
            f"Time: {r.total_time_seconds:.0f}s",
            "",
            "### Phase 1: VLM Recognition",
            "",
            f"| Metric | Value | Target |",
            f"|--------|-------|--------|",
            f"| Food Precision | {r.vlm.food_precision:.2f} | - |",
            f"| Food Recall | {r.vlm.food_recall:.2f} | - |",
            f"| **Food F1** | **{r.vlm.food_f1:.2f}** | {targets.get('vlm', {}).get('food_recognition_f1', '-')} |",
            f"| Weight MAPE | {r.vlm.weight_mape:.1f}% | {targets.get('vlm', {}).get('weight_mape', '-')}% |",
            f"| Matched/Missed/Extra | {r.vlm.matched_items}/{r.vlm.missed_items}/{r.vlm.extra_items} | - |",
            "",
            "### Phase 2: USDA Matching",
            "",
            f"| Metric | Value | Target |",
            f"|--------|-------|--------|",
            f"| **Match Accuracy** | **{r.matching.match_accuracy:.1%}** | {targets.get('matching', {}).get('usda_match_accuracy', '-')} |",
            f"| Correct/Acceptable/Wrong | {r.matching.correct_matches}/{r.matching.acceptable_matches}/{r.matching.wrong_matches} | - |",
            "",
        ])

        if r.matching.wrong_match_details:
            lines.extend([
                "**Wrong Matches (Top 10):**",
                "",
                "| Image | Label | VLM Query | USDA Matched |",
                "|-------|-------|-----------|-------------|",
            ])
            for d in r.matching.wrong_match_details[:10]:
                lines.append(f"| {d.get('image', '')} | {d['label']} | {d['vlm_query']} | {d['usda_matched']} |")
            lines.append("")

        lines.extend([
            "### Phase 3: Nutrition Accuracy",
            "",
            f"| Metric | Value | Target |",
            f"|--------|-------|--------|",
            f"| **Calorie MAE** | **{r.nutrition.calorie_mae:.1f}%** | {targets.get('nutrition', {}).get('calorie_mae', '-')}% |",
            f"| Protein MAE | {r.nutrition.protein_mae:.1f}% | - |",
            f"| Fat MAE | {r.nutrition.fat_mae:.1f}% | - |",
            f"| Carbs MAE | {r.nutrition.carbs_mae:.1f}% | - |",
            f"| **30%+ Error Rate** | **{r.nutrition.high_error_rate:.1f}%** ({r.nutrition.high_error_count}件) | {targets.get('nutrition', {}).get('high_error_rate', '-')}% |",
            "",
        ])

        if r.nutrition.high_error_cases:
            lines.extend([
                "**High Error Cases (Top 10):**",
                "",
                "| Image | Label Cal | API Cal | Error |",
                "|-------|-----------|---------|-------|",
            ])
            for c in r.nutrition.high_error_cases[:10]:
                lines.append(f"| {c.get('image', '')} | {c['label_cal']:.0f} | {c['api_cal']:.0f} | {c['calorie_signed_pct']:+.1f}% |")
            lines.append("")

        # Recommendations
        lines.extend([
            f"### Bottleneck: **{r.bottleneck.upper()}**",
            "",
            "**Recommendations:**",
            "",
        ])
        for rec in r.recommendations:
            lines.append(f"- {rec}")
        lines.extend(["", "---", ""])

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return md_path


def save_json(results: List[PDCACycleResult], output_dir: Path) -> Path:
    """詳細結果をJSON保存"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"pdca_results_{timestamp}.json"

    data = []
    for r in results:
        d = {
            "timestamp": r.timestamp,
            "model_id": r.model_id,
            "model_label": r.model_label,
            "prompt_file": r.prompt_file,
            "prompt_label": r.prompt_label,
            "success_count": r.success_count,
            "error_count": r.error_count,
            "total_time_seconds": r.total_time_seconds,
            "bottleneck": r.bottleneck,
            "recommendations": r.recommendations,
            "vlm": {
                "food_f1": r.vlm.food_f1,
                "food_precision": r.vlm.food_precision,
                "food_recall": r.vlm.food_recall,
                "weight_mape": r.vlm.weight_mape,
                "matched": r.vlm.matched_items,
                "missed": r.vlm.missed_items,
                "extra": r.vlm.extra_items,
            },
            "matching": {
                "accuracy": r.matching.match_accuracy,
                "correct": r.matching.correct_matches,
                "acceptable": r.matching.acceptable_matches,
                "wrong": r.matching.wrong_matches,
                "wrong_details": r.matching.wrong_match_details,
            },
            "nutrition": {
                "calorie_mae": r.nutrition.calorie_mae,
                "protein_mae": r.nutrition.protein_mae,
                "fat_mae": r.nutrition.fat_mae,
                "carbs_mae": r.nutrition.carbs_mae,
                "high_error_rate": r.nutrition.high_error_rate,
                "high_error_count": r.nutrition.high_error_count,
                "high_error_cases": r.nutrition.high_error_cases,
            },
        }
        data.append(d)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return json_path


# ========== CLI ==========


async def main():
    parser = argparse.ArgumentParser(description="PDCA Evaluation Cycle Runner")
    parser.add_argument("--config", default="test_scripts/pdca/config.yaml", help="設定ファイル")
    parser.add_argument("--models", nargs="+", help="評価するモデル（config内のキー名）")
    parser.add_argument("--prompts", nargs="+", help="評価するプロンプト（config内のキー名）")
    parser.add_argument("--limit", type=int, help="画像数を制限")
    parser.add_argument("--output-dir", default="test_scripts/pdca/output", help="出力ディレクトリ")
    args = parser.parse_args()

    config_path = PROJECT_ROOT / args.config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    limit = args.limit or config["dataset"]["num_images"]
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # 対象モデル・プロンプトを決定
    models = {}
    if args.models:
        for m in args.models:
            if m in config["models"]:
                models[m] = config["models"][m]
            else:
                logger.error(f"Unknown model: {m}. Available: {list(config['models'].keys())}")
                sys.exit(1)
    else:
        models = config["models"]

    prompts = {}
    if args.prompts:
        for p in args.prompts:
            if p in config["prompts"]:
                prompts[p] = config["prompts"][p]
            else:
                logger.error(f"Unknown prompt: {p}. Available: {list(config['prompts'].keys())}")
                sys.exit(1)
    else:
        prompts = config["prompts"]

    # Reranker設定
    reranker_cfg = config.get("reranker", {})
    reranker_model = reranker_cfg.get("model")
    reranker_instruction = reranker_cfg.get("instruction")

    # 全組み合わせ実行
    all_results = []
    total = len(models) * len(prompts)
    idx = 0

    for model_label, model_cfg in models.items():
        for prompt_label, prompt_cfg in prompts.items():
            idx += 1
            logger.info(f"\n[{idx}/{total}] {model_label} x {prompt_label}")

            result = await run_pdca_cycle(
                model_label=model_label,
                model_id=model_cfg["model_id"],
                prompt_label=prompt_label,
                prompt_file=prompt_cfg.get("file"),
                config=config,
                limit=limit,
                reranker_model=reranker_model,
                reranker_instruction=reranker_instruction,
            )
            all_results.append(result)

    # レポート生成
    md_path = generate_report(all_results, config, output_dir)
    json_path = save_json(all_results, output_dir)

    # サマリー表示
    print(f"\n{'='*60}")
    print("PDCA CYCLE COMPLETE")
    print(f"{'='*60}")
    print(f"\n{'Model':<20} {'Prompt':<12} {'VLM F1':>8} {'Match':>8} {'Cal MAE':>8} {'30%+':>6} {'Bottleneck':<12}")
    print("-" * 80)
    for r in all_results:
        print(
            f"{r.model_label:<20} {r.prompt_label:<12} "
            f"{r.vlm.food_f1:>7.2f} {r.matching.match_accuracy:>7.1%} "
            f"{r.nutrition.calorie_mae:>7.1f}% {r.nutrition.high_error_count:>5} {r.bottleneck:<12}"
        )
    print(f"\nReport: {md_path}")
    print(f"JSON:   {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
