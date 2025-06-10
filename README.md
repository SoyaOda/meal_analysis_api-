# 食事分析 API (Meal Analysis API) v2.0

## 概要

この API は、**Google Gemini AI** と **マルチデータベース栄養検索システム**を使用した高度な食事画像分析システムです。**動的栄養計算機能**により、料理の特性に応じて最適な栄養計算戦略を自動選択し、正確な栄養価情報を提供します。

## 🌟 主な機能

### **🔥 新機能: マルチデータベース栄養検索 v2.0**

- **📊 3 つのデータベース統合検索**: 1 つのクエリで複数のデータベースから包括的な栄養情報を取得
  - **YAZIO**: 1,825 項目 - バランスの取れた食品カテゴリ
  - **MyNetDiary**: 1,142 項目 - 科学的/栄養学的アプローチ
  - **EatThisMuch**: 8,878 項目 - 最大かつ最も包括的なデータベース
- **⚡ 高速検索パフォーマンス**: 平均 0.010 秒/クエリで複数 DB 検索
- **🎯 高精度マッチング**: 各 DB から上位 3 件、完全一致で 90.9%の成功率
- **💾 詳細結果保存**: JSON・マークダウン形式での検索結果自動保存

### **従来機能: 動的栄養計算システム**

- **🧠 AI 駆動の計算戦略決定**: Gemini AI が各料理に対して最適な栄養計算方法を自動選択
- **🎯 高精度栄養計算**: 食材重量 × 100g あたり栄養価で正確な実栄養価を算出
- **📊 3 層集計システム**: 食材 → 料理 → 食事全体の自動栄養集計

### **コア機能**

- **フェーズ 1**: Gemini AI による食事画像の分析（料理識別、食材抽出、重量推定）
- **マルチ DB 検索**: 3 つのデータベースからの包括的栄養情報取得
- **複数料理対応**: 1 枚の画像で複数の料理を同時分析
- **英語・日本語対応**: 多言語での食材・料理認識
- **OpenAPI 3.0 準拠**: 完全な API 文書化とタイプ安全性

## 🏗 プロジェクト構造

```
meal_analysis_api_2/
├── db/                                   # マルチデータベース（新機能）
│   ├── yazio_db.json                     # YAZIO栄養データベース（1,825項目）
│   ├── mynetdiary_db.json                # MyNetDiary栄養データベース（1,142項目）
│   └── eatthismuch_db.json               # EatThisMuch栄養データベース（8,878項目）
├── app_v2/                               # 新アーキテクチャ版
│   ├── components/                       # コンポーネントベース設計
│   │   ├── local_nutrition_search_component.py  # マルチDB検索コンポーネント
│   │   ├── phase1_component.py           # 画像分析コンポーネント
│   │   └── base.py                       # ベースコンポーネント
│   ├── pipeline/                         # パイプライン管理
│   │   ├── orchestrator.py               # メイン処理オーケストレーター
│   │   └── result_manager.py             # 結果管理システム
│   ├── models/                           # データモデル
│   │   ├── nutrition_search_models.py    # 栄養検索モデル
│   │   └── phase1_models.py              # Phase1モデル
│   ├── main/
│   │   └── app.py                        # FastAPIアプリケーション
│   └── config/                           # 設定管理
├── test_multi_db_nutrition_search.py     # マルチDB検索テストスクリプト（新機能）
├── test_local_nutrition_search_v2.py     # ローカル検索テストスクリプト
├── test_images/                          # テスト用画像
└── requirements.txt                      # Python依存関係
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

### app_v2 サーバーの起動（マルチ DB 対応）

```bash
# app_v2サーバーの起動
python -m app_v2.main.app
```

**⚠️ 注意**: 相対インポートエラーを回避するため、必ずモジュール形式で実行してください。

サーバーが起動すると、以下の URL でアクセス可能になります：

- **API**: http://localhost:8000
- **ドキュメント**: http://localhost:8000/docs
- **ヘルスチェック**: http://localhost:8000/health

## 🧪 テストの実行

### 🔥 マルチデータベース栄養検索テスト（最新機能）

**重要**: サーバーが起動している状態で実行してください。

```bash
# 別のターミナルで実行
python test_multi_db_nutrition_search.py
```

**期待される結果**:

- **検索速度**: 11 クエリを 0.10 秒で処理
- **マッチ率**: 各 DB90.9%のクエリで結果発見
- **総マッチ数**: 87 件（平均 7.9 件/クエリ）
- **データベース統計**:
  - YAZIO: 1,825 項目
  - MyNetDiary: 1,142 項目
  - EatThisMuch: 8,878 項目

**テスト結果例**:

```
📈 Multi-Database Search Results Summary:
- Total queries: 11
- Total matches found: 87
- Average matches per query: 7.9
- Search time: 0.10s

