#!/usr/bin/env python3
"""
Query Builder - Elasticsearch JSONクエリ構築モジュール

BM25F + function_scoreを使用した高度な検索クエリを構築
仕様書に従ったマルチシグナルブースティング戦略を実装
"""

from typing import Dict, List, Optional, Any
import json

class NutritionSearchQueryBuilder:
    """栄養データベース検索用のElasticsearchクエリビルダー"""
    
    def __init__(self):
        """クエリビルダーの初期化"""
        # デフォルトのスコアリング重み
        self.default_weights = {
            "exact_phrase_bonus": 100.0,
            "exact_word_bonus": 80.0,
            "phrase_proximity_bonus": 50.0,
            "prefix_match_bonus": 10.0,
            "base_field_boost": 1.0,
            "exact_field_boost": 3.0
        }
    
    def build_search_query(
        self,
        processed_query: str,
        original_query: str,
        db_type_filter: Optional[str] = None,
        size: int = 20,
        weights: Optional[Dict[str, float]] = None,
        enable_highlight: bool = True,
        enable_synonyms: bool = True
    ) -> Dict[str, Any]:
        """
        包括的な検索クエリを構築
        
        Args:
            processed_query: 前処理済みクエリ文字列
            original_query: 元のユーザークエリ文字列
            db_type_filter: データベースタイプフィルタ ("dish", "ingredient", "branded")
            size: 返却する結果数
            weights: カスタムスコア重み
            enable_highlight: ハイライト機能を有効にするか
            enable_synonyms: 類義語展開を有効にするか（将来拡張用）
            
        Returns:
            Elasticsearch JSONクエリ
        """
        # 重みのマージ
        final_weights = self.default_weights.copy()
        if weights:
            final_weights.update(weights)
        
        # ベースクエリ（BM25Fスコア用）
        base_query = self._build_base_query(processed_query, final_weights)
        
        # フィルタ追加
        if db_type_filter and db_type_filter != "all":
            base_query = self._add_filters(base_query, db_type_filter)
        
        # function_scoreクエリでブースティング
        function_score_query = self._build_function_score_query(
            base_query, 
            original_query, 
            processed_query,
            final_weights
        )
        
        # 完全なクエリ構築
        search_query = {
            "query": function_score_query,
            "size": size,
            "_source": ["db_type", "id", "search_name", "nutrition", "weight"]
        }
        
        # ハイライト追加
        if enable_highlight:
            search_query["highlight"] = self._build_highlight_config()
        
        return search_query
    
    def _build_base_query(self, processed_query: str, weights: Dict[str, float]) -> Dict[str, Any]:
        """
        BM25Fベースクエリを構築
        
        Args:
            processed_query: 前処理済みクエリ
            weights: スコア重み
            
        Returns:
            ベースクエリ辞書
        """
        return {
            "multi_match": {
                "query": processed_query,
                "fields": [
                    f"search_name^{weights['base_field_boost']}",
                    f"search_name.exact^{weights['exact_field_boost']}"
                ],
                "type": "best_fields",
                "operator": "OR",
                "fuzziness": "AUTO",
                "max_expansions": 50,
                "prefix_length": 2
            }
        }
    
    def _add_filters(self, base_query: Dict[str, Any], db_type: str) -> Dict[str, Any]:
        """
        フィルタを追加してboolクエリに変換
        
        Args:
            base_query: ベースクエリ
            db_type: データベースタイプフィルタ
            
        Returns:
            フィルタ付きboolクエリ
        """
        return {
            "bool": {
                "must": [base_query],
                "filter": [
                    {"term": {"db_type": db_type}}
                ]
            }
        }
    
    def _build_function_score_query(
        self, 
        base_query: Dict[str, Any], 
        original_query: str,
        processed_query: str,
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        function_scoreクエリでマルチシグナルブースティングを構築
        
        Args:
            base_query: ベースクエリ
            original_query: 元のクエリ
            processed_query: 処理済みクエリ
            weights: スコア重み
            
        Returns:
            function_scoreクエリ
        """
        functions = []
        
        # 1. 完全一致フレーズボーナス（最優先）
        functions.append({
            "filter": {
                "match_phrase": {
                    "search_name.exact": {
                        "query": original_query,
                        "slop": 0
                    }
                }
            },
            "weight": weights["exact_phrase_bonus"]
        })
        
        # 2. 近接フレーズボーナス（slop=1許容）
        functions.append({
            "filter": {
                "match_phrase": {
                    "search_name": {
                        "query": original_query,
                        "slop": 1
                    }
                }
            },
            "weight": weights["phrase_proximity_bonus"]
        })
        
        # 3. 完全一致単語ボーナス（個別単語レベル）
        # 処理済みクエリの各単語に対して
        for word in processed_query.split():
            if len(word) > 2:  # 短すぎる単語は除外
                functions.append({
                    "filter": {
                        "term": {
                            "search_name.exact": word
                        }
                    },
                    "weight": weights["exact_word_bonus"] * 0.5  # 単語レベルは少し低めに
                })
        
        # 4. 前方一致ボーナス（低優先度）
        functions.append({
            "filter": {
                "match_phrase_prefix": {
                    "search_name": {
                        "query": original_query,
                        "max_expansions": 10
                    }
                }
            },
            "weight": weights["prefix_match_bonus"]
        })
        
        return {
            "function_score": {
                "query": base_query,
                "functions": functions,
                "score_mode": "sum",  # 各ボーナスを累積
                "boost_mode": "sum",  # ベーススコアにボーナスを加算
                "max_boost": 1000.0  # 上限設定
            }
        }
    
    def _build_highlight_config(self) -> Dict[str, Any]:
        """
        ハイライト設定を構築
        
        Returns:
            ハイライト設定辞書
        """
        return {
            "fields": {
                "search_name": {
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"],
                    "fragment_size": 150,
                    "number_of_fragments": 1
                },
                "search_name.exact": {
                    "pre_tags": ["<strong>"],
                    "post_tags": ["</strong>"],
                    "fragment_size": 150,
                    "number_of_fragments": 1
                }
            },
            "require_field_match": False
        }
    
    def build_simple_query(
        self, 
        query: str, 
        db_type_filter: Optional[str] = None,
        size: int = 20
    ) -> Dict[str, Any]:
        """
        シンプルな検索クエリを構築（デバッグ用）
        
        Args:
            query: 検索クエリ
            db_type_filter: データベースタイプフィルタ
            size: 返却する結果数
            
        Returns:
            シンプルなElasticsearchクエリ
        """
        base_query = {
            "multi_match": {
                "query": query,
                "fields": ["search_name^2", "search_name.exact^3"],
                "type": "best_fields",
                "fuzziness": "AUTO"
            }
        }
        
        if db_type_filter and db_type_filter != "all":
            base_query = {
                "bool": {
                    "must": [base_query],
                    "filter": [{"term": {"db_type": db_type_filter}}]
                }
            }
        
        return {
            "query": base_query,
            "size": size,
            "_source": ["db_type", "id", "search_name", "nutrition", "weight"]
        }
    
    def build_analysis_query(self, text: str, analyzer: str = "custom_food_analyzer") -> Dict[str, Any]:
        """
        アナライザのテスト用クエリを構築
        
        Args:
            text: 分析するテキスト
            analyzer: 使用するアナライザ名
            
        Returns:
            分析用クエリ
        """
        return {
            "analyzer": analyzer,
            "text": text
        }
    
    def get_weight_explanation(self) -> Dict[str, Any]:
        """
        現在の重み設定の説明を取得
        
        Returns:
            重み設定の説明辞書
        """
        return {
            "weights": self.default_weights,
            "explanations": {
                "exact_phrase_bonus": "完全フレーズ一致時の最高ボーナス",
                "exact_word_bonus": "完全単語一致時のボーナス",
                "phrase_proximity_bonus": "近接フレーズ一致時のボーナス",
                "prefix_match_bonus": "前方一致時の低ボーナス",
                "base_field_boost": "search_nameフィールドの基本ブースト",
                "exact_field_boost": "search_name.exactフィールドのブースト"
            },
            "strategy": {
                "score_mode": "sum",
                "boost_mode": "sum",
                "description": "BM25Fベーススコア + 累積ボーナススコア"
            }
        }

# 便利関数
def build_nutrition_search_query(
    processed_query: str,
    original_query: str,
    db_type_filter: Optional[str] = None,
    size: int = 20,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    栄養データベース検索クエリの構築（便利関数）
    
    Args:
        processed_query: 前処理済みクエリ
        original_query: 元のクエリ
        db_type_filter: データベースタイプフィルタ
        size: 結果数
        custom_weights: カスタム重み
        
    Returns:
        Elasticsearchクエリ辞書
    """
    builder = NutritionSearchQueryBuilder()
    return builder.build_search_query(
        processed_query=processed_query,
        original_query=original_query,
        db_type_filter=db_type_filter,
        size=size,
        weights=custom_weights
    ) 