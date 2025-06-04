# 食事分析 API (Meal Analysis API) v2.1

## 概要

この API は、**Google Gemini AI** と **USDA データベース**を使用した高度な食事画像分析システムです。**動的栄養計算機能**により、料理の特性に応じて最適な栄養計算戦略を自動選択し、正確な栄養価情報を提供します。

## 🌟 主な機能

### **🆕 v2.1 新機能: モジュラーアーキテクチャ**

- **🏗️ 4 フェーズ分離設計**: 各処理段階を独立したコンポーネントとして完全分離
  - `Phase 1`: 画像処理・食品認識 (`image_processor`)
  - `USDA DB Query`: データベース検索・クエリ実行 (`db_interface`)
  - `Phase 2`: データ解釈・栄養素マッピング (`data_interpreter`)
  - `Nutrition Calculation`: 栄養計算・集計 (`nutrition_calculator`)
- **📁 フェーズ出力保存機能**: 各フェーズの入出力を JSON 形式で自動保存・デバッグ支援
- **⚙️ 設定駆動型設計**: データベースやプロンプト戦略をコード変更なしで修正可能
- **🔧 抽象化レイヤー**: DB ハンドラーや解釈戦略のプラガブル実装
- **📊 Pydantic モデル**: 全フェーズ間のタイプセーフなデータ転送

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

### レガシー API 構造（FastAPI サーバー）

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
```

### 🆕 新モジュラーアーキテクチャ（v2.1）

```
meal_analysis_api/
├── src/                                  # 🆕 新しいモジュラーコア
│   ├── image_processor/                  # Phase 1: 画像処理
│   │   ├── processor.py                  # 画像分析エンジン
│   │   └── image_models.py               # 入出力Pydanticモデル
│   ├── db_interface/                     # USDA DB抽象化レイヤー
│   │   ├── base_handler.py               # 抽象DBハンドラー
│   │   ├── usda_handler.py               # USDA実装
│   │   └── db_models.py                  # クエリ・結果モデル
│   ├── data_interpreter/                 # Phase 2: データ解釈
│   │   ├── interpreter.py                # 解釈エンジン
│   │   ├── interpretation_models.py      # 解釈結果モデル
│   │   └── strategies/                   # 解釈戦略（プラガブル）
│   │       ├── base_strategy.py          # 抽象戦略クラス
│   │       └── default_usda_strategy.py  # USDA用デフォルト戦略
│   ├── nutrition_calculator/             # Phase 4: 栄養計算
│   │   ├── calculator.py                 # 栄養計算エンジン
│   │   └── calculation_models.py         # 計算結果モデル
│   ├── orchestration/                    # ワークフロー統括
│   │   └── workflow_manager.py           # 4フェーズ統合オーケストレーター
│   ├── common/                           # 共通コンポーネント
│   │   ├── config_loader.py              # 設定管理
│   │   └── exceptions.py                 # カスタム例外
│   └── main.py                           # 🆕 新しいメインエントリポイント
├── configs/                              # 🆕 設定ファイル集約
│   ├── main_config.yaml                  # メイン設定（プロンプト、DB戦略）
│   └── prompts/                          # プロンプトテンプレート
├── test_results/                         # 結果保存ディレクトリ
│   └── phase_outputs/                    # 🆕 フェーズ別出力保存
├── tests/                                # 🆕 テストスイート
│   ├── unit/                             # 単体テスト
│   └── integration/                      # 統合テスト
├── test_images/                          # テスト用画像
├── test_english_phase1_v2.py             # レガシーテストスクリプト
├── test_english_phase2_v2.py             # レガシーテストスクリプト
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

### 🆕 新しいモジュラーアーキテクチャ（推奨）

#### **統合 4 フェーズワークフロー**

新しいモジュラーアーキテクチャでは、1 つのコマンドで全 4 フェーズを実行できます：

```bash
# 基本的な使用方法
python -m src.main test_images/food2.jpg

# 設定ファイルを指定
python -m src.main test_images/food2.jpg --config configs/main_config.yaml

# フェーズ出力保存を有効化
python -m src.main test_images/food2.jpg --save-phases

# デバッグモードで実行
python -m src.main test_images/food2.jpg --debug

# 結果をJSONファイルに保存
python -m src.main test_images/food2.jpg --output results/meal_analysis.json
```

#### **フェーズ出力保存機能 🔍**

`--save-phases` オプションまたは設定ファイルで `SAVE_PHASE_OUTPUTS: true` にすると、各フェーズの入出力が詳細に保存されます：

