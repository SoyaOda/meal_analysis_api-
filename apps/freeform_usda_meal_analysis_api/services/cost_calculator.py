#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Token使用量とコスト計算サービス
"""

import json
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CostCalculator:
    """
    Token使用量からコストを計算するサービス

    model_pricing.jsonを読み込んで各モデルの価格情報を保持し、
    token数からコストを計算する。
    """

    def __init__(self, pricing_file: Optional[str] = None):
        """
        Args:
            pricing_file: model_pricing.jsonのパス（Noneの場合はデフォルト）
        """
        if pricing_file is None:
            # デフォルト: config/model_pricing.json
            pricing_file = str(Path(__file__).parent.parent / "config" / "model_pricing.json")

        self.pricing_file = Path(pricing_file)
        self.pricing_data: Dict = {}

        # ロード実行
        self._load_pricing_data()

    def _load_pricing_data(self):
        """model_pricing.jsonから価格情報をロード"""
        logger.info(f"📂 Loading model pricing data from: {self.pricing_file}")

        with open(self.pricing_file, 'r', encoding='utf-8') as f:
            self.pricing_data = json.load(f)

        model_count = len(self.pricing_data.get("models", {}))
        logger.info(f"✅ Loaded pricing data for {model_count} models")

    def get_model_pricing(self, model_id: str) -> Dict[str, float]:
        """
        指定されたモデルの価格情報を取得

        Args:
            model_id: モデルID（例: "Qwen/Qwen3-VL-30B-A3B-Thinking"）

        Returns:
            {
                "input_price_per_million": float,
                "output_price_per_million": float
            }
        """
        models = self.pricing_data.get("models", {})

        if model_id in models:
            model_info = models[model_id]
            return {
                "input_price_per_million": model_info["input_price_per_million"],
                "output_price_per_million": model_info["output_price_per_million"]
            }

        # モデルが見つからない場合はデフォルトを使用
        logger.warning(f"Model '{model_id}' not found in pricing data, using default pricing")
        default_info = self.pricing_data.get("default", {})
        return {
            "input_price_per_million": default_info.get("input_price_per_million", 0.50),
            "output_price_per_million": default_info.get("output_price_per_million", 0.50)
        }

    def calculate_cost(
        self,
        model_id: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> Dict[str, any]:
        """
        Token使用量からコストを計算

        Args:
            model_id: モデルID
            prompt_tokens: 入力トークン数
            completion_tokens: 出力トークン数

        Returns:
            {
                "prompt_tokens": int,
                "completion_tokens": int,
                "total_tokens": int,
                "estimated_cost_usd": float,
                "model_pricing": {
                    "input_price_per_million": float,
                    "output_price_per_million": float
                }
            }
        """
        pricing = self.get_model_pricing(model_id)

        # コスト計算（per million tokens）
        input_cost = (prompt_tokens / 1_000_000) * pricing["input_price_per_million"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output_price_per_million"]
        total_cost = input_cost + output_cost

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": round(total_cost, 6),
            "model_pricing": pricing
        }
