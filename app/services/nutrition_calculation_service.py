"""
栄養素計算サービス (v2.1対応)

このサービスは純粋な計算ロジックを提供します：
1. 100gあたりの栄養素データから実際の栄養素を計算
2. 食材リストから料理全体の栄養素を集計
3. 料理リストから食事全体の栄養素を集計
4. Phase2での重量再計算とバランシング
"""

import logging
from typing import List, Optional, Dict, Tuple
from ..api.v1.schemas.meal import CalculatedNutrients, RefinedIngredientResponse, RefinedDishResponse, Phase1Ingredient

logger = logging.getLogger(__name__)


class WeightCalculationResult:
    """重量計算結果を格納するクラス"""
    def __init__(self, 
                 final_weight_g: float, 
                 calculation_method: str, 
                 original_phase1_weight_g: Optional[float] = None,
                 ingredient_weights: Optional[Dict[str, float]] = None):
        self.final_weight_g = final_weight_g
        self.calculation_method = calculation_method
        self.original_phase1_weight_g = original_phase1_weight_g
        self.ingredient_weights = ingredient_weights or {}


class NutritionCalculationService:
    """栄養素計算サービスクラス (v2.1対応)"""
    
    @staticmethod
    def calculate_actual_nutrients(
        key_nutrients_per_100g: Dict[str, float], 
        estimated_weight_g: float
    ) -> CalculatedNutrients:
        """
        100gあたりの主要栄養素データから実際の栄養素量を計算 (v2.1仕様)
        
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
            
            # v2.1で追加された栄養素も計算
            fiber_g = key_nutrients_per_100g.get('fiber_g')
            fiber_g = round(fiber_g * multiplier, 2) if fiber_g is not None else None
            
            sugars_g = key_nutrients_per_100g.get('sugars_g')
            sugars_g = round(sugars_g * multiplier, 2) if sugars_g is not None else None
            
            sodium_mg = key_nutrients_per_100g.get('sodium_mg')
            sodium_mg = round(sodium_mg * multiplier, 2) if sodium_mg is not None else None
            
            result = CalculatedNutrients(
                calories_kcal=calories_kcal,
                protein_g=protein_g,
                carbohydrates_g=carbohydrates_g,
                fat_g=fat_g,
                fiber_g=fiber_g,
                sugars_g=sugars_g,
                sodium_mg=sodium_mg
            )
            
            logger.debug(f"Calculated nutrients for {estimated_weight_g}g: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating actual nutrients: {e}")
            return CalculatedNutrients()  # エラー時はデフォルト値を返す
    
    @staticmethod
    def aggregate_nutrients_for_dish_from_ingredients(
        ingredients: List[RefinedIngredientResponse]
    ) -> CalculatedNutrients:
        """
        材料リストから料理全体の栄養素を集計 (v2.1仕様)
        
        Args:
            ingredients: RefinedIngredientResponseのリスト（各要素は計算済みのactual_nutrientsを持つ）
            
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
            total_fiber = 0.0
            total_sugars = 0.0
            total_sodium = 0.0
            
            # Optional栄養素のカウンター
            fiber_count = 0
            sugars_count = 0
            sodium_count = 0
            calculated_count = 0
            
            for ingredient in ingredients:
                if ingredient.actual_nutrients:
                    total_calories += ingredient.actual_nutrients.calories_kcal
                    total_protein += ingredient.actual_nutrients.protein_g
                    total_carbohydrates += ingredient.actual_nutrients.carbohydrates_g
                    total_fat += ingredient.actual_nutrients.fat_g
                    
                    # Optional栄養素の処理
                    if ingredient.actual_nutrients.fiber_g is not None:
                        total_fiber += ingredient.actual_nutrients.fiber_g
                        fiber_count += 1
                    
                    if ingredient.actual_nutrients.sugars_g is not None:
                        total_sugars += ingredient.actual_nutrients.sugars_g
                        sugars_count += 1
                    
                    if ingredient.actual_nutrients.sodium_mg is not None:
                        total_sodium += ingredient.actual_nutrients.sodium_mg
                        sodium_count += 1
                    
                    calculated_count += 1
                else:
                    logger.warning(f"Ingredient '{ingredient.ingredient_name}' has no actual_nutrients")
            
            # 小数点以下2桁に丸める
            result = CalculatedNutrients(
                calories_kcal=round(total_calories, 2),
                protein_g=round(total_protein, 2),
                carbohydrates_g=round(total_carbohydrates, 2),
                fat_g=round(total_fat, 2),
                fiber_g=round(total_fiber, 2) if fiber_count > 0 else None,
                sugars_g=round(total_sugars, 2) if sugars_count > 0 else None,
                sodium_mg=round(total_sodium, 2) if sodium_count > 0 else None
            )
            
            logger.info(f"Aggregated nutrients from {calculated_count}/{len(ingredients)} ingredients: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error aggregating nutrients for dish: {e}")
            return CalculatedNutrients()
    
    @staticmethod
    def aggregate_nutrients_for_meal(
        dishes: List[RefinedDishResponse]
    ) -> CalculatedNutrients:
        """
        料理リストから食事全体の栄養素を集計 (v2.1仕様)
        
        Args:
            dishes: RefinedDishResponseのリスト（各要素は計算済みのdish_total_actual_nutrientsを持つ）
            
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
            total_fiber = 0.0
            total_sugars = 0.0
            total_sodium = 0.0
            
            # Optional栄養素のカウンター
            fiber_count = 0
            sugars_count = 0
            sodium_count = 0
            calculated_count = 0
            
            for dish in dishes:
                if dish.dish_total_actual_nutrients:
                    total_calories += dish.dish_total_actual_nutrients.calories_kcal
                    total_protein += dish.dish_total_actual_nutrients.protein_g
                    total_carbohydrates += dish.dish_total_actual_nutrients.carbohydrates_g
                    total_fat += dish.dish_total_actual_nutrients.fat_g
                    
                    # Optional栄養素の処理
                    if dish.dish_total_actual_nutrients.fiber_g is not None:
                        total_fiber += dish.dish_total_actual_nutrients.fiber_g
                        fiber_count += 1
                    
                    if dish.dish_total_actual_nutrients.sugars_g is not None:
                        total_sugars += dish.dish_total_actual_nutrients.sugars_g
                        sugars_count += 1
                    
                    if dish.dish_total_actual_nutrients.sodium_mg is not None:
                        total_sodium += dish.dish_total_actual_nutrients.sodium_mg
                        sodium_count += 1
                    
                    calculated_count += 1
                else:
                    logger.warning(f"Dish '{dish.dish_name}' has no dish_total_actual_nutrients")
            
            # 小数点以下2桁に丸める
            result = CalculatedNutrients(
                calories_kcal=round(total_calories, 2),
                protein_g=round(total_protein, 2),
                carbohydrates_g=round(total_carbohydrates, 2),
                fat_g=round(total_fat, 2),
                fiber_g=round(total_fiber, 2) if fiber_count > 0 else None,
                sugars_g=round(total_sugars, 2) if sugars_count > 0 else None,
                sodium_mg=round(total_sodium, 2) if sodium_count > 0 else None
            )
            
            logger.info(f"Aggregated meal nutrients from {calculated_count}/{len(dishes)} dishes: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error aggregating nutrients for meal: {e}")
            return CalculatedNutrients()
    
    @staticmethod
    def calculate_refined_dish_weight(
        phase1_total_dish_weight_g: Optional[float],
        phase1_ingredients: List[Phase1Ingredient],
        calculation_strategy: str,
        has_valid_fdc_id: bool = True
    ) -> WeightCalculationResult:
        """
        Phase2で使用する精密な重量を計算
        
        Args:
            phase1_total_dish_weight_g: Phase1で推定された料理全体の重量
            phase1_ingredients: Phase1で認識された材料リスト
            calculation_strategy: 計算戦略 ("dish_level" or "ingredient_level")
            has_valid_fdc_id: 有効なFDC IDが取得できているか
            
        Returns:
            WeightCalculationResult: 計算結果
        """
        ingredients_total_weight = sum(ing.weight_g for ing in phase1_ingredients)
        
        # 材料重量の辞書を作成
        ingredient_weights = {ing.ingredient_name: ing.weight_g for ing in phase1_ingredients}
        
        if calculation_strategy == "dish_level" and has_valid_fdc_id:
            # dish_level戦略の場合、Phase1のdish全体重量を優先
            if phase1_total_dish_weight_g and phase1_total_dish_weight_g > 0:
                final_weight = phase1_total_dish_weight_g
                method = f"Phase1推定dish重量を使用: {phase1_total_dish_weight_g}g (材料合計: {ingredients_total_weight}g)"
            else:
                # フォールバック: 材料重量の合計
                final_weight = ingredients_total_weight
                method = f"Phase1 dish重量が無効のため材料重量合計を使用: {ingredients_total_weight}g"
        
        elif calculation_strategy == "ingredient_level":
            # ingredient_level戦略の場合、材料重量の合計を使用
            final_weight = ingredients_total_weight
            method = f"ingredient_level戦略により材料重量合計を使用: {ingredients_total_weight}g"
            
            # Phase1 dish重量との差異をチェック
            if phase1_total_dish_weight_g and abs(phase1_total_dish_weight_g - ingredients_total_weight) > 5:
                method += f" (Phase1 dish重量 {phase1_total_dish_weight_g}g との差異: {abs(phase1_total_dish_weight_g - ingredients_total_weight):.1f}g)"
        
        else:
            # dish_level戦略だがFDC IDが無効な場合
            final_weight = ingredients_total_weight
            method = f"dish_level戦略だがFDC ID無効のため材料重量合計を使用: {ingredients_total_weight}g"
        
        return WeightCalculationResult(
            final_weight_g=final_weight,
            calculation_method=method,
            original_phase1_weight_g=phase1_total_dish_weight_g,
            ingredient_weights=ingredient_weights
        )


# サービスインスタンスを取得するファクトリ関数
def get_nutrition_calculation_service() -> NutritionCalculationService:
    """
    栄養計算サービスインスタンスを取得
    
    Returns:
        NutritionCalculationService: 栄養計算サービスインスタンス
    """
    return NutritionCalculationService() 