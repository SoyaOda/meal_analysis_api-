#!/usr/bin/env python3
"""
Search Handler - 栄養データベース検索APIエンドポイント

HTTPリクエストを処理し、クエリ前処理、クエリ構築、Elasticsearch検索を統合
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# プロジェクトパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp.query_preprocessor import preprocess_query, analyze_query
from api.query_builder import build_nutrition_search_query

# Elasticsearchクライアント（実際の実装では設定から読み込み）
try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    print("Warning: Elasticsearch client not available. Install with: pip install elasticsearch")

@dataclass
class SearchRequest:
    """検索リクエストのデータクラス"""
    query: str
    db_type_filter: Optional[str] = None
    size: int = 20
    enable_highlight: bool = True
    enable_synonyms: bool = True
    custom_weights: Optional[Dict[str, float]] = None

@dataclass
class SearchResponse:
    """検索レスポンスのデータクラス"""
    results: List[Dict[str, Any]]
    total_hits: int
    query_info: Dict[str, Any]
    took_ms: int
    max_score: float

class NutritionSearchHandler:
    """栄養データベース検索ハンドラー"""
    
    def __init__(self, elasticsearch_host: str = "localhost:9200", index_name: str = "nutrition_db"):
        """
        検索ハンドラーを初期化
        
        Args:
            elasticsearch_host: Elasticsearchホスト
            index_name: インデックス名
        """
        self.elasticsearch_host = elasticsearch_host
        self.index_name = index_name
        self.es_client = None
        
        # ロギング設定
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        if ELASTICSEARCH_AVAILABLE:
            try:
                self.es_client = Elasticsearch([elasticsearch_host])
                # 接続テスト
                if self.es_client.ping():
                    self.logger.info(f"Elasticsearch接続成功: {elasticsearch_host}")
                else:
                    self.logger.warning(f"Elasticsearch接続失敗: {elasticsearch_host}")
            except Exception as e:
                self.logger.error(f"Elasticsearch初期化エラー: {e}")
        else:
            self.logger.warning("Elasticsearchクライアントが利用できません")
    
    def search(self, request: SearchRequest) -> SearchResponse:
        """
        検索を実行
        
        Args:
            request: 検索リクエスト
            
        Returns:
            検索レスポンス
        """
        start_time = datetime.now()
        
        try:
            # 1. クエリ前処理
            processed_query = preprocess_query(
                request.query, 
                expand_synonyms=request.enable_synonyms
            )
            
            # 2. クエリ分析（デバッグ情報）
            query_analysis = analyze_query(request.query)
            
            # 3. Elasticsearchクエリ構築
            es_query = build_nutrition_search_query(
                processed_query=processed_query,
                original_query=request.query,
                db_type_filter=request.db_type_filter,
                size=request.size,
                custom_weights=request.custom_weights
            )
            
            # 4. Elasticsearch検索実行
            if self.es_client:
                response = self.es_client.search(
                    index=self.index_name,
                    body=es_query
                )
                results = self._format_search_results(response)
                total_hits = response['hits']['total']['value']
                max_score = response['hits']['max_score'] or 0.0
            else:
                # モックレスポンス（Elasticsearch未接続時）
                results = self._mock_search_results(request.query)
                total_hits = len(results)
                max_score = 1.0
            
            # 5. レスポンス構築
            end_time = datetime.now()
            took_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return SearchResponse(
                results=results,
                total_hits=total_hits,
                query_info={
                    "original_query": request.query,
                    "processed_query": processed_query,
                    "analysis": query_analysis,
                    "elasticsearch_query": es_query,
                    "db_type_filter": request.db_type_filter
                },
                took_ms=took_ms,
                max_score=max_score
            )
            
        except Exception as e:
            self.logger.error(f"検索エラー: {e}")
            return SearchResponse(
                results=[],
                total_hits=0,
                query_info={
                    "original_query": request.query,
                    "error": str(e)
                },
                took_ms=0,
                max_score=0.0
            )
    
    def _format_search_results(self, es_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Elasticsearchレスポンスを整形
        
        Args:
            es_response: Elasticsearchレスポンス
            
        Returns:
            整形済み結果リスト
        """
        results = []
        
        for hit in es_response['hits']['hits']:
            result = {
                **hit['_source'],
                '_score': hit['_score'],
                '_id': hit['_id']
            }
            
            # ハイライト情報を追加
            if 'highlight' in hit:
                result['_highlight'] = hit['highlight']
            
            results.append(result)
        
        return results
    
    def _mock_search_results(self, query: str) -> List[Dict[str, Any]]:
        """
        モック検索結果を生成（テスト用）
        
        Args:
            query: 検索クエリ
            
        Returns:
            モック結果リスト
        """
        # 簡単なモックデータ
        mock_results = [
            {
                "db_type": "dish",
                "id": 123456,
                "search_name": f"Cooked {query} with vegetables",
                "nutrition": {
                    "calories": 150.0,
                    "protein": 25.0,
                    "fat": 5.0,
                    "carbs": 15.0
                },
                "weight": 100.0,
                "_score": 2.5
            },
            {
                "db_type": "ingredient", 
                "id": 789012,
                "search_name": f"{query.capitalize()}, raw, fresh",
                "nutrition": {
                    "calories": 120.0,
                    "protein": 20.0,
                    "fat": 3.0,
                    "carbs": 10.0
                },
                "weight": 100.0,
                "_score": 2.0
            }
        ]
        
        return mock_results
    
    def health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック
        
        Returns:
            システム状態情報
        """
        status = {
            "service": "nutrition_search",
            "status": "healthy",
            "elasticsearch": {
                "available": ELASTICSEARCH_AVAILABLE,
                "connected": False,
                "host": self.elasticsearch_host,
                "index": self.index_name
            },
            "components": {
                "query_preprocessor": True,
                "query_builder": True
            }
        }
        
        if self.es_client:
            try:
                status["elasticsearch"]["connected"] = self.es_client.ping()
                if status["elasticsearch"]["connected"]:
                    # インデックス存在確認
                    index_exists = self.es_client.indices.exists(index=self.index_name)
                    status["elasticsearch"]["index_exists"] = index_exists
            except Exception as e:
                status["elasticsearch"]["error"] = str(e)
                status["status"] = "degraded"
        
        return status

# 便利関数
def create_search_handler(
    elasticsearch_host: str = "localhost:9200",
    index_name: str = "nutrition_db"
) -> NutritionSearchHandler:
    """検索ハンドラーのファクトリ関数"""
    return NutritionSearchHandler(elasticsearch_host, index_name)

def search_nutrition_db(
    query: str,
    db_type_filter: Optional[str] = None,
    size: int = 20,
    elasticsearch_host: str = "localhost:9200",
    index_name: str = "nutrition_db"
) -> SearchResponse:
    """便利な検索関数"""
    handler = create_search_handler(elasticsearch_host, index_name)
    request = SearchRequest(
        query=query,
        db_type_filter=db_type_filter,
        size=size
    )
    return handler.search(request) 