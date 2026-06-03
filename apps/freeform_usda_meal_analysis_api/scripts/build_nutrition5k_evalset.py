#!/usr/bin/env python
"""Build an EXTERNAL, independent-ground-truth calorie eval set from Nutrition5k.

Nutrition5k (Google Research, CVPR 2021, CC BY 4.0) provides ~5k real cafeteria
dishes with PHYSICALLY-MEASURED total mass/calories/macros + per-ingredient masses,
and an overhead RGB photo per dish. The GT is weighed-mass x USDA per-gram lookup —
fully independent of any VLM, so it is NOT circular (unlike LLM-generated labels).

This converter pulls the overhead-RGB subset anonymously via gsutil and writes the
harness's exact label schema so `run_pdca_batch_eval.py --images-dir/--labels-dir`
can evaluate gemini-3.1-pro vs gemini-3-flash on independent calorie GT at N>>50, and
so `fit_calorie_calibration.py` can fit/validate the calibration on a TRULY EXTERNAL
held-out set (disjoint from the frozen-50) — the prerequisite the repo already requires.

CAVEAT (documented): Nutrition5k is Google-cafeteria Western-plated food, so this widens
the calorie check (independent GT, 70x N) but does NOT prove cross-cuisine generalization.

Usage:
  python -m apps.freeform_usda_meal_analysis_api.scripts.build_nutrition5k_evalset \
    --limit 200 --out-dir test_images_n5k --seed 7
Then evaluate:
  python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval --config <cfg> \
    --api-url http://localhost:8006 --images-dir test_images_n5k/images \
    --labels-dir test_images_n5k/images_label_with_nutrition --limit 200 --no-use-vlm-cache
"""

import argparse
import json
import random
import subprocess
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GSUTIL = "/Users/odasoya/google-cloud-sdk/bin/gsutil"
BUCKET = "gs://nutrition5k_dataset/nutrition5k_dataset"
OVERHEAD = f"{BUCKET}/imagery/realsense_overhead"
META_DIR = (
    PROJECT_ROOT / "apps/freeform_usda_meal_analysis_api/data/nutrition5k/metadata"
)


def parse_dish_metadata(csv_path: Path) -> Dict[str, Dict]:
    """Nutrition5k row: dish_id, total_kcal, total_mass, total_fat, total_carb,
    total_protein, then repeating [ingr_id, name, grams, kcal, fat, carb, protein]."""
    dishes: Dict[str, Dict] = {}
    for line in csv_path.read_text(encoding="utf-8").splitlines():
        parts = line.split(",")
        if len(parts) < 6 or not parts[0].startswith("dish_"):
            continue
        dish_id = parts[0]
        try:
            total = {
                "calories": float(parts[1]),
                "fat": float(parts[3]),
                "carbs": float(parts[4]),
                "protein": float(parts[5]),
            }
        except ValueError:
            continue
        ingredients: List[Dict] = []
        rest = parts[6:]
        # 7 fields per ingredient: id, name, grams, kcal, fat, carb, protein
        for i in range(0, len(rest) - 6, 7):
            name = rest[i + 1].strip()
            try:
                grams = float(rest[i + 2])
                kcal = float(rest[i + 3])
                fat = float(rest[i + 4])
                carb = float(rest[i + 5])
                protein = float(rest[i + 6])
            except (ValueError, IndexError):
                continue
            if name and grams > 0:
                ingredients.append(
                    {
                        "name": name,
                        "weight_g": round(grams, 1),
                        "calorie": round(kcal, 1),
                        "fat_g": round(fat, 2),
                        "carbs_g": round(carb, 2),
                        "protein_g": round(protein, 2),
                    }
                )
        if ingredients:
            dishes[dish_id] = {"total": total, "ingredients": ingredients}
    return dishes


def to_harness_label(dish: Dict) -> Dict:
    """Map a Nutrition5k dish to the harness label schema (dishes/main_food/extras with
    nutrition.calorie). main_food = largest-mass ingredient; extras = the rest."""
    ings = sorted(dish["ingredients"], key=lambda x: -x["weight_g"])

    def entry(ing: Dict) -> Dict:
        return {
            "search_name": ing["name"],
            "weight_g": ing["weight_g"],
            "nutrition": {
                "calorie": ing["calorie"],
                "protein_g": ing["protein_g"],
                "fat_g": ing["fat_g"],
                "carbs_g": ing["carbs_g"],
            },
        }

    return {
        "dishes": [
            {"main_food": entry(ings[0]), "extras": [entry(i) for i in ings[1:]]}
        ]
    }


