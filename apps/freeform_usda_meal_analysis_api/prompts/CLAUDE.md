# prompts/ — 過学習防止ルール（path-scoped）

このディレクトリのVLMプロンプトを作成・編集するときは次を厳守する。

- **評価データ固有情報を埋め込まない**: `test_foodXX` / 画像ID / ground truth の数値 / label の `search_name`・`weight_g`・カロリー値、および50枚評価セットに過適合した料理名語彙を prompt に含めない。
- 改善は**一般化可能な指示**として書く（例: 「皿/碗の直径を先に推定してスケールの基準にする」「rice/pasta/積み重ね食品は密度を考慮する」「目に見えない調理油・脂を加味する」）。汎用的な栄養知識・推定方法はOK。
- 新しい prompt は既存命名規則 `freeform_prompt_usda_format_ver_<ver>_<slug>_<YYYYMMDD>.txt` に従う。
- 採用判定に使った prompt は、再現性のため実験config (`evals/configs/*.json`) の `prompt_text` にも保持し、lesson に `prompt_sha256` を記録する。

詳細は `apps/freeform_usda_meal_analysis_api/AGENTS.md`（Anti-Overfitting Policy / Prompt Reproducibility Rules）を参照。
