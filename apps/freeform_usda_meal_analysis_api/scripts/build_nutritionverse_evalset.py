#!/usr/bin/env python
"""Build a harness-compatible eval set from NutritionVerse-Real.

NutritionVerse-Real is distributed through Kaggle as food images plus physically
measured dish/component weights and nutrition values. This converter does not
download Kaggle data; it expects the dataset zip to have already been extracted
under data/nutritionverse_real/.

IMPORTANT — the image filename `dish_<N>` is NOT the same numbering as the
metadata CSV `dish_id`. They are independent id spaces (verified: image dish_2 is
an apple, metadata dish_id 2 is bread+lobster). The dataset ships no crosswalk, so
joining by id == id produces ~40% WRONG calorie GT. The only reliable key is
CONTENT: each image's COCO ingredient multiset is matched to the metadata dish
with the same multiset, and only UNIQUE matches are kept (ambiguous / no-match are
dropped). See evals/lessons/20260603_nutritionverse_real_broken_id_mapping.md.

Output schema matches run_pdca_batch_eval.py:
  test_images_nvreal/images/test_food{N}.jpg
  test_images_nvreal/images_label_with_nutrition/test_food{NN}.json
  test_images_nvreal/manifest.json

Each matched dish keeps one representative image (first sorted jpg filename).
"""

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "data/nutritionverse_real"
DEFAULT_OUT_DIR = PROJECT_ROOT / "test_images_nvreal"
METADATA_CSV = "nutritionverse_dish_metadata3.csv"
MANUAL_REL = "nutritionverse-manual/nutritionverse-manual"
IMAGES_REL = f"{MANUAL_REL}/images"
SPLITS_REL = f"{MANUAL_REL}/updated-manual-dataset-splits.csv"
COCO_REL = f"{MANUAL_REL}/images/_annotations.coco.json"
IMAGE_DISH_RE = re.compile(r"^dish_(\d+)_")
NUMERIC_SUFFIX_RE = re.compile(r"-\d+$")
ITEM_SLOTS = range(1, 8)


def _float(value: Optional[str], default: float = 0.0) -> float:
    if value is None:
        return default
    value = str(value).strip()
    if not value:
        return default
    return float(value)


def _round(value: float, ndigits: int) -> float:
    return round(float(value), ndigits)


def normalize_name(name: str) -> str:
    """Canonical ingredient name for cross-source content matching.

    Strips a trailing numeric instance suffix (`...-sushi-roll-1` -> `...-sushi-roll`)
    so COCO category names and metadata ingredient names line up.
    """
    return NUMERIC_SUFFIX_RE.sub("", name.strip().lower())


def parse_dish_metadata(csv_path: Path) -> Dict[str, Dict[str, Any]]:
    dishes: Dict[str, Dict[str, Any]] = {}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dish_id = str(row["dish_id"]).strip()
            ingredients: List[Dict[str, Any]] = []
            for i in ITEM_SLOTS:
                name = (row.get(f"food_item_type_{i}") or "").strip()
                grams = _float(row.get(f"food_weight_g_{i}"))
                if not name or grams <= 0:
                    continue
                ingredients.append(
                    {
                        "name": name,
                        "weight_g": _round(grams, 1),
                        "calorie": _round(_float(row.get(f"calories(kCal)_{i}")), 2),
                        "fat_g": _round(_float(row.get(f"fat(g)_{i}")), 3),
                        "carbs_g": _round(_float(row.get(f"carbohydrates(g)_{i}")), 3),
                        "protein_g": _round(_float(row.get(f"protein(g)_{i}")), 3),
                    }
                )
            if ingredients:
                dishes[dish_id] = {
                    "total": {
                        "weight_g": _round(_float(row.get("total_food_weight")), 1),
                        "calories": _round(_float(row.get("total_calories")), 2),
                        "fat_g": _round(_float(row.get("total_fats")), 3),
                        "carbs_g": _round(_float(row.get("total_carbohydrates")), 3),
                        "protein_g": _round(_float(row.get("total_protein")), 3),
                    },
                    "ingredients": ingredients,
                }
    return dishes


