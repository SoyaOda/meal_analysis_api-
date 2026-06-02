# パイプライン改善提案書 — ポーション推定とステップ別根本改修の評価 (2026-06-01)

> 対象: `apps/freeform_usda_meal_analysis_api`（単一写真・低コスト VLM による食事カロリー推定パイプライン）
> 問い: 「ポーション推定について prompt と model の両面で、さらに各パイプラインステップごとに、2026年の最新ベストプラクティスに基づく改善案はあるのか、ないのか？」
> 方針: ユーザーの「ないならないでいい」に従い、根本改修が不要な箇所は正直に "不要" と明記する。

---

## 1. 結論サマリー

- **根本改修が必要なのは2箇所だけ**: (1) **post-hoc キャリブレーション層の不在**（パイプライン全体）と (2) **prompt によるポーション上限キャップ**（VLM 抽出ステップ）。この2つが計測された calibration slope 0.47（系統的な過小推定）を機械的に生み出している。
- **モデル選択・retrieval・nutrition DB は根本改修不要**: gemini-3-flash-preview は予算内で最良（自前計測で 3.5-flash は slope 0.21 と悪化、3.1-flash-lite は同等で2倍遅い）。hybrid retrieval（BM25+Qwen3-Embedding-8B+RRF+Qwen3-Reranker）と Qwen3 系は 2026 SOTA そのもので、自前の分解計測でも retrieval 修正は calorie MAE をほぼ動かさなかった。slope は「全汎用 VLM 共通の構造的バイアス」であり、モデル交換では直らない（PMC12513282）。
- **単一の最大レバー = post-hoc 線形キャリブレーション**: slope は bias/scale 問題であり、`true_hat = (pred - b)/m` を **held-out で robust 推定（Theil-Sen/Deming）** して挿入するのが、slope を 0.47 → ~1.0 へ機械的に戻す唯一の安価な手段。サンプリング平均化・ensemble は分散を減らすが共有方向バイアスは直さない（バイアス推定量を平均してもバイアスは残る）。
- **prompt で 0.47 → ~0.6-0.7 まで詰められる**: grams 出力・per-component CoT は既に v13 が実装済みで best-practice。残る prompt 改修は「weight_g ハードキャップ（80-400/5-120）の撤廃 + 数値プレート径アンカー + 隠れ油/調理法の明示」。slope ~1.0 はキャリブレーションでしか到達しない。
- **単一写真からの現実的な達成 MAE**: 低コスト汎用 VLM の現実的フロンティアは **20-30% MAPE**（frontier モデルでも energy 35-37%、人間栄養士 41%）。現状 20.6% は既に "good" の端。**sub-15% は depth/fine-tune がないと到達不能なため目標化しない**。KPI は MAE の追い込みではなく **calibration_slope → 1.0 と high-error(>30%) 率の低下**で判定すべき。

---

## 2. 我々の出発点（局所化された問題）

メトリクス分解の結果、誤差の正体は **系統的なポーション/質量の過小推定であり、大盛り食事ほど悪化する**ことが確定した。予測カロリーと真値の calibration slope ≈ **0.47**（理想 1.0）、intercept ~300 kcal、すなわち `pred ≈ 300 + 0.47*true` で、1500 kcal の食事は ~1010 kcal（-33%）と予測される。signed mean error は -3〜-7%（負＝過小）、R² ~0.16（ノイジー）。最悪マクロは **FAT（MAE ~40%、隠れた調理油・脂質）**。重要なのは、この slope が **モデル非依存**であり（gemini-3.5-flash はむしろ slope 0.21 と悪化、frontier 各モデルも -0.23〜-0.50 のバイアス slope を示す: PMC12513282）、複数設定で 0.46-0.48 に安定再現する点である。retrieval は bottleneck ではない（fusion 数式修正＋重みスイープで calorie MAE はほぼ不変）。つまり改善レバーは **portion-mass の処理（VLM prompt と後処理キャリブレーション）に集中している**。

---

## 3. ステップ別 改修案

### 3.1 VLM 抽出 + ポーション/質量推定

