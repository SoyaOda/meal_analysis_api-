from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import json
import logging
from typing import Optional
from datetime import datetime
import os
import uuid
from pathlib import Path

from app.services.gemini_service import GeminiMealAnalyzer
from app.services.usda_service import USDAService
from app.services.nutrition_calculation_service import NutritionCalculationService
from app.core.config import get_settings

# ロギングの設定
logger = logging.getLogger(__name__)

# ルーターの作成
router = APIRouter()

# 設定の取得
settings = get_settings()

# 結果保存ディレクトリの作成
RESULTS_DIR = Path("analysis_results")
RESULTS_DIR.mkdir(exist_ok=True)

# サービスインスタンスのキャッシュ
_gemini_analyzer = None
_usda_service = None
_nutrition_service = None

async def get_gemini_service():
    """GeminiMealAnalyzerの依存性注入"""
    global _gemini_analyzer
    if _gemini_analyzer is None:
        settings = get_settings()
        _gemini_analyzer = GeminiMealAnalyzer(
            project_id=settings.GEMINI_PROJECT_ID,
            location=settings.GEMINI_LOCATION,
            model_name=settings.GEMINI_MODEL_NAME
        )
    return _gemini_analyzer

async def get_usda_service():
    """USDAServiceの依存性注入"""
    global _usda_service
    if _usda_service is None:
        _usda_service = USDAService()
    return _usda_service

async def get_nutrition_service():
    """NutritionCalculationServiceの依存性注入"""
    global _nutrition_service
    if _nutrition_service is None:
        _nutrition_service = NutritionCalculationService()
    return _nutrition_service

