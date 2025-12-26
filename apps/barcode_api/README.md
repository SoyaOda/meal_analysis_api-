# Barcode API - FoodData Central (FDC) バーコード検索API

FoodData Central (FDC) データベースとOpen Food Factsを使用したバーコード検索APIです。多様な単位での栄養価表示とスマートな単位生成に対応しています。

## 本番環境

Cloud Runは複数のURLを提供します。どちらのURLでも同じサービスにアクセス可能です：

| URL | 形式 |
|-----|------|
| `https://barcode-api-1077966746907.us-central1.run.app` | プロジェクト番号ベース（Flutter側で使用） |
| `https://barcode-api-x27n75dvja-uc.a.run.app` | リビジョンID ベース |

```bash
# ヘルスチェック
curl https://barcode-api-1077966746907.us-central1.run.app/health

# バーコード検索
curl -X POST "https://barcode-api-1077966746907.us-central1.run.app/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "0016000275287"}'
```

## 概要

このAPIは以下の機能を提供します：

- **バーコード検索**: GTIN/UPCコードから製品と栄養情報を取得
- **多単位栄養価表示**: 100g、1食分、カップ、個数など多様な単位での栄養価計算
- **スマート単位生成**: 食品タイプに応じて適切な単位オプションを自動生成
- **拡張栄養素**: 基本4栄養素から17種類の栄養素に拡張
- **家庭用単位解析**: "0.25 cup", "2 cookies"などの表記を自動解析
- **フォールバック検索**: FDC未ヒット時にOpen Food Factsで補完

## ディレクトリ構成

```
apps/barcode_api/
├── README.md               # このファイル
├── main.py                 # FastAPIアプリケーションメイン
├── Dockerfile              # Cloud Run用Dockerファイル
├── deploy.sh               # Cloud Runデプロイスクリプト
├── entrypoint.sh           # コンテナ起動スクリプト（GCSからDB取得）
├── api/
│   ├── __init__.py
│   └── barcode.py          # バーコード検索APIエンドポイント
├── models/
│   ├── __init__.py
│   └── nutrition.py        # 栄養情報データモデル（NutrientUnitOption追加）
├── services/
│   ├── __init__.py
│   ├── fdc_service.py      # FDCデータベース検索サービス
│   ├── gtin_service.py     # GTIN正規化・検証サービス
│   ├── off_service.py      # Open Food Facts APIサービス
│   └── cache_service.py    # TTLキャッシュサービス
├── utils/
│   ├── __init__.py
│   ├── unit_parser.py      # 単位解析・変換ユーティリティ
│   └── smart_unit_generator.py  # スマート単位生成エンジン
├── data/                   # 設定・参照データ
│   ├── unit_conversions.json      # 単位変換定義
│   ├── food_density_data.json     # 食品密度データ
│   └── fdc_unit_analysis.json     # FDCデータ分析結果
└── scripts/                # 管理・メンテナンススクリプト
    ├── setup_fdc_database.py      # FDCデータベース構築スクリプト
    └── analyze_fdc_units.py        # FDCデータ単位パターン分析
```

## ローカル起動方法

```bash
# プロジェクトルートから実行
PYTHONPATH=/path/to/meal_analysis_api_2 PORT=8003 python -m apps.barcode_api.main
```

**必要条件**:
- FDCデータベース: `db/FoodData_Central/fdc_barcode.db`（約2.8GB）
- データベースがない場合は `scripts/setup_fdc_database.py` を実行

## Cloud Run デプロイ

### 事前準備

1. **FDCデータベースをGCSにアップロード**（初回のみ、約5-10分）:
```bash
# GCSバケットを作成（既存の場合はスキップ）
gsutil mb -l us-central1 gs://new-snap-calorie-data

# FDCデータベースをアップロード
gsutil cp db/FoodData_Central/fdc_barcode.db gs://new-snap-calorie-data/fdc/fdc_barcode.db
```

2. **実行権限を付与**:
```bash
chmod +x apps/barcode_api/deploy.sh
chmod +x apps/barcode_api/entrypoint.sh
```

3. **GCSアクセス権限を付与**（初回のみ）:
```bash
# Cloud Runサービスアカウントにストレージ読み取り権限を付与
gsutil iam ch serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com:roles/storage.objectViewer gs://new-snap-calorie-data

# プロジェクト番号の確認方法
gcloud projects describe new-snap-calorie --format="value(projectNumber)"
```

### デプロイ実行

