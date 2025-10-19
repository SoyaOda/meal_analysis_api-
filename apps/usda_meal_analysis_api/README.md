# USDA Meal Analysis API

USDA FNDDS統合データベースを使用した食事分析API（meal_analysis_apiのUSDA版）

## 📋 概要

このAPIは、USDA Word Query API（ポート8004）と連携して動作し、USDA FFNDSデータベースに基づいた食事分析を提供します。

### 主な特徴

- **USDA FNDDS統合**: 1,542件のUSDA食材データベースを使用
- **音声入力対応**: 音声ファイルから食事内容を分析
- **画像入力対応**: 食事画像から料理と食材を識別
- **高精度栄養計算**: USDA栄養データに基づく正確な栄養価計算
- **Word Query API連携**: usda_word_query_apiを使用した食材検索

### データソース

- **栄養データベース**: USDA FNDDS
- **総食材数**: 1,542件
  - 生食材: 1,399件
  - 準備済み食材: 143件

## 🚀 セットアップ

### 前提条件

1. **USDA Word Query APIの起動**（必須）

```bash
# 別ターミナルでポート8004で起動
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8004 python -m apps.usda_word_query_api.main
```

2. **Elasticsearchの設定**

USDA Word Query APIが使用するElasticsearchインデックス（`usda_unified_nutrition_db`）が正しく設定されている必要があります。

### APIサーバーの起動

#### デフォルト起動（ポート8005）

```bash
# ローカルのusda_word_query_apiを使用（推奨）
WORD_QUERY_API_URL=http://localhost:8004 \
INGREDIENT_ELASTICSEARCH_INDEX=usda_unified_nutrition_db \
NUTRITION_DATA_SOURCE=usda_api \
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
GOOGLE_CLOUD_PROJECT=new-snap-calorie \
PORT=8005 \
python -m apps.usda_meal_analysis_api.main
```

#### 環境変数の説明

| 環境変数 | 必須 | デフォルト | 説明 |
|---------|------|-----------|------|
| `WORD_QUERY_API_URL` | ✅ | `https://word-query-api-...` | USDA Word Query APIのURL（ローカル: `http://localhost:8004`） |
| `INGREDIENT_ELASTICSEARCH_INDEX` | ✅ | `mynetdiary_...` | Elasticsearchインデックス名（USDA用: `usda_unified_nutrition_db`） |
| `NUTRITION_DATA_SOURCE` | ✅ | `mynetdiary_api` | データソース識別子（USDA用: `usda_api`） |
| `PYTHONPATH` | ✅ | - | プロジェクトルートパス |
| `GOOGLE_CLOUD_PROJECT` | ✅ | `new-snap-calorie` | Google Cloudプロジェクト名 |
| `PORT` | ❌ | 8005 | APIサーバーのポート番号 |

## 📚 API エンドポイント

### ベースURL

```
http://localhost:8005
```

### エンドポイント一覧

#### 1. ルートエンドポイント

```bash
GET /
```

レスポンス例:
```json
{
  "message": "USDA 食事分析 API v2.0 - USDA FNDDS統合アーキテクチャ版",
  "version": "2.1.0-usda",
  "architecture": "Unified Component-based Pipeline with USDA FNDDS",
  "docs": "/docs"
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
  "version": "v2.1-usda",
  "architecture": "unified",
  "data_source": "USDA_FNDDS",
  "word_query_api": "usda_word_query_api",
  "components": [
    "Phase1Component",
    "Phase1SpeechComponent",
    "AdvancedNutritionSearchComponent",
    "NutritionCalculationComponent"
  ]
}
```

#### 3. 画像入力による食事分析

```bash
POST /api/v1/meal-analyses/complete
Content-Type: multipart/form-data

Parameters:
- image: 食事画像ファイル
- user_context: コンテキスト情報（オプション）
```

**使用例:**

```bash
curl -X POST "http://localhost:8005/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=dinner analysis"
```

#### 4. 音声入力による食事分析

```bash
POST /api/v1/meal-analyses/voice
Content-Type: multipart/form-data

Parameters:
- audio_file: 音声ファイル（WAV/MP3）
- user_context: コンテキスト情報（オプション）
```