🔍 Detailed Query Results:
1. 'Roasted Potatoes' (dish)
   EatThisMuch: 3 matches
     Best: 'Roasted Potatoes' (score: 1.000)
     Nutrition: 91.0 kcal, 1.9g protein
```

### ローカル栄養検索テスト

```bash
# ローカル栄養データベース検索の統合テスト
python test_local_nutrition_search_v2.py
```

### 基本テスト（フェーズ 1 のみ）

```bash
python test_phase1_only.py
```

## 🚀 ローカル栄養データベース検索システム v2.0

### **新機能: ローカルデータベース統合**

システムが USDA API 依存からローカル栄養データベース検索に対応しました：

- **🔍 BM25F + マルチシグナルブースティング検索**: 高精度な食材マッチング
- **📊 8,878 項目のローカルデータベース**: オフライン栄養計算対応
- **⚡ 90.9%マッチ率**: 実測値による高い成功率
- **🔄 USDA 互換性**: 既存システムとの完全互換性維持

### サーバー起動（v2.0 対応）

```bash
# app_v2サーバーの起動
python -m app_v2.main.app
```

### ローカル栄養検索テスト

**重要**: サーバーが起動している状態で実行してください。

```bash
# ローカル栄養データベース検索の統合テスト
python test_local_nutrition_search_v2.py
```

**期待される結果**:

- **マッチ率**: 90.9% (10/11 検索成功)
- **レスポンス時間**: ~11 秒
- **データベース**: ローカル栄養データ (8,878 項目)
- **検索方法**: BM25F + マルチシグナルブースティング

**テスト結果例**:

```
🔍 Local Nutrition Search Results:
- Matches found: 10
- Match rate: 90.9%
- Search method: local_nutrition_database
- Total searches: 11
- Successful matches: 10

🍽 Final Meal Nutrition:
- Calories: 400.00 kcal
- Protein: 60.00 g
- Carbohydrates: 220.00 g
- Fat: 120.00 g
```

### データベース詳細

**ローカル栄養データベース構成**:

- `dish_db.json`: 4,583 料理データ
- `ingredient_db.json`: 1,473 食材データ
- `branded_db.json`: 2,822 ブランド食品
- `unified_nutrition_db.json`: 8,878 統合データ

## 📡 API 使用方法

### 🔥 完全分析 (推奨): 全フェーズ統合

**1 つのリクエストで全ての分析を実行**

```bash
curl -X POST "http://localhost:8000/api/v1/meal-analyses/complete" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@test_images/food3.jpg"
```

このエンドポイントは以下を自動実行します：

- フェーズ 1: 画像分析
- USDA 照合: 食材データベース検索
- フェーズ 2: 計算戦略決定
- 栄養計算: 最終栄養価算出
- 結果保存: 自動的にファイル保存

**保存された結果の取得**

```bash
# 全結果一覧
curl "http://localhost:8000/api/v1/meal-analyses/results"

# 特定の結果取得
curl "http://localhost:8000/api/v1/meal-analyses/results/{analysis_id}"
```

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
