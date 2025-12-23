#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build FAISS index with nutrition data embedded in metadata

This script builds a self-contained FAISS index where nutrition information
is embedded directly in the metadata JSON, eliminating the need for separate
USDA JSON files.

Output:
  - usda_index_full.faiss: FAISS vector index
  - usda_metadata.json: Metadata with nutrition information

Modes:
  - Default: Build full index (embeddings + metadata + portions)
  - --metadata-only: Update only metadata file with portions (no embedding/FAISS rebuild)
"""

import sys
import json
import asyncio
import argparse
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Tuple, Optional


# USDA栄養素ID → 内部キー名のマッピング
NUTRIENT_IDS = {
    1008: "calories",      # Energy (kcal) - Survey/SR Legacy
    2047: "calories",      # Energy (Atwater General Factors) - Foundation
    2048: "calories",      # Energy (Atwater Specific Factors) - Foundation (fallback)
    1003: "protein_g",     # Protein (g)
    1004: "fat_g",         # Total lipid (fat) (g)
    1005: "carbs_g"        # Carbohydrate, by difference (g)
}


def parse_usda_name(description: str) -> Tuple[str, str]:
    """
    Parse USDA food description into main_name and descriptors

    Example: "Milk, whole" -> ("Milk", "whole")
    """
    if ',' not in description:
        return description.strip(), ""

    parts = description.split(',', 1)
    main_name = parts[0].strip()
    descriptors = parts[1].strip() if len(parts) > 1 else ""

    return main_name, descriptors


def extract_nutrition(food_nutrients: List[Dict]) -> Dict[str, float]:
    """
    Extract nutrition data from foodNutrients array

    Returns:
        Dict with keys: calories, protein_g, fat_g, carbs_g
    """
    nutrients = {}

    # カロリーの優先順位: 1008 > 2047 > 2048
    # (1008: Energy kcal, 2047: Atwater General, 2048: Atwater Specific)

    for food_nutrient in food_nutrients:
        nutrient = food_nutrient.get('nutrient', {})
        nutrient_id = nutrient.get('id')

        if nutrient_id in NUTRIENT_IDS:
            amount = food_nutrient.get('amount', 0.0)
            key = NUTRIENT_IDS[nutrient_id]

            # caloriesの場合、既に値があれば優先順位をチェック
            if key == "calories" and "calories" in nutrients:
                # 既存の値より優先順位が高い場合のみ上書き
                # (低いインデックスが高優先)
                continue

            nutrients[key] = round(float(amount), 1)

    # 必要な栄養素が揃っていない場合は0で補完
    required_keys = {"calories", "protein_g", "fat_g", "carbs_g"}
    for key in required_keys:
        if key not in nutrients:
            nutrients[key] = 0.0

    return nutrients


def extract_portions_from_survey(food_data: Dict) -> Optional[List[Dict]]:
    """
    Extract portions from Survey (FNDDS) food data

    Args:
        food_data: Food data from surveyDownload.json

    Returns:
        List of portion dicts or None if no portions
    """
    food_portions = food_data.get('foodPortions', [])

    if not food_portions:
        return None

    portions = []
    for portion in food_portions:
        gram_weight = portion.get('gramWeight', 0)
        description = portion.get('portionDescription', '')

        if gram_weight > 0 and description:
            portions.append({
                "description": description,
                "gram_weight": round(gram_weight, 1)
            })

    return portions if portions else None


def extract_portions_from_foundation(food_data: Dict) -> Optional[List[Dict]]:
    """
    Extract portions from Foundation Food data

    Args:
        food_data: Food data from Foundation Food JSON

    Returns:
        List of portion dicts or None if no portions
    """
    food_portions = food_data.get('foodPortions', [])

    if not food_portions:
        return None

    portions = []
    for portion in food_portions:
        gram_weight = portion.get('gramWeight', 0)
        measure_unit = portion.get('measureUnit', {})
        value = portion.get('value', portion.get('amount', 1))
        unit_name = measure_unit.get('name', 'serving')

        # Build description
        if value and unit_name:
            description = f"{value} {unit_name}"
        else:
            description = unit_name

        if gram_weight > 0 and description:
            portions.append({
                "description": description,
                "gram_weight": round(gram_weight, 1)
            })

    return portions if portions else None


def extract_portions_from_sr_legacy(food_data: Dict) -> Optional[List[Dict]]:
    """
    Extract portions from SR Legacy food data

    Args:
        food_data: Food data from SR Legacy JSON

    Returns:
        List of portion dicts or None if no portions
    """
    food_portions = food_data.get('foodPortions', [])

    if not food_portions:
        return None

    portions = []
    for portion in food_portions:
        gram_weight = portion.get('gramWeight', 0)
        modifier = portion.get('modifier', '')
        amount = portion.get('amount', portion.get('value', 1))

        # Build description
        if amount and modifier:
            description = f"{amount} {modifier}"
        elif modifier:
            description = modifier
        else:
            description = "serving"

        if gram_weight > 0 and description:
            portions.append({
                "description": description,
                "gram_weight": round(gram_weight, 1)
            })

    return portions if portions else None


def load_usda_data_with_nutrition(
    survey_path: str,
    foundation_path: str,
    sr_legacy_path: Optional[str] = None,
    max_items: Optional[int] = None,
    include_portions: bool = True
) -> List[Dict]:
    """
    Load USDA data with nutrition information and portions

    食品の栄養素データ(foodNutrients)が空の場合は除外する

    Args:
        survey_path: Path to surveyDownload.json
        foundation_path: Path to Foundation Foods JSON
        sr_legacy_path: Path to SR Legacy Foods JSON (optional)
        max_items: Maximum number of items (for testing)
        include_portions: Whether to extract portions information (default: True)

    Returns:
        List of food items with nutrition data and portions
    """
    items = []
    skipped_count = 0

    # Load Survey Foods (FNDDS)
    print(f"Loading Survey Foods from {survey_path}...")
    with open(survey_path, 'r', encoding='utf-8') as f:
        survey_data = json.load(f)
        survey_foods = survey_data.get('SurveyFoods', [])

        for item in survey_foods:
            if max_items and len(items) >= max_items:
                break

            description = item.get('description', '')
            if not description:
                continue

            # foodNutrientsが空配列の場合はスキップ
            food_nutrients = item.get('foodNutrients', [])
            if len(food_nutrients) == 0:
                skipped_count += 1
                print(f"  ⚠️  Skipped (no nutrients): {description}")
                continue

            # Parse main_name and descriptors
            main_name, descriptors = parse_usda_name(description)

            # Extract nutrition
            nutrition = extract_nutrition(food_nutrients)

            # Extract portions (if enabled)
            portions = extract_portions_from_survey(item) if include_portions else None

            items.append({
                'id': f"survey_{item.get('fdcId', 'unknown')}",
                'source': 'survey',
                'fdc_id': item.get('fdcId'),
                'food_code': item.get('foodCode'),
                'description': description,
                'main_name': main_name,
                'descriptors': descriptors,
                'nutrition': nutrition,
                'portions': portions
            })

    print(f"✅ Loaded {len(items)} Survey Foods (skipped {skipped_count})")

    # Load Foundation Foods
    if not max_items or len(items) < max_items:
        print(f"Loading Foundation Foods from {foundation_path}...")
        foundation_start = len(items)
        foundation_skipped = 0
        with open(foundation_path, 'r', encoding='utf-8') as f:
            foundation_data = json.load(f)
            foundation_foods = foundation_data.get('FoundationFoods', [])

            for item in foundation_foods:
                if max_items and len(items) >= max_items:
                    break

                description = item.get('description', '')
                if not description:
                    continue

                # foodNutrientsが空配列の場合はスキップ
                food_nutrients = item.get('foodNutrients', [])
                if len(food_nutrients) == 0:
                    foundation_skipped += 1
                    print(f"  ⚠️  Skipped (no nutrients): {description}")
                    continue

                # Parse main_name and descriptors
                main_name, descriptors = parse_usda_name(description)

                # Extract nutrition
                nutrition = extract_nutrition(food_nutrients)

                # Extract portions (if enabled)
                portions = extract_portions_from_foundation(item) if include_portions else None

                items.append({
                    'id': f"foundation_{item.get('fdcId', 'unknown')}",
                    'source': 'foundation',
                    'fdc_id': item.get('fdcId'),
                    'ndb_number': item.get('ndbNumber'),
                    'description': description,
                    'main_name': main_name,
                    'descriptors': descriptors,
                    'nutrition': nutrition,
                    'portions': portions
                })

        print(f"✅ Loaded {len(items) - foundation_start} Foundation Foods (skipped {foundation_skipped})")
        skipped_count += foundation_skipped

    # Load SR Legacy Foods
    if sr_legacy_path and (not max_items or len(items) < max_items):
        print(f"Loading SR Legacy Foods from {sr_legacy_path}...")
        sr_legacy_start = len(items)
        sr_legacy_skipped = 0
        with open(sr_legacy_path, 'r', encoding='utf-8') as f:
            sr_legacy_data = json.load(f)
            sr_legacy_foods = sr_legacy_data.get('SRLegacyFoods', [])

            for item in sr_legacy_foods:
                if max_items and len(items) >= max_items:
                    break

                description = item.get('description', '')
                if not description:
                    continue

                # foodNutrientsが空配列の場合はスキップ
                food_nutrients = item.get('foodNutrients', [])
                if len(food_nutrients) == 0:
                    sr_legacy_skipped += 1
                    print(f"  ⚠️  Skipped (no nutrients): {description}")
                    continue

                # Parse main_name and descriptors
                main_name, descriptors = parse_usda_name(description)

                # Extract nutrition
                nutrition = extract_nutrition(food_nutrients)

                # Extract portions (if enabled)
                portions = extract_portions_from_sr_legacy(item) if include_portions else None

                items.append({
                    'id': f"sr_legacy_{item.get('fdcId', 'unknown')}",
                    'source': 'sr_legacy',
                    'fdc_id': item.get('fdcId'),
                    'ndb_number': item.get('ndbNumber'),
                    'description': description,
                    'main_name': main_name,
                    'descriptors': descriptors,
                    'nutrition': nutrition,
                    'portions': portions
                })

        print(f"✅ Loaded {len(items) - sr_legacy_start} SR Legacy Foods (skipped {sr_legacy_skipped})")
        skipped_count += sr_legacy_skipped

    print(f"📊 Total: {len(items)} food items with nutrition data (total skipped: {skipped_count})")

    return items


async def build_embeddings_with_deepinfra(items: List[Dict]) -> np.ndarray:
    """
    Build embeddings using DeepInfra API (Qwen3-Embedding-8B)
    Processes in batches due to API limitations (max 1024 items per request)

    Args:
        items: List of food items

    Returns:
        Embeddings array (N x D)
    """
    # Import shared service directly
    import sys
    from pathlib import Path
    repo_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(repo_root))

    from shared.services.deepinfra_service import DeepInfraService

    print("\n🔨 Building embeddings with DeepInfra API...")

    # Prepare texts (full description)
    texts = [item['description'] for item in items]

    # Initialize DeepInfra service
    embedding_service = DeepInfraService(model_id="Qwen/Qwen3-Embedding-8B")

    # Process in batches (max 1024 per batch)
    batch_size = 1024
    all_embeddings = []
    
    print(f"📍 Encoding {len(texts)} embeddings in batches of {batch_size}...")
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        print(f"  Batch {batch_num}/{total_batches}: {len(batch)} items (items {i+1}-{i+len(batch)})")
        
        batch_embeddings = await embedding_service.generate_embeddings(batch)
        all_embeddings.extend(batch_embeddings)
        
        print(f"  ✓ Batch {batch_num}/{total_batches} completed")

    # Convert to numpy array
    embeddings_array = np.array(all_embeddings).astype('float32')

    print(f"✅ Embeddings shape: {embeddings_array.shape}")

    return embeddings_array


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """
    Build FAISS index from embeddings

    Args:
        embeddings: Embeddings array (N x D)

    Returns:
        FAISS index
    """
    print("\n🔨 Building FAISS index...")

    # Normalize embeddings for cosine similarity
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

    # Get dimension
    dimension = embeddings.shape[1]

    # Build index
    print(f"Building index (dimension={dimension})...")
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    print(f"✅ Index: {index.ntotal} vectors")

    return index


def save_index_and_metadata(
    index: faiss.IndexFlatIP,
    items: List[Dict],
    output_dir: str
):
    """
    Save FAISS index and metadata to disk

    Args:
        index: FAISS index
        items: Food items with nutrition data
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"\n💾 Saving to {output_dir}...")

    # Save FAISS index
    index_path = output_path / "usda_index_full.faiss"
    faiss.write_index(index, str(index_path))
    print(f"✅ Saved index: {index_path}")

    # Save metadata with nutrition
    metadata_path = output_path / "usda_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    # Calculate metadata size
    metadata_size_mb = metadata_path.stat().st_size / (1024 * 1024)
    print(f"✅ Saved metadata: {metadata_path} ({len(items)} items, {metadata_size_mb:.1f}MB)")

    print("\n✅ All data saved successfully!")




