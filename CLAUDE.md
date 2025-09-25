# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

必ず serena MCP が日本語で対応すること！
日本語で応答すること！

### 3. API サーバーの起動

#### Word Query API (ポート 8002)

```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8002 python -m apps.word_query_api.main
```

#### Meal Analysis API (ポート 8001)

```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 GOOGLE_CLOUD_PROJECT=new-snap-calorie PORT=8001 python -m apps.meal_analysis_api.main
```

## 📚 API エンドポイント

### Meal Analysis API (http://localhost:8001)

#### 音声入力による食事分析

```bash
curl -X POST "http://localhost:8001/api/v1/meal-analyses/voice" \
  -F "audio_file=@test-audio/lunch_detailed.wav" \
  -F "user_context=lunch analysis"
```

#### 画像入力による食事分析

```bash
curl -X POST "http://localhost:8001/api/v1/meal-analyses/complete" \
  -F "image=@test_images/food1.jpg" \
  -F "user_context=dinner analysis"
```

[Instruction]
apps に 2 つの API が実装されている。詳細を README.md を見て理解すること。

[命令]
md_files/barcode_spec_UDC.md と md_files/barcode_spec1.md に沿って実装をしたい。
[未実装の部分]

[実装が完了した部分]

## ✅ FDC データベースセットアップ

- **FDCDatabaseSetup** クラス実装完了 (`apps/barcode_api/scripts/setup_fdc_database.py`)
- 453MB の FDC データ自動ダウンロード機能
- SQLite データベース構築（正しいスキーマ）
- 2,064,912 件の food レコード
- 1,977,398 件の branded_food（バーコード付き商品）
- 26,805,037 件の food_nutrient（栄養データ）
- 477 件の nutrient（栄養素マスタ）
- インデックス設定済み（gtin_upc 検索最適化）
- データ整合性確認機能
- 強制ダウンロードオプション
- 進行状況表示機能

## ✅ 依存関係

- `requirements.txt`に必要パッケージ追加済み（requests, pandas）

[未実装の部分]

## ❌ バーコード API 実装

### 1. FastAPI アプリケーション

- **未実装**: `apps/barcode_api/main.py` - メイン API アプリケーション
- **未実装**: API サーバー起動設定

### 2. データモデル

- **未実装**: `apps/barcode_api/models/nutrition.py` - 栄養情報データモデル
- **未実装**: `apps/barcode_api/models/barcode.py` - バーコード関連モデル

### 3. ビジネスロジック

- **未実装**: `apps/barcode_api/services/fdc_service.py` - FDC データベース検索サービス
- **未実装**: `apps/barcode_api/services/gtin_service.py` - GTIN 正規化処理
- **未実装**: `apps/barcode_api/services/cache_service.py` - キャッシュ管理

### 4. API エンドポイント

- **未実装**: `apps/barcode_api/api/barcode.py` - バーコード検索 API
- **未実装**: `POST /api/v1/barcode/lookup` エンドポイント
- **未実装**: バーコードから fdc_id 検索ロジック
- **未実装**: 栄養情報取得・整形ロジック

### 5. GTIN 処理機能

- **未実装**: UPC-12 → EAN-13 変換
- **未実装**: チェックデジット検証
- **未実装**: GTIN 正規化（0 埋め処理）

### 6. データ検索・処理

- **未実装**: 重複 GTIN 最新版選択（publication_date 使用）
- **未実装**: サービングサイズ計算ロジック
- **未実験**: 主要栄養素抽出（Energy=1008, Fat=1004, Carbohydrate=1005, Protein=1003）

### 7. キャッシュシステム

- **未実装**: インメモリキャッシュ（cachetools.TTLCache）
- **未実装**: Redis 対応（オプション）

### 8. Open Food Facts 連携

- **未実装**: FDC 未ヒット時のフォールバック検索
- **未実装**: OFF API 連携
- **未実装**: レートリミット管理

### 9. エラーハンドリング・ログ

- **未実装**: 包括的エラーハンドリング
- **未実装**: ログ機能
- **未実装**: ヘルスチェックエンドポイント

[実装の上でのポイント]
・一度に複数の Script を実装しないこと。Script ごとに機能の Test をして実装した内容がきちんと動くことを確認して次の機能の実装に移ること。
・こちらで作業する必要がある部分や必要な情報があれば、その都度どのようにしたらいいか教えて。
