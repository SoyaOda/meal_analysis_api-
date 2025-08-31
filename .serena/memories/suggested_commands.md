# 推奨コマンド一覧

## 開発環境セットアップ
```bash
# Python仮想環境作成・アクティベート
python -m venv venv
source venv/bin/activate  # macOS

# 依存関係インストール
pip install -r requirements.txt

# Google Cloud認証設定
gcloud auth login
gcloud auth application-default login
gcloud config set project new-snap-calorie
```

## ローカル開発・テスト
```bash
# APIサーバー起動（ローカル）
python -m app_v2.main.app

# 単体テスト実行
python test_multi_db_nutrition_search.py
python test_local_nutrition_search_v2.py
python test_niche_food_mappings.py

# Elasticsearchテスト
python test_elasticsearch_connection.py
python test_advanced_elasticsearch_search.py
```

## Cloud Run デプロイ
```bash
# Dockerビルド・プッシュ
gcloud builds submit --tag gcr.io/new-snap-calorie/meal-analysis-api:v9

# Cloud Runデプロイ
gcloud run deploy meal-analysis-api --image gcr.io/new-snap-calorie/meal-analysis-api:v9 --region=us-central1 --allow-unauthenticated

# 環境変数更新
gcloud run services update meal-analysis-api --region=us-central1 --set-env-vars="GEMINI_MODEL_NAME=gemini-2.5-flash,ELASTIC_HOST=http://10.128.0.2:9200,ELASTIC_INDEX=mynetdiary_nutrition_db"
```

## Elasticsearch VM 管理
```bash
# VM接続
gcloud compute ssh elasticsearch-vm --zone=us-central1-a

# インデックス作成
gcloud compute ssh elasticsearch-vm --zone=us-central1-a --command="cd meal_analysis_api_2 && python3 create_elasticsearch_index.py"

# Elasticsearchステータス確認
gcloud compute ssh elasticsearch-vm --zone=us-central1-a --command="curl -X GET 'localhost:9200/_cluster/health?pretty'"
```

## API テスト
```bash
# ヘルスチェック
curl "https://meal-analysis-api-1077966746907.us-central1.run.app/health"

# 食事分析API実行
curl -X POST "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/complete" -H "Content-Type: multipart/form-data" -F "image=@test_images/food3.jpg"
```

## Git操作
```bash
# 変更確認・コミット
git status
git add .
git commit -m "commit message"
git push origin main
```

## システム管理 (macOS)
```bash
# ファイル検索
find . -name "*.py" -type f
grep -r "pattern" .
ls -la

# プロセス管理
ps aux | grep python
lsof -i :8000

# 容量確認
du -sh .
df -h
```