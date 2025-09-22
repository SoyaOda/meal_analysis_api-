"""
Shared models for unified API system
"""

# Phase1 Models
from .phase1_models import (
    Phase1Input,
    Phase1Output,
    DetectedFoodItem,
    Dish,
    Ingredient,
    RootResponse
)

# Nutrition Search Models - 存在するものだけインポート
try:
    from .nutrition_search_models import (
        SuggestionResponse,
        SuggestionErrorResponse,
        QueryInfo,
        Suggestion,
        FoodInfo,
        NutritionPreview,
        SearchMetadata,
        SearchStatus,
        DebugInfo,
        NutritionQueryInput,
        NutritionQueryOutput,
        NutritionMatch
    )
except ImportError:
    # nutrition_search_modelsが見つからない場合は無視
    pass

# Nutrition Calculation Models - 存在するものだけインポート
try:
    from .nutrition_calculation_models import (
        NutritionCalculationInput,
        NutritionCalculationOutput,
        NutritionInfo,
        IngredientNutrition,
        DishNutrition,
        MealNutrition
    )
except ImportError:
    # nutrition_calculation_modelsが見つからない場合は無視
    pass

__all__ = [
    # Phase1 Models
    "Phase1Input",
    "Phase1Output",
    "DetectedFoodItem",
    "Dish",
    "Ingredient",
    "RootResponse",

    # Nutrition Search Models
    "SuggestionResponse",
    "SuggestionErrorResponse",
    "QueryInfo",
    "Suggestion",
    "FoodInfo",
    "NutritionPreview",
    "SearchMetadata",
    "SearchStatus",
    "DebugInfo",
    "NutritionQueryInput",
    "NutritionQueryOutput",
    "NutritionMatch",

    # Nutrition Calculation Models
    "NutritionCalculationInput",
    "NutritionCalculationOutput",
    "NutritionInfo",
    "IngredientNutrition",
    "DishNutrition",
    "MealNutrition"
]