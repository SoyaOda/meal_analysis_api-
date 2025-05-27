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
    RefinedDish
)

# サービス
from ....services.usda_service import USDAService, get_usda_service, USDASearchResultItem as USDAServiceItem
from ....services.gemini_service import GeminiMealAnalyzer
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
    summary="Refine Meal Analysis with USDA Data",
    description="Refine meal analysis results using USDA FoodData Central database and Gemini AI for more accurate nutritional information."
)
async def refine_meal_analysis(
    settings: Annotated[Settings, Depends(get_settings)],
    image: Annotated[UploadFile, File(description="Meal image file.")],
    initial_analysis_data: Annotated[str, Form(description="JSON response string from Phase 1 API.")],
    usda_service: Annotated[USDAService, Depends(get_usda_service)],
    gemini_service: Annotated[GeminiMealAnalyzer, Depends(get_gemini_analyzer)]
):
    """
    Meal analysis refinement endpoint
    
    1. Receive image and Phase 1 analysis results
    2. Search USDA database for each ingredient
    3. Re-analyze with Gemini using USDA candidates
    4. Return refined results
    """
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
    
    # 3. USDA candidate information collection and prompt text generation
    usda_candidates_prompt_segments = []
    # Dictionary to store USDA search results for later key_nutrients_per_100g assignment (key_nutrients_per_100g will be added later)
    all_usda_search_results_map: Dict[int, USDAServiceItem] = {}
    
    # Data type priority
    preferred_data_types = ["Foundation", "SR Legacy", "Branded"]
    
    for dish in initial_analysis.dishes:
        for ingredient in dish.ingredients:
            search_query = ingredient.ingredient_name
            logger.info(f"Searching USDA for ingredient: {search_query}")
            
            try:
                # Execute USDA search
                usda_results: List[USDAServiceItem] = await usda_service.search_foods(
                    query=search_query,
                    data_types=preferred_data_types,
                    page_size=settings.USDA_SEARCH_CANDIDATES_LIMIT
                )
                
                if usda_results:
                    segment = f"USDA candidates for ingredient '{ingredient.ingredient_name}':\n"
                    for i, item in enumerate(usda_results):
                        all_usda_search_results_map[item.fdc_id] = item  # Save for later reference
                        
                        # Format nutrient information for prompt
                        nutrients_str_parts = []
                        for nutr in item.food_nutrients:
                            if nutr.name and nutr.amount is not None and nutr.unit_name:
                                # Convert nutrient name to a more readable format
                                nutrient_display_name = _get_nutrient_display_name(nutr.name, nutr.nutrient_number)
                                nutrients_str_parts.append(f"{nutrient_display_name}: {nutr.amount}{nutr.unit_name}")
                        
                        nutrients_str = ", ".join(nutrients_str_parts) if nutrients_str_parts else "No nutrient information"
                        
                        segment += (
                            f"{i+1}. FDC ID: {item.fdc_id}, Name: {item.description} ({item.data_type or 'N/A'}), "
                            f"Nutrients (per 100g): {nutrients_str}"
                        )
                        if item.brand_owner:
                            segment += f", Brand: {item.brand_owner}"
                        if item.ingredients_text:  # Branded Foods ingredient information
                            segment += f", Ingredients: {item.ingredients_text[:100]}..."  # If too long, omit
                        segment += "\n"
                    
                    usda_candidates_prompt_segments.append(segment)
                else:
                    logger.warning(f"No USDA results found for ingredient: {search_query}")
                    usda_candidates_prompt_segments.append(f"No USDA candidates found for ingredient '{ingredient.ingredient_name}'.\n")
                    
            except RuntimeError as e:  # USDA service error
                logger.error(f"USDA search error for ingredient '{search_query}': {e}")
                # Even if some USDA searches fail, let Gemini decide
                usda_candidates_prompt_segments.append(f"Error searching USDA candidates for ingredient '{ingredient.ingredient_name}': {str(e)}\n")
            except Exception as e:
                logger.error(f"Unexpected error during USDA search for '{search_query}': {e}")
                usda_candidates_prompt_segments.append(f"Unexpected error searching USDA candidates for ingredient '{ingredient.ingredient_name}': {str(e)}\n")
    
    usda_candidates_prompt_text = "\n---\n".join(usda_candidates_prompt_segments) if usda_candidates_prompt_segments else "No USDA candidate information available."
    
    # 4. Call Gemini service (phase 2 method)
    try:
        logger.info("Calling Gemini for phase 2 analysis")
        refined_gemini_output_dict = await gemini_service.analyze_image_with_usda_context(
            image_bytes=image_bytes,
            image_mime_type=image.content_type,
            usda_candidates_text=usda_candidates_prompt_text,
            initial_ai_output_text=initial_analysis_data  # Pass Phase 1 output as is
        )
        
        # 5. Parse Gemini output and optionally add key_nutrients_per_100g
        # Parse with Pydantic model to verify it's in the correct schema format
        refined_analysis_response = MealAnalysisRefinementResponse(**refined_gemini_output_dict)
        
        # Add key_nutrients_per_100g in backend
        for dish_resp in refined_analysis_response.dishes:
            for ing_resp in dish_resp.ingredients:
                if ing_resp.fdc_id and ing_resp.fdc_id in all_usda_search_results_map:
                    usda_item = all_usda_search_results_map[ing_resp.fdc_id]
                    key_nutrients = {}
                    
                    # Extract necessary items from USDASearchResultItemPydantic.food_nutrients
                    for nutr in usda_item.food_nutrients:
                        if nutr.name and nutr.amount is not None:
                            # Determine key name based on nutrient number
                            if nutr.nutrient_number == "208":  # Energy
                                key_nutrients["calories_kcal"] = nutr.amount
                            elif nutr.nutrient_number == "203":  # Protein
                                key_nutrients["protein_g"] = nutr.amount
                            elif nutr.nutrient_number == "204":  # Total lipid (fat)
                                key_nutrients["fat_g"] = nutr.amount
                            elif nutr.nutrient_number == "205":  # Carbohydrate
                                key_nutrients["carbohydrate_g"] = nutr.amount
                            elif nutr.nutrient_number == "291":  # Fiber
                                key_nutrients["fiber_g"] = nutr.amount
                            elif nutr.nutrient_number == "269":  # Total sugars
                                key_nutrients["sugars_g"] = nutr.amount
                            elif nutr.nutrient_number == "307":  # Sodium
                                key_nutrients["sodium_mg"] = nutr.amount
                    
                    ing_resp.key_nutrients_per_100g = key_nutrients if key_nutrients else None
        
        logger.info(f"Phase 2 analysis completed successfully. Refined {len(refined_analysis_response.dishes)} dishes.")
        return refined_analysis_response
        
    except RuntimeError as e:  # Gemini service or USDA service error
        logger.error(f"External service error: {e}")
        raise HTTPException(status_code=503, detail=f"External service integration error: {str(e)}")
    except ValueError as e:  # JSON parsing error
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    except Exception as e:  # Unexpected other error
        logger.error(f"Unexpected error in refine_meal_analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected internal error occurred: {str(e)}")


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