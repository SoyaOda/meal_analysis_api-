# Meal Analysis API Documentation

## 概要

AI画像認識・音声認識と栄養データベース検索を統合した高精度食事分析APIです。DeepInfra Vision AI、Google Cloud Speech-to-Text v2、Word Query API栄養データベースを活用し、食事画像や音声から料理・食材・栄養価を自動計算します。

## 🚀 本番環境情報

### API基本情報
- **API URL**: `https://meal-analysis-api-1077966746907.us-central1.run.app`
- **バージョン**: v2.1
- **アーキテクチャ**: Component-based Pipeline
- **プラットフォーム**: Google Cloud Run
- **AI Engine**: DeepInfra (Gemma 3-27B Vision & Text Models)
- **音声認識**: Google Cloud Speech-to-Text v2
- **栄養データベース**: Word Query API統合 (Elasticsearch)

### インフラ構成
- **Cloud Run**:
  - メモリ: 2GB
  - CPU: 1コア
  - 並行性: 1 (決定性確保)
  - 最大インスタンス: 10
  - タイムアウト: 300秒
- **AI推論サービス**: DeepInfra API
- **音声認識サービス**: Google Cloud Speech-to-Text v2 API
- **栄養検索**: Word Query API (Elasticsearch統合)

## 📋 主要エンドポイント

### 1. ルートエンドポイント
```
GET /
```
API基本情報の取得

**レスポンス例**:
```json
{
  "message": "食事分析 API v2.0 - コンポーネント化版",
  "version": "2.0.0",
  "architecture": "Component-based Pipeline",
  "docs": "/docs"
}
```

### 2. ヘルスチェック
```
GET /health
```
API稼働状況の確認

**レスポンス例**:
```json
{
  "status": "healthy",
  "version": "v2.0",
  "components": ["Phase1Component", "AdvancedNutritionSearchComponent", "NutritionCalculationComponent"]
}
```

### 3. 完全食事分析API ⭐
```
POST /api/v1/meal-analyses/complete
```
**メインAPI - 食事画像から栄養価までの完全分析**

#### パラメータ

| パラメータ | 型 | 必須 | 説明 | デフォルト | 制限 |
|-----------|---|-----|-----|---------|-----|
| `image` | file | ✅ | 分析対象の食事画像 | - | JPEG/PNG, ~10MB |
| `ai_model_id` | string | ❌ | 使用AIモデル | デフォルト | Gemma3-27B等 |
| `optional_text` | string | ❌ | 追加情報テキスト(英語) | null | 補助情報 |
| `temperature` | float | ❌ | AI推論ランダム性 | 0.0 | 0.0-1.0 |
| `seed` | integer | ❌ | 再現性シード値 | 123456 | - |
| `test_execution` | boolean | ❌ | テスト実行モード | false | - |
| `test_results_dir` | string | ❌ | テスト結果保存先 | null | テスト実行時のみ |
| `save_detailed_logs` | boolean | ❌ | 分析ログ保存 | true | - |

#### リクエスト例
```bash
# 基本的な分析
curl -X POST "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/complete" \
  -F "image=@food.jpg" \
  -F "temperature=0.0" \
  -F "seed=123456"

# 追加テキスト付き分析
curl -X POST "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/complete" \
  -F "image=@meal.jpg" \
  -F "optional_text=This is a homemade low-sodium pasta" \
  -F "temperature=0.0" \
  -F "seed=123456"
```

### 4. 音声からの完全食事分析API ⭐ **NEW**
```
POST /api/v1/meal-analyses/voice
```
**新機能 - 音声データから栄養価までの完全分析**

#### パラメータ

| パラメータ | 型 | 必須 | 説明 | デフォルト | 制限 |
|-----------|---|-----|-----|---------|-----|
| `audio` | file | ✅ | 分析対象の音声ファイル | - | WAV形式推奨, ~10MB |
| `llm_model_id` | string | ❌ | 使用するLLMモデルID | デフォルト | Gemma3-27B等 |
| `language_code` | string | ❌ | 音声認識言語コード | "en-US" | **en-US推奨** |
| `optional_text` | string | ❌ | 追加情報テキスト(英語) | null | 音声と併せて分析 |
| `temperature` | float | ❌ | AI推論ランダム性 | 0.0 | 0.0-1.0 |
| `seed` | integer | ❌ | 再現性シード値 | 123456 | - |
| `test_execution` | boolean | ❌ | テスト実行モード | false | - |
| `test_results_dir` | string | ❌ | テスト結果保存先 | null | テスト実行時のみ |
| `save_detailed_logs` | boolean | ❌ | 詳細ログ保存 | true | - |

