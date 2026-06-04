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
from ..core.vlm_cache import get_vlm_cache

logger = logging.getLogger(__name__)

# Self-verification (2nd-pass) prompt; injects the candidate list at {{CANDIDATES}}.
VERIFY_PROMPT_FILE = "freeform_verify_pass_20260602.txt"


def apply_verification(
    vlm_response: Dict[str, Any],
    verdicts: list,
    drop_unsure: bool = False,
) -> Tuple[Dict[str, Any], int]:
    """Remove items the self-verification pass marked 'not_present' from the dish structure.

    Matches verdict "item" to a dish's main_food/extra by exact search_name; a name that
    does not match is KEPT (fail-safe toward recall — a paraphrased verdict never silently
    drops a real item). 'unsure' is kept unless drop_unsure=True. A dish left with no
    main_food and no extras is removed. Returns (filtered_response, n_dropped).
    """
    drop = {v.get("item") for v in verdicts if v.get("verdict") == "not_present"}
    if drop_unsure:
        drop |= {v.get("item") for v in verdicts if v.get("verdict") == "unsure"}
    drop.discard(None)
    n_dropped = 0
    new_dishes = []
    for dish in vlm_response.get("dishes", []) or []:
        main_food = dish.get("main_food")
        if main_food and main_food.get("search_name") in drop:
            main_food = None
            n_dropped += 1
        extras = []
        for extra in dish.get("extras") or []:
            if extra.get("search_name") in drop:
                n_dropped += 1
            else:
                extras.append(extra)
        if main_food is None and not extras:
            continue
        new_dish = dict(dish)
        new_dish["main_food"] = main_food
        new_dish["extras"] = extras
        new_dishes.append(new_dish)
    out = dict(vlm_response)
    out["dishes"] = new_dishes
    return out, n_dropped


