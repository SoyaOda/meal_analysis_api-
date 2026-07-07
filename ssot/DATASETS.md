# DATASETS.md — データセット / Ground Truth 台帳（SSOT）

**updated: 2026-07-08** / ガバナンス規則は `ssot/DEVELOPMENT_OS.md` §8。
ローカル実在の機械検証は `ssot/datasets.json` + `python scripts/verify_datasets.py`（/os-audit に組込）。

## Provenance tiers

| Tier | 意味 | 採用判定での扱い |
|------|------|------------------|
| **T1** | weighed（物理計量 GT） | tie-break の正。calibration fit は in-domain T1 のみ |
| **T2** | expert-estimate（専門家推定） | eval proxy として有効。fit 不可 |
| **T3** | scraped / derived（レシピ意図分量等） | recognition / density-prior / サニティ限定。**E13 の代替不可**（lessons `20260606_e14_*` / DRIVE_DATASET_INVENTORY 結論） |
| **T4** | model-estimate（モデル推定 GT） | **tie-break 禁止**。トレンド参照のみ（frozen-50 の pro 優位アーティファクトの教訓） |

## 1. Eval 画像セット（PDCA rotation）

| 名称 | 場所（repo root 相対） | n | GT | 用途 | 再構築 | git |
|------|------------------------|---|----|------|--------|-----|
| **frozen-50** | `test_images/` + `test_images/images_label_with_nutrition/*.json` | 50 | **T4**（GPT-5-pro 推定） | rotation（in-dist トレンドのみ・tie-break 禁止） | 手作業 curated（スクリプト無し）。**GT ラベル JSON は git 追跡**（2026-07-08〜） | 画像 ignore / ラベル追跡 |
| **NVReal-104** | `test_images_nvreal/` (185MB) | 104 | **T1** weighed | rotation | `scripts/build_nutritionverse_evalset.py` — **要 手動 Kaggle DL**（`data/nutritionverse_real/` に展開済み前提） | ignore |
| **N5k** | `test_images_n5k/` (14MB) | 250（split: test_100 / fit_150） | **T1** weighed | rotation（test_100）+ calibration fit（fit_150, disjoint） | `scripts/build_nutrition5k_evalset.py` — 公開 GCS 匿名（⚠️ gsutil パスがハードコード） | ignore |
| **JFB-100** | `test_images_jfb/` (244MB, ~1000枚) | 100 使用 | **T2** expert-estimate | rotation（実ドメイン proxy）。**E14 fit 禁止** | `scripts/build_jfb_evalset.py` — 公開 S3, CC-BY-4.0, 認証不要 | ignore |
| **E13**（未収集） | `test_images_e13*`（予定） | 目標 200-500 | **T1** weighed in-domain | E14 fit + blind holdout（本命） | `scripts/ingest_e13_collection.py`（infra 完成・物理計量が律速） | ignore 予定 |

- splits（git 追跡・immutable）: `apps/freeform_usda_meal_analysis_api/evals/splits/{dev_40_v1, holdout_10_v1, jfb_test_100, n5k_test_100, n5k_fit_150}.txt`
- **sealed holdout 温存**: JFB の未使用 ~900 枚・N5k の未使用分は「未見 holdout」として温存し、rotation セット saturation 時の refresh 原資にする（DEVELOPMENT_OS §8）。
- rotation の baseline 値・実行コマンドの正典 = `apps/freeform_usda_meal_analysis_api/docs/EXTERNAL_TESTSET_PLAN_20260603.md`。

## 2. 検索・栄養 DB 資産（freeform serving に必須）

