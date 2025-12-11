#!/bin/bash
# Freeform USDA Meal Analysis API - Cloud Run デプロイスクリプト (v4-dev)
#
# 使用方法:
#   cd apps/freeform_usda_meal_analysis_api
#   bash deploy_v4_dev.sh
#
# 注意: deploy_optimized.shと同じ:optimizedタグを使用
#       .envファイルは自動的に読み込まれます

set -e

# リポジトリルートの.envファイルを読み込む
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"

if [ -f "${ENV_FILE}" ]; then
    echo "📂 Loading environment variables from ${ENV_FILE}..."
    set -a  # 自動的にexportする
    source "${ENV_FILE}"
    set +a
    echo "✅ Environment variables loaded"
    echo ""
else
    echo "⚠️  Warning: .env file not found at ${ENV_FILE}"
    echo "   API keys must be set manually"
    echo ""
fi

# gcloud コマンドのパス設定
GCLOUD="/Users/odasoya/google-cloud-sdk/bin/gcloud"

# 設定
PROJECT_ID="new-snap-calorie"
REGION="us-central1"
SERVICE_NAME="freeform-usda-meal-analysis-api-v4-dev"
# 重要: deploy_optimized.shと同じ:optimizedタグを使用（:latestではない）
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:optimized"

echo "=================================="
echo "Freeform USDA Meal Analysis API"
echo "Cloud Run Deployment (v4-dev)"
echo "=================================="
echo ""
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo "Image: ${IMAGE_TAG}"
echo ""

# VLM Provider API Keys チェック
if [ -z "$DEEPINFRA_API_KEY" ]; then
    echo "❌ Error: DEEPINFRA_API_KEY environment variable is not set"
    echo "Please set it before running this script:"
    echo "  source /Users/odasoya/meal_analysis_api_2/.env"
    exit 1
fi

echo "✅ DEEPINFRA_API_KEY is set"

# ALIBABA_API_KEY はオプション
if [ -z "$ALIBABA_API_KEY" ]; then
    echo "⚠️  ALIBABA_API_KEY is not set (optional, only needed for alibaba: provider)"
else
    echo "✅ ALIBABA_API_KEY is set"
fi

# OPENROUTER_API_KEY はオプション
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  OPENROUTER_API_KEY is not set (optional, only needed for openrouter: provider)"
else
    echo "✅ OPENROUTER_API_KEY is set"
fi
echo ""

# アプリケーションディレクトリを基準にリポジトリルートに移動
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "${SCRIPT_DIR}/../.."

# 1. Docker イメージのビルドとプッシュ（Dockerfile.optimizedを使用）
echo "📦 Building and pushing Docker image..."
echo "   Tag: ${IMAGE_TAG}"
echo "   Dockerfile: Dockerfile.optimized"

# Dockerfile.optimizedをルートにコピー
if [ -f "apps/freeform_usda_meal_analysis_api/Dockerfile.optimized" ]; then
    cp apps/freeform_usda_meal_analysis_api/Dockerfile.optimized Dockerfile
else
    echo "❌ Error: Dockerfile.optimized not found"
    exit 1
fi

$GCLOUD builds submit \
  --tag "${IMAGE_TAG}" \
  --timeout=900 \
  --machine-type=E2_HIGHCPU_32 \
  --project="${PROJECT_ID}" \
  .

# 一時的なDockerfileを削除
rm -f Dockerfile

echo "✅ Docker image built and pushed"
echo ""

# 2. Cloud Run デプロイ
echo "🚀 Deploying to Cloud Run (v4-dev)..."
echo "   Image: ${IMAGE_TAG}"

# 環境変数を構築
ENV_VARS="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},LOG_LEVEL=INFO,DEEPINFRA_API_KEY=${DEEPINFRA_API_KEY}"

# ALIBABA_API_KEY が設定されている場合は追加
if [ ! -z "$ALIBABA_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},ALIBABA_API_KEY=${ALIBABA_API_KEY}"
fi

# OPENROUTER_API_KEY が設定されている場合は追加
if [ ! -z "$OPENROUTER_API_KEY" ]; then
    ENV_VARS="${ENV_VARS},OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"
fi

$GCLOUD run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_TAG}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8006 \
  --timeout=300 \
  --memory=2Gi \
  --cpu=1 \
  --concurrency=80 \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="${ENV_VARS}" \
  --project="${PROJECT_ID}"

echo ""
echo "=================================="
echo "✅ Deployment Complete!"
echo "=================================="
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
echo "📝 Test normalized_units:"
echo "curl -s ${SERVICE_URL}/api/v1/metadata/2705385 | jq '.normalized_units'"
echo ""
