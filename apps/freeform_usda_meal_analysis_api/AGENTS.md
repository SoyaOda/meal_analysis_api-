# AGENTS.md (freeform_usda_meal_analysis_api)

## Scope
このファイルは `apps/freeform_usda_meal_analysis_api` のみを対象とする。

## Objective
写真からのカロリー推定精度を、**再現可能なPDCA**で継続改善する。
最適化対象は主に以下。
- VLMモデル（OpenRouter経由）
- プロンプト
- reasoning / temperature / max_tokens
- seed（ただし provider 側非決定性を前提に扱う）

## Model Focus (as of 2026-02-24)
当面は次の1モデルに集中する。
- `openrouter:google/gemini-3-flash-preview`（default）

重要な制約（OpenRouter models API確認済み）:
- `gemini-3-flash-preview`: `input_modalities` に `image` を含む（画像解析に使用可）

運用ルール:
- `/api/v1/meal-analyses/complete` のPDCAでは、**画像入力対応モデルのみ**を候補に入れる。
- thinking前提のため `reasoning_effort` は原則 `medium` 以上から開始する。

## Ground Rules
- 1回の変更は1意図（small, reviewable）
- 50画像ベンチを標準評価セットとして固定（`test_images/images/test_food1.jpg`〜`test_food50.jpg`）
- 比較は必ずベースライン差分で判断し、単発結果で採用しない
- **採用判断は原則「全50例」のGround truth総カロリー比較を完了してから行う**
- 実験結果・失敗学習を `evals/` 配下へ必ず保存する
- API仕様変更時は後方互換性（旧評価スクリプト）を壊さない
- プロンプトに `test_foodXX` / `ground truth` / ラベル値など評価データ固有情報を埋め込まない（過学習禁止）
- PDCA評価時は原則 `use_vlm_cache=false`（キャッシュ混入による見かけ改善を禁止）

## Session Bootstrap (Mandatory)
新しいセッション開始時は、実験前に必ず次を実行する。

```bash
python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap \
  --api-url https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app
```

必読:
- `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md`
- `apps/freeform_usda_meal_analysis_api/evals/knowledge/session_bootstrap_latest.md`

この2つを読まずにPDCAを開始しない。

## Admin Panel Safety Rules (Critical)
- Admin UIの `Local` は localhost固定ではなく **相対パス**。
- 本番ドメインで `/admin` を開いている場合、`Local` タブで保存しても本番設定が更新される。
- 設定変更後は必ず `/admin/api/config?refresh=true` を叩き、`updated_at` と値を確認する。
- 画面のタブラベルだけで保存先を判断しない。

## Prompt Reproducibility Rules
- `Prompt Text (Override)` を使う場合、実験config (`evals/configs/*.json`) に同じ `prompt_text` を保持し、再現性を確保する。
- lessonには可能な限り `prompt_sha256` を記録する。
- 昇格候補は、同一promptで反復評価して指標の分散を確認する。

## Standard PDCA Loop
1. Plan
- `scripts/sync_openrouter_candidates.py` で最新モデル候補を更新
- `evals/configs/*.json` に今回の実験マトリクスを定義

2. Do
- API起動後、`scripts/run_pdca_batch_eval.py` で実験実行
- 出力先: `evals/runs/<timestamp>/`
- 原則 `--limit 50` で実行する
- 中断時は分割実行を許可（例: `--start-index 1 --end-index 25` と `--start-index 26 --end-index 50`）し、**最終的に50件全体をカバー**する
- 分析は原則 `--no-use-vlm-cache` で実行する

3. Check
- 指標: `calorie_mae_percent`, `calorie_p50_percent`, `calorie_p90_percent`, `high_error_rate_30_percent`, `avg_latency_sec`, `avg_cost_usd`
- Ground truthとのカロリー誤差を50件全体で確認する
- 分割実行した場合は、全分割を合わせて50件の集計（加重平均）を作成してから判定する
- ベースライン差分を確認し、採用可否を判定

