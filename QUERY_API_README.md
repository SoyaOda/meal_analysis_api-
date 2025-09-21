# Word Query API Documentation

## 概要

MyNetDiary栄養検索システムを基盤とした高性能な食材検索予測APIです。ユーザーが食材名を入力する際のリアルタイム検索候補提案機能を提供します。

## 🚀 本番環境情報

### API基本情報
- **API URL**: `https://word-query-api-1077966746907.us-central1.run.app`
- **バージョン**: v2.0 - 栄養検索専用版
- **プラットフォーム**: Google Cloud Run (独立サービス)
- **データベース**: Elasticsearch 8.15.1 (Google Compute Engine VM)
- **OpenAPI/Swagger**: 完全対応（リアルなExample値付き）

### インフラ構成
- **Cloud Run**:
  - メモリ: 1GB
  - CPU: 1コア
  - タイムアウト: 300秒
  - 自動スケーリング対応
  - 独立したword-query-apiサービス
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
  "message": "Word Query API v2.0 - 栄養検索専用版",
  "version": "2.0.0",
  "architecture": "Nutrition Search Service",
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
  "components": ["ElasticsearchComponent", "MyNetDiaryNutritionSearchComponent"]
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
curl "https://word-query-api-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=chicken&limit=5"

# デバッグ情報付き
curl "https://word-query-api-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=chickpeas&limit=10&debug=true"
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
        "calories": 165.0,
        "protein": 31.0,
        "carbohydrates": 0.0,
        "fat": 3.6,
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

### Exact Match優先検索戦略 + 7段階Tierシステム

#### **Exact Match Layer (最優先)**
- **exact_match** (Score: 999+): original_name完全一致 (Case Sensitive)
- **exact_match** (Score: 998+): original_name完全一致 (Case Insensitive)

#### **7段階Tier検索 (フォールバック)**
1. **tier_1_exact** (Score: 15+): search_name完全一致
2. **tier_2_description** (Score: 12+): description完全一致
3. **tier_3_phrase** (Score: 10+): search_nameプレフィックス一致
4. **tier_4_phrase_desc** (Score: 8+): descriptionプレフィックス一致
5. **tier_5_term** (Score: 6+): search_name部分一致
6. **tier_6_multi** (Score: 4+): description部分一致
7. **tier_7_fuzzy** (Score: 2+): ファジーマッチ

#### **match_type値の説明**
| match_type | 説明 | 例 |
|------------|------|-----|
| `exact_match` | original_name完全一致 | "Rice brown long grain cooked without salt" |
| `tier_1_exact` | search_name完全一致 | "Rice" |
| `tier_3_phrase` | プレフィックス一致 | "chicken" → "chicken breast" |
| `tier_5_term` | 部分一致 | "breast" → "chicken breast" |
| `tier_7_fuzzy` | ファジーマッチ | その他のマッチ |

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
curl "https://word-query-api-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=chicken&limit=3"

# 2. 代替名検索（ひよこ豆/ガルバンゾ豆）
curl "https://word-query-api-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=garbanzo&limit=5"

# 3. 部分一致検索
curl "https://word-query-api-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=brown%20rice&limit=5"

# 4. Exact Match検索（original_name完全一致）
curl "https://word-query-api-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=Rice%20brown%20long%20grain%20cooked%20without%20salt&limit=1"

# 5. match_type詳細確認（デバッグ付き）
curl "https://word-query-api-1077966746907.us-central1.run.app/api/v1/nutrition/suggest?q=chicken&limit=3&debug=true"
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

- **デプロイ日時**: 2025-09-18 18:44
- **リビジョン**: `word-query-api-00005-266`
- **コンテナイメージ**: `gcr.io/new-snap-calorie/word-query-api:nutrition-only-v2`
- **ステータス**: 🟢 稼働中（栄養検索専用版）

### 環境変数

