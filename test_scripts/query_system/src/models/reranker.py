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
    BGE LLM-based Reranker with custom food-matching prompts (Phase 2)
    
    Uses bge-reranker-v2.5-gemma2-lightweight (9B parameters, BEIR 63.67)
    with domain-specific task instructions for improved accuracy.
    """
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2.5-gemma2-lightweight",
        use_fp16: bool = True,
        device: str = "cpu"
    ):
        """
        Initialize FlagLLMReranker with custom food-matching prompt
        
        Args:
            model_name: LLM-based reranker model name
            use_fp16: Whether to use FP16 precision (default: True for speed)
            device: Device for model ("cpu" or "cuda")
        """
        print(f"Loading reranker model: {model_name}...")
        
        from FlagEmbedding import FlagLLMReranker
        import os
        
        # Custom task instruction for food matching
        # Priority: Exact food identity > Cooking method > Preparation details
        self.task_prompt = """You are matching user food descriptions to entries in the USDA nutrition database for accurate calorie calculation.

Priority for matching (most important first):
1. **Food Identity**: The main food name must match exactly (e.g., "tomatoes" must match "tomatoes", NOT "cherries" even if "cherry tomatoes" was mentioned)
2. **Cooking Method**: Raw vs cooked matters significantly for nutrition values
   - If query specifies a cooking method (e.g., "grilled", "roasted", "fried"), prefer exact matches
   - If query only says "cooked" without specifics, accept any cooked form
   - If database entry says "NS as to cooking method", it's acceptable for ambiguous queries
3. **Preparation Details**: Additional descriptors like "boneless", "skinless", "sliced" are helpful but less critical

Examples:
- Query "cherry tomatoes, raw" → Match "Tomatoes, raw" (food identity "tomatoes" is correct)
- Query "chicken breast, cooked" → Match "Chicken breast, NS as to cooking method" (acceptable for ambiguous "cooked")
- Query "beef steak, grilled" → Match "Beef, steak, grilled" (exact cooking method match preferred)

Given a user query and a database entry, determine if they match well for nutrition calculation."""
        
        # Set cache directory for model downloads
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        
        # Initialize FlagLLMReranker with custom instruction
        self.model = FlagLLMReranker(
            model_name,
            use_fp16=use_fp16,
            query_instruction_for_rerank=self.task_prompt,
            cache_dir=cache_dir,
            trust_remote_code=True  # Required for custom model code
        )
        
        print("Reranker model loaded successfully.")
    
    def rerank(
        self,
        query: str,
        candidates: List[str],
        return_scores: bool = True
    ):
        """
        Rerank candidates using FlagLLMReranker with custom prompt
        
        Args:
            query: Query text (field-labeled format from text_normalizer)
            candidates: List of candidate texts (field-labeled format)
            return_scores: Whether to return all scores (default: True)
        
        Returns:
            If return_scores=True: (best_index, scores_array)
            If return_scores=False: best_index
        """
        # Build query-passage pairs with custom task instruction
        pairs = [[query, candidate] for candidate in candidates]
        
        # Compute scores using FlagLLMReranker
        # Note: FlagLLMReranker uses the task prompt internally via query_instruction
        scores = self.model.compute_score(
            pairs,
            use_dataloader=True,
            batch_size=8,
            normalize=True
        )
        
        # Convert to numpy array
        import numpy as np
        scores = np.array(scores)
        
        # Find best match
        best_idx = int(np.argmax(scores))
        
        if return_scores:
            return best_idx, scores
        return best_idx
