# Evals Workspace

`apps/freeform_usda_meal_analysis_api` のモデル/プロンプト最適化用アーティファクト置き場。

## Structure
- `configs/`: 実験設定（候補モデル、プロンプト、予算上限）
- `catalog/`: OpenRouterモデル一覧スナップショット
- `baselines/`: ベースライン結果JSON
- `runs/`: 実験結果（raw + summary）
- `lessons/`: 学習ログ（失敗理由、次仮説）
- `templates/`: 実験計画とポストモーテムの雛形
- `splits/`: dev/holdout画像index定義
- `knowledge/`: 構造化ログ（jsonl）

`runs/` は `.gitignore` で生成物を除外（`.gitkeep` のみ管理）。

## Naming
- run: `runs/YYYYMMDD_HHMMSS/`
- baseline: `baselines/<name>.json`
- lesson: `lessons/YYYYMMDD_<slug>.md`

## Utilities
- 分割run統合: `python -m apps.freeform_usda_meal_analysis_api.scripts.merge_pdca_runs --runs <runA> <runB>`
- 知見JSONL更新: `python -m apps.freeform_usda_meal_analysis_api.scripts.export_pdca_knowledge`
- セッション開始スナップショット生成:
  - `python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap --api-url <api-url>`
  - 出力: `evals/knowledge/session_bootstrap_latest.md`

## Required Fields (summary)
- `calorie_mae_percent`
- `calorie_p50_percent`
- `calorie_p90_percent`
- `high_error_rate_30_percent`
- `avg_latency_sec`
- `avg_cost_usd`
- `evaluated_image_count`
- `expected_image_count`
- `coverage_complete`
- `all_success`
