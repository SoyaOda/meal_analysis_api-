# Freeform USDA Meal Analysis API - 耐障害性・パフォーマンス改善計画

## 概要

本ドキュメントは、`apps/freeform_usda_meal_analysis_api` の速度・安定性・ベストプラクティス観点での改善方針を、業界標準のリサーチに基づいて詳細に記述したものである。

**作成日**: 2024-12-23
**最終更新**: 2024-12-23（P0-P3全て実装完了）
**対象**: Freeform USDA Meal Analysis API v1.0.0

---

## 1. 現状分析

### 1.1 アーキテクチャ概要

```
[クライアント]
    ↓
[FastAPI Server (port 8006)]
    ↓
[Pipeline]
    ├─ Phase 1: VLM Analysis (OpenRouter/DeepInfra)
    ├─ Phase 2: USDA Food Search (Embedding + Reranker)
    └─ Phase 3: Nutrition Calculation
```

### 1.2 現在の実装状況

| 項目 | 現状 | 評価 |
|------|------|------|
| HTTP接続管理 | httpx.Timeout設定あり (connect=10s, read=180s) | ✅ 良好 |
| 自動リトライ | tenacity による Exponential Backoff + Jitter | ✅ **P0実装済** |
| VLMキャッシュ | 画像+プロンプト+モデルIDでキャッシュ | ✅ **P1実装済** |
| Embeddingキャッシュ | テキスト+モデルでキャッシュ | ✅ **P2実装済** |
| Circuit Breaker | aiobreaker による障害時フェイルファスト | ✅ **P3実装済** |
| 並列処理 | Phase 2 の Reranker で asyncio.gather() | ⚠️ 部分的 |
| エラーハンドリング | リトライ + Circuit Breaker で強化済み | ✅ 良好 |

### 1.3 主要な外部依存

1. **VLM API** (OpenRouter/DeepInfra) - レイテンシ: 2-10秒
2. **Embedding API** (DeepInfra/Novita) - レイテンシ: 100-500ms
3. **Reranker API** (DeepInfra) - レイテンシ: 200-800ms
4. **Firestore** (Config管理) - レイテンシ: 50-200ms

---

## 2. ベストプラクティス・リサーチ結果

### 2.1 リトライ戦略

