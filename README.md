# 食事分析 API (Meal Analysis API) v2.0

## 概要

この API は、**Google Gemini AI** と **USDA データベース**を使用した高度な食事画像分析システムです。**動的栄養計算機能**により、料理の特性に応じて最適な栄養計算戦略を自動選択し、正確な栄養価情報を提供します。

## 🌟 主な機能

### **新機能: 動的栄養計算システム v2.0**

- **🧠 AI 駆動の計算戦略決定**: Gemini AI が各料理に対して最適な栄養計算方法を自動選択
  - `dish_level`: シンプルな食品（緑茶、果物など）は料理全体の USDA ID で計算
  - `ingredient_level`: 複雑な料理（サラダ、炒め物など）は食材ごとに詳細計算して集計
- **🎯 高精度栄養計算**: 食材重量 × 100g あたり栄養価で正確な実栄養価を算出
- **📊 3 層集計システム**: 食材 → 料理 → 食事全体の自動栄養集計
- **⚡ リアルタイム USDA 統合**: 20,000+ 食品データベースとの即座な照合

### **コア機能**

- **フェーズ 1**: Gemini AI による食事画像の分析（料理識別、食材抽出、重量推定）
- **フェーズ 2**: USDA データベースによる栄養成分の精緻化と動的計算
- **複数料理対応**: 1 枚の画像で複数の料理を同時分析
- **英語・日本語対応**: 多言語での食材・料理認識
- **OpenAPI 3.0 準拠**: 完全な API 文書化とタイプ安全性

## 🏗 プロジェクト構造

```
meal_analysis_api/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── meal_analyses.py          # フェーズ1: 基本分析エンドポイント
│   │   │   └── meal_analyses_refine.py   # フェーズ2: 動的栄養計算エンドポイント
│   │   └── schemas/
│   │       └── meal.py                   # Pydanticモデル（栄養計算対応）
│   ├── core/
│   │   └── config.py                     # 設定管理
│   ├── services/
│   │   ├── gemini_service.py             # Gemini AI統合（2フェーズ対応）
│   │   ├── usda_service.py               # USDA API クライアント
│   │   └── nutrition_calculation_service.py # 栄養計算エンジン
│   ├── prompts/                          # AI プロンプトテンプレート
│   │   ├── phase1_system_prompt.txt      # フェーズ1システムプロンプト
│   │   ├── phase1_user_prompt_template.txt
│   │   ├── phase2_system_prompt.txt      # フェーズ2システムプロンプト（戦略決定用）
│   │   └── phase2_user_prompt_template.txt
│   └── main.py                           # FastAPIアプリケーション
├── test_images/                          # テスト用画像
├── test_english_phase2.py                # 統合テストスクリプト
├── requirements.txt                      # Python依存関係
└── service-account-key.json             # GCP認証キー
```

## 🚀 セットアップ

### 1. 依存関係のインストール

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境のアクティベート
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate     # Windows

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

# Vertex AI設定
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
export GEMINI_PROJECT_ID="your-gcp-project-id"
export GEMINI_LOCATION="us-central1"
export GEMINI_MODEL_NAME="gemini-2.5-flash-preview-05-20"
```

## 🖥 サーバー起動

### 開発環境での起動

**🎯 推奨方法 (main.py 直接実行)**

main.py には環境変数の自動設定機能が組み込まれているため、最も簡単な起動方法です：

```bash
# モジュールとして実行（推奨）
python -m app.main
```

**従来の方法 (uvicorn コマンド)**

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

**⚠️ 注意**: `python app/main.py`では相対インポートエラーが発生します。必ず`python -m app.main`を使用してください。

サーバーが起動すると、以下の URL でアクセス可能になります：

- **API**: http://localhost:8000
- **ドキュメント**: http://localhost:8000/docs
- **ヘルスチェック**: http://localhost:8000/health

## 🧪 テストの実行

### 1. 基本テスト（フェーズ 1 のみ）

```bash
python test_phase1_only.py
```

### 2. **🔥 統合テスト（動的栄養計算システム）**

**重要**: サーバーが起動している状態で実行してください。

```bash
# 別のターミナルで実行
python test_english_phase2.py
```

このテストは以下を実行します：

1. **フェーズ 1**: 食事画像の分析（英語の食材名で出力）
2. **フェーズ 2**:
   - Gemini AI による最適計算戦略の決定
   - USDA データベースとの自動照合
   - 動的栄養計算（dish_level/ingredient_level）
   - 食事全体の栄養集計

**期待される結果例**:

```
食事全体の栄養価:
- カロリー: 337.95 kcal
- たんぱく質: 13.32g
- 炭水化物: 56.19g
- 脂質: 6.67g
```

### 3. その他のテスト

```bash
# USDA APIのみのテスト
python test_usda_only.py

# Vertex AI直接テスト
python test_direct_vertexai.py
```

## 📡 API 使用方法

### 🔥 完全分析 (推奨): 全フェーズ統合

**1 つのリクエストで全ての分析を実行**

```bash
curl -X POST "http://localhost:8000/api/v1/meal-analyses/complete" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg"
```

このエンドポイントは以下を自動実行します：

- フェーズ 1: 画像分析
- USDA 照合: 食材データベース検索
- フェーズ 2: 計算戦略決定
- 栄養計算: 最終栄養価算出
- 結果保存: 自動的にファイル保存

**保存された結果の取得**

```bash
# 全結果一覧
curl "http://localhost:8000/api/v1/meal-analyses/results"

