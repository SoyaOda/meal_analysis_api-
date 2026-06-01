# PDCA Session Start Checklist (Agent Mandatory)

このチェックリストは、異なるセッションでも同じ精度改善フローを再現するための必須手順。

## 0. Scope
- 対象: `apps/freeform_usda_meal_analysis_api`
- 目的: モデル/プロンプトPDCAを、過去知見を踏まえて再現可能に回す

## 1. Must Read (順番固定)
1. `apps/freeform_usda_meal_analysis_api/AGENTS.md`
2. `apps/freeform_usda_meal_analysis_api/CLAUDE.md`
3. `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json`
4. 直近の `apps/freeform_usda_meal_analysis_api/evals/lessons/*.md` 上位3〜5件
5. 必要に応じて `apps/freeform_usda_meal_analysis_api/evals/knowledge/experiment_log.jsonl`

## 2. Bootstrap Snapshot生成（毎セッション最初）
```bash
python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap \
  --api-url https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app
```

- 出力: `apps/freeform_usda_meal_analysis_api/evals/knowledge/session_bootstrap_latest.md`
- このファイルを読み、以下を必ず確認する:
  - 現行 baseline 指標（MAE / high30 / latency / cost）
  - 直近 lesson の decision と有効/無効要素
  - 現在の本番設定（prompt_text active有無、temperature、stage1_top_k など）

## 3. Plan作成時の必須記載
- 今回の仮説（何を改善するか）
- baseline との差分で改善判定する指標
- 評価画像集合（dev40 / holdout10 / full50）
- 昇格判定のゲート（full50完了、failure=0、coverage_complete=true）
- 過学習防止宣言（`test_foodXX`/ground truth情報をpromptへ埋め込まない）

## 4. 実験実行の必須ルール
- 原則 `use_vlm_cache=false`
- 採用判定は full50（中断時は分割実行 + mergeで50件カバー）
- 単発runでは昇格しない。候補は反復評価で安定性確認

## 5. 実験後の必須ルール
- `evals/runs/<timestamp>/` の summary確認
- `evals/lessons/YYYYMMDD_<slug>.md` を必ず記録
  - worked / did-not-work を分離
  - 可能なら `prompt_sha256` を記録
- 必要に応じて baseline 更新
- `python -m apps.freeform_usda_meal_analysis_api.scripts.export_pdca_knowledge`

## 6. Admin Panel運用の注意（重要）
- Admin UIの `Local` は **baseUrl=""（相対パス）** で、開いているドメインに対して保存する。
- つまり本番URLで `/admin` を開いた状態で `Local` タブ保存すると、本番設定が更新される。
- タブラベルだけを信用せず、保存後に `/admin/api/config?refresh=true` で `updated_at` を確認する。

## 7. Definition of Done
- full50 gate（または分割統合で等価）に基づく判定
- lesson更新済み
- 知見ログ更新済み
- 「何が効いた/効かなかった」が次セッションで再利用できる形で残っている
