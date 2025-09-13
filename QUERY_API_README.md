# Query API Documentation

## 概要

MyNetDiary栄養検索システムを基盤とした高性能な食材検索予測APIです。ユーザーが食材名を入力する際のリアルタイム検索候補提案機能を提供します。

## 🚀 本番環境情報

### API基本情報
- **API URL**: `https://meal-analysis-api-v2-1077966746907.us-central1.run.app`
- **バージョン**: v2.0
- **アーキテクチャ**: Component-based Pipeline
- **プラットフォーム**: Google Cloud Run
- **データベース**: Elasticsearch 8.19.3 (Google Compute Engine VM)

### インフラ構成
- **Cloud Run**:
  - メモリ: 2GB
  - CPU: 2コア
  - タイムアウト: 300秒
  - 自動スケーリング対応
- **Elasticsearch VM**:
  - インスタンス: `elasticsearch-vm`
  - ゾーン: `us-central1-a`
  - データ: 1,142件の栄養データ（MyNetDiary List Support DB）

## 📋 主要エンドポイント

### 1. ルートエンドポイント
```
GET /
```
API基本情報の取得

**レスポンス例**:
```json
{
  "message": "食事分析 API v2.0 - コンポーネント化版",
  "version": "2.0.0",
  "architecture": "Component-based Pipeline",
  "docs": "/docs"
}
```

### 2. ヘルスチェック
```
GET /health
```
API稼働状況の確認

**レスポンス例**:
```json
{
  "status": "healthy",
  "version": "v2.0",
  "components": ["Phase1Component", "USDAQueryComponent"]
}
```

### 3. 栄養検索候補API ⭐
```
GET /api/v1/nutrition/suggest
```
**メインAPI - 食材検索予測機能**

#### パラメータ

| パラメータ | 型 | 必須 | 説明 | デフォルト | 制限 |
|-----------|---|-----|-----|---------|-----|
| `q` | string | ✅ | 検索クエリ | - | 最低2文字 |
| `limit` | integer | ❌ | 提案数 | 10 | 1-50件 |
| `debug` | boolean | ❌ | デバッグ情報含める | false | - |

#### リクエスト例
```bash
# 基本的な検索
curl "https://meal-analysis-api-v2-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=chicken&limit=5"

# デバッグ情報付き
curl "https://meal-analysis-api-v2-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=chickpeas&limit=10&debug=true"
```

#### レスポンス形式

```json
{
  "query_info": {
    "original_query": "chickpeas",
    "processed_query": "chickpeas",
    "timestamp": "2025-09-13T18:20:00.000Z",
    "suggestion_type": "autocomplete"
  },
  "suggestions": [
    {
      "rank": 1,
      "suggestion": "Chickpeas",
      "match_type": "exact_match",
      "confidence_score": 100.0,
      "food_info": {
        "search_name": "Chickpeas",
        "search_name_list": ["Chickpeas", "garbanzo beans"],
        "description": "boiled, with salt",
        "original_name": "Chickpeas or garbanzo beans boiled with salt"
      },
      "nutrition_preview": {
        "calories": 164.02,
        "protein": 9.15,
        "per_serving": "100g"
      },
      "alternative_names": ["garbanzo beans"]
    }
  ],
  "metadata": {
    "total_suggestions": 8,
    "total_hits": 8,
    "search_time_ms": 34,
    "processing_time_ms": 299,
    "elasticsearch_index": "mynetdiary_list_support_db"
  },
  "status": {
    "success": true,
    "message": "Suggestions generated successfully"
  }
}
```

### 4. 栄養検索ヘルスチェック
```
GET /api/v1/nutrition/suggest/health
```
Elasticsearch接続状況の確認

### 5. API仕様書
```
GET /docs
```
Swagger UI（インタラクティブAPI仕様書）

## 🎯 検索機能の特徴

### 7段階Tier検索戦略

1. **Tier 1** (Score: 15+): Exact Match (search_name配列要素)
2. **Tier 2** (Score: 12+): Exact Match (description)
3. **Tier 3** (Score: 10+): Phrase Match (search_name配列要素)
4. **Tier 4** (Score: 8+): Phrase Match (description)
5. **Tier 5** (Score: 6+): Term Match (search_name要素の完全一致)
6. **Tier 6** (Score: 4+): Multi-field match
7. **Tier 7** (Score: 2+): Fuzzy Match (search_name配列要素)

### 代替名検索対応

- **chickpeas** ↔ **garbanzo beans** の双方向検索
- **tomato** ↔ **tomatoes** の単複形対応
- 1,142件の栄養データで高精度マッチング

### パフォーマンス

