# Vertex AI 移行セットアップガイド

このガイドでは、食事分析 API を Google 開発者向け API から Vertex AI に移行する手順を説明します。

## 前提条件

1. Google Cloud Platform (GCP) アカウント
2. 課金が有効になっている GCP プロジェクト
3. Google Cloud SDK (gcloud) のインストール

## セットアップ手順

### 1. Google Cloud SDK のインストール

まだインストールしていない場合は、以下からインストールしてください：
https://cloud.google.com/sdk/docs/install

### 2. Google Cloud 認証の設定

#### 方法 1: gcloud 認証（開発環境推奨）

```bash
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
   - Storage Object Viewer (必要に応じて)
3. キーファイルをダウンロード
4. 環境変数を設定：

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your-service-account-key.json"
```

### 3. Vertex AI API の有効化

```bash
# Vertex AI APIを有効化
gcloud services enable aiplatform.googleapis.com
```

### 4. 環境変数の設定

`.env`ファイルを更新：

```bash
# Google Cloud/Vertex AI Configuration
GEMINI_PROJECT_ID=your-actual-project-id
GEMINI_LOCATION=us-central1
GEMINI_MODEL_NAME=gemini-1.5-flash

# API Configuration
API_LOG_LEVEL=INFO
FASTAPI_ENV=development

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### 5. 依存関係の更新

```bash
# 仮想環境をアクティベート
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows

# 新しい依存関係をインストール
pip install -r requirements.txt
```

### 6. API の起動とテスト

```bash
# APIサーバーを起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 別のターミナルでテストを実行
python test_api.py
```

## トラブルシューティング

### 認証エラーが発生する場合

1. `gcloud auth list`で現在の認証状態を確認
2. `gcloud config list`で現在のプロジェクト設定を確認
3. 必要に応じて再度認証を実行

### Vertex AI API が有効になっていない場合

```bash
gcloud services list --enabled | grep aiplatform
```

有効になっていない場合は、上記の手順 3 を実行してください。

### クォータエラーが発生する場合

GCP コンソールで Vertex AI のクォータを確認し、必要に応じて増加リクエストを送信してください。

## 本番環境へのデプロイ

Google Cloud Run へのデプロイについては、別途デプロイメントガイドを参照してください。