**現状評価**: v13 prompt（`prompts/freeform_prompt_usda_format_ver_v13_beverage_subject_prodcapture_20260226.txt`）は grams-per-component 出力・3パス内部 CoT（component map → portioning → density correction）・内部 low/likely/high レンジ・密度推論を既に実装しており、NutriBench CoT(+4.2pp)・grams-not-volume・decompose-then-recompute の知見に整合する。**ここは best-practice に近い。** ただし slope 0.47 の根本原因となる2つの実測ギャップがある: (a) prompt が schema で `weight_g: 80-400`（main）/ `5-120`（extras）と**ハードキャップ**し、"typical serving" の PORTION ANCHORS を提示している → 教科書的な regression-to-the-prior で大盛りを平均へ圧縮する（コード側 clamp は `models/response_models.py`・`vlm_service.py` に**存在しない**ため、純粋に prompt 由来の天井）。(b) どこにも **post-hoc キャリブレーション層がない**（`services/pipeline.py` で weight_g が nutrition 計算へ直行）。

**根本改修は必要か**: **Yes**（ステップ置換は不要だが、2つの追加が必要）。

| 優先度 | 施策 | 期待効果(slope/MAE) | 工数 | リスク | 根拠 |
|---|---|---|---|---|---|
| **P0** | post-hoc 線形キャリブレーション層を calorie 合算後に挿入。`corrected = (raw - b)/m`、(m,b) は **held-out で Theil-Sen/Deming** 推定し versioned config に保存、デフォルト off | slope 0.47→~1.0（**唯一 slope を直接反転**）。大盛りの -33% を回復、MAE ~20.6%→12-15% 圏へ。fat には効かない | S | 小 holdout(10) への過学習・OLS だと過補正。要 fit-set 拡張 | PMC12513282「correction must be portion-size-dependent, fit robustly (Theil-Sen/Deming, not OLS)」; arch research PRIORITY 1 |
| **P0** | weight_g ハードキャップ撤廃 + PORTION ANCHORS を「数値プレート径アンカー（dinner plate 26-27cm / bowl 15cm）」へ再構成 + 高さ/積み重ねを明示。grams+CoT は維持 | 生 slope 0.47→~0.6-0.7（regression-to-prior の解消）。キャリブレーション補正量を縮小し過学習リスク低減。p90=38% 圧縮 | S | 小盛りの分散増・過大推定の可能性。<2dish 変動はノイズ扱い | research「PLATE/BOWL DIAMETER AS SCALE ANCHOR」「regression-to-prior compresses large portions = sub-1.0 slope」「models ignore food HEIGHT/stacking」 |
| **P1** | 隠れ油/調理法の明示（揚げ物は重量の5-15%油吸収等）+ **決定論的 kcal/g sanity check**（マッチした FNDDS record 由来、0-9 kcal/g ハードキャップ） | 最悪マクロ FAT ~40%→~30%。油物の slope を局所的に押し上げ。高誤差(>30%)テール(22%)を捕捉 | M | 過剰な油仮定で lean dish 過大推定 → "visibly fried/oily" 条件で gate | research「EXPLICIT HIDDEN-OIL/FAT + COOKING-METHOD」「oils difficult to detect visually」arXiv 2602.05078; nutrition-DB「0-9 kcal/g 後処理 check」 |
| **P2** | VLM が household-unit を出した場合のみ `data/normalized_portions.json`（FNDDS 実測 grams_per_unit）を mass prior/clamp として配線 | mass 誤差を実測へアンカー。間接的 slope 改善（限定的） | M | record ミスマッチで誤 anchor 伝播。現 VLM は grams のみ出力のためカバレッジ部分的 | nutrition-DB research「FNDDS portion weights as gram anchor … 現状 UI-only」 |
| **P3** | median-of-3 self-consistency（per-component grams、adaptive stop）— **キャリブレーション後のみ** | 分散低減（R²~0.16 / p90 改善）。**slope はほぼ不変**（過小サンプルの中央値も過小） | M | コスト3-5倍（cache-off eval で実害）。bias 修正と誤認する危険 | research「3-5 samples sweet spot」「reduces variance not slope」arXiv 2511.00751 |

### 3.2 VLM モデル選択 / 推論設定

**現状評価**: 現行（`openrouter:google/gemini-3-flash-preview`, temp 0.3, seed 123456, reasoning_effort=medium, 単一コール）は予算内で最良。**モデルは本問題のレバーではない。** 自前計測3本: (1) 3.5-flash は全軸で悪化（24.9% MAE, slope 0.21, fat 54%）、3.1-flash-lite は統計的同等（paired 95%CI[-5.63,+5.09], p=0.94）で2倍遅い。(2) GPT-5-mini full50 で 29.7% MAE（悪化）、3倍遅い。(3) gemini-3-flash-preview が accuracy/latency/cost の最良バランス（20.65% MAE, 15.8s, $0.0072/img, slope 0.48）。reasoning_effort=high は medium より既に**退行**を計測済み。

