"""
Utility functions for MEAL ANALYSIS API v2.0

This package contains utility functions for:
- Text processing and lemmatization
- Search enhancement tools
- Data manipulation helpers
"""

from .lemmatization import *

__all__ = [
    # lemmatization module exports
    "get_lemmatizer",
    "lemmatize_term", 
    "lemmatize_terms_batch",
    "create_lemmatized_query_variations"
] 