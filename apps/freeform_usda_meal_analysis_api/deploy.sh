#!/bin/bash
# Freeform USDA Meal Analysis API - Cloud Run デプロイスクリプト
#
# 使用方法:
#   開発環境: ./deploy.sh                              (デフォルト: development)
#   本番環境: ENVIRONMENT=production ./deploy.sh
#
# 注意: .envファイルは自動的に読み込まれます

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
    echo "   API keys must be set manually"
    echo ""
fi

# gcloud コマンドのパス設定（環境に依存しない）
GCLOUD=$(which gcloud 2>/dev/null || echo "$HOME/google-cloud-sdk/bin/gcloud")
if [ ! -x "$GCLOUD" ]; then
    echo "❌ Error: gcloud not found. Please install Google Cloud SDK."
    exit 1
fi

# ========== 環境設定 ==========
# ENVIRONMENT: "development" (デフォルト) または "production"
ENVIRONMENT=${ENVIRONMENT:-"development"}

# 設定
PROJECT_ID="new-snap-calorie"
REGION="us-central1"

# 環境に応じたサービス名
if [ "$ENVIRONMENT" = "production" ]; then
    SERVICE_NAME=${SERVICE_NAME:-"freeform-usda-meal-analysis-api"}
else
    SERVICE_NAME=${SERVICE_NAME:-"freeform-usda-meal-analysis-api-v4-dev"}
fi

IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:optimized"

# 許可するオリジン（本番環境用、カンマ区切り）
ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-"*"}

echo "============================================"
echo "Freeform USDA Meal Analysis API"
echo "Cloud Run Deployment"
echo "============================================"
echo ""
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "Environment: ${ENVIRONMENT}"
echo "Image: ${IMAGE_TAG}"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "CORS Origins: ${ALLOWED_ORIGINS}"
fi
echo ""

# ========== 既存サービスからAPIキー自動取得 ==========
# 必須APIキーが環境変数に設定されていない場合、既存のCloud Runサービスから取得
fetch_api_key_from_service() {
    local key_name=$1
    local value=$($GCLOUD run services describe "${SERVICE_NAME}" \
        --region="${REGION}" \
        --project="${PROJECT_ID}" \
        --format="yaml(spec.template.spec.containers[0].env)" 2>/dev/null \
        | grep -A1 "name: ${key_name}" | grep "value:" | sed "s/.*value: //")
    echo "$value"
}

echo "🔑 Checking API Keys..."

# DEEPINFRA_API_KEY チェック（必須）
if [ -z "$DEEPINFRA_API_KEY" ]; then
    echo "   DEEPINFRA_API_KEY not in environment, fetching from existing service..."
    DEEPINFRA_API_KEY=$(fetch_api_key_from_service "DEEPINFRA_API_KEY")
    if [ -z "$DEEPINFRA_API_KEY" ]; then
        echo "❌ Error: DEEPINFRA_API_KEY not found in environment or existing service"
        echo "Please set it before running this script:"
        echo "  export DEEPINFRA_API_KEY=your-api-key"
        exit 1
    fi
    echo "   ✅ DEEPINFRA_API_KEY fetched from existing service"
else
    echo "   ✅ DEEPINFRA_API_KEY is set from environment"
fi

# OPENROUTER_API_KEY チェック（必須）
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "   OPENROUTER_API_KEY not in environment, fetching from existing service..."
    OPENROUTER_API_KEY=$(fetch_api_key_from_service "OPENROUTER_API_KEY")
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo "❌ Error: OPENROUTER_API_KEY not found in environment or existing service"
        echo "Please set it before running this script:"
        echo "  export OPENROUTER_API_KEY=your-api-key"
        exit 1
    fi
    echo "   ✅ OPENROUTER_API_KEY fetched from existing service"
else
    echo "   ✅ OPENROUTER_API_KEY is set from environment"
fi

# ALIBABA_API_KEY はオプション
if [ -z "$ALIBABA_API_KEY" ]; then
    echo "   ⚠️  ALIBABA_API_KEY is not set (optional)"
else
    echo "   ✅ ALIBABA_API_KEY is set"
fi
echo ""

# アプリケーションディレクトリを基準にリポジトリルートに移動
cd "${REPO_ROOT}"

# クリーンアップ関数（エラー時も確実に実行）
cleanup() {
    echo "🧹 Cleaning up temporary files..."
    # Dockerfileを復元（バックアップがあれば）
    if [ -f Dockerfile.backup ]; then
        mv Dockerfile.backup Dockerfile
    else
        rm -f Dockerfile
    fi
    # .gcloudignoreを復元
    if [ -f .gcloudignore.backup ]; then
        mv .gcloudignore.backup .gcloudignore
    else
        rm -f .gcloudignore
    fi
}

