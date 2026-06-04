## 総評

結論から言うと、**「VLM → 食材/重量JSON → USDA検索/RAG → 栄養集計」という根本設計には賛成**です。2026年時点でも、栄養値をVLMの内部知識だけで直接出させるより、権威DBへ接地する構成の方が妥当です。実際、2025年の DietAI24 も MLLM + RAG + FNDDS で栄養DBに接地する方向を採っており、FNDDSを権威データベースとして使っています。USDA FoodData Central 自体も、Foundation/SR Legacy/FNDDS/Branded など複数データ型を提供する公式の食品成分データ源です。([Nature][1])

ただし、**今の mozu は「単一写真からVLMだけで grams と density を当てる」部分に過度に賭けています**。あなた方の「200–1500 kcal の本命レンジで ~27% MAE、bias なし、grams:density が 50:50」というPDCA結論はかなり信頼できますが、ここから先はプロンプトや一括calibrationではなく、**入力・相互作用・専用portion推定・不確実性伝播**の設計問題です。単眼写真のportion推定は、既知スケールがないと小さいピザが近いのか大きいピザが遠いのか区別できない、という幾何学的な曖昧性を持つため、single-photo-only のまま27%壁を大きく破るのは難しいです。([arXiv][2])

私の賛否を先にまとめると、**frozen-50の無効化、Pro撤回、calibration VOID、v14不採用、self-consistencyは小幅改善、embedding/reranker過剰、実測mozuデータが最終arbiter**という主要結論には概ね賛成です。一方で、**「prompt/calibrationでは動かない」から先の打ち手が狭すぎる**、**v13が認識とUSDA検索を混ぜすぎている**、**評価KPIのNorth Starが README と rubric で矛盾している**、そして**コード上のリリースブロッカーが複数ある**点は強く指摘します。

---

## 1. 根本パイプライン設計レビュー

### 賛成する点

**VLMに総カロリーを直接出させるより、USDAへ接地して per-100g × grams で積み上げる設計は正しい**です。DietAI24 のような近年の研究でも、MLLMの視覚認識をFNDDSなどの標準栄養DBに接地させるRAG設計が有効な方向として示されています。([Nature][1])

特に mozu の用途では、直接VLM推定だけにすると、同じ「fried chicken」「pasta」「salad」でも調理法・油・ソース・店・量で栄養密度が大きく変わるため、説明可能性も再現性も落ちます。USDA FDC/FNDDS/SR Legacy/Foundation を分けて扱える構成は、後で「FNDDS優先」「Foundationは素材用」「Branded/Menuは将来拡張」というポリシーを入れやすいです。USDA FDC は FNDDS を NHANES の What We Eat in America 報告食品の分析用データとして位置付け、FNDDSは2年周期で更新されます。([USDA FoodData Central][3])

### 反対・修正すべき点

現在のパイプラインは、概念的には以下の3つを1つのVLM出力に押し込みすぎています。

1. **何が写っているか**
2. **何グラムか**
3. **USDAのどのレコードに寄せるべきか**

v13 は `search_name` を USDA-style comma naming に強制していますが、これは認識性能と検索性能を混ぜています。VLMが「見えた食品名」ではなく「USDAに刺さりそうな名前」を出すため、評価上は認識が良く見えたり、逆に density がズレたりします。ここは分離すべきです。

推奨する中間表現は、例えばこうです。

```json
{
  "visible_food": "cheeseburger",
  "canonical_food_class": "burger",
  "preparation": ["beef patty", "bun", "cheese", "sauce"],
  "portion": {
    "likely_g": 230,
    "low_g": 180,
    "high_g": 310,
    "visual_basis": ["whole burger", "fits standard bun", "one patty"],
    "scale_confidence": 0.55
  },
  "density_risk": {
    "oil_sauce_hidden": "medium",
    "cheese_or_fat_visible": true
  },
  "retrieval_queries": [
    "cheeseburger with bun and cheese",
    "hamburger, single patty, with cheese",
    "sandwich, burger, cheese"
  ]
}
```

