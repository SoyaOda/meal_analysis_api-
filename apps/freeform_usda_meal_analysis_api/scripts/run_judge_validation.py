#!/usr/bin/env python3
"""Validate the Claude-as-judge BEFORE trusting it: perturbation / discriminative-power gate.

Inject synthetic degradations into real predictions and check the judge LOWERS the
RIGHT dimension. Public evaluators miss >50% of injected degradations, so this is the
must-pass gate before the judge may be used for anything beyond advisory. No human
labels needed. (Golden kappa/Pearson is a separate, later gate that needs human labels;
this file also writes a golden_set template.) See docs/EVAL_RUBRIC.md.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import httpx

from apps.freeform_usda_meal_analysis_api.scripts.run_judge_eval import (
    IMAGES_DIR,
    RUBRIC_PATH,
    build_candidate_view,
    build_gt_view,
    call_judge,
)
from apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval import (
    parse_image_index_from_name,
)

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
JUDGE_DIR = APP_DIR / "evals" / "judge"


def resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()


# ---- perturbations: (name, targeted_dimension, fn) ----------------------------------
def pert_wrong_food(cv: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(cv)
    if out.get("ingredients"):
        out["ingredients"][0]["name"] = "chocolate layer cake"
        out["ingredients"][0]["matched_desc"] = "Cake, chocolate, with frosting"
    return out


def pert_portion_2x(cv: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(cv)
    for it in out.get("ingredients", []):
        if it.get("weight_g") is not None:
            it["weight_g"] = round(float(it["weight_g"]) * 2.0, 1)
        if it.get("calories") is not None:
            it["calories"] = round(float(it["calories"]) * 2.0, 1)
    t = out.get("total_nutrition") or {}
    for k in ("calories", "protein", "fat", "carbs", "protein_g", "fat_g", "carbs_g"):
        if t.get(k) is not None:
            t[k] = round(float(t[k]) * 2.0, 1)
    return out


def pert_calorie_inflate(cv: Dict[str, Any]) -> Dict[str, Any]:
    # Keep foods + weights, but ~2x the calories only -> breaks self-consistency.
    out = copy.deepcopy(cv)
    for it in out.get("ingredients", []):
        if it.get("calories") is not None:
            it["calories"] = round(float(it["calories"]) * 2.0, 1)
    t = out.get("total_nutrition") or {}
    if t.get("calories") is not None:
        t["calories"] = round(float(t["calories"]) * 2.0, 1)
    return out


PERTURBATIONS = [
    ("wrong_food", "recognition", pert_wrong_food),
    ("portion_2x", "portion_plausibility", pert_portion_2x),
    ("calorie_inflate_2x", "nutrient_validity", pert_calorie_inflate),
]


def dim_score(judged: Dict[str, Any], dim: str) -> float:
    return float((judged.get("dimensions") or {}).get(dim, {}).get("score"))


_GOLDEN_DIMS = [
    "recognition",
    "naming_db_match",
    "portion_plausibility",
    "nutrient_validity",
    "total_plausibility",
    "user_conviction",
]


def _golden_score(entry: Dict[str, Any], dim: str):
    """Read a 0-5 score for `dim` from a golden entry (human_scores or dimensions)."""
    hs = entry.get("human_scores") or {}
    if dim in hs:
        v = hs[dim]
        return v.get("score") if isinstance(v, dict) else v
    d = (entry.get("dimensions") or {}).get(dim)
    return d.get("score") if isinstance(d, dict) else d


def quadratic_weighted_kappa(a: List[float], b: List[float], lo: int = 0, hi: int = 5):
    import numpy as np

    n = hi - lo + 1
    obs = np.zeros((n, n))
    for x, y in zip(a, b):
        obs[int(round(x)) - lo][int(round(y)) - lo] += 1
    if obs.sum() == 0:
        return None
    w = np.array(
        [[((i - j) ** 2) / ((n - 1) ** 2) for j in range(n)] for i in range(n)]
    )
    exp = np.outer(obs.sum(1), obs.sum(0)) / obs.sum()
    den = (w * exp).sum()
    if den == 0:
        return 1.0
    return round(1.0 - (w * obs).sum() / den, 4)


def golden_eval(golden_path: Path, judge_file: Path) -> Dict[str, Any]:
    """Quadratic-weighted kappa + Pearson r between judge and human golden, per dimension."""
    import numpy as np

    golden: Dict[str, Any] = {}
    for line in golden_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            e = json.loads(line)
            golden[e["image_id"]] = e
    per = json.loads(judge_file.read_text(encoding="utf-8")).get("per_image") or []

    result: Dict[str, Any] = {}
    comp_g: List[float] = []
    comp_j: List[float] = []
    for dim in _GOLDEN_DIMS:
        pairs = []
        for pi in per:
            iid = pi.get("image_id")
            if iid not in golden:
                continue
            js = (pi.get("dimensions") or {}).get(dim, {}).get("score")
            gs = _golden_score(golden[iid], dim)
            if js is None or gs is None:
                continue
            pairs.append((float(gs), float(js)))
        if len(pairs) >= 2:
            g = [p[0] for p in pairs]
            j = [p[1] for p in pairs]
            r = (
                float(np.corrcoef(g, j)[0, 1])
                if len(set(g)) > 1 and len(set(j)) > 1
                else None
            )
            result[dim] = {
                "n": len(pairs),
                "weighted_kappa": quadratic_weighted_kappa(g, j),
                "pearson_r": round(r, 4) if r is not None else None,
            }
            comp_g += g
            comp_j += j
        else:
            result[dim] = {"n": len(pairs), "weighted_kappa": None, "pearson_r": None}

    comp_r = (
        float(np.corrcoef(comp_g, comp_j)[0, 1])
        if len(comp_g) >= 2 and len(set(comp_g)) > 1 and len(set(comp_j)) > 1
        else None
    )
    kappas = [
        v["weighted_kappa"] for v in result.values() if v["weighted_kappa"] is not None
    ]
    gate_pass = bool(
        kappas and min(kappas) >= 0.6 and comp_r is not None and comp_r >= 0.80
    )
    return {
        "per_dimension": result,
        "composite_pearson_r": round(comp_r, 4) if comp_r is not None else None,
        "min_weighted_kappa": round(min(kappas), 4) if kappas else None,
        "gate_pass": gate_pass,
        "criteria": "per-dim weighted_kappa>=0.6 AND composite_pearson_r>=0.80",
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Judge validation: perturbation gate (default) or --golden kappa/Pearson"
    )
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--candidate", default=None)
    ap.add_argument("--image-index-file", default=None)
    ap.add_argument(
        "--limit", type=int, default=6, help="Images to test (cost-bounded)"
    )
    ap.add_argument("--judge-model", default="anthropic/claude-sonnet-4.6")
    ap.add_argument("--timeout-sec", type=int, default=120)
    ap.add_argument("--write-golden-template", action="store_true")
    ap.add_argument(
        "--golden", default=None, help="golden_set.jsonl -> run kappa/Pearson mode"
    )
    ap.add_argument(
        "--judge-file",
        default=None,
        help="judge_<candidate>.json to validate against golden",
    )
    args = ap.parse_args()

    # --- golden mode (no API): compare judge per-image scores to human golden ---
    if args.golden:
        if not args.judge_file:
            raise RuntimeError(
                "--golden requires --judge-file (a judge_<candidate>.json)"
            )
        out = golden_eval(resolve(args.golden), resolve(args.judge_file))
        out_path = JUDGE_DIR / "validation_golden.json"
        out_path.write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("=== Golden agreement (judge vs human) ===")
        for dim, v in out["per_dimension"].items():
            print(
                f"  {dim:22s} n={v['n']:>2} weighted_kappa={v['weighted_kappa']} pearson_r={v['pearson_r']}"
            )
        print(
            f"  composite_pearson_r={out['composite_pearson_r']} min_kappa={out['min_weighted_kappa']} gate_pass={out['gate_pass']}"
        )
        print(f"Saved: {out_path}")
        return 0

    if not args.run_dir or not args.candidate:
        raise RuntimeError("perturbation mode requires --run-dir and --candidate")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    run_dir = resolve(args.run_dir)
    raw = json.loads((run_dir / "raw_results.json").read_text(encoding="utf-8"))
    rubric = RUBRIC_PATH.read_text(encoding="utf-8")
    cand = next(r for r in raw["results"] if r["summary"]["name"] == args.candidate)
    rows = [
        r for r in cand["image_results"] if r.get("success") and r.get("pred_items")
    ]
    rows.sort(key=lambda r: parse_image_index_from_name(r["image"]))
    if args.image_index_file:
        keep = {
            int(t)
            for t in resolve(args.image_index_file).read_text().split()
            if t.strip().isdigit()
        }
        rows = [r for r in rows if parse_image_index_from_name(r["image"]) in keep]
    rows = rows[: args.limit]
    if not rows:
        raise RuntimeError("no judgeable rows (need pred_items)")

    JUDGE_DIR.mkdir(parents=True, exist_ok=True)
    if args.write_golden_template:
        tmpl = JUDGE_DIR / "golden_set.template.jsonl"
        with tmpl.open("w", encoding="utf-8") as f:
            for r in rows:
                idx = parse_image_index_from_name(r["image"])
                f.write(
                    json.dumps(
                        {
                            "image_id": f"test_food{idx}",
                            "human_scores": {
                                d: None
                                for d in [
                                    "recognition",
                                    "naming_db_match",
                                    "portion_plausibility",
                                    "nutrient_validity",
                                    "total_plausibility",
                                    "user_conviction",
                                ]
                            },
                            "note": "Label each 0-5 by viewing test_images/images/%s + the GT json."
                            % r["image"],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        print(
            f"Wrote golden template: {tmpl} (label human_scores 0-5, then run --golden)"
        )

    results: List[Dict[str, Any]] = []
    with httpx.Client() as client:
        for i, r in enumerate(rows, 1):
            idx = parse_image_index_from_name(r["image"])
            image_bytes = (IMAGES_DIR / r["image"]).read_bytes()
            gt_view = build_gt_view(idx)
            base_cv = build_candidate_view(r)

            orig = call_judge(
                client,
                api_key,
                args.judge_model,
                rubric,
                image_bytes,
                gt_view,
                base_cv,
                f"test_food{idx}",
                args.timeout_sec,
            )
            row_out: Dict[str, Any] = {
                "image_id": f"test_food{idx}",
                "perturbations": {},
            }
            for pname, dim, fn in PERTURBATIONS:
                pert_cv = fn(base_cv)
                pj = call_judge(
                    client,
                    api_key,
                    args.judge_model,
                    rubric,
                    image_bytes,
                    gt_view,
                    pert_cv,
                    f"test_food{idx}",
                    args.timeout_sec,
                )
                try:
                    delta = dim_score(orig, dim) - dim_score(pj, dim)
                except Exception:
                    delta = None
                row_out["perturbations"][pname] = {
                    "targeted_dim": dim,
                    "orig_score": dim_score(orig, dim),
                    "pert_score": dim_score(pj, dim),
                    "delta": round(delta, 3) if delta is not None else None,
                    "detected": (delta is not None and delta > 0),
                }
            results.append(row_out)
            print(
                f"  [{i}/{len(rows)}] test_food{idx}: "
                + ", ".join(
                    f"{p}:{v['orig_score']:.0f}->{v['pert_score']:.0f}(Δ{v['delta']})"
                    for p, v in row_out["perturbations"].items()
                )
            )

    # discriminative power per perturbation
    summary: Dict[str, Any] = {}
    for pname, dim, _ in PERTURBATIONS:
        deltas = [
            r["perturbations"][pname]["delta"]
            for r in results
            if r["perturbations"][pname]["delta"] is not None
        ]
        detected = [r["perturbations"][pname]["detected"] for r in results]
        summary[pname] = {
            "targeted_dim": dim,
            "mean_delta": round(statistics.mean(deltas), 3) if deltas else None,
            "detection_rate": round(sum(detected) / len(detected), 3)
            if detected
            else None,
            "n": len(results),
        }
    overall_detection = statistics.mean(
        [
            s["detection_rate"]
            for s in summary.values()
            if s["detection_rate"] is not None
        ]
    )
    out = {
        "generated_at": datetime.now().isoformat(),
        "judge_model": args.judge_model,
        "candidate": args.candidate,
        "n_images": len(results),
        "per_perturbation": summary,
        "overall_detection_rate": round(overall_detection, 3),
        "gate_pass": overall_detection
        >= 0.8,  # design: must detect injected degradations
        "per_image": results,
    }
    out_path = JUDGE_DIR / f"validation_perturbation_{args.candidate}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== Discriminative-power gate ===")
    for p, s in summary.items():
        print(
            f"  {p:18s} (-> {s['targeted_dim']}): detection_rate={s['detection_rate']} mean_delta={s['mean_delta']}"
        )
    print(
        f"  OVERALL detection_rate={out['overall_detection_rate']}  gate_pass={out['gate_pass']}"
    )
    print(f"Saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
