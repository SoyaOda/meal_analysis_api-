# Phase: MAINTENANCE（2026-07-08 OS 制定）

**最初に読む**: 本ファイル → [`docs/DATA_REFRESH_RUNBOOK.md`](../docs/DATA_REFRESH_RUNBOOK.md) → [`README.md`](../README.md) → [`ssot/DEVELOPMENT_OS.md`](../../../ssot/DEVELOPMENT_OS.md)（repo 全体ガバナンス）。

`barcode_api` は本番稼働中の主成果物の一つ（`ssot/DEVELOPMENT_OS.md` §1）。精度 PDCA は回さず、**本番安定運用 + データ鮮度維持**が主目的。

- **本番 URL**: `https://barcode-api-1077966746907.us-central1.run.app`（プロジェクト番号ベース、Flutter 側で使用）／`https://barcode-api-x27n75dvja-uc.a.run.app`（リビジョンIDベース）
- **現行バージョン**: v3.3.0（2025-12-26、GTINバリエーション対応・OFF API v2移行）— `README.md` 更新履歴より

## 🔴 本番アラート（2026-07-08 検出・FDC refresh 実行時に発覚）

FDC refresh（ユーザー指示）を実行しようとして、本番側の複数ブロッカーを検出。**refresh は未完（本番反映は一切していない）**。要ユーザー対応（GCP コンソール）:

1. **barcode 本番が無応答**: `/api/v1/barcode/health` と `/` が **HTTP 000（40s タイムアウト・無応答）**。Cloud Run ログ上は **本日 2026-07-08 00:06:31 UTC に正常起動（"Application startup complete" + health 200）**したのが最後で、以降ログが途絶。直近3日に ERROR/CRITICAL ログは無し。→ アプリのクラッシュではなく **cold-start / 起動タイムアウト系**の疑い（entrypoint が起動時に GCS から 2.8GB DB を DL する設計 → 再 DL がタイムアウトすると 000 になりうる）。要 Cloud Run 調査（リビジョン `barcode-api-00018-x2z`・min-instances 実値・起動 timeout・GCS DL 所要）。
2. **本番 GCS バケットへの書き込み不可**: `gs://new-snap-calorie-data/fdc/` への `gsutil cp` が **403「The billing account for the owning project is disabled in state absent」**。読み取り（objectViewer）は可。→ バケット所有プロジェクトの billing 状態を確認要（`new-snap-calorie` 自体は `billingEnabled: true`・billing account `01DA39-E816D2-F72DEC` は `open: true` なので、バケット所有プロジェクトが別 or リンク不整合の可能性）。
3. **ローカルディスク逼迫**: 空き 13GB/99%。FDC フルビルド（459MB zip 展開 + 2.8GB SQLite 構築）はピーク ~10GB で**安全マージン不足**。→ 数GB の空け（例: 未追跡の `web_scraping/` 6.4GB 等）が必要。

参考: freeform 本番（同一プロジェクト番号 1077966746907）は `/health` 正常 → プロジェクト全体の Cloud Run billing は生存。barcode 固有のダウンと、バケット書き込みの billing ブロックは別事象の可能性。
最新 FDC データ自体は入手可能（`FoodData_Central_csv_2026-04-30.zip`, 459MB・現行 prod 2025-12-14 版より約4ヶ月新しい）。上記3点が解消され次第 `docs/DATA_REFRESH_RUNBOOK.md` の手順で実行可能。

## 🟢 本番の現状（authoritative）

- **デプロイ構成**: Cloud Run 2環境。`barcode-api-dev`（min-instances=0, max=5, 4Gi/2CPU, concurrency=80, コールドスタートあり）／`barcode-api`（production, min-instances=1, max=3, 同スペック）。デプロイは `apps/barcode_api/deploy.sh`（`ENVIRONMENT=production` で本番切替）。
- **データ経路**: リクエスト → FDC Branded Foods SQLite（GTIN 11/12/13/14桁バリエーション検索）→ 未ヒット時のみ Open Food Facts v2 API (`world.openfoodfacts.net/api/v2`) にフォールバック → TTLCache（1時間）。
- **FDC DB**: 本番正 = `gs://new-snap-calorie-data/fdc/fdc_barcode.db`。**確認済み（2026-07-08 `gsutil ls -l`）: 2,996,285,440 bytes (2.79 GiB), 最終更新 2025-12-14T13:09:34Z**。ローカル実体はこのマシンには現状なし（`db/FoodData_Central/` に csv 展開のみ残置、DB ファイル自体は未生成）。Cloud Run はコンテナ起動時に `entrypoint.sh` が GCS から `/app/db/FoodData_Central/fdc_barcode.db` へダウンロードしてから `gunicorn` 起動。
- **リビジョン運用**: `deploy.sh` は Dockerfile.optimized をビルド→push→`gcloud run deploy`。DB 更新のみの場合は README 記載の `gcloud run services update barcode-api --region=us-central1 --no-traffic` でコンテナ再起動しGCSから再DL（詳細は runbook）。

