# -*- coding: utf-8 -*-
"""
Reranking model module

Provides candidate reranking using BGE CrossEncoder.
This implementation uses BAAI/bge-reranker-base which is compatible with macOS
and does not have the NaN score issues that affected ms-marco-MiniLM-L-6-v2.
"""

from typing import List, Tuple, Union
import numpy as np
from sentence_transformers import CrossEncoder


class RerankerModel:
    """
    Reranking model using BGE CrossEncoder

    Uses BAAI/bge-reranker-base which is based on XLM-RoBERTa and does not
    depend on SDPA (Scaled Dot-Product Attention), avoiding NaN score issues
    on macOS with PyTorch 2.7.1.

    Scores query-candidate pairs to rerank search results.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        device: str = "cpu"
    ):
        """
        Args:
            model_name: BGE reranker model name (default: BAAI/bge-reranker-base)
            device: Device to use ("cpu" or "cuda")
        """
        self.model_name = model_name
        self.device = device

        print(f"Loading reranker model: {model_name}...")
        self.model = CrossEncoder(model_name, device=device)
        print(f"Reranker model loaded successfully.")

    def rerank(
        self,
        query: str,
        candidates: List[str],
        return_scores: bool = True
    ) -> Union[int, Tuple[int, np.ndarray]]:
        """
        Rerank candidates based on query relevance

        Args:
            query: Query text
            candidates: List of candidate texts
            return_scores: Whether to return scores

        Returns:
            If return_scores=False: Best candidate index
            If return_scores=True: (best_index, scores_array)
        """
        if not candidates:
            raise ValueError("Candidates list is empty")

        # Create query-candidate pairs
        pairs = [[query, candidate] for candidate in candidates]

        # Score all pairs
        scores = self.model.predict(
            pairs,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        # Get best candidate index
        best_idx = int(np.argmax(scores))

        if return_scores:
            return best_idx, scores
        return best_idx

    def score_pairs(
        self,
        pairs: List[Tuple[str, str]]
    ) -> np.ndarray:
        """
        Score a list of text pairs

        Args:
            pairs: List of (query, candidate) tuples

        Returns:
            Array of scores for each pair
        """
        if not pairs:
            raise ValueError("Pairs list is empty")

        # Score all pairs
        scores = self.model.predict(
            pairs,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        return scores

    def __repr__(self) -> str:
        return f"RerankerModel(model={self.model_name}, device={self.device})"