def metadata_content_index(
    dishes: Dict[str, Dict[str, Any]],
) -> Dict[frozenset, List[str]]:
    """Map a normalized ingredient multiset -> list of dish_ids carrying it."""
    index: Dict[frozenset, List[str]] = defaultdict(list)
    for dish_id, dish in dishes.items():
        multiset = Counter(normalize_name(ing["name"]) for ing in dish["ingredients"])
        index[frozenset(multiset.items())].append(dish_id)
    return index


def parse_image_map(images_dir: Path) -> Dict[str, List[Path]]:
    by_dish: Dict[str, List[Path]] = defaultdict(list)
    for path in sorted(images_dir.glob("*.jpg")):
        match = IMAGE_DISH_RE.match(path.name)
        if match:
            by_dish[match.group(1)].append(path)
    return by_dish


def parse_coco_content(coco_path: Path) -> Dict[str, Counter]:
    """image dish_N -> normalized ingredient multiset.

    COCO counts visible instances per category per image; angles of the same dish
    can see different counts (occlusion), so per category we take the MAX count
    across that dish's images as the best estimate of the true instance count.
    """
    coco = json.loads(coco_path.read_text(encoding="utf-8"))
    cat_name = {c["id"]: c["name"] for c in coco["categories"]}
    file_of_image = {im["id"]: im["file_name"] for im in coco["images"]}

    per_image: Dict[int, Counter] = defaultdict(Counter)
    for ann in coco["annotations"]:
        per_image[ann["image_id"]][cat_name.get(ann["category_id"], "")] += 1

    images_of_dish: Dict[str, List[int]] = defaultdict(list)
    for image_id, file_name in file_of_image.items():
        match = IMAGE_DISH_RE.match(file_name)
        if match:
            images_of_dish[match.group(1)].append(image_id)

    content: Dict[str, Counter] = {}
    for dish_n, image_ids in images_of_dish.items():
        normalized_per_image: List[Counter] = []
        for image_id in image_ids:
            counter: Counter = Counter()
            for raw_name, count in per_image.get(image_id, {}).items():
                if raw_name:
                    counter[normalize_name(raw_name)] += count
            normalized_per_image.append(counter)
        categories = set().union(*[set(c) for c in normalized_per_image]) or set()
        content[dish_n] = Counter(
            {
                cat: max(c.get(cat, 0) for c in normalized_per_image)
                for cat in categories
            }
        )
    return content


def parse_splits(splits_path: Path) -> Dict[str, str]:
    if not splits_path.exists():
        return {}
    with splits_path.open(newline="", encoding="utf-8-sig") as f:
        return {
            row["file_name"]: row["category"]
            for row in csv.DictReader(f)
            if row.get("file_name")
        }


def to_harness_label(dish: Dict[str, Any]) -> Dict[str, Any]:
    ingredients = sorted(dish["ingredients"], key=lambda x: -float(x["weight_g"]))

    def entry(ingredient: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "search_name": ingredient["name"],
            "weight_g": ingredient["weight_g"],
            "nutrition": {
                "calorie": ingredient["calorie"],
                "protein_g": ingredient["protein_g"],
                "fat_g": ingredient["fat_g"],
                "carbs_g": ingredient["carbs_g"],
            },
        }

    return {
        "dishes": [
            {
                "main_food": entry(ingredients[0]),
                "extras": [entry(ingredient) for ingredient in ingredients[1:]],
            }
        ]
    }


def match_images_to_metadata(
    image_content: Dict[str, Counter],
    images_by_dish: Dict[str, List[Path]],
    content_index: Dict[frozenset, List[str]],
) -> Tuple[List[Tuple[str, str]], Dict[str, int]]:
    """Return [(image_dish_N, metadata_dish_id)] for UNIQUE content matches only."""
    matched: List[Tuple[str, str]] = []
    stats = {"unique": 0, "ambiguous": 0, "nomatch": 0, "no_image": 0}
    for dish_n in sorted(image_content, key=int):
        if dish_n not in images_by_dish:
            stats["no_image"] += 1
            continue
        key = frozenset(image_content[dish_n].items())
        candidates = content_index.get(key, [])
        if len(candidates) == 1:
            matched.append((dish_n, candidates[0]))
            stats["unique"] += 1
        elif len(candidates) > 1:
            stats["ambiguous"] += 1
        else:
            stats["nomatch"] += 1
    return matched, stats


