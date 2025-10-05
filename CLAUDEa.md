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

#### Barcode API (ポート 8003)

```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8003 python -m apps.barcode_api.main
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

### Barcode API (http://localhost:8003)

#### バーコード検索

```bash
curl -X POST "http://localhost:8003/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "000000016872"}'
```

#### キャッシュ統計確認

```bash
curl -X GET "http://localhost:8003/api/v1/barcode/cache-stats"
```

#### キャッシュクリア

```bash
curl -X DELETE "http://localhost:8003/api/v1/barcode/cache"
```

[Instruction]
apps に 2 つの API が実装されている。詳細を README.md を見て理解すること。

[命令]
md_files/barcode_spec_UDC.md と md_files/barcode_spec1.md に沿って実装をしたい。
## ✅ 実装が完了した部分

### FDC データベースセットアップ ✅

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

### FastAPI アプリケーション ✅

- **完了**: `apps/barcode_api/main.py` - FastAPI アプリケーション実装済み
- **完了**: API サーバー起動設定（ポート8003）
- **完了**: ヘルスチェックエンドポイント（`/health`, `/api/v1/barcode/health`）
- **完了**: データベース統計エンドポイント（`/api/v1/barcode/stats`）

### データモデル ✅

- **完了**: `apps/barcode_api/models/nutrition.py` - 17栄養素対応の詳細データモデル
  - MainNutrients（17栄養素）
  - ServingNutrients（1食分栄養素）
  - AlternativeNutrients（代替単位栄養素）
  - HouseholdServingInfo（家庭用単位情報）
  - ProductInfo（製品情報）
  - NutritionResponse（包括的レスポンス）

### ビジネスロジック ✅

- **完了**: `apps/barcode_api/services/fdc_service.py` - FDC データベース検索サービス
- **完了**: `apps/barcode_api/utils/unit_parser.py` - 単位解析・変換システム
- **完了**: 体積・重量・個数単位の解析・変換
- **完了**: 分数→小数変換
- **完了**: 食品密度推定による体積↔重量変換

### API エンドポイント ✅

- **完了**: `apps/barcode_api/api/barcode.py` - バーコード検索 API
- **完了**: `POST /api/v1/barcode/lookup` エンドポイント
- **完了**: バーコードから fdc_id 検索ロジック
- **完了**: 17栄養素情報取得・整形ロジック
- **完了**: 多単位栄養価計算（100g、1食分、カップ、大さじ等）

### データ検索・処理 ✅

- **完了**: 重複 GTIN 最新版選択（publication_date 使用）
- **完了**: サービングサイズ計算ロジック
- **完了**: 17栄養素抽出（Energy, Protein, Fat, Carbohydrate + 13追加栄養素）
- **完了**: household_serving_fulltext解析

### エラーハンドリング・ログ ✅

- **完了**: 包括的エラーハンドリング
- **完了**: 構造化ログ機能
- **完了**: ヘルスチェック機能

### パフォーマンス ✅

- **完了**: 平均応答時間8ms（206万件データから検索）
- **完了**: SQLiteインデックス最適化

### ドキュメント・保守 ✅

- **完了**: `apps/barcode_api/README.md` - 包括的ドキュメント
- **完了**: メンテナンススクリプト手順
- **完了**: cron設定例・運用ガイド
- **完了**: トラブルシューティング

### GTIN 正規化処理 ✅

- **完了**: `apps/barcode_api/services/gtin_service.py` - GTIN正規化・検証サービス
- **完了**: UPC-12 → EAN-13 変換
- **完了**: チェックデジット検証（UPC-12/EAN-13）
- **完了**: GTIN 正規化（ゼロ埋め、文字除去）
- **完了**: エッジケース処理（空白除去、ハイフン処理、英数字混在拒否）
- **完了**: 国コード判定機能
- **完了**: 包括的テストデータセット（`test_barcodes/`）
- **完了**: パフォーマンステスト（平均0.01ms/call）

### キャッシュシステム ✅

- **完了**: `apps/barcode_api/services/cache_service.py` - TTLCacheベースキャッシュシステム
- **完了**: スレッドセーフなキャッシュ操作（RLock使用）
- **完了**: キャッシュ統計追跡（ヒット数、ミス数、ヒット率）
- **完了**: ヘルスチェック機能
- **完了**: シングルトンパターンによるグローバルインスタンス管理
- **完了**: TTL設定（デフォルト3600秒）
- **完了**: 最大エントリ数制限（デフォルト1000）
- **完了**: FDCサービス統合（自動キャッシュ保存・取得）
- **完了**: キャッシュ統計API（`GET /api/v1/barcode/cache-stats`）
- **完了**: キャッシュクリアAPI（`DELETE /api/v1/barcode/cache`）

### Open Food Facts フォールバック連携 ✅

- **完了**: `apps/barcode_api/services/off_service.py` - Open Food Facts APIクライアント
- **完了**: FDC未ヒット時の自動フォールバック検索機能
- **完了**: OFF栄養素データの正規化・変換処理
- **完了**: HTTPエラー・タイムアウト処理
- **完了**: シングルトンパターンによるサービス管理
- **完了**: ヘルスチェック機能（Nutella製品でテスト）
- **完了**: 非同期HTTPクライアント（httpx使用）
- **完了**: データソース識別（`"data_source": "Open Food Facts"`）

### スマート単位生成システム ✅ (v3.0.0)

- **完了**: `apps/barcode_api/utils/smart_unit_generator.py` - 食品タイプ別単位生成エンジン
- **完了**: `NutrientUnitOption` データモデル（全17栄養素対応）
- **完了**: `unit_options` フィールドをNutritionResponseに追加
- **完了**: 食品タイプ自動判定（liquid, baked_goods, snacks, cereal, candy）
- **完了**: 食品タイプ別密度推定（0.3〜1.0）による体積→重量変換
- **完了**: メーカー指定サービング優先（`is_primary: true`）
- **完了**: 家庭用サービング情報解析・統合
- **完了**: 推奨単位自動生成（cup, oz, piece等）
- **完了**: 重複除去・優先順位ソート機能
- **完了**: エラー時フォールバック単位（1g, 100g）
- **完了**: 英語表記出力（国際対応）
- **完了**: FDC・OFF両サービス統合済み

## ❌ 未実装の部分

### 現在未実装の項目はありません

すべての主要機能が実装完了しています：
- ✅ FDCデータベース検索（プライマリ）
- ✅ Open Food Factsフォールバック（セカンダリ）
- ✅ スマート単位生成システム
- ✅ 17栄養素対応
- ✅ TTLキャッシュシステム
- ✅ 英語表記出力

[実装の上でのポイント]
・一度に複数の Script を実装しないこと。Script ごとに機能の Test をして実装した内容がきちんと動くことを確認して次の機能の実装に移ること。
・こちらで作業する必要がある部分や必要な情報があれば、その都度どのようにしたらいいか教えて。