#### リクエスト例
```bash
# 基本的な音声分析（WAV形式・英語音声）
curl -X POST "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/voice" \
  -F "audio=@breakfast.wav" \
  -F "language_code=en-US"

# 高精度分析（推奨設定）
curl -X POST "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/voice" \
  -F "audio=@meal_voice.wav" \
  -F "language_code=en-US" \
  -F "optional_text=This is a homemade breakfast with organic ingredients" \
  -F "temperature=0.3" \
  -F "seed=789456" \
  -F "save_detailed_logs=true"

# 決定的分析（再現性確保）
curl -X POST "https://meal-analysis-api-1077966746907.us-central1.run.app/api/v1/meal-analyses/voice" \
  -F "audio=@breakfast_detailed.wav" \
  -F "language_code=en-US" \
  -F "temperature=0.0" \
  -F "seed=123456"
```

#### レスポンス形式

音声分析も画像分析と同一のレスポンス形式で返されます：

```json
{
  "analysis_id": "10bccc2a",
  "input_type": "voice",
  "total_dishes": 2,
  "total_ingredients": 4,
  "processing_time_seconds": 23.33,
  "dishes": [
    {
      "dish_name": "Two Large Eggs",
      "confidence": 0.95,
      "ingredients": [
        {
          "ingredient_name": "Egg whole raw",
          "weight_g": 100.0,
          "nutrition_per_100g": {
            "calories": 156.0,
            "protein": 12.0
          },
          "calculated_nutrition": {
            "calories": 156.0,
            "protein": 12.0,
            "fat": 0.0,
            "carbs": 0.0,
            "fiber": null,
            "sugar": null,
            "sodium": null
          },
          "source_db": "mynetdiary_api",
          "calculation_notes": [
            "Scaled from 100g base data using factor 1.000",
            "Source: mynetdiary_api database"
          ]
        }
      ],
      "total_nutrition": {
        "calories": 312.0,
        "protein": 24.0,
        "fat": 0.0,
        "carbs": 0.0,
        "fiber": null,
        "sugar": null,
        "sodium": null
      },
      "calculation_metadata": {
        "ingredient_count": 2,
        "total_weight_g": 200.0,
        "calculation_method": "weight_based_scaling"
      }
    }
  ],
  "total_nutrition": {
    "calories": 423.93,
    "protein": 28.33,
    "fat": 0.0,
    "carbs": 0.0
  },
  "ai_model_used": "google/gemma-3-27b-it",
  "match_rate_percent": 100.0,
  "search_method": "elasticsearch"
}
```

### 5. パイプライン情報
```
GET /api/v1/meal-analyses/pipeline-info
```
パイプライン構成情報の取得

### 6. API仕様書
```
GET /docs
```
Swagger UI（インタラクティブAPI仕様書）

## 📊 パラメータ統一仕様

### 🎯 **画像・音声分析の完全パラメータ統一**

| パラメータ | 画像分析 | 音声分析 | デフォルト値 | 説明 |
|------------|----------|----------|-------------|------|
| **言語設定** | N/A | `language_code` | `"en-US"` | 音声認識言語 |
| **追加テキスト** | `optional_text` | `optional_text` | `null` | 英語想定の補助情報 |
| **ランダム性制御** | `temperature` | `temperature` | `0.0` | AI推論の決定性制御 |
| **再現性制御** | `seed` | `seed` | `123456` | 結果の再現性確保 |
| **テスト出力先** | `test_results_dir` | `test_results_dir` | `null` | テスト結果保存先 |
| **テスト実行** | `test_execution` | `test_execution` | `false` | テストモード |
| **詳細ログ** | `save_detailed_logs` | `save_detailed_logs` | `true` | 分析ログ保存 |

### 📋 レスポンススキーマ

#### 成功レスポンス (HTTP 200) - SimplifiedCompleteAnalysisResponse

