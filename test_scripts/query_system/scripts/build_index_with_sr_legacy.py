# -*- coding: utf-8 -*-
"""
Build FAISS index with Survey + Foundation + SR Legacy USDA data
Expected total: ~13,565 items (Survey 5,432 + Foundation 340 + SR Legacy 7,793)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.index.builder import IndexBuilder


def main():
    """Build index with Survey + Foundation + SR Legacy"""
    print("=" * 80)
    print("USDA Index Builder with SR Legacy")
    print("=" * 80)

    # Paths
    usda_db_path = project_root.parent.parent / "usda_database"
    output_path = project_root / "data"

    survey_json = usda_db_path / "surveyDownload.json"
    foundation_json = usda_db_path / "FoodData_Central_foundation_food_json_2025-04-24 2.json"
    sr_legacy_json = usda_db_path / "FoodData_Central_sr_legacy_food_json_2018-04 2.json"

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

    print(f"\n📂 Data sources:")
    print(f"  - Survey: {survey_json.name} (~5,432 items)")
    print(f"  - Foundation: {foundation_json.name} (~340 items)")
    print(f"  - SR Legacy: {sr_legacy_json.name} (~7,793 items)")
    print(f"  Expected total: ~13,565 items")
    print()

    # Build index
    builder = IndexBuilder(device="cpu")

    # Load data
    print("📥 Loading USDA data...")
    builder.load_usda_data(
        survey_path=str(survey_json),
        foundation_path=str(foundation_json),
        sr_legacy_path=str(sr_legacy_json)
    )

    print(f"\n📊 Building embeddings for {len(builder.items)} items...")
    print("⚠️  This may take 10-15 minutes (2.4x larger than before)...")
    print()

    # Build embeddings
    embeddings_main, embeddings_full = builder.build_embeddings(
        batch_size=32,
        show_progress=True
    )

    # Build indexes
    builder.build_faiss_indexes(embeddings_main, embeddings_full)

    # Save
    builder.save(str(output_path))

    print("\n" + "=" * 80)
    print("✅ Index build with SR Legacy completed!")
    print("=" * 80)
    print(f"\n📊 Final Statistics:")
    print(f"  - Total items indexed: {len(builder.items)}")
    print(f"  - Survey items: {sum(1 for item in builder.items if item['source'] == 'survey')}")
    print(f"  - Foundation items: {sum(1 for item in builder.items if item['source'] == 'foundation')}")
    print(f"  - SR Legacy items: {sum(1 for item in builder.items if item['source'] == 'sr_legacy')}")
    print(f"  - Output directory: {output_path}")
    print()


if __name__ == "__main__":
    main()
