# mozu パイプライン PDCA 再設計プラン — 3 AI レビューの全アイデアを検証可能にする

## Context（なぜこの計画か）
3つの AI（ai1/ai2/ai3）に現行パイプライン一式をレビューさせた。結論は**強く収束**:
1. 根本設計（VLM→食材/重量JSON→USDA RAG→栄養集計）は2026でも妥当。VLM直接カロリーより堅い。
2. しかし現行は **「単一写真から点推定する一発器」に作り込みすぎ**。**~27% MAE の壁は prompt/model でなく、入力情報・不確実性・検索候補分布・実測校正の設計問題**。
3. **過去 PDCA の主要結論（frozen-50 撤回 / pro 撤回 / v14 不採用 / global calibration VOID / 8B embedding 過剰 / 実測データが最終arbiter）は全員が支持**。ただし「prompt/calibrationでは動かない」「self-consistencyが唯一のlever」は**言い過ぎ**（= schema変更・user_context・条件付き校正・密度分布化はまだ未検証）。

本セッションで **3 AI が共通指摘したコードバグを実リポで4件確定**（下記 F1）。本計画は、3 AI の**全アイデアを漏れなく PDCA 実験にマップ**し、優先順・依存・KPI・期待効果を定義する。各実験は「仮説→変更→検証(eval/KPI/gate)→期待」のカード形式。末尾に**アイデア→実験の網羅マトリクス**を付す。

**設計思想の転換（3 AI 共通の核）**: mozu を「一発で当てるAI」から **「写真だけなら範囲推定・不確実時に1問聞く・補助情報があれば<20%を狙う・PFCまで破綻しない推定システム」** へ。

---

## Part A: Phase 0 — Foundation（精度実験の前提。これ無しの A/B は信頼できない）

### F1. 確定コードバグの修正（実リポで検証済み・全AI指摘）
| # | バグ（確定） | 場所 | 修正 |
|---|---|---|---|
| a | **`user_context` が死んでいる**（VLM に渡らない） | `services/pipeline.py` `analyze_image`(L101)に引数なし、`_analyze_meal_once`→`analyze_image` 呼び出しに未伝播 | `analyze_image` に `user_context` を追加し prompt 冒頭へ注入＋retrieval normalizer へ |
| b | **reranker `top_k=1` ハードコード** | `pipeline.py` L978（`effective_reranker_top_n` 計算済みなのに無視） | `top_k=effective_reranker_top_n` に。top-k 返却を可能化 |
| c | **`settings.VLM_MODEL_ID` 未定義**（`DEFAULT_VLM_MODEL_ID` のみ）→ AttributeError 潜在 | `services/vlm_service.py` L84 | `settings.DEFAULT_VLM_MODEL_ID` に修正 |
| d | **`match_rate_percent` が dish 非空率**（ingredientマッチ率でない） | `pipeline.py` L818 | ingredient-level / calorie-weighted な定義に変更 |
| e | calibration docstring が VOID 結論と矛盾＋有効化時に `weight_g` をスケール（危険） | `core/calorie_calibration.py` | deprecated/guard 化（in-domain実測fitなしで起動不可）。補正は別フィールド、表示gramsは不変 |
| f | config-drift 検知が VLM のみ | `admin/config_manager.py` `detect_config_drift` | embedding/reranker/weights/self_consistency/calibration も対象に |
| g | USDA検索1件失敗で全体失敗（ai1） | `pipeline.py` | partial result + warning + user-correction path を返す |

### F2. VLM呼び出しの stateless 化（全AI指摘の race condition）
`_analyze_meal_once` が `self.vlm_service.prompt/model_id/provider` をリクエスト毎に mutate → 同時リクエストで race、かつ self-consistency 並列化を阻害。prompt/model/schema を request-local に渡す形へ。→ **self-consistency 並列化（latency ~1×化）の前提**。

### F3. KPI の SSOT 矛盾を解消（全AI指摘）
README「主役=総カロリーMAE」 vs EVAL_RUBRIC「最終KPI=USER CONVICTION」が矛盾。二層に分離:
- **Model-Promotion KPI（実測GT・客観）**: 総kcal MAE% / MdAPE / p90 APE / signed bias / slope / 30%+rate / **PFC 絶対グラムMAE**（%でなく。fat MAE%は分母小で爆発）/ **density error(kcal/100g)** / **calorie-weighted recognition** / **subgroup別MAE**（<300/300-700/700-1500/>1500・bowl/plate・fried/high-fat・mixed）/ **interval coverage**。
- **Product KPI**: conviction / correction rate / retention（judge は人手golden検証まで advisory）。
- **promotion gate を AND 条件化**（ai3）: MAE≥2pt改善 ∧ paired CI上限<0 ∧ p90非悪化 ∧ bias非悪化 ∧ 30%+非悪化 ∧ recognition非悪化 ∧ latency/cost予算内 ∧ **subgroup回帰ガード**。**総カロリーだけで promote しない**（hamburger例: total近いがPFC崩壊＝相殺）。

