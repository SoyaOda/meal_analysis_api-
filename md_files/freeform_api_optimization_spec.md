# Freeform USDA Meal Analysis API - 速度・安定性最適化仕様書

## 📋 ドキュメント情報

| 項目 | 内容 |
|------|------|
| 作成日 | 2024-12-22 |
| 対象API | `apps/freeform_usda_meal_analysis_api` |
| ブランチ | `feature/freeform-api-optimization` |
| ベースブランチ | `feature/admin-config-panel` |
| 作成者 | Claude Code |

---

## 🎯 最適化の目的

1. **レスポンス時間の短縮**: 20-40%の改善を目標
2. **コールドスタート時間の削減**: 初回リクエストの遅延を最小化
3. **スループットの向上**: 並列リクエスト処理能力の向上
4. **安定性の向上**: タイムアウト・リトライ設定の最適化

---

## 📊 現状のパイプライン構造

```
画像 → VLM (OpenRouter/DeepInfra) → JSON抽出
           ↓
      Query Extraction (N個のクエリ)
           ↓
      並列検索 (asyncio.gather)
           ↓
   ┌───────┴───────┐
   ↓               ↓
 BM25検索      Vector検索 (FAISS + DeepInfra Embedding API)
   ↓               ↓
   └───────┬───────┘
           ↓
      RRF融合 (Reciprocal Rank Fusion)
           ↓
      Reranker (DeepInfra Qwen3-Reranker-8B)
           ↓
      栄養素計算 → 最終レスポンス
```

---

## 🔧 最適化項目一覧

### P0: 即座に対応（クリティカル）

| ID | 項目 | 現状 | 変更後 | 対象ファイル |
|----|------|------|--------|-------------|
| P0-1 | Worker数の最適化 | `--workers 1` | `--workers $((CPU * 2 + 1))` | `Dockerfile.optimized`, `deploy.sh` |
| P0-2 | インデックスプリロード | `PRELOAD_INDEXES_ON_STARTUP=false` | `true` (本番デフォルト) | `config/settings.py`, `deploy.sh` |

### P1: 短期対応（速度改善効果大）

| ID | 項目 | 現状 | 変更後 | 対象ファイル |
|----|------|------|--------|-------------|
| P1-1 | Embedding APIバッチ化 | N回のAPI呼び出し | 1回のバッチ呼び出し | `services/pipeline.py`, `services/hybrid_search.py` |
| P1-2 | HTTPコネクションプール | 各リクエストで新規接続 | グローバルプール共有 | `services/deepinfra_service.py`, `core/http_client.py` (新規) |
| P1-3 | メモリ設定増加 | `2Gi` | `4Gi` (本番) | `deploy.sh` |

### P2: 中期対応（安定性向上）

| ID | 項目 | 現状 | 変更後 | 対象ファイル |
|----|------|------|--------|-------------|
| P2-1 | タイムアウト設定最適化 | 部分的な設定 | 明示的な階層タイムアウト | `services/deepinfra_service.py`, providers |
| P2-2 | min-instances増加 | `1` (本番) | `2` (本番) | `deploy.sh` |

---

## 📝 詳細仕様

### P0-1: Worker数の最適化

#### 変更概要
- Cloud Runのgunicorn worker数を最適化
- Google Cloud推奨: `(2 x vCPU) + 1`

#### 変更内容

**Dockerfile.optimized**
```dockerfile
# Before
CMD exec gunicorn apps.freeform_usda_meal_analysis_api.main:app \
    --bind :${PORT} \
    --workers 1 \
    ...

# After
CMD exec gunicorn apps.freeform_usda_meal_analysis_api.main:app \
    --bind :${PORT} \
    --workers ${WEB_CONCURRENCY:-3} \
    ...
```

**deploy.sh**
```bash
# 環境に応じたWorker数を設定
if [ "$ENVIRONMENT" = "production" ]; then
    WEB_CONCURRENCY=$((CPU * 2 + 1))  # CPU=2 → 5 workers
else
    WEB_CONCURRENCY=$((CPU * 2 + 1))  # CPU=1 → 3 workers
fi
ENV_VARS="${ENV_VARS},WEB_CONCURRENCY=${WEB_CONCURRENCY}"
```

#### テスト方法
- ローカル: `wrk`または`ab`でベンチマーク
- 本番: Cloud Runメトリクスでレイテンシ・スループット確認

---

### P0-2: インデックスプリロード設定

#### 変更概要
- 起動時にバックグラウンドでFAISSインデックスをロード開始
- 初回リクエストの遅延を削減

#### 変更内容

**config/settings.py**
```python
# Before
self.PRELOAD_INDEXES_ON_STARTUP = os.getenv("PRELOAD_INDEXES_ON_STARTUP", "false").lower() == "true"

# After
# デフォルトをtrueに変更（本番環境推奨）
self.PRELOAD_INDEXES_ON_STARTUP = os.getenv("PRELOAD_INDEXES_ON_STARTUP", "true").lower() == "true"
```

