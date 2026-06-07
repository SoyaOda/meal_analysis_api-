# mozu アプリ UI/UX 実装ハンドオフ — E13 データ収集 & E14 校正（将来参照用）

- date: 2026-06-07
- status: **HANDOFF / 実装仕様**（backend 試行錯誤は一旦完了。ここから先は「アプリで実データを集める」フェーズ）
- 対象読者: 将来 **mozu アプリの UI/UX を実装する人**（このリポジトリの PDCA 文脈を知らなくても着手できるよう自己完結 + 深掘りは相互リンク）
- 深い根拠: `docs/E13_DATA_COLLECTION_PLAN_20260606.md`（なぜ/層化/n 設計の SSOT）, lesson `evals/lessons/20260606_e14_conditional_calibration_poc_works_indomain_but_lab_data_does_not_transfer.md`（校正の効き方・転移失敗の定量）, `plans/current.md`（運用 SSOT）, データ契約の実体 `scripts/ingest_e13_collection.py`。

---

## 0. なぜこの文書があるか（30秒サマリ）
mozu のカロリー精度 PDCA は **prompt / schema / retrieval / モデル選択 / self-consistency / 校正 PoC まで実施し天井に到達**、本番スタック（flash + E7 + light + SC K=3 + E2）も出荷済み。**残る唯一の本命レバー = E14 条件付き校正**で、それは **実 mozu ドメインの weighed（写真＝実測した皿）データ = E13** が前提。E13 収集は **物理計量 + eye-level 撮影をユーザー/オペレータが行う**ので、**mozu アプリの UI/UX 実装が必要**。
→ **この文書 = ① E13 をアプリ機能としてどう作るか（データ契約 + 画面要件）+ ② 集めた後の E14 fit→検証パイプライン（実装済み・データ待ち）** を、実装着手時に正しく参照できる形でまとめたもの。

## 1. 認識合わせ：backend 試行錯誤は「一旦完了」で正しい
| 区分 | 状態 |
|---|---|
| prompt/schema/retrieval/model/SC の探索 | ✅ **天井マップ済み**（本命レンジ ~20-24% は純粋 variance floor。`plans/current.md` の「天井マッピング」参照） |
| 本番スタック | ✅ 出荷済み（flash + E7 top_n5 + 0.6B light + SC K=3 resilient + E2 floor20） |
| E13 ingestion インフラ | ✅ 実装済み（`scripts/ingest_e13_collection.py`、turnkey・E2E 検証済） |
| E14 条件付き校正 | ✅ **PoC で機構確認済**（in-domain −18.5pt）。本実装は data 待ち |
| **E13 実ドメイン weighed 収集** | 🔴 **未着手＝唯一の律速。アプリ UI/UX が必要（本文書の主題）** |
| E8 user_context | 🟡 配線済だが、実ドメイン photo+context signal が要る（=同じく app 依存） |

**結論**: 「精度を上げる backend 試行錯誤」は完了。残りは (a) アプリで E13 を集める（②の前提）、(b) 集まったら実装済みパイプラインで E14 を fit/検証。**data 無しで進められる backend の探索は無い**（n=50 単発は draw-noise ±3pt で判定不能、lab データは実ドメインに転移しないことが定量確定済み）。

---

## 2. ① E13 収集プロトコル — アプリ機能仕様

### 2.1 ゴールと不変条件（load-bearing）
- 作るもの: **weighed（写真＝実測した皿）かつ 実 mozu ドメイン（実 eye-level スマホ写真）**の `{ photo → per-item grams + per-item nutrition + stratum }`。
- **pixel から grams は復元不可**（単眼スケール曖昧）→ **撮影の瞬間に計量**し、写真を GT に *ペア付け*する。これが全設計の前提。
- 非交渉:
  - **per-item grams + per-item nutrition + stratum を全件必須**（欠損は ingest が hard-fail。fallback 禁止）。
  - 専門家(管理栄養士)は **食品 ID / 材料リストの QA のみ**。**推定 portion を GT にしない**（写真推定は ~50%+ 誤差＝我々が消したい当のもの）。