この形なら、**認識評価、portion評価、検索評価、栄養密度評価**を別々に改善できます。

---

## 2. VLMモデル選定レビュー

### あなた方の結論への賛否

**Flashへ戻した判断には賛成**です。添付PDCAでは、Proは frozen-50 では良く見えたが、そのGTが GPT-5-pro 推定だったため「Pro-likeな命名への一致」を測っていた可能性が高く、NutritionVerse-Real の clean COCO recognition では Flash 82.5% > Pro 80.6%、calorieでも頑健優位なし、という整理でした。これはモデル選定としてかなり健全です。

ただし、**“Flashが最適”ではなく、“現時点の実測分布ではProに払う理由がない”**と表現すべきです。高単価アプリでは、モデル名よりも **測定GTでの champion/challenger 運用**が重要です。

### 2026年時点で追加すべき運用ルール

1つ目は、**preview model ID を本番の安定基盤にしない**ことです。Gemini API のリリースノートを見ると、2025〜2026年に preview/旧モデルの停止・置換が継続的に発生しており、2026年6月1日には Gemini 2.0 Flash 系が shutdown、2026年5月19日には `gemini-3.5-flash` GA がリリースされています。([Google AI for Developers][4])
OpenRouter経由でも、実体モデルの変更・リダイレクト・preview廃止に備えて、**model id、provider、prompt hash、response schema version、eval run id**を全レスポンスに焼き込むべきです。

2つ目は、**VLMの勝敗を総MAEだけで決めない**ことです。モデル比較は最低限、次の3層で見るべきです。

* recognition weighted by calorie impact
* portion error by food class
* density/retrieval error by selected USDA record

「Flash/Proの総カロリーMAEが同等」でも、Proが油脂・ソース検出に強い、Flashが主食量に強い、などの差があるなら、将来の ensemble / per-class routing に使えます。今のPDCAは総量の勝敗をよく見ていますが、**モデルの“使い分け可能性”の分析はまだ浅い**です。

3つ目は、**provider-native structured output を使う**ことです。OpenAI は JSON Schema 準拠を保証する Structured Outputs を提供し、Gemini も structured output mode で JSON Schema のサブセットをサポートしています。([OpenAI Developers][5])
今の `VLMService.analyze_image` は raw response をJSONとして読む前提が強く、コードフェンスや余計な文への耐性よりも、そもそもモデル側に schema を渡す構成へ寄せた方が安定します。

---

## 3. プロンプト v13 レビュー

v13 の良い点は、**component map → portioning → density correction**の3-pass設計です。これは、食材漏れ、量、密度の誤差源を意識していて妥当です。visible sauces/garnishes を拾わせる点も良いです。

ただし、v13 には大きな問題が4つあります。

### 問題1: grams の固定レンジが強すぎる

v13 は `main_food.weight_g: 80-400`、extras `5-120` を schema 内に書いています。これはVLMに安全な範囲を与える一方で、**小さい食品・巨大皿・複数個・半分残し・シェア皿を潰します**。v14 が巨大皿には効いたが本命レンジでは効かなかったというPDCAは納得できますが、根本は v13/v14 のどちらかではなく、**単一の likely_g だけを出す設計**です。

改善案は、`weight_g` を単点ではなく **low / likely / high / confidence / visual_basis** にすることです。最終UIでは likely を見せても、内部では分布を持たせるべきです。

### 問題2: USDA命名強制が早すぎる

`USDA NAME QUALITY` で comma naming を要求していますが、これは **VLMの視覚認識を検索器の都合に寄せて歪める**リスクがあります。

変更案は、VLMにはまず自然名・調理属性・見える材料を出させ、検索用クエリは後段の normalizer が作ることです。

```json
"food_identity": {
  "natural_name": "slice of pepperoni pizza",
  "visible_components": ["crust", "cheese", "pepperoni", "tomato sauce"],
  "preparation": ["baked", "cheese-topped"],
  "not_visible_but_possible": ["oil in dough", "extra cheese"]
},
"retrieval_intent": {
  "prefer_database": "FNDDS",
  "candidate_query_hints": ["pizza with pepperoni, regular crust"]
}
```

