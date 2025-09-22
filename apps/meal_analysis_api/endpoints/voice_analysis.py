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

from apps.meal_analysis_api.models.voice_analysis_models import (
    VoiceAnalysisInput,
    VoiceCompleteAnalysisResponse,
    VoiceAnalysisErrorResponse,
    VoiceAnalysisErrorCodes
)
from apps.meal_analysis_api.models.meal_analysis_models import SimplifiedCompleteAnalysisResponse
from shared.components.phase1_speech_component import Phase1SpeechComponent
from shared.components.advanced_nutrition_search_component import AdvancedNutritionSearchComponent
from shared.components.nutrition_calculation_component import NutritionCalculationComponent
from shared.models.nutrition_search_models import NutritionQueryInput
from shared.models.nutrition_calculation_models import NutritionCalculationInput
from shared.pipeline.result_manager import ResultManager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/voice", response_model=SimplifiedCompleteAnalysisResponse)
async def analyze_meal_from_voice(
    audio: UploadFile = File(...),
    llm_model_id: Optional[str] = Form(None),
    language_code: str = Form("en-US"),
    optional_text: Optional[str] = Form(None),
    temperature: Optional[float] = Form(0.0),
    seed: Optional[int] = Form(123456),
    test_execution: bool = Form(False),
    test_results_dir: Optional[str] = Form(None),
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
        optional_text: 追加のテキスト情報（英語想定）- 音声と併せて分析に使用
                      例: "This is a homemade breakfast", "Restaurant meal with extra cheese"
        temperature: AI推論のランダム性制御 (0.0-1.0, デフォルト: 0.0 - 決定的)
        seed: 再現性のためのシード値 (デフォルト: 123456)
        test_execution: テスト実行モード（デフォルト: False）
        test_results_dir: テスト結果保存先ディレクトリ（テスト実行時のみ）
        save_detailed_logs: 詳細ログ保存（デフォルト: True）

    Returns:
        完全な栄養分析結果（画像分析と同一フォーマット）

    Raises:
        HTTPException: 各種エラー（400: 不正入力, 500: 処理失敗）
    """
    analysis_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()

    logger.info(f"[{analysis_id}] Starting voice meal analysis (language: {language_code}, temperature: {temperature}, seed: {seed})")
    if optional_text:
        logger.info(f"[{analysis_id}] Optional text provided: '{optional_text[:50]}{'...' if len(optional_text) > 50 else ''}'")

    try:
        # Step 1: 入力検証
        await _validate_audio_input(audio)

        # temperature パラメータの範囲検証
        if temperature is not None and (temperature < 0.0 or temperature > 1.0):
            raise HTTPException(
                status_code=400,
                detail={"code": VoiceAnalysisErrorCodes.INVALID_PARAMETERS, "message": "temperature must be between 0.0 and 1.0"}
            )

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
        if save_detailed_logs:
            result_manager = ResultManager()
            if test_execution and test_results_dir:
                result_manager.initialize_session(analysis_id, test_results_dir)
            else:
                result_manager.initialize_session(analysis_id)
        else:
            result_manager = None

        # Phase1Speechコンポーネントの実行
        phase1_speech_component = Phase1SpeechComponent()
        voice_input = VoiceAnalysisInput(
            audio_bytes=audio_data,
            audio_mime_type=audio.content_type or "audio/wav",
            llm_model_id=llm_model_id,
            language_code=language_code,
            optional_text=optional_text,  # 追加テキスト情報
            temperature=temperature,       # ランダム性制御
            seed=seed                     # 再現性制御
        )

        # Phase1の詳細ログを作成
        phase1_log = result_manager.create_execution_log("Phase1SpeechComponent", f"{analysis_id}_phase1_speech") if result_manager else None

        # 音声分析実行
        phase1_result = await phase1_speech_component.execute(
            input_data=voice_input,
            execution_log=phase1_log,
            language_code=language_code,
            llm_model_id=llm_model_id,
            temperature=temperature,
            seed=seed
        )

        logger.info(f"[{analysis_id}] Phase 1 completed - Detected {len(phase1_result.dishes)} dishes")

        # ResultManagerにPhase1結果を追加（音声データを含む）
        if result_manager:
            # 音声テキスト変換データを含むPhase1結果を構築
            phase1_data = {
                "detected_food_items": [
                    {
                        "item_name": item.item_name,
                        "confidence": item.confidence,
                        "attributes": [
                            {
                                "type": attr.type.value if hasattr(attr.type, 'value') else str(attr.type),
                                "value": attr.value,
                                "confidence": attr.confidence
                            }
                            for attr in item.attributes
                        ],
                        "brand": item.brand or "",
                        "category_hints": item.category_hints,
                        "negative_cues": item.negative_cues
                    }
                    for item in phase1_result.detected_food_items
                ],
                "dishes": [
                    {
                        "dish_name": dish.dish_name,
                        "confidence": dish.confidence,
                        "ingredients": [
                            {
                                "ingredient_name": ing.ingredient_name,
                                "confidence": ing.confidence,
                                "weight_g": ing.weight_g
                            }
                            for ing in dish.ingredients
                        ],
                        "attributes": [
                            {
                                "type": attr.type.value if hasattr(attr.type, 'value') else str(attr.type),
                                "value": attr.value,
                                "confidence": attr.confidence
                            }
                            for attr in dish.detected_attributes
                        ]
                    }
                    for dish in phase1_result.dishes
                ],
                "analysis_confidence": phase1_result.analysis_confidence,
                "processing_notes": phase1_result.processing_notes,
                # 音声入力データを追加
                "input_data": {
                    "audio_bytes": len(audio_data),  # バイト数のみ保存（実際のデータは大きすぎるため）
                    "audio_mime_type": audio.content_type or "audio/wav",
                    "language_code": language_code,
                    "llm_model_id": llm_model_id,
                    "optional_text": optional_text,
                    "temperature": temperature,
                    "seed": seed
                },
                # 音声テキスト変換結果を追加（Phase1Speechから取得）
                "processing_details": {}
            }
            
            # Phase1SpeechComponentから音声認識結果を取得
            if hasattr(phase1_log, 'get_speech_transcription'):
                speech_transcription = phase1_log.get_speech_transcription()
                if speech_transcription:
                    phase1_data["processing_details"]["speech_recognition_result"] = speech_transcription
            
            # 代替手段：Phase1Speechの実行ログから音声認識結果を抽出
            if phase1_log and hasattr(phase1_log, 'logs'):
                for log_entry in phase1_log.logs:
                    if "Speech recognition successful:" in log_entry.get("message", ""):
                        # ログメッセージから音声認識結果を抽出
                        message = log_entry["message"]
                        if "'" in message:
                            transcription = message.split("'")[1]
                            phase1_data["processing_details"]["speech_recognition_result"] = transcription
                            break
            
            result_manager.add_phase_result("Phase1SpeechComponent", phase1_data)

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

        # ResultManagerに栄養検索結果を追加
        if result_manager:
            # 安全な方式でmatchesを処理
            matches_data = []
            try:
                for match in nutrition_search_result.matches:
                    if hasattr(match, 'query_term'):
                        # 正常なオブジェクトの場合
                        match_data = {
                            "query_term": match.query_term,
                            "matched_food": getattr(match, 'matched_food', str(match)),
                            "confidence_score": getattr(match, 'confidence_score', 0.0),
                            "source_database": getattr(match, 'source_database', 'unknown'),
                            "nutrition_per_100g": getattr(match, 'nutrition_per_100g', {})
                        }
                    else:
                        # 文字列または他の形式の場合
                        match_data = {
                            "query_term": str(match),
                            "matched_food": str(match),
                            "confidence_score": 1.0,
                            "source_database": "elasticsearch",
                            "nutrition_per_100g": {}
                        }
                    matches_data.append(match_data)
            except Exception as e:
                logger.warning(f"Error processing matches: {e}, using simplified format")
                matches_data = [{"query_term": str(match), "matched_food": str(match)} for match in nutrition_search_result.matches]
            
            nutrition_search_data = {
                "matches_count": len(nutrition_search_result.matches),
                "match_rate": nutrition_search_result.get_match_rate(),
                "search_summary": nutrition_search_result.search_summary,
                "search_method": "elasticsearch",
                "matches": matches_data
            }
            result_manager.add_phase_result("AdvancedNutritionSearchComponent", nutrition_search_data)

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

        # ResultManagerに栄養計算結果を追加
        if result_manager:
            nutrition_calculation_data = {
                "dishes": [
                    {
                        "dish_name": dish.dish_name,
                        "confidence": dish.confidence,
                        "ingredients": [
                            {
                                "ingredient_name": ing.ingredient_name,
                                "weight_g": ing.weight_g,
                                "nutrition_per_100g": ing.nutrition_per_100g,
                                "calculated_nutrition": {
                                    "calories": ing.calculated_nutrition.calories,
                                    "protein": ing.calculated_nutrition.protein,
                                    "fat": ing.calculated_nutrition.fat,
                                    "carbs": ing.calculated_nutrition.carbs,
                                    "fiber": ing.calculated_nutrition.fiber,
                                    "sugar": ing.calculated_nutrition.sugar,
                                    "sodium": ing.calculated_nutrition.sodium
                                },
                                "source_db": ing.source_db,
                                "calculation_notes": ing.calculation_notes
                            }
                            for ing in dish.ingredients
                        ],
                        "total_nutrition": {
                            "calories": dish.total_nutrition.calories,
                            "protein": dish.total_nutrition.protein,
                            "fat": dish.total_nutrition.fat,
                            "carbs": dish.total_nutrition.carbs,
                            "fiber": dish.total_nutrition.fiber,
                            "sugar": dish.total_nutrition.sugar,
                            "sodium": dish.total_nutrition.sodium
                        },
                        "calculation_metadata": dish.calculation_metadata
                    }
                    for dish in nutrition_calculation_result.meal_nutrition.dishes
                ],
                "total_nutrition": {
                    "calories": nutrition_calculation_result.meal_nutrition.total_nutrition.calories,
                    "protein": nutrition_calculation_result.meal_nutrition.total_nutrition.protein,
                    "fat": nutrition_calculation_result.meal_nutrition.total_nutrition.fat,
                    "carbs": nutrition_calculation_result.meal_nutrition.total_nutrition.carbs,
                    "fiber": nutrition_calculation_result.meal_nutrition.total_nutrition.fiber,
                    "sugar": nutrition_calculation_result.meal_nutrition.total_nutrition.sugar,
                    "sodium": nutrition_calculation_result.meal_nutrition.total_nutrition.sodium
                },
                "calculation_summary": nutrition_calculation_result.meal_nutrition.calculation_summary,
                "warnings": nutrition_calculation_result.meal_nutrition.warnings,
                "match_rate_percent": nutrition_search_result.get_match_rate() * 100,
                "search_method": "elasticsearch"
            }
            result_manager.add_phase_result("NutritionCalculationComponent", nutrition_calculation_data)

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
                "total_calories": nutrition_calculation_result.meal_nutrition.total_nutrition.calories,
                "optional_text_used": optional_text,
                "temperature": temperature,
                "seed": seed
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

    # 料理情報を構築（実際のレスポンス構造に合わせて修正）
    dishes = []
    for dish in nutrition_calculation_result.meal_nutrition.dishes:
        # 食材詳細リストを構築
        ingredients = []
        for ing in dish.ingredients:
            ingredient_data = {
                "ingredient_name": ing.ingredient_name,
                "weight_g": ing.weight_g,
                "nutrition_per_100g": ing.nutrition_per_100g,
                "calculated_nutrition": {
                    "calories": ing.calculated_nutrition.calories,
                    "protein": ing.calculated_nutrition.protein,
                    "fat": ing.calculated_nutrition.fat,
                    "carbs": ing.calculated_nutrition.carbs,
                    "fiber": ing.calculated_nutrition.fiber,
                    "sugar": ing.calculated_nutrition.sugar,
                    "sodium": ing.calculated_nutrition.sodium
                },
                "source_db": ing.source_db,
                "calculation_notes": ing.calculation_notes
            }
            ingredients.append(ingredient_data)

        dish_data = {
            "dish_name": dish.dish_name,
            "confidence": dish.confidence,
            "ingredients": ingredients,
            "total_nutrition": {
                "calories": dish.total_nutrition.calories,
                "protein": dish.total_nutrition.protein,
                "fat": dish.total_nutrition.fat,
                "carbs": dish.total_nutrition.carbs,
                "fiber": dish.total_nutrition.fiber,
                "sugar": dish.total_nutrition.sugar,
                "sodium": dish.total_nutrition.sodium
            },
            "calculation_metadata": dish.calculation_metadata
        }
        dishes.append(dish_data)

    # 総栄養価
    total_nutrition = {
        "calories": nutrition_calculation_result.meal_nutrition.total_nutrition.calories,
        "protein": nutrition_calculation_result.meal_nutrition.total_nutrition.protein,
        "fat": nutrition_calculation_result.meal_nutrition.total_nutrition.fat,
        "carbs": nutrition_calculation_result.meal_nutrition.total_nutrition.carbs,
        "fiber": nutrition_calculation_result.meal_nutrition.total_nutrition.fiber,
        "sugar": nutrition_calculation_result.meal_nutrition.total_nutrition.sugar,
        "sodium": nutrition_calculation_result.meal_nutrition.total_nutrition.sodium
    }

    # 使用モデル決定（音声分析ではNLUでLLMを使用）
    from shared.config.settings import get_settings
    settings = get_settings()
    ai_model_used = llm_model_id or settings.DEEPINFRA_MODEL_ID

    return SimplifiedCompleteAnalysisResponse(
        analysis_id=analysis_id,
        input_type="voice",  # 音声分析特有のフィールド
        total_dishes=len(dishes),
        total_ingredients=sum(len(dish["ingredients"]) for dish in dishes),
        processing_time_seconds=processing_time,
        dishes=dishes,
        total_nutrition=total_nutrition,
        ai_model_used=ai_model_used,
        match_rate_percent=nutrition_search_result.get_match_rate() * 100,
        search_method="elasticsearch"
    )