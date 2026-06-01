#!/usr/bin/env python3
"""Run reproducible PDCA batch eval for prompt/model candidates."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
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
            pred = normalize_total_nutrition(payload)
            abs_err = calorie_abs_percent_error(label["calories"], pred["calories"])
            usage = payload.get("usage") or {}
            cost = usage.get("estimated_cost_usd")
            if cost is None:
                cost = usage.get("cost_usd")

            row.update(
                {
                    "prediction": pred,
                    "calorie_abs_percent_error": abs_err,
                    "usage": usage,
                    "cost_usd": cost,
                    "model_used": payload.get("ai_model_used"),
                    "prompt_used": payload.get("prompt_file_used"),
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
) -> Dict[str, Any]:
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
        return {"decision": "promote", "reasons": ["all gates passed"]}
    return {"decision": "hold", "reasons": reasons}


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
        "| candidate | mae% | p50% | p90% | 30%+ | latency(s) | avg_cost | eval | fail | cache_hit% | decision |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")

    for row in run_payload["results"]:
        s = row["summary"]
        d = row.get("decision", {})
        lines.append(
            "| {name} | {mae:.2f} | {p50:.2f} | {p90:.2f} | {h30:.2f} | {lat:.2f} | {cost} | {eval_count} | {fail} | {cache_hit:.2f} | {decision} |".format(
                name=s["name"],
                mae=s["calorie_mae_percent"],
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
                decision=d.get("decision", "n/a"),
            )
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

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = resolve_path(args.output_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    async def run_all() -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
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
                )
                row["baseline_delta"] = compare_to_baseline(
                    row["summary"], baseline_summary
                )
                row["decision"] = gate_decision(
                    row["summary"],
                    baseline_summary,
                    budget,
                    required_image_count=args.required_image_count,
                )
                out.append(row)
        return out

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
