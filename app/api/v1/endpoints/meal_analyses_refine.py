from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from typing import Annotated, List, Optional, Dict
import json
import logging
import asyncio  # 非同期処理のため
import time  # 実行時間測定のため

# 新しいPydanticモデル
from ..schemas.meal import (
    Phase1AnalysisResponse,  # Phase 1 出力をパースするために使用
    Phase2GeminiResponse,    # Phase 2 Gemini出力をパースするために使用
    MealAnalysisRefinementResponse,
    USDASearchResultItem,
    RefinedDishResponse,
    RefinedIngredientResponse,
    CalculatedNutrients
)

# サービス
from ....services.usda_service import USDAService, get_usda_service
from ....services.gemini_service import GeminiMealAnalyzer
from ....services.nutrition_calculation_service import NutritionCalculationService, get_nutrition_calculation_service, WeightCalculationResult
from ....services.logging_service import get_meal_analysis_logger, ProcessingPhase, LogLevel
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
    summary="Refine Meal Analysis with USDA Data & Enhanced Gemini Strategy (v2.1)",
    description="v2.1: Phase 1からUSDAクエリ候補を受信し、全候補で検索を実行。Phase 2 Geminiがcalculation_strategyを決定し、FDC IDを選択。決定論的で精度の高い栄養計算を提供。"
)
async def refine_meal_analysis(
    settings: Annotated[Settings, Depends(get_settings)],
    image: Annotated[UploadFile, File(description="Meal image file.")],
    # NEW: Phase 1 出力は JSON 文字列として受け取る
    phase1_analysis_json: Annotated[str, Form(description="JSON response string from Phase 1 API.")],
    usda_service: Annotated[USDAService, Depends(get_usda_service)],
    gemini_service: Annotated[GeminiMealAnalyzer, Depends(get_gemini_analyzer)]
):
    """
    v2.1仕様：食事分析精緻化エンドポイント
    
    処理フロー:
    1. Phase 1分析結果とUSDAクエリ候補を受信
    2. 全USDAクエリ候補で並列検索を実行
    3. Phase 2 Geminiで calculation_strategy 決定とFDC ID選択
    4. calculation_strategyに基づく栄養計算
    5. 精緻化された結果を返す
    """
    # ログサービス初期化
    meal_logger = get_meal_analysis_logger()
    session_id = meal_logger.start_session(
        endpoint="/api/v1/meal-analyses/refine",
        image_filename=getattr(image, 'filename', None),
        image_size_bytes=None  # 後で設定
    )
    
    start_time = time.time()
    warnings = []
    errors = []

    try:
        # 1. Image validation (既存ロジック)
        meal_logger.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.REQUEST_RECEIVED,
            message="Validating image file"
        )
        
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid image file format.")
        
        try:
            image_bytes = await image.read()
            # Update image size in session
            if session_id in meal_logger.active_sessions:
                meal_logger.active_sessions[session_id].image_size_bytes = len(image_bytes)
            
            # File size check (e.g., 10MB)
            if len(image_bytes) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Image file size too large (max 10MB).")
        except Exception as e:
            logger.error(f"Error reading image file: {e}")
            meal_logger.log_error(
                session_id=session_id,
                phase=ProcessingPhase.REQUEST_RECEIVED,
                error_message="Failed to read image file",
                error_details=str(e)
            )
            raise HTTPException(status_code=400, detail="Failed to read image file.")

        # 2. Parse Phase 1 analysis_data
        try:
            phase1_dict = json.loads(phase1_analysis_json)
            phase1_analysis = Phase1AnalysisResponse(**phase1_dict)
            
            # ログにPhase 1情報を記録
            dishes_count = len(phase1_analysis.dishes)
            usda_queries_count = sum(len(dish.usda_query_candidates) for dish in phase1_analysis.dishes)
            
            meal_logger.log_entry(
                session_id=session_id,
                level=LogLevel.INFO,
                phase=ProcessingPhase.PHASE1_COMPLETE,
                message=f"Phase 1 data received: {dishes_count} dishes, {usda_queries_count} USDA queries",
                data={
                    "dishes_count": dishes_count,
                    "usda_queries_count": usda_queries_count,
                    "phase1_output": phase1_dict
                }
            )
            
        except Exception as e:
            meal_logger.log_error(
                session_id=session_id,
                phase=ProcessingPhase.PHASE1_COMPLETE,
                error_message="Failed to parse Phase 1 JSON",
                error_details=str(e)
            )
            raise HTTPException(status_code=400, detail=f"Invalid Phase 1 JSON: {e}")

        # 3. Enhanced USDA Search with Tiered Strategy
        usda_search_start_time = time.time()
        
        # query_map は Phase 1 の query_term と original_term (表示用) のマッピングに引き続き使用
        query_map = {}
        for dish in phase1_analysis.dishes:
            for candidate in dish.usda_query_candidates:
                query_map[candidate.query_term] = candidate.original_term or dish.dish_name

        # Enhanced USDA search with tiered approach
        all_usda_search_results_map: Dict[int, USDASearchResultItem] = {}
        search_details_for_log = []
        
        # Detect brand context from image or Phase 1 analysis
        brand_context = None
        brand_indicators = ["la madeleine", "madeleine"]
        for dish in phase1_analysis.dishes:
            for candidate in dish.usda_query_candidates:
                query_lower = candidate.query_term.lower()
                for brand in brand_indicators:
                    if brand in query_lower:
                        brand_context = "La Madeleine"
                        break
                if brand_context:
                    break

        logger.info(f"Starting enhanced tiered USDA search for {len(phase1_analysis.dishes)} dishes, brand_context: {brand_context}")

        # Execute tiered search for each unique query candidate
        processed_query_terms = set()
        
        for dish in phase1_analysis.dishes:
            for candidate in dish.usda_query_candidates:
                if candidate.query_term in processed_query_terms:
                    continue
                
                processed_query_terms.add(candidate.query_term)
                
                # NEW: Find corresponding Phase1Ingredient details for enhanced tiered search
                corresponding_ingredient = None
                if candidate.granularity_level == "ingredient":
                    # Find the ingredient from this dish that matches the original_term
                    for ingredient in dish.ingredients:
                        if (ingredient.ingredient_name.lower() in candidate.original_term.lower() or 
                            candidate.original_term.lower() in ingredient.ingredient_name.lower()):
                            corresponding_ingredient = ingredient
                            break
                
                try:
                    # Use enhanced tiered search strategy with ingredient details
                    tiered_results = await usda_service.execute_tiered_usda_search(
                        phase1_candidate=candidate,
                        phase1_ingredient_details=corresponding_ingredient,  # NEW: Pass ingredient details
                        brand_context=brand_context,
                        max_results_cap=15
                    )
                    
                    # Add results to global map for deduplication
                    for result in tiered_results:
                        if result.fdc_id not in all_usda_search_results_map:
                            all_usda_search_results_map[result.fdc_id] = result
                    
                    # Enhanced logging with ingredient state info
                    ingredient_info = ""
                    if corresponding_ingredient:
                        ingredient_info = f" (ingredient: {corresponding_ingredient.ingredient_name}, state: {corresponding_ingredient.state}, prep: {corresponding_ingredient.preparation_method})"
                    
                    search_details_for_log.append({
                        "phase1_query_term": candidate.query_term,
                        "original_term": query_map.get(candidate.query_term, candidate.original_term),
                        "granularity": candidate.granularity_level,
                        "search_strategy": "enhanced_tiered_search",
                        "ingredient_state": corresponding_ingredient.state if corresponding_ingredient else None,
                        "ingredient_prep_method": corresponding_ingredient.preparation_method if corresponding_ingredient else None,
                        "results_count": len(tiered_results),
                        "status": "success" if tiered_results else "no_results"
                    })
                    
                    logger.info(f"Enhanced tiered search for '{candidate.query_term}'{ingredient_info}: {len(tiered_results)} results")
                    
                except Exception as e:
                    logger.error(f"Enhanced tiered search failed for '{candidate.query_term}': {str(e)}")
                    search_details_for_log.append({
                        "phase1_query_term": candidate.query_term,
                        "original_term": query_map.get(candidate.query_term, candidate.original_term),
                        "granularity": candidate.granularity_level,
                        "search_strategy": "enhanced_tiered_search",
                        "ingredient_state": corresponding_ingredient.state if corresponding_ingredient else None,
                        "ingredient_prep_method": corresponding_ingredient.preparation_method if corresponding_ingredient else None,
                        "results_count": 0,
                        "status": "error",
                        "error_message": str(e)
                    })

        usda_search_duration = (time.time() - usda_search_start_time) * 1000
        logger.info(f"Enhanced tiered USDA searches completed in {usda_search_duration:.2f} ms. Total unique results: {len(all_usda_search_results_map)}")

        # Log comprehensive search summary
        meal_logger.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.USDA_SEARCH_COMPLETE,
            message=f"Tiered USDA search completed: {len(search_details_for_log)} queries processed, {len(all_usda_search_results_map)} unique FDC IDs found",
            data={
                "total_queries": len(search_details_for_log),
                "unique_fdc_ids": len(all_usda_search_results_map),
                "brand_context": brand_context,
                "search_duration_ms": usda_search_duration,
                "search_details": search_details_for_log
            }
        )

        # 4. Format USDA results for Gemini prompt using enhanced results
        usda_candidates_prompt_segments = []
        
        # Create a mapping from query_term to results for Gemini prompt generation
        query_to_results_map = {}
        for dish in phase1_analysis.dishes:
            for candidate in dish.usda_query_candidates:
                query_to_results_map[candidate.query_term] = []
        
        # Populate the mapping with relevant results based on query similarity
        for fdc_id, result in all_usda_search_results_map.items():
            # Check which query this result best matches
            best_match_query = None
            best_match_score = 0
            
            for query_term in query_to_results_map.keys():
                # Simple keyword-based matching
                query_keywords = set(query_term.lower().replace(',', ' ').split())
                result_keywords = set(result.description.lower().replace(',', ' ').split())
                match_score = len(query_keywords.intersection(result_keywords))
                
                if match_score > best_match_score:
                    best_match_score = match_score
                    best_match_query = query_term
            
            # Add result to the best matching query (or first query if no good match)
            if best_match_query and best_match_score > 0:
                query_to_results_map[best_match_query].append(result)
            else:
                # Fallback: add to first query if no good match found
                first_query = next(iter(query_to_results_map.keys()), None)
                if first_query:
                    query_to_results_map[first_query].append(result)
        
        for dish in phase1_analysis.dishes:
            for candidate in dish.usda_query_candidates:
                phase1_query_term = candidate.query_term
                
                # Retrieve the results for this phase1_query_term
                results_for_this_query = query_to_results_map.get(phase1_query_term, [])
                
                prompt_segment_header = (
                    f"USDA candidates for Phase 1 query: '{phase1_query_term}' "
                    f"(Original term: '{query_map.get(phase1_query_term, candidate.original_term)}', "
                    f"Granularity: {candidate.granularity_level}, "
                    f"Reason from Phase 1: '{candidate.reason_for_query}'):\n"
                )
                
                segment_content = ""
                if not results_for_this_query:
                    segment_content = f"  No USDA candidates found for this query.\n"
                else:
                    for j, item in enumerate(results_for_this_query):                        
                        brand_part = f", Brand: {item.brand_owner}" if item.brand_owner else ""
                        score_part = f"{item.score:.2f}" if item.score is not None else "N/A"
                        tier_info = f" (Tier {getattr(item, 'search_tier', 'N/A')})" if hasattr(item, 'search_tier') else ""
                        
                        segment_content += (
                            f"  {j+1}. FDC ID: {item.fdc_id}, Name: {item.description} "
                            f"(Type: {item.data_type or 'N/A'}{brand_part}), "
                            f"Score: {score_part}{tier_info}\n"
                        )
                        if getattr(item, 'ingredients', None):
                            ingredients_preview = str(item.ingredients)[:100] if item.ingredients else ""
                            if ingredients_preview:
                                segment_content += f"     Ingredients (partial): {ingredients_preview}...\n"
                
                usda_candidates_prompt_segments.append(prompt_segment_header + segment_content)

        usda_candidates_prompt_text = "\n---\n".join(usda_candidates_prompt_segments)
        
        # 6. Call Gemini service (Phase 2) for strategy and FDC ID selection
        meal_logger.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.PHASE2_START,
            message="Starting Phase 2 Gemini for strategy determination and FDC ID selection"
        )
        
        phase2_start_time = time.time()
        try:
            logger.info("Calling Gemini Phase 2 for strategy determination and FDC ID selection")
            # NEW: refine_analysis_phase2 を使用
            gemini_output_dict = await gemini_service.refine_analysis_phase2(
                image_bytes=image_bytes,
                image_mime_type=image.content_type,
                phase1_output_text=phase1_analysis_json,
                usda_results_text=usda_candidates_prompt_text
            )
            gemini_phase2_response = Phase2GeminiResponse(**gemini_output_dict)
            phase2_duration = (time.time() - phase2_start_time) * 1000
            
            # Phase 2結果を解析してログに記録
            strategy_decisions = {}
            fdc_selections = {}
            for dish in gemini_phase2_response.dishes:
                strategy_decisions[dish.dish_name] = {
                    "strategy": dish.calculation_strategy,
                    "reason": dish.reason_for_strategy
                }
                fdc_selections[dish.dish_name] = {
                    "dish_fdc_id": dish.fdc_id,
                    "dish_reason": dish.reason_for_choice,
                    "ingredients": [{
                        "name": ing.ingredient_name,
                        "fdc_id": ing.fdc_id,
                        "reason": ing.reason_for_choice
                    } for ing in dish.ingredients]
                }
            
            meal_logger.update_phase2_results(
                session_id=session_id,
                duration_ms=phase2_duration,
                strategy_decisions=strategy_decisions,
                fdc_selections=fdc_selections,
                phase2_output=gemini_output_dict
            )

        except Exception as e:
            meal_logger.log_error(
                session_id=session_id,
                phase=ProcessingPhase.PHASE2_START,
                error_message="Gemini Phase 2 failed",
                error_details=str(e)
            )
            raise HTTPException(status_code=503, detail=f"Gemini Phase 2 error: {e}")

        # Check for skipped dishes - CRITICAL ERROR HANDLING
        phase1_dish_names = {dish.dish_name for dish in phase1_analysis.dishes}
        phase2_dish_names = {dish.dish_name for dish in gemini_phase2_response.dishes}
        skipped_dishes = phase1_dish_names - phase2_dish_names
        
        if skipped_dishes:
            error_message = f"Critical Error: Phase 2 skipped dishes that must be processed: {list(skipped_dishes)}"
            meal_logger.log_error(
                session_id=session_id,
                phase=ProcessingPhase.PHASE2_START,
                error_message=error_message,
                error_details=f"Phase 1 identified {len(phase1_dish_names)} dishes, but Phase 2 only processed {len(phase2_dish_names)} dishes. Skipped: {skipped_dishes}"
            )
            raise HTTPException(
                status_code=422, 
                detail={
                    "error": "DISH_PROCESSING_INCOMPLETE",
                    "message": error_message,
                    "skipped_dishes": list(skipped_dishes),
                    "phase1_dishes": list(phase1_dish_names),
                    "phase2_dishes": list(phase2_dish_names),
                    "recommendation": "Image may contain dishes that cannot be analyzed with current USDA database. Please try with a different image or contact support."
                }
            )

        # Check for dishes with missing FDC IDs - ZERO TOLERANCE FOR UNPROCESSABLE DISHES
        unprocessable_dishes = []
        for dish in gemini_phase2_response.dishes:
            if dish.calculation_strategy == "dish_level":
                if not dish.fdc_id:
                    unprocessable_dishes.append({
                        "dish_name": dish.dish_name,
                        "strategy": dish.calculation_strategy,
                        "issue": "No FDC ID selected for dish-level calculation",
                        "reason": dish.reason_for_choice or "No reason provided"
                    })
            elif dish.calculation_strategy == "ingredient_level":
                # Check if all critical ingredients have FDC IDs
                ingredients_without_fdc = [
                    ing.ingredient_name for ing in dish.ingredients 
                    if not ing.fdc_id and ing.ingredient_name.lower() not in ["garnish", "seasoning", "salt", "pepper"]
                ]
                if len(ingredients_without_fdc) > len(dish.ingredients) * 0.5:  # More than 50% missing
                    unprocessable_dishes.append({
                        "dish_name": dish.dish_name,
                        "strategy": dish.calculation_strategy,
                        "issue": f"Too many ingredients without FDC IDs: {ingredients_without_fdc}",
                        "reason": "Insufficient USDA database coverage for ingredient-level calculation"
                    })

        if unprocessable_dishes:
            error_message = f"Critical Error: {len(unprocessable_dishes)} dishes cannot be processed due to missing USDA data"
            meal_logger.log_error(
                session_id=session_id,
                phase=ProcessingPhase.PHASE2_START,
                error_message=error_message,
                error_details=f"Unprocessable dishes: {unprocessable_dishes}"
            )
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "INSUFFICIENT_USDA_DATA",
                    "message": error_message,
                    "unprocessable_dishes": unprocessable_dishes,
                    "recommendation": "The meal contains dishes that cannot be accurately analyzed with the current USDA FoodData Central database. Please try with a simpler meal or contact support for assistance."
                }
            )

        # 7. Process Gemini output and perform Nutrition Calculation
        meal_logger.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.NUTRITION_CALC_START,
            message="Starting nutrition calculation based on Phase 2 strategy"
        )
        
        nutrition_calc_start_time = time.time()
        refined_dishes_response: List[RefinedDishResponse] = []
        nutrition_service = get_nutrition_calculation_service()  # 栄養計算サービス

        for gemini_dish in gemini_phase2_response.dishes:
            # Phase 1 Dish を名前で探す (厳密にはIDなどで引くべきだが、今回は名前で)
            p1_dish = next((d for d in phase1_analysis.dishes if d.dish_name == gemini_dish.dish_name), None)
            if not p1_dish:
                warnings.append(f"Could not match Phase 2 dish '{gemini_dish.dish_name}' to Phase 1.")
                continue

            # Phase1推奨戦略と実際の戦略の比較は廃止（Phase1がstrategy推奨をしなくなったため）
            # phase1_recommendation = p1_dish.calculation_strategy_recommendation  # 削除
            final_strategy = gemini_dish.calculation_strategy
            # strategy_changed = gemini_dish.strategy_changed_from_phase1 if hasattr(gemini_dish, 'strategy_changed_from_phase1') else (phase1_recommendation != final_strategy)  # 削除
            strategy_changed = False  # Phase1は戦略推奨をしないため、常にPhase2で決定

            dish_total_nutrients = None
            refined_ingredients_list: List[RefinedIngredientResponse] = []
            dish_key_nutrients_100g = None
            weight_calculation_method = f"Phase2 image-based weight estimation (Strategy: {final_strategy}, Phase2 decision)"
            
            # Phase2での重量推定：Geminiからの重量推定を優先、フォールバックで既存システム
            if gemini_dish.calculation_strategy == "dish_level" and gemini_dish.estimated_dish_weight_g:
                # Phase2 Gemini画像ベース重量推定を使用
                actual_weight_used_g = gemini_dish.estimated_dish_weight_g
                weight_calculation_method = f"Phase2 Gemini visual estimation: {actual_weight_used_g}g (Strategy: {final_strategy}, Phase2 decision)"
            elif gemini_dish.calculation_strategy == "ingredient_level":
                # ingredient_levelの場合、個別材料重量をチェック
                gemini_ingredient_weights = {
                    ing.ingredient_name: ing.estimated_weight_g 
                    for ing in gemini_dish.ingredients 
                    if hasattr(ing, 'estimated_weight_g') and ing.estimated_weight_g
                }
                
                if gemini_ingredient_weights:
                    actual_weight_used_g = sum(gemini_ingredient_weights.values())
                    weight_calculation_method = f"Phase2 Gemini ingredient weights: {actual_weight_used_g}g total (Strategy: {final_strategy}, Phase2 decision)"
                else:
                    # フォールバック：既存の推定システム
                    actual_weight_used_g = 200.0  # デフォルト重量
                    weight_calculation_method = f"Fallback default weight: {actual_weight_used_g}g (Strategy: {final_strategy}, Phase2 decision)"
            else:
                # フォールバック：既存の推定システム
                actual_weight_used_g = 200.0  # デフォルト重量
                weight_calculation_method = f"Fallback default weight: {actual_weight_used_g}g (Strategy: {final_strategy}, Phase2 decision)"

            if gemini_dish.calculation_strategy == "dish_level":
                dish_fdc_id = gemini_dish.fdc_id
                
                if dish_fdc_id:
                    dish_key_nutrients_100g = await usda_service.get_food_details_for_nutrition(dish_fdc_id)
                    if dish_key_nutrients_100g and actual_weight_used_g > 0:
                        dish_total_nutrients = nutrition_service.calculate_actual_nutrients(dish_key_nutrients_100g, actual_weight_used_g)
                        
                        meal_logger.log_entry(
                            session_id=session_id,
                            level=LogLevel.INFO,
                            phase=ProcessingPhase.NUTRITION_CALC_START,
                            message=f"Dish-level nutrition calculated for '{gemini_dish.dish_name}': {actual_weight_used_g}g using FDC {dish_fdc_id}",
                            data={"dish_weight_g": actual_weight_used_g, "fdc_id": dish_fdc_id, "calculation_method": weight_calculation_method}
                        )
                    else:
                        warnings.append(f"Could not calculate dish-level nutrition for '{gemini_dish.dish_name}'. Switching to ingredient-level.")
                        gemini_dish.calculation_strategy = "ingredient_level"
                        weight_calculation_method = "Fallback to ingredient-level due to nutrition calculation failure"

                # Material information for dish_level (fallback FDC IDs for reference)
                if gemini_dish.calculation_strategy == "dish_level":
                    # Phase2での個別材料重量推定：Geminiの重量がある場合はそれを優先
                    ingredient_weights = {}
                    for gemini_ing in gemini_dish.ingredients:
                        if hasattr(gemini_ing, 'estimated_weight_g') and gemini_ing.estimated_weight_g:
                            # Geminiからの重量推定を使用
                            ingredient_weights[gemini_ing.ingredient_name] = gemini_ing.estimated_weight_g
                    
                    # Geminiからの重量がない材料については推定システムを使用
                    if len(ingredient_weights) < len(gemini_dish.ingredients):
                        fallback_weights = nutrition_service.estimate_ingredient_weights_from_dish(
                            total_dish_weight_g=actual_weight_used_g,
                            ingredients=p1_dish.ingredients
                        )
                        for gemini_ing in gemini_dish.ingredients:
                            if gemini_ing.ingredient_name not in ingredient_weights:
                                ingredient_weights[gemini_ing.ingredient_name] = fallback_weights.get(gemini_ing.ingredient_name, 0.0)
                    
                    for gemini_ing in gemini_dish.ingredients:
                        # Phase2で推定された重量を使用（Gemini優先、フォールバックで推定システム）
                        estimated_weight = ingredient_weights.get(gemini_ing.ingredient_name, 0.0)
                        ing_nutrients_100g = await usda_service.get_food_details_for_nutrition(gemini_ing.fdc_id) if gemini_ing.fdc_id else None
                        refined_ingredients_list.append(RefinedIngredientResponse(
                            ingredient_name=gemini_ing.ingredient_name,
                            weight_g=estimated_weight,
                            fdc_id=gemini_ing.fdc_id,  # Fallback ID
                            usda_source_description=gemini_ing.usda_source_description,
                            reason_for_choice=gemini_ing.reason_for_choice,
                            key_nutrients_per_100g=ing_nutrients_100g,
                            actual_nutrients=None  # Not calculated here
                        ))

            # Handle ingredient_level (including fallback cases)
            if gemini_dish.calculation_strategy == "ingredient_level":
                ingredient_nutrients_list = []
                for gemini_ing in gemini_dish.ingredients:
                    # Phase2で推定された重量を使用：Gemini優先、フォールバックで推定システム
                    if hasattr(gemini_ing, 'estimated_weight_g') and gemini_ing.estimated_weight_g:
                        # Geminiからの重量推定を使用
                        estimated_weight = gemini_ing.estimated_weight_g
                    else:
                        # フォールバック：推定システムを使用
                        ingredient_weights = nutrition_service.estimate_ingredient_weights_from_dish(
                            total_dish_weight_g=actual_weight_used_g,
                            ingredients=p1_dish.ingredients
                        )
                        estimated_weight = ingredient_weights.get(gemini_ing.ingredient_name, 0.0)
                    
                    ing_fdc_id = gemini_ing.fdc_id
                    ing_nutrients_100g = None
                    ing_actual_nutrients = None

                    # Enhanced ingredient-level fallback processing
                    if not ing_fdc_id and estimated_weight > 0:
                        # Try fallback searches for missing ingredients
                        fallback_attempted = False
                        
                        # Look for alternative query candidates from Phase 1 for this ingredient
                        for p1_dish_check in phase1_analysis.dishes:
                            if p1_dish_check.dish_name == gemini_dish.dish_name:
                                for candidate_query in p1_dish_check.usda_query_candidates:
                                    # Check if this query might be a broader alternative for the current ingredient
                                    if (candidate_query.granularity_level == "ingredient" and 
                                        gemini_ing.ingredient_name.lower() in candidate_query.query_term.lower()):
                                        
                                        # Try searching with the broader query term
                                        try:
                                            fallback_results = await usda_service.search_foods_rich(
                                                query=candidate_query.query_term,
                                                page_size=5,
                                                data_types=["Foundation", "SR Legacy", "Branded"],
                                                require_all_words=False  # More permissive for fallback
                                            )
                                            
                                            if fallback_results and len(fallback_results) > 0:
                                                # Use the first reasonable result as fallback
                                                fallback_fdc_id = fallback_results[0].fdc_id
                                                if fallback_fdc_id:
                                                    ing_fdc_id = fallback_fdc_id
                                                    gemini_ing.fdc_id = fallback_fdc_id
                                                    gemini_ing.reason_for_choice = f"Fallback search using broader query '{candidate_query.query_term}' after original search failed"
                                                    fallback_attempted = True
                                                    
                                                    meal_logger.log_entry(
                                                        session_id=session_id,
                                                        level=LogLevel.INFO,
                                                        phase=ProcessingPhase.NUTRITION_CALC_START,
                                                        message=f"Fallback successful for ingredient '{gemini_ing.ingredient_name}' using query '{candidate_query.query_term}'"
                                                    )
                                                    break
                                        except Exception as e:
                                            meal_logger.log_entry(
                                                session_id=session_id,
                                                level=LogLevel.WARNING,
                                                phase=ProcessingPhase.NUTRITION_CALC_START,
                                                message=f"Fallback search failed for ingredient '{gemini_ing.ingredient_name}': {str(e)}"
                                            )
                                            continue
                                            
                                if fallback_attempted and ing_fdc_id:
                                    break
                        
                        if not fallback_attempted or not ing_fdc_id:
                            warnings.append(f"Missing FDC ID for ingredient '{gemini_ing.ingredient_name}' - no suitable fallback found")

                    if ing_fdc_id and estimated_weight > 0:
                        ing_nutrients_100g = await usda_service.get_food_details_for_nutrition(ing_fdc_id)
                        if ing_nutrients_100g:
                            ing_actual_nutrients = nutrition_service.calculate_actual_nutrients(ing_nutrients_100g, estimated_weight)
                            ingredient_nutrients_list.append(ing_actual_nutrients)
                        else:
                            warnings.append(f"Could not get nutrition data for ingredient '{gemini_ing.ingredient_name}' (FDC ID: {ing_fdc_id})")
                    elif not ing_fdc_id:
                        warnings.append(f"Missing FDC ID for ingredient '{gemini_ing.ingredient_name}'")
                    elif estimated_weight <= 0:
                        warnings.append(f"Missing or invalid weight for ingredient '{gemini_ing.ingredient_name}'")

                    refined_ingredients_list.append(RefinedIngredientResponse(
                        ingredient_name=gemini_ing.ingredient_name,
                        weight_g=estimated_weight,
                        fdc_id=ing_fdc_id,
                        usda_source_description=gemini_ing.usda_source_description,
                        reason_for_choice=gemini_ing.reason_for_choice,
                        key_nutrients_per_100g=ing_nutrients_100g,
                        actual_nutrients=ing_actual_nutrients
                    ))
                
                # Aggregate nutrients from valid ingredients
                dish_total_nutrients = nutrition_service.aggregate_nutrients_for_dish_from_ingredients(
                    [ing for ing in refined_ingredients_list if ing.actual_nutrients]  # None を除外
                )

            # RefinedDishResponse を作成
            refined_dishes_response.append(RefinedDishResponse(
                dish_name=gemini_dish.dish_name,
                type=p1_dish.type,
                quantity_on_plate=p1_dish.quantity_on_plate,
                estimated_total_dish_weight_g=None,  # Phase1に重量推定なし
                actual_weight_used_for_calculation_g=actual_weight_used_g,
                weight_calculation_method=weight_calculation_method,
                calculation_strategy=gemini_dish.calculation_strategy,
                reason_for_strategy=gemini_dish.reason_for_strategy,
                fdc_id=gemini_dish.fdc_id,
                usda_source_description=gemini_dish.usda_source_description,
                reason_for_choice=gemini_dish.reason_for_choice,
                key_nutrients_per_100g=dish_key_nutrients_100g,
                ingredients=refined_ingredients_list,
                dish_total_actual_nutrients=dish_total_nutrients
            ))

        # 8. Calculate total meal nutrients
        total_meal_nutrients = nutrition_service.aggregate_nutrients_for_meal(
            refined_dishes_response
        )
        
        nutrition_calc_duration = (time.time() - nutrition_calc_start_time) * 1000
        total_calories = total_meal_nutrients.calories_kcal if total_meal_nutrients else 0.0
        
        # 栄養計算結果をログに記録
        meal_logger.update_nutrition_results(
            session_id=session_id,
            duration_ms=nutrition_calc_duration,
            total_calories=total_calories,
            final_nutrition={
                "total_meal_nutrients": total_meal_nutrients.dict() if total_meal_nutrients else None,
                "dishes_count": len(refined_dishes_response),
                "warnings_count": len(warnings),
                "errors_count": len(errors)
            }
        )

        # 9. Create final response
        response = MealAnalysisRefinementResponse(
            dishes=refined_dishes_response,
            total_meal_nutrients=total_meal_nutrients,
            warnings=warnings if warnings else None,
            errors=errors if errors else None
        )
        
        # 8. Enhanced Iterative Improvement Loop with Cooking State Validation
        MAX_RETRY_ATTEMPTS = 1  # Maximum retry attempts per problematic ingredient
        retry_summary = []
        needs_recalculation = False
        
        # Function to check cooking state mismatch
        def has_cooking_state_mismatch(ingredient_name: str, usda_description: str, phase1_state: str) -> bool:
            """Check if there's a cooking state mismatch between Phase1 and selected FDC ID"""
            if not usda_description or not phase1_state:
                return False
            
            usda_lower = usda_description.lower()
            state_lower = phase1_state.lower()
            
            # Define cooking state indicators
            cooked_indicators = ["cooked", "prepared", "grilled", "fried", "baked", "boiled", "steamed", "roasted"]
            raw_indicators = ["raw", "fresh", "uncooked"]
            dry_indicators = ["dry", "dried", "dehydrated", "uncooked"]
            
            # Check for mismatches
            if state_lower == "cooked":
                # Phase1 says cooked, but USDA suggests dry/raw
                if any(indicator in usda_lower for indicator in dry_indicators + raw_indicators):
                    return True
            elif state_lower == "raw":
                # Phase1 says raw, but USDA suggests cooked
                if any(indicator in usda_lower for indicator in cooked_indicators):
                    return True
            elif state_lower == "dry":
                # Phase1 says dry, but USDA suggests cooked
                if any(indicator in usda_lower for indicator in cooked_indicators):
                    return True
            
            return False
        
        for dish_idx, dish_response in enumerate(response.dishes):
            for ing_idx, ingredient_response in enumerate(dish_response.ingredients):
                # Find corresponding Phase1 ingredient for state comparison
                p1_ingredient_state = None
                for p1_dish in phase1_analysis.dishes:
                    if p1_dish.dish_name == dish_response.dish_name:
                        for p1_ing in p1_dish.ingredients:
                            if p1_ing.ingredient_name == ingredient_response.ingredient_name:
                                p1_ingredient_state = p1_ing.state
                                break
                    if p1_ingredient_state:
                        break
                
                # Identify problematic ingredients
                is_problematic = False
                problem_reason = ""
                
                # Case 1: Missing FDC ID
                if ingredient_response.fdc_id is None and ingredient_response.weight_g > 0:
                    is_problematic = True
                    problem_reason = "Missing FDC ID"
                
                # Case 2: Cooking state mismatch
                elif (ingredient_response.fdc_id and 
                      ingredient_response.usda_source_description and 
                      p1_ingredient_state and
                      has_cooking_state_mismatch(ingredient_response.ingredient_name, 
                                               ingredient_response.usda_source_description, 
                                               p1_ingredient_state)):
                    is_problematic = True
                    problem_reason = f"Cooking state mismatch: Phase1='{p1_ingredient_state}' vs USDA='{ingredient_response.usda_source_description}'"
                
                if is_problematic and ingredient_response.weight_g > 0:  # Only retry significant ingredients
                    meal_logger.log_entry(
                        session_id=session_id,
                        level=LogLevel.WARNING,
                        phase=ProcessingPhase.NUTRITION_CALC_START,
                        message=f"Problematic ingredient detected: {ingredient_response.ingredient_name} - {problem_reason}"
                    )
                    
                    for attempt in range(MAX_RETRY_ATTEMPTS):
                        meal_logger.log_entry(
                            session_id=session_id, 
                            level=LogLevel.INFO, 
                            phase=ProcessingPhase.PHASE1_START,
                            message=f"Retry attempt {attempt + 1} for problematic ingredient: {ingredient_response.ingredient_name} in dish {dish_response.dish_name}",
                            data={
                                "problematic_ingredient": ingredient_response.ingredient_name,
                                "dish_name": dish_response.dish_name,
                                "weight_g": ingredient_response.weight_g,
                                "problem_reason": problem_reason,
                                "attempt_number": attempt + 1
                            }
                        )
                        
                        try:
                            # Collect relevant USDA candidates from all_usda_search_results_map
                            relevant_candidates = []
                            
                            # Look for alternatives that better match the cooking state
                            for fdc_id_key, usda_item in all_usda_search_results_map.items():
                                if ingredient_response.ingredient_name.lower() in usda_item.description.lower():
                                    # Prioritize candidates that match cooking state
                                    if p1_ingredient_state:
                                        state_match = False
                                        if p1_ingredient_state.lower() == "cooked":
                                            state_match = any(term in usda_item.description.lower() 
                                                            for term in ["cooked", "prepared", "grilled", "fried", "baked", "boiled", "steamed"])
                                        elif p1_ingredient_state.lower() == "raw":
                                            state_match = any(term in usda_item.description.lower() 
                                                            for term in ["raw", "fresh", "uncooked"])
                                        elif p1_ingredient_state.lower() == "dry":
                                            state_match = any(term in usda_item.description.lower() 
                                                            for term in ["dry", "dried", "dehydrated"])
                                        
                                        if state_match:
                                            relevant_candidates.append((usda_item, "cooking_state_match"))
                                    
                                    relevant_candidates.append((usda_item, "name_match"))
                            
                            # Sort candidates: cooking state matches first, then by score
                            relevant_candidates.sort(key=lambda x: (0 if x[1] == "cooking_state_match" else 1, -(x[0].score or 0)))
                            
                            # Try top candidates
                            selected_fallback = None
                            best_fallback_reason = "No suitable fallback found after retry."
                            
                            for candidate_item, match_type in relevant_candidates[:3]:  # Try top 3
                                # Additional validation for cooking state
                                if p1_ingredient_state and match_type == "cooking_state_match":
                                    selected_fallback = candidate_item
                                    best_fallback_reason = f"Enhanced retry: Selected '{candidate_item.description}' for better cooking state match (Phase1: {p1_ingredient_state})"
                                    break
                                elif not selected_fallback and match_type == "name_match":
                                    # Fallback to name match if no cooking state match
                                    selected_fallback = candidate_item
                                    best_fallback_reason = f"Enhanced retry: Selected '{candidate_item.description}' as best available match"
                            
                            if selected_fallback:
                                # Update the ingredient with better FDC ID
                                old_fdc_id = ingredient_response.fdc_id
                                response.dishes[dish_idx].ingredients[ing_idx].fdc_id = selected_fallback.fdc_id
                                response.dishes[dish_idx].ingredients[ing_idx].usda_source_description = selected_fallback.description
                                response.dishes[dish_idx].ingredients[ing_idx].reason_for_choice = best_fallback_reason
                                
                                # Get new nutrition data
                                new_nutrition_100g = await usda_service.get_food_details_for_nutrition(selected_fallback.fdc_id)
                                if new_nutrition_100g:
                                    response.dishes[dish_idx].ingredients[ing_idx].key_nutrients_per_100g = new_nutrition_100g
                                    response.dishes[dish_idx].ingredients[ing_idx].actual_nutrients = nutrition_service.calculate_actual_nutrients(new_nutrition_100g, ingredient_response.weight_g)
                                    needs_recalculation = True
                                
                                retry_summary.append({
                                    "ingredient": ingredient_response.ingredient_name,
                                    "status": "success",
                                    "old_fdc_id": old_fdc_id,
                                    "new_fdc_id": selected_fallback.fdc_id,
                                    "problem_reason": problem_reason,
                                    "solution": best_fallback_reason
                                })
                                
                                meal_logger.log_entry(
                                    session_id=session_id,
                                    level=LogLevel.INFO,
                                    phase=ProcessingPhase.NUTRITION_CALC_START,
                                    message=f"Enhanced retry successful for {ingredient_response.ingredient_name}: {old_fdc_id} -> {selected_fallback.fdc_id}"
                                )
                                
                                break  # Success, exit retry loop for this ingredient
                            else:
                                retry_summary.append({
                                    "ingredient": ingredient_response.ingredient_name,
                                    "status": "failed - no suitable candidate",
                                    "problem_reason": problem_reason
                                })
                                
                        except Exception as retry_e:
                            meal_logger.log_entry(
                                session_id=session_id,
                                level=LogLevel.ERROR,
                                phase=ProcessingPhase.NUTRITION_CALC_START,
                                message=f"Error during enhanced retry for {ingredient_response.ingredient_name}: {retry_e}"
                            )
                            retry_summary.append({
                                "ingredient": ingredient_response.ingredient_name,
                                "status": "error",
                                "details": str(retry_e),
                                "problem_reason": problem_reason
                            })
                            break
                    
                    # Log final outcome for this ingredient
                    if not any(r["ingredient"] == ingredient_response.ingredient_name and r["status"] == "success" for r in retry_summary):
                        meal_logger.log_entry(
                            session_id=session_id,
                            level=LogLevel.WARNING,
                            phase=ProcessingPhase.NUTRITION_CALC_START,
                            message=f"All retry attempts failed for {ingredient_response.ingredient_name} - {problem_reason}"
                        )
        
        # Recalculate dish and meal totals if any ingredients were updated
        if needs_recalculation:
            meal_logger.log_entry(
                session_id=session_id,
                level=LogLevel.INFO,
                phase=ProcessingPhase.NUTRITION_CALC_START,
                message="Recalculating nutrition after enhanced iterative improvements..."
            )
            
            for dish_response in response.dishes:
                if dish_response.calculation_strategy == "ingredient_level":
                    # Recalculate dish total from updated ingredients
                    valid_ingredients = [ing for ing in dish_response.ingredients if ing.actual_nutrients]
                    dish_response.dish_total_actual_nutrients = nutrition_service.aggregate_nutrients_for_dish_from_ingredients(valid_ingredients)
            
            # Recalculate meal total
            response.total_meal_nutrients = nutrition_service.aggregate_nutrients_for_meal(response.dishes)
        
        # Log retry summary
        if retry_summary:
            meal_logger.log_entry(
                session_id=session_id,
                level=LogLevel.INFO,
                phase=ProcessingPhase.NUTRITION_CALC_START,
                message=f"Enhanced iterative improvement completed: {len(retry_summary)} ingredients processed",
                data={"retry_summary": retry_summary}
            )

        # セッション終了
        meal_logger.end_session(
            session_id=session_id,
            warnings=warnings,
            errors=errors
        )
        
        return response

    except Exception as e:
        # 予期しないエラーのログ記録
        meal_logger.log_error(
            session_id=session_id,
            phase=ProcessingPhase.ERROR_OCCURRED,
            error_message="Unexpected error during request processing",
            error_details=str(e)
        )
        
        # セッション終了（エラー時）
        meal_logger.end_session(
            session_id=session_id,
            warnings=warnings,
            errors=errors + [str(e)]
        )
        
        raise 