def save_analysis_result(result_data: dict, analysis_id: str) -> str:
    """分析結果をファイルに保存する"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meal_analysis_{analysis_id}_{timestamp}.json"
        filepath = RESULTS_DIR / filename
        
        # メタデータを追加
        result_data["metadata"] = {
            "analysis_id": analysis_id,
            "timestamp": datetime.now().isoformat(),
            "processing_pipeline": ["phase1", "usda_query", "phase2", "nutrition_calculation"]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Analysis result saved to: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"Failed to save analysis result: {e}")
        raise HTTPException(status_code=500, detail="Failed to save analysis result")

@router.post("/complete")
async def complete_meal_analysis(
    image: UploadFile = File(...),
    save_results: bool = True,
    gemini_service: GeminiMealAnalyzer = Depends(get_gemini_service),
    usda_service: USDAService = Depends(get_usda_service),
    nutrition_service: NutritionCalculationService = Depends(get_nutrition_service)
):
    """
    完全な食事分析を実行（全フェーズ統合）
    
    - Phase 1: Gemini AIによる画像分析
    - USDA Query: 食材のUSDAデータベース照合
    - Phase 2: 計算戦略決定と栄養価精緻化
    - Nutrition Calculation: 最終栄養価計算
    
    Args:
        image: 分析対象の食事画像
        save_results: 結果を保存するかどうか (デフォルト: True)
    
    Returns:
        完全な分析結果と栄養価計算
    """
    
    analysis_id = str(uuid.uuid4())[:8]  # 短縮版ID
    
    try:
        # 画像の検証
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="アップロードされたファイルは画像である必要があります")
        
        # 画像データの読み込み
        image_data = await image.read()
        logger.info(f"[{analysis_id}] Starting complete meal analysis pipeline")
        
        # === Phase 1: 初期画像分析 ===
        logger.info(f"[{analysis_id}] Phase 1: Initial image analysis")
        phase1_result = await gemini_service.analyze_image_and_text(
            image_bytes=image_data,
            image_mime_type=image.content_type,
            optional_text=None
        )
        
        if not phase1_result or "dishes" not in phase1_result:
            raise HTTPException(status_code=422, detail="Phase 1: 画像から料理を検出できませんでした")
        
        logger.info(f"[{analysis_id}] Phase 1 completed - Detected {len(phase1_result['dishes'])} dishes")
        
        # === USDA Query Phase: 食材のUSDAデータベース照合 ===
        logger.info(f"[{analysis_id}] USDA Query Phase: Database matching")
        
        # 全食材のリストを作成
        all_ingredients = []
        for dish in phase1_result["dishes"]:
            for ingredient in dish.get("ingredients", []):
                all_ingredients.append(ingredient["ingredient_name"])
        
        # USDAデータベースでの照合
        usda_matches = {}
        for ingredient_name in all_ingredients:
            try:
                usda_results = await usda_service.search_foods(ingredient_name)
                if usda_results and len(usda_results) > 0:
                    # USDASearchResultItemオブジェクトから辞書に変換
                    best_match = usda_results[0]
                    usda_matches[ingredient_name] = {
                        "fdcId": best_match.fdc_id,
                        "description": best_match.description,
                        "dataType": best_match.data_type,
                        "score": best_match.score
                    }
                    logger.debug(f"[{analysis_id}] USDA match for '{ingredient_name}': FDC ID {best_match.fdc_id}")
                else:
                    logger.warning(f"[{analysis_id}] No USDA match for: {ingredient_name}")
            except Exception as e:
                logger.error(f"[{analysis_id}] USDA search error for '{ingredient_name}': {e}")
        
        logger.info(f"[{analysis_id}] USDA Query completed - {len(usda_matches)}/{len(all_ingredients)} ingredients matched")
        
        # === Phase 2: 計算戦略決定と栄養価精緻化 ===
        logger.info(f"[{analysis_id}] Phase 2: Strategy determination and nutritional refinement")
        
        # Phase 2でGemini AIに計算戦略を決定させる
        phase2_result = await gemini_service.analyze_image_with_usda_context(
            image_bytes=image_data,
            image_mime_type=image.content_type,
            usda_candidates_text=json.dumps(usda_matches),
            initial_ai_output_text=json.dumps(phase1_result)
        )
        
        if not phase2_result or "dishes" not in phase2_result:
            raise HTTPException(status_code=422, detail="Phase 2: 栄養価の精緻化に失敗しました")
        
        logger.info(f"[{analysis_id}] Phase 2 completed - Strategy determined and nutrition refined")
        
        # === Nutrition Calculation Phase: 最終栄養価計算 ===
        logger.info(f"[{analysis_id}] Nutrition Calculation Phase: Final nutrition computation")
        
        # Phase 2の結果をベースに栄養計算を実行
        final_result = phase2_result.copy()
        
        # 各料理の栄養価を計算
        for dish in final_result.get("dishes", []):
            calculation_strategy = dish.get("calculation_strategy", "ingredient_level")
            
            if calculation_strategy == "ingredient_level":
                # 食材レベルの計算
                total_calories = 0.0
                total_protein = 0.0
                total_carbs = 0.0
                total_fat = 0.0
                
                for ingredient in dish.get("ingredients", []):
                    fdc_id = ingredient.get("fdc_id")
                    weight_g = 0.0
                    
                    # Phase 1から重量を取得
                    for phase1_dish in phase1_result.get("dishes", []):
                        if phase1_dish["dish_name"] == dish["dish_name"]:
                            for phase1_ingredient in phase1_dish.get("ingredients", []):
                                if phase1_ingredient["ingredient_name"] == ingredient["ingredient_name"]:
                                    weight_g = phase1_ingredient["weight_g"]
                                    break
                            break
                    
                    ingredient["weight_g"] = weight_g
                    
                    # USDAから栄養データを取得
                    if fdc_id:
                        try:
                            nutrition_data = await usda_service.get_food_details_for_nutrition(fdc_id)
                            if nutrition_data:
                                ingredient["key_nutrients_per_100g"] = nutrition_data
                                
                                # 実際の栄養価を計算 (重量 * 100gあたり栄養価 / 100)
                                multiplier = weight_g / 100.0
                                actual_calories = (nutrition_data.get("calories_kcal", 0) or 0) * multiplier
                                actual_protein = (nutrition_data.get("protein_g", 0) or 0) * multiplier
                                actual_carbs = (nutrition_data.get("carbohydrates_g", 0) or 0) * multiplier
                                actual_fat = (nutrition_data.get("fat_g", 0) or 0) * multiplier
                                
                                ingredient["actual_nutrients"] = {
                                    "calories_kcal": round(actual_calories, 2),
                                    "protein_g": round(actual_protein, 2),
                                    "carbohydrates_g": round(actual_carbs, 2),
                                    "fat_g": round(actual_fat, 2)
                                }
                                
                                # 料理全体の栄養価に加算
                                total_calories += actual_calories
                                total_protein += actual_protein
                                total_carbs += actual_carbs
                                total_fat += actual_fat
                                
                                logger.debug(f"[{analysis_id}] Calculated nutrition for {ingredient['ingredient_name']}: {actual_calories:.2f} kcal")
                            else:
                                logger.warning(f"[{analysis_id}] No nutrition data for FDC ID {fdc_id}")
                                ingredient["key_nutrients_per_100g"] = None
                                ingredient["actual_nutrients"] = None
                        except Exception as e:
                            logger.error(f"[{analysis_id}] Error getting nutrition data for FDC ID {fdc_id}: {e}")
                            ingredient["key_nutrients_per_100g"] = None
                            ingredient["actual_nutrients"] = None
                    else:
                        ingredient["key_nutrients_per_100g"] = None
                        ingredient["actual_nutrients"] = None
                
                # 料理全体の栄養価を設定
                dish["dish_total_actual_nutrients"] = {
                    "calories_kcal": round(total_calories, 2),
                    "protein_g": round(total_protein, 2),
                    "carbohydrates_g": round(total_carbs, 2),
                    "fat_g": round(total_fat, 2)
                }
                
            elif calculation_strategy == "dish_level":
                # 料理レベルの計算
                dish_fdc_id = dish.get("fdc_id")
                dish_weight = sum(
                    next((phase1_ingredient["weight_g"] for phase1_dish in phase1_result.get("dishes", [])
                          if phase1_dish["dish_name"] == dish["dish_name"]
                          for phase1_ingredient in phase1_dish.get("ingredients", [])), 0)
                    for _ in [None]  # 単一の合計重量計算
                )
                
                if dish_fdc_id and dish_weight > 0:
                    try:
                        nutrition_data = await usda_service.get_food_details_for_nutrition(dish_fdc_id)
                        if nutrition_data:
                            dish["key_nutrients_per_100g"] = nutrition_data
                            
                            # 料理全体の栄養価を計算
                            multiplier = dish_weight / 100.0
                            dish["dish_total_actual_nutrients"] = {
                                "calories_kcal": round((nutrition_data.get("calories_kcal", 0) or 0) * multiplier, 2),
                                "protein_g": round((nutrition_data.get("protein_g", 0) or 0) * multiplier, 2),
                                "carbohydrates_g": round((nutrition_data.get("carbohydrates_g", 0) or 0) * multiplier, 2),
                                "fat_g": round((nutrition_data.get("fat_g", 0) or 0) * multiplier, 2)
                            }
                        else:
                            dish["dish_total_actual_nutrients"] = {"calories_kcal": 0, "protein_g": 0, "carbohydrates_g": 0, "fat_g": 0}
                    except Exception as e:
                        logger.error(f"[{analysis_id}] Error getting dish nutrition data for FDC ID {dish_fdc_id}: {e}")
                        dish["dish_total_actual_nutrients"] = {"calories_kcal": 0, "protein_g": 0, "carbohydrates_g": 0, "fat_g": 0}
                else:
                    dish["dish_total_actual_nutrients"] = {"calories_kcal": 0, "protein_g": 0, "carbohydrates_g": 0, "fat_g": 0}
        
        # 食事全体の栄養価を計算
        meal_total_calories = 0.0
        meal_total_protein = 0.0
        meal_total_carbs = 0.0
        meal_total_fat = 0.0
        
        for dish in final_result.get("dishes", []):
            dish_nutrients = dish.get("dish_total_actual_nutrients", {})
            meal_total_calories += dish_nutrients.get("calories_kcal", 0)
            meal_total_protein += dish_nutrients.get("protein_g", 0)
            meal_total_carbs += dish_nutrients.get("carbohydrates_g", 0)
            meal_total_fat += dish_nutrients.get("fat_g", 0)
        
        final_result["total_meal_nutrients"] = {
            "calories_kcal": round(meal_total_calories, 2),
            "protein_g": round(meal_total_protein, 2),
            "carbohydrates_g": round(meal_total_carbs, 2),
            "fat_g": round(meal_total_fat, 2)
        }
        
        logger.info(f"[{analysis_id}] Nutrition Calculation completed - Total calories: {meal_total_calories:.2f} kcal")
        

        
        # === 結果の統合と保存 ===
        complete_result = {
            "analysis_id": analysis_id,
            "phase1_result": phase1_result,
            "usda_matches_count": len(usda_matches),
            "usda_matches": usda_matches,
            "phase2_result": phase2_result,
            "final_nutrition_result": final_result,
            "processing_summary": {
                "total_dishes": len(final_result.get("dishes", [])),
                "total_ingredients": sum(len(dish.get("ingredients", [])) for dish in final_result.get("dishes", [])),
                "usda_match_rate": f"{len(usda_matches)}/{len(all_ingredients)} ({len(usda_matches)/len(all_ingredients)*100:.1f}%)" if all_ingredients else "0/0 (0%)",
                "total_calories": final_result.get("total_meal_nutrients", {}).get("calories_kcal", 0),
                "pipeline_status": "completed"
            }
        }
        
        # 結果の保存
        saved_file = None
        if save_results:
            saved_file = save_analysis_result(complete_result, analysis_id)
            complete_result["saved_to"] = saved_file
        
        logger.info(f"[{analysis_id}] Complete analysis pipeline finished successfully")
        
        return JSONResponse(
            status_code=200,
            content=complete_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{analysis_id}] Complete analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Complete analysis failed: {str(e)}"
        )

@router.get("/results")
async def list_saved_results():
    """保存された分析結果の一覧を取得"""
    try:
        results = []
        for file_path in RESULTS_DIR.glob("meal_analysis_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append({
                        "filename": file_path.name,
                        "analysis_id": data.get("analysis_id"),
                        "timestamp": data.get("metadata", {}).get("timestamp"),
                        "summary": data.get("processing_summary", {}),
                        "file_path": str(file_path)
                    })
            except Exception as e:
                logger.error(f"Error reading result file {file_path}: {e}")
                continue
        
        # タイムスタンプでソート（新しい順）
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "total_results": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Failed to list saved results: {e}")
        raise HTTPException(status_code=500, detail="Failed to list saved results")

@router.get("/results/{analysis_id}")
async def get_saved_result(analysis_id: str):
    """特定の分析結果を取得"""
    try:
        # analysis_idに一致するファイルを検索
        matching_files = list(RESULTS_DIR.glob(f"meal_analysis_{analysis_id}_*.json"))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail=f"Analysis ID '{analysis_id}' not found")
        
        # 最新のファイルを取得（複数ある場合）
        latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        return result_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get saved result for ID {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get saved result") 