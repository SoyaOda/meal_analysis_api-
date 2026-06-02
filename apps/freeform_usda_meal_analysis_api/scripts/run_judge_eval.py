#!/usr/bin/env python3
"""Claude(VLM)-as-judge eval: score the FULL meal-analysis output for user-conviction.

Post-processes a FINISHED run dir (does not touch the generation loop). For each
selected image it sends the PHOTO + GT labels + the candidate's structured output to a
Claude vision judge (via OpenRouter, no new dependency), gets the locked rubric JSON,
computes a geometric-mean conviction, and aggregates per-dimension means + failure tags.

ADVISORY by default: until the judge is validated against a human golden set
(weighted kappa >= 0.6 + perturbation gate), these scores must NOT gate promotion.
See docs/EVAL_RUBRIC.md / docs/JUDGE_EVAL_DESIGN_20260602.md.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval import (
    bootstrap_mean_ci,
    load_label_items,
    load_label_nutrition,
    parse_image_index_from_name,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_DIR = Path(__file__).resolve().parents[1]
IMAGES_DIR = PROJECT_ROOT / "test_images" / "images"
LABELS_DIR = PROJECT_ROOT / "test_images" / "images_label_with_nutrition"
RUBRIC_PATH = APP_DIR / "evals" / "judge" / "judge_rubric_v1.txt"
CACHE_DIR = APP_DIR / "evals" / "judge" / "cache"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Geometric-mean weights (sum=1.0); see docs/EVAL_RUBRIC.md.
DIMENSION_WEIGHTS = {
    "recognition": 0.30,
    "naming_db_match": 0.25,
    "portion_plausibility": 0.20,
    "nutrient_validity": 0.15,
    "total_plausibility": 0.10,
}
RUBRIC_VERSION = "v1"


def resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (PROJECT_ROOT / p).resolve()


def overall_conviction(dimensions: Dict[str, Any]) -> Optional[float]:
    """Geometric mean of the 5 weighted dimensions -> 0-100 (one weak dim tanks it)."""
    product = 1.0
    for key, weight in DIMENSION_WEIGHTS.items():
        entry = dimensions.get(key) or {}
        score = entry.get("score")
        if score is None:
            return None
        frac = max(float(score), 0.0) / 5.0
        frac = max(frac, 0.002)  # clamp 0 -> ~0.01 so a single 0 doesn't hard-zero
        product *= frac**weight
    return round(100.0 * product, 2)


def build_candidate_view(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ingredients": row.get("pred_items") or [],
        "total_nutrition": row.get("prediction") or {},
    }


def build_gt_view(image_index: int) -> Dict[str, Any]:
    label_path = LABELS_DIR / f"test_food{image_index:02d}.json"
    return {
        "items": load_label_items(label_path),
        "total_nutrition": load_label_nutrition(label_path),
    }


def parse_judge_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in judge output: {text[:200]}")
    return json.loads(cleaned[start : end + 1])


def call_judge(
    client: httpx.Client,
    api_key: str,
    judge_model: str,
    rubric: str,
    image_bytes: bytes,
    gt_view: Dict[str, Any],
    candidate_view: Dict[str, Any],
    image_id: str,
    timeout_sec: int,
) -> Dict[str, Any]:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    user_text = (
        f"{rubric}\n\nimage_id: {image_id}\n\n"
        f"GROUND_TRUTH (numeric truth):\n{json.dumps(gt_view, ensure_ascii=False)}\n\n"
        f"CANDIDATE_OUTPUT (score this):\n{json.dumps(candidate_view, ensure_ascii=False)}"
    )
    body = {
        "model": judge_model,
        "temperature": 0,
        "max_tokens": 4000,
        "usage": {"include": True},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            }
        ],
    }
    resp = client.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json=body,
        timeout=timeout_sec,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"judge HTTP {resp.status_code}: {resp.text[:400]}")
    payload = resp.json()
    content = payload["choices"][0]["message"]["content"]
    usage = payload.get("usage") or {}
    parsed = parse_judge_json(content)
    parsed["_cost_usd"] = usage.get("cost")
    return parsed


def cache_key(
    image_bytes: bytes, candidate_view: Dict[str, Any], contract: Dict[str, Any]
) -> str:
    h = hashlib.sha256()
    h.update(hashlib.sha256(image_bytes).digest())
    h.update(json.dumps(candidate_view, sort_keys=True, ensure_ascii=False).encode())
    h.update(json.dumps(contract, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()


def aggregate(per_image: List[Dict[str, Any]]) -> Dict[str, Any]:
    convictions = [
        r["overall_conviction"]
        for r in per_image
        if r.get("overall_conviction") is not None
    ]
    dims = list(DIMENSION_WEIGHTS.keys()) + ["user_conviction"]
    per_dimension_mean: Dict[str, Any] = {}
    for d in dims:
        vals = [
            float(r["dimensions"][d]["score"])
            for r in per_image
            if r.get("dimensions", {}).get(d, {}).get("score") is not None
        ]
        per_dimension_mean[d] = round(statistics.mean(vals), 3) if vals else None
    tag_counts: Dict[str, int] = {}
    for r in per_image:
        for t in r.get("failure_tags") or []:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    edits = [
        r.get("edits_needed") for r in per_image if r.get("edits_needed") is not None
    ]
    ci = bootstrap_mean_ci(convictions) if convictions else None
    return {
        "n_images": len(per_image),
        "overall_conviction_mean": round(statistics.mean(convictions), 2)
        if convictions
        else None,
        "overall_conviction_ci": [ci["ci_low"], ci["ci_high"]] if ci else None,
        "per_dimension_mean": per_dimension_mean,
        "failure_tag_counts": dict(sorted(tag_counts.items(), key=lambda kv: -kv[1])),
        "edits_needed_mean": round(statistics.mean(edits), 2) if edits else None,
        "needs_human_review_rate": round(
            sum(1 for r in per_image if r.get("needs_human_review")) / len(per_image), 3
        )
        if per_image
        else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Claude-as-judge eval (advisory)")
    ap.add_argument(
        "--run-dir", required=True, help="Finished run dir with raw_results.json"
    )
    ap.add_argument(
        "--candidates",
        default=None,
        help="Comma-separated candidate names (default: all)",
    )
    ap.add_argument(
        "--image-index-file", default=None, help="Index file to limit images"
    )
    ap.add_argument("--limit", type=int, default=None, help="Max images per candidate")
    ap.add_argument(
        "--judge-model",
        default="anthropic/claude-sonnet-4.6",
        help="OpenRouter judge model id (Claude vision; cross-family vs Gemini generator)",
    )
    ap.add_argument(
        "--samples", type=int, default=1, help="Judge samples per image (averaged)"
    )
    ap.add_argument("--timeout-sec", type=int, default=120)
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set (judge calls OpenRouter)")

    run_dir = resolve(args.run_dir)
    raw = json.loads((run_dir / "raw_results.json").read_text(encoding="utf-8"))
    rubric = RUBRIC_PATH.read_text(encoding="utf-8")
    contract = {
        "judge_model_id": args.judge_model,
        "rubric_version": RUBRIC_VERSION,
        "prompt_sha256": hashlib.sha256(rubric.encode()).hexdigest()[:16],
        "weights": DIMENSION_WEIGHTS,
        "n_samples": args.samples,
    }
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    only = set(args.candidates.split(",")) if args.candidates else None
    index_filter = None
    if args.image_index_file:
        index_filter = {
            int(t)
            for t in resolve(args.image_index_file).read_text().split()
            if t.strip().isdigit()
        }

    results = raw.get("results", [])
    overall_out: Dict[str, Any] = {}
    with httpx.Client() as client:
        for cand_row in results:
            name = cand_row["summary"]["name"]
            if only and name not in only:
                continue
            rows = [
                r
                for r in cand_row["image_results"]
                if r.get("success") and r.get("pred_items") is not None
            ]
            rows.sort(key=lambda r: parse_image_index_from_name(r["image"]))
            if index_filter is not None:
                rows = [
                    r
                    for r in rows
                    if parse_image_index_from_name(r["image"]) in index_filter
                ]
            if args.limit:
                rows = rows[: args.limit]
            if not rows:
                print(f"[{name}] no judgeable images (need pred_items); skipping")
                continue

            per_image: List[Dict[str, Any]] = []
            total_cost = 0.0
            judge_failures = 0
            print(
                f"[{name}] judging {len(rows)} images x {args.samples} samples with {args.judge_model}"
            )
            for i, r in enumerate(rows, 1):
                idx = parse_image_index_from_name(r["image"])
                image_path = IMAGES_DIR / r["image"]
                image_bytes = image_path.read_bytes()
                gt_view = build_gt_view(idx)
                cand_view = build_candidate_view(r)
                key = cache_key(image_bytes, cand_view, contract)
                cache_file = CACHE_DIR / f"{key}.json"

                if cache_file.exists() and not args.no_cache:
                    judged = json.loads(cache_file.read_text(encoding="utf-8"))
                else:
                    try:
                        sample_dims: List[Dict[str, Any]] = []
                        base_judged: Optional[Dict[str, Any]] = None
                        for _s in range(max(1, args.samples)):
                            j = call_judge(
                                client,
                                api_key,
                                args.judge_model,
                                rubric,
                                image_bytes,
                                gt_view,
                                cand_view,
                                f"test_food{idx}",
                                args.timeout_sec,
                            )
                            sample_dims.append(j.get("dimensions") or {})
                            base_judged = j
                            if j.get("_cost_usd"):
                                total_cost += float(j["_cost_usd"])
                    except Exception as exc:  # noqa: BLE001 - skip a bad image, don't crash run
                        judge_failures += 1
                        print(
                            f"  [WARN] {name} {r['image']} judge failed: {str(exc)[:160]}"
                        )
                        continue
                    # average dimension scores across samples
                    judged = base_judged or {}
                    avg_dims: Dict[str, Any] = {}
                    for d in list(DIMENSION_WEIGHTS.keys()) + ["user_conviction"]:
                        scs = [
                            float(sd[d]["score"])
                            for sd in sample_dims
                            if sd.get(d, {}).get("score") is not None
                        ]
                        if scs:
                            merged = dict((sample_dims[0].get(d) or {}))
                            merged["score"] = round(statistics.mean(scs), 3)
                            avg_dims[d] = merged
                    judged["dimensions"] = avg_dims
                    judged["overall_conviction"] = overall_conviction(avg_dims)
                    judged["image_id"] = f"test_food{idx}"
                    judged.pop("_cost_usd", None)
                    if not args.no_cache:
                        cache_file.write_text(
                            json.dumps(judged, ensure_ascii=False, indent=2)
                        )
                per_image.append(judged)
                if i % 5 == 0 or i == len(rows):
                    print(f"  [{name}] {i}/{len(rows)}")
                time.sleep(0)

            agg = aggregate(per_image)
            agg["contract"] = contract
            agg["judge_cost_usd"] = round(total_cost, 4)
            agg["judge_failures"] = judge_failures
            agg["advisory_only"] = True
            agg["note"] = (
                "ADVISORY: judge not yet validated vs golden set; do NOT gate on this."
            )
            out_path = run_dir / f"judge_{name}.json"
            out_path.write_text(
                json.dumps(
                    {"summary": agg, "per_image": per_image},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            overall_out[name] = agg
            print(
                f"[{name}] conviction_mean={agg['overall_conviction_mean']} "
                f"dims={agg['per_dimension_mean']} cost=${agg['judge_cost_usd']} -> {out_path.name}"
            )

    summary_path = run_dir / "judge_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(),
                "contract": contract,
                "candidates": overall_out,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved judge summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
