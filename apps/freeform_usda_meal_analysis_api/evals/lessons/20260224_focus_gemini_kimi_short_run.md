# Lesson: Focused Gemini vs Kimi short run

- Date: 2026-02-24
- Run directory: `apps/freeform_usda_meal_analysis_api/evals/runs/20260224_220307`
- Eval set: 5 images (`test_food1.jpg`-`test_food5.jpg`)
- Config: `apps/freeform_usda_meal_analysis_api/evals/configs/pdca_focus_gemini_kimi_20260224.json`

## Results (5-image quick check)
- `gemini3_flash_v7`
  - calorie_mae_percent: 12.1219
  - high_error_rate_30_percent: 0.0
  - avg_latency_sec: 7.6195
  - avg_cost_usd: 0.009809
  - decision: `promote`
- `kimi_k25_v7`
  - calorie_mae_percent: 9.4628
  - high_error_rate_30_percent: 0.0
  - avg_latency_sec: 5.944
  - avg_cost_usd: null
  - decision: `hold` (reason: `avg_cost_usd unavailable`)

## What was learned
- 短期サンプルでは `kimi-k2.5` が MAE/latency ともに良い結果。
- ただしコスト未算出だと gate 判定が `hold` になる。
- `config/model_pricing.json` に `openrouter:moonshotai/kimi-k2.5` を追加して、次回runから cost gate を有効化。

## Action
- ベースライン更新は見送り（5画像のみのため）。
- 次は同じ2モデルで **50画像本評価** を実施し、正式な採用判定を行う。
