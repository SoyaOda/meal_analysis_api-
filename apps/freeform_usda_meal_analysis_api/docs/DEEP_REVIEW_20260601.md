# Deep Review — freeform_usda_meal_analysis_api (2026-06-01)

> Lead reviewer による総合レビュー。対象: `apps/freeform_usda_meal_analysis_api`（食事写真 → 食材・栄養推定、主要KPI = 総カロリーMAE%、固定50枚ベンチ）。
> 全主張はコード/評価データ/外部リサーチに基づく。重大度タグ: P0(最優先) / P1 / P2 / P3。工数: S(数時間) / M(1-2日) / L(数日)。

---

## 1. エグゼクティブサマリー

### 現状 (Current State)
- ベースライン: `openrouter:google/gemini-3-flash-preview` + prompt v11b(component density) + temp 0.3 / reasoning medium / max_tokens 12288 / stage1_top_k 50。**calorie_mae 11.38%**, high-error(>30%) 4.0%, latency 14.3s, cost $0.0072/枚（`evals/baselines/current_baseline.json` で検証済: 11.3765%, 50/50成功, coverage_complete）。
- アーキテクチャは妥当: 4段(VLM → ハイブリッド検索 → USDA栄養 → 線形合算)。USDA FNDDS/Survey の選択、FAISS Flat(13,564件)、BM25+dense+RRF、Qwen3-Embedding/Reranker、prompt内部の二段分解(Pass1/2/3) はいずれも 2025-2026 のSOTA慣行と整合。
- **11.38% は単写真VLMとして本物のSOTA級**: GPT-5 image-only(30.5%)を大きく上回り、フル食材リスト付きGPT-5(13.9%)や専用RGB-Dモデル(13.5-14.7%)すら凌ぐ。だからこそ独立検証(Nutrition5k)が必要。

### Top 5 Takeaways
1. **数値の土台が統計的に脆い。** 採用ゲートは単一n=50ランで固定1.0pt差(`scripts/run_pdca_batch_eval.py:587`)だが、同一v11b構成の再走で 11.37 → 13.28(mae_std 2.36)。ラン間ノイズがゲート閾値の約2.4倍。**1.0pt差は統計的に無意味** → これを直すまで他の精度施策は測定不能。
2. **prod ≠ ベンチ(構造的ドリフト)。** Firestore永続docが verbatim返却され code default と一切リコンサイルしない(`admin/config_manager.py:299`)。本番は prompt v7 を配信、全PDCAは v11b を計測。ハーネスも served config 一致を assert していない(`run_pdca_batch_eval.py:394-395`)。ユーザーはベンチした pipeline を使っていない。
3. **サイレントfallbackが no-fallback ルールに反し、ベンチを不可視に汚染。** `_parallel_search`→sequential(`pipeline.py:852`)、ConfigManager→in-memory(`config_manager.py:311`)、栄養欠損→0kcal。いずれも失敗を隠し、PDCAで劣化経路の結果を「正常」に見せる。
4. **検索の数学バグ。** index は IndexFlatIP(内積=コサイン)だが `vector_scores = 1.0/(1.0+distances)`(`hybrid_search.py:529,846,999` で検証)は L2距離変換で順序を圧縮/反転。加えてクエリベクトルが L2正規化されない(`normalize_L2` がservices内に皆無)。重み付き融合のvector項(0.6, 支配的)が歪む。
5. **次の精度レバーは検索チューニングではなく portion/mass 推定。** 業界横断でカロリー誤差の支配源は分量推定(中央値15-25%、VLM weight MAPE 36-110%)。plate/bowl径によるスケールアンカー、FNDDS世帯計量のグラム変換、大盛り時の下方バイアス補正が最高ROI。

### 単一最重要次手 (Highest-Leverage Next Step)
**採用ゲートを paired BCa bootstrap CI + 強制リピートに置換する(P0)。** これは前提条件であり、ノイズと信号を区別できない限り、prompt改善も検索修正も「効いたか」を判定できない。先にこれをやってから精度施策のA/Bに入る。

---

## 2. システム全体アーキテクチャ

