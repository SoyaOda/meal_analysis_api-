"""
Base Interpretation Strategy

データ解釈戦略の抽象基底クラス
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..interpretation_models import InterpretedFoodItem
from ...db_interface.db_models import RawFoodData
from ...image_processor.image_models import IdentifiedItem


class BaseInterpretationStrategy(ABC):
    """データ解釈戦略の抽象基底クラス"""
    
    def __init__(self, strategy_config: Dict[str, Any]):
        """
        戦略設定で初期化
        
        Args:
            strategy_config: 戦略固有の設定
        """
        self.strategy_config = strategy_config
    
    @abstractmethod
    async def interpret(
        self, 
        raw_food_data: RawFoodData, 
        identified_item_info: Optional[IdentifiedItem] = None
    ) -> InterpretedFoodItem:
        """
        生データを解釈して標準化されたフォーマットに変換
        
        Args:
            raw_food_data: データベースからの生データ
            identified_item_info: 元の認識アイテム情報（量情報など）
            
        Returns:
            InterpretedFoodItem: 解釈済み食品アイテム
        """
        raise NotImplementedError
    
    @abstractmethod
    def select_best_match(
        self, 
        candidates: List[RawFoodData], 
        original_query: str
    ) -> Optional[RawFoodData]:
        """
        複数の候補から最適なマッチを選択
        
        Args:
            candidates: 候補リスト
            original_query: 元のクエリ
            
        Returns:
            Optional[RawFoodData]: 選択された候補（なければNone）
        """
        raise NotImplementedError
    
    def validate_nutrient_data(self, nutrients: Dict[str, Any]) -> bool:
        """
        栄養素データの妥当性を検証
        
        Args:
            nutrients: 栄養素データ
            
        Returns:
            bool: 妥当性
        """
        # 基本的な検証ロジック
        if not nutrients:
            return False
        
        # 主要栄養素の存在確認
        required_nutrients = ["Energy", "Protein"]
        for nutrient in required_nutrients:
            if not any(nutrient.lower() in key.lower() for key in nutrients.keys()):
                return False
        
        return True 