**根本改修は必要か**: **No.**

| 優先度 | 施策 | 期待効果(slope/MAE) | 工数 | リスク | 根拠 |
|---|---|---|---|---|---|
| **P0** | gemini-3-flash-preview を base model として凍結し、slope 修正目的のモデル探索を停止。closed question を lessons に記録 | slope 効果ゼロ（それが狙い）。$0.36/full50×N の浪費を回避し slope レバーへ再配分 | S | 機会費用のみ。四半期ごとに候補再チェック | lesson 20260601_model_drift; PMC12513282「Switching among general VLMs will NOT fix the slope」 |
| **P2** | reasoning_effort=medium 維持（low/minimal を A/B 可）、portion で high は使わない | ~中立。最良でも latency/cost 低減 | S | 低 | lesson 20260225_dev40「high regressed vs medium」; PMC11990770「thinking gave only -4.7% MAE, unstable」 |
| **P2** | median-of-N(3-5) を VLM ステップで**分散低減目的のみ** | 分散低減のみ。slope ~ゼロ | M | コスト3-5倍 | lesson 20260225_v12（同設定 9.95 vs 13.28, std 2.36）; 自己整合性 research |
| **P3** | Kimi-k2.5 / 現行 GPT-5.x を同一 prompt で**一度だけ full50 確認**（paired BCa gate） | 大半は改善なしを確認する due-diligence。slope は要キャリブレーション | M | $0.3-0.5/model, Kimi は93s latency で gate 落ち | experiment_log（Kimi 5-img のみ、未検証）; January-AI bench |
| **P3** | LoRA fine-tune（Nutrition5k）を **唯一のモデルレベル slope 修正**として記録、インフラ前提で凍結 | 唯一 slope を機械的に flatten（LLaVA r 0.66→0.93, MAE 177→64kcal）。ただし近期効果ゼロ（self-host 不可） | L | self-host 必須・OpenRouter 配信不可・運用負荷 | PMC11990770; CaLoRAify arXiv 2412.09936（4×A800 ~7h） |

### 3.3 Food→USDA retrieval + nutrition 計算

**現状評価**: retrieval スタック自体は 2026 best-practice そのもので **bottleneck ではない**（自前分解＋FoodOntoRAG 2026 の両方が裏付け: hybrid+selector F1 0.858 vs dense 0.706）。Qwen3-Embedding-8B は MTEB #1-tier(70.58)。corpus も FNDDS/survey（as-consumed）で正しい。**retrieval/embedding/reranker の交換は不要。** ただし nutrition 計算側は無防備: `services/nutrition_service.py` は `per_100g * weight_g/100` を妥当性チェックなしで計算、`services/hybrid_search.py` の selector は record の `source` を通すが**ランキングに使っていない**。corpus は 57% が sr_legacy（7,793 生食材）で、as-consumed の料理が生食材 record にマッチしてエネルギー密度が狂うリスクがある。

**根本改修は必要か**: **No**（retrieval は不変、nutrition 計算側に低リスクの追加のみ）。

| 優先度 | 施策 | 期待効果(slope/MAE) | 工数 | リスク | 根拠 |
|---|---|---|---|---|---|
| **P2** | 各マッチ item に決定論的 energy-density sanity bound（0-9 kcal/g + record 自身の密度で record-anchored）。逸脱は flag/log | slope は不変。高誤差(>30%)テールと FAT MAE を抑制。主に guardrail/observability | S | 低（dense food 誤 flag → 0-9 ハードキャップで緩和）。silent clamp 禁止 | research「energy-density sanity bounds 0-9 kcal/g, 後処理 DB-anchored が in-prompt より強い」 |
| **P2** | selector に source-tier prior: cooked/mixed dish では survey(FNDDS) を sr_legacy より soft に優先。cooking_method ヒントで record bias | 油物/dense の系統的過小カウントを局所緩和（fat 集中）。global slope は不変 | M | 「bottleneck でない」selector を触る → 生 record が正しい item を退行させ得る。soft 信号で holdout 検証必須 | research「FNDDS = 正しい data type」「prep-method drives record selection」PMC12688007; FoodOntoRAG |
| **P3** | FNDDS household→grams 変換は**実装しない**（正直な否定）。VLM は weight_g しか出さないため `normalized_portions.json` は配線不可。唯一可能なのは gram 妥当性 prior だが、これは calibration ステップの領域 | 配線不能なレバーへの浪費を防止。retrieval を不変に保つ | S | 低（scoping のみ） | research の前提「when the VLM estimates in household units」は不成立（v10a schema は weight_g integer のみ） |

