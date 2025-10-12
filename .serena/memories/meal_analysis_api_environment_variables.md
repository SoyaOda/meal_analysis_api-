# Meal Analysis API - 環境変数リスト

## 必須環境変数

### 1. PYTHONPATH
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2
```
- プロジェクトルートへのパス

### 2. GOOGLE_CLOUD_PROJECT
```bash
GOOGLE_CLOUD_PROJECT=new-snap-calorie
```
- Google CloudプロジェクトID
- **必須**: 音声認識などのGoogle Cloudサービスで使用

### 3. DEEPINFRA_API_KEY
```bash
DEEPINFRA_API_KEY=your_api_key_here
```
- DeepInfra APIキー
- **必須**: LLM（画像分析、NLU）および音声認識（Whisper）で使用

## オプション環境変数

### 4. PORT
```bash
PORT=8001
```
- デフォルト: 8001
- APIサーバーのポート番号

### 5. WORD_QUERY_API_URL
```bash
WORD_QUERY_API_URL="http://localhost:8002"
```
- デフォルト: `https://word-query-api-1077966746907.us-central1.run.app` (Cloud Run)
- Word Query APIのベースURL
- **ローカル開発時は設定推奨**

### 6. DEEPINFRA_MODEL_ID
```bash
DEEPINFRA_MODEL_ID="google/gemma-3-27b-it"
```
- デフォルト: `google/gemma-3-27b-it`
- 使用するLLMモデル
- サポートされるモデル:
  - `Qwen/Qwen2.5-VL-32B-Instruct` (高速・高精度)
  - `google/gemma-3-27b-it` (多様性重視)
  - `meta-llama/Llama-3.2-90B-Vision-Instruct` (最新)

### 7. DEEPINFRA_BASE_URL
```bash
DEEPINFRA_BASE_URL="https://api.deepinfra.com/v1/openai"
```
- デフォルト: `https://api.deepinfra.com/v1/openai`
- DeepInfra APIのベースURL

### 8. OPENAI_API_KEY
```bash
OPENAI_API_KEY=your_openai_key_here
```
- OpenAI Whisper APIを使用する場合のみ必要
- デフォルトではDeepInfra Whisperを使用

## Google Cloud関連（オプション）

### 9. GOOGLE_APPLICATION_CREDENTIALS
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```
- Google Cloud認証情報ファイルパス
- サービスアカウントキーファイルのパス

### 10. GOOGLE_CLOUD_PROJECT_NUMBER
```bash
GOOGLE_CLOUD_PROJECT_NUMBER=1077966746907
```
- デフォルト: `1077966746907`
- Google Cloudプロジェクト番号

### 11. GOOGLE_CLOUD_REGION
```bash
GOOGLE_CLOUD_REGION=us-central1
```
- デフォルト: `us-central1`
- Google Cloudリージョン

## Elasticsearch設定（オプション）

### 12. elasticsearch_url
```bash
elasticsearch_url="http://localhost:9200"
```
- デフォルト: `http://localhost:9200`

### 13. elasticsearch_index_name
```bash
elasticsearch_index_name="nutrition_fuzzy_search"
```
- デフォルト: `nutrition_fuzzy_search`

### 14. elasticsearch_timeout
```bash
elasticsearch_timeout=30
```
- デフォルト: 30秒

## その他の設定

### 15. API_LOG_LEVEL
```bash
API_LOG_LEVEL=INFO
```
- デフォルト: `INFO`
- ログレベル: DEBUG, INFO, WARNING, ERROR

### 16. FASTAPI_ENV
```bash
FASTAPI_ENV=development
```
- デフォルト: `development`

### 17. RESULTS_DIR
```bash
RESULTS_DIR=analysis_results
```
- デフォルト: `analysis_results`
- 分析結果の保存先ディレクトリ

## 推奨ローカル起動コマンド

```bash
# ローカルWord Query API使用
WORD_QUERY_API_URL="http://localhost:8002" \
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
GOOGLE_CLOUD_PROJECT=new-snap-calorie \
PORT=8001 \
python -m apps.meal_analysis_api.main
```

## Cloud Run本番環境使用コマンド

```bash
# Cloud RunのWord Query API使用
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
GOOGLE_CLOUD_PROJECT=new-snap-calorie \
PORT=8001 \
python -m apps.meal_analysis_api.main
```