### データフロー(テキスト図)
```
[Client] --multipart image--> POST /api/v1/meal-analyses/complete  (routers/analysis.py:75)
   |                                  \--SSE--> /stream (routers/streaming.py:384  ※完全複製・ドリフト済)
   v
[analyze_meal_from_image] (services/pipeline.py:276)
   | ConfigManager(Firestore) から effective config 解決(override > config > init)
   | ★ pipeline.vlm_service.prompt/model を in-place 変異(pipeline.py:378-415) ← 並行時に config bleed
   v
Step1: VLM (services/vlm_service.py:79 → providers/{openrouter|deepinfra|alibaba})
   |  image→JSON {meal_title, dishes[].main_food/extras: search_name, weight_g, confidence}
   |  ※ response_schema 強制なし。4-5系統のJSON手書きcleanup。VLMキャッシュ照合(vlm_cache.py:100)
   v
Step2: extract_queries (services/query_extraction.py:20)
   |  dishes を flat query list 化。weight_g 直読み。欠損時 density_map/typical_weights fallback(magic number)
   v
Step3: _parallel_search (pipeline.py:729)  ★ 例外時 sequential へサイレントfallback(pipeline.py:852)
   |  batch-embed → per-query [BM25(main_name+desc) + FAISS(full desc, IP) → RRF(k=60) + 重み付き融合] → batch-rerank top1
   |  (services/hybrid_search.py, services/usda_search.py, services/deepinfra_service.py:460)
   v
Step4: _enrich_food_item → fdc_id → 栄養 per-100g (services/nutrition_service.py:59)
   |  NutritionCalculator.calculate = per100g × weight_g/100 (線形)。欠損→None/0kcal サイレント
   v
_calculate_total_nutrition (pipeline.py:1081) 全dish合算 → total_nutrition.calories = KPI
   v
[AnalysisResponse]  ai_model_used/prompt_file_used は変異済 shared state を読む(pipeline.py:657-667)
```

### サブシステム要約(各2-4行 + ファイル参照)
- **Pipeline Orchestration**: 4段を3トランスポート(JSON / SSE / 未使用Cloud Tasks)に配線。`analyze_meal_from_image` が config優先順位を解決し shared VLM state を変異してから `analyze_image` を呼ぶ。SSEは全ロジックを inline 複製。`services/pipeline.py:95,276,729,989`。
- **VLM / Provider**: `VLMService` が prompt をeager load、`VLMProviderFactory` が `provider:model` を解析。3プロバイダはOpenAI互換クライアントをラップ。reasoning_effortはOpenRouterのみ honor。`services/vlm_service.py:79`, `providers/factory.py:35`。
- **Retrieval / DB**: 13,564件USDA統一コーパス(FAISS Flat IP 4096-dim 222MB + BM25 + reranker)。dense と sparse は異なるテキスト面を index。`services/hybrid_search.py:480,936`, `services/usda_search.py:69`。
- **Nutrition + Portions**: per-100g × weight/100 の純線形合算。誤差源は上流(VLM weight + record match)であり計算層ではない。portions_normalizer はUI専用で計算経路外。`services/nutrition_service.py:93`, `services/pipeline.py:1081`。
- **EVAL / PDCA**: 固定50枚、dev40/holdout10、leakageスキャン、cost/latencyゲート、split-merge、repeated-eval、knowledge export、session bootstrap。KPIは総カロリーMAE%のみ。`scripts/run_pdca_batch_eval.py:666`。
- **API / Config / Admin**: ConfigManager(Firestore-backed)が runtime SSOT、settings.py はfallback。Admin dashboard が dot-key PUT で更新。`/health` が live config を返す。`admin/config_manager.py:279`, `routers/health.py:34`。
- **Resilience / Core**: tenacity retry + aiobreaker circuit breaker + VLM/embeddingキャッシュ + httpx pool + startup index loader。`core/retry.py:57`, `core/circuit_breaker.py:88`, `core/vlm_cache.py:100`。

---

## 3. 各サブシステムの所見

### Pipeline Orchestration
- **強み**: 4段が明快に分離。config優先順位が明示的(override > ConfigManager > init)で `prompt_file_used` を応答に反映。`_calculate_total_nutrition` は型検証付きで不正型に raise(fail-loud)。
- **[high]** `_parallel_search` が2-phase失敗を握りつぶし sequential へサイレントfallback(`pipeline.py:852`)。劣化経路の結果がベンチを汚染。
- **[high]** query-drop / dish-index 不整合で IndexError or 栄養誤割当の可能性(`query_extraction.py:193`, `pipeline.py:1007-1015`)。位置依存zipの脆い結合。
- **[medium]** shared VLM state の per-request 変異 → 並行時の config bleed + provenance 誤ラベル(`pipeline.py:378-415,657-667`)。
- **[medium]** SSEが応答構築ロジックの完全複製で既にドリフト。`/stream` は usda_match 無しmain_foodをサイレントskip(`streaming.py:575`)、`/complete` は raise(`pipeline.py:454`)→ KPIが経路で食い違う。
- **[low]** `async_processor.py` は dead code(存在しない `services.meal_analyzer` を import)。エラー契約が `/complete`(500/400) と `/stream`(SSE error) で不一致。

