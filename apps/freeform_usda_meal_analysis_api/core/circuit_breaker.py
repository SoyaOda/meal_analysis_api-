"""
Circuit Breaker

外部API障害時のカスケード障害を防止し、即座にフェイルファストする。
aiobreaker を使用した非同期対応 Circuit Breaker パターンの実装。

状態遷移:
- CLOSED: 正常状態。リクエストを通す。
- OPEN: 障害検出。リクエストを即座に拒否（fail_max連続失敗で遷移）
- HALF-OPEN: 回復確認中。一部のリクエストを通す（reset_timeout後に遷移）

使用例:
    from ..core.circuit_breaker import vlm_breaker, embedding_breaker

    # デコレータとして使用
    @vlm_breaker
    async def call_vlm_api(...):
        ...

    # コンテキストマネージャとして使用
    async with vlm_breaker:
        response = await api_call()
"""

import logging
from typing import Optional, Dict, Any

try:
    from aiobreaker import CircuitBreaker, CircuitBreakerListener
    AIOBREAKER_AVAILABLE = True
except ImportError:
    AIOBREAKER_AVAILABLE = False
    CircuitBreaker = None
    CircuitBreakerListener = None

logger = logging.getLogger(__name__)


def _get_state_name(state) -> str:
    """状態オブジェクトから状態名を取得"""
    class_name = type(state).__name__
    # CircuitClosedState -> closed, CircuitOpenState -> open, etc.
    return class_name.replace("Circuit", "").replace("State", "").lower()


class LoggingListener:
    """Circuit Breaker状態変化をログ出力するリスナー

    CircuitBreakerListener の全メソッドを実装:
    - before_call: 呼び出し前
    - success: 成功時
    - failure: 失敗時
    - state_change: 状態変化時
    """

    def before_call(self, cb, func, *args, **kwargs):
        """呼び出し前のコールバック"""
        pass  # ログ不要

    def success(self, cb):
        """成功時のコールバック"""
        pass  # 成功は通常ログ不要

    def failure(self, cb, exception):
        """失敗時のコールバック"""
        logger.warning(
            f"⚠️ Circuit Breaker '{cb.name}': failure recorded - {type(exception).__name__}"
        )

    def state_change(self, cb, old_state, new_state):
        """状態変化時のコールバック"""
        old_name = _get_state_name(old_state)
        new_name = _get_state_name(new_state)
        logger.warning(
            f"🔌 Circuit Breaker '{cb.name}': {old_name} → {new_name}"
        )

        if new_name == "open":
            logger.error(
                f"❌ Circuit Breaker '{cb.name}' OPEN - API calls will be rejected"
            )
        elif new_name == "closed":
            logger.info(
                f"✅ Circuit Breaker '{cb.name}' CLOSED - API calls resumed"
            )


def _create_circuit_breaker(
    name: str,
    fail_max: int = 5,
    timeout_seconds: int = 60,
    exclude: tuple = ()
) -> Optional[CircuitBreaker]:
    """
    Circuit Breaker を作成

    Args:
        name: Circuit Breaker 名（ログ識別用）
        fail_max: OPEN に遷移する連続失敗回数
        timeout_seconds: OPEN から HALF-OPEN に遷移するまでの秒数
        exclude: リトライ対象から除外する例外タイプ

    Returns:
        CircuitBreaker インスタンス（aiobreaker未インストール時はNone）
    """
    from datetime import timedelta

    if not AIOBREAKER_AVAILABLE:
        logger.warning(
            f"aiobreaker not installed - Circuit Breaker '{name}' disabled. "
            "Install with: pip install aiobreaker"
        )
        return None

    breaker = CircuitBreaker(
        name=name,
        fail_max=fail_max,
        timeout_duration=timedelta(seconds=timeout_seconds),
        exclude=exclude,
        listeners=[LoggingListener()]
    )

    logger.info(
        f"🔌 Circuit Breaker '{name}' initialized: "
        f"fail_max={fail_max}, timeout={timeout_seconds}s"
    )

    return breaker


# VLM API用 Circuit Breaker
# 処理時間が長いため、timeout を長めに設定
vlm_breaker = _create_circuit_breaker(
    name="vlm_api",
    fail_max=5,
    timeout_seconds=60,  # 1分後に再試行
)

# Embedding API用 Circuit Breaker
embedding_breaker = _create_circuit_breaker(
    name="embedding_api",
    fail_max=5,
    timeout_seconds=30,
)

# Reranker API用 Circuit Breaker
reranker_breaker = _create_circuit_breaker(
    name="reranker_api",
    fail_max=5,
    timeout_seconds=30,
)


def get_breaker_stats() -> Dict[str, Any]:
    """
    全 Circuit Breaker の統計情報を取得

    Returns:
        各 Circuit Breaker の状態と統計
    """
    if not AIOBREAKER_AVAILABLE:
        return {"error": "aiobreaker not installed"}

    stats = {}

    for name, breaker in [
        ("vlm_api", vlm_breaker),
        ("embedding_api", embedding_breaker),
        ("reranker_api", reranker_breaker),
    ]:
        if breaker is not None:
            stats[name] = {
                "state": _get_state_name(breaker.state),
                "fail_counter": breaker.fail_counter,
                "fail_max": breaker.fail_max,
                "timeout_duration": str(breaker.timeout_duration),
            }

    return stats


def reset_all_breakers() -> None:
    """全 Circuit Breaker をリセット（デバッグ/テスト用）"""
    if not AIOBREAKER_AVAILABLE:
        return

    for name, breaker in [
        ("vlm_api", vlm_breaker),
        ("embedding_api", embedding_breaker),
        ("reranker_api", reranker_breaker),
    ]:
        if breaker is not None:
            breaker.close()
            logger.info(f"🔌 Circuit Breaker '{name}' reset to CLOSED")


def with_circuit_breaker(breaker):
    """
    Circuit Breaker を条件付きで適用するデコレータファクトリ

    aiobreaker がインストールされていない場合は、元の関数をそのまま返す。

    使用例:
        @with_circuit_breaker(vlm_breaker)
        async def call_api(...):
            ...
    """
    def decorator(func):
        if breaker is None:
            # Circuit Breaker が無効な場合は元の関数をそのまま返す
            return func

        # Circuit Breaker でラップ（aiobreaker はデコレータとして動作）
        wrapped = breaker(func)

        # メタデータを保持
        wrapped.__name__ = func.__name__
        wrapped.__doc__ = func.__doc__
        return wrapped

    return decorator
