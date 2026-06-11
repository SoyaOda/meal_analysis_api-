# Model Watch Report — 2026-06-11

- Source: https://openrouter.ai/api/v1/models（取得 338 モデル）
- Baseline: `openrouter:google/gemini-3-flash-preview` avg $0.007159/image（in $0.5/1M, out $3.0/1M）
- 予算ゲート: baseline × 10.0 = $0.071590/image（k3 = k1 × 3 で判定）
- コスト試算: factor = (in/base_in)×0.21 + (out/base_out)×0.79
- 前回スナップショット: なし（初回実行・new判定は省略）
- Registry: /Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/evals/knowledge/tested_models.json（vlm 10 件）
- 価格未公開でスキップ: 0 件

## Untested × 予算内（est k1 昇順, 75 件）

| model_id | est k1 $/img | est k3 $/img | factor | in $/1M | out $/1M | budget | new |
|---|---|---|---|---|---|---|---|
| `openrouter:qwen/qwen3.5-9b` | 0.000583 | 0.001750 | 0.0815 | 0.1 | 0.15 | fits_k3 |  |
| `openrouter:qwen/qwen3.5-flash-02-23` | 0.000686 | 0.002057 | 0.0958 | 0.065 | 0.26 | fits_k3 |  |
| `openrouter:bytedance-seed/seed-1.6-flash` | 0.000791 | 0.002373 | 0.1105 | 0.075 | 0.3 | fits_k3 |  |
| `openrouter:google/gemma-4-26b-a4b-it` | 0.000803 | 0.002408 | 0.1121 | 0.06 | 0.33 | fits_k3 |  |
| `openrouter:openai/gpt-5-nano` | 0.000904 | 0.002713 | 0.1263 | 0.05 | 0.4 | fits_k3 |  |
| `openrouter:xiaomi/mimo-v2.5` | 0.000949 | 0.002846 | 0.1325 | 0.14 | 0.28 | fits_k3 |  |
| `openrouter:google/gemma-4-31b-it` | 0.001039 | 0.003118 | 0.1452 | 0.12 | 0.36 | fits_k3 |  |
| `openrouter:bytedance-seed/seed-2.0-mini` | 0.001055 | 0.003164 | 0.1473 | 0.1 | 0.4 | fits_k3 |  |
| `openrouter:google/gemini-2.5-flash-lite` | 0.001055 | 0.003164 | 0.1473 | 0.1 | 0.4 | fits_k3 |  |
| `openrouter:google/gemini-2.5-flash-lite-preview-09-2025` | 0.001055 | 0.003164 | 0.1473 | 0.1 | 0.4 | fits_k3 |  |
| `openrouter:mistralai/mistral-small-2603` | 0.001582 | 0.004746 | 0.2210 | 0.15 | 0.6 | fits_k3 |  |
| `openrouter:qwen/qwen3.5-35b-a3b` | 0.002306 | 0.006918 | 0.3221 | 0.14 | 1.0 | fits_k3 |  |
| `openrouter:qwen/qwen3.6-35b-a3b` | 0.002336 | 0.007009 | 0.3263 | 0.15 | 1.0 | fits_k3 |  |
| `openrouter:qwen/qwen3.6-flash` | 0.002685 | 0.008054 | 0.3750 | 0.1875 | 1.125 | fits_k3 |  |
| `openrouter:stepfun/step-3.7-flash` | 0.002769 | 0.008308 | 0.3868 | 0.2 | 1.15 | fits_k3 |  |
| `openrouter:qwen/qwen3-vl-8b-thinking` | 0.002925 | 0.008775 | 0.4086 | 0.117 | 1.365 | fits_k3 |  |
| `openrouter:openai/gpt-5.4-nano` | 0.002958 | 0.008874 | 0.4132 | 0.2 | 1.25 | fits_k3 |  |
| `openrouter:minimax/minimax-m3` | 0.003164 | 0.009493 | 0.4420 | 0.3 | 1.2 | fits_k3 |  |
| `openrouter:perceptron/perceptron-mk1` | 0.003279 | 0.009836 | 0.4580 | 0.15 | 1.5 | fits_k3 |  |
| `openrouter:qwen/qwen3-vl-30b-a3b-thinking` | 0.003332 | 0.009995 | 0.4654 | 0.13 | 1.56 | fits_k3 |  |
| `openrouter:qwen/qwen3.5-27b` | 0.003527 | 0.010582 | 0.4927 | 0.195 | 1.56 | fits_k3 |  |
| `openrouter:google/gemini-3.1-flash-lite-preview` | 0.003580 | 0.010739 | 0.5000 | 0.25 | 1.5 | fits_k3 |  |
| `openrouter:baidu/ernie-4.5-vl-424b-a47b` | 0.003619 | 0.010858 | 0.5056 | 0.42 | 1.25 | fits_k3 |  |
| `openrouter:qwen/qwen3.5-plus-02-15` | 0.003723 | 0.011168 | 0.5200 | 0.26 | 1.56 | fits_k3 |  |
| `openrouter:qwen/qwen3.7-plus` | 0.004219 | 0.012657 | 0.5893 | 0.4 | 1.6 | fits_k3 |  |
| `openrouter:qwen/qwen3.5-plus-20260420` | 0.004295 | 0.012886 | 0.6000 | 0.3 | 1.8 | fits_k3 |  |
| `openrouter:bytedance-seed/seed-1.6` | 0.004522 | 0.013566 | 0.6317 | 0.25 | 2.0 | fits_k3 |  |
| `openrouter:bytedance-seed/seed-2.0-lite` | 0.004522 | 0.013566 | 0.6317 | 0.25 | 2.0 | fits_k3 |  |
| `openrouter:openai/gpt-5.1-codex-mini` | 0.004522 | 0.013566 | 0.6317 | 0.25 | 2.0 | fits_k3 |  |
| `openrouter:qwen/qwen3.6-plus` | 0.004653 | 0.013960 | 0.6500 | 0.325 | 1.95 | fits_k3 |  |
| `openrouter:qwen/qwen3.5-122b-a10b` | 0.004703 | 0.014109 | 0.6569 | 0.26 | 2.08 | fits_k3 |  |
| `openrouter:z-ai/glm-4.5v` | 0.005197 | 0.015592 | 0.7260 | 0.6 | 1.8 | fits_k3 |  |
| `openrouter:qwen/qwen3.6-27b` | 0.005393 | 0.016180 | 0.7534 | 0.289 | 2.4 | fits_k3 |  |
| `openrouter:qwen/qwen3.5-397b-a17b` | 0.005584 | 0.016752 | 0.7800 | 0.39 | 2.34 | fits_k3 |  |
| `openrouter:amazon/nova-2-lite-v1` | 0.005615 | 0.016845 | 0.7843 | 0.3 | 2.5 | fits_k3 |  |
| `openrouter:google/gemini-2.5-flash` | 0.005615 | 0.016845 | 0.7843 | 0.3 | 2.5 | fits_k3 |  |
| `openrouter:x-ai/grok-build-0.1` | 0.006777 | 0.020332 | 0.9467 | 1.0 | 2.0 | fits_k3 |  |
| `openrouter:google/gemini-3.1-flash-image-preview` | 0.007159 | 0.021477 | 1.0000 | 0.5 | 3.0 | fits_k3 |  |
| `openrouter:x-ai/grok-4.20` | 0.008471 | 0.025414 | 1.1833 | 1.25 | 2.5 | fits_k3 |  |
| `openrouter:x-ai/grok-4.3` | 0.008471 | 0.025414 | 1.1833 | 1.25 | 2.5 | fits_k3 |  |
| `openrouter:moonshotai/kimi-k2.6` | 0.008473 | 0.025419 | 1.1836 | 0.68 | 3.41 | fits_k3 |  |
| `openrouter:openai/gpt-5.4-mini` | 0.010739 | 0.032216 | 1.5000 | 0.75 | 4.5 | fits_k3 |  |
| `openrouter:openai/gpt-5-image-mini` | 0.011287 | 0.033862 | 1.5767 | 2.5 | 2.0 | fits_k3 |  |
| `openrouter:openai/o4-mini` | 0.011602 | 0.034807 | 1.6207 | 1.1 | 4.4 | fits_k3 |  |
| `openrouter:openai/o4-mini-high` | 0.011602 | 0.034807 | 1.6207 | 1.1 | 4.4 | fits_k3 |  |
| `openrouter:anthropic/claude-haiku-4.5` | 0.012433 | 0.037298 | 1.7367 | 1.0 | 5.0 | fits_k3 |  |
| `openrouter:x-ai/grok-4.20-multi-agent` | 0.017325 | 0.051974 | 2.4200 | 2.0 | 6.0 | fits_k3 |  |
| `openrouter:mistralai/mistral-medium-3-5` | 0.018649 | 0.055948 | 2.6050 | 1.5 | 7.5 | fits_k3 |  |
| `openrouter:openai/o3` | 0.021095 | 0.063286 | 2.9467 | 2.0 | 8.0 | fits_k3 |  |
| `openrouter:openai/o4-mini-deep-research` | 0.021095 | 0.063286 | 2.9467 | 2.0 | 8.0 | fits_k3 |  |
| `openrouter:perplexity/sonar-reasoning-pro` | 0.021095 | 0.063286 | 2.9467 | 2.0 | 8.0 | fits_k3 |  |
| `openrouter:google/gemini-2.5-pro` | 0.022611 | 0.067832 | 3.1583 | 1.25 | 10.0 | fits_k3 |  |
| `openrouter:google/gemini-2.5-pro-preview` | 0.022611 | 0.067832 | 3.1583 | 1.25 | 10.0 | fits_k3 |  |
| `openrouter:google/gemini-2.5-pro-preview-05-06` | 0.022611 | 0.067832 | 3.1583 | 1.25 | 10.0 | fits_k3 |  |
| `openrouter:openai/gpt-5` | 0.022611 | 0.067832 | 3.1583 | 1.25 | 10.0 | fits_k3 |  |
| `openrouter:openai/gpt-5-codex` | 0.022611 | 0.067832 | 3.1583 | 1.25 | 10.0 | fits_k3 |  |
| `openrouter:openai/gpt-5.1-codex` | 0.022611 | 0.067832 | 3.1583 | 1.25 | 10.0 | fits_k3 |  |
| `openrouter:openai/gpt-5.1-codex-max` | 0.022611 | 0.067832 | 3.1583 | 1.25 | 10.0 | fits_k3 |  |
| `openrouter:google/gemini-3-pro-image-preview` | 0.028636 | 0.085908 | 4.0000 | 2.0 | 12.0 | fits_k1 |  |
| `openrouter:google/gemini-3.1-pro-preview-customtools` | 0.028636 | 0.085908 | 4.0000 | 2.0 | 12.0 | fits_k1 |  |
| `openrouter:openai/gpt-5.2` | 0.031655 | 0.094964 | 4.4217 | 1.75 | 14.0 | fits_k1 |  |
| `openrouter:openai/gpt-5.2-codex` | 0.031655 | 0.094964 | 4.4217 | 1.75 | 14.0 | fits_k1 |  |
| `openrouter:openai/gpt-5.3-codex` | 0.031655 | 0.094964 | 4.4217 | 1.75 | 14.0 | fits_k1 |  |
| `openrouter:openai/gpt-5.4` | 0.035795 | 0.107385 | 5.0000 | 2.5 | 15.0 | fits_k1 |  |
| `openrouter:anthropic/claude-sonnet-4` | 0.037298 | 0.111895 | 5.2100 | 3.0 | 15.0 | fits_k1 |  |
| `openrouter:anthropic/claude-sonnet-4.5` | 0.037298 | 0.111895 | 5.2100 | 3.0 | 15.0 | fits_k1 |  |
| `openrouter:anthropic/claude-sonnet-4.6` | 0.037298 | 0.111895 | 5.2100 | 3.0 | 15.0 | fits_k1 |  |
| `openrouter:perplexity/sonar-pro-search` | 0.037298 | 0.111895 | 5.2100 | 3.0 | 15.0 | fits_k1 |  |
| `openrouter:openai/gpt-5-image` | 0.048920 | 0.146760 | 6.8333 | 10.0 | 10.0 | fits_k1 |  |
| `openrouter:openai/gpt-5.4-image-2` | 0.052332 | 0.156997 | 7.3100 | 8.0 | 15.0 | fits_k1 |  |
| `openrouter:anthropic/claude-opus-4.5` | 0.062164 | 0.186492 | 8.6833 | 5.0 | 25.0 | fits_k1 |  |
| `openrouter:anthropic/claude-opus-4.6` | 0.062164 | 0.186492 | 8.6833 | 5.0 | 25.0 | fits_k1 |  |
| `openrouter:anthropic/claude-opus-4.7` | 0.062164 | 0.186492 | 8.6833 | 5.0 | 25.0 | fits_k1 |  |
| `openrouter:anthropic/claude-opus-4.8` | 0.062164 | 0.186492 | 8.6833 | 5.0 | 25.0 | fits_k1 |  |
| `openrouter:openai/gpt-5.5` | 0.071590 | 0.214770 | 10.0000 | 5.0 | 30.0 | fits_k1 |  |

