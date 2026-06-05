# apps/freeform_usda_meal_analysis_api/services/providers/google_provider.py
"""Google AI Studio (Gemini) VLM provider — native generateContent API.

E17': OpenRouter 経由では渡せない gemini-3 の native params（`media_resolution` /
`thinking_level`）を直叩きで A/B するための provider。`VLMProviderFactory` に
`"google"` として登録され、`vlm_model_id="google:gemini-3-flash-preview"` で使われる。

native params は per-candidate に切り替えられるよう **model id の suffix** で指定する:
    google:gemini-3-flash-preview              → API 既定
    google:gemini-3-flash-preview|media=high   → mediaResolution=MEDIA_RESOLUTION_HIGH
    google:gemini-3-flash-preview|think=high   → thinkingConfig.thinkingLevel=high
これにより 1 サーバ・1 eval run で複数 variant を candidate として A/B できる。

キーは env `GEMINI_API_KEY`（無ければ `GOOGLE_API_KEY`）。ハードコード禁止。新規依存なし（httpx）。
"""

import os
import json
import base64
import logging
from typing import Any, Dict, Optional, Tuple, Union

import httpx

from .base_provider import BaseVLMProvider

logger = logging.getLogger(__name__)

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
_MEDIA_MAP = {
    "low": "MEDIA_RESOLUTION_LOW",
    "medium": "MEDIA_RESOLUTION_MEDIUM",
    "high": "MEDIA_RESOLUTION_HIGH",
}
_TIMEOUT = httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=10.0)


class GoogleVLMProvider(BaseVLMProvider):
    """Gemini を Google AI Studio の generateContent で直接叩く VLM provider。"""

    def __init__(self, model_id: str, **kwargs):
        super().__init__(model_id)
        # "model|key=val|key=val" を分解
        parts = model_id.split("|")
        self.model = parts[0]
        opts = dict(p.split("=", 1) for p in parts[1:] if "=" in p)
        self.media_resolution = opts.get("media")  # low/medium/high
        self.thinking_level = opts.get("think")  # low/high/none

        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key が未設定です。環境変数 'GEMINI_API_KEY'（または 'GOOGLE_API_KEY'）を設定してください。"
            )
        logger.info(
            f"GoogleVLMProvider initialized: model={self.model} "
            f"media={self.media_resolution} think={self.thinking_level}"
        )

    def _build_generation_config(
        self, max_tokens: int, temperature: float
    ) -> Dict[str, Any]:
        gen: Dict[str, Any] = {
            "temperature": float(temperature),
            "maxOutputTokens": int(max_tokens),
            "responseMimeType": "application/json",
        }
        if self.media_resolution:
            gen["mediaResolution"] = _MEDIA_MAP.get(
                self.media_resolution.lower(), self.media_resolution
            )
        if self.thinking_level and self.thinking_level.lower() != "none":
            gen["thinkingConfig"] = {"thinkingLevel": self.thinking_level.lower()}
        return gen

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        cand = (data.get("candidates") or [{}])[0]
        finish = cand.get("finishReason")
        text = "".join(
            p.get("text", "")
            for p in cand.get("content", {}).get("parts", [])
            if "text" in p
        )
        if not text:
            raise ValueError(
                f"[Google Provider] 応答テキストが空です。finishReason={finish}, "
                f"promptFeedback={data.get('promptFeedback')}"
            )
        return text

    @staticmethod
    def _validate_json(text: str) -> str:
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            # responseMimeType=json でも稀に markdown fence が付くことへの保険
            cleaned = text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```", 2)[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip().rstrip("`").strip()
            json.loads(cleaned)  # 失敗時は例外を送出（no fallback）
            return cleaned

    @staticmethod
    def _usage(data: Dict[str, Any]) -> Dict[str, Any]:
        um = data.get("usageMetadata", {})
        return {
            "prompt_tokens": um.get("promptTokenCount", 0),
            "completion_tokens": um.get("candidatesTokenCount", 0),
            "total_tokens": um.get("totalTokenCount", 0),
        }

    async def _generate(
        self, parts: list, max_tokens: int, temperature: float
    ) -> Dict[str, Any]:
        body = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": self._build_generation_config(max_tokens, temperature),
        }
        url = f"{_BASE_URL}/models/{self.model}:generateContent"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                url, json=body, headers={"x-goog-api-key": self.api_key}
            )
            r.raise_for_status()
            return r.json()

    async def analyze_image(
        self,
        image_bytes: bytes,
        image_mime_type: str = "image/jpeg",
        prompt: str = "Describe what you see in this image.",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
        return_usage: bool = False,
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        from ...config import get_settings

        settings = get_settings()
        if max_tokens is None:
            max_tokens = settings.VLM_MAX_TOKENS
        if temperature is None:
            temperature = settings.VLM_TEMPERATURE

        b64 = base64.b64encode(image_bytes).decode("utf-8")
        parts = [
            {"text": prompt},
            {"inline_data": {"mime_type": image_mime_type, "data": b64}},
        ]
        logger.info(
            f"🖼️  Gemini native generateContent: model={self.model} "
            f"media={self.media_resolution} think={self.thinking_level} temp={temperature}"
        )
        try:
            data = await self._generate(parts, max_tokens, temperature)
        except Exception as e:
            logger.error(f"Google VLM API call failed: {e}")
            raise RuntimeError(f"[Google Provider] API call failed: {e}") from e

        text = self._validate_json(self._extract_text(data))
        usage = self._usage(data)
        if return_usage:
            return text, usage
        return text

    async def analyze_text(
        self,
        text: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        return_usage: bool = False,
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        from ...config import get_settings

        settings = get_settings()
        if max_tokens is None:
            max_tokens = settings.VLM_MAX_TOKENS
        if temperature is None:
            temperature = settings.VLM_TEMPERATURE

        parts = [{"text": f"{prompt}\n\n{text}"}]
        data = await self._generate(parts, max_tokens, temperature)
        out = self._validate_json(self._extract_text(data))
        usage = self._usage(data)
        if return_usage:
            return out, usage
        return out