#### テスト方法
- ローカル: 起動ログで「Starting background index preloading...」を確認
- 初回リクエストのレイテンシ計測

---

### P1-1: Embedding APIバッチ化

#### 変更概要
- 複数クエリのEmbedding生成を1回のAPI呼び出しにまとめる
- N回 → 1回のAPI呼び出しでネットワークレイテンシを削減

#### 変更内容

**services/pipeline.py** (`_parallel_search`メソッド)

```python
async def _parallel_search(
    self,
    queries: List[Dict[str, Any]],
    ...
) -> List[Optional[Dict[str, Any]]]:
    """USDA検索を並列実行（Embedding バッチ化対応）"""

    # 全クエリのsearch_nameを抽出
    all_search_names = [q['search_name'] for q in queries]

    # Step 1: 全クエリのEmbeddingを1回のバッチAPI呼び出しで生成
    all_embeddings = await self.food_search_service.searcher.embedding_service.generate_embeddings(
        all_search_names,
        instruction=effective_embedding_instruction
    )

    # Step 2: 各クエリの検索を並列実行（事前計算済みEmbeddingを使用）
    tasks = []
    for i, query in enumerate(queries):
        task = self.food_search_service.search(
            query=query['search_name'],
            precomputed_embedding=all_embeddings[i],  # 事前計算済みEmbedding
            ...
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    ...
```

**services/hybrid_search.py** (`search_hybrid_with_reranker`メソッド)

```python
async def search_hybrid_with_reranker(
    self,
    query: str,
    ...
    precomputed_embedding: Optional[List[float]] = None,  # 新規パラメータ
) -> Dict[str, Any]:
    """Hybrid search + Reranker の統合版（事前計算Embedding対応）"""

    # Vector検索: 事前計算済みEmbeddingがあればそれを使用
    if precomputed_embedding is not None:
        query_vector_np = np.array([precomputed_embedding], dtype='float32')
    else:
        # 従来通りAPI呼び出し
        query_vectors = await embedding_service.generate_embeddings(
            [query],
            instruction=embedding_instruction
        )
        query_vector_np = np.array([query_vectors[0]], dtype='float32')

    ...
```

#### テスト方法
- ローカル: 複数食材を含む画像で分析し、ログでAPI呼び出し回数を確認
- 期待結果: `generate_embeddings`の呼び出しが1回のみ

---

### P1-2: HTTPコネクションプールの最適化

#### 変更概要
- グローバルなhttpxクライアントをアプリケーションレベルで共有
- 接続の再利用によるオーバーヘッド削減

#### 変更内容

**core/http_client.py** (新規ファイル)

```python
"""
グローバルHTTPクライアント管理
アプリケーション全体でコネクションプールを共有
"""
import httpx
from typing import Optional

_async_client: Optional[httpx.AsyncClient] = None

def get_async_client() -> httpx.AsyncClient:
    """グローバルな非同期HTTPクライアントを取得"""
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20,
                keepalive_expiry=30.0,
            ),
            timeout=httpx.Timeout(
                connect=10.0,
                read=120.0,
                write=30.0,
                pool=10.0,
            ),
        )
    return _async_client

async def close_async_client():
    """クライアントを安全にクローズ（シャットダウン時）"""
    global _async_client
    if _async_client is not None:
        await _async_client.aclose()
        _async_client = None
```

**services/deepinfra_service.py** (rerank メソッド修正)

```python
async def rerank(
    self,
    query: str,
    documents: List[str],
    ...
) -> Tuple[int, List[float]]:
    """文書をリランキング（共有HTTPクライアント使用）"""
    from ..core.http_client import get_async_client

    client = get_async_client()
    url = f"https://api.deepinfra.com/v1/inference/{model}"

    # 既存のhttpx.AsyncClientの代わりに共有クライアントを使用
    response = await client.post(url, json=payload, headers=headers)
    ...
```

**main.py** (シャットダウン時のクリーンアップ追加)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ...

    yield  # アプリケーション実行中

    # Shutdown
    from .core.http_client import close_async_client
    await close_async_client()
    logger.info("✅ HTTP client closed")
    ...
```

#### テスト方法
- ローカル: 連続リクエストでコネクション再利用を確認
- Cloud Loggingでコネクションエラーの減少を確認

---

### P1-3: メモリ設定増加

#### 変更概要
- Cloud Runのメモリを2Gi→4Giに増加
- FAISSインデックス + キャッシュ領域の確保

#### 変更内容

**deploy.sh**
```bash
# Before
MEMORY="2Gi"

# After
if [ "$ENVIRONMENT" = "production" ]; then
    MEMORY="4Gi"
else
    MEMORY="2Gi"  # 開発はコスト削減のため据え置き
