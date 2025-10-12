#!/usr/bin/env python3
"""
Nutrition Calculation Component

Phase1結果と栄養検索結果から実際の栄養素を計算するコンポーネント
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from shared.components.base import BaseComponent
from shared.models.nutrition_calculation_models import (
    NutritionCalculationInput,
    NutritionCalculationOutput,
    NutritionInfo,
    IngredientNutrition,
    DishNutrition,
    MealNutrition
)
from shared.models.phase1_models import Phase1Output
from shared.models.nutrition_search_models import NutritionQueryOutput, NutritionMatch


class NutritionCalculationComponent(BaseComponent[NutritionCalculationInput, NutritionCalculationOutput]):
    """栄養計算コンポーネント"""
    
    def __init__(self):
        super().__init__("NutritionCalculationComponent")
        
    async def process(self, input_data: NutritionCalculationInput) -> NutritionCalculationOutput:
        """
        栄養計算の主処理
        
        Args:
            input_data: Phase1結果と栄養検索結果
            
        Returns:
            NutritionCalculationOutput: 計算された栄養情報
        """
        start_time = datetime.now()
        
        phase1_result: Phase1Output = input_data.phase1_result
        nutrition_search_result: NutritionQueryOutput = input_data.nutrition_search_result
        
        self.logger.info(f"Starting nutrition calculation for {len(phase1_result.dishes)} dishes")
        
        # 料理別の栄養計算
        dish_nutritions = []
        total_meal_nutrition = None
        warnings = []
        
        for dish in phase1_result.dishes:
            try:
                dish_nutrition = await self._calculate_dish_nutrition(
                    dish, nutrition_search_result.matches
                )
                dish_nutritions.append(dish_nutrition)
                
                # 食事全体の栄養情報を累積
                if total_meal_nutrition is None:
                    total_meal_nutrition = dish_nutrition.total_nutrition
                else:
                    total_meal_nutrition = total_meal_nutrition + dish_nutrition.total_nutrition
                    
            except Exception as e:
                warning_msg = f"Failed to calculate nutrition for dish '{dish.dish_name}': {str(e)}"
                self.logger.warning(warning_msg)
                warnings.append(warning_msg)
        
        # デフォルト値の設定
        if total_meal_nutrition is None:
            total_meal_nutrition = NutritionInfo(
                calories=0.0, protein=0.0, fat=0.0, carbs=0.0
            )
        
        # 計算サマリーの作成
        end_time = datetime.now()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        calculation_summary = {
            "total_dishes": len(phase1_result.dishes),
            "successful_calculations": len(dish_nutritions),
            "failed_calculations": len(phase1_result.dishes) - len(dish_nutritions),
            "total_ingredients": sum(len(dish.ingredients) for dish in dish_nutritions),
            "processing_time_ms": processing_time_ms
        }
        
        # 食事全体の栄養情報
        meal_nutrition = MealNutrition(
            dishes=dish_nutritions,
            total_nutrition=total_meal_nutrition,
            calculation_summary=calculation_summary,
            warnings=warnings
        )
        
        # メタデータ
        calculation_metadata = {
            "calculation_timestamp": end_time.isoformat(),
            "total_nutrition_matches": nutrition_search_result.get_total_matches()
        }
        
        result = NutritionCalculationOutput(
            meal_nutrition=meal_nutrition,
            calculation_metadata=calculation_metadata,
            processing_time_ms=processing_time_ms
        )
        
        self.logger.info(f"Nutrition calculation completed: {len(dish_nutritions)} dishes, "
                        f"{calculation_summary['total_ingredients']} ingredients, "
                        f"{total_meal_nutrition.calories:.1f} kcal total")
        
        return result
    
    async def _calculate_dish_nutrition(self, dish, nutrition_matches: Dict[str, Any]) -> DishNutrition:
        """
        料理レベルの栄養計算
        
        Args:
            dish: Phase1で検出された料理
            nutrition_matches: 栄養検索結果のマッチング
            
        Returns:
            DishNutrition: 料理の栄養計算結果
        """
        ingredient_nutritions = []
        dish_total_nutrition = None
        
        for ingredient in dish.ingredients:
            try:
                ingredient_nutrition = await self._calculate_ingredient_nutrition(
                    ingredient, nutrition_matches
                )
                ingredient_nutritions.append(ingredient_nutrition)
                
                # 料理全体の栄養情報を累積
                if dish_total_nutrition is None:
                    dish_total_nutrition = ingredient_nutrition.calculated_nutrition
                else:
                    dish_total_nutrition = dish_total_nutrition + ingredient_nutrition.calculated_nutrition
                    
            except Exception as e:
                self.logger.error(f"Failed to calculate nutrition for ingredient '{ingredient.ingredient_name}': {e}")
                raise
        
        # デフォルト値の設定
        if dish_total_nutrition is None:
            dish_total_nutrition = NutritionInfo(
                calories=0.0, protein=0.0, fat=0.0, carbs=0.0
            )
        
        # 計算メタデータ
        calculation_metadata = {
            "ingredient_count": len(ingredient_nutritions),
            "total_weight_g": sum(ing.weight_g for ing in ingredient_nutritions),
            "calculation_method": "weight_based_scaling"
        }
        
        return DishNutrition(
            dish_name=dish.dish_name,
            confidence=dish.confidence or 0.0,
            ingredients=ingredient_nutritions,
            total_nutrition=dish_total_nutrition,
            calculation_metadata=calculation_metadata
        )
    
    async def _calculate_ingredient_nutrition(self, ingredient, nutrition_matches: Dict[str, Any]) -> IngredientNutrition:
        """
        食材レベルの栄養計算（新方式: default_unit + unit_to_grams）
        
        Args:
            ingredient: Phase1で検出された食材
            nutrition_matches: 栄養検索結果のマッチング
            
        Returns:
            IngredientNutrition: 食材の栄養計算結果
        """
        ingredient_name = ingredient.ingredient_name
        weight_g = ingredient.weight_g
        
        # 栄養検索結果から該当する食材を取得
        if ingredient_name not in nutrition_matches:
            raise ValueError(f"No nutrition data found for ingredient '{ingredient_name}'")
        
        nutrition_match = nutrition_matches[ingredient_name]
        
        # リスト形式の場合は最初の要素を使用
        if isinstance(nutrition_match, list):
            if len(nutrition_match) == 0:
                raise ValueError(f"Empty nutrition match list for ingredient '{ingredient_name}'")
            nutrition_match = nutrition_match[0]
        
        # NutritionMatchオブジェクトから栄養情報を取得
        if not isinstance(nutrition_match, NutritionMatch):
            raise ValueError(f"Invalid nutrition match type for ingredient '{ingredient_name}': {type(nutrition_match)}")
        
        source_db = nutrition_match.source_db

        # 新方式の栄養データフィールドを取得（NutritionMatchオブジェクトの属性として）
        default_unit = nutrition_match.default_unit
        default_nutrition = nutrition_match.default_nutrition
        unit_to_grams = nutrition_match.unit_to_grams

        # 旧方式の栄養データ（100g基準、フォールバック用）
        nutrition_data = nutrition_match.nutrition
        
        # 新方式データの存在確認
        if not default_unit or not default_nutrition or not unit_to_grams:
            # フォールバック: 旧方式（100g基準）
            nutrition_per_100g = nutrition_data
            
            # 必須栄養価データの検証
            required_nutrients = ["calories", "protein", "fat", "carbs"]
            for nutrient in required_nutrients:
                if nutrient not in nutrition_per_100g:
                    raise ValueError(f"Missing required nutrition data '{nutrient}' for ingredient '{ingredient_name}' from {source_db}")
                if nutrition_per_100g[nutrient] is None:
                    raise ValueError(f"Null value for required nutrition data '{nutrient}' for ingredient '{ingredient_name}' from {source_db}")
            
            # 100g基準の計算（フォールバック）
            scaling_factor = weight_g / 100.0
            
            calculated_nutrition = NutritionInfo(
                calories=nutrition_per_100g["calories"] * scaling_factor,
                protein=nutrition_per_100g["protein"] * scaling_factor,
                fat=nutrition_per_100g["fat"] * scaling_factor,
                carbs=nutrition_per_100g["carbs"] * scaling_factor,
                fiber=nutrition_per_100g.get("fiber") * scaling_factor if nutrition_per_100g.get("fiber") is not None else None,
                sugar=nutrition_per_100g.get("sugar") * scaling_factor if nutrition_per_100g.get("sugar") is not None else None,
                sodium=nutrition_per_100g.get("sodium") * scaling_factor if nutrition_per_100g.get("sodium") is not None else None
            )
            
            calculation_notes = [
                f"Scaled from 100g base data using factor {scaling_factor:.3f} (fallback method)",
                f"Source: {source_db} database"
            ]
            
        else:
            # 新方式: default_unit + unit_to_gramsを使用
            
            # default_unitがunit_to_gramsに存在することを確認
            if default_unit not in unit_to_grams:
                raise ValueError(f"default_unit '{default_unit}' not found in unit_to_grams for ingredient '{ingredient_name}'")
            
            # 必須栄養価データの検証（新方式フィールド名）
            required_nutrients = ["calorie", "Protein_g", "Total_Fat_g", "Total_Carbs_g"]
            for nutrient in required_nutrients:
                if nutrient not in default_nutrition:
                    raise ValueError(f"Missing required nutrition data '{nutrient}' for ingredient '{ingredient_name}' from {source_db}")
                if default_nutrition[nutrient] is None:
                    raise ValueError(f"Null value for required nutrition data '{nutrient}' for ingredient '{ingredient_name}' from {source_db}")
            
            # グラム換算係数を計算
            grams_per_unit = unit_to_grams[default_unit]
            per_gram_factor = 1.0 / grams_per_unit
            
            # 栄養計算（新方式）
            calculated_nutrition = NutritionInfo(
                calories=default_nutrition["calorie"] * per_gram_factor * weight_g,
                protein=default_nutrition["Protein_g"] * per_gram_factor * weight_g,
                fat=default_nutrition["Total_Fat_g"] * per_gram_factor * weight_g,
                carbs=default_nutrition["Total_Carbs_g"] * per_gram_factor * weight_g,
                fiber=default_nutrition.get("Dietary_Fiber_g") * per_gram_factor * weight_g if default_nutrition.get("Dietary_Fiber_g") is not None else None,
                sugar=default_nutrition.get("Total_Sugars_g") * per_gram_factor * weight_g if default_nutrition.get("Total_Sugars_g") is not None else None,
                sodium=default_nutrition.get("Sodium_mg") * per_gram_factor * weight_g if default_nutrition.get("Sodium_mg") is not None else None
            )
            
            calculation_notes = [
                f"Calculated using default_unit method: {default_nutrition['calorie']:.1f}kcal/{default_unit} = {default_nutrition['calorie'] * per_gram_factor:.3f}kcal/g × {weight_g}g",
                f"Conversion: 1 {default_unit} = {grams_per_unit}g",
                f"Source: {source_db} database"
            ]
        
        # 100g換算値（互換性のため）
        nutrition_per_100g = {
            "calories": calculated_nutrition.calories / weight_g * 100 if weight_g > 0 else 0,
            "protein": calculated_nutrition.protein / weight_g * 100 if weight_g > 0 else 0,
            "fat": calculated_nutrition.fat / weight_g * 100 if weight_g > 0 else 0,
            "carbs": calculated_nutrition.carbs / weight_g * 100 if weight_g > 0 else 0,
        }
        
        return IngredientNutrition(
            ingredient_name=ingredient_name,
            weight_g=weight_g,
            nutrition_per_100g=nutrition_per_100g,
            calculated_nutrition=calculated_nutrition,
            source_db=source_db,
            calculation_notes=calculation_notes
        ) 