### 問題3: user_context がプロンプトに入っていない

コードを見る限り、`analyze_meal_from_image(..., user_context)` は受け取っていますが、画像パイプライン内でVLM入力にも検索にも使われていません。これはかなり大きな見落としです。`services.pipeline.py` では `user_context` が `_analyze_meal_once` に渡されるだけで、`analyze_image` 呼び出しには入っていません。

2025年の ACETADA ベンチマークでは、位置情報・時刻などのコンテキストメタデータを入れると、多くのモデルで栄養推定性能が改善し、既存のモバイル栄養パイプラインに低遅延で統合できる可能性が示されています。([arXiv][6])
mozu でも「これはChipotleのbowl」「自炊の鶏胸肉200g」「半分だけ食べた」「皿は直径26cm」などのユーザー情報は、27%壁を破る最重要レバーです。

### 問題4: “reason internally, output likely only” では不確実性が死ぬ

v13 は low/likely/high を内部で考えろと言っていますが、出力は likely だけです。これでは下流で不確実性を使えません。総カロリーのmedian self-consistencyよりも、**ingredient単位の不確実性伝播**の方がプロダクト価値があります。

出力には最低限、次を足すべきです。

```json
"uncertainty": {
  "recognition_alternatives": [
    {"name": "cream sauce", "probability": 0.55},
    {"name": "cheese sauce", "probability": 0.30}
  ],
  "portion_low_g": 120,
  "portion_likely_g": 180,
  "portion_high_g": 260,
  "needs_user_confirmation": true,
  "confirmation_question": "Is this a small, medium, or large serving of pasta?"
}
```

---

## 4. embedding / reranker 構成レビュー

### あなた方の結論への賛否

**Qwen3-Embedding-8B + Qwen3-Reranker-4B はこの用途には過剰、という結論に賛成**です。13,564件の短いUSDA食品名コーパスで、しかもrerankerを使うなら、first-stage embedding は recall@50 が出れば十分です。8B embedding の30秒cold startは、品質問題ではなく製品設計上の失敗です。

ただし、`EMBEDDING_RERANKER_RESEARCH_20260604.md` の「Voyage 3.5-lite + gte-reranker-modernbert-base」をそのまま結論にするのは少し危険です。2026年6月時点の Voyage 公式docsでは `voyage-4-lite` が latency/cost 最適化モデルとして並び、`voyage-3.5-lite` は older models 側に置かれています。`voyage-3.5-lite` はまだ選択肢ですが、今からA/Bするなら **Voyage 4-lite / Voyage 4 / Gemini embedding / small self-hosted model** も入れるべきです。([Voyage AI][7])

### 推奨構成

私なら、検索を次のように分解します。

**Stage 0: deterministic lexical / alias expansion**

* FNDDS description
* SR Legacy description
* cooked/raw flag
* preparation method
* full-fat/low-fat
* sauce/oil/cheese/fried modifiers
* common synonyms
* kcal_per_100g bucket
* portion metadata

この時点で、BM25/SQLite FTSだけでもかなり当たるはずです。

**Stage 1: lightweight embedding recall**

候補は以下をA/Bします。

* Voyage `voyage-4-lite` or `voyage-3.5-lite`
* Gemini embedding
* self-host small model: bge/e5/EmbeddingGemma/Qwen3-0.6B系

Gemini embedding は `gemini-embedding-001` で 3072次元が基本で、次元を縮める場合は正規化に注意が必要です。Google docs では、`gemini-embedding-001` で 3072未満の `output_dimensionality` を使う場合は manual normalization が必要とされています。([Google AI for Developers][8])

**Stage 2: rerank**

