"""
栄養検索システム用データモデル
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class NutritionInfo(BaseModel):
    """栄養情報"""
    calories: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None
    carbohydrates: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None


class SearchResult(BaseModel):
    """検索結果アイテム"""
    id: str
    name: str
    description: Optional[str] = None
    nutrition: NutritionInfo
    source_db: str
    score: float
    match_type: str  # "exact", "lemmatized", "partial", "fuzzy"


class SearchQuery(BaseModel):
    """検索クエリ"""
    query: str
    max_results: int = 10
    source_db_filter: Optional[List[str]] = None
    min_score: float = 0.1


class BatchSearchQuery(BaseModel):
    """バッチ検索クエリ"""
    queries: List[str]
    max_results: int = 5


class SearchResponse(BaseModel):
    """検索レスポンス"""
    query: str
    results: List[SearchResult]
    total_found: int
    search_time_ms: int
    lemmatized_query: Optional[str] = None


class BatchSearchResponse(BaseModel):
    """バッチ検索レスポンス"""
    queries: List[str] 
    responses: List[SearchResponse]
    total_search_time_ms: int
    summary: Dict[str, Any]


class SearchStats(BaseModel):
    """検索統計"""
    total_documents: int
    total_searches: int
    average_response_time_ms: float
    match_rate_percent: float
    database_distribution: Dict[str, int] 