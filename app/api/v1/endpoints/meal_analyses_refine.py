from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from typing import Annotated, List, Optional, Dict
import json
import logging

# Pydanticモデル
from ..schemas.meal import (
    InitialAnalysisData,
    MealAnalysisRefinementResponse,
    USDASearchResultItem,
    USDANutrient,
    RefinedIngredient,
    RefinedDish,
    CalculatedNutrients
)

# サービス
from ....services.usda_service import USDAService, get_usda_service, USDASearchResultItem as USDAServiceItem
from ....services.gemini_service import GeminiMealAnalyzer
from ....services.nutrition_calculation_service import NutritionCalculationService
from ....core.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Geminiサービスインスタンスのキャッシュ
_gemini_analyzer = None

async def get_gemini_analyzer(settings: Annotated[Settings, Depends(get_settings)]) -> GeminiMealAnalyzer:
    """
    Geminiサービスインスタンスを取得（シングルトン）
    """
    global _gemini_analyzer
    if _gemini_analyzer is None:
        _gemini_analyzer = GeminiMealAnalyzer(
            project_id=settings.GEMINI_PROJECT_ID,
            location=settings.GEMINI_LOCATION,
            model_name=settings.GEMINI_MODEL_NAME
        )
    return _gemini_analyzer


@router.post(
    "/refine",
    response_model=MealAnalysisRefinementResponse,
    summary="Refine Meal Analysis with USDA Data and Dynamic Nutrition Calculation",
    description="Refine meal analysis results using USDA FoodData Central database and Gemini AI with dynamic calculation strategy (dish_level or ingredient_level) for accurate nutritional information."
)
async def refine_meal_analysis(
    settings: Annotated[Settings, Depends(get_settings)],
    image: Annotated[UploadFile, File(description="Meal image file.")],
    initial_analysis_data: Annotated[str, Form(description="JSON response string from Phase 1 API.")],
    usda_service: Annotated[USDAService, Depends(get_usda_service)],
    gemini_service: Annotated[GeminiMealAnalyzer, Depends(get_gemini_analyzer)]
):
    """
    Meal analysis refinement endpoint with dynamic nutrition calculation strategy
    
    処理フロー（仕様書準拠）:
    1. 画像とフェーズ1分析データを受信
    2. 各食材についてUSDAデータベースを検索
    3. GeminiにUSDA候補情報を提供してcalculation_strategyを決定
    4. calculation_strategyに基づいて栄養計算を実行
    5. 精緻化された結果を返す
    """
    warnings = []
    errors = []
    
    # 1. Image validation
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file format.")
    
    try:
        image_bytes = await image.read()
        # File size check (e.g., 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image file size too large (max 10MB).")
    except Exception as e:
        logger.error(f"Error reading image file: {e}")
        raise HTTPException(status_code=400, detail="Failed to read image file.")
    
    # 2. Parse initial_analysis_data
    try:
        initial_analysis_dict = json.loads(initial_analysis_data)
        initial_analysis = InitialAnalysisData(**initial_analysis_dict)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="initial_analysis_data is not valid JSON format.")
    except Exception as e:  # Pydantic validation error
        logger.error(f"Validation error for initial_analysis_data: {e}")
        raise HTTPException(status_code=422, detail=f"initial_analysis_data format error: {str(e)}")
    
    # 3. USDA candidate information collection
    usda_candidates_prompt_segments = []
    all_usda_search_results_map: Dict[int, USDAServiceItem] = {}
    
    # Data type priority
    preferred_data_types = ["Foundation", "SR Legacy", "FNDDS", "Branded"]
    
    # Search for both individual ingredients and potential dish-level items
    all_search_terms = set()
    
    # Add ingredient names
    for dish in initial_analysis.dishes:
        # Add dish name for potential dish-level calculation
        all_search_terms.add(dish.dish_name)
        
        for ingredient in dish.ingredients:
            all_search_terms.add(ingredient.ingredient_name)
    
    # Execute USDA searches
    for search_term in all_search_terms:
        logger.info(f"Searching USDA for: {search_term}")
        
        try:
            usda_results: List[USDAServiceItem] = await usda_service.search_foods(
                query=search_term,
                data_types=preferred_data_types,
                page_size=settings.USDA_SEARCH_CANDIDATES_LIMIT
            )
            
            if usda_results:
                segment = f"USDA candidates for '{search_term}':\n"
                for i, item in enumerate(usda_results):
                    all_usda_search_results_map[item.fdc_id] = item
                    
                    # Format nutrient information for prompt
                    nutrients_str_parts = []
                    for nutr in item.food_nutrients:
                        if nutr.name and nutr.amount is not None and nutr.unit_name:
                            nutrient_display_name = _get_nutrient_display_name(nutr.name, nutr.nutrient_number)
                            nutrients_str_parts.append(f"{nutrient_display_name}: {nutr.amount}{nutr.unit_name}")
                    
                    nutrients_str = ", ".join(nutrients_str_parts) if nutrients_str_parts else "No nutrient information"
                    
                    segment += (
                        f"{i+1}. FDC ID: {item.fdc_id}, Name: {item.description} ({item.data_type or 'N/A'}), "
                        f"Nutrients (per 100g): {nutrients_str}"
                    )
                    if item.brand_owner:
                        segment += f", Brand: {item.brand_owner}"
                    if item.ingredients_text:
                        segment += f", Ingredients: {item.ingredients_text[:100]}..."
                    segment += "\n"
                
                usda_candidates_prompt_segments.append(segment)
            else:
                logger.warning(f"No USDA results found for: {search_term}")
                usda_candidates_prompt_segments.append(f"No USDA candidates found for '{search_term}'.\n")
                
        except RuntimeError as e:
            error_msg = f"USDA search error for '{search_term}': {e}"
            logger.error(error_msg)
            errors.append(error_msg)
            usda_candidates_prompt_segments.append(f"Error searching USDA candidates for '{search_term}': {str(e)}\n")
        except Exception as e:
            error_msg = f"Unexpected error during USDA search for '{search_term}': {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    usda_candidates_prompt_text = "\n---\n".join(usda_candidates_prompt_segments) if usda_candidates_prompt_segments else "No USDA candidate information available."
    
    # 4. Call Gemini service (phase 2) for strategy determination and FDC ID matching
    try:
        logger.info("Calling Gemini for phase 2 analysis with dynamic strategy determination")
        refined_gemini_output_dict = await gemini_service.analyze_image_with_usda_context(
            image_bytes=image_bytes,
            image_mime_type=image.content_type,
            usda_candidates_text=usda_candidates_prompt_text,
            initial_ai_output_text=initial_analysis_data
        )
        
        logger.info(f"Gemini phase 2 completed. Processing {len(refined_gemini_output_dict.get('dishes', []))} dishes.")
        
    except RuntimeError as e:
        error_msg = f"Gemini service error: {e}"
        logger.error(error_msg)
        raise HTTPException(status_code=503, detail=f"External service integration error: {str(e)}")
    except Exception as e:
        error_msg = f"Unexpected error in Gemini phase 2: {e}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    # 5. Process Gemini output with dynamic calculation strategy (仕様書準拠)
    refined_dishes = []
    nutrition_service = NutritionCalculationService()
    
    for i, dish_response in enumerate(refined_gemini_output_dict.get('dishes', [])):
        try:
            strategy = dish_response.get('calculation_strategy')
            dish_name = dish_response.get('dish_name', f'Dish {i+1}')
            
            logger.info(f"Processing dish '{dish_name}' with strategy '{strategy}'")
            
            dish_total_actual_nutrients = None
            refined_ingredients = []
            
            # Get corresponding initial analysis dish for weight information
            initial_dish = None
            if i < len(initial_analysis.dishes):
                initial_dish = initial_analysis.dishes[i]
            
            if strategy == "dish_level":
                # Dish-level calculation
                dish_fdc_id = dish_response.get('fdc_id')
                
                if dish_fdc_id and initial_dish:
                    # Calculate dish total weight from initial analysis ingredients
                    dish_weight_g = sum(ing.weight_g for ing in initial_dish.ingredients)
                    
                    # Get nutrition data for the dish
                    key_nutrients_100g = await usda_service.get_food_details_for_nutrition(dish_fdc_id)
                    
                    if key_nutrients_100g and dish_weight_g > 0:
                        dish_total_actual_nutrients = nutrition_service.calculate_actual_nutrients(
                            key_nutrients_100g, dish_weight_g
                        )
                        logger.info(f"Dish-level calculation completed for '{dish_name}': {dish_total_actual_nutrients}")
                    else:
                        warning_msg = f"Could not calculate dish-level nutrition for '{dish_name}' (FDC ID: {dish_fdc_id})"
                        logger.warning(warning_msg)
                        warnings.append(warning_msg)
                
                # Process ingredients (descriptive purpose, no nutrition calculation)
                for ing_data in dish_response.get('ingredients', []):
                    # Find corresponding initial ingredient for weight
                    initial_weight = 0.0
                    if initial_dish:
                        for initial_ing in initial_dish.ingredients:
                            if initial_ing.ingredient_name.lower() in ing_data.get('ingredient_name', '').lower() or \
                               ing_data.get('ingredient_name', '').lower() in initial_ing.ingredient_name.lower():
                                initial_weight = initial_ing.weight_g
                                break
                    
                    refined_ingredient = RefinedIngredient(
                        ingredient_name=ing_data.get('ingredient_name', ''),
                        weight_g=initial_weight,
                        fdc_id=None,  # Not used in dish_level strategy
                        usda_source_description=None,
                        key_nutrients_per_100g=None,
                        actual_nutrients=None  # Not calculated in dish_level
                    )
                    refined_ingredients.append(refined_ingredient)
            
            elif strategy == "ingredient_level":
                # Ingredient-level calculation
                ingredient_actual_nutrients_list = []
                
                for ing_data in dish_response.get('ingredients', []):
                    ing_fdc_id = ing_data.get('fdc_id')
                    ing_name = ing_data.get('ingredient_name', '')
                    
                    # Find corresponding initial ingredient for weight
                    initial_weight = 0.0
                    if initial_dish:
                        for initial_ing in initial_dish.ingredients:
                            if initial_ing.ingredient_name.lower() in ing_name.lower() or \
                               ing_name.lower() in initial_ing.ingredient_name.lower():
                                initial_weight = initial_ing.weight_g
                                break
                    
                    actual_ing_nutrients = None
                    key_nutrients_100g = None
                    
                    if ing_fdc_id and initial_weight > 0:
                        # Get nutrition data for the ingredient
                        key_nutrients_100g = await usda_service.get_food_details_for_nutrition(ing_fdc_id)
                        
                        if key_nutrients_100g:
                            actual_ing_nutrients = nutrition_service.calculate_actual_nutrients(
                                key_nutrients_100g, initial_weight
                            )
                            ingredient_actual_nutrients_list.append(actual_ing_nutrients)
                            logger.debug(f"Ingredient-level calculation for '{ing_name}': {actual_ing_nutrients}")
                        else:
                            warning_msg = f"Could not get nutrition data for ingredient '{ing_name}' (FDC ID: {ing_fdc_id})"
                            logger.warning(warning_msg)
                            warnings.append(warning_msg)
                    else:
                        warning_msg = f"Missing FDC ID or weight for ingredient '{ing_name}'"
                        logger.warning(warning_msg)
                        warnings.append(warning_msg)
                    
                    refined_ingredient = RefinedIngredient(
                        ingredient_name=ing_name,
                        weight_g=initial_weight,
                        fdc_id=ing_fdc_id,
                        usda_source_description=ing_data.get('usda_source_description'),
                        key_nutrients_per_100g=key_nutrients_100g,
                        actual_nutrients=actual_ing_nutrients
                    )
                    refined_ingredients.append(refined_ingredient)
                
                # Aggregate nutrients from ingredients
                if ingredient_actual_nutrients_list:
                    dish_total_actual_nutrients = nutrition_service.aggregate_nutrients_for_dish_from_ingredients(
                        refined_ingredients
                    )
                    logger.info(f"Ingredient-level aggregation completed for '{dish_name}': {dish_total_actual_nutrients}")
            
            else:
                error_msg = f"Unknown calculation_strategy '{strategy}' for dish '{dish_name}'"
                logger.error(error_msg)
                errors.append(error_msg)
            
            # Create refined dish
            refined_dish = RefinedDish(
                dish_name=dish_name,
                type=dish_response.get('type', 'Unknown'),
                quantity_on_plate=dish_response.get('quantity_on_plate', ''),
                calculation_strategy=strategy,
                fdc_id=dish_response.get('fdc_id') if strategy == "dish_level" else None,
                usda_source_description=dish_response.get('usda_source_description') if strategy == "dish_level" else None,
                key_nutrients_per_100g=key_nutrients_100g if strategy == "dish_level" and 'key_nutrients_100g' in locals() else None,
                ingredients=refined_ingredients,
                dish_total_actual_nutrients=dish_total_actual_nutrients
            )
            
            refined_dishes.append(refined_dish)
            
        except Exception as e:
            error_msg = f"Error processing dish {i+1}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # 6. Calculate total meal nutrients
    total_meal_nutrients = None
    if refined_dishes:
        total_meal_nutrients = nutrition_service.aggregate_nutrients_for_meal(refined_dishes)
        logger.info(f"Total meal nutrients calculated: {total_meal_nutrients}")
    
    # 7. Create final response
    response = MealAnalysisRefinementResponse(
        dishes=refined_dishes,
        total_meal_nutrients=total_meal_nutrients,
        warnings=warnings if warnings else None,
        errors=errors if errors else None
    )
    
    logger.info(f"Phase 2 analysis completed successfully. Processed {len(refined_dishes)} dishes with {len(warnings)} warnings and {len(errors)} errors.")
    return response


def _get_nutrient_display_name(name: str, nutrient_number: Optional[str]) -> str:
    """
    Display nutrient names in a standardized format
    """
    nutrient_mapping = {
        "208": "Energy",
        "203": "Protein", 
        "204": "Fat",
        "205": "Carbohydrate",
        "291": "Dietary Fiber",
        "269": "Sugars",
        "307": "Sodium"
    }
    
    if nutrient_number and nutrient_number in nutrient_mapping:
        return nutrient_mapping[nutrient_number]
    return name 