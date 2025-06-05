import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from ..components import Phase1Component, USDAQueryComponent
from ..models import (
    Phase1Input, Phase1Output,
    USDAQueryInput, USDAQueryOutput
)
from ..config import get_settings
from .result_manager import ResultManager

logger = logging.getLogger(__name__)


class MealAnalysisPipeline:
    """
    食事分析パイプラインのオーケストレーター
    
    4つのフェーズを統合して完全な分析を実行します。
    """
    
    def __init__(self):
        """パイプラインの初期化"""
        self.pipeline_id = str(uuid.uuid4())[:8]
        self.settings = get_settings()
        
        # コンポーネントの初期化
        self.phase1_component = Phase1Component()
        self.usda_query_component = USDAQueryComponent()
        # TODO: Phase2ComponentとNutritionCalculationComponentを追加
        
        self.logger = logging.getLogger(f"{__name__}.{self.pipeline_id}")
        
    async def execute_complete_analysis(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        optional_text: Optional[str] = None,
        save_results: bool = True,
        save_detailed_logs: bool = True
    ) -> Dict[str, Any]:
        """
        完全な食事分析を実行
        
        Args:
            image_bytes: 画像データ
            image_mime_type: 画像のMIMEタイプ
            optional_text: オプションのテキスト
            save_results: 結果を保存するかどうか
            save_detailed_logs: 詳細ログを保存するかどうか
            
        Returns:
            完全な分析結果
        """
        analysis_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()
        
        # ResultManagerの初期化
        result_manager = ResultManager(analysis_id) if save_detailed_logs else None
        
        self.logger.info(f"[{analysis_id}] Starting complete meal analysis pipeline")
        
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
            
            # === USDA Query Phase: データベース照合 ===
            self.logger.info(f"[{analysis_id}] USDA Query Phase: Database matching")
            
            usda_input = USDAQueryInput(
                ingredient_names=phase1_result.get_all_ingredient_names(),
                dish_names=phase1_result.get_all_dish_names()
            )
            
            # USDA Queryの詳細ログを作成
            usda_log = result_manager.create_execution_log("USDAQueryComponent", f"{analysis_id}_usda") if result_manager else None
            
            usda_result = await self.usda_query_component.execute(usda_input, usda_log)
            
            self.logger.info(f"[{analysis_id}] USDA Query completed - {usda_result.get_match_rate():.1%} match rate")
            
            # === 暫定的な結果の構築 (Phase2とNutritionは後で追加) ===
            
            # Phase1の結果を辞書形式に変換
            phase1_dict = {
                "dishes": [
                    {
                        "dish_name": dish.dish_name,
                        "type": dish.type,
                        "quantity_on_plate": dish.quantity_on_plate,
                        "ingredients": [
                            {
                                "ingredient_name": ing.ingredient_name,
                                "weight_g": ing.weight_g
                            }
                            for ing in dish.ingredients
                        ]
                    }
                    for dish in phase1_result.dishes
                ]
            }
            
            # 簡単な栄養計算（暫定）
            total_calories = sum(
                len(dish.ingredients) * 50  # 仮の計算
                for dish in phase1_result.dishes
            )
            
            # 完全分析結果の構築
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            complete_result = {
                "analysis_id": analysis_id,
                "phase1_result": phase1_dict,
                "usda_result": {
                    "matches_count": len(usda_result.matches),
                    "match_rate": usda_result.get_match_rate(),
                    "search_summary": usda_result.search_summary
                },
                "processing_summary": {
                    "total_dishes": len(phase1_result.dishes),
                    "total_ingredients": len(phase1_result.get_all_ingredient_names()),
                    "usda_match_rate": f"{len(usda_result.matches)}/{len(usda_input.get_all_search_terms())} ({usda_result.get_match_rate():.1%})",
                    "total_calories": total_calories,
                    "pipeline_status": "completed",
                    "processing_time_seconds": processing_time
                },
                # 暫定的な最終結果
                "final_nutrition_result": {
                    "dishes": phase1_dict["dishes"],
                    "total_meal_nutrients": {
                        "calories_kcal": total_calories,
                        "protein_g": total_calories * 0.15,  # 仮の値
                        "carbohydrates_g": total_calories * 0.55,  # 仮の値
                        "fat_g": total_calories * 0.30,  # 仮の値
                    }
                },
                "metadata": {
                    "pipeline_version": "v2.0",
                    "timestamp": datetime.now().isoformat(),
                    "components_used": ["Phase1Component", "USDAQueryComponent"]
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
                
                logger.info(f"[{analysis_id}] Detailed logs saved to folder: {result_manager.get_analysis_folder_path()}")
                logger.info(f"[{analysis_id}] Saved {len(saved_files)} files across all phases")
            
            if save_results:
                # 通常の結果保存（互換性維持）
                saved_file = f"analysis_results/meal_analysis_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                complete_result["legacy_saved_to"] = saved_file
            
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
        return {
            "pipeline_id": self.pipeline_id,
            "version": "v2.0",
            "components": [
                self.phase1_component.get_component_info(),
                self.usda_query_component.get_component_info()
            ]
        } 