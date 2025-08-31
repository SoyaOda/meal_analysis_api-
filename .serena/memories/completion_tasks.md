# タスク完了時の実行項目

## コード変更後の必須チェック
1. **型チェック**: Pydanticモデルの型定義確認
2. **インポート確認**: 相対インポートの正常性確認
3. **ローカルテスト**: `python -m app_v2.main.app` でサーバー起動確認

## API修正後の検証
```bash
# 1. ローカル起動テスト
python -m app_v2.main.app

# 2. ヘルスチェック
curl "http://localhost:8000/health"

# 3. 基本API動作確認
curl -X POST "http://localhost:8000/api/v1/meal-analyses/complete" -H "Content-Type: multipart/form-data" -F "image=@test_images/food3.jpg"
```

## Cloud Run デプロイ後の検証
```bash
# 1. ビルド・デプロイ
gcloud builds submit --tag gcr.io/new-snap-calorie/meal-analysis-api:v[VERSION]
gcloud run deploy meal-analysis-api --image gcr.io/new-snap-calorie/meal-analysis-api:v[VERSION] --region=us-central1

# 2. 本番ヘルスチェック
curl "https://meal-analysis-api-1077966746907.us-central1.run.app/health"

# 3. 本番API動作確認
curl -X POST "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/complete" -H "Content-Type: multipart/form-data" -F "image=@test_images/food3.jpg"
```

## Elasticsearch関連変更後
```bash
# 1. VM内Elasticsearch稼働確認
gcloud compute ssh elasticsearch-vm --zone=us-central1-a --command="curl -X GET 'localhost:9200/_cluster/health?pretty'"

# 2. インデックス再作成（必要に応じて）
gcloud compute ssh elasticsearch-vm --zone=us-central1-a --command="cd meal_analysis_api_2 && python3 create_elasticsearch_index.py"

# 3. API経由でElasticsearch接続確認
curl "https://meal-analysis-api-1077966746907.us-central1.run.app/health" | grep ElasticsearchNutritionSearchComponent
```

## ドキュメント更新
- README.md の技術仕様更新
- API_DEPLOY_README.md の手順・URL更新
- 新機能追加時のopenapi.yaml更新

## Git管理
```bash
# 作業完了時の標準フロー
git add .
git commit -m "descriptive commit message"
git push origin main
```

## パフォーマンス確認指標
- **API応答時間**: 20秒以内（複雑な画像）
- **ヘルスチェック**: 1秒以内
- **Elasticsearch検索**: 3秒以内
- **メモリ使用量**: Cloud Run 1GB制限内