## Tested（registry 突合, 9 件）

| model_id | verdict | date | evidence |
|---|---|---|---|
| `openrouter:z-ai/glm-4.6v` | rejected | 2026-06-02 | lesson 20260602_broad_vlm_sweep（21.24% / high30 35% / latency 75s） |
| `openrouter:google/gemini-3.1-flash-lite` | rejected | 2026-06-01 | lesson 20260601_model_drift_newer_gemini_no_recovery（20.86% 統計同等で2倍遅） |
| `openrouter:openai/gpt-5-mini` | rejected | 2026-02-24 | full50 MAE 29.73% vs gemini 21.98%, latency 42s |
| `openrouter:moonshotai/kimi-k2.5` | rejected | 2026-06-02 | lesson 20260602_broad_vlm_sweep |
| `openrouter:qwen/qwen3-vl-235b-a22b-thinking` | rejected | 2026-06-02 | lesson 20260602_broad_vlm_sweep（29.51% / +15.6% 系統過大） |
| `openrouter:google/gemini-3-flash-preview` | adopted | 2026-06-04 | settings.py default; docs/MOZU_MODEL_DECISION_20260603.md |
| `openrouter:google/gemini-3.5-flash` | rejected | 2026-06-02 | lesson 20260601_model_drift_newer_gemini_no_recovery |
| `openrouter:openai/gpt-5.1` | rejected | 2026-06-02 | lesson 20260602_broad_vlm_sweep（22.80% mediocre / high30 35%） |
| `openrouter:google/gemini-3.1-pro-preview` | withdrawn | 2026-06-04 | lesson 20260604_recognition_clean_gt_pro_no_edge_flash_cost_rational |

## Over budget（14 件, 安い順抜粋 5 件）

| model_id | est k1 $/img | in $/1M | out $/1M |
|---|---|---|---|
| `openrouter:openai/o3-deep-research` | 0.105476 | 10.0 | 40.0 |
| `openrouter:anthropic/claude-fable-5` | 0.124328 | 10.0 | 50.0 |
| `openrouter:anthropic/claude-opus-4.8-fast` | 0.124328 | 10.0 | 50.0 |
| `openrouter:openai/o1` | 0.158214 | 15.0 | 60.0 |
| `openrouter:anthropic/claude-opus-4` | 0.186492 | 15.0 | 75.0 |

## Registry にあるが現カタログに無い vlm（1 件）

- `google:gemini-3-flash-preview` — rejected (2026-06-05)
