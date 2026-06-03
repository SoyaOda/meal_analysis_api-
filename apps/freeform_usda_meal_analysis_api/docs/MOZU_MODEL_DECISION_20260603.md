# mozu モデル採用決定: gemini-3.1-pro（2026-06-03）

このアプリ（`freeform_usda_meal_analysis_api`）は **mozu**（Finch 型の高単価 calorie tracker app）用 API。本ドキュメントは VLM 採用モデルの決定記録（SSOT）。

## 決定
- **採用候補モデル = `openrouter:google/gemini-3.1-pro-preview`**（既定。settings.py / config_manager 既定も更新済）。
- `openrouter:google/gemini-3-flash-preview` は安価代替として残す。
- 本番 Cloud Run / Firestore は本決定では未変更（deploy は別工程・要明示指示）。

## 根拠（gemini-3.1-pro vs gemini-3-flash, 同 v13 prompt の clean A/B）
判定は ADVISORY な LLM-judge（sonnet-4.6 rubric v2, 0.944 discriminative gate 合格・golden 未確定）＋ 決定的メトリクス＋ paired bootstrap CI。

### 確実（artifact 直・credit 不要）
- **recognition（決定的 Hungarian F1）が flash 比で 4/4 独立 run 再現的に向上**: Δ = +0.062 / +0.016 / +0.031 / +0.019（recall・precision とも↑）。per-dish correct% 13.5%→16.5%（full50）/+2.9〜4.5pt。
- **conviction（headline KPI）も 4/4 run で pro>flash**（+1.93 / +1.52 / +2.39 / +2.10, mean +1.99）。ただし各 run は CI 重複で個別 NS（n=40-50 の限界）。
- **worst-tail calorie 改善**: high_error_rate_30% 18→14、abs_kcal_mae 136→122。

### 非有意 / トレードオフ
- raw total-calorie MAE 19.54→17.32 は paired CI[-10.99,+3.02] p=0.56 で **NS**。harness gate は両候補 `hold`（=自動昇格はしていない。mozu 方針として人的に採用）。
- **naming_db_match が一貫して微減**（Δ -0.10〜-0.15, 4/4）。命名は VLM 後の reranker で効くので回復余地（下記 follow-up）。
- calorie signed bias が flash +1.2% → pro **-5.3%（系統的過小）**。→ calibration で補正（下記）。

## コスト（実トークン × OpenRouter 現行価格）
- 単価: flash input$0.5/output$3 per M → pro input$2/output$12 per M（4x）。1食 ≒ prompt1862tok（画像込）+ completion: flash1951 / pro1518。
- **per-meal**: flash $0.0073 → **pro $0.0224**（VLM 部分 3.23x。pro は completion が少なく 4x 未満）。calibration 層は affine 計算のみ＝$0。
- **1ユーザー（記録 3-5食/日）**: pro 月 $2.0〜3.4 / 年 $24.6〜41.0。flash 比の割増は **+$16.6〜27.7/ユーザー/年**。高単価アプリ mozu では許容範囲。

## レイテンシ（PDCA 全 run 統合, 各 n=170, フルパイプライン秒）
- flash mean 32.9s / median 30.5s / p95 62.9s。pro mean 33.1s / median 31.8s / p95 **51.8s**。
- **pro/flash = 1.01x（+0.2s）＝実質同等**。pro は completion が少なく相殺＋遅延は VLM 以外の固定部（embedding＋FAISS/BM25＋DeepInfra reranker＋栄養）が支配。速度ペナルティ無し。

## 採用前提・follow-up（ロードマップ）
1. **calorie under-bias の補正（必須・本番化前）**: calibration 層を**外部 held-out データで fit**してから enable。現状 `evals/calorie_calibration_pro_v13.json`（eval50 内 fit, enabled=false）は暫定。disjoint 検証では pro+calib MAE 13.98%（bias -1.6%）> flash+calib 15.61%。
2. **naming 微回帰の回収（安価）**: pro + 修正済み reranker instruction（bug 修正済, [[evals/lessons/20260602_reranker_instruction_was_inert_bug_fixed]]）の A/B。
3. **judge の golden 確定**: 人手 golden で κ 検証 → conviction を「真のゲート」化（ドラフト `evals/judge/golden_set.draft_claude_v2.jsonl` レビュー）。
4. **本番 deploy**: Firestore `config.vlm.model_id` を pro へ＋ calibration config 配備（要明示指示・要 OpenRouter 予算確認）。

## 関連 lesson
- `evals/lessons/20260603_pro_stability_confirmed_and_calorie_bias_calibrated.md`（stability 4/4 + bias 補正）
- `evals/lessons/20260603_gemini31pro_promote_hold_adversarial_verified.md`（adversarial review・over-claim 訂正）
- `evals/lessons/20260603_gemini31pro_breaks_recognition_ceiling_deterministic.md`