`gte-reranker-modernbert-base` は有力です。Hugging Face のモデルカードでは 149M の English text reranker とされ、MTEB/BEIR/LoCo/CoIRなどで競争力があると説明されています。([Hugging Face][9])
Voyage reranker のような hosted reranker も、query + candidate documents をsemantic relevanceで再順位付けする標準形なので、運用負荷を下げる選択肢です。([Voyage AI][10])

### 重要な実装修正

`services.pipeline.py` の `_parallel_search` では、`effective_reranker_top_n` を取得しているのに、`batch_rerank_candidates(..., top_k=1)` とハードコードされています。つまり admin/config で `reranker_top_n` を変えても、2-phase path では効きません。これはA/B評価の信頼性に関わります。

また、現状のreranker documentが USDA description だけなら弱いです。rerankerには次のような enriched document を渡すべきです。

```text
description: "Pizza, pepperoni, regular crust"
source: survey/FNDDS
kcal_per_100g: 285
protein/fat/carbs per100g: ...
common_portion: 1 slice 107g
preparation: baked, regular crust, cheese, pepperoni
raw_cooked: cooked/prepared
```

USDA検索の失敗は「間違った名前」よりも「間違った密度」を生むので、retrieval eval も Hit@1 だけでなく **kcal_per_100g error** を見るべきです。

---

## 5. ~27% MAE の壁を破る手法

ここが最重要です。私は、**single-photo + VLM-only + no user interaction では、27% MAEを大きく下げるのは難しい**と見ます。理由は、portion推定のスケール曖昧性が構造的だからです。2026年の portion estimation survey でも、単眼画像では絶対スケールと形状を復元する必要があり、Depth sensing / Multi-view stereo / Model-based approaches などが議論されています。([arXiv][2])

Nutrition5k が強い評価データなのも、単なる1枚画像ではなく、4方向のside-angle videos、overhead RGB-D、ingredient mass、total mass/calories、PFCを持っているからです。([GitHub][11])
つまり、研究データセットが示しているのは「正確にやるには追加視点・depth・重量GTが効く」ということです。

### 優先度A: ユーザー入力を1〜2タップで入れる

最も現実的で効果が大きいのは、**VLMが不確実な時だけ確認するUI**です。

例:

* “Is this a small / regular / large serving?”
* “How many slices did you eat?”
* “Was this restaurant food or homemade?”
* “Did you eat all of it?”
* “Add a common object or choose plate size?”

これはレイテンシもコストもほぼ増やさず、スケール曖昧性を直接潰します。ACETADAの文脈メタデータ改善の示唆とも整合します。([arXiv][6])

### 優先度A: scale reference をプロダクトに組み込む

「任意でクレカを置いてください」はUXが悪いですが、以下なら現実的です。

* 皿サイズプリセット: small / regular / large plate
* 手・フォーク・箸・缶・スマホを参照物として検出
* iPhone Pro等ではLiDAR/depthを任意利用
* 同じユーザーの皿サイズをプロフィール化
* restaurant/menu item の標準量を使う

surveyでも、fiducial marker、RGB-D、LiDAR、multi-view はスケール問題の解決策として議論されていますが、ユーザー負担やデバイス制約があります。([arXiv][2])
mozuの高単価アプリなら、全ユーザーに強制ではなく、**高信頼モード**として提供する価値があります。

### 優先度A: multi-photo / before-after / leftover

1枚追加で「横から」撮らせるだけでも厚み推定が改善します。before/afterで摂取量も分かります。毎食必須にすると継続率が落ちるので、以下の条件でだけ出すべきです。

* prediction interval が広い
* calorie-dense item がある
* pasta/rice/bowl/salad/curry など体積が不明
* ユーザーが高精度モードをON

### 優先度B: 専用 portion model をVLMの後ろに置く

VLMに grams を直接出させるのではなく、

1. VLMで食品クラス・部位・皿・容器を検出
2. segmentation / depth prior / plate geometry で面積・高さを推定
3. food classごとの密度分布を掛ける
4. VLMは例外・属性補正に使う

という構成にすべきです。

