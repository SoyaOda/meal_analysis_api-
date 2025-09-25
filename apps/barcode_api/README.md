# Barcode API - FoodData Central (FDC) バーコード検索API

FoodData Central (FDC) データベースとOpen Food Factsを使用したバーコード検索APIです。多様な単位での栄養価表示とスマートな単位生成に対応しています。

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
├── api/
│   ├── __init__.py
│   └── barcode.py          # バーコード検索APIエンドポイント
├── models/
│   ├── __init__.py
│   └── nutrition.py        # 栄養情報データモデル（NutrientUnitOption追加）
├── services/
│   ├── __init__.py
│   ├── fdc_service.py      # FDCデータベース検索サービス
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

## API起動方法

```bash
# プロジェクトルートから実行
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8003 python -m apps.barcode_api.main
```

## APIエンドポイント

### バーコード検索

```bash
curl -X POST "http://localhost:8003/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "000000016872", "include_all_nutrients": false}'
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

**cron設定例**:
```bash
# 毎月1日午前2時に実行
0 2 1 * * cd /path/to/project && python apps/barcode_api/scripts/setup_fdc_database.py --force-download
```

### 2. FDCデータ分析

**ファイル**: `scripts/analyze_fdc_units.py`

**目的**: FDCデータの単位・表記パターンを分析し、単位解析精度向上のためのデータを生成

**実行方法**:
```bash
python apps/barcode_api/scripts/analyze_fdc_units.py
```

**推奨実行頻度**:
- **FDCデータ更新後**: 新しいデータパターンを検出するため
- **四半期**: 単位解析の精度改善のため

**出力ファイル**:
- `apps/barcode_api/data/fdc_unit_analysis.json`

## データファイルの管理

### 1. 単位変換定義

**ファイル**: `data/unit_conversions.json`

**内容**: 体積・重量・個数単位の変換係数と正規化ルール

**更新タイミング**: 新しい単位パターンが発見された場合

### 2. 食品密度データ

**ファイル**: `data/food_density_data.json`

**内容**: 体積→重量変換のための食品カテゴリ別密度データ

**更新タイミング**: より正確な密度データが入手可能になった場合

### 3. FDCデータ分析結果

**ファイル**: `data/fdc_unit_analysis.json`

**内容**: FDCデータの単位パターン分析結果（自動生成）

**更新タイミング**: `analyze_fdc_units.py`実行時に自動更新

## 運用監視

### ログファイル

- **場所**: `barcode_api.log`（実行ディレクトリに生成）
- **レベル**: INFO以上
- **監視項目**:
  - データベース接続エラー
  - バーコード検索失敗
  - 単位解析エラー

### データベース統計監視

定期的にデータベース統計APIを呼び出し、以下の値を監視：

```json
{
  "food_count": 2064912,
  "branded_food_count": 1977398,
  "food_nutrient_count": 26805037,
  "nutrient_count": 477,
  "products_with_barcode": 1977398
}
```

## トラブルシューティング

### よくある問題

1. **データベースファイルが見つからない**
   ```
   FileNotFoundError: FDCデータベースファイルが見つかりません
   ```
   → `setup_fdc_database.py`を実行してデータベースを構築

2. **単位解析が失敗する**
   - `data/unit_conversions.json`の設定を確認
   - `analyze_fdc_units.py`を実行して新パターンを調査

3. **メモリ不足エラー**
   - 大容量データ処理時に発生可能
   - チャンクサイズを調整（`setup_fdc_database.py`内のCHUNK_SIZE）

### パフォーマンス最適化

1. **データベースインデックス**
   - GTINインデックス: `branded_food.gtin_upc`
   - 栄養素インデックス: `food_nutrient(fdc_id, nutrient_id)`

2. **キャッシュ戦略**
   - よく検索されるバーコードの結果をキャッシュ
   - 単位変換結果のメモ化

## 開発・テスト

### 単体テスト
```bash
# 単位解析テスト
python -m pytest apps/barcode_api/tests/test_unit_parser.py