| フィールド | 型 | 必須/任意 | 説明 | 例 |
|-----------|---|-----------|------|-----|
| **analysis_id** | string | ✅ 必須 | 分析セッションID | "10bccc2a" |
| **input_type** | string | ✅ 必須 | 入力タイプ | "voice" or "image" |
| **total_dishes** | integer | ✅ 必須 | 検出された料理数 | 2 |
| **total_ingredients** | integer | ✅ 必須 | 総食材数 | 4 |
| **processing_time_seconds** | number | ✅ 必須 | 処理時間（秒） | 23.33 |
| **dishes** | array | ✅ 必須 | 料理一覧（DishSummary配列） | - |
| ↳ **dish_name** | string | ✅ 必須 | 料理名 | "Two Large Eggs" |
| ↳ **confidence** | number | ✅ 必須 | 識別信頼度 | 0.95 |
| ↳ **ingredients** | array | ✅ 必須 | 食材詳細（IngredientSummary配列） | - |
| ↳ ↳ **ingredient_name** | string | ✅ 必須 | 食材名 | "Egg whole raw" |
| ↳ ↳ **weight_g** | number | ✅ 必須 | 重量（g） | 100.0 |
| ↳ ↳ **nutrition_per_100g** | object | ✅ 必須 | 100gあたり栄養情報 | {"calories": 156.0, "protein": 12.0} |
| ↳ ↳ **calculated_nutrition** | object | ✅ 必須 | 計算済み栄養情報 | 詳細栄養価 |
| ↳ ↳ **source_db** | string | ✅ 必須 | データソース | "mynetdiary_api" |
| ↳ ↳ **calculation_notes** | array | ✅ 必須 | 計算注記 | ["Scaled from 100g..."] |
| ↳ **total_nutrition** | object | ✅ 必須 | 料理の総栄養価 | 栄養情報 |
| ↳ **calculation_metadata** | object | ✅ 必須 | 計算メタデータ | {"ingredient_count": 2, ...} |
| **total_nutrition** | object | ✅ 必須 | 総栄養価 | - |
| ↳ **calories** | number | ✅ 必須 | 総カロリー（kcal） | 423.93 |
| ↳ **protein** | number | ✅ 必須 | 総タンパク質（g） | 28.33 |
| ↳ **fat** | number | ✅ 必須 | 総脂質（g） | 0.0 |
| ↳ **carbs** | number | ✅ 必須 | 総炭水化物（g） | 0.0 |
| **ai_model_used** | string | ✅ 必須 | 使用AIモデル | "google/gemma-3-27b-it" |
| **match_rate_percent** | number | ✅ 必須 | 栄養検索マッチ率（%） | 100.0 |
| **search_method** | string | ✅ 必須 | 検索方法 | "elasticsearch" |

## 🎯 分析機能の特徴

### デュアル入力対応パイプライン

#### 画像分析パイプライン
1. **Phase 1 - 画像認識** (Phase1Component):
   - DeepInfra Gemma 3-27B Vision Model
   - 構造化された料理・食材・重量推定
   - 高精度な信頼度スコア計算

#### 音声分析パイプライン ⭐ **NEW**
1. **Phase 1 - 音声認識** (Phase1SpeechComponent):
   - Google Cloud Speech-to-Text v2 API
   - 高精度音声認識（英語対応）
   - DeepInfra Gemma 3-27B NLU処理
   - 音声→テキスト→料理・食材・重量抽出

#### 共通処理パイプライン
2. **Phase 2 - 栄養検索** (AdvancedNutritionSearchComponent):
   - Word Query API統合 (Elasticsearch)
   - 高速・高精度な栄養データベース検索
   - 94-100% マッチ率達成

3. **Phase 3 - 栄養計算** (NutritionCalculationComponent):
   - 重量ベース栄養価算出
   - カロリー・マクロ栄養素計算
   - 料理別・全体統計

### 決定性制御

- **温度パラメータ**: 0.0 (完全決定的) - 1.0 (創造的)
- **シードパラメータ**: 再現性確保のための固定値
- **結果安定性**: 95-100% 一貫性

## 📊 パフォーマンス

### 画像分析
- **平均処理時間**: 12-18秒/画像
- **料理認識精度**: 95%以上
- **栄養検索精度**: 94-100% マッチ率
- **API料金**: 約0.15-0.23円/回

