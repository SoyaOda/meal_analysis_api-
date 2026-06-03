# mozu 外部テストセット: 自律取得の可否と計画（2026-06-03）

公開後の多様な食事写真への汎化を検証するための外部テストセットを、**人手ラベル無し・mozu 実データ無しで自律取得できるか**の徹底リサーチ結果（5エージェント workflow）と実行計画。

## 結論: PARTIAL-YES（部分的に可能）
- **認識(recognition)の汎化検証は完全に自律可能**（多様 cuisine のラベル付き画像データセットが豊富。GT は食品名でよく、栄養GT不要）。ユーザーの懸念（多様写真での hallucination/wrong-food）を直接突ける、最も安価で高価値。
- **カロリーの汎化検証は「実測GT付きデータ」=Nutrition5k 等に限られる**（cafeteria/プレート料理のみ。多様 cuisine やパッケージ食品の実測栄養は存在しない）。
- **真の「公開分布 ×実測ポートションカロリー」は自律取得不可** → 公開後の実ユーザー写真＋独立ラベル（実測/ラベル/管理栄養士）が唯一の本物。撮影後に質量は復元できないため後付け不能。
- **LLM 生成 GT は使用不可（循環的でバイアス）** — 確定ルール。

## 自律取得できるソース（ライセンス込み）
| ソース | GT栄養 | GT食品名 | 多様性 | License | 用途 |
|---|---|---|---|---|---|
| **Nutrition5k**(Google, CVPR21) | ◎実測(cal/mass/macros+成分質量) | 成分ラベル | 低(単一cafeteria/Western/俯瞰) | CC BY 4.0(商用可) | 独立カロリー検証(プレート全体食) |
| NutritionVerse-Real | ○栄養(~889img/251dish) | 部分 | 低-中 | 研究 | カロリー補強(小N) |
| **Open Food Facts** | ○パッケージ per-100g | ○ | 高(パッケージ/多国) | 画像CC-BY-SA/データODbL | パッケージ食品の命名+ラベル栄養 |
| USDA FDC Branded | ○ per-serving | ○ | 高(US branded) | CC0 | OFF補完(画像少) |
| **ISIA Food-500** | × | ○(500多cuisine) | 高(中/日/西明示) | 研究 | 認識汎化(cuisine横断) |
| Food-101 / FoodX-251 / Food2K / UEC-Food256 | × | ○(細粒度) | 中-高 | 研究 | 認識汎化の幅 |
| FoodSeg103 | × | ○成分マスク | 中 | 研究 | 多item認識(取りこぼし) |
| Recipe1M+ → USDA | △近似(レシピ材料→栄養, 一皿単位) | ○ | 高(多cuisine) | 研究 | 粗いカロリー汎化(ポーション曖昧) |

## 実行計画（多層, 現harness互換）
- **Tier 1 — 認識汎化（自律・最優先・栄養GT不要）**: ISIA Food-500 / FoodX-251 / Food2K から cuisine 横断で ~150-300枚サンプル → pro vs flash → 認識(name-match)。pro の hallucination/wrong-food 優位が Western50枚の外でも保たれるか。**ユーザー懸念を直接検証**。
- **Tier 2 — 独立カロリー汎化（自律・プレート食）**: Nutrition5k の**俯瞰RGB画像＋栄養CSV**を pull(CC BY 4.0) → total cal/macros(+成分質量を items に)を harness 化 → pro(+calibration) vs flash。実測GTで最強のカロリー検証。NutritionVerse-Real で補強。
- **Tier 3 — パッケージ食品（自律）**: Open Food Facts の商品画像＋per-100g 栄養をサンプル → branded 認識 + DB照合/栄養 lookup。50枚が完全に欠く大カテゴリ。命名/ラベル栄養を検証(ポーションは非対象)。
- **横断**: 現50枚を in-distribution 基準として、50＋3 tier を**横並びで報告**し汎化ギャップを可視化。calibration は Tier-2 の disjoint split で fit/検証（eval50 でなく独立データで pro -5.3% bias 補正）。

## 自律 vs 要・実データ
- **自律可**: Nutrition5k/OFF/認識データセットの DL＋harness 整形、pro-vs-flash 実行、独立データでの calibration fit/検証。
- **要・実データ/人手**: 真の公開分布(実ユーザー phone 写真・多cuisine・パッケージ・実ポーション)の検証＝公開後の実写真＋独立ラベルが必須。任意写真の実測ポーションカロリー。Nutrition5k 成分→USDA search_name マッピング(完全 dish-match 必要時)。

## 注意（各 tier は stress-test であって本番ゲートではない）
- Nutrition5k=単一 cafeteria/俯瞰/Western（それ自体が一分布）。OFF=商品写真でプレート写真でない（ポーション非検証）。認識データは 1画像1GT名・研究ライセンス(内部利用のみ・再配布不可)。Recipe 由来は一皿単位で近似。

## コスト/工数
- DL は無料(Nutrition5k は俯瞰のみ抽出で軽量化, OFF/認識はサンプリング)。整形は各ソースのラベル→harness schema 変換が要(中程度)。**eval は ~300-600画像で OpenRouter ~\$10-25(pro+judge)**。現残 ~\$11 は全 tier 同時には不足 → 補充 or tier ごと。

## Ready-to-run（2026-06-03 構築済・クレジット補充後にそのまま実行）
Nutrition5k 250枚は構築済（`test_images_n5k/`, gitignore・seed7 再現可）。他PCでは先に再構築:
```
python -m apps.freeform_usda_meal_analysis_api.scripts.build_nutrition5k_evalset --limit 250 --workers 16 --seed 7
```
評価（ローカルサーバ起動後。pro は既定モデル。harness の dir 上書きで N5k を指す）:
```
# pro vs flash を N5k 250枚で（独立実測GTで calorie MAE / recognition F1 / paired CI）
python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini31pro_vs_flash_dev40_20260602.json \
  --api-url http://localhost:8006 \
  --images-dir test_images_n5k/images \
  --labels-dir test_images_n5k/images_label_with_nutrition \
  --limit 250 --no-use-vlm-cache
```
外部 calibration の fit/検証（N5k を FIT/TEST に分割。eval50 と disjoint）:
```
# run-dir = 上記 run の出力。candidate = pro_v13。FIT/TEST split は index ファイルで指定
python -m apps.freeform_usda_meal_analysis_api.scripts.fit_calorie_calibration \
  --run-dir <n5k_run_dir> --candidate pro_v13 \
  --fit-split <n5k_fit.txt> --test-split <n5k_test.txt> \
  --config-out apps/freeform_usda_meal_analysis_api/evals/calorie_calibration_pro_n5k.json
```
推定コスト: pro 250枚 ~\$5.5 + flash ~\$1.7 + judge(任意, recognitionは決定的で judge 不要) → カロリー検証だけなら ~\$7。判定後に lesson + baseline 追記。

## Fallback（方法を採らない場合）
50枚据え置きは「in-distribution の相対比較」としてのみ妥当で、**pro の優位は公開分布で未証明**と明記必須。その場合でも**最低 Tier 1（多様 cuisine 認識チェック）だけは実施推奨**（安価・栄養GT不要・懸念を直接検証）。