### 2.2 データ契約（アプリが必ず出力する形）★最重要
アプリは **1 食 = 1 枚の eye-level 写真 + 1 つの JSON manifest** を出力すれば、後段（ingest→harness→eval→E14）は完全 turnkey。`scripts/ingest_e13_collection.py --template` で実スキーマを出力可能。

**meal レベル**
| field | 必須 | 許容値 / 形式 | UI 入力 |
|---|---|---|---|
| `image` | ✅ | コレクションdir相対の画像パス（eye-level 写真） | カメラ撮影 |
| `meal_name` | 推奨 | 文字列 | テキスト |
| `angle` | ✅ | `eye-level` \| `overhead`（**eye-level を優先収集**） | 撮影ガイドで自動/選択 |
| `container` | ✅ | `plate` \| `bowl` \| `takeout` \| `tray` | 選択 |
| `size_bucket` | ✅ | `auto`（total kcal から自動: <300=lt_300 / <700=300_700 / <1500=700_1500 / else gte_1500）\| 明示値 | 通常 `auto` |
| `cuisine` | 任意 | 文字列（例 american, japanese） | 選択 |
| `eat_context` | ✅ | `home` \| `restaurant` \| `chain` | 選択 |
| `fat_level` | ✅ | `lean` \| `mixed` \| `high_fat` | 選択 |
| `ingredients` | ✅ | 下記 item の非空配列 | 計量フロー |

**ingredient レベル（item ごと・数値は全て必須）**
| field | 必須 | 形式 | 取得元 |
|---|---|---|---|
| `name` | ✅ | 文字列 | 食品検索 |
| `grams` | ✅ | 数値（**秤で実測**） | 0.1–1g 秤 |
| `calories` | ✅ | 数値（per-item 合計 kcal） | USDA/FNDDS×grams / barcode / chain menu |
| `protein_g` / `fat_g` / `carbs_g` | ✅ | 数値（g） | 同上 |
| `fdc_id` | 任意 | 文字列（provenance） | USDA FDC |

> 出力ハーネス形式（ingest が自動生成・参考）: `test_images_<name>/images/test_food{i}.jpg` + `images_label_with_nutrition/test_food{i:02d}.json`（`total_food_weight_g` + per-item `weight_g`/`nutrition` + `stratum` を保持）→ `run_pdca_batch_eval` にそのまま流れ、`decomposed`(grams比/density比) と `dish_match_agg` を自動 emit。

### 2.3 収集フロー（weigh-as-you-plate, eye-level）
1. **0.1–1g 秤で逐次盛り付け**: 材料を1つずつ載せ、**incremental grams を記録**。
2. **per-item GT 計算**: `USDA/FNDDS の per-gram 栄養 × 実測 grams` → per-item kcal + P/F/C + grams（実測なら誤差 <5%＝参照標準）。
3. **盛り付け直後に eye-level で 1–3 枚撮影**: リアルなスマホ角度/光。任意で既知参照（標準皿/カトラリー、任意で fiducial）をフレーム内に（eval を honest に）。
4. **stratum メタを記録**（§2.5）。
5. **専門家 QA**: 食品 ID / 材料リストの検証、実装不能ログのフラグ。

### 2.4 必要な UI/UX（画面・フロー要件）
将来アプリで実装すべき画面群（mozu の「キャリブレーション貢献」フロー等として）:
- **A. 計量フロー**: Bluetooth 秤連携 or 手入力。材料を1つずつ追加 → 各 item の **grams（実測）** と **food ID**（USDA/FNDDS 検索 or **barcode スキャン** or **chain メニュー選択**）→ 栄養を自動引き当て（calories/P/F/C）。合計 grams/kcal をライブ表示。
- **B. 撮影フロー**: 盛り付け直後に **eye-level（斜め）** で 1–3 枚。**撮影ガイドで angle を eye-level に誘導**（傾きセンサ）。リアルな角度/光を許容（綺麗に撮らせない）。任意で既知参照物の同梱を促す。
- **C. stratum タグ付け**: `angle / container / size / cuisine / eat_context / fat_level`。多くは自動推定可だが**確定はユーザー/オペレータ**。
- **D. QA レビュー**: 食品 ID 確認・実装不能ログのフラグ（管理栄養士ロール）。
- **E. consent / privacy**: 実ユーザー写真を使う場合の同意取得。operator-plated（運営が盛り付け）なら不要。
- **F. coverage トラッカー**: stratum セル（特に edge: small/large・bowl・overhead・fried/high_fat）の充足度を可視化（ingest の coverage 出力に対応）→ **active learning** で薄いセルを優先依頼。

