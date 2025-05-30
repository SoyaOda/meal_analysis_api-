# 食事分析 API (Meal Analysis API) v2.1

## 概要

この API は、**Google Gemini AI** と **USDA データベース**を使用した高度な食事画像分析システムです。**動的栄養計算機能**により、料理の特性に応じて最適な栄養計算戦略を自動選択し、正確な栄養価情報を提供します。

## 🌟 主な機能

### **新機能: 動的栄養計算システム v2.0**

- **🧠 AI 駆動の計算戦略決定**: Gemini AI が各料理に対して最適な栄養計算方法を自動選択
  - `dish_level`: シンプルな食品（緑茶、果物など）は料理全体の USDA ID で計算
  - `ingredient_level`: 複雑な料理（サラダ、炒め物など）は食材ごとに詳細計算して集計
- **🎯 高精度栄養計算**: 食材重量 × 100g あたり栄養価で正確な実栄養価を算出
- **📊 3 層集計システム**: 食材 → 料理 → 食事全体の自動栄養集計
- **⚡ リアルタイム USDA 統合**: 20,000+ 食品データベースとの即座な照合

### **コア機能**

- **フェーズ 1**: Gemini AI による食事画像の分析（料理識別、食材抽出、重量推定）
- **フェーズ 2**: USDA データベースによる栄養成分の精緻化と動的計算
- **複数料理対応**: 1 枚の画像で複数の料理を同時分析
- **英語・日本語対応**: 多言語での食材・料理認識
- **OpenAPI 3.0 準拠**: 完全な API 文書化とタイプ安全性

## 🏗 プロジェクト構造

```
meal_analysis_api/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── meal_analyses.py          # フェーズ1: 基本分析エンドポイント
│   │   │   └── meal_analyses_refine.py   # フェーズ2: 動的栄養計算エンドポイント
│   │   └── schemas/
│   │       └── meal.py                   # Pydanticモデル（栄養計算対応）
│   ├── core/
│   │   └── config.py                     # 設定管理
│   ├── services/
│   │   ├── gemini_service.py             # Gemini AI統合（2フェーズ対応）
│   │   ├── usda_service.py               # USDA API クライアント
│   │   └── nutrition_calculation_service.py # 栄養計算エンジン
│   ├── prompts/                          # AI プロンプトテンプレート
│   │   ├── phase1_system_prompt.txt      # フェーズ1システムプロンプト
│   │   ├── phase1_user_prompt_template.txt
│   │   ├── phase2_system_prompt.txt      # フェーズ2システムプロンプト（戦略決定用）
│   │   └── phase2_user_prompt_template.txt
│   └── main.py                           # FastAPIアプリケーション
├── test_images/                          # テスト用画像
├── test_english_phase2.py                # 統合テストスクリプト (v2.0)
├── test_english_phase2_v2.py             # 高度戦略テストスクリプト (v2.1)
├── analyze_logs.py                       # ログ分析ツール
├── logs/                                 # ログファイル（自動生成）
├── requirements.txt                      # Python依存関係
└── service-account-key.json             # GCP認証キー
```

## 🚀 セットアップ

### 1. 依存関係のインストール

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境のアクティベート
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate     # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. Google Cloud 設定

#### Google Cloud SDK のインストール

まだインストールしていない場合は、以下からインストールしてください：
https://cloud.google.com/sdk/docs/install

#### Google Cloud 認証の設定

開発環境では以下のコマンドで認証を設定：

```bash
# Google Cloudにログイン
gcloud auth login

# アプリケーションのデフォルト認証情報を設定
gcloud auth application-default login

# プロジェクトIDを設定
gcloud config set project YOUR_PROJECT_ID
```

本番環境ではサービスアカウントキーを使用：

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your-service-account-key.json"
```

#### Vertex AI API の有効化

```bash
# Vertex AI APIを有効化
gcloud services enable aiplatform.googleapis.com
```

### 3. 環境変数の設定

以下の環境変数を設定してください：

```bash
# USDA API設定
export USDA_API_KEY="your-usda-api-key"