### VLM / Provider
- **強み**: provider抽象が ABC で整理。JSON最終失敗時は `/tmp` にdumpして raise(fail-loud)。OpenRouterは cost を usage から抽出。
- **[high]** Alibaba provider に retry も circuit breaker も無い(`alibaba_provider.py:146`)。耐障害性がプロバイダ間で不一致。
- **[high]** OpenRouterの `']'→'}'` ヒューリスティック(`openrouter_provider.py:283`)が有効JSONを意味的に破壊し得る。「cleaning successful」ログが改変を隠す。
- **[medium]** JSON cleanup が4-5系統に分岐(各provider + dead deepinfra_service + text_analysis_serviceの別regex)。同一モデルでも provider依存の結果 → ベンチ非可搬。
- **[medium]** `config.vlm.prompt_text` が VLMService に無視される(`vlm_service.py:55`)。silent config drift。
- **[medium]** 全escaping errorを `raise Exception(...)` で包み、型を消失(`openrouter_provider.py:339` 他)。retry分類と breaker exclude を破壊。

### Retrieval / DB
- **強み**: FNDDS/Survey はmixed-meal正解、FAISS Flat は13.5k件に正しいindex type、BM25+dense+RRF は標準、Qwen3 は強い選択。
- **[high]** dense=full description / sparse=`main_name+descriptors` と異なるテキスト面をindex(`build_bm25_index.py:51`)。口語名(fries/soda/coke)のlexical recall低下。
- **[high]** クエリベクトルが L2正規化されない(services内に `normalize_L2` 皆無)。コサイン順位がプロバイダ前提に暗黙依存、fail-loud違反。
- **[high]** index version drift: FAISS/metadata は1/19、BM25は10/28・12/6で共有checksum無し(`usda_bm25_index/params.index.json`)。行整合が崩れれば誤item返却の潜在地雷。
- **[medium]** 内積similarityにL2距離変換 `1/(1+d)`(`hybrid_search.py:529,846,999` で検証)。vector_normalized項が歪曲。
- **[medium]** RRF項が数値的にinert(~0.016-0.03 vs 0-1正規化)。実質 bm25*0.4+vector*0.6、rrf_weight=0.55は機能していない(`hybrid_search.py:582-585`)。
- **[medium]** reranker が `description` のみで採点。source-tier(sr_legacy 7793/13564 が支配・生食材寄り)を無視 → 「fried X」が生commodityにマッチしカロリー膨張。
- **[low]** 「Soft drink, cola」ハードコードprobe + 全クエリ `print(json.dumps)`(`hybrid_search.py:363,676`)。本番デバッグ出力。

### Nutrition + Portions
- **強み**: 計算層は忠実な線形 multiply-and-sum(`nutrition_service.py:120` 検証)。誤差源ではない。13,564件全てに4栄養素キーあり。
- **[high]** 栄養/weight/fdc_id 欠損をサイレントに0.0扱い(`pipeline.py:1104,1136`, `nutrition_service.py:155`)。MAEを不可視に下方バイアス。
- **[high]** `calculate` が未知fdc_idで None返却 → 合算がfalsy skip(`pipeline.py:1097`)。index/metadataドリフト時にカロリーが静かに消える。
- **[medium]** dish合計とmeal合計が独立2経路(`pipeline.py:622` vs `:649`)。編集で静かにdesync。
- **[medium]** density_map/typical_weights の未検証magic number(`query_extraction.py:107-134`)。v11b下は休眠だが weight_g欠損時にMAE支配の可能性。
- **[low]** estimated_cost_usd が reranker/embedding コストを除外(VLM-only)。fiber/sugar/sodium はDB未収載なのに応答schemaに存在。

### EVAL / PDCA
- **強み**: 運用が成熟(固定golden set、splits、leakageスキャン、cost/latencyゲート、split-merge、repeated-eval、bootstrap)。多くのチームより先行。
- **[high]** ラン間MAE分散(~2pt)が1.0pt採用マージンを超過、CI/有意検定なし(`run_pdca_batch_eval.py:587`)。
- **[high]** GT macros/per-dish weight/食材名を loadするが採点せず、生payloadも capture時に破棄(`:124,388-397`)。誤差の所在が診断不能、相殺誤差を success と誤判定。
- **[high]** served config と candidate の一致を assert しない(`:394-395`)→ v7/v11b ドリフトが不可視。
- **[medium]** MAE/high30 が success行分母 → 静かな失敗が標本を縮め罰されない。
- **[medium]** signed bias/calibration metric 無し(abs()で符号破棄、`:136`)。midpoint_calibration/energy_density_sanity variant の効果が測れない。
- **[medium]** label_cal<=0 で 0/100 退化。絶対kcal metric 不在。
- **[low]** holdout_10 が静的every-5th、毎セッション再利用で第二dev set化。leakage検出が浅い。

