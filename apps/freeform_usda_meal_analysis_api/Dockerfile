# Freeform USDA Meal Analysis API - Cloud Storage Optimized Dockerfile
# データはCloud Storageから起動時にダウンロード（コスト・速度最適化）

FROM python:3.10-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージのインストール
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのみコピー（data/は除外）
# .gcloudignoreでdata/を除外するため、ここでは全体をコピー
COPY . ./freeform_usda_meal_analysis_api

# 環境変数のデフォルト設定
ENV LOG_LEVEL=INFO
ENV USDA_INDEX_DIR=/tmp/faiss
ENV USDA_METADATA_FILE=/tmp/faiss/usda_metadata.json
ENV PYTHONPATH=/app

# Cloud Storageから起動時にダウンロードするため、/tmpを使用可能に
# Cloud Runは/tmpを書き込み可能なボリュームとして提供

# python -m でモジュールとして起動
# main.pyの起動時に Cloud Storage から FAISS データをダウンロード
CMD ["python", "-m", "freeform_usda_meal_analysis_api.main"]