# スクリプト終了時（成功・失敗問わず）にクリーンアップを実行
trap cleanup EXIT

# 1. Docker イメージのビルドとプッシュ（Dockerfile.optimizedを使用）
echo "📦 Building and pushing Docker image..."
echo "   Tag: ${IMAGE_TAG}"
echo "   Dockerfile: Dockerfile.optimized"

# 既存のDockerfileをバックアップ
if [ -f Dockerfile ]; then
    mv Dockerfile Dockerfile.backup
fi

# Dockerfile.optimizedをルートにコピー
if [ -f "apps/freeform_usda_meal_analysis_api/Dockerfile.optimized" ]; then
    cp apps/freeform_usda_meal_analysis_api/Dockerfile.optimized Dockerfile
else
    echo "❌ Error: Dockerfile.optimized not found"
    exit 1
fi

# バックアップと一時的な.gcloudignoreを作成
if [ -f .gcloudignore ]; then
    mv .gcloudignore .gcloudignore.backup
fi

cat > .gcloudignore << 'GCLOUDIGNORE'
# Freeform USDA Meal Analysis API用の.gcloudignore
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

# 他のアプリケーション（freeform_usda_meal_analysis_api以外）
apps/word_query_api/
apps/meal_analysis_api/
apps/usda_word_query_api/
apps/usda_meal_analysis_api/
apps/barcode_api/

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

$GCLOUD builds submit \
  --tag "${IMAGE_TAG}" \
  --timeout=900 \
  --machine-type=E2_HIGHCPU_32 \
  --project="${PROJECT_ID}" \
  .

echo "✅ Docker image built and pushed"
echo ""

# 2. Cloud Run デプロイ
echo "🚀 Deploying to Cloud Run..."

# 環境変数を構築
ENV_VARS="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"
ENV_VARS="${ENV_VARS},ENVIRONMENT=${ENVIRONMENT}"
# 必須APIキー
ENV_VARS="${ENV_VARS},DEEPINFRA_API_KEY=${DEEPINFRA_API_KEY}"
ENV_VARS="${ENV_VARS},OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"

# ALIBABA_API_KEY が設定されている場合は追加（オプション）
if [ ! -z "$ALIBABA_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},ALIBABA_API_KEY=${ALIBABA_API_KEY}"
fi

# 環境に応じた設定
if [ "$ENVIRONMENT" = "production" ]; then
    echo "🚀 Production Mode: min-instances=2, optimized for performance"
    MIN_INSTANCES=2
    MAX_INSTANCES=10
    MEMORY="4Gi"
    CPU=2
    CONCURRENCY=80
    LOG_LEVEL="WARNING"
    # Worker数: (2 x CPU) + 1 = 5
    WEB_CONCURRENCY=5
    ENV_VARS="${ENV_VARS},LOG_LEVEL=${LOG_LEVEL}"
    ENV_VARS="${ENV_VARS},ALLOWED_ORIGINS=${ALLOWED_ORIGINS}"
    ENV_VARS="${ENV_VARS},WEB_CONCURRENCY=${WEB_CONCURRENCY}"
    # 本番はプリロード有効
    ENV_VARS="${ENV_VARS},PRELOAD_INDEXES_ON_STARTUP=true"
else
    echo "🔧 Development Mode: min-instances=0, cost-optimized"
    MIN_INSTANCES=0
    MAX_INSTANCES=10
    MEMORY="2Gi"
    CPU=1
    CONCURRENCY=80
    LOG_LEVEL="INFO"
    # Worker数: (2 x CPU) + 1 = 3
    WEB_CONCURRENCY=3
    ENV_VARS="${ENV_VARS},LOG_LEVEL=${LOG_LEVEL}"
    ENV_VARS="${ENV_VARS},WEB_CONCURRENCY=${WEB_CONCURRENCY}"
    # 開発もプリロード有効（テスト用）
    ENV_VARS="${ENV_VARS},PRELOAD_INDEXES_ON_STARTUP=true"
fi

# Cloud Run デプロイ
$GCLOUD run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_TAG}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8006 \
  --timeout=300 \
  --memory="${MEMORY}" \
  --cpu="${CPU}" \
  --cpu-boost \
  --execution-environment=gen2 \
  --concurrency="${CONCURRENCY}" \
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
curl -s "${SERVICE_URL}/health" | jq '.' || echo "Health check failed (may need time to start)"
echo ""
