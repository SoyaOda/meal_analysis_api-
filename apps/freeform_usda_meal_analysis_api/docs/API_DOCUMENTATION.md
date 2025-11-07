# Freeform USDA Meal Analysis API - フロントエンド向けAPI仕様書

**Version**: 1.0.0
**Base URL**: `https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app`

## 📚 ドキュメント

- **Swagger UI**: https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/docs
- **ReDoc**: https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/redoc
- **OpenAPI JSON**: https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/openapi.json

---

## 🎯 API概要

このAPIは、食事画像から栄養価を自動計算するサービスです。USDA FNDDS（Food and Nutrient Database for Dietary Studies）データベース（13,564件）を基に、高精度な栄養価推定を提供します。

### 主要機能

1. **食事分析** - 画像から食材を検出し、栄養価を計算（Match rate: 平均95%以上）
2. **食材検索** - USDA DBから類似食材を検索（3モード: Fast/Accurate/Hybrid）
3. **メタデータ配信** - USDA食材の詳細情報（gzip圧縮推奨: 8.4MB→0.7MB）
4. **ヘルスチェック** - サービス稼働状態確認

---

## 📋 エンドポイント一覧

### 1. Root - API情報

#### `GET /`
API情報とエンドポイント一覧を取得

**Response Example**:
```json
{
  "name": "Freeform USDA Meal Analysis API",
  "version": "1.0.0",
  "status": "running",
  "documentation": {
    "swagger": "/docs",
    "redoc": "/redoc",
    "openapi": "/openapi.json"
  },
  "endpoints": {
    "health": "/health",
    "analysis": "/api/v1/meal-analyses",
    "retrieval": "/api/v1/retrieve"
  }
}
```

---

### 2. Health - ヘルスチェック

#### `GET /health`
サービスの基本稼働状態を確認

**Response Example**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_id": "Qwen/Qwen3-VL-30B-A3B-Thinking",
  "prompt_file": "freeform_prompt_usda_format_ver_v7_experimental_20251027.txt"
}
```

#### `GET /health/ready`
インデックスのロード状態を確認（Cloud Run readiness probe用）

**Response Example**:
```json
{
  "status": "ready",
  "service": "freeform-usda-meal-analysis-api",
  "indexes_loaded": true,
  "message": "Service is ready to accept requests"
}
```

---

### 3. Analysis - 食事分析（メイン機能）

#### `POST /api/v1/meal-analyses/complete`
画像から食事を分析し、栄養価を計算

**Request**:
- `Content-Type`: `multipart/form-data`
- **image** (required): 食事画像ファイル (JPG, PNG)
- **model_id** (optional): VLMモデルID（デフォルト: `Qwen/Qwen3-VL-30B-A3B-Thinking`）
- **user_context** (optional): ユーザーコンテキスト

**cURL Example**:
```bash
curl -X POST \
  "https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/api/v1/meal-analyses/complete" \
  -F "image=@food.jpg"
```

**Response Example** (simplified):
```json
{
  "analysis_id": "a1b2c3d4",
  "input_type": "image",
  "total_dishes": 2,
  "total_ingredients": 3,
  "processing_time_seconds": 32.5,
  "dishes": [
    {
      "ingredients": [
        {
          "ingredient_name": "penne pasta with tomato sauce",
          "weight_g": 400.0,
          "nutrition_per_100g": {
            "calories": 87.0,
            "protein": 2.5,
            "fat": 2.2,
            "carbs": 14.4
          },
          "calculated_nutrition": {
            "calories": 348.0,
            "protein": 10.0,
            "fat": 8.8,
            "carbs": 57.6
          },
          "source_db": "usda_fndds",
          "fdc_id": "2708930"
        }
      ],
      "total_nutrition": {
        "calories": 348.0,
        "protein": 10.0,
        "fat": 8.8,
        "carbs": 57.6
      }
    }
  ],
  "total_nutrition": {
    "calories": 1432.0,
    "protein": 14.4,
    "fat": 124.4,
    "carbs": 64.2
  },
  "ai_model_used": "Qwen/Qwen3-VL-30B-A3B-Thinking",
  "match_rate_percent": 100.0,
  "usage": {
    "prompt_tokens": 2311,
    "completion_tokens": 4497,
    "total_tokens": 6808,
    "estimated_cost_usd": 0.005122
  }
}
```

**処理時間**: 平均30-35秒
**Match Rate**: 平均95%以上

---

### 4. Retrieval - 食材検索

#### `GET /api/v1/retrieve`
USDA DBから類似食材を検索

**Query Parameters**:
- **q** (required): 検索クエリ（例: "chicken breast"）
- **mode** (optional): 検索モード（デフォルト: `hybrid`）
  - `fast`: FAISS検索のみ（高速、平均180ms）
  - `accurate`: FAISS + Reranking（高精度、平均800ms）
  - `hybrid`: BM25 + FAISS + RRF（最高精度、平均200ms）
- **top_k** (optional): 返却結果数（デフォルト: 10、最大: 50）
- **include_nutrition** (optional): 栄養情報を含めるか（デフォルト: true）
- **debug** (optional): デバッグ情報を含めるか（デフォルト: false）

**cURL Example**:
```bash
curl -X GET \
  "https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/api/v1/retrieve?q=chicken%20breast&mode=hybrid&top_k=3"