def load_portions_mapping_from_usda(
    survey_path: str,
    foundation_path: str,
    sr_legacy_path: Optional[str] = None
) -> Dict[int, Optional[List[Dict]]]:
    """
    Load portions mapping from original USDA data files

    Args:
        survey_path: Path to surveyDownload.json
        foundation_path: Path to Foundation Foods JSON
        sr_legacy_path: Path to SR Legacy Foods JSON (optional)

    Returns:
        Dict mapping fdc_id to portions list (or None if no portions)
    """
    print("=" * 80)
    print("📂 Loading portions data from original USDA files...")
    print("=" * 80)

    portions_map = {}

    # Load Survey (FNDDS)
    print(f"\n🔍 Loading Survey (FNDDS): {survey_path}")
    if Path(survey_path).exists():
        with open(survey_path, 'r', encoding='utf-8') as f:
            survey_data = json.load(f)
            for food in survey_data.get('SurveyFoods', []):
                fdc_id = food.get('fdcId')
                if fdc_id:
                    portions = extract_portions_from_survey(food)
                    portions_map[fdc_id] = portions
        print(f"   ✅ Loaded {len([v for v in portions_map.values() if v])} foods with portions")
    else:
        print(f"   ⚠️ File not found: {survey_path}")

    # Load Foundation Food
    print(f"\n🔍 Loading Foundation Food: {foundation_path}")
    if Path(foundation_path).exists():
        with open(foundation_path, 'r', encoding='utf-8') as f:
            foundation_data = json.load(f)
            for food in foundation_data.get('FoundationFoods', []):
                fdc_id = food.get('fdcId')
                if fdc_id:
                    portions = extract_portions_from_foundation(food)
                    portions_map[fdc_id] = portions
        print(f"   ✅ Loaded {len([v for v in portions_map.values() if v])} foods with portions (cumulative)")
    else:
        print(f"   ⚠️ File not found: {foundation_path}")

    # Load SR Legacy
    if sr_legacy_path:
        print(f"\n🔍 Loading SR Legacy: {sr_legacy_path}")
        if Path(sr_legacy_path).exists():
            with open(sr_legacy_path, 'r', encoding='utf-8') as f:
                sr_data = json.load(f)
                for food in sr_data.get('SRLegacyFoods', []):
                    fdc_id = food.get('fdcId')
                    if fdc_id:
                        portions = extract_portions_from_sr_legacy(food)
                        portions_map[fdc_id] = portions
            print(f"   ✅ Loaded {len([v for v in portions_map.values() if v])} foods with portions (cumulative)")
        else:
            print(f"   ⚠️ File not found: {sr_legacy_path}")

    total_with_portions = len([v for v in portions_map.values() if v is not None])
    print(f"\n📊 Total foods with portions: {total_with_portions}/{len(portions_map)}")

    return portions_map