**参考資料**:
- [OpenAI Cookbook - How to handle rate limits](https://cookbook.openai.com/examples/how_to_handle_rate_limits)
- [Markaicode - LLM API Retry Logic Implementation](https://markaicode.com/llm-api-retry-logic-implementation/)
- [Instructor - Python Retry Logic with Tenacity](https://python.useinstructor.com/concepts/retrying/)

**業界標準の推奨設定**:

```python
# 推奨リトライパラメータ
MAX_RETRIES = 3-5
BASE_DELAY = 1.0秒
MAX_DELAY = 60秒
RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]
```

**Exponential Backoff with Jitter**:
```python
import random

def get_backoff_delay(attempt: int, base: float = 1.0, max_delay: float = 60.0) -> float:
    """Jitter付き指数バックオフ"""
    delay = min(base * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)  # 10% jitter
    return delay + jitter
```

**Retry-Afterヘッダーの優先**:
```python
if "Retry-After" in response.headers:
    delay = int(response.headers["Retry-After"])
else:
    delay = get_backoff_delay(attempt)
```

### 2.2 キャッシュ戦略

**参考資料**:
- [Redis - What is Semantic Caching](https://redis.io/blog/what-is-semantic-caching/)
- [RedisVL - LLM Caching Guide](https://redis.io/docs/latest/develop/ai/redisvl/user_guide/llmcache/)
- [GPTCache - Semantic cache for LLMs](https://github.com/zilliztech/GPTCache)

**2段階キャッシュアーキテクチャ**:

```
[クエリ]
    ↓
[L1: Exact Match Cache (In-Memory LRU)]
    ↓ (miss)
[L2: Semantic Cache (Redis + Vector)]
    ↓ (miss)
[LLM API]
    ↓
[Cache Update]
```

**期待効果（業界ベンチマーク）**:
- キャッシュヒット時レイテンシ: 45ms（API呼び出し: 2100ms）
- コスト削減: 60-90%
- 推奨類似度閾値: 0.95（高精度）〜 0.85（高ヒット率）

**VLM画像キャッシュの特殊考慮**:
- 画像ハッシュ（SHA256）による完全一致キャッシュ
- **キャッシュキー = 画像ハッシュ + プロンプトハッシュ + モデルID**（重要）
- TTL: 24時間〜7日間（ユースケースに依存）

> **重要**: モデルIDをキャッシュキーに含めないと、異なるモデルで同じ画像を分析した際に誤った結果が返される。
> 例: GPT-4Vの結果がGeminiリクエスト時にキャッシュヒットしてしまう問題を防止。

### 2.3 Circuit Breaker パターン

**参考資料**:
- [PyBreaker - Circuit Breaker for Python](https://github.com/danielfm/pybreaker)
- [aiobreaker - Async Circuit Breaker](https://github.com/arlyon/aiobreaker)
- [CodeReliant - Circuit Breaker Pattern](https://www.codereliant.io/p/circuit-breaker-pattern)

**推奨パラメータ**:
```python
FAILURE_THRESHOLD = 5      # 連続失敗でOPEN
RECOVERY_TIMEOUT = 30      # OPENからHALF-OPENまでの秒数
SUCCESS_THRESHOLD = 2      # CLOSEDに戻るための連続成功数
```

**状態遷移**:
```
CLOSED → (5連続失敗) → OPEN → (30秒後) → HALF-OPEN
                                              ↓
                            (成功) → CLOSED  (失敗) → OPEN
```

### 2.4 HTTP クライアント管理

**参考資料**:
- [HTTPX - Async Support](https://www.python-httpx.org/async/)
- [aiohttp - Request Lifecycle](https://docs.aiohttp.org/en/stable/http_request_lifecycle.html)
- [Speakeasy - Python HTTP Clients Comparison](https://www.speakeasy.com/blog/python-http-clients-requests-vs-httpx-vs-aiohttp)

**ベストプラクティス**:
1. **シングルトンクライアント**: ホットループでクライアントを再生成しない
2. **コネクションプーリング**: セッション/クライアントを再利用
3. **HTTP/2サポート**: 可能であればhttpxを使用（ネイティブHTTP/2対応）

```python
# グローバルクライアントパターン
class HTTPClientManager:
    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                http2=True
            )
        return cls._client
```

### 2.5 VLM API 特有の考慮事項

**参考資料**:
- [Fireworks AI - Vision Models Guide](https://docs.fireworks.ai/guides/querying-vision-language-models)
- [vLLM - Using VLMs](https://docs.vllm.ai/en/latest/models/vlm.html)

**推奨設定**:
- 画像サイズ: リサイズして5MB以下に
- タイムアウト: 120-180秒（VLMは処理時間が長い）
- プロンプトキャッシング: 長い会話ではURL参照を使用

---

## 3. 段階的改善計画

### Phase 0 (P0): 即時対応 - リトライ強化 [推定工数: 1-2日]

**目的**: API呼び出し失敗時の耐障害性を向上

**3.1 tenacity によるリトライロジック実装**

```python
# apps/freeform_usda_meal_analysis_api/core/retry.py

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log
)
import logging

logger = logging.getLogger(__name__)

# LLM API用リトライデコレータ
llm_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=60, jitter=5),
    retry=retry_if_exception_type((
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        RateLimitError,
        APIConnectionError,
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)

# Embedding/Reranker用リトライデコレータ（より短いタイムアウト）
embedding_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.5, max=10, jitter=2),
    retry=retry_if_exception_type((
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
```

**適用箇所**:
- `deepinfra_service.py`: VLM API呼び出し
- `embedding_providers.py`: Embedding API呼び出し
- `reranker_providers.py`: Reranker API呼び出し

**3.2 依存パッケージ追加**

```bash
pip install tenacity
```

`requirements.txt` に追加:
```
tenacity>=8.2.0
```

---

### Phase 1 (P1): VLM 画像キャッシュ [推定工数: 2-3日]

**目的**: 同一画像の再分析時のレイテンシ削減とコスト削減

**3.3 完全一致キャッシュ実装**

```python
# apps/freeform_usda_meal_analysis_api/core/vlm_cache.py

import hashlib
import json
import logging
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    response: Dict[str, Any]
    usage: Dict[str, Any]
    created_at: datetime
    model_id: str  # モデルIDも記録

class VLMCache:
    """VLM結果の完全一致キャッシュ

    キャッシュキーは「画像ハッシュ + プロンプトハッシュ + モデルID」の複合キー。
    これにより、同じ画像でも異なるモデルで分析した場合は別エントリとして扱われる。

    ユースケース:
    - モデル比較: GPT-4V vs Gemini vs Claude で同じ画像を分析 → 各モデルの結果を個別にキャッシュ
    - 再試行: 同じモデル・同じ画像 → キャッシュヒットで即座に結果を返す
    - プロンプト変更: Admin Panelでプロンプト変更後 → キャッシュミスで新しいAPIコール
    """

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._ttl = timedelta(hours=ttl_hours)
        self._lock = asyncio.Lock()

        # メトリクス
        self._hits = 0
        self._misses = 0

    def _compute_cache_key(self, image_bytes: bytes, prompt: str, model_id: str) -> str:
        """画像 + プロンプト + モデルIDから一意なキャッシュキーを生成

        Args:
            image_bytes: 画像データ
            prompt: VLMプロンプト
            model_id: VLMモデルID (例: "openrouter:openai/gpt-4-vision", "deepinfra:gemma-3-27b")

        Returns:
            キャッシュキー文字列
        """
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        model_hash = hashlib.sha256(model_id.encode()).hexdigest()[:8]
        return f"{image_hash}:{prompt_hash}:{model_hash}"

    async def get(self, image_bytes: bytes, prompt: str, model_id: str) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """キャッシュから結果を取得"""
        key = self._compute_cache_key(image_bytes, prompt, model_id)

        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                logger.debug(f"Cache MISS: {key[:16]}...")
                return None

            # TTLチェック
            if datetime.now() - entry.created_at > self._ttl:
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache EXPIRED: {key[:16]}...")
                return None

            self._hits += 1
            logger.info(f"Cache HIT: {key[:16]}... (hits={self._hits}, misses={self._misses})")
            return entry.response, entry.usage

    async def set(
        self,
        image_bytes: bytes,
        prompt: str,
        model_id: str,
        response: Dict[str, Any],
        usage: Dict[str, Any]
    ) -> None:
        """キャッシュに結果を保存"""
        key = self._compute_cache_key(image_bytes, prompt, model_id)

        async with self._lock:
            # LRU: 最大サイズ超過時は古いエントリを削除
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
                del self._cache[oldest_key]

            self._cache[key] = CacheEntry(
                response=response,
                usage=usage,
                created_at=datetime.now(),
                model_id=model_id
            )
            logger.info(f"Cache SET: {key[:32]}... model={model_id} (size={len(self._cache)})")

    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "size": len(self._cache),
            "max_size": self._max_size
        }

# グローバルインスタンス
_vlm_cache: Optional[VLMCache] = None

def get_vlm_cache() -> VLMCache:
    global _vlm_cache
    if _vlm_cache is None:
        _vlm_cache = VLMCache(max_size=1000, ttl_hours=24)
    return _vlm_cache
```

**3.4 VLMService への統合**

```python
# vlm_service.py の analyze_image メソッドを修正

async def analyze_image(self, image_bytes: bytes, ...) -> Tuple[Dict, Dict]:
    # キャッシュチェック（model_idを含めることで異なるモデル間での誤ヒットを防止）
    cache = get_vlm_cache()
    cached = await cache.get(image_bytes, self.prompt, self.model_id)
    if cached:
        response, usage = cached
        # キャッシュヒットをusageに記録
        usage["cached"] = True
        logger.info(f"VLM Cache HIT for model={self.model_id}")
        return response, usage

    # API呼び出し（既存ロジック）
    raw_response, usage = await self.provider.analyze_image(...)

    # パース成功後にキャッシュ保存
    vlm_response = json.loads(raw_response)
    usage["cached"] = False
    await cache.set(image_bytes, self.prompt, self.model_id, vlm_response, usage)

    return vlm_response, usage
```

**キャッシュキー設計のポイント**:

| 操作 | キャッシュキー | 結果 |
|------|---------------|------|
| GPT-4V + 画像A | `abc123:def456:gpt4v` | API呼び出し → キャッシュ保存 |
| Gemini + 画像A | `abc123:def456:gemini` | API呼び出し → キャッシュ保存（別エントリ） |
| GPT-4V + 画像A（再試行） | `abc123:def456:gpt4v` | **キャッシュヒット** |
| GPT-4V + 画像A + 新プロンプト | `abc123:xyz789:gpt4v` | API呼び出し（プロンプト変更）|

---

### Phase 2 (P2): Embedding/Reranker キャッシュ [推定工数: 1-2日]

**目的**: 同一クエリの Embedding 再計算を防止

**3.5 Embedding キャッシュ実装**

```python
# apps/freeform_usda_meal_analysis_api/core/embedding_cache.py

import hashlib
from typing import List, Dict, Optional
from functools import lru_cache

class EmbeddingCache:
    """Embedding結果のインメモリキャッシュ"""

    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, List[float]] = {}
        self._max_size = max_size

    def _compute_key(self, text: str, model: str) -> str:
        combined = f"{model}:{text}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def get(self, text: str, model: str) -> Optional[List[float]]:
        key = self._compute_key(text, model)
        return self._cache.get(key)

    def set(self, text: str, model: str, embedding: List[float]) -> None:
        key = self._compute_key(text, model)
        if len(self._cache) >= self._max_size:
            # 簡易LRU: 10%削除
            keys_to_delete = list(self._cache.keys())[:self._max_size // 10]
            for k in keys_to_delete:
                del self._cache[k]
        self._cache[key] = embedding

    def get_batch(self, texts: List[str], model: str) -> Tuple[List[Optional[List[float]]], List[int]]:
        """バッチ取得: キャッシュヒット/ミスを分離"""
        results = []
        miss_indices = []
        for i, text in enumerate(texts):
            cached = self.get(text, model)
            results.append(cached)
            if cached is None:
                miss_indices.append(i)
        return results, miss_indices

# グローバルインスタンス
_embedding_cache = EmbeddingCache()

def get_embedding_cache() -> EmbeddingCache:
    return _embedding_cache
```

---

### Phase 3 (P3): Circuit Breaker 導入 [推定工数: 1-2日]

**目的**: 外部API障害時のカスケード障害を防止

**3.6 aiobreaker による実装**

```bash
pip install aiobreaker
```

```python
# apps/freeform_usda_meal_analysis_api/core/circuit_breakers.py

from aiobreaker import CircuitBreaker, CircuitBreakerListener
import logging

logger = logging.getLogger(__name__)

class LoggingListener(CircuitBreakerListener):
    """Circuit Breaker状態変化をログ出力"""

    def state_change(self, cb, old_state, new_state):
        logger.warning(f"Circuit Breaker '{cb.name}': {old_state.name} → {new_state.name}")

# VLM API用（高タイムアウト耐性）
vlm_breaker = CircuitBreaker(
    name="vlm_api",
    fail_max=5,
    reset_timeout=60,
    listeners=[LoggingListener()]
)

# Embedding API用
embedding_breaker = CircuitBreaker(
    name="embedding_api",
    fail_max=5,
    reset_timeout=30,
    listeners=[LoggingListener()]
)

# Reranker API用
reranker_breaker = CircuitBreaker(
    name="reranker_api",
    fail_max=5,
    reset_timeout=30,
    listeners=[LoggingListener()]
)
```

**3.7 サービスへの適用**

```python
# deepinfra_service.py

from ..core.circuit_breakers import vlm_breaker

class DeepInfraService:
    @vlm_breaker
    async def analyze_image(self, ...):
        # 既存ロジック
        ...
```

---

### ~~Phase 4 (P4): バッチ Embedding~~ ✅ 実装済み

> **注意**: この項目は `freeform_api_optimization_spec.md` に基づき既に実装されています。

**実装済みコード** (`deepinfra_service.py:294`):
```python
async def generate_embeddings(self, texts: List[str], ...) -> List[List[float]]:
    response = await self.client.embeddings.create(
        input=formatted_texts,  # ← リストで一括送信（バッチAPI呼び出し）
        model=model,
        encoding_format="float"
    )
    return [item.embedding for item in response.data]
```

**実装済みコード** (`pipeline.py:661-662`):
```python
# Phase 1: Batch embedding generation
embeddings = await self.food_search_service.batch_generate_embeddings(query_texts)
```

---

### ~~Redis セマンティックキャッシュ~~ ❌ 不採用

**不採用理由（Calorie Tracking App観点）**:

| 観点 | 評価 |
|------|------|
| VLM画像分析 | 画像は毎回ユニーク → セマンティック類似度が意味をなさない |
| 食材クエリ | "chicken" ≈ "grilled chicken" のマッチは可能だが... |
| インフラコスト | Redis運用コスト・複雑性が発生 |
| Embedding APIコスト | $0.0001/1K tokens と安価 → キャッシュ節約効果が小さい |
| 代替案 | インメモリLRUキャッシュで頻出クエリは十分カバー可能 |

**結論**: Calorie Tracking Appでは**インメモリキャッシュ（P2）で十分**であり、Redisセマンティックキャッシュは過剰投資となる。

---

## 4. Calorie Tracking App 向け考慮事項

本APIはカロリートラッキングアプリに組み込まれることを前提としている。
アプリ特有のユースケースを考慮した上での各Phaseの評価を以下に示す。

### 4.1 アプリの特性

- ユーザーが食事写真を撮影 → 即座に栄養情報が欲しい（リアルタイム性重視）
- モバイルネットワーク環境（不安定な接続が発生しやすい）
- 同じ画像の完全一致再送信は稀（撮影ごとに角度・照明が異なる）
- **ただし**: モデル比較や精度テストで同じ画像を異なる設定で送信するユーザーが存在
- 同じ食材クエリは繰り返される傾向（"chicken", "rice", "salad" 等）

### 4.2 Phase別 メリット・デメリット

| Phase | 項目 | メリット | デメリット | 状態 |
|-------|------|---------|-----------|------|
| **P0** | リトライ | モバイル環境での一時的接続エラーを自動回復。「再試行してください」表示を削減 | リトライ時に数秒の追加遅延（ただし失敗よりはるかに良い） | ✅ **実装済み** |
| **P1** | VLM画像キャッシュ | モデル比較時：各モデル結果を1回取得後、再比較が即座。誤タップ重複防止。デバッグ高速化 | メモリ消費増加（ただし軽微） | ✅ **実装済み** |
| **P2** | Embeddingキャッシュ | 頻出食材 "grilled chicken", "white rice" 等でAPI削減。レイテンシ300ms→1ms | メモリ消費増加（ただし軽微） | ✅ **実装済み** |
| **P3** | Circuit Breaker | API障害時に即座にエラー返却（30秒ハングより良いUX）。サーバーリソース節約 | エラーが即座に表示される（ただし正しい動作） | ✅ **実装済み** |
| ~~P4~~ | バッチEmbedding | 複数料理時のAPI呼び出し N回→1回に削減 | - | ✅ **実装済み** |
| ~~P4~~ | セマンティックキャッシュ | 類似クエリでヒット | Redisインフラ必要、コスト対効果が低い | ❌ **不採用** |

### 4.3 VLM画像キャッシュが有効なシナリオ

```
シナリオ1: モデル比較
  1. GPT-4Vで画像分析 → キャッシュ保存 (key: img:prompt:gpt4v)
  2. Geminiで同じ画像 → 新規API呼び出し (key: img:prompt:gemini)
  3. GPT-4Vに戻って確認 → キャッシュヒット！

シナリオ2: 誤タップによる重複リクエスト
  1. ユーザーが送信ボタンを2回タップ
  2. 1回目: API呼び出し → キャッシュ保存
  3. 2回目: キャッシュヒット → 即座に結果（重複課金なし）

シナリオ3: Admin Panelでのデバッグ
  1. 同じ画像で設定を微調整しながらテスト
  2. 設定変更なしの再テスト → キャッシュヒット
```

---

## 5. 実装状況

### 5.1 実装完了項目 ✅

| Phase | 改善項目 | 効果 | 実装ファイル |
|-------|---------|------|-------------|
| P0 | Retry with Exponential Backoff | 安定性 ⬆️⬆️⬆️ | `core/retry.py` |
| P1 | VLM 画像キャッシュ（model_id含む） | コスト ⬇️⬇️ / レイテンシ ⬇️⬇️ | `core/vlm_cache.py` |
| P2 | Embedding キャッシュ | レイテンシ ⬇️⬇️ | `core/embedding_cache.py` |
| P3 | Circuit Breaker | 安定性 ⬆️⬆️ | `core/circuit_breaker.py` |
| P4 | バッチ Embedding | レイテンシ ⬇️⬇️ | `deepinfra_service.py`, `pipeline.py` |

### 5.2 不採用項目

| 項目 | 理由 |
|------|------|
| Redis セマンティックキャッシュ | Calorie Tracking Appではコスト対効果が低い |

---

## 6. 期待効果

### 6.1 レイテンシ改善

| シナリオ | 現状 | 改善後 | 削減率 |
|---------|------|--------|--------|
| VLM キャッシュヒット | 3-5秒 | 50ms | **98%** |
| Embedding キャッシュヒット | 300ms | 1ms | **99%** |
| リトライによる回復 | 失敗 | 成功 | **可用性向上** |

### 6.2 コスト削減（月間推定）

- VLM API: 10,000リクエスト/月 → 60%ヒット率で4,000リクエスト
- 推定コスト削減: **60%**（$30 → $12/月）

### 6.3 可用性向上

- Circuit Breaker による障害時の即時フェイルファスト
- リトライによる一時的障害からの自動回復
- 目標: **99.5% → 99.9%** 可用性

---

## 7. 監視・メトリクス

### 7.1 追加すべきメトリクス

```python
# Prometheus形式のメトリクス例

# キャッシュメトリクス
vlm_cache_hits_total
vlm_cache_misses_total
vlm_cache_size

# Circuit Breaker メトリクス
circuit_breaker_state{name="vlm_api"}  # 0=CLOSED, 1=OPEN, 2=HALF_OPEN
circuit_breaker_failures_total{name="vlm_api"}

# リトライメトリクス
api_retries_total{service="vlm", attempt="1|2|3"}
```

### 7.2 アラート設定

- キャッシュヒット率が50%以下に低下
- Circuit Breaker が OPEN 状態に移行
- リトライ3回失敗が1分間に10回以上発生

---

## 8. 参考リンク

### リトライ・エラーハンドリング
- [OpenAI Cookbook - Rate Limits](https://cookbook.openai.com/examples/how_to_handle_rate_limits)
- [Tenacity Documentation](https://python.useinstructor.com/concepts/retrying/)
- [Markaicode - LLM Error Handling](https://markaicode.com/llm-error-handling-production-guide/)

### キャッシュ戦略
- [Redis - Semantic Caching](https://redis.io/blog/what-is-semantic-caching/)
- [RedisVL - LLM Caching](https://redis.io/docs/latest/develop/ai/redisvl/user_guide/llmcache/)
- [GPTCache GitHub](https://github.com/zilliztech/GPTCache)

### Circuit Breaker
- [PyBreaker GitHub](https://github.com/danielfm/pybreaker)
- [aiobreaker Documentation](https://aiobreaker.netlify.app/)

### HTTP クライアント
- [HTTPX Async Support](https://www.python-httpx.org/async/)
- [aiohttp Request Lifecycle](https://docs.aiohttp.org/en/stable/http_request_lifecycle.html)

### VLM 特有
- [Fireworks AI Vision Models](https://docs.fireworks.ai/guides/querying-vision-language-models)
- [vLLM Using VLMs](https://docs.vllm.ai/en/latest/models/vlm.html)

---

## 9. 次のアクション

1. **P0 実装開始**: `tenacity` パッケージのインストールとリトライデコレータの実装
2. **テスト環境準備**: 障害シミュレーション用のモックサーバー構築
3. **メトリクス設計**: Prometheus/Datadogへのメトリクス送信設計
4. **段階的デプロイ**: カナリアリリースで効果測定

---

*本ドキュメントは継続的に更新される予定です。*
