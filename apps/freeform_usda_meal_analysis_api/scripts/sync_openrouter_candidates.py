#!/usr/bin/env python3
"""Fetch and filter OpenRouter model catalog for PDCA experiments."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.request import urlopen

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


def parse_price_per_million(value: Any) -> float | None:
    """Convert OpenRouter per-token string to USD per 1M tokens."""
    if value is None:
        return None
    try:
        parsed = float(value) * 1_000_000
        if parsed < 0:
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def has_image_input(model: Dict[str, Any]) -> bool:
    arch = model.get("architecture") or {}
    input_modalities = arch.get("input_modalities") or []
    modality = (arch.get("modality") or "").lower()
    return "image" in input_modalities or "image" in modality


def supports_reasoning_control(model: Dict[str, Any]) -> bool:
    supported = set(model.get("supported_parameters") or [])
    return "reasoning" in supported or "include_reasoning" in supported


def filter_models(
    models: List[Dict[str, Any]],
    max_prompt_price: float,
    max_completion_price: float,
    thinking_only: bool,
    require_image: bool,
    exclude_patterns: List[str],
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    for model in models:
        raw_id = str(model.get("id", ""))
        if any(re.search(pattern, raw_id) for pattern in exclude_patterns):
            continue

        if require_image and not has_image_input(model):
            continue

        has_reasoning = supports_reasoning_control(model)
        if thinking_only and not has_reasoning:
            continue

        pricing = model.get("pricing") or {}
        prompt_price = parse_price_per_million(pricing.get("prompt"))
        completion_price = parse_price_per_million(pricing.get("completion"))

        if prompt_price is None or completion_price is None:
            continue

        if prompt_price > max_prompt_price:
            continue

        if completion_price > max_completion_price:
            continue

        candidate = {
            "model_id": f"openrouter:{raw_id}",
            "raw_model_id": raw_id,
            "name": model.get("name"),
            "prompt_price_per_million_usd": round(prompt_price, 6),
            "completion_price_per_million_usd": round(completion_price, 6),
            "image_price_per_million_usd": parse_price_per_million(pricing.get("image")),
            "internal_reasoning_price_per_million_usd": parse_price_per_million(pricing.get("internal_reasoning")),
            "context_length": model.get("context_length"),
            "max_completion_tokens": (model.get("top_provider") or {}).get("max_completion_tokens"),
            "supports_reasoning_control": has_reasoning,
            "supported_parameters": model.get("supported_parameters") or [],
            "input_modalities": (model.get("architecture") or {}).get("input_modalities") or [],
            "recommended_reasoning_effort": "medium" if has_reasoning else None,
            "score": round(prompt_price + completion_price, 6),
        }
        candidates.append(candidate)

    candidates.sort(key=lambda x: (x["score"], x["model_id"]))
    return candidates


def load_models() -> List[Dict[str, Any]]:
    with urlopen(OPENROUTER_MODELS_URL, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("data") or []


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync OpenRouter model candidates")
    parser.add_argument("--max-prompt-price", type=float, default=3.0, help="USD per 1M input tokens")
    parser.add_argument("--max-completion-price", type=float, default=15.0, help="USD per 1M output tokens")
    parser.add_argument("--thinking-only", action="store_true", help="Keep models with reasoning controls only")
    parser.add_argument(
        "--require-image",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require image input support (--no-require-image to disable)",
    )
    parser.add_argument("--top-n", type=int, default=40, help="Keep top N by blended price score")
    parser.add_argument(
        "--exclude-pattern",
        action="append",
        default=[r"^openrouter/auto$", r"^openrouter/free$", r":free$"],
        help="Regex pattern for model IDs to exclude (can be repeated)",
    )
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    args = parser.parse_args()

    models = load_models()

    candidates = filter_models(
        models=models,
        max_prompt_price=args.max_prompt_price,
        max_completion_price=args.max_completion_price,
        thinking_only=args.thinking_only,
        require_image=args.require_image,
        exclude_patterns=args.exclude_pattern,
    )

    if args.top_n > 0:
        candidates = candidates[: args.top_n]

    now = datetime.now(timezone.utc)
    default_output = (
        Path("apps/freeform_usda_meal_analysis_api/evals/catalog")
        / f"openrouter_candidates_{now.strftime('%Y%m%d')}.json"
    )
    output_path = Path(args.output) if args.output else default_output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "generated_at_utc": now.isoformat(),
        "source": OPENROUTER_MODELS_URL,
        "filters": {
            "max_prompt_price_per_million_usd": args.max_prompt_price,
            "max_completion_price_per_million_usd": args.max_completion_price,
            "thinking_only": args.thinking_only,
            "require_image": args.require_image,
            "exclude_patterns": args.exclude_pattern,
            "top_n": args.top_n,
        },
        "total_models_received": len(models),
        "total_candidates": len(candidates),
        "candidates": candidates,
    }

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved: {output_path}")
    print(f"Models received: {len(models)}")
    print(f"Candidates: {len(candidates)}")
    for item in candidates[:10]:
        print(
            f"- {item['model_id']} "
            f"(in=${item['prompt_price_per_million_usd']}/1M, out=${item['completion_price_per_million_usd']}/1M, "
            f"reasoning={item['supports_reasoning_control']})"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
