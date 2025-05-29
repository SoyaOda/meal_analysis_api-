from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from typing import Annotated, List, Optional, Dict
import json
import logging
import asyncio  # 非同期処理のため

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
    warnings = []
    errors = []

    # 1. Image validation (既存ロジック)
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

    # 2. Parse Phase 1 analysis_data
    try:
        phase1_dict = json.loads(phase1_analysis_json)
        phase1_analysis = Phase1AnalysisResponse(**phase1_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Phase 1 JSON: {e}")

    # 3. Execute ALL USDA searches based on Phase 1 candidates
    usda_search_tasks = []
    query_map = {}  # クエリと元の料理/食材名をマッピング
    unique_queries = set()

    for dish in phase1_analysis.dishes:
        for candidate in dish.usda_query_candidates:
            if candidate.query_term not in unique_queries:
                # NEW: search_foods_rich を使用
                usda_search_tasks.append(usda_service.search_foods_rich(candidate.query_term))
                query_map[candidate.query_term] = candidate.original_term or dish.dish_name
                unique_queries.add(candidate.query_term)

    # 非同期でUSDA検索を実行
    logger.info(f"Starting {len(usda_search_tasks)} USDA searches")
    usda_search_results_list = await asyncio.gather(*usda_search_tasks, return_exceptions=True)

    # 4. Format USDA results for Gemini prompt
    usda_candidates_prompt_segments = []
    all_usda_search_results_map: Dict[int, USDASearchResultItem] = {}  # FDC ID で引けるように
    search_term_to_results: Dict[str, List[USDASearchResultItem]] = {}  # クエリ -> 結果

    for query, results_or_exc in zip(unique_queries, usda_search_results_list):
        original_term = query_map.get(query, query)
        if isinstance(results_or_exc, Exception):
            segment = f"Error searching USDA for '{query}' (related to '{original_term}'): {results_or_exc}\n"
            errors.append(f"USDA Search failed for {query}: {results_or_exc}")
        elif not results_or_exc:
            segment = f"No USDA candidates found for '{query}' (related to '{original_term}').\n"
        else:
            search_term_to_results[query] = results_or_exc
            segment = f"USDA candidates for '{query}' (related to '{original_term}'):\n"
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
        usda_candidates_prompt_segments.append(segment)

    usda_candidates_prompt_text = "\n---\n".join(usda_candidates_prompt_segments)

    # 5. Call Gemini service (Phase 2) for strategy and FDC ID selection
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

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Gemini Phase 2 error: {e}")

    # 6. Process Gemini output and perform Nutrition Calculation
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
        [dish for dish in refined_dishes_response if dish.dish_total_actual_nutrients]
    )

    # 8. Create final response
    return MealAnalysisRefinementResponse(
        dishes=refined_dishes_response,
        total_meal_nutrients=total_meal_nutrients,
        warnings=warnings if warnings else None,
        errors=errors if errors else None
    ) 