**使用例:**

```bash
curl -X POST "http://localhost:8005/api/v1/meal-analyses/voice" \
  -F "audio_file=@test-audio/lunch_detailed.wav" \
  -F "user_context=lunch analysis"
```

### レスポンス形式

すべてのエンドポイントは以下の形式でレスポンスを返します：

```json
{
  "analysis_id": "eaf0df18",
  "input_type": "image",
  "total_dishes": 5,
  "total_ingredients": 14,
  "processing_time_seconds": 31.27,
  "dishes": [
    {
      "dish_name": "Meatloaf",
      "confidence": 0.95,
      "ingredients": [
        {
          "ingredient_name": "Beef, for use with vegetables",
          "weight_g": 150.0,
          "nutrition_per_100g": {
            "calories": 191.0,
            "protein": 32.4,
            "fat": 6.82,
            "carbs": 0.0
          },
          "calculated_nutrition": {
            "calories": 286.5,
            "protein": 48.6,
            "fat": 10.23,
            "carbs": 0.0
          },
          "source_db": "usda_api"
        }
      ],
      "total_nutrition": {
        "calories": 346.8,
        "protein": 50.74,
        "fat": 11.03,
        "carbs": 11.14
      }
    }
  ],
  "total_nutrition": {
    "calories": 1027.0,
    "protein": 71.87,
    "fat": 42.33,
    "carbs": 88.73
  },
  "ai_model_used": "google/gemma-3-27b-it",
  "match_rate_percent": 78.6
}
```

## 🔧 アーキテクチャ

### コンポーネント構成

1. **Phase1Component**: 画像から料理・食材を識別
2. **Phase1SpeechComponent**: 音声から料理・食材を識別
3. **AdvancedNutritionSearchComponent**: USDA Word Query APIを使用した食材検索
4. **NutritionCalculationComponent**: 栄養価計算

### データフロー

```
[入力: 画像/音声]
  ↓
[Phase1: 料理・食材識別]
  ↓
[Phase2: USDA Word Query APIで栄養検索]
  ↓ (http://localhost:8004/api/v1/nutrition/suggest)
[Phase3: 栄養価計算]
  ↓
[出力: 分析結果JSON]
```

## 📊 既存APIとの比較

| 項目 | Meal Analysis API | USDA Meal Analysis API |
|------|------------------|----------------------|
| ポート | 8001 | 8005 |
| Word Query API | word_query_api (8002) | usda_word_query_api (8004) |
| データベース | MyNetDiary | USDA FNDDS |
| 総食材数 | ~8,000件 | 1,542件 |
| データソース | mynetdiary_api | usda_api |
| インデックス | mynetdiary_converted_... | usda_unified_nutrition_db |

## 🔗 関連ドキュメント

- **Swagger UI**: http://localhost:8005/docs
- **ReDoc**: http://localhost:8005/redoc
- **USDA Word Query API**: http://localhost:8004/docs

## 📝 開発メモ

### USDA固有の設定

本APIはUSDA FFNDSデータベースを使用するため、以下の環境変数を**必ず**設定してください：

```bash
export WORD_QUERY_API_URL=http://localhost:8004
export INGREDIENT_ELASTICSEARCH_INDEX=usda_unified_nutrition_db
export NUTRITION_DATA_SOURCE=usda_api
```

### トラブルシューティング

1. **Word Query API接続エラー**
   - usda_word_query_apiが起動しているか確認
   - `http://localhost:8004/health` でヘルスチェック

2. **食材が見つからない**
   - Elasticsearchインデックス `usda_unified_nutrition_db` が存在するか確認
   - `apps/usda_word_query_api/elasticsearch/load_usda_db.py` でインデックスを再作成

3. **音声認識エラー**
   - Google Cloud認証が正しく設定されているか確認
   - `GOOGLE_CLOUD_PROJECT` 環境変数が設定されているか確認

## 🎉 まとめ

USDA Meal Analysis APIは、USDA FFNDSデータベースを活用した高精度な食事分析システムです。
既存のmeal_analysis_apiと同じアーキテクチャを使用しながら、USDAの公式栄養データベースに基づいた
より正確な栄養情報を提供します。
