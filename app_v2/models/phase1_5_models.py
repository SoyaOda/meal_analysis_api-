#!/usr/bin/env python3
"""
Phase1.5 Models - Alternative Query Generation

exact matchがなかった項目に対する代替クエリ生成のためのデータモデル
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class NoMatchItem(BaseModel):
    """exact matchがなかった項目の情報"""
    original_query: str = Field(..., description="元のクエリ")
    item_type: str = Field(..., description="dish または ingredient")
    confidence: float = Field(..., description="Phase1での信頼度")
    search_results_count: int = Field(default=0, description="検索結果数")
    best_match_score: Optional[float] = Field(default=None, description="最高スコア")
    best_match_name: Optional[str] = Field(default=None, description="最高スコアの項目名")

class AlternativeQuery(BaseModel):
    """代替クエリの提案"""
    original_query: str = Field(..., description="元のクエリ")
    alternative_query: str = Field(..., description="代替クエリ")
    reasoning: str = Field(..., description="代替クエリを提案する理由")
    confidence: float = Field(..., description="代替クエリの信頼度 (0.0-1.0)")
    strategy: str = Field(..., description="使用した戦略 (broader_term, specific_variant, cooking_method, etc.)")

class Phase1_5Input(BaseModel):
    """Phase1.5への入力データ"""
    image_bytes: bytes = Field(..., description="画像データ")
    image_mime_type: str = Field(..., description="画像のMIMEタイプ")
    phase1_result: Dict[str, Any] = Field(..., description="Phase1の解析結果")
    failed_queries: List[str] = Field(..., description="検索に失敗したクエリリスト")
    failure_history: List[Dict[str, Any]] = Field(default_factory=list, description="過去の失敗履歴")
    iteration: int = Field(default=1, description="現在の反復回数")

class Phase1_5Output(BaseModel):
    """Phase1.5からの出力データ"""
    alternative_queries: List[AlternativeQuery] = Field(..., description="代替クエリ提案リスト")
    iteration: int = Field(..., description="処理した反復回数")
    total_alternatives_generated: int = Field(..., description="生成された代替クエリの総数")
    timestamp: datetime = Field(default_factory=datetime.now, description="処理時刻")

# 後方互換性のためのエイリアス
Phase15Input = Phase1_5Input
Phase15Output = Phase1_5Output

class EnhancedSearchResult(BaseModel):
    """Phase1.5による拡張検索結果"""
    original_matches: Dict[str, List[Any]] = Field(..., description="元の検索結果")
    alternative_matches: Dict[str, List[Dict[str, Any]]] = Field(..., description="代替クエリでの検索結果")
    final_consolidated_results: Dict[str, Dict[str, Any]] = Field(..., description="統合された最終結果")
    all_exact_matches: bool = Field(..., description="全ての項目がexact matchかどうか")
    processing_summary: Dict[str, Any] = Field(default_factory=dict, description="処理サマリー")
    phase15_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Phase1.5のメタデータ") 