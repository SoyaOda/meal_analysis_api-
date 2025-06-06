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
from ..models.usda_models import USDAQueryInput, USDAQueryOutput
from ..models.nutrition_search_models import (
    NutritionQueryInput, NutritionQueryOutput, NutritionMatch, NutritionNutrient,
    convert_usda_query_input_to_nutrition, convert_nutrition_to_usda_query_output
)
from ..config import get_settings

# nutrition_db_experimentのパスを追加
NUTRITION_DB_EXPERIMENT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "nutrition_db_experiment"
)
sys.path.append(NUTRITION_DB_EXPERIMENT_PATH)

class LocalNutritionSearchComponent(BaseComponent[USDAQueryInput, USDAQueryOutput]):
    """
    ローカル栄養データベース検索コンポーネント
    
    nutrition_db_experimentで実装したローカル検索システムを使用して食材名を検索し、
    USDAQueryComponentと互換性のある結果を返します。
    
    内部的には汎用的なNutritionQueryモデルを使用し、
    外部インターフェースではUSDAQueryモデルとの互換性を保持します。
    """
    
    def __init__(self):
        super().__init__("LocalNutritionSearchComponent")
        
        # ローカル検索システムの初期化
        self._initialize_local_search_system()
        
        # ローカルデータベースファイルのパス（正しいパスに修正）
        self.local_db_paths = {
            "dish_db": os.path.join(NUTRITION_DB_EXPERIMENT_PATH, "nutrition_db", "dish_db.json"),
            "ingredient_db": os.path.join(NUTRITION_DB_EXPERIMENT_PATH, "nutrition_db", "ingredient_db.json"),
            "branded_db": os.path.join(NUTRITION_DB_EXPERIMENT_PATH, "nutrition_db", "branded_db.json"),
            "unified_db": os.path.join(NUTRITION_DB_EXPERIMENT_PATH, "nutrition_db", "unified_nutrition_db.json")
        }
        
        # ローカルデータベースの読み込み
        self.local_databases = self._load_local_databases()
    
    def _initialize_local_search_system(self):
        """ローカル検索システムの初期化"""
        try:
            # nutrition_db_experimentの検索コンポーネントをインポート
            search_service_path = os.path.join(NUTRITION_DB_EXPERIMENT_PATH, "search_service")
            sys.path.append(search_service_path)
            
            from nlp.query_preprocessor import FoodQueryPreprocessor
            from api.search_handler import NutritionSearchHandler, SearchRequest
            
            self.query_preprocessor = FoodQueryPreprocessor()
            self.search_handler = NutritionSearchHandler()
            
            self.logger.info("Local nutrition search system initialized successfully")
            
        except ImportError as e:
            self.logger.error(f"Failed to import local search components: {e}")
            # フォールバック: シンプルな文字列マッチング
            self.query_preprocessor = None
            self.search_handler = None
            self.logger.warning("Using fallback simple string matching for local search")
        except Exception as e:
            self.logger.error(f"Error initializing local search system: {e}")
            self.query_preprocessor = None
            self.search_handler = None
    
    def _load_local_databases(self) -> Dict[str, List[Dict[str, Any]]]:
        """ローカルデータベースファイルを読み込み"""
        databases = {}
        
        for db_name, db_path in self.local_db_paths.items():
            try:
                if os.path.exists(db_path):
                    with open(db_path, 'r', encoding='utf-8') as f:
                        databases[db_name] = json.load(f)
                    self.logger.info(f"Loaded {db_name}: {len(databases[db_name])} items")
                else:
                    self.logger.warning(f"Local database file not found: {db_path}")
                    databases[db_name] = []
            except Exception as e:
                self.logger.error(f"Error loading {db_name}: {e}")
                databases[db_name] = []
        
        total_items = sum(len(db) for db in databases.values())
        self.logger.info(f"Total local database items loaded: {total_items}")
        
        return databases
    
    async def process(self, input_data: USDAQueryInput) -> USDAQueryOutput:
        """
        ローカル検索の主処理（USDA互換インターフェース）
        
        Args:
            input_data: USDAQueryInput
            
        Returns:
            USDAQueryOutput: USDA互換のローカル検索結果
        """
        # USDAQueryInputを汎用NutritionQueryInputに変換
        nutrition_input = convert_usda_query_input_to_nutrition(input_data)
        nutrition_input.preferred_source = "local_database"
        
        # 内部的な汎用検索処理を実行
        nutrition_result = await self._process_nutrition_search(nutrition_input)
        
        # 結果をUSDAQueryOutput形式に変換して返す
        return convert_nutrition_to_usda_query_output(nutrition_result)
    
    async def _process_nutrition_search(self, input_data: NutritionQueryInput) -> NutritionQueryOutput:
        """
        汎用栄養検索の主処理
        
        Args:
            input_data: NutritionQueryInput
            
        Returns:
            NutritionQueryOutput: 汎用検索結果
        """
        self.logger.info(f"Starting local nutrition search for {len(input_data.get_all_search_terms())} terms")
        
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
        
        # 検索サマリーを作成（汎用形式）
        search_summary = {
            "total_searches": total_searches,
            "successful_matches": successful_matches,
            "failed_searches": total_searches - successful_matches,
            "match_rate_percent": round((successful_matches / total_searches) * 100, 1) if total_searches > 0 else 0,
            "search_method": "local_nutrition_database",
            "database_source": "nutrition_db_experiment",
            "preferred_source": input_data.preferred_source,
            "total_database_items": sum(len(db) for db in self.local_databases.values())
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
                self.log_processing_detail(f"search_{search_index}_db_type", best_result['db_type'])
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
            best_db_source = None
            
            # 検索優先順位の決定
            search_order = []
            
            # dish_namesに含まれる場合は料理データベースを優先
            if search_term in input_data.dish_names:
                search_order = ["dish_db", "unified_db", "ingredient_db", "branded_db"]
            elif search_term in input_data.ingredient_names:
                search_order = ["ingredient_db", "unified_db", "dish_db", "branded_db"]
            else:
                search_order = ["unified_db", "dish_db", "ingredient_db", "branded_db"]
            
            # 各データベースで検索（優先順位順）
            for db_name in search_order:
                if db_name not in self.local_databases:
                    continue
                    
                database = self.local_databases[db_name]
                
                for item in database:
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
                    
                    # データベース優先度によるボーナス
                    db_bonus = 1.0
                    if db_name == search_order[0]:
                        db_bonus = 1.2  # 第一優先データベース
                    elif db_name == search_order[1]:
                        db_bonus = 1.1  # 第二優先データベース
                    
                    final_score = score * db_bonus
                    
                    if final_score > best_score:
                        best_score = final_score
                        best_match = item.copy()
                        best_db_source = db_name
            
            if best_match and best_score > 0.1:  # 最低閾値
                # データベースソース情報を追加
                best_match['_db_source'] = best_db_source
                best_match['_match_score'] = best_score
                
                self.log_reasoning(
                    f"match_selection_{search_index}",
                    f"Selected local item '{best_match['search_name']}' (ID: {best_match.get('id', 'N/A')}) for search term '{search_term}' from {best_db_source} using direct database search (score: {best_score:.3f})"
                )
                
                # 詳細なマッチ情報をログ
                self.log_processing_detail(f"search_{search_index}_selected_id", best_match.get('id', 'N/A'))
                self.log_processing_detail(f"search_{search_index}_selected_name", best_match['search_name'])
                self.log_processing_detail(f"search_{search_index}_db_source", best_db_source)
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
        ローカルデータベースアイテムをNutritionMatch形式に変換
        
        Args:
            local_item: ローカルデータベースのアイテム
            search_term: 元の検索語彙
            
        Returns:
            NutritionMatch: 変換されたマッチ結果
        """
        # 栄養素情報の変換
        nutrients = []
        if 'nutrition' in local_item and local_item['nutrition']:
            nutrition_data = local_item['nutrition']
            
            # 主要栄養素のマッピング（ローカルDBの形式に合わせて調整）
            nutrient_mapping = {
                'calories_kcal': ('Energy', '208', 'kcal'),
                'calories': ('Energy', '208', 'kcal'),  # 別名対応
                'protein_g': ('Protein', '203', 'g'),
                'protein': ('Protein', '203', 'g'),  # 別名対応
                'fat_g': ('Total lipid (fat)', '204', 'g'),
                'fat': ('Total lipid (fat)', '204', 'g'),  # 別名対応
                'carbohydrates_g': ('Carbohydrate, by difference', '205', 'g'),
                'carbs': ('Carbohydrate, by difference', '205', 'g'),  # 別名対応
                'carbohydrates': ('Carbohydrate, by difference', '205', 'g'),  # 別名対応
                'fiber_g': ('Fiber, total dietary', '291', 'g'),
                'fiber': ('Fiber, total dietary', '291', 'g'),  # 別名対応
                'sugars_g': ('Sugars, total', '269', 'g'),
                'sugars': ('Sugars, total', '269', 'g'),  # 別名対応
                'sodium_mg': ('Sodium, Na', '307', 'mg'),
                'sodium': ('Sodium, Na', '307', 'mg')  # 別名対応
            }
            
            for local_key, (usda_name, nutrient_number, unit) in nutrient_mapping.items():
                if local_key in nutrition_data and nutrition_data[local_key] is not None:
                    try:
                        amount = float(nutrition_data[local_key])
                        nutrients.append(NutritionNutrient(
                            name=usda_name,
                            amount=amount,
                            unit_name=unit,
                            nutrient_id=None,  # ローカルデータにはIDがない
                            nutrient_number=nutrient_number
                        ))
                    except (ValueError, TypeError):
                        # 数値に変換できない場合はスキップ
                        continue
        
        # IDの取得（様々な形式に対応）
        item_id = local_item.get('id') or local_item.get('fdc_id') or local_item.get('_id') or 0
        
        # データタイプの決定
        data_type = "Local_Unknown"
        if 'db_type' in local_item:
            data_type = f"Local_{local_item['db_type'].title()}"
        elif '_db_source' in local_item:
            db_source = local_item['_db_source'].replace('_db', '')
            data_type = f"Local_{db_source.title()}"
        
        # 説明の取得（様々なフィールド名に対応）
        description = (
            local_item.get('search_name') or 
            local_item.get('description') or 
            local_item.get('name') or 
            search_term
        )
        
        # ブランド情報（branded_dbの場合）
        brand_owner = local_item.get('brand_owner') or local_item.get('brand_name')
        
        # 食材リスト（dish_dbの場合）
        ingredients_text = None
        if 'ingredients' in local_item:
            if isinstance(local_item['ingredients'], list):
                ingredients_text = ', '.join(local_item['ingredients'])
            elif isinstance(local_item['ingredients'], str):
                ingredients_text = local_item['ingredients']
        
        # マッチスコア
        score = local_item.get('_match_score') or local_item.get('_score') or 1.0
        
        # オリジナルデータの保存
        original_data = {
            "source": "local_nutrition_database",
            "original_data": local_item,
            "search_term": search_term,
            "db_source": local_item.get('_db_source', 'unknown'),
            "match_score": score
        }
        
        # NutritionMatchオブジェクトの作成
        return NutritionMatch(
            id=item_id,
            description=description,
            data_type=data_type,
            source="local_database",
            brand_owner=brand_owner,
            ingredients_text=ingredients_text,
            nutrients=nutrients,
            score=score,
            original_data=original_data
        ) 