### 3.4 パイプライン全体アーキテクチャ（orchestration / verification / calibration / ensembling）

**現状評価**: 現行は厳密に**線形4ステップ**（`services/pipeline.py`: VLM → query抽出 → hybrid USDA search → 線形 nutrition 合算）。キャリブレーション層・self-consistency・critic/verifier・ensembling・後処理 sanity check が**production path に一切ない**。slope/bias は offline eval 診断（`scripts/run_pdca_batch_eval.py:compute_decomposed_metrics` L267-282）でのみ計算され、予測へフィードバックされない。本問題は明確に **bias/scale 問題**（slope 0.47, signed -3〜-7%, 設定間で安定）であり、最大の構造ギャップは**キャリブレーション層の不在**、次が**決定論的 energy-density sanity check の不在**。さらに方法論的欠陥として slope を **OLS で算出**（x-error で減衰）しており、真の slope はもっと急な可能性が高い。

**根本改修は必要か**: **Yes.**

| 優先度 | 施策 | 期待効果(slope/MAE) | 工数 | リスク | 根拠 |
|---|---|---|---|---|---|
| **P0** | Step4 後に post-hoc portion-size-dependent キャリブレーション層（Theil-Sen/Deming の slope+intercept）、disjoint held-out で fit。config flag・default off・prompt 変更ごとに再 fit | **唯一 slope 0.47→~1.0 を機械的に強制**し intercept ~300 を除去。大盛りテールで MAE 大幅減 | M | 10点 holdout への過学習 → 要 fit-set 拡張(Nutrition5k subset)・nested k-fold・robust fit。flat multiplier 厳禁 | PMC12513282 + fastml + arch research PRIORITY 1; lesson 20260601「slope 安定 ~0.47」 |
| **P1** | 決定論的 energy-density sanity check + selective LLM-revise critic（flag 時のみ）。warnings フィールドへ出力 | FAT MAE ~40% と high-error テール(22%)を直撃。central slope より分散/P90(38%)に効く。pass 時コスト~0 | M | 誤マッチ record で false flag → bounds を緩く・clamp-to-record 優先 | research: hidden oil arXiv 2602.05078（cream→milk 380kcal）; SETS/PAG selective revision; arXiv 2601.04491 |
| **P1** | v13 の weight_g ハードキャップ緩和 + decomposition を DB エネルギー密度に bind + 数値プレート径アンカー（CoT/grams は維持） | 生 slope 0.47→~0.6-0.7、残差補正を縮小（過学習リスク低減）。無料 | S | キャップ撤廃で分散増/小盛り過大 → density check で緩和・holdout gate | research: regression-to-prior; NutriBench grams+CoT; plate-diameter anchor |
| **P2** | self-consistency / multi-model ensembling を **slope 修正目的では追加しない**。sampling spread は無料の uncertainty band としてのみ使用 | slope ~ゼロ。分散/R²ノイズ低減のみ。コスト3-5倍で<2% は割に合わない | M | bias 問題に variance 修正を投じる浪費 | research「reduces variance not slope」「averaging biased estimators yields biased mean」 |
| **P2** | eval の slope 推定を OLS → Theil-Sen に修正（既存キーは残し additive） | MAE 直接効果なし。キャリブレーション定数を真 slope に fit でき adoption gate が信頼可能に | S | 低（additive・要 test 追加） | research「OLS slope is attenuated by x-error」; `compute_decomposed_metrics` は教科書 OLS |

### 3.5 Eval 方法論 + 現実的目標

