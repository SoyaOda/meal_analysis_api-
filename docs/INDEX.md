# docs/ INDEX

`docs/` 配下のドキュメント一覧。新規に文書を追加・archive した場合は、必ず同一 diff でこの INDEX を更新すること。

## (a) CURRENT — 現役ドキュメント（`docs/` 直下）

| ファイル | 日付 | 目的 |
|---|---|---|
| `API_QUICKSTART.md` | 2026-06-02 | 6 アプリ（monorepo）それぞれの起動コマンドと代表的なエンドポイント呼び出し例をまとめたクイックスタート |
| `MACHINE_MIGRATION.md` | 2026-07-07 | 本リポジトリと Claude Code 開発環境一式を別の Mac に移行するための完全手順（macOS 向け） |
| `INDEX.md` | 2026-07-08 | 本ファイル。`docs/` 配下（直下・archive・maintenance）の文書索引 |

### `docs/maintenance/`（運用レポート）

| ファイル | 日付 | 目的 |
|---|---|---|
| `maintenance/BRANCH_AUDIT_20260708.md` | 2026-07-08 | ローカルブランチ59本の棚卸しレポート（KEEP／削除候補カテゴリA〜F、削除コマンドはコメントアウトのreport-only） |

## (b) ARCHIVED — `docs/archive/2025/` 配下

いずれも 2025 年内に作成され、2026 年時点で後継ドキュメント／現行実装により superseded 済みのため archive（削除はせず履歴保持のため `git mv`）。

| ファイル | 最終更新 | 目的 | Archive 理由 |
|---|---|---|---|
| `api_changes_2025-09-23.md` | 2025-09-24 | Word Query API / Meal Analysis API の機能改善差分（dev branch, 2025-09-23 時点） | 日付限定の変更履歴スナップショット。現行 API の一次情報源ではなく、内容は各アプリの README / コードに反映済み |
| `api_changes_2025-09-24.md` | 2025-09-24 | Word Query API の検索パラメータ設計見直し差分（dev branch, 2025-09-24 時点） | 同上。日付限定の変更履歴スナップショットで、現行仕様は各アプリの README / コードが正 |
| `current_phase1_vlm_prompt.md` | 2025-10-19 | Phase1 VLM（Gemma 3 / DeepInfra, MyNetDiary版）プロンプトのスナップショット（要約版） | 生成元 `shared/config/prompts/phase1_prompts.py` は継続改修されており、当時のプロンプト文面スナップショットは現行実装と乖離。プロンプトは常にコードが正 |
| `current_phase1_vlm_prompt_complete.md` | 2025-10-19 | 同上（食材リスト全文を含む完全版） | 同上 |
| `current_usda_phase1_vlm_prompt_complete.md` | 2025-10-19 | Phase1 VLM プロンプトの USDA FNDDS 版スナップショット（完全版） | 同上。USDA 版もプロンプト実装は継続改修中でスナップショットは陳腐化 |
| `current_usda_phase1_vlm_prompt_v3_granularity.md` | 2025-10-19 | 粒度制御システム対応 v3.0 プロンプトのスナップショット | 同上。v3 granularity という当時世代の仕様であり、現行 freeform_usda 系のプロンプトはさらに改修が進んでいる |
| `current_usda_phase1_vlm_prompt_v3_granularity_complete.md` | 2025-10-19 | 同上（完全版・プロンプト本文全文） | 同上 |
| `ingredient_list_full.txt` | 2025-10-19 | MyNetDiary版 食材リスト全文（当時のプロンプトに埋め込まれていたもの） | 上記プロンプトスナップショット群に付随するデータで、同時に陳腐化 |
| `usda_ingredient_list_full.txt` | 2025-10-19 | USDA FNDDS版 食材リスト全文（当時のプロンプトに埋め込まれていたもの） | 同上 |

### repo root 直下から archive（2026-07-08 追加）

| ファイル | 最終更新 | 目的 | Archive 理由 |
|---|---|---|---|
| `COMPREHENSIVE_MODEL_EVALUATION.md` | 2025-10-19 | Vision Model 徹底評価レポート（写真一致度分析） | pre-mozu 期のモデル評価。現行のモデル選定 SSOT は freeform の `MOZU_MODEL_DECISION_20260603.md` + `tested_models.json` |
| `MODEL_COMPARISON_REPORT.md` | 2025-10-19 | Vision Model 比較レポート | 同上（`COMPREHENSIVE_MODEL_EVALUATION.md` と相互参照のセット） |
| `LLAMA4_TEST_REPORT.md` | 2025-10-19 | Llama-4-Maverick テスト結果 | 同上。当時の候補モデル検証記録 |
| `LLAMA4_FOOD4_ERROR_ANALYSIS.md` | 2025-10-19 | Llama-4 の food4 エラー原因分析 | 同上 |
| `MATCH_RATE_ANALYSIS.md` | 2025-10-19 | マッチ率計算ロジックの分析 | pre-mozu 期の分析。現行メトリクス定義は freeform の eval harness（`run_pdca_batch_eval.py`）が正 |

### `docs/archive/2025/md_files/`（旧 root `md_files/` を丸ごと archive）

| ファイル | 最終更新 | 目的 | Archive 理由 |
|---|---|---|---|
| `api_deploy.md` | 2025-09-05 | Firebase / Cloud Run への FastAPI デプロイ手順（初心者向け解説） | 当時の `new-snap-calorie` Firebase プロジェクトを前提とした古いデプロイ手順。現行のデプロイ運用とは異なる |
| `barcode_spec_UDC.md` | 2025-09-24 | バーコード情報（FDC Branded Foods の gtin_upc）の設計メモ | `barcode_api` 実装済みの初期設計メモ。実装検討時の一次資料であり、現行仕様は `apps/barcode_api` のコード／README が正 |
| `barcode_spec1.md` | 2025-09-24 | Open Food Facts と FoodData Central の比較・商用利用検討（バーコード栄養情報 API 詳細設計） | 同上。実装前の比較検討メモで、実装済みの現在は `apps/barcode_api` のコードが正 |
| `deepresearch_voice_record.md` | 2025-09-21 | 音声入力対応（Speech-to-Text 連携）の実装戦略検討 | 実装検討フェーズのリサーチメモ。当時の計画であり、現行の各アプリ実装とは独立した提案書 |
| `freeform_api_optimization_spec.md` | 2025-12-23 | freeform_usda_meal_analysis_api の速度・安定性最適化仕様書（作成 2024-12-22） | 内容は既に実装済み（`freeform_api_resilience_improvement_plan.md` 内に「既に実装されています」と明記）。現行の改善方針は `apps/freeform_usda_meal_analysis_api/docs/DEEP_REVIEW_20260601.md` 等の最新ドキュメントを参照 |
| `freeform_api_resilience_improvement_plan.md` | 2025-12-23 | freeform_usda_meal_analysis_api の耐障害性・パフォーマンス改善計画（P0-P3実装完了と明記） | 計画済み項目は実装完了済み（文書内に明記）。現行の改善ロードマップは `apps/freeform_usda_meal_analysis_api/docs/DEEP_REVIEW_20260601.md` を参照 |

## (c) 運用規約

1. 新規ドキュメントはファイル名に日付を含める（例: `<topic>_YYYYMMDD.md`）。
2. 既存文書が新版により superseded されたら、文書冒頭に banner（`> **[ARCHIVED]** superseded by <path>` 等）を付けたうえで `git mv docs/<f> docs/archive/<year>/<f>` で移動する（削除しない）。
3. archive／新規追加・削除の変更は、必ずこの `docs/INDEX.md` の更新を同一 diff に含める。