```bash
# フェーズ出力保存を有効化して実行
python -m src.main test_images/food2.jpg --save-phases
```

**保存されるファイル**:

```
test_results/phase_outputs/
├── phase1_food2_20250604_180324.json        # Phase 1: 画像処理結果
├── usda_db_query_food2_20250604_180331.json # USDA DBクエリ結果
├── phase2_food2_20250604_180331.json        # Phase 2: データ解釈結果
├── nutrition_calculation_food2_20250604_180331.json # 栄養計算結果
└── workflow_summary_food2_20250604_180331.json     # 全体サマリー
```

**各フェーズの詳細確認方法**:

```bash
# Phase 1で認識された食品アイテム
cat test_results/phase_outputs/phase1_food2_*.json | jq '.output.identified_items'

# USDAデータベースから取得された最初の食品データ
cat test_results/phase_outputs/usda_db_query_food2_*.json | jq '.output.retrieved_foods[0]'

# Phase 2で解釈された最初の食品
cat test_results/phase_outputs/phase2_food2_*.json | jq '.output.interpreted_foods[0]'

# 最終的な栄養素集計結果
cat test_results/phase_outputs/nutrition_calculation_food2_*.json | jq '.output.total_nutrients'

# ワークフロー全体のサマリー
cat test_results/phase_outputs/workflow_summary_food2_*.json | jq '.output'
```

#### **利用可能なオプション**

```bash
# ヘルプ表示
python -m src.main --help

# 主要オプション:
#   image_path: 解析する画像ファイルのパス（必須）
#   --config: 設定ファイルのパス（デフォルト: configs/main_config.yaml）
#   --output: 結果出力ファイルパス（JSONファイル）
#   --text: 補助テキスト情報
#   --debug: デバッグモードで実行
#   --quiet: クワイエットモード（エラーのみ表示）
#   --save-phases: 各フェーズの入出力をJSONファイルに保存
#   --no-save-phases: フェーズ出力保存を無効化
```

### レガシーテスト（参考）

#### 1. **Phase 1 テスト（USDA クエリ候補生成）**

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

#### 2. **Phase 2 テスト（動的栄養計算システム）**

#### 基本的な使用方法

```bash
# デフォルト画像と最新のPhase 1結果を使用
python test_english_phase2_v2.py

# 特定の画像を指定（Phase 1結果は自動検索）
python test_english_phase2_v2.py test_images/food1.jpg

# 画像とPhase 1結果ファイルを両方指定
python test_english_phase2_v2.py test_images/food1.jpg test_results/phase1_result_food1_20240530_120000.json

# 結果を自動保存するオプション付き
python test_english_phase2_v2.py test_images/food1.jpg --save-results
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

### **新モジュラーアーキテクチャ（v2.1）**

- **アーキテクチャパターン**: 4 フェーズ分離、ストラテジーパターン、依存性注入
- **型安全性**: Pydantic V2 モデル、完全な型ヒント対応
- **設定管理**: YAML 設定ファイル、環境変数統合
- **データ永続化**: JSON フェーズ出力、構造化ログ
- **テスタビリティ**: 単体テスト、統合テスト、モッキング対応
- **拡張性**: プラガブル DB、解釈戦略、プロンプトテンプレート

### **フェーズ間データフロー**

```
ImageInput → ProcessedImageData → QueryParameters → RawDBResult → StructuredNutrientInfo → FinalNutritionReport
```

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

## ⚙️ モジュラーアーキテクチャの設定とカスタマイズ

### **設定ファイル（configs/main_config.yaml）**

新しいアーキテクチャでは、全ての設定を `configs/main_config.yaml` で管理します：

```yaml
# フェーズ出力保存設定
SAVE_PHASE_OUTPUTS: true
PHASE_OUTPUT_DIR: "test_results/phase_outputs"

# プロンプト設定（クエリ生成戦略）
PROMPTS:
  default_usda_search_v1: "{food_name}"
  usda_raw_food_search: "raw {food_name}"
  usda_cooked_food_search: "cooked {food_name}"

# データ解釈設定
INTERPRETER_CONFIG:
  STRATEGY_NAME: "DefaultUSDA"
  STRATEGY_CONFIGS:
    DefaultUSDA:
      NUTRIENT_MAP:
        "Protein": "PROTEIN"
        "Total lipid (fat)": "TOTAL_FAT"
        "Energy": "CALORIES"
      TARGET_UNITS:
        "PROTEIN": "g"
        "TOTAL_FAT": "g"
        "CALORIES": "kcal"
