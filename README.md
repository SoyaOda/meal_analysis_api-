# Meal Analysis API

食事画像から料理・食材を分析し、USDA FoodData Central データベースと連携して正確な栄養情報を提供する REST API です。

## 特徴

- 📷 **画像分析**: Google Gemini AI を使用して食事画像から料理と食材を識別
- 🥗 **フェーズ 1 分析**: 画像から料理名、種類、量、材料を推定
- 🔬 **フェーズ 2 精緻化**: USDA FoodData Central データベースと連携して正確な栄養情報を付与
- 🌍 **英語対応**: すべての出力は英語で統一
- 📊 **栄養情報**: 各食材の 100g あたりの主要栄養素（カロリー、タンパク質、脂質、炭水化物など）を提供

## 必要条件

- Python 3.9 以上
- Google Cloud Platform (GCP) アカウント
- 課金が有効になっている GCP プロジェクト
- USDA FoodData Central API キー

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/SoyaOda/meal_analysis_api-.git
cd meal_analysis_api
```

### 2. Python 仮想環境の作成

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境のアクティベート
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. Google Cloud 認証の設定

#### 方法 1: gcloud 認証（開発環境推奨）

```bash
# Google Cloud SDKのインストール（未インストールの場合）
# https://cloud.google.com/sdk/docs/install

# Google Cloudにログイン
gcloud auth login

# アプリケーションのデフォルト認証情報を設定
gcloud auth application-default login

# プロジェクトIDを設定
gcloud config set project YOUR_PROJECT_ID
```

#### 方法 2: サービスアカウント（本番環境推奨）

1. GCP コンソールでサービスアカウントを作成
2. 必要な権限を付与：
   - Vertex AI User
   - Storage Object Viewer（必要に応じて）
3. キーファイル（`service-account-key.json`）をダウンロード
4. プロジェクトルートに配置

### 5. Vertex AI API の有効化

```bash
# Vertex AI APIを有効化
gcloud services enable aiplatform.googleapis.com
```

### 6. USDA API キーの取得

1. [USDA FoodData Central API](https://fdc.nal.usda.gov/api-key-signup.html)でアカウントを作成
2. API キーを取得

### 7. 環境変数の設定（.env ファイル）

プロジェクトルートに`.env`ファイルを作成：

```bash
# Vertex AI設定
GEMINI_PROJECT_ID=your-gcp-project-id
GEMINI_LOCATION=us-central1
GEMINI_MODEL_NAME=gemini-2.5-flash-preview-05-20

# USDA API設定
USDA_API_KEY=your-usda-api-key
USDA_API_BASE_URL=https://api.nal.usda.gov/fdc/v1
USDA_API_TIMEOUT=10.0
USDA_SEARCH_CANDIDATES_LIMIT=5
USDA_KEY_NUTRIENT_NUMBERS_STR=208,203,204,205,291,269,307

# キャッシュ設定
CACHE_TYPE=simple
USDA_CACHE_TTL_SECONDS=3600

# API設定
API_LOG_LEVEL=INFO
FASTAPI_ENV=development

# サーバー設定
HOST=0.0.0.0
PORT=8000
```

## 実行方法

### API サーバーの起動

```bash
# サービスアカウントを使用する場合
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# FastAPIサーバーを起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### フェーズ 2 テストの実行（test_english_phase2.py）

1. 別のターミナルウィンドウを開く
2. 仮想環境をアクティベート
3. テストスクリプトを実行：

```bash
# 仮想環境のアクティベート
source venv/bin/activate  # macOS/Linux

# テストを実行
python test_english_phase2.py
```

このスクリプトは以下を実行します：

- フェーズ 1: 画像から料理と食材を英語で識別
- フェーズ 2: USDA データベースと連携して栄養情報を付与

## API エンドポイント

### フェーズ 1: 初期画像分析

```
POST /api/v1/meal-analyses
```

- 画像をアップロードして料理と食材を分析

### フェーズ 2: USDA 精緻化

```
POST /api/v1/meal-analyses/refine
```

- フェーズ 1 の結果と USDA データベースを使用して栄養情報を精緻化

### ドキュメント

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI 仕様: http://localhost:8000/openapi.json

## プロジェクト構造

```
meal_analysis_api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── meal_analyses.py      # フェーズ1エンドポイント
│   │       │   └── meal_analyses_refine.py # フェーズ2エンドポイント
│   │       └── schemas/
│   │           └── meal.py               # Pydanticモデル
│   ├── core/
│   │   └── config.py                     # 設定管理
│   ├── services/
│   │   ├── gemini_service.py             # Gemini AI連携
│   │   └── usda_service.py               # USDA API連携
│   └── main.py                           # FastAPIアプリケーション
├── test_images/                          # テスト用画像
├── tests/                                # ユニットテスト
├── .env                                  # 環境変数
├── requirements.txt                      # Python依存関係
└── openapi.yaml                          # OpenAPI仕様書
```

## トラブルシューティング

### 認証エラーが発生する場合

```bash
# 現在の認証状態を確認
gcloud auth list

# 現在のプロジェクト設定を確認
gcloud config list

# 必要に応じて再度認証を実行
gcloud auth application-default login
```

### Vertex AI API が有効になっていない場合

```bash
# 有効なAPIを確認
gcloud services list --enabled | grep aiplatform

# 有効になっていない場合は有効化
gcloud services enable aiplatform.googleapis.com
```

### USDA API レートリミット

- 1 時間あたり 1,000 リクエストの制限があります
- キャッシュ機能により、同じ食材の検索結果は再利用されます

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まず issue を開いて変更内容を説明してください。

## ライセンス

[MIT](https://choosealicense.com/licenses/mit/)