### F4. 評価インフラ拡張（新KPIの実装＋retrieval gold set）
- `run_pdca_batch_eval.py` に F3 の新指標（PFC絶対・density error・subgroup・interval coverage・calorie-weighted recognition）を追加。
- **retrieval gold set を構築（500-1000件）**: 実VLM出力クエリ → 許容FDC候補/NG候補/raw-cooked/acceptable density range を人手付与。retrieval を end-to-end と切り離して評価（Hit@1 / **density_oracle@3** / kcal-100g error / source-tier correct）。

### F5. モデル provenance & preview 固定回避（全AI指摘）
全レスポンスに `model_id/prompt_hash/schema_version/eval_run_id` を焼き込む。`gemini-3-flash-preview` を恒久SSOTにせず stable 系（3.5 Flash等）を追跡。

---

## Part B: Phase 1-5 — PDCA 実験ロードマップ

各カード: **仮説(出所AI) / 変更 / 検証(set・KPI・gate) / 期待 / 依存**。eval は原則 N5k + NVReal 実測 + 構築する mozu 実測、`use_vlm_cache=false`、過学習防止（eval固有情報をpromptに入れない）。

### Phase 1 — Schema/prompt 再設計（v15）※「prose微調整」でなく情報設計変更
- **E1 v15 schema 分離**（ai1/2/3）: `canonical_name`/`visual_components` と `usda_query_candidates` と `portion{low,likely,high}`+`portion_basis`+`scale_reference`+`density_risk`+`prep_form` を分離。provider-native structured output(JSON Schema)。**検証**: v13 vs v15、実測3セット、Model-Promotion KPI 全部＋small-dish bucket。**期待**: 認識/portion/検索を別々に改善可能化＋PFC改善。**依存**: F1,F3,F4。
- **E2 80g下限→20g**（ai1/2/3）: main_food floor 80→20、extras 5→1。**検証**: <300kcal bucket の signed bias/MAE＋overall 非悪化。**期待**: 小皿過大(1.27x)是正。**依存**: E1。
- **E3 clarification_question フィールド**（ai1/3）: schemaに出力（UIはまだ）。**検証**: 出力頻度×実誤差の相関（高不確実=高誤差か）。**期待**: E9 の前提（どの食事で聞くべきかの信号）。

### Phase 2 — Retrieval 再設計
- **E4 Stage-0 lexical/alias 正規化**（ai2/3）: raw↔cooked / full↔low-fat / sauce/fried 修飾 / synonym / typo を BM25前段で展開。**検証**: retrieval gold Hit@1 + end-to-end。**期待**: 小コーパスで高効率・cold無し。**依存**: F4。
- **E5 embedding A/B**（全AI）: Qwen3-8B(現) vs Qwen3-0.6B vs embeddinggemma-300m vs bge-m3（全DeepInfra）[+ Voyage-4-lite/gemini-embedding-2 はベンダー承認時]。各で13.5k再埋め込み+FAISS再構築。**KPI**: Hit@1/density_oracle@3/kcal-100g error/latency(cold&warm)/end-to-end calorie。**期待**: ~30s→<1-3s、品質非劣。**依存**: F4,F5。
- **E6 reranker A/B**（全AI）: Qwen3-Reranker-4B(現) vs nemotron-rerank-1b vs Qwen3-Reranker-0.6B（DeepInfra）[+ gte-modernbert 自己ホスト optional]。**enriched documents**（kcal/100g・prep・raw/cooked を doc に付与）。config `reranker_top_n` を使用（F1-b後）。**KPI**: density error/Hit@1,3/latency。**期待**: 4B(77.7%/1100ms)→ nemotron(83%/243ms)。**依存**: F1-b,F4。
- **E7 top-1→top-k density 分布**（全AI）: top-k 候補を確率付き保持→ `E[kcal]=E[g]×E[kcal/g]` ＋ low/likely/high。**検証**: 総カロリーMAE + interval coverage。**期待**: density誤差(50%)に直接。**依存**: E6。

