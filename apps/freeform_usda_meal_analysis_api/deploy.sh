#!/bin/bash
# Freeform USDA Meal Analysis API - Cloud Run デプロイスクリプト

set -e

# gcloud コマンドのパス設定
GCLOUD="/Users/odasoya/google-cloud-sdk/bin/gcloud"

# 設定
PROJECT_ID="new-snap-calorie"
REGION="us-central1"
SERVICE_NAME="freeform-usda-meal-analysis-api"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "=================================="
echo "Freeform USDA Meal Analysis API"
echo "Cloud Run Deployment"
echo "=================================="
echo ""
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Service: ${SERVICE_NAME}"
echo ""

# VLM Provider API Keys チェック
if [ -z "$DEEPINFRA_API_KEY" ]; then
    echo "❌ Error: DEEPINFRA_API_KEY environment variable is not set"
    echo "Please set it before running this script:"
    echo "  export DEEPINFRA_API_KEY=your-api-key"
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

# アプリケーションディレクトリに移動（自己完結型）
cd "$(dirname "$0")"

# 1. Docker イメージのビルドとプッシュ
echo "📦 Building and pushing Docker image..."
$GCLOUD builds submit \
  --tag "${IMAGE_TAG}" \
  --timeout=900 \
  --project="${PROJECT_ID}" \
  .

echo "✅ Docker image built and pushed"
echo ""

# 2. Cloud Run デプロイ
echo "🚀 Deploying to Cloud Run..."

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
  --timeout=600 \
  --memory=2Gi \
  --cpu=1 \
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