```

### **データベースの切り替え方法**

現在は USDA をサポートしていますが、他のデータベースに切り替え可能：

```yaml
DB_CONFIG:
  TYPE: "USDA" # 将来: "OPENFOODFACTS", "CUSTOM_SQL" など
  DEFAULT_QUERY_STRATEGY: "default_usda_search_v1"
  USDA:
    USDA_API_BASE_URL: "https://api.nal.usda.gov/fdc/v1"
```

新しいデータベースを追加する場合：

1. `src/db_interface/` に新しいハンドラークラスを作成
2. `DBHandler` 抽象基底クラスを継承
3. 設定ファイルで `TYPE` を変更

### **プロンプト戦略のカスタマイズ**

クエリ生成戦略をコード変更なしで修正可能：

```yaml
PROMPTS:
  # 基本戦略
  default_usda_search_v1: "{food_name}"

  # 調理状態を含む戦略
  usda_cooked_food_search: "cooked {food_name}"

  # 詳細属性を含む戦略
  usda_detailed_search: "{food_name} {state} {type}"

  # カスタム戦略例
  my_custom_strategy: "organic {food_name} fresh"
```

### **栄養素マッピングのカスタマイズ**

USDA の栄養素名を標準名にマッピング：

```yaml
INTERPRETER_CONFIG:
  STRATEGY_CONFIGS:
    DefaultUSDA:
      NUTRIENT_MAP:
        # USDA名 -> 標準名
        "Protein": "PROTEIN"
        "Total lipid (fat)": "TOTAL_FAT"
        "Calcium, Ca": "CALCIUM"
        # 新しいマッピングを追加可能
        "Vitamin D (D2 + D3)": "VITAMIN_D"
```

### **解釈戦略の拡張**

新しい解釈戦略を追加する場合：

1. `src/data_interpreter/strategies/` に新しい戦略クラスを作成
2. `BaseInterpretationStrategy` を継承
3. 設定ファイルで戦略を指定：

```yaml
INTERPRETER_CONFIG:
  STRATEGY_NAME: "MyCustomStrategy" # 新しい戦略
  STRATEGY_CONFIGS:
    MyCustomStrategy:
      # カスタム設定
```

### **フェーズ出力のカスタマイズ**

フェーズ出力保存の詳細制御：

```yaml
# 出力制御
SAVE_PHASE_OUTPUTS: true
PHASE_OUTPUT_DIR: "custom_output_dir"

# 個別フェーズの制御（将来実装予定）
PHASE_OUTPUT_SETTINGS:
  save_phase1: true
  save_usda_query: true
  save_phase2: true
  save_nutrition_calc: true
  save_workflow_summary: true
```

### **環境別設定の管理**

```bash
# 開発環境
python -m src.main image.jpg --config configs/dev_config.yaml

# 本番環境
python -m src.main image.jpg --config configs/prod_config.yaml

# テスト環境
python -m src.main image.jpg --config configs/test_config.yaml
```

## 🔧 技術仕様

### **新モジュラーアーキテクチャ（v2.1）**

- **アーキテクチャパターン**: 4 フェーズ分離、ストラテジーパターン、依存性注入
- **型安全性**: Pydantic V2 モデル、完全な型ヒント対応
- **設定管理**: YAML 設定ファイル、環境変数統合
- **データ永続化**: JSON フェーズ出力、構造化ログ
- **テスタビリティ**: 単体テスト、統合テスト、モッキング対応
- **拡張性**: プラガブル DB、解釈戦略、プロンプトテンプレート

### **フェーズ間データフロー**

```
ImageInput → ProcessedImageData → QueryParameters → RawDBResult → StructuredNutrientInfo → FinalNutritionReport
```

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

## ⚙️ モジュラーアーキテクチャの設定とカスタマイズ

### **設定ファイル（configs/main_config.yaml）**

新しいアーキテクチャでは、全ての設定を `configs/main_config.yaml` で管理します：

```yaml
# フェーズ出力保存設定
SAVE_PHASE_OUTPUTS: true
PHASE_OUTPUT_DIR: "test_results/phase_outputs"

# プロンプト設定（クエリ生成戦略）
PROMPTS:
  default_usda_search_v1: "{food_name}"
  usda_raw_food_search: "raw {food_name}"
  usda_cooked_food_search: "cooked {food_name}"

# データ解釈設定
INTERPRETER_CONFIG:
  STRATEGY_NAME: "DefaultUSDA"
  STRATEGY_CONFIGS:
    DefaultUSDA:
      NUTRIENT_MAP:
        "Protein": "PROTEIN"
        "Total lipid (fat)": "TOTAL_FAT"
        "Energy": "CALORIES"
      TARGET_UNITS:
        "PROTEIN": "g"
        "TOTAL_FAT": "g"
        "CALORIES": "kcal"