class VLMService:
    """
    VLMを使用して画像から食事情報を抽出するサービス

    複数のVLMプロバイダー（DeepInfra, Alibaba Cloud等）をサポートし、
    画像から料理とその重量、説明を抽出する。
    """

    def __init__(
        self, model_id: Optional[str] = None, prompt_file: Optional[str] = None
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
            # NOTE(F1-c): settings.VLM_MODEL_ID は未定義（DEFAULT_VLM_MODEL_ID のみ）。
            # model_id=None で VLMService を作る経路の AttributeError を防ぐ防御的修正。
            model_id = settings.DEFAULT_VLM_MODEL_ID

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

        # Self-verification (2nd-pass) prompt — loaded once, used only when enabled.
        self._verify_prompt = self._load_prompt(
            settings.get_prompt_path(VERIFY_PROMPT_FILE)
        )

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

        with open(prompt_path, "r", encoding="utf-8") as f:
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
        reasoning_effort: Optional[str] = None,
        use_cache: bool = True,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        画像を解析して食事情報を抽出

        キャッシュ機能:
        - 同一画像 + 同一プロンプト + 同一モデルの結果をキャッシュ
        - キャッシュヒット時はAPI呼び出しをスキップ（3-5秒 → 50ms）
        - モデル比較時も正しく動作（model_idがキャッシュキーに含まれる）
        - use_cache=Falseでキャッシュをバイパス可能

        Args:
            image_bytes: 画像データ（バイト列）
            image_mime_type: 画像のMIMEタイプ
            temperature: AI推論のランダム性制御。Noneの場合、config設定値を使用。
            seed: 再現性のためのシード値。Noneの場合、config設定値を使用。
            max_tokens: 最大出力トークン数。Noneの場合、config設定値を使用。
            reasoning_effort: Reasoning effortレベル（minimal/low/medium/high/xhigh）
            use_cache: キャッシュを使用するかどうか（デフォルト: True）

        Returns:
            (vlm_response, usage_info) のタプル
            - vlm_response: VLMの解析結果（dishes配列を含むJSON）
            - usage_info: トークン使用量と料金情報
        """
        from ..admin.config_manager import get_config_manager

        config_manager = get_config_manager()
        config = config_manager.get_config()

        effective_temperature = (
            temperature if temperature is not None else config.vlm.temperature
        )
        effective_seed = seed if seed is not None else config.vlm.seed
        effective_max_tokens = (
            max_tokens if max_tokens is not None else config.vlm.max_tokens
        )
        effective_reasoning_effort = (
            reasoning_effort
            if reasoning_effort is not None
            else config.vlm.reasoning_effort
        )

        logger.info(f"Analyzing image ({len(image_bytes)} bytes, {image_mime_type})")
        logger.info(
            "Parameters: temperature=%s, seed=%s, max_tokens=%s, reasoning_effort=%s, use_cache=%s",
            effective_temperature,
            effective_seed,
            effective_max_tokens,
            effective_reasoning_effort,
            use_cache,
        )

        # キャッシュチェック（use_cache=Trueの場合のみ）
        cache = get_vlm_cache()
        cache_context = {
            "temperature": effective_temperature,
            "seed": effective_seed,
            "max_tokens": effective_max_tokens,
            "reasoning_effort": effective_reasoning_effort,
        }
        if use_cache:
            cached = await cache.get(
                image_bytes=image_bytes,
                prompt=self.prompt,
                model_id=self.model_id,
                cache_context=cache_context,
            )
            if cached:
                vlm_response, usage = cached
                # キャッシュヒットをusageに記録
                usage = dict(usage)  # コピーを作成
                usage["cached"] = True
                logger.info(
                    f"VLM analysis complete (cached): {len(vlm_response.get('dishes', []))} dishes found"
                )
                return vlm_response, usage
        else:
            logger.debug("VLM cache bypassed")

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
            "max_tokens": effective_max_tokens,
            "temperature": effective_temperature,
            "seed": effective_seed,
            "reasoning_effort": effective_reasoning_effort,
        }

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
            logger.error(
                f"Raw response: {raw_response[:500] if raw_response else 'None'}"
            )
            raise ValueError(
                f"[VLM Service] Failed to parse VLM response as JSON: {e}"
            ) from e

        # dishes配列の存在チェック
        if "dishes" not in vlm_response:
            logger.error("VLM response does not contain 'dishes' field")
            raise ValueError(
                f"[VLM Service] VLM response does not contain 'dishes' field. Response keys: {list(vlm_response.keys())}"
            )

        # vlm_responseがNoneの場合の追加チェック（念のため）
        if vlm_response is None:
            logger.error("VLM response is None after parsing")
            raise ValueError("[VLM Service] VLM response is None after parsing")

        # キャッシュに保存（use_cache=Trueの場合のみ）
        if use_cache:
            await cache.set(
                image_bytes=image_bytes,
                prompt=self.prompt,
                model_id=self.model_id,
                response=vlm_response,
                usage=usage,
                cache_context=cache_context,
            )

        # usageにcached=Falseを追加
        usage["cached"] = False

        logger.info(
            f"VLM analysis complete: {len(vlm_response.get('dishes', []))} dishes found"
        )

        return vlm_response, usage

    async def verify_items(
        self,
        image_bytes: bytes,
        candidate_names: list,
        image_mime_type: str = "image/jpeg",
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        max_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Second-pass self-verification: re-show the image with the candidate food list
        and ask which items are actually visible. Returns {"verdicts": [...], "missing":
        [...]}. Used to DROP invented items (a precision lever). Fails loud on a bad
        response. This is a SEPARATE (uncached) VLM call; the single-pass path never calls
        it.
        """
        if not candidate_names:
            return {"verdicts": [], "missing": []}

        from ..admin.config_manager import get_config_manager

        config = get_config_manager().get_config()
        eff_temp = temperature if temperature is not None else config.vlm.temperature
        eff_seed = seed if seed is not None else config.vlm.seed
        eff_max = max_tokens if max_tokens is not None else config.vlm.max_tokens
        eff_re = (
            reasoning_effort
            if reasoning_effort is not None
            else config.vlm.reasoning_effort
        )

        numbered = "\n".join(f"{i + 1}. {n}" for i, n in enumerate(candidate_names))
        prompt = self._verify_prompt.replace("{{CANDIDATES}}", numbered)

        try:
            raw_response, _usage = await self.provider.analyze_image(
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                prompt=prompt,
                return_usage=True,
                max_tokens=eff_max,
                temperature=eff_temp,
                seed=eff_seed,
                reasoning_effort=eff_re,
            )
        except Exception as e:
            raise RuntimeError(f"[VLM Service] verify pass API call failed: {e}") from e

        if not raw_response:
            raise ValueError("[VLM Service] verify pass returned empty response")
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"[VLM Service] verify pass JSON parse failed: {e}; raw: {raw_response[:300]}"
            ) from e
        return {
            "verdicts": parsed.get("verdicts") or [],
            "missing": parsed.get("missing") or [],
        }

    async def analyze_image_from_file(
        self,
        image_path: str,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        max_tokens: Optional[int] = None,
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
        with open(image_file, "rb") as f:
            image_bytes = f.read()

        # MIMEタイプ取得
        mime_type, _ = mimetypes.guess_type(str(image_file))
        if not mime_type:
            logger.error(f"Failed to guess MIME type for file: {image_file}")
            raise ValueError(
                f"[VLM Service] Cannot determine MIME type for image file: {image_file}"
            )

        logger.info(f"Analyzing image file: {image_file.name}")

        return await self.analyze_image(
            image_bytes=image_bytes,
            image_mime_type=mime_type,
            temperature=temperature,
            seed=seed,
            max_tokens=max_tokens,
        )

    def get_prompt(self) -> str:
        """使用中のプロンプトを返す"""
        return self.prompt