### Phase 3 — 入力情報レバー（27%壁の本命）
- **E8 user_context → VLM+retrieval**（全AI最重要）: 「半分食べた/店名/メニュー/皿径/大盛り」を prompt+normalizer へ。**検証**: context有/無の split A/B（leak管理＝許可フィールド固定）。**期待**: 27%壁の最大レバー。**依存**: F1-a。
- **E9 1問確認ループ**（全AI）: 不確実時のみ1問（GTから模擬回答 or 小規模対話eval）。**KPI**: one-question-improvement MAE / selective abstention precision。**期待**: K=3 self-consistency超の効率。**依存**: E3,E8。
- **E10 multi-photo / before-after / scale-reference 高精度モード**（全AI）: 横1枚追加・参照物・depth/ARKit・食べ残し。**検証**: 撮影した小規模 captured set で MAE。**期待**: 単眼スケール曖昧性を物理的に突破（研究: 重量情報で大幅改善）。**依存**: E8（データ取得設計）。
- **E11 total-mass-first → 配分**（ai3）: 画像全体の総食物質量→面積/体積比で配分→density化（per-item積上げの別ルート）。**検証**: 総カロリーMAE 対 per-item。**期待**: grams側の改善。**依存**: E1。
- **E12 self-consistency v2**（全AI）: ①**selective**(高不確実/高カロリー/density分散大/VLM-DB乖離時のみ) ②**parallel**(F2後) ③**structured-consensus**(K出力の食材をクラスタ・ingredient別median portion・weighted density mixture、retrievalはunique query 1回)。**検証**: MAE + latency 対 現行K=3-median。**期待**: ~2pt を latency増なしで。**依存**: F2,E7。

### Phase 4 — 条件付き校正 + 実測データ
- **E13 実測 mozu 200-500件 層化収集**（全AI: 20-50は方向確認のみ）: food-group/angle/容器/大小/cuisine/外食自炊/高低脂質 で層化。**active learning**（高不確実/高カロリー/モデル間不一致を優先）。blind holdout 分離。**期待**: 校正・promotion gate の母集団。
- **E14 条件付き/階層校正**（全AI: global VOIDは維持）: food-group×container×size×angle×confidence の**乗算的**補正を E13 で fit→held-out検証。**補正後カロリーは別フィールド**（表示gramsは改変しない）。grams under と density over の相殺を壊さぬよう同時最適化。**依存**: E13,E7。
- **E15 専用 portion モデル**（ai2/3, P2）: segmentation + depth prior + food-class density。VLMは属性補正に。**検証**: portion grams MAE。**依存**: E10,E13。
- **E16 direct-VLM-calorie を feature 化**（ai1）: USDA-total + VLM-direct + dish_type + weight + confidence の小 stacker。**検証**: 相殺誤差検出で MAE/PFC。**依存**: F4。

### Phase 5 — モデルルーティング
- **E17 Gemini 3.5 Flash + native params A/B**（全AI）: 3.5 Flash を同一gateで。`thinking_level`/`media_resolution` を Google API直で eval。**KPI**: Model-Promotion 全部。**依存**: F3,F4,F5。
- **E18 tiered routing**（ai1/3）: Flash既定 + 高不確実時のみ Pro/3.5 を**second-opinion/不確実性検知器**として。2モデル乖離大→ユーザー確認。**期待**: コスト維持で難例改善。**依存**: E9,E17。

---

