# Claude-as-Judge 評価システム設計書（full output / user-conviction KPI）

- 文書ID: `JUDGE_EVAL_DESIGN_20260602`
- 対象: `apps/freeform_usda_meal_analysis_api` の PDCA 評価基盤（"OS"）
- 目的: 1枚の食事写真からの **構造化出力全体**（認識・分量・成分・USDA命名/DBマッチ・総合 user-conviction）を、写真と GT 両方に grounding した **Claude(VLM)-as-judge** で採点し、既存の total-calorie MAE ゲートを **置換せず補完**する。
- 前提コード（実物確認済み）:
  - 認識マッチが壊れている: `scripts/run_pdca_batch_eval.py:301-304` の `_name_similarity` は `difflib.SequenceMatcher`。実 run `evals/runs/20260602_092436` で `dish_match_agg.f1 ≈ 0.068`、一方 calorie MAE ≈ 21%。→ 認識シグナルは事実上ノイズ。
  - judge が必要とする入力は既に run dir に揃う: `raw_results.json` の `results[].image_results[]` に `image`(写真パス)/`label`(GTパス)/`prediction`(全出力)/`pred_items`(per-ingredient)/`dish_match`。
  - 既存資産: BCa paired bootstrap (`bootstrap_mean_ci:101`)、`compute_decomposed_metrics:226`、`detect_prompt_leakage:552`、multi-criterion `gate_decision:957`、`compare_to_baseline:934`、splits (`dev_40_v1.txt`/`holdout_10_v1.txt`)、versioned prompts (`prompts/freeform_prompt_*_vNN_*.txt`)、`scripts/CLAUDE.md` の **additive-only schema / no-fallback** 契約。
  - 依存: `scipy 1.17` / `numpy 2.2.6` は導入済み。**`anthropic` SDK は未導入**（依存追加はユーザ承認が必要）。OpenRouter 経由で `anthropic/claude-*` を呼べば新規依存ゼロ。
  - generator = `openrouter:google/gemini-3-flash-preview`（Gemini系）→ Claude judge は **cross-family**。

---

## 1. 目的と KPI 再定義

### 1.1 なぜ total-calorie MAE では不十分か

このアプリは **カロリートラッキングアプリ**であり、UI には「認識された料理/食材」「各分量(g)」「全栄養素」が表示される。最終 KPI は総カロリー精度ではなく **USER CONVICTION（ユーザが自分の写真とアプリ出力を見て『これは正しい』と納得し、そのまま記録として受け入れるか）** である。

total-calorie MAE は次を **見えない**:

- **認識の正しさ**（写真にある料理を当てたか、無い物を捏造していないか）
- **per-item の妥当性**（各食材の g、各 calculated_nutrition）
- **命名/DBマッチ品質**（matched_db_description が、ユーザが受け入れられる USDA レコードか）
- **相殺誤差**（compensating error）: 過大評価と過小評価が打ち消し合い、**間違った内訳なのに総カロリーは合う** ケースが現に発生している（実 run で fat MAE ≈ 42%、signed bias -6.4%）。total MAE はこれを通してしまう。

decomposition 層（signed bias / Theil-Sen slope / macro MAE / difflib-Hungarian recall・precision）を足しても、difflib が USDA冗長名（"Chicken, broilers or fryers, breast, meat only, cooked, roasted"）と短い GT名（"grilled chicken"）を **文字一致で結べず F1≈0.07** となり、認識は実質測れていない。

### 1.2 user-conviction を KPI に据える根拠

JMIR Human Factors 2025（画像補助食事想起の利用者選好調査, 26名）は、信頼/受容を駆動する要因の順位を次の通り示した:

1. 正しい **食品識別 / DB名検索の一致**（名前が一致しないとき "really angry")
2. 妥当な **分量推定**（"the most difficult aspect"）
3. それ以外（栄養素、総量）

そして **ユーザ自身の写真が #1 の信頼アンカー**（77% が画像補助方式を選好）。
→ 本設計の judge は「foods > names > portions > nutrients > total」の重みで採点し、必ず **実写真を grounding** する。
出典: https://humanfactors.jmir.org/2025/1/e79565

### 1.3 judge が測るもの（5+1 次元）

| 次元 | 何を見るか | 主入力 |
|------|-----------|--------|
| D1 recognition_correctness | 予測料理/食材が写真に実在し、GT を網羅しているか（再現+捏造） | 写真+GT |
| D2 naming_db_match | matched_db_description / fdc_id がユーザの受け入れる USDA レコードか（raw/cooked, beef/pork 取り違え等） | 写真+GT |
| D3 portion_plausibility | weight_g が写真の見た目と GT に対し妥当か（banded） | 写真+GT |
| D4 nutrient_validity | calculated_nutrition が weight_g×per-100g と self-consistent かつその食品として妥当か | GT+算術 |
| D5 total_plausibility | 総量が皿全体として妥当で、**正しい部品から積み上がっているか（相殺でないか）** | 写真+GT |
| D6 user_conviction (holistic) | ユーザが写真+出力を見て **そのまま記録を受け入れるか**。+ `edits_needed`（修正したい item 数） | 写真+GT |