これはエンドツーエンド calorie regression より説明可能で、今のUSDA RAGとも相性が良いです。

### 優先度B: densityをUSDA 1点決めにしない

今は ingredientごとに top1 USDA match を決めていますが、density誤差が半分を占めるなら、top1固定はもったいないです。

候補ごとに以下を持たせます。

```json
[
  {"fdc_id": 123, "desc": "pasta with cream sauce", "kcal_per_100g": 210, "p": 0.45},
  {"fdc_id": 456, "desc": "pasta with tomato sauce", "kcal_per_100g": 150, "p": 0.35},
  {"fdc_id": 789, "desc": "pasta with cheese sauce", "kcal_per_100g": 240, "p": 0.20}
]
```

最終的には expected calories と prediction interval を返し、UIでは「約620 kcal、範囲520–780 kcal」のように出す。高単価アプリでは、**単点の自信過剰**より、**不確実性込みの誠実な推定**の方が信頼につながります。

### 優先度C: self-consistency の実装改善

K=3 medianで~2pt改善という結論には賛成ですが、今の実装は「K回フルパイプラインを回して、総カロリー中央値の1サンプルを採用」です。これは自己整合性はありますが、VLMのK出力から得られる情報を捨てています。

改善案:

* VLMをK回だけ走らせる
* すべての候補食材を正規化・クラスタリング
* majority / weighted union で food set を作る
* portionは ingredient単位で median
* retrievalは unique query に対して1回だけ
* density候補はweighted mixture

これなら、K倍レイテンシを抑えつつ、総カロリーmedianより構造的な改善が狙えます。

---

## 6. 評価KPI設計レビュー

### 良い点

実測GTを重視し、paired BCa bootstrap CIでpromote判定する設計は良いです。frozen-50を「GPT-5-pro一致度」と見直した判断も正しいです。公開データセットだけでなく実mozu分布が最終arbiter、という結論も賛成です。

### 重大な矛盾

READMEでは「KPIの主役 = 総カロリーMAE」とあります。一方、`05_kpis_and_eval/EVAL_RUBRIC.md` では「Final KPI is USER CONVICTION, not total calorie accuracy」と書かれています。これは意思決定上危険です。

整理すべきです。

* **North Star**: user retained trust / conviction / continued logging
* **Safety release gate**: calorie MAE, p90 error, high-error-rate
* **Debug metrics**: recognition, portion, retrieval, density
* **Ops gate**: latency p50/p95/p99, cost, timeout rate

総カロリーだけを最適化すると、「食品は間違っているが偶然合計は近い」モデルが勝ちます。高単価アプリではこれは悪い体験です。

### 追加すべきKPI

最低限、次を入れてください。

| 領域                | KPI                                                                                       |
| ----------------- | ----------------------------------------------------------------------------------------- |
| 総カロリー             | MAE%, MdAPE, p50/p90/p95 absolute kcal error, within ±20% / ±30%                          |
| bias              | signed mean %, calibration slope, calorie-band別bias                                       |
| recognition       | item recall/F1 だけでなく calorie-weighted recall                                              |
| portion           | grams MAE, log ratio error, food-class別 error                                             |
| density/retrieval | selected USDA kcal/100g error, Hit@K acceptable FDC, raw/cooked/fried/full-fat confusions |
| uncertainty       | prediction interval coverage, confidence calibration                                      |
| UX                | user correction rate, edit distance, confirmation acceptance, trust rating                |
| ops               | p50/p95/p99 latency, cold start rate, cost, cache hit rate                                |
| robustness        | lighting, angle, occlusion, bowl/plate, homemade/restaurant, cuisine strata               |

特に `sample_eval_summary_NVReal.md` の `dish_token_f1=0.12` のような値は、clean COCO recognition と矛盾して見えるため、token F1は低優先にし、**COCO/ingredient ontologyベースのrecognition**と**calorie-weighted recognition**を主にすべきです。

---

## 7. PDCA結論の誤り・見落とし

### 強く賛成するPDCA結論