def list_overhead_dishes() -> List[str]:
    out = subprocess.run(
        [GSUTIL, "ls", f"{OVERHEAD}/"], capture_output=True, text=True, timeout=180
    )
    ids = []
    for line in out.stdout.splitlines():
        line = line.strip().rstrip("/")
        if "/dish_" in line:
            ids.append(line.rsplit("/", 1)[-1])
    return ids


def download_rgb(dish_id: str, dest: Path) -> bool:
    r = subprocess.run(
        [GSUTIL, "-q", "cp", f"{OVERHEAD}/{dish_id}/rgb.png", str(dest)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return r.returncode == 0 and dest.exists()


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a Nutrition5k external eval set")
    ap.add_argument("--limit", type=int, default=200, help="Number of dishes to build")
    ap.add_argument("--out-dir", default="test_images_n5k")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument(
        "--min-ingredients", type=int, default=1, help="Skip dishes with fewer items"
    )
    args = ap.parse_args()

    META_DIR.mkdir(parents=True, exist_ok=True)
    meta: Dict[str, Dict] = {}
    for csv in ("dish_metadata_cafe1.csv", "dish_metadata_cafe2.csv"):
        p = META_DIR / csv
        if not p.exists():
            print(f"pulling {csv} from Nutrition5k bucket...")
            subprocess.run(
                [GSUTIL, "-q", "cp", f"{BUCKET}/metadata/{csv}", str(p)],
                check=False,
                timeout=120,
            )
        if p.exists():
            meta.update(parse_dish_metadata(p))
    if not meta:
        raise RuntimeError(f"No metadata under {META_DIR} and gsutil pull failed")
    print(f"parsed {len(meta)} dishes from metadata")

    print("listing overhead-RGB dishes (gsutil)...")
    overhead = set(list_overhead_dishes())
    print(f"  {len(overhead)} dishes have an overhead rgb.png")

    usable = [
        d
        for d in meta
        if d in overhead and len(meta[d]["ingredients"]) >= args.min_ingredients
    ]
    random.seed(args.seed)
    random.shuffle(usable)
    selected = usable[: args.limit]
    print(f"selected {len(selected)} dishes (limit {args.limit})")

    out = PROJECT_ROOT / args.out_dir
    img_dir = out / "images"
    lbl_dir = out / "images_label_with_nutrition"
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    manifest: List[Dict] = []

    built = 0
    for dish_id in selected:
        idx = built + 1
        jpg = img_dir / f"test_food{idx}.jpg"
        png_tmp = img_dir / f"_{dish_id}.png"
        if not download_rgb(dish_id, png_tmp):
            print(f"  [skip] {dish_id}: rgb.png download failed")
            continue
        # Convert png -> jpg (the harness/pipeline expects jpg; use PIL)
        try:
            from PIL import Image

            Image.open(png_tmp).convert("RGB").save(jpg, "JPEG", quality=92)
        except Exception as e:  # noqa: BLE001
            print(f"  [skip] {dish_id}: jpg convert failed: {e}")
            png_tmp.unlink(missing_ok=True)
            continue
        png_tmp.unlink(missing_ok=True)
        label = to_harness_label(meta[dish_id])
        (lbl_dir / f"test_food{idx:02d}.json").write_text(
            json.dumps(label, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        manifest.append(
            {
                "idx": idx,
                "dish_id": dish_id,
                "gt_calories": meta[dish_id]["total"]["calories"],
                "n_items": len(meta[dish_id]["ingredients"]),
            }
        )
        built += 1
        if built % 25 == 0:
            print(f"  built {built}/{len(selected)}")

    (out / "manifest.json").write_text(
        json.dumps(
            {
                "source": "Nutrition5k (CC BY 4.0), overhead RGB subset",
                "seed": args.seed,
                "n": built,
                "dishes": manifest,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nBuilt {built} images+labels under {out}")
    print(
        f"  images: {img_dir}\n  labels: {lbl_dir}\n  manifest: {out / 'manifest.json'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
