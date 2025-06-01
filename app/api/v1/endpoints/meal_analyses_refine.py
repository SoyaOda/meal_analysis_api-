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
from ....services.nutrition_calculation_service import NutritionCalculationService, get_nutrition_calculation_service
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

        # 3. Execute Enhanced USDA searches based on Phase 1 candidates (improved v2.1)
        meal_logger.log_entry(
            session_id=session_id,
            level=LogLevel.INFO,
            phase=ProcessingPhase.USDA_SEARCH_START,
            message="Starting enhanced USDA searches with brand-aware strategy and explicit query-result mapping"
        )
        
        usda_search_start_time = time.time()
        
        # query_map は Phase 1 の query_term と original_term (表示用) のマッピングに引き続き使用
        query_map = {}
        for dish in phase1_analysis.dishes:
            for candidate in dish.usda_query_candidates:
                query_map[candidate.query_term] = candidate.original_term or dish.dish_name

        # 各Phase 1クエリ候補と、それに対するUSDA検索パラメータをペアで保持するリスト
        # これにより、結果とのマッピングが崩れないようにする
        query_tasks_with_context = []

        # ブランドクエリと通常クエリの準備ロジック
        branded_candidates_from_phase1 = []
        regular_candidates_from_phase1 = []
        detected_brands = set()

        for dish in phase1_analysis.dishes:
            for candidate in dish.usda_query_candidates:
                # 重複排除: 同じquery_termは一度だけ処理
                existing_query_terms = [task['phase1_candidate'].query_term for task in query_tasks_with_context]
                if candidate.query_term in existing_query_terms:
                    continue
                    
                if candidate.granularity_level == "branded_product":
                    branded_candidates_from_phase1.append(candidate)
                    # ブランド名を抽出
                    query_parts = candidate.query_term.split()
                    if len(query_parts) >= 2:
                        potential_brand = query_parts[0] + (" " + query_parts[1] if len(query_parts) > 2 else "")
                        detected_brands.add(potential_brand)
                else:
                    regular_candidates_from_phase1.append(candidate)
        
        logger.info(f"Preparing USDA search tasks: {len(branded_candidates_from_phase1)} branded, {len(regular_candidates_from_phase1)} regular candidates")
        if detected_brands:
            logger.info(f"Detected brands: {list(detected_brands)}")

        # 1. ブランド優先検索タスクの準備
        for candidate in branded_candidates_from_phase1:
            query_parts = candidate.query_term.split()
            brand_name_filter = None
            search_query = candidate.query_term

            # ブランド名抽出ロジックの改善
            if "la madeleine" in candidate.query_term.lower():
                brand_name_filter = "La Madeleine"
                # クエリからブランド名部分を除去
                search_query = candidate.query_term.lower().replace("la madeleine", "").strip()
                if not search_query: 
                    search_query = candidate.query_term
            elif len(query_parts) > 1:
                # 一般的なブランド名抽出の試み
                potential_brand = query_parts[0]
                if len(query_parts) > 2 and not query_parts[1].lower() in ["salad", "pasta", "chicken", "beef", "cheese", "dressing"]:
                    potential_brand = f"{query_parts[0]} {query_parts[1]}"
                    search_query = " ".join(query_parts[2:])
                else:
                    search_query = " ".join(query_parts[1:])
                if not search_query: 
                    search_query = candidate.query_term
                brand_name_filter = potential_brand

            search_params = {
                "query": search_query,
                "data_types": ["Branded", "FNDDS"],
                "page_size": 15,
                "require_all_words": True,
                "brand_owner_filter": brand_name_filter
            }
            query_tasks_with_context.append({'phase1_candidate': candidate, 'search_params': search_params})

        # 2. 通常検索タスクの準備
        for candidate in regular_candidates_from_phase1:
            cooking_keywords = ["cooked", "raw", "grilled", "fried", "baked", "steamed", "processed"]
            query_lower = candidate.query_term.lower()
            has_cooking_state = any(keyword in query_lower for keyword in cooking_keywords)
            
            data_types_for_regular = ["Foundation", "FNDDS", "SR Legacy"]
            require_all_words_for_regular = False

            if candidate.granularity_level == "dish":
                data_types_for_regular = ["FNDDS", "Branded", "Foundation"]
                require_all_words_for_regular = True
            elif candidate.granularity_level == "ingredient":
                if has_cooking_state:
                    data_types_for_regular = ["FNDDS", "Foundation"]
                else:
                    data_types_for_regular = ["Foundation", "FNDDS"]
        
            search_params = {
                "query": candidate.query_term,
                "data_types": data_types_for_regular,
                "page_size": 12,
                "require_all_words": require_all_words_for_regular,
                "brand_owner_filter": None
            }
            query_tasks_with_context.append({'phase1_candidate': candidate, 'search_params': search_params})

        # USDA検索タスクの非同期実行
        usda_search_api_tasks = []
        for task_info in query_tasks_with_context:
            usda_search_api_tasks.append(
                usda_service.search_foods_rich(**task_info['search_params'])
            )
        
        logger.info(f"Executing {len(usda_search_api_tasks)} USDA search API tasks.")
        usda_search_results_list = await asyncio.gather(*usda_search_api_tasks, return_exceptions=True)
        usda_search_duration = (time.time() - usda_search_start_time) * 1000
        logger.info(f"USDA searches completed in {usda_search_duration:.2f} ms.")

        # 4. Enhanced USDA results processing with Tiered Search fallback
        augmented_usda_search_results_map = {}  # Store results per original query_term
        all_usda_search_results_map: Dict[int, USDASearchResultItem] = {}
        search_details_for_log = []

        if len(query_tasks_with_context) != len(usda_search_results_list):
            logger.error("Mismatch between number of query tasks and results. This should not happen.")
            errors.append("Internal error: USDA search task-result mismatch")

        for i, task_info in enumerate(query_tasks_with_context):
            original_phase1_candidate = task_info['phase1_candidate']
            original_query_term = original_phase1_candidate.query_term
            current_results_or_exc = usda_search_results_list[i]
            
            # Initialize with original search results
            final_candidates_for_query = list(current_results_or_exc) if isinstance(current_results_or_exc, list) else []
            
            log_detail_for_query = {
                "phase1_query_term": original_query_term,
                "original_term_from_phase1": query_map.get(original_query_term, original_phase1_candidate.original_term),
                "granularity": original_phase1_candidate.granularity_level,
                "usda_search_params_initial": task_info['search_params'],
                "status_initial_search": "error" if isinstance(current_results_or_exc, Exception) else ("no_results" if not final_candidates_for_query else "success"),
                "results_count_initial": len(final_candidates_for_query) if isinstance(final_candidates_for_query, list) else 0,
                "fallback_searches_attempted": []
            }
            if isinstance(current_results_or_exc, Exception):
                log_detail_for_query["error_message_initial"] = str(current_results_or_exc)

            # --- Tiered Fallback Logic for Ingredients ---
            is_ingredient_query = original_phase1_candidate.granularity_level == "ingredient"
            
            # Enhanced criteria for "poor results"
            is_poor_results = False
            if not final_candidates_for_query:
                is_poor_results = True
            elif len(final_candidates_for_query) < 2:
                is_poor_results = True
            else:
                # Check if results are compositionally relevant
                query_keywords = set(original_query_term.lower().replace(',', ' ').split())
                relevant_results = 0
                for result in final_candidates_for_query:
                    desc_keywords = set(result.description.lower().split())
                    # Check for any keyword overlap (basic relevance check)
                    if query_keywords.intersection(desc_keywords):
                        relevant_results += 1
                
                if relevant_results == 0:
                    is_poor_results = True
                    logger.info(f"No compositionally relevant results found for '{original_query_term}' - triggering fallback")

            if is_ingredient_query and is_poor_results and not isinstance(current_results_or_exc, Exception):
                fallback_queries = []
                
                # Generate smart fallback queries
                term_lower = original_query_term.lower()
                
                # 1. Remove cooking state (e.g., "Penne pasta, cooked" -> "Penne pasta")
                term_parts = original_query_term.split(',')
                if len(term_parts) > 1:
                    base_term = term_parts[0].strip()
                    fallback_queries.append(base_term)
                
                # 2. Pasta-specific fallbacks
                if "pasta" in term_lower:
                    if "penne" in term_lower:
                        fallback_queries.extend(["Pasta, cooked", "Pasta, wheat, cooked", "Pasta"])
                    else:
                        fallback_queries.extend(["Pasta, cooked", "Pasta"])
                
                # 3. Dressing-specific fallbacks
                elif "dressing" in term_lower:
                    if "creamy" in term_lower or "cream" in term_lower:
                        fallback_queries.extend(["Salad dressing, creamy", "Salad dressing", "Dressing"])
                    else:
                        fallback_queries.extend(["Salad dressing", "Dressing"])
                
                # 4. Meat-specific fallbacks
                elif "chicken" in term_lower:
                    fallback_queries.extend(["Chicken, cooked", "Chicken"])
                
                # 5. Vegetable-specific fallbacks
                elif any(veg in term_lower for veg in ["lettuce", "tomato", "pepper", "onion"]):
                    base_veg = None
                    if "lettuce" in term_lower:
                        base_veg = "Lettuce"
                    elif "tomato" in term_lower:
                        base_veg = "Tomato"
                    elif "pepper" in term_lower:
                        base_veg = "Pepper"
                    elif "onion" in term_lower:
                        base_veg = "Onion"
                    
                    if base_veg:
                        fallback_queries.extend([f"{base_veg}, raw", base_veg])
                
                # 6. Generic term extraction (remove specific adjectives)
                generic_term = original_query_term
                for specific in ["penne", "romaine", "caesar", "italian", "greek"]:
                    generic_term = generic_term.replace(specific, "").strip()
                generic_term = ' '.join(generic_term.split())  # Clean up extra spaces
                if generic_term and generic_term != original_query_term:
                    fallback_queries.append(generic_term)
                
                # Remove duplicates and empty queries
                fallback_queries = [q for q in list(dict.fromkeys(fallback_queries)) if q and q.lower() != original_query_term.lower()]
                
                seen_fallback_fdc_ids = {item.fdc_id for item in final_candidates_for_query}

                for fb_idx, fallback_query in enumerate(fallback_queries[:3]):  # Limit to 3 fallback attempts
                    logger.info(f"Attempting fallback search #{fb_idx+1} for '{original_query_term}' with query: '{fallback_query}'")
                    
                    fallback_search_params = {
                        "query": fallback_query,
                        "data_types": ["Foundation", "FNDDS", "SR Legacy"],
                        "page_size": 5,
                        "require_all_words": False,
                        "search_context": "ingredient"
                    }
                    
                    fallback_attempt_log = {
                        "fallback_query": fallback_query,
                        "params": fallback_search_params,
                        "attempt_number": fb_idx + 1
                    }
                    
                    try:
                        fb_results = await usda_service.search_foods_rich(**fallback_search_params)
                        fallback_attempt_log["status"] = "success"
                        fallback_attempt_log["results_count"] = len(fb_results) if fb_results else 0
                        
                        if fb_results:
                            logger.info(f"Fallback search #{fb_idx+1} for '{fallback_query}' found {len(fb_results)} results.")
                            new_results_added = 0
                            for item in fb_results:
                                if item.fdc_id not in seen_fallback_fdc_ids:
                                    # Mark as fallback for tracking
                                    item.fallback_query_used = fallback_query
                                    item.fallback_attempt = fb_idx + 1
                                    final_candidates_for_query.append(item)
                                    seen_fallback_fdc_ids.add(item.fdc_id)
                                    new_results_added += 1
                            
                            fallback_attempt_log["new_results_added"] = new_results_added
                            
                            if new_results_added > 0:
                                logger.info(f"Added {new_results_added} new candidates from fallback search")
                        
                        log_detail_for_query["fallback_searches_attempted"].append(fallback_attempt_log)
                        
                        # Stop if we have sufficient results now
                        if len(final_candidates_for_query) >= 3:
                            break
                            
                    except Exception as fb_e:
                        logger.error(f"Error during fallback USDA search #{fb_idx+1} for '{fallback_query}': {fb_e}")
                        fallback_attempt_log["status"] = "error"
                        fallback_attempt_log["error_message"] = str(fb_e)
                        log_detail_for_query["fallback_searches_attempted"].append(fallback_attempt_log)
                
                # Update log with final results
                log_detail_for_query["final_results_count"] = len(final_candidates_for_query)
                log_detail_for_query["fallback_success"] = len(final_candidates_for_query) > log_detail_for_query["results_count_initial"]
                        
            augmented_usda_search_results_map[original_query_term] = final_candidates_for_query
            search_details_for_log.append(log_detail_for_query)

        # 5. Format USDA results for Gemini prompt using augmented results
        usda_candidates_prompt_segments = []
        
        for dish in phase1_analysis.dishes:
            for candidate in dish.usda_query_candidates:
                phase1_query_term = candidate.query_term
                
                # Retrieve the (potentially augmented) list of results for this phase1_query_term
                results_for_this_query = augmented_usda_search_results_map.get(phase1_query_term, [])
                
                prompt_segment_header = (
                    f"USDA candidates for Phase 1 query: '{phase1_query_term}' "
                    f"(Original term: '{query_map.get(phase1_query_term, candidate.original_term)}', "
                    f"Granularity: {candidate.granularity_level}, "
                    f"Reason from Phase 1: '{candidate.reason_for_query}'):\n"
                )
                
                segment_content = ""
                if not results_for_this_query:
                    segment_content = f"  No USDA candidates found for this query (including fallbacks).\n"
                else:
                    for j, item in enumerate(results_for_this_query):
                        # Store all results for later FDC ID lookup during nutrition calculation
                        all_usda_search_results_map[item.fdc_id] = item
                        
                        brand_part = f", Brand: {item.brand_owner}" if item.brand_owner else ""
                        score_part = f"{item.score:.2f}" if item.score is not None else "N/A"
                        fallback_info = f" (from fallback: '{item.fallback_query_used}')" if hasattr(item, 'fallback_query_used') else ""
                        
                        segment_content += (
                            f"  {j+1}. FDC ID: {item.fdc_id}, Name: {item.description} "
                            f"(Type: {item.data_type or 'N/A'}{brand_part}), "
                            f"Score: {score_part}{fallback_info}\n"
                        )
                        if item.ingredients_text:
                            segment_content += f"     Ingredients (partial): {item.ingredients_text[:100]}...\n"
                
                usda_candidates_prompt_segments.append(prompt_segment_header + segment_content)

        usda_candidates_prompt_text = "\n---\n".join(usda_candidates_prompt_segments)
        
        # Update USDA search duration to include fallback time
        usda_search_duration = (time.time() - usda_search_start_time) * 1000
        
        # Enhanced USDA search results logging
        total_initial_results = sum(detail["results_count_initial"] for detail in search_details_for_log)
        total_final_results = sum(detail.get("final_results_count", detail["results_count_initial"]) for detail in search_details_for_log)
        fallback_successes = sum(1 for detail in search_details_for_log if detail.get("fallback_success", False))
        
        meal_logger.update_usda_search_results(
            session_id=session_id,
            duration_ms=usda_search_duration,
            queries_executed=len(query_tasks_with_context),
            results_found=total_final_results,
            search_details={
                "initial_results": total_initial_results,
                "final_results": total_final_results,
                "fallback_successes": fallback_successes,
                "detailed_searches": search_details_for_log
            }
        )

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

        # Phase 1 の重量情報をマッピングしやすくする
        phase1_weights_map = {
            (d.dish_name, i.ingredient_name): i.weight_g
            for d in phase1_analysis.dishes
            for i in d.ingredients
        }

        for gemini_dish in gemini_phase2_response.dishes:
            # Phase 1 Dish を名前で探す (厳密にはIDなどで引くべきだが、今回は名前で)
            p1_dish = next((d for d in phase1_analysis.dishes if d.dish_name == gemini_dish.dish_name), None)
            if not p1_dish:
                warnings.append(f"Could not match Phase 2 dish '{gemini_dish.dish_name}' to Phase 1.")
                continue

            dish_total_nutrients = None
            refined_ingredients_list: List[RefinedIngredientResponse] = []
            dish_key_nutrients_100g = None

            if gemini_dish.calculation_strategy == "dish_level":
                dish_fdc_id = gemini_dish.fdc_id
                
                # Dish-level fallback processing implementation
                if not dish_fdc_id:
                    # Try fallback: if original search was branded, try generic dish search
                    warnings.append(f"Original dish-level search failed for '{gemini_dish.dish_name}'. Attempting fallback to ingredient-level calculation.")
                    
                    # Force switch to ingredient_level strategy
                    gemini_dish.calculation_strategy = "ingredient_level"
                    meal_logger.log_entry(
                        session_id=session_id,
                        level=LogLevel.INFO,
                        phase=ProcessingPhase.NUTRITION_CALC_START,
                        message=f"Switching from dish_level to ingredient_level for '{gemini_dish.dish_name}' due to missing FDC ID"
                    )
                
                if gemini_dish.calculation_strategy == "dish_level" and dish_fdc_id:
                    dish_weight_g = sum(ing.weight_g for ing in p1_dish.ingredients)
                    dish_key_nutrients_100g = await usda_service.get_food_details_for_nutrition(dish_fdc_id)
                    if dish_key_nutrients_100g and dish_weight_g > 0:
                        dish_total_nutrients = nutrition_service.calculate_actual_nutrients(dish_key_nutrients_100g, dish_weight_g)
                    else:
                        warnings.append(f"Could not calculate dish-level nutrition for '{gemini_dish.dish_name}'. Switching to ingredient-level.")
                        gemini_dish.calculation_strategy = "ingredient_level"

                # Material information for dish_level (fallback FDC IDs for reference)
                if gemini_dish.calculation_strategy == "dish_level":
                    for gemini_ing in gemini_dish.ingredients:
                        weight = phase1_weights_map.get((gemini_dish.dish_name, gemini_ing.ingredient_name), 0.0)
                        ing_nutrients_100g = await usda_service.get_food_details_for_nutrition(gemini_ing.fdc_id) if gemini_ing.fdc_id else None
                        refined_ingredients_list.append(RefinedIngredientResponse(
                            ingredient_name=gemini_ing.ingredient_name,
                            weight_g=weight,
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
                    weight = phase1_weights_map.get((gemini_dish.dish_name, gemini_ing.ingredient_name), 0.0)
                    ing_fdc_id = gemini_ing.fdc_id
                    ing_nutrients_100g = None
                    ing_actual_nutrients = None

                    # Enhanced ingredient-level fallback processing
                    if not ing_fdc_id and weight > 0:
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
                                                max_results=5,
                                                data_types=["Foundation", "SR Legacy", "FNDDS"],
                                                require_all_words=False  # More permissive for fallback
                                            )
                                            
                                            if fallback_results and len(fallback_results) > 0:
                                                # Use the first reasonable result as fallback
                                                fallback_fdc_id = fallback_results[0].get('fdcId')
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

                    if ing_fdc_id and weight > 0:
                        ing_nutrients_100g = await usda_service.get_food_details_for_nutrition(ing_fdc_id)
                        if ing_nutrients_100g:
                            ing_actual_nutrients = nutrition_service.calculate_actual_nutrients(ing_nutrients_100g, weight)
                            ingredient_nutrients_list.append(ing_actual_nutrients)
                        else:
                            warnings.append(f"Could not get nutrition data for ingredient '{gemini_ing.ingredient_name}' (FDC ID: {ing_fdc_id})")
                    elif not ing_fdc_id:
                        warnings.append(f"Missing FDC ID for ingredient '{gemini_ing.ingredient_name}'")
                    elif weight <= 0:
                        warnings.append(f"Missing or invalid weight for ingredient '{gemini_ing.ingredient_name}'")

                    refined_ingredients_list.append(RefinedIngredientResponse(
                        ingredient_name=gemini_ing.ingredient_name,
                        weight_g=weight,
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