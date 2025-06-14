# Advanced Elasticsearch Strategic Search Test - Standalone Edition

## 概要

`test_standalone_analysis.py`は、API サーバーを使わずに直接`app_v2`のパイプラインを実行し、`test_advanced_elasticsearch_search.py`と同様の Advanced Elasticsearch 戦略的検索を行うスタンドアロンテストスクリプトです。

## app_v2 アーキテクチャ構成

### ディレクトリ構造

```
app_v2/
├── components/           # コンポーネント層（各処理段階の実装）
│   ├── base.py                                    # BaseComponent抽象クラス
│   ├── phase1_component.py                        # Phase1: 画像分析コンポーネント
│   ├── elasticsearch_nutrition_search_component.py # Elasticsearch栄養検索コンポーネント
│   └── local_nutrition_search_component.py        # ローカル栄養検索コンポーネント
├── pipeline/            # パイプライン層（処理の統合・管理）
│   ├── orchestrator.py                           # MealAnalysisPipeline（メイン処理統合）
│   └── result_manager.py                         # ResultManager（結果保存管理）
├── services/            # サービス層（外部API・計算処理）
│   ├── gemini_service.py                         # Gemini AI サービス
│   └── nutrition_calculation_service.py          # 栄養計算サービス
├── models/              # データモデル層（型定義・データ構造）
│   ├── phase1_models.py                          # Phase1関連のデータモデル
│   ├── nutrition_search_models.py                # 栄養検索関連のデータモデル
│   ├── nutrition_models.py                       # 栄養価関連のデータモデル
│   └── phase2_models.py                          # Phase2関連のデータモデル（未実装）
├── api/                 # API層（FastAPI エンドポイント）
│   └── v1/endpoints/meal_analysis.py             # 食事分析APIエンドポイント
├── utils/               # ユーティリティ層
├── config/              # 設定層
└── main/                # メイン実行層
```

## test_standalone_analysis.py 実行フロー

### 1. 初期化フェーズ

```python
# 環境設定
setup_environment()

# 画像読み込み
image_bytes = open("test_images/food1.jpg", "rb").read()
image_mime_type = get_image_mime_type("test_images/food1.jpg")

# 結果保存ディレクトリ作成
main_results_dir = f"analysis_results/elasticsearch_test_{timestamp}"
api_calls_dir = f"{main_results_dir}/api_calls"
```

### 2. Step 1: 完全食事分析実行

#### 呼び出されるファイル・クラス

- `app_v2/pipeline/orchestrator.py` → `MealAnalysisPipeline`
- `app_v2/pipeline/result_manager.py` → `ResultManager`
- `app_v2/components/phase1_component.py` → `Phase1Component`
- `app_v2/services/gemini_service.py` → `GeminiService`
- `app_v2/components/elasticsearch_nutrition_search_component.py` → `ElasticsearchNutritionSearchComponent`

#### 処理内容

1. **Phase1Component 実行**

   - Gemini AI による画像分析
   - 料理・食材の検出と構造化
   - 信頼度スコアの算出

2. **ElasticsearchNutritionSearchComponent 実行**

   - Phase1 結果から検索クエリ抽出
   - Elasticsearch 栄養データベース検索
   - 見出し語化検索（lemmatized enhanced search）

3. **ResultManager による結果保存**
   - フェーズ別ログ保存
   - 詳細実行ログ作成

### 3. Step 2: Phase1 結果から検索クエリ抽出

#### 処理内容

```python
# Phase1結果から料理名・食材名を抽出
dish_names = [dish.get('dish_name', '') for dish in dishes]
ingredient_names = []
for dish in dishes:
    for ingredient in dish.get('ingredients', []):
        ingredient_names.append(ingredient.get('ingredient_name', ''))

# 重複除去
all_queries = list(set(dish_names + ingredient_names))
```

### 4. Step 3: Advanced Elasticsearch 戦略的検索実行

#### 呼び出されるファイル・クラス

- `app_v2/components/elasticsearch_nutrition_search_component.py` → `ElasticsearchNutritionSearchComponent`
- `app_v2/models/nutrition_search_models.py` → `NutritionQueryInput`, `NutritionQueryOutput`

#### 処理内容

1. **検索コンポーネント初期化**

   ```python
   es_component = ElasticsearchNutritionSearchComponent(
       multi_db_search_mode=False,   # 見出し語化検索を優先
       results_per_db=5,             # 各データベースから5つずつ結果を取得
       enable_advanced_features=False # 構造化検索は無効化
   )
   ```

2. **検索実行**
   - 見出し語化完全一致ブースト: 2.0
   - 複合語ペナルティ: 0.8
   - 各検索語に対して Elasticsearch 検索実行

### 5. Step 4: 戦略的検索結果分析

#### 処理内容

- 検索サマリー生成
- マッチ率計算
- 検索時間測定
- 見出し語化効果の分析

### 6. Step 5: 戦略的検索結果保存

#### 保存されるファイル構造

```
analysis_results/elasticsearch_test_YYYYMMDD_HHMMSS/
├── comprehensive_multi_image_results.md          # 包括的結果（英語形式）
├── api_calls/                                    # 完全分析結果
│   └── meal_analysis_YYYYMMDD_HHMMSS/
│       └── analysis_XXXXXXXX/                    # 分析ID別フォルダ
│           ├── meal_analysis_XXXXXXXX.json       # 完全分析結果JSON
│           ├── phase1/                           # Phase1結果
│           │   ├── input_output.json
│           │   ├── prompts_and_reasoning.md
│           │   └── detected_items.txt
│           ├── nutrition_search_query/           # 栄養検索結果
│           │   ├── input_output.json
│           │   ├── search_results.md
│           │   └── match_details.txt
│           ├── phase2/                           # Phase2結果（未実装）
│           ├── nutrition_calculation/            # 栄養計算結果（未実装）
│           ├── pipeline_summary.json             # パイプライン全体サマリー
│           └── complete_analysis_log.json        # 完全実行ログ
└── food1/                                        # 戦略的検索結果
    ├── advanced_elasticsearch_search_results.json # 検索結果JSON
    └── advanced_elasticsearch_summary.md          # 検索サマリーMarkdown
```

