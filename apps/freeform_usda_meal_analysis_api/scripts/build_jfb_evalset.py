#!/usr/bin/env python
"""Build the JFB (January Food Benchmark) in-domain eval set for the mozu harness.

JFB (January AI, arXiv 2508.09966, CC-BY-4.0) is 1,000 REAL eye-level mobile-app
user photos with human-validated meal name + ingredients + macronutrients — the
closest PUBLIC proxy to mozu's deployment domain (eye-level smartphone photos of
users' own diverse real meals: home + restaurant, mixed cuisines, real plating).
This is the in-domain complement to the overhead/lab sets (Nutrition5k, NVReal).

GT = human/expert-ESTIMATED total calories + P/F/C + per-ingredient macros (NOT
weighed). So JFB is an in-domain calorie/macro/recognition benchmark; it does NOT
provide weighed per-item grams (use it as an eval/promotion proxy, not to FIT E14
calibration — that needs a weighed mozu-domain set, see docs/E13_DATA_COLLECTION_PLAN).

It downloads the public (unsigned) S3 tarball, converts to the harness's exact
label schema, and writes an evenly-spread routine-eval split. test_images_jfb/ is
gitignored (rebuildable via this script).

Usage:
  python -m apps.freeform_usda_meal_analysis_api.scripts.build_jfb_evalset \
    --out-dir test_images_jfb --split-size 100
Then evaluate:
  python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval --config <cfg> \
    --api-url http://localhost:8006 --images-dir test_images_jfb/images \
    --labels-dir test_images_jfb/images_label_with_nutrition \
    --image-index-file apps/freeform_usda_meal_analysis_api/evals/splits/jfb_test_100.txt \
    --required-image-count 100 --no-use-vlm-cache
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_DIR = PROJECT_ROOT / "apps" / "freeform_usda_meal_analysis_api"
S3_URL = (
    "https://january-food-image-dataset-public.s3.amazonaws.com/"
    "food-scan-benchmark-dataset.tar.gz"
)


def download_and_extract(cache_dir: Path) -> Path:
    """Download the JFB tarball (public, unsigned S3) and extract it; return dataset root."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    ds_root = cache_dir / "food-scan-benchmark-dataset"
    if (ds_root / "food_scan_bench_v1.csv").exists():
        print(f"Using cached dataset at {ds_root}")
        return ds_root
    archive = cache_dir / "fsb.tar.gz"
    print(f"Downloading JFB from {S3_URL} ...")
    urllib.request.urlretrieve(S3_URL, archive)  # noqa: S310 (trusted public CC-BY-4.0 asset)
    print(f"Downloaded {archive.stat().st_size // (1024 * 1024)} MB. Extracting ...")
    with tarfile.open(archive) as tar:
        tar.extractall(path=cache_dir)
    archive.unlink(missing_ok=True)
    return ds_root


def parse_ingredients(raw: str) -> List[Dict[str, Any]]:
    """JFB ingredients_list is a (sometimes double-encoded) stringified list of dicts."""
    try:
        val = ast.literal_eval(raw)
        if isinstance(val, str):
            val = ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return []
    if not isinstance(val, list):
        return []
    return [g for g in val if isinstance(g, dict)]


def build(out_dir: Path, split_size: int, cache_dir: Path) -> None:
    ds_root = download_and_extract(cache_dir)
    csv_path = ds_root / "food_scan_bench_v1.csv"
    img_src = ds_root / "fsb_images"

    img_dst = out_dir / "images"
    lab_dst = out_dir / "images_label_with_nutrition"
    img_dst.mkdir(parents=True, exist_ok=True)
    lab_dst.mkdir(parents=True, exist_ok=True)

    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    n_ok = 0
    for i, row in enumerate(rows, start=1):
        src = img_src / row["image_filename"]
        if not src.exists():
            raise SystemExit(f"missing JFB image: {src}")
        extras = [
            {
                "search_name": ing.get("name"),
                "weight_g": None,  # JFB has no weighed grams
                "nutrition": {
                    "calorie": float(ing.get("calories", 0) or 0),
                    "protein_g": float(ing.get("protein", 0) or 0),
                    "fat_g": float(ing.get("fat", 0) or 0),
                    "carbs_g": float(ing.get("carbs", 0) or 0),
                },
            }
            for ing in parse_ingredients(row["ingredients_list"])
        ]
        label = {
            "meal_name": row["meal_name"],
            "source": "JFB",
            "image_id": row["image_id"],
            "gt_type": "expert_estimated",
            "dishes": [
                {"dish_name": row["meal_name"], "main_food": None, "extras": extras}
            ],
        }
        shutil.copy(src, img_dst / f"test_food{i}.jpg")
        (lab_dst / f"test_food{i:02d}.json").write_text(
            json.dumps(label, ensure_ascii=False), encoding="utf-8"
        )
        n_ok += 1

    step = max(1, n_ok // split_size)
    idxs = list(range(1, n_ok + 1, step))[:split_size]
    split = APP_DIR / "evals" / "splits" / f"jfb_test_{split_size}.txt"
    split.write_text("\n".join(str(i) for i in idxs) + "\n", encoding="utf-8")
    print(f"Built {n_ok} JFB images+labels -> {out_dir}")
    print(
        f"Split jfb_test_{split_size} ({len(idxs)} indices, {idxs[0]}..{idxs[-1]} step {step}) -> {split}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the JFB in-domain eval set")
    ap.add_argument("--out-dir", default=str(PROJECT_ROOT / "test_images_jfb"))
    ap.add_argument("--split-size", type=int, default=100)
    ap.add_argument(
        "--cache-dir", default=str(Path(tempfile.gettempdir()) / "jfb_data")
    )
    args = ap.parse_args()
    build(Path(args.out_dir).resolve(), args.split_size, Path(args.cache_dir).resolve())


if __name__ == "__main__":
    main()
