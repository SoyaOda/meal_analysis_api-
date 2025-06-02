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

    @staticmethod
    def convert_raw_nutrients_to_cooked(
        raw_nutrients_per_100g: Dict[str, float],
        food_category: str,  # 例: "pasta", "chicken_breast", "potatoes"
        target_preparation_method: str,  # 例: "boiled", "roasted"
        original_raw_weight_g: float = 100.0  # 通常は100gベースで変換
    ) -> Dict[str, float]:
        """
        生の状態の100gあたり栄養素を、指定された調理方法適用後の
        調理済み100gあたり栄養素に変換する (v2.2新機能)
        
        Args:
            raw_nutrients_per_100g: 生の状態での100gあたり栄養素辞書
            food_category: 食品カテゴリ（歩留まりと保持率の決定に使用）
            target_preparation_method: 目標調理方法
            original_raw_weight_g: 元の生重量（通常は100g）
            
        Returns:
            Dict[str, float]: 調理済み100gあたりの栄養素辞書
        """
        # 1. food_category と target_preparation_method に基づいて、
        #    重量変化率（歩留まり係数 cooked_weight / raw_weight）を取得。
        yield_factor = NutritionCalculationService._get_yield_factor(food_category, target_preparation_method)
        
        # 2. 栄養素保持率を取得。
        retention_factors = NutritionCalculationService._get_retention_factors(food_category, target_preparation_method)
        
        cooked_nutrients_per_100g = {}
        for nutrient_name, raw_value_per_100g_raw in raw_nutrients_per_100g.items():
            if raw_value_per_100g_raw is None:  # Optionalな栄養素がNoneの場合
                cooked_nutrients_per_100g[nutrient_name] = None
                continue
            
            # a. 重量変化による濃度変化を計算
            #    調理済み100gあたりの栄養素量 = (元の100g中の栄養素量 / 歩留まり係数)
            value_adjusted_for_yield = raw_value_per_100g_raw / yield_factor
            
            # b. 栄養素保持率を適用
            retention = retention_factors.get(nutrient_name, 1.0)  # デフォルト保持率100%
            final_value = value_adjusted_for_yield * retention
            
            cooked_nutrients_per_100g[nutrient_name] = round(final_value, 3)  # 有効数字3桁程度
        
        logger.info(f"Converted raw nutrients for {food_category} ({target_preparation_method}) to cooked state. "
                   f"Yield: {yield_factor}, Retention applied: {len([k for k, v in retention_factors.items() if v != 1.0])} nutrients")
        return cooked_nutrients_per_100g
    
    @staticmethod
    def _get_yield_factor(food_category: str, prep_method: str) -> float:
        """
        食品カテゴリと調理方法に基づいて歩留まり係数を取得
        歩留まり係数 = 調理後重量 / 調理前重量
        
        Args:
            food_category: 食品カテゴリ
            prep_method: 調理方法
            
        Returns:
            float: 歩留まり係数
        """
        # 歩留まり係数データベース（実際の実装では外部ファイルまたはデータベースから読み込み）
        yield_database = {
            # パスタ類 - 乾燥から調理済みへ
            ("pasta", "boiled"): 2.4,
            ("pasta", "unknown"): 2.2,  # デフォルト
            ("macaroni", "boiled"): 2.4,
            ("noodles", "boiled"): 2.3,
            ("spaghetti", "boiled"): 2.4,
            ("penne", "boiled"): 2.4,
            
            # 肉類 - 生から調理済みへ（水分損失）
            ("chicken_breast", "roasted"): 0.75,
            ("chicken_breast", "grilled"): 0.72,
            ("chicken_breast", "baked"): 0.76,
            ("chicken", "roasted"): 0.74,
            ("chicken", "grilled"): 0.71,
            ("beef", "roasted"): 0.70,
            ("beef", "grilled"): 0.68,
            ("pork", "roasted"): 0.72,
            ("ground_meat", "baked"): 0.73,
            
            # 野菜類 - 生から調理済みへ
            ("potatoes", "boiled"): 0.98,  # 水分を吸収するが軽微
            ("potatoes", "baked"): 0.79,   # 水分損失
            ("carrots", "boiled"): 0.90,
            ("green_beans", "boiled"): 0.88,
            ("green_beans", "steamed"): 0.92,
            ("corn", "boiled"): 0.95,
            ("peas", "boiled"): 0.90,
            ("spinach", "steamed"): 0.10,  # 大幅に体積減少
            ("broccoli", "steamed"): 0.85,
            
            # 米・穀物類 - 乾燥から調理済みへ
            ("rice", "boiled"): 3.0,  # 米は水分を大幅に吸収
            ("quinoa", "boiled"): 2.8,
            ("barley", "boiled"): 2.5,
            
            # その他
            ("fish", "grilled"): 0.77,
            ("fish", "baked"): 0.80,
            ("eggs", "boiled"): 0.96,  # 重量変化は最小
        }
        
        # 完全一致を試行
        key = (food_category.lower(), prep_method.lower())
        if key in yield_database:
            return yield_database[key]
        
        # 部分一致を試行（カテゴリのみ）
        for (cat, method), factor in yield_database.items():
            if cat in food_category.lower() or food_category.lower() in cat:
                if method == prep_method.lower() or prep_method.lower() == "unknown":
                    return factor
        
        # デフォルト値
        logger.warning(f"No yield factor found for {food_category} + {prep_method}, using default 1.0")
        return 1.0  # 変化なし
    
    @staticmethod
    def _get_retention_factors(food_category: str, prep_method: str) -> Dict[str, float]:
        """
        食品カテゴリと調理方法に基づいて栄養素保持率を取得
        
        Args:
            food_category: 食品カテゴリ
            prep_method: 調理方法
            
        Returns:
            Dict[str, float]: 栄養素名と保持率（0.0-1.0）のマッピング
        """
        # 基本的な保持率（多くの栄養素は90-100%保持）
        base_factors = {
            "calories_kcal": 1.0,      # カロリーは通常変化なし
            "protein_g": 0.95,         # タンパク質は若干の損失
            "carbohydrates_g": 0.98,   # 炭水化物は大きく変化しない
            "fat_g": 0.92,             # 脂質は調理により一部損失
            "fiber_g": 0.98,           # 食物繊維は比較的安定
            "sugars_g": 0.97,          # 糖類は比較的安定
            "sodium_mg": 1.05          # ナトリウムは濃縮により若干増加
        }
        
        # 特定の食品×調理方法の補正
        specific_adjustments = {
            # 野菜の茹で調理 - ビタミンなど水溶性栄養素の損失が大きい
            ("potatoes", "boiled"): {"vitamin_c_mg": 0.75},
            ("carrots", "boiled"): {"vitamin_c_mg": 0.80},
            ("green_beans", "boiled"): {"vitamin_c_mg": 0.70},
            ("broccoli", "steamed"): {"vitamin_c_mg": 0.85},  # 蒸しは保持率が高い
            
            # 肉類の調理 - 高温調理による損失
            ("chicken", "grilled"): {"protein_g": 0.92, "fat_g": 0.85},
            ("beef", "grilled"): {"protein_g": 0.90, "fat_g": 0.80},
            ("fish", "baked"): {"protein_g": 0.94, "fat_g": 0.88},
            
            # パスタ類 - 栄養素は比較的安定
            ("pasta", "boiled"): {"protein_g": 0.98, "carbohydrates_g": 0.99},
            
            # 葉物野菜 - 大幅な損失の可能性
            ("spinach", "steamed"): {"vitamin_c_mg": 0.50, "fiber_g": 0.95},
        }
        
        # 基本保持率から開始
        retention_factors = base_factors.copy()
        
        # 特定調整を適用
        key = (food_category.lower(), prep_method.lower())
        if key in specific_adjustments:
            retention_factors.update(specific_adjustments[key])
        else:
            # 部分一致を試行
            for (cat, method), adjustments in specific_adjustments.items():
                if (cat in food_category.lower() or food_category.lower() in cat) and method == prep_method.lower():
                    retention_factors.update(adjustments)
                    break
        
        return retention_factors

    @staticmethod
    def _map_ingredient_to_food_category(ingredient_name: str) -> str:
        """
        材料名から食品カテゴリにマッピングして、調理変換に使用
        
        Args:
            ingredient_name: Phase1で識別された材料名
            
        Returns:
            str: 調理変換に使用する食品カテゴリ
        """
        ingredient_lower = ingredient_name.lower()
        
        # パスタ類
        pasta_terms = ["pasta", "penne", "spaghetti", "macaroni", "noodles", "linguine", "fettuccine", "rigatoni"]
        if any(term in ingredient_lower for term in pasta_terms):
            return "pasta"
        
        # 肉類
        chicken_terms = ["chicken", "poultry"]
        if any(term in ingredient_lower for term in chicken_terms):
            if "breast" in ingredient_lower:
                return "chicken_breast"
            else:
                return "chicken"
        
        beef_terms = ["beef", "steak", "hamburger"]
        if any(term in ingredient_lower for term in beef_terms):
            return "beef"
        
        pork_terms = ["pork", "ham", "bacon"]
        if any(term in ingredient_lower for term in pork_terms):
            return "pork"
        
        meat_terms = ["meat", "ground"]
        if any(term in ingredient_lower for term in meat_terms):
            return "ground_meat"
        
        fish_terms = ["fish", "salmon", "tuna", "cod", "tilapia", "trout"]
        if any(term in ingredient_lower for term in fish_terms):
            return "fish"
        
        # 野菜類
        potato_terms = ["potato", "potatoes"]
        if any(term in ingredient_lower for term in potato_terms):
            return "potatoes"
        
        carrot_terms = ["carrot", "carrots"]
        if any(term in ingredient_lower for term in carrot_terms):
            return "carrots"
        
        green_bean_terms = ["green bean", "green beans", "string bean"]
        if any(term in ingredient_lower for term in green_bean_terms):
            return "green_beans"
        
        corn_terms = ["corn"]
        if any(term in ingredient_lower for term in corn_terms):
            return "corn"
        
        peas_terms = ["peas", "green peas"]
        if any(term in ingredient_lower for term in peas_terms):
            return "peas"
        
        spinach_terms = ["spinach"]
        if any(term in ingredient_lower for term in spinach_terms):
            return "spinach"
        
        broccoli_terms = ["broccoli"]
        if any(term in ingredient_lower for term in broccoli_terms):
            return "broccoli"
        
        # 穀物類
        rice_terms = ["rice"]
        if any(term in ingredient_lower for term in rice_terms):
            return "rice"
        
        quinoa_terms = ["quinoa"]
        if any(term in ingredient_lower for term in quinoa_terms):
            return "quinoa"
        
        barley_terms = ["barley"]
        if any(term in ingredient_lower for term in barley_terms):
            return "barley"
        
        # その他
        egg_terms = ["egg", "eggs"]
        if any(term in ingredient_lower for term in egg_terms):
            return "eggs"
        
        # デフォルト：食品名をそのまま使用（小文字化）
        logger.info(f"No specific food category mapping found for '{ingredient_name}', using generic mapping")
        return ingredient_lower.replace(" ", "_")


# サービスインスタンスを取得するファクトリ関数
def get_nutrition_calculation_service() -> NutritionCalculationService:
    """
    栄養計算サービスインスタンスを取得
    
    Returns:
        NutritionCalculationService: 栄養計算サービスインスタンス
    """
    return NutritionCalculationService() 