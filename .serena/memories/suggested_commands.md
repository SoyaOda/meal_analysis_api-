# Suggested Commands - 推奨コマンド

## サーバー起動
```bash
# app_v2 サーバーの起動（推奨方法）
python -m app_v2.main.app
```

## Elasticsearch 起動
```bash
# Elasticsearch 8.10.4 の起動
elasticsearch-8.10.4/bin/elasticsearch

# ヘルスチェック
curl -X GET "localhost:9200/_cluster/health?pretty"
```

## テスト実行
```bash
# マルチデータベース栄養検索テスト（最新機能）
python test_multi_db_nutrition_search.py

# ローカル栄養検索テスト
python test_local_nutrition_search_v2.py

# 基本テスト（フェーズ1のみ）
python test_phase1_only.py
```

## Google Cloud 設定
```bash
# Google Cloudにログイン
gcloud auth login

# アプリケーションのデフォルト認証情報を設定
gcloud auth application-default login

# プロジェクトIDを設定
gcloud config set project YOUR_PROJECT_ID

# Vertex AI APIを有効化
gcloud services enable aiplatform.googleapis.com
```

## 仮想環境セットアップ
```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境のアクティベート（macOS/Linux）
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

## API テスト用 curl コマンド
```bash
# 完全分析エンドポイント
curl -X POST "http://localhost:8000/api/v1/meal-analyses/complete" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg"

# ヘルスチェック
curl "http://localhost:8000/health"
```