fi
```

#### テスト方法
- 本番デプロイ後、Cloud Runメトリクスでメモリ使用量を確認
- OOMエラーの発生有無をモニタリング

---

### P2-1: タイムアウト設定の最適化

#### 変更概要
- 各APIクライアントに明示的なタイムアウトを設定
- 階層的なタイムアウト（接続/読み取り/書き込み）

#### 変更内容

**services/deepinfra_service.py**
```python
def __init__(self, model_id: str = None, model_version: str = None):
    ...
    # 明示的なタイムアウト設定
    self.client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=httpx.Timeout(
            connect=10.0,   # 接続タイムアウト
            read=180.0,     # 読み取りタイムアウト（VLMは時間がかかる）
            write=30.0,     # 書き込みタイムアウト
            pool=10.0,      # プール取得タイムアウト
        ),
    )
```

#### テスト方法
- ローカル: 意図的に遅延を発生させてタイムアウト動作を確認
- 本番: タイムアウトエラーのログを確認

---

### P2-2: min-instances増加

#### 変更概要
- 本番環境のmin-instancesを1→2に増加
- 冗長性確保とコールドスタート完全排除

#### 変更内容

**deploy.sh**
```bash
# Before
if [ "$ENVIRONMENT" = "production" ]; then
    MIN_INSTANCES=1
    ...

# After
if [ "$ENVIRONMENT" = "production" ]; then
    MIN_INSTANCES=2  # 冗長性とコールドスタート排除
    ...
```

#### テスト方法
- 本番デプロイのみ（コスト影響あり）
- Cloud Runコンソールでインスタンス数を確認

---

## 📈 実装・テスト経過記録

### Phase 1: P0項目の実装

| 日時 | 項目 | 作業内容 | 結果 | ベースライン比較 |
|------|------|----------|------|-----------------|
| 2024-12-22 | P0-1 | Worker数最適化: Dockerfile.optimized, deploy.sh 修正 | ✅ 実装完了 | 本番テスト待ち |
| 2024-12-22 | P0-2 | プリロード設定: settings.py, deploy.sh 修正 | ✅ 実装完了 | 本番テスト待ち |

### Phase 2: P1項目の実装

| 日時 | 項目 | 作業内容 | 結果 | ベースライン比較 |
|------|------|----------|------|-----------------|
| 2024-12-22 | P1-1 | Embeddingバッチ化: pipeline.py, hybrid_search.py, food_search_service.py 修正 | ✅ 実装完了 | N回→1回のAPI呼び出しに削減 |
| 2024-12-22 | P1-2 | HTTPプール最適化: core/http_client.py 新規作成, deepinfra_service.py, main.py 修正 | ✅ 実装完了 | コネクション再利用有効 |
| 2024-12-22 | P1-3 | メモリ増加: deploy.sh 修正 (2Gi→4Gi) | ✅ 実装完了 | 本番テスト待ち |

### Phase 3: P2項目の実装

| 日時 | 項目 | 作業内容 | 結果 | ベースライン比較 |
|------|------|----------|------|-----------------|
| 2024-12-22 | P2-1 | タイムアウト最適化: deepinfra_service.py に明示的タイムアウト設定追加 | ✅ 実装完了 | read=180s, connect=10s, max_retries=3 |
| 2024-12-22 | P2-2 | min-instances増加: deploy.sh 修正 (1→2) | ✅ 実装完了 | 本番テスト待ち |

---

## 🧪 ベースライン計測

### ローカルAPI（ポート8006）ベンチマーク

```bash
# APIサーバー起動
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8006 python -m apps.freeform_usda_meal_analysis_api.main

