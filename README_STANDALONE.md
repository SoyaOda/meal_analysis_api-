# 🚀 スタンドアロン食事分析実行ガイド

## 概要

`test_standalone_analysis.py` は、**API サーバーを立ち上げることなく**、直接 `MealAnalysisPipeline` を実行できるシンプルなスタンドアロンスクリプトです。

**Google Gemini AI** と **Elasticsearch ベース栄養検索システム**を使用して、`test_images/food1.jpg` の食事画像を分析し、料理・食材の識別と栄養データベース照合を行います。

## 🌟 特徴

- ✅ **API サーバー不要**: 直接パイプラインを実行
- ✅ **シンプル実行**: `python test_standalone_analysis.py` だけで完了
- ✅ **高速処理**: Elasticsearch による高性能栄養検索
- ✅ **詳細結果表示**: 料理・食材・栄養価・処理時間を見やすく表示
- ✅ **自動保存**: 分析結果を JSON ファイルに自動保存

## 🔧 前提条件

### 1. 必要なサービスの起動

スタンドアロン実行でも、以下のサービスが起動している必要があります：

#### Elasticsearch サーバーの起動

```bash
# Elasticsearchを起動（バックグラウンド実行）
elasticsearch-8.10.4/bin/elasticsearch &
```

**確認方法**:

```bash
# Elasticsearchの動作確認
curl -X GET "localhost:9200/_cluster/health?pretty"
```

正常な場合、以下のような応答が返ります：

```json
{
  "cluster_name": "elasticsearch",
  "status": "yellow",
  "number_of_nodes": 1
}
```

### 2. 環境設定

以下の環境変数が設定されている必要があります（スクリプト内で自動設定されますが、確認推奨）：

```bash
# Google Cloud認証
export GOOGLE_APPLICATION_CREDENTIALS="/Users/odasoya/meal_analysis_api_2/service-account-key.json"

# Gemini AI設定
export GEMINI_PROJECT_ID="recording-diet-ai-3e7cf"
export GEMINI_LOCATION="us-central1"
export GEMINI_MODEL_NAME="gemini-2.5-flash-preview-05-20"
```

### 3. 必要なファイル

- ✅ `test_images/food1.jpg` - 分析対象の画像ファイル
- ✅ `service-account-key.json` - Google Cloud 認証キー
- ✅ Elasticsearch インデックス `nutrition_db` - 栄養データベース

## 🚀 実行方法

### 基本実行

```bash
python test_standalone_analysis.py
```

**これだけです！** 他に何も必要ありません。

## 📊 実行結果例

```
🚀 食事分析スタンドアロンテスト v2.0
📝 APIサーバー不要の直接パイプライン実行

🚀 スタンドアロン食事分析テスト開始
📁 分析対象: test_images/food1.jpg
📊 画像サイズ: 96,595 bytes
🔍 MIMEタイプ: image/jpeg
🔧 検索方法: Elasticsearch (高性能)
============================================================

✅ 分析が完了しました！
============================================================
📋 分析結果サマリー (ID: 8f0bd76b)
----------------------------------------
🍽️  検出された料理: 3個
   1. Caesar Salad (信頼度: 0.95)
   2. Pasta Salad (信頼度: 0.90)
   3. Iced Tea (信頼度: 0.98)

🥕 検出された食材: 3個
   1. Caesar Salad (信頼度: 0.95)
   2. Pasta Salad (信頼度: 0.90)
   3. Iced Tea (信頼度: 0.98)

🔍 栄養データベース照合結果:
   - マッチ件数: 15件
   - 成功率: 100.0%
   - 検索方法: elasticsearch_lemmatized_enhanced

⏱️  処理統計:
   - 処理時間: 24.24秒
   - 総料理数: 3個
   - 総食材数: 12個

🍎 暫定栄養価 (概算):
   - カロリー: 600 kcal
   - タンパク質: 90.0 g
   - 炭水化物: 330.0 g
   - 脂質: 180.0 g

💾 結果保存先: analysis_results/api_quick_results_20250614_142605/meal_analysis_8f0bd76b.json

============================================================
🎯 スタンドアロン分析テスト完了！
✅ テスト成功！
```

## 📁 出力ファイル

実行後、以下の場所に詳細な分析結果が保存されます：

```
analysis_results/
└── api_quick_results_YYYYMMDD_HHMMSS/
    └── meal_analysis_[ID].json
```

**保存内容**:

- Phase1 分析結果（検出された料理・食材）
- 栄養データベース検索結果
- 処理時間・統計情報
- 暫定栄養価計算結果

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. Elasticsearch に接続できない

**エラー**: `ConnectionError: Connection refused`

**解決方法**:

```bash
# Elasticsearchが起動しているか確認
curl -X GET "localhost:9200/"

# 起動していない場合は起動
elasticsearch-8.10.4/bin/elasticsearch &
```

#### 2. 画像ファイルが見つからない

**エラー**: `❌ エラー: 画像ファイルが見つかりません: test_images/food1.jpg`

**解決方法**:

```bash
# ファイルの存在確認
ls -la test_images/food1.jpg

# ファイルがない場合は、適切な画像ファイルを配置
```

#### 3. Google Cloud 認証エラー

**エラー**: `google.auth.exceptions.DefaultCredentialsError`

**解決方法**:

```bash
# サービスアカウントキーのパス確認
ls -la service-account-key.json

# 環境変数の設定確認
echo $GOOGLE_APPLICATION_CREDENTIALS
```

#### 4. 栄養データベースインデックスが見つからない

**エラー**: `Index 'nutrition_db' not found`

**解決方法**:

```bash
# インデックスの作成
python create_elasticsearch_index.py
```

## 🆚 他のテストスクリプトとの比較

| スクリプト                              | 実行方法                                       | API サーバー | 対象画像       | 用途               |
| --------------------------------------- | ---------------------------------------------- | ------------ | -------------- | ------------------ |
| `test_standalone_analysis.py`           | `python test_standalone_analysis.py`           | **不要**     | food1.jpg 固定 | **シンプルテスト** |
| `test_advanced_elasticsearch_search.py` | `python test_advanced_elasticsearch_search.py` | 必要         | 複数画像       | 高度なテスト       |
| `run_analysis_standalone.py`            | `python run_analysis_standalone.py [画像パス]` | **不要**     | 任意           | 柔軟な実行         |

## 💡 使用場面

- ✅ **開発・デバッグ時**: API サーバーを立ち上げずに素早くテスト
- ✅ **デモ・プレゼン時**: シンプルな実行でシステムの動作を確認
- ✅ **パフォーマンス測定**: 純粋なパイプライン処理時間の測定
- ✅ **CI/CD 環境**: 自動テストでの基本動作確認

## 🔗 関連ドキュメント

- [メイン README](README.md) - 全体的なシステム概要
- [API サーバー実行方法](README.md#🖥-サーバー起動) - API サーバーを使った実行方法
- [高度なテスト方法](README.md#🧪-テストの実行) - より詳細なテスト実行方法