## 主要コンポーネントの役割

### MealAnalysisPipeline (orchestrator.py)

- **役割**: 全体の処理統合・管理
- **機能**:
  - Phase1Component → ElasticsearchNutritionSearchComponent の順次実行
  - 結果の統合・構造化
  - エラーハンドリング

### Phase1Component (phase1_component.py)

- **役割**: 画像分析・料理検出
- **機能**:
  - Gemini AI による構造化画像分析
  - 料理・食材の検出と信頼度算出
  - 検索クエリ生成用データ作成

### ElasticsearchNutritionSearchComponent (elasticsearch_nutrition_search_component.py)

- **役割**: 高性能栄養データベース検索
- **機能**:
  - 見出し語化検索（lemmatized enhanced search）
  - 複数データベース対応
  - スコアリング・ランキング
  - 検索結果の構造化

### ResultManager (result_manager.py)

- **役割**: 結果保存・ログ管理
- **機能**:
  - フェーズ別結果保存
  - 詳細実行ログ作成
  - ファイル構造管理

### GeminiService (gemini_service.py)

- **役割**: Gemini AI API 連携
- **機能**:
  - 構造化プロンプト実行
  - JSON 形式レスポンス処理
  - エラーハンドリング

## 実行結果の特徴

### 1. 完全分析結果 (api_calls/)

- **Phase1 結果**: 検出された料理・食材の詳細情報
- **栄養検索結果**: データベースマッチング結果
- **実行ログ**: 各コンポーネントの詳細実行情報
- **プロンプト情報**: Gemini AI に送信されたプロンプト内容

### 2. 戦略的検索結果 (food1/)

- **検索結果 JSON**: 全検索結果の構造化データ
- **検索サマリー**: マッチ率・検索時間等の統計情報

### 3. 包括的結果 (comprehensive_multi_image_results.md)

- **英語形式**: test_advanced_elasticsearch_search.py と同様の形式
- **統計情報**: 総合的な分析・検索結果サマリー
- **詳細結果**: 料理別・食材別の検索結果詳細

## 実行コマンド

```bash
python test_standalone_analysis.py
```

## 期待される出力例

```
🚀 Advanced Elasticsearch Strategic Search Test - Standalone Edition v3.0
📝 APIサーバー不要の直接パイプライン実行 + Advanced Elasticsearch戦略的検索

🚀 Advanced Elasticsearch Strategic Search Test (Standalone) 開始
📁 分析対象: test_images/food1.jpg
📊 画像サイズ: 96,595 bytes
🔍 MIMEタイプ: image/jpeg
🔧 検索方法: Advanced Elasticsearch Strategic Search (APIサーバー不要)
============================================================
📁 メイン結果保存ディレクトリ: analysis_results/elasticsearch_test_20250614_HHMMSS
📁 完全分析結果保存ディレクトリ: analysis_results/elasticsearch_test_20250614_HHMMSS/api_calls

🔄 Step 1: 完全食事分析実行中...
✅ 完全分析が完了しました！ (26.37秒)

🔄 Step 2: Phase1結果から検索クエリを抽出中...
📊 抽出された検索クエリ:
   - 料理名: 3個
   - 食材名: 11個
   - 総クエリ数: 14個

🔄 Step 3: Advanced Elasticsearch戦略的検索実行中...
✅ Advanced Elasticsearch戦略的検索完了 (0.107秒)

🔄 Step 4: 戦略的検索結果分析中...
📈 Advanced Elasticsearch戦略的検索結果サマリー:
   - 総検索数: 14
   - 成功マッチ: 14
   - 失敗検索: 0
   - マッチ率: 100.0%

🔄 Step 5: 戦略的検索結果保存中...
✅ 戦略的検索結果保存完了！

================================================================================
🎯 Advanced Elasticsearch Strategic Search Test 完了サマリー
================================================================================
📋 分析ID: 3d4fdfb9
⏱️  処理時間サマリー:
   - 完全分析時間: 26.37秒
   - 戦略的検索時間: 0.107秒
   - 総処理時間: 26.47秒
🔍 戦略的検索結果サマリー:
   - 総検索数: 14
   - 成功マッチ: 14
   - マッチ率: 100.0%
   - 総結果数: 70
✅ Advanced Elasticsearch Strategic Search Test 完了！
🎯 総合成功率: 100.0%
```

## 技術的特徴

### 1. コンポーネント化アーキテクチャ

- 各処理段階が独立したコンポーネントとして実装
- 再利用性・テスタビリティの向上
- 明確な責任分離

### 2. 統一されたデータモデル

- 型安全性の確保
- データ構造の一貫性
- バリデーション機能

### 3. 詳細なログ・結果保存

- フェーズ別の詳細ログ
- 実行時間・エラー情報の記録
- 再現可能な結果保存

### 4. 高性能 Elasticsearch 検索

- 見出し語化検索による精度向上
- スコアリング・ランキング機能
- 複数データベース対応

このスタンドアロン版により、API サーバーを起動することなく、完全な食事分析パイプラインと Advanced Elasticsearch 戦略的検索を実行・検証することができます。
