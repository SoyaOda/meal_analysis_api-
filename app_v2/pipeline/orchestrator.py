import uuid
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from ..components import Phase1Component, ElasticsearchNutritionSearchComponent, MyNetDiaryNutritionSearchComponent, FuzzyIngredientSearchComponent, NutritionCalculationComponent
from ..services.deepinfra_service import DeepInfraService
from ..models import (
    Phase1Input, Phase1Output,
    NutritionQueryInput
)
from ..models.nutrition_calculation_models import NutritionCalculationInput
from ..config import get_settings
from .result_manager import ResultManager

logger = logging.getLogger(__name__)


class MealAnalysisPipeline:
    """
    食事分析パイプラインのオーケストレーター
    
    4つのフェーズを統合して完全な分析を実行します。
    """
    
    def __init__(self, use_local_nutrition_search: Optional[bool] = None, use_elasticsearch_search: Optional[bool] = None, use_mynetdiary_specialized: Optional[bool] = False, use_fuzzy_matching: Optional[bool] = None):
        """
        パイプラインの初期化
        
        Args:
            use_local_nutrition_search: 廃止予定（互換性のため残存）
            use_elasticsearch_search: Elasticsearch栄養データベース検索を使用するかどうか
                                    None: 設定ファイルから自動取得（デフォルト: True）
                                    True: ElasticsearchNutritionSearchComponent使用（推奨）
                                    False: ElasticsearchNutritionSearchComponent使用（デフォルト設定）
            use_mynetdiary_specialized: MyNetDiary専用検索を使用するかどうか
                                      True: MyNetDiaryNutritionSearchComponent使用（ingredient厳密検索）
                                      False: 従来のElasticsearch検索使用（デフォルト）
            use_fuzzy_matching: ファジーマッチング検索を使用するかどうか
                              True: FuzzyIngredientSearchComponent使用（高精度ファジーマッチング）
                              False: 従来の検索使用
                              None: 設定ファイルから自動取得（デフォルト: True）
        """
        self.pipeline_id = str(uuid.uuid4())[:8]
        self.settings = get_settings()
        
        # Elasticsearch検索優先度の決定
        if use_elasticsearch_search is not None:
            self.use_elasticsearch_search = use_elasticsearch_search
        elif hasattr(self.settings, 'USE_ELASTICSEARCH_SEARCH'):
            self.use_elasticsearch_search = self.settings.USE_ELASTICSEARCH_SEARCH
        else:
            # デフォルトはElasticsearch使用
            self.use_elasticsearch_search = True
        
        # レガシーパラメータは無視（常にElasticsearch使用）
        self.use_local_nutrition_search = False
        
        # ファジーマッチング使用の決定
        if use_fuzzy_matching is not None:
            self.use_fuzzy_matching = use_fuzzy_matching
        elif hasattr(self.settings, 'fuzzy_search_enabled'):
            self.use_fuzzy_matching = self.settings.fuzzy_search_enabled
        else:
            # デフォルトはファジーマッチング使用
            self.use_fuzzy_matching = True
        
        # Vision Serviceの初期化
        # DeepInfraServiceを使用（フォールバックなし）
        self.vision_service = DeepInfraService()
        logger.info("Using DeepInfra Gemma 3 for image analysis")
        
        # コンポーネントの初期化
        self.phase1_component = Phase1Component(vision_service=self.vision_service)
        
        # 栄養データベース検索コンポーネントの選択
        if self.use_fuzzy_matching:
            # 新しいファジーマッチング検索コンポーネント（推奨）
            self.nutrition_search_component = FuzzyIngredientSearchComponent()
            self.search_component_name = "FuzzyIngredientSearchComponent"
            logger.info("Using Fuzzy Ingredient Search (5-tier cascade, high-precision matching)")
        elif use_mynetdiary_specialized:
            # MyNetDiary専用検索コンポーネント
            self.nutrition_search_component = MyNetDiaryNutritionSearchComponent(
                results_per_db=5
            )
            self.search_component_name = "MyNetDiaryNutritionSearchComponent"
            logger.info("Using MyNetDiary specialized nutrition search (ingredient strict matching)")
        else:
            # 従来のElasticsearch検索コンポーネント
            self.nutrition_search_component = ElasticsearchNutritionSearchComponent(
                strategic_search_mode=True,
                results_per_db=5
            )
            self.search_component_name = "ElasticsearchNutritionSearchComponent"
            logger.info("Using Elasticsearch nutrition database search (high-performance, multi-DB mode)")
            
        # 栄養計算コンポーネントの初期化
        self.nutrition_calculation_component = NutritionCalculationComponent()
        
        # TODO: Phase2Componentを追加
        
        self.logger = logging.getLogger(f"{__name__}.{self.pipeline_id}")
        
    async def execute_complete_analysis(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        optional_text: Optional[str] = None,
        save_detailed_logs: bool = True,
        test_execution: bool = False,
        test_results_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        完全な食事分析を実行
        
        Args:
            image_bytes: 画像データ
            image_mime_type: 画像のMIMEタイプ
            optional_text: オプションのテキスト
            save_detailed_logs: 分析ログを保存するかどうか
            
        Returns:
            完全な分析結果
        """
        analysis_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()
        
        # ResultManagerの初期化
        if save_detailed_logs:
            if test_execution and test_results_dir:
                # テスト実行時はテスト結果ディレクトリ内のapi_calls/フォルダに保存
                api_calls_dir = f"{test_results_dir}/api_calls"
                result_manager = ResultManager(analysis_id, save_directory=api_calls_dir)
            else:
                # 通常の実行時は既存の保存先
                result_manager = ResultManager(analysis_id)
        else:
            result_manager = None
        
        self.logger.info(f"[{analysis_id}] Starting complete meal analysis pipeline")
        self.logger.info(f"[{analysis_id}] Nutrition search method: Elasticsearch (high-performance)")
        
        try:
            # === Phase 1: 画像分析 ===
            self.logger.info(f"[{analysis_id}] Phase 1: Image analysis")
            
            phase1_input = Phase1Input(
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                optional_text=optional_text
            )
            
            # Phase1の詳細ログを作成
            phase1_log = result_manager.create_execution_log("Phase1Component", f"{analysis_id}_phase1") if result_manager else None
            
            phase1_result = await self.phase1_component.execute(phase1_input, phase1_log)
            
            self.logger.info(f"[{analysis_id}] Phase 1 completed - Detected {len(phase1_result.dishes)} dishes")
            
            # === Nutrition Search Phase: データベース照合 ===
            if self.use_fuzzy_matching:
                search_phase_name = "Fuzzy Ingredient Search"
            else:
                search_phase_name = "Elasticsearch Search"
            self.logger.info(f"[{analysis_id}] {search_phase_name} Phase: Database matching")
            
            # === 統一された栄養検索入力を作成 ===
            if self.use_fuzzy_matching:
                # ファジーマッチング検索の場合は、食材名のリストを直接渡す
                ingredient_names = phase1_result.get_all_ingredient_names()
                nutrition_search_input = [{"name": name} for name in ingredient_names]
            else:
                # 従来のElasticsearch検索を使用
                preferred_source = "elasticsearch"
                nutrition_search_input = NutritionQueryInput(
                    ingredient_names=phase1_result.get_all_ingredient_names(),
                    dish_names=phase1_result.get_all_dish_names(),
                    preferred_source=preferred_source
                )
            
            # Nutrition Searchの詳細ログを作成
            search_log = result_manager.create_execution_log(self.search_component_name, f"{analysis_id}_nutrition_search") if result_manager else None
            
            if self.use_fuzzy_matching:
                # ファジーマッチングコンポーネントの場合はprocessメソッドを使用
                nutrition_search_result = await self.nutrition_search_component.process(nutrition_search_input)
            else:
                # 従来のコンポーネントの場合はexecuteメソッドを使用
                nutrition_search_result = await self.nutrition_search_component.execute(nutrition_search_input, search_log)
            
            self.logger.info(f"[{analysis_id}] {search_phase_name} completed - {nutrition_search_result.get_match_rate():.1%} match rate")
            
            # === Nutrition Calculation Phase: 栄養計算 ===
            self.logger.info(f"[{analysis_id}] Nutrition Calculation Phase: Computing nutrition values")
            
            nutrition_calculation_input = NutritionCalculationInput(
                phase1_result=phase1_result,
                nutrition_search_result=nutrition_search_result
            )
            
            # Nutrition Calculationの詳細ログを作成
            calculation_log = result_manager.create_execution_log("NutritionCalculationComponent", f"{analysis_id}_nutrition_calculation") if result_manager else None
            
            nutrition_calculation_result = await self.nutrition_calculation_component.execute(nutrition_calculation_input, calculation_log)
            
            self.logger.info(f"[{analysis_id}] Nutrition Calculation completed - {nutrition_calculation_result.meal_nutrition.calculation_summary['total_ingredients']} ingredients, {nutrition_calculation_result.meal_nutrition.total_nutrition.calories:.1f} kcal total")
            
            # === 結果の構築 ===
            
            # Phase1の結果を辞書形式に変換（構造化データを含む）
            phase1_dict = {
                "detected_food_items": [
                    {
                        "item_name": item.item_name,
                        "confidence": item.confidence,
                        "attributes": [
                            {
                                "type": attr.type.value if hasattr(attr.type, 'value') else str(attr.type),
                                "value": attr.value,
                                "confidence": attr.confidence
                            }
                            for attr in item.attributes
                        ],
                        "brand": item.brand or "",
                        "category_hints": item.category_hints,
                        "negative_cues": item.negative_cues
                    }
                    for item in phase1_result.detected_food_items
                ],
                "dishes": [
                    {
                        "dish_name": dish.dish_name,
                        "confidence": dish.confidence,
                        "ingredients": [
                            {
                                "ingredient_name": ing.ingredient_name,
                                "confidence": ing.confidence,
                                "weight_g": ing.weight_g
                            }
                            for ing in dish.ingredients
                        ],
                        "attributes": [
                            {
                                "type": attr.type.value if hasattr(attr.type, 'value') else str(attr.type),
                                "value": attr.value,
                                "confidence": attr.confidence
                            }
                            for attr in dish.detected_attributes
                        ]
                    }
                    for dish in phase1_result.dishes
                ],
                "analysis_confidence": phase1_result.analysis_confidence,
                "processing_notes": phase1_result.processing_notes
            }
            
            # 栄養計算結果を辞書形式に変換
            nutrition_calculation_dict = {
                "dishes": [
                    {
                        "dish_name": dish.dish_name,
                        "confidence": dish.confidence,
                        "ingredients": [
                            {
                                "ingredient_name": ing.ingredient_name,
                                "weight_g": ing.weight_g,
                                "nutrition_per_100g": ing.nutrition_per_100g,
                                "calculated_nutrition": {
                                    "calories": ing.calculated_nutrition.calories,
                                    "protein": ing.calculated_nutrition.protein,
                                    "fat": ing.calculated_nutrition.fat,
                                    "carbs": ing.calculated_nutrition.carbs,
                                    "fiber": ing.calculated_nutrition.fiber,
                                    "sugar": ing.calculated_nutrition.sugar,
                                    "sodium": ing.calculated_nutrition.sodium
                                },
                                "source_db": ing.source_db,
                                "calculation_notes": ing.calculation_notes
                            }
                            for ing in dish.ingredients
                        ],
                        "total_nutrition": {
                            "calories": dish.total_nutrition.calories,
                            "protein": dish.total_nutrition.protein,
                            "fat": dish.total_nutrition.fat,
                            "carbs": dish.total_nutrition.carbs,
                            "fiber": dish.total_nutrition.fiber,
                            "sugar": dish.total_nutrition.sugar,
                            "sodium": dish.total_nutrition.sodium
                        },
                        "calculation_metadata": dish.calculation_metadata
                    }
                    for dish in nutrition_calculation_result.meal_nutrition.dishes
                ],
                "total_nutrition": {
                    "calories": nutrition_calculation_result.meal_nutrition.total_nutrition.calories,
                    "protein": nutrition_calculation_result.meal_nutrition.total_nutrition.protein,
                    "fat": nutrition_calculation_result.meal_nutrition.total_nutrition.fat,
                    "carbs": nutrition_calculation_result.meal_nutrition.total_nutrition.carbs,
                    "fiber": nutrition_calculation_result.meal_nutrition.total_nutrition.fiber,
                    "sugar": nutrition_calculation_result.meal_nutrition.total_nutrition.sugar,
                    "sodium": nutrition_calculation_result.meal_nutrition.total_nutrition.sodium
                },
                "calculation_summary": nutrition_calculation_result.meal_nutrition.calculation_summary,
                "warnings": nutrition_calculation_result.meal_nutrition.warnings
            }
            
            # 検索方法の特定（常にElasticsearch）
            search_method = "elasticsearch"
            search_api_method = "elasticsearch"
            
            # 完全分析結果の構築
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            complete_result = {
                "analysis_id": analysis_id,
                "phase1_result": phase1_dict,
                "nutrition_search_result": {
                    "matches_count": len(nutrition_search_result.matches),
                    "match_rate": nutrition_search_result.get_match_rate(),
                    "search_summary": nutrition_search_result.search_summary,
                    "search_method": search_method
                },

                "processing_summary": {
                    "total_dishes": len(phase1_result.dishes),
                    "total_ingredients": len(phase1_result.get_all_ingredient_names()),
                    "nutrition_search_match_rate": self._calculate_match_rate_display(nutrition_search_input, nutrition_search_result),
                    "nutrition_calculation_status": "completed",
                    "total_calories": nutrition_calculation_result.meal_nutrition.total_nutrition.calories,
                    "pipeline_status": "completed",
                    "processing_time_seconds": processing_time,
                    "search_method": search_method
                },
                # 最終栄養結果
                "final_nutrition_result": nutrition_calculation_dict,
                "metadata": {
                    "pipeline_version": "v2.0",
                    "timestamp": datetime.now().isoformat(),
                    "components_used": ["Phase1Component", self.search_component_name, "NutritionCalculationComponent"],
                    "nutrition_search_method": search_api_method
                }
            }
            
            # ResultManagerに最終結果を設定
            if result_manager:
                result_manager.set_final_result(complete_result)
                result_manager.finalize_pipeline()
            
            # 結果の保存
            saved_files = {}
            if save_detailed_logs and result_manager:
                # 新しいフェーズ別保存方式
                saved_files = result_manager.save_phase_results()
                complete_result["analysis_folder"] = result_manager.get_analysis_folder_path()
                complete_result["saved_files"] = saved_files
                
                logger.info(f"[{analysis_id}] Analysis logs saved to folder: {result_manager.get_analysis_folder_path()}")
                logger.info(f"[{analysis_id}] Saved {len(saved_files)} files across all phases")
            

            
            self.logger.info(f"[{analysis_id}] Complete analysis pipeline finished successfully in {processing_time:.2f}s")
            
            return complete_result
            
        except Exception as e:
            self.logger.error(f"[{analysis_id}] Complete analysis failed: {str(e)}", exc_info=True)
            
            # エラー時もResultManagerを保存
            if result_manager:
                result_manager.set_final_result({"error": str(e), "timestamp": datetime.now().isoformat()})
                result_manager.finalize_pipeline()
                error_saved_files = result_manager.save_phase_results()
                self.logger.info(f"[{analysis_id}] Error analysis logs saved to folder: {result_manager.get_analysis_folder_path()}")
            
            raise
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """パイプライン情報を取得"""
        search_method = "elasticsearch"
            
        return {
            "pipeline_id": self.pipeline_id,
            "version": "v2.0",
            "nutrition_search_method": search_method,
            "components": [
                {
                    "component_name": "Phase1Component",
                    "component_type": "analysis",
                    "execution_count": 0
                },
                {
                    "component_name": self.search_component_name,
                    "component_type": "nutrition_search",
                    "execution_count": 0
                },
                {
                    "component_name": "NutritionCalculationComponent",
                    "component_type": "nutrition_calculation",
                    "execution_count": 0
                }
            ]
        } 

    def _calculate_match_rate_display(self, nutrition_search_input, nutrition_search_result):
        """マッチ率の表示文字列を計算（重複食材を考慮した改良版）"""
        if self.use_fuzzy_matching:
            # ファジーマッチングの場合は辞書のリスト形式: [{"name": "ingredient_name"}, ...]
            ingredient_names = [item["name"] for item in nutrition_search_input]
            total_ingredients = len(ingredient_names)  # 重複含む総食材数
            unique_ingredients = len(set(ingredient_names))  # ユニーク食材数
            successful_matches = len(nutrition_search_result.matches)  # マッチしたユニーク食材数
            
            # 重複がある場合の表示
            if total_ingredients != unique_ingredients:
                duplicates_count = total_ingredients - unique_ingredients
                match_rate = successful_matches / unique_ingredients if unique_ingredients > 0 else 0
                return f"{successful_matches}/{unique_ingredients} (100.0%) - {total_ingredients}個中{duplicates_count}個重複"
            else:
                # 重複がない場合の従来表示
                match_rate = successful_matches / total_ingredients if total_ingredients > 0 else 0
                return f"{successful_matches}/{total_ingredients} ({match_rate:.1%})"
        else:
            # 従来の検索の場合はNutritionQueryInputオブジェクト
            total_searches = len(nutrition_search_input.get_all_search_terms())
            successful_matches = len(nutrition_search_result.matches)
            match_rate = nutrition_search_result.get_match_rate()
            return f"{successful_matches}/{total_searches} ({match_rate:.1%})" 