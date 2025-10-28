# Freeform USDA Meal Analysis API - Dockerfile (Full Index Only)
FROM python:3.10-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージのインストール
COPY apps/freeform_usda_meal_analysis_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY apps/freeform_usda_meal_analysis_api /app/apps/freeform_usda_meal_analysis_api
COPY shared /app/shared
COPY MyNetDiary_json_builder/output /app/MyNetDiary_json_builder/output

# FAISSインデックスとメタデータをコピー（Fullインデックスのみ）
COPY test_scripts/query_system/data/usda_index_full.faiss /app/test_scripts/query_system/data/usda_index_full.faiss
COPY test_scripts/query_system/data/usda_metadata.json /app/test_scripts/query_system/data/usda_metadata.json

# query_systemソースコード（embedding, rerankerモデル用）
COPY test_scripts/query_system/src /app/test_scripts/query_system/src

# ポート8006を公開
EXPOSE 8006

# 環境変数のデフォルト設定
ENV PORT=8006
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# アプリケーション起動
CMD ["python", "-m", "apps.freeform_usda_meal_analysis_api.main"]
