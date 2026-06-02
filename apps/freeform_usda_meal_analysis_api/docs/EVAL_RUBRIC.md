# Eval Rubric (canonical) — full-output / user-conviction

正典ルーブリック。詳細な設計根拠・出典は `docs/JUDGE_EVAL_DESIGN_20260602.md`。`AGENTS.md` / `CLAUDE.md` はここにリンクし重複させない。

## KPI
最終KPIは総カロリー精度ではなく **USER CONVICTION**: ユーザが自分の写真とアプリ出力（認識した料理/食材・分量g・全栄養素）を見て「正しい、そのまま記録してよい」と納得するか。重要度順（JMIR 2025）: foods > names > portions > nutrients > total。

## 2層構成
- **Tier 0（決定論的・写真不要・コスト0・常時）** — `scripts/run_pdca_batch_eval.py` が算出、summary.json に追加キー:
  - `recognition_agg` {recall, precision, f1}: pred↔GT を Hungarian で1対1マッチ。similarity = `max(char-LCS, content-token-overlap)`（USDA冗長名↔短いGT名に対応、difflib単独のF1≈0.07を解消）。`similarity_fn` は pluggable（embedding backend推奨・要依存承認）。閾値 T=0.75 は held-out で調整し評価50では調整しない。
  - `portion_bands` {within_10, within_25, gross}: マッチ item の |pred_g-gt_g|/gt_g。
  - `nutrient_self_consistency_rate`: 各item calories/weight_g が 0.1–9 kcal/g の妥当範囲内の割合。
- **Tier 1/2（Claude(VLM)-as-judge）** — subagent `meal-output-judge`。写真+GT両方にgrounding、6次元0-5。コストcascade（routine=15-20枚 / full50=昇格候補・曖昧subsetのみ）+ output-hash cache。

## 6次元（judge, 各0-5）
| 次元 | 重み | 何を見るか |
|------|------|-----------|
| recognition | 0.30 | 写真にある料理をGT網羅で当て、捏造しないか |
| naming_db_match | 0.25 | matched USDAレコードが受け入れ可能か（raw/cooked, beef/pork等） |
| portion_plausibility | 0.20 | weight_g が写真とGTに妥当か |
| nutrient_validity | 0.15 | calculated_nutrition が self-consistent & 妥当か |
| total_plausibility | 0.10 | 正しい部品から積上がるか（相殺誤差でないか） |
| user_conviction (holistic) | — | そのまま記録を受け入れるか（融合に入れずcross-check） |

`overall_conviction (0-100) = 100 × Π (score_d/5)^{w_d}`（D1–D5の**幾何平均**: 1次元崩壊で全体が落ちる=信頼の性質に一致。score 0→0.01 クランプ）。重み±0.05はρ>0.95で安定。重みは config に記録し無断調整禁止。

## バイアス対策（必須）
- 入力は **写真→GT→候補** の順（image-first / anti-anchoring）。写真は認識/分量妥当性のみ、数値truthはGT。
- **verbosity bias 最大**: 長いUSDA名≠良い。blind judging（候補のmodel/prompt情報除去）。dish順 randomize。
- **pointwise を primary**（longitudinal追跡・floor）。pairwise は最終adopt時のみ両順序consistent。
- **multi-sample N≥3 平均**、seed記録。
- judge=Claude / generator=Gemini の cross-family（self-preference中和）。model_idは固定pin。

## 検証（信頼の前提・これ未達ならjudgeはadvisoryのみ、ゲート不可）
- human golden 15-25枚で per-dimension **quadratic-weighted κ≥0.6**（目標0.8）, composite **Pearson r≥0.80**。
- **perturbation/discriminative-power gate**: 合成劣化（誤食品置換 / 分量2倍 / 食品正のままcalorie2倍=相殺誤差 / 悪DBマッチ / 言い換え不変）で judge が正しい次元を下げるか。
- `judge_model_id` or `rubric_version` 変更ごとに再検証（drift; minor bumpで3-8pt）。
- `judge_vs_numeric_corr` を記録、judge↑だがMAE↓は judge-gaming 疑い→human spot-check。

## ゲート（conviction は calorie MAE を補完・置換しない）
promote は **全AND**: ①既存品質ゲート ②calorie paired-BCa CI<0 ③per-dimension FLOOR非退行（recognition/naming/portion/nutrient）④conviction paired-delta 非負 & Wilcoxon p<0.05 ⑤p95(worst tail)も。
→「**間違った食品なのに総カロリーが合う**」候補を promote 不能化。未検証judge/contract欠落時は理由付きHOLD（silent promote禁止）。`gate.use_judge` は default OFF。

## 版管理 / anti-leakage
- `judge_contract = {judge_model_id, rubric_version, prompt_sha256, embedding_model_id, n_samples, weights, seed}` を artifact に pin。
- ルーブリックは `evals/judge/judge_rubric_vN.txt` で版管理。`detect_prompt_leakage` をルーブリックにも適用（test ID/GT数値/per-image閾値を埋め込まない）。
- judge-only holdout（`evals/splits/judge_holdout_v1.txt`）を生成prompt iterationで見せない。

## ロードマップ
- **v0（実装済）**: Tier0 決定論的指標（recognition F1 token-overlap, portion bands, nutrient self-consistency）。
- **v1（要承認）**: `scripts/run_judge_eval.py`（finished run を後処理）+ rubric_v1 + golden検証。要: (1)embedding/SDK依存可否, (2)golden 15-25枚人手ラベル。
- **v2（v1検証合格後）**: judge floor + conviction delta を `gate_decision` に flag配線（default OFF）。
