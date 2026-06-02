---
name: pdca-check
description: freeform_usda_meal_analysis_api のPDCA run結果を現行baselineと採用ゲートで比較する。指定したrunディレクトリのsummaryを読み、calorie MAE差分・high30・latency・cost・coverage/failureを確認し、promote/hold/reject の根拠を提示する。
when_to_use: PDCA評価を実行した後に採用可否を判定したいとき、または過去runの結果を baseline と比較したいとき。
argument-hint: "<run_dir | evals/runs/<timestamp>>"
allowed-tools: Bash, Read
---

# PDCA Check / Gate Decision (freeform_usda_meal_analysis_api)

run結果を `current_baseline.json` と採用ゲートに照らして判定する。

## 手順
1. `$ARGUMENTS` の run ディレクトリの `summary.md` / `summary.json` を読む。
2. `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json` を読む。
3. 採用ゲートに照らして判定する（AGENTS.md の Promotion Gate）:
   - `required_image_count` を満たす（通常50）
   - `failure_count == 0` かつ `coverage_complete == true`
   - `calorie_mae_percent` が baseline 比で改善（**ノイズ評価に注意** — 単発1.0pt差はラン間ノイズ内のことがある。`run_pdca_repeated_eval` の `mae_std` を併読し、paired比較が可能なら優先する）
   - `high_error_rate_30_percent` が悪化しない
   - `avg_latency_sec` が +20% 以内 / `avg_cost_usd` が予算内
4. 安定性: 昇格候補は最低2反復（または分割統合で等価50件）で `mae_mean` / `mae_std` を確認する。

## 出力
- 候補ごとの baseline 差分（mae / high30 / latency / cost）
- promote / hold / reject の判定と根拠
- 採用時の次アクション（baseline更新 + lesson記録）/ 不採用時の次仮説

## 参照
- `apps/freeform_usda_meal_analysis_api/AGENTS.md`（Promotion Gate / Stability Policy）
- `apps/freeform_usda_meal_analysis_api/scripts/merge_pdca_runs.py`（分割統合）