**現状評価**: eval 方法論は既に強力で 2026 best-practice 整合（多くの公刊 food-VLM 論文より上）。`run_pdca_batch_eval.py` は MAE%+p50/p90+high-error率、BCa bootstrap 95%CI(10000 resamples)、paired permutation test + paired BCa delta CI の promote gate、診断分解（signed bias%、calibration slope/intercept/R²、per-macro MAE、Hungarian dish-match F1+matched-weight MAE）を実装済み。これは research が挙げる canonical メトリクスそのもの（recognition vs quantification 分離 + Bland-Altman slope）。**メトリクス設計の根本改修は不要。** 残る欠陥は2つ: (a) slope が OLS（減衰）、(b) `dev_40` と `holdout_10` が同一50枚の分割（union==50, 外部データなし）で**クリーンな held-out がない** → 後処理キャリブレーションを安全に fit できない。

**根本改修は必要か**: **No**（メトリクス設計は維持、目標再アンカーと held-out 取得が必要）。

| 優先度 | 施策 | 期待効果(slope/MAE) | 工数 | リスク | 根拠 |
|---|---|---|---|---|---|
| **P0** | research-anchored 目標バンドを文書化、20.6% を "near-frontier" と再フレーム（11.4% は artifact として recovery 目標から外す）。adoption 基準を slope→1.0 + high30 低下に | 到達不能な 11.4% 追求の浪費防止・50枚過学習防止 | S | 「20%=good」への抵抗 → 11.4% は再現せず frontier band 下と文書化 | PMC12513282(35-37%, slope -0.30..-0.45); Nutrition5k(人間41%, depth26.1%); lesson 20260601 |
| **P1** | calibration slope を OLS → Theil-Sen+Deming に置換（両方 report、robust を primary に） | MAE 効果なし。真 slope に fit でき A/B slope-delta が信頼可能に | S | 低（additive・要 test） | calibration research「fit robustly (Theil-Sen/Deming)」 |
| **P1** | **外部 held-out set（30-100枚）を取得/借用**（Nutrition5k subset or 大盛り/油物寄りの新規ラベル）。50枚は frozen 維持、キャリブレーションは外部 set でのみ fit | 最大レバー（後処理キャリブレーション）を**unblock**。slope 0.47→~10-13% MAE を回収可能に | L | ラベリング労力・Nutrition5k domain-shift → 自ドメイン優先・補正 slope を frozen 50 で検証 | calibration paper「fit on data that excludes eval set」; overfitting research; verified dev_40∪holdout_10==50 |
| **P1** | multi-seed 反復 full50 eval を adoption 必須化。MAE%・robust slope・high30 の3量を CI で gate（MAE CI<0 **かつ** slope CI が 1.0 へ動く時のみ win） | n=50 のノイズを win と誤認するのを防止（drift で 10/50 dish 変動） | M | 3倍 full50 コスト(~$1.08/候補) | overfitting research「multiple seeds, report CIs, treat small gains as noise」; drift lesson |
| **P2** | 決定論的 kcal/g 妥当性診断を eval に追加、`implausible_density_count` を report（推論変更なし） | 失敗チャネル分離（密度 blowup vs portion 過小）。次施策をターゲット化 | S | 低（additive 診断のみ・silent clamp 禁止） | arXiv 2602.05078/thecalcs; verifier-loop arXiv 2506.10406 |

---

## 4. 最新リサーチ要約（2026、軸別）

### 軸A: ベースライン現実 / slope 診断
- frontier VLM (GPT-4o/Claude 3.5/Gemini 1.5 Pro) も食事写真で bias slope -0.23〜-0.50（effective slope 0.55-0.70）、weight MAPE 36-37%。**我々の 0.47 は同一 regime**。Bland-Altman bias-vs-portion 回帰が systematic underestimation の canonical 診断。 — https://pmc.ncbi.nlm.nih.gov/articles/PMC12513282/
- 単一2D写真からの体積復元は**ill-posed**（scale ambiguity が「最も根強い課題」）。 — https://arxiv.org/html/2602.05078v1
- 人間栄養士 41% / 素人 53% PMAE、depth学習モデル 26.1%。 — https://ar5iv.labs.arxiv.org/html/2103.03375

### 軸B: 後処理キャリブレーション（最大レバー）
- 系統的補正係数は accuracy 改善に有効だが **portion-size-dependent（slope+intercept）** 必須、eval set を除外した held-out で fit、**robust(Theil-Sen/Deming)** で（OLS は減衰）。 — https://pmc.ncbi.nlm.nih.gov/articles/PMC12513282/
- 小データ(<1000点)では isotonic より linear/Platt が頑健。held-out fit が必須。 — https://fastml.com/classifier-calibration-with-platts-scaling-and-isotonic-regression/

