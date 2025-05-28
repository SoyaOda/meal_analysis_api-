"""
栄養素計算サービス

このサービスは純粋な計算ロジックを提供します：
1. 100gあたりの栄養素データから実際の栄養素を計算
2. 食材リストから料理全体の栄養素を集計
3. 料理リストから食事全体の栄養素を集計
"""

import logging
from typing import List, Optional, Dict
from ..api.v1.schemas.meal import CalculatedNutrients, RefinedIngredient, RefinedDish

logger = logging.getLogger(__name__)


class NutritionCalculationService:
    """栄養素計算サービスクラス"""
    
    @staticmethod
    def calculate_actual_nutrients(
        key_nutrients_per_100g: Dict[str, float], 
        estimated_weight_g: float
    ) -> CalculatedNutrients:
        """
        100gあたりの主要栄養素データから実際の栄養素量を計算
        
        Args:
            key_nutrients_per_100g: 100gあたりの主要栄養素データ
            estimated_weight_g: 推定グラム数
            
        Returns:
            CalculatedNutrients: 計算済み栄養素オブジェクト
        """
        if not key_nutrients_per_100g or estimated_weight_g <= 0:
            logger.warning(f"Invalid input: key_nutrients_per_100g={key_nutrients_per_100g}, estimated_weight_g={estimated_weight_g}")
            return CalculatedNutrients()  # デフォルト値（全て0.0）を返す
        
        try:
            # 計算式: (Nutrient_Value_per_100g / 100) × estimated_weight_g
            multiplier = estimated_weight_g / 100.0
            
            # 各栄養素を計算（見つからない/Noneの場合は0.0として扱う）
            calories_kcal = round((key_nutrients_per_100g.get('calories_kcal', 0.0) or 0.0) * multiplier, 2)
            protein_g = round((key_nutrients_per_100g.get('protein_g', 0.0) or 0.0) * multiplier, 2)
            carbohydrates_g = round((key_nutrients_per_100g.get('carbohydrates_g', 0.0) or 0.0) * multiplier, 2)
            fat_g = round((key_nutrients_per_100g.get('fat_g', 0.0) or 0.0) * multiplier, 2)
            
            result = CalculatedNutrients(
                calories_kcal=calories_kcal,
                protein_g=protein_g,
                carbohydrates_g=carbohydrates_g,
                fat_g=fat_g
            )
            
            logger.debug(f"Calculated nutrients for {estimated_weight_g}g: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating actual nutrients: {e}")
            return CalculatedNutrients()  # エラー時はデフォルト値を返す
    
    @staticmethod
    def aggregate_nutrients_for_dish_from_ingredients(
        ingredients: List[RefinedIngredient]
    ) -> CalculatedNutrients:
        """
        材料リストから料理全体の栄養素を集計
        
        Args:
            ingredients: RefinedIngredientのリスト（各要素は計算済みのactual_nutrientsを持つ）
            
        Returns:
            CalculatedNutrients: 料理の集計栄養素
        """
        if not ingredients:
            logger.warning("No ingredients provided for aggregation")
            return CalculatedNutrients()
        
        try:
            total_calories = 0.0
            total_protein = 0.0
            total_carbohydrates = 0.0
            total_fat = 0.0
            
            calculated_count = 0
            
            for ingredient in ingredients:
                if ingredient.actual_nutrients:
                    total_calories += ingredient.actual_nutrients.calories_kcal
                    total_protein += ingredient.actual_nutrients.protein_g
                    total_carbohydrates += ingredient.actual_nutrients.carbohydrates_g
                    total_fat += ingredient.actual_nutrients.fat_g
                    calculated_count += 1
                else:
                    logger.warning(f"Ingredient '{ingredient.ingredient_name}' has no actual_nutrients")
            
            # 小数点以下2桁に丸める
            result = CalculatedNutrients(
                calories_kcal=round(total_calories, 2),
                protein_g=round(total_protein, 2),
                carbohydrates_g=round(total_carbohydrates, 2),
                fat_g=round(total_fat, 2)
            )
            
            logger.info(f"Aggregated nutrients from {calculated_count}/{len(ingredients)} ingredients: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error aggregating nutrients for dish: {e}")
            return CalculatedNutrients()
    
    @staticmethod
    def aggregate_nutrients_for_meal(
        dishes: List[RefinedDish]
    ) -> CalculatedNutrients:
        """
        料理リストから食事全体の栄養素を集計
        
        Args:
            dishes: RefinedDishのリスト（各要素は計算済みのdish_total_actual_nutrientsを持つ）
            
        Returns:
            CalculatedNutrients: 食事全体の総栄養素
        """
        if not dishes:
            logger.warning("No dishes provided for meal aggregation")
            return CalculatedNutrients()
        
        try:
            total_calories = 0.0
            total_protein = 0.0
            total_carbohydrates = 0.0
            total_fat = 0.0
            
            calculated_count = 0
            
            for dish in dishes:
                if dish.dish_total_actual_nutrients:
                    total_calories += dish.dish_total_actual_nutrients.calories_kcal
                    total_protein += dish.dish_total_actual_nutrients.protein_g
                    total_carbohydrates += dish.dish_total_actual_nutrients.carbohydrates_g
                    total_fat += dish.dish_total_actual_nutrients.fat_g
                    calculated_count += 1
                else:
                    logger.warning(f"Dish '{dish.dish_name}' has no dish_total_actual_nutrients")
            
            # 小数点以下2桁に丸める
            result = CalculatedNutrients(
                calories_kcal=round(total_calories, 2),
                protein_g=round(total_protein, 2),
                carbohydrates_g=round(total_carbohydrates, 2),
                fat_g=round(total_fat, 2)
            )
            
            logger.info(f"Aggregated meal nutrients from {calculated_count}/{len(dishes)} dishes: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error aggregating nutrients for meal: {e}")
            return CalculatedNutrients()


# サービスインスタンスを取得するファクトリ関数
def get_nutrition_calculation_service() -> NutritionCalculationService:
    """
    栄養計算サービスインスタンスを取得
    
    Returns:
        NutritionCalculationService: 栄養計算サービスインスタンス
    """
    return NutritionCalculationService() 