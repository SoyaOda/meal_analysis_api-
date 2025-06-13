#!/usr/bin/env python3
"""
Enhanced Nutrition Search Component with Phase1.5 Integration

Phase1.5（代替クエリ生成）を統合した拡張栄養検索コンポーネント
exact matchがない場合に自動的にPhase1.5で代替クエリを生成し、再検索を実行
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .base import BaseComponent
from .elasticsearch_nutrition_search_component import ElasticsearchNutritionSearchComponent
from .phase1_5_component import Phase1_5Component
from ..models.nutrition_search_models import NutritionQueryInput, NutritionQueryOutput, NutritionMatch
from ..models.phase1_5_models import Phase15Input, NoMatchItem, EnhancedSearchResult

class EnhancedNutritionSearchComponent(BaseComponent[NutritionQueryInput, EnhancedSearchResult]):
    """
    Phase1.5統合拡張栄養検索コンポーネント
    
    1. 通常のElasticsearch検索を実行
    2. exact matchがない項目を検出
    3. Phase1.5で代替クエリを生成
    4. 代替クエリで再検索
    5. 結果を統合して全てexact matchの結果を返す
    """
    
    def __init__(
        self,
        elasticsearch_url: str = "http://localhost:9200",
        enable_phase15: bool = True,
        phase15_model: str = "gemini-1.5-flash",
        max_phase15_iterations: int = 3,  # 最大Phase1.5試行回数
        debug: bool = False
    ):
        super().__init__("EnhancedNutritionSearchComponent")
        
        self.enable_phase15 = enable_phase15
        self.max_phase15_iterations = max_phase15_iterations
        self.debug = debug
        
        # 画像データを保持するための変数
        self.current_image_bytes = b''
        self.current_image_mime_type = 'image/jpeg'
        
        # Elasticsearch検索コンポーネント
        self.es_component = ElasticsearchNutritionSearchComponent(
            elasticsearch_url=elasticsearch_url,
            enable_auto_niche_update=True,  # 自動更新は有効のまま
            debug=debug
        )
        
        # Phase1.5コンポーネント
        if self.enable_phase15:
            self.phase15_component = Phase1_5Component()
        else:
            self.phase15_component = None
        
        self.logger.info(f"Enhanced nutrition search component initialized (Phase1.5: {enable_phase15}, Max iterations: {max_phase15_iterations})")
    
    def set_image_data(self, image_bytes: bytes, image_mime_type: str = 'image/jpeg'):
        """Phase1.5で使用する画像データを設定"""
        self.current_image_bytes = image_bytes
        self.current_image_mime_type = image_mime_type
        self.logger.info(f"Image data set for Phase1.5: {len(image_bytes)} bytes, {image_mime_type}")
    
    async def process(self, input_data: NutritionQueryInput) -> EnhancedSearchResult:
        """
        拡張検索の主処理（再帰的Phase1.5対応）
        
        Args:
            input_data: NutritionQueryInput
            
        Returns:
            EnhancedSearchResult: 拡張検索結果
        """
        start_time = datetime.now()
        
        try:
            # Step 1: 通常のElasticsearch検索を実行
            self.logger.info("Step 1: Executing initial Elasticsearch search...")
            current_search_result = await self.es_component.execute(input_data)
            
            # 再帰的Phase1.5実行の履歴を管理
            phase15_history = []
            all_alternative_matches = {}
            iteration_count = 0
            
            # Step 2: 再帰的にPhase1.5を実行
            while iteration_count < self.max_phase15_iterations:
                iteration_count += 1
                
                # exact matchがない項目を検出
                no_match_items = self._identify_no_match_items(current_search_result, input_data)
                
                self.logger.info(f"Iteration {iteration_count}: No exact matches found for {len(no_match_items)} items")
                
                # デバッグ情報を追加
                if no_match_items:
                    self.logger.info(f"No match items: {[item.original_query for item in no_match_items]}")
                
                # 全てexact matchまたはPhase1.5が無効な場合は終了
                if not no_match_items or not self.enable_phase15 or not self.phase15_component:
                    self.logger.info(f"Stopping iterations: no_match_items={len(no_match_items)}, phase15_enabled={self.enable_phase15}, phase15_component_exists={self.phase15_component is not None}")
                    break
                
                # Phase1.5で代替クエリを生成（履歴を含む）
                self.logger.info(f"Iteration {iteration_count}: Generating alternative queries with Phase1.5...")
                phase15_result = await self._execute_phase15_with_history(
                    input_data, no_match_items, current_search_result, phase15_history
                )
                
                if not phase15_result or not phase15_result.alternative_queries:
                    self.logger.warning(f"Iteration {iteration_count}: Phase1.5 failed to generate alternative queries")
                    break
                
                # 代替クエリで再検索
                self.logger.info(f"Iteration {iteration_count}: Re-searching with {len(phase15_result.alternative_queries)} alternative queries...")
                iteration_alternative_matches = await self._execute_alternative_searches(phase15_result.alternative_queries)
                
                # 代替検索結果をマージ
                for query, matches in iteration_alternative_matches.items():
                    if query not in all_alternative_matches:
                        all_alternative_matches[query] = []
                    all_alternative_matches[query].extend(matches)
                
                # Phase1.5履歴に追加
                phase15_history.append({
                    "iteration": iteration_count,
                    "no_match_items": [item.dict() for item in no_match_items],
                    "alternative_queries": [alt.dict() for alt in phase15_result.alternative_queries],
                    "total_alternatives_generated": phase15_result.total_alternatives_generated
                })
                
                # 新しい検索結果で次のイテレーションの準備
                # 代替検索で見つかったexact matchを元の結果に統合
                updated_matches = dict(current_search_result.matches)
                for query, alt_matches in iteration_alternative_matches.items():
                    for alt_match_data in alt_matches:
                        match = alt_match_data["match"]
                        if getattr(match, 'is_exact_match', False):
                            # exact matchが見つかった場合、元の結果を置き換え
                            updated_matches[query] = [match]
                            break
                
                # 更新された結果で新しいNutritionQueryOutputを作成
                current_search_result = NutritionQueryOutput(
                    matches=updated_matches,
                    search_summary=current_search_result.search_summary,
                    warnings=current_search_result.warnings,
                    errors=current_search_result.errors
                )
                
                self.logger.info(f"Iteration {iteration_count} completed. Continuing to next iteration...")
            
            # 最終結果を作成
            final_result = self._create_final_result_with_history(
                original_matches=current_search_result.matches,
                alternative_matches=all_alternative_matches,
                phase15_history=phase15_history,
                processing_time=(datetime.now() - start_time).total_seconds(),
                total_iterations=iteration_count
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Enhanced search completed in {processing_time:.2f}s after {iteration_count} iterations. Final exact match rate: {self._calculate_exact_match_rate(final_result):.1%}")
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error in enhanced nutrition search: {e}")
            # エラー時は初期検索結果を返す
            return self._create_final_result_with_history(
                original_matches=getattr(current_search_result, 'matches', {}) if 'current_search_result' in locals() else {},
                alternative_matches={},
                phase15_history=[],
                processing_time=(datetime.now() - start_time).total_seconds(),
                total_iterations=0,
                error=str(e)
            )
    
    def _identify_no_match_items(
        self, 
        search_result: NutritionQueryOutput, 
        input_data: NutritionQueryInput
    ) -> List[NoMatchItem]:
        """exact matchがない項目を特定"""
        no_match_items = []
        
        # 全ての検索クエリを取得
        all_queries = input_data.get_all_search_terms()
        dish_names = input_data.dish_names or []
        ingredient_names = input_data.ingredient_names or []
        
        self.logger.info(f"Checking {len(all_queries)} queries for exact matches...")
        
        for query in all_queries:
            # この項目の検索結果を取得
            query_matches = search_result.matches.get(query, [])
            
            # exact matchがあるかチェック
            has_exact_match = any(
                getattr(match, 'is_exact_match', False) for match in query_matches
            )
            
            self.logger.debug(f"Query '{query}': {len(query_matches)} matches, exact_match={has_exact_match}")
            
            if not has_exact_match:
                # 最高スコアの結果を取得
                best_match = None
                best_score = 0.0
                if query_matches:
                    best_match = max(query_matches, key=lambda x: getattr(x, 'score', 0))
                    best_score = getattr(best_match, 'score', 0.0)
                
                # 項目タイプを判定
                item_type = "dish" if query in dish_names else "ingredient"
                
                no_match_item = NoMatchItem(
                    original_query=query,
                    item_type=item_type,
                    confidence=1.0,  # Phase1での信頼度（ここでは仮に1.0）
                    search_results_count=len(query_matches),
                    best_match_score=best_score if best_match else None,
                    best_match_name=getattr(best_match, 'search_name', None) if best_match else None
                )
                
                no_match_items.append(no_match_item)
        
        return no_match_items
    
    async def _execute_phase15(
        self, 
        input_data: NutritionQueryInput, 
        no_match_items: List[NoMatchItem], 
        search_result: NutritionQueryOutput
    ) -> Optional[Any]:
        """Phase1.5を実行"""
        try:
            # Phase1結果を再構築（実際のPhase1結果がない場合の仮実装）
            phase1_result = self._reconstruct_phase1_result(input_data)
            
            # 検索コンテキストを作成
            search_context = {
                "databases_searched": ["elasticsearch"],
                "search_stats": {
                    "total_queries": len(input_data.get_all_search_terms()),
                    "successful_matches": len([q for q, matches in search_result.matches.items() 
                                             if any(getattr(m, 'is_exact_match', False) for m in matches)]),
                    "failed_searches": len(no_match_items)
                }
            }
            
            # Phase1.5入力を作成
            phase15_input = Phase15Input(
                image_path=getattr(input_data, 'image_path', ''),  # 画像パスが必要
                phase1_result=phase1_result,
                no_match_items=no_match_items,
                search_context=search_context
            )
            
            # Phase1.5実行
            return await self.phase15_component.process(phase15_input)
            
        except Exception as e:
            self.logger.error(f"Error executing Phase1.5: {e}")
            return None
    
    def _reconstruct_phase1_result(self, input_data: NutritionQueryInput) -> Dict[str, Any]:
        """NutritionQueryInputからPhase1結果を再構築"""
        dishes = []
        
        # 料理情報を再構築
        if input_data.dish_names:
            for dish_name in input_data.dish_names:
                dish_ingredients = []
                
                # この料理に関連する食材を推定
                if input_data.ingredient_names:
                    dish_ingredients = [
                        {"ingredient_name": ing, "confidence": 0.8}
                        for ing in input_data.ingredient_names
                    ]
                
                dishes.append({
                    "dish_name": dish_name,
                    "confidence": 0.9,
                    "ingredients": dish_ingredients
                })
        
        # 料理がない場合は食材のみの料理を作成
        elif input_data.ingredient_names:
            dishes.append({
                "dish_name": "Mixed ingredients",
                "confidence": 0.7,
                "ingredients": [
                    {"ingredient_name": ing, "confidence": 0.8}
                    for ing in input_data.ingredient_names
                ]
            })
        
        return {"dishes": dishes}
    
    async def _execute_alternative_searches(self, alternative_queries: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """代替クエリで再検索を実行"""
        alternative_matches = {}
        
        for alt_query in alternative_queries:
            try:
                # 代替クエリで新しい検索入力を作成
                # 全ての代替クエリを食材として扱う（シンプルなアプローチ）
                alt_input = NutritionQueryInput(
                    ingredient_names=[alt_query.alternative_query],
                    dish_names=[],
                    preferred_source="elasticsearch"
                )
                
                self.logger.debug(f"Searching alternative query: '{alt_query.alternative_query}' (strategy: {alt_query.strategy})")
                
                # 検索実行
                alt_result = await self.es_component.execute(alt_input)
                
                # 結果を保存
                if alt_result.matches:
                    for query, matches in alt_result.matches.items():
                        # 元のクエリをキーとして保存（複数の代替クエリ結果を蓄積）
                        if alt_query.original_query not in alternative_matches:
                            alternative_matches[alt_query.original_query] = []
                        
                        alternative_matches[alt_query.original_query].extend([
                            {
                                "match": match,
                                "alternative_query": alt_query.alternative_query,
                                "reasoning": alt_query.reasoning,
                                "strategy": alt_query.strategy
                            }
                            for match in matches
                        ])
                        
                        self.logger.debug(f"Found {len(matches)} matches for alternative query '{alt_query.alternative_query}'")
                
            except Exception as e:
                self.logger.error(f"Error searching with alternative query '{alt_query.alternative_query}': {e}")
                continue
        
        return alternative_matches
    
    async def _execute_phase15_with_history(
        self, 
        input_data: NutritionQueryInput, 
        no_match_items: List[NoMatchItem], 
        search_result: NutritionQueryOutput,
        phase15_history: List[Dict[str, Any]]
    ) -> Optional[Any]:
        """Phase1.5を履歴付きで実行"""
        try:
            # Phase1結果を再構築（実際のPhase1結果がない場合の仮実装）
            phase1_result = self._reconstruct_phase1_result(input_data)
            
            # 検索コンテキストを作成（履歴を含む）
            search_context = {
                "databases_searched": ["elasticsearch"],
                "search_stats": {
                    "total_queries": len(input_data.get_all_search_terms()),
                    "successful_matches": len([q for q, matches in search_result.matches.items() 
                                             if any(getattr(m, 'is_exact_match', False) for m in matches)]),
                    "failed_searches": len(no_match_items)
                },
                "phase15_history": phase15_history,  # 過去の試行履歴を追加
                "current_iteration": len(phase15_history) + 1
            }
            
            # 保存された画像データを使用
            image_bytes = self.current_image_bytes
            image_mime_type = self.current_image_mime_type
            
            if not image_bytes:
                self.logger.warning("No image data available for Phase1.5. Phase1.5 requires image data.")
                return None
            
            # 失敗したクエリのリストを作成
            failed_queries = [item.original_query for item in no_match_items]
            
            # 失敗履歴を作成
            failure_history = []
            for history_item in phase15_history:
                failure_history.append({
                    "iteration": history_item.get("iteration", 1),
                    "failed_queries": [item.get("original_query", "") for item in history_item.get("no_match_items", [])],
                    "alternative_queries": history_item.get("alternative_queries", [])
                })
            
            # Phase1.5入力を作成
            from ..models.phase1_5_models import Phase1_5Input
            phase15_input = Phase1_5Input(
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                phase1_result=phase1_result,
                failed_queries=failed_queries,
                failure_history=failure_history,
                iteration=len(phase15_history) + 1
            )
            
            # Phase1.5実行
            return await self.phase15_component.process(phase15_input)
            
        except Exception as e:
            self.logger.error(f"Error executing Phase1.5 with history: {e}")
            return None

    def _create_final_result_with_history(
        self,
        original_matches: Dict[str, List[Any]],
        alternative_matches: Dict[str, List[Dict[str, Any]]],
        phase15_history: List[Dict[str, Any]],
        processing_time: float,
        total_iterations: int,
        error: Optional[str] = None
    ) -> EnhancedSearchResult:
        """履歴付きで最終結果を作成"""
        
        # 統合された結果を作成
        final_consolidated_results = {}
        
        # 元の結果から exact match があるものを追加
        for query, matches in original_matches.items():
            exact_matches = [m for m in matches if getattr(m, 'is_exact_match', False)]
            if exact_matches:
                final_consolidated_results[query] = {
                    "match": exact_matches[0],  # 最初のexact matchを使用
                    "source": "original_search",
                    "is_exact_match": True
                }
        
        # 代替検索結果から exact match があるものを追加
        for original_query, alt_results in alternative_matches.items():
            if original_query not in final_consolidated_results:
                # exact matchを探す
                for alt_result in alt_results:
                    match = alt_result["match"]
                    if getattr(match, 'is_exact_match', False):
                        final_consolidated_results[original_query] = {
                            "match": match,
                            "source": "alternative_search",
                            "alternative_query": alt_result["alternative_query"],
                            "reasoning": alt_result["reasoning"],
                            "strategy": alt_result["strategy"],
                            "is_exact_match": True
                        }
                        break
        
        # 全てexact matchかどうかを判定
        total_original_queries = len(original_matches)
        all_exact_matches = len(final_consolidated_results) == total_original_queries and total_original_queries > 0
        
        return EnhancedSearchResult(
            original_matches=original_matches,
            alternative_matches=alternative_matches,
            final_consolidated_results=final_consolidated_results,
            all_exact_matches=all_exact_matches,
            processing_summary={
                "processing_time_seconds": processing_time,
                "original_queries_count": len(original_matches),
                "final_exact_matches_count": len(final_consolidated_results),
                "exact_match_rate": self._calculate_exact_match_rate_from_data(final_consolidated_results, original_matches),
                "phase15_enabled": self.enable_phase15,
                "total_phase15_iterations": total_iterations,
                "max_iterations_reached": total_iterations >= self.max_phase15_iterations,
                "convergence_achieved": all_exact_matches,
                "error": error
            },
            phase15_metadata={
                "total_iterations": total_iterations,
                "iteration_history": phase15_history,
                "final_iteration_successful": all_exact_matches
            }
        )
    
    def _calculate_exact_match_rate(self, result: EnhancedSearchResult) -> float:
        """exact match率を計算"""
        if not result.original_matches:
            return 0.0
        
        total_queries = len(result.original_matches)
        exact_matches = len(result.final_consolidated_results)
        
        return exact_matches / total_queries if total_queries > 0 else 0.0
    
    def _calculate_exact_match_rate_from_data(self, final_results: Dict, original_matches: Dict) -> float:
        """データからexact match率を計算"""
        if not original_matches:
            return 0.0
        
        total_queries = len(original_matches)
        exact_matches = len(final_results)
        
        return exact_matches / total_queries if total_queries > 0 else 0.0 