- `elasticsearch_url`: http://35.193.16.212:9200
- `elasticsearch_index_name`: mynetdiary_list_support_db
- `API_LOG_LEVEL`: INFO
- `HOST`: 0.0.0.0
- `PORT`: 8000

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
    "elasticsearch_query_used": "exact_match_first_with_7_tier_fallback",
    "tier_scoring": {
      "exact_match_original_name": 999,
      "exact_match_case_insensitive": 998,
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
- **ブランチ**: query_api_deploy
- **Google Cloud プロジェクト**: new-snap-calorie
- **Elasticsearch VM**: elasticsearch-vm (us-central1-a)

## 📚 関連ドキュメント

- `README_NUTRITION_SEARCH.md`: 栄養検索システム詳細
- `API_README.md`: API全般の仕様
- `md_files/api_deploy.md`: デプロイメント手順

## 🔄 更新履歴

### 2025-09-21 v2.1 Exact Match強化版 - 検索精度向上リリース 🎯

#### 🛠 主要変更項目
- ✅ **Exact Match機能実装**: original_name完全一致で最高精度検索を実現
- ✅ **match_type細分化**: 11種類の詳細なマッチタイプ分類システム
- ✅ **Swagger仕様完全対応**: MatchType Enumで全てのmatch_type値を明示
- ✅ **検索精度向上**: Brown Rice問題等の誤判定を根本解決
- ✅ **下位互換性維持**: 既存のmatch_type値も継続サポート

#### 🔧 技術的変更
1. **Exact Match Layer追加**:
   - original_name.keyword完全一致 (Case Sensitive: Score 999)
   - original_name完全一致 (Case Insensitive: Score 998)
   - 7-Tierアルゴリズムよりも優先実行

2. **match_type詳細化**:
   - `exact_match`: original_name完全一致
   - `tier_1_exact` ~ `tier_7_fuzzy`: 7段階詳細分類
   - 従来の`fuzzy_match`, `prefix_match`, `partial_match`も維持

3. **判定ロジック改善**:
   - `determine_match_type()`関数で_explanationフィールド活用
   - Elasticsearchの検索戦略結果を正確に反映
   - 誤判定問題（Brown Rice等）を根本解決

#### 🎯 解決した課題
- **Brown Rice問題**: "Rice brown long grain cooked without salt" が `fuzzy_match` → `exact_match` に修正
- **100%マッチ率誤表示**: API応答率とマッチ精度を正確に区別
- **Swagger仕様不備**: 全11種類のmatch_type値をEnum定義

### 2025-09-18 v2.0 栄養検索専用版 - サービス分離リリース 🎯

#### 🛠 主要変更項目
- ✅ **完全分離**: meal-analysis-apiから栄養検索機能のみを分離
- ✅ **不要エンドポイント削除**: `/api/v1/meal-analyses/complete` エンドポイントを削除
- ✅ **コンポーネント名修正**: 実際の技術スタック反映 (Elasticsearch + MyNetDiary)
- ✅ **API専用化**: word-query-apiを栄養検索専用サービスとして最適化
- ✅ **安全デプロイ**: meal-analysis-apiを影響させずに独立更新
- ✅ **パフォーマンス向上**: 13-88ms高速レスポンス確認

#### 🔧 技術的変更
1. **サービス分離**:
   - meal_analysis.routerの削除
   - nutrition_search.routerのみ保持
   - タイトル変更: "Word Query API v2.0 - 栄養検索専用版"

2. **コンポーネント正確化**:
   - 旧: `["USDAQueryComponent", "NutritionSearchComponent"]`
   - 新: `["ElasticsearchComponent", "MyNetDiaryNutritionSearchComponent"]`

3. **デプロイ最適化**:
   - 新イメージ: nutrition-only-v2
   - リビジョン: word-query-api-00005-266
   - 完全独立運用

### 2025-09-13 v2.0
- 7段階Tier検索システム実装
- 代替名検索機能追加（chickpeas ↔ garbanzo beans）
- Cloud Run本番環境デプロイ完了
- Elasticsearch VM統合
- ローカル vs API 100%互換性確認

---

**🎊 Word Query API 栄養検索専用版が正常稼働中！**
高速で正確な食材検索予測機能を専用APIとして提供しています。

**📖 Swagger UI**: https://word-query-api-1077966746907.us-central1.run.app/docs