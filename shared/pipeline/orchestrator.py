import uuid
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from ..components import Phase1Component, NutritionCalculationComponent
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
    
    def __init__(self, model_id: Optional[str] = None):
        """
        パイプラインの初期化

        常にWord Query API（AdvancedNutritionSearchComponent）を使用します。

        Args:
            model_id: 使用する画像分析モデルID（None: 設定ファイルのデフォルト使用）
        """
        self.pipeline_id = str(uuid.uuid4())[:8]
        self.settings = get_settings()

        # 指定されたモデルIDの保存
        self.model_id = model_id

        # シンプルに：常にWord Query API（AdvancedNutritionSearchComponent）を使用
        self.use_elasticsearch_search = True
        self.use_fuzzy_matching = False
        self.use_local_nutrition_search = False

        # Vision Serviceの初期化（モデルID対応）
        try:
            # DeepInfraServiceを試行（model_idパラメータ付き）
            self.vision_service = DeepInfraService(model_id=self.model_id)
            logger.info(f"Using DeepInfra service with model: {self.vision_service.model_id}")

            # モデル設定情報をログ出力
            if self.vision_service.model_config:
                expected_time = self.vision_service.model_config.get("expected_response_time_ms", "unknown")
                best_for = self.vision_service.model_config.get("best_for", "general")
                logger.info(f"Model characteristics - Expected time: {expected_time}ms, Best for: {best_for}")

        except ValueError as e:
            # 環境変数が設定されていない場合はエラーを発生させる
            logger.error(f"DeepInfra service initialization failed: {e}")
            raise RuntimeError(f"DeepInfra service configuration error: {e}") from e

        # コンポーネントの初期化
        self.phase1_component = Phase1Component(vision_service=self.vision_service)

        # 栄養データベース検索コンポーネント：常にWord Query APIを使用
        from ..components.advanced_nutrition_search_component import AdvancedNutritionSearchComponent
        self.nutrition_search_component = AdvancedNutritionSearchComponent()
        self.search_component_name = "AdvancedNutritionSearchComponent"
        logger.info("Using Word Query API (Advanced Nutrition Search with multi-tier performance strategy)")

        # 栄養計算コンポーネントの初期化
        self.nutrition_calculation_component = NutritionCalculationComponent()

        # TODO: Phase2Componentを追加

        self.logger = logging.getLogger(f"{__name__}.{self.pipeline_id}")
        
    async def execute_complete_analysis(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        optional_text: Optional[str] = None,
        temperature: Optional[float] = 0.0,
        seed: Optional[int] = 123456,
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
            temperature: AI推論のランダム性制御 (0.0-1.0)
            seed: 再現性のためのシード値
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
                result_manager = ResultManager(base_dir=api_calls_dir)
                result_manager.initialize_session(analysis_id)
            else:
                # 通常の実行時は既存の保存先
                result_manager = ResultManager()
                result_manager.initialize_session(analysis_id)
        else:
            result_manager = None
        
        self.logger.info(f"[{analysis_id}] Starting complete meal analysis pipeline")
        self.logger.info(f"[{analysis_id}] Nutrition search method: Word Query API (high-performance)")
        
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
            
            phase1_result = await self.phase1_component.execute(phase1_input, phase1_log, temperature=temperature, seed=seed)
            
            self.logger.info(f"[{analysis_id}] Phase 1 completed - Detected {len(phase1_result.dishes)} dishes")
            
            # === Nutrition Search Phase: データベース照合 ===
            if self.use_fuzzy_matching:
                search_phase_name = "Fuzzy Ingredient Search"
            else:
                search_phase_name = "Word Query API Search"
            self.logger.info(f"[{analysis_id}] {search_phase_name} Phase: Database matching")
            
            # === 栄養検索入力を作成（Word Query API用） ===
            nutrition_search_input = NutritionQueryInput(
                ingredient_names=phase1_result.get_all_ingredient_names(),
                dish_names=phase1_result.get_all_dish_names(),
                preferred_source="advanced_search"
            )

            # Nutrition Searchの詳細ログを作成
            search_log = result_manager.create_execution_log(self.search_component_name, f"{analysis_id}_nutrition_search") if result_manager else None

            # Word Query API実行
            nutrition_search_result = await self.nutrition_search_component.process(nutrition_search_input)
            
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
                "processing_notes": phase1_result.processing_notes,
                "metadata": {
                    "ai_model_used": self.deepinfra_service.model_id if hasattr(self, 'deepinfra_service') else "unknown"
                },
                "input_data": {
                    "image_mime_type": image_mime_type,
                    "optional_text": optional_text,
                    "temperature": temperature,
                    "seed": seed
                }
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
                "warnings": nutrition_calculation_result.meal_nutrition.warnings,
                "match_rate_percent": nutrition_search_result.get_match_rate() * 100
            }

            # 完全分析結果の構築
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            complete_result = {
                "analysis_id": analysis_id,
                "phase1_result": phase1_dict,
                "nutrition_search_result": {
                    "matches_count": len(nutrition_search_result.matches),
                    "match_rate": nutrition_search_result.get_match_rate(),
                    "search_summary": nutrition_search_result.search_summary
                },

                "processing_summary": {
                    "total_dishes": len(phase1_result.dishes),
                    "total_ingredients": len(phase1_result.get_all_ingredient_names()),
                    "nutrition_search_match_rate": self._calculate_match_rate_display(nutrition_search_input, nutrition_search_result),
                    "nutrition_calculation_status": "completed",
                    "total_calories": nutrition_calculation_result.meal_nutrition.total_nutrition.calories,
                    "pipeline_status": "completed",
                    "processing_time_seconds": processing_time
                },
                # 最終栄養結果
                "final_nutrition_result": nutrition_calculation_dict,
                "metadata": {
                    "pipeline_version": "v2.0",
                    "timestamp": datetime.now().isoformat(),
                    "components_used": ["Phase1Component", self.search_component_name, "NutritionCalculationComponent"]
                }
            }
            
            # 新しいResultManagerで各フェーズの結果を保存
            if result_manager:
                # Phase1の結果を追加
                result_manager.add_phase_result("phase1", phase1_dict)
                
                # 栄養検索の結果を追加
                # 安全にmatchesを処理
                matches_data = []
                if hasattr(nutrition_search_result, 'matches') and nutrition_search_result.matches:
                    for match in nutrition_search_result.matches:
                        if hasattr(match, 'query_term'):  # matchがオブジェクトの場合
                            matches_data.append({
                                "query_term": match.query_term,
                                "matched_food": match.matched_food,
                                "confidence_score": match.confidence_score,
                                "source_database": match.source_database,
                                "nutrition_per_100g": match.nutrition_per_100g
                            })
                        elif isinstance(match, dict):  # matchが辞書の場合
                            matches_data.append({
                                "query_term": match.get("query_term", ""),
                                "matched_food": match.get("matched_food", ""),
                                "confidence_score": match.get("confidence_score", 0.0),
                                "source_database": match.get("source_database", ""),
                                "nutrition_per_100g": match.get("nutrition_per_100g", {})
                            })

                nutrition_search_dict = {
                    "matches_count": len(nutrition_search_result.matches) if hasattr(nutrition_search_result, 'matches') else 0,
                    "match_rate": nutrition_search_result.get_match_rate(),
                    "search_summary": nutrition_search_result.search_summary,
                    "matches": matches_data
                }
                result_manager.add_phase_result("nutrition_search", nutrition_search_dict)
                
                # 栄養計算の結果を追加
                result_manager.add_phase_result("nutrition_calculation", nutrition_calculation_dict)
                
                # 最終結果を保存（final_resultを渡す）
                result_manager.finalize_pipeline(complete_result)
                
                complete_result["analysis_folder"] = result_manager.get_analysis_folder_path()
                
                logger.info(f"[{analysis_id}] Analysis logs saved to folder: {result_manager.get_analysis_folder_path()}")
                logger.info(f"[{analysis_id}] Saved 3 files in new structured format")

            
            self.logger.info(f"[{analysis_id}] Complete analysis pipeline finished successfully in {processing_time:.2f}s")
            
            return complete_result
            
        except Exception as e:
            self.logger.error(f"[{analysis_id}] Complete analysis failed: {str(e)}", exc_info=True)
            
            # エラー時もResultManagerを保存
            if result_manager:
                error_data = {"error": str(e), "timestamp": datetime.now().isoformat()}
                result_manager.add_phase_result("error", error_data)
                # エラー時でもcomplete_resultが存在する場合は渡す
                error_complete_result = getattr(self, 'complete_result', {}) if 'complete_result' in locals() else {}
                result_manager.finalize_pipeline(error_complete_result)
                self.logger.info(f"[{analysis_id}] Error analysis logs saved to folder: {result_manager.get_analysis_folder_path()}")
            
            raise
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """パイプライン情報を取得"""
        return {
            "pipeline_id": self.pipeline_id,
            "version": "v2.0",
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
        """マッチ率の表示文字列を計算（Word Query API用）"""
        from ..models.nutrition_search_models import NutritionQueryInput
        if not isinstance(nutrition_search_input, NutritionQueryInput):
            raise TypeError(f"Expected NutritionQueryInput, got {type(nutrition_search_input)}")

        total_searches = len(nutrition_search_input.get_all_search_terms())
        successful_matches = len(nutrition_search_result.matches)
        match_rate = nutrition_search_result.get_match_rate()
        return f"{successful_matches}/{total_searches} ({match_rate:.1%})" 