async def update_metadata_only(
    survey_path: str,
    foundation_path: str,
    sr_legacy_path: Optional[str],
    metadata_path: Path
):
    """
    Update only metadata file with portions information (no FAISS rebuild)

    Args:
        survey_path: Path to surveyDownload.json
        foundation_path: Path to Foundation Foods JSON
        sr_legacy_path: Path to SR Legacy Foods JSON (optional)
        metadata_path: Path to usda_metadata.json
    """
    print("\n" + "=" * 80)
    print("🔄 METADATA-ONLY UPDATE MODE")
    print("=" * 80)
    print("\nThis mode ONLY updates usda_metadata.json with portions information.")
    print("FAISS index will NOT be modified.\n")

    # Check if metadata file exists
    if not metadata_path.exists():
        print(f"❌ Error: Metadata file not found: {metadata_path}")
        print("   Please run the full build first (without --metadata-only).")
        sys.exit(1)

    # Step 1: Load portions mapping
    portions_map = load_portions_mapping_from_usda(
        survey_path=survey_path,
        foundation_path=foundation_path,
        sr_legacy_path=sr_legacy_path
    )

    if not portions_map:
        print("\n❌ Error: No portion data loaded from original USDA files")
        sys.exit(1)

    # Step 2: Update metadata file
    print("\n" + "=" * 80)
    print("📝 Updating metadata file...")
    print("=" * 80)

    print(f"\n🔍 Loading metadata: {metadata_path}")
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    print(f"   ✅ Loaded {len(metadata)} food items")

    # Update each item with portions
    updated_count = 0
    null_count = 0

    for item in metadata:
        fdc_id = item.get('fdc_id')
        if fdc_id in portions_map:
            item['portions'] = portions_map[fdc_id]
            if portions_map[fdc_id] is not None:
                updated_count += 1
            else:
                null_count += 1
        else:
            item['portions'] = None
            null_count += 1

    # Save updated metadata
    print(f"\n💾 Saving updated metadata...")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"   ✅ Metadata updated successfully!")
    print(f"\n📊 Statistics:")
    print(f"   - Total items: {len(metadata)}")
    print(f"   - With portions: {updated_count} ({updated_count/len(metadata)*100:.1f}%)")
    print(f"   - With null portions: {null_count} ({null_count/len(metadata)*100:.1f}%)")

    print("\n" + "=" * 80)
    print("✅ Metadata-only update completed successfully!")
    print("=" * 80)
    print(f"\n📝 Next steps:")
    print(f"   1. Restart the API to load updated metadata")
    print(f"   2. Test the retrieve endpoint to verify portions field")
    print(f"   3. curl 'http://localhost:8006/api/v1/retrieve?q=chicken&mode=fast&top_k=1'\n")

