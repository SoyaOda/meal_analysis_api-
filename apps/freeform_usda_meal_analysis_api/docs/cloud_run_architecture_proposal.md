# Cloud Run デプロイメント アーキテクチャ提案書

## 📋 エグゼクティブサマリー

現在の同期処理APIを、Cloud Runで安定かつ低レイテンシで動作するよう最適化します。
VLMレスポンス時間（30秒〜5分）とインデックスサイズ（700MB）の課題に対し、段階的な改善アプローチを提案します。

## 🎯 目標

1. **レスポンス時間の最適化**: 平均待ち時間を50%削減
2. **エラーレートの改善**: 現在の20-25%から5%以下へ
3. **スケーラビリティ**: 同時100ユーザーまで対応
4. **コスト効率**: リソース使用の最適化

## 📊 現状分析

### 問題点
- VLMレスポンス時間: 30秒〜5分（モデル依存）
- インデックスロード: 起動時に700MB読み込み
- エラー率: 20-25%（主にタイムアウト）
- 並列処理時の競合問題

### ボトルネック
1. **外部API依存**: OpenRouter/DeepInfraの応答時間
2. **大規模インデックス**: FAISSとBM25の初期化
3. **同期処理**: ユーザーが長時間待機

## 🏗️ 提案アーキテクチャ

### Phase 1: 同期処理の最適化（即座に実装可能）

#### 1.1 Cloud Run設定の最適化

```yaml
# cloudrun.yaml の主要設定
spec:
  template:
    metadata:
      annotations:
        # コールドスタート最適化
        run.googleapis.com/startup-cpu-boost: "true"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      timeoutSeconds: 600  # 10分タイムアウト
      containerConcurrency: 10
      resources:
        limits:
          memory: 4Gi
          cpu: "4"
  metadata:
    annotations:
      autoscaling.knative.dev/minScale: "1"  # 最小1インスタンス維持
      autoscaling.knative.dev/maxScale: "100"
```

#### 1.2 Dockerfile最適化

```dockerfile
# マルチステージビルドで軽量化
FROM python:3.11-slim as builder
# 依存関係のインストール

FROM python:3.11-slim
# 最小限のランタイム環境
# インデックスファイルを事前にコンテナに含める
COPY data/faiss/ /app/data/faiss/
COPY data/bm25/ /app/data/bm25/

# gunicornで本番環境対応
CMD ["gunicorn", "--workers", "1", "--timeout", "600"]
```

#### 1.3 アプリケーション最適化

```python
# startup_optimizer.py
class StartupOptimizer:
    """コールドスタート最適化"""

    async def lazy_load_indexes(self):
        """インデックスの遅延ロード"""
        # リクエスト時に初回のみロード

    @lru_cache(maxsize=128)
    def cached_search(self, query: str):
        """頻繁なクエリをキャッシュ"""
```

### Phase 2: 非同期処理アーキテクチャ（中期的実装）

#### 2.1 Cloud Tasks統合

```python
# async_processor.py
class AsyncMealAnalyzer:
    """非同期処理フロー"""

    async def submit_analysis(self, image_data: bytes) -> str:
        """分析ジョブをCloud Tasksに送信"""
        task_id = generate_task_id()

        # Cloud Tasksにジョブ送信
        task = {
            'http_request': {
                'url': f'{WORKER_URL}/process',
                'body': encode_image(image_data),
                'headers': {'Task-ID': task_id}
            }
        }

        # Firestoreに初期状態を保存
        await firestore.save_status(task_id, 'processing')

        return task_id

    async def get_result(self, task_id: str):
        """結果の取得（ポーリング or Webhook）"""
        status = await firestore.get_status(task_id)

        if status == 'completed':
            return await firestore.get_result(task_id)
        elif status == 'processing':
            return {'status': 'processing', 'progress': 50}
        else:
            return {'status': 'error', 'message': 'Analysis failed'}
```

#### 2.2 フロントエンド統合パターン

```javascript
// client.js
async function analyzeMealAsync(imageFile) {
    // 1. ジョブ送信
    const response = await fetch('/api/v1/meal-analyses/async', {
        method: 'POST',
        body: createFormData(imageFile)
    });
    const { task_id } = await response.json();

    // 2. ポーリングで結果待機
    return pollForResult(task_id);
}

async function pollForResult(taskId) {
    const maxRetries = 60;  // 最大5分
    const interval = 5000;  // 5秒間隔

    for (let i = 0; i < maxRetries; i++) {
        const result = await fetch(`/api/v1/tasks/${taskId}`);
        const data = await result.json();

        if (data.status === 'completed') {
            return data.result;
        } else if (data.status === 'error') {
            throw new Error(data.message);
        }

        // プログレス表示
        updateProgress(data.progress);

        await sleep(interval);
    }

    throw new Error('Timeout');
}
```

