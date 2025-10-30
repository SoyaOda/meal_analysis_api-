# Freeform USDA Meal Analysis API - Local Data Included
# FAISSデータをイメージに含める（ローカル環境と同じ動作）

FROM python:3.10-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージのインストール
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコード全体をコピー（data/を含む）
COPY . ./freeform_usda_meal_analysis_api

# 環境変数のデフォルト設定
ENV LOG_LEVEL=INFO
ENV USDA_INDEX_DIR=/app/freeform_usda_meal_analysis_api/data/faiss
ENV USDA_METADATA_FILE=/app/freeform_usda_meal_analysis_api/data/faiss/usda_metadata.json
ENV PYTHONPATH=/app

# python -m でモジュールとして起動
CMD ["python", "-m", "freeform_usda_meal_analysis_api.main"]
