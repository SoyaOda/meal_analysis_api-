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
        # Phase1には重量情報がないため、デフォルト重量推定を使用
        if not phase1_ingredients:
            return WeightCalculationResult(
                final_weight_g=100.0,  # デフォルト重量
                calculation_method="No ingredients found - using default weight",
                original_phase1_weight_g=phase1_total_dish_weight_g,
                ingredient_weights={}
            )
        
        # 簡単な画像ベース重量推定（材料数に基づく）
        ingredient_count = len(phase1_ingredients)
        
        # 基本的な重量推定ロジック
        if ingredient_count == 1:
            estimated_weight = 150.0  # 単一材料料理
        elif ingredient_count <= 3:
            estimated_weight = 200.0  # シンプルな料理
        elif ingredient_count <= 5:
            estimated_weight = 250.0  # 標準的な料理
        else:
            estimated_weight = 300.0  # 複雑な料理
        
        # 料理タイプに基づく調整
        dish_weight_adjustments = {
            'salad': 0.8,
            'soup': 1.2,
            'pasta': 1.1,
            'rice': 1.0,
            'meat': 1.3,
            'sandwich': 1.1,
            'dessert': 0.7
        }
        
        # 材料名から料理タイプを推定
        for ingredient in phase1_ingredients:
            name = ingredient.ingredient_name.lower()
            for dish_type, adjustment in dish_weight_adjustments.items():
                if dish_type in name:
                    estimated_weight *= adjustment
                    break
        
        estimated_weight = round(estimated_weight, 1)
        
        # 材料重量の辞書を作成（Phase2で推定）
        ingredient_weights = {}
        if phase1_ingredients:
            # estimate_ingredient_weights_from_dishを使用して材料重量を配分
            ingredient_weights = NutritionCalculationService.estimate_ingredient_weights_from_dish(
                estimated_weight, phase1_ingredients
            )
        
        method = f"Phase2 image-based weight estimation: {estimated_weight}g ({ingredient_count} ingredients)"
        
        return WeightCalculationResult(
            final_weight_g=estimated_weight,
            calculation_method=method,
            original_phase1_weight_g=phase1_total_dish_weight_g,
            ingredient_weights=ingredient_weights
        )

    @staticmethod
    def estimate_ingredient_weights_from_dish(
        total_dish_weight_g: float,
        ingredients: List[Phase1Ingredient]
    ) -> Dict[str, float]:
        """
        料理全体重量から各材料の重量を推定（Phase2重量計算用）
        
        Args:
            total_dish_weight_g: 料理全体の重量
            ingredients: Phase1で認識された材料リスト
            
        Returns:
            Dict[str, float]: 材料名 -> 推定重量のマッピング
        """
        if not ingredients or total_dish_weight_g <= 0:
            return {}
        
        # Phase1で重量情報がないため、基本的な推定ロジックを実装
        # 簡単な割合ベースの推定（将来的にはより高度な推定に置換可能）
        ingredient_count = len(ingredients)
        
        if ingredient_count == 1:
            # 材料が1つの場合、全重量を割り当て
            return {ingredients[0].ingredient_name: total_dish_weight_g}
        
        # 基本重量配分（均等分割からスタート）
        base_weight = total_dish_weight_g / ingredient_count
        
        # 材料タイプに基づく調整係数
        type_weights = {}
        for ingredient in ingredients:
            name = ingredient.ingredient_name.lower()
            
            # 肉類（高重量）
            if any(meat in name for meat in ['beef', 'chicken', 'pork', 'fish', 'meat', 'ground']):
                type_weights[ingredient.ingredient_name] = 1.5
            # 主食類（高重量）
            elif any(staple in name for staple in ['rice', 'pasta', 'noodle', 'bread', 'potato']):
                type_weights[ingredient.ingredient_name] = 1.3
            # チーズ・乳製品（中重量）
            elif any(dairy in name for dairy in ['cheese', 'milk', 'cream', 'butter']):
                type_weights[ingredient.ingredient_name] = 1.1
            # 野菜類（標準重量）
            elif any(veg in name for veg in ['lettuce', 'tomato', 'onion', 'pepper', 'carrot', 'bean', 'pea', 'corn']):
                type_weights[ingredient.ingredient_name] = 1.0
            # 調味料・ソース類（低重量）
            elif any(sauce in name for sauce in ['sauce', 'dressing', 'oil', 'seasoning', 'ketchup']):
                type_weights[ingredient.ingredient_name] = 0.3
            # その他（標準重量）
            else:
                type_weights[ingredient.ingredient_name] = 1.0
        
        # 重量係数の合計
        total_weight_factor = sum(type_weights.values())
        
        # 調整された重量配分
        estimated_weights = {}
        for ingredient in ingredients:
            weight_ratio = type_weights[ingredient.ingredient_name] / total_weight_factor
            estimated_weights[ingredient.ingredient_name] = round(total_dish_weight_g * weight_ratio, 1)
        
        logger.info(f"Estimated ingredient weights for dish ({total_dish_weight_g}g): {estimated_weights}")
        return estimated_weights


# サービスインスタンスを取得するファクトリ関数
def get_nutrition_calculation_service() -> NutritionCalculationService:
    """
    栄養計算サービスインスタンスを取得
    
    Returns:
        NutritionCalculationService: 栄養計算サービスインスタンス
    """
    return NutritionCalculationService() 