D6 は gestalt（holistic）。D1–D5 を幾何平均で 0-100 conviction に融合し、D6 はその cross-check として別出力。

---

## 2. 評価ルーブリック（次元・尺度・重み・出力スキーマ）

### 2.1 尺度と anchor

- 各次元 **0-5 の整数**（0=最悪, 5=最良）。0-5 は human-LLM 一致が最良（ICC 0.853 vs 0-10 の 0.805, 0-100 の 0.840）。出典: https://arxiv.org/html/2601.03444v1
- プロンプトには **0 と 5 の anchor のみ**を記述（中間記述は寄与しないとアブレーションで判明、トークン削減）。出典: https://arxiv.org/html/2506.13639v1
- **generic な anchor 例を 2-3 件**（0=明確に悪い / 5=明確に良い）。ただし **50枚の評価画像からは絶対に取らない**（leakage防止）。出典: https://www.confident-ai.com/blog/why-llm-as-a-judge-is-the-best-llm-evaluation-method

### 2.2 hybrid aggregation（additive checklist + implicit holistic）

- **検証可能な事実は additive yes/no チェック**: 各 GT 料理を認識したか / 各 weight が tolerance 内か / calories ≈ weight×per-100g か。
- **soft な次元は implicit holistic**（judge が全 sub-criteria を見て重み付け）: naming 品質, 視覚的妥当性, conviction。implicit は additive 加算式を HealthBench で最大 ~28% 上回る。出典: https://scale.com/blog/rubrics-as-rewards
- **CoT は soft 次元のみ**（D1の視覚部・D3の視覚部・D6）。CoT は要約で Spearman 0.51→0.66 だが criteria が具体的なら寄与小。機械的次元(D3band/D4算術)では CoT を省きコスト削減。出典: https://www.confident-ai.com/blog/g-eval-the-definitive-guide
- **evidence-anchored (RULERS)**: 各スコア前に「写真の手がかり + 使った GT フィールド」を必ず cite。inter-rater 信頼性が上がり、spot-check の監査証跡になる。出典: https://arxiv.org/pdf/2601.08654

### 2.3 重みと融合（幾何平均）

```
overall_conviction (0-100) = 100 × Π_{d∈D1..D5} (score_d / 5)^{w_d}
```

推奨初期重み（SMART 風 elicitation、JMIR順序に整合）:

| 次元 | weight |
|------|--------|
| D1 recognition | 0.30 |
| D2 naming_db_match | 0.25 |
| D3 portion | 0.20 |
| D4 nutrient | 0.15 |
| D5 total | 0.10 |

- **幾何平均**を採る理由: いずれか1次元が崩れると全体が落ちる = 「1つでも誤った食品があれば信頼は崩壊する」という conviction の性質に一致。算術平均だと「総量は良いが食品が誤り」を覆い隠す（相殺誤差の罠）。JFB も geometric mean + ingredient F1 を最大重み(0.40) とし、weight ±0.05 で Spearman ρ>0.95 と安定。出典: https://arxiv.org/html/2508.09966v1
- D6 と `edits_needed` は **融合に入れず**、judge 自身の gestalt として別出力（融合値との乖離は escalation シグナル）。
- 重み + **±0.05 感度チェック**を config に記録（監査可能・無断調整禁止）。
- score_d=0 のとき幾何平均が 0 に潰れる縮退を避けるため **0→0.01 にクランプ**し、multi-sample 平均で偶発0を緩和。
- **anti-leakage**: ルーブリック本文に test 画像ID・固定 GT 数値・per-image 閾値を **一切埋め込まない**。tolerance は相対表現（"within X% of reference"）のみ。出典: https://www.godaddy.com/resources/news/calibrating-scores-of-llm-as-a-judge

### 2.4 judge 出力 JSON スキーマ（locked / strict）

judge は次の JSON **のみ**を返す（外側に散文を出さない）:

```json
{
  "judge_contract": {"judge_model_id": "anthropic/claude-...", "rubric_version": "v1", "prompt_sha256": "..."},
  "image_id": "test_foodNN",
  "photo_observation": "<候補出力を見る前に、写真から見える foods+おおよその分量>",
  "dimensions": {
    "recognition":        {"score": 0, "evidence": "<視覚手がかり + GTフィールド>"},
    "naming_db_match":     {"score": 0, "evidence": "..."},
    "portion_plausibility":{"score": 0, "evidence": "..."},
    "nutrient_validity":   {"score": 0, "evidence": "..."},
    "total_plausibility":  {"score": 0, "evidence": "..."},
    "user_conviction":     {"score": 0, "reasoning": "<scoreの前にCoT>"}
  },
  "per_dish": [
    {"dish_index": 0, "predicted_name": "", "matched_gt_name": null,
     "status": "correct|coarse_ok|wrong_food|hallucinated|missed",
     "portion_band": "within_10|within_25|gross|na",
     "name_match_ok": true, "nutrient_self_consistent": true, "note": ""}
  ],
  "missed_gt_items": [],
  "hallucinated_items": [],
  "overall_conviction": 0,
  "edits_needed": 0,
  "failure_tags": [],
  "confidence": 0.0,
  "needs_human_review": false
}
```

- `overall_conviction`(0-100) は **judge ではなく Python が幾何平均式で計算**（judge の算術ノイズ除去・幾何平均セマンティクス保証）。judge の `user_conviction`(0-5) は cross-check 専用。
- `failure_tags` は **クローズドな語彙**（machine-aggregatable → どのタグが増えているかで次に書くべき生成プロンプト規則が分かる）:
  `missed_main_food, missed_side, hallucinated_item, wrong_food_identity, raw_vs_cooked_mismatch, bad_usda_match, name_too_generic, portion_overestimate, portion_underestimate, density_error, nutrient_inconsistent, compensating_error, double_counting, beverage_handling, granularity_split, granularity_merge`
  タグ語彙は `rubric_version` と一緒にバージョン管理（lesson から新タグが出たら追加、無断変更しない）。
- `needs_human_review=true`（または `confidence<0.6`）は human spot-check pool へ routing。
- 構造化 multi-dimensional forced-choice は self-preference を ~31.5% 削減。出典: https://arxiv.org/html/2604.22891v2 / atomic per-item claim 検証(precision/recall) は ICCV2025 PROVE: https://openaccess.thecvf.com/content/ICCV2025/papers/Prabhu_Trust_but_Verify_Programmatic_VLM_Evaluation_in_the_Wild_ICCV_2025_paper.pdf

---

## 3. ジャッジ機構

### 3.1 モデルと transport

- judge = **Claude vision**（rubric pass は最強クラス Opus 系 vision、cheap cascade tier は Sonnet/Haiku 系 vision）。
- **既存 OpenRouter transport を再利用**（id 形式 `anthropic/claude-...`）→ **新規 Python 依存ゼロ**。コスト計上経路も generator と同一。
- generator=Gemini / judge=Claude の **cross-family** は self-preference を消す最もクリーンな手段（Claude は自家系列に対し **負の** self-bias β=-0.229 なので Claude系テキストを贔屓しない）。出典: https://arxiv.org/html/2604.22891v2
- モデルIDは **固定文字列で pin**（floating alias 禁止）。raw judge score は minor model bump で 3-8pt ドリフトし、version 跨ぎ比較は不可。出典: https://futureagi.com/blog/evaluating-llm-judge-bias-mitigation-2026/
- mixed-family panel（Claude+GPT+cheap Claude の median/majority）は **最終 adopt 決定のみ**（3-5x コスト）。PoLL は多様 panel が単体を上回り 7x 安い: https://arxiv.org/abs/2404.18796

### 3.2 入力順序と grounding（reference-AND-photo, image-first）

1. **(A) 写真を先に** 提示し、候補を見る前に judge が「見える foods + おおよその分量」を列挙（grounded-verification / anti-anchoring）。
2. **(B) GT JSON を reference** として提示（search_name/description/weight_g/per-nutrient = 数値の truth）。
3. **(C) 候補の full 構造化出力を最後に**（テキストに過度に anchor させない）。

- 写真は **認識/hallucination + 分量の視覚的妥当性のみ**に使う。**g を truth として再推定させない**（VLM 自身が重量 MAPE ~36% の弱い推定器）。出典: https://pmc.ncbi.nlm.nih.gov/articles/PMC12513282/
- reference+criteria は信頼性の 2大レバー（criteria 除去 -11%, reference 除去 -4%）。image-only は VLM judge で -5~9%。出典: https://www.emergentmind.com/topics/vlm-as-a-judge / https://arxiv.org/html/2506.13639v1
- VLM judge は候補テキストを過信し、改竄画像でスコアを inflate する → 視覚証拠を先に出させる。出典: https://mllm-judge.github.io/
- 候補から **model/version/prompt メタを除去**（blind judging）。dish 順序を seed 付きで randomize（position anchoring 除去）。

### 3.3 difflib → embedding-cosine + Hungarian（決定論的 recognition 層 = 安価な常時 gate）

judge の **下に** 置く cheap layer を直す。`dish_match_metrics` の Hungarian は残し、cost を差し替える:

```
Sim(a,b) = max(LCS_string_ratio, embedding_cosine(name|matched_desc, gt_search_name|description))
match if Sim >= T  (T=0.75 を held-out calibration split で調整、50評価画像では調整しない)
```

- `max(string, semantic)` + hypernym 等価ルール（"leafy greens" ⊇ 個別 greens）で **coarse-but-valid** な予測（main_food が GT より粗い）を罰しない。出典: https://pmc.ncbi.nlm.nih.gov/articles/PMC13092701/
- JFB 検証: cost=1-cos, Hungarian, T=0.75, text-embedding-3-small が human 類似度と r=0.82。出典: https://arxiv.org/html/2508.09966v1
- 追加の決定論的 per-item 指標（写真不要・コスト0）:
  - **portion bands**: |pred_g - gt_g|/gt_g を within-10% / within-25% / gross にバケット。出典: https://pmc.ncbi.nlm.nih.gov/articles/PMC9291996/
  - **calorie self-consistency**: 各 item の calories ≈ weight_g × per-100g かの整合チェック。
- これらは summary.json に **追加キー**として出す（`recognition_agg`, `portion_bands`, `nutrient_self_consistency_rate`）。既存キーは削除/改名しない。
- 依存方針: embedding backend は **pluggable `similarity_fn`** とし、(a) project の既存 embedding 経路 か (b) offline synonym/hypernym map のいずれか。**backend 未設定なら raise（difflib への silent fallback 禁止 = no-fallback ルール）**。embedding 用の新規依存追加は **ユーザ承認が必要**。

### 3.4 採点モードと bias 対策

- **PRIMARY = pointwise**（D1-D6 を 0-5、PDCA の longitudinal 追跡 + floor）。絶対スコアは pairwise より安定（flip ~9% vs ~35%）で、冗長 USDA名による gaming に強い。出典: https://arxiv.org/abs/2504.14716
- **pairwise は最終 adopt のみ**（候補 A vs baseline）。両順序で評価し **order-consistent な verdict のみ採用**。VLM では pairwise が absolute より ~8% 信頼度高いが、clear-cut では swap が逆効果(-2.5~-7.0pp)になり得るので routine では使わない。出典: https://arxiv.org/pdf/2602.02219 / https://mllm-judge.github.io/
- **最大の bias は verbosity/style (0.76-0.92)**: 「長い matched_db_description が本質的に良いわけではない」と明示。position bias は pointwise では無視可能(≤0.04)。出典: https://arxiv.org/html/2604.23178
- **multi-sample 平均**: 各 (image, candidate) を N≥3 回、per-dimension スコアを **平均**（sampling+averaging が majority/median を上回り corr 0.666）。seed を記録。出典: https://arxiv.org/html/2506.13639v1

### 3.5 reproducibility（judge_contract）

- すべての judge artifact に `judge_contract = {judge_model_id, rubric_version, prompt_sha256, embedding_model_id, n_samples, weights, seed}` を pin。生成プロンプトを `freeform_prompt_*_vNN_*.txt` で版管理しているのと同じ規律で、ルーブリックも `evals/judge/judge_rubric_vN.txt` で版管理。出典: https://futureagi.com/blog/evaluating-llm-judge-bias-mitigation-2026/

### 3.6 cost control（cascade + cache）

3段カスケード:

- **Tier 0（常時・無料）**: 既存数値層 + §3.3 の embedding 認識/portion/nutrient-consistency。
- **Tier 1（cheap/sampled）**: routine dev A/B では Claude judge を **固定 stratified 15-20枚**に限定。
- **Tier 2（full 50）**: (a) 数値ゲートを既に通過した promotion 候補, (b) **数値が曖昧/相殺誤差が疑われる** subset（総量は良いが macro MAE 大 / 認識F1 低 / test-retest 高分散）に限定。
- **judge cache**: `sha256(image_bytes) + sha256(canonical候補JSON) + judge_contract` を key に `evals/judge/cache/` へ保存（出力ハッシュ key なので generation の use_vlm_cache=false でも安全、再 run / merge が無料）。
- prompt trim（0/5 anchor のみ, soft 次元のみ CoT）。`judge_cost_usd` を summary.json の first-class 行で追跡、**judge spend を generation の ~15-25% 未満**に保つ。
- 根拠: classifier cascade で judge 呼び出し ~10x 削減 / FrugalGPT 78x / judge cost <10-25% of gen。出典: https://futureagi.com/blog/ci-cd-llm-eval-github-actions-2026/ / https://arxiv.org/html/2604.13717

---

## 4. ジャッジの検証（信頼してよいと言える根拠）

judge は **検証されるまで何のゲートにも使わない**。`evals/judge/` 配下に検証 artifact を置く。

### 4.1 human golden set（kappa / Pearson ゲート）

