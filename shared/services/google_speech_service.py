"""
Google Cloud Speech-to-Text v2統合サービス

音声データをテキストに変換する機能を提供します。
"""
import os
import logging
from typing import Optional
from google.cloud import speech

logger = logging.getLogger(__name__)


class GoogleSpeechService:
    """
    Google Speech-to-Text API V2を使用した音声認識サービス

    Google Cloud Speech-to-Text APIのEnhancedモデルを使用して
    高精度な音声認識を提供します。
    """

    def __init__(self):
        """
        Google音声認識サービスの初期化
        
        認証情報はGoogle Cloud SDKの設定またはサービスアカウントキーから取得
        """
        self.client = None
        self._init_speech_client()
        logger.info("GoogleSpeechService initialized successfully")
        
    def _init_speech_client(self):
        """Google Cloud Speech clientの初期化"""
        try:
            from google.cloud import speech
            self.client = speech.SpeechClient()
            logger.info("Google Cloud Speech client initialized")
        except ImportError as e:
            logger.error("Google Cloud Speech library not found. Install: pip install google-cloud-speech")
            raise RuntimeError("Google Cloud Speech library is required") from e
        except Exception as e:
            logger.error(f"Failed to initialize Google Speech client: {e}")
            raise RuntimeError(f"Google Speech client initialization error: {e}") from e

    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        language_code: str = "en-US"
    ) -> str:
        """
        音声データをテキストに変換

        Args:
            audio_data: WAV音声バイナリデータ
            language_code: 言語コード (ISO BCP-47形式、例: "en-US", "ja-JP")

        Returns:
            認識されたテキスト

        Raises:
            RuntimeError: 音声認識が失敗した場合
        """
        logger.info(f"Starting Google Speech-to-Text recognition for audio ({len(audio_data)} bytes, language: {language_code})")
        
        try:
            from google.cloud import speech
            import asyncio

            # Google Speech-to-Text設定
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                # Enhancedモデルを使用（より高精度）
                model="latest_long",
                use_enhanced=True,
                # 自動句読点追加
                enable_automatic_punctuation=True,
                # 最大代替候補数
                max_alternatives=1,
            )

            audio = speech.RecognitionAudio(content=audio_data)

            # 非同期実行（実際のAPIは同期なので、thread poolを使用）
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.recognize(config=config, audio=audio)
            )

            # 結果の処理
            if not response.results:
                error_msg = "No speech recognized from audio data"
                logger.warning(error_msg)
                raise RuntimeError(error_msg)

            # 最も信頼度の高い転写結果を取得
            transcript = response.results[0].alternatives[0].transcript
            confidence = response.results[0].alternatives[0].confidence

            logger.info(f"Google Speech-to-Text recognition successful: '{transcript}' (confidence: {confidence:.3f})")
            return transcript.strip()

        except Exception as e:
            logger.error(f"Google Speech-to-Text recognition failed: {e}")
            raise RuntimeError(f"Google Speech-to-Text conversion failed: {e}") from e

    def detect_audio_format(self, audio_data: bytes) -> tuple[str, int]:
        """
        音声データのフォーマットを推定する

        Args:
            audio_data: 音声バイナリデータ

        Returns:
            tuple: (エンコーディング, 推定サンプリングレート)
        """
        # 簡易的なフォーマット判定
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