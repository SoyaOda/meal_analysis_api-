# 食事分析API v2.0 - 統合アーキテクチャ

統合コンポーネントベースパイプラインによる高度な食事分析システム

## 🏗️ アーキテクチャ概要

```
apps/meal_analysis_api (ポート8001)
    ├── 音声分析エンドポイント (/api/v1/meal-analyses/voice)
    ├── 画像分析エンドポイント (/api/v1/meal-analyses/complete)
    └── ローカル通信 ↓

apps/word_query_api (ポート8002)
    ├── 栄養検索API (/api/v1/nutrition/suggest)
    └── Elasticsearch接続 ↓

栄養データベース (Elasticsearch)
    └── MyNetDiary統合データベース
```

## 🚀 クイックスタート

### 前提条件
- Python 3.8+
- Elasticsearch (ローカル実行中)
- Google Cloud SDK (音声認識用・オプション)
- DeepInfra API キー (NLU処理 + 音声認識用)

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定
```bash
export GOOGLE_CLOUD_PROJECT=new-snap-calorie
export DEEPINFRA_API_KEY=your_deepinfra_api_key
export ELASTICSEARCH_URL=http://localhost:9200
```

### 3. APIサーバーの起動

#### Word Query API (ポート8002)
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8002 python -m apps.word_query_api.main
```

#### Meal Analysis API (ポート8001)
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 GOOGLE_CLOUD_PROJECT=new-snap-calorie PORT=8001 python -m apps.meal_analysis_api.main
```

## 📚 API エンドポイント

### Meal Analysis API (http://localhost:8001)

#### 音声入力による食事分析

##### DeepInfra Whisper使用（デフォルト・推奨）
```bash
curl -X POST "http://localhost:8001/api/v1/meal-analyses/voice" \
  -F "audio_file=@test-audio/lunch_detailed.wav" \
  -F "speech_service=deepinfra_whisper" \
  -F "whisper_model=openai/whisper-large-v3-turbo" \
  -F "language_code=en-US" \
  -F "temperature=0.0" \
  -F "user_context=lunch analysis"
```

##### Google Speech-to-Text使用（従来方式）
```bash
curl -X POST "http://localhost:8001/api/v1/meal-analyses/voice" \
  -F "audio_file=@test-audio/lunch_detailed.wav" \
  -F "speech_service=google" \
  -F "language_code=en-US" \
  -F "user_context=lunch analysis"
```

**音声認識パラメータ**:
- `speech_service` (str): 音声認識サービス (`deepinfra_whisper` | `google`, デフォルト: `deepinfra_whisper`)
- `whisper_model` (str): DeepInfra Whisperモデル (`openai/whisper-large-v3-turbo` | `openai/whisper-large-v3` | `openai/whisper-base`)
- `language_code` (str): 言語コード (`en-US` | `ja-JP` など)
- `temperature` (float): AI推論ランダム性 (0.0-1.0)

#### 画像入力による食事分析
```bash
curl -X POST "http://localhost:8001/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=dinner analysis"
```

#### ヘルスチェック
```bash
curl "http://localhost:8001/health"
```

### Word Query API (http://localhost:8002)

#### 栄養情報検索
```bash
curl "http://localhost:8002/api/v1/nutrition/suggest?q=chicken&limit=5"
```

## 🧩 コンポーネント構成

### 共有コンポーネント (`shared/components/`)

1. **Phase1Component**
   - 画像から食事情報を抽出
   - Google Vision API統合

2. **Phase1SpeechComponent**
   - 音声から食事情報を抽出
   - **音声認識**: Google Cloud Speech-to-Text v2 または DeepInfra Whisper API
   - **NLU処理**: DeepInfra LLM (gemma-3-27b-it)
   - **コスト最適化**: DeepInfra Whisperで99%コスト削減

3. **AdvancedNutritionSearchComponent**
   - ローカルWord Query API連携
   - 7階層検索戦略
   - 代替名サポート (chickpeas ↔ garbanzo beans)

4. **NutritionCalculationComponent**
   - 栄養価計算とカロリー推定
   - 食材量の自動推定

### 専用コンポーネント (`apps/word_query_api/`)

5. **ElasticsearchNutritionSearchComponent**
   - 直接Elasticsearch検索
   - MyNetDiary データベース統合

6. **FuzzyIngredientSearchComponent**
   - 5階層ファジーマッチング
   - Jaro-Winkler類似度アルゴリズム

## 📁 プロジェクト構造

```
meal_analysis_api_2/
├── apps/
│   ├── meal_analysis_api/          # メイン食事分析API
│   │   ├── main.py
│   │   └── endpoints/
│   │       ├── meal_analysis.py    # 画像分析エンドポイント
│   │       └── voice_analysis.py   # 音声分析エンドポイント
│   └── word_query_api/             # 栄養検索API
│       ├── main.py
│       └── endpoints/
│           └── nutrition_search.py
├── shared/
│   ├── components/                 # 共有コンポーネント
│   ├── models/                     # データモデル定義
│   ├── config/                     # 設定管理
│   └── utils/                      # ユーティリティ関数
├── test-audio/                     # テスト用音声ファイル
├── test_images/                    # テスト用画像ファイル
└── analysis_results/               # 分析結果保存
```

## 🔧 設定ファイル

