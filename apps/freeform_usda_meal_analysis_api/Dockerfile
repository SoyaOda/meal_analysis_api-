# Freeform USDA Meal Analysis API - Self-Contained Dockerfile
# 完全自己完結型：shared/への依存なし、データも全て内包

FROM python:3.10-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージのインストール
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーション全体をfreeform_usda_meal_analysis_apiパッケージとしてコピー
# これにより、相対インポートが正しく機能する
COPY . ./freeform_usda_meal_analysis_api

# 環境変数のデフォルト設定
ENV LOG_LEVEL=INFO
ENV USDA_INDEX_DIR=/app/freeform_usda_meal_analysis_api/data/faiss
ENV USDA_METADATA_FILE=/app/freeform_usda_meal_analysis_api/data/faiss/usda_metadata.json
ENV PYTHONPATH=/app

# python -m でモジュールとして起動
# main.pyの__main__ブロックがPORT環境変数を処理してuvicornを起動
CMD ["python", "-m", "freeform_usda_meal_analysis_api.main"]