```

### **データベースの切り替え方法**

現在は USDA をサポートしていますが、他のデータベースに切り替え可能：

```yaml
DB_CONFIG:
  TYPE: "USDA" # 将来: "OPENFOODFACTS", "CUSTOM_SQL" など
  DEFAULT_QUERY_STRATEGY: "default_usda_search_v1"
  USDA:
    USDA_API_BASE_URL: "https://api.nal.usda.gov/fdc/v1"
```

新しいデータベースを追加する場合：

1. `src/db_interface/` に新しいハンドラークラスを作成
2. `DBHandler` 抽象基底クラスを継承
3. 設定ファイルで `TYPE` を変更

### **プロンプト戦略のカスタマイズ**

クエリ生成戦略をコード変更なしで修正可能：

```yaml
PROMPTS:
  # 基本戦略
  default_usda_search_v1: "{food_name}"

  # 調理状態を含む戦略
  usda_cooked_food_search: "cooked {food_name}"

  # 詳細属性を含む戦略
  usda_detailed_search: "{food_name} {state} {type}"

  # カスタム戦略例
  my_custom_strategy: "organic {food_name} fresh"
```

### **栄養素マッピングのカスタマイズ**

USDA の栄養素名を標準名にマッピング：

```yaml
INTERPRETER_CONFIG:
  STRATEGY_CONFIGS:
    DefaultUSDA:
      NUTRIENT_MAP:
        # USDA名 -> 標準名
        "Protein": "PROTEIN"
        "Total lipid (fat)": "TOTAL_FAT"
        "Calcium, Ca": "CALCIUM"
        # 新しいマッピングを追加可能
        "Vitamin D (D2 + D3)": "VITAMIN_D"
```

### **解釈戦略の拡張**

新しい解釈戦略を追加する場合：

1. `src/data_interpreter/strategies/` に新しい戦略クラスを作成
2. `BaseInterpretationStrategy` を継承
3. 設定ファイルで戦略を指定：

```yaml
INTERPRETER_CONFIG:
  STRATEGY_NAME: "MyCustomStrategy" # 新しい戦略
  STRATEGY_CONFIGS:
    MyCustomStrategy:
      # カスタム設定
```

### **フェーズ出力のカスタマイズ**

フェーズ出力保存の詳細制御：

```yaml
# 出力制御
SAVE_PHASE_OUTPUTS: true
PHASE_OUTPUT_DIR: "custom_output_dir"

# 個別フェーズの制御（将来実装予定）
PHASE_OUTPUT_SETTINGS:
  save_phase1: true
  save_usda_query: true
  save_phase2: true
  save_nutrition_calc: true
  save_workflow_summary: true
```

### **環境別設定の管理**

```bash
# 開発環境
python -m src.main image.jpg --config configs/dev_config.yaml

# 本番環境
python -m src.main image.jpg --config configs/prod_config.yaml

# テスト環境
python -m src.main image.jpg --config configs/test_config.yaml
```

## 🔧 技術仕様

### **新モジュラーアーキテクチャ（v2.1）**

- **アーキテクチャパターン**: 4 フェーズ分離、ストラテジーパターン、依存性注入
- **型安全性**: Pydantic V2 モデル、完全な型ヒント対応
- **設定管理**: YAML 設定ファイル、環境変数統合
- **データ永続化**: JSON フェーズ出力、構造化ログ
- **テスタビリティ**: 単体テスト、統合テスト、モッキング対応
- **拡張性**: プラガブル DB、解釈戦略、プロンプトテンプレート

### **フェーズ間データフロー**

```
ImageInput → ProcessedImageData → QueryParameters → RawDBResult → StructuredNutrientInfo → FinalNutritionReport
```

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

### **新モジュラーアーキテクチャ（v2.1）**

- **フレームワーク**: モジュラー設計、ストラテジーパターン
- **型安全性**: Pydantic V2、完全型ヒント対応
- **設定管理**: YAML 設定ファイル、環境変数統合
- **テスト**: 単体テスト、統合テスト、フェーズ別テスト対応

### **レガシー API（v2.0）**

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

### **共通技術要件**

- **Python バージョン**: 3.9+
- **主要ライブラリ**:
  - `google-cloud-aiplatform` (Vertex AI)
  - `httpx` (非同期 HTTP)
  - `pydantic` (データバリデーション)
  - `pillow` (画像処理)
  - `PyYAML` (設定ファイル)
  - `pathlib` (パス操作)

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
