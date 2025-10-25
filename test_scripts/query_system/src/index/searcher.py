# -*- coding: utf-8 -*-
"""
FAISS index searcher module (spec3.md two-stream approach)

Implements two-stream weighted search:
- Search main_only index with weight 0.7
- Search full index with weight 0.3
- Combine scores and return Top-K candidates
"""

import json
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from ..models.embedding import EmbeddingModel
from ..preprocessing.text_normalizer import (
    parse_usda_name,
    build_main_only_text,
    build_full_text,
    normalize_text
)


class IndexSearcher:
    """
    FAISS index searcher for USDA food database

    Implements spec3.md two-stream weighted search:
    S_emb = 0.7 * cosine(Q_main, E_main) + 0.3 * cosine(Q_full, E_full)
    """

    def __init__(
        self,
        index_dir: str,
        embedding_model: Optional[EmbeddingModel] = None,
        device: str = "cpu",
        weight_main: float = 0.7,
        weight_full: float = 0.3
    ):
        """
        Args:
            index_dir: Directory containing FAISS indexes and metadata
            embedding_model: Pre-initialized embedding model (optional)
            device: Device for model ("cpu" or "cuda")
            weight_main: Weight for main_only score (default: 0.7)
            weight_full: Weight for full score (default: 0.3)
        """
        self.index_dir = Path(index_dir)
        self.embedding_model = embedding_model or EmbeddingModel(device=device)
        self.weight_main = weight_main
        self.weight_full = weight_full

        # Load indexes and metadata
        self._load_indexes()
        self._load_metadata()

    def _load_indexes(self):
        """Load FAISS indexes from disk"""
        print(f"Loading FAISS indexes from {self.index_dir}...")

        # Load main_only index
        main_path = self.index_dir / "usda_index_main.faiss"
        if not main_path.exists():
            raise FileNotFoundError(f"Main index not found: {main_path}")
        self.index_main = faiss.read_index(str(main_path))
        print(f"✅ Loaded main index: {self.index_main.ntotal} vectors")

        # Load full index
        full_path = self.index_dir / "usda_index_full.faiss"
        if not full_path.exists():
            raise FileNotFoundError(f"Full index not found: {full_path}")
        self.index_full = faiss.read_index(str(full_path))
        print(f"✅ Loaded full index: {self.index_full.ntotal} vectors")

    def _load_metadata(self):
        """Load metadata from disk"""
        metadata_path = self.index_dir / "usda_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_path}")

        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.items = json.load(f)
        print(f"✅ Loaded metadata: {len(self.items)} items")

    def search(
        self,
        query_main: str,
        query_descriptors: str = "",
        top_k: int = 10
    ) -> List[Dict]:
        """
        Search for food items using two-stream weighted approach

        Args:
            query_main: Main food name (e.g., "chicken breast")
            query_descriptors: Optional descriptors (e.g., "grilled, boneless")
            top_k: Number of candidates to return

        Returns:
            List of top-K candidates with metadata and scores
        """
        # Build query texts
        text_main = normalize_text(build_main_only_text(query_main))
        text_full = normalize_text(build_full_text(query_main, query_descriptors))

        # Encode queries
        emb_main = self.embedding_model.encode(text_main, batch_size=1, show_progress_bar=False)
        emb_full = self.embedding_model.encode(text_full, batch_size=1, show_progress_bar=False)

        # Normalize embeddings (for cosine similarity via inner product)
        emb_main = emb_main / np.linalg.norm(emb_main, axis=1, keepdims=True)
        emb_full = emb_full / np.linalg.norm(emb_full, axis=1, keepdims=True)

        # Search both indexes
        # Note: We retrieve more candidates (top_k * 2) to ensure good coverage after merging
        k_search = min(top_k * 2, self.index_main.ntotal)

        scores_main, indices_main = self.index_main.search(emb_main, k_search)
        scores_full, indices_full = self.index_full.search(emb_full, k_search)

        # Weighted combination
        # S_emb = 0.7 * score_main + 0.3 * score_full
        combined_scores = {}  # {index: combined_score}

        # Add main scores
        for idx, score in zip(indices_main[0], scores_main[0]):
            if idx != -1:  # Valid index
                combined_scores[idx] = self.weight_main * score

        # Add full scores
        for idx, score in zip(indices_full[0], scores_full[0]):
            if idx != -1:  # Valid index
                if idx in combined_scores:
                    combined_scores[idx] += self.weight_full * score
                else:
                    combined_scores[idx] = self.weight_full * score

        # Sort by combined score (descending)
        sorted_indices = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)

        # Build result candidates
        candidates = []
        for idx in sorted_indices[:top_k]:
            item = self.items[idx]
            candidates.append({
                'index': int(idx),
                'score': float(combined_scores[idx]),
                'score_main': float(scores_main[0][np.where(indices_main[0] == idx)[0][0]]) if idx in indices_main[0] else 0.0,
                'score_full': float(scores_full[0][np.where(indices_full[0] == idx)[0][0]]) if idx in indices_full[0] else 0.0,
                'fdc_id': item.get('fdc_id'),
                'source': item.get('source'),
                'description': item.get('description'),
                'main_name': item.get('main_name'),
                'descriptors': item.get('descriptors', '')
            })

        return candidates

    def get_item_by_index(self, index: int) -> Optional[Dict]:
        """
        Get item metadata by index

        Args:
            index: Item index

        Returns:
            Item metadata or None if not found
        """
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def __repr__(self) -> str:
        return (
            f"IndexSearcher(items={len(self.items)}, "
            f"main_vectors={self.index_main.ntotal}, "
            f"full_vectors={self.index_full.ntotal}, "
            f"weights=({self.weight_main:.1f}, {self.weight_full:.1f}))"
        )


def main():
    """Example usage"""
    import sys
    from pathlib import Path

    # Paths
    project_root = Path(__file__).parent.parent.parent
    index_dir = project_root / "data"

    if not index_dir.exists():
        print(f"❌ Index directory not found: {index_dir}")
        print("Please run build_index_small.py first.")
        sys.exit(1)

    # Initialize searcher
    searcher = IndexSearcher(str(index_dir), device="cpu")
    print(f"\n{searcher}\n")

    # Example queries
    queries = [
        ("chicken breast", "grilled"),
        ("rice", "white, cooked"),
        ("milk", "whole"),
    ]

    for query_main, query_desc in queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {query_main} | {query_desc}")
        print('=' * 60)

        candidates = searcher.search(query_main, query_desc, top_k=5)

        for i, cand in enumerate(candidates, 1):
            print(f"\n{i}. Score: {cand['score']:.4f} (main={cand['score_main']:.4f}, full={cand['score_full']:.4f})")
            print(f"   {cand['description']}")
            print(f"   Source: {cand['source']}, FDC ID: {cand['fdc_id']}")


if __name__ == "__main__":
    main()
