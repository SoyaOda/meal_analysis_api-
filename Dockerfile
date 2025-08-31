FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# NLTK のデータをダウンロード（lemmatization に必要）
RUN python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4'); nltk.download('punkt')"

COPY . .

ENV PORT=8000

CMD ["python", "-m", "app_v2.main.app"]