### 軸C: prompt 技法（slope 0.47→~0.7）
- grams(metric) > household measures（NutriBench、GPT 系は metric で最良）。 — https://arxiv.org/html/2407.12843v6
- CoT「component→grams→kcal」で +4.2pp、multi-item で誤差安定化。GPT-4o-mini+CoT が GPT-4o-base 超え。 — https://arxiv.org/html/2407.12843v6
- 隠れ油/調理法の明示 + energy-density sanity（油は最高密度・視認困難、cream→milk 380kcal 誤差）。 — https://arxiv.org/html/2602.05078
- context/ingredient 注入が**最大の単一レバー**: image-only 123kcal → +ingredients 53kcal（-57% MAE）。 — https://pmc.ncbi.nlm.nih.gov/articles/PMC12655113/

### 軸D: アーキテクチャ（decompose / verify / self-consistency）
- decompose-then-recompute（nutritionist-inspired 2段 MLLM、CVPR 2025）が one-step direct query より高精度。 — https://cvpr.thecvf.com/virtual/2025/35662
- self-consistency は numeric では median 集約、N=3-5 が sweet spot、強モデルは<2%。**分散低減であり bias slope は直さない**。 — https://arxiv.org/abs/2203.11171 / https://arxiv.org/html/2511.00751
- RAG-grounded per-ingredient 密度（CaLoRAify）でハルシネーション緩和。 — https://arxiv.org/html/2412.09936v1
- selective verify-then-revise（PAG）が model collapse 回避。 — https://arxiv.org/html/2506.10406

### 軸E: retrieval / nutrition DB（変更不要の裏付け）
- hybrid BM25+dense+RRF+LLM/cross-encoder selector が短い food-name linking の SOTA（F1 0.858）。 — https://arxiv.org/pdf/2603.09758
- Qwen3-Embedding-8B は MTEB #1-tier(70.58)。 — https://arxiv.org/abs/2506.05176
- FNDDS/Survey が mixed-meal "as consumed" の正しい data type、~22k portion weights。 — https://fdc.nal.usda.gov/data-documentation/ / https://www.ars.usda.gov/ARSUserFiles/80400530/pdf/fndds/2021_2023_At_A_Glance.pdf
- 調理法は FNDDS record 選択で扱う（bolt-on multiplier ではない）。 — https://pmc.ncbi.nlm.nih.gov/articles/PMC12688007/

### 軸F: モデルレベル slope 修正（インフラ前提）
- LoRA on Nutrition5k が唯一安価に slope を flatten（LLaVA r 0.66→0.93, MAE 177→64kcal）。OpenRouter 配信不可で self-host 必須。 — https://pmc.ncbi.nlm.nih.gov/articles/PMC11990770/ / https://arxiv.org/html/2412.09936v1
- depth/3D（MonoBite MAPE 0.23, CVPR2025 MetaFood 優勝）は専用学習モデルで drop-in 不可。 — https://arxiv.org/html/2602.13041v1
- 単一写真の達成精度: 低コスト汎用 VLM は 30-57% MAPE、GT weight 供給で Gemini 57%→20%、専用/fine-tune で sub-15%。 — https://digitalcommons.odu.edu/computerscience_fac_pubs/417/

---

## 5. 推奨ロードマップ（統合・重複排除・P0→P3）

判定原則: **MAE だけでなく calibration_slope→1.0 を主基準とする**。MAE は下がるが slope が flatten しない変更は constant-multiplier/過学習であり真の改善ではない。各 prompt 変更後に slope は動くので**キャリブレーションは毎回再 fit**。

### P0（即着手・最大レバー）
1. **外部 held-out set 取得**（§3.5 P1, 実は前提条件）— これが無いとキャリブレーションを安全に fit できない。Nutrition5k subset or 大盛り/油物寄り新規ラベル 30-100枚。frozen 50 は維持。
2. **post-hoc Theil-Sen/Deming キャリブレーション層**を Step4 後に挿入（§3.1/§3.4 P0）— slope 0.47→~1.0 を機械的に強制する**唯一の手段**。config flag・default off・external set で fit・frozen 50 で検証。
3. **weight_g ハードキャップ撤廃 + 数値プレート径アンカー**（§3.1/§3.4）— 生 slope を ~0.6-0.7 へ。残差補正を縮小し過学習リスク低減。grams+CoT は維持。
4. **目標バンド再アンカー**（§3.5）— 20.6% を near-frontier と文書化、11.4% を recovery 目標から外す。
5. **gemini-3-flash-preview 凍結**（§3.2）— モデル探索を停止し slope レバーへ再配分。

