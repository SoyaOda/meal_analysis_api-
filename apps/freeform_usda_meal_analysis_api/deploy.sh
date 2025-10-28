#!/bin/bash
# Freeform USDA Meal Analysis API - Cloud Run デプロイスクリプト

set -e

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

# DEEPINFRA_API_KEY 環境変数チェック
if [ -z "$DEEPINFRA_API_KEY" ]; then
    echo "❌ Error: DEEPINFRA_API_KEY environment variable is not set"
    echo "Please set it before running this script:"
    echo "  export DEEPINFRA_API_KEY=your-api-key"
    exit 1
fi

echo "✅ DEEPINFRA_API_KEY is set"
echo ""

# プロジェクトルートに移動
cd "$(dirname "$0")/../.."

# 1. Docker イメージのビルドとプッシュ
echo "📦 Building and pushing Docker image..."
gcloud builds submit \
  --tag "${IMAGE_TAG}" \
  --timeout=900 \
  --project="${PROJECT_ID}" \
  -f apps/freeform_usda_meal_analysis_api/Dockerfile \
  .

echo "✅ Docker image built and pushed"
echo ""

# 2. Cloud Run デプロイ
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_TAG}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8006 \
  --timeout=600 \
  --memory=2Gi \
  --cpu=1 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars="LOG_LEVEL=INFO" \
  --set-env-vars="DEEPINFRA_API_KEY=${DEEPINFRA_API_KEY}" \
  --project="${PROJECT_ID}"

echo ""
echo "=================================="
echo "✅ Deployment Complete!"
echo "=================================="
echo ""

# サービスURLを取得
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region="${REGION}" \
  --platform managed \
  --format="value(status.url)" \
  --project="${PROJECT_ID}")

echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📚 API Docs: ${SERVICE_URL}/docs"
echo "🏥 Health Check: ${SERVICE_URL}/health"
echo ""
