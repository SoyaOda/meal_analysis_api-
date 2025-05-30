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
            message="Starting enhanced USDA searches with brand-aware strategy"
        )
        
        usda_search_start_time = time.time()
        usda_search_tasks = []
        query_map = {}  # クエリと元の料理/食材名をマッピング
        unique_queries = set()
        
        # 改善: ブランド認識と検索戦略の強化
        detected_brands = set()
        branded_queries = []
        regular_queries = []

        for dish in phase1_analysis.dishes:
            for candidate in dish.usda_query_candidates:
                if candidate.query_term not in unique_queries:
                    unique_queries.add(candidate.query_term)
                    query_map[candidate.query_term] = candidate.original_term or dish.dish_name
                    
                    # ブランド検索の特定とカテゴライズ
                    if candidate.granularity_level == "branded_product":
                        branded_queries.append(candidate)
                        # ブランド名を抽出（例: "La Madeleine Caesar Salad" → "La Madeleine"）
                        query_parts = candidate.query_term.split()
                        if len(query_parts) >= 2:
                            potential_brand = query_parts[0] + (" " + query_parts[1] if len(query_parts) > 2 else "")
                            detected_brands.add(potential_brand)
                    else:
                        regular_queries.append(candidate)

        logger.info(f"Enhanced USDA search strategy: {len(branded_queries)} branded queries, {len(regular_queries)} regular queries")
        if detected_brands:
            logger.info(f"Detected brands: {list(detected_brands)}")

        # 1. ブランド優先検索を実行
        for candidate in branded_queries:
            # ブランド名を抽出してフィルター検索
            query_parts = candidate.query_term.split()
            if len(query_parts) >= 2:
                brand_name = query_parts[0] + (" " + query_parts[1] if len(query_parts) > 2 else "")
                remaining_query = " ".join(query_parts[2:]) if len(query_parts) > 2 else query_parts[-1]
                
                # ブランドフィルター付きで高精度検索
                usda_search_tasks.append(
                    usda_service.search_foods_rich(
                        query=remaining_query,
                        data_types=["Branded", "FNDDS"],  # Brandedを優先
                        page_size=15,  # ブランド検索では結果を多めに取得
                        require_all_words=True,  # 精度重視
                        brand_owner_filter=brand_name
                    )
                )
            else:
                # フォールバック: 通常検索
                usda_search_tasks.append(
                    usda_service.search_foods_rich(
                        query=candidate.query_term,
                        data_types=["Branded", "FNDDS", "Foundation"]
                    )
                )

        # 2. 通常検索を実行（調理状態を考慮した最適化）
        for candidate in regular_queries:
            # 調理状態キーワードの検出と検索最適化
            cooking_keywords = ["cooked", "raw", "grilled", "fried", "baked", "steamed", "processed"]
            has_cooking_state = any(keyword in candidate.query_term.lower() for keyword in cooking_keywords)
            
            if candidate.granularity_level == "dish":
                # 料理レベル: FNDDSを優先
                data_types = ["FNDDS", "Branded", "Foundation"]
                require_all_words = True  # 料理名は精度重視
            elif candidate.granularity_level == "ingredient":
                # 材料レベル: 調理状態に応じて最適化
                if has_cooking_state:
                    data_types = ["FNDDS", "Foundation"]  # 調理済み材料
                else:
                    data_types = ["Foundation", "FNDDS"]  # 生材料
                require_all_words = False  # 材料は柔軟性重視
            else:
                # デフォルト
                data_types = ["Foundation", "FNDDS", "SR Legacy"]
                require_all_words = False
            
            usda_search_tasks.append(
                usda_service.search_foods_rich(
                    query=candidate.query_term,
                    data_types=data_types,
                    page_size=12,
                    require_all_words=require_all_words
                )
            )

        # 非同期でUSDA検索を実行
        logger.info(f"Starting {len(usda_search_tasks)} enhanced USDA searches")
        usda_search_results_list = await asyncio.gather(*usda_search_tasks, return_exceptions=True)
        usda_search_duration = (time.time() - usda_search_start_time) * 1000

        # 4. Format USDA results for Gemini prompt
        usda_candidates_prompt_segments = []
        all_usda_search_results_map: Dict[int, USDASearchResultItem] = {}  # FDC ID で引けるように
        search_term_to_results: Dict[str, List[USDASearchResultItem]] = {}  # クエリ -> 結果
        total_results_found = 0
        search_details = []

        for query, results_or_exc in zip(unique_queries, usda_search_results_list):
            original_term = query_map.get(query, query)
            if isinstance(results_or_exc, Exception):
                segment = f"Error searching USDA for '{query}' (related to '{original_term}'): {results_or_exc}\n"
                errors.append(f"USDA Search failed for {query}: {results_or_exc}")
                search_details.append({
                    "query": query,
                    "original_term": original_term,
                    "status": "error",
                    "error": str(results_or_exc)
                })
            elif not results_or_exc:
                segment = f"No USDA candidates found for '{query}' (related to '{original_term}').\n"
                search_details.append({
                    "query": query,
                    "original_term": original_term,
                    "status": "no_results"
                })
            else:
                search_term_to_results[query] = results_or_exc
                total_results_found += len(results_or_exc)
                segment = f"USDA candidates for '{query}' (related to '{original_term}'):\n"
                
                result_summaries = []
                for i, item in enumerate(results_or_exc):
                    all_usda_search_results_map[item.fdc_id] = item
                    # NEW: データタイプとブランド情報をプロンプトに含める
                    segment += (
                        f"  {i+1}. FDC ID: {item.fdc_id}, Name: {item.description} "
                        f"(Type: {item.data_type or 'N/A'}"
                        f"{f', Brand: {item.brand_owner}' if item.brand_owner else ''}), "
                        f"Score: {item.score:.2f}\n"
                        # 必要であれば ingredientsText や nutrients も一部含める
                    )
                    if item.ingredients_text:
                        segment += f"    Ingredients: {item.ingredients_text[:150]}...\n"
                    
                    result_summaries.append({
                        "fdc_id": item.fdc_id,
                        "description": item.description,
                        "data_type": item.data_type,
                        "score": item.score
                    })
                
                search_details.append({
                    "query": query,
                    "original_term": original_term,
                    "status": "success",
                    "results_count": len(results_or_exc),
                    "results": result_summaries
                })
            
            usda_candidates_prompt_segments.append(segment)

        usda_candidates_prompt_text = "\n---\n".join(usda_candidates_prompt_segments)
        
        # USDA検索結果をログに記録
        meal_logger.update_usda_search_results(
            session_id=session_id,
            duration_ms=usda_search_duration,
            queries_executed=len(unique_queries),
            results_found=total_results_found,
            search_details=search_details
        )

        # 5. Call Gemini service (Phase 2) for strategy and FDC ID selection
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

        # 6. Process Gemini output and perform Nutrition Calculation
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
                if dish_fdc_id:
                    dish_weight_g = sum(ing.weight_g for ing in p1_dish.ingredients)
                    dish_key_nutrients_100g = await usda_service.get_food_details_for_nutrition(dish_fdc_id)
                    if dish_key_nutrients_100g and dish_weight_g > 0:
                        dish_total_nutrients = nutrition_service.calculate_actual_nutrients(dish_key_nutrients_100g, dish_weight_g)
                    else:
                        warnings.append(f"Could not calculate dish-level nutrition for '{gemini_dish.dish_name}'")
                else:
                    warnings.append(f"Dish-level strategy selected for '{gemini_dish.dish_name}' but no FDC ID provided.")

                # 材料情報は説明的に残すが、栄養計算はしない (Fallback FDC ID は取得・表示)
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

            elif gemini_dish.calculation_strategy == "ingredient_level":
                ingredient_nutrients_list = []
                for gemini_ing in gemini_dish.ingredients:
                    weight = phase1_weights_map.get((gemini_dish.dish_name, gemini_ing.ingredient_name), 0.0)
                    ing_fdc_id = gemini_ing.fdc_id
                    ing_nutrients_100g = None
                    ing_actual_nutrients = None

                    if ing_fdc_id and weight > 0:
                        ing_nutrients_100g = await usda_service.get_food_details_for_nutrition(ing_fdc_id)
                        if ing_nutrients_100g:
                            ing_actual_nutrients = nutrition_service.calculate_actual_nutrients(ing_nutrients_100g, weight)
                            ingredient_nutrients_list.append(ing_actual_nutrients)
                        else:
                            warnings.append(f"Could not get nutrition for ingredient '{gemini_ing.ingredient_name}' (FDC ID: {ing_fdc_id})")
                    else:
                        warnings.append(f"Missing FDC ID or weight for ingredient '{gemini_ing.ingredient_name}'")

                    refined_ingredients_list.append(RefinedIngredientResponse(
                        ingredient_name=gemini_ing.ingredient_name,
                        weight_g=weight,
                        fdc_id=ing_fdc_id,
                        usda_source_description=gemini_ing.usda_source_description,
                        reason_for_choice=gemini_ing.reason_for_choice,
                        key_nutrients_per_100g=ing_nutrients_100g,
                        actual_nutrients=ing_actual_nutrients
                    ))
                # 材料から料理全体の栄養を合計
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

        # 7. Calculate total meal nutrients
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

        # 8. Create final response
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