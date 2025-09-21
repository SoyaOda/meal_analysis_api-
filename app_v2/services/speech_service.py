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
        language_code: str = "en-US"
    ) -> str:
        """
        WAV音声バイナリデータをテキストに変換する
        
        Args:
            audio_data: WAV音声バイナリデータ
            language_code: 言語コード（デフォルト: en-US）
        
        Returns:
            認識されたテキスト
        
        Raises:
            RuntimeError: 音声認識が失敗した場合
        """
        logger.info(f"Starting speech recognition for audio data ({len(audio_data)} bytes)")
        
        try:
            # WAVヘッダーからサンプルレートを検出
            sample_rate = self._extract_sample_rate_from_wav(audio_data)
            logger.info(f"Detected sample rate: {sample_rate} Hz")
            
            # 音声設定
            audio = speech.RecognitionAudio(content=audio_data)
            
            # 認識設定 - WAV形式のみ対応、サンプルレートは省略（WAVヘッダーから自動検出）
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                language_code=language_code,
                enable_automatic_punctuation=True,  # 句読点を自動付与
                use_enhanced=True,  # 高精度モデルを使用
                model="latest_long"  # 長い音声に適したモデル
            )
            
            # 音声認識を実行
            logger.info(f"Calling Google Speech-to-Text API (language: {language_code}, WAV format)")
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
    
    def _extract_sample_rate_from_wav(self, audio_data: bytes) -> int:
        """
        WAVファイルのヘッダーからサンプルレートを抽出
        
        Args:
            audio_data: WAVファイルのバイナリデータ
            
        Returns:
            サンプルレート（Hz）
            
        Raises:
            ValueError: WAVヘッダーが無効な場合
        """
        if len(audio_data) < 44:
            raise ValueError("Invalid WAV file: too short")
        
        # WAVヘッダーの確認
        if audio_data[:4] != b'RIFF' or audio_data[8:12] != b'WAVE':
            raise ValueError("Invalid WAV file header")
        
        # サンプルレートはオフセット24-27バイト（リトルエンディアン）
        sample_rate = int.from_bytes(audio_data[24:28], byteorder='little')
        
        if sample_rate <= 0:
            raise ValueError(f"Invalid sample rate: {sample_rate}")
        
        return sample_rate

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
        elif (audio_data.startswith(b'ID3') or 
              audio_data[:2] == b'\xff\xfb' or  # MP3 フレーム (MPEG-1 Layer 3)
              audio_data[:2] == b'\xff\xf3' or  # MP3 フレーム (MPEG-1 Layer 3, 別パターン)
              audio_data[:2] == b'\xff\xf2'):   # MP3 フレーム (MPEG-2 Layer 3)
            return "MP3", 16000
        else:
            # デフォルト
            logger.warning("Could not detect audio format, defaulting to LINEAR16")
            return "LINEAR16", 16000