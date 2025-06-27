"""
栄養検索エンジン - 7段階検索戦略と見出し語化機能
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

from .models import SearchQuery, SearchResponse, SearchResult, NutritionInfo, BatchSearchQuery, BatchSearchResponse
from utils.lemmatization import lemmatize_term, create_lemmatized_query_variations
from utils.elasticsearch_client import get_elasticsearch_client

logger = logging.getLogger(__name__)


class NutritionSearchEngine:
    """栄養データベース検索エンジン"""
    
    def __init__(self):
        self.es_client = get_elasticsearch_client()
        
        # 検索パラメータ
        self.lemmatized_exact_match_boost = 2.0
        self.compound_word_penalty = 0.8
        self.enable_lemmatization = True
        
        # 統計
        self.total_searches = 0
        self.total_response_time = 0
        
        logger.info("🔍 NutritionSearchEngine initialized")
    
    async def search(self, query: SearchQuery) -> SearchResponse:
        """単一検索実行"""
        start_time = datetime.now()
        
        if not self.es_client.is_connected():
            return SearchResponse(
                query=query.query,
                results=[],
                total_found=0,
                search_time_ms=0,
                lemmatized_query=None
            )
        
        # 見出し語化処理
        lemmatized_query = lemmatize_term(query.query) if self.enable_lemmatization else query.query
        
        # 7段階検索クエリ構築
        es_query = self._build_advanced_search_query(query.query, lemmatized_query, query.max_results)
        
        # Elasticsearch検索実行
        response = await self.es_client.search(es_query)
        
        # 結果変換
        results = []
        if response and response.get('hits', {}).get('hits'):
            results = await self._convert_es_results(response['hits']['hits'], query.query, lemmatized_query)
            
            # スコアフィルタリング
            results = [r for r in results if r.score >= query.min_score]
            
            # ソースDBフィルタリング
            if query.source_db_filter:
                results = [r for r in results if r.source_db in query.source_db_filter]
        
        # 統計更新
        end_time = datetime.now()
        search_time_ms = int((end_time - start_time).total_seconds() * 1000)
        self.total_searches += 1
        self.total_response_time += search_time_ms
        
        return SearchResponse(
            query=query.query,
            results=results,
            total_found=len(results),
            search_time_ms=search_time_ms,
            lemmatized_query=lemmatized_query if lemmatized_query != query.query else None
        )
    
    async def batch_search(self, batch_query: BatchSearchQuery) -> BatchSearchResponse:
        """バッチ検索実行"""
        start_time = datetime.now()
        
        # 並列検索実行
        search_tasks = []
        for query_text in batch_query.queries:
            search_query = SearchQuery(
                query=query_text,
                max_results=batch_query.max_results
            )
            search_tasks.append(self.search(search_query))
        
        responses = await asyncio.gather(*search_tasks)
        
        # 統計情報作成
        end_time = datetime.now()
        total_search_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        total_results = sum(len(r.results) for r in responses)
        successful_searches = sum(1 for r in responses if len(r.results) > 0)
        
        summary = {
            "total_queries": len(batch_query.queries),
            "successful_searches": successful_searches,
            "total_results": total_results,
            "average_results_per_query": total_results / len(batch_query.queries) if batch_query.queries else 0,
            "match_rate_percent": (successful_searches / len(batch_query.queries) * 100) if batch_query.queries else 0
        }
        
        return BatchSearchResponse(
            queries=batch_query.queries,
            responses=responses,
            total_search_time_ms=total_search_time_ms,
            summary=summary
        )
    
    def _build_advanced_search_query(self, original_term: str, lemmatized_term: str, max_results: int) -> Dict[str, Any]:
        """7段階検索戦略のElasticsearchクエリ構築"""
        
        bool_query = {
            "bool": {
                "should": [
                    # 1. 見出し語化完全一致（最高ブースト）
                    {
                        "match": {
                            "search_name_lemmatized.exact": {
                                "query": lemmatized_term,
                                "boost": self.lemmatized_exact_match_boost * 3.0
                            }
                        }
                    },
                    # 2. 見出し語化一致（高ブースト）
                    {
                        "match": {
                            "search_name_lemmatized": {
                                "query": lemmatized_term,
                                "boost": self.lemmatized_exact_match_boost * 2.0
                            }
                        }
                    },
                    # 3. 元の語での完全一致
                    {
                        "match": {
                            "search_name.exact": {
                                "query": original_term,
                                "boost": 1.8
                            }
                        }
                    },
                    # 4. 元の語での一致
                    {
                        "match": {
                            "search_name": {
                                "query": original_term,
                                "boost": 1.5
                            }
                        }
                    },
                    # 5. 見出し語化部分一致
                    {
                        "match_phrase": {
                            "search_name_lemmatized": {
                                "query": lemmatized_term,
                                "boost": self.lemmatized_exact_match_boost
                            }
                        }
                    },
                    # 6. 元の語での部分一致
                    {
                        "match_phrase": {
                            "search_name": {
                                "query": original_term,
                                "boost": 1.0
                            }
                        }
                    },
                    # 7. あいまい検索（typo対応）
                    {
                        "fuzzy": {
                            "search_name_lemmatized": {
                                "value": lemmatized_term,
                                "fuzziness": "AUTO",
                                "boost": 0.5
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }
        
        return {
            "query": bool_query,
            "size": max_results * 2,  # スコア調整後に絞り込むため多めに取得
            "_source": ["id", "search_name", "description", "original_name", "data_type", "nutrition", "source_db"]
        }
    
    async def _convert_es_results(self, es_hits: List[Dict[str, Any]], original_term: str, lemmatized_term: str) -> List[SearchResult]:
        """Elasticsearch結果をSearchResultに変換"""
        results = []
        
        for hit in es_hits:
            source = hit['_source']
            
            # 栄養情報変換
            nutrition_data = source.get('nutrition', {})
            nutrition = NutritionInfo(**nutrition_data)
            
            # マッチタイプ判定
            match_type = self._determine_match_type(
                source.get('search_name', ''),
                source.get('search_name_lemmatized', ''),
                original_term,
                lemmatized_term
            )
            
            # スコア調整
            adjusted_score = self._calculate_adjusted_score(
                hit['_score'],
                original_term,
                lemmatized_term,
                source.get('search_name', ''),
                source.get('search_name_lemmatized', ''),
                match_type
            )
            
            result = SearchResult(
                id=str(source.get('id', '')),
                name=source.get('search_name', ''),
                description=source.get('description', ''),
                original_name=source.get('original_name', ''),
                nutrition=nutrition,
                source_db=source.get('source_db', ''),
                score=adjusted_score,
                match_type=match_type
            )
            
            results.append(result)
        
        # スコア順でソート
        results.sort(key=lambda x: x.score, reverse=True)
        
        # 同スコア結果の再ランキング（search_name + description での再検索）
        results = await self._rerank_tied_scores(results, original_term, lemmatized_term)
        
        return results
    
    def _determine_match_type(self, db_name: str, db_name_lemmatized: str, original_term: str, lemmatized_term: str) -> str:
        """マッチタイプを判定"""
        db_name_lower = db_name.lower()
        db_lemmatized_lower = db_name_lemmatized.lower()
        original_lower = original_term.lower()
        lemmatized_lower = lemmatized_term.lower()
        
        if db_name_lower == original_lower or db_lemmatized_lower == lemmatized_lower:
            return "exact"
        elif db_lemmatized_lower == lemmatized_lower:
            return "lemmatized"
        elif original_lower in db_name_lower or lemmatized_lower in db_lemmatized_lower:
            return "partial"
        else:
            return "fuzzy"
    
    def _calculate_adjusted_score(
        self, 
        base_score: float, 
        original_term: str, 
        lemmatized_term: str, 
        db_name: str, 
        db_name_lemmatized: str, 
        match_type: str
    ) -> float:
        """スコア調整計算"""
        
        # ベーススコア調整
        if match_type == "exact":
            adjustment = self.lemmatized_exact_match_boost
        elif match_type == "lemmatized":
            adjustment = self.lemmatized_exact_match_boost * 0.9
        elif match_type == "partial":
            adjustment = 0.8
        else:  # fuzzy
            adjustment = 0.5
        
        # 複合語ペナルティ
        if len(original_term.split()) > 1:
            adjustment *= self.compound_word_penalty
        
        return base_score * adjustment
    
    async def _rerank_tied_scores(self, results: List[SearchResult], original_term: str, lemmatized_term: str) -> List[SearchResult]:
        """同じスコアの結果をsearch_name + descriptionで再ランキング"""
        if len(results) <= 1:
            return results
        
        # スコアグループを作成
        score_groups = {}
        for result in results:
            rounded_score = round(result.score, 2)  # 小数点2桁で丸める
            if rounded_score not in score_groups:
                score_groups[rounded_score] = []
            score_groups[rounded_score].append(result)
        
        # 各スコアグループで再ランキング
        reranked_results = []
        for score in sorted(score_groups.keys(), reverse=True):
            group = score_groups[score]
            
            if len(group) == 1:
                # 単一結果はそのまま
                reranked_results.extend(group)
            else:
                # 複数結果を再ランキング
                reranked_group = await self._rerank_group_with_description(group, original_term, lemmatized_term)
                reranked_results.extend(reranked_group)
        
        return reranked_results
    
    async def _rerank_group_with_description(self, group: List[SearchResult], original_term: str, lemmatized_term: str) -> List[SearchResult]:
        """同スコアグループをsearch_name + descriptionで再ランキング"""
        try:
            # グループのIDを取得
            group_ids = [result.id for result in group]
            
            # search_name + description での再検索クエリを構築
            rerank_query = self._build_description_search_query(original_term, lemmatized_term, group_ids)
            
            # 再検索実行
            response = await self.es_client.search(rerank_query)
            
            if not response or not response.get('hits', {}).get('hits'):
                return group  # 再検索失敗時は元の順序を維持
            
            # 再検索結果でスコアマップを作成
            rerank_scores = {}
            for hit in response['hits']['hits']:
                item_id = str(hit['_source'].get('id', ''))
                rerank_scores[item_id] = hit['_score']
            
            # 再ランキング実行とスコア更新
            original_base_score = group[0].score  # 同スコアグループなので最初のスコアを基準に
            reranked_group = []
            
            # descriptionの関連性を評価して差別化
            for i, result in enumerate(sorted(group, key=lambda r: rerank_scores.get(r.id, 0), reverse=True)):
                # descriptionによる追加ボーナス計算
                desc_bonus = self._calculate_description_relevance_bonus(result.description, original_term, lemmatized_term)
                rerank_bonus = rerank_scores.get(result.id, 0) * 0.1
                position_penalty = i * 0.001  # 同じrerankスコアでも順序を保つための微調整
                
                new_score = original_base_score + rerank_bonus + desc_bonus - position_penalty
                
                # 結果のスコアを更新
                updated_result = SearchResult(
                    id=result.id,
                    name=result.name,
                    description=result.description,
                    original_name=result.original_name,
                    nutrition=result.nutrition,
                    source_db=result.source_db,
                    score=new_score,
                    match_type=result.match_type
                )
                reranked_group.append(updated_result)
            
            return reranked_group
            
        except Exception as e:
            logger.warning(f"Reranking failed: {e}")
            return group  # エラー時は元の順序を維持
    
    def _calculate_description_relevance_bonus(self, description: str, original_term: str, lemmatized_term: str) -> float:
        """descriptionの関連性に基づくスコアボーナス計算"""
        if not description or description == "None":
            return 0.0
        
        desc_lower = description.lower()
        original_lower = original_term.lower()
        lemmatized_lower = lemmatized_term.lower()
        
        bonus = 0.0
        
        # 関連性の高い調理法・形態キーワードにボーナス
        cooking_methods = ["raw", "cooked", "boiled", "baked", "grilled", "fried", "steamed", "roasted"]
        forms = ["boneless", "skinless", "whole", "ground", "tenderloins", "meat only"]
        containers = ["canned", "fresh", "frozen", "dried"]
        
        # 調理法の関連性
        for method in cooking_methods:
            if method in desc_lower:
                if "raw" in desc_lower and ("fresh" in original_lower or "raw" in original_lower):
                    bonus += 0.02  # 生に関連する検索には生食品を優先
                elif method in original_lower or method in lemmatized_lower:
                    bonus += 0.05  # 検索語に含まれる調理法
                else:
                    bonus += 0.01  # 一般的な調理法
        
        # 形態の関連性
        for form in forms:
            if form in desc_lower:
                if form in original_lower or form in lemmatized_lower:
                    bonus += 0.03
                else:
                    bonus += 0.005
        
        # 容器・保存形態
        for container in containers:
            if container in desc_lower:
                bonus += 0.002
        
        # 単語数による複雑さペナルティ（簡潔な記述を優先）
        word_count = len(description.split(", "))
        if word_count > 3:
            bonus -= (word_count - 3) * 0.001
        
        return bonus
    
    def _build_description_search_query(self, original_term: str, lemmatized_term: str, target_ids: List[str]) -> Dict[str, Any]:
        """search_name + description での再検索クエリ構築"""
        
        bool_query = {
            "bool": {
                "must": [
                    # 対象IDでフィルタリング
                    {
                        "terms": {
                            "id": target_ids
                        }
                    }
                ],
                "should": [
                    # search_name + description の組み合わせフィールドでの検索
                    {
                        "multi_match": {
                            "query": lemmatized_term,
                            "fields": ["search_name_lemmatized^2.0", "description^1.0"],
                            "type": "best_fields"
                        }
                    },
                    {
                        "multi_match": {
                            "query": original_term,
                            "fields": ["search_name^2.0", "description^1.0"],
                            "type": "best_fields"
                        }
                    },
                    # フレーズマッチ
                    {
                        "multi_match": {
                            "query": lemmatized_term,
                            "fields": ["search_name_lemmatized", "description"],
                            "type": "phrase",
                            "boost": 1.5
                        }
                    },
                    # ファジー検索
                    {
                        "multi_match": {
                            "query": lemmatized_term,
                            "fields": ["search_name_lemmatized", "description"],
                            "fuzziness": "AUTO",
                            "boost": 0.5
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }
        
        return {
            "query": bool_query,
            "size": len(target_ids),
            "_source": ["id", "search_name", "description", "original_name"]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """検索統計取得"""
        avg_response_time = (self.total_response_time / self.total_searches) if self.total_searches > 0 else 0
        
        return {
            "total_searches": self.total_searches,
            "average_response_time_ms": avg_response_time,
            "total_documents": self.es_client.get_total_documents(),
            "elasticsearch_health": self.es_client.get_index_stats()
        } 