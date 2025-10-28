#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VLM (Vision Language Model) Service

DeepInfra APIを使用して画像から食事情報を抽出する。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import mimetypes

from shared.services.deepinfra_service import DeepInfraService
from shared.config import get_settings

logger = logging.getLogger(__name__)


class VLMService:
    """
    VLMを使用して画像から食事情報を抽出するサービス

    DeepInfraのQwen3-VL-235Bモデルを使用して、画像から料理とその重量、説明を抽出する。
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        prompt_file: Optional[str] = None
    ):
        """
        Args:
            model_id: DeepInfra VLMモデルID（Noneの場合はconfig設定値を使用）
            prompt_file: プロンプトファイルのパス（Noneの場合はデフォルトのUSDAフォーマットプロンプトを使用）
        """
        # config からデフォルト値を取得
        settings = get_settings()
        if model_id is None:
            model_id = settings.VLM_MODEL_ID

        self.model_id = model_id
        self.deepinfra_service = DeepInfraService(model_id=model_id)

        # プロンプトロード
        if prompt_file:
            self.prompt = self._load_prompt(prompt_file)
        else:
            # デフォルト: freeform_prompt_usda_format_ver.txt (apps内のpromptsディレクトリ)
            default_prompt_path = (
                Path(__file__).parent.parent / "prompts" / "freeform_prompt_usda_format_ver.txt"
            )
            self.prompt = self._load_prompt(str(default_prompt_path))

        logger.info(f"VLMService initialized with model: {model_id}")
        logger.info(f"Prompt length: {len(self.prompt)} characters")

    def _load_prompt(self, prompt_file: str) -> str:
        """プロンプトファイルを読み込む"""
        prompt_path = Path(prompt_file)

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()

        logger.info(f"Loaded prompt from: {prompt_file}")
        return prompt

    async def analyze_image(
        self,
        image_bytes: bytes,
        image_mime_type: str = "image/jpeg",
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        画像を解析して食事情報を抽出

        Args:
            image_bytes: 画像データ（バイト列）
            image_mime_type: 画像のMIMEタイプ
            temperature: AI推論のランダム性制御。Noneの場合、config設定値を使用。
            seed: 再現性のためのシード値。Noneの場合、config設定値を使用。
            max_tokens: 最大出力トークン数。Noneの場合、config設定値を使用。
            thinking_budget: Thinkingモデルの推論トークン数の上限。Noneの場合、config設定値を使用。

        Returns:
            (vlm_response, usage_info) のタプル
            - vlm_response: VLMの解析結果（dishes配列を含むJSON）
            - usage_info: トークン使用量と料金情報
        """
        logger.info(f"Analyzing image ({len(image_bytes)} bytes, {image_mime_type})")
        logger.info(f"Parameters: temperature={temperature}, seed={seed}, max_tokens={max_tokens}")

        # VLM呼び出し
        raw_response, usage = await self.deepinfra_service.analyze_image(
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            prompt=self.prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            seed=seed,
            return_usage=True,
            thinking_budget=thinking_budget
        )

        # JSONパース
        try:
            vlm_response = json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse VLM response as JSON: {e}")
            logger.error(f"Raw response: {raw_response}")
            raise ValueError(f"VLM response is not valid JSON: {e}")

        # dishes配列の存在チェック
        if "dishes" not in vlm_response:
            logger.warning("VLM response does not contain 'dishes' field")
            vlm_response = {"dishes": []}

        logger.info(f"VLM analysis complete: {len(vlm_response.get('dishes', []))} dishes found")

        return vlm_response, usage

    async def analyze_image_from_file(
        self,
        image_path: str,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        画像ファイルから食事情報を抽出

        Args:
            image_path: 画像ファイルのパス
            temperature: AI推論のランダム性制御。Noneの場合、config設定値を使用。
            seed: 再現性のためのシード値。Noneの場合、config設定値を使用。
            max_tokens: 最大出力トークン数。Noneの場合、config設定値を使用。
            thinking_budget: Thinkingモデルの推論トークン数の上限。Noneの場合、config設定値を使用。

        Returns:
            (vlm_response, usage_info) のタプル
        """
        image_file = Path(image_path)

        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # 画像読み込み
        with open(image_file, 'rb') as f:
            image_bytes = f.read()

        # MIMEタイプ取得
        mime_type, _ = mimetypes.guess_type(str(image_file))
        if not mime_type:
            mime_type = "image/jpeg"  # デフォルト

        logger.info(f"Analyzing image file: {image_file.name}")

        return await self.analyze_image(
            image_bytes=image_bytes,
            image_mime_type=mime_type,
            temperature=temperature,
            seed=seed,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget
        )

    def get_prompt(self) -> str:
        """使用中のプロンプトを返す"""
        return self.prompt
