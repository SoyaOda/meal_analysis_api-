FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システム依存パッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 必要なPythonパッケージをインストール
COPY requirements-barcode.txt .
RUN pip install --no-cache-dir -r requirements-barcode.txt

# アプリケーションコードをコピー
COPY apps/barcode_api /app/apps/barcode_api

# データディレクトリを作成
RUN mkdir -p /app/db/FoodData_Central

# 環境変数
ENV PYTHONPATH=/app
ENV PORT=8003

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# ポート公開
EXPOSE 8003

# 起動コマンド
CMD ["python", "-m", "apps.barcode_api.main"]