async def main_async():
    """Main async function"""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Build FAISS index with nutrition data and portions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full build (embeddings + metadata + portions)
  python build_index_with_nutrition.py

  # Metadata-only update (only update portions, no FAISS rebuild)
  python build_index_with_nutrition.py --metadata-only
        """
    )
    parser.add_argument(
        '--metadata-only',
        action='store_true',
        help='Update only metadata file with portions (no FAISS index rebuild)'
    )

    args = parser.parse_args()

    # Paths
    api_dir = Path(__file__).parent.parent
    data_dir = api_dir / "data"
    output_dir = data_dir / "faiss"

    # Use usda_database directory for original USDA data
    project_root = Path(__file__).parent.parent.parent.parent
    usda_database_dir = project_root / "usda_database"

    survey_json = usda_database_dir / "surveyDownload.json"
    foundation_json = usda_database_dir / "FoodData_Central_foundation_food_json_2025-04-24 2.json"
    sr_legacy_json = usda_database_dir / "FoodData_Central_sr_legacy_food_json_2018-04 2.json"
    metadata_path = output_dir / "usda_metadata.json"

    # Check files exist
    if not survey_json.exists():
        print(f"❌ Survey file not found: {survey_json}")
        sys.exit(1)
    if not foundation_json.exists():
        print(f"❌ Foundation file not found: {foundation_json}")
        sys.exit(1)
    if not sr_legacy_json.exists():
        print(f"❌ SR Legacy file not found: {sr_legacy_json}")
        sys.exit(1)

    # Metadata-only mode
    if args.metadata_only:
        await update_metadata_only(
            survey_path=str(survey_json),
            foundation_path=str(foundation_json),
            sr_legacy_path=str(sr_legacy_json),
            metadata_path=metadata_path
        )
        return

    # Full build mode
    print("=" * 80)
    print("USDA Index Builder with Nutrition Data")
    print("=" * 80)

    print(f"\n📂 Data sources:")
    print(f"  - Survey: {survey_json.name}")
    print(f"  - Foundation: {foundation_json.name}")
    print(f"  - SR Legacy: {sr_legacy_json.name}")
    print(f"\n📂 Output: {output_dir}")
    print()

    # Step 1: Load data with nutrition and portions
    items = load_usda_data_with_nutrition(
        survey_path=str(survey_json),
        foundation_path=str(foundation_json),
        sr_legacy_path=str(sr_legacy_json),
        include_portions=True  # Always include portions in full build
    )

    # Step 2: Build embeddings
    embeddings = await build_embeddings_with_deepinfra(items)

    # Step 3: Build FAISS index
    index = build_faiss_index(embeddings)

    # Step 4: Save
    save_index_and_metadata(index, items, str(output_dir))

    print("\n" + "=" * 80)
    print("✅ Index building completed!")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  - Total items: {len(items)}")
    print(f"  - Index vectors: {index.ntotal}")
    print(f"  - Survey items: {sum(1 for item in items if item['source'] == 'survey')}")
    print(f"  - Foundation items: {sum(1 for item in items if item['source'] == 'foundation')}")
    print(f"  - SR Legacy items: {sum(1 for item in items if item['source'] == 'sr_legacy')}")
    print(f"  - With portions: {sum(1 for item in items if item.get('portions'))}")
    print(f"  - Output: {output_dir}")
    print()
    print("⚠️  Next steps:")
    print("  1. Update nutrition_service.py to use metadata.json")
    print("  2. Test the API with the new index")
    print("  3. Delete apps/freeform_usda_meal_analysis_api/data/usda_json/ directory")
    print()


def main():
    """Entry point"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
