---
name: pdca-bootstrap
description: freeform_usda_meal_analysis_api のPDCAセッションを開始する。現行baseline・最新lesson・本番remote設定のスナップショットを生成して確認する。新しいセッションで精度改善（prompt/model/検索パラメータ）に着手する前に必ず実行する。
when_to_use: ユーザーが freeform の精度改善・PDCA・評価に着手しようとしているとき、またはセッション最初の状況把握を求めたとき。
argument-hint: "[--api-url <URL>]"
allowed-tools: Bash, Read
---

# PDCA Bootstrap (freeform_usda_meal_analysis_api)

新セッションの最初に現行状態を取得し、過去知見を踏まえて再現可能にPDCAを回すための起点。

## 手順

1. リポジトリルート (`/Users/odasoya/meal_analysis_api_2`) から bootstrap を実行する。
   `$ARGUMENTS` で `--api-url` が渡されればそれを使い、無ければ本番 Cloud Run URL を使う。

   ```bash
   python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap \
     --api-url https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app
   ```

2. 生成された `apps/freeform_usda_meal_analysis_api/evals/knowledge/session_bootstrap_latest.md` を読み、
   次を必ず確認・要約する:
   - 現行 baseline 指標（`calorie_mae_percent` / `high_error_rate_30_percent` / `avg_latency_sec` / `avg_cost_usd`）
   - **Remote Config Check**: 本番が配信中の `vlm_model_id` / `vlm_prompt_file` と、`current_baseline.json` の構成が一致しているか（不一致なら config ドリフトを警告する）
   - 直近 lesson の decision（worked / did-not-work）
   - **Negative Registry Summary**: check the verdict counts and entry id list (do-not-retry
     hypotheses). Before starting any new experiment, run `check_prior_art --query "<keyword>"`
     for its lever/topic (read-before-write, required per `ssot/DEVELOPMENT_OS.md` §5).
   - **Lessons Index Freshness**: confirm the status. If it says "regenerated", the
     `evals/lessons/INDEX.md` was stale and has just been auto-rebuilt this run — note that
     in your session summary.
   - **Branch Consistency**: if a WARNING line is present (current branch does not match
     the `plans/current.md` resume branch), surface it to the user before proceeding —
     do not silently continue on the wrong branch.

3. `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json` を読み、baseline の出所runと採用条件を確認する。

## 出力

- 現行baselineの1行サマリー（mae / high30 / latency / cost）
- 本番configとbaselineの一致/不一致（ドリフトの有無）
- 直近lessonの要点（次に試すべき仮説）
- Negative registry のverdict別件数 + check_prior_art 必須の確認
- lessons INDEX freshness の状態（regenerated であればその旨）
- branch consistency の WARNING の有無

## 参照
- `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md`
- `apps/freeform_usda_meal_analysis_api/AGENTS.md`