- `evals/judge/golden_set.jsonl`: **~15-25枚**を per-dimension 0-5 で人手ラベル（理想は held-out pool、生成プロンプトを iterate する画像と分ける）。50枚ベンチでは textbook の 200-500 は非現実的なのでスケールダウン。
- 採用基準: per-dimension **quadratic-weighted Cohen's κ ≥ 0.6**（目標 ~0.8）、composite **Pearson r ≥ 0.80**。
- 出典: Judge's Verdict（r≥0.80, weighted κ vs human-human ~0.80, |z|<1 human-likeness, test-retest）https://arxiv.org/html/2510.09738v1 / 実務 κ≥0.6・α~0.8 https://futureagi.com/blog/llm-as-judge-best-practices-2026

### 4.2 perturbation / discriminative-power gate（最重要）

実出力から合成劣化を作り、judge が **正しい次元を下げる**ことを必須化:

- (a) 正しい食品 → 誤った食品に置換 → recognition が下がるか
- (b) 分量 2倍/半分 → portion が下がるか
- (c) **食品は正しいまま calories を ~2倍に inflate（まさに相殺誤差ケース）** → nutrient/total が下がるか
- (d) 良い DB マッチ → 悪いマッチに置換 → naming が下がるか
- (e) 意味保存の言い換え（USDA冗長 ↔ 口語）→ スコアが **変わらない**こと（robustness）

公開 evaluator は注入劣化の **>50% を見逃す**ため、この gate は judge を信頼する前の **必須条件 + anti-overfit セーフガード**。`discriminative_power` と `robustness` を first-class baseline 指標として追跡し、ルーブリック変更でこれが悪化したら却下。出典: https://arxiv.org/pdf/2406.13439 / https://medium.com/@adnanmasood/rubric-based-evals-llm-as-a-judge-methodologies-and-empirical-validation-in-domain-context-71936b989e80

### 4.3 test-retest / drift / 数値との整合

- judge を golden set で **3回**実行し per-dimension を平均、intra-rater 安定性と |z|<1 human-likeness を記録。
- **drift tripwire**: `judge_model_id` または `rubric_version` が変わるたびに 4.1+4.2 を **再実行**し mean-shift をログ（minor bump で 3-8pt シフト・60-90日でドリフト）。
- **judge-vs-numeric 相関**: clear-cut では judge が calorie MAE% と一致すべき。`judge_vs_numeric_corr` を summary.json に記録。乖離（judge改善だが MAE悪化）は **「judge gaming 疑い」**として human spot-check へ。
- 全結果を `evals/judge/validation_<contract>.json` に保存。

---

## 5. PDCA（運用 OS）統合

### 5.1 storage（file-based SSOT を保持 / SaaS 不採用）

PDCA は既に file-based の SSOT（configs/runs/baselines/lessons/splits/knowledge/summary.json）。Braintrust/LangSmith 等への移行は **SSOT を分断**するので不採用。代わりにそれら platform が enforce する標準化を `evals/` 内で再現する（versioned dataset/rubric/judge-prompt, per-criterion JSON+rationale, paired-bootstrap gate, human-adjudication escalation）。出典: https://www.braintrust.dev/articles/best-prompt-evaluation-tools-2025

新規ファイル:
- `evals/judge/judge_rubric_vN.txt`（生成プロンプトと同じ版管理）
- `evals/judge/judge_contract.json`
- `evals/judge/golden_set.jsonl`, `evals/judge/perturbation_suite.jsonl`
- `evals/judge/validation_<contract>.json`, `evals/judge/cache/`
- `evals/baselines/judge_baseline.json`（current_baseline.json の隣）
- `evals/splits/judge_holdout_v1.txt`
- 各 run dir に `evals/runs/<ts>/judge_<candidate>.json`（per-image 内訳 + evidence + needs_human_review）

summary.json への **追加キー（既存キーは削除/改名しない）**:

```json
"judge": {
  "contract": {"judge_model_id": "...", "rubric_version": "v1", "prompt_sha256": "..."},
  "per_dimension_mean": {"recognition": 0.0, "naming_db_match": 0.0, "portion_plausibility": 0.0,
                         "nutrient_validity": 0.0, "total_plausibility": 0.0, "user_conviction": 0.0},
  "per_dimension_ci": {"recognition": [lo, hi]},
  "overall_conviction_mean": 0.0, "overall_conviction_ci": [lo, hi],
  "overall_conviction_p95": 0.0,
  "conviction_paired_delta": 0.0, "conviction_paired_ci": [lo, hi], "wilcoxon_p": 0.0,
  "edits_needed_mean": 0.0, "failure_tag_counts": {},
  "judge_vs_numeric_corr": 0.0, "golden_kappa": {"recognition": 0.0},
  "discriminative_power": 0.0, "n_images": 0, "n_samples": 3, "judge_cost_usd": 0.0
}
"recognition_agg": {"recall": 0.0, "precision": 0.0, "f1": 0.0},
"portion_bands": {"within_10": 0.0, "within_25": 0.0, "gross": 0.0},
"nutrient_self_consistency_rate": 0.0
```

