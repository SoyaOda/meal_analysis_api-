# Meal Analysis API - デプロイメント完全ガイド

## 概要

この API は写真から食事を分析し、栄養情報を計算するシステムです。Deep Infra AI (Qwen2.5-VL-32B-Instruct 等) と Elasticsearch を使用した高精度な食事分析を提供します。

## 現在の動作状況

### ローカル環境

- ✅ **テスト状況**: 100%成功 (10/10 食材マッチング)
- ✅ **AI 分析**: Deep Infra Qwen2.5-VL-32B-Instruct モデル正常動作
- ✅ **栄養計算**: 完全動作 (総カロリー: 413.9 kcal)
- ✅ **処理時間**: 約 11 秒
- ✅ **Model ID 対応**: API で model_id 外部指定可能

### Elasticsearch 設定

- **使用中インデックス**: `mynetdiary_list_support_db`
- **ドキュメント数**: 1,142 件
- **データベースソース**: MyNetDiary 変換済みデータ
- **URL**: `http://localhost:9200`

## 環境設定

### 1. 必須環境変数 (.env)

```bash
# Deep Infra API設定（メイン）
DEEPINFRA_API_KEY=your_deepinfra_api_key_here
DEEPINFRA_MODEL_ID=Qwen/Qwen2.5-VL-32B-Instruct
DEEPINFRA_BASE_URL=https://api.deepinfra.com/v1/openai

# Elasticsearch設定
USE_ELASTICSEARCH_SEARCH=true
elasticsearch_url=http://localhost:9200
elasticsearch_index_name=mynetdiary_list_support_db

# API設定
API_LOG_LEVEL=INFO
FASTAPI_ENV=development
HOST=0.0.0.0
PORT=8000
```

### 2. Elasticsearch の準備

```bash
# Elasticsearchの起動
./elasticsearch-8.10.4/bin/elasticsearch

# インデックス確認
curl -X GET "localhost:9200/_cat/indices?v" | grep mynetdiary

# 使用中のインデックス状態確認
curl -X GET "localhost:9200/mynetdiary_list_support_db/_stats"
```

## ローカル開発・テスト

### 1. 環境準備

```bash
# 仮想環境の有効化
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### 2. テスト実行

```bash
# 単一画像分析テスト（メインテスト）
python test_single_image_analysis.py

# 結果確認（JSON形式で保存される）
cat single_image_analysis_result.json
```

### 3. ローカル API 起動

```bash
# FastAPI サーバー起動
python -m app_v2.main.app

# API ドキュメント確認
# ブラウザで http://localhost:8000/docs
```

### 4. API テスト

```bash
# 基本的なテスト例（デフォルトモデル使用）
curl -X POST "http://localhost:8000/api/v1/meal-analysis/complete" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food1.jpg"

# モデル指定テスト例
curl -X POST "http://localhost:8000/api/v1/meal-analysis/complete" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food1.jpg" \
  -F "model_id=google/gemma-3-27b-it" \
  -F "optional_text=この料理の栄養成分を詳しく分析してください"
```

## Google Cloud Run デプロイメント

### 1. Google Cloud SDK 設定

```bash
# Google Cloud SDK パスの設定
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

# プロジェクト確認
gcloud config get-value project
# 期待値: new-snap-calorie

# 認証確認
gcloud auth list
```

### 2. Docker イメージビルド & プッシュ

```bash
# Container Registry にビルド＆プッシュ
gcloud builds submit --tag gcr.io/new-snap-calorie/meal-analysis-api:latest .
```

### 3. Cloud Run デプロイ

```bash
# Cloud Run サービスデプロイ
gcloud run deploy meal-analysis-api \
  --image gcr.io/new-snap-calorie/meal-analysis-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 900s \
  --concurrency 10 \
  --update-env-vars DEEPINFRA_API_KEY=[実際のAPIキー]
```

### 4. 環境変数の設定（デプロイ後）

```bash
# 重要な環境変数を設定
gcloud run services update meal-analysis-api \
  --region us-central1 \
  --update-env-vars \
    DEEPINFRA_API_KEY=[実際のキー],\
    DEEPINFRA_MODEL_ID=Qwen/Qwen2.5-VL-32B-Instruct,\
    USE_ELASTICSEARCH_SEARCH=false,\
    API_LOG_LEVEL=INFO
