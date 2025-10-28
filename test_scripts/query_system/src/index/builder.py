# -*- coding: utf-8 -*-
"""
FAISS index builder module (spec3.md two-stream approach)

Builds two FAISS indexes:
- index_main: main_name only embeddings
- index_full: main_name + descriptors embeddings
"""

import json
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from tqdm import tqdm

from ..models.embedding import EmbeddingModel
from ..preprocessing.text_normalizer import (
    parse_usda_name,
    build_main_only_text,
    build_full_text,
    normalize_text
)


class IndexBuilder:
    """
    FAISS index builder for USDA food database

    Builds two indexes following spec3.md design:
    - main_only: For preventing main name confusion
    - full: For semantic neighborhood consideration
    """

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        device: str = "cpu"
    ):
        """
        Args:
            embedding_model: Pre-initialized embedding model (optional)
            device: Device for model ("cpu" or "cuda")
        """
        self.embedding_model = embedding_model or EmbeddingModel(device=device)
        self.items = []  # List of food items with metadata
        self.index_main = None  # FAISS index for main_name embeddings
        self.index_full = None  # FAISS index for full embeddings

    def load_usda_data(
        self,
        survey_path: str,
        foundation_path: str,
        sr_legacy_path: Optional[str] = None,
        max_items: Optional[int] = None
    ) -> List[Dict]:
        """
        Load USDA data from Survey, Foundation, and optionally SR Legacy JSON files

        Args:
            survey_path: Path to surveyDownload.json (FNDDS)
            foundation_path: Path to Foundation Foods JSON
            sr_legacy_path: Path to SR Legacy Foods JSON (optional)
            max_items: Maximum number of items to load (for testing, default: None = all)

        Returns:
            List of parsed food items
        """
        items = []

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

                # Parse main_name and descriptors
                main_name, descriptors = parse_usda_name(description)

                items.append({
                    'id': f"survey_{item.get('fdcId', 'unknown')}",
                    'source': 'survey',
                    'fdc_id': item.get('fdcId'),
                    'food_code': item.get('foodCode'),
                    'description': description,
                    'main_name': main_name,
                    'descriptors': descriptors
                })

        print(f"✅ Loaded {len(items)} Survey Foods")

        # Load Foundation Foods (only if not yet reached max_items)
        if not max_items or len(items) < max_items:
            print(f"Loading Foundation Foods from {foundation_path}...")
            foundation_start = len(items)
            with open(foundation_path, 'r', encoding='utf-8') as f:
                foundation_data = json.load(f)
                foundation_foods = foundation_data.get('FoundationFoods', [])

                for item in foundation_foods:
                    if max_items and len(items) >= max_items:
                        break

                    description = item.get('description', '')
                    if not description:
                        continue

                    # Parse main_name and descriptors
                    main_name, descriptors = parse_usda_name(description)

                    items.append({
                        'id': f"foundation_{item.get('fdcId', 'unknown')}",
                        'source': 'foundation',
                        'fdc_id': item.get('fdcId'),
                        'ndb_number': item.get('ndbNumber'),
                        'description': description,
                        'main_name': main_name,
                        'descriptors': descriptors
                    })

            print(f"✅ Loaded {len(items) - foundation_start} Foundation Foods")

        # Load SR Legacy Foods (only if provided and not yet reached max_items)
        if sr_legacy_path and (not max_items or len(items) < max_items):
            print(f"Loading SR Legacy Foods from {sr_legacy_path}...")
            sr_legacy_start = len(items)
            with open(sr_legacy_path, 'r', encoding='utf-8') as f:
                sr_legacy_data = json.load(f)
                sr_legacy_foods = sr_legacy_data.get('SRLegacyFoods', [])

                for item in sr_legacy_foods:
                    if max_items and len(items) >= max_items:
                        break

                    description = item.get('description', '')
                    if not description:
                        continue

                    # Parse main_name and descriptors
                    main_name, descriptors = parse_usda_name(description)

                    items.append({
                        'id': f"sr_legacy_{item.get('fdcId', 'unknown')}",
                        'source': 'sr_legacy',
                        'fdc_id': item.get('fdcId'),
                        'ndb_number': item.get('ndbNumber'),
                        'description': description,
                        'main_name': main_name,
                        'descriptors': descriptors
                    })

            print(f"✅ Loaded {len(items) - sr_legacy_start} SR Legacy Foods")

        print(f"📊 Total: {len(items)} food items")

        self.items = items
        return items

    def build_embeddings(
        self,
        batch_size: int = 32,
        show_progress: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build two-stream embeddings for all items

        Args:
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            (embeddings_main, embeddings_full) tuple
        """
        if not self.items:
            raise ValueError("No items loaded. Call load_usda_data() first.")

        print("\n🔨 Building two-stream embeddings...")

        # Prepare texts
        texts_main = []
        texts_full = []

        for item in self.items:
            main_name = item['main_name']
            descriptors = item['descriptors']

            # Build and normalize texts
            text_main = normalize_text(build_main_only_text(main_name))
            text_full = normalize_text(build_full_text(main_name, descriptors))

            texts_main.append(text_main)
            texts_full.append(text_full)

        # Encode main_only embeddings
        print("\n📍 Encoding main_only embeddings...")
        embeddings_main = self.embedding_model.encode(
            texts_main,
            batch_size=batch_size,
            show_progress_bar=show_progress
        )

        # Encode full embeddings
        print("\n📍 Encoding full embeddings...")
        embeddings_full = self.embedding_model.encode(
            texts_full,
            batch_size=batch_size,
            show_progress_bar=show_progress
        )

        print(f"✅ Embeddings shape: {embeddings_main.shape}")

        return embeddings_main, embeddings_full

    def build_faiss_indexes(
        self,
        embeddings_main: np.ndarray,
        embeddings_full: np.ndarray
    ) -> Tuple[faiss.IndexFlatIP, faiss.IndexFlatIP]:
        """
        Build FAISS indexes from embeddings

        Args:
            embeddings_main: Main-only embeddings (N x D)
            embeddings_full: Full embeddings (N x D)

        Returns:
            (index_main, index_full) tuple
        """
        print("\n🔨 Building FAISS indexes...")

        # Ensure embeddings are normalized (for cosine similarity via inner product)
        embeddings_main = embeddings_main / np.linalg.norm(
            embeddings_main, axis=1, keepdims=True
        )
        embeddings_full = embeddings_full / np.linalg.norm(
            embeddings_full, axis=1, keepdims=True
        )

        # Get dimension
        dimension = embeddings_main.shape[1]

        # Build main_only index
        print(f"Building main_only index (dimension={dimension})...")
        index_main = faiss.IndexFlatIP(dimension)
        index_main.add(embeddings_main)
        print(f"✅ Main index: {index_main.ntotal} vectors")

        # Build full index
        print(f"Building full index (dimension={dimension})...")
        index_full = faiss.IndexFlatIP(dimension)
        index_full.add(embeddings_full)
        print(f"✅ Full index: {index_full.ntotal} vectors")

        self.index_main = index_main
        self.index_full = index_full

        return index_main, index_full

    def save(
        self,
        output_dir: str,
        index_main_name: str = "usda_index_main.faiss",
        index_full_name: str = "usda_index_full.faiss",
        metadata_name: str = "usda_metadata.json"
    ):
        """
        Save indexes and metadata to disk

        Args:
            output_dir: Output directory
            index_main_name: Main index filename
            index_full_name: Full index filename
            metadata_name: Metadata filename
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"\n💾 Saving to {output_dir}...")

        # Save FAISS indexes
        if self.index_main is not None:
            main_path = output_path / index_main_name
            faiss.write_index(self.index_main, str(main_path))
            print(f"✅ Saved main index: {main_path}")

        if self.index_full is not None:
            full_path = output_path / index_full_name
            faiss.write_index(self.index_full, str(full_path))
            print(f"✅ Saved full index: {full_path}")

        # Save metadata
        metadata_path = output_path / metadata_name
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved metadata: {metadata_path} ({len(self.items)} items)")

        print("\n✅ All data saved successfully!")

    def build_all(
        self,
        survey_path: str,
        foundation_path: str,
        output_dir: str,
        sr_legacy_path: Optional[str] = None,
        batch_size: int = 32,
        show_progress: bool = True
    ):
        """
        Complete pipeline: load data → build embeddings → build indexes → save

        Args:
            survey_path: Path to surveyDownload.json
            foundation_path: Path to Foundation Foods JSON
            output_dir: Output directory
            sr_legacy_path: Path to SR Legacy Foods JSON (optional)
            batch_size: Batch size for encoding
            show_progress: Show progress bar
        """
        print("=" * 60)
        print("USDA Food Database Index Builder (spec3.md)")
        print("=" * 60)

        # Step 1: Load data
        self.load_usda_data(survey_path, foundation_path, sr_legacy_path)

        # Step 2: Build embeddings
        embeddings_main, embeddings_full = self.build_embeddings(
            batch_size=batch_size,
            show_progress=show_progress
        )

        # Step 3: Build FAISS indexes
        self.build_faiss_indexes(embeddings_main, embeddings_full)

        # Step 4: Save
        self.save(output_dir)

        print("\n" + "=" * 60)
        print("✅ Index building completed!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  - Total items: {len(self.items)}")
        print(f"  - Main index vectors: {self.index_main.ntotal}")
        print(f"  - Full index vectors: {self.index_full.ntotal}")
        print(f"  - Output directory: {output_dir}")


def main():
    """Example usage"""
    import sys
    from pathlib import Path

    # Project paths
    project_root = Path(__file__).parent.parent.parent.parent.parent
    usda_db_path = project_root / "usda_database"
    output_path = Path(__file__).parent.parent.parent / "data"

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
        print(f"⚠️  SR Legacy file not found: {sr_legacy_json} (skipping)")
        sr_legacy_json = None

    # Build index
    builder = IndexBuilder(device="cpu")
    builder.build_all(
        survey_path=str(survey_json),
        foundation_path=str(foundation_json),
        sr_legacy_path=str(sr_legacy_json) if sr_legacy_json else None,
        output_dir=str(output_path),
        batch_size=32,
        show_progress=True
    )


if __name__ == "__main__":
    main()
