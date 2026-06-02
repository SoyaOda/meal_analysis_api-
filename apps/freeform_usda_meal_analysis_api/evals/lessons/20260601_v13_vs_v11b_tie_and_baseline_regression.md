# Lesson: v13-beverage ≈ v11b (tie) + baseline no longer reproduces (~2x regression)

- Date: 2026-06-01
- Model: `openrouter:google/gemini-3-flash-preview`
- Run: `evals/runs/20260601_204037` (full50, remote prod API, `use_vlm_cache=false`, paired BCa gate)
- Decision: **Hold / keep production prompt (v13). Do NOT update baseline.** Investigate model/infra drift (top priority).

## Context
本番Firestoreは v7 ファイル名だが、実際は **2841字のカスタム prompt_text override = v11b＋飲料対応** を配信していた（`updated_by admin`, `2026-02-26`）。どのcommit済promptとも不一致のため `prompts/freeform_prompt_usda_format_ver_v13_beverage_subject_prodcapture_20260226.txt` として保全し、v13 と呼ぶ。
v13 と v11b の差分: 飲料主体の写真を dish として扱う（v11b は背景飲料を無視）。

## Paired result (v13 vs v11b, full50, paired baseline = v11b)
| candidate | mae% | mae 95%CI | p50 | p90 | high30 | latency | paired Δ(vs v11b) 95%CI | p |
|---|---|---|---|---|---|---|---|---|
| v11b_baseline | 20.27 | [15.73, 26.65] | 17.00 | 36.65 | 20.0 | 20.0s | — | — |
| v13_beverage_prod | 20.73 | [16.88, 25.96] | 16.36 | 43.95 | 18.0 | 18.8s | **[-4.73, +4.56]** | **0.84** |

- paired Δ(v13 − v11b) = +0.46pt, 95%CI が0を大きくまたぐ、sign-flip p=0.84。
- → **v13 と v11b は calorie MAE で統計的に区別不能（非劣性）**。50枚に飲料主体写真がほぼ無いため妥当。
- config-fidelity 確認: 全行 `model_used=gemini-3-flash-preview`, `prompt_used=[Custom Prompt Text (API Override)]` → per-request override が適用済み（eval は正しい構成を計測）。

## 🚨 重大: baseline が再現しない（model/infra ドリフト疑い）
- `current_baseline.json`（2026-02-25, v11b temp03）= **mae 11.38% / high30 4.0%**。
- 本runの v11b（同一prompt・同一model）= **mae 20.27% / high30 20.0%**。**約2倍の劣化**。
- 誤差は10/50枚が>30%に分散（単一外れ値ではない）。worst: test_food15(87.8%), test_food44(84.8%), test_food18(67%).
- 3ヶ月の経過 + `-preview` モデル + OpenRouter provider routing 変化が最有力原因。

## What worked
- paired BCa bootstrap gate が「v13≈v11b（有意差なし）」を正しく検出（単発MAE比較では0.46pt差を誤って解釈しうる）。
- config-fidelity（model/prompt 記録）で eval が正しい構成を計測したことを確認。

## What did not work / open
- 旧baseline(11.38%)が再現しない。**採用判定の絶対基準が無効化**。
- portion推定/検索の改善以前に、まず **現行システムの実力を再ベースライン**する必要。

## Action taken
- v13 prompt を `prompts/` に保全し、`settings.py DEFAULT_PROMPT_FILE` と `config_manager VLMConfig.prompt_file` のコード既定を v13 に昇格（= 本番稼働中promptと一致, 再現性確保）。
- baseline は **更新しない**（劣化を昇格扱いにしない）。
- 本番configは変更しない（v13ファイルは未デプロイ。prodのprompt_text override がv13内容の唯一の保持先。label修正はデプロイ後）。

## Next hypotheses (recommended priority order)
1. **再ベースライン**: v13 を full50 + 反復(`run_pdca_repeated_eval`)で再評価し、現行の真の baseline を確立。
2. **ドリフト調査**: 同一画像で model snapshot 固定 / provider 固定 (OpenRouter `provider` ルーティング) を試し、11%→20% の原因を切り分け。`gemini-3-flash-preview` が更新された可能性 → 固定版/別modelの再評価。
3. 継続監視（nightly eval + /health config_drift）で次回の劣化を即検知。