### 2.5 層化・必要 n・サンプリング優先度
bias は **set-specific で相殺**する（global な edge は無い）ので、E14 が *per-cell* で補正できるよう層化必須。
- **層化軸**（証拠は `E13_DATA_COLLECTION_PLAN §4`）: ①**camera angle**(eye-level≫overhead, **eye-level を過剰サンプル**) ②**dish/portion size**(small<300 は OVER / large 700-1500+ は UNDER＝相殺) ③**density class**(lean vs dense/fried/full-fat) ④**container**(bowl vs plate)・**composition**(単品/snack vs mixed) ⑤**hidden-fat**(fat が最悪 38-41% MAE)。副タグ: cuisine, eat-out vs home。
- **必要 n**: **total 200–500**（20–50 は *方向確認のみ*・採用ゲートにしない）。**edge セルごとに ~30–90+**、特に large/small・bowl/plate・overhead/eye-level の edge を**意図的に過剰サンプル**。**fit / blind-holdout split は収集前に決定**し、各セルが両 split に十分入るように。
- **優先度**（**不確実性で優先しない**＝E3 が否定）: ①stratum coverage/balance ②**cross-MODEL 不一致**(flash-vs-pro 等。within-model dispersion ではない) ③high-leverage セル(high predicted kcal × size/density edge)。

### 2.6 GT sourcing（stratum 別・コスト最適化）
| stratum | GT 方法 | per-item grams | 精度 |
|---|---|---|---|
| 家庭の mixed | 各材料を秤量 + recipe 分解→USDA/FNDDS | yes | 高(weighed) |
| 単品 packaged | barcode/label + **as-eaten を秤量** | yes | ~5–10% |
| chain restaurant | Nutritionix/MenuStat 公表値(法的に±20%内) | no(item total) | item レベル良 |
| hard plates(ソース/高密度/occluded) | full weigh-as-you-plate | yes | 高 |

### 2.7 ユーザー判断事項（コードで解決不能・UI/UX 着手前に決める）
- **build vs partner**: 自前収集 or 委託（labor-bound でソフト工数でない）。
- **who/where**: 誰が盛り付け+計量+撮影。mozu 実ユーザーを反映する cuisine / eat-context mix。
- **budget & scale**: 200（最安の defensible）vs 500（edge の per-cell power）。
- **privacy/consent**: 実ユーザー写真を使うか（vs operator-plated）。

---

## 3. ② E14 fit → blind holdout パイプライン（収集後・backend・**準備済み**）

### 3.1 データ → ハーネス（turnkey・実装済み）
```bash
# 1) 収集 manifest(+画像) を harness 形式へ変換（全件 validate・no fallback・stratum coverage 報告）
python -m apps.freeform_usda_meal_analysis_api.scripts.ingest_e13_collection \
  --collection-dir <収集dir> --out-name e13_pilot
#   → test_images_e13_pilot/ + evals/splits/e13_pilot_all.txt + coverage(angle×size, <30 を THIN 表示)

# 2) baseline を取る（decomposed: grams比/density比 を自動 emit）
python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config <config> --api-url http://localhost:8006 \
  --image-index-file apps/freeform_usda_meal_analysis_api/evals/splits/e13_pilot_all.txt \
  --required-image-count <n> --no-use-vlm-cache
```

