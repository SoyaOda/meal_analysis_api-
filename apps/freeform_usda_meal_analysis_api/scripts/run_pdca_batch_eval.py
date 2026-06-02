#!/usr/bin/env python3
"""Run reproducible PDCA batch eval for prompt/model candidates."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import random
import re
import statistics
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_IMAGES_DIR = PROJECT_ROOT / "test_images" / "images"
DEFAULT_LABELS_DIR = PROJECT_ROOT / "test_images" / "images_label_with_nutrition"
DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT / "apps" / "freeform_usda_meal_analysis_api" / "evals" / "runs"
)
DEFAULT_PROMPTS_DIR = (
    PROJECT_ROOT / "apps" / "freeform_usda_meal_analysis_api" / "prompts"
)

LEAKAGE_PATTERNS = {
    "test_image_id": re.compile(r"\btest_food\d+\b", re.IGNORECASE),
    "label_directory": re.compile(r"images_label_with_nutrition", re.IGNORECASE),
    "ground_truth_word": re.compile(r"\bground\s*truth\b", re.IGNORECASE),
    "label_answer_hint": re.compile(r"\b(label|answer)\s*calor", re.IGNORECASE),
}
RETRYABLE_STATUS_CODES = {0, 429, 500, 502, 503, 504}
# Paired BCa bootstrap defaults (deterministic given seed) for the promote gate.
DEFAULT_BOOTSTRAP_RESAMPLES = 10000
DEFAULT_BOOTSTRAP_SEED = 12345
SEARCH_OVERRIDE_KEYS = [
    "stage1_top_k",
    "bm25_weight",
    "vector_weight",
    "rrf_k",
    "rrf_weight",
    "reranker_model",
    "reranker_instruction",
    "reranker_top_n",
]


@dataclass
class CandidateSummary:
    name: str
    vlm_model_id: str
    prompt_path: Optional[str]
    calorie_mae_percent: float
    calorie_p50_percent: float
    calorie_p90_percent: float
    high_error_rate_30_percent: float
    avg_latency_sec: float
    avg_cost_usd: Optional[float]
    total_cost_usd: float
    success_count: int
    failure_count: int
    cache_hit_rate_percent: float
    evaluated_image_count: int
    expected_image_count: int
    coverage_complete: bool
    all_success: bool


@dataclass
class ImageSetBuildResult:
    items: List[Dict[str, Path]]
    requested_indices: List[int]
    present_indices: List[int]
    missing_indices: List[int]


def safe_percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * p
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return ordered[lower]
    frac = rank - lower
    return ordered[lower] * (1 - frac) + ordered[upper] * frac


def _mean(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


def bootstrap_mean_ci(
    values: List[float],
    *,
    n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    alpha: float = 0.05,
    seed: int = DEFAULT_BOOTSTRAP_SEED,
) -> Optional[Dict[str, Any]]:
    """BCa (bias-corrected and accelerated) bootstrap CI for the mean of `values`.

    Used for (a) a single run's MAE uncertainty and (b) paired per-image error
    deltas (candidate - baseline). Deterministic given `seed`. Returns None when
    there is no data; collapses to the point estimate for degenerate samples.
    """
    n = len(values)
    if n == 0:
        return None
    point = _mean(values)
    if n < 3 or all(v == values[0] for v in values):
        return {
            "point": round(point, 4),
            "ci_low": round(point, 4),
            "ci_high": round(point, 4),
            "n": n,
            "n_resamples": 0,
            "alpha": alpha,
            "method": "degenerate",
        }

    rng = random.Random(seed)
    boot_means: List[float] = []
    for _ in range(n_resamples):
        total = 0.0
        for _ in range(n):
            total += values[rng.randrange(n)]
        boot_means.append(total / n)
    boot_means.sort()

    normal = statistics.NormalDist()
    # Bias-correction factor z0 (clamped away from 0/1 to keep inv_cdf finite).
    below = sum(1 for b in boot_means if b < point)
    prop = below / n_resamples
    prop = min(max(prop, 1.0 / (n_resamples + 1)), n_resamples / (n_resamples + 1))
    z0 = normal.inv_cdf(prop)

    # Acceleration factor via jackknife of the mean.
    total_sum = sum(values)
    jack = [(total_sum - v) / (n - 1) for v in values]
    jack_mean = _mean(jack)
    diffs = [jack_mean - j for j in jack]
    num = sum(d**3 for d in diffs)
    den = 6.0 * (sum(d**2 for d in diffs) ** 1.5)
    accel = num / den if den != 0 else 0.0

    z_lo = normal.inv_cdf(alpha / 2.0)
    z_hi = normal.inv_cdf(1.0 - alpha / 2.0)

    def adjusted(z: float) -> float:
        denom = 1.0 - accel * (z0 + z)
        if denom == 0.0:
            denom = 1e-12
        prob = normal.cdf(z0 + (z0 + z) / denom)
        return min(max(prob, 0.0), 1.0)

    ci_low = safe_percentile(boot_means, adjusted(z_lo))
    ci_high = safe_percentile(boot_means, adjusted(z_hi))
    return {
        "point": round(point, 4),
        "ci_low": round(ci_low, 4),
        "ci_high": round(ci_high, 4),
        "n": n,
        "n_resamples": n_resamples,
        "alpha": alpha,
        "method": "bca",
    }


def sign_flip_pvalue(
    deltas: List[float],
    *,
    n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    seed: int = DEFAULT_BOOTSTRAP_SEED + 1,
) -> Optional[float]:
    """Two-sided sign-flip permutation p-value for H0: mean paired delta == 0."""
    n = len(deltas)
    if n == 0:
        return None
    observed = abs(_mean(deltas))
    rng = random.Random(seed)
    count = 0
    for _ in range(n_resamples):
        total = 0.0
        for d in deltas:
            total += d if rng.random() < 0.5 else -d
        if abs(total / n) >= observed - 1e-12:
            count += 1
    return round((count + 1) / (n_resamples + 1), 5)


def paired_calorie_deltas(
    candidate_rows: List[Dict[str, Any]],
    baseline_rows: List[Dict[str, Any]],
) -> tuple[List[float], List[str]]:
    """Per-image (candidate - baseline) calorie abs %-error deltas on shared successes.

    Pairing by image cancels per-image difficulty variance, which is the dominant
    noise source; only images where BOTH candidate and baseline succeeded are used.
    """
    base_err: Dict[str, float] = {
        r["image"]: float(r["calorie_abs_percent_error"])
        for r in baseline_rows
        if r.get("success") and r.get("calorie_abs_percent_error") is not None
    }
    deltas: List[float] = []
    images: List[str] = []
    for r in candidate_rows:
        if (
            r.get("success")
            and r.get("calorie_abs_percent_error") is not None
            and r["image"] in base_err
        ):
            deltas.append(float(r["calorie_abs_percent_error"]) - base_err[r["image"]])
            images.append(r["image"])
    return deltas, images


def compute_decomposed_metrics(success_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Diagnostic decomposition of total-calorie error from already-stored data.

    Uses each row's `label` and `prediction` totals (calories + macros). Reveals
    WHERE error comes from that abs-MAE hides: directional bias (over/under),
    calibration slope (do predictions flatten as the true meal grows), absolute
    kcal scale, and per-macro error. No extra API calls.
    """
    signed: List[float] = []
    abs_kcal: List[float] = []
    pairs: List[tuple] = []  # (label_cal, pred_cal)
    macro_errs: Dict[str, List[float]] = {"protein": [], "fat": [], "carbs": []}

    for r in success_rows:
        label = r.get("label") or {}
        pred = r.get("prediction") or {}
        lc = float(label.get("calories", 0) or 0)
        pc = float(pred.get("calories", 0) or 0)
        if lc > 0:
            signed.append((pc - lc) / lc * 100.0)
            abs_kcal.append(abs(pc - lc))
            pairs.append((lc, pc))
        for macro in macro_errs:
            lv = float(label.get(macro, 0) or 0)
            pv = float(pred.get(macro, 0) or 0)
            if lv > 0:
                macro_errs[macro].append(abs(pv - lv) / lv * 100.0)

    out: Dict[str, Any] = {
        "signed_mean_error_percent": round(_mean(signed), 4) if signed else None,
        "signed_median_error_percent": (
            round(safe_percentile(signed, 0.5), 4) if signed else None
        ),
        "abs_kcal_mae": round(_mean(abs_kcal), 4) if abs_kcal else None,
        "macro_mae_percent": {
            macro: (round(_mean(vals), 4) if vals else None)
            for macro, vals in macro_errs.items()
        },
        "n": len(pairs),
    }

    # Calibration: least-squares regression of predicted on true calories.
    if len(pairs) >= 2:
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        mx = _mean(xs)
        my = _mean(ys)
        sxx = sum((x - mx) ** 2 for x in xs)
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        slope = sxy / sxx if sxx else 0.0
        intercept = my - slope * mx
        ss_tot = sum((y - my) ** 2 for y in ys)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
        r2 = 1.0 - ss_res / ss_tot if ss_tot else 0.0
        out["calibration_slope"] = round(slope, 4)
        out["calibration_intercept"] = round(intercept, 4)
        out["calibration_r2"] = round(r2, 4)

        # Robust slope: OLS slope is attenuated by noise in the true calories
        # (errors-in-variables) AND model over-dispersion, so it OVERSTATES
        # calibration quality. Theil-Sen (median of pairwise slopes) is parameter-free
        # and reliable here. Deming/orthogonal regression is intentionally NOT used:
        # it needs a known x/y error-variance ratio, and with our noisy low-R^2 data a
        # delta=1 orthogonal slope blows up (measured ~1.5) and would mislead.
        try:
            from scipy.stats import theilslopes

            ts_slope, ts_intercept, _lo, _hi = theilslopes(ys, xs)
            out["theil_sen_slope"] = round(float(ts_slope), 4)
            out["theil_sen_intercept"] = round(float(ts_intercept), 4)
        except Exception:
            pass
    return out


