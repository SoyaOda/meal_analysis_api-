"""
Google Cloud Speech-to-Text v2統合サービス

音声データをテキストに変換する機能を提供します。
"""
import os
import logging
from typing import Optional
from google.cloud import speech

logger = logging.getLogger(__name__)


class SpeechService:
    """Google Cloud Speech-to-Text v2を使用した音声認識サービス"""

    def __init__(self):
        """
        Speech-to-Textクライアントの初期化

        環境変数GOOGLE_APPLICATION_CREDENTIALSが設定されている必要があります。
        """
        try:
            self.client = speech.SpeechClient()
            logger.info("Google Cloud Speech-to-Text client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Speech-to-Text client: {e}")
            raise RuntimeError(f"Speech service configuration error: {e}") from e

    async def transcribe_audio(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        encoding: str = "LINEAR16",
        language_code: str = "en-US"
    ) -> str:
        """
        音声バイナリデータをテキストに変換する

        Args:
            audio_data: 音声バイナリデータ
            sample_rate: サンプリングレート（Hz）
            encoding: 音声エンコーディング（LINEAR16, FLAC, MP3, etc.）
            language_code: 言語コード（デフォルト: en-US）

        Returns:
            認識されたテキスト

        Raises:
            RuntimeError: 音声認識が失敗した場合
        """
        logger.info(f"Starting speech recognition for audio data ({len(audio_data)} bytes)")

        try:
            # 音声設定
            audio = speech.RecognitionAudio(content=audio_data)

            # エンコーディングの設定
            if encoding == "LINEAR16":
                audio_encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
            elif encoding == "FLAC":
                audio_encoding = speech.RecognitionConfig.AudioEncoding.FLAC
            elif encoding == "MP3":
                audio_encoding = speech.RecognitionConfig.AudioEncoding.MP3
            elif encoding == "WAV":
                audio_encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
            else:
                logger.warning(f"Unknown encoding {encoding}, defaulting to LINEAR16")
                audio_encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16

            # 認識設定
            config = speech.RecognitionConfig(
                encoding=audio_encoding,
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                enable_automatic_punctuation=True,  # 句読点を自動付与
                use_enhanced=True,  # 高精度モデルを使用
                model="latest_long"  # 長い音声に適したモデル
            )

            # 音声認識を実行
            logger.info(f"Calling Google Speech-to-Text API (language: {language_code}, encoding: {encoding})")
            response = self.client.recognize(config=config, audio=audio)

            # 結果からテキストを抽出
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript

            transcript = transcript.strip()

            if transcript:
                logger.info(f"Speech recognition successful: '{transcript[:100]}{'...' if len(transcript) > 100 else ''}'")
                return transcript
            else:
                logger.warning("Speech recognition returned empty result")
                raise RuntimeError("No speech detected in audio data")

        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            raise RuntimeError(f"Speech-to-text conversion failed: {e}") from e

    def detect_audio_format(self, audio_data: bytes) -> tuple[str, int]:
        """
        音声データのフォーマットを推定する

        Args:
            audio_data: 音声バイナリデータ

        Returns:
            tuple: (エンコーディング, 推定サンプリングレート)
        """
        # 簡易的なフォーマット判定（ヘッダーベース）
        if audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:12]:
            return "LINEAR16", 16000
        elif audio_data.startswith(b'fLaC'):
            return "FLAC", 16000
        elif audio_data.startswith(b'ID3') or audio_data[0:2] == b'\xff\xfb':
            return "MP3", 16000
        else:
            # デフォルト
            logger.warning("Could not detect audio format, defaulting to LINEAR16")
            return "LINEAR16", 16000