```

**Response Example**:
```json
{
  "query": "chicken breast",
  "mode": "hybrid",
  "results": [
    {
      "fdc_id": "167782",
      "description": "Chicken, broilers or fryers, breast, meat only, grilled",
      "main_name": "Chicken, broilers or fryers, breast, meat only",
      "descriptors": "grilled",
      "source": "survey",
      "score": 0.95,
      "nutrition_per_100g": {
        "calories": 165.0,
        "protein": 31.0,
        "fat": 3.6,
        "carbs": 0.0
      }
    }
  ],
  "metadata": {
    "total_results": 3,
    "search_time_ms": 179,
    "index_type": "FAISS",
    "algorithm": "BM25+Vector_RRF"
  },
  "status": {
    "success": true,
    "message": "Search completed successfully"
  }
}
```

#### `GET /api/v1/retrieve/health`
Retrieval APIの稼働状態確認

---

### 5. Metadata - メタデータ配信

#### `GET /api/v1/metadata`
USDA食材メタデータ全件取得（13,564件）

**Query Parameters**:
- **compressed** (optional): gzip圧縮（デフォルト: true、推奨）

**重要**: フロントエンドでの初回読み込み時に取得し、ローカルストレージにキャッシュすることを推奨

**cURL Example**:
```bash
curl -X GET \
  "https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/api/v1/metadata?compressed=true"
```

**データサイズ**:
- 非圧縮: 8.4 MB
- gzip圧縮: 0.7 MB（推奨）

**JavaScript使用例**:
```javascript
// gzip圧縮版を取得（推奨）
const response = await fetch(
  'https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/api/v1/metadata?compressed=true'
);
const metadata = await response.json();

// ローカルストレージにキャッシュ（24時間）
localStorage.setItem('usda_metadata', JSON.stringify({
  items: metadata,
  timestamp: Date.now()
}));
```

#### `GET /api/v1/metadata/info`
メタデータの統計情報取得

**Response Example**:
```json
{
  "total_items": 13564,
  "file_size_mb": 8.36,
  "compressed_size_mb": 0.67,
  "compression_ratio": 0.08,
  "sources": {
    "survey": 7000,
    "foundation": 5000,
    "sr_legacy": 1564
  },
  "portions_coverage_percent": 85.5,
  "items_with_portions": 11600
}
```

#### `GET /api/v1/metadata/search`
メタデータ検索（軽量版、部分一致）

**Query Parameters**:
- **q** (required): 検索クエリ
- **limit** (optional): 返却件数（デフォルト: 20、最大: 100）
- **offset** (optional): オフセット（デフォルト: 0）
- **source** (optional): データソースフィルター（survey/foundation/sr_legacy）

**cURL Example**:
```bash
curl -X GET \
  "https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/api/v1/metadata/search?q=chicken&limit=10"
```

**Note**: 高度な検索（セマンティック検索）には `/api/v1/retrieve` を使用してください。

#### `GET /api/v1/metadata/{fdc_id}`
FDC ID指定で単一食材の詳細情報取得

**cURL Example**:
```bash
curl -X GET \
  "https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/api/v1/metadata/167782"
```

---

## 🔐 認証

現在、認証は不要です（Cloud Runのデフォルト設定）。

将来的に認証が必要になった場合は、以下のヘッダーを追加してください：
```
Authorization: Bearer YOUR_API_KEY
```

---

## ⚠️ エラーハンドリング

### HTTPステータスコード

- **200**: 成功
- **400**: リクエストエラー（パラメータ不正など）
- **404**: リソースが見つからない
- **500**: サーバーエラー
- **503**: サービス利用不可（初期化中など）

### エラーレスポンス例

```json
{
  "error": "ValidationError",
  "message": "Invalid input format",
  "detail": {...},
  "analysis_id": "a1b2c3d4"
}
```

---

## 📊 パフォーマンス目安

| エンドポイント | 平均処理時間 | 備考 |
|---------------|------------|------|
| `/health` | <100ms | 即座 |
| `/api/v1/retrieve?mode=fast` | 180ms | FAISS検索のみ |
| `/api/v1/retrieve?mode=accurate` | 800ms | FAISS + Rerank |
| `/api/v1/retrieve?mode=hybrid` | 200ms | BM25 + Vector（推奨） |
| `/api/v1/metadata/search` | <300ms | 部分一致検索 |
| `/api/v1/meal-analyses/complete` | 30-35秒 | VLM処理含む |

---

## 🚀 フロントエンド実装推奨フロー

### 1. アプリ起動時
```javascript
// メタデータをキャッシュ
const metadata = await fetchAndCacheMetadata();
```

### 2. 食材検索時
```javascript
// Hybrid modeで検索（最高精度）
const results = await fetch(
  `${API_BASE}/api/v1/retrieve?q=${query}&mode=hybrid&top_k=10`
).then(r => r.json());
```

### 3. 画像分析時
```javascript
const formData = new FormData();
formData.append('image', imageFile);

const analysis = await fetch(
  `${API_BASE}/api/v1/meal-analyses/complete`,
  { method: 'POST', body: formData }
).then(r => r.json());

// 処理時間: 30-35秒
// progress indicatorを表示推奨
```

---

## 🛠️ 開発ツール

### Postman Collection
OpenAPI JSONをインポートしてください：
```
https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/openapi.json
```

### TypeScript型定義生成
```bash
npx openapi-typescript \
  https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/openapi.json \
  --output types/api.ts
```

---

## 📞 サポート

- **GitHub Issues**: (リポジトリURL)
- **Swagger UI**: https://freeform-usda-meal-analysis-api-v2-x27n75dvja-uc.a.run.app/docs
- **技術仕様**: OpenAPI JSON参照

---

## 📝 変更履歴

### v1.0.0 (2025-11-07)
- 初回リリース
- 全11エンドポイント実装
- Lazy Loading対応
- Hybrid Search実装（BM25 + Vector）
- gzip圧縮メタデータ配信