# Vertex AI設定
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
export GEMINI_PROJECT_ID="your-gcp-project-id"
export GEMINI_LOCATION="us-central1"
export GEMINI_MODEL_NAME="gemini-2.5-flash-preview-05-20"
```

## 🖥 サーバー起動

### 開発環境での起動

提供された完全なコマンドでサーバーを起動：

```bash
export USDA_API_KEY="vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg" && export GOOGLE_APPLICATION_CREDENTIALS="/Users/odasoya/meal_analysis_api /service-account-key.json" && export GEMINI_PROJECT_ID=recording-diet-ai-3e7cf && export GEMINI_LOCATION=us-central1 && export GEMINI_MODEL_NAME=gemini-2.5-flash-preview-05-20 && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

または、環境変数を個別に設定してから起動：

```bash
# 環境変数設定
export USDA_API_KEY="vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg"
export GOOGLE_APPLICATION_CREDENTIALS="/Users/odasoya/meal_analysis_api /service-account-key.json"
export GEMINI_PROJECT_ID="recording-diet-ai-3e7cf"
export GEMINI_LOCATION="us-central1"
export GEMINI_MODEL_NAME="gemini-2.5-flash-preview-05-20"

# サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

サーバーが起動すると、以下の URL でアクセス可能になります：

- **API**: http://localhost:8000
- **ドキュメント**: http://localhost:8000/docs
- **ヘルスチェック**: http://localhost:8000/health

## 🧪 テストの実行

### 1. **Phase 1 テスト（USDA クエリ候補生成）**

#### 基本的な使用方法

```bash
# デフォルト画像を使用（自動検索）
python test_english_phase1_v2.py

# 特定の画像を指定
python test_english_phase1_v2.py test_images/food1.jpg

# カスタム画像パスを指定
python test_english_phase1_v2.py ~/Downloads/my_meal.jpg
```

#### ヘルプとオプション

```bash
# ヘルプ表示
python test_english_phase1_v2.py --help

# 利用可能なオプション:
#   image_path: 解析する画像ファイルのパス（省略可能）
```

**結果の保存**:

- `test_results/phase1_result_[画像名]_[タイムスタンプ].json` - タイムスタンプ付きファイル
- `phase1_analysis_result_v2.json` - Phase 2 テスト用のデフォルトファイル

### 2. **Phase 2 テスト（動的栄養計算システム）**

#### 基本的な使用方法

```bash
# デフォルト画像と最新のPhase 1結果を使用
python test_english_phase2_v2.py

# 特定の画像を指定（Phase 1結果は自動検索）
python test_english_phase2_v2.py test_images/food1.jpg

# 画像とPhase 1結果ファイルを両方指定
python test_english_phase2_v2.py test_images/food1.jpg test_results/phase1_result_food1_20240530_120000.json
```

#### ヘルプとオプション

```bash
# ヘルプ表示
python test_english_phase2_v2.py --help

# 利用可能なオプション:
#   image_path: 解析する画像ファイルのパス（省略可能）
#   phase1_result_file: Phase 1結果JSONファイルのパス（省略可能）
```

**結果の保存**:

- `test_results/phase2_result_[画像名]_[タイムスタンプ].json` - タイムスタンプ付きファイル
- `phase2_analysis_result_v2.json` - 後続処理用のデフォルトファイル

### 3. **統合テストワークフロー例**

```bash
# 1. Phase 1: 画像分析とUSDAクエリ候補生成
python test_english_phase1_v2.py test_images/food1.jpg

# 2. Phase 2: 戦略決定と栄養計算
python test_english_phase2_v2.py test_images/food1.jpg

# または、一度に実行（推奨）:
python test_english_phase1_v2.py test_images/food1.jpg && python test_english_phase2_v2.py test_images/food1.jpg
```

### 4. **テスト結果の確認**

```bash
# 保存された結果ファイルの確認
ls -la test_results/

