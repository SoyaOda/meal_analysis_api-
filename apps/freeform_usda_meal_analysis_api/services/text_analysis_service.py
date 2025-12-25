"""
Text Analysis Service for Voice Input

テキスト入力（音声認識結果）から食事情報を抽出するサービス
VLMServiceと同じインターフェースパターンを使用
"""

import json
import logging
import re
from typing import Dict, Any, Tuple, Optional

from .providers import VLMProviderFactory

logger = logging.getLogger(__name__)


class TextAnalysisService:
    """
    テキストから食事情報を抽出するサービス

    音声認識で得られたテキストをLLM/VLMに渡して、
    USDA検索用のJSON形式に変換する
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        prompt_file: Optional[str] = None,
        prompt_text: Optional[str] = None
    ):
        """
        TextAnalysisServiceを初期化

        Args:
            model_id: 使用するLLM/VLMモデルID（Noneの場合はデフォルト）
            prompt_file: プロンプトファイル名（Noneの場合はデフォルト）
            prompt_text: カスタムプロンプトテキスト（prompt_fileより優先）
        """
        from ..config import get_settings
        settings = get_settings()

        # モデル設定
        self.model_id = model_id or settings.DEFAULT_VOICE_MODEL_ID

        # プロバイダー初期化
        self.provider = VLMProviderFactory.create_provider(
            model_id=self.model_id
        )

        # プロンプト読み込み（prompt_textが指定されている場合はそちらを優先）
        if prompt_text:
            self.prompt = prompt_text
            self.prompt_file = "[custom_prompt_text]"
            logger.info("TextAnalysisService initialized:")
            logger.info(f"  Model: {self.model_id}")
            logger.info("  Prompt: [Custom prompt text provided]")
        else:
            prompt_path = settings.get_voice_prompt_path(prompt_file)
            self.prompt = self._load_prompt(prompt_path)
            self.prompt_file = prompt_file or settings.DEFAULT_VOICE_PROMPT_FILE
            logger.info("TextAnalysisService initialized:")
            logger.info(f"  Model: {self.model_id}")
            logger.info(f"  Prompt: {self.prompt_file}")

    def _load_prompt(self, prompt_path: str) -> str:
        """プロンプトファイルを読み込む"""
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    async def analyze_text(
        self,
        text: str,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        max_tokens: Optional[int] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        テキストを分析して食事情報を抽出

        Args:
            text: 分析対象のテキスト（音声認識結果など）
            temperature: 生成温度
            seed: 再現性のためのシード値
            max_tokens: 最大出力トークン数

        Returns:
            (parsed_result, usage_info) - 解析結果とtoken使用量情報

        Raises:
            ValueError: テキストが空の場合
            RuntimeError: LLM呼び出しに失敗した場合
        """
        if not text or not text.strip():
            raise ValueError("Input text is empty")

        from ..config import get_settings
        settings = get_settings()

        # デフォルト値の設定
        temperature = temperature if temperature is not None else settings.DEFAULT_VOICE_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else settings.DEFAULT_VOICE_MAX_TOKENS

        logger.info(f"Analyzing text with LLM: '{text[:100]}...'")
        logger.info(f"  Model: {self.model_id}")
        logger.info(f"  Temperature: {temperature}")
        logger.info(f"  Max tokens: {max_tokens}")

        # LLM呼び出し
        try:
            response, usage = await self.provider.analyze_text(
                text=text,
                prompt=self.prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                seed=seed,
                return_usage=True
            )
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise RuntimeError(f"LLM analysis failed: {e}") from e

        # JSONパース
        parsed_result = self._parse_json_response(response)

        # Usage情報を整形
        usage_info = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "raw_vlm_output": response
        }

        logger.info(f"Text analysis completed: {len(parsed_result.get('dishes', []))} dishes found")

        return parsed_result, usage_info

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        LLMレスポンスからJSONを抽出してパース

        Args:
            response: LLMの生出力

        Returns:
            パースされたJSON辞書

        Raises:
            ValueError: JSONパースに失敗した場合
        """
        # <think>タグを除去（Thinkingモデルの場合）
        content = response
        if "<think>" in content:
            content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)

        # コードブロックを除去
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content)
        content = content.strip()

        # JSONを抽出
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            json_str = json_match.group()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                logger.error(f"Content: {json_str[:500]}...")
                raise ValueError(f"Failed to parse LLM response as JSON: {e}") from e

        logger.error(f"No JSON found in response: {content[:500]}...")
        raise ValueError("No valid JSON found in LLM response")

    def get_prompt(self) -> str:
        """現在のプロンプトを取得"""
        return self.prompt

    def set_prompt(self, prompt: str) -> None:
        """プロンプトを設定"""
        self.prompt = prompt

    def reload_prompt(self, prompt_file: Optional[str] = None) -> None:
        """プロンプトを再読み込み"""
        from ..config import get_settings
        settings = get_settings()

        prompt_path = settings.get_voice_prompt_path(prompt_file)
        self.prompt = self._load_prompt(prompt_path)
        self.prompt_file = prompt_file or settings.DEFAULT_VOICE_PROMPT_FILE

        logger.info(f"Prompt reloaded: {self.prompt_file}")