### Phase 3: エッジキャッシング（長期的最適化）

#### 3.1 Cloud CDN統合

```yaml
# cdn-config.yaml
apiVersion: compute.cnrm.cloud.google.com/v1beta1
kind: BackendService
metadata:
  name: meal-analysis-cdn
spec:
  cdnPolicy:
    cacheMode: "CACHE_ALL_STATIC"
    defaultTtl: 3600
    maxTtl: 86400
    negativeCaching: true
```

#### 3.2 Redis/Memorystore活用

```python
# cache_manager.py
class CacheManager:
    """分散キャッシュ管理"""

    async def get_cached_analysis(self, image_hash: str):
        """類似画像の結果をキャッシュから取得"""
        return await redis.get(f"analysis:{image_hash}")

    async def cache_analysis(self, image_hash: str, result: dict):
        """分析結果をキャッシュ（TTL: 24時間）"""
        await redis.setex(
            f"analysis:{image_hash}",
            86400,
            json.dumps(result)
        )
```

## 📈 期待される改善効果

| メトリクス | 現在 | Phase 1後 | Phase 2後 | Phase 3後 |
|-----------|------|-----------|-----------|-----------|
| 平均レスポンス時間 | 2-3分 | 90秒 | 5秒（非同期） | 3秒 |
| エラー率 | 20-25% | 10% | 5% | 2% |
| 同時処理可能数 | 5 | 20 | 100+ | 500+ |
| コールドスタート | 15秒 | 8秒 | 8秒 | 5秒 |
| 月額コスト（推定） | $500 | $400 | $600 | $700 |

## 🚀 実装ロードマップ

### Week 1-2: Phase 1
- [ ] Cloud Run設定ファイル作成
- [ ] Dockerfile最適化
- [ ] 起動時最適化の実装
- [ ] 基本的なキャッシング実装

### Week 3-4: Phase 2
- [ ] Cloud Tasks設定
- [ ] Firestore統合
- [ ] 非同期APIエンドポイント追加
- [ ] ポーリング/Webhook実装

### Week 5-6: Phase 3
- [ ] Cloud CDN設定
- [ ] Redis/Memorystore統合
- [ ] 分散キャッシュ実装
- [ ] パフォーマンステスト

## 💰 コスト分析

### 月額推定コスト（1万リクエスト/月）

| サービス | Phase 1 | Phase 2 | Phase 3 |
|----------|---------|---------|---------|
| Cloud Run | $200 | $250 | $250 |
| Cloud Tasks | - | $50 | $50 |
| Firestore | - | $100 | $100 |
| Cloud CDN | - | - | $50 |
| Redis | - | - | $250 |
| **合計** | **$200** | **$400** | **$700** |

## 🔐 セキュリティ考慮事項

1. **API認証**: Firebase Auth or API Keys
2. **レート制限**: Cloud Armor統合
3. **データ暗号化**: TLS 1.3必須
4. **画像データ管理**: 24時間後自動削除

## 📊 モニタリング戦略

```yaml
# monitoring.yaml
alerts:
  - name: high-latency
    condition: response_time > 5s
    threshold: 10%

  - name: error-rate
    condition: error_rate > 5%
    duration: 5m

  - name: memory-usage
    condition: memory > 3.5Gi
    duration: 10m
```

## 🎯 成功指標（KPI）

1. **P95レイテンシ**: 3秒以下（非同期）
2. **可用性**: 99.9%以上
3. **エラー率**: 5%以下
4. **ユーザー満足度**: 4.5/5.0以上

## 📝 まとめ

この3段階アプローチにより、即座の改善から長期的な最適化まで段階的に実装できます。
Phase 1で現在の問題の大部分を解決し、Phase 2-3でユーザー体験を大幅に向上させます。

### 次のステップ

1. **Phase 1の即座実装**: Cloud Run設定とDockerfile最適化
2. **ステークホルダーレビュー**: アーキテクチャの承認取得
3. **詳細設計書作成**: 各Phaseの実装詳細
4. **プロトタイプ開発**: Phase 1の概念実証

## 📚 参考資料

- [Cloud Run ベストプラクティス](https://cloud.google.com/run/docs/tips)
- [非同期処理パターン](https://cloud.google.com/tasks/docs/dual-overview)
- [Cloud CDN設定ガイド](https://cloud.google.com/cdn/docs)
- [Firestore パフォーマンス最適化](https://firebase.google.com/docs/firestore/best-practices)