# 最新のPhase 1結果を確認
cat test_results/phase1_result_*.json | jq '.dishes[0].usda_query_candidates'

# 最新のPhase 2結果を確認
cat test_results/phase2_result_*.json | jq '.dishes[0].calculation_strategy'
```

### 5. **旧バージョンテスト（参考）**

#### v2.0 統合テスト

```bash
# 別のターミナルで実行
python test_english_phase2.py
```

## 📡 API 使用方法

### フェーズ 1: 基本分析

```bash
curl -X POST "http://localhost:8000/api/v1/meal-analyses" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg"
```

### フェーズ 2: 動的栄養計算

```bash
# 最初にフェーズ1の結果を取得
initial_result=$(curl -X POST "http://localhost:8000/api/v1/meal-analyses" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg")

# フェーズ2で動的栄養計算
curl -X POST "http://localhost:8000/api/v1/meal-analyses/refine" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg" \
  -F "initial_analysis_data=$initial_result"
```

## 📋 レスポンス例

### フェーズ 1 レスポンス

```json
{
  "dishes": [
    {
      "dish_name": "Fried Fish with Spaghetti and Tomato Sauce",
      "type": "Main Dish",
      "quantity_on_plate": "2 pieces of fish, 1 small serving of spaghetti",
      "ingredients": [
        {
          "ingredient_name": "White Fish Fillet",
          "weight_g": 150.0
        },
        {
          "ingredient_name": "Spaghetti (cooked)",
          "weight_g": 80.0
        }
      ]
    }
  ]
}
```

### フェーズ 2 レスポンス（動的栄養計算）

```json
{
  "dishes": [
    {
      "dish_name": "Spinach and Daikon Radish Aemono",
      "type": "Side Dish",
      "calculation_strategy": "ingredient_level",
      "fdc_id": null,
      "ingredients": [
        {
          "ingredient_name": "Spinach",
          "weight_g": 80.0,
          "fdc_id": 1905313,
          "usda_source_description": "SPINACH",
          "key_nutrients_per_100g": {
            "calories_kcal": 24.0,
            "protein_g": 3.53,
            "carbohydrates_g": 3.53,
            "fat_g": 0.0
          },
          "actual_nutrients": {
            "calories_kcal": 19.2,
            "protein_g": 2.82,
            "carbohydrates_g": 2.82,
            "fat_g": 0.0
          }
        }
      ],
      "dish_total_actual_nutrients": {
        "calories_kcal": 57.45,
        "protein_g": 3.85,
        "carbohydrates_g": 4.57,
        "fat_g": 3.31
      }
    },
    {
      "dish_name": "Green Tea",
      "type": "Drink",
      "calculation_strategy": "dish_level",
      "fdc_id": 1810668,
      "usda_source_description": "GREEN TEA",
      "key_nutrients_per_100g": {
        "calories_kcal": 0.0,
        "protein_g": 0.0,
        "carbohydrates_g": 0.0,
        "fat_g": 0.0
      },
      "dish_total_actual_nutrients": {
        "calories_kcal": 0.0,
        "protein_g": 0.0,
        "carbohydrates_g": 0.0,
        "fat_g": 0.0
      }
    }
  ],
  "total_meal_nutrients": {
    "calories_kcal": 337.95,
    "protein_g": 13.32,
    "carbohydrates_g": 56.19,
    "fat_g": 6.67
  },
  "warnings": null,
  "errors": null
}
```

## 🔧 技術仕様

### 動的計算戦略の決定ロジック

**Dish Level (`dish_level`)**:

- シンプルな単品食品（果物、飲み物、基本食材）
- 標準化された既製品で適切な USDA ID が存在する場合
- 例: 緑茶、りんご、白米

**Ingredient Level (`ingredient_level`)**:

- 複雑な調理済み料理（炒め物、サラダ、スープ）
- 複数食材の組み合わせで料理全体の USDA ID が不適切な場合
- 例: 野菜炒め、手作りサラダ、味噌汁

### 栄養計算式

```
実栄養価 = (100gあたり栄養価 ÷ 100) × 推定重量(g)
```

### 集計階層

1. **食材レベル**: 個別食材の重量 × 100g 栄養価
2. **料理レベル**: 食材レベルの合計 または 料理全体計算
3. **食事レベル**: 全料理の栄養価合計

## ⚠️ エラーハンドリング

API は以下の HTTP ステータスコードを返します：

- `200 OK`: 正常な分析完了
- `400 Bad Request`: 不正なリクエスト（画像形式エラーなど）
- `422 Unprocessable Entity`: バリデーションエラー
- `503 Service Unavailable`: 外部サービス（USDA/Gemini）エラー
- `500 Internal Server Error`: サーバー内部エラー

## 🔍 トラブルシューティング

### 認証エラーが発生する場合

```bash
# 現在の認証状態を確認
gcloud auth list

# 現在のプロジェクト設定を確認
gcloud config list

# 必要に応じて再度認証
gcloud auth application-default login
```

### Vertex AI API が有効になっていない場合

```bash
# APIの有効状況を確認
gcloud services list --enabled | grep aiplatform

# 有効でない場合は有効化
gcloud services enable aiplatform.googleapis.com
```

### USDA API エラーが発生する場合

- API キーが正しく設定されているか確認
- レートリミット（3,600 件/時）に達していないか確認
- ネットワーク接続を確認

## 💻 開発情報

- **フレームワーク**: FastAPI 0.104+
- **AI サービス**: Google Vertex AI (Gemini 2.5 Flash)
- **栄養データベース**: USDA FoodData Central API
- **認証**: Google Cloud サービスアカウント
- **Python バージョン**: 3.9+
- **主要ライブラリ**:
  - `google-cloud-aiplatform` (Vertex AI)
  - `httpx` (非同期 HTTP)
  - `pydantic` (データバリデーション)
  - `pillow` (画像処理)

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 注意事項

**セキュリティ**: API キーやサービスアカウントキーは絶対にリポジトリにコミットしないでください。環境変数として安全に管理してください。

## 📊 ログ分析機能

API の実行ログを詳細に記録・分析する機能が実装されています。

### ログファイル

以下のログファイルが自動的に生成されます：

```
logs/
├── meal_analysis_sessions.jsonl     # セッション詳細ログ（JSONL形式）
├── meal_analysis_detailed.jsonl     # 詳細処理ログ（JSONL形式）
└── *.log                           # 従来のテキストログファイル
```

### ログ分析ツール

```bash
# 基本分析レポート表示
python analyze_logs.py --report

# CSVエクスポート
python analyze_logs.py --export sessions.csv

# 遅いセッション分析（5秒以上）
python analyze_logs.py --slow --threshold 5000

# エラーパターン分析
python analyze_logs.py --errors

# 過去7日間のデータのみ分析
python analyze_logs.py --report --days 7

# 日付範囲指定
python analyze_logs.py --report --start-date 2025-05-01 --end-date 2025-05-31
```

### ログ分析レポート例

```
📊 食事分析API ログレポート

## 📊 基本統計
- **総セッション数**: 50
- **成功セッション**: 48 (96.0%)
- **失敗セッション**: 2 (4.0%)

## ⏱️ パフォーマンス統計
- **平均総実行時間**: 8542.3ms
- **平均Phase1時間**: 2156.7ms
- **平均USDA検索時間**: 1834.2ms
- **平均Phase2時間**: 3251.8ms
- **平均栄養計算時間**: 1299.6ms

## 🎯 戦略統計
- **Dish Level戦略**: 85回
- **Ingredient Level戦略**: 127回
- **戦略比率**: Dish 40.1% vs Ingredient 59.9%
```

## 🚀 本番環境での使用
