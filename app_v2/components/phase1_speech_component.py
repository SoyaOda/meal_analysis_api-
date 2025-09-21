"""
Phase1Speech: 音声分析コンポーネント

音声データから料理・食材情報を抽出し、既存のPhase1Componentと同等の出力を生成します。
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, Any

from ..components.base import BaseComponent, ComponentError
from ..models.phase1_models import Phase1Input, Phase1Output, Dish, Ingredient
from ..models.voice_analysis_models import VoiceAnalysisInput, VoiceAnalysisOutput
from ..services.speech_service import SpeechService
from ..services.nlu_service import NLUService

logger = logging.getLogger(__name__)


class Phase1SpeechComponent(BaseComponent):
    """
    Phase1Speech: 音声分析コンポーネント

    音声認識 + NLU処理により、音声から料理・食材情報を抽出し、
    既存のPhase1Componentと同等のPhase1Outputを生成します。
    """

    def __init__(self, speech_service: Optional[SpeechService] = None, nlu_service: Optional[NLUService] = None):
        super().__init__("Phase1SpeechComponent")

        # サービスの初期化（依存性注入）
        self.speech_service = speech_service or SpeechService()
        self.nlu_service = nlu_service or NLUService()

        logger.info("Phase1SpeechComponent initialized successfully")

    async def execute(
        self,
        input_data: VoiceAnalysisInput,
        execution_log: Optional = None,
        language_code: str = "en-US",
        llm_model_id: Optional[str] = None
    ) -> Phase1Output:
        """
        音声分析専用のexecuteメソッド

        Args:
            input_data: VoiceAnalysisInput (音声バイナリデータ等)
            execution_log: 詳細実行ログ（オプション）
            language_code: 音声認識言語コード
            llm_model_id: 使用するLLMモデルID

        Returns:
            Phase1Output: 既存システムと同等の構造化分析結果
        """
        self.execution_count += 1
        execution_id = f"{self.component_name}_{self.execution_count}"
        analysis_id = str(uuid.uuid4())[:8]

        # 詳細ログの設定
        if execution_log:
            self.current_execution_log = execution_log
            self.current_execution_log.set_input({
                "audio_size_bytes": len(input_data.audio_bytes),
                "audio_mime_type": input_data.audio_mime_type,
                "language_code": language_code,
                "llm_model_id": llm_model_id
            })

        self.logger.info(f"[{execution_id}] Starting {self.component_name} processing (language: {language_code})")

        try:
            start_time = datetime.now()
            result = await self.process(input_data, language_code=language_code, llm_model_id=llm_model_id)
            end_time = datetime.now()

            processing_time = (end_time - start_time).total_seconds()
            self.logger.info(f"[{execution_id}] {self.component_name} completed in {processing_time:.2f}s")

            # 詳細ログに出力データを記録
            if self.current_execution_log:
                self.current_execution_log.set_output({
                    "detected_dishes_count": len(result.dishes),
                    "total_ingredients_count": sum(len(dish.ingredients) for dish in result.dishes),
                    "analysis_confidence": result.analysis_confidence,
                    "processing_time_seconds": processing_time
                })
                self.current_execution_log.finalize()

            return result

        except Exception as e:
            self.logger.error(f"[{execution_id}] {self.component_name} failed: {str(e)}", exc_info=True)

            # 詳細ログにエラーを記録
            if self.current_execution_log:
                self.current_execution_log.add_error(str(e))
                self.current_execution_log.finalize()

            raise ComponentError(f"{self.component_name} processing failed: {str(e)}") from e
        finally:
            self.current_execution_log = None

    async def process(
        self,
        input_data: VoiceAnalysisInput,
        language_code: str = "en-US",
        llm_model_id: Optional[str] = None
    ) -> Phase1Output:
        """
        音声分析の主処理

        Args:
            input_data: VoiceAnalysisInput
            language_code: 音声認識言語コード
            llm_model_id: 使用するLLMモデルID

        Returns:
            Phase1Output: 既存システムと同等の構造化分析結果
        """
        self.logger.info("Starting speech analysis for food extraction")

        # Step 1: 音声フォーマット検出
        audio_encoding, sample_rate = self.speech_service.detect_audio_format(input_data.audio_bytes)
        self.log_processing_detail("detected_audio_format", {"encoding": audio_encoding, "sample_rate": sample_rate})

        # Step 2: 音声認識（Speech-to-Text）
        self.logger.info("Step 1: Speech-to-Text conversion")
        try:
            # MP3の場合は明示的にMP3として指定
            if input_data.audio_mime_type and "mp3" in input_data.audio_mime_type.lower():
                audio_encoding = "MP3"

            transcript = await self.speech_service.transcribe_audio(
                audio_data=input_data.audio_bytes,
                sample_rate=sample_rate,
                encoding=audio_encoding,
                language_code=language_code
            )
            self.log_processing_detail("speech_recognition_result", transcript)

        except Exception as e:
            self.logger.error(f"Speech recognition failed: {e}")
            raise ComponentError(f"Speech-to-text conversion failed: {e}") from e

        if not transcript.strip():
            error_msg = "No speech detected in audio data"
            self.logger.error(error_msg)
            raise ComponentError(error_msg)

        # Step 3: NLU処理（食品抽出）
        self.logger.info("Step 2: NLU processing for food extraction")
        try:
            nlu_result = await self.nlu_service.extract_foods_from_text(
                text=transcript,
                model_id=llm_model_id
            )
            self.log_processing_detail("nlu_extraction_result", nlu_result)

        except Exception as e:
            self.logger.error(f"NLU food extraction failed: {e}")
            raise ComponentError(f"Food extraction from text failed: {e}") from e

        # Step 4: 既存Phase1Output形式に変換
        self.logger.info("Step 3: Converting to Phase1Output format")
        try:
            phase1_output = self._convert_to_phase1_output(nlu_result, transcript)
            self.log_processing_detail("phase1_conversion_result", {
                "dishes_count": len(phase1_output.dishes),
                "total_ingredients": sum(len(dish.ingredients) for dish in phase1_output.dishes),
                "overall_confidence": phase1_output.analysis_confidence
            })

            self.log_reasoning(
                "speech_analysis_completion",
                f"Speech analysis completed: {len(phase1_output.dishes)} dishes identified "
                f"from transcript '{transcript[:100]}{'...' if len(transcript) > 100 else ''}'"
            )

            return phase1_output

        except Exception as e:
            self.logger.error(f"Phase1Output conversion failed: {e}")
            raise ComponentError(f"Output format conversion failed: {e}") from e

    def _convert_to_phase1_output(self, nlu_result: dict, original_transcript: str) -> Phase1Output:
        """
        NLU結果を既存Phase1Output形式に変換

        Args:
            nlu_result: NLUサービスからの結果
            original_transcript: 元の音声認識テキスト

        Returns:
            Phase1Output: 既存システムと同等の出力
        """
        dishes = []
        warnings = []

        # NLU結果から料理情報を抽出
        nlu_dishes = nlu_result.get("dishes", [])

        if not nlu_dishes:
            warnings.append("No dishes detected from speech input")
            # フォールバック：基本的な食事エントリを作成
            dishes.append(Dish(
                dish_name="Unspecified meal from voice",
                confidence=0.3,
                ingredients=[Ingredient(
                    ingredient_name="unknown food",
                    weight_g=100.0,
                    confidence=0.3
                )],
                detected_attributes=[]
            ))
        else:
            for dish_data in nlu_dishes:
                # 各料理の食材を変換
                ingredients = []
                for ingredient_data in dish_data.get("ingredients", []):
                    if "weight_g" not in ingredient_data:
                        self.logger.warning(f"Missing weight_g for ingredient: {ingredient_data}")
                        continue

                    ingredient = Ingredient(
                        ingredient_name=ingredient_data["ingredient_name"],
                        weight_g=float(ingredient_data["weight_g"]),
                        confidence=ingredient_data.get("confidence", 0.7),
                        detected_attributes=[]  # 音声からは詳細属性は取得困難
                    )
                    ingredients.append(ingredient)

                if ingredients:  # 有効な食材がある場合のみ追加
                    dish = Dish(
                        dish_name=dish_data["dish_name"],
                        confidence=dish_data.get("confidence", 0.7),
                        ingredients=ingredients,
                        detected_attributes=[]  # 音声からは詳細属性は取得困難
                    )
                    dishes.append(dish)

        # 全体的な信頼度を計算
        if dishes:
            overall_confidence = sum(dish.confidence for dish in dishes) / len(dishes)
        else:
            overall_confidence = 0.0

        # 処理ノートを生成
        processing_notes = [
            f"Voice analysis from transcript: '{original_transcript[:100]}{'...' if len(original_transcript) > 100 else ''}'",
            f"Detected {len(dishes)} dishes via speech recognition + NLU",
            f"Overall confidence: {overall_confidence:.2f}"
        ]

        return Phase1Output(
            detected_food_items=[],  # 音声分析では詳細な構造化アイテムは生成しない
            dishes=dishes,
            analysis_confidence=overall_confidence,
            processing_notes=processing_notes,
            warnings=warnings
        )