### 主要設定 (`shared/config/settings.py`)
- Elasticsearch接続設定
- API キー管理
- ログレベル設定
- ファジーマッチング閾値

## 📊 テストデータ

### 音声ファイル
- `test-audio/lunch_detailed.wav` - 昼食の詳細説明
- `test-audio/breakfast_detailed.mp3` - 朝食の詳細説明

### 画像ファイル
- `test_images/food1.jpg` - 料理画像サンプル

## 🧪 テスト実行例

### 音声分析テスト

#### DeepInfra Whisper使用（デフォルト・推奨）
```bash
curl -X POST "http://localhost:8001/api/v1/meal-analyses/voice" \
  -F "audio_file=@test-audio/lunch_detailed.wav" \
  -F "speech_service=deepinfra_whisper" \
  -F "whisper_model=openai/whisper-large-v3-turbo" \
  -F "temperature=0.0" \
  -F "user_context=昼食の栄養分析"
```

#### Google Speech-to-Text使用
```bash
curl -X POST "http://localhost:8001/api/v1/meal-analyses/voice" \
  -F "audio_file=@test-audio/lunch_detailed.wav" \
  -F "speech_service=google" \
  -F "user_context=昼食の栄養分析"
```

### 画像分析テスト
```bash
# food1.jpgを使用した画像分析
curl -X POST "http://localhost:8001/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=夕食の栄養分析"
```

## 🔍 デバッグとモニタリング

### ログ確認
```bash
# Meal Analysis APIログ
tail -f logs/meal_analysis_api.log

# Word Query APIログ
tail -f logs/word_query_api.log
```

### APIステータス確認
```bash
# 両APIの稼働状況確認
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## 🚧 開発ガイドライン

### 新しいコンポーネントの追加
1. `shared/components/`に新しいコンポーネントを作成
2. `BaseComponent`を継承
3. `process()`メソッドを実装
4. `shared/components/__init__.py`に追加

### API エンドポイントの追加
1. 適切な`endpoints/`ディレクトリに新しいルーターを作成
2. `main.py`でルーターを登録
3. 必要に応じて新しいモデルを`shared/models/`に追加

## 📈 パフォーマンス最適化

### 推奨設定
- **並列処理**: APIクライアントの並行リクエスト有効
- **キャッシュ**: Elasticsearchクエリ結果のキャッシュ
- **ログレベル**: 本番環境ではINFOレベル以上
- **音声認識**: DeepInfra Whisper使用を推奨（コスト・速度最適化）

### 音声認識バックエンド比較
| サービス | コスト（分あたり） | 処理速度 | 精度 | 推奨用途 |
|----------|-------------------|----------|------|----------|
| Google Speech-to-Text V2 | $0.021 | 標準 | 高 | 企業システム |
| DeepInfra Whisper large-v3-turbo | $0.0002 | 高速 | 高 | **推奨**・コスト重視 |
| OpenAI Whisper | $0.006 | 標準 | 高 | バランス重視 |
| Local Whisper | $0 | 低速 | 中-高 | 完全プライベート |

### モニタリング指標
- API応答時間
- 栄養検索マッチ率
- Elasticsearch接続状況
- 音声認識精度
- API使用コスト

## 🎙️ 音声認識統合詳細

### サポートされているWhisperモデル

#### DeepInfra API（推奨）
- `openai/whisper-large-v3-turbo` - 最速・高精度（$0.0002/分）
- `openai/whisper-large-v3` - 高精度・標準速度
- `openai/whisper-base` - 軽量・高速

#### OpenAI API
- `whisper-1` - 公式OpenAI API ($0.006/分)

#### ローカル実行
- `tiny`, `base`, `small`, `medium`, `large-v3`, `large-v3-turbo`
- 英語専用: `tiny.en`, `base.en`, `small.en`, `medium.en`

### 実装アーキテクチャ
```
Phase1SpeechComponent
├── GoogleSpeechService (従来)
│   └── Google Cloud Speech-to-Text V2
└── WhisperSpeechService (新規)
    ├── DeepInfra API ← 推奨
    ├── OpenAI API
    └── Local Whisper
```

### 移行ガイド
1. **テスト環境**: `use_whisper=true` で DeepInfra Whisper をテスト
2. **コスト比較**: 音声分析頻度に応じたコスト削減効果を確認
3. **本番適用**: 精度とコストを検証後、デフォルト設定を変更

## 🔒 セキュリティ

- API キーの環境変数管理
- CORS設定の適切な制限
- 入力ファイルサイズ制限
- ログでの機密情報マスキング

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 🤝 コントリビューション

1. フォークしてブランチを作成
2. 変更を実装
3. テストを実行
4. プルリクエストを作成

---

**最終更新**: 2025-09-24
**バージョン**: v2.2.0 - DeepInfra Whisper統合
**アーキテクチャ**: マルチバックエンド音声認識対応・統合コンポーネントベースパイプライン

### 🆕 v2.2.0 新機能
- ✨ **DeepInfra Whisper API統合**: 99%コスト削減（$0.021 → $0.0002/分）
- 🔄 **マルチバックエンド対応**: Google Speech-to-Text V2 ⟷ DeepInfra Whisper 切り替え可能
- ⚡ **処理速度向上**: DeepInfra Whisper large-v3-turbo で15%高速化
- 🎛️ **モデル選択機能**: API経由でWhisperモデルを動的選択可能