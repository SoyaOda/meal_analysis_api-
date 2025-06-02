# 一括食事分析スクリプト (run_all_food_analysis.sh)

## 概要

このスクリプトは、food1.jpg〜food5.jpg までの全ての画像に対して Phase1 と Phase2 の分析を自動実行し、結果を 1 つのテキストファイルにまとめて保存します。

## 機能

### ✨ 主な機能

- **自動一括処理**: food1.jpg〜food5.jpg までの 5 つの画像を順次処理
- **Phase1 & Phase2 実行**: 各画像に対して完全な 2 段階分析を実行
- **統合結果出力**: 全ての結果をタイムスタンプ付きの 1 つの txt ファイルに保存
- **詳細なログ記録**: 実行時間、成功/失敗状況、エラーログを記録
- **カラフルな進捗表示**: 実行状況が一目でわかる色付きログ出力

### 🛡️ エラーハンドリング

- **事前チェック**: サーバー起動状況と画像ファイル存在確認
- **詳細エラーログ**: 失敗時のエラー内容を結果ファイルに記録
- **部分失敗対応**: 一部の画像が失敗しても他の画像処理を継続
- **自動クリーンアップ**: 一時ファイルの自動削除

### 📊 出力内容

- **実行サマリー**: 処理画像数、成功率、総実行時間
- **個別結果**: 各画像の Phase1 と Phase2 の完全な JSON 結果
- **性能メトリクス**: 各段階の実行時間と成功/失敗状況

## 使用方法

### 前提条件

1. **サーバーが起動していること**

   ```bash
   # サーバー起動コマンド
   export USDA_API_KEY="vSWtKJ3jYD0Cn9LRyVJUFkuyCt9p8rEtVXz74PZg" && export GOOGLE_APPLICATION_CREDENTIALS="/Users/odasoya/meal_analysis_api /service-account-key.json" && export GEMINI_PROJECT_ID=recording-diet-ai-3e7cf && export GEMINI_LOCATION=us-central1 && export GEMINI_MODEL_NAME=gemini-2.5-flash-preview-05-20 && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **画像ファイルが存在すること**
   - `test_images/food1.jpg`
   - `test_images/food2.jpg`
   - `test_images/food3.jpg`
   - `test_images/food4.jpg`
   - `test_images/food5.jpg`

### 実行方法

```bash
# スクリプトの実行
./run_all_food_analysis.sh
```

### 出力ファイル

実行すると、以下の形式のファイルが生成されます：

```
all_food_analysis_results_YYYYMMDD_HHMMSS.txt
```

例: `all_food_analysis_results_20250602_130517.txt`

## 出力ファイルの構造

### 1. ヘッダー情報

```
# 食事分析API - 全食品画像一括分析結果
# Generated: 2025年 6月 2日 月曜日 13時05分17秒 JST
# Script: run_all_food_analysis.sh
# Images processed: food1.jpg - food5.jpg
```

### 2. 分析サマリー

```
================================================================================
ANALYSIS SUMMARY
================================================================================
Total Images Processed: 5 (food1.jpg - food5.jpg)
Successful Analyses: 5
Failed Analyses: 0
Total Execution Time: 397.0s
Success Rate: 100.0%
```

### 3. 個別分析結果

各画像について以下の情報が記録されます：

```
================================================================================
FOOD1.JPG ANALYSIS RESULTS - SUCCESS
================================================================================
Image: test_images/food1.jpg
Analysis Time: 2025年 6月 2日 月曜日 13時06分53秒 JST
Phase 1 Duration: 16.0s (Success: true)
Phase 2 Duration: 80.0s (Success: true)

--- PHASE 1 RESULTS ---
{完全なPhase1 JSON結果}

--- PHASE 2 RESULTS ---
{完全なPhase2 JSON結果}
```

## 結果の確認方法

### 全体結果の確認

```bash
# 結果ファイル全体を表示
cat all_food_analysis_results_YYYYMMDD_HHMMSS.txt

# ファイルサイズの確認
ls -lh all_food_analysis_results_*.txt
```

### サマリーのみの確認

```bash
# 先頭20行（サマリー部分）のみ表示
head -20 all_food_analysis_results_YYYYMMDD_HHMMSS.txt
```

### 特定画像の結果確認

```bash
# food3.jpgの結果のみ抽出
sed -n '/FOOD3.JPG ANALYSIS RESULTS/,/FOOD4.JPG ANALYSIS RESULTS/p' all_food_analysis_results_YYYYMMDD_HHMMSS.txt
```

### エラー内容の確認

```bash
# 失敗した分析の検索
grep -A 10 -B 5 "FAILED" all_food_analysis_results_YYYYMMDD_HHMMSS.txt
```

## 性能情報

### 典型的な実行時間

- **Food1 (Caesar Salad)**: Phase1: 16s, Phase2: 80s
- **Food2 (Fish & Spaghetti)**: Phase1: 18s, Phase2: 67s
- **Food3 (Complex Meal)**: Phase1: 20s, Phase2: 65s
- **Food4 (Japanese Meal)**: Phase1: 14s, Phase2: 67s
- **Food5 (Simple Dish)**: Phase1: 8s, Phase2: 42s

### 総実行時間

約 6〜7 分（397 秒前後）

## トラブルシューティング

### よくある問題

1. **サーバーが起動していない**

   ```
   [ERROR] Server is not running or not healthy
   ```

   → サーバーを起動してから再実行

2. **画像ファイルが見つからない**

   ```
   [ERROR] Missing image files:
   ```

   → test_images/ディレクトリに必要な画像があることを確認

3. **Phase2 でタイムアウト**
   → サーバーの負荷状況を確認し、時間をおいて再実行

### ログの確認

実行時の詳細ログは、一時的に以下に保存されます：

- `temp_analysis_YYYYMMDD_HHMMSS/`（自動削除される）

エラーが発生した場合は、スクリプトを修正して一時ファイルを保持するよう変更できます。

## カスタマイズ

### 画像範囲の変更

```bash
# スクリプト内の以下の行を変更
for i in {1..5}; do    # 1〜5を任意の範囲に変更
```

### タイムアウト設定

```bash
# test_english_phase2_v2.pyのタイムアウト設定を調整可能
```

### 出力形式の変更

`append_results_to_file`関数を編集することで、出力形式をカスタマイズできます。
