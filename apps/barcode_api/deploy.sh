#!/bin/bash
# Barcode API - Cloud Run デプロイスクリプト
#
# 使用方法:
#   開発環境: ./deploy.sh                              (デフォルト: development)
#   本番環境: ENVIRONMENT=production ./deploy.sh
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

# gcloud コマンドのパス設定（環境に依存しない）
GCLOUD=$(which gcloud)

# ========== 環境設定 ==========
# ENVIRONMENT: "development" (デフォルト) または "production"
ENVIRONMENT=${ENVIRONMENT:-"development"}

# 設定
PROJECT_ID="new-snap-calorie"
REGION="us-central1"

# 環境に応じたサービス名
if [ "$ENVIRONMENT" = "production" ]; then
    SERVICE_NAME=${SERVICE_NAME:-"barcode-api"}
else
    SERVICE_NAME=${SERVICE_NAME:-"barcode-api-dev"}
fi

IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

# GCSバケット設定
GCS_BUCKET="new-snap-calorie-data"
GCS_DB_PATH="gs://${GCS_BUCKET}/fdc/fdc_barcode.db"

# 許可するオリジン（本番環境用、カンマ区切り）
ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-"*"}

echo "============================================"
echo "Barcode API"
echo "Cloud Run Deployment"
echo "============================================"
echo ""
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "Environment: ${ENVIRONMENT}"
echo "Database: ${GCS_DB_PATH}"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "CORS Origins: ${ALLOWED_ORIGINS}"
fi
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

# クリーンアップ関数（エラー時も確実に実行）
cleanup() {
    echo "🧹 Cleaning up temporary files..."
    rm -f Dockerfile Dockerfile.barcode
    rm -f .gcloudignore
    if [ -f .gcloudignore.backup ]; then
        mv .gcloudignore.backup .gcloudignore
    fi
}

# スクリプト終了時（成功・失敗問わず）にクリーンアップを実行
trap cleanup EXIT

# 1. Dockerfile.optimizedを準備
echo "📦 Preparing Dockerfile.optimized..."

# Dockerfile.optimizedをルートにコピー
if [ -f "apps/barcode_api/Dockerfile.optimized" ]; then
    cp apps/barcode_api/Dockerfile.optimized Dockerfile
else
    echo "❌ Error: Dockerfile.optimized not found"
    exit 1
fi

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

# 2. Docker イメージのビルドとプッシュ
echo "📦 Building Docker image..."

$GCLOUD builds submit \
  --tag "${IMAGE_TAG}" \
  --timeout=1200 \
  --machine-type=E2_HIGHCPU_8 \
  --project="${PROJECT_ID}" \
  .

echo "✅ Docker image built and pushed"
echo ""

# 3. Cloud Run デプロイ
echo "🚀 Deploying to Cloud Run..."

# 環境変数を構築
ENV_VARS="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},ENVIRONMENT=${ENVIRONMENT}"
ENV_VARS="${ENV_VARS},GCS_DB_PATH=${GCS_DB_PATH}"

# 環境に応じた設定
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🚀 Production Mode: min-instances=1, optimized for performance"
    MIN_INSTANCES=1
    MAX_INSTANCES=3
    MEMORY="4Gi"
    CPU=2
    LOG_LEVEL="WARNING"
    ENV_VARS="${ENV_VARS},LOG_LEVEL=${LOG_LEVEL}"
    ENV_VARS="${ENV_VARS},ALLOWED_ORIGINS=${ALLOWED_ORIGINS}"
else
    echo "🔧 Development Mode: min-instances=0, cost-optimized"
    MIN_INSTANCES=0
    MAX_INSTANCES=5
    MEMORY="4Gi"
    CPU=2
    LOG_LEVEL="INFO"
    ENV_VARS="${ENV_VARS},LOG_LEVEL=${LOG_LEVEL}"
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
  --concurrency=80 \
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