### 3.2 E14 fit 方式（PoC で機構確立済 — `20260606_e14_*`）
- **条件付き乗算補正**: `corrected = pred × factor[cell]`、`factor = median(GT/pred)` を **fit split** で算出、**clamp [0.5, 2.5]**。
- **cell = predicted-calorie bucket（5分位）× food-group × angle × container** の階層。**conditional は global に勝つ**（実 JFB で 38.1 vs 41.3）。
- **hierarchical shrinkage + 十分な per-cell n**（小 split の per-bucket overfit を防ぐ＝§2.5 の n 設計が効く）。
- **観測可能特徴のみで条件付け**（predicted-calorie bucket 等。不確実性は使わない＝E3）。

### 3.3 採用ゲート（非交渉・lesson 由来）
- 🔴 **in-domain でのみ fit**: lab/global fit を実ドメインに適用すると **raw より悪化**（weighed lab fit→JFB = 55.5 vs raw 53.8）。**production の global/lab 校正は禁止**、holdout 通過まで `calorie_calibration` 無効。
- **blind holdout の paired CI 上限 < 0**（fit/holdout split は fit 前に固定）。
- **AND-gate(F3)**: MAE ≥2pt AND CI 上限<0 AND p90/bias/high30/recognition 非悪化 AND latency/cost 予算内 AND subgroup guard。**total-calorie 単独で採用しない**。
- **corrected calorie は別フィールド**（表示 grams は不変・F1-e VOID guard）。
- **grams と density を協調補正**（片方だけ補正は 0.88×1.14≈0.98 の相殺を壊し悪化）。
- **no eval-leak**（test id/label/GT/校正定数を prompt/pipeline に埋めない。E13 GT は fit/検証専用）。eval は `use_vlm_cache=false`。

### 3.4 期待効果
JFB self-cal で **in-domain −18.5pt** の天井（real-domain の +44% over-prediction を是正）。ただし JFB GT は推定なので *構造的天井*の提示であり、production 係数には **E13 の weighed 実ドメイン set が必須**。

---

## 4. 実装着手チェックリスト（UI/UX 実装を始めるとき）
1. §2.7 のユーザー判断（build/partner・scale 200/500・privacy・cuisine mix）を確定。
2. fit / blind-holdout split のルールを**収集前に**決める（stratum 各セルが両 split に入る配分）。
3. アプリに §2.4 の A–F フロー（計量・eye-level 撮影・stratum タグ・QA・consent・coverage）を実装。出力は **§2.2 のデータ契約 JSON + 画像**ちょうど。
4. `ingest_e13_collection.py --template` でスキーマ整合を確認しつつ、まず **pilot 20–50 食**でフロー+manifest+harness を E2E 検証（方向確認のみ）。
5. coverage の薄い edge セルを active learning（§2.5 優先度）で埋め、**total 200–500 / edge ~30–90+** へ。
6. §3 のパイプラインで E14 を fit→blind holdout、§3.3 の AND-gate で採用判定。corrected calorie は別フィールドで返す。
7. 採用後も barcode/chain-API で安価にスケール継続、set 成長に応じ条件付き校正を定期 re-fit。

## 5. 参照（相互リンク）
- 設計 SSOT（なぜ/層化/n/公開データセット）: `docs/E13_DATA_COLLECTION_PLAN_20260606.md`
- 校正の効き方・転移失敗の定量: `evals/lessons/20260606_e14_conditional_calibration_poc_works_indomain_but_lab_data_does_not_transfer.md`
- データ契約の実体（`--template`）: `scripts/ingest_e13_collection.py`
- 実ドメイン reality check（JFB 53.8%/+43.9%）: `evals/lessons/20260606_jfb_*`, `docs/EXTERNAL_TESTSET_PLAN_20260603.md`
- 運用 SSOT / 現状: `plans/current.md`, `docs/MOZU_PDCA_COMPLETE_20260606.md`
- 参考: スクレイピングデータは E13 の代替不可（styled+recipe-intended 分量・写真↔量が loose）: `docs/DRIVE_DATASET_INVENTORY_20260607.md`, `docs/ENGLISH_RECIPE_SOURCE_SURVEY_20260607.md`
