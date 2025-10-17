# USDA Word Query API

USDA FNDDS統合データベースを利用した高精度栄養検索API（word_query_apiのUSDA版）

## 📋 概要

USDA FNDDS（Food and Nutrient Database for Dietary Studies）のデータを基に、1,542件の食材情報を提供する検索APIです。
Elasticsearchを使用した高速検索と、語幹化（Stemming）による柔軟なマッチングを実現しています。

### 主な特徴

- **高精度検索**: 7層のTierアルゴリズムによる検索最適化
- **食材タイプフィルタ**: raw（生食材）とprepared（準備済み）のフィルタリング
- **豊富な栄養情報**: カロリー、タンパク質、脂質、炭水化物の詳細データ
- **単位変換対応**: gram、oz、cup等、複数の単位に対応
- **語幹化検索**: Porter Stemmerによる柔軟な検索マッチング

### データ統計

- **総アイテム数**: 1,542件
  - 生食材（raw）: 1,399件
  - 準備済み（prepared）: 143件
- **データソース**: USDA FNDDS
- **インデックスサイズ**: 1.47 MB

## 🚀 セットアップ

### 1. 必要な環境

- Python 3.8+
- Elasticsearch 7.x+
- 必要なPythonパッケージ（requirements.txtを参照）

### 2. Elasticsearchインデックスの作成

```bash
# データローダースクリプトを実行
python apps/usda_word_query_api/elasticsearch/load_usda_db.py
```

このスクリプトは以下の処理を行います：
- Elasticsearchへの接続確認
- 既存インデックスの削除（存在する場合）
- 新しいインデックスの作成（USDA専用設定）
- usda_unified_db.jsonのロード（1,542件）
- インデックスの検証

### 3. APIサーバーの起動

```bash
# デフォルトポート8004で起動
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8004 python -m apps.usda_word_query_api.main
```

## 📚 API エンドポイント

### ベースURL

```
http://localhost:8004
```

### エンドポイント一覧

#### 1. ルートエンドポイント

```bash
GET /
```

レスポンス例:
```json
{
  "message": "USDA Word Query API",
  "version": "1.0.0",
  "status": "healthy",
  "data_source": "USDA FNDDS",
  "total_items": 1542
}
```

#### 2. ヘルスチェック

```bash
GET /health
```

レスポンス例:
```json
{
  "status": "healthy",
  "api": "usda-word-query",
  "version": "1.0.0",
  "architecture": "unified",
  "data_source": "USDA_FNDDS"
}
```

#### 3. 検索API（メインエンドポイント）

```bash
GET /api/v1/usda/suggest?q={query}&limit={limit}&ingredient_type={type}&debug={bool}
```

**パラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 説明 |
|----------|---|------|----------|------|
| `q` | string | ✅ | - | 検索クエリ（最小2文字） |
| `limit` | integer | ❌ | 10 | 結果数（1-50） |
| `ingredient_type` | string | ❌ | all | フィルタ: `raw`, `prepared`, `all` |
| `debug` | boolean | ❌ | false | デバッグ情報を含める |

**使用例:**

```bash
# 基本検索
curl "http://localhost:8004/api/v1/usda/suggest?q=chicken&limit=5"

# 生食材のみ
curl "http://localhost:8004/api/v1/usda/suggest?q=rice&ingredient_type=raw"

# 準備済み食材のみ
curl "http://localhost:8004/api/v1/usda/suggest?q=rice&ingredient_type=prepared"

# デバッグモード
curl "http://localhost:8004/api/v1/usda/suggest?q=chicken&debug=true"
```

**レスポンス例:**

```json
{
  "query_info": {
    "original_query": "chicken",
    "processed_query": "chicken",
    "timestamp": "2025-10-16T14:00:19.663897Z",
    "suggestion_type": "autocomplete"
  },
  "suggestions": [
    {
      "rank": 1,
      "suggestion": "Chicken feet",
      "match_type": "tier_1_exact",
      "confidence_score": 100.0,
      "food_info": {
        "search_name": "Chicken feet",
        "search_name_list": ["Chicken feet", "Feet chicken", "Chicken paws"],
        "description": "Chicken feet",
        "original_name": "Chicken feet",
        "ingredient_type": "raw"
      },
      "nutrition_preview": {
        "calories": 215.0,
        "protein": 19.4,
        "carbohydrates": 0.2,
        "fat": 14.6,
        "per_serving": "100g"
      },
      "default_unit": "gram",
      "default_nutrition": {
        "calorie": 2.15,
        "Protein_g": 0.194,
        "Total_Fat_g": 0.146,
        "Total_Carbs_g": 0.002
      },
      "unit_to_grams": {
        "gram": 1.0,
        "foot": 35,
        "oz": 28.35,
        "lb": 453.6
      }
    }
  ],
  "metadata": {
    "total_suggestions": 5,
    "total_hits": 56,
    "search_time_ms": 325,
    "processing_time_ms": 325,
    "elasticsearch_index": "usda_unified_nutrition_db"
  },
  "status": {
    "success": true,
    "message": "USDA suggestions generated successfully"
  }
}
```

