"""
音声分析用のPydanticモデル

音声入力から食事分析までのデータモデルを定義します。
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class VoiceAnalysisInput(BaseModel):
    """音声分析の入力モデル"""
    model_config = {"protected_namespaces": ()}

    audio_bytes: bytes = Field(..., description="音声バイナリデータ")
    audio_mime_type: str = Field(..., description="音声ファイルのMIMEタイプ")
    llm_model_id: Optional[str] = Field(None, description="使用するLLMモデルID")
    language_code: str = Field("en-US", description="音声認識言語コード")


class SpeechRecognitionResult(BaseModel):
    """音声認識結果モデル"""
    model_config = {"protected_namespaces": ()}

    transcript: str = Field(..., description="認識されたテキスト")
    confidence: float = Field(..., description="認識信頼度", ge=0.0, le=1.0)
    language_detected: str = Field(..., description="検出された言語")
    processing_time_ms: float = Field(..., description="処理時間（ミリ秒）")


class VoiceExtractedFood(BaseModel):
    """音声から抽出された食品情報"""
    model_config = {"protected_namespaces": ()}

    ingredient_name: str = Field(..., description="食材名")
    weight_g: float = Field(..., description="重量（グラム）", gt=0)
    confidence: Optional[float] = Field(None, description="抽出信頼度", ge=0.0, le=1.0)


class VoiceExtractedDish(BaseModel):
    """音声から抽出された料理情報"""
    model_config = {"protected_namespaces": ()}

    dish_name: str = Field(..., description="料理名")
    confidence: float = Field(..., description="識別信頼度", ge=0.0, le=1.0)
    ingredients: List[VoiceExtractedFood] = Field(..., description="食材リスト")
    estimated_serving_size: Optional[str] = Field(None, description="推定サービングサイズ")


class VoiceNLUResult(BaseModel):
    """音声NLU処理結果モデル"""
    model_config = {"protected_namespaces": ()}

    original_text: str = Field(..., description="元のテキスト")
    dishes: List[VoiceExtractedDish] = Field(..., description="抽出された料理リスト")
    llm_model_used: str = Field(..., description="使用されたLLMモデル")
    processing_time_ms: float = Field(..., description="処理時間（ミリ秒）")
    extraction_confidence: float = Field(..., description="全体的な抽出信頼度", ge=0.0, le=1.0)


class VoiceAnalysisOutput(BaseModel):
    """音声分析の最終出力モデル"""
    model_config = {"protected_namespaces": ()}

    analysis_id: str = Field(..., description="分析セッションID")
    speech_recognition: SpeechRecognitionResult = Field(..., description="音声認識結果")
    nlu_result: VoiceNLUResult = Field(..., description="NLU処理結果")
    total_processing_time_ms: float = Field(..., description="総処理時間（ミリ秒）")
    warnings: List[str] = Field(default_factory=list, description="警告メッセージ")


class VoiceCompleteAnalysisResponse(BaseModel):
    """音声入力完全分析レスポンス（既存APIレスポンスと統一）"""
    model_config = {"protected_namespaces": ()}

    analysis_id: str = Field(..., description="分析セッションID")
    input_type: str = Field(default="voice", description="入力タイプ")

    # 音声固有情報
    speech_recognition: SpeechRecognitionResult = Field(..., description="音声認識結果")

    # 既存APIとの統一フォーマット
    total_dishes: int = Field(..., description="検出された料理数")
    total_ingredients: int = Field(..., description="総食材数")
    processing_time_seconds: float = Field(..., description="処理時間（秒）")

    dishes: List[Dict[str, Any]] = Field(..., description="料理詳細リスト")
    total_nutrition: Dict[str, float] = Field(..., description="総栄養価")

    ai_model_used: str = Field(..., description="使用されたAIモデル")
    match_rate_percent: float = Field(..., description="栄養検索マッチ率（%）")
    search_method: str = Field(..., description="検索方法")

    warnings: List[str] = Field(default_factory=list, description="警告メッセージ")


class VoiceAnalysisErrorResponse(BaseModel):
    """音声分析エラーレスポンス"""
    model_config = {"protected_namespaces": ()}

    error: Dict[str, str] = Field(..., description="エラー情報")
    analysis_id: Optional[str] = Field(None, description="分析セッションID（利用可能な場合）")
    timestamp: str = Field(..., description="エラー発生時刻")


# 共通エラーコード定義
class VoiceAnalysisErrorCodes:
    """音声分析エラーコード定数"""

    INVALID_AUDIO_FILE = "INVALID_AUDIO_FILE"
    EMPTY_AUDIO_FILE = "EMPTY_AUDIO_FILE"
    UNSUPPORTED_AUDIO_FORMAT = "UNSUPPORTED_AUDIO_FORMAT"
    SPEECH_TO_TEXT_FAILED = "SPEECH_TO_TEXT_FAILED"
    NO_SPEECH_DETECTED = "NO_SPEECH_DETECTED"
    LLM_EXTRACTION_FAILED = "LLM_EXTRACTION_FAILED"
    NUTRITION_SEARCH_FAILED = "NUTRITION_SEARCH_FAILED"
    NUTRITION_CALCULATION_FAILED = "NUTRITION_CALCULATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"