"""OpenRouter クレジット残高のプリフライトチェック。

PDCA 評価や model-refresh サイクルの開始前に実行し、残高不足での
評価中断（2026-06-11 の事故: クレジット枯渇 402 → circuit breaker 開放 →
同一 run の後続候補が連鎖全滅 + 本番 API 停止）を防ぐ。

使い方:
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python -m \
        apps.freeform_usda_meal_analysis_api.scripts.check_openrouter_credits \
        --min-usd 10.0

残高が --min-usd 未満なら exit code 1（明確なエラーで止める。fallback しない）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import Optional

from dotenv import load_dotenv

CREDITS_ENDPOINT = "https://openrouter.ai/api/v1/credits"
DEFAULT_MIN_USD = 10.0
REQUEST_TIMEOUT_SEC = 15


def fetch_credits(api_key: str) -> dict:
    """OpenRouter credits API から残高情報を取得する。"""
    req = urllib.request.Request(
        CREDITS_ENDPOINT,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SEC) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"credits API の応答形式が想定外: {payload}")
    return data


def resolve_api_key() -> Optional[str]:
    """repo ルートの .env を含む環境から OPENROUTER_API_KEY を解決する。

    settings.py と同じく dotenv 経由（override=False のため、shell に古いキーが
    残っている場合は `env -u OPENROUTER_API_KEY` を付けて呼ぶこと）。
    """
    load_dotenv()
    return os.getenv("OPENROUTER_API_KEY")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--min-usd",
        type=float,
        default=DEFAULT_MIN_USD,
        help=f"必要残高（USD）。下回れば exit 1（default: {DEFAULT_MIN_USD}）",
    )
    args = parser.parse_args()

    api_key = resolve_api_key()
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY が解決できない（.env / 環境変数を確認）")
        return 1

    data = fetch_credits(api_key)
    total_credits = data.get("total_credits")
    total_usage = data.get("total_usage")
    if total_credits is None or total_usage is None:
        raise RuntimeError(f"credits API に total_credits/total_usage が無い: {data}")

    balance = float(total_credits) - float(total_usage)
    print(
        f"OpenRouter credits: total=${float(total_credits):.2f} used=${float(total_usage):.2f} balance=${balance:.2f}"
    )

    if balance < args.min_usd:
        print(
            f"NG: 残高 ${balance:.2f} < 必要額 ${args.min_usd:.2f} — 評価を開始しないこと。チャージ: https://openrouter.ai/settings/credits"
        )
        return 1
    print(f"OK: 残高 ${balance:.2f} >= ${args.min_usd:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