## Non-Negotiables

- **本番操作・deploy・commit/push はユーザー明示指示が必要**（`ssot/DEVELOPMENT_OS.md` §6 準拠）。
- **FDC DB 差し替え**は `docs/DATA_REFRESH_RUNBOOK.md` の手順（構築→ローカル検証→版付きGCSアップロード→Cloud Run再起動→本番プローブ→ロールバック手段確保）を経ずに行わない。
- **参照データ3本**（`data/unit_conversions.json` / `data/food_density_data.json` / `data/fdc_unit_analysis.json`）は git 追跡方針（`ssot/DATASETS.md` §3, 2026-07-08〜）。変更は diff レビュー対象。
  - ✅ **施行済み（2026-07-08 同日）**: `.gitignore` に `!apps/barcode_api/data/*.json` の allowlist 例外を追加し3ファイルをステージ済み（コミットはユーザー批准待ち）。
- **no-fallback 原則**: 既存コードは想定外時に例外を投げて止める設計（`fdc_service.py` / `off_service.py`）。ドキュメント整備に伴うコード変更は行わない。

## 既知のギャップ / リスク

- **テストスイート無し**: `test_barcodes/` はアドホックスクリプト（`comprehensive_gtin_test.py` 等）のみ。CI/pytest 化されていない。
- **FDC 月次 refresh が手動**: cron/CI 化されておらず、実行漏れのリスクがある。
- **GCS DB のバージョニング/ロールバック未整備**: `fdc_barcode.db` が単一オブジェクト名で上書き運用されており、直前世代のバックアップが存在しない（今回のrunbookで版付け運用を提案）。
- **OFF v2 フォールバックの網羅検証不足**: v2 移行（2025-12-26）後の系統的な回帰確認記録が見当たらない。

## 次の一手 queue（優先順）

1. **FDC 月次 refresh の初回 runbook 実走**（DB 鮮度確認から。現行 GCS DB は 2025-12-14 更新＝2026-07-08 時点で約7ヶ月経過）。
2. **最小スモークテスト整備**: `test_barcodes/valid_barcodes.json` を使った lookup 回帰（既知 GTIN 数件で HTTP 200 + 栄養非退化を機械的に確認できる形に）。
3. **GCS DB の版付け提案**: `fdc_barcode_YYYYMMDD.db` を先に置いてから `fdc_barcode.db`（latest ポインタ）を差し替える運用へ移行（旧版はロールバック原資として残す）。
4. **freeform DB レーン P3（FDC Branded Foods）との棲み分け設計**: freeform 側は `apps/freeform_usda_meal_analysis_api/plans/current.md` の「DBレーン」P3（FDC Branded Foods, 0.6B/dim1024 なら ~2GB）で barcode_api との重複・共用可否検討が保留中。相互参照して設計する。

## Pending owner decisions

- FDC refresh 自動化方式（手動継続 / cron / CI）— `ssot/DEVELOPMENT_OS.md` §11-3 と同一の未決事項。

## Session Log

| Date | Session | 作業内容 |
|------|---------|---------|
| 2026-07-08 | fdc-refresh-blocked | FDC refresh 着手 → 本番3ブロッカー検出で中断（本番反映なし）: ①barcode 本番 HTTP 000 ダウン ②GCS 書込 403 billing disabled ③local disk 13GB逼迫。最新データ2026-04-30は入手可。詳細は「🔴 本番アラート」節。 |
| 2026-07-08 | os-founding | plans/docs/CLAUDE.md 新設・参照データ git 追跡化・runbook 制定（コード変更なし）。`plans/current.md` / `docs/DATA_REFRESH_RUNBOOK.md` / `CLAUDE.md` / `AGENTS.md` を新設し、`README.md` 先頭に SSOT ポインタを追加。GCS 上の FDC DB 鮮度（2025-12-14, 2.79GiB）を実測確認。参照データ3JSONの git 追跡方針は `ssot/DATASETS.md` で決定済みだが `.gitignore` 側の allowlist 追加は別レーン（root do-not-touch）として未実施であることを明記。 |
