#!/bin/bash
# Barcode API - Cloud Run デプロイスクリプト
#
# FDCデータベース(約3GB)をCloud Storage経由で配信
# 
# 事前準備:
#   1. FDCデータベースをGCSにアップロード:
#      gsutil cp db/FoodData_Central/fdc_barcode.db gs://new-snap-calorie-data/fdc/fdc_barcode.db
#   2. このスクリプトを実行

set -e

# リポジトリルートの.envファイルを読み込む
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"

if [ -f "${ENV_FILE}" ]; then
    echo "📂 Loading environment variables from ${ENV_FILE}..."
    set -a
    source "${ENV_FILE}"
    set +a
    echo "✅ Environment variables loaded"
    echo ""
else
    echo "⚠️  Warning: .env file not found at ${ENV_FILE}"
    echo ""
fi

# gcloud コマンドのパス設定
GCLOUD="/opt/homebrew/bin/gcloud"

# 設定
PROJECT_ID="new-snap-calorie"
REGION="us-central1"
SERVICE_NAME=${SERVICE_NAME:-"barcode-api"}
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

# GCSバケット設定
GCS_BUCKET="new-snap-calorie-data"
GCS_DB_PATH="gs://${GCS_BUCKET}/fdc/fdc_barcode.db"

# デプロイモード選択
DEPLOY_MODE=${DEPLOY_MODE:-"cost"}  # "cost" or "performance"

echo "============================================"
echo "Barcode API"
echo "Cloud Run Deployment"
echo "============================================"
echo ""
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "Deploy Mode: ${DEPLOY_MODE}"
echo "Database: ${GCS_DB_PATH}"
echo ""

# GCSにデータベースがあるか確認
echo "📦 Checking FDC database in GCS..."
if gsutil ls "${GCS_DB_PATH}" > /dev/null 2>&1; then
    echo "✅ FDC database found in GCS"
else
    echo "❌ FDC database not found in GCS"
    echo ""
    echo "Please upload the database first:"
    echo "  gsutil cp db/FoodData_Central/fdc_barcode.db ${GCS_DB_PATH}"
    exit 1
fi
echo ""

# リポジトリルートに移動
cd "${REPO_ROOT}"

# 1. Dockerfileを準備
echo "📦 Preparing Dockerfile..."
cp apps/barcode_api/Dockerfile Dockerfile.barcode

# バックアップと一時的な.gcloudignoreを作成
if [ -f .gcloudignore ]; then
    mv .gcloudignore .gcloudignore.backup
fi

cat > .gcloudignore << 'GCLOUDIGNORE'
# Barcode API用の.gcloudignore
.git
.gitignore

# Python
__pycache__/
*.pyc

# 不要な大規模ディレクトリ
web_scraping/
db/
core_food_processing/
usda_database/
raw_nutrition_data/
venv/
elasticsearch-8.10.4/
usda_data_processing/
MyNetDiary_json_builder/
web_scraping_2/
nutrition_db_experiment/
analysis_results/
app_backup/

# 他のアプリケーション（barcode_api以外）
apps/word_query_api/
apps/meal_analysis_api/
apps/usda_word_query_api/
apps/usda_meal_analysis_api/
apps/freeform_usda_meal_analysis_api/

# テストファイル
test_images/
test-audio/
test_scripts/
test_barcodes/

# ログ
*.log

# 環境変数ファイル
.env
.env.*
GCLOUDIGNORE

# 起動スクリプトを含むDockerfileに更新
cat > Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システム依存パッケージをインストール（Google Cloud SDK含む）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates \
    && curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update && apt-get install -y google-cloud-cli \
    && rm -rf /var/lib/apt/lists/*

# 必要なPythonパッケージをインストール
COPY requirements-barcode.txt .
RUN pip install --no-cache-dir -r requirements-barcode.txt

# アプリケーションコードをコピー
COPY apps/barcode_api /app/apps/barcode_api

# データディレクトリを作成
RUN mkdir -p /app/db/FoodData_Central

# 起動スクリプトをコピー
COPY apps/barcode_api/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 環境変数
ENV PYTHONPATH=/app
ENV PORT=8003

# ポート公開
EXPOSE 8003

# 起動コマンド
ENTRYPOINT ["/app/entrypoint.sh"]
DOCKERFILE

# 2. Docker イメージのビルドとプッシュ
echo "📦 Building Docker image..."

$GCLOUD builds submit \
  --tag "${IMAGE_TAG}" \
  --timeout=1200 \
  --machine-type=E2_HIGHCPU_8 \
  --project="${PROJECT_ID}" \
  .

# 一時ファイルを削除
rm -f Dockerfile Dockerfile.barcode

# .gcloudignoreを復元
rm -f .gcloudignore
if [ -f .gcloudignore.backup ]; then
    mv .gcloudignore.backup .gcloudignore
fi

echo "✅ Docker image built and pushed"
echo ""

# 3. Cloud Run デプロイ
echo "🚀 Deploying to Cloud Run..."

# 環境変数を構築
ENV_VARS="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},LOG_LEVEL=INFO"
ENV_VARS="${ENV_VARS},GCS_DB_PATH=${GCS_DB_PATH}"

# デプロイモードに応じた設定
if [ "$DEPLOY_MODE" = "performance" ]; then
    echo "⚡ Performance Mode: min-instances=1 for zero cold starts"
    MIN_INSTANCES=1
    MAX_INSTANCES=10
    MEMORY="4Gi"  # DBダウンロード + SQLite用に多めに
    CPU=2
else
    echo "💰 Cost Mode: min-instances=0"
    MIN_INSTANCES=0
    MAX_INSTANCES=10
    MEMORY="4Gi"
    CPU=2
fi

# Cloud Run デプロイ
$GCLOUD run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_TAG}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8003 \
  --timeout=300 \
  --memory="${MEMORY}" \
  --cpu="${CPU}" \
  --cpu-boost \
  --execution-environment=gen2 \
  --concurrency=100 \
  --max-instances="${MAX_INSTANCES}" \
  --min-instances="${MIN_INSTANCES}" \
  --set-env-vars="${ENV_VARS}" \
  --project="${PROJECT_ID}"

echo ""
echo "============================================"
echo "✅ Deployment Complete!"
echo "============================================"
echo ""

# サービスURLを取得
SERVICE_URL=$($GCLOUD run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --platform managed \
  --format="value(status.url)" \
  --project="${PROJECT_ID}")

echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📚 API Docs: ${SERVICE_URL}/docs"
echo "🏥 Health Check: ${SERVICE_URL}/health"
echo ""

# ヘルスチェック
echo "📊 Testing deployment..."
echo ""
echo "Health check:"
curl -s "${SERVICE_URL}/health" | jq '.' || echo "Health check failed (may need time to start)"
echo ""