## Part C: アイデア→実験 網羅マトリクス（全アイデアが検証対象）
| AIアイデア | 出所 | 実験 |
|---|---|---|
| 認識/query/portion 分離 | 1,2,3 | E1 |
| weight low/likely/high・分散伝播 | 1,2,3 | E1,E7,E12 |
| 80g下限撤廃 | 1,2,3 | E2 |
| USDA命名を後段分離 | 1,2,3 | E1 |
| density_risk/可視油/prep | 1,2,3 | E1 |
| clarification question | 1,3 | E3,E9 |
| provider-native structured output | 1,2 | F5,E1 |
| user_context 活用 | 1,2,3 | E8(+F1a) |
| top-k density 分布 | 1,2,3 | E7 |
| Stage-0 lexical/alias | 2,3 | E4 |
| enriched reranker docs | 2 | E6 |
| embedding 軽量化 A/B | 1,2,3 | E5 |
| reranker 軽量化 A/B | 1,2,3 | E6 |
| retrieval gold + kcal/100g・density_oracle@3 | 1,2,3 | F4 |
| scale/multi-photo/before-after/depth | 1,2,3 | E10 |
| total-mass-first | 3 | E11 |
| self-consistency selective/parallel/structured | 1,2,3 | E12 |
| 条件付き/階層校正 | 1,2,3 | E14 |
| 200-500 層化実測 + active learning | 1,2,3 | E13 |
| 専用 portion モデル | 2,3 | E15 |
| direct-VLM-calorie を feature | 1 | E16 |
| Gemini 3.5 Flash / native params | 1,3 | E17 |
| tiered routing / Pro=不確実性検知 | 1,3 | E18 |
| preview固定回避 + provenance | 1,2,3 | F5 |
| KPI SSOT統一・PFC絶対・interval coverage・subgroup guard・calorie-weighted recognition | 1,2,3 | F3,F4 |
| 確定コードバグ(VLM_MODEL_ID/reranker top_k/match_rate/calibration docstring/config-drift/stateless/partial-fail) | 1,2,3 | F1,F2 |

---

## Part D: 推奨シーケンス・依存・検証
**順序**（依存に基づく）:
1. **Phase 0 全部（F1-F5）**を先に（バグ修正＋KPI＋eval gold set＋stateless＋provenance）。精度実験はこの後でないと信頼できない。
2. **並行で着手可能な早期勝ち**: E5/E6（embedding/reranker A/B＝latency本丸）、E8（user_context＝精度本丸）、E2（80g floor＝安価）。
3. **Phase 1（E1,E3）→ Phase 2（E4,E7）→ Phase 3（E9,E11,E12）**。
4. **E13（実測収集）は今すぐ並行開始**（リードタイム長）。揃い次第 **E14**。
5. **Phase 5（E17,E18）**は F5 後に随時。**E10/E15**は P2（プロダクト/データ依存）。

**各実験の検証手段**: `scripts/run_pdca_batch_eval.py`（F4拡張後）で実測3セット A/B → Model-Promotion KPI + subgroup guard + paired CI。retrieval系は retrieval gold set。latency/cost は per-stage計測（embedding cold/warm含む）。全て lesson 化＋ promotion gate 通過のみ採用。

**進め方の原則**（過去PDCA継続）: 1度に1機能・eval確認後に次へ・no fallback・過学習防止・結果保存なしに改善と言わない・promote主張はrun自身のartifactのみ。

**最初の着手候補（ユーザー承認後）**: F1（確定バグ7件）+ F3（KPI分離）+ F4（eval拡張＋retrieval gold set 雛形）。これが全実験の土台。

---

## Part E: Provider-agnostic「最良モデル」前提への拡張（2026-06-04 ユーザー指示）

**方針転換**: VLM / Embedding / Reranker の各スロットを **DeepInfra / OpenRouter に限定せず、provider 横断で最良モデルを採用する前提**で探索する。従来 E5/E6/E17 は DeepInfra/OpenRouter に事実上固定だったため、premium provider を正式候補に格上げする。オンボード合意済み provider（キー用意可）: **Voyage AI / Google AI(Gemini) / Cohere / OpenAI**。

### F-PROV. Provider 抽象化の基盤（前提タスク）
- **Embedding**: 現状 query 時は app-local `DeepInfraService` 直結で `services/embedding_providers.py` の factory を通っていない。query+build の両方を `EMBEDDING_PROVIDER`+`EMBEDDING_MODEL` で provider 選択できる**統一クライアント**に通す（provider 別の input_type/prompt 規約・dim・正規化を内包）。`format_embedding_query/document`（実装済）を provider 別に拡張。
- **Reranker**: 既に `RerankerProviderFactory`+`RERANKER_PROVIDER` env で抽象化済。Cohere/Voyage provider クラスを追加。config に `reranker.provider` を追加。
- **VLM**: `VLMProviderFactory`（deepinfra/openrouter）に **Google AI Studio native provider** を追加（E17 の native params: `thinking_level`/`media_resolution` を直叩き）。
- 各 provider は `*_API_KEY` を env から読む（ハードコード禁止・`.env` 管理）。

