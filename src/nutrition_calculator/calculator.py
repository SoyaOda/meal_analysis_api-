"""
Nutrition Calculator - 栄養計算ロジック

栄養素の集計と最終レポート生成
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..data_interpreter.interpretation_models import StructuredNutrientInfo, InterpretedFoodItem, NutrientValue
from .calculation_models import FinalNutritionReport, NutrientSummary
from ..common.exceptions import NutritionCalculationError

logger = logging.getLogger(__name__)


class NutritionCalculator:
    """栄養計算クラス - 最終フェーズの集計と計算"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        設定で初期化
        
        Args:
            config: 栄養計算設定
        """
        self.config = config
        self.rounding_precision = config.get("ROUNDING_PRECISION", 2)
        self.enable_daily_values = config.get("ENABLE_DAILY_VALUES", False)
        
        # 1日摂取目標値（DV: Daily Values）
        self.daily_values = config.get("DAILY_VALUES", {
            "CALORIES": 2000,
            "PROTEIN": 50,
            "TOTAL_FAT": 65,
            "CARBOHYDRATE_BY_DIFFERENCE": 300,
            "FIBER": 25,
            "SODIUM": 2300,  # mg
            "CALCIUM": 1000,  # mg
            "IRON": 18,  # mg
            "VITAMIN_C": 90,  # mg
            "VITAMIN_A": 900  # µg
        })
        
        logger.info(f"NutritionCalculator initialized. DV enabled: {self.enable_daily_values}")
    
    async def calculate_totals(self, structured_info: StructuredNutrientInfo) -> FinalNutritionReport:
        """
        解釈済みデータから栄養素を集計して最終レポートを生成
        
        Args:
            structured_info: 構造化された栄養情報
            
        Returns:
            FinalNutritionReport: 最終栄養レポート
        """
        try:
            if not structured_info.interpreted_foods:
                return self._create_empty_report(structured_info)
            
            # 栄養素集計
            aggregated_nutrients = self._aggregate_nutrients(structured_info.interpreted_foods)
            
            # 栄養素サマリー作成
            nutrient_summaries = self._create_nutrient_summaries(
                aggregated_nutrients, 
                structured_info.interpreted_foods
            )
            
            # メタデータ作成
            metadata = self._create_metadata(structured_info)
            
            # マクロ栄養素内訳計算
            macro_breakdown = self._calculate_macro_breakdown(nutrient_summaries)
            
            # 栄養データ完全性スコア
            completeness_score = self._calculate_completeness_score(structured_info.interpreted_foods)
            
            # 総重量計算
            total_weight = self._calculate_total_weight(structured_info.interpreted_foods)
            
            # 総カロリー抽出
            total_calories = (
                nutrient_summaries.get("CALORIES", NutrientSummary(total_amount=0, unit="kcal", contributing_foods=[])).total_amount
                if "CALORIES" in nutrient_summaries else None
            )
            
            return FinalNutritionReport(
                total_nutrients=nutrient_summaries,
                detailed_items=structured_info.interpreted_foods,
                metadata=metadata,
                total_calories=total_calories,
                total_weight_g=total_weight,
                nutrition_completeness_score=completeness_score,
                macro_breakdown=macro_breakdown
            )
            
        except Exception as e:
            logger.error(f"Error in nutrition calculation: {e}", exc_info=True)
            raise NutritionCalculationError(f"Failed to calculate nutrition totals: {str(e)}") from e
    
    def _aggregate_nutrients(self, interpreted_foods: List[InterpretedFoodItem]) -> Dict[str, Dict[str, Any]]:
        """栄養素を集計"""
        aggregated = {}
        
        for food_item in interpreted_foods:
            food_name = food_item.selected_food_description
            
            for nutrient_name, nutrient_value in food_item.processed_nutrients.items():
                if nutrient_name not in aggregated:
                    aggregated[nutrient_name] = {
                        "total_amount": 0.0,
                        "unit": nutrient_value.unit,
                        "contributing_foods": [],
                        "unit_conflicts": set()
                    }
                
                # 単位の整合性チェック
                if aggregated[nutrient_name]["unit"] != nutrient_value.unit:
                    aggregated[nutrient_name]["unit_conflicts"].add(nutrient_value.unit)
                    logger.warning(f"Unit conflict for {nutrient_name}: {aggregated[nutrient_name]['unit']} vs {nutrient_value.unit}")
                    
                    # 単位変換を試行（簡易版）
                    converted_amount = self._convert_nutrient_units(
                        nutrient_value.amount, 
                        nutrient_value.unit, 
                        aggregated[nutrient_name]["unit"]
                    )
                else:
                    converted_amount = nutrient_value.amount
                
                # 集計
                aggregated[nutrient_name]["total_amount"] += converted_amount
                aggregated[nutrient_name]["contributing_foods"].append(
                    f"{food_name} ({nutrient_value.amount} {nutrient_value.unit})"
                )
        
        # 丸め処理
        for nutrient_data in aggregated.values():
            nutrient_data["total_amount"] = round(
                nutrient_data["total_amount"], 
                self.rounding_precision
            )
        
        logger.info(f"Aggregated {len(aggregated)} unique nutrients from {len(interpreted_foods)} food items")
        return aggregated
    
    def _create_nutrient_summaries(
        self, 
        aggregated_nutrients: Dict[str, Dict[str, Any]], 
        interpreted_foods: List[InterpretedFoodItem]
    ) -> Dict[str, NutrientSummary]:
        """栄養素サマリーを作成"""
        summaries = {}
        
        for nutrient_name, nutrient_data in aggregated_nutrients.items():
            # DV計算
            daily_value_percentage = None
            if self.enable_daily_values and nutrient_name in self.daily_values:
                dv = self.daily_values[nutrient_name]
                daily_value_percentage = (nutrient_data["total_amount"] / dv) * 100
                daily_value_percentage = round(daily_value_percentage, 1)
            
            summaries[nutrient_name] = NutrientSummary(
                total_amount=nutrient_data["total_amount"],
                unit=nutrient_data["unit"],
                contributing_foods=nutrient_data["contributing_foods"],
                daily_value_percentage=daily_value_percentage
            )
        
        return summaries
    
    def _create_metadata(self, structured_info: StructuredNutrientInfo) -> Dict[str, Any]:
        """レポートメタデータを作成"""
        return {
            "calculation_timestamp": datetime.utcnow().isoformat() + "Z",
            "num_food_items_processed": len(structured_info.interpreted_foods),
            "interpretation_strategy_used": structured_info.interpretation_strategy_used,
            "has_interpretation_errors": structured_info.has_errors(),
            "interpretation_errors_count": len(structured_info.parsing_errors) if structured_info.parsing_errors else 0,
            "rounding_precision_used": self.rounding_precision,
            "daily_values_enabled": self.enable_daily_values,
            "processing_metadata": structured_info.processing_metadata
        }
    
    def _calculate_macro_breakdown(self, nutrient_summaries: Dict[str, NutrientSummary]) -> Optional[Dict[str, float]]:
        """マクロ栄養素内訳を計算（カロリー比率）"""
        try:
            # カロリー計算（1g = 4kcal for protein/carbs, 9kcal for fat）
            protein_g = nutrient_summaries.get("PROTEIN", NutrientSummary(total_amount=0, unit="g", contributing_foods=[])).total_amount
            fat_g = nutrient_summaries.get("TOTAL_FAT", NutrientSummary(total_amount=0, unit="g", contributing_foods=[])).total_amount
            carb_g = nutrient_summaries.get("CARBOHYDRATE_BY_DIFFERENCE", NutrientSummary(total_amount=0, unit="g", contributing_foods=[])).total_amount
            
            protein_kcal = protein_g * 4
            fat_kcal = fat_g * 9
            carb_kcal = carb_g * 4
            total_macro_kcal = protein_kcal + fat_kcal + carb_kcal
            
            if total_macro_kcal == 0:
                return None
            
            return {
                "protein_percentage": round((protein_kcal / total_macro_kcal) * 100, 1),
                "fat_percentage": round((fat_kcal / total_macro_kcal) * 100, 1),
                "carbohydrate_percentage": round((carb_kcal / total_macro_kcal) * 100, 1),
                "total_macro_kcal": round(total_macro_kcal, 1)
            }
        except Exception as e:
            logger.warning(f"Failed to calculate macro breakdown: {e}")
            return None
    
    def _calculate_completeness_score(self, interpreted_foods: List[InterpretedFoodItem]) -> float:
        """栄養データの完全性スコアを計算"""
        if not interpreted_foods:
            return 0.0
        
        # 期待される主要栄養素
        expected_nutrients = ["PROTEIN", "TOTAL_FAT", "CARBOHYDRATE_BY_DIFFERENCE", "CALORIES"]
        
        total_score = 0
        for food_item in interpreted_foods:
            item_score = 0
            for nutrient in expected_nutrients:
                if nutrient in food_item.processed_nutrients:
                    item_score += 1
            total_score += item_score / len(expected_nutrients)
        
        completeness = total_score / len(interpreted_foods)
        return round(completeness, 3)
    
    def _calculate_total_weight(self, interpreted_foods: List[InterpretedFoodItem]) -> Optional[float]:
        """総重量を計算"""
        total_weight = 0
        weight_found = False
        
        for food_item in interpreted_foods:
            if food_item.serving_size_g:
                total_weight += food_item.serving_size_g
                weight_found = True
        
        return round(total_weight, 1) if weight_found else None
    
    def _convert_nutrient_units(self, amount: float, from_unit: str, to_unit: str) -> float:
        """栄養素単位の変換（簡易版）"""
        if from_unit == to_unit:
            return amount
        
        # 基本的な変換
        conversion_map = {
            ("mg", "g"): 0.001,
            ("g", "mg"): 1000,
            ("µg", "mg"): 0.001,
            ("mg", "µg"): 1000,
            ("µg", "g"): 0.000001,
            ("g", "µg"): 1000000
        }
        
        conversion_key = (from_unit, to_unit)
        if conversion_key in conversion_map:
            converted = amount * conversion_map[conversion_key]
            logger.info(f"Converted {amount} {from_unit} to {converted} {to_unit}")
            return converted
        
        # 変換できない場合は元の値を返す
        logger.warning(f"No conversion available from {from_unit} to {to_unit}")
        return amount
    
    def _create_empty_report(self, structured_info: StructuredNutrientInfo) -> FinalNutritionReport:
        """空のレポートを作成"""
        return FinalNutritionReport(
            total_nutrients={},
            detailed_items=[],
            metadata={
                "status": "No nutrition data available",
                "calculation_timestamp": datetime.utcnow().isoformat() + "Z",
                "num_food_items_processed": 0,
                "interpretation_strategy_used": structured_info.interpretation_strategy_used,
                "has_interpretation_errors": structured_info.has_errors(),
                "error_details": structured_info.parsing_errors
            }
        ) 