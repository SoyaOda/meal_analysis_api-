#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VLM (Vision Language Model) Service

VLMプロバイダー（DeepInfra, Alibaba Cloud等）を使用して画像から食事情報を抽出する。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import mimetypes

from ..config import get_settings

logger = logging.getLogger(__name__)


class VLMService:
    """
    VLMを使用して画像から食事情報を抽出するサービス

    複数のVLMプロバイダー（DeepInfra, Alibaba Cloud等）をサポートし、
    画像から料理とその重量、説明を抽出する。
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        prompt_file: Optional[str] = None
    ):
        """
        Args:
            model_id: VLMモデルID（"provider:model_id" または "model_id" 形式）
                     None の場合は config 設定値を使用
            prompt_file: プロンプトファイル名（None の場合は config のデフォルトプロンプトを使用）
        """
        # config からデフォルト値を取得
        settings = get_settings()
        if model_id is None:
            model_id = settings.VLM_MODEL_ID

        self.model_id = model_id
        
        # VLMProviderFactoryを使ってプロバイダーを生成
        from .providers import VLMProviderFactory
        self.provider = VLMProviderFactory.create_provider(model_id)
        
        # 後方互換性のために deepinfra_service プロパティも保持
        # （pipeline.py で使われているため）
        self.deepinfra_service = self.provider

        # プロンプトロード - config管理を使用
        prompt_path = settings.get_prompt_path(prompt_file)
        self.prompt = self._load_prompt(prompt_path)

        logger.info(f"VLMService initialized with model: {model_id}")
        logger.info(f"Using prompt file: {prompt_path}")
        logger.info(f"Prompt length: {len(self.prompt)} characters")
        
        # ✅ 追加: Promptの最初の部分をログ出力（デバッグ用）
        prompt_preview = self.prompt[:500] if len(self.prompt) > 500 else self.prompt
        logger.info(f"Prompt preview (first 500 chars):\n{prompt_preview}")

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
        reasoning_effort: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        画像を解析して食事情報を抽出

        Args:
            image_bytes: 画像データ（バイト列）
            image_mime_type: 画像のMIMEタイプ
            temperature: AI推論のランダム性制御。Noneの場合、config設定値を使用。
            seed: 再現性のためのシード値。Noneの場合、config設定値を使用。
            max_tokens: 最大出力トークン数。Noneの場合、config設定値を使用。
            reasoning_effort: Reasoning effortレベル（minimal/low/medium/high/xhigh）

        Returns:
            (vlm_response, usage_info) のタプル
            - vlm_response: VLMの解析結果（dishes配列を含むJSON）
            - usage_info: トークン使用量と料金情報
        """
        logger.info(f"Analyzing image ({len(image_bytes)} bytes, {image_mime_type})")
        logger.info(f"Parameters: temperature={temperature}, seed={seed}, max_tokens={max_tokens}")
        
        # ✅ 追加: VLM呼び出し直前にpromptの内容をログ出力
        logger.info(f"📝 Using prompt (length: {len(self.prompt)} chars)")
        prompt_preview = self.prompt[:300] if len(self.prompt) > 300 else self.prompt
        logger.info(f"📝 Prompt preview (first 300 chars):\n{prompt_preview}")

        # API呼び出しパラメータ構築（Noneは渡さない）
        api_params = {
            "image_bytes": image_bytes,
            "image_mime_type": image_mime_type,
            "prompt": self.prompt,
            "return_usage": True,
        }
        
        # Optional パラメータは None でない場合のみ追加
        if max_tokens is not None:
            api_params["max_tokens"] = max_tokens
        if temperature is not None:
            api_params["temperature"] = temperature
        if seed is not None:
            api_params["seed"] = seed
        if reasoning_effort is not None:
            api_params["reasoning_effort"] = reasoning_effort

        # VLM呼び出し（providerを使用）
        try:
            raw_response, usage = await self.provider.analyze_image(**api_params)
        except Exception as e:
            logger.error(f"VLM API call failed: {e}")
            raise RuntimeError(f"[VLM Service] API call failed: {e}") from e

        # raw_responseのNullチェック
        if raw_response is None:
            logger.error("VLM returned None response")
            raise ValueError("[VLM Service] VLM returned None response")

        # JSONパース
        try:
            vlm_response = json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse VLM response as JSON: {e}")
            logger.error(f"Raw response: {raw_response[:500] if raw_response else 'None'}")
            raise ValueError(f"[VLM Service] Failed to parse VLM response as JSON: {e}") from e

        # dishes配列の存在チェック
        if "dishes" not in vlm_response:
            logger.error("VLM response does not contain 'dishes' field")
            raise ValueError(f"[VLM Service] VLM response does not contain 'dishes' field. Response keys: {list(vlm_response.keys())}")

        # vlm_responseがNoneの場合の追加チェック（念のため）
        if vlm_response is None:
            logger.error("VLM response is None after parsing")
            raise ValueError("[VLM Service] VLM response is None after parsing")

        logger.info(f"VLM analysis complete: {len(vlm_response.get('dishes', []))} dishes found")

        return vlm_response, usage

    async def analyze_image_from_file(
        self,
        image_path: str,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        max_tokens: Optional[int] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        画像ファイルから食事情報を抽出

        Args:
            image_path: 画像ファイルのパス
            temperature: AI推論のランダム性制御。Noneの場合、config設定値を使用。
            seed: 再現性のためのシード値。Noneの場合、config設定値を使用。
            max_tokens: 最大出力トークン数。Noneの場合、config設定値を使用。

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
            logger.error(f"Failed to guess MIME type for file: {image_file}")
            raise ValueError(f"[VLM Service] Cannot determine MIME type for image file: {image_file}")

        logger.info(f"Analyzing image file: {image_file.name}")

        return await self.analyze_image(
            image_bytes=image_bytes,
            image_mime_type=mime_type,
            temperature=temperature,
            seed=seed,
            max_tokens=max_tokens
        )

    def get_prompt(self) -> str:
        """使用中のプロンプトを返す"""
        return self.prompt
