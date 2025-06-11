import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from ..components import Phase1Component, USDAQueryComponent, LocalNutritionSearchComponent, ElasticsearchNutritionSearchComponent
from ..models import (
    Phase1Input, Phase1Output,
    USDAQueryInput, USDAQueryOutput,
    NutritionQueryInput
)
from ..config import get_settings
from .result_manager import ResultManager

logger = logging.getLogger(__name__)


class MealAnalysisPipeline:
    """
    食事分析パイプラインのオーケストレーター
    
    4つのフェーズを統合して完全な分析を実行します。
    """
    
    def __init__(self, use_local_nutrition_search: Optional[bool] = None, use_elasticsearch_search: Optional[bool] = None):
        """
        パイプラインの初期化
        
        Args:
            use_local_nutrition_search: ローカル栄養データベース検索を使用するかどうか（レガシー）
            use_elasticsearch_search: Elasticsearch栄養データベース検索を使用するかどうか
                                    None: 設定ファイルから自動取得
                                    True: ElasticsearchNutritionSearchComponent使用（推奨）
                                    False: 従来のUSDAQueryComponent使用
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
        
        # レガシー互換性の処理
        if use_local_nutrition_search is not None and use_elasticsearch_search is None:
            # 旧パラメータが指定された場合はそちらを優先
            if use_local_nutrition_search:
                self.use_elasticsearch_search = False
                self.use_local_nutrition_search = True
            else:
                self.use_elasticsearch_search = False
                self.use_local_nutrition_search = False
        else:
            self.use_local_nutrition_search = not self.use_elasticsearch_search and (
                use_local_nutrition_search or getattr(self.settings, 'USE_LOCAL_NUTRITION_SEARCH', False)
            )
        
        # コンポーネントの初期化
        self.phase1_component = Phase1Component()
        
        # 栄養データベース検索コンポーネントの選択
        if self.use_elasticsearch_search:
            self.nutrition_search_component = ElasticsearchNutritionSearchComponent(
                multi_db_search_mode=True,
                results_per_db=5
            )
            self.search_component_name = "ElasticsearchNutritionSearchComponent"
            logger.info("Using Elasticsearch nutrition database search (high-performance, multi-DB mode)")
        elif self.use_local_nutrition_search:
            self.nutrition_search_component = LocalNutritionSearchComponent()
            self.search_component_name = "LocalNutritionSearchComponent"
            logger.info("Using local nutrition database search (nutrition_db_experiment)")
        else:
            self.nutrition_search_component = USDAQueryComponent()
            self.search_component_name = "USDAQueryComponent"
            logger.info("Using traditional USDA API search")
            
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
        if self.use_elasticsearch_search:
            self.logger.info(f"[{analysis_id}] Nutrition search method: Elasticsearch (high-performance)")
        elif self.use_local_nutrition_search:
            self.logger.info(f"[{analysis_id}] Nutrition search method: Local Database")
        else:
            self.logger.info(f"[{analysis_id}] Nutrition search method: USDA API")
        
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
            if self.use_elasticsearch_search:
                search_phase_name = "Elasticsearch Search"
            elif self.use_local_nutrition_search:
                search_phase_name = "Local Nutrition Search"
            else:
                search_phase_name = "USDA Query"
                
            self.logger.info(f"[{analysis_id}] {search_phase_name} Phase: Database matching")
            
            # === 統一された栄養検索入力を作成 ===
            if self.use_elasticsearch_search or self.use_local_nutrition_search:
                # Elasticsearch検索またはローカル検索の場合はNutritionQueryInputを使用
                preferred_source = "elasticsearch" if self.use_elasticsearch_search else "local_database"
                nutrition_search_input = NutritionQueryInput(
                    ingredient_names=phase1_result.get_all_ingredient_names(),
                    dish_names=phase1_result.get_all_dish_names(),
                    preferred_source=preferred_source
                )
            else:
                # USDA検索の場合はUSDAQueryInputを使用（レガシー互換性）
                nutrition_search_input = USDAQueryInput(
                    ingredient_names=phase1_result.get_all_ingredient_names(),
                    dish_names=phase1_result.get_all_dish_names()
                )
            
            # Nutrition Searchの詳細ログを作成
            search_log = result_manager.create_execution_log(self.search_component_name, f"{analysis_id}_nutrition_search") if result_manager else None
            
            nutrition_search_result = await self.nutrition_search_component.execute(nutrition_search_input, search_log)
            
            self.logger.info(f"[{analysis_id}] {search_phase_name} completed - {nutrition_search_result.get_match_rate():.1%} match rate")
            
            # === 暫定的な結果の構築 (Phase2とNutritionは後で追加) ===
            
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
                                "confidence": ing.confidence
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
            
            # 簡単な栄養計算（暫定）
            total_calories = sum(
                len(dish.ingredients) * 50  # 仮の計算
                for dish in phase1_result.dishes
            )
            
            # 検索方法の特定
            if self.use_elasticsearch_search:
                search_method = "elasticsearch"
                search_api_method = "elasticsearch"
            elif self.use_local_nutrition_search:
                search_method = "local_nutrition_database"
                search_api_method = "local_database"
            else:
                search_method = "usda_api"
                search_api_method = "usda_api"
            
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
                # レガシー互換性のため、usdaキーも残す
                "usda_result": {
                    "matches_count": len(nutrition_search_result.matches),
                    "match_rate": nutrition_search_result.get_match_rate(),
                    "search_summary": nutrition_search_result.search_summary
                },
                "processing_summary": {
                    "total_dishes": len(phase1_result.dishes),
                    "total_ingredients": len(phase1_result.get_all_ingredient_names()),
                    "nutrition_search_match_rate": f"{len(nutrition_search_result.matches)}/{len(nutrition_search_input.get_all_search_terms())} ({nutrition_search_result.get_match_rate():.1%})",
                    "usda_match_rate": f"{len(nutrition_search_result.matches)}/{len(nutrition_search_input.get_all_search_terms())} ({nutrition_search_result.get_match_rate():.1%})",  # レガシー互換性
                    "total_calories": total_calories,
                    "pipeline_status": "completed",
                    "processing_time_seconds": processing_time,
                    "search_method": search_method
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
                    "components_used": ["Phase1Component", self.search_component_name],
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
        if self.use_elasticsearch_search:
            search_method = "elasticsearch"
        elif self.use_local_nutrition_search:
            search_method = "local_database"
        else:
            search_method = "usda_api"
            
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
                }
            ]
        } 