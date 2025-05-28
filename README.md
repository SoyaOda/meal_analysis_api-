# 食事分析 API (Meal Analysis API)

## 概要

この API は、Google Gemini AI と USDA データベースを使用して食事の画像を分析し、料理名、食材、重量、栄養成分を構造化された JSON で返す FastAPI アプリケーションです。

## 主な機能

- **フェーズ 1**: Gemini AI による食事画像の分析（料理識別、食材抽出、重量推定）
- **フェーズ 2**: USDA データベースによる栄養成分の精緻化（英語版のみ）
- 複数の料理が含まれる画像の分析
- OpenAPI 3.0 仕様書による詳細な API 文書化
- Vertex AI 統合による本番環境対応

## プロジェクト構造

```
meal_analysis_api/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── meal_analyses.py      # メイン分析エンドポイント
│   │   │   └── health.py             # ヘルスチェック
│   │   └── schemas/
│   │       ├── meal.py               # Pydanticモデル
│   │       └── usda.py               # USDAレスポンスモデル
│   ├── core/
│   │   └── config.py                 # 設定管理
│   ├── services/
│   │   ├── gemini_service.py         # Gemini AI統合
│   │   ├── usda_client.py            # USDA API クライアント
│   │   └── meal_normalization_service.py  # フェーズ2統合サービス
│   ├── prompts/                      # Geminiプロンプトテンプレート
│   └── main.py                       # FastAPIアプリケーション
├── test_images/                      # テスト用画像
├── requirements.txt                  # Python依存関係
├── openapi.yaml                     # OpenAPI仕様書
└── service-account-key.json         # GCP認証キー
```

## セットアップ

### 1. 依存関係のインストール

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境のアクティベート
source venv/bin/activate  # macOS/Linux

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. Google Cloud 設定

#### Google Cloud SDK のインストール

まだインストールしていない場合は、以下からインストールしてください：
https://cloud.google.com/sdk/docs/install

#### Google Cloud 認証の設定

開発環境では以下のコマンドで認証を設定：

```bash
# Google Cloudにログイン
gcloud auth login

# アプリケーションのデフォルト認証情報を設定
gcloud auth application-default login

# プロジェクトIDを設定
gcloud config set project YOUR_PROJECT_ID
```

本番環境ではサービスアカウントキーを使用：

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your-service-account-key.json"
```

#### Vertex AI API の有効化

```bash
# Vertex AI APIを有効化
gcloud services enable aiplatform.googleapis.com
```

### 3. 環境変数の設定

以下の環境変数を設定してください：

```bash
# USDA API設定
export USDA_API_KEY="your-usda-api-key"

# Vertex AI設定（開発環境）
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
export GEMINI_PROJECT_ID="your-gcp-project-id"
export GEMINI_LOCATION="us-central1"
export GEMINI_MODEL_NAME="gemini-2.5-flash-preview-05-20"
```

## サーバー起動

### 開発環境での起動

提供された完全なコマンドでサーバーを起動：

```bash
export USDA_API_KEY="vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg" && export GOOGLE_APPLICATION_CREDENTIALS="/Users/odasoya/meal_analysis_api /service-account-key.json" && export GEMINI_PROJECT_ID=recording-diet-ai-3e7cf && export GEMINI_LOCATION=us-central1 && export GEMINI_MODEL_NAME=gemini-2.5-flash-preview-05-20 && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

または、環境変数を個別に設定してから起動：

