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

| テスト項目 | 最適化前 | 最適化後 | 改善率 |
|-----------|---------|---------|--------|
| コールドスタート時間 | | | |
| 単一画像分析（3食材） | | | |
| 単一画像分析（10食材） | | | |
| 並列リクエスト（5同時） | | | |

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

## 📚 参考資料

- [Advanced Performance Tuning for FastAPI on Google Cloud Run](https://davidmuraya.com/blog/fastapi-performance-tuning-on-google-cloud-run/)
- [Optimize Python applications for Cloud Run | Google Cloud](https://cloud.google.com/run/docs/tips/python)
- [Optimizing RAG with Hybrid Search & Reranking | VectorHub](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking)
- [Uvicorn Deployment with Gunicorn](https://www.uvicorn.org/deployment/)