### E5'/E6'/E17' premium 候補マトリクス（要キー）
| slot | provider | 候補モデル | 備考 |
|---|---|---|---|
| Embedding | Voyage | `voyage-3.5-lite` / `voyage-3.5` | research doc 本命・warm hosted・1024dim Matryoshka・$0.02/1M |
| Embedding | Google | `gemini-embedding-001` | MMTEB 上位・MRL truncatable |
| Embedding | OpenAI | `text-embedding-3-large` | ベースライン比較用 |
| Embedding | Cohere | `embed-v4.0` | retrieval 定番 |
| Reranker | Cohere | `rerank-v3.5` | retrieval 定番・高品質 |
| Reranker | Voyage | `rerank-2.5` / `rerank-2.5-lite` | warm hosted・無料枠大 |
| Reranker | (self-host) | `gte-reranker-modernbert-base` | research doc 本命(83% Hit@1) ただし self-host 要 |
| VLM | Google native | `gemini-3-*`（AI Studio 直） | native params A/B（E17） |

### 検証方法（E5/E6 と同一の厳密 isolation）
- Embedding A/B: 各候補で 13,564 docs 再index（`build_embedding_ab_index.py` を provider 対応に拡張）→ `VLM_CACHE_DIR` 凍結で retrieval 単独分離 → calorie MAE + dense recall probe + latency(cold/warm)。
- Reranker A/B: 同一 embedding・VLM 凍結で per-request override。
- VLM A/B: native params は frozen 不可（VLM 自体を変える）→ 通常の paired eval。
- 全て promotion gate（F3 AND条件）+ lesson 化。

### 重要な留意（情報に基づく優先順位）
- **Embedding は既に open SOTA 天井近く**: 現 Qwen3-Embedding-8B=MMTEB open #1 系、0.6B が非劣性確認済。premium closed prem の主利点は **warm-hosting（cold-start 解消）**であり cold-start は 0.6B 採用で既に解消済 → premium embedding の品質上振れは限定的の見込み（要検証）。
- **3 AI レビューの最大レバーは retrieval モデルでなく E8(user_context)/E13/E14(実測校正)**。provider 横断探索と並行して、これらの 27%壁レバーも進める。

### 進捗（2026-06-04〜05 セッション）
- **E5/E6（DeepInfra 範囲）完了**: light スタック **Qwen3-Embedding-0.6B + Qwen3-Reranker-0.6B** が現行 8B+4B 比で calorie MAE −3.45pt(凍結)/−3.87pt(実VLM)・p90/dish_match 改善・~9×低レイテンシ（lesson `20260604_e5e6_lightweight_embedding_reranker_ab`）。bge-m3/gemma/4B は品質劣化 or bias反転で非クリーン。gate は paired CI 上限>0 で HOLD-for-significance（方向一貫・latency/cost 勝ちは無条件）。
- **F-PROV 基盤 実装完了**: `services/extra_providers.py`（Voyage/Google/Cohere/OpenAI を `"provider:model"` 接頭辞で routing・429 retry・新規依存なし）+ query/build/rerank 経路に配線（DeepInfra 既定不変）。キー `.env` 登録済。
- **E5'/E6'（cross-provider）完了**: Google `gemini-embedding-001`(MTEB#1)/Cohere `embed-v4.0`/OpenAI `text-embedding-3-large` 埋め込み + Cohere `rerank-v3.5` を凍結VLM・retrieval単独分離でA/B。**結論=premium はどれも free open にクリーン勝ちせず**（全 paired CI 0跨ぎ・強い埋め込みは平均MAE −2〜3pt だが bias を負反転）。**retrieval slot は天井**（lesson `20260605_cross_provider_retrieval_no_clean_win`）。Voyage は 403（キー要確認）。
- **E17'（VLM native）完了**: `GoogleVLMProvider` 実装（factory に `"google"` 登録、native params を model-id suffix `|media=high|think=high` で per-candidate 指定）。A/B(cache=false 実VLM, 8B+4B固定): **Google-native も native params も calorie 改善せず**（OpenRouter baseline 18.2% が最良、google_native +7.0pt p=0.004 悪化／media=high +4.8／think=high +3.7、全て悪化）。caveat: n=50 cache=false の VLM draw 分散大だが「勝ち無し」は明確。lesson `20260605_cross_provider_retrieval_no_clean_win` に統合。
- **全 cross-provider スロット結論**: embedding / reranker / VLM-native のいずれも free/現行スタックにクリーン勝ちせず＝**モデル選択は天井**。**次の本命レバー = E8(user_context)・E13/E14(実測校正)・E3/E9(不確実性/1問確認)**（3 AI レビューの核）。retrieval/VLMモデルの更なる探索は非優先。
</content>
