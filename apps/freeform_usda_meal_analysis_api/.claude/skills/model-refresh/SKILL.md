---
name: model-refresh
description: freeform_usda_meal_analysis_api の新モデル定期評価サイクル（model-refresh）を回す。OpenRouter カタログから未テストの画像対応モデルを検知し、smoke→dev40→pooled rotation の段階ゲートで現行 prod 構成（flash スタック）への挑戦者を評価する。OpenRouter APIコストを消費するため自動起動は無効。
argument-hint: "[watch | smoke | dev40 | rotation <candidate>] （省略時はプロトコル全体の状況確認から開始）"
disable-model-invocation: true
allowed-tools: Bash, Read, Write
---

# Model Refresh（新モデル定期評価・入れ替えサイクル）

正典: `apps/freeform_usda_meal_analysis_api/docs/MODEL_REFRESH_PROTOCOL_20260611.md`（ゲート数値・教訓・予算制約はそちらが SSOT。先に読むこと）。

## 前提
- `/pdca-bootstrap` 実行済み（baseline / 本番 config 確認）。
- ローカル API 起動済み（venv-with-space + env unsets。`PYTHONPATH=/Users/odasoya/meal_analysis_api_2 PORT=8006` で `apps.freeform_usda_meal_analysis_api.main`）。
- 予算: per-image ≤ baseline×10（SC K込み）、latency ≤ ×2。

## 手順（段階ゲート）

### 0. プリフライト（必須）
```bash
python -m apps.freeform_usda_meal_analysis_api.scripts.check_openrouter_credits --min-usd <想定コスト×2>
```
残高不足なら停止（402→breaker連鎖→本番停止の事故歴: lesson 20260611）。

### 1. watch — 検知・候補選定
```bash
python -m apps.freeform_usda_meal_analysis_api.scripts.model_watch \
  --update-pricing \
  --emit-config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_model_refresh_smoke5_<date>.json \
  --prompt-file <現行prodプロンプトのテキストファイル>
```
- レポート（`evals/catalog/model_watch_<date>.md`）で「untested × 予算内」を確認。
- 既テスト（`evals/knowledge/tested_models.json`）は再評価しない。

### 2. smoke — 故障検出（5枚, K=1）
`run_pdca_batch_eval --limit 5 --required-image-count 5 --no-use-vlm-cache`
- 落とす: failure>0 / MAE>60% / latency>2×。n=5 で優劣判断しない。

### 3. dev40 — 粗い序列（K=1, paired vs v13f_flash）
`--image-index-file evals/splits/dev_40_v1.txt --required-image-count 40`
- shortlist: paired ΔMAE ≤ +1.0pt ∧ latency/cost ゲート内。
- ⚠️ GT-artifact guard: dev40 GT は GPT-5-pro 推定。GPT系の勝ちはここで信用しない。

### 4. rotation — 本判定（JFB-100 / NVReal-104 / N5k-100, paired）
各セットの run 完了後:
```bash
python -m apps.freeform_usda_meal_analysis_api.scripts.pool_paired_rotation \
  --runs <jfb_run> <nvreal_run> <n5k_run> \
  --candidate <name> --baseline-candidate v13f_flash
```
- 昇格: pooled BCa CI 全体<0 ∧ 3セット符号一致 ∧ high30 非悪化 ∧ latency/cost 内。

### 5. 採用処理
- 勝者は SC K=3 形態 + `run_pdca_repeated_eval --repeats 2` で安定性確認。
- lesson 記録 + `tested_models.json` へ verdict 追記（**負けも必ず記録**）。
- baseline 更新は promote 時のみ。本番反映（Firestore/deploy）はユーザー明示指示が必要。

## 出力
- 各段階の通過/脱落モデルと根拠（ΔMAE, CI, latency, cost）
- 最終 verdict（promote / hold / reject）と lesson ファイルパス
