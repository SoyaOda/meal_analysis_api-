# 環境設定とコマンド

## 必要な環境変数
```bash
# Deep Infra API設定（必須）
DEEPINFRA_API_KEY=your_deepinfra_api_key_here
DEEPINFRA_MODEL_ID=Qwen/Qwen2.5-VL-32B-Instruct  # またはgoogle/gemma-3-27b-it
DEEPINFRA_BASE_URL=https://api.deepinfra.com/v1/openai

# Elasticsearch設定
USE_ELASTICSEARCH_SEARCH=true
elasticsearch_url=http://localhost:9200
elasticsearch_index_name=nutrition_fuzzy_search
```

## 基本コマンド

### 開発環境セットアップ
```bash
# 仮想環境アクティベート
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### テスト実行
```bash
# 写真解析システムのテスト
source venv/bin/activate && python test_single_image_analysis.py
```

### API起動
```bash
# ローカルAPI起動
python -m app_v2.main.app

# または
uvicorn app_v2.main.app:app --host 0.0.0.0 --port 8000
```

### Google Cloud デプロイ
```bash
# Google Cloud SDK パス設定
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# プロジェクト設定
gcloud config set project new-snap-calorie

# Cloud Run デプロイ
gcloud builds submit --tag gcr.io/new-snap-calorie/meal-analysis-api:latest .
gcloud run deploy meal-analysis-api \
  --image gcr.io/new-snap-calorie/meal-analysis-api:latest \
  --platform managed --region us-central1 \
  --allow-unauthenticated
```

## システムユーティリティ (macOS)
- `find`, `grep`, `ls`, `cd`: 標準Unix コマンド
- `brew`: パッケージマネージャー
- `git`: バージョン管理