* **frozen-50 のGTは実測でないため、実精度評価に使えない**
  賛成です。これは重大な methodological bug で、撤回できているのは良いです。

* **Pro採用撤回・Flash復帰**
  賛成です。ただし「Flashが恒久最適」ではなく「今の実測GTではPro premiumが正当化されない」です。

* **calibration VOID**
  賛成です。bias符号が分布で反転するなら、単一affine補正は危険です。

* **v14 portion scaling 不採用**
  賛成です。巨大皿tailだけ改善して本命レンジが動かないなら、採用理由は弱いです。

* **self-consistency はrobustだが小幅**
  賛成です。ただし実装は「median sample採用」から「structured consensus」へ進化させる余地があります。

* **embedding/rerankerは過剰**
  賛成です。30秒embeddingは製品上の最優先修正です。

### 見落とし・修正すべき結論

**1. “prompt/calibrationでは動かない” は正しいが、“打ち手がない” ではない。**
動かすべきは prompt ではなく、user_context、scale reference、multi-photo、portion model、density mixture、uncertainty UIです。

**2. “recognition 82%なら十分” ではない。**
カロリー影響の大きい油・チーズ・ドレッシング・ナッツ・ソース・揚げ衣を1つ落とすだけで総カロリーが大きくズレます。item recall ではなく calorie-weighted recall が必要です。

**3. USDA命名強制はPDCAで過小評価されています。**
検索ヒット率を上げる一方で、VLMの自然な視覚認識を歪めます。認識名と検索クエリは分けるべきです。

**4. density誤差の扱いが弱い。**
gramsとdensityが50:50なら、検索top1を確定する現設計は不十分です。topK density mixture と uncertainty propagation が必要です。

**5. “実mozuデータが最終arbiter” は正しいが、収集設計が不足しています。**
ただ実測データを集めるだけでなく、能動学習が必要です。高不確実・高カロリー・高頻度・モデル間不一致のサンプルから優先的に実測/ユーザー補正GTを集めるべきです。

---

## 8. コード上の重大指摘

添付コードを読む限り、設計以前に直すべき実装問題があります。

### リリースブロッカー級

`services.vlm_service.py` で、`model_id is None` のとき `settings.VLM_MODEL_ID` を参照していますが、`config.settings.py` 側は `DEFAULT_VLM_MODEL_ID` です。添付状態のままだと、`MealAnalysisPipeline(vlm_model_id=None)` で初期化時に落ちる可能性があります。`services.vlm_service.py:81-85`, `config.settings.py:64-66`

また、`VLMService.__init__` が self-verification prompt を常に eager load していますが、ZIP内には該当の `freeform_verify_pass_20260602.txt` が見当たりません。self-verification OFFでも初期化で落ちる設計になり得ます。`services.vlm_service.py:101-104`

### 本番運用リスク

`_analyze_meal_once` で `self.vlm_service.prompt` と `self.vlm_service.model_id/provider` をリクエストごとに mutate しています。これは self-consistency 並列化だけでなく、通常の複数ユーザー同時リクエストでも race condition になります。`services.pipeline.py:517-560`

解決策は、VLM call を stateless にして、`prompt`, `model_id`, `provider`, `schema` を request-local config として渡すことです。

### user_context が死んでいる

`user_context` は `analyze_meal_from_image` に存在しますが、画像VLM解析に渡されていません。これは27%壁を破る最大レバーを捨てています。`services.pipeline.py:343-351`, `420-424`

### `reranker_top_n` が効いていない

`_parallel_search` では `effective_reranker_top_n` を計算しているのに、`batch_rerank_candidates(..., top_k=1)` がハードコードです。A/BやtopK uncertainty評価を阻害します。`services.pipeline.py:924-979`

### match_rate が実質dish non-empty rate

`match_rate_percent` は `len(api_dishes)` を分母に、ingredientが1つ以上あるdish数を分子にしています。これは ingredient match rate ではありません。ユーザーや評価ログに出すと誤解を招きます。`services.pipeline.py:815-820`