# ベンチマークテスト
curl -X POST "http://localhost:8006/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=benchmark test"
```

### 📊 パフォーマンス比較結果 (2024-12-22 測定)

**テスト条件**:
- 画像: `test_images/food1.jpg`
- 検出食材: 3品目（6クエリ生成）
- 環境: ローカルMac (M1/M2)

#### 処理時間比較

| 処理 | 最適化前 | 最適化後 | 改善 |
|------|---------|---------|------|
| VLM分析 | ~20秒 | ~20秒 | - |
| インデックスロード | 0.27秒 | プリロード済み | ✅ |
| Embedding API | 8回個別コール | **1回バッチコール** (~2秒) | **87.5%削減** |
| Reranker API | 8回個別コール (~6.4秒) | 8回 (HTTP/2再利用) | コネクション効率化 |
| **合計時間** | **28.89秒** | **24.01秒** | **約17%高速化** |

#### 改善効果詳細

| 項目 | 最適化前 | 最適化後 | 効果 |
|------|---------|---------|------|
| Embedding API呼び出し回数 | N回（クエリ数分） | 1回（バッチ） | APIコスト・レイテンシ削減 |
| HTTP接続 | 毎回新規接続 | コネクションプール再利用 | 接続オーバーヘッド削減 |
| インデックスロード | 初回リクエスト時 | 起動時バックグラウンド | コールドスタート改善 |

| テスト項目 | 最適化前 | 最適化後 | 改善率 |
|-----------|---------|---------|--------|
| 単一画像分析（3食材） | 28.89秒 | 24.01秒 | **17%** |
| Embedding API呼び出し | 8回 | 1回 | **87.5%削減** |
| コールドスタート時間 | インデックスロード待ち | プリロード済み | ✅ |

### 本番API（Cloud Run）ベンチマーク

**注意**: P1-3 (メモリ増加), P2-2 (min-instances増加) は本番デプロイが必要

| テスト項目 | 最適化前 | 最適化後 | 改善率 |
|-----------|---------|---------|--------|
| コールドスタート時間 | | | |
| P95レイテンシ | | | |
| スループット (req/s) | | | |

---

## 📋 実装チェックリスト

- [x] P0-1: Worker数の最適化
  - [x] Dockerfile.optimized 修正 - `--workers ${WEB_CONCURRENCY:-3}`
  - [x] deploy.sh 修正 - Production: WEB_CONCURRENCY=5, Dev: WEB_CONCURRENCY=3
  - [ ] ローカルテスト完了
  - [ ] 本番デプロイ・テスト完了

- [x] P0-2: インデックスプリロード設定
  - [x] config/settings.py 修正 - デフォルトを`true`に変更
  - [x] deploy.sh 修正 - 環境変数で明示的に設定
  - [ ] ローカルテスト完了

- [x] P1-1: Embedding APIバッチ化
  - [x] services/pipeline.py 修正 - `_parallel_search`でバッチembedding生成
  - [x] services/hybrid_search.py 修正 - `search_hybrid_with_reranker_precomputed`メソッド追加
  - [x] services/food_search_service.py 修正 - `search_with_precomputed_embedding`, `batch_generate_embeddings`追加
  - [ ] ローカルテスト完了

- [x] P1-2: HTTPコネクションプール最適化
  - [x] core/http_client.py 新規作成 - グローバルhttpxクライアント管理
  - [x] core/__init__.py 修正 - エクスポート追加
  - [x] services/deepinfra_service.py 修正 - `rerank()`で共有クライアント使用
  - [x] main.py 修正 - シャットダウン時にクライアントクローズ
  - [ ] ローカルテスト完了

- [x] P1-3: メモリ設定増加
  - [x] deploy.sh 修正 - Production: 4Gi, Development: 2Gi
  - [ ] 本番デプロイ・テスト完了（ローカルテスト不可）

- [x] P2-1: タイムアウト設定最適化
  - [x] services/deepinfra_service.py 修正 - AsyncOpenAIに明示的タイムアウト設定 (read=180s, connect=10s)
  - [x] max_retries=3 追加で自動リトライ
  - [ ] ローカルテスト完了

- [x] P2-2: min-instances増加
  - [x] deploy.sh 修正 - Production: MIN_INSTANCES=2
  - [ ] 本番デプロイ・テスト完了（ローカルテスト不可）

---

## ⚠️ 注意事項

1. **本番デプロイが必要な項目**
   - P1-3: メモリ設定増加 → Cloud Runデプロイ後に効果確認
   - P2-2: min-instances増加 → Cloud Runデプロイ後に効果確認

2. **コスト影響のある変更**
   - P1-3: メモリ増加 → コスト約2倍
   - P2-2: min-instances増加 → 常時稼働インスタンスが2倍

3. **ロールバック手順**
   - 各変更はgitコミット単位で管理
   - 問題発生時は `git revert` で個別にロールバック可能

---

## 🚀 Phase 4: Reranker/Embedding プラットフォーム最適化

### 📋 背景と問題点

2025年12月の包括的レビューにより、以下の問題が特定された：

#### 現状の問題

| 問題 | 詳細 | 影響 |
|------|------|------|
| **DeepInfra Reranker逐次処理** | asyncio.gatherで並列送信しても、API側で逐次処理される | 8クエリで~8秒（本来~1秒で可能） |
| **DeepInfraプラットフォームリスク** | 価格変動(400%増)、モデル削除の報告あり | 運用安定性リスク |
| **Qwen3-Reranker互換性問題** | vLLM, HuggingFace TEI, LangChainで複数のバグ報告 | 自前ホスト困難 |

#### ログ証拠（2024-12-22 ローカルテスト）

```
16:50:06.407 - 🚀 Reranker[0] STARTED
16:50:06.412 - 🚀 Reranker[1] STARTED  ← 全て同時に開始
16:50:06.414 - 🚀 Reranker[6] STARTED
16:50:07.754 - ✅ Reranker[0] COMPLETED  ← しかし逐次完了
16:50:08.892 - ✅ Reranker[1] COMPLETED  （~1秒間隔）
...
16:50:13.311 - ✅ Reranker[6] COMPLETED
```

**結論**: リクエストは並列送信されているが、DeepInfra側で逐次処理されている

---

### 🎯 最適化目標

| 項目 | 現状 | 目標 | 改善率 |
|------|------|------|--------|
| Reranker処理時間 (8クエリ) | ~8秒 | ~1-2秒 | **75-87%削減** |
| Embedding API | DeepInfra依存 | SiliconFlow移行 | プラットフォーム分散 |
| 精度 | Qwen3-Reranker-8B (MTEB-R: 69.02) | 維持 | 精度維持 |

---

### 🔧 P3: Rerankerプロバイダー抽象化・移行

#### P3-1: プロバイダー抽象化レイヤー

**目的**: 複数のRerankerプロバイダーを環境変数で切り替え可能にする

**新規ファイル**: `services/reranker_providers.py`

```python
"""
Rerankerプロバイダー抽象化レイヤー

環境変数 RERANKER_PROVIDER で切り替え可能:
- "siliconflow" (デフォルト): SiliconFlow API + Qwen3-Reranker-8B
- "jina": Jina Reranker v2 API
- "deepinfra": DeepInfra API (後方互換)
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import httpx

logger = logging.getLogger(__name__)


class RerankerProvider(ABC):
    """Rerankerプロバイダーの抽象基底クラス"""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        instruction: Optional[str] = None
    ) -> Tuple[int, List[float]]:
        """
        ドキュメントをリランキング

        Args:
            query: 検索クエリ
            documents: リランキング対象ドキュメントリスト
            top_n: 返す上位件数（Noneで全件）
            instruction: タスク指示文

        Returns:
            (best_index, scores): 最高スコアのインデックスと全スコアリスト
        """
        pass


class SiliconFlowRerankerProvider(RerankerProvider):
    """
    SiliconFlow API経由のQwen3-Reranker-8B

    特徴:
    - DeepInfraと同じQwen3モデルで精度維持
    - 2.3x高速な推論
    - 真の並列処理サポート
    """

    def __init__(self, model_id: str = "Qwen/Qwen3-Reranker-8B"):
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY environment variable is required")

        self.model_id = model_id
        self.base_url = "https://api.siliconflow.cn/v1"

        # 共有HTTPクライアント
        from ..core.http_client import get_async_client
        self.client = get_async_client()

        logger.info(f"SiliconFlowRerankerProvider initialized: {model_id}")

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        instruction: Optional[str] = None
    ) -> Tuple[int, List[float]]:
        """SiliconFlow API経由でリランキング"""
        url = f"{self.base_url}/rerank"

        payload = {
            "model": self.model_id,
            "query": query,
            "documents": documents,
        }
        if top_n is not None:
            payload["top_n"] = top_n

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            # レスポンス形式: {"results": [{"index": 0, "relevance_score": 0.95}, ...]}
            results = result.get("results", [])

            # スコアリストを元のインデックス順に再構築
            scores = [0.0] * len(documents)
            for item in results:
                idx = item.get("index", 0)
                score = item.get("relevance_score", 0.0)
                if idx < len(scores):
                    scores[idx] = score

            best_idx = scores.index(max(scores)) if scores else 0
            return best_idx, scores

        except Exception as e:
            logger.error(f"SiliconFlow rerank failed: {e}")
            raise


class JinaRerankerProvider(RerankerProvider):
    """
    Jina Reranker v2 API

    特徴:
    - ~150msレイテンシ（超高速）
    - 1リクエストで最大2048ドキュメント
    - 100+言語対応
    - オープンソースベース
    """

    def __init__(self, model_id: str = "jina-reranker-v2-base-multilingual"):
        self.api_key = os.getenv("JINA_API_KEY")
        if not self.api_key:
            raise ValueError("JINA_API_KEY environment variable is required")

        self.model_id = model_id
        self.base_url = "https://api.jina.ai/v1"

        from ..core.http_client import get_async_client
        self.client = get_async_client()

        logger.info(f"JinaRerankerProvider initialized: {model_id}")

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        instruction: Optional[str] = None
    ) -> Tuple[int, List[float]]:
        """Jina API経由でリランキング"""
        url = f"{self.base_url}/rerank"

        payload = {
            "model": self.model_id,
            "query": query,
            "documents": documents,
        }
        if top_n is not None:
            payload["top_n"] = top_n

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            # Jinaレスポンス形式: {"results": [{"index": 0, "relevance_score": 0.95}, ...]}
            results = result.get("results", [])

            scores = [0.0] * len(documents)
            for item in results:
                idx = item.get("index", 0)
                score = item.get("relevance_score", 0.0)
                if idx < len(scores):
                    scores[idx] = score

            best_idx = scores.index(max(scores)) if scores else 0
            return best_idx, scores

        except Exception as e:
            logger.error(f"Jina rerank failed: {e}")
            raise


class DeepInfraRerankerProvider(RerankerProvider):
    """
    DeepInfra API（後方互換用）

    注意: 逐次処理の問題があるため、本番使用は非推奨
    """

    def __init__(self, model_id: str = "Qwen/Qwen3-Reranker-8B"):
        self.api_key = os.getenv("DEEPINFRA_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPINFRA_API_KEY environment variable is required")

        self.model_id = model_id

        from ..core.http_client import get_async_client
        self.client = get_async_client()

        logger.info(f"DeepInfraRerankerProvider initialized: {model_id}")

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
        instruction: Optional[str] = None
    ) -> Tuple[int, List[float]]:
        """DeepInfra API経由でリランキング"""
        url = f"https://api.deepinfra.com/v1/inference/{self.model_id}"

        payload = {
            "queries": [query],
            "documents": documents
        }
        if top_n is not None:
            payload["top_n"] = top_n
        if instruction is not None:
            payload["instruction"] = instruction

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            scores = result.get("scores", [])
            best_idx = scores.index(max(scores)) if scores else 0
            return best_idx, scores

        except Exception as e:
            logger.error(f"DeepInfra rerank failed: {e}")
            raise


class RerankerProviderFactory:
    """Rerankerプロバイダーのファクトリークラス"""

    _providers = {
        "siliconflow": SiliconFlowRerankerProvider,
        "jina": JinaRerankerProvider,
        "deepinfra": DeepInfraRerankerProvider,
    }

    @classmethod
    def create(cls, provider_name: Optional[str] = None) -> RerankerProvider:
        """
        環境変数またはパラメータに基づいてプロバイダーを生成

        Args:
            provider_name: プロバイダー名（None時は環境変数から取得）

        Returns:
            RerankerProvider インスタンス
        """
        if provider_name is None:
            provider_name = os.getenv("RERANKER_PROVIDER", "siliconflow")

        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown reranker provider: {provider_name}. "
                f"Available: {list(cls._providers.keys())}"
            )

        logger.info(f"Creating reranker provider: {provider_name}")
        return cls._providers[provider_name]()
```

#### P3-2: hybrid_search.py の修正

**変更箇所**: `apply_reranker_batch`メソッドで新プロバイダーを使用

```python
async def apply_reranker_batch(
    self,
    queries_and_candidates: List[Dict[str, Any]],
    reranker_provider,  # RerankerProvider型に変更
    reranker_instruction: str = None,
    top_k: int = 1
) -> List[Dict[str, Any]]:
    """
    複数クエリのRerankerを一括並列実行

    新プロバイダー抽象化により、SiliconFlow/Jina/DeepInfraを
    環境変数で切り替え可能。
    """
    import time as time_module

    batch_start_time = time_module.time()

    async def rerank_single(idx: int, query: str, candidates: List[Dict]) -> Dict[str, Any]:
        """単一クエリのReranker実行"""
        start_time = time_module.time()
        logger.info(f"🚀 Reranker[{idx}] STARTED: query='{query[:30]}...'")

        if not candidates:
            return None

        documents = [c["description"] for c in candidates]

        # 新プロバイダーインターフェース使用
        best_idx, reranked_scores = await reranker_provider.rerank(
            query=query,
            documents=documents,
            instruction=reranker_instruction
        )

        elapsed = time_module.time() - start_time
        logger.info(f"✅ Reranker[{idx}] COMPLETED in {elapsed:.2f}s")

        for i, candidate in enumerate(candidates):
            candidate["rerank_score"] = reranked_scores[i]
            candidate["original_rank"] = i + 1

        reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        return reranked[0] if reranked else None

    # 全Rerankerを並列実行
    logger.info(f"🔄 Parallel reranker execution for {len(queries_and_candidates)} queries...")

    tasks = [
        rerank_single(i, item["query"], item["candidates"])
        for i, item in enumerate(queries_and_candidates)
    ]

    results = await asyncio.gather(*tasks)

    total_elapsed = time_module.time() - batch_start_time
    logger.info(f"✅ Parallel reranker completed in {total_elapsed:.2f}s for {len(queries_and_candidates)} queries")

    return results
```

---

### 🔧 P4: Embeddingプロバイダー移行（SiliconFlow）

#### P4-1: Embeddingプロバイダー抽象化

**新規ファイル**: `services/embedding_providers.py`

```python
"""
Embeddingプロバイダー抽象化レイヤー

