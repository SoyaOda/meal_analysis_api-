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

# ポート8006を公開
EXPOSE 8006

# 環境変数のデフォルト設定
ENV PORT=8006
ENV LOG_LEVEL=INFO

# アプリケーション起動（PYTHONPATHは不要）
CMD ["python", "-m", "main"]
