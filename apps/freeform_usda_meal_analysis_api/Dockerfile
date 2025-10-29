# Freeform USDA Meal Analysis API - Self-Contained Dockerfile
# 完全自己完結型：shared/への依存なし、データも全て内包

FROM python:3.10-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーション全体をコピー（自己完結型）
COPY . .

# 環境変数のデフォルト設定
ENV LOG_LEVEL=INFO
ENV USDA_INDEX_DIR=/app/data/faiss
ENV USDA_METADATA_FILE=/app/data/faiss/usda_metadata.json

# アプリケーション起動: Cloud RunのPORT環境変数を正しく処理
# シェル形式を使用してPORT変数を展開
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8006}