4. Act
- 採用時: `evals/baselines/` のベースラインJSONを更新
- 不採用時: `evals/lessons/` に失敗理由・次仮説を記録

## Promotion Gate (採用基準)
候補構成を本命へ昇格する条件:
- `required_image_count` を満たす（通常は50）
- 失敗0件（`failure_count == 0`）
- カバレッジ完了（`coverage_complete == true`）
- `calorie_mae_percent` がベースライン比で 1.0pt 以上改善
- `high_error_rate_30_percent` が悪化しない
- `avg_latency_sec` が +20% 以内
- `avg_cost_usd` が予算上限内（実験configの `budget.max_avg_cost_usd_per_image`）
- 上記判定は**50件全体集計**を対象に行う（部分集合のみの結果では採用しない）

## Stability Policy
- 採用候補は、同一50件で最低2回（または2分割以上を統合した等価50件）確認し、指標のぶれを記録する。
- 目安: `calorie_mae_percent` の差が 1.0pt 以内、`high_error_rate_30_percent` の差が 2.0pt 以内を安定とみなす。
- 安定性が満たせない場合は hold にし、`evals/lessons/` に原因仮説を記録する。
- `seed` 固定を使っても provider 側で完全再現しない可能性があるため、**昇格判定は反復実行の平均/分散で判断**する。
- 反復評価には `scripts/run_pdca_repeated_eval.py` を使い、最低2反復の `mae_mean` / `mae_std` / `high30_mean` を保存する。

## Anti-Overfitting Policy
- チューニング中は `evals/splits/dev_40_v1.txt` を主に使い、最終判定は full50 で行う。
- 週次で holdout をローテーションし、同一subset固定の最適化を避ける。
- lessonには「効いた要素/効かなかった要素」を必ず分離して記録する。

## Directory Contract
- `evals/configs/`: 実験設定JSON
- `evals/catalog/`: OpenRouterモデル一覧スナップショット
- `evals/runs/`: 実行結果（raw + summary）
- `evals/baselines/`: 比較基準JSON
- `evals/lessons/`: 学習ログ（失敗/成功）
- `evals/templates/`: 実験計画とポストモーテム雛形
- `evals/splits/`: dev/holdout index定義
- `evals/knowledge/`: 構造化知見ログ

## Quick Commands
```bash
# 1) 最新候補の取得（thinking + image対応 + 価格上限）
python -m apps.freeform_usda_meal_analysis_api.scripts.sync_openrouter_candidates \
  --max-prompt-price 3.0 \
  --max-completion-price 15.0 \
  --thinking-only

# 2) 50画像バッチ評価（Gemini prompt sweep）
python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json \
  --api-url http://localhost:8006 \
  --limit 50 \
  --no-use-vlm-cache

# 3) 中断時の分割実行例（最終的に50件を揃える）
python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json \
  --api-url http://localhost:8006 \
  --start-index 1 \
  --end-index 25 \
  --no-use-vlm-cache

python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json \
  --api-url http://localhost:8006 \
  --start-index 26 \
  --end-index 50 \
  --no-use-vlm-cache

# 4) 分割runを統合して正式判定
python -m apps.freeform_usda_meal_analysis_api.scripts.merge_pdca_runs \
  --runs \
  apps/freeform_usda_meal_analysis_api/evals/runs/<run_1_25> \
  apps/freeform_usda_meal_analysis_api/evals/runs/<run_26_50> \
  --required-image-count 50

# 5) 構造化知見ログを更新
python -m apps.freeform_usda_meal_analysis_api.scripts.export_pdca_knowledge

# 6) 反復実行で安定性評価（推奨）
python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_repeated_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/<config>.json \
  --api-url http://localhost:8006 \
  --repeats 2 \
  --image-index-file apps/freeform_usda_meal_analysis_api/evals/splits/holdout_10_v1.txt \
  --required-image-count 10 \
  --no-use-vlm-cache
```
