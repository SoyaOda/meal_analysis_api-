# mozu モデル採用決定: gemini-3.1-pro（2026-06-03）

このアプリ（`freeform_usda_meal_analysis_api`）は **mozu**（Finch 型の高単価 calorie tracker app）用 API。本ドキュメントは VLM 採用モデルの決定記録（SSOT）。

> ## ⚠️ 2026-06-03 重要訂正（GT 妥当性レビュー後）
> **frozen-50 の GT は GPT-5-pro の推定値**（confidence フィールド・5g丸め重量で確定）。よって本書の **calorie 系の数値は「実精度」でなく「GPT-5-pro との一致度」**。訂正点（詳細・根拠: `evals/lessons/20260603_frozen50_gt_is_gpt5pro_estimate_two_gate_strategy.md`）:
> - **「cal_MAE ~18%」は実精度でない**（=GPT-5-pro一致度）。**実精度はレンジで報告**（50: ~18% 楽観床 / Nutrition5k 実測GT: ~58% 悲観天井, 真値は中間）。
> - **pro の「-5.3% 過小バイアス」は LABELER アーティファクト**（実測GTでは **+30.7% 過大**に反転）。→ **下記 follow-up #1（calorie under-bias 補正）は VOID／一旦停止**（適用すると実精度が悪化）。`calorie_calibration_pro_v13.json`（50-fit）も **VOID**（gemini→GPT-5-pro を学習しており実カロリーを保証しない）。
> - **pro 採用は維持**（独立実測 N5k で calorie MAE が方向的に一貫して ~7pt 低い＋過大bias が小＋決定的 recognition F1 4/4）。**ただし採用根拠から frozen-50 の calorie 数値は外す**。⚠️ **2 run 目で再現確認: calorie 優位は「有意」でなく BORDERLINE**（denoised paired CI[-15.2,+0.9] p=0.076。run1単独 CI[-18.5,-1.3] は楽観 draw）。かつ **pro は run間再現性が flash より低い**（bit-identical 率 20% vs 52%, median |Δrun| 10pt vs 0pt）＝本番で同写真→kcal 揺れが大きいトレードオフ。詳細 `evals/lessons/20260603_n5k_pro_advantage_test_retest_borderline.md`。
> - **eval 戦略 = TWO-GATE**: GATE A=Nutrition5k 総カロリー（独立実測・方向/回帰チェック, totals-only）／GATE B=frozen-50 **画像**（phone-angle 現実性＋相対A/B; ラベルは真値扱いしない）。**真のゲート=実ドメイン実測アンカー（要構築: Western・eye-level phone 写真 20-50枚を実測×USDA）**。
> - **Nutrition5k へ全面切替はしない**（俯瞰/cafeteria＝分布違い・「general Western」でない・名前不一致で recognition 不可信・affine calib が自前 held-out で 132% に暴発）。tuning/calibration の対象にはしない。

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
1. ~~**calorie under-bias の補正（必須・本番化前）**~~ → **🔴 VOID／停止（2026-06-03訂正）**。狙っていた「-5.3% 過小」は GPT-5-pro ラベラーの符号で、**実測GTでは +30.7% 過大**。`calorie_calibration_pro_v13.json`（50-fit, slope0.606/int315）も `pro_n5k.json`（N5k-fit, 自前held-outで132%に暴発）も **VOID**。**calibration は実ドメイン実測アンカーで・乗算的(slope-only, intercept=0)に再 fit するまで両方 enabled=false 維持**。
2. **naming 微回帰の回収（安価）**: pro + 修正済み reranker instruction（bug 修正済, [[evals/lessons/20260602_reranker_instruction_was_inert_bug_fixed]]）の A/B。
3. **judge の golden 確定**: 人手 golden で κ 検証 → conviction を「真のゲート」化（ドラフト `evals/judge/golden_set.draft_claude_v2.jsonl` レビュー）。
4. **本番 deploy**: Firestore `config.vlm.model_id` を pro へ＋ calibration config 配備（要明示指示・要 OpenRouter 予算確認）。

## 関連 lesson
- `evals/lessons/20260603_pro_stability_confirmed_and_calorie_bias_calibrated.md`（stability 4/4 + bias 補正）
- `evals/lessons/20260603_gemini31pro_promote_hold_adversarial_verified.md`（adversarial review・over-claim 訂正）
- `evals/lessons/20260603_gemini31pro_breaks_recognition_ceiling_deterministic.md`
