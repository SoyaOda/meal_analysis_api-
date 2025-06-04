"""
Default USDA Interpretation Strategy

USDAデータの標準解釈戦略
既存のPhase2ロジックをカプセル化
"""

import logging
from typing import Dict, Any, List, Optional
from .base_strategy import BaseInterpretationStrategy
from ..interpretation_models import InterpretedFoodItem, NutrientValue
from ...db_interface.db_models import RawFoodData
from ...image_processor.image_models import IdentifiedItem

logger = logging.getLogger(__name__)


class DefaultUSDAInterpretationStrategy(BaseInterpretationStrategy):
    """USDA用のデフォルト解釈戦略"""
    
    def __init__(self, strategy_config: Dict[str, Any]):
        super().__init__(strategy_config)
        
        # 栄養素マッピング設定
        self.nutrient_map = strategy_config.get("NUTRIENT_MAP", {
            "Protein": "PROTEIN",
            "Total lipid (fat)": "TOTAL_FAT", 
            "Carbohydrate, by difference": "CARBOHYDRATE_BY_DIFFERENCE",
            "Energy": "CALORIES",
            "Fiber, total dietary": "FIBER",
            "Sugars, total including NLEA": "SUGAR",
            "Calcium, Ca": "CALCIUM",
            "Iron, Fe": "IRON",
            "Sodium, Na": "SODIUM",
            "Vitamin C, total ascorbic acid": "VITAMIN_C",
            "Vitamin A, RAE": "VITAMIN_A"
        })
        
        # 目標単位設定
        self.target_units = strategy_config.get("TARGET_UNITS", {
            "PROTEIN": "g",
            "TOTAL_FAT": "g",
            "CARBOHYDRATE_BY_DIFFERENCE": "g", 
            "CALORIES": "kcal",
            "FIBER": "g",
            "SUGAR": "g",
            "CALCIUM": "mg",
            "IRON": "mg",
            "SODIUM": "mg",
            "VITAMIN_C": "mg",
            "VITAMIN_A": "µg"
        })
        
        # 選択優先度キーワード
        self.preferred_keywords = ["raw", "fresh", "generic", "average"]
        self.avoid_keywords = ["baby", "infant", "dietary supplement"]
        
        logger.info(f"DefaultUSDA strategy initialized with {len(self.nutrient_map)} nutrient mappings")
    
    async def interpret(
        self, 
        raw_food_data: RawFoodData, 
        identified_item_info: Optional[IdentifiedItem] = None
    ) -> InterpretedFoodItem:
        """
        USDA生データを解釈して標準化フォーマットに変換
        """
        processed_nutrients = {}
        
        # 栄養素データの解析と標準化
        for nutrient_name_from_db, nutrient_data in raw_food_data.nutrients.items():
            standard_nutrient_name = self.nutrient_map.get(nutrient_name_from_db)
            
            if standard_nutrient_name:
                try:
                    # USDAデータ構造に応じた値の抽出
                    if isinstance(nutrient_data, dict):
                        amount = float(nutrient_data.get("value", 0))
                        unit = nutrient_data.get("unit", "")
                    else:
                        # 旧形式対応
                        parts = str(nutrient_data).split()
                        amount = float(parts[0]) if parts else 0
                        unit = parts[1] if len(parts) > 1 else ""
                    
                    # 単位変換（必要に応じて）
                    amount, unit = self._convert_units(amount, unit, standard_nutrient_name)
                    
                    # スケーリング（serving sizeに基づく）
                    if identified_item_info and identified_item_info.weight_g:
                        # 100gあたりの値を実際の重量に調整
                        serving_ratio = identified_item_info.weight_g / 100.0
                        amount *= serving_ratio
                    
                    processed_nutrients[standard_nutrient_name] = NutrientValue(
                        amount=round(amount, 3),
                        unit=unit
                    )
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse nutrient '{nutrient_name_from_db}': {nutrient_data}. Error: {e}")
                    continue
        
        return InterpretedFoodItem(
            matched_query_term=raw_food_data.matched_query_term,
            selected_food_description=raw_food_data.food_description,
            db_source_id=raw_food_data.db_source_id,
            processed_nutrients=processed_nutrients,
            confidence_score=raw_food_data.confidence_score,
            food_category=raw_food_data.food_category,
            serving_size_g=identified_item_info.weight_g if identified_item_info else None,
            data_source="USDA_FDC"
        )
    
    def select_best_match(
        self, 
        candidates: List[RawFoodData], 
        original_query: str
    ) -> Optional[RawFoodData]:
        """
        複数のUSDA候補から最適なマッチを選択
        """
        if not candidates:
            return None
        
        if len(candidates) == 1:
            return candidates[0]
        
        # スコアリング
        scored_candidates = []
        for candidate in candidates:
            score = self._calculate_match_score(candidate, original_query)
            scored_candidates.append((score, candidate))
        
        # 最高スコアの候補を選択
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_candidate = scored_candidates[0]
        
        logger.info(f"Selected '{best_candidate.food_description}' with score {best_score} for query '{original_query}'")
        return best_candidate
    
    def _calculate_match_score(self, candidate: RawFoodData, original_query: str) -> float:
        """候補のマッチスコアを計算"""
        score = 0.0
        description = candidate.food_description.lower()
        query_lower = original_query.lower()
        
        # 1. データタイプによる重み付け
        data_type_weights = {
            "Foundation": 1.0,
            "SR Legacy": 0.9,
            "Survey (FNDDS)": 0.8,
            "Branded": 0.6
        }
        score += data_type_weights.get(candidate.data_type, 0.5)
        
        # 2. クエリ語の含有度
        query_words = query_lower.split()
        for word in query_words:
            if word in description:
                score += 0.5
        
        # 3. 優先キーワードのボーナス
        for keyword in self.preferred_keywords:
            if keyword in description:
                score += 0.3
        
        # 4. 回避キーワードのペナルティ
        for keyword in self.avoid_keywords:
            if keyword in description:
                score -= 0.5
        
        # 5. ブランド品のペナルティ（genericを優先）
        if candidate.brand_owner:
            score -= 0.2
        
        # 6. 栄養素データの完全性
        nutrient_completeness = len(candidate.nutrients) / 50.0  # 50栄養素を基準
        score += min(nutrient_completeness, 0.5)
        
        return max(score, 0.0)
    
    def _convert_units(self, amount: float, unit: str, nutrient_name: str) -> tuple[float, str]:
        """栄養素単位の変換"""
        target_unit = self.target_units.get(nutrient_name, unit)
        
        if unit == target_unit:
            return amount, unit
        
        # 基本的な単位変換
        conversion_map = {
            ("mg", "g"): 0.001,
            ("g", "mg"): 1000,
            ("µg", "mg"): 0.001,
            ("mg", "µg"): 1000,
            ("IU", "µg"): {  # ビタミン固有の変換
                "VITAMIN_A": 0.3,
                "VITAMIN_D": 0.025,
                "VITAMIN_E": 0.67
            }
        }
        
        conversion_key = (unit, target_unit)
        if conversion_key in conversion_map:
            multiplier = conversion_map[conversion_key]
            if isinstance(multiplier, dict):
                multiplier = multiplier.get(nutrient_name, 1.0)
            
            return amount * multiplier, target_unit
        
        # 変換できない場合は元の値を返す
        logger.warning(f"No conversion available from {unit} to {target_unit} for {nutrient_name}")
        return amount, unit 