- **平均応答時間**: 20-50ms
- **検索精度**: 代替名検出100%
- **同時接続**: Cloud Run自動スケーリング対応

## 📊 使用例とテストケース

### 基本的な検索例

```bash
# 1. チキン料理の検索
curl "https://meal-analysis-api-v2-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=chicken&limit=3"

# 2. 代替名検索（ひよこ豆/ガルバンゾ豆）
curl "https://meal-analysis-api-v2-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=garbanzo&limit=5"

# 3. 部分一致検索
curl "https://meal-analysis-api-v2-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=brown%20rice&limit=5"
```

### レスポンス時間ベンチマーク

| クエリ | 結果数 | 応答時間 | 代替名検出 |
|--------|--------|----------|-----------|
| `chickpeas` | 8件 | 34ms | ✅ garbanzo beans |
| `garbanzo beans` | 33件 | 31ms | ✅ chickpeas |
| `tomato` | 28件 | 32ms | ✅ tomatoes |
| `chicken breast` | 27件 | 29ms | ✅ chicken, breast |
| `brown rice` | 28件 | 26ms | ✅ rice, brown |

## 🔧 デプロイメント情報

### 最新デプロイ状況

- **デプロイ日時**: 2025-09-13 18:18
- **リビジョン**: `meal-analysis-api-v2-00004-t4r`
- **コンテナイメージ**: `gcr.io/new-snap-calorie/meal-analysis-api-v2:latest`
- **ステータス**: 🟢 稼働中

### 環境変数

- `USDA_API_KEY`: vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg
- `GEMINI_PROJECT_ID`: new-snap-calorie
- `GEMINI_LOCATION`: us-central1
- `GEMINI_MODEL_NAME`: gemini-2.5-flash-preview-05-20

### 依存関係

- **Python**: 3.9-slim
- **主要ライブラリ**:
  - FastAPI 0.104.1
  - Elasticsearch 8.15.1
  - Pydantic 2.5.0
  - NLTK 3.8.1
  - Uvicorn 0.24.0

## 🛠 開発・テスト情報

### ローカル vs API比較テスト結果

test_mynetdiary_list_support_optimized.pyと同じテストケースでの比較:

- **結果一致率**: 100% (9/9 テスト)
- **代替名検出一致率**: 100% (9/9 テスト)
- **API応答時間**: 277.4ms (平均)
- **ローカル応答時間**: 415.0ms (平均)
- **性能向上**: API が 33% 高速

### テスト用スクリプト

プロジェクト内の比較テストスクリプト:
- `test_local_vs_api_comparison.py`: ローカルとAPIの詳細比較
- `test_mynetdiary_list_support_optimized.py`: オリジナルテストスイート

### デバッグ情報（debug=true時）

```json
{
  "debug_info": {
    "elasticsearch_query_used": "7_tier_optimized_search_name_list",
    "tier_scoring": {
      "tier_1_exact_match": 15,
      "tier_2_exact_description": 12,
      "tier_3_phrase_match": 10,
      "tier_4_phrase_description": 8,
      "tier_5_term_match": 6,
      "tier_6_multi_field": 4,
      "tier_7_fuzzy_match": 2
    }
  }
}
```

## 🚨 エラーハンドリング

### 一般的なエラー

```json
{
  "query_info": {
    "original_query": "x",
    "timestamp": "2025-09-13T18:20:00.000Z"
  },
  "suggestions": [],
  "metadata": {
    "total_suggestions": 0,
    "processing_time_ms": 15
  },
  "status": {
    "success": false,
    "message": "Query must be at least 2 characters long"
  }
}
```

### HTTPステータスコード

- `200`: 成功
- `400`: リクエストエラー（クエリ長さ不足など）
- `422`: バリデーションエラー
- `500`: サーバーエラー
- `503`: Elasticsearch接続エラー

## 📞 サポート・連絡先

- **プロジェクト**: meal_analysis_api_2
- **ブランチ**: query_system_demo
- **Google Cloud プロジェクト**: new-snap-calorie
- **Elasticsearch VM**: elasticsearch-vm (us-central1-a)

## 📚 関連ドキュメント

- `README_NUTRITION_SEARCH.md`: 栄養検索システム詳細
- `API_README.md`: API全般の仕様
- `md_files/api_deploy.md`: デプロイメント手順

## 🔄 更新履歴

### 2025-09-13 v2.0
- 7段階Tier検索システム実装
- 代替名検索機能追加（chickpeas ↔ garbanzo beans）
- Cloud Run本番環境デプロイ完了
- Elasticsearch VM統合
- ローカル vs API 100%互換性確認
- 平均応答時間33%改善

---

**🎊 APIは正常に稼働中です！**
本格的な食材検索予測機能をご利用いただけます。