decoupling: judge は **別 runner（`scripts/run_judge_eval.py`）として finished run dir を後処理**。hot な生成ループに触らないので、古い run の再 judge / judge model 差し替え / 生成プロンプトが同一プロセスで judge に迎合する事故の回避が可能。

### 5.2 ゲート: conviction が calorie MAE を **補完**（置換しない）

`gate_decision:957` を multi-objective に拡張。promote は **全部** 成立時のみ:

1. 既存品質ゲート（coverage_complete / failure_count==0 / all_success）— 不変
2. 既存 paired BCa calorie-error CI が完全に <0 — **不変**
3. **新: per-dimension 絶対 FLOOR**（例 recognition≥4.0, naming≥3.5, portion≥3.0, nutrient≥3.0、いずれも noise floor ~0.1 を超えて baseline から退行しない）
4. **新: holistic conviction の paired delta が bootstrap CI 内で非負**、ordinal は **Wilcoxon signed-rank p<0.05**
5. mean だけでなく **p95（worst tail）**も gate

- これが「**間違った食品なのに総カロリーが合う**」候補を **promote 不能**にする中核: calorie BCa を通っても recognition/naming floor で落ちる。
- floor は config に置き baseline の実測 per-dimension mean から **一度キャリブレーションして版管理**（eval set のpass率最大化で手調整しない = overfit防止）。
- **no-fallback**: judge が gate に要求されたのに `golden_kappa<0.6`（未検証）/ verdict・contract 欠落 のときは **理由付きで HOLD**（calorie だけで silent promote しない）。`decision.gate_mode="multi_criterion_judged"` を記録。judge=None 時は legacy 挙動を完全保持（backward compat）。
- 出典: 二重ゲート（floor=catastrophic, delta=slow drift, p<0.05 AND effect>noise）+ p95 + 単一集約禁止 https://futureagi.com/blog/ci-cd-llm-eval-github-actions-2026/ / Wilcoxon for ordinal https://medium.com/@adnanmasood/rubric-based-evals-llm-as-a-judge-methodologies-and-empirical-validation-in-domain-context-71936b989e80

### 5.3 anti-overfit（judge ≠ generator / no gaming）

1. **judge-only holdout**（`evals/splits/judge_holdout_v1.txt`）を生成プロンプト iteration で **絶対に見せない**、adopt 時のみ surface。
2. **judge ≠ generator family**（Gemini gen / Claude judge）を config に明記（self-preference 中和）。
3. **rubric anti-leakage**: `detect_prompt_leakage:552` を **ルーブリックファイルにも適用**（test ID / GT数値 / per-image閾値 禁止）。
4. **promote 時は必ず数値 MAE を judge スコアと並記**。judge↑ かつ MAE↓ なら "possible judge-gaming" として human spot-check 必須。
5. **judge は adopt の 1入力**であり唯一の oracle ではない（定期 human spot-check 継続）。
- 出典: holdout / judge≠generator / 「judge に迎合させない」/ one-token-fools-judge https://softwaredoug.com/blog/2025/11/02/llm-judges-arent-the-shortcut-you-think

---

## 6. SSOT 更新方針（作成/更新する docs・plans）

### 6.1 作成

- **`docs/EVAL_RUBRIC.md`** — ルーブリック正典: 6次元、0/5 anchor のみ、checklist vs implicit の切り分け、evidence-anchoring 必須、conviction 重み + 根拠、検証/perturbation 受け入れ基準。AGENTS.md/CLAUDE.md はここに **リンク**（重複させない）。
- `evals/judge/`（rubric_vN.txt, judge_contract.json, golden_set.jsonl, validation_*.json, perturbation_suite.jsonl, cache/）
- `evals/baselines/judge_baseline.json`
- `evals/splits/judge_holdout_v1.txt`
- judge 用 lesson テンプレ追記（`evals/templates/lesson_template.md` に judge 次元欄）

### 6.2 更新

