"""Ingest a weighed-as-you-plate E13 collection into the mozu eval harness format.

The physical collection (weigh each ingredient on a scale, shoot an EYE-LEVEL photo,
record per-ingredient nutrition from a food DB) is done by a human — see
docs/E13_DATA_COLLECTION_PLAN_20260606.md §3. This script makes the rest turnkey:
it validates each collected meal manifest, converts it to the harness format
(test_food{i}.jpg + nested label JSON carrying per-item grams + nutrition +
total_food_weight_g + stratum metadata), writes a split, and reports stratum
coverage so under-filled cells (E13 §4/§6) are visible.

Input manifest (one JSON per meal, OR a manifests.json list), schema:
{
  "image": "meal_001.jpg",            # path relative to the collection dir
  "meal_name": "Grilled chicken plate",
  "angle": "eye-level",               # eye-level | overhead   (E13 dominant stratum)
  "container": "plate",               # plate | bowl | takeout | tray
  "size_bucket": "auto",              # auto | lt_300 | 300_700 | 700_1500 | gte_1500
  "cuisine": "american",
  "eat_context": "home",              # home | restaurant | chain
  "fat_level": "mixed",               # lean | mixed | high_fat
  "ingredients": [
    {"name": "grilled chicken breast", "grams": 150,
     "calories": 248, "protein_g": 46.5, "fat_g": 5.4, "carbs_g": 0.0,
     "fdc_id": "171534"}              # fdc_id optional (provenance)
  ]
}
Nutrition per ingredient is REQUIRED (collector looks it up: USDA/FNDDS, barcode,
or chain menu). grams REQUIRED (weighed). This keeps ingestion decoupled from the
retrieval server. Usage:
  python -m apps...scripts.ingest_e13_collection --collection-dir <dir> [--out-name e13_pilot] [--template]
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_DIR = PROJECT_ROOT / "apps" / "freeform_usda_meal_analysis_api"

ANGLES = {"eye-level", "overhead"}
CONTAINERS = {"plate", "bowl", "takeout", "tray"}
EAT = {"home", "restaurant", "chain"}
FAT = {"lean", "mixed", "high_fat"}
REQUIRED_ING_NUM = ("grams", "calories", "protein_g", "fat_g", "carbs_g")

TEMPLATE: Dict[str, Any] = {
    "image": "meal_001.jpg",
    "meal_name": "Grilled chicken plate",
    "angle": "eye-level",
    "container": "plate",
    "size_bucket": "auto",
    "cuisine": "american",
    "eat_context": "home",
    "fat_level": "mixed",
    "ingredients": [
        {
            "name": "grilled chicken breast",
            "grams": 150,
            "calories": 248,
            "protein_g": 46.5,
            "fat_g": 5.4,
            "carbs_g": 0.0,
            "fdc_id": "171534",
        },
        {
            "name": "white rice, cooked",
            "grams": 180,
            "calories": 234,
            "protein_g": 4.9,
            "fat_g": 0.5,
            "carbs_g": 50.6,
            "fdc_id": "169756",
        },
    ],
}


def size_bucket(cal: float) -> str:
    if cal < 300:
        return "lt_300"
    if cal < 700:
        return "300_700"
    if cal < 1500:
        return "700_1500"
    return "gte_1500"


def validate(meal: Dict[str, Any], idx: int) -> List[str]:
    errs: List[str] = []
    if not meal.get("image"):
        errs.append(f"[{idx}] missing 'image'")
    if meal.get("angle") not in ANGLES:
        errs.append(f"[{idx}] angle must be one of {ANGLES}, got {meal.get('angle')!r}")
    if meal.get("container") not in CONTAINERS:
        errs.append(f"[{idx}] container must be one of {CONTAINERS}")
    if meal.get("eat_context") not in EAT:
        errs.append(f"[{idx}] eat_context must be one of {EAT}")
    if meal.get("fat_level") not in FAT:
        errs.append(f"[{idx}] fat_level must be one of {FAT}")
    ings = meal.get("ingredients")
    if not isinstance(ings, list) or not ings:
        errs.append(f"[{idx}] 'ingredients' must be a non-empty list")
        return errs
    for j, ing in enumerate(ings):
        if not ing.get("name"):
            errs.append(f"[{idx}] ingredient {j} missing 'name'")
        for k in REQUIRED_ING_NUM:
            if not isinstance(ing.get(k), (int, float)):
                errs.append(
                    f"[{idx}] ingredient {j} ({ing.get('name')}) missing numeric '{k}'"
                )
    return errs


def to_label(meal: Dict[str, Any]) -> Tuple[Dict[str, Any], float, float]:
    extras: List[Dict[str, Any]] = []
    tot_cal = tot_g = 0.0
    for ing in meal["ingredients"]:
        g = float(ing["grams"])
        extras.append(
            {
                "search_name": ing["name"],
                "weight_g": g,
                "fdc_id": ing.get("fdc_id"),
                "nutrition": {
                    "calorie": float(ing["calories"]),
                    "protein_g": float(ing["protein_g"]),
                    "fat_g": float(ing["fat_g"]),
                    "carbs_g": float(ing["carbs_g"]),
                },
            }
        )
        tot_cal += float(ing["calories"])
        tot_g += g
    sb = meal.get("size_bucket")
    if sb in (None, "auto"):
        sb = size_bucket(tot_cal)
    label = {
        "meal_name": meal.get("meal_name", ""),
        "source": "E13",
        "total_food_weight_g": round(tot_g, 1),
        "stratum": {
            "angle": meal["angle"],
            "container": meal["container"],
            "size_bucket": sb,
            "cuisine": meal.get("cuisine"),
            "eat_context": meal["eat_context"],
            "fat_level": meal["fat_level"],
        },
        "dishes": [
            {
                "dish_name": meal.get("meal_name", ""),
                "main_food": None,
                "extras": extras,
            }
        ],
    }
    return label, tot_cal, tot_g


def load_manifests(coll: Path) -> List[Dict[str, Any]]:
    single = coll / "manifests.json"
    if single.exists():
        data = json.loads(single.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else [data]
    meals = []
    for p in sorted(coll.glob("*.json")):
        if p.name == "manifests.json":
            continue
        meals.append(json.loads(p.read_text(encoding="utf-8")))
    return meals


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Ingest E13 weighed collection -> harness eval set"
    )
    ap.add_argument(
        "--collection-dir", help="dir with per-meal *.json manifests + images"
    )
    ap.add_argument(
        "--out-name", default="e13", help="eval set name -> test_images_<name>/"
    )
    ap.add_argument(
        "--template", action="store_true", help="print a manifest template and exit"
    )
    args = ap.parse_args()

    if args.template:
        print(json.dumps(TEMPLATE, indent=2, ensure_ascii=False))
        return
    if not args.collection_dir:
        ap.error("--collection-dir required (or use --template)")

    coll = Path(args.collection_dir).expanduser().resolve()
    meals = load_manifests(coll)
    if not meals:
        raise SystemExit(f"no manifests found in {coll}")

    # validate ALL first (no partial/fallback ingest)
    all_errs: List[str] = []
    for i, m in enumerate(meals, 1):
        all_errs += validate(m, i)
    if all_errs:
        raise SystemExit("VALIDATION FAILED (nothing written):\n" + "\n".join(all_errs))

    out_root = PROJECT_ROOT / f"test_images_{args.out_name}"
    img_dst = out_root / "images"
    lab_dst = out_root / "images_label_with_nutrition"
    img_dst.mkdir(parents=True, exist_ok=True)
    lab_dst.mkdir(parents=True, exist_ok=True)

    coverage: Dict[Tuple[str, str], int] = {}
    cals: List[float] = []
    for i, meal in enumerate(meals, 1):
        src_img = (coll / meal["image"]).resolve()
        if not src_img.exists():
            raise SystemExit(f"image not found: {src_img}")
        label, tot_cal, _ = to_label(meal)
        shutil.copy(src_img, img_dst / f"test_food{i}.jpg")
        (lab_dst / f"test_food{i:02d}.json").write_text(
            json.dumps(label, ensure_ascii=False), encoding="utf-8"
        )
        st = label["stratum"]
        coverage[(st["angle"], st["size_bucket"])] = (
            coverage.get((st["angle"], st["size_bucket"]), 0) + 1
        )
        cals.append(tot_cal)

    split = APP_DIR / "evals" / "splits" / f"{args.out_name}_all.txt"
    split.write_text(
        "\n".join(str(i) for i in range(1, len(meals) + 1)) + "\n", encoding="utf-8"
    )

    print(f"ingested {len(meals)} meals -> {out_root}")
    print(
        f"GT calories: min {min(cals):.0f} max {max(cals):.0f} median {median(cals):.0f}"
    )
    print(f"split: {split}")
    print(
        "\nSTRATUM COVERAGE (angle x size_bucket) — fill thin cells (E13 §6 edge cells ~30-90+):"
    )
    for (angle, sb), n in sorted(coverage.items()):
        flag = "  <-- THIN" if n < 30 else ""
        print(f"  {angle:<10} {sb:<10} n={n}{flag}")


if __name__ == "__main__":
    main()
