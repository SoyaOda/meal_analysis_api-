#!/bin/bash
# Cloud Run デプロイスクリプト（Phase 1実装）

set -e

# 設定変数
PROJECT_ID="new-snap-calorie"
SERVICE_NAME="freeform-usda-meal-analysis-api"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Cloud Run デプロイメント開始${NC}"
echo "================================"

# 1. プロジェクト設定
echo -e "${YELLOW}1. Google Cloud プロジェクト設定...${NC}"
gcloud config set project ${PROJECT_ID}

# 2. Docker イメージのビルド
echo -e "${YELLOW}2. Docker イメージをビルド中...${NC}"
docker build \
  -f apps/freeform_usda_meal_analysis_api/Dockerfile.optimized \
  -t ${IMAGE_NAME}:latest \
  -t ${IMAGE_NAME}:$(date +%Y%m%d-%H%M%S) \
  .

# 3. Container Registry へプッシュ
echo -e "${YELLOW}3. イメージをContainer Registryにプッシュ中...${NC}"
docker push ${IMAGE_NAME}:latest

# 4. Cloud Run サービスのデプロイ
echo -e "${YELLOW}4. Cloud Runサービスをデプロイ中...${NC}"

gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --memory 4Gi \
  --cpu 4 \
  --timeout 600 \
  --concurrency 10 \
  --min-instances 1 \
  --max-instances 100 \
  --port 8080 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars "USDA_INDEX_DIR=/app/data/faiss" \
  --set-env-vars "BM25_INDEX_PATH=/app/data/bm25/bm25_index.pkl" \
  --set-env-vars "NUTRITION_DATA_SOURCE=usda_api" \
  --set-env-vars "INGREDIENT_ELASTICSEARCH_INDEX=usda_unified_nutrition_db" \
  --set-env-vars "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}" \
  --set-env-vars "DEEPINFRA_API_KEY=${DEEPINFRA_API_KEY}" \
  --service-account "meal-analysis-api@${PROJECT_ID}.iam.gserviceaccount.com"

# 5. サービスURLの取得
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --format 'value(status.url)')

echo ""
echo -e "${GREEN}✅ デプロイ完了!${NC}"
echo "================================"
echo -e "サービスURL: ${GREEN}${SERVICE_URL}${NC}"
echo ""

# 6. ヘルスチェック
echo -e "${YELLOW}ヘルスチェック実行中...${NC}"
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" ${SERVICE_URL}/health)

if [ $HEALTH_CHECK -eq 200 ]; then
  echo -e "${GREEN}✅ ヘルスチェック成功${NC}"
else
  echo -e "${RED}❌ ヘルスチェック失敗 (HTTP: ${HEALTH_CHECK})${NC}"
  exit 1
fi

# 7. テストリクエスト例
echo ""
echo "================================"
echo "テストコマンド例:"
echo ""
echo "curl -X POST ${SERVICE_URL}/api/v1/meal-analyses/complete \\"
echo "  -F 'image=@test_images/food1.jpg' \\"
echo "  -F 'model_id=openrouter:qwen/qwen3-vl-235b-a22b-thinking'"
echo ""

# 8. モニタリングURL
echo "================================"
echo "モニタリング:"
echo "Cloud Console: https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics?project=${PROJECT_ID}"
echo ""

echo -e "${GREEN}🎉 すべての処理が完了しました!${NC}"