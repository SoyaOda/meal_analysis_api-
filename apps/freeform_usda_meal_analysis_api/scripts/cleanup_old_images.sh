#!/bin/bash
# 古いContainer Registryイメージを削除してストレージコストを削減
# v9デプロイ後、v9が安定してから実行すること

set -e

echo "🗑️  古いContainer Registryイメージを削除します"
echo ""
echo "⚠️  警告: この操作は取り消せません"
echo "   v9が正常に動作していることを確認してから実行してください"
echo ""
read -p "続行しますか？ (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "キャンセルしました"
    exit 1
fi

echo ""
echo "削除対象イメージ:"
echo "  - v1-port-fix"
echo "  - v2-no-expose"
echo "  - v3-module-import"
echo "  - v4-correct-dir"
echo "  - v5-import-fixed"
echo "  - v6-cmd-fix"
echo "  - v7-runpy-entrypoint"
echo "  - latest（古いバージョン）"
echo ""

# 削除実行
REPO="gcr.io/new-snap-calorie/freeform-usda-meal-analysis-api"

echo "🗑️  v1-v7を削除中..."
/Users/odasoya/google-cloud-sdk/bin/gcloud container images delete ${REPO}:v1-port-fix --quiet 2>/dev/null || echo "  v1 already deleted or not found"
/Users/odasoya/google-cloud-sdk/bin/gcloud container images delete ${REPO}:v2-no-expose --quiet 2>/dev/null || echo "  v2 already deleted or not found"
/Users/odasoya/google-cloud-sdk/bin/gcloud container images delete ${REPO}:v3-module-import --quiet 2>/dev/null || echo "  v3 already deleted or not found"
/Users/odasoya/google-cloud-sdk/bin/gcloud container images delete ${REPO}:v4-correct-dir --quiet 2>/dev/null || echo "  v4 already deleted or not found"
/Users/odasoya/google-cloud-sdk/bin/gcloud container images delete ${REPO}:v5-import-fixed --quiet 2>/dev/null || echo "  v5 already deleted or not found"
/Users/odasoya/google-cloud-sdk/bin/gcloud container images delete ${REPO}:v6-cmd-fix --quiet 2>/dev/null || echo "  v6 already deleted or not found"
/Users/odasoya/google-cloud-sdk/bin/gcloud container images delete ${REPO}:v7-runpy-entrypoint --quiet 2>/dev/null || echo "  v7 already deleted or not found"

echo ""
echo "🗑️  latestタグを削除中..."
/Users/odasoya/google-cloud-sdk/bin/gcloud container images delete ${REPO}:latest --quiet 2>/dev/null || echo "  latest already deleted or not found"

echo ""
echo "🗑️  タグなしイメージを削除中..."
/Users/odasoya/google-cloud-sdk/bin/gcloud container images list-tags ${REPO} --filter='-tags:*' --format="get(digest)" --limit=999 | \
while read digest; do
  if [ ! -z "$digest" ]; then
    /Users/odasoya/google-cloud-sdk/bin/gcloud container images delete "${REPO}@sha256:${digest}" --quiet 2>/dev/null || echo "  Failed to delete ${digest}"
  fi
done

echo ""
echo "✅ 削除完了"
echo ""
echo "残っているイメージ:"
/Users/odasoya/google-cloud-sdk/bin/gcloud container images list-tags ${REPO} --format="table(tags,timestamp.date())"

echo ""
echo "💰 予想削減額: 約$0.10/月"