#### 4. ヘルスチェック（検索API）

```bash
GET /api/v1/usda/suggest/health
```

レスポンス例:
```json
{
  "status": "healthy",
  "service": "usda_suggestion_api",
  "elasticsearch_index": "usda_unified_nutrition_db",
  "algorithm": "usda_7_tier_optimized",
  "test_query_success": true
}
```

#### 5. 統計情報

```bash
GET /api/v1/usda/stats
```

レスポンス例:
```json
{
  "status": "success",
  "index_name": "usda_unified_nutrition_db",
  "total_documents": 1542,
  "ingredient_type_breakdown": {
    "raw": 1399,
    "prepared": 143
  },
  "timestamp": "2025-10-16T14:00:19.201196Z"
}
```

## 🔍 検索アルゴリズム

7層のTierアルゴリズムを採用:

| Tier | マッチタイプ | ブースト | 説明 |
|------|------------|---------|------|
| 1 | Exact Match (stemmed_search_name) | 15 | 語幹化された検索名での完全一致 |
| 2 | Exact Match (stemmed_description) | 12 | 語幹化された説明での完全一致 |
| 3 | Phrase Match (stemmed_search_name) | 10 | 語幹化された検索名でのフレーズ一致 |
| 4 | Phrase Match (stemmed_description) | 8 | 語幹化された説明でのフレーズ一致 |
| 5 | Term Match | 6 | キーワード一致 |
| 6 | Multi-field Match | 4 | 複数フィールドでのマッチング |
| 7 | Fuzzy Match | 2 | あいまいマッチング |

## 🏗️ プロジェクト構造

```
apps/usda_word_query_api/
├── main.py                     # FastAPIアプリケーション
├── config.py                   # 設定ファイル
├── README.md                   # このファイル
├── endpoints/
│   ├── __init__.py
│   └── usda_search.py         # 検索エンドポイント
├── elasticsearch/
│   ├── __init__.py
│   ├── index_settings.py      # インデックス設定
│   └── load_usda_db.py        # データローダー
└── models/
    └── __init__.py
```

## 🔧 設定

### config.py

```python
# Elasticsearch設定
ELASTICSEARCH_URL = "http://35.193.16.212:9200"
USDA_INDEX_NAME = "usda_unified_nutrition_db"

# API設定
API_TITLE = "USDA Word Query API"
API_VERSION = "1.0.0"
DEFAULT_PORT = 8004

# 検索設定
DEFAULT_SEARCH_SIZE = 10
MAX_SEARCH_SIZE = 50
MIN_QUERY_LENGTH = 2

# 食材タイプ
INGREDIENT_TYPES = ["raw", "prepared"]
```

## 📊 パフォーマンス

- **平均検索時間**: 290-330ms
- **同時接続**: サポート（FastAPI非同期処理）
- **インデックスサイズ**: 1.47 MB
- **レスポンスフォーマット**: JSON

## 🔗 関連ドキュメント

- **Swagger UI**: http://localhost:8004/docs
- **ReDoc**: http://localhost:8004/redoc
- **元データ**: `/Users/odasoya/meal_analysis_api_2/usda_data_processing/db/usda_unified_db.json`

## 📝 開発メモ

### 既存APIとの共存

本APIは独立したサービスとして実装されており、既存のword_query_api（ポート8002）と並行して動作可能です。

### Elasticsearchインデックス

- **インデックス名**: `usda_unified_nutrition_db`
- **既存インデックス**: `mynetdiary_converted_tool_calls_list_stemmed_with_nutrition`（word_query_api用）

両方のインデックスは独立しており、互いに干渉しません。

## 🎉 まとめ

USDA Word Query APIは、word_query_apiのUSDA版として、USDA FFNDSデータを活用した高精度な栄養検索システムです。
語幹化による柔軟な検索、ingredient_typeフィルタ、豊富な栄養情報により、
食事分析アプリケーションの基盤として最適です。
