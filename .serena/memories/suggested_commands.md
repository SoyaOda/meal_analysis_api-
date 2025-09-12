# 推奨コマンド一覧

## 日常開発コマンド

### 1. 環境準備
```bash
source venv/bin/activate
```

### 2. テスト実行
```bash
# 写真解析システムのテスト（主要テスト）
python test_single_image_analysis.py

# その他のテスト
python test_multi_image_analysis.py
python test_local_nutrition_search_v2.py
```

### 3. API開発・テスト
```bash
# FastAPI起動
python -m app_v2.main.app

# API ドキュメント確認
# ブラウザで http://localhost:8000/docs
```

### 4. デプロイメント
```bash
# Google Cloud SDK パス設定
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# Cloud Run デプロイ（完全版）
gcloud builds submit --tag gcr.io/new-snap-calorie/meal-analysis-api:latest .
gcloud run deploy meal-analysis-api \
  --image gcr.io/new-snap-calorie/meal-analysis-api:latest \
  --platform managed --region us-central1 \
  --allow-unauthenticated \
  --update-env-vars DEEPINFRA_API_KEY=実際のキー
```

### 5. デバッグ・確認
```bash
# 現在のCloud Runサービス確認
gcloud run services list --region=us-central1

# ログ確認
gcloud logs tail --format="value(timestamp, severity, textPayload)"
```

## タスク完了後の確認項目
1. テスト実行: `python test_single_image_analysis.py`
2. API動作確認: FastAPI起動後 `/docs` で動作確認
3. 環境変数チェック: `.env` ファイルの設定確認