### calibration コードのコメントがPDCA結論と矛盾

`core.calorie_calibration.py` のdocstringは「systematically under-estimate」「MAE 18.7%→15.0%」など、現在の VOID 結論と矛盾しています。さらに有効化時に calorie factor で `weight_g` までスケールしていますが、これは意味論的に危険です。カロリー補正は「補正後total」として別フィールドに出すべきで、見た目の重量を改変すべきではありません。`core.calorie_calibration.py:1-9`, `services.pipeline.py:1287-1328`

### group_queries_by_dish が空query dishに弱い

`group_queries_by_dish` は queries が空なら `[]` を返し、`_build_enriched_dishes` は `grouped_queries[dish_index]` を参照します。dishはあるがqueryが空、または一部dishだけqueryなし、という不正/境界出力で落ちます。`services.query_extraction.py:189-202`, `services.pipeline.py:1148-1178`

---

## 最終提案: 次の2週間でやるべき順番

**最優先は、精度実験ではなく本番安全性と測定可能性の修正**です。

1. `settings.VLM_MODEL_ID` bug、verify prompt eager load、prompt path不整合、mutable VLMService、`reranker_top_n`無効、match_rate誤定義を修正する。
2. v13を、自然認識・portion分布・retrieval queryを分離した v15 schema に置き換える。provider-native structured output を使う。
3. user_context をVLM promptとretrieval normalizerに入れる。皿サイズ・食べ残し・店名・メニュー名・大中小をUIで取れるようにする。
4. retrievalを軽量化する。まずは現行Qwen3-8Bを捨て、BM25/alias + lightweight embedding + small rerankerで A/B。評価は Hit@1 だけでなく kcal/100g error と acceptable FDC set。
5. self-consistencyは現状K=3 medianのまま本番defaultにはせず、structured consensus版を別実装する。
6. KPIを「North Star = user trust」「release gate = measured calorie safety」「debug = recognition/portion/retrieval」に整理する。
7. mozu実測データ収集は、ランダムではなく uncertainty / high-calorie / model-disagreement priority で集める。

全体として、あなた方のPDCAはかなり健全です。特に frozen-50 の撤回、Pro撤回、calibration VOID は正しい判断です。最大の見落としは、**27%の壁を“モデル/プロンプト問題”として見すぎていて、“入力情報量と不確実性UIの問題”として設計し切れていないこと**です。単一写真で魔法のように grams を当てるより、ユーザーから1ビットでもスケール情報を取る方が、次の精度改善には効く可能性が高いです。

[1]: https://www.nature.com/articles/s43856-025-01159-0 "DietAI24 as a framework for comprehensive nutrition estimation using multimodal large language models | Communications Medicine"
[2]: https://arxiv.org/html/2602.05078v1 "Food Portion Estimation: From Pixels to Calories"
[3]: https://fdc.nal.usda.gov/ "USDA FoodData Central"
[4]: https://ai.google.dev/gemini-api/docs/changelog "Release notes  |  Gemini API  |  Google AI for Developers"
[5]: https://developers.openai.com/api/docs/guides/structured-outputs "Structured model outputs | OpenAI API"
[6]: https://arxiv.org/html/2507.07048v1 "Evaluating Large Multimodal Models for Nutrition Analysis: A Benchmark Enriched with Contextual Metadata"
[7]: https://docs.voyageai.com/docs/embeddings "Text Embeddings"
[8]: https://ai.google.dev/gemini-api/docs/embeddings "Embeddings  |  Gemini API  |  Google AI for Developers"
[9]: https://huggingface.co/Alibaba-NLP/gte-reranker-modernbert-base "Alibaba-NLP/gte-reranker-modernbert-base · Hugging Face"
[10]: https://docs.voyageai.com/docs/reranker "Rerankers"
[11]: https://github.com/google-research-datasets/Nutrition5k "GitHub - google-research-datasets/Nutrition5k: Detailed visual + nutritional data for over 5,000 plates of food. · GitHub"
