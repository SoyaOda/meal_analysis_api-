"""
Speech Service for Voice Input

DeepInfra Whisper API を使用した音声認識（STT）サービス
"""

import os
import io
import logging
import time
from typing import Optional, Tuple, Dict, Any
from enum import Enum
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class WhisperModel(Enum):
    """利用可能なWhisperモデル"""
    LARGE_V3 = "openai/whisper-large-v3"
    LARGE_V3_TURBO = "openai/whisper-large-v3-turbo"
    BASE = "openai/whisper-base"


class SpeechService:
    """
    DeepInfra Whisper API を使用した音声認識サービス

    対応フォーマット:
    - WAV (audio/wav, audio/x-wav)
    - MP3 (audio/mpeg)
    - FLAC (audio/flac)
    - OGG (audio/ogg)
    - M4A (audio/m4a)
    - WEBM (audio/webm)
    """

    # DeepInfra Whisper API endpoint
    API_URL = "https://api.deepinfra.com/v1/inference"

    # 対応フォーマットとMIMEタイプのマッピング
    SUPPORTED_FORMATS = {
        b"RIFF": ("wav", "audio/wav"),
        b"ID3": ("mp3", "audio/mpeg"),
        b"\xff\xfb": ("mp3", "audio/mpeg"),
        b"\xff\xfa": ("mp3", "audio/mpeg"),
        b"fLaC": ("flac", "audio/flac"),
        b"OggS": ("ogg", "audio/ogg"),
        b"\x00\x00\x00": ("m4a", "audio/m4a"),  # M4A/MP4 (ftyp box)
        b"\x1aE\xdf\xa3": ("webm", "audio/webm"),  # WebM
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        SpeechServiceを初期化

        Args:
            api_key: DeepInfra API Key（Noneの場合は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("DEEPINFRA_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPINFRA_API_KEY is required for speech recognition")

        # デフォルト設定 - ConfigManagerから取得
        from ..admin.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_config()
        self.default_model = config.voice.whisper_model

        logger.info(f"SpeechService initialized with model: {self.default_model}")

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "en",
        model: Optional[str] = None,
        temperature: float = 0.0,
        prompt: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        音声をテキストに変換

        Args:
            audio_data: 音声データ（バイト列）
            language: 言語コード（en, ja, etc.）
            model: Whisperモデル（Noneの場合はデフォルト）
            temperature: 生成温度
            prompt: オプションのプロンプト（文脈のヒント）

        Returns:
            (transcript, metadata) - 認識テキストとメタデータ

        Raises:
            ValueError: 音声フォーマットが不正な場合
            RuntimeError: API呼び出しに失敗した場合
        """
        start_time = time.time()

        # 音声フォーマットの検出
        audio_format, mime_type = self.detect_audio_format(audio_data)
        logger.info(f"Detected audio format: {audio_format} ({mime_type})")

        # モデル設定
        model = model or self.default_model

        # API URL
        api_url = f"{self.API_URL}/{model}"

        # API呼び出し（リトライロジック付き）
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        # 音声サイズのログ（デバッグ用）
        audio_size_kb = len(audio_data) / 1024
        logger.info(f"Sending audio to Whisper API: {audio_size_kb:.1f}KB, format={audio_format}, model={model}")

        result = await self._call_whisper_api_with_retry(
            api_url=api_url,
            audio_data=audio_data,
            audio_format=audio_format,
            mime_type=mime_type,
            language=language,
            temperature=temperature,
            prompt=prompt,
            headers=headers
        )

        # 処理時間
        processing_time = time.time() - start_time

        # 結果の解析
        transcript = result.get("text", "").strip()

        # メタデータ
        metadata = {
            "whisper_model": model,
            "audio_size_bytes": len(audio_data),
            "audio_format": audio_format,
            "language_requested": language,
            "language_detected": result.get("detected_language"),
            "stt_processing_time_seconds": round(processing_time, 2),
            "audio_duration_seconds": result.get("duration"),
        }

        logger.info(f"Transcription completed: '{transcript[:100]}...' in {processing_time:.2f}s")

        return transcript, metadata

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(RuntimeError),
        before_sleep=lambda retry_state: logger.warning(
            f"Whisper API call failed (attempt {retry_state.attempt_number}), retrying in {retry_state.next_action.sleep:.1f}s..."
        )
    )
    async def _call_whisper_api_with_retry(
        self,
        api_url: str,
        audio_data: bytes,
        audio_format: str,
        mime_type: str,
        language: str,
        temperature: float,
        prompt: Optional[str],
        headers: dict
    ) -> Dict[str, Any]:
        """
        リトライロジック付きのWhisper API呼び出し

        Args:
            api_url: API endpoint URL
            audio_data: 音声データ
            audio_format: 音声フォーマット
            mime_type: MIMEタイプ
            language: 言語コード
            temperature: 生成温度
            prompt: オプションのプロンプト
            headers: HTTPヘッダー

        Returns:
            API応答のJSONデータ

        Raises:
            RuntimeError: API呼び出しが3回失敗した場合
        """
        # FormDataは毎回再作成する必要がある（ストリームの再利用不可）
        form_data = aiohttp.FormData()
        form_data.add_field(
            "audio",
            io.BytesIO(audio_data),
            filename=f"audio.{audio_format}",
            content_type=mime_type
        )
        form_data.add_field("language", language)
        form_data.add_field("temperature", str(temperature))
        if prompt:
            form_data.add_field("prompt", prompt)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(api_url, data=form_data, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as response:
                    response_text = await response.text()

                    if response.status != 200:
                        logger.error(
                            f"Whisper API error: status={response.status}, "
                            f"audio_size={len(audio_data)}bytes, "
                            f"response={response_text[:500]}"
                        )
                        # 5xx エラーはリトライ対象
                        if 500 <= response.status < 600:
                            raise RuntimeError(f"Whisper API server error: {response.status} - {response_text}")
                        # 4xx エラーはリトライしない
                        raise ValueError(f"Whisper API client error: {response.status} - {response_text}")

                    import json
                    return json.loads(response_text)

            except aiohttp.ClientError as e:
                logger.error(f"HTTP request failed: {e}, audio_size={len(audio_data)}bytes")
                raise RuntimeError(f"Failed to connect to Whisper API: {e}") from e

    @staticmethod
    def detect_audio_format(audio_data: bytes) -> Tuple[str, str]:
        """
        音声データのフォーマットを検出

        Args:
            audio_data: 音声データ（バイト列）

        Returns:
            (format_name, mime_type) - フォーマット名とMIMEタイプ

        Raises:
            ValueError: 未対応のフォーマットの場合
        """
        if len(audio_data) < 12:
            raise ValueError("Audio data too short to detect format")

        # WAV (RIFF header)
        if audio_data[:4] == b"RIFF" and audio_data[8:12] == b"WAVE":
            return "wav", "audio/wav"

        # MP3 (ID3 tag or sync word)
        if audio_data[:3] == b"ID3":
            return "mp3", "audio/mpeg"
        if audio_data[:2] in (b"\xff\xfb", b"\xff\xfa", b"\xff\xf3", b"\xff\xf2"):
            return "mp3", "audio/mpeg"

        # FLAC
        if audio_data[:4] == b"fLaC":
            return "flac", "audio/flac"

        # OGG (Vorbis, Opus)
        if audio_data[:4] == b"OggS":
            return "ogg", "audio/ogg"

        # M4A/AAC (checking for ftyp box)
        if audio_data[4:8] == b"ftyp":
            ftyp_brand = audio_data[8:12]
            if ftyp_brand in (b"M4A ", b"mp42", b"isom", b"iso2"):
                return "m4a", "audio/m4a"

        # WebM
        if audio_data[:4] == b"\x1aE\xdf\xa3":
            return "webm", "audio/webm"

        # フォーマット検出失敗
        hex_preview = audio_data[:20].hex()
        raise ValueError(
            f"Unsupported audio format. Header bytes: {hex_preview}\n"
            f"Supported formats: WAV, MP3, FLAC, OGG, M4A, WEBM"
        )

    @staticmethod
    def get_available_models() -> list:
        """利用可能なWhisperモデルのリストを返す"""
        return [model.value for model in WhisperModel]

    async def health_check(self) -> Dict[str, Any]:
        """
        サービスのヘルスチェック

        Returns:
            ヘルス情報の辞書
        """
        return {
            "status": "healthy",
            "service": "speech_service",
            "default_model": self.default_model,
            "available_models": self.get_available_models(),
            "api_key_configured": bool(self.api_key)
        }