```bash
# 環境変数設定
export USDA_API_KEY="vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg"
export GOOGLE_APPLICATION_CREDENTIALS="/Users/odasoya/meal_analysis_api /service-account-key.json"
export GEMINI_PROJECT_ID="recording-diet-ai-3e7cf"
export GEMINI_LOCATION="us-central1"
export GEMINI_MODEL_NAME="gemini-2.5-flash-preview-05-20"

# サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

サーバーが起動すると、以下の URL でアクセス可能になります：

- API: http://localhost:8000
- ドキュメント: http://localhost:8000/docs
- ヘルスチェック: http://localhost:8000/health

## テストの実行

### 1. 基本テスト（フェーズ 1 のみ）

```bash
python test_phase1_only.py
```

### 2. 統合テスト（英語版フェーズ 1+フェーズ 2）

**重要**: サーバーが起動している状態で実行してください。

```bash
# 別のターミナルで実行
python test_english_phase2.py
```

このテストは以下を実行します：

1. **フェーズ 1**: 食事画像の分析（英語の食材名で出力）
2. **フェーズ 2**: USDA データベースとの照合による栄養成分の精緻化

テスト画像は `test_images/food3.jpg` を使用し、以下の情報を取得します：

- 料理名と食材の識別
- 重量の推定
- USDA FDC ID による栄養成分の精緻化

### 3. その他のテスト

```bash
# USDA APIのみのテスト
python test_usda_only.py

# Vertex AI直接テスト
python test_direct_vertexai.py

# 単一フェーズ2テスト
python test_single_phase2.py
```

## API 使用方法

### フェーズ 1: 基本分析

```bash
curl -X POST "http://localhost:8000/api/v1/meal-analyses" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food1.jpg"
```

### フェーズ 2: USDA 精緻化（英語版）

```bash
# 最初にフェーズ1の結果を取得
initial_result=$(curl -X POST "http://localhost:8000/api/v1/meal-analyses" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg")

# フェーズ2で精緻化
curl -X POST "http://localhost:8000/api/v1/meal-analyses/refine" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg" \
  -F "initial_analysis_data=$initial_result"
```

## レスポンス例

### フェーズ 1 レスポンス

```json
{
  "analysis_timestamp": "2024-01-20T10:30:00Z",
  "total_estimated_weight_g": 450,
  "dishes": [
    {
      "dish_name": "Grilled Salmon",
      "ingredients": [
        {
          "ingredient_name": "salmon",
          "weight_g": 120
        }
      ]
    }
  ]
}
```

### フェーズ 2 レスポンス

```json
{
  "analysis_timestamp": "2024-01-20T10:30:00Z",
  "total_estimated_weight_g": 450,
  "dishes": [
    {
      "dish_name": "Grilled Salmon",
      "ingredients": [
        {
          "ingredient_name": "salmon",
          "weight_g": 120,
          "fdc_id": 175167,
          "usda_source_description": "Fish, salmon, Atlantic, farmed, cooked, dry heat",
          "key_nutrients_per_100g": {
            "protein": 25.44,
            "fat": 12.35,
            "carbs": 0
          }
        }
      ]
    }
  ]
}
```

## エラーハンドリング

API は以下の HTTP ステータスコードを返します：

- `200 OK`: 正常な分析完了
- `400 Bad Request`: 不正なリクエスト（画像形式エラーなど）
- `422 Unprocessable Entity`: バリデーションエラー
- `500 Internal Server Error`: サーバー内部エラー

## トラブルシューティング

### 認証エラーが発生する場合

```bash
# 現在の認証状態を確認
gcloud auth list

# 現在のプロジェクト設定を確認
gcloud config list

# 必要に応じて再度認証
gcloud auth application-default login
```

### Vertex AI API が有効になっていない場合

```bash
# APIの有効状況を確認
gcloud services list --enabled | grep aiplatform

# 有効でない場合は有効化
gcloud services enable aiplatform.googleapis.com
```

### USDA API エラーが発生する場合

- API キーが正しく設定されているか確認
- レートリミット（1,000 件/時）に達していないか確認

## 開発情報

- **フレームワーク**: FastAPI
- **AI サービス**: Google Vertex AI (Gemini 2.5 Flash)
- **データベース**: USDA FoodData Central
- **認証**: Google Cloud サービスアカウント
- **Python バージョン**: 3.8+

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 注意事項

**セキュリティ**: API キーやサービスアカウントキーは絶対にリポジトリにコミットしないでください。環境変数として安全に管理してください。