# Food-name qualifier tokens that should not drive matching (USDA descriptions are
# verbose: "Chicken, broilers or fryers, breast, meat only, cooked, roasted").
_FOOD_STOPWORDS = {
    "raw",
    "cooked",
    "fresh",
    "prepared",
    "style",
    "home",
    "recipe",
    "ns",
    "with",
    "without",
    "and",
    "or",
    "the",
    "of",
    "in",
    "meat",
    "only",
    "fryers",
    "broilers",
    "type",
    "added",
    "fat",
    "made",
    "from",
    "includes",
    "all",
    "types",
    "cuts",
    "nfs",
}


def _food_tokens(s: Optional[str]) -> set:
    tokens = re.split(r"[^a-z0-9]+", (s or "").lower())
    return {t for t in tokens if len(t) > 2 and t not in _FOOD_STOPWORDS}


def _token_overlap(a: Optional[str], b: Optional[str]) -> float:
    """Overlap coefficient on content tokens (robust to USDA verbosity & word order)."""
    ta, tb = _food_tokens(a), _food_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def _name_similarity(a: Optional[str], b: Optional[str]) -> float:
    """Dependency-free name similarity: max(char-LCS ratio, content-token overlap).

    The token-overlap term is what makes USDA-style verbose names match short GT names
    (the old char-only difflib gave F1~0.07). An embedding backend can replace this via
    the `similarity_fn` arg of dish_match_metrics (recommended upgrade; needs a dep)."""
    import difflib

    lcs = difflib.SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()
    return max(lcs, _token_overlap(a, b))


def load_label_items(label_path: Path) -> List[Dict[str, Any]]:
    """Flatten GT dishes -> per-item list [{name, weight_g, calories}] for dish-matching."""
    data = json.loads(label_path.read_text(encoding="utf-8"))
    items: List[Dict[str, Any]] = []
    for dish in data.get("dishes", []):
        for source_key in ("main_food", "extras"):
            entries = dish.get(source_key)
            if entries is None:
                continue
            for entry in entries if isinstance(entries, list) else [entries]:
                if not entry:
                    continue
                n = entry.get("nutrition") or {}
                items.append(
                    {
                        "name": entry.get("search_name"),
                        "weight_g": entry.get("weight_g"),
                        "calories": float(n.get("calorie", 0) or 0),
                    }
                )
    return items