# 特定の結果取得
curl "http://localhost:8000/api/v1/meal-analyses/results/{analysis_id}"
```

### フェーズ 1: 基本分析

```bash
curl -X POST "http://localhost:8000/api/v1/meal-analyses" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg"
```

### フェーズ 2: 動的栄養計算

```bash
# 最初にフェーズ1の結果を取得
initial_result=$(curl -X POST "http://localhost:8000/api/v1/meal-analyses" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg")

# フェーズ2で動的栄養計算
curl -X POST "http://localhost:8000/api/v1/meal-analyses/refine" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg" \
  -F "initial_analysis_data=$initial_result"
```

## 📋 レスポンス例

### フェーズ 1 レスポンス

```json
{
  "dishes": [
    {
      "dish_name": "Fried Fish with Spaghetti and Tomato Sauce",
      "type": "Main Dish",
      "quantity_on_plate": "2 pieces of fish, 1 small serving of spaghetti",
      "ingredients": [
        {
          "ingredient_name": "White Fish Fillet",
          "weight_g": 150.0
        },
        {
          "ingredient_name": "Spaghetti (cooked)",
          "weight_g": 80.0
        }
      ]
    }
  ]
}
```

### フェーズ 2 レスポンス（動的栄養計算）

```json
{
  "dishes": [
    {
      "dish_name": "Spinach and Daikon Radish Aemono",
      "type": "Side Dish",
      "calculation_strategy": "ingredient_level",
      "fdc_id": null,
      "ingredients": [
        {
          "ingredient_name": "Spinach",
          "weight_g": 80.0,
          "fdc_id": 1905313,
          "usda_source_description": "SPINACH",
          "key_nutrients_per_100g": {
            "calories_kcal": 24.0,
            "protein_g": 3.53,
            "carbohydrates_g": 3.53,
            "fat_g": 0.0
          },
          "actual_nutrients": {
            "calories_kcal": 19.2,
            "protein_g": 2.82,
            "carbohydrates_g": 2.82,
            "fat_g": 0.0
          }
        }
      ],
      "dish_total_actual_nutrients": {
        "calories_kcal": 57.45,
        "protein_g": 3.85,
        "carbohydrates_g": 4.57,
        "fat_g": 3.31
      }
    },
    {
      "dish_name": "Green Tea",
      "type": "Drink",
      "calculation_strategy": "dish_level",
      "fdc_id": 1810668,
      "usda_source_description": "GREEN TEA",
      "key_nutrients_per_100g": {
        "calories_kcal": 0.0,
        "protein_g": 0.0,
        "carbohydrates_g": 0.0,
        "fat_g": 0.0
      },
      "dish_total_actual_nutrients": {
        "calories_kcal": 0.0,
        "protein_g": 0.0,
        "carbohydrates_g": 0.0,
        "fat_g": 0.0
      }
    }
  ],
  "total_meal_nutrients": {
    "calories_kcal": 337.95,
    "protein_g": 13.32,
    "carbohydrates_g": 56.19,
    "fat_g": 6.67
  },
  "warnings": null,
  "errors": null
}
```

## 🔧 技術仕様

### 動的計算戦略の決定ロジック

**Dish Level (`dish_level`)**:

- シンプルな単品食品（果物、飲み物、基本食材）
- 標準化された既製品で適切な USDA ID が存在する場合
- 例: 緑茶、りんご、白米

**Ingredient Level (`ingredient_level`)**:

- 複雑な調理済み料理（炒め物、サラダ、スープ）
- 複数食材の組み合わせで料理全体の USDA ID が不適切な場合
- 例: 野菜炒め、手作りサラダ、味噌汁

### 栄養計算式

```
実栄養価 = (100gあたり栄養価 ÷ 100) × 推定重量(g)
```

### 集計階層

1. **食材レベル**: 個別食材の重量 × 100g 栄養価
2. **料理レベル**: 食材レベルの合計 または 料理全体計算
3. **食事レベル**: 全料理の栄養価合計

## ⚠️ エラーハンドリング

API は以下の HTTP ステータスコードを返します：

- `200 OK`: 正常な分析完了
- `400 Bad Request`: 不正なリクエスト（画像形式エラーなど）
- `422 Unprocessable Entity`: バリデーションエラー
- `503 Service Unavailable`: 外部サービス（USDA/Gemini）エラー
- `500 Internal Server Error`: サーバー内部エラー

## 🔍 トラブルシューティング

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
- レートリミット（3,600 件/時）に達していないか確認
- ネットワーク接続を確認

## 💻 開発情報

- **フレームワーク**: FastAPI 0.104+
- **AI サービス**: Google Vertex AI (Gemini 2.5 Flash)
- **栄養データベース**: USDA FoodData Central API
- **認証**: Google Cloud サービスアカウント
- **Python バージョン**: 3.9+
- **主要ライブラリ**:
  - `google-cloud-aiplatform` (Vertex AI)
  - `httpx` (非同期 HTTP)
  - `pydantic` (データバリデーション)
  - `pillow` (画像処理)

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 注意事項

**セキュリティ**: API キーやサービスアカウントキーは絶対にリポジトリにコミットしないでください。環境変数として安全に管理してください。
