"""
音声分析API エンドポイント

音声データから食事分析を行うAPIエンドポイントを定義します。
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse

from ....models.voice_analysis_models import (
    VoiceAnalysisInput,
    VoiceCompleteAnalysisResponse,
    VoiceAnalysisErrorResponse,
    VoiceAnalysisErrorCodes
)
from ....models.meal_analysis_models import SimplifiedCompleteAnalysisResponse
from ....components.phase1_speech_component import Phase1SpeechComponent
from ....components.advanced_nutrition_search_component import AdvancedNutritionSearchComponent
from ....components.nutrition_calculation_component import NutritionCalculationComponent
from ....models.nutrition_search_models import NutritionQueryInput
from ....models.nutrition_calculation_models import NutritionCalculationInput
from ....pipeline.result_manager import ResultManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/voice", response_model=SimplifiedCompleteAnalysisResponse)
async def analyze_meal_from_voice(
    audio: UploadFile = File(...),
    llm_model_id: Optional[str] = Form(None),
    language_code: str = Form("en-US"),
    test_execution: bool = Form(False),
    save_detailed_logs: bool = Form(True)
) -> SimplifiedCompleteAnalysisResponse:
    """
    音声からの完全食事分析

    音声データを受け取り、音声認識→NLU処理→栄養検索→栄養計算の
    完全なパイプラインを実行して栄養分析結果を返します。

    Args:
        audio: 分析対象の音声ファイル（WAV, MP3, M4A, FLAC等）
        llm_model_id: 使用するLLMモデルID（オプション、デフォルト: gemma-3-27b-it）
        language_code: 音声認識言語コード（デフォルト: en-US）
        test_execution: テスト実行モード（デフォルト: False）
        save_detailed_logs: 詳細ログ保存（デフォルト: True）

    Returns:
        完全な栄養分析結果（画像分析と同一フォーマット）

    Raises:
        HTTPException: 各種エラー（400: 不正入力, 500: 処理失敗）
    """
    analysis_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()

    logger.info(f"[{analysis_id}] Starting voice meal analysis (language: {language_code})")

    try:
        # Step 1: 入力検証
        await _validate_audio_input(audio)

        # 音声データ読み込み
        audio_data = await audio.read()
        if not audio_data:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": VoiceAnalysisErrorCodes.EMPTY_AUDIO_FILE,
                    "message": "Audio file is empty"
                }
            )

        # Step 2: 音声分析（Phase1Speech）
        logger.info(f"[{analysis_id}] Phase 1: Voice analysis (Speech-to-Text + NLU)")

        # ResultManagerの初期化
        result_manager = ResultManager(analysis_id) if save_detailed_logs else None

        # Phase1Speechコンポーネントの実行
        phase1_speech_component = Phase1SpeechComponent()
        voice_input = VoiceAnalysisInput(
            audio_bytes=audio_data,
            audio_mime_type=audio.content_type or "audio/wav",
            llm_model_id=llm_model_id,
            language_code=language_code
        )

        # Phase1の詳細ログを作成
        phase1_log = result_manager.create_execution_log("Phase1SpeechComponent", f"{analysis_id}_phase1_speech") if result_manager else None

        # 音声分析実行
        phase1_result = await phase1_speech_component.execute(
            input_data=voice_input,
            execution_log=phase1_log,
            language_code=language_code,
            llm_model_id=llm_model_id
        )

        logger.info(f"[{analysis_id}] Phase 1 completed - Detected {len(phase1_result.dishes)} dishes")

        # Step 3: 栄養検索（既存コンポーネント再利用）
        logger.info(f"[{analysis_id}] Phase 2: Nutrition database search")

        nutrition_search_component = AdvancedNutritionSearchComponent()
        nutrition_search_input = NutritionQueryInput(
            ingredient_names=phase1_result.get_all_ingredient_names(),
            dish_names=phase1_result.get_all_dish_names(),
            preferred_source="advanced_search"
        )

        # 栄養検索の詳細ログを作成
        search_log = result_manager.create_execution_log("AdvancedNutritionSearchComponent", f"{analysis_id}_nutrition_search") if result_manager else None

        nutrition_search_result = await nutrition_search_component.process(nutrition_search_input)

        logger.info(f"[{analysis_id}] Phase 2 completed - {nutrition_search_result.get_match_rate():.1%} match rate")

        # Step 4: 栄養計算（既存コンポーネント再利用）
        logger.info(f"[{analysis_id}] Phase 3: Nutrition calculation")

        nutrition_calculation_component = NutritionCalculationComponent()
        nutrition_calculation_input = NutritionCalculationInput(
            phase1_result=phase1_result,
            nutrition_search_result=nutrition_search_result
        )

        # 栄養計算の詳細ログを作成
        calculation_log = result_manager.create_execution_log("NutritionCalculationComponent", f"{analysis_id}_nutrition_calculation") if result_manager else None

        nutrition_calculation_result = await nutrition_calculation_component.execute(nutrition_calculation_input, calculation_log)

        logger.info(f"[{analysis_id}] Phase 3 completed - {nutrition_calculation_result.meal_nutrition.total_nutrition.calories:.1f} kcal total")

        # Step 5: レスポンス構築
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # 画像分析と同一フォーマットのレスポンスを生成
        response = _build_unified_response(
            analysis_id=analysis_id,
            phase1_result=phase1_result,
            nutrition_calculation_result=nutrition_calculation_result,
            nutrition_search_result=nutrition_search_result,
            processing_time=processing_time,
            llm_model_id=llm_model_id
        )

        # 詳細ログの保存
        if result_manager:
            result_manager.set_final_result({
                "analysis_id": analysis_id,
                "input_type": "voice",
                "processing_time_seconds": processing_time,
                "total_dishes": len(phase1_result.dishes),
                "total_calories": nutrition_calculation_result.meal_nutrition.total_nutrition.calories
            })
            result_manager.finalize_pipeline()
            saved_files = result_manager.save_phase_results()
            logger.info(f"[{analysis_id}] Analysis logs saved to folder: {result_manager.get_analysis_folder_path()}")

        logger.info(f"[{analysis_id}] Voice meal analysis completed successfully in {processing_time:.2f}s")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{analysis_id}] Voice meal analysis failed: {str(e)}", exc_info=True)

        # エラー時もResultManagerを保存
        if 'result_manager' in locals() and result_manager:
            result_manager.set_final_result({
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "analysis_id": analysis_id
            })
            result_manager.finalize_pipeline()
            result_manager.save_phase_results()

        raise HTTPException(
            status_code=500,
            detail={
                "code": VoiceAnalysisErrorCodes.INTERNAL_ERROR,
                "message": f"Voice meal analysis failed: {str(e)}"
            }
        )


async def _validate_audio_input(audio: UploadFile) -> None:
    """WAV音声入力の検証"""
    # ファイル名チェック
    if not audio.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "code": VoiceAnalysisErrorCodes.INVALID_AUDIO_FILE,
                "message": "Audio filename is required"
            }
        )

    # WAV拡張子チェックのみ
    if not audio.filename.lower().endswith('.wav'):
        raise HTTPException(
            status_code=400,
            detail={
                "code": VoiceAnalysisErrorCodes.UNSUPPORTED_AUDIO_FORMAT,
                "message": "Only WAV format is supported"
            }
        )

    # MIMEタイプチェック（緩和版）- None の場合は拡張子チェックを優先
    if audio.content_type and audio.content_type not in [
        'audio/wav', 'audio/wave', 'audio/x-wav', 'audio/vnd.wave',
        'application/octet-stream'  # ブラウザがWAVを正しく認識しない場合
    ]:
        # MIMEタイプが設定されているが、WAVでもoctet-streamでもない場合のみエラー
        if not audio.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400,
                detail={
                    "code": VoiceAnalysisErrorCodes.INVALID_AUDIO_FILE,
                    "message": f"Uploaded file must be an audio file (received: {audio.content_type})"
                }
            )


def _build_unified_response(
    analysis_id: str,
    phase1_result,
    nutrition_calculation_result,
    nutrition_search_result,
    processing_time: float,
    llm_model_id: Optional[str]
) -> SimplifiedCompleteAnalysisResponse:
    """画像分析と同一フォーマットのレスポンスを構築"""

    # 料理情報を構築
    dishes = []
    for dish in nutrition_calculation_result.meal_nutrition.dishes:
        dish_data = {
            "dish_name": dish.dish_name,
            "confidence": dish.confidence,
            "ingredient_count": len(dish.ingredients),
            "ingredients": [
                {
                    "name": ing.ingredient_name,
                    "weight_g": ing.weight_g,
                    "calories": ing.calculated_nutrition.calories
                }
                for ing in dish.ingredients
            ],
            "total_calories": dish.total_nutrition.calories
        }
        dishes.append(dish_data)

    # 総栄養価
    total_nutrition = {
        "calories": nutrition_calculation_result.meal_nutrition.total_nutrition.calories,
        "protein": nutrition_calculation_result.meal_nutrition.total_nutrition.protein,
        "fat": nutrition_calculation_result.meal_nutrition.total_nutrition.fat,
        "carbs": nutrition_calculation_result.meal_nutrition.total_nutrition.carbs
    }

    # 使用モデル決定
    from ....config.settings import get_settings
    settings = get_settings()
    ai_model_used = llm_model_id or settings.DEEPINFRA_MODEL_ID

    return SimplifiedCompleteAnalysisResponse(
        analysis_id=analysis_id,
        total_dishes=len(dishes),
        total_ingredients=sum(len(dish["ingredients"]) for dish in dishes),
        processing_time_seconds=processing_time,
        dishes=dishes,
        total_nutrition=total_nutrition,
        ai_model_used=ai_model_used,
        match_rate_percent=nutrition_search_result.get_match_rate() * 100,
        search_method="elasticsearch"
    )