# Phase: mozu API（2026-06-03〜）

このアプリ（`freeform_usda_meal_analysis_api`）を **mozu**（Finch 型の高単価 calorie tracker app）用 API として開発するフェーズ。ブランチ `feature/mozu-api`。
前フェーズ（PDCA 土台整備＋モデル探索）は `plans/done/deep_review_improvements_20260601.md` にアーカイブ。

## Goal
mozu に組み込む写真カロリー推定 API を、採用候補 **gemini-3.1-pro** を軸に本番投入できる品質まで仕上げる。

## 採用済み決定（SSOT: `docs/MOZU_MODEL_DECISION_20260603.md`）
- **VLM 採用候補 = `openrouter:google/gemini-3.1-pro-preview`**（settings.py / config_manager 既定を更新済）。
  - recognition が flash 比 4/4 run 再現的に向上、conviction も 4/4 で +方向（個別 NS）、**レイテンシ同等（+0.2s）**、コスト ~3.2x（高単価アプリで許容）。
  - flash は安価代替として保持。
- 本番 Cloud Run / Firestore は未変更（deploy は別工程）。

## Exit Criteria（本番投入の条件）
| 項目 | 閾値 | 現在 |
|------|------|------|
| calorie under-bias 補正 | 外部held-out fit の calibration で signed≈0 | pro: eval内fitで -5.3%→-1.6%（**外部fit未**） |
| naming 回帰の解消/許容 | naming_db_match が flash 同等以上 or 許容判断 | pro -0.125（4/4, 未解消） |
| judge を真のゲート化 | human golden κ≥0.6 | 未（draft 準備済） |
| 本番 deploy | Firestore model=pro + calibration 配備 | 未（要明示指示・予算確認） |

## Roadmap（推奨順）
1. ~~naming 回帰の回収（reranker）~~ → **実施済・不成立**（form-tuned reranker は naming 回復せず raw_vs_cooked 悪化。naming は VLM クエリに形態が無く reranker 非対応）。pro 小回帰(-0.125)は**据え置き許容**。lesson `20260603_pro_naming_reranker_form_did_not_recover`。
2. **calorie calibration の本番化準備（次の本命）**: 外部（eval50 と disjoint な mozu 実データ等）ラベルを収集 →`fit_calorie_calibration.py` で fit → held-out 検証 → `config/calorie_calibration.json` を enable。pro の -5.3% under-bias 補正に必須。
3. **judge golden 確定**: `evals/judge/golden_set.draft_claude_v2.jsonl` を人手レビュー → `golden_set.jsonl` → `run_judge_validation --golden` で κ。合格次第 conviction を採用ゲートに。
4. **公開前: 多様な外部テストセット**（cuisine/パッケージ食品/実環境写真）で汎化検証。現状は狭い Western プレート50枚のみ＝公開分布未検証。
5. **本番 deploy**: 上記が揃い次第、Firestore `config.vlm.model_id`=pro ＋ calibration を配備（要ユーザ明示指示・予算確認）。
- 余技 follow-up: full-fat-default 単独 reranker で決定的 cal_MAE 改善（24.55→19.67 観測）が残るか isolate。

## 引き継ぎ済みの土台（前フェーズ成果, 全て利用可）
- PDCA: paired BCa bootstrap CI ゲート + 強制 stability（`scripts/run_pdca_batch_eval.py` 他）。
- portion = 決定的メトリクス（`dish_match_metrics.portion_score_0_5`）、LLM portion は advisory。
- calorie calibration 層（`core/calorie_calibration.py`, default OFF, affine）。
- LLM-judge（`scripts/run_judge_eval.py`, rubric v2, advisory）+ 0.944 discriminative gate 合格。
- 検索: hybrid（FAISS IP cosine + BM25 + RRF + Qwen3-Reranker）。**reranker instruction bug 修正済**（query 焼込）。
- self-verification 2nd pass（opt-in, default OFF。同一tier verifier は非有効）。
- 知見は `evals/lessons/`（20+本）に蓄積。

## Non-Negotiables（前フェーズから継続）
- 採用判定は原則50例フル評価 + Ground truth総カロリー比較 + 安定性（複数 run）。
- 過学習防止: prompt に評価データ固有情報を埋め込まない。calibration は eval と disjoint なデータで fit。
- PDCA評価は原則 `use_vlm_cache=false`（同一VLMの reranker-only A/B 等の isolation 目的では cache=true を justified exception として明記）。
- 本番（Cloud Run/Firestore）操作・deploy は要ユーザ明示指示。
- promote 主張は run 自身の artifact のみ引用（cross-run 値は文脈）。

## Session Log
| Date | Session | 作業内容 |
|------|---------|---------|
| 2026-06-03 | mozu-pivot | **mozu phase 開始**。pro を採用候補に決定（recognition 4/4再現・速度同等・コスト ~3.2x/+$16-28/ユーザー/年）。settings.py/config_manager 既定を pro に、model-focus doc 4箇所更新、決定記録 `docs/MOZU_MODEL_DECISION_20260603.md` 作成。前フェーズを `plans/done/` にアーカイブ。ブランチ `feature/mozu-api` 作成。 |
| 2026-06-03 | mozu-pivot | **naming回復 A/B(#1) → 不成立**: pro+形態双方向reranker vs pro+現行(cache共有でreranker isolate, 39/40でレコード変化)。判定: **raw_vs_cooked 20→25悪化・correct% 19.1→16.4↓・conviction↓**で naming回復せず(over-steering)。但し**決定的cal_MAE 24.55→19.67(-4.9pt)改善**(主にfull-fat-default由来と推定)。**naming は reranker非対応(形態signalがVLMクエリに不在)→ VLMプロンプト側課題**。pro小回帰(-0.125)は据え置き。follow-up: full-fat-default単独でcal改善が残るか。lesson: `20260603_pro_naming_reranker_form_did_not_recover.md`。 |