def save_jpeg(src: Path, dest: Path) -> None:
    Image.open(src).convert("RGB").save(dest, "JPEG", quality=92)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a NutritionVerse-Real external eval set (content-matched GT)"
    )
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    out_dir = Path(args.out_dir)
    metadata_csv = source_dir / METADATA_CSV
    images_dir = source_dir / IMAGES_REL
    coco_path = source_dir / COCO_REL
    splits_path = source_dir / SPLITS_REL

    for required in (metadata_csv, images_dir, coco_path):
        if not required.exists():
            raise FileNotFoundError(f"missing required input: {required}")

    dishes = parse_dish_metadata(metadata_csv)
    images_by_dish = parse_image_map(images_dir)
    image_content = parse_coco_content(coco_path)
    splits = parse_splits(splits_path)
    content_index = metadata_content_index(dishes)

    matched, stats = match_images_to_metadata(
        image_content, images_by_dish, content_index
    )
    print(
        f"content-match: unique={stats['unique']} ambiguous={stats['ambiguous']} "
        f"nomatch={stats['nomatch']} no_image={stats['no_image']}"
    )
    if args.limit is not None:
        matched = matched[: args.limit]

    image_out = out_dir / "images"
    label_out = out_dir / "images_label_with_nutrition"
    image_out.mkdir(parents=True, exist_ok=True)
    label_out.mkdir(parents=True, exist_ok=True)

    manifest_dishes: List[Dict[str, Any]] = []
    built = 0
    for idx, (dish_n, dish_id) in enumerate(matched, start=1):
        dish = dishes[dish_id]
        source_images = sorted(images_by_dish[dish_n])
        source_image = source_images[0]
        dest_image = image_out / f"test_food{idx}.jpg"
        dest_label = label_out / f"test_food{idx:02d}.json"

        save_jpeg(source_image, dest_image)
        dest_label.write_text(
            json.dumps(to_harness_label(dish), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        manifest_dishes.append(
            {
                "idx": idx,
                "image_dish_n": dish_n,
                "metadata_dish_id": dish_id,
                "matched_content": sorted(image_content[dish_n].elements()),
                "gt_calories": dish["total"]["calories"],
                "gt_protein_g": dish["total"]["protein_g"],
                "gt_fat_g": dish["total"]["fat_g"],
                "gt_carbs_g": dish["total"]["carbs_g"],
                "total_food_weight_g": dish["total"]["weight_g"],
                "n_items": len(dish["ingredients"]),
                "source_image_file": source_image.name,
                "source_image_path": str(source_image.relative_to(PROJECT_ROOT)),
                "source_image_split": splits.get(source_image.name),
                "n_source_images_for_dish": len(source_images),
            }
        )
        built += 1
        if built % 25 == 0:
            print(f"  built {built}/{len(matched)}")

    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "source": "NutritionVerse-Real (Kaggle: nutritionverse/nutritionverse-real)",
                "join_strategy": "COCO ingredient multiset == metadata multiset, unique-only",
                "source_dir": str(source_dir.relative_to(PROJECT_ROOT)),
                "metadata_csv": str(metadata_csv.relative_to(PROJECT_ROOT)),
                "images_dir": str(images_dir.relative_to(PROJECT_ROOT)),
                "coco": str(coco_path.relative_to(PROJECT_ROOT)),
                "representative_image_strategy": "first sorted jpg filename per image dish_N",
                "n": built,
                "match_stats": stats,
                "metadata_dish_count": len(dishes),
                "image_dish_count": len(images_by_dish),
                "dishes": manifest_dishes,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nBuilt {built} content-verified images+labels under {out_dir}")
    print(f"  images: {image_out}")
    print(f"  labels: {label_out}")
    print(f"  manifest: {out_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