### API / Config / Admin
- **[high]** prod prompt drift が構造的: 永続docが code default とリコンサイルしない(`config_manager.py:299`)。version stamp/startup reconcile/health flag いずれも無し。
- **[high]** Firestore失敗をサイレントに in-memory default へfallback(`config_manager.py:209,311`)。no-fallback違反、transient IAM障害で本番configが静かに切替わる。
- **[medium]** Admin save が Local tab で相対パス → 別環境へ誤書込みのfootgun(`dashboard.html:723`)。
- **[medium]** Admin endpoints が完全に無認証(`router.py:106`)。誰でも本番model/promptを変更可能。
- **[medium]** ConfigManager singleton が初回引数のみ採用、cache_ttl(5s debug値)が本番値。
- **[low]** dashboard が APIConfig SSOT を部分的にしかカバーせず(use_cache/seed のUI欠落)。`update_config` がtypoキーをサイレント無視、deprecated `datetime.utcnow()`。

### Resilience / Core
- **[high]** retry-over-breaker stacking(`openrouter_provider.py:60-61`)。1失敗requestが最大3 breaker失敗を計上、fail_max=5で約2requestでtrip。
- **[high]** breaker `exclude=()` で permanent/application error(auth, JSON parse)もtrip閾値に計上(`circuit_breaker.py:92`)。
- **[medium]** reranker 5xx/429 が retry されない(`httpx.HTTPStatusError` が RETRYABLE_EXCEPTIONS 不在, `retry.py:44`)。
- **[medium]** VLM/embedding provider が共有HTTP pool をbypass(`openrouter_provider.py:53`)。最大遅延のVLM呼が pool恩恵なし。
- **[medium]** cache が created_at evict(=FIFO, not LRU)。process-global で24h TTL → use_vlm_cache=true 時にラン間汚染。
- **[low]** aiobreaker/BigQuery のソフト無効化(fail-loud違反)。`startup_optimizer.get_indexes` の busy-wait + dead lru_cache stub。

---

## 4. 最新リサーチ要約 (2025-2026)

