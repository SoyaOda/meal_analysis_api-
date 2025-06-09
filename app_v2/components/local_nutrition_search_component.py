#!/usr/bin/env python3
"""
Local Nutrition Search Component

USDA database queryを nutrition_db_experiment で実装したローカル検索システムに置き換える
"""

import os
import sys
import json
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path

from .base import BaseComponent
from ..models.nutrition_search_models import (
    NutritionQueryInput, NutritionQueryOutput, NutritionMatch
)
from ..config import get_settings

# nutrition_db_experimentのパスを追加
NUTRITION_DB_EXPERIMENT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "nutrition_db_experiment"
)
sys.path.append(NUTRITION_DB_EXPERIMENT_PATH)

class LocalNutritionSearchComponent(BaseComponent[NutritionQueryInput, NutritionQueryOutput]):
    """
    ローカル栄養データベース検索コンポーネント
    
    nutrition_db_experimentで実装したローカル検索システムを使用して食材名を検索し、
    純粋なローカル形式で結果を返します。
    """
    
    def __init__(self):
        super().__init__("LocalNutritionSearchComponent")
        
        # ローカル検索システムの初期化
        self._initialize_local_search_system()
        
        # unified_dbのみを使用
        self.unified_db_path = os.path.join(NUTRITION_DB_EXPERIMENT_PATH, "nutrition_db", "unified_nutrition_db.json")
        
        # ローカルデータベースの読み込み
        self.unified_database = self._load_unified_database()
        
        # nutrition_db_experimentのコンポーネント
        self.search_handler = None
        self.query_preprocessor = None
        
        self.logger.info(f"LocalNutritionSearchComponent initialized with {len(self.unified_database)} total items")

    def _initialize_local_search_system(self):
        """nutrition_db_experimentの検索システムを初期化"""
        try:
            # 検索システムのインポート（オプション）
            from api.search_handler import SearchHandler
            from api.query_preprocessor import QueryPreprocessor
            
            self.search_handler = SearchHandler()
            self.query_preprocessor = QueryPreprocessor()
            
            self.logger.info("Advanced local search system initialized")
        except ImportError as e:
            self.logger.warning(f"Advanced search system not available, will use direct database search: {e}")
        except Exception as e:
            self.logger.error(f"Failed to initialize advanced search system: {e}")
    
    def _load_unified_database(self) -> List[Dict[str, Any]]:
        """unified_nutrition_db.jsonを読み込み"""
        try:
            if os.path.exists(self.unified_db_path):
                with open(self.unified_db_path, 'r', encoding='utf-8') as f:
                    database = json.load(f)
                self.logger.info(f"Loaded unified_db: {len(database)} items")
                return database
            else:
                self.logger.warning(f"Unified database file not found: {self.unified_db_path}")
                return []
        except Exception as e:
            self.logger.error(f"Error loading unified_db: {e}")
            return []
    
    async def process(self, input_data: NutritionQueryInput) -> NutritionQueryOutput:
        """
        ローカル検索の主処理（純粋なローカル形式）
        
        Args:
            input_data: NutritionQueryInput
            
        Returns:
            NutritionQueryOutput: 純粋なローカル検索結果
        """
        self.logger.info(f"Starting local nutrition search for {len(input_data.get_all_search_terms())} terms")
        
        # input_dataを保存してスコア計算で使用
        self._current_input_data = input_data
        
        search_terms = input_data.get_all_search_terms()
        
        # 検索対象の詳細をログに記録
        self.log_processing_detail("search_terms", search_terms)
        self.log_processing_detail("ingredient_names", input_data.ingredient_names)
        self.log_processing_detail("dish_names", input_data.dish_names)
        self.log_processing_detail("total_search_terms", len(search_terms))
        self.log_processing_detail("search_method", "local_nutrition_database")
        self.log_processing_detail("preferred_source", input_data.preferred_source)
        
        matches = {}
        warnings = []
        errors = []
        
        successful_matches = 0
        total_searches = len(search_terms)
        
        # 各検索語彙について照合を実行
        for search_index, search_term in enumerate(search_terms):
            self.logger.debug(f"Searching local database for: {search_term}")
            
            # 検索開始をログ
            self.log_processing_detail(f"search_{search_index}_term", search_term)
            self.log_processing_detail(f"search_{search_index}_start", f"Starting local search for '{search_term}'")
            
            try:
                # ローカル検索の実行
                if self.search_handler and self.query_preprocessor:
                    # 高度な検索システムを使用
                    match_result = await self._advanced_local_search(search_term, search_index, input_data)
                else:
                    # フォールバック: シンプルな文字列マッチング
                    match_result = await self._simple_local_search(search_term, search_index, input_data)
                
                if match_result:
                    matches[search_term] = match_result
                    successful_matches += 1
                    self.logger.debug(f"Found local match for '{search_term}': ID {match_result.id}")
                else:
                    self.log_reasoning(
                        f"no_match_{search_index}",
                        f"No local database match found for '{search_term}' - may not exist in local nutrition database"
                    )
                    self.logger.warning(f"No local match found for: {search_term}")
                    warnings.append(f"No local match found for: {search_term}")
                    
            except Exception as e:
                error_msg = f"Local search error for '{search_term}': {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                
                # エラーの詳細をログ
                self.log_reasoning(
                    f"search_error_{search_index}",
                    f"Local database search error for '{search_term}': {str(e)}"
                )
        
        # 検索サマリーを作成（純粋なローカル形式）
        search_summary = {
            "total_searches": total_searches,
            "successful_matches": successful_matches,
            "failed_searches": total_searches - successful_matches,
            "match_rate_percent": round((successful_matches / total_searches) * 100, 1) if total_searches > 0 else 0,
            "search_method": "local_nutrition_database",
            "database_source": "nutrition_db_experiment",
            "preferred_source": input_data.preferred_source,
            "total_database_items": len(self.unified_database)
        }
        
        # 全体的な検索成功率をログ
        overall_success_rate = successful_matches / total_searches if total_searches > 0 else 0
        self.log_processing_detail("search_summary", search_summary)
        
        # 検索品質の評価をログ
        if overall_success_rate >= 0.8:
            self.log_reasoning("search_quality", "Excellent local search results with high match rate")
        elif overall_success_rate >= 0.6:
            self.log_reasoning("search_quality", "Good local search results with acceptable match rate")
        elif overall_success_rate >= 0.4:
            self.log_reasoning("search_quality", "Moderate local search results, some items may need manual review")
        else:
            self.log_reasoning("search_quality", "Poor local search results, many items not found in local database")
        
        result = NutritionQueryOutput(
            matches=matches,
            search_summary=search_summary,
            warnings=warnings if warnings else None,
            errors=errors if errors else None
        )
        
        self.logger.info(f"Local nutrition search completed: {successful_matches}/{total_searches} matches ({result.get_match_rate():.1%})")
        
        return result
    
    async def _advanced_local_search(self, search_term: str, search_index: int, input_data: NutritionQueryInput) -> Optional[NutritionMatch]:
        """
        nutrition_db_experimentの高度な検索システムを使用したローカル検索
        
        Args:
            search_term: 検索語彙
            search_index: 検索インデックス（ログ用）
            input_data: 入力データ（検索タイプ判定用）
            
        Returns:
            NutritionMatch または None
        """
        try:
            from api.search_handler import SearchRequest
            
            # 検索タイプの決定（料理か食材かの推定）
            db_type_filter = None  # 全データベースを検索
            
            # dish_namesに含まれる場合は料理として優先検索
            if search_term in input_data.dish_names:
                db_type_filter = "dish"
                self.log_processing_detail(f"search_{search_index}_type", "dish")
            elif search_term in input_data.ingredient_names:
                db_type_filter = "ingredient"
                self.log_processing_detail(f"search_{search_index}_type", "ingredient")
            
            # 検索リクエストの作成
            request = SearchRequest(
                query=search_term,
                db_type_filter=db_type_filter,
                size=5  # 上位5件を取得
            )
            
            # 検索実行
            response = self.search_handler.search(request)
            
            # 検索結果の詳細をログ
            self.log_processing_detail(f"search_{search_index}_results_count", response.total_hits)
            self.log_processing_detail(f"search_{search_index}_processing_time_ms", response.took_ms)
            self.log_processing_detail(f"search_{search_index}_processed_query", response.query_info.get('processed_query'))
            
            if response.results:
                # nutrition_db_experimentの検索システムが模擬データを返した場合は、実際のデータベース検索にフォールバック
                best_result = response.results[0]
                
                # 模擬データかどうかをチェック（IDが123456の場合は模擬データ）
                if best_result.get('id') == 123456:
                    self.logger.warning(f"nutrition_db_experiment returned mock data for '{search_term}', falling back to direct database search")
                    return await self._direct_database_search(search_term, search_index, input_data)
                
                # マッチ選択の推論理由をログ
                self.log_reasoning(
                    f"match_selection_{search_index}",
                    f"Selected local item '{best_result['search_name']}' (ID: {best_result['id']}) for search term '{search_term}' based on local search algorithm (score: {best_result.get('_score', 'N/A')})"
                )
                
                # 詳細なマッチ情報をログ
                self.log_processing_detail(f"search_{search_index}_selected_id", best_result['id'])
                self.log_processing_detail(f"search_{search_index}_selected_name", best_result['search_name'])
                self.log_processing_detail(f"search_{search_index}_data_type", best_result.get('data_type', 'unknown'))
                self.log_processing_detail(f"search_{search_index}_score", best_result.get('_score'))
                
                # NutritionMatch形式に変換
                return self._convert_to_nutrition_match(best_result, search_term)
            
            # 結果がない場合は直接データベース検索にフォールバック
            return await self._direct_database_search(search_term, search_index, input_data)
            
        except Exception as e:
            self.logger.error(f"Advanced local search failed for '{search_term}': {e}")
            # エラーの場合も直接データベース検索にフォールバック
            return await self._direct_database_search(search_term, search_index, input_data)
    
    async def _direct_database_search(self, search_term: str, search_index: int, input_data: NutritionQueryInput) -> Optional[NutritionMatch]:
        """
        ローカルデータベースファイルを直接検索
        
        Args:
            search_term: 検索語彙
            search_index: 検索インデックス（ログ用）
            input_data: 入力データ（検索タイプ判定用）
            
        Returns:
            NutritionMatch または None
        """
        try:
            self.log_processing_detail(f"search_{search_index}_method", "direct_database_search")
            
            search_term_lower = search_term.lower()
            best_match = None
            best_score = 0
            
            # unified_databaseから直接検索
            for item in self.unified_database:
                # search_nameフィールドで検索
                if 'search_name' not in item:
                    continue
                    
                item_name = item['search_name'].lower()
                score = 0
                
                # スコアリングアルゴリズム
                if search_term_lower == item_name:
                    score = 1.0  # 完全一致
                elif search_term_lower in item_name:
                    # 部分一致（語順考慮）
                    if item_name.startswith(search_term_lower):
                        score = 0.9  # 前方一致
                    elif item_name.endswith(search_term_lower):
                        score = 0.8  # 後方一致
                    else:
                        score = 0.7  # 中間一致
                elif item_name in search_term_lower:
                    score = 0.6  # 逆部分一致
                else:
                    # 単語レベルの一致をチェック
                    search_words = search_term_lower.split()
                    item_words = item_name.split()
                    
                    common_words = set(search_words) & set(item_words)
                    if common_words:
                        score = len(common_words) / max(len(search_words), len(item_words)) * 0.5
                
                # data_type優先度によるボーナス
                data_type = item.get('data_type', 'unknown')
                db_bonus = 1.0
                
                # dish_namesに含まれる場合は料理データを優先
                if search_term in input_data.dish_names and data_type == 'dish':
                    db_bonus = 1.2
                # ingredient_namesに含まれる場合は食材データを優先
                elif search_term in input_data.ingredient_names and data_type == 'ingredient':
                    db_bonus = 1.2
                
                final_score = score * db_bonus
                
                if final_score > best_score:
                    best_score = final_score
                    best_match = item.copy()
            
            if best_match and best_score > 0.1:  # 最低閾値
                # マッチスコア情報を追加
                best_match['_match_score'] = best_score
                
                self.log_reasoning(
                    f"match_selection_{search_index}",
                    f"Selected local item '{best_match['search_name']}' (ID: {best_match.get('id', 'N/A')}) for search term '{search_term}' using direct database search (score: {best_score:.3f})"
                )
                
                # 詳細なマッチ情報をログ
                self.log_processing_detail(f"search_{search_index}_selected_id", best_match.get('id', 'N/A'))
                self.log_processing_detail(f"search_{search_index}_selected_name", best_match['search_name'])
                self.log_processing_detail(f"search_{search_index}_data_type", best_match.get('data_type', 'unknown'))
                self.log_processing_detail(f"search_{search_index}_match_score", best_score)
                
                return self._convert_to_nutrition_match(best_match, search_term)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Direct database search failed for '{search_term}': {e}")
            return None
    
    async def _simple_local_search(self, search_term: str, search_index: int, input_data: NutritionQueryInput) -> Optional[NutritionMatch]:
        """
        シンプルな文字列マッチングによるフォールバック検索（実際のデータベース使用）
        
        Args:
            search_term: 検索語彙
            search_index: 検索インデックス（ログ用）
            input_data: 入力データ（検索タイプ判定用）
            
        Returns:
            NutritionMatch または None
        """
        # 高度検索システムが利用できない場合は、直接データベース検索を使用
        return await self._direct_database_search(search_term, search_index, input_data)
    
    def _convert_to_nutrition_match(self, local_item: Dict[str, Any], search_term: str) -> NutritionMatch:
        """
        ローカルデータベースアイテムをNutritionMatch形式に変換（簡素化版）
        
        Args:
            local_item: ローカルデータベースのアイテム
            search_term: 元の検索語彙
            
        Returns:
            NutritionMatch: 変換されたマッチ結果（簡素化されたローカル形式）
        """
        # IDの取得
        item_id = local_item.get('id', 0)
        
        # 基本情報の取得
        search_name = local_item.get('search_name', search_term)
        description = local_item.get('description')  # brandedの場合のみ存在
        data_type = local_item.get('data_type', 'unknown')  # db_type → data_typeに変更
        
        # 栄養データ（100gあたり正規化済み）
        nutrition = local_item.get('nutrition', {})
        weight = local_item.get('weight')
        
        # マッチスコア
        score = local_item.get('_match_score') or local_item.get('_score') or 1.0
        
        # スコア計算の詳細分析
        search_term_lower = search_term.lower()
        item_name_lower = search_name.lower()
        
        # 基本マッチタイプの判定
        match_type = "unknown"
        base_score = 0.0
        if search_term_lower == item_name_lower:
            match_type = "exact_match"
            base_score = 1.0
        elif search_term_lower in item_name_lower:
            if item_name_lower.startswith(search_term_lower):
                match_type = "prefix_match"
                base_score = 0.9
            elif item_name_lower.endswith(search_term_lower):
                match_type = "suffix_match"
                base_score = 0.8
            else:
                match_type = "contains_match"
                base_score = 0.7
        elif item_name_lower in search_term_lower:
            match_type = "reverse_contains"
            base_score = 0.6
        else:
            # 単語レベルの一致
            search_words = set(search_term_lower.split())
            item_words = set(item_name_lower.split())
            common_words = search_words & item_words
            if common_words:
                match_type = "word_match"
                base_score = len(common_words) / max(len(search_words), len(item_words)) * 0.5
        
        # データタイプボーナスの計算
        type_bonus = 1.0
        if hasattr(self, '_current_input_data'):
            input_data = self._current_input_data
            if search_term in input_data.dish_names and data_type == 'dish':
                type_bonus = 1.2
            elif search_term in input_data.ingredient_names and data_type == 'ingredient':
                type_bonus = 1.2
        
        # 検索メタデータ（詳細な計算情報を含む）
        search_metadata = {
            "search_term": search_term,
            "match_score": score,
            "score_breakdown": {
                "match_type": match_type,
                "base_score": round(base_score, 3),
                "type_bonus": round(type_bonus, 3),
                "final_score": round(base_score * type_bonus, 3)
            },
            "calculation": f"{base_score:.3f} × {type_bonus:.3f} = {score:.3f}"
        }
        
        # NutritionMatchオブジェクトの作成（簡素化版）
        return NutritionMatch(
            id=item_id,
            search_name=search_name,
            description=description,
            data_type=data_type,  # db_type → data_typeに変更
            nutrition=nutrition,
            weight=weight,
            score=score,
            search_metadata=search_metadata
        ) 