# mozu API — PDCA 全経過と現状（包括ドキュメント, 2026-06-06）

写真カロリー推定 API（`freeform_usda_meal_analysis_api`、mozu 用）の 2026-02〜06 PDCA を**全て**まとめた SSOT。各実験の数値・決定・lesson 参照を保持。
- **読む順**: §1 Executive → §2 現状 → §3 中心診断（最重要）→ §4 採用 lever → §5 天井マッピング → §6 本命 lever → §7 eval 基盤 → §8 主要決定の変遷 → §9 時系列タイムライン → §10 次の一手 → §11 lesson 索引。
- 詳細は各 `evals/lessons/<file>.md`。運用ハンドオフは `plans/current.md`。モデル決定 SSOT は `docs/MOZU_MODEL_DECISION_20260603.md`。

---

## 1. Executive summary
- **製品**: 1枚の食事写真 → VLM(食材+グラム) → USDA(FNDDS)検索 → 栄養計算。mozu（高単価 calorie tracker）用。
- **中心結論**: **写真カロリー推定の精度はモデル/prompt/schema/retrieval では天井**。realistic レンジ(200-1500kcal)は系統 bias ほぼ無しの **~20-24% variance floor**、系統 bias は分布固有(小皿 over × 大皿 under が相殺)。**真の lever = 実測 in-domain データに基づく条件付き校正(E14) / 入力情報(E8)**。これは E13 実測データ収集が唯一の律速。
- **本番反映済みの実利**: **E7 top-k density(−2〜7pt)・light スタック(embedding ~9×高速・無料)・SC K=3(−2.5pt, 耐障害)・E2 floor20(小皿 −20pt)**。
- **棄却/天井（再試行不要）**: pro(撤回)・cross-provider 全スロット・schema v9c〜v18・portion scaling・不確実性検知(E3)・recognition の一般 lever。
- **未 deploy の最大余地**: **E14 条件付き校正**（PoC で in-domain −18.5pt の天井を確認、但し実 in-domain ラベルデータが必須）。

## 2. 現在の本番状態（authoritative）
Cloud Run revision **`00041-sfj`**（2026-06-06 deploy）。Firestore config 駆動。
| 要素 | 値 |
|---|---|
| VLM | **flash** `openrouter:google/gemini-3-flash-preview`（pro 撤回済） |
| embedding | **Qwen3-Embedding-0.6B**（`usda_index_full.faiss` dim1024 / 13564 vec / 55.5MB） |
| reranker | **Qwen3-Reranker-0.6B**, top_n=**5**（E7 density mixture 有効, τ=`E7_DENSITY_TEMP` 既定1.0） |
| self-consistency | **K=3** median（`_select_resilient` 耐障害: 成功サンプルで median・全滅時のみ hard-fail） |
| prompt | v13 + **E2 floor20**（weight `20-400`/`1-120`, len 2841, Firestore text override） |
| rollback | `/tmp/deploy_rollback/`（Firestore `put_rollback.json`=k1+元prompt / 旧 revision `00040-f2k`）。手順書 `docs/DEPLOY_RUNBOOK_E7_LIGHT_20260605.md` |

**deploy 履歴**: ① baseline(~2/26 image: 8B emb + 4B rerank + E7off + SCoff + v13) → ② `00040-f2k`(2026-06-05: 0.6B light + E7 top_n=5) → ③ `00041-sfj`(2026-06-06: + SC K=3 + E2 floor20)。

## 3. 中心診断：カロリー精度の壁（最重要）
PDCA 全体が収束した**壁の構造**。これが「なぜ prompt/model で動かないか」の答え。

