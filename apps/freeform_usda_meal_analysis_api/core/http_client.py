"""
グローバルHTTPクライアント管理

アプリケーション全体でコネクションプールを共有し、
接続の再利用によるオーバーヘッドを削減する。

使用例:
    from ..core.http_client import get_async_client

    client = get_async_client()
    response = await client.post(url, json=payload, headers=headers)
"""

import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# グローバルな非同期HTTPクライアント
_async_client: Optional[httpx.AsyncClient] = None


def get_async_client() -> httpx.AsyncClient:
    """
    グローバルな非同期HTTPクライアントを取得

    シングルトンパターンでクライアントを管理し、
    コネクションプールを再利用する。

    Returns:
        httpx.AsyncClient: 共有HTTPクライアント
    """
    global _async_client

    if _async_client is None:
        logger.info("🔧 Initializing global async HTTP client...")

        _async_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=100,          # 最大同時接続数
                max_keepalive_connections=20, # Keep-Alive接続の最大数
                keepalive_expiry=30.0,        # Keep-Alive接続の有効期限（秒）
            ),
            timeout=httpx.Timeout(
                connect=10.0,   # 接続タイムアウト
                read=120.0,     # 読み取りタイムアウト（Reranker APIは時間がかかることがある）
                write=30.0,     # 書き込みタイムアウト
                pool=10.0,      # プール取得タイムアウト
            ),
            # HTTP/2サポートを有効化（接続多重化で高速化）
            # 要件: pip install httpx[http2]
            http2=True,
        )

        logger.info("✅ Global async HTTP client initialized")
        logger.info(f"   Max connections: 100, Keep-alive: 20")

    return _async_client


async def close_async_client() -> None:
    """
    HTTPクライアントを安全にクローズ

    アプリケーションのシャットダウン時に呼び出す。
    """
    global _async_client

    if _async_client is not None:
        logger.info("🔧 Closing global async HTTP client...")
        await _async_client.aclose()
        _async_client = None
        logger.info("✅ Global async HTTP client closed")


async def health_check_client() -> bool:
    """
    HTTPクライアントのヘルスチェック

    Returns:
        bool: クライアントが正常に動作している場合True
    """
    global _async_client

    if _async_client is None:
        return False

    try:
        # クライアントが閉じられていないか確認
        return not _async_client.is_closed
    except Exception:
        return False
