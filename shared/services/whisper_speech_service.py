#!/usr/bin/env python3
"""
OpenAI Whisper API + Local Whisperを使用した音声認識サービス
"""
import logging
import io
import tempfile
from typing import Optional, Union
from enum import Enum
import asyncio
import os

logger = logging.getLogger(__name__)

class WhisperBackend(Enum):
    """Whisperバックエンドの種類"""
    OPENAI_API = "openai_api"
    LOCAL_WHISPER = "local_whisper"
    DEEPINFRA_API = "deepinfra_api"

class WhisperModel(Enum):
    """利用可能なWhisperモデル"""
    # OpenAI API用
    WHISPER_1 = "whisper-1"

    # DeepInfra API用
    DEEPINFRA_LARGE_V3 = "openai/whisper-large-v3"
    DEEPINFRA_LARGE_V3_TURBO = "openai/whisper-large-v3-turbo"
    DEEPINFRA_BASE = "openai/whisper-base"

    # Local Whisper用
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE_V3 = "large-v3"
    LARGE_V3_TURBO = "large-v3-turbo"

    # English専用モデル
    TINY_EN = "tiny.en"
    BASE_EN = "base.en"
    SMALL_EN = "small.en"
    MEDIUM_EN = "medium.en"

class WhisperSpeechService:
    """
    OpenAI Whisper API + Local Whisperを使用した音声認識サービス

    設定に応じてOpenAI APIまたはローカルWhisperを使用
    """

    def __init__(
        self,
        backend: WhisperBackend = WhisperBackend.DEEPINFRA_API,
        openai_api_key: Optional[str] = None,
        deepinfra_api_key: Optional[str] = None
    ):
        """
        Whisper音声認識サービスの初期化

        Args:
            backend: 使用するWhisperバックエンド
            openai_api_key: OpenAI APIキー（API使用時）
            deepinfra_api_key: DeepInfra APIキー（API使用時）
        """
        self.backend = backend
        self._openai_client = None
        self._deepinfra_api_key = None
        self._local_whisper_model = None

        if self.backend == WhisperBackend.OPENAI_API:
            self._init_openai_client(openai_api_key)
        elif self.backend == WhisperBackend.DEEPINFRA_API:
            self._init_deepinfra_client(deepinfra_api_key)
        else:
            # ローカルWhisperの初期化は実際の使用時まで遅延
            pass

        logger.info(f"WhisperSpeechService initialized with backend: {backend.value}")

    def _init_openai_client(self, api_key: Optional[str] = None):
        """OpenAI APIクライアントの初期化"""
        try:
            import openai

            # APIキーの取得
            final_api_key = api_key or os.environ.get("OPENAI_API_KEY")
            if not final_api_key:
                raise RuntimeError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.")

            self._openai_client = openai.OpenAI(api_key=final_api_key)
            logger.info("OpenAI client initialized successfully")

        except ImportError as e:
            raise RuntimeError("openai library not installed. Run: pip install openai") from e
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise RuntimeError(f"OpenAI client initialization error: {e}") from e

    def _init_deepinfra_client(self, api_key: Optional[str] = None):
        """DeepInfra APIクライアントの初期化"""
        try:
            from shared.config.settings import get_settings
            settings = get_settings()
            
            # APIキーの取得（既存の実装方式に合わせる）
            final_api_key = api_key or settings.DEEPINFRA_API_KEY or os.environ.get("DEEPINFRA_API_KEY")
            if not final_api_key:
                raise RuntimeError("DeepInfra API key not provided. Set DEEPINFRA_API_KEY environment variable or configure in settings.")

            self._deepinfra_api_key = final_api_key
            logger.info("DeepInfra client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize DeepInfra client: {e}")
            raise RuntimeError(f"DeepInfra client initialization error: {e}") from e

    def _init_local_whisper(self, model_name: str):
        """ローカルWhisperモデルの初期化（遅延初期化）"""
        try:
            import whisper
            import torch

            logger.info(f"Loading local Whisper model: {model_name}")
            self._local_whisper_model = whisper.load_model(model_name)

            # GPU利用可能時は自動でGPU使用
            if torch.cuda.is_available():
                self._local_whisper_model = self._local_whisper_model.cuda()
                logger.info(f"Using GPU for Whisper model: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("Using CPU for Whisper model")

        except ImportError as e:
            raise RuntimeError("openai-whisper library not installed. Run: pip install openai-whisper torch torchaudio") from e
        except Exception as e:
            logger.error(f"Failed to initialize local Whisper model: {e}")
            raise RuntimeError(f"Local Whisper model initialization error: {e}") from e

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language_code: str = "en-US",
        model: WhisperModel = WhisperModel.DEEPINFRA_LARGE_V3_TURBO,
        temperature: float = 0.0,
        response_format: str = "text",
        prompt: Optional[str] = None
    ) -> str:
        """
        音声データをテキストに変換

        Args:
            audio_data: WAV音声バイナリデータ
            language_code: 言語コード（ISO 639-1形式、例: "en", "ja"）
            model: 使用するWhisperモデル
            temperature: 推論時の温度パラメータ (0.0-1.0)
            response_format: レスポンス形式 ("text", "json", "srt", "vtt")
            prompt: 転写を導くためのオプションプロンプト

        Returns:
            認識されたテキスト

        Raises:
            RuntimeError: 音声認識が失敗した場合
        """
        logger.info(f"Starting speech recognition for audio data ({len(audio_data)} bytes) using {self.backend.value}")

        try:
            if self.backend == WhisperBackend.OPENAI_API:
                return await self._transcribe_with_openai_api(
                    audio_data, language_code, model, temperature, response_format, prompt
                )
            elif self.backend == WhisperBackend.DEEPINFRA_API:
                return await self._transcribe_with_deepinfra_api(
                    audio_data, language_code, model, temperature, response_format, prompt
                )
            else:
                return await self._transcribe_with_local_whisper(
                    audio_data, language_code, model, temperature, prompt
                )

        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            raise RuntimeError(f"Speech-to-text conversion failed: {e}") from e

    async def _transcribe_with_openai_api(
        self,
        audio_data: bytes,
        language_code: str,
        model: WhisperModel,
        temperature: float,
        response_format: str,
        prompt: Optional[str]
    ) -> str:
        """OpenAI APIを使用した音声認識"""
        logger.info(f"Using OpenAI API with model: {model.value}")

        # 言語コードをWhisper APIが認識する形式に変換
        # "en-US" -> "en", "ja-JP" -> "ja"
        whisper_language = language_code.split('-')[0] if '-' in language_code else language_code

        # 音声データを一時ファイルに保存（OpenAI APIはファイルオブジェクトを要求）
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as audio_file:
                # OpenAI APIの呼び出しパラメータ準備
                transcribe_params = {
                    "model": model.value if model == WhisperModel.WHISPER_1 else "whisper-1",
                    "file": audio_file,
                    "language": whisper_language if whisper_language != "en" else None,  # 英語はデフォルト
                    "temperature": temperature,
                    "response_format": response_format
                }

                # オプションプロンプトを追加
                if prompt:
                    transcribe_params["prompt"] = prompt

                logger.info(f"Calling OpenAI Whisper API with params: {dict((k,v if k != 'file' else '<audio_file>') for k,v in transcribe_params.items())}")

                # 非同期でAPI呼び出し（実際のライブラリが同期なので、thread pool使用）
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self._openai_client.audio.transcriptions.create(**transcribe_params)
                )

                # レスポンス形式に応じた処理
                if response_format == "text":
                    transcript = result
                else:
                    # JSON形式等の場合
                    transcript = result.text if hasattr(result, 'text') else str(result)

                logger.info(f"OpenAI API transcription successful: '{transcript[:100]}{'...' if len(transcript) > 100 else ''}'")
                return transcript.strip()

        finally:
            # 一時ファイルのクリーンアップ
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    async def _transcribe_with_deepinfra_api(
        self,
        audio_data: bytes,
        language_code: str,
        model: WhisperModel,
        temperature: float,
        response_format: str,
        prompt: Optional[str]
    ) -> str:
        """DeepInfra APIを使用した音声認識"""
        import aiohttp
        
        logger.info(f"Using DeepInfra API with model: {model.value}")

        # 言語コードをWhisper APIが認識する形式に変換
        whisper_language = language_code.split('-')[0] if '-' in language_code else language_code

        # 音声データを一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        try:
            # DeepInfra APIエンドポイント
            api_url = f"https://api.deepinfra.com/v1/inference/{model.value}"
            
            headers = {
                "Authorization": f"Bearer {self._deepinfra_api_key}"
            }

            # マルチパートフォームデータの準備
            async with aiohttp.ClientSession() as session:
                with aiohttp.FormData() as data:
                    # 音声ファイルをアップロード
                    with open(temp_file_path, 'rb') as audio_file:
                        data.add_field('audio', audio_file, 
                                     filename='audio.wav',
                                     content_type='audio/wav')
                    
                    # オプションパラメータ
                    if whisper_language != "en":
                        data.add_field('language', whisper_language)
                    if temperature != 0.0:
                        data.add_field('temperature', str(temperature))
                    if prompt:
                        data.add_field('prompt', prompt)
                    
                    logger.info(f"Calling DeepInfra Whisper API: {api_url}")

                    async with session.post(api_url, headers=headers, data=data) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise RuntimeError(f"DeepInfra API error {response.status}: {error_text}")
                        
                        result = await response.json()
                        
                        # DeepInfraのレスポンス形式に応じた処理
                        if 'text' in result:
                            transcript = result['text']
                        elif 'results' in result and result['results']:
                            transcript = result['results'][0].get('text', '')
                        else:
                            transcript = str(result)

                        logger.info(f"DeepInfra API transcription successful: '{transcript[:100]}{'...' if len(transcript) > 100 else ''}'")
                        return transcript.strip()

        finally:
            # 一時ファイルのクリーンアップ
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    async def _transcribe_with_local_whisper(
        self,
        audio_data: bytes,
        language_code: str,
        model: WhisperModel,
        temperature: float,
        prompt: Optional[str]
    ) -> str:
        """ローカルWhisperを使用した音声認識"""
        logger.info(f"Using local Whisper with model: {model.value}")

        # モデルの初期化（遅延初期化）
        if self._local_whisper_model is None:
            self._init_local_whisper(model.value)

        # 言語コードをWhisperが認識する形式に変換
        whisper_language = language_code.split('-')[0] if '-' in language_code else language_code

        # 音声データを一時ファイルに保存
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name

        try:
            # Whisperの転写オプション
            transcribe_options = {
                "language": whisper_language if whisper_language != "en" else None,
                "temperature": temperature
            }

            # オプションプロンプトを追加
            if prompt:
                transcribe_options["initial_prompt"] = prompt

            logger.info(f"Running local Whisper with options: {transcribe_options}")

            # 非同期でWhisper実行（CPUバウンドなのでthread pool使用）
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._local_whisper_model.transcribe(temp_file_path, **transcribe_options)
            )

            transcript = result["text"].strip()
            logger.info(f"Local Whisper transcription successful: '{transcript[:100]}{'...' if len(transcript) > 100 else ''}'")

            return transcript

        finally:
            # 一時ファイルのクリーンアップ
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def detect_audio_format(self, audio_data: bytes) -> tuple[str, int]:
        """
        音声データのフォーマットを推定する（既存SpeechServiceとの互換性）

        Args:
            audio_data: 音声バイナリデータ

        Returns:
            tuple: (エンコーディング, 推定サンプリングレート)
        """
        # 簡易的なフォーマット判定（既存実装と同様）
        if audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]:
            return ("wav", 16000)
        elif audio_data.startswith(b'fLaC'):
            return ("flac", 16000)
        elif (audio_data.startswith(b'ID3') or
              audio_data[:2] == b'\\xff\\xfb' or
              audio_data[:2] == b'\\xff\\xf3' or
              audio_data[:2] == b'\\xff\\xf2'):
            return ("mp3", 16000)
        else:
            logger.warning("Could not detect audio format, defaulting to WAV")
            return ("wav", 16000)

    def get_supported_models(self) -> list[WhisperModel]:
        """バックエンドでサポートされているモデル一覧を取得"""
        if self.backend == WhisperBackend.OPENAI_API:
            return [WhisperModel.WHISPER_1]
        elif self.backend == WhisperBackend.DEEPINFRA_API:
            return [
                WhisperModel.DEEPINFRA_LARGE_V3,
                WhisperModel.DEEPINFRA_LARGE_V3_TURBO,
                WhisperModel.DEEPINFRA_BASE
            ]
        else:
            return [
                WhisperModel.TINY, WhisperModel.BASE, WhisperModel.SMALL,
                WhisperModel.MEDIUM, WhisperModel.LARGE_V3, WhisperModel.LARGE_V3_TURBO,
                WhisperModel.TINY_EN, WhisperModel.BASE_EN,
                WhisperModel.SMALL_EN, WhisperModel.MEDIUM_EN
            ]