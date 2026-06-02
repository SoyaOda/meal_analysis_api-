#!/usr/bin/env python3
"""Fit the post-hoc calorie calibration (true ≈ slope*pred + intercept) from a run.

Fits a ROBUST (Theil-Sen) affine map on a FIT split and (if given) validates it on a
disjoint TEST split, reporting MAE/signed-bias before vs after. Writes the fitted
params to config/calorie_calibration.json. Writes enabled=FALSE by default — review
the held-out validation, and only flip enabled=true once fit on data DISJOINT from the
benchmark you judge it on (anti-overfit rule).
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = APP_DIR / "config" / "calorie_calibration.json"


def resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (PROJECT_ROOT / p).resolve()


def parse_index(name: str) -> int:
    m = re.search(r"test_food(\d+)\.jpg", name)
    return int(m.group(1)) if m else -1


def load_index_set(path: Optional[Path]) -> Optional[set]:
    if path is None:
        return None
    return {int(t) for t in path.read_text().split() if t.strip().isdigit()}


def pairs_from_run(
    run_dir: Path, candidate: Optional[str]
) -> List[Tuple[int, float, float]]:
    """Return [(image_index, true_cal, pred_cal)] for successful rows of a candidate."""
    data = json.loads((run_dir / "raw_results.json").read_text(encoding="utf-8"))
    results = data.get("results", [])
    if candidate:
        row = next(r for r in results if r["summary"]["name"] == candidate)
    else:
        row = results[0]
    out: List[Tuple[int, float, float]] = []
    for x in row["image_results"]:
        if not x.get("success"):
            continue
        true_cal = float((x.get("label") or {}).get("calories", 0) or 0)
        pred_cal = float((x.get("prediction") or {}).get("calories", 0) or 0)
        if true_cal > 0:
            out.append((parse_index(x["image"]), true_cal, pred_cal))
    return out


def theil_sen_fit(
    true_vals: List[float], pred_vals: List[float]
) -> Tuple[float, float]:
    """Robust fit of true ≈ slope*pred + intercept (Theil-Sen)."""
    from scipy.stats import theilslopes

    slope, intercept, _lo, _hi = theilslopes(true_vals, pred_vals)
    return float(slope), float(intercept)


def mae(pairs: List[Tuple[float, float]]) -> float:
    return statistics.mean(abs(p - t) / t * 100.0 for t, p in pairs)


def signed(pairs: List[Tuple[float, float]]) -> float:
    return statistics.mean((p - t) / t * 100.0 for t, p in pairs)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fit post-hoc calorie calibration")
    ap.add_argument("--run-dir", required=True, help="Run dir with raw_results.json")
    ap.add_argument("--candidate", default=None, help="Candidate name (default: first)")
    ap.add_argument(
        "--fit-split", default=None, help="Index file for the FIT set (default: all)"
    )
    ap.add_argument(
        "--test-split", default=None, help="Index file for a disjoint TEST set"
    )
    ap.add_argument("--config-out", default=str(DEFAULT_CONFIG))
    ap.add_argument("--min-factor", type=float, default=0.5)
    ap.add_argument("--max-factor", type=float, default=2.5)
    ap.add_argument(
        "--enable",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Write enabled=true (default false — review held-out validation first)",
    )
    ap.add_argument("--provenance", default="", help="Note describing the fit set")
    args = ap.parse_args()

    run_dir = resolve(args.run_dir)
    all_pairs = pairs_from_run(run_dir, args.candidate)
    fit_idx = load_index_set(resolve(args.fit_split)) if args.fit_split else None
    test_idx = load_index_set(resolve(args.test_split)) if args.test_split else None

    fit_pairs = [(t, p) for i, t, p in all_pairs if (fit_idx is None or i in fit_idx)]
    if len(fit_pairs) < 2:
        raise RuntimeError("Need >=2 fit points")

    slope, intercept = theil_sen_fit(
        [t for t, _ in fit_pairs], [p for _, p in fit_pairs]
    )
    print(f"Fit (Theil-Sen, true ≈ slope*pred + intercept) on n={len(fit_pairs)}:")
    print(f"  slope={slope:.4f}  intercept={intercept:.2f}")
    print(f"  fit-set raw MAE={mae(fit_pairs):.2f}% signed={signed(fit_pairs):+.2f}%")
    cal_fit = [(t, slope * p + intercept) for t, p in fit_pairs]
    print(
        f"  fit-set CAL MAE={mae(cal_fit):.2f}% signed={signed(cal_fit):+.2f}% (in-sample)"
    )

    if test_idx is not None:
        test_pairs = [(t, p) for i, t, p in all_pairs if i in test_idx]
        if test_pairs:
            cal_test = [(t, slope * p + intercept) for t, p in test_pairs]
            print(f"\nHELD-OUT TEST (n={len(test_pairs)}, disjoint from fit):")
            print(f"  RAW MAE={mae(test_pairs):.2f}% signed={signed(test_pairs):+.2f}%")
            print(f"  CAL MAE={mae(cal_test):.2f}% signed={signed(cal_test):+.2f}%")

    config: Dict = {
        "enabled": bool(args.enable),
        "slope": round(slope, 6),
        "intercept": round(intercept, 4),
        "min_factor": args.min_factor,
        "max_factor": args.max_factor,
        "provenance": args.provenance
        or f"Theil-Sen fit on {run_dir.name} (fit n={len(fit_pairs)}). corrected=slope*raw+intercept.",
        "fitted_at": datetime.now().isoformat(),
        "fit_set": args.fit_split,
    }
    out_path = resolve(args.config_out)
    out_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {out_path} (enabled={config['enabled']})")
    if not config["enabled"]:
        print(
            "NOTE: enabled=false. Review the held-out validation, ensure the fit set is"
        )
        print(
            "      DISJOINT from any benchmark you judge it on, then set enabled=true."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
