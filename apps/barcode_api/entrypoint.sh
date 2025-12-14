#!/bin/bash
# Barcode API エントリーポイント
#
# GCSからFDCデータベースをダウンロードしてからアプリを起動

set -e

DB_PATH="/app/db/FoodData_Central/fdc_barcode.db"
GCS_DB_PATH="${GCS_DB_PATH:-gs://new-snap-calorie-data/fdc/fdc_barcode.db}"

echo "🚀 Barcode API Starting..."
echo ""

# データベースが既に存在するか確認
if [ -f "${DB_PATH}" ]; then
    echo "✅ FDC database already exists locally"
    DB_SIZE=$(ls -lh "${DB_PATH}" | awk '{print $5}')
    echo "   Size: ${DB_SIZE}"
else
    echo "📥 Downloading FDC database from GCS..."
    echo "   Source: ${GCS_DB_PATH}"
    echo "   Destination: ${DB_PATH}"
    echo ""
    
    # GCSからダウンロード（Cloud Run環境ではサービスアカウントで認証済み）
    gsutil -q cp "${GCS_DB_PATH}" "${DB_PATH}"
    
    if [ -f "${DB_PATH}" ]; then
        DB_SIZE=$(ls -lh "${DB_PATH}" | awk '{print $5}')
        echo "✅ Download complete"
        echo "   Size: ${DB_SIZE}"
    else
        echo "❌ Failed to download database"
        exit 1
    fi
fi

echo ""
echo "🌐 Starting Barcode API on port ${PORT:-8003}..."
echo ""

# Pythonアプリケーションを起動
exec python -m apps.barcode_api.main
