# Golden Labeling Guide (judge validation)

目的: Claude-as-judge を **ゲートに使える**ようにするための **人手 golden set** を作る。judge は既に discriminative-power ゲート（合成劣化を正しく検出）に合格済みだが、**絶対水準の人間校正**（"39/100"が人の感覚と合うか、絶対floorでゲートしてよいか）は人手ラベルでしか検証できない。設計根拠: `docs/EVAL_RUBRIC.md` / `JUDGE_EVAL_DESIGN_20260602.md`。

## なぜ人手か（重要）
- judge も golden も Claude だと **循環**（自己同意するだけで人の納得感と合っているか分からない）。
- そこで: **Opusが高精度ドラフトを作成 → 人間がレビュー・修正して確定**する。ゼロから付けるより速く、かつ最終判断は人間。

## 手順
1. ドラフトを開く: `evals/judge/golden_set.draft_claude.jsonl`（各行 = 1画像、`dimensions.<dim>.score`(0-5) + reasoning + draft_source="claude_opus")。
2. 各画像について、実際に確認しながらドラフトの 0-5 を**レビュー・修正**する:
   - 写真: `test_images/images/test_food<N>.jpg`
   - GT（真値）: `test_images/images_label_with_nutrition/test_food<N>.json`
   - 採点対象の候補出力: `evals/judge/labeling/test_food<N>.json` の `candidate_output`
3. 各次元 0-5（0=明確に悪い / 5=明確に良い）。重要度 foods > names > portions > nutrients > total。
   - **recognition**: 写真の料理を当て、GTを網羅、捏造なし。
   - **naming_db_match**: matched USDA レコードが受け入れ可能（raw/cooked, 別食品, 過度に一般的 は減点）。
   - **portion_plausibility**: weight_g が写真とGTに妥当。
   - **nutrient_validity**: calculated nutrition が weight×per-100g と整合し妥当。
   - **total_plausibility**: 総量が妥当で、正しい部品から積み上がる（相殺誤差でない）。
   - **user_conviction**: そのまま記録を受け入れるか（総合）。
4. 修正したら各行に `"reviewed_by": "<your name>"` を付け、確定版を `evals/judge/golden_set.jsonl` に保存（同フォーマット、`human_scores` でも `dimensions.<dim>.score` でも可）。
5. 規模: まず ~15-20枚（ドラフトは20枚分用意済み）。最終は 25枚程度まで拡張推奨。

## 検証の実行
```
# judge を golden に対して検証（quadratic-weighted κ と Pearson r を次元別に算出）
python -m apps.freeform_usda_meal_analysis_api.scripts.run_judge_validation \
  --golden apps/freeform_usda_meal_analysis_api/evals/judge/golden_set.jsonl \
  --judge-file apps/freeform_usda_meal_analysis_api/evals/runs/<ts>/judge_gemini3flash_medium.json
```
- 合格基準: 各次元 **quadratic-weighted Cohen's κ ≥ 0.6**（目標0.8）、composite **Pearson r ≥ 0.80**。
- 合格 → judge を昇格ゲートの **絶対floor**（recognition/naming等の非退行）に使用可（v2, `gate.use_judge`）。
- 不合格 → judge は **advisory/相対ランキングのみ**（絶対ゲート不可）。rubric を見直し再検証。

## 注意
- golden は生成プロンプト iteration で**見せない held-out** にする（judge-only holdout）。
- judge_model_id / rubric_version を変えたら golden 検証を**再実行**（drift）。
- ドラフトの数値を鵜呑みにしない。あくまで人間が最終判断。