1. **ベースライン回帰の発見（6/1）**: Feb の frozen-50 MAE 11.38% が再現せず、3ヶ月後は安定して ~20%（モデル/retrieval 越しに std 0.3pt）。新しい Gemini でも回復せず（gemini-3.5-flash は全軸悪化）。原因はモデル/provider drift と推定、未特定。
2. **分解診断①（6/1, full range）**: ~20% を signed bias + Theil-Sen slope + Hungarian dish-match に分解 → **系統的 portion UNDER-estimation**（calib slope ~0.47, intercept ~300 → pred≈300+0.47·true, 1500kcal→~1010=−33%, R²~0.16 ノイジー）。**VLM の質量推定問題で retrieval/matching でない**（weight sweep も retrieval 修正も MAE 動かず）。fat が最悪マクロ(38-41%)。
3. **分解診断②（6/4, realistic range）**: pred/GT = (grams比)×(density比) に factorize → **realistic 200-1500kcal は calorie bias ほぼゼロ**（NVReal 0.98 / N5k 1.02）、**誤差寄与は grams:density ≈ 50:50**、個別偏り(NVReal grams 0.88 under / density 1.14 over)は**セット固有で相殺**。反実仮想: 完璧 grams でも 23.7%、完璧 density でも 19.7% 残る = **純粋分散の floor**。→ 片 lever 修正は相殺を崩し悪化。
4. **GT 妥当性危機（6/3）**: frozen-50 の GT は **GPT-5-pro 推定**（全 label が confidence 0.78-0.90 + weight 5g 丸め＝モデル生成の痕跡）。「~18% MAE」は**実精度でなく GPT-5-pro 一致度**。実測 N5k では同モデルが +30.7% OVER（frozen-50 は −5.3% UNDER）＝**bias 符号が labeler で反転**。→ calorie 系の prompt A/B(v14-v17) と calibration JSON を VOID。
5. **実ドメインの現実（6/6, JFB）**: 実 eye-level ユーザー写真(JFB)で v13 は **MAE 53.8% / +43.9% 系統 OVER**（curated frozen-50 ~16% が隠していた）。⚠️ JFB GT は専門家推定なので絶対値より**過大方向**が actionable。
6. **image-only 天井（外部研究）**: 厳密 GT の Nutrition5k でも 2D RGB モデルは ~70kcal MAE / ~26% MAPE。専門家の写真推定も ~58% MAE。→ 写真単独推定には intrinsic な floor がある。

**帰結**: realistic レンジの誤差は「系統 bias 無しの分散 floor」、系統 bias は「分布固有で相殺」。だから global な prompt/model nudge は一方の分布を助け他方を害す。**変えられるのは分散低減(self-consistency=採用済)と、分布条件付きの実測校正(E14)だけ**。

## 4. 採用 lever（本番反映済み・evidence）
| lever | 機構 | evidence | deploy |
|---|---|---|---|
| **E7 top-k density mixture** (top_n 1→5) | top-1 の hard density pick を softmax(rerank/τ)重みの top-k 密度平均に（density は誤差の~50%・retrieval 側） | frozen-VLM 分離 50-set −4.03pt(p=0.042)・k-sweep 単調(top1 18.5→k5 15.8→k10 14.7, p=0.034)・**NVReal −7.67pt(p=0.037)**・全3セット方向一貫・latency/cost ~0 | ✅ `00040-f2k` |
| **light スタック** (8B+4B → 0.6B+0.6B) | 軽量 embedding/reranker | calorie **非劣性**(wash, draw 間で符号 flip)・**embedding ~9×高速**(28-31s cold-start 解消)・**無料**(vs paid 8B/4B) | ✅ `00040-f2k` |
| **SC K=3 median(耐障害)** | seed 違い K サンプルの median total-calorie（分散低減） | pooled N=253 で **+2.5〜3.2pt(3セット全正)**・cost/accuracy: K1→K3 −2.53/K3→K5 −0.28 ⇒ K=3 sweet spot・`_select_resilient` で K>1 単発失敗が 500 にならない・latency ~1.15× | ✅ `00041-sfj` |
| **E2 weight floor 80→20 / 5→1** | 小皿の grams 上限を下げ過大予測を是正 | **3セット(N5k/NVReal/JFB)・pooled lt_300(n=87) −20.75pt CI[−40.8,−0.1] 有意**(JFB 単独有意)・大皿非悪化・機構確認(weight↓→過大是正) | ✅ `00041-sfj` |