### VLM Food SOTA / Portion 推定
- 専用Nutrition5kモデル(RGB-D/ViT) ~13.5% MAPE(28 kcal MAE)、2025各種で14.4-14.7%。**11.38% はこれを上回る → 要独立検証**。 https://pmc.ncbi.nlm.nih.gov/articles/PMC13092701/
- CVPR2025 二段(分解→計算)で one-shot比 15-20% 誤差削減、非可視item幻覚減。 https://openaccess.thecvf.com/content/CVPR2025W/MTF/papers/Khlaisamniang_Decomposing_Food_Images_for_Better_Nutrition_Analysis_A_Nutritionist-Inspired_Two-Step_CVPRW_2025_paper.pdf
- prompt修飾子の独立効果: expert persona −10.4 MAPE pt(最大)、multimodal CoT −64 kcal、scale hint −40 kcal。 https://arxiv.org/html/2507.07048v1
- GPT-5: image-only 30.5% MAPE、フル食材リスト付きでも13.9%。bowls/deep dish が高誤差。 https://pmc.ncbi.nlm.nih.gov/articles/PMC12655113/
- 臨床head-to-head: 旧Gemini 1.5 Pro は energy 64.2% MAPE と弱いが、**Gemini 3 Flash は別世代**(81.2% MMMU-Pro, Roboflow vision #1, counting/spatial が強化) → 選択は妥当。 https://pmc.ncbi.nlm.nih.gov/articles/PMC12513282/ , https://blog.google/products-and-platforms/products/gemini/gemini-3-flash/ , https://blog.roboflow.com/use-gemini-3-5-flash-vision/
- スケール曖昧性が中核未解決問題、plate径は ~2%誤差で推定可能(marker-less scale anchor)。 https://arxiv.org/html/2602.05078
- 制約デコード(JSON schema)は精度を ~3-4% 改善し reasoning を害さない、Gemini は flat schema で85-98%遵守。 https://arxiv.org/html/2501.10868v1

### Nutrition DB & Retrieval
- FNDDS/Survey が「as consumed」mixed-meal の正解data type。SR Legacyは生食材、Branded は±20%許容で最不信頼。 https://fdc.nal.usda.gov/data-documentation/ , https://fdc.nal.usda.gov/faq/
- portion/quantity推定が支配的誤差源(中央値15-25%)。FNDDS世帯計量をVLMに渡しグラム変換すべき。 https://arxiv.org/html/2602.05078v1
- 2025 SOTA food entity linking は normalize(調理法+synonym)→ NER→NEL 二段。 https://arxiv.org/html/2509.22125
- RRF k≈60 は標準だが、短い literal food名では BM25比重↑、低RRF k(20-40)が有効。 https://blog.serghei.pl/posts/reciprocal-rank-fusion-explained/ , https://ceur-ws.org/Vol-4173/T3-7.pdf
- Qwen3-Embedding 4096-dim が222MBの主因。4B(2560)やMRL truncation(1024/2048)/float16で2-4x削減・精度維持。8B reranker は0.6B比+3pt程度。 https://arxiv.org/html/2506.05176v1 , https://docs.bswen.com/blog/2026-02-25-best-reranker-models/
- 13.5k件は FAISS Flat が公式推奨(IVFは~1M+で初めて有利)。 https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index

### Eval Methodology
- Eval-driven development が標準: golden set 50-200(failure-mode重み付け)、prompt変更毎にCI、PR差分。 https://www.braintrust.dev/articles/best-ai-evals-tools-cicd-2025
- 「When Better Prompts Hurt」: 汎用prompt改善がタスク精度を-10〜13%退化させ得る。5%差検出に~400-600例必要 → n=50ではCI必須。 https://arxiv.org/html/2601.22025v1
- MAPEは過小予測を、sMAPEは過大予測を有利化。MAE(kcal)+signed bias を併記すべき。 https://towardsdatascience.com/choosing-the-correct-error-metric-mape-vs-smape-5328dec53fac/
- 回帰推定は小値で過大・大値で過小(regression to the mean)。predicted-vs-actual calibration slope で診断。 https://arxiv.org/html/2405.15950v2
- ID誤差と portion/mass誤差は分離可能、Hungarian割当で recall/precision/F1。 https://pmc.ncbi.nlm.nih.gov/articles/PMC13092701/ , https://github.com/rafaelpadilla/Object-Detection-Metrics
- paired BCa bootstrap protocol: per-image paired delta + BCa CI + sign-flip permutation、CI下限>0でのみ採用。 https://arxiv.org/pdf/2511.19794 , https://arxiv.org/pdf/2404.12967
- LLM/VLMは temp=0でも非決定的(kernel variance)。3-5回反復推奨。 https://arxiv.org/html/2506.09501v2
- overfitting対策: never-tuned holdout、定期rotation、hard negative、metamorphic test。 https://arxiv.org/html/2502.07445v2

### Claude Code Best Practices (2026)
- Claude は CLAUDE.md を読む(AGENTS.md は読まない)。先頭に独立行 `@AGENTS.md` import で一元化。各ファイル<200行。 https://code.claude.com/docs/en/memory
- commands は skills に統合(`.claude/skills/x/SKILL.md`)。skillは on-demand load、`` !`cmd` `` で live state注入、`context: fork` でサブエージェント実行。 https://code.claude.com/docs/en/skills
- subagent(`.claude/agents/*.md`)は冗長作業を別contextに隔離、`memory: project` で学習蓄積、安価モデル可。 https://code.claude.com/docs/en/sub-agents
- hooks(`.claude/settings.json`)で決定的自動化: PostToolUse `Write|Edit`→format/lint、SessionStart→bootstrap、Stop→handoff。 https://code.claude.com/docs/en/hooks
- monorepo は two-tier CLAUDE.md(root=layout、per-app=stack/commands)、app dir 内で起動。 https://code.claude.com/docs/en/large-codebases
- headless `claude -p` + binary evals(明示pass/fail assertion)で自己改善ループ。`--bare` で再現的CI。 https://code.claude.com/docs/en/headless
- Gemini 3 は `thinking_level`(未指定=high → cost膨張)、OpenRouterは prompt prefix安定化でcache hit、`response_format` strict JSON。 https://ai.google.dev/gemini-api/docs/gemini-3 , https://openrouter.ai/docs/guides/best-practices/prompt-caching

---

## 5. 全体レビュー所見 (Honest Assessment)

### Architecture & Pipeline
マクロ設計は研究検証済で堅実。誤差は計算層(忠実な線形)ではなく上流2点 ―(1) VLM weight_g 推定、(2) per-100g密度を決める fdc_id マッチ ― で生じる。研究は分量推定が支配的(15-25%)と一致するため、最高ROIは VLM portion 推定(scale anchor / density prior / 大盛り補正)、次が検索の正しさ。計算層は fail-loud 硬化のみで十分。
最も危険な構造的問題: prod config drift(prod≠ベンチ)、no-fallbackポリシー違反のサイレントfallback群、内積indexにL2距離変換という確定数学バグ、ノイズ内に収まる1.0pt採用ゲート、schema強制なしの脆いJSON parsing。

### Eval Framework
運用は成熟だが科学的弱点が2点に集中。(1) 採用判定が単一n=50集計の点推定で固定1.0ptゲート、自身の repeat data が mae_std 2.36(`evals/repeat_runs/20260225_122414`)を示すのにノイズ>閾値。(2) GTは豊富(per-dish main_food/extras + weight_g + 全macros)だがKPIは meal-level abs calorie %のみ、生payloadは capture時に破棄され遡及解析も不可。誤差の所在を診断できず相殺誤差を見逃す。
**ツール判断: 自作ループは維持が正解。** Hungarian dish-matching / USDA fdc_id正確性 / energy-density誤差 はドメイン固有で、promptfoo/Braintrust への移行は net-negative。高ROIは `run_pdca_batch_eval.py` への metric + 統計の追加であって移行ではない。

---

## 6. 優先度付きロードマップ(統合・重複排除済)

| 優先度 | 領域 | 施策 | 根拠 | 工数 | 根拠箇所 |
|---|---|---|---|---|---|
| **P0** | Eval | 採用ゲートを paired BCa bootstrap CI(CI下限>0でのみ採用)+ run_repeated_eval にコード強制stability閾値 + 強制 seed/generation_id 記録に置換 | 単一1.0ptゲートが mae_std 2.36 のノイズ内。全精度施策の前提 | M | `run_pdca_batch_eval.py:587`; `evals/repeat_runs/20260225_122414`; arXiv 2511.19794 |
| **P0** | Config/Eval | served config == candidate を各呼でassert(model/prompt SHA、不一致でfail-loud)+ prod Firestore を v11b へ明示promote + `/health` config_drift flag + APIConfig schema_version | prod=v7/ベンチ=v11b、ハーネスも未検証 → ベンチ無意味化 | M | `config_manager.py:299`; `run_pdca_batch_eval.py:394-395`; bootstrap remote check |
| **P0** | Retrieval | 内積scoreを `1/(1+d)` から直接similarityへ修正(3箇所)+ クエリ `faiss.normalize_L2`(or assert)+ 修正後に融合weight sweep再走 | IndexFlatIP に L2変換は順序歪曲。正規化未実施は暗黙provider依存 | S | `hybrid_search.py:529,846,999`; `build_index_with_nutrition.py:446`; services内 normalize_L2 皆無 |
| **P0** | Claude Code | lean root CLAUDE.md(6アプリ orient, <60行, `@AGENTS.md` import)+ 薄いper-app wrapper + 他4アプリにstub | root .claude/ は settings.local.json のみ、5アプリにorient無し | M | root `.claude/`; root CLAUDE.md(4921B); freeform CLAUDE.md(89L)+AGENTS.md(163L) |
| **P1** | Pipeline | KPI経路のサイレントfallback除去(raise化): `_parallel_search`→sequential / ConfigManager→in-memory / 栄養欠損→0kcal | no-fallback ルール違反、ベンチを不可視汚染 | M | `pipeline.py:852,1097,1104,1136`; `config_manager.py:311`; `nutrition_service.py:115` |
| **P1** | VLM/Accuracy | 二段分解prompt + plate/bowl径scale anchor + density/隠れ油の明示推論 + FNDDS世帯計量のグラム変換(hardened gate でA/B) | portion推定が支配的誤差源、二段で-15-20%、persona/CoT/scale が独立効果 | L | prompts v11b(plate anchor無); arXiv 2507.07048, 2602.05078; `usda_metadata.json` portions未活用 |
| **P1** | VLM | OpenRouterに flat `response_format` JSON schema強制 + 単一 `parse_vlm_json` に統一 + `']'→'}'` ヒューリスティック削除 | schema強制で+3-4%精度・parse失敗減、破壊的ヒューリスティックがdish改変 | M | providers内 response_format皆無; `openrouter_provider.py:283`; 4-5系統cleanup |
| **P1** | Eval | metric分解: signed bias + calibration slope + 絶対kcal MAE + macro MAE% + Hungarian dish-matchで weight/density誤差。生payload永続化 | 誤差の所在診断、相殺誤差検出、calibration variantの効果測定 | M | `run_pdca_batch_eval.py:93,124,136,388-397`; PMC13092701; arXiv 2405.15950 |
| **P1** | Resilience | breaker-OUTSIDE-retry に順序変更 + exclude= に permanent error + `httpx.HTTPStatusError` を RETRYABLE 追加 + 共通基底へ集約(Alibaba継承) | retry-over-breakerで早期trip、permanent errorがtrip計上、reranker 5xx非retry | M | `openrouter_provider.py:60-61`; `circuit_breaker.py:92`; `retry.py:44`; `alibaba_provider.py:146` |
| **P1** | Claude Code | PDCAスクリプトを skills(`pdca-bootstrap/run/check`)+ forked `pdca-runner` subagent(summaryのみ返却)+ root `/plan` `/handoff` skill にwrap | 評価substanceは先行だがwiringゼロ、loopを再現可能化 | M | freeform に `.claude/`・`plans/` 無; global project-setup.md が想定 |
| **P1** | Claude Code | hooks追加(PostToolUse `Write|Edit`→ruff+py_compile / SessionStart→bootstrap / Stop→handoff)+ path-scoped rules(`prompts/**` anti-overfit, `scripts/run_pdca_*` backward-compat)+ `.env` deny | 散文ルールは強制されない、決定的hookへ | S | `.claude/settings.json`無; CLAUDE.md散文 py_compile+ruff |
| **P2** | Pipeline | shared `pipeline.vlm_service` state の per-request変異を引数渡しへ変更 | 並行時 config bleed + provenance誤ラベル(P0 config-fidelity の前提) | M | `pipeline.py:378-415,657-667`; `streaming.py:428-463` |
| **P2** | Pipeline | `run_core_pipeline` + `build_api_response` を抽出し /complete と /stream を同一ロジック化 | 4-way複製・override drift・/stream のサイレントunder-count | L | `streaming.py:384,575` vs `pipeline.py:454,276` |
| **P2** | Retrieval | BM25を full description で再構築 + 共有build-hashを両artifactにwrite & load時assert + synonym/調理法正規化 | dense/sparseテキスト面不一致、index date drift(checksum無) | L | `build_bm25_index.py:51`; FAISS 1/19 vs BM25 10/28・12/6; arXiv 2509.22125 |
| **P2** | Retrieval | 融合をpure RRF(低k 20-40) or pure weighted の一方に統一 + source-tier/prepared prior を reranker投入 + per-dish match精度を計測 | RRF項がinert、description-only rerankで生commodityマッチ | M | `hybrid_search.py:582-585,606`; metadata sr_legacy=7793 |
| **P2** | Nutrition | 欠損fdc_id/栄養/weightで raise化 + dish/meal二重合算を単一helperへ + index⇔nutrition_db 整合のstartup assert | サイレント0kcalで不可視MAE deflation、二経路desyncリスク | S | `nutrition_service.py:115,155`; `pipeline.py:622,1097,1104,1136` |
| **P2** | Infra/Cost | embedding を MRL 1024/2048 or float16 で222MB削減(Flat維持)+ reranker 0.6B/v2-m3 A/B + cost に embedding/reranker 加算 | 222MBは4096-dim起因、8B rerankerは+3pt程度、cost KPIがVLM-only | M | `usda_search.py:94`; arXiv 2506.05176; `cost_calculator.py:130` |
| **P3** | Pipeline | density_map/typical_weights を config化 + weight-source provenance を calculation_notes に出力 + use_vlm_cache=false をコード強制 | magic number / fallback がeval provenance外、cache汚染がpolicy-only | S | `query_extraction.py:108-134`; `vlm_cache.py:100`; `run_pdca_batch_eval.py:505` |
| **P3** | Cleanup | dead code削除(`async_processor.py` / DeepInfraService VLM path / legacy hybrid + cola probe / startup_optimizer stub)+ per-query `print(json.dumps)` をflag化 | no-dead-code / no-debug-output ルール違反 | M | `async_processor.py:250`; `deepinfra_service.py:88`; `hybrid_search.py:363,676`; `startup_optimizer.py:102` |
| **P3** | Security/検証 | /admin + 変更endpointに認証 + save時に解決先URL表示・非Local確認ダイアログ + Nutrition5kで11.38%を外部検証 | admin無認証で本番config変更可、SOTA超えの数値は要独立検証 | M | `router.py:106`; `dashboard.html:722-746`; PMC13092701, PMC12655113 |

---

## 7. Claude Code 開発環境 整備プラン

現状: root `.claude/` は `settings.local.json` のみ。freeform アプリに `.claude/` も `plans/` も無い。global `project-setup.md` が前提とする `/plan` `/handoff` skill / hooks が存在しない。

### 3-Layer Documentation
- **Layer 1 (rules, 常時load)**: 各レベルで `CLAUDE.md` を `@AGENTS.md` import + 短い `## Claude Code` の薄wrapper化(重複排除)。root CLAUDE.md を<60行に書き直し、6アプリ(word_query/meal_analysis/barcode/usda_word_query/usda_meal_analysis/freeform)を1行ずつ + port + 「app dir 内で起動」。長いcurl例は各README/per-app CLAUDE.md へ移動。
- **Layer 2 (design SSOT)**: 既存 `docs/PDCA_BEST_PRACTICES_20260224.md` / `PDCA_SESSION_START_CHECKLIST.md` / 本レビュー(`docs/DEEP_REVIEW_20260601.md`)。`docs/architecture.md`(~100行)を追加し本章2のデータフロー図を正典化。
- **Layer 3 (per-session handoff)**: freeform は既に `evals/knowledge/session_bootstrap_latest.md` を実質Layer-3として運用。これを `plans/current.md` として標準化(or マッピングを文書化)。

### Skills(`apps/freeform_usda_meal_analysis_api/.claude/skills/`)
- `pdca-bootstrap`: `` !`python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap` `` の出力 + current_baseline を注入。
- `pdca-run`: `run_pdca_batch_eval` を呼ぶ。`disable-model-invocation: true`(API予算を消費するため)。
- `pdca-check`: run dir を `current_baseline.json` と採用ゲートで比較。
- root `/plan`(current.md読み次タスク1-3提案)/ `/handoff`(Status更新 + Session Log追記)。各 SKILL.md <200行、スクリプトは inline せず参照。

### Subagent(`.claude/agents/pdca-runner.md`)
安価モデル + `memory: project` + 制限tool。50枚evalを実行し summary metrics(mae, p50/p90, high30, latency, cost)+ verdict のみ返却 → 数千行の per-image 生出力を main context外に隔離。失敗パターンを memory に蓄積(`evals/lessons/` と並走)。read-only 調査は built-in Explore agent。

### Hooks(`.claude/settings.json`, commit対象)
- PostToolUse matcher `Write|Edit`: `*.py` に `ruff format` + `python -m py_compile`(CLAUDE.md散文ルールを置換)。
- SessionStart: `pdca_session_bootstrap` 実行 + current baseline 表示。
- Stop: `/handoff` リマインダー。
- `permissions.deny`: `.env`。

### path-scoped rules(`.claude/rules/`)
- `prompts/**`: 「test_foodXX / ground-truth / label値 / 50-set由来のdish-name語彙 を埋め込まない」(anti-overfit)。
- `scripts/run_pdca_*` `scripts/merge_pdca_runs*`: 「CLI backward compatibility を維持」。

### Eval-loop wiring(reproducibility)
- `evals/configs/*.json` で単一OpenRouter provider pin + 明示 `reasoning`/Gemini `thinking_level`(未指定=high → cost膨張)+ `response_format` strict JSON + 安定prompt prefix(imageを末尾)で cache hit。
- 採用ゲートを headless binary eval 化: nightly/CI で `claude -p`(or 素のジョブ)が `use_vlm_cache=false` で50枚走り、failure_count==0 / coverage_complete / paired-CI改善 / latency・cost budget を assert、pass/fail + lesson を `evals/` へ。`--bare` で決定的CI。

### Monorepo conventions
- 編集対象アプリの dir 内で Claude を起動(該当app + root のみload)。`claudeMdExcludes` で他アプリ除外可。
- Claude Code config の DRI を指名、CLAUDE.md/rules を PR レビュー、major model更新後に workaround rule を剪定。`/memory` で実際のload確認。

---

## 8. 次アクション提案(次セッションの具体的初手)

1. **採用ゲートを paired bootstrap 化(P0, M)。** `run_pdca_batch_eval.py` に per-image paired delta + BCa 95% CI(stdlib `random.choices`/`statistics` で~30行)を追加し、`gate_decision` を「paired-delta CI上限<0でのみpromote」へ。`run_pdca_repeated_eval` にコード強制 stability 閾値。これが他全施策の前提。

2. **config-fidelity assert + prod を v11b へ promote(P0, M)。** 各 `/complete` 後に `payload.ai_model_used`/`prompt_file_used`(理想は prompt SHA)を candidate と照合し不一致で row を fail。`/health` に config_drift flag。認証付きで prod Firestore を v11b へ reset/PUT し `?refresh=true` で検証、`evals/lessons/` に記録。

3. **検索の数学バグ修正(P0, S)。** `hybrid_search.py:529,846,999` の `1/(1+d)` を直接 similarity へ、クエリに `faiss.normalize_L2`(or unit-norm assert)。**修正後**に融合weight sweep を hardened gate で再走(現weightは歪んだ目的関数でチューニング済のため)。

4. **Claude Code 基盤 wiring(P0/P1, M)。** lean root CLAUDE.md(`@AGENTS.md` + 6アプリ)+ `.claude/settings.json` hooks(ruff/py_compile, SessionStart bootstrap, Stop handoff)+ PDCA skills 3本 + `pdca-runner` subagent + path-scoped rules。plan mode で着手。

5. **サイレントfallback除去(P1, M)。** `_parallel_search`→sequential、ConfigManager→in-memory(prod)、栄養欠損→0kcal を raise 化。`python -m py_compile` で各変更を検証しつつ機能単位でテスト。

> 注: 1→2→3 は精度A/Bの前提(ゲートが信頼できて初めて prompt/検索の改善を判定可能)。4 は並行可能。5 以降で portion-estimation prompt A/B(P1, L)に着手。