```bash
# 開発環境（デフォルト: min-instances=0、コールドスタートあり）
./apps/barcode_api/deploy.sh

# 本番環境（min-instances=1、常時起動、コールドスタートなし）
ENVIRONMENT=production ./apps/barcode_api/deploy.sh

# 本番環境 + CORS制限
ENVIRONMENT=production ALLOWED_ORIGINS="https://yourapp.com" ./apps/barcode_api/deploy.sh
```

### デプロイ設定

| 環境 | サービス名 | min-instances | max-instances | メモリ | CPU | concurrency |
|------|-----------|---------------|---------------|--------|-----|-------------|
| development | barcode-api-dev | 0 | 5 | 4Gi | 2 | 80 |
| production | barcode-api | 1 | 3 | 4Gi | 2 | 80 |

### Cloud Runアーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                   Cloud Run                          │
│  ┌───────────────────────────────────────────────┐  │
│  │  entrypoint.sh                                │  │
│  │  1. GCSからFDCデータベースをダウンロード      │  │
│  │  2. /app/db/FoodData_Central/fdc_barcode.db  │  │
│  │  3. Pythonアプリケーション起動               │  │
│  └───────────────────────────────────────────────┘  │
│                        ↓                            │
│  ┌───────────────────────────────────────────────┐  │
│  │  Barcode API (FastAPI)                        │  │
│  │  - バーコード検索                             │  │
│  │  - 栄養情報取得                               │  │
│  │  - Open Food Factsフォールバック              │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
           ↑                              ↑
    ┌──────┴──────┐               ┌───────┴───────┐
    │ Cloud Storage│               │ Open Food Facts│
    │ (FDC DB)     │               │ (Fallback API) │
    └─────────────┘               └────────────────┘
```

## APIエンドポイント

### バーコード検索

```bash
curl -X POST "http://localhost:8003/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "000000016872", "include_all_nutrients": false}'
```

**レスポンス例**:
```json
{
  "success": true,
  "gtin": "000000016872",
  "product": {
    "fdc_id": 1055419,
    "description": "SUNRIDGE, ZEN PARTY MIX",
    "brand_owner": "Edward Leeds & Company",
    "ingredients": "..."
  },
  "serving_info": {
    "serving_size": 30.0,
    "serving_unit": "g"
  },
  "nutrients_per_100g": {
    "energy_kcal": 533.0,
    "protein_g": 16.67,
    "fat_g": 36.67,
    "carbohydrate_g": 36.67
  },
  "unit_options": [
    {
      "unit_id": "1serving",
      "display_name": "1 serving (30.0g)",
      "is_primary": true,
      "energy_kcal": 159.9
    }
  ],
  "data_source": "FDC"
}
```

### ヘルスチェック

```bash
curl -X GET "http://localhost:8003/health"
curl -X GET "http://localhost:8003/api/v1/barcode/health"
```

### データベース統計

```bash
curl -X GET "http://localhost:8003/api/v1/barcode/stats"
```

## メンテナンススクリプト

### 1. FDCデータベース構築・更新

**ファイル**: `scripts/setup_fdc_database.py`

**目的**: FDCの最新データをダウンロードし、SQLiteデータベースを構築・更新

**実行方法**:
```bash
# 初回セットアップまたは強制更新
python apps/barcode_api/scripts/setup_fdc_database.py --force-download

# 通常の更新チェック（既存データがある場合はスキップ）
python apps/barcode_api/scripts/setup_fdc_database.py
```

**推奨実行頻度**:
- **月次**: FDC Branded Foodsデータは毎月更新されるため
- **自動化**: cronジョブまたはCI/CDパイプラインで実行

**データベース更新後のCloud Run反映**:
```bash
# GCSのデータベースを更新
gsutil cp db/FoodData_Central/fdc_barcode.db gs://new-snap-calorie-data/fdc/fdc_barcode.db