# FDCサービステスト
python -m pytest apps/barcode_api/tests/test_fdc_service.py
```

### 統合テスト
```bash
# APIエンドポイントテスト
curl -X POST "http://localhost:8003/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "000000016872", "include_all_nutrients": false}'
```

## ライセンス・データソース

- **FoodData Central**: USDA提供のパブリックドメインデータ
- **API**: プロジェクト固有のライセンスに従う

## 新機能：スマート単位生成システム

### unit_options フィールド

v3.0.0から、APIレスポンスに`unit_options`フィールドが追加されました。これにより、食品タイプに応じた適切な単位での栄養価が自動生成されます。

```json
{
  "success": true,
  "gtin": "000000016872",
  "unit_options": [
    {
      "unit_id": "1serving",
      "display_name": "1 serving (30.0g)",
      "unit_type": "serving",
      "is_primary": true,
      "equivalent_weight_g": 30.0,
      "energy_kcal": 159.9,
      "protein_g": 5.0,
      "fat_g": 11.0,
      "carbohydrate_g": 11.0
    },
    {
      "unit_id": "1g",
      "display_name": "1 gram",
      "unit_type": "weight",
      "is_primary": false,
      "equivalent_weight_g": 1.0,
      "energy_kcal": 5.33,
      "protein_g": 0.167
    },
    {
      "unit_id": "1cup",
      "display_name": "1 cup",
      "unit_type": "volume",
      "is_primary": false,
      "equivalent_weight_g": 236.588,
      "energy_kcal": 1261.0
    }
  ]
}
```

### 食品タイプ別単位生成ロジック

SmartUnitGeneratorが以下の食品タイプを自動判定し、適切な単位を生成します：

#### 1. Liquid（液体系食品）
- **判定キーワード**: juice, milk, water, soda, drink, beverage, soup, etc.
- **推奨単位**: ml, fl oz, cup, liter
- **密度**: 1.0 (水ベース)
- **例**: 1 cup = 236.6g

#### 2. Baked Goods（焼き菓子）
- **判定キーワード**: cookie, cracker, cake, bread, muffin, etc.
- **推奨単位**: piece, slice, cookie, cracker
- **密度**: 0.4
- **例**: 1 cup = 94.6g, 1 piece = 推定15g

#### 3. Snacks（スナック菓子）
- **判定キーワード**: chips, popcorn, nuts, pretzels, etc.
- **推奨単位**: g, oz, cup, piece
- **密度**: 0.3
- **例**: 1 cup = 71g, 1 piece = 推定20g

#### 4. Cereal（シリアル）
- **判定キーワード**: cereal, granola, oats, muesli, etc.
- **推奨単位**: cup, g, oz
- **密度**: 0.4
- **例**: 1 cup = 94.6g

#### 5. Candy（キャンディ）
- **判定キーワード**: candy, chocolate, gummy, etc.
- **推奨単位**: piece, g, oz
- **密度**: 0.8
- **例**: 1 piece = 推定5g

### 単位生成の優先順位

1. **メーカー指定サービング**: `is_primary: true`でマーク
2. **家庭用サービング情報**: household_serving_fulltextから解析
3. **食品タイプ推奨単位**: 上記ロジックで自動生成
4. **基本単位**: 1g, 100g（全食品共通）

### 体積単位の重量換算

体積単位（cup, fl oz等）は密度推定により重量換算されます：

```python
# 食品タイプ別密度
density_estimates = {
    "liquid": 1.0,      # 液体（水ベース）
    "snacks": 0.3,      # スナック菓子
    "cereal": 0.4,      # シリアル類
    "candy": 0.8,       # キャンディ類
    "default": 0.6      # デフォルト
}

# 1 US cup = 236.588ml × 密度 = グラム換算
cup_weight_g = 236.588 * density
```

### Open Food Facts フォールバック

FDCデータベースで見つからない場合、自動的にOpen Food Facts APIで検索します：

- **データソース表示**: `"data_source": "Open Food Facts"`
- **単位生成**: 同様のロジックで適切な単位を生成
- **キャッシュ**: TTLCache（1時間）で高速化

## 更新履歴

- **v1.0.0**: 基本的なバーコード検索機能
- **v2.0.0**: 多単位栄養価表示機能追加
- **v2.1.0**: 拡張栄養素対応（17種類）
- **v3.0.0**: スマート単位生成システム、Open Food Factsフォールバック、TTLキャッシュ追加