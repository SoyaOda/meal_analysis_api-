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

# 依存性注入
from ....dependencies import get_gemini_analyzer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/refine",
    response_model=MealAnalysisRefinementResponse,
    summary="食事分析結果をUSDAデータで精緻化 (Refine Meal Analysis with USDA Data)",
    description="画像と初期AI分析結果を基に、USDA食品データベースの情報を参照し、Gemini AIで再分析・精緻化します。"
)
async def refine_meal_analysis(
    settings: Annotated[Settings, Depends(get_settings)],
    image: Annotated[UploadFile, File(description="食事の画像ファイル。")],
    initial_analysis_data: Annotated[str, Form(description="フェーズ1APIが出力したJSONレスポンスの文字列。")],
    usda_service: Annotated[USDAService, Depends(get_usda_service)],
    gemini_service: Annotated[GeminiMealAnalyzer, Depends(get_gemini_analyzer)]
):
    """
    食事分析結果の精緻化エンドポイント
    
    1. 画像とフェーズ1の分析結果を受け取る
    2. 各食材についてUSDAデータベースを検索
    3. USDA候補情報と共にGeminiで再分析
    4. 精緻化された結果を返す
    """
    # 1. 画像バリデーション
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="無効な画像ファイル形式です。")
    
    try:
        image_bytes = await image.read()
        # ファイルサイズチェック（例: 10MB）
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="画像ファイルサイズが大きすぎます（最大10MB）。")
    except Exception as e:
        logger.error(f"Error reading image file: {e}")
        raise HTTPException(status_code=400, detail="画像ファイルの読み取りに失敗しました。")
    
    # 2. initial_analysis_dataをパース
    try:
        initial_analysis_dict = json.loads(initial_analysis_data)
        initial_analysis = InitialAnalysisData(**initial_analysis_dict)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="initial_analysis_dataが不正なJSON形式です。")
    except Exception as e:  # Pydanticバリデーションエラーなど
        logger.error(f"Validation error for initial_analysis_data: {e}")
        raise HTTPException(status_code=422, detail=f"initial_analysis_dataの形式エラー: {str(e)}")
    
    # 3. USDA候補情報を収集し、プロンプト用テキストを生成
    usda_candidates_prompt_segments = []
    # 各料理・材料についてUSDA検索結果を格納する辞書（後でkey_nutrients_per_100gを付与するため）
    all_usda_search_results_map: Dict[int, USDAServiceItem] = {}
    
    # データタイプの優先順位
    preferred_data_types = ["Foundation", "SR Legacy", "Branded"]
    
    for dish in initial_analysis.dishes:
        for ingredient in dish.ingredients:
            search_query = ingredient.ingredient_name
            logger.info(f"Searching USDA for ingredient: {search_query}")
            
            try:
                # USDA検索を実行
                usda_results: List[USDAServiceItem] = await usda_service.search_foods(
                    query=search_query,
                    data_types=preferred_data_types,
                    page_size=settings.USDA_SEARCH_CANDIDATES_LIMIT
                )
                
                if usda_results:
                    segment = f"食材「{search_query}」に対するUSDA候補:\n"
                    for i, item in enumerate(usda_results):
                        all_usda_search_results_map[item.fdc_id] = item  # 後で参照するために保存
                        
                        # プロンプトに含める栄養素情報を整形
                        nutrients_str_parts = []
                        for nutr in item.food_nutrients:
                            if nutr.name and nutr.amount is not None and nutr.unit_name:
                                # 栄養素名をわかりやすく変換
                                nutrient_display_name = _get_nutrient_display_name(nutr.name, nutr.nutrient_number)
                                nutrients_str_parts.append(f"{nutrient_display_name}: {nutr.amount}{nutr.unit_name}")
                        
                        nutrients_str = ", ".join(nutrients_str_parts) if nutrients_str_parts else "栄養素情報なし"
                        
                        segment += (
                            f"{i+1}. FDC ID: {item.fdc_id}, 名称: {item.description} ({item.data_type or 'N/A'}), "
                            f"栄養素(100gあたり): {nutrients_str}"
                        )
                        if item.brand_owner:
                            segment += f", ブランド: {item.brand_owner}"
                        if item.ingredients_text:  # Branded Foodsの原材料情報
                            segment += f", 原材料: {item.ingredients_text[:100]}..."  # 長すぎる場合は省略
                        segment += "\n"
                    
                    usda_candidates_prompt_segments.append(segment)
                else:
                    logger.warning(f"No USDA results found for ingredient: {search_query}")
                    usda_candidates_prompt_segments.append(f"食材「{search_query}」のUSDA候補は見つかりませんでした。\n")
                    
            except RuntimeError as e:  # USDAService内でのエラー
                logger.error(f"USDA search error for ingredient '{search_query}': {e}")
                # 一部のUSDA検索が失敗しても、他の情報でGeminiに判断させる
                usda_candidates_prompt_segments.append(f"食材「{search_query}」のUSDA候補検索中にエラーが発生しました: {str(e)}\n")
            except Exception as e:
                logger.error(f"Unexpected error during USDA search for '{search_query}': {e}")
                usda_candidates_prompt_segments.append(f"食材「{search_query}」のUSDA候補検索中に予期せぬエラー: {str(e)}\n")
    
    usda_candidates_prompt_text = "\n---\n".join(usda_candidates_prompt_segments) if usda_candidates_prompt_segments else "USDA候補情報はありませんでした。"
    
    # 4. Geminiサービス（フェーズ2用メソッド）を呼び出し
    try:
        logger.info("Calling Gemini for phase 2 analysis")
        refined_gemini_output_dict = await gemini_service.analyze_image_with_usda_context(
            image_bytes=image_bytes,
            image_mime_type=image.content_type,
            usda_candidates_text=usda_candidates_prompt_text,
            initial_ai_output_text=initial_analysis_data  # フェーズ1の出力をそのまま渡す
        )
        
        # 5. Gemini出力をパースし、必要に応じてkey_nutrients_per_100gを付与
        # Pydanticモデルでパースすることで、スキーマ通りの構造になっているか検証
        refined_analysis_response = MealAnalysisRefinementResponse(**refined_gemini_output_dict)
        
        # バックエンドで key_nutrients_per_100g を付与
        for dish_resp in refined_analysis_response.dishes:
            for ing_resp in dish_resp.ingredients:
                if ing_resp.fdc_id and ing_resp.fdc_id in all_usda_search_results_map:
                    usda_item = all_usda_search_results_map[ing_resp.fdc_id]
                    key_nutrients = {}
                    
                    # USDASearchResultItemPydantic.food_nutrients から必要なものを抽出
                    for nutr in usda_item.food_nutrients:
                        if nutr.name and nutr.amount is not None:
                            # 栄養素番号に基づいてキー名を決定
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
        
    except RuntimeError as e:  # GeminiサービスまたはUSDAサービスからのエラー
        logger.error(f"External service error: {e}")
        raise HTTPException(status_code=503, detail=f"外部サービス連携エラー: {str(e)}")
    except ValueError as e:  # JSONパースエラーなど
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=f"処理エラー: {str(e)}")
    except Exception as e:  # その他の予期せぬエラー
        logger.error(f"Unexpected error in refine_meal_analysis: {e}")
        raise HTTPException(status_code=500, detail=f"予期せぬ内部エラーが発生しました: {str(e)}")


def _get_nutrient_display_name(name: str, nutrient_number: Optional[str]) -> str:
    """
    栄養素名を日本語でわかりやすく表示するための変換
    """
    nutrient_mapping = {
        "208": "エネルギー",
        "203": "タンパク質", 
        "204": "脂質",
        "205": "炭水化物",
        "291": "食物繊維",
        "269": "糖質",
        "307": "ナトリウム"
    }
    
    if nutrient_number and nutrient_number in nutrient_mapping:
        return nutrient_mapping[nutrient_number]
    return name 