| 資産 | 場所 | サイズ | 再構築 | git |
|------|------|--------|--------|-----|
| FAISS index（serving, 0.6B/dim1024/13,564vec） | `apps/freeform_usda_meal_analysis_api/data/faiss/usda_index_full.faiss` | 55.6MB | `scripts/build_index_with_nutrition.py`（⚠️ FNDDS 元データの所在は §4 リスク参照） | ignore（Docker image + migration bundle で移送） |
| USDA metadata（栄養値） | `.../data/faiss/usda_metadata.json` | — | 同上 | ignore |
| 栄養正規化辞書 | `.../data/normalized_portions.json` | 8MB | — | ignore（migration 必須資産） |
| BM25 index | `.../data/faiss/usda_bm25_index/`（bm25s 形式 dir） | — | `scripts/build_bm25_index.py` | ignore |
| 8B index（バックアップ） | `.../data/faiss/usda_index_full.8b.faiss` | 222MB | build script（E5 撤退時の残置） | ignore |
| A/B 実験 index 群（7 変種） | `.../data/faiss_ab/` | 739MB | `scripts/build_embedding_ab_index.py` | ignore |

## 3. barcode_api 資産

| 資産 | 場所 | 再構築 / 更新 | git |
|------|------|----------------|-----|
| FDC Branded Foods DB | ローカル `db/FoodData_Central/fdc_barcode.db`（~2.8GB）+ **本番正 = `gs://new-snap-calorie-data/fdc/fdc_barcode.db`** | `apps/barcode_api/scripts/setup_fdc_database.py`（USDA 公式 DL）。**月次更新 SOP = `apps/barcode_api/docs/DATA_REFRESH_RUNBOOK.md`** | ignore |
| 参照データ 3 本（unit_conversions / food_density_data / fdc_unit_analysis） | `apps/barcode_api/data/*.json` | `scripts/analyze_fdc_units.py`（fdc_unit_analysis）/ 手動 curated（他 2 本） | **追跡**（2026-07-08〜。fresh clone で壊れないため） |
| Open Food Facts | 外部 API（fallback, world.openfoodfacts.net/api/v2） | — | — |

## 4. リスク台帳（fresh-machine / 消失リスク）

1. **NVReal は自律再構築不可**（手動 Kaggle DL 前提）— 消失時は Kaggle 再取得が必要。
2. **build_nutrition5k_evalset.py の gsutil パスがハードコード**（`/Users/odasoya/google-cloud-sdk/bin/gsutil`）— 他マシンで要修正。
3. **FAISS rebuild の FNDDS 元データ所在が未確認**（`usda_metadata.json` 併設だが CSV 原本の登記なし）— 実運用は Docker image / migration bundle が正。次回 index 再構築時に原本パスを本 doc に追記すること。
4. **frozen-50 は T4**（GPT-5-pro 推定 GT）— tie-break 禁止を厳守。
5. **E13 未収集** — 本命 lever のデータが存在しない（product 側依存）。
6. **Drive-only 資産は repo から検証不可**（下記 §5）。
7. 旧重複 FAISS が `test_scripts/query_system/data/` に 444MB 残置（2025-10 版・SSOT ではない・削除候補）。
8. `VLM_CACHE_DIR`（opt-in の VLM 凍結キャッシュ）は台帳外の一時資産 — A/B 分離実験の再現はキャッシュではなく手順で担保する。

## 5. 外部・Drive 資産（参照のみ・T3 中心）

正典 = `apps/freeform_usda_meal_analysis_api/docs/DRIVE_DATASET_INVENTORY_20260607.md` / `ENGLISH_RECIPE_SOURCE_SURVEY_20260607.md`。
要点: おいしい健康 8,244 レシピ（JSON-LD kcal+PFC, T3）/ allrecipes（cleaned JSON, T3）/ Cookpad・楽天（栄養なし）/ VireoFood172（認識のみ）。
**戦略結論（不変）**: styled + recipe-intended 分量は E13/E14 実ドメイン校正の代替不可。用途は recognition / density-prior / 言語別サニティに限定。

## 6. 新データセット追加時の手続き

1. 本 doc に manifest 行を追加: 出所 / 収集方式 / 日付 / license・consent / tier / 許可用途 / 再構築手順。
2. `ssot/datasets.json` に検証 entry を追加（required / min_count）。
3. eval 用なら split を `evals/splits/` に固定（immutable）。
4. 使用開始は 1–3 の後（登記なしの資産で採用判定をしない）。
