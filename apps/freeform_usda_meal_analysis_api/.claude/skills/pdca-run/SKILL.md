---
name: pdca-run
description: freeform_usda_meal_analysis_api のPDCAバッチ評価を実行する。指定した実験config（evals/configs/*.json）でVLM/prompt/検索パラメータを50画像（または指定split）に対して評価し、calorie MAE等の指標と採用ゲート判定を出力する。OpenRouter APIコストを消費するため自動起動は無効。
argument-hint: "<config.json> [--api-url <URL>] [--limit 50 | --image-index-file <split>]"
disable-model-invocation: true
allowed-tools: Bash, Read
---

# PDCA Batch Eval Run (freeform_usda_meal_analysis_api)

実験configに沿って評価を実行する。**APIコストを消費する**ため、ユーザーの明示的な `/pdca-run` 起動でのみ実行する。

## 前提
- API起動（ローカルなら別ターミナルで `PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8006 python -m apps.freeform_usda_meal_analysis_api.main`）。
- 評価は原則 `--no-use-vlm-cache`（キャッシュ混入禁止）。
- 過学習防止: prompt に評価データ固有情報（`test_foodXX` / label値 / ground truth）を埋め込まない。

## 手順
0. **Prior-art check (required before creating/editing an experiment config)**: run
   `check_prior_art` with the lever's name and key terms as keywords, e.g.:

   ```bash
   PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python -m \
     apps.freeform_usda_meal_analysis_api.scripts.check_prior_art \
     --query "<lever name>" "<key term>"
   ```

   If it reports any hits (in `negative_results.json`, `tested_models.json`, the
   lessons INDEX, or `docs/*.md`), read the matching lesson(s) in full before
   proceeding, then explicitly state one of:
   - (a) do not run this experiment — it is already a settled do-not-retry finding, or
   - (b) proceed anyway, citing new evidence that satisfies the entry's `reopen_when`
     condition (see `ssot/DEVELOPMENT_OS.md` §5 — never re-litigate without this).

1. `$ARGUMENTS` の先頭を config パスとして受け取り、`evals/configs/` に存在することを確認する。
2. リポジトリルートから実行する（split未指定なら full50）:

   ```bash
   python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
     --config <config.json> \
     --api-url <api-url> \
     --limit 50 \
     --no-use-vlm-cache
   ```

   - 開発中チューニングは `--image-index-file apps/freeform_usda_meal_analysis_api/evals/splits/dev_40_v1.txt --required-image-count 40` を使う。
   - 中断時は `--start-index/--end-index` で分割し、最終的に `merge_pdca_runs` で50件をカバーする。

3. 出力 `evals/runs/<timestamp>/summary.md` を読み、候補ごとの指標と decision を要約する。

## 採用判定
判定は `/pdca-check` に渡すか、`evals/runs/<timestamp>/summary.md` の decision を確認する。
**単発runでは昇格しない** — 候補は反復評価（`run_pdca_repeated_eval`）で安定性を確認する。

## 参照
- `apps/freeform_usda_meal_analysis_api/AGENTS.md`（Standard PDCA Loop / Promotion Gate）
- `apps/freeform_usda_meal_analysis_api/scripts/run_pdca_batch_eval.py`
