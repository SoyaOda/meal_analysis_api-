# -*- coding: utf-8 -*-
"""
Two-stage hybrid search pipeline (spec3.md)

Stage 1: Two-stream weighted FAISS search (0.7*main + 0.3*full)
Stage 2: BGE-reranker with field-labeled templates
"""

from typing import List, Dict, Optional
from pathlib import Path

from .index.searcher import IndexSearcher
from .models.reranker import RerankerModel
from .preprocessing.text_normalizer import build_rerank_text


class FoodSearchPipeline:
    """
    Two-stage food name matching pipeline (spec3.md)

    Stage 1: Retrieve Top-K candidates with weighted embedding search
    Stage 2: Rerank candidates with BGE-reranker using field labels
    """

    def __init__(
        self,
        index_dir: str,
        device: str = "cpu",
        weight_main: float = 0.6,
        weight_full: float = 0.4,
        stage1_top_k: int = 40,
        reranker_model: str = "BAAI/bge-reranker-v2.5-gemma2-lightweight"
    ):
        """
        Args:
            index_dir: Directory containing FAISS indexes and metadata
            device: Device for models ("cpu" or "cuda")
            weight_main: Weight for main_only score in Stage 1 (default: 0.6, Phase 1 improved)
            weight_full: Weight for full score in Stage 1 (default: 0.4, Phase 1 improved)
            stage1_top_k: Number of candidates to retrieve in Stage 1 (default: 40, Phase 1 improved)
            reranker_model: Reranker model name (default: BAAI/bge-reranker-v2.5-gemma2-lightweight, Phase 2)
        """
        self.index_dir = Path(index_dir)
        self.device = device
        self.stage1_top_k = stage1_top_k

        # Initialize Stage 1: Searcher
        print("Initializing Stage 1: Two-stream weighted searcher...")
        self.searcher = IndexSearcher(
            str(index_dir),
            device=device,
            weight_main=weight_main,
            weight_full=weight_full
        )

        # Initialize Stage 2: Reranker (Phase 2: LLM-based with custom prompts)
        print("\nInitializing Stage 2: BGE LLM-reranker...")
        self.reranker = RerankerModel(model_name=reranker_model, device=device)

        print("\nPipeline initialized successfully!")

    def search(
        self,
        query_main: str,
        query_descriptors: str = "",
        return_top_k: int = 5,
        return_candidates: bool = False
    ) -> Dict:
        """
        Search for best matching food item

        Args:
            query_main: Main food name (e.g., "chicken breast")
            query_descriptors: Optional descriptors (e.g., "grilled, boneless")
            return_top_k: Number of final results to return (default: 5)
            return_candidates: Whether to return Stage 1 candidates (default: False)

        Returns:
            Dictionary with results:
            - best_match: Top result after reranking
            - top_k: Top-K results after reranking
            - candidates: Stage 1 candidates (if return_candidates=True)
        """
        # Stage 1: Two-stream weighted search
        print(f"\nStage 1: Retrieving {self.stage1_top_k} candidates...")
        candidates = self.searcher.search(
            query_main=query_main,
            query_descriptors=query_descriptors,
            top_k=self.stage1_top_k
        )
        print(f" Retrieved {len(candidates)} candidates")

        # Stage 2: Rerank with field-labeled templates
        print(f"\nStage 2: Reranking with BGE-reranker...")

        # Phase 1: Normalize query for reranker (same as embedding)
        from .preprocessing.text_normalizer import normalize_compound_words
        normalized_query_main = normalize_compound_words(query_main)

        # Build query text with field labels
        query_text = build_rerank_text(normalized_query_main, query_descriptors, is_query=True)

        # Build candidate texts with field labels
        candidate_texts = [
            build_rerank_text(cand['main_name'], cand['descriptors'], is_query=False)
            for cand in candidates
        ]

        # Rerank
        best_idx, scores = self.reranker.rerank(
            query=query_text,
            candidates=candidate_texts,
            return_scores=True
        )

        print(f" Reranking completed")

        # Build results
        results_with_scores = []
        for i, (cand, score) in enumerate(zip(candidates, scores)):
            result = {
                'rank': i + 1,
                'rerank_score': float(score),
                'stage1_score': cand['score'],
                'index': cand['index'],
                'fdc_id': cand['fdc_id'],
                'source': cand['source'],
                'description': cand['description'],
                'main_name': cand['main_name'],
                'descriptors': cand['descriptors']
            }
            results_with_scores.append(result)

        # Sort by rerank score (descending)
        results_with_scores.sort(key=lambda x: x['rerank_score'], reverse=True)

        # Update ranks
        for i, result in enumerate(results_with_scores):
            result['rank'] = i + 1

        # Build return dictionary
        output = {
            'query': {
                'main': query_main,
                'descriptors': query_descriptors
            },
            'best_match': results_with_scores[0] if results_with_scores else None,
            'top_k': results_with_scores[:return_top_k]
        }

        if return_candidates:
            output['stage1_candidates'] = candidates

        return output

    def search_batch(
        self,
        queries: List[Dict[str, str]],
        return_top_k: int = 5
    ) -> List[Dict]:
        """
        Search for multiple queries

        Args:
            queries: List of query dictionaries with 'main' and 'descriptors' keys
            return_top_k: Number of final results per query

        Returns:
            List of result dictionaries
        """
        results = []
        for query in queries:
            result = self.search(
                query_main=query.get('main', ''),
                query_descriptors=query.get('descriptors', ''),
                return_top_k=return_top_k,
                return_candidates=False
            )
            results.append(result)
        return results

    def __repr__(self) -> str:
        return (
            f"FoodSearchPipeline("
            f"items={len(self.searcher.items)}, "
            f"stage1_k={self.stage1_top_k}, "
            f"weights=({self.searcher.weight_main:.1f}, {self.searcher.weight_full:.1f}))"
        )


def main():
    """Example usage"""
    import sys
    from pathlib import Path

    # Paths
    project_root = Path(__file__).parent.parent
    index_dir = project_root / "data"

    if not index_dir.exists():
        print(f"L Index directory not found: {index_dir}")
        print("Please run scripts/build_index_small.py first.")
        sys.exit(1)

    # Initialize pipeline
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=20
    )

    print(f"\n{pipeline}\n")

    # Example queries
    queries = [
        {"main": "milk", "descriptors": "whole"},
        {"main": "rice", "descriptors": "white, cooked"},
        {"main": "yogurt", "descriptors": "Greek, nonfat"},
    ]

    for query in queries:
        print("\n" + "=" * 60)
        print(f"Query: {query['main']} | {query['descriptors']}")
        print("=" * 60)

        result = pipeline.search(
            query_main=query['main'],
            query_descriptors=query['descriptors'],
            return_top_k=3
        )

        print(f"\n<� Best Match:")
        best = result['best_match']
        print(f"   Score: {best['rerank_score']:.4f} (Stage1: {best['stage1_score']:.4f})")
        print(f"   {best['description']}")

        print(f"\n=� Top 3:")
        for i, item in enumerate(result['top_k'], 1):
            print(f"   {i}. {item['rerank_score']:.4f} - {item['description']}")


if __name__ == "__main__":
    main()