```

**注意**: Cloud Run 環境では Elasticsearch が利用できないため、`USE_ELASTICSEARCH_SEARCH=false`に設定し、フォールバック検索を使用します。

## デプロイ確認

### 1. サービス状態確認

```bash
# Cloud Run サービス一覧
gcloud run services list --region=us-central1

# サービス詳細
gcloud run services describe meal-analysis-api --region=us-central1
```

### 2. ログ確認

```bash
# リアルタイムログ
gcloud logs tail --format="value(timestamp, severity, textPayload)"

# 特定時間のログ
gcloud logs read --limit=50 --format="value(timestamp, severity, textPayload)"
```

### 3. API 動作テスト

```bash
# デプロイされたAPIのURLを取得
export API_URL=$(gcloud run services describe meal-analysis-api --region=us-central1 --format="value(status.url)")

# 基本APIテスト
curl -X POST "$API_URL/api/v1/meal-analysis/complete" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food1.jpg"

# モデル指定APIテスト
curl -X POST "$API_URL/api/v1/meal-analysis/complete" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food1.jpg" \
  -F "model_id=google/gemma-3-27b-it"
```

## トラブルシューティング

### よくある問題と解決法

1. **課金無効エラー**

   ```
   ERROR: This API method requires billing to be enabled
   ```

   → Google Cloud コンソールで課金を有効化

2. **Elasticsearch 接続エラー**

   ```
   ConnectionError: [Errno 111] Connection refused
   ```

   → Elasticsearch が起動しているか確認
   → `./elasticsearch-8.10.4/bin/elasticsearch`

3. **Deep Infra API エラー**

   ```
   APIError: APIとの通信に一時的な問題が発生しました
   ```

   → API キーの確認
   → レート制限の確認

4. **メモリ不足エラー**
   → Cloud Run のメモリを 2Gi 以上に設定

### ログ確認コマンド

```bash
# エラーログのみ
gcloud logs read "resource.type=cloud_run_revision" --filter="severity=ERROR" --limit=10

# 特定のサービスのログ
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=meal-analysis-api" --limit=20
```

## パフォーマンス指標

### ローカル環境での性能

- **分析時間**: 約 11 秒
- **食材認識率**: 100% (10/10)
- **メモリ使用量**: 約 500MB

### 推奨 Cloud Run 設定

- **CPU**: 1 vCPU
- **メモリ**: 2Gi
- **タイムアウト**: 900 秒
- **同時実行数**: 10
- **最小インスタンス**: 0

## API 仕様

### エンドポイント

- **POST** `/api/v1/meal-analysis/complete`: 完全な食事画像分析
- **GET** `/health`: ヘルスチェック
- **GET** `/docs`: API ドキュメント

### API パラメーター

#### POST /api/v1/meal-analysis/complete

**パラメーター:**

- `image` (必須): 分析対象の画像ファイル
- `optional_text` (オプション): AI へのテキストプロンプト (デフォルト: "食事の画像です")
- `model_id` (オプション): 使用する Deep Infra Model ID (デフォルト: Qwen/Qwen2.5-VL-32B-Instruct)
- `save_detailed_logs` (オプション): 詳細ログ保存 (デフォルト: true)

**利用可能モデル例:**

- `Qwen/Qwen2.5-VL-32B-Instruct` (デフォルト・推奨)
- `google/gemma-3-27b-it`
- その他 Deep Infra 対応 Vision Language Models

### レスポンス例

```json
{
  "analysis_id": "1bc0b8da",
  "processing_summary": {
    "total_dishes": 2,
    "total_ingredients": 10,
    "nutrition_search_match_rate": "10/10 (100.0%)",
    "total_calories": 413.93,
    "processing_time_seconds": 11.0
  },
  "final_nutrition_result": {
    "total_nutrition": {
      "calories": 413.93,
      "protein": 11.45,
      "fat": 25.87,
      "carbs": 23.73
    }
  }
}
```

## 更新履歴

- **2025-09-12**: Model ID 外部指定機能追加完了
- **2025-09-12**: API 入力パラメーター拡張 (model_id, optional_text)
- **2025-09-12**: Deep Infra Qwen2.5-VL-32B-Instruct 統合完了
- **2025-09-12**: MyNetDiary データベース形式に対応
- **2025-09-12**: Elasticsearch ファジーマッチング最適化