# Cloud Runインスタンスを再起動（新しいDBをダウンロード）
gcloud run services update barcode-api --region=us-central1 --no-traffic
```

### 2. FDCデータ分析

**ファイル**: `scripts/analyze_fdc_units.py`

**目的**: FDCデータの単位・表記パターンを分析し、単位解析精度向上のためのデータを生成

**実行方法**:
```bash
python apps/barcode_api/scripts/analyze_fdc_units.py
```

## データファイルの管理

### 1. 単位変換定義

**ファイル**: `data/unit_conversions.json`

**内容**: 体積・重量・個数単位の変換係数と正規化ルール

### 2. 食品密度データ

**ファイル**: `data/food_density_data.json`

**内容**: 体積→重量変換のための食品カテゴリ別密度データ

### 3. FDCデータベース

**場所**: `db/FoodData_Central/fdc_barcode.db`（プロジェクトルート）

**サイズ**: 約2.8GB

**内容**: USDA FoodData Central Branded Foodsデータ

## トラブルシューティング

### よくある問題

1. **データベースファイルが見つからない**
   ```
   FileNotFoundError: FDCデータベースファイルが見つかりません
   ```
   → `setup_fdc_database.py`を実行してデータベースを構築

2. **Cloud Run起動が遅い**
   - 初回起動時はGCSからDBダウンロード（約60-90秒）
   - `DEPLOY_MODE=performance` で常時起動を推奨

3. **メモリ不足エラー**
   - Cloud Runのメモリを4Gi以上に設定
   - SQLiteクエリの最適化を検討

4. **バーコードが見つからない（404）**
   - FDCデータベースには様々な形式のGTINが保存されている（11桁、12桁、13桁、14桁）
   - v3.3.0以降は自動的に複数バリエーションで検索
   - 例: アプリが`0016000275287`（13桁）を送信 → DB内の`16000275287`（11桁）でヒット

5. **Open Food Factsタイムアウト**
   - 旧API（`world.openfoodfacts.org/api/v0`）はタイムアウト問題あり
   - v3.3.0以降は新API（`world.openfoodfacts.net/api/v2`）を使用

### パフォーマンス最適化

1. **データベースインデックス**
   - GTINインデックス: `branded_food.gtin_upc`
   - 栄養素インデックス: `food_nutrient(fdc_id, nutrient_id)`

2. **キャッシュ戦略**
   - TTLCache（1時間）でバーコード検索結果をキャッシュ
   - Open Food Facts結果もキャッシュ

## 開発・テスト

### GTIN正規化テスト
```bash
python test_barcodes/comprehensive_gtin_test.py
```

### APIエンドポイントテスト
```bash
# FDCデータ
curl -X POST "http://localhost:8003/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "000000016872"}'

# Open Food Factsフォールバック
curl -X POST "http://localhost:8003/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "5449000000996"}'
```

## スマート単位生成システム

### unit_options フィールド

APIレスポンスに`unit_options`フィールドが含まれ、食品タイプに応じた適切な単位での栄養価が自動生成されます。

### 食品タイプ別単位生成

| タイプ | キーワード例 | 推奨単位 | 密度 |
|--------|-------------|---------|------|
| Liquid | juice, milk, soda | ml, cup, fl oz | 1.0 |
| Baked Goods | cookie, bread, cake | piece, slice | 0.4 |
| Snacks | chips, nuts, pretzels | g, cup, piece | 0.3 |
| Cereal | cereal, granola, oats | cup, g | 0.4 |
| Candy | candy, chocolate, gummy | piece, g | 0.8 |

### Open Food Facts フォールバック

FDCデータベースで見つからない場合、自動的にOpen Food Facts APIで検索:

- **APIエンドポイント**: `https://world.openfoodfacts.net/api/v2`（v3.3.0以降）
- **データソース表示**: `"data_source": "Open Food Facts"`
- **対応製品**: 世界中の食品（特に欧州・日本製品に強い）
- **キャッシュ**: TTLCache（1時間）
- **タイムアウト**: 10秒

## ライセンス・データソース

- **FoodData Central**: USDA提供のパブリックドメインデータ
- **Open Food Facts**: オープンデータベース（ODbL）

## 更新履歴

- **v1.0.0**: 基本的なバーコード検索機能
- **v2.0.0**: 多単位栄養価表示機能追加
- **v2.1.0**: 拡張栄養素対応（17種類）
- **v3.0.0**: スマート単位生成システム、Open Food Factsフォールバック、TTLキャッシュ追加
- **v3.1.0**: Cloud Runデプロイ対応、GCS連携追加
- **v3.2.0**: Cloud Runデプロイ完了、本番環境URL追加、GCS権限設定手順追加
- **v3.3.0** (2025-12-26): GTINバリエーション対応、Open Food Facts API v2移行
  - FDCデータベース検索で複数GTIN形式対応（11/12/13/14桁）
  - Open Food Facts APIを`world.openfoodfacts.org/api/v0`から`world.openfoodfacts.net/api/v2`に移行（タイムアウト問題解決）