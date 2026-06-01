# Lesson: Gemini v11b temp03 adopted after full50 + repeat stability

- Date: 2026-02-25
- Model: `openrouter:google/gemini-3-flash-preview`
- Promoted prompt: `freeform_prompt_usda_format_ver_v11b_gemini_component_density_20260225.txt`
- Promoted params: `reasoning_effort=medium`, `temperature=0.3`, `max_tokens=12288`, `stage1_top_k=50`, `use_vlm_cache=false`

## Runs used
- Dev40 scan (v9b seed/prompt sweep):
  - `apps/freeform_usda_meal_analysis_api/evals/runs/20260225_103124`
- Full50 gate run (v9b vs v11b temp02/temp03):
  - `apps/freeform_usda_meal_analysis_api/evals/runs/20260225_105950`
- Full50 repeat stability run (v11b temp03):
  - `apps/freeform_usda_meal_analysis_api/evals/runs/20260225_112102`

## Gate result on full50 (`20260225_105950`)
- Previous baseline reference (`current_baseline` before update): `mae=12.51`, `high30=6.0`
- `gemini3_flash_v11b_component_density_temp03_full50`
  - `calorie_mae_percent=11.3662` (`-1.1438 pt`)
  - `high_error_rate_30_percent=6.0` (`+0.0 pt`)
  - `avg_latency_sec=14.542` (faster than baseline)
  - `avg_cost_usd=0.007222` (within budget)
  - Gate decision: `promote`

## Stability result (full50 repeat)
- Compare first full50 promote run vs repeat:
  - Run A: `20260225_105950` (`mae=11.3662`, `high30=6.0`)
  - Run B: `20260225_112102` (`mae=11.3765`, `high30=4.0`)
  - `delta_mae=+0.0103 pt` (stable, within 1.0pt threshold)
  - `delta_high30=-2.0 pt` (within 2.0pt stability threshold)
- Note: per-image predictions still changed on many images (`30/50`), but aggregate KPI stayed stable.

## What worked
- `v11b` kept prompt complexity moderate while adding explicit portion anchors for rice/pasta/sauce handling.
- `temperature=0.3` outperformed `temperature=0.2` on full50 MAE.
- Full50 + repeat check prevented adopting a dev-only improvement that could fail to reproduce.

## What did not work
- `v11a` midpoint-calibration variant improved median but increased high-error outliers.
- `v11b temp02` looked good on dev40 but regressed on full50 MAE.
- `v9b + seed7` did not produce reliable gains vs non-seeded v9b on dev40.

## Action taken
- Updated baseline files:
  - `apps/freeform_usda_meal_analysis_api/evals/baselines/baseline_20260225_gemini3_flash_v11b_component_density_temp03.json`
  - `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json`