### P1（次着手）
6. **eval slope を OLS→Theil-Sen/Deming**（§3.4/§3.5）— additive キー、test 追加。キャリブレーション定数を真 slope に fit するため P0-2 の前提。
7. **隠れ油/調理法 prompt + 決定論的 kcal/g sanity check + selective LLM-revise**（§3.1/§3.4）— FAT MAE ~40%→~30%、high-error テール捕捉。warnings 出力。
8. **multi-seed 反復 full50 を adoption 必須化**、MAE/slope/high30 を CI で gate（§3.5）。

### P2（条件付き）
9. energy-density sanity bound を nutrition_service に（§3.3）— guardrail/observability。
10. source-tier prior を selector に soft 追加（§3.3）— 油物/dense の局所改善、holdout 検証必須。
11. FNDDS household→grams mass prior 配線（§3.1）— household-unit item のみ、限定効果。
12. self-consistency / ensembling は **slope 目的では不採用**、spread は uncertainty band のみ（§3.4）。

### P3（凍結/将来）
13. Kimi-k2.5 / GPT-5.x の一度きり full50 確認（§3.2）— due-diligence。
14. LoRA fine-tune（Nutrition5k）— self-host 取得時のみ。唯一のモデルレベル slope 修正として記録（§3.2）。

### 最初に A/B すべきもの
**P0-3（prompt キャップ撤廃 + プレートアンカー）を dev_40 → full50 で A/B**（無料・即時）。判定は MAE 改善ではなく **calibration_slope が 1.0 へ動くか**。並行して P0-1（外部 set 取得）を進め、揃い次第 P0-2（キャリブレーション層）を fit → frozen 50 で補正 slope を検証。

---

## 6. やらないこと（正直な "ない" の明示）

ユーザーの「ないならないでいい」に従い、**今やる価値がない**ものを明記する:

- **モデル交換による slope 修正 — やらない**: 自前計測（3.5-flash slope 0.21, GPT-5-mini 29.7% MAE）と research（全汎用 VLM が -0.23〜-0.50 の共有バイアス）が、モデル交換では slope が直らないことを一致して示す。gemini-3-flash-preview は予算内最良で凍結。
- **retrieval / embedding / reranker の交換 — やらない**: hybrid BM25+Qwen3-Embedding-8B+RRF+Qwen3-Reranker は FoodOntoRAG 2026 SOTA そのもので、自前分解でも retrieval 修正は MAE をほぼ動かさなかった。Qwen3 は MTEB #1-tier。**ここを触ると再現性を壊すリスクだけが残る。**
- **FNDDS household→grams 単位変換 — やらない（配線不能）**: 現 VLM は weight_g（grams）しか出さず household unit を出さないため、`normalized_portions.json` は接続できない。slope は multiplicative bias なので unit 変換では解けない（キャリブレーション領域）。
- **self-consistency / multi-model ensembling を slope 目的で — やらない**: 分散は減るが共有方向バイアスは直らない（過小サンプルの中央値も過小）。コスト3-5倍で<2% は割に合わない。spread を uncertainty band として使うのは可。
- **reasoning_effort=high — やらない**: medium より退行を計測済み。research も portion で thinking は +3-5% MAPE/3-5倍コストで不安定。
- **11.4% MAE への回帰を目標化 — やらない**: 旧 provider/cache/50枚過学習の artifact である可能性が高く、低コスト単一写真の frontier band(20-30%)を下回る非現実的目標。現状 20.6% は既に "good" の端。
- **メトリクス設計の根本改修 — やらない**: eval は既に 2026 best-practice 整合（BCa CI, paired gate, 分解診断）。改修は OLS→Theil-Sen と外部 held-out 取得のみ。
- **depth/3D/NeRF パイプライン — 今はやらない**: 精度フロンティア（MonoBite MAPE 0.23）だが専用学習モデルが必要で、低コスト OpenRouter text-VLM への drop-in 不可。将来 vision ステージ追加時の方向性として記録のみ。