（補足: Feb の prompt 採用 = v9b_recall_balance 12.51% → v11b_component_density@temp0.3 11.38% は当時の frozen-50 基準。後にベースライン回帰でこの数値は再現せず、現行は v13。）

## 5. 天井マッピング（再試行しない negative）
### 5.1 モデル選択は天井
- **pro 採用→撤回（6/3-4）**: 詳細は §8。3 独立実測セットで calorie 符号 flip、clean GT で recognition も tie/やや劣。**flash が cost-rational**（同等精度・~1/3 コスト）。
- **broad VLM sweep / 新 Gemini（6/1-2）**: gemini-3.5-flash は全軸悪化、3.1-flash-lite は同等で2倍遅い、qwen3-vl/kimi は大幅悪化。thinking は raw MAE でなく slope を上げるが calibration が要る。
- **cross-provider 全スロット（6/5）**: premium embedding(Gemini-001 MTEB#1/Cohere-v4/OpenAI-3-large)・reranker(Cohere-v3.5)・VLM-native(Google generateContent) いずれも **paired CI 0跨ぎでクリーン勝ち無し**（強埋め込みは bias 負反転、native は +7pt p=0.004 悪化）。

### 5.2 prompt / schema は天井（v9c〜v18 の系譜）
- **Feb sweeps**: v9c/v10a/v10b/v11a/v12・temp/top_k/reasoning_effort/seed は全て non-promote（dev40 単発勝ちが full50 で再現せず＝**provider 非決定性 std ~2.36pt が支配**）。reasoning_effort=high < medium。
- **v14/v14b scale anchor（6/1-2）**: weight cap 緩和+scale anchor は slope 0.42→0.66 に上げるが bias を over に flip（v14 +14.8%）。mild な v14b は de-bias するが MAE 不変（R²0.16 で分散支配）・calibration と冗長。
- **v15 natural names（6/2）**: 棄却。/retrieve は clean name なら 8/9 正解＝**matching は VLM food-ID capability-bound**で命名 STYLE は lever でない。
- **v16 grounding / evidence field（6/2）**: **evidence field は hallucination を増やし backfire**(1.90→2.02/img)。whole-plate scan も enumeration を促す。
- **v17 describe-shape identity（6/2-3）**: wrong_food は再現的に減る(76→61/78→68)が conviction は noise band 内、**full50 で cooked-default が +4.6pt calorie 回帰**＝棄却。
- **E1 v15/v18 schema 分離（6/6, 本セッション）**: 9失敗 lesson の pre-mortem→pooled −6.21pt **だが set-specific(符号 flip +0.46/−1.69/−14.26)**＝global deflation で N5k 小皿のみ修正・eye-level wash・大皿悪化・recognition 非汎化＝**REJECT**。
- **portion scaling v14（6/4）**: realistic 200-1500 は 27.1→27.0% 改善ゼロ、MAE 改善は非現実的 >1500 giant-tail のみ。

### 5.3 不確実性検知は不成立（E3, 6/5）
無課金 proxy 9種 + SC 分散(seed1-5 K=5) いずれも誤差を予測しない（pooled N=253, CV ρ+0.048 CI[−0.08,+0.17], AUC 0.51）。高誤差の 46/52/46% が低CV=**「自信を持って間違える」**。→ **E9(不確実時1問)/E18(tiered routing) の安価信号版 不成立**。

### 5.4 recognition の一般 lever は floor
- **union-of-K self-consistency（6/4）**: recall +5.4pt だが wrong-food 3倍(13→37)＝phantom が calorie 悪化。見落としは bimodal(0/5 or 5/5)=系統的でサンプリング分散でない。
- **same-tier self-verification（6/2）**: flash が flash を検証＝同 bias で rubber-stamp、conviction flat。
- **reranker instruction（6/2）**: prod の instruction は no-op だった(DeepInfra 無視)→query 焼込で修正(mild win: naming 1.675→1.825, high30 27.5→15.0)。だが reranker は conviction lever でない(VLM クエリに視覚 context 無し)。
- **embedding matcher（6/2, eval 側）**: pred↔GT マッチングで token/char に負ける(kappa 0.50→0.12)。

### 5.5 E7 tail（6/6）
E7 は mean を改善するが hard-set p90 tail を肥大(N5k 112→134)。selective-E7(単一/支配アイテム→top1)は無効(mean 悪化・p90 不変)＝**tail は E7 機構の表裏**。

## 6. 本命 lever（実測データ待ち＝唯一の律速）
§3 の帰結: 真の lever は分布条件付きの実測校正(E14)と入力情報(E8)。

- **E14 条件付き校正 PoC（6/6, offline 既存予測）**: predicted-bucket × median(GT/pred) を fit→blind-holdout。**in-domain で機能**（JFB held-out 56.6→**38.1 = −18.5pt**・実ドメインで conditional>global, N5k 69→52）。**だが weighed lab(NVReal+N5k) fit→実 JFB は raw より悪化(55.5)** ＝lab の bucket 構造が実ドメインと不一致＝**in-domain ラベル set(E13)が必須**を定量確定。global/lab 校正は本番有効化**不可**（実ドメインで悪化）。global calibration は元々 VOID（§8）。lesson `20260606_e14_*`。
- **E13 実測データ収集（6/6, 計画+infra 完成）**: `docs/E13_DATA_COLLECTION_PLAN_20260606.md`。核心: **eye-level 写真は単眼スケール曖昧で portion GT を写真から復元不可→撮影時に mass 捕捉必須**＝**weigh-as-you-plate を eye-level 撮影で**。GT は **per-item grams 必須**（grams/density 分解・PFC 用）。層化=angle/size/density/container/fat。active learning=層カバレッジ+cross-model 乖離(不確実性は E3 で否定)。per-stratum n(edge 30-90+)+blind holdout。`scripts/ingest_e13_collection.py`(turnkey: weighed-log+写真→harness 形式・全件 validate・coverage 報告・E2E 検証済)。**残る人手=物理計量のみ**。
  - **計量を最小化できる**: 栄養が独立に既知の食事（**チェーン店メニュー**=公開栄養 / **パッケージ**=バーコード / レシピ計量の自炊）は eye-level 撮影+栄養紐付けだけで GT 成立（計量不要、~5-20% で専門家 58% より遥かに良）。計量は任意 composed plate の残差のみ。最もスケールするのは **mozu 公開後のアプリ運用データ**（バーコード/チェーン log の受動収集）。⚠️ レシピサイトのスクレイピングは**写真≠記載分量**でカロリー GT に不適（recognition には有用だがそこは天井でない）。
- **E8 user_context（配線済・データ待ち）**: F1-a で router→VLM の effective_prompt に注入済。"ate HALF"→760→556kcal の paid smoke 検証済。精度 A/B は実 context 注釈データ(実 mozu)待ち。
- **JFB(実 in-domain eval) を rotation 追加**: §7。

## 7. eval 基盤・方法論
- **rotation**（小lever は pooled 判定・`use_vlm_cache=false`）: **frozen-50**(eye-level, in-dist, GT=GPT-5-pro推定) / **NVReal-104**(eye-level, weighed) / **N5k-100/250**(overhead, weighed) / **JFB-100**(eye-level, real-user, estimated-GT)。コマンド・baseline は `docs/EXTERNAL_TESTSET_PLAN_20260603.md`。再構築: `build_nutrition5k_evalset.py`/`build_nutritionverse_evalset.py`/`build_jfb_evalset.py`。
- **GT 妥当性の教訓**: frozen-50=GPT-5-pro 推定(§3.4)・NVReal は最初 id-join バグで 40% GT 誤り→COCO 内容 join で 104 content-verified に修正(deterministic な schema/sum チェックは画像-ラベル対応ミスを検出できない＝必ず目視 spot-check)。
- **方法論の確立**: paired BCa bootstrap CI ゲート + 強制 stability・**frozen-VLM 分離**(VLM cache でretrieval/post-processing だけを isolate＝E7 を測定可能にした鍵)・decomposition(signed bias/slope/bucket) + dish_match_agg を自動 emit・**pooled large-N**(n=50 単独は draw-noise ±3pt 支配)・blind holdout・過学習防止(prompt に eval 固有情報を入れない)。
- **judge**: sonnet-4.6 rubric v2, **discriminative gate 0.944 pass**(相対判定は信頼可)・但し **golden human kappa 未検証**で絶対値は advisory。conviction は ~32/100 の VLM-capability 天井(prompt lever で動かず)。portion は決定的メトリクス(dish_match portion_bands)、LLM portion は advisory。

## 8. 主要決定の変遷（重要な方針転換）
- **pro 採用 → 撤回**: 6/3 に gemini-3.1-pro が frozen-50 で recognition F1 +30%・4/4 安定 → 暫定採用。だが (a) GT 危機で「recognition 4/4」は GPT-5-pro 命名一致度と判明、(b) 3 独立実測で calorie 符号 flip(N5k −7pt borderline / NVReal +2.2 NS / frozen ≈)、(c) clean COCO GT で recognition も flash 82.5% vs pro 80.6%(やや劣) → **撤回・flash 採用**（同等精度・~1/3 コスト）。`docs/MOZU_MODEL_DECISION_20260603.md`。
- **calibration VOID**: global affine calibration は frozen-50 fit だと gemini→GPT-5-pro 学習、N5k fit だと held-out 132% 暴発（over-bias は multiplicative で affine 不可・分布依存）→ **VOID/disabled**。E14 で**条件付き**化が唯一の道（corrected calorie は別フィールド・表示 grams 不変）。
- **light スタック採用根拠の訂正**: draw#1 −3.45pt は lucky draw、draw#2 +0.96 で wash → **採用根拠は latency/cost 勝ち＋非劣性**（calorie 改善は主張しない）。
- **SC の温度交絡の訂正**: temp0.5「−7pt」は temp 運+小n の過大評価、robust 値は temp0.3 K=3 で ~2pt。本セッション pooled N=253 で +2.5-3.2pt 確定→採用。
- **「prompt では動かない」の精緻化**: 3 AI レビューは「prompt では動かない/self-consistency が唯一」を言い過ぎと指摘したが、本フェーズの網羅実験で **prompt/schema/retrieval/model は実際に天井**と再確認。動くのは分散低減と実測条件付き校正。

## 9. 時系列タイムライン（全経過）

### Phase 0 — PDCA 基盤 + prompt sweeps（2026-02-24〜25）
| date | 実験 | 結果 | 決定 |
|---|---|---|---|
| 2025-12-21 | seed research | prompt 複雑化 D/E/F/G は効かず・誤差は VLM recognition+weight | rule 採用(minimal change/30%gate/model swap) |
| 02-24 | baseline 選定 flash v7 vs gpt5-mini | flash 21.98% vs gpt5-mini 29.73%(遅い) | flash v7 採用 |
| 02-24 | v9b_recall_balance full50 | 12.51%(v7 比 −9.47pt)・stability ok | **v9b 採用** |
| 02-25 | v10b/v9c/temp/top_k/reasoning sweep | 昇格無し(v9c_temp02 単発勝ち再現せず)・reasoning high<medium | hold |
| 02-25 | v11b_component_density temp0.3 full50 | 11.37%(−1.14pt)・stability ok | **v11b@temp0.3 採用** |
| 02-25 | v12/seed/temp sweep | 昇格無し・**full50 同config で 9.95% vs 13.28%(std 2.36pt)** | 反復評価を主ゲートに |
| (随時) | OpenRouter 401 | circuit breaker で run 無効化 | キー更新・breaker reset |

### Phase 1 — 回帰発見・分解・schema・judge 基盤（2026-06-01〜02）
| date | 実験 | 結果 | 決定 |
|---|---|---|---|
| 06-01 | v13 vs v11b | tie(+0.46pt NS)・**baseline 11.38% → 20% に回帰** | v13 維持・回帰は promote しない |
| 06-01 | 新 Gemini で回復? | 3.5-flash 24.95%(悪化)・3.1-flash-lite 同等で2倍遅・~20% は安定 | flash-preview 維持・分解へ |
| 06-01 | retrieval weight sweep | 全 CI 0跨ぎ・昇格無し | retrieval は lever でない |
| 06-01 | **分解診断(full range)** | 系統 portion UNDER・slope 0.47・fat 38-41% | 分解を eval に採用 |
| 06-01 | v14 scale anchor | slope 0.42→0.66 だが bias を +14.8% に over・MAE NS | hold・校正層へ |
| 06-02 | calibration 層 実装 | held-out 18.73→14.95%(−3.8pt, bias 除去)・R²0.16 で discrimination 不可 | 実装・**disabled**(外部 fit 待ち) |
| 06-02 | v14b mild | de-bias するが MAE 不変・校正と冗長 | hold |
| 06-02 | broad VLM sweep | thinking は slope を上げる(校正可)が raw MAE 勝者無し | freeze 結論を slope 視点で訂正 |
| 06-02 | v15 natural names | judge flat・matching は VLM food-ID capability-bound | 棄却 |
| 06-02 | v16 grounding | evidence field が hallucination 増(backfire) | 棄却・describe-shape のみ救出 |
| 06-02 | v17 describe-shape | wrong_food 減るが conviction noise・後に calorie 回帰 | candidate(後に full50 棄却) |
| 06-02 | judge conviction | USDA matching/food-ID が #1 bottleneck・model で動かず | matching へ pivot |
| 06-02 | judge discriminative gate | **0.944 pass**(相対判定信頼可) | 相対 arbiter 採用 |
| 06-02 | golden kit / self-agreement | naming/conviction robust・portion/nutrient 不安定 | rubric v2 へ |
| 06-02 | rubric v2/v3 | v2 で nutrient kappa 0.22→0.64・**v3 mechanical portion は悪化** | v2 採用・portion は決定的メトリクスに |
| 06-02 | embedding matcher | token/char に負ける | 棄却(default token) |
| 06-02 | reranker instruction bug | prod instruction は no-op→query 焼込で修正 | fix 採用(mild win) |
| 06-02 | same-tier self-verification | conviction flat(同 bias rubber-stamp) | infra 採用・default OFF |

### Phase 2 — pro 採用→GT 危機→撤回（2026-06-03〜04）
| date | 実験 | 結果 | 決定 |
|---|---|---|---|
| 06-03 | pro vs flash recognition | frozen-50 F1 +30%・4/4 安定だが conviction/calorie NS・naming −0.125 | hold(adversarial 検証) |
| 06-03 | v17 full50 | **calorie +4.6pt 回帰**(cooked-default が密な記録に) | 棄却 |
| 06-03 | pro naming reranker | naming 回復せず・but full-fat-default で cal −4.9pt | 棄却 |
| 06-03 | pro stability+calib | recognition 4/4 再現・under-bias は校正で除去可 | **暫定採用**(後に撤回) |
| 06-03 | **N5k 外部評価(250 実測)** | flash 68%/pro 58%・frozen-50 比 ~3倍悪化・affine calib 暴発 | pro 強化(暫定)・精度は range 報告 |
| 06-03 | N5k test-retest | pro 優位は borderline(denoised CI[−15.2,+0.9])・pro 再現性低い | downgrade(要 ≥2 run) |
| 06-03 | **frozen-50 GT 危機** | GT=GPT-5-pro 推定・bias 符号が labeler で反転 | TWO-GATE・calorie 数値/校正 VOID |
| 06-03 | NVReal id-join バグ | 40% GT 誤り→COCO 内容 join に修正 | 104 content-verified 再構築 |
| 06-04 | **NVReal eye-level(104 実測)** | flash 40.0/pro 42.2% NS・**3セットで pro 符号 flip** | pro calorie 優位を棄却 |
| 06-04 | **clean GT recognition** | flash 82.5% vs pro 80.6%(やや劣) | **pro 撤回・flash 採用** |

### Phase 3 — 分解・self-consistency・retrieval・E-series（2026-06-04〜05）
| date | 実験 | 結果 | 決定 |
|---|---|---|---|
| 06-04 | portion scaling v14 | realistic 27.1→27.0%(改善ゼロ)・giant-tail のみ | 棄却 |
| 06-04 | **realistic 分解** | bias ≈0・grams:density 50:50・edges 相殺 | 片 lever 不可・分散低減のみ |
| 06-04 | recognition union-SC | recall +5.4 だが wrong-food 3倍 | 棄却 |
| 06-04 | **SC median-of-K** | pooled −2.1pt CI[−3.94,−0.35] p=0.02 | 採用(opt-in, default OFF) |
| 06-04 | **E5/E6 light スタック** | 0.6B+0.6B 非劣性・~9×高速・無料(draw 間 wash) | 採用(latency/cost) |
| 06-05 | cross-provider | premium 全スロットでクリーン勝ち無し | 棄却・light 維持 |
| 06-05 | **E7 top-k density** | frozen-VLM −4.03pt(p=0.042)・k単調・NVReal −7.67(p=0.037) | **採用 top_n=5** |
| 06-05 | E12 SC v2(n=50) | K=3 が n=50 で再現せず(+1.3 NS, fail=1) | 並列化 code 採用・K=3 default は保留 |
| 06-05 | E2 floor20(n=50) | 無害だが <300 データ無く inconclusive | N5k 検証へ保留 |

### Phase 4 — 本セッション（2026-06-05〜06）
| date | 実験 | 結果 | 決定 |
|---|---|---|---|
| 06-05 | doc 整合 | 4 ファイルの pro→flash 統一 | — |
| 06-05 | **E3 不確実性診断** | proxy/SC 分散とも誤差予測せず(pooled AUC 0.51) | E9/E18 安価版 不成立 |
| 06-05 | **SC K=3 採用** | median pooled +2.5-3.2pt・耐障害 ensembling | code 採用→本番 deploy |
| 06-05 | **E7+light 本番 deploy** | revision `00040-f2k`・全検証パス | — |
| 06-06 | E7 tail | selective-E7 無効(tail は機構の表裏) | — |
| 06-06 | **E1 v15/v18** | pooled −6.21 だが set-specific・大皿悪化 | REJECT |
| 06-06 | **E2 floor20 検証** | 3セット・pooled lt_300 −20.75pt 有意・大皿非悪化 | adopt-worthy→本番 deploy |
| 06-06 | **JFB 統合** | 実 eye-level 1000枚・v13 実ドメイン 53.8%/+44% over | rotation 追加 |
| 06-06 | **E14 PoC** | in-domain −18.5pt・lab 転移失敗 | E13 必須を定量化 |
| 06-06 | **E13 計画+infra** | weigh-as-you-plate・ingestion turnkey | 物理計量がユーザー作業 |
| 06-06 | **E2+SC K=3 本番 deploy** | revision `00041-sfj`・全検証パス | — |

## 10. 次の一手・open questions
- **唯一の律速 = E13 実測 in-domain データ収集**（物理計量 or 計量フリー=チェーン/パッケージ/アプリ運用）。揃えば E14 で実ドメイン ~18pt 改善見込み。infra(ingestion)完備。
- **E8 user_context** の精度 A/B も同データ待ち。
- **未解決の謎**: frozen-50 11.38%→20% 回帰の根本原因(provider drift 推定・未特定)。
- **JFB の絶対値**: GT が専門家推定なので weighed E13 で真値較正が要る。
- **判定済みで再試行不要**: prompt/schema(v9c-v18)・モデル/cross-provider・不確実性検知・recognition 一般 lever・global calibration。

## 11. lesson 索引（全56本, テーマ別）
**基盤/sweeps(Feb)**: 20260224_{seed_from_20251221, full50_top2_results, focus_gemini_kimi_short_run, openrouter_local_key_failure, gemini_prompt_sweep_blocked_openrouter401, gemini_v9b_full50_adoption} / 20260225_{gemini_v10_dev40_blocked_openrouter401, dev40_prompt_param_sweeps_no_promote, gemini_v11b_temp03_full50_adoption, v12_and_v11b_param_sweeps_no_promote}
**回帰/分解/schema(6/1-2)**: 20260601_{v13_vs_v11b_tie_and_baseline_regression, model_drift_newer_gemini_no_recovery, retrieval_weight_sweep_no_promote, metric_decomposition_localizes_portion_underestimation, v14_scale_anchor_raises_slope_but_overcorrects} / 20260602_{calorie_calibration_layer_implemented, v14b_mild_redundant_with_calibration, broad_vlm_sweep_thinking_helps_slope, v15_natural_names_rejected_matching_is_capability_bound, v16_grounding_mixed_identity_helps_evidence_field_backfires, v17_describe_shape_identity_mild_win_near_noise, rubric_v2_stabilizes_nutrient, rubric_v3_portion_should_be_deterministic}
**judge/recognition/retrieval 基盤(6/2)**: 20260602_{judge_conviction_usda_matching_is_top_bottleneck, judge_passes_discriminative_power_gate, golden_kit_and_judge_self_agreement, embedding_matcher_does_not_beat_token, reranker_instruction_was_inert_bug_fixed, self_verification_implemented_same_tier_verifier_ineffective}
**pro 採用→撤回/GT(6/3-4)**: 20260603_{gemini31pro_breaks_recognition_ceiling_deterministic, gemini31pro_promote_hold_adversarial_verified, v17_full50_rejected_calorie_regression, pro_naming_reranker_form_did_not_recover, pro_stability_confirmed_and_calorie_bias_calibrated, nutrition5k_external_eval_generalization_gap, n5k_pro_advantage_test_retest_borderline, frozen50_gt_is_gpt5pro_estimate_two_gate_strategy, nutritionverse_real_broken_id_mapping} / 20260604_{nutritionverse_real_eyelevel_eval_pro_calorie_edge_not_robust, recognition_clean_gt_pro_no_edge_flash_cost_rational}
**分解/SC/retrieval/E-series(6/4-5)**: 20260604_{v14_portion_scaling_helps_slope_but_not_realistic_range, realistic_range_error_decomposition_grams_vs_density, recognition_union_self_consistency_not_clean_win, self_consistency_median_ensemble_significant_calorie_win, e5e6_lightweight_embedding_reranker_ab} / 20260605_{cross_provider_retrieval_no_clean_win, e12_self_consistency_v2_parallel_no_reproduce_at_n50, e2_weight_floor20_inconclusive_50set_no_small_dish_data, e7_topk_density_mixture_robust_calorie_win_adopted, e3_uncertainty_no_error_signal_but_sc_median_robust_at_pooled_N}
**本セッション(6/6)**: 20260606_{e1_v18_identity_separation_set_specific_deflation_not_generalizing, e2_floor20_validated_small_dish_over_prediction_fix, jfb_real_indomain_eval_integrated_overprediction_and_e2_confirmed, e14_conditional_calibration_poc_works_indomain_but_lab_data_does_not_transfer}
（その他基盤 doc: `MOZU_MODEL_DECISION_20260603` / `EXTERNAL_TESTSET_PLAN_20260603` / `E13_DATA_COLLECTION_PLAN_20260606` / `DEPLOY_RUNBOOK_E7_LIGHT_20260605` / `PDCA_ROADMAP_3AI_REVIEW_20260604` / `DEEP_REVIEW_20260601`）
