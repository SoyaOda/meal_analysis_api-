# ベースイメージとして軽量な Python ランタイムを使用
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# Python の依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 環境変数で Uvicorn のポートを受け取る設定（Cloud Run は PORT 環境変数を使用）
ENV PORT=8000

# コンテナ起動時に FastAPI(Uvicorn)を起動
# "-m app_v2.main.app" を指定してモジュールとして実行
CMD ["python", "-m", "app_v2.main.app"]