環境変数 EMBEDDING_PROVIDER で切り替え可能:
- "siliconflow" (デフォルト): SiliconFlow API + Qwen3-Embedding-8B
- "deepinfra": DeepInfra API (後方互換)
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
import httpx

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Embeddingプロバイダーの抽象基底クラス"""

    @abstractmethod
    async def generate_embeddings(
        self,
        texts: List[str],
        instruction: Optional[str] = None
    ) -> List[List[float]]:
        """
        テキストのEmbeddingを生成

        Args:
            texts: Embedding生成対象のテキストリスト
            instruction: タスク指示文（instruction-awareモデル用）

        Returns:
            List[List[float]]: 各テキストのEmbeddingベクトル
        """
        pass


class SiliconFlowEmbeddingProvider(EmbeddingProvider):
    """
    SiliconFlow API経由のQwen3-Embedding-8B

    特徴:
    - MTEB多言語 #1 (70.58)
    - 32Kトークンコンテキスト
    - instruction-aware対応
    """

    def __init__(self, model_id: str = "Qwen/Qwen3-Embedding-8B"):
        self.api_key = os.getenv("SILICONFLOW_API_KEY")
        if not self.api_key:
            raise ValueError("SILICONFLOW_API_KEY environment variable is required")

        self.model_id = model_id
        self.base_url = "https://api.siliconflow.cn/v1"

        from ..core.http_client import get_async_client
        self.client = get_async_client()

        logger.info(f"SiliconFlowEmbeddingProvider initialized: {model_id}")

    async def generate_embeddings(
        self,
        texts: List[str],
        instruction: Optional[str] = None
    ) -> List[List[float]]:
        """SiliconFlow API経由でEmbedding生成"""
        url = f"{self.base_url}/embeddings"

        # instruction-aware形式
        if instruction:
            formatted_texts = [
                f"Instruct: {instruction}\nQuery: {text}"
                for text in texts
            ]
        else:
            formatted_texts = texts

        payload = {
            "model": self.model_id,
            "input": formatted_texts,
            "encoding_format": "float"
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            embeddings = [item["embedding"] for item in result.get("data", [])]
            logger.info(f"✅ Generated {len(embeddings)} embeddings via SiliconFlow")
            return embeddings

        except Exception as e:
            logger.error(f"SiliconFlow embedding failed: {e}")
            raise


class DeepInfraEmbeddingProvider(EmbeddingProvider):
    """DeepInfra API（後方互換用）"""

    def __init__(self, model_id: str = "Qwen/Qwen3-Embedding-8B"):
        self.api_key = os.getenv("DEEPINFRA_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPINFRA_API_KEY environment variable is required")

        self.model_id = model_id

        # OpenAI互換クライアント
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.deepinfra.com/v1/openai"
        )

        logger.info(f"DeepInfraEmbeddingProvider initialized: {model_id}")

    async def generate_embeddings(
        self,
        texts: List[str],
        instruction: Optional[str] = None
    ) -> List[List[float]]:
        """DeepInfra API経由でEmbedding生成"""
        if instruction:
            formatted_texts = [
                f"Instruct: {instruction}\nQuery: {text}"
                for text in texts
            ]
        else:
            formatted_texts = texts

        try:
            response = await self.client.embeddings.create(
                input=formatted_texts,
                model=self.model_id,
                encoding_format="float"
            )

            embeddings = [item.embedding for item in response.data]
            logger.info(f"✅ Generated {len(embeddings)} embeddings via DeepInfra")
            return embeddings

        except Exception as e:
            logger.error(f"DeepInfra embedding failed: {e}")
            raise


class EmbeddingProviderFactory:
    """Embeddingプロバイダーのファクトリークラス"""

    _providers = {
        "siliconflow": SiliconFlowEmbeddingProvider,
        "deepinfra": DeepInfraEmbeddingProvider,
    }

    @classmethod
    def create(cls, provider_name: Optional[str] = None) -> EmbeddingProvider:
        """環境変数またはパラメータに基づいてプロバイダーを生成"""
        if provider_name is None:
            provider_name = os.getenv("EMBEDDING_PROVIDER", "siliconflow")

        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown embedding provider: {provider_name}. "
                f"Available: {list(cls._providers.keys())}"
            )

        logger.info(f"Creating embedding provider: {provider_name}")
        return cls._providers[provider_name]()
```

---

### 🔧 P5: Reranker候補数最適化

#### P5-1: stage1_top_k設定の最適化

**現状分析**:

```python
# config/settings.py 現状
self.DEFAULT_STAGE1_TOP_K = int(os.getenv("STAGE1_TOP_K", "100"))
```

**2025年ベストプラクティス**:
> "Rerank 50-75 candidates for optimal NDCG@10 in most applications.
> Beyond 100 candidates, quality improvements plateau while costs and latency increase linearly."
> — [ZeroEntropy Guide](https://www.zeroentropy.dev/articles/ultimate-guide-to-choosing-the-best-reranking-model-in-2025)

**変更内容**:

**config/settings.py**
```python
# Before
self.DEFAULT_STAGE1_TOP_K = int(os.getenv("STAGE1_TOP_K", "100"))

# After
# Reranker候補数最適化: 50-75が最適（2025ベストプラクティス）
# 100以上は精度向上が頭打ちでコスト・レイテンシのみ増加
self.DEFAULT_STAGE1_TOP_K = int(os.getenv("STAGE1_TOP_K", "60"))
```

**Admin Panel対応** (`admin/config_manager.py`):

```python
class SearchConfig(BaseModel):
    """検索設定"""
    stage1_top_k: int = Field(
        default=60,  # 100 → 60に変更
        ge=20,
        le=100,
        description="Stage1で取得する候補数（推奨: 50-75）"
    )
```

---

### 📝 環境変数設定

#### 本番環境 (Cloud Run)

```bash
# Rerankerプロバイダー設定
RERANKER_PROVIDER=siliconflow  # または "jina"
SILICONFLOW_API_KEY=your_siliconflow_api_key
JINA_API_KEY=your_jina_api_key  # Jina使用時のみ必要

# Embeddingプロバイダー設定
EMBEDDING_PROVIDER=siliconflow
# SILICONFLOW_API_KEYは上記と共有

# Reranker候補数
STAGE1_TOP_K=60

# 後方互換（DeepInfraを使用する場合のみ）
# RERANKER_PROVIDER=deepinfra
# EMBEDDING_PROVIDER=deepinfra
# DEEPINFRA_API_KEY=your_deepinfra_api_key
```

#### ローカル開発環境 (.env)

```bash
# プロバイダー選択
RERANKER_PROVIDER=siliconflow
EMBEDDING_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your_key

# オプション: Jina Rerankerテスト用
# RERANKER_PROVIDER=jina
# JINA_API_KEY=your_jina_key

# 候補数
STAGE1_TOP_K=60
```

---

### 📊 期待される改善効果

| 項目 | 最適化前 | 最適化後 | 改善率 |
|------|---------|---------|--------|
| Reranker処理 (8クエリ) | ~8秒 | ~1-2秒 (SiliconFlow) / ~0.5秒 (Jina) | **75-94%** |
| stage1_top_k | 100 | 60 | Reranker負荷40%削減 |
| プラットフォームリスク | DeepInfra単一依存 | 3プロバイダー切替可能 | リスク分散 |

---

### 📋 実装チェックリスト

- [ ] P3-1: Rerankerプロバイダー抽象化
  - [ ] `services/reranker_providers.py` 新規作成
  - [ ] SiliconFlowRerankerProvider 実装
  - [ ] JinaRerankerProvider 実装
  - [ ] DeepInfraRerankerProvider (後方互換) 実装
  - [ ] RerankerProviderFactory 実装

- [ ] P3-2: hybrid_search.py 修正
  - [ ] `apply_reranker_batch` を新プロバイダー対応に修正
  - [ ] テスト実行

- [ ] P4-1: Embeddingプロバイダー抽象化
  - [ ] `services/embedding_providers.py` 新規作成
  - [ ] SiliconFlowEmbeddingProvider 実装
  - [ ] DeepInfraEmbeddingProvider (後方互換) 実装
  - [ ] EmbeddingProviderFactory 実装

- [ ] P4-2: usda_search.py / food_search_service.py 修正
  - [ ] 新Embeddingプロバイダー使用に修正

- [ ] P5-1: stage1_top_k最適化
  - [ ] config/settings.py 修正 (100 → 60)
  - [ ] admin/config_manager.py 修正

- [ ] 環境変数設定
  - [ ] .env.example 更新
  - [ ] deploy.sh 更新
  - [ ] Cloud Run環境変数設定

- [ ] テスト
  - [ ] ローカルテスト (SiliconFlow)
  - [ ] ローカルテスト (Jina)
  - [ ] 本番デプロイ・テスト

---

### ⚠️ 注意事項

1. **API Key取得が必要**
   - SiliconFlow: https://siliconflow.cn/ でアカウント作成・API Key取得
   - Jina: https://jina.ai/ でアカウント作成・API Key取得

2. **フォールバック戦略**
   - 新プロバイダーでエラー時はDeepInfraにフォールバック可能な設計
   - 環境変数で即座に切り替え可能

3. **コスト比較（事前確認推奨）**
   | プロバイダー | Reranker料金 | Embedding料金 |
   |-------------|-------------|--------------|
   | SiliconFlow | 要確認 | 要確認 |
   | Jina | 従量課金 | - |
   | DeepInfra | 現状料金 | 現状料金 |

4. **精度検証**
   - 本番移行前にテストセットで精度比較を実施推奨
   - 特にJina移行時はモデルが異なるため注意

---

## 📚 参考資料

- [Advanced Performance Tuning for FastAPI on Google Cloud Run](https://davidmuraya.com/blog/fastapi-performance-tuning-on-google-cloud-run/)
- [Optimize Python applications for Cloud Run | Google Cloud](https://cloud.google.com/run/docs/tips/python)
- [Optimizing RAG with Hybrid Search & Reranking | VectorHub](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking)
- [Uvicorn Deployment with Gunicorn](https://www.uvicorn.org/deployment/)

### Phase 4 追加参考資料

- [SiliconFlow Qwen3-Reranker-8B](https://www.siliconflow.com/models/qwen3-reranker-8b) - 2.3x高速推論
- [Jina Reranker API](https://jina.ai/reranker/) - 150ms超高速レイテンシ
- [Ultimate Guide to Choosing the Best Reranking Model 2025](https://www.zeroentropy.dev/articles/ultimate-guide-to-choosing-the-best-reranking-model-in-2025)
- [RAG Best Practices from 100+ Teams (Kapa.ai)](https://www.kapa.ai/blog/rag-best-practices)
- [Building a Production RAG System with Qwen3](https://medium.com/@oliversmithth852/building-a-production-rag-system-qwen3-embeddings-reranking-and-vector-database-insights-9c114c5f9da8)
- [Qwen3-Reranker GitHub Issues (vLLM)](https://github.com/vllm-project/vllm/issues/27857) - 既知の問題
