"""
Data Interpreter - Phase2ロジック

データ解釈フェーズのメインロジック
戦略パターンを使用してUSDA結果を標準化
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..db_interface.db_models import RawDBResult, RawFoodData
from .interpretation_models import StructuredNutrientInfo, InterpretedFoodItem
from .strategies.base_strategy import BaseInterpretationStrategy
from .strategies.default_usda_strategy import DefaultUSDAInterpretationStrategy
from ..image_processor.image_models import IdentifiedItem
from ..common.exceptions import InterpretationRuleError

logger = logging.getLogger(__name__)


class DataInterpreter:
    """データ解釈クラス - Phase2機能をカプセル化"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        設定で初期化
        
        Args:
            config: データ解釈設定
        """
        self.config = config
        
        # 戦略の初期化
        strategy_name = config.get("STRATEGY_NAME", "DefaultUSDA")
        strategy_configs = config.get("STRATEGY_CONFIGS", {})
        strategy_config = strategy_configs.get(strategy_name, {})
        
        # 戦略ローダー
        self.strategy = self._load_strategy(strategy_name, strategy_config)
        
        logger.info(f"DataInterpreter initialized with strategy: {strategy_name}")
    
    def _load_strategy(self, strategy_name: str, strategy_config: Dict[str, Any]) -> BaseInterpretationStrategy:
        """解釈戦略をロード"""
        strategy_map = {
            "DefaultUSDA": DefaultUSDAInterpretationStrategy,
            # 将来的に他の戦略を追加
            # "PrioritizeRawFood": PrioritizeRawFoodStrategy,
            # "CustomStrategy": CustomInterpretationStrategy,
        }
        
        strategy_class = strategy_map.get(strategy_name)
        if not strategy_class:
            raise InterpretationRuleError(f"Unknown interpretation strategy: {strategy_name}")
        
        return strategy_class(strategy_config)
    
    async def interpret_data(
        self, 
        db_result: RawDBResult, 
        original_identified_items: Optional[List[IdentifiedItem]] = None
    ) -> StructuredNutrientInfo:
        """
        データベース結果を解釈して標準化フォーマットに変換
        
        Args:
            db_result: データベース検索結果
            original_identified_items: 元の認識アイテムリスト（量情報など）
            
        Returns:
            StructuredNutrientInfo: 構造化された栄養情報
        """
        interpreted_items: List[InterpretedFoodItem] = []
        parsing_errors: List[str] = []
        
        # データベースエラーを継承
        if db_result.errors:
            parsing_errors.extend(db_result.errors)
        
        # 元のアイテム情報を辞書に変換（マッチング用）
        item_map = {}
        if original_identified_items:
            item_map = {item.name: item for item in original_identified_items}
        
        # 食品アイテムごとにグループ化
        grouped_foods = self._group_foods_by_query_term(db_result.retrieved_foods)
        
        for query_term, food_candidates in grouped_foods.items():
            try:
                # 最適なマッチを選択
                selected_food = self.strategy.select_best_match(food_candidates, query_term)
                
                if selected_food:
                    # 元のアイテム情報を取得
                    original_item = item_map.get(query_term)
                    
                    # 解釈処理を実行
                    interpreted_item = await self.strategy.interpret(selected_food, original_item)
                    interpreted_items.append(interpreted_item)
                    
                    logger.info(f"Successfully interpreted '{query_term}' -> '{selected_food.food_description}'")
                else:
                    error_msg = f"No suitable match found for '{query_term}'"
                    parsing_errors.append(error_msg)
                    logger.warning(error_msg)
                    
            except Exception as e:
                error_msg = f"Error interpreting '{query_term}': {str(e)}"
                parsing_errors.append(error_msg)
                logger.error(error_msg, exc_info=True)
        
        # 処理メタデータの作成
        processing_metadata = {
            "total_db_results": len(db_result.retrieved_foods),
            "successfully_interpreted": len(interpreted_items),
            "processing_timestamp": datetime.utcnow().isoformat() + "Z",
            "source_database": db_result.source_db_name,
            "unique_query_terms": len(grouped_foods),
            "strategy_used": self.strategy.__class__.__name__
        }
        
        return StructuredNutrientInfo(
            interpreted_foods=interpreted_items,
            interpretation_strategy_used=self.strategy.__class__.__name__,
            parsing_errors=parsing_errors if parsing_errors else None,
            processing_metadata=processing_metadata
        )
    
    def _group_foods_by_query_term(self, foods: List[RawFoodData]) -> Dict[str, List[RawFoodData]]:
        """食品を元のクエリ用語でグループ化"""
        groups = {}
        for food in foods:
            query_term = food.matched_query_term
            if query_term not in groups:
                groups[query_term] = []
            groups[query_term].append(food)
        
        logger.info(f"Grouped {len(foods)} foods into {len(groups)} query terms")
        return groups
    
    def validate_interpretation_results(self, structured_info: StructuredNutrientInfo) -> bool:
        """解釈結果の妥当性を検証"""
        if not structured_info.interpreted_foods:
            logger.warning("No interpreted foods found")
            return False
        
        # 各食品アイテムの栄養素データを検証
        valid_items = 0
        for item in structured_info.interpreted_foods:
            if self.strategy.validate_nutrient_data(item.processed_nutrients):
                valid_items += 1
        
        validity_ratio = valid_items / len(structured_info.interpreted_foods)
        logger.info(f"Validation: {valid_items}/{len(structured_info.interpreted_foods)} items valid ({validity_ratio:.2%})")
        
        # 50%以上が有効な場合は全体として有効とする
        return validity_ratio >= 0.5
    
    def get_interpretation_summary(self, structured_info: StructuredNutrientInfo) -> Dict[str, Any]:
        """解釈結果のサマリーを生成"""
        summary = {
            "total_items": structured_info.get_total_items(),
            "has_errors": structured_info.has_errors(),
            "strategy_used": structured_info.interpretation_strategy_used,
            "error_count": len(structured_info.parsing_errors) if structured_info.parsing_errors else 0
        }
        
        # 栄養素統計
        if structured_info.interpreted_foods:
            all_nutrients = set()
            for item in structured_info.interpreted_foods:
                all_nutrients.update(item.processed_nutrients.keys())
            
            summary["unique_nutrients_found"] = len(all_nutrients)
            summary["common_nutrients"] = list(all_nutrients)[:10]  # 最初の10個
        
        return summary 