- **`AGENTS.md`** — Ground Rules / Promotion Gate に "Judge Eval" 小節（multi-objective: calorie MAE AND recognition/naming floor AND conviction 非退行 / judge≠generator / rubric anti-leakage）、Directory Contract に `evals/judge/` 行。
- **`CLAUDE.md`（freeform）** — Runbook に judge コマンド、cascade/cost ルール。
- **`docs/PDCA_SESSION_START_CHECKLIST.md`** — Must-Read に「EVAL_RUBRIC.md + judge_contract + 最新 validation を読む」、ループに judge ステップ。
- **`docs/PDCA_BEST_PRACTICES_20260224.md`** — judge プロトコル（pointwise primary / pairwise for adopt / reference+photo grounding / biases & mitigations）。
- **`scripts/CLAUDE.md`** — additive-only schema 契約を summary.json `judge` キーと `judge_<candidate>.json` に拡張。
- **`plans/current.md`** — "Judge Eval" track（v0/v1/v2 タスク）+ Session Log。
- **`summary.md` writer** — judge per-dimension mean + conviction を人間可読サマリに surface。
- **`pdca_session_bootstrap.py`** — 最新 judge_contract / golden_kappa / discriminative_power を surface し、各セッションが「judge は今信頼できる状態か」を機械チェックで把握。
- judge_contract tuple は **doc ではなく artifact に pin**（doc drift しても reproducibility が残る）。
- 出典: rubric-in-git / 3-layer SSOT を分断しない https://futureagi.com/blog/evaluating-llm-judge-bias-mitigation-2026/

---

## 7. 段階的ロードマップ

各 phase は **前 phase の artifact 存在 + 受け入れチェック合格**まで次へ進まない（1機能ずつ test して進む方針）。

### v0 — no-LLM / no-cost / no-dep（今〜次セッション）

- 内容: `run_pdca_batch_eval.py` で difflib→embedding(or synonym map) マッチ + portion bands + calorie self-consistency を **追加キー**で実装。`tests/test_pdca_eval_logic.py` にケース追加。
- コマンド例:
  ```
  python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
    --config <existing> --api-url <url> \
    --image-index-file evals/splits/dev_40_v1.txt --required-image-count 40 --no-use-vlm-cache
  ```
- 受け入れ: recognition F1 が ~0.07 から妥当値へ上昇 + tests green + `py_compile` OK。
- 工数: 0.5-1日。embedding backend が無ければ synonym/hypernym map で起動（**silent な difflib fallback は禁止 = 無ければ raise**）。新規依存（embedding lib）が必要なら **ユーザ承認待ち**。

### v1 — Claude VLM judge（後処理 runner）+ 検証（ユーザの依存/golden 承認後）

- 内容: `scripts/run_judge_eval.py --run-dir evals/runs/<ts> [--candidate] [--images <split>] [--samples 3]`、rubric_v1 + contract、golden_set 人手ラベル(~15-25枚)、perturbation_suite、VALIDATION + DISCRIMINATIVE-POWER 実行。
- コマンド例:
  ```
  python -m apps.freeform_usda_meal_analysis_api.scripts.run_judge_eval \
    --run-dir evals/runs/<ts> --images evals/splits/judge_holdout_v1.txt --samples 3
  python -m apps.freeform_usda_meal_analysis_api.scripts.run_judge_eval \
    --validate --golden evals/judge/golden_set.jsonl
  ```
- 受け入れ（"信頼" 条件）: **weighted κ ≥ 0.6 AND perturbation 全合格 AND robustness 安定**。満たさなければ judge は **advisory のみ**（ゲート不可）。
- 工数: 2-4日（+ ユーザの一度きり golden ラベリング）。transport は OpenRouter 経由 Claude（新規依存ゼロ）。native prompt caching が欲しければ `anthropic` SDK 追加を別途ユーザ提案。
- **ユーザ hand-off**: (1) embedding/SDK 依存の可否, (2) golden_set ~15-25枚の per-dimension 人手ラベル。

### v2 — gate 統合（v1 検証合格後のみ）

- 内容: judge floor + conviction delta を `gate_decision` に config flag (`gate.use_judge:true`、**default OFF**) で配線。
- 受け入れ: 既知-good / 既知-bad の合成候補が正しく promote/HOLD される（特に「食品誤り×総カロリー一致」が HOLD）。
- 工数: 1-2日。
- **phase 遷移の decision rule**: v0(F1妥当+tests) → v1(κ≥0.6+perturbation) → v2(合成 good/bad の判定正) を満たすまで前進しない。

---

## 8. リスクと非目標

### 8.1 リスクと緩和