### 音声分析 ⭐ **NEW**
- **平均処理時間**: 15-25秒/音声（10-60秒音声）
- **音声認識精度**: 95%以上 (Google Cloud STT v2)
- **料理抽出精度**: 90%以上 (Gemma 3-27B NLU)
- **栄養検索精度**: 94-100% マッチ率
- **API料金**: 約0.41円/回 (10秒音声の場合)

## 🔧 技術仕様

### サポートモデル

#### Vision Models（画像分析用）
- `google/gemma-3-27b-it` (デフォルト)
- `Qwen/Qwen2.5-VL-32B-Instruct`
- `meta-llama/Llama-3.2-90B-Vision-Instruct`

#### Text Models（音声NLU処理用）
- `google/gemma-3-27b-it` (デフォルト)
- その他DeepInfra対応テキストモデル

### 音声認識対応言語
- **英語**: `en-US` (米国) **← 強く推奨・最高精度**
- **その他言語**: サポート予定

### 対応音声フォーマット
- **推奨**: WAV形式（24kHz対応）
- **最大サイズ**: 10MB
- **推奨音声長**: 10-60秒
- **品質**: 自動サンプルレート検出で最適化

## 🚨 エラーハンドリング

### HTTPステータスコード

- `200`: 分析成功
- `400`: リクエストエラー（パラメータ不正など）
- `413`: ファイルサイズ超過
- `422`: バリデーションエラー
- `500`: サーバーエラー（AI API接続エラー等）

### 一般的なエラー

#### 画像分析エラー
```json
{
  "detail": "temperature must be between 0.0 and 1.0"
}
```

#### 音声分析エラー
```json
{
  "detail": {
    "code": "UNSUPPORTED_AUDIO_FORMAT",
    "message": "Only WAV format is supported"
  }
}
```

## 💰 料金・パフォーマンス

### API利用料金

#### 画像分析
- **1回あたり**: 0.15-0.23円
- **月間3,000回**: 450-690円
- **内訳**: DeepInfra Vision API

#### 音声分析
- **1回あたり**: 約0.41円
- **月間1,000回**: 約410円
- **内訳**:
  - Google Cloud Speech-to-Text v2: 約0.4円
  - DeepInfra NLU処理: 約0.01円
  - 栄養検索・計算: 無料

## 📞 サポート・連絡先

- **プロジェクト**: meal_analysis_api_2
- **現在のブランチ**: voice_input1
- **Google Cloud プロジェクト**: new-snap-calorie (1077966746907)
- **デプロイURL**: https://meal-analysis-api-1077966746907.us-central1.run.app

## 🔄 更新履歴

### 2025-09-21 v2.1 Voice Input Enhancement ⭐ **NEW**
- **🎯 パラメータ統一**: 画像・音声分析のパラメータを完全統一
  - `optional_text`: 英語想定の追加テキスト情報
  - `temperature`: AI推論ランダム性制御 (0.0-1.0, デフォルト: 0.0)
  - `seed`: 再現性制御 (デフォルト: 123456)
  - `test_results_dir`: テスト結果保存先
- **🌐 言語設定**: 音声分析で`language_code="en-US"`をデフォルト化
- **📊 詳細レスポンス**: 実際のAPI構造と完全一致したPydanticモデル
- **🔧 Swagger更新**: 全パラメータが/docsに正確に反映
- **✅ テスト完了**: 新パラメータでの動作確認済み

### 2025-09-21 v2.1 Voice Input Support
- **🎤 音声入力機能追加**: POST `/api/v1/meal-analyses/voice` エンドポイント実装
- **🧠 Google Cloud Speech-to-Text v2統合**: 高精度音声認識
- **🔧 Phase1SpeechComponent**: 音声分析専用コンポーネント追加
- **💰 料金効率**: 約0.41円/回（10秒音声）

### 2025-09-19 v2.0 Clean Release
- **🎯 Pydantic警告完全解決**: 全警告ゼロ化
- **🔧 APIパラメータ改善**: `model_id` → `ai_model_id`変更
- **📊 性能向上**: 平均処理時間12-18秒、マッチ率100%達成

---

**🎊 APIは正常に稼働中です！**
高精度でクリーンな食事画像・音声分析と栄養計算機能をご利用いただけます。