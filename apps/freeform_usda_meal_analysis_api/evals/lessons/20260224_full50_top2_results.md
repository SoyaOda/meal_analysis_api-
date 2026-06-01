# Lesson: Full50 Top2 Results

- Date: 2026-02-24
- Run directory: `apps/freeform_usda_meal_analysis_api/evals/runs/20260224_192722`
- Eval set: 50 images (`test_food1.jpg`-`test_food50.jpg`)

## Candidates
1. `gemini3_flash_v7_exp_meal_title`
2. `gpt5_mini_v7_exp_meal_title`

## Results
- gemini3_flash_v7_exp_meal_title
  - calorie_mae_percent: 21.9784
  - high_error_rate_30_percent: 24.0
  - avg_latency_sec: 21.5895
  - avg_cost_usd: 0.01063
- gpt5_mini_v7_exp_meal_title
  - calorie_mae_percent: 29.7288
  - high_error_rate_30_percent: 32.0
  - avg_latency_sec: 41.9667
  - avg_cost_usd: 0.005525

## Decision
- Baselineは `gemini3_flash_v7_exp_meal_title` を採用。
- 理由: MAE, 30%超過率, latency の3軸で優位。コストは予算上限 (`<=0.05`) 内。

## Next hypothesis
- Prompt最適化は「小さな差分」だけ試す（重量推定ルールの局所修正）。
- モデルはGemini 3 Flashを軸に、次回は1-2候補のみ比較して探索効率を維持する。
