# -*- coding: utf-8 -*-
"""
Build FAISS index with small subset (for testing)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.index.builder import IndexBuilder


def main():
    """Build index with first 100 items"""
    print("=" * 60)
    print("USDA Index Builder (Small Test - 100 items)")
    print("=" * 60)

    # Paths
    usda_db_path = project_root.parent.parent / "usda_database"
    output_path = project_root / "data"

    survey_json = usda_db_path / "surveyDownload.json"
    foundation_json = usda_db_path / "FoodData_Central_foundation_food_json_2025-04-24 2.json"

    # Check files exist
    if not survey_json.exists():
        print(f"❌ Survey file not found: {survey_json}")
        sys.exit(1)
    if not foundation_json.exists():
        print(f"❌ Foundation file not found: {foundation_json}")
        sys.exit(1)

    # Build index
    builder = IndexBuilder(device="cpu")

    # Load data
    builder.load_usda_data(
        survey_path=str(survey_json),
        foundation_path=str(foundation_json)
    )

    # Take only first 100 items for testing
    print(f"\n⚠️  Limiting to first 100 items for testing")
    builder.items = builder.items[:100]

    # Build embeddings
    embeddings_main, embeddings_full = builder.build_embeddings(
        batch_size=32,
        show_progress=False  # Disable progress bar for background execution
    )

    # Build indexes
    builder.build_faiss_indexes(embeddings_main, embeddings_full)

    # Save
    builder.save(str(output_path))

    print("\n" + "=" * 60)
    print("✅ Small test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