| リスク | 緩和 |
|--------|------|
| judge bias（verbosity 0.76-0.92 が最大） | 「長い USDA名 ≠ 良い」と明示、blind judging、length 非依存。position は pointwise で無視可、pairwise(adopt)は swap+consistency。出典 https://arxiv.org/html/2604.23178 |
| judge への over-trust（公開 evaluator は劣化の>50%見逃し） | perturbation gate を信頼前の必須条件化。judge は adopt の1入力、唯一 oracle にしない。human spot-check 継続。出典 https://arxiv.org/pdf/2406.13439 |
| judge drift（minor bump で 3-8pt） | model/rubric 変更ごとに golden+perturbation 再検証。contract で version 跨ぎ比較を禁止。 |
| judge gaming（生成プロンプトが judge に迎合） | judge-only holdout、judge≠generator、rubric anti-leakage、MAE 並記の乖離検知。出典 https://softwaredoug.com/blog/2025/11/02/llm-judges-arent-the-shortcut-you-think |
| コスト（50×N×3 samples の VLM） | Tier0-2 cascade + output-hash cache、prompt trim、judge spend <15-25% of gen。出典 https://futureagi.com/blog/ci-cd-llm-eval-github-actions-2026/ |
| 幾何平均の縮退（1次元0で全0） | 0→0.01 クランプ + multi-sample 平均で偶発0緩和。 |
| 小ベンチ(50)で κ が noisy | contract 変更時のみ再 label、spot-check から golden を機会的に拡張。 |
| judge の g 再推定（自身が誤推定器） | 写真は plausibility/hallucination 専用、数値は GT を truth。 |

### 8.2 非目標（やらないこと）

- total-calorie MAE ゲートを **置換しない**（judge は補完のみ。calorie 厳密性は維持）。
- 単一の blended "LLM quality" 数値に潰さない（per-dimension vector + per-dimension floor を維持、root-cause 診断のため）。
- SaaS eval platform（Braintrust/LangSmith）へ移行しない（file-based SSOT 分断を避ける）。
- ルーブリックに test 画像ID / 固定 GT 数値 / per-image 閾値を埋め込まない（anti-leakage）。
- judge を validate 前にゲートへ入れない（unvalidated judge は no judge より悪い）。
- 未検証の judge への silent fallback / silent promote をしない（no-fallback ルール）。
- routine cycle に pairwise を使わない（clear-cut で逆効果、コスト高。pointwise を longitudinal の primary に）。

---

### 主要出典一覧

- pointwise vs pairwise 安定性: https://arxiv.org/abs/2504.14716
- reference+criteria レバー / averaging / anchor は両端のみ: https://arxiv.org/html/2506.13639v1
- 0-5 尺度 ICC: https://arxiv.org/html/2601.03444v1
- implicit holistic > additive (HealthBench): https://scale.com/blog/rubrics-as-rewards
- G-Eval CoT: https://www.confident-ai.com/blog/g-eval-the-definitive-guide
- bias 体系研究(verbosity 支配/position 無視可/swap逆効果): https://arxiv.org/html/2604.23178
- self-preference(符号付き/cross-family): https://arxiv.org/html/2604.22891v2
- VLM-as-judge(写真 grounding 必須): https://www.emergentmind.com/topics/vlm-as-a-judge / https://mllm-judge.github.io/
- VLM 食品推定の弱さ: https://pmc.ncbi.nlm.nih.gov/articles/PMC12513282/
- atomic claim 検証(PROVE): https://openaccess.thecvf.com/content/ICCV2025/papers/Prabhu_Trust_but_Verify_Programmatic_VLM_Evaluation_in_the_Wild_ICCV_2025_paper.pdf
- judge 検証(r/κ/z/test-retest): https://arxiv.org/html/2510.09738v1
- 統計集約/judge誤差補正: https://arxiv.org/pdf/2511.21140
- コスト cascade: https://arxiv.org/html/2604.13717 / https://futureagi.com/blog/ci-cd-llm-eval-github-actions-2026/
- anti-leakage: https://www.godaddy.com/resources/news/calibrating-scores-of-llm-as-a-judge
- JFB(幾何平均/embedding+Hungarian T=0.75): https://arxiv.org/html/2508.09966v1
- set-matching precision/recall + hypernym: https://pmc.ncbi.nlm.nih.gov/articles/PMC13092701/
- banded portion: https://pmc.ncbi.nlm.nih.gov/articles/PMC9291996/
- user-conviction 順位(JMIR): https://humanfactors.jmir.org/2025/1/e79565
- RULERS locked+evidence-anchored: https://arxiv.org/pdf/2601.08654
- perturbation/discriminative-power: https://arxiv.org/pdf/2406.13439
- EVALOps(版管理/drift/judge_contract): https://futureagi.com/blog/evaluating-llm-judge-bias-mitigation-2026/ / https://futureagi.com/blog/llm-as-judge-best-practices-2026
- adopt-vs-extend(SaaS不採用): https://www.braintrust.dev/articles/best-prompt-evaluation-tools-2025
- judge gaming/holdout: https://softwaredoug.com/blog/2025/11/02/llm-judges-arent-the-shortcut-you-think
- position bias(swap/randomize): https://arxiv.org/pdf/2602.02219
- PoLL(panel): https://arxiv.org/abs/2404.18796
- rubric 設計/Wilcoxon: https://medium.com/@adnanmasood/rubric-based-evals-llm-as-a-judge-methodologies-and-empirical-validation-in-domain-context-71936b989e80
