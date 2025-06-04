"""
Workflow Manager - メインオーケストレーター

4フェーズの栄養推定ワークフローを統括
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ..image_processor.processor import ImageProcessor
from ..image_processor.image_models import ImageInput, ProcessedImageData
from ..db_interface.base_handler import DBHandler
from ..db_interface.usda_handler import USDADatabaseHandler
from ..db_interface.db_models import QueryParameters, RawDBResult, IdentifiedItemForDB
from ..data_interpreter.interpreter import DataInterpreter
from ..data_interpreter.interpretation_models import StructuredNutrientInfo
from ..nutrition_calculator.calculator import NutritionCalculator
from ..nutrition_calculator.calculation_models import FinalNutritionReport
from ..common.exceptions import NutrientEstimationError

logger = logging.getLogger(__name__)


class NutrientEstimationWorkflow:
    """栄養推定ワークフローの統括クラス"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        設定でワークフローを初期化
        
        Args:
            config: アプリケーション設定
        """
        self.config = config
        
        # 各モジュールコンポーネントの初期化
        self._initialize_components()
        
        logger.info("NutrientEstimationWorkflow initialized successfully")
    
    def _initialize_components(self):
        """各モジュールコンポーネントを初期化"""
        try:
            # 1. Image Processor初期化
            image_config = self.config.get("IMAGE_PROCESSOR_CONFIG", {})
            self.image_processor = ImageProcessor(image_config)
            
            # 2. DB Handler初期化
            db_config = self.config.get("DB_CONFIG", {})
            self.db_handler = self._initialize_db_handler(db_config)
            
            # 3. Data Interpreter初期化
            interpreter_config = self.config.get("INTERPRETER_CONFIG", {})
            self.data_interpreter = DataInterpreter(interpreter_config)
            
            # 4. Nutrition Calculator初期化
            calculator_config = self.config.get("CALCULATOR_CONFIG", {})
            self.nutrition_calculator = NutritionCalculator(calculator_config)
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow components: {e}")
            raise NutrientEstimationError(f"Workflow initialization failed: {str(e)}") from e
    
    def _initialize_db_handler(self, db_config: Dict[str, Any]) -> DBHandler:
        """データベースハンドラーを初期化"""
        db_type = db_config.get("TYPE", "USDA")
        
        if db_type == "USDA":
            usda_config = db_config.get("USDA", {})
            # プロンプト設定を注入
            usda_config.update({
                "PROMPTS": self.config.get("PROMPTS", {})
            })
            return USDADatabaseHandler(usda_config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def set_gemini_service(self, gemini_service):
        """Geminiサービスを設定（依存関係注入）"""
        self.image_processor.set_gemini_service(gemini_service)
        logger.info("Gemini service configured for ImageProcessor")
    
    async def process_image_to_nutrition(
        self, 
        image_path: str, 
        optional_text: Optional[str] = None
    ) -> FinalNutritionReport:
        """
        画像から栄養レポートまでの完全なワークフローを実行
        
        Args:
            image_path: 分析対象の画像パス
            optional_text: 補助テキスト情報
            
        Returns:
            FinalNutritionReport: 最終栄養レポート
        """
        try:
            logger.info(f"Starting nutrition estimation workflow for: {image_path}")
            
            # === Phase 1: 画像処理 ===
            logger.info("Phase 1: Image Processing")
            processed_data = await self._execute_phase1(image_path, optional_text)
            
            if not processed_data.identified_items:
                return self._create_empty_report("No food items identified in image", image_path)
            
            logger.info(f"Phase 1 completed: {len(processed_data.identified_items)} items identified")
            
            # === Phase 2: データベースクエリ ===
            logger.info("Phase 2: Database Query")
            db_result = await self._execute_phase2(processed_data)
            
            if not db_result.retrieved_foods:
                return self._create_empty_report("No nutrition data found in database", image_path, db_result.errors)
            
            logger.info(f"Phase 2 completed: {len(db_result.retrieved_foods)} food records retrieved")
            
            # === Phase 3: データ解釈 ===
            logger.info("Phase 3: Data Interpretation")
            structured_info = await self._execute_phase3(db_result, processed_data.identified_items)
            
            if not structured_info.interpreted_foods:
                return self._create_empty_report(
                    "No food data could be interpreted", 
                    image_path, 
                    structured_info.parsing_errors
                )
            
            logger.info(f"Phase 3 completed: {len(structured_info.interpreted_foods)} foods interpreted")
            
            # === Phase 4: 栄養計算 ===
            logger.info("Phase 4: Nutrition Calculation")
            final_report = await self._execute_phase4(structured_info)
            
            logger.info("Nutrition estimation workflow completed successfully")
            return final_report
            
        except Exception as e:
            logger.error(f"Workflow failed for image {image_path}: {e}", exc_info=True)
            return self._create_error_report(str(e), image_path)
    
    async def _execute_phase1(self, image_path: str, optional_text: Optional[str]) -> ProcessedImageData:
        """Phase 1: 画像処理を実行"""
        try:
            image_input = ImageInput(image_path=image_path)
            return await self.image_processor.process_image(image_input)
        except Exception as e:
            logger.error(f"Phase 1 failed: {e}")
            raise NutrientEstimationError(f"Image processing failed: {str(e)}") from e
    
    async def _execute_phase2(self, processed_data: ProcessedImageData) -> RawDBResult:
        """Phase 2: データベースクエリを実行"""
        try:
            # IdentifiedItemをDBクエリ用に変換
            db_query_items = self._convert_to_db_items(processed_data.identified_items)
            
            # クエリパラメータ作成
            query_strategy = self.config.get("DB_CONFIG", {}).get("DEFAULT_QUERY_STRATEGY", "default_usda_search_v1")
            query_params = QueryParameters(
                items_to_query=db_query_items,
                query_strategy_id=query_strategy,
                max_results_per_item=5
            )
            
            # データベース接続と検索
            await self.db_handler.connect()
            try:
                return await self.db_handler.fetch_nutrition_data(query_params)
            finally:
                await self.db_handler.disconnect()
                
        except Exception as e:
            logger.error(f"Phase 2 failed: {e}")
            raise NutrientEstimationError(f"Database query failed: {str(e)}") from e
    
    async def _execute_phase3(
        self, 
        db_result: RawDBResult, 
        original_items: list
    ) -> StructuredNutrientInfo:
        """Phase 3: データ解釈を実行"""
        try:
            return await self.data_interpreter.interpret_data(db_result, original_items)
        except Exception as e:
            logger.error(f"Phase 3 failed: {e}")
            raise NutrientEstimationError(f"Data interpretation failed: {str(e)}") from e
    
    async def _execute_phase4(self, structured_info: StructuredNutrientInfo) -> FinalNutritionReport:
        """Phase 4: 栄養計算を実行"""
        try:
            return await self.nutrition_calculator.calculate_totals(structured_info)
        except Exception as e:
            logger.error(f"Phase 4 failed: {e}")
            raise NutrientEstimationError(f"Nutrition calculation failed: {str(e)}") from e
    
    def _convert_to_db_items(self, identified_items: list) -> list[IdentifiedItemForDB]:
        """IdentifiedItemをDB検索用に変換"""
        db_items = []
        for item in identified_items:
            db_item = IdentifiedItemForDB(
                name=item.name,
                quantity_estimate=item.quantity_estimate,
                attributes=item.attributes,
                weight_g=item.weight_g,
                state=item.state
            )
            db_items.append(db_item)
        return db_items
    
    def _create_empty_report(
        self, 
        reason: str, 
        image_path: str, 
        errors: Optional[list] = None
    ) -> FinalNutritionReport:
        """空のレポートを作成"""
        return FinalNutritionReport(
            total_nutrients={},
            detailed_items=[],
            metadata={
                "status": reason,
                "image_path": image_path,
                "workflow_completed": False,
                "errors": errors or []
            }
        )
    
    def _create_error_report(self, error_message: str, image_path: str) -> FinalNutritionReport:
        """エラーレポートを作成"""
        return FinalNutritionReport(
            total_nutrients={},
            detailed_items=[],
            metadata={
                "status": "Workflow failed",
                "error": error_message,
                "image_path": image_path,
                "workflow_completed": False
            }
        )
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """ワークフローの状態を取得"""
        return {
            "components_initialized": True,
            "image_processor": self.image_processor is not None,
            "db_handler": self.db_handler is not None,
            "data_interpreter": self.data_interpreter is not None,
            "nutrition_calculator": self.nutrition_calculator is not None,
            "db_connected": self.db_handler.is_connected() if self.db_handler else False
        } 