def extract_pred_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Reduced per-ingredient view of a prediction for dish-matching (PART A capture)."""
    items: List[Dict[str, Any]] = []
    for dish in payload.get("dishes") or []:
        for ing in dish.get("ingredients") or []:
            calc = ing.get("calculated_nutrition")
            calories = None
            if isinstance(calc, dict):
                calories = calc.get("calories")
            items.append(
                {
                    "name": ing.get("ingredient_name"),
                    "matched_desc": ing.get("matched_db_description"),
                    "fdc_id": ing.get("fdc_id"),
                    "weight_g": ing.get("weight_g"),
                    "calories": calories,
                }
            )
    return items


def _default_pred_gt_similarity(p: Dict[str, Any], g: Dict[str, Any]) -> float:
    """Similarity of a predicted item to a GT item using BOTH the predicted name and
    the matched USDA description (the verbose matched_desc is often what aligns with
    the short GT search_name)."""
    gname = g.get("name")
    return max(
        _name_similarity(p.get("name"), gname),
        _name_similarity(p.get("matched_desc"), gname),
    )


def _cosine(a: List[float], b: List[float]) -> float:
    import numpy as _np

    av = _np.asarray(a, dtype=float)
    bv = _np.asarray(b, dtype=float)
    na = float(_np.linalg.norm(av))
    nb = float(_np.linalg.norm(bv))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(av @ bv / (na * nb))


class EmbeddingSimilarity:
    """Pluggable pred-vs-GT similarity for dish_match_metrics using sentence embeddings.

    Closes the semantic gaps the dependency-free token/char matcher misses (e.g. GT
    'cucumber' vs predicted 'green salad with cucumber slices', where char/token overlap
    falls under the 0.75 threshold and the item drops to an unmatched 0). `embed_fn(texts)
    -> list[vector]` is injected (default: the app's EmbeddingProviderFactory / Qwen3-
    Embedding-8B — NO new dependency). Call warm(texts) once to batch-embed, then use the
    instance AS the similarity_fn. Similarity = max(cos(pred.name, gt.name),
    cos(pred.matched_desc, gt.name)).
    """

    def __init__(self, embed_fn) -> None:
        self._embed = embed_fn
        self._cache: Dict[str, List[float]] = {}

    def warm(self, texts: List[str]) -> None:
        miss = sorted({t for t in texts if t and t not in self._cache})
        if not miss:
            return
        vecs = self._embed(miss)
        if len(vecs) != len(miss):
            raise RuntimeError(
                f"embed_fn returned {len(vecs)} vectors for {len(miss)} texts"
            )
        for t, v in zip(miss, vecs):
            self._cache[t] = v

    def __call__(self, p: Dict[str, Any], g: Dict[str, Any]) -> float:
        gv = self._cache.get(g.get("name"))
        if gv is None:
            return 0.0
        best = 0.0
        for key in ("name", "matched_desc"):
            pv = self._cache.get(p.get(key))
            if pv is not None:
                best = max(best, _cosine(pv, gv))
        return best


def build_embedding_fn(provider_name: Optional[str] = None):
    """Sync embed_fn backed by the app's existing embedding provider (no new dependency).

    Reuses EmbeddingProviderFactory (env EMBEDDING_PROVIDER, default 'deepinfra' /
    Qwen3-Embedding-8B). Safe to call from sync scripts (wraps the async provider in
    asyncio.run). Names are embedded WITHOUT an instruction so pred and GT are symmetric.
    """
    import asyncio

    from apps.freeform_usda_meal_analysis_api.services.embedding_providers import (
        EmbeddingProviderFactory,
    )

    provider = EmbeddingProviderFactory.create(provider_name)

    def _embed(texts: List[str]) -> List[List[float]]:
        return asyncio.run(provider.generate_embeddings(texts))

    return _embed


# Plausible food energy-density range (kcal per gram); pure fat ~9, water/leafy ~0.1.
_KCAL_PER_G_MIN = 0.1
_KCAL_PER_G_MAX = 9.0


def portion_score_from_bands(
    portion_bands: Dict[str, float], matched: int
) -> Optional[int]:
    """Deterministic 0-5 portion_plausibility score from the matched-item weight bands.

    This is the reproducible (zero run-variance) replacement for an LLM judge's portion
    score; see lesson 20260602_rubric_v3_portion_should_be_deterministic.md. f25 = fraction
    of matched items within 25% of GT weight, f10 = fraction within 10%. Returns None when
    no matched item carried a comparable weight (banded == 0), so callers can distinguish
    "no portion signal" from a real 0.
    """
    if not matched:
        return 0
    f10 = float(portion_bands.get("within_10", 0.0))
    f25 = f10 + float(portion_bands.get("within_25", 0.0))
    if f25 == 0.0 and float(portion_bands.get("gross", 0.0)) == 0.0:
        return None
    if f25 >= 0.999 and f10 >= 0.5:
        return 5
    if f25 >= 0.75:
        return 4
    if f25 >= 0.50:
        return 3
    if f25 >= 0.25:
        return 2
    if f25 > 0.0:
        return 1
    return 0


def dish_match_metrics(
    pred_items: List[Dict[str, Any]],
    gt_items: List[Dict[str, Any]],
    sim_threshold: float = 0.75,
    similarity_fn=None,
) -> Optional[Dict[str, Any]]:
    """One-to-one Hungarian match (cost = 1 - similarity) of predicted vs GT items.

    Separates identification error (recall/precision/F1) from portion error
    (matched weight bands) and adds a per-item nutrient self-consistency check.
    `similarity_fn(pred_item, gt_item)->[0,1]` is pluggable; the default is a
    dependency-free max(char-LCS, content-token-overlap) over name + matched_desc
    (T=0.75 per design; calibrate on a held-out split, NOT the eval-50). Pass an
    embedding-based fn to upgrade (recommended). Returns None if scipy is
    unavailable or GT is empty.
    """
    if not gt_items:
        return None
    try:
        import numpy as _np
        from scipy.optimize import linear_sum_assignment
    except Exception:
        return None

    sim = similarity_fn or _default_pred_gt_similarity
    n_pred = len(pred_items)
    n_gt = len(gt_items)

    # Per-item nutrient self-consistency (implied kcal/g within a plausible range);
    # independent of matching, computed over all predicted items with the data.
    consistent = 0
    checkable = 0
    for p in pred_items:
        cal = p.get("calories")
        wt = p.get("weight_g")
        if cal is not None and wt and float(wt) > 0:
            checkable += 1
            kcal_per_g = float(cal) / float(wt)
            if _KCAL_PER_G_MIN <= kcal_per_g <= _KCAL_PER_G_MAX:
                consistent += 1
    nutrient_self_consistency = round(consistent / checkable, 4) if checkable else None

    if n_pred == 0:
        return {
            "recall": 0.0,
            "precision": 0.0,
            "f1": 0.0,
            "matched": 0,
            "n_pred": 0,
            "n_gt": n_gt,
            "matched_weight_mae_g": None,
            "portion_bands": {"within_10": 0.0, "within_25": 0.0, "gross": 1.0},
            "portion_score_0_5": 0,
            "nutrient_self_consistency": nutrient_self_consistency,
        }

    cost = _np.ones((n_pred, n_gt), dtype=float)
    for i, p in enumerate(pred_items):
        for j, g in enumerate(gt_items):
            cost[i, j] = 1.0 - sim(p, g)

    rows_idx, cols_idx = linear_sum_assignment(cost)
    matched = 0
    weight_errs: List[float] = []
    band_within_10 = 0
    band_within_25 = 0
    band_gross = 0
    for i, j in zip(rows_idx, cols_idx):
        if (1.0 - cost[i, j]) >= sim_threshold:
            matched += 1
            pw = pred_items[i].get("weight_g")
            gw = gt_items[j].get("weight_g")
            if pw is not None and gw is not None and float(gw) > 0:
                rel = abs(float(pw) - float(gw)) / float(gw)
                weight_errs.append(abs(float(pw) - float(gw)))
                if rel <= 0.10:
                    band_within_10 += 1
                elif rel <= 0.25:
                    band_within_25 += 1
                else:
                    band_gross += 1

    recall = matched / n_gt if n_gt else 0.0
    precision = matched / n_pred if n_pred else 0.0
    f1 = (
        (2 * recall * precision / (recall + precision)) if (recall + precision) else 0.0
    )
    banded = band_within_10 + band_within_25 + band_gross
    portion_bands = {
        "within_10": round(band_within_10 / banded, 4) if banded else 0.0,
        "within_25": round(band_within_25 / banded, 4) if banded else 0.0,
        "gross": round(band_gross / banded, 4) if banded else 0.0,
    }
    return {
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "f1": round(f1, 4),
        "matched": matched,
        "n_pred": n_pred,
        "n_gt": n_gt,
        "matched_weight_mae_g": (round(_mean(weight_errs), 2) if weight_errs else None),
        "portion_bands": portion_bands,
        "portion_score_0_5": portion_score_from_bands(portion_bands, matched),
        "nutrient_self_consistency": nutrient_self_consistency,
    }


def load_label_nutrition(label_path: Path) -> Dict[str, float]:
    data = json.loads(label_path.read_text(encoding="utf-8"))
    total_calorie = 0.0
    total_protein = 0.0
    total_fat = 0.0
    total_carbs = 0.0

    for dish in data.get("dishes", []):
        main_food = dish.get("main_food")
        if main_food:
            n = main_food.get("nutrition") or {}
            total_calorie += float(n.get("calorie", 0) or 0)
            total_protein += float(n.get("protein_g", 0) or 0)
            total_fat += float(n.get("fat_g", 0) or 0)
            total_carbs += float(n.get("carbs_g", 0) or 0)

        for extra in dish.get("extras", []):
            n = extra.get("nutrition") or {}
            total_calorie += float(n.get("calorie", 0) or 0)
            total_protein += float(n.get("protein_g", 0) or 0)
            total_fat += float(n.get("fat_g", 0) or 0)
            total_carbs += float(n.get("carbs_g", 0) or 0)

    return {
        "calories": total_calorie,
        "protein": total_protein,
        "fat": total_fat,
        "carbs": total_carbs,
    }


def normalize_total_nutrition(payload: Dict[str, Any]) -> Dict[str, float]:
    t = payload.get("total_nutrition") or {}
    return {
        "calories": float(t.get("calories", 0) or 0),
        "protein": float(t.get("protein", t.get("protein_g", 0)) or 0),
        "fat": float(t.get("fat", t.get("fat_g", 0)) or 0),
        "carbs": float(
            t.get("carbs", t.get("carbs_g", t.get("carbohydrate_g", 0))) or 0
        ),
    }


def calorie_abs_percent_error(label_cal: float, pred_cal: float) -> float:
    if label_cal <= 0:
        return 0.0 if pred_cal <= 0 else 100.0
    return abs(pred_cal - label_cal) / label_cal * 100.0


def parse_image_index_from_name(filename: str) -> int:
    match = re.search(r"test_food(\d+)\.jpg$", filename)
    if not match:
        return 0
    return int(match.group(1))


def load_image_indices(path: Path) -> List[int]:
    raw = path.read_text(encoding="utf-8").splitlines()
    indices: List[int] = []
    seen: set[int] = set()
    for line in raw:
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        value = int(text)
        if value < 1:
            raise ValueError(f"index must be >=1: {value}")
        if value in seen:
            raise ValueError(f"duplicated index in {path}: {value}")
        seen.add(value)
        indices.append(value)
    return indices


def build_image_set(
    images_dir: Path,
    labels_dir: Path,
    limit: int,
    start_index: int = 1,
    end_index: Optional[int] = None,
) -> ImageSetBuildResult:
    items: List[Dict[str, Path]] = []
    if start_index < 1:
        raise ValueError("start_index must be >= 1")

    requested_indices: List[int]
    if end_index is not None:
        if end_index < start_index:
            raise ValueError("end_index must be >= start_index")
        requested_indices = list(range(start_index, end_index + 1))
    else:
        requested_indices = list(range(start_index, start_index + limit))

    present_indices: List[int] = []
    for i in requested_indices:
        image_path = images_dir / f"test_food{i}.jpg"
        label_path = labels_dir / f"test_food{i:02d}.json"
        if image_path.exists() and label_path.exists():
            items.append({"image": image_path, "label": label_path})
            present_indices.append(i)

    present_set = set(present_indices)
    missing_indices = [i for i in requested_indices if i not in present_set]
    return ImageSetBuildResult(
        items=items,
        requested_indices=requested_indices,
        present_indices=present_indices,
        missing_indices=missing_indices,
    )


def prompt_sha256_short(prompt_text: str) -> str:
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:16]


def resolve_prompt_content(candidate: Dict[str, Any]) -> Optional[str]:
    prompt_text = candidate.get("prompt_text")
    if prompt_text:
        return str(prompt_text)

    prompt_path = candidate.get("prompt_path")
    if not prompt_path:
        return None

    candidate_paths: List[Path] = []
    raw = Path(str(prompt_path))
    if raw.is_absolute():
        candidate_paths.append(raw)
    else:
        candidate_paths.append((DEFAULT_PROMPTS_DIR / raw).resolve())
        candidate_paths.append((PROJECT_ROOT / raw).resolve())

    for path in candidate_paths:
        if path.exists():
            return path.read_text(encoding="utf-8")
    return None


def detect_prompt_leakage(prompt_text: str) -> List[str]:
    matched: List[str] = []
    for name, pattern in LEAKAGE_PATTERNS.items():
        if pattern.search(prompt_text):
            matched.append(name)
    return matched


def _normalize_model_id(model_id: str) -> str:
    """Tolerant model-id form for comparison (strip provider prefix, lowercase)."""
    value = str(model_id).strip().lower()
    if ":" in value:
        value = value.split(":", 1)[1]
    return value


def config_fidelity_mismatch(
    candidate: Dict[str, Any], payload: Dict[str, Any]
) -> Optional[str]:
    """Return a reason string if the served config != the requested candidate.

    Guards against the eval silently measuring a different model/prompt than the
    one requested (e.g. a server-side override winning), which is exactly how
    benchmarked accuracy can diverge from production undetected. Prompt files are
    only checked when the candidate requests a prompt_path (an inline prompt_text
    override has no file name to compare against).
    """
    reasons: List[str] = []

    requested_model = candidate.get("vlm_model_id")
    served_model = payload.get("ai_model_used")
    if requested_model and served_model:
        requested_norm = _normalize_model_id(requested_model)
        served_norm = _normalize_model_id(str(served_model))
        if requested_norm not in served_norm and served_norm not in requested_norm:
            reasons.append(f"model requested={requested_model} served={served_model}")

    if candidate.get("prompt_path") and not candidate.get("prompt_text"):
        requested_prompt = Path(str(candidate["prompt_path"])).name
        served_prompt = payload.get("prompt_file_used")
        if served_prompt and Path(str(served_prompt)).name != requested_prompt:
            reasons.append(
                f"prompt_file requested={requested_prompt} served={served_prompt}"
            )

    return "; ".join(reasons) if reasons else None


async def call_complete_api(
    client: httpx.AsyncClient,
    api_url: str,
    image_path: Path,
    candidate: Dict[str, Any],
    timeout_sec: int,
) -> Dict[str, Any]:
    url = f"{api_url.rstrip('/')}/api/v1/meal-analyses/complete"

    image_bytes = image_path.read_bytes()
    data: Dict[str, str] = {
        "user_context": "pdca_batch_eval",
        "vlm_model_id": candidate["vlm_model_id"],
        "use_vlm_cache": str(bool(candidate.get("use_vlm_cache", False))).lower(),
    }

    prompt_path = candidate.get("prompt_path")
    prompt_text = candidate.get("prompt_text")
    if prompt_text:
        data["prompt_text"] = str(prompt_text)
    elif prompt_path:
        data["prompt_path"] = str(prompt_path)

    if candidate.get("reasoning_effort"):
        data["reasoning_effort"] = str(candidate["reasoning_effort"])
    if candidate.get("temperature") is not None:
        data["temperature"] = str(candidate["temperature"])
    if candidate.get("seed") is not None:
        data["seed"] = str(candidate["seed"])
    if candidate.get("max_tokens") is not None:
        data["max_tokens"] = str(candidate["max_tokens"])
    if candidate.get("stage1_top_k") is not None:
        data["stage1_top_k"] = str(candidate["stage1_top_k"])
    if candidate.get("bm25_weight") is not None:
        data["bm25_weight"] = str(candidate["bm25_weight"])
    if candidate.get("vector_weight") is not None:
        data["vector_weight"] = str(candidate["vector_weight"])
    if candidate.get("rrf_k") is not None:
        data["rrf_k"] = str(candidate["rrf_k"])
    if candidate.get("rrf_weight") is not None:
        data["rrf_weight"] = str(candidate["rrf_weight"])
    if candidate.get("reranker_model"):
        data["reranker_model"] = str(candidate["reranker_model"])
    if candidate.get("reranker_instruction"):
        data["reranker_instruction"] = str(candidate["reranker_instruction"])
    if candidate.get("reranker_top_n") is not None:
        data["reranker_top_n"] = str(candidate["reranker_top_n"])

    start = time.perf_counter()
    try:
        files = {"image": (image_path.name, image_bytes, "image/jpeg")}
        resp = await client.post(url, data=data, files=files, timeout=timeout_sec)
        text = resp.text
        latency = time.perf_counter() - start
        if resp.status_code != 200:
            return {
                "success": False,
                "latency_sec": latency,
                "status": resp.status_code,
                "error": text[:1000],
            }
        payload = json.loads(text)
        return {
            "success": True,
            "latency_sec": latency,
            "payload": payload,
        }
    except Exception as e:  # pragma: no cover
        return {
            "success": False,
            "latency_sec": time.perf_counter() - start,
            "status": 0,
            "error": str(e),
        }


async def evaluate_candidate(
    client: httpx.AsyncClient,
    api_url: str,
    candidate: Dict[str, Any],
    image_set: List[Dict[str, Path]],
    expected_image_count: int,
    timeout_sec: int,
    concurrency: int,
    max_retries: int,
    retry_backoff_sec: float,
    assert_config_fidelity: bool = False,
) -> Dict[str, Any]:
    semaphore = asyncio.Semaphore(concurrency)
    results: List[Dict[str, Any]] = []
    total_count = len(image_set)
    processed_count = 0
    success_count_progress = 0
    failure_count_progress = 0
    progress_lock = asyncio.Lock()

    async def run_one(item: Dict[str, Path]) -> None:
        nonlocal processed_count, success_count_progress, failure_count_progress
        async with semaphore:
            label = load_label_nutrition(item["label"])
            attempt = 0
            api: Dict[str, Any] = {}
            while True:
                api = await call_complete_api(
                    client=client,
                    api_url=api_url,
                    image_path=item["image"],
                    candidate=candidate,
                    timeout_sec=timeout_sec,
                )
                if api.get("success"):
                    break

                status_code = int(api.get("status") or 0)
                if attempt >= max_retries or status_code not in RETRYABLE_STATUS_CODES:
                    break
                sleep_sec = retry_backoff_sec * (2**attempt)
                await asyncio.sleep(sleep_sec)
                attempt += 1

            row: Dict[str, Any] = {
                "image": item["image"].name,
                "label": label,
                "latency_sec": round(api.get("latency_sec", 0.0), 4),
                "success": api.get("success", False),
                "attempts": attempt + 1,
            }

            if not api.get("success"):
                row["status"] = api.get("status")
                row["error"] = api.get("error")
                results.append(row)
                async with progress_lock:
                    processed_count += 1
                    failure_count_progress += 1
                    if processed_count % 5 == 0 or processed_count == total_count:
                        print(
                            f"[{candidate['name']}] progress {processed_count}/{total_count} "
                            f"(ok={success_count_progress}, fail={failure_count_progress})"
                        )
                return

            payload = api["payload"]

            # 配信された設定が要求候補と一致するかを検証（fail-loud）。
            # 不一致は config_drift 失敗として扱い、failure_count>0 でゲートを hold させる。
            fidelity_error = (
                config_fidelity_mismatch(candidate, payload)
                if assert_config_fidelity
                else None
            )
            if fidelity_error:
                row["success"] = False
                row["status"] = "config_drift"
                row["error"] = "config_drift: " + fidelity_error
                results.append(row)
                async with progress_lock:
                    processed_count += 1
                    failure_count_progress += 1
                    if processed_count % 5 == 0 or processed_count == total_count:
                        print(
                            f"[{candidate['name']}] progress {processed_count}/{total_count} "
                            f"(ok={success_count_progress}, fail={failure_count_progress})"
                        )
                return

            pred = normalize_total_nutrition(payload)
            abs_err = calorie_abs_percent_error(label["calories"], pred["calories"])
            usage = payload.get("usage") or {}
            cost = usage.get("estimated_cost_usd")
            if cost is None:
                cost = usage.get("cost_usd")

            # PART A: persist reduced per-ingredient prediction + per-image dish match
            # (identification vs portion error) so error can be decomposed/diagnosed.
            pred_items = extract_pred_items(payload)
            per_image_dish_match = dish_match_metrics(
                pred_items, load_label_items(item["label"])
            )

            row.update(
                {
                    "prediction": pred,
                    "calorie_abs_percent_error": abs_err,
                    "pred_items": pred_items,
                    "dish_match": per_image_dish_match,
                    "usage": usage,
                    "cost_usd": cost,
                    "model_used": payload.get("ai_model_used"),
                    "prompt_used": payload.get("prompt_file_used"),
                    # 再現性デバッグ用に provider 側の非決定性メタデータを記録（無ければ None）
                    "seed": candidate.get("seed"),
                    "generation_id": (
                        payload.get("generation_id")
                        or usage.get("generation_id")
                        or payload.get("id")
                    ),
                    "provider": payload.get("provider") or usage.get("provider"),
                }
            )
            results.append(row)
            async with progress_lock:
                processed_count += 1
                success_count_progress += 1
                if processed_count % 5 == 0 or processed_count == total_count:
                    print(
                        f"[{candidate['name']}] progress {processed_count}/{total_count} "
                        f"(ok={success_count_progress}, fail={failure_count_progress})"
                    )

    await asyncio.gather(*(run_one(item) for item in image_set))

    success_rows = [r for r in results if r.get("success")]
    error_rows = [r for r in results if not r.get("success")]
    calorie_errors = [
        float(r.get("calorie_abs_percent_error", 0.0)) for r in success_rows
    ]
    latencies = [float(r.get("latency_sec", 0.0)) for r in success_rows]
    costs = [
        float(r["cost_usd"]) for r in success_rows if r.get("cost_usd") is not None
    ]
    cache_hits = sum(
        1 for r in success_rows if (r.get("usage") or {}).get("cached") is True
    )
    evaluated_image_count = len(results)
    failure_count = len(error_rows)
    coverage_complete = evaluated_image_count == expected_image_count
    all_success = failure_count == 0

    summary = CandidateSummary(
        name=candidate["name"],
        vlm_model_id=candidate["vlm_model_id"],
        prompt_path=candidate.get("prompt_path"),
        calorie_mae_percent=round(statistics.mean(calorie_errors), 4)
        if calorie_errors
        else 0.0,
        calorie_p50_percent=round(safe_percentile(calorie_errors, 0.5), 4)
        if calorie_errors
        else 0.0,
        calorie_p90_percent=round(safe_percentile(calorie_errors, 0.9), 4)
        if calorie_errors
        else 0.0,
        high_error_rate_30_percent=round(
            (sum(1 for e in calorie_errors if e >= 30.0) / len(calorie_errors) * 100.0)
            if calorie_errors
            else 0.0,
            4,
        ),
        avg_latency_sec=round(statistics.mean(latencies), 4) if latencies else 0.0,
        avg_cost_usd=round(statistics.mean(costs), 6) if costs else None,
        total_cost_usd=round(sum(costs), 6),
        success_count=len(success_rows),
        failure_count=failure_count,
        cache_hit_rate_percent=round((cache_hits / len(success_rows) * 100.0), 4)
        if success_rows
        else 0.0,
        evaluated_image_count=evaluated_image_count,
        expected_image_count=expected_image_count,
        coverage_complete=coverage_complete,
        all_success=all_success,
    )

    return {
        "candidate": candidate,
        "summary": asdict(summary),
        "image_results": sorted(
            results, key=lambda r: parse_image_index_from_name(r["image"])
        ),
    }


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def build_candidate_list(
    config: Dict[str, Any],
    cli_concurrency: Optional[int],
    cli_use_vlm_cache: Optional[bool],
) -> List[Dict[str, Any]]:
    defaults = config.get("defaults") or {}
    candidates = config.get("candidates") or []
    out: List[Dict[str, Any]] = []

    for c in candidates:
        item = {
            "name": c["name"],
            "vlm_model_id": c["vlm_model_id"],
            "prompt_path": c.get("prompt_path"),
            "prompt_text": c.get("prompt_text"),
            "reasoning_effort": c.get(
                "reasoning_effort", defaults.get("reasoning_effort")
            ),
            "temperature": c.get("temperature", defaults.get("temperature")),
            "seed": c.get("seed", defaults.get("seed")),
            "max_tokens": c.get("max_tokens", defaults.get("max_tokens")),
            "stage1_top_k": c.get("stage1_top_k", defaults.get("stage1_top_k")),
            "concurrency": cli_concurrency
            if cli_concurrency is not None
            else c.get("concurrency", defaults.get("concurrency", 2)),
            "use_vlm_cache": (
                cli_use_vlm_cache
                if cli_use_vlm_cache is not None
                else c.get("use_vlm_cache", defaults.get("use_vlm_cache", False))
            ),
        }
        for key in SEARCH_OVERRIDE_KEYS:
            if key in c:
                item[key] = c.get(key)
            elif key in defaults:
                item[key] = defaults.get(key)
        prompt_content = resolve_prompt_content(item)
        item["prompt_sha256"] = (
            prompt_sha256_short(prompt_content) if prompt_content else None
        )
        out.append(item)

    return out


def load_baseline_summary(path: Optional[Path]) -> Optional[Dict[str, Any]]:
    if path is None or not path.exists():
        return None
    data = load_json(path)
    return data.get("summary")


def compare_to_baseline(
    summary: Dict[str, Any], baseline: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    if not baseline:
        return {}

    keys = [
        "calorie_mae_percent",
        "high_error_rate_30_percent",
        "avg_latency_sec",
        "avg_cost_usd",
    ]
    delta: Dict[str, Any] = {}
    for key in keys:
        base_value = baseline.get(key)
        new_value = summary.get(key)
        if base_value is None or new_value is None:
            delta[f"delta_{key}"] = None
        else:
            delta[f"delta_{key}"] = round(float(new_value) - float(base_value), 6)
    return delta


def gate_decision(
    summary: Dict[str, Any],
    baseline: Optional[Dict[str, Any]],
    budget: Dict[str, Any],
    required_image_count: int,
    paired: Optional[Dict[str, Any]] = None,
    paired_requested: bool = False,
) -> Dict[str, Any]:
    """Promote-gate decision.

    When `paired` carries a valid BCa CI on per-image (candidate - baseline)
    calorie-error deltas, the MAE criterion becomes "the whole 95% CI is below 0"
    (statistically significant improvement on the SAME images), instead of the
    legacy fixed 1.0pt single-run margin. All other gates are unchanged.

    `paired_requested` is True when a paired baseline was explicitly configured
    for this candidate. If a paired comparison was requested but no usable BCa CI
    is available (degenerate / too few shared successes), we HOLD with an explicit
    reason rather than silently downgrading to the weaker fixed-margin gate
    (fail-loud, per the no-fallback rule). When `paired` is None AND
    `paired_requested` is False the legacy behavior is preserved (backward compatible).
    """
    reasons: List[str] = []
    evaluated = int(summary.get("evaluated_image_count", 0))
    failure_count = int(summary.get("failure_count", 0))
    coverage_complete = bool(summary.get("coverage_complete", False))
    all_success = bool(summary.get("all_success", False))

    if evaluated < required_image_count:
        reasons.append(
            f"evaluated_image_count {evaluated} < required {required_image_count}"
        )
    if not coverage_complete:
        reasons.append("coverage incomplete")
    if failure_count > 0:
        reasons.append(f"failure_count={failure_count}")
    if not all_success:
        reasons.append("all_success=false")

    if reasons:
        return {"decision": "hold", "reasons": reasons}

    if not baseline:
        return {
            "decision": "no-baseline",
            "reasons": ["baseline not provided", "quality gates passed"],
        }

    paired_ci = (paired or {}).get("ci") if paired else None
    use_paired = bool(paired_ci and paired_ci.get("method") == "bca")

    if not use_paired and paired_requested:
        # Paired test was explicitly requested but no usable BCa CI is available.
        # Do NOT silently fall back to the weaker fixed-margin gate (no-fallback rule).
        method = paired_ci.get("method") if paired_ci else None
        n_paired = paired.get("n_paired") if paired else None
        return {
            "decision": "hold",
            "reasons": [
                f"paired CI unavailable (method={method}, n_paired={n_paired}); "
                f"refusing to fall back to fixed 1.0pt margin"
            ],
            "gate_mode": "paired_unavailable",
        }

    if use_paired:
        ci_low = paired_ci["ci_low"]
        ci_high = paired_ci["ci_high"]
        # delta = candidate_error - baseline_error; improvement => whole CI < 0.
        mae_improved = ci_high < 0.0
        if not mae_improved:
            reasons.append(
                f"paired calorie-error delta 95% CI not entirely < 0 "
                f"([{ci_low}, {ci_high}])"
            )
    else:
        mae_improved = (
            summary["calorie_mae_percent"] <= baseline["calorie_mae_percent"] - 1.0
        )
        if not mae_improved:
            reasons.append("calorie_mae improvement < 1.0pt")

    high_error_ok = (
        summary["high_error_rate_30_percent"] <= baseline["high_error_rate_30_percent"]
    )
    if not high_error_ok:
        reasons.append("high_error_rate_30_percent regressed")

    latency_ok = summary["avg_latency_sec"] <= baseline["avg_latency_sec"] * 1.2
    if not latency_ok:
        reasons.append("avg_latency_sec exceeded +20%")

    max_avg_cost = budget.get("max_avg_cost_usd_per_image")
    cost_ok = True
    if max_avg_cost is not None:
        avg_cost = summary.get("avg_cost_usd")
        if avg_cost is None:
            reasons.append("avg_cost_usd unavailable")
            cost_ok = False
        elif avg_cost > float(max_avg_cost):
            reasons.append("avg_cost_usd exceeded budget")
            cost_ok = False

    if mae_improved and high_error_ok and latency_ok and cost_ok:
        passed = "all gates passed"
        if use_paired:
            passed = (
                "all gates passed (paired 95% CI "
                f"[{paired_ci['ci_low']}, {paired_ci['ci_high']}] < 0)"
            )
        return {
            "decision": "promote",
            "reasons": [passed],
            "gate_mode": "paired" if use_paired else "fixed_margin",
        }
    return {
        "decision": "hold",
        "reasons": reasons,
        "gate_mode": "paired" if use_paired else "fixed_margin",
    }


def write_markdown_summary(path: Path, run_payload: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# PDCA Batch Eval Summary")
    lines.append("")
    lines.append(f"- generated_at: {run_payload['generated_at']}")
    lines.append(f"- api_url: {run_payload['api_url']}")
    lines.append(f"- image_count: {run_payload['image_count']}")
    lines.append(
        f"- requested_image_count: {run_payload.get('requested_image_count', run_payload['image_count'])}"
    )
    lines.append(
        f"- required_image_count_for_promote: {run_payload.get('required_image_count', 'n/a')}"
    )
    missing_indices = run_payload.get("missing_indices") or []
    lines.append(f"- missing_indices_count: {len(missing_indices)}")
    lines.append("")
    lines.append(
        "| candidate | mae% | mae_ci95 | p50% | p90% | 30%+ | latency(s) | avg_cost | eval | fail | cache_hit% | pairedΔci95 (p) | decision |"
    )
    lines.append("|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")

    def _fmt_ci(ci: Optional[Dict[str, Any]]) -> str:
        if not ci:
            return "n/a"
        return f"[{ci['ci_low']:.2f}, {ci['ci_high']:.2f}]"

    for row in run_payload["results"]:
        s = row["summary"]
        d = row.get("decision", {})
        paired = row.get("paired") or {}
        paired_ci = paired.get("ci")
        pval = paired.get("sign_flip_pvalue")
        paired_cell = (
            f"{_fmt_ci(paired_ci)} (p={pval})" if paired_ci is not None else "n/a"
        )
        lines.append(
            "| {name} | {mae:.2f} | {mae_ci} | {p50:.2f} | {p90:.2f} | {h30:.2f} | {lat:.2f} | {cost} | {eval_count} | {fail} | {cache_hit:.2f} | {paired} | {decision} |".format(
                name=s["name"],
                mae=s["calorie_mae_percent"],
                mae_ci=_fmt_ci(s.get("calorie_mae_ci")),
                p50=s["calorie_p50_percent"],
                p90=s["calorie_p90_percent"],
                h30=s["high_error_rate_30_percent"],
                lat=s["avg_latency_sec"],
                cost=(
                    "{:.4f}".format(s["avg_cost_usd"])
                    if s.get("avg_cost_usd") is not None
                    else "N/A"
                ),
                eval_count=s.get("evaluated_image_count", 0),
                fail=s.get("failure_count", 0),
                cache_hit=s.get("cache_hit_rate_percent", 0.0),
                paired=paired_cell,
                decision=d.get("decision", "n/a"),
            )
        )

    if any(r.get("paired") for r in run_payload["results"]):
        lines.append("")
        lines.append(
            "> pairedΔci95 = 95% BCa CI of per-image (candidate - baseline) calorie "
            "abs %-error vs the paired baseline candidate; promote requires the whole "
            "CI < 0. p = two-sided sign-flip permutation p-value."
        )

    # Diagnostic decomposition: localize WHERE total-calorie error comes from.
    if any(r["summary"].get("decomposed") for r in run_payload["results"]):
        lines.append("")
        lines.append("## Diagnostic decomposition")
        lines.append("")
        lines.append(
            "| candidate | signed_mean% | signed_med% | calib_slope(OLS) | ts_slope | abs_kcal | macro MAE% (P/F/C) | dish recall/prec/F1 | matched_wt_MAE_g |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---|---|---:|")
        for r in run_payload["results"]:
            dm = r["summary"].get("decomposed") or {}
            macro = dm.get("macro_mae_percent") or {}

            def _f(v, fmt="{:.2f}"):
                return fmt.format(v) if isinstance(v, (int, float)) else "n/a"

            dma = r["summary"].get("dish_match_agg") or {}
            dish_cell = (
                f"{_f(dma.get('recall'))}/{_f(dma.get('precision'))}/{_f(dma.get('f1'))}"
                if dma
                else "n/a"
            )
            lines.append(
                "| {name} | {sm} | {smd} | {slope} | {ts} | {kcal} | {p}/{f}/{c} | {dish} | {wt} |".format(
                    name=r["summary"]["name"],
                    sm=_f(dm.get("signed_mean_error_percent")),
                    smd=_f(dm.get("signed_median_error_percent")),
                    slope=_f(dm.get("calibration_slope"), "{:.3f}"),
                    ts=_f(dm.get("theil_sen_slope"), "{:.3f}"),
                    kcal=_f(dm.get("abs_kcal_mae"), "{:.0f}"),
                    p=_f(macro.get("protein")),
                    f=_f(macro.get("fat")),
                    c=_f(macro.get("carbs")),
                    dish=dish_cell,
                    wt=_f(dma.get("matched_weight_mae_g"), "{:.0f}"),
                )
            )
        lines.append("")
        lines.append(
            "> signed_mean<0 = systematic UNDER-estimation. calib_slope<1 = predictions "
            "compress as the true meal grows (under-estimate large meals; ideal=1.0). "
            "dish_match via Hungarian name-matching separates identification vs portion error."
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PDCA batch eval")
    parser.add_argument("--config", required=True, help="Path to eval config JSON")
    parser.add_argument("--api-url", default="http://localhost:8006")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--start-index",
        type=int,
        default=1,
        help="Start image index (1-based, e.g. 26)",
    )
    parser.add_argument(
        "--end-index",
        type=int,
        default=None,
        help="Optional end image index (inclusive, e.g. 50)",
    )
    parser.add_argument(
        "--image-index-file",
        default=None,
        help="Optional text file of image indices (one per line)",
    )
    parser.add_argument("--timeout-sec", type=int, default=300)
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Retries for retryable API failures per image (429/5xx)",
    )
    parser.add_argument(
        "--retry-backoff-sec",
        type=float,
        default=1.5,
        help="Initial backoff seconds for retries (exponential)",
    )
    parser.add_argument("--concurrency", type=int, default=None)
    parser.add_argument(
        "--use-vlm-cache",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override candidate use_vlm_cache (default: from config, fallback false for eval integrity)",
    )
    parser.add_argument(
        "--allow-missing-images",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Allow missing image/label pairs in requested index range",
    )
    parser.add_argument(
        "--required-image-count",
        type=int,
        default=50,
        help="Minimum evaluated image count for promote gate",
    )
    parser.add_argument(
        "--allow-prompt-leakage",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Allow prompt text that appears to reference eval dataset internals",
    )
    parser.add_argument(
        "--assert-config-fidelity",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Fail any image whose served ai_model_used/prompt_file_used does not "
            "match the requested candidate (catches eval-vs-prod config drift). "
            "Trips the failure_count>0 hold gate on mismatch."
        ),
    )
    parser.add_argument(
        "--baseline-file", default=None, help="Optional baseline JSON override"
    )
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument(
        "--write-baseline",
        default=None,
        help="Write selected candidate summary as baseline JSON path",
    )
    parser.add_argument(
        "--baseline-candidate", default=None, help="Candidate name to write as baseline"
    )
    parser.add_argument(
        "--paired-baseline-candidate",
        default=None,
        help=(
            "Name of a co-run candidate to use as the paired reference. When set, "
            "each other candidate is gated by a paired BCa bootstrap 95%% CI on "
            "per-image calorie-error deltas (promote only if the CI is entirely < 0). "
            "Falls back to config 'paired_baseline_candidate'."
        ),
    )
    parser.add_argument(
        "--bootstrap-resamples",
        type=int,
        default=DEFAULT_BOOTSTRAP_RESAMPLES,
        help="Bootstrap resamples for MAE/paired CIs (0 disables CI computation)",
    )
    parser.add_argument(
        "--bootstrap-seed",
        type=int,
        default=DEFAULT_BOOTSTRAP_SEED,
        help="Seed for deterministic bootstrap resampling",
    )
    args = parser.parse_args()

    config_path = resolve_path(args.config)
    config = load_json(config_path)

    explicit_indices: Optional[List[int]] = None
    if args.image_index_file:
        explicit_indices = load_image_indices(resolve_path(args.image_index_file))

    image_set_result = build_image_set(
        DEFAULT_IMAGES_DIR,
        DEFAULT_LABELS_DIR,
        args.limit,
        start_index=args.start_index,
        end_index=args.end_index,
    )
    if explicit_indices is not None:
        requested = explicit_indices
        items: List[Dict[str, Path]] = []
        present_indices: List[int] = []
        for idx in explicit_indices:
            image_path = DEFAULT_IMAGES_DIR / f"test_food{idx}.jpg"
            label_path = DEFAULT_LABELS_DIR / f"test_food{idx:02d}.json"
            if image_path.exists() and label_path.exists():
                items.append({"image": image_path, "label": label_path})
                present_indices.append(idx)
        present_set = set(present_indices)
        missing_indices = [idx for idx in requested if idx not in present_set]
        image_set_result = ImageSetBuildResult(
            items=items,
            requested_indices=requested,
            present_indices=present_indices,
            missing_indices=missing_indices,
        )

    if image_set_result.missing_indices and not args.allow_missing_images:
        missing_preview = ", ".join(
            str(i) for i in image_set_result.missing_indices[:10]
        )
        raise RuntimeError(
            f"Missing image/label pairs for requested indices: {missing_preview}"
        )

    image_set = image_set_result.items
    if not image_set:
        raise RuntimeError("No test images/labels found")

    candidates = build_candidate_list(config, args.concurrency, args.use_vlm_cache)
    if not candidates:
        raise RuntimeError("No candidates defined in config")

    if not args.allow_prompt_leakage:
        leak_reasons: List[str] = []
        for c in candidates:
            prompt_content = resolve_prompt_content(c)
            if not prompt_content:
                continue
            matches = detect_prompt_leakage(prompt_content)
            if matches:
                leak_reasons.append(f"{c['name']}: {','.join(matches)}")
        if leak_reasons:
            raise RuntimeError(
                "Prompt leakage check failed: " + "; ".join(leak_reasons)
            )

    baseline_file: Optional[Path]
    if args.baseline_file:
        baseline_file = resolve_path(args.baseline_file)
    else:
        baseline_cfg = config.get("baseline_file")
        baseline_file = resolve_path(baseline_cfg) if baseline_cfg else None

    baseline_summary = load_baseline_summary(baseline_file)
    budget = config.get("budget") or {}

    paired_baseline_name = args.paired_baseline_candidate or config.get(
        "paired_baseline_candidate"
    )
    if paired_baseline_name and not any(
        c["name"] == paired_baseline_name for c in candidates
    ):
        raise RuntimeError(
            f"paired_baseline_candidate '{paired_baseline_name}' not found among candidates"
        )
    bootstrap_resamples = max(0, int(args.bootstrap_resamples))
    bootstrap_seed = int(args.bootstrap_seed)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = resolve_path(args.output_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    def _success_calorie_errors(image_results: List[Dict[str, Any]]) -> List[float]:
        return [
            float(x["calorie_abs_percent_error"])
            for x in image_results
            if x.get("success") and x.get("calorie_abs_percent_error") is not None
        ]

    async def run_all() -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        async with httpx.AsyncClient() as client:
            for c in candidates:
                print(f"Evaluating: {c['name']} ({c['vlm_model_id']})")
                row = await evaluate_candidate(
                    client=client,
                    api_url=args.api_url,
                    candidate=c,
                    image_set=image_set,
                    expected_image_count=len(image_set_result.requested_indices),
                    timeout_sec=args.timeout_sec,
                    concurrency=int(c["concurrency"]),
                    max_retries=max(0, int(args.max_retries)),
                    retry_backoff_sec=max(0.0, float(args.retry_backoff_sec)),
                    assert_config_fidelity=args.assert_config_fidelity,
                )
                rows.append(row)

        # Second pass (requires all candidates): single-run MAE CI, paired
        # bootstrap vs the co-run baseline candidate, then the promote gate.
        baseline_image_results: Optional[List[Dict[str, Any]]] = None
        if paired_baseline_name:
            for r in rows:
                if r["summary"]["name"] == paired_baseline_name:
                    baseline_image_results = r["image_results"]
                    break

        for r in rows:
            success_rows = [x for x in r["image_results"] if x.get("success")]
            if bootstrap_resamples > 0:
                r["summary"]["calorie_mae_ci"] = bootstrap_mean_ci(
                    _success_calorie_errors(r["image_results"]),
                    n_resamples=bootstrap_resamples,
                    seed=bootstrap_seed,
                )

            # Diagnostic decomposition (directional bias, calibration, macros).
            r["summary"]["decomposed"] = compute_decomposed_metrics(success_rows)

            # Aggregate per-image dish-match (identification vs portion error).
            dm = [
                x["dish_match"] for x in success_rows if x.get("dish_match") is not None
            ]
            if dm:
                weight_maes = [
                    d["matched_weight_mae_g"]
                    for d in dm
                    if d.get("matched_weight_mae_g") is not None
                ]
                r["summary"]["dish_match_agg"] = {
                    "recall": round(_mean([d["recall"] for d in dm]), 4),
                    "precision": round(_mean([d["precision"] for d in dm]), 4),
                    "f1": round(_mean([d["f1"] for d in dm]), 4),
                    "matched_weight_mae_g": (
                        round(_mean(weight_maes), 2) if weight_maes else None
                    ),
                    "n_images": len(dm),
                }
                # Design (JUDGE_EVAL_DESIGN) additive keys: recognition / portion / nutrient.
                r["summary"]["recognition_agg"] = {
                    "recall": r["summary"]["dish_match_agg"]["recall"],
                    "precision": r["summary"]["dish_match_agg"]["precision"],
                    "f1": r["summary"]["dish_match_agg"]["f1"],
                }
                band_keys = ("within_10", "within_25", "gross")
                bands = [d.get("portion_bands") for d in dm if d.get("portion_bands")]
                if bands:
                    r["summary"]["portion_bands"] = {
                        k: round(_mean([b.get(k, 0.0) for b in bands]), 4)
                        for k in band_keys
                    }
                # Deterministic portion_plausibility (0-5) — the reproducible gate signal
                # that replaces the unstable LLM judge portion score (see lesson
                # 20260602_rubric_v3_portion_should_be_deterministic.md).
                portion_scores = [
                    d["portion_score_0_5"]
                    for d in dm
                    if d.get("portion_score_0_5") is not None
                ]
                r["summary"]["portion_score_0_5_mean"] = (
                    round(_mean(portion_scores), 4) if portion_scores else None
                )
                nsc = [
                    d["nutrient_self_consistency"]
                    for d in dm
                    if d.get("nutrient_self_consistency") is not None
                ]
                r["summary"]["nutrient_self_consistency_rate"] = (
                    round(_mean(nsc), 4) if nsc else None
                )

            paired_requested = bool(
                baseline_image_results is not None
                and r["summary"]["name"] != paired_baseline_name
                and bootstrap_resamples > 0
            )
            paired: Optional[Dict[str, Any]] = None
            if paired_requested:
                deltas, _paired_images = paired_calorie_deltas(
                    r["image_results"], baseline_image_results
                )
                if deltas:
                    ci = bootstrap_mean_ci(
                        deltas,
                        n_resamples=bootstrap_resamples,
                        seed=bootstrap_seed,
                    )
                    paired = {
                        "baseline_candidate": paired_baseline_name,
                        "n_paired": len(deltas),
                        "mean_delta": ci["point"] if ci else None,
                        "ci": ci,
                        "sign_flip_pvalue": sign_flip_pvalue(
                            deltas,
                            n_resamples=bootstrap_resamples,
                            seed=bootstrap_seed + 1,
                        ),
                    }
            r["paired"] = paired
            r["baseline_delta"] = compare_to_baseline(r["summary"], baseline_summary)
            r["decision"] = gate_decision(
                r["summary"],
                baseline_summary,
                budget,
                required_image_count=args.required_image_count,
                paired=paired,
                paired_requested=paired_requested,
            )
        return rows

    results = asyncio.run(run_all())

    payload = {
        "generated_at": datetime.now().isoformat(),
        "api_url": args.api_url,
        "config_path": str(config_path),
        "baseline_file": str(baseline_file) if baseline_file else None,
        "baseline_summary": baseline_summary,
        "budget": budget,
        "image_count": len(image_set),
        "requested_image_count": len(image_set_result.requested_indices),
        "required_image_count": args.required_image_count,
        "requested_indices": image_set_result.requested_indices,
        "present_indices": image_set_result.present_indices,
        "missing_indices": image_set_result.missing_indices,
        "results": results,
    }

    raw_path = run_dir / "raw_results.json"
    summary_path = run_dir / "summary.json"
    summary_md_path = run_dir / "summary.md"

    raw_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary_payload = {
        "generated_at": payload["generated_at"],
        "api_url": payload["api_url"],
        "image_count": payload["image_count"],
        "requested_image_count": payload["requested_image_count"],
        "required_image_count": payload["required_image_count"],
        "requested_indices": payload["requested_indices"],
        "present_indices": payload["present_indices"],
        "missing_indices": payload["missing_indices"],
        "baseline_file": payload["baseline_file"],
        "results": [
            {
                "candidate": r["candidate"],
                "summary": r["summary"],
                "baseline_delta": r.get("baseline_delta", {}),
                "decision": r.get("decision", {}),
                "paired": r.get("paired"),
                # 将来のクロスランpaired解析/再診断のため per-image 誤差を summary にも保持
                "per_image_calorie_errors": {
                    x["image"]: round(float(x["calorie_abs_percent_error"]), 4)
                    for x in r["image_results"]
                    if x.get("success")
                    and x.get("calorie_abs_percent_error") is not None
                },
            }
            for r in results
        ],
    }
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_markdown_summary(summary_md_path, summary_payload)

    print(f"Saved run: {run_dir}")
    print(f"- raw: {raw_path}")
    print(f"- summary: {summary_path}")
    print(f"- markdown: {summary_md_path}")

    if args.write_baseline:
        target = resolve_path(args.write_baseline)
        target.parent.mkdir(parents=True, exist_ok=True)

        chosen: Optional[Dict[str, Any]] = None
        if args.baseline_candidate:
            for r in results:
                if r["summary"]["name"] == args.baseline_candidate:
                    chosen = r
                    break
        else:
            promote_rows = [
                r for r in results if r.get("decision", {}).get("decision") == "promote"
            ]
            ordered = sorted(
                promote_rows, key=lambda r: r["summary"]["calorie_mae_percent"]
            )
            chosen = ordered[0] if ordered else None

        if chosen is None:
            raise RuntimeError("No promotable candidate matched for baseline write")

        baseline_payload = {
            "generated_at": datetime.now().isoformat(),
            "source_run": str(run_dir),
            "summary": chosen["summary"],
        }
        target.write_text(
            json.dumps(baseline_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Baseline written: {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
