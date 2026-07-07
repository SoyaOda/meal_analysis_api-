# FDC データベース月次更新 Runbook（barcode_api）

> ⚠️ **本番反映（GCS 上書き・Cloud Run 再起動/デプロイ）はユーザー明示指示が必要**。ステップ (0)〜(2) はローカル作業のみで安全に実行できるが、(3) 以降はユーザーの許可を得てから進めること。

運用 SSOT は [`../plans/current.md`](../plans/current.md)。本 doc はその「次の一手 queue ①」の実行手順。repo 全体規約は [`../../../ssot/DEVELOPMENT_OS.md`](../../../ssot/DEVELOPMENT_OS.md)。

## 前提

- FDC Branded Foods データは USDA により**月次**で更新される（[`../README.md`](../README.md) 「メンテナンススクリプト」節）。
- 本番正データは GCS: `gs://new-snap-calorie-data/fdc/fdc_barcode.db`。ローカル実体は `db/FoodData_Central/fdc_barcode.db`（リポジトリルート直下、~2.8GB、gitignore 対象）。
- Cloud Run コンテナは起動時に `entrypoint.sh` が GCS からこのファイルをダウンロードしてから API を起動する（ローカルに既に存在する場合はダウンロードをスキップ）。

## 手順

### (0) 事前: 現行 DB の世代確認

```bash
gsutil ls -l gs://new-snap-calorie-data/fdc/fdc_barcode.db
```

2026-07-08 時点の実測値（参考）:

```
2996285440  2025-12-14T13:09:34Z  gs://new-snap-calorie-data/fdc/fdc_barcode.db
```

サイズ（~2.8GB）と最終更新日時から鮮度を判断する。ローカルディスクは、ダウンロード用ZIP（[`../scripts/setup_fdc_database.py`](../scripts/setup_fdc_database.py) のコメントによれば CSV版で約453MB）+ 展開後 CSV 群 + 生成後 SQLite DB（~2.8GB）が同時に存在しうるため、**目安として 10GB 以上の空き容量**を確保すること（正確な必要量は未確認・実測推奨）。

### (1) ローカル再構築

```bash
# プロジェクトルートから実行
python apps/barcode_api/scripts/setup_fdc_database.py --force-download
```

内部処理（[`setup_fdc_database.py`](../scripts/setup_fdc_database.py) `run_setup()`）: 既存データ削除 → 最新 CSV ZIP のダウンロード URL を `fdc.nal.usda.gov/download-datasets/` から動的取得 → ダウンロード → 展開 → SQLite スキーマ作成（`food` / `branded_food` / `food_nutrient` / `nutrient` 四テーブル + インデックス）→ CSV → SQLite インポート（チャンク10,000行）→ `verify_database()` で各テーブル行数・バーコード付き商品数・主要栄養素IDの存在を出力。

所要時間: ZIPダウンロード + CSVインポートの合計時間は**未確認**（実行して実測すること。大容量CSV × 4テーブルのため相応の時間を見込む）。

完了後、`db/FoodData_Central/fdc_barcode.db` が新しい `publication_date` で再生成される。

### (2) ローカル検証

サーバーを起動:

```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8003 python -m apps.barcode_api.main
```

[`../../../test_barcodes/valid_barcodes.json`](../../../test_barcodes/valid_barcodes.json) に記載の既知 GTIN（例: `"000000016872"` = SUNRIDGE ZEN PARTY MIX, `fdc_available: true`）で lookup し、HTTP 200 と栄養値の非退化（`nutrients_per_100g.energy_kcal` が `null` でも `0` でもないこと）を確認する:

```bash
curl -s -X POST "http://localhost:8003/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "000000016872"}' | jq '.success, .data_source, .nutrients_per_100g.energy_kcal'
```

`test_barcodes/valid_barcodes.json` 内の他の `fdc_available: true` サンプルでも複数件（3〜5件目安）繰り返し、いずれも FDC ヒット（`data_source: "FDC"`）かつ非退化であることを確認する。あわせてヘルスチェックも確認:

```bash
curl -s http://localhost:8003/health | jq '.'
```

### (3) GCS へアップロード（⚠️ ユーザー許可必須・版付け推奨）

これまでの運用は `fdc_barcode.db` を直接上書きしており、直前世代のバックアップが存在しない。今回から**日付サフィックス付きオブジェクトを先に置いてから latest 名を差し替える**運用を推奨する:

```bash
# 1. 現行 latest を日付付きでバックアップ（初回のみ・今回の refresh 前に必ず実施）
gsutil cp gs://new-snap-calorie-data/fdc/fdc_barcode.db \
          gs://new-snap-calorie-data/fdc/fdc_barcode_20251214.db   # 現行 latest の実際の更新日（(0)で確認した値）を使う

# 2. 新しい DB を日付付きでアップロード
gsutil cp db/FoodData_Central/fdc_barcode.db \
          gs://new-snap-calorie-data/fdc/fdc_barcode_YYYYMMDD.db   # 今回の構築日

# 3. latest ポインタ（entrypoint.sh が参照する名前）を差し替え
gsutil cp gs://new-snap-calorie-data/fdc/fdc_barcode_YYYYMMDD.db \
          gs://new-snap-calorie-data/fdc/fdc_barcode.db
```

旧版（日付付きオブジェクト）は削除せずロールバック原資として残す。`entrypoint.sh` の `GCS_DB_PATH` 既定値は `gs://new-snap-calorie-data/fdc/fdc_barcode.db`（latest 名固定）であり、コード変更なしで版付け運用に対応できる。

### (4) Cloud Run 再起動/再デプロイ（⚠️ ユーザー許可必須）

DB のみの更新で足りる場合（[`../README.md`](../README.md) 「メンテナンススクリプト」節）:

```bash
gcloud run services update barcode-api --region=us-central1 --no-traffic
```

イメージ自体の更新も伴う場合は通常の [`../deploy.sh`](../deploy.sh) 経由:

```bash
# 開発環境
./apps/barcode_api/deploy.sh

# 本番環境
ENVIRONMENT=production ./apps/barcode_api/deploy.sh
```

### (5) 本番プローブ

```bash
curl -s https://barcode-api-1077966746907.us-central1.run.app/health | jq '.'
curl -s -X POST "https://barcode-api-1077966746907.us-central1.run.app/api/v1/barcode/lookup" \
  -H "Content-Type: application/json" \
  -d '{"gtin": "000000016872"}' | jq '.success, .data_source'
```

### (6) ロールバック

新 DB に問題が見つかった場合、latest ポインタを旧世代へ戻す:

```bash
gsutil cp gs://new-snap-calorie-data/fdc/fdc_barcode_<旧世代の日付>.db \
          gs://new-snap-calorie-data/fdc/fdc_barcode.db

gcloud run services update barcode-api --region=us-central1 --no-traffic
```

### (7) 記録

[`../plans/current.md`](../plans/current.md) の Session Log に、更新した世代（日付）・`verify_database()` が出力した各テーブル行数・バーコード付き商品数を追記する。

## `analyze_fdc_units.py` の再実行が必要になる条件

[`../data/fdc_unit_analysis.json`](../data/fdc_unit_analysis.json) は [`../scripts/analyze_fdc_units.py`](../scripts/analyze_fdc_units.py) が `db/FoodData_Central/fdc_barcode.db` の `branded_food.household_serving_fulltext` / `serving_size_unit` を走査して生成する単位・表記パターン分析結果。以下のいずれかに該当する場合、再実行を検討する:

- FDC 側の CSV スキーマ変更（列追加/削除、`branded_food` テーブル構造の変更）で `setup_fdc_database.py` のスキーマ定義との不整合が疑われる場合。
- 月次更新後、単位表記のバリエーション（体積/個数キーワードのパターン）が大きく変化したと疑われる場合（例: 新カテゴリの食品が大量追加された等）。

再実行:

```bash
python apps/barcode_api/scripts/analyze_fdc_units.py
```

出力は `data/fdc_unit_analysis.json` を上書きする。この JSON は git 追跡対象（`ssot/DATASETS.md` §3、`.gitignore` allowlist 施行済み 2026-07-08）であり、更新時は diff レビューを経ること。レビュー観点:

- 既存パターンカテゴリ（volume / count / weight / mixed / other）の件数分布が大きく変化していないか（`utils/unit_parser.py` / `utils/smart_unit_generator.py` の想定と乖離しないか、コードは do-not-touch のため差分のみ確認）。
- 新規の単位キーワードが出現していないか（将来のコード改修候補としてメモに残す。本 runbook の範囲ではコード修正はしない）。
