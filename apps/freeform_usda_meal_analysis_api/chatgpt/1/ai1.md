## 総評

添付一式を読む限り、mozu の現在の方向性、つまり **「VLMで可視食材と分量を構造化 → USDA/FNDDS系DBにgrounding → 栄養を積み上げる」** という大枠は、2026年時点でも妥当です。むしろ、VLMにカロリーやPFCを直接“暗算”させるより堅いです。2025年の DietAI24 も、MLLM単体の栄養値生成ではなく、FNDDSなどの標準栄養DBにRAGでgroundする設計を採っており、MLLMの内部知識だけで栄養値を出す問題を明確に避けています。([Nature][1])

ただし、現在の設計は **「単一写真から点推定を返す一発パイプライン」** として作り込みすぎています。ここが最大の構造的限界です。単一RGB画像から重量・体積を当てる問題は、既知スケールや深度がない限り本質的に不良設定です。2D画像では奥行きと絶対スケールが失われるため、小さい料理が近くにあるのか、大きい料理が遠くにあるのかを幾何的に区別できません。([arXiv][2]) したがって、~27% MAEの壁を破る主戦場は、promptやglobal calibrationではなく、**不確実性表現、ユーザー補助入力、scale/depth/multiview、実測データによる条件付き補正** です。

私の結論は次です。

**強く賛成**: frozen-50を実測GT扱いしない、pro採用撤回、flash cost-rational、v14不採用、global calibration VOID、measured GT重視、embedding 8Bのlatency問題認識。

**部分的に反対**: 「promptでは動かない」「calibration不可」「self-consistencyが唯一のlever」という言い切りは強すぎます。正しくは、**今の点推定v13 promptとglobal calibrationでは動かなかった** です。schema変更、uncertainty、composite-vs-component検索、ユーザー確認、per-food conditional calibration はまだ大きな余地があります。

**最重要修正**: mozu は「一発で正解するAI」ではなく、**“写真だけなら範囲推定、必要時に1問だけ聞く、補助情報があれば20%未満を狙う”推定システム** に変えるべきです。

---

## (1) 根本のパイプライン設計

### 評価: 大枠は賛成。ただし one-shot 点推定から脱却すべき

`VLM → query extraction → USDA hybrid search/rerank → per100g scaling → total` は、説明可能性・デバッグ性・DB更新性の面で良い設計です。FoodData Central自体もFNDDS、Foundation Foods、SR Legacy、Branded Foodsなど複数のデータ型を含み、FNDDSはNHANES dietary surveyに接続された実用的な食品・分量文脈を持ちます。([USDA FoodData Central][3]) SR Legacyは最終リリースで更新されない一方、FNDDSは2年周期で更新されるため、USDA内でもsource tieringを明示すべきです。([USDA FoodData Central][4])

ただし、現行は **VLMが `search_name` と `weight_g` を同時に決め、そのまま検索・計算へ流す** 設計です。これは以下の3つを混同しています。

1. 画像上の視覚認識: “what is visibly there?”
2. USDA検索用の正規化: “what should we query?”
3. 重量推定: “how many grams?”

この3つは分離した方がよいです。特に `search_name` を最初からUSDA風に出させると、VLMが「見えたもの」ではなく「DBにありそうな名前」を出す方向に寄ります。これは検索には効く一方、recognition評価やユーザー納得感、誤認検出を濁します。

### 推奨アーキテクチャ

次のような二段または三段構成に変えるべきです。

```json
{
  "visual_items": [
    {
      "visual_label": "burger with bun and cheese",
      "role": "composite_dish | component | sauce | garnish",
      "visible_evidence": ["bun", "patty", "cheese"],
      "portion": {
        "likely_g": 260,
        "low_g": 190,
        "high_g": 360,
        "basis": "plate_fraction + thickness_guess",
        "uncertainty_reason": "no scale reference"
      },
      "search_queries": [
        "cheeseburger, regular, on bun",
        "double cheeseburger, on bun"
      ],
      "confidence": {
        "recognition": 0.86,
        "portion": 0.45,
        "db_match": 0.70
      },
      "needs_user_check": "Is this a single or double patty burger?"
    }
  ]
}
```

その後に、

* **dish-level composite record検索**: FNDDSの「as consumed」レコードを優先候補にする。
* **component-level検索**: 肉、パン、チーズ、ソースを分解して積み上げる。
* **selector/critic**: compositeとcomponentのどちらが妥当かを、料理タイプ・可視分解可能性・kcal/g plausibilityで選ぶ。
* **Monte Carlo集計**: `low/likely/high_g` と top-k DB候補を使って calorie/PFC の分布を出す。
* **UI clarification**: 不確実性が総カロリーに大きく効く1点だけ聞く。

現行の `sample_pipeline_output_hamburger.json` はこの問題をよく示しています。総カロリーは775.85 kcalに対して932 kcalで20%誤差に収まっていますが、PFCは fat 30g GTに対して63g、carbs 87g GTに対して31gと大きく崩れています。つまり **総カロリーだけが相殺で近い** 可能性があります。高単価トラッカーなら、これはpromoteしてはいけません。

---

## (2) VLMモデル選定

### 評価: flash復帰には賛成。ただし preview固定は危険

あなた方のPDCAで、proが独立実測GTに対して頑健な優位を示さず、recognitionでもflash優位が出たなら、**flashをデフォルトに戻す判断は正しい** です。外部の汎用VLMリーダーボードより、自分たちの実測GT・本番分布A/Bが強いです。

ただし、`openrouter:google/gemini-3-flash-preview` を本番の固定デフォルトにするのは危険です。GoogleのGeminiモデル一覧では、Gemini 3 FlashはPreview、Gemini 3.5 FlashはStableとして掲載されており、同じページで本番アプリはstable modelをpinするのが望ましいとされています。([Google AI for Developers][5]) したがって、今の結論は「flash系が妥当」であって、**特定preview IDを長期本番SSOTにする** ことではありません。

### 推奨

VLMは「単一最強モデル」ではなく、**tiered routing** にしてください。

* **通常**: stableなFlash系、temperature 0.3、structured output、K=1。
* **高不確実性ケース**: K=3 median、またはPro/高性能VLMを1回だけcriticとして使う。
* **失敗しやすい料理**: composite dish、ソース多め、盛り付けが重なる、写真角度が悪い、scaleなし大皿。
* **月次A/B**: current default vs candidateを、固定のreal measured holdoutで比較。

Gemini 3.1 Pro Previewは画像入力やstructured output、thinkingを持つ高機能モデルですが、公式説明上もagentic workflowsやcomplex tasks向けの色が強く、食事写真のportion推定でFlashより良いとは外部情報だけでは言えません。([Google AI for Developers][6]) あなた方の実測A/Bを優先するのが正しいです。

---

## (3) prompt v13

### 評価: v13維持には賛成。ただし schema が古い

v13の良い点は、JSON限定、visible components重視、ソース・油・ドレッシングを別扱い、USDA検索に寄せた命名、moderate correctionです。v14で本命レンジが動かなかったなら、v13維持は妥当です。

ただし、v13の最大の問題は **prompt文面ではなく出力schema** です。

### 問題点

第一に、`main_food.weight_g: 80-400` の下限が強すぎます。大皿過小だけでなく、小さいmain、半分食べた料理、少量の高密度食品で過大推定を誘発します。v14は大皿上限緩和に寄っていますが、**小皿・軽食・partial consumptionの下限問題** は別に検証すべきです。

第二に、`main_food + extras` という構造が mixed dish に弱いです。FNDDSには「as consumed」の混合料理レコードがあります。ハンバーガー、パスタ、サラダ、ピザ、burrito、stewなどは、無理にcomponent分解するとDB密度が崩れる場合があります。

第三に、USDA風 `search_name` をVLMに直接出させるため、視覚認識とDB検索が絡まっています。これは、recognition judgeやユーザー表示には不利です。

第四に、VLMは内部で low/likely/high を考えるのに、出力は likely の点推定だけです。下流が分散を捨てているので、~27%の“純粋分散”に対して戦えません。

### v13.5としての改善案

v14のように重量アンカーだけをいじるのではなく、以下をschemaに入れるべきです。

```json
{
  "dish_name": "string",
  "items": [
    {
      "visual_label": "string",
      "display_name": "string",
      "role": "composite | component | sauce | garnish | beverage",
      "usda_query_candidates": ["string", "string"],
      "weight_g": {
        "low": 120,
        "likely": 180,
        "high": 260
      },
      "portion_basis": "plate_fraction | count | package | user_context | unknown",
      "prep_form": "raw | cooked | fried | grilled | creamy | unknown",
      "visible_oil_sauce": "none | visible | likely_hidden | unknown",
      "confidence": {
        "recognition": 0.0,
        "portion": 0.0
      },
      "clarification_question": null
    }
  ]
}
```

特に `clarification_question` は強力です。例えば「これはダブルパティですか？」「食べたのは全部ですか？」「皿の直径は約何cmですか？」の1問で、K=3 self-consistencyより大きく効くケースがあります。

また、Google/Gemini系はstructured outputsをサポートしているため、プロンプトだけでなくAPI側のJSON Schema/Pydantic validationを使うべきです。GoogleのGemini 3.1系モデルページでもstructured outputsは明示されています。([Google AI for Developers][6])

---

## (4) embedding / reranker構成

### 評価: 8B embedder過剰という結論に賛成。ただし移行先はA/Bで決めるべき

13,564件のUSDA小コーパス、短い食品名クエリ、さらにcross-encoder rerankerあり、という条件では、Qwen3-Embedding-8B dim4096はほぼ確実に過剰です。Qwen3公式情報でも、Embeddingは0.6B/1024次元、4B/2560次元、8B/4096次元の階層があり、rerankerも0.6B/4B/8Bが用意されています。([Qwen][7]) この用途で8B serverless cold startを毎回踏むのは設計負債です。

一方で、`EMBEDDING_RERANKER_RESEARCH_20260604.md` の「Voyage + gte-reranker-modernbert-baseへ決め打ち」は少し早いです。Voyageは現行docs上では `voyage-4-lite` などの新系列があり、1024 default、256/512/2048次元などを選べます。([Voyage AI][8]) Gemini Embedding 2も2026年4月GAで、テキスト・画像・音声・動画・PDFを同一空間に埋め込める3072次元上限のモデルとして出ています。([Google Cloud Documentation][9]) したがって、2026年時点では「Voyage 3.5-lite一択」ではなく、**小さく速い候補をretrieval gold setで比較** が正しいです。

### 推奨構成

本番候補は以下です。

| 層         | 推奨                                                                          | 理由                                |
| --------- | --------------------------------------------------------------------------- | --------------------------------- |
| Lexical   | BM25 + synonym/alias辞書                                                      | USDA/FNDDSは名称・調理法・raw/cookedが効くため |
| Dense     | Qwen3-Embedding-0.6B / Voyage-4-lite / Gemini Embedding 2 / EmbeddingGemma系 | 8B不要。dim 256-1024で十分な可能性          |
| Fusion    | まずは単純RRFまたはweighted RRF                                                     | 現行はRRFと正規化scoreが混在しややopaque       |
| Rerank    | 小型cross-encoderを常時warm                                                      | top50短文ペアなら4Bは過剰                  |
| Guardrail | kcal/g・raw/cooked・source tier critic                                        | 検索scoreだけで決めない                    |

最初にやるべきはモデル変更ではなく、**retrieval gold set作成** です。500〜1000件でよいので、実際のVLM出力クエリに対して、許容FDC候補、NG候補、raw/cooked違い、acceptable density rangeを人手で付けます。評価指標は、Hit@1だけでなく、`kcal_per_100g absolute error`、`source_type correct`、`raw/cooked form correct`、`end-to-end calorie delta` を見るべきです。

### コード上の注意

同梱コードには、検索系でいくつか実装修正が必要です。

* `services.food_search_service.py` の list-query branch では、`search_hybrid_with_reranker()` が dict `{results, debug_info}` を返すのに、呼び出し側がlistとしてiterateしている箇所があります。未使用経路だとしても危険です。
* `services.hybrid_search.py` はBM25/vector/RRF/score正規化の関数が重複しており、融合ロジックが複数系統に見えます。A/B時に「どのfusionを評価したか」が曖昧になります。
* USDA corpusが13.5kしかないので、neural retrievalだけでなく、**food alias table**、`raw↔cooked`、`with/without sauce`、`regular/low-fat/full-fat` の正規化辞書がかなり効くはずです。

---

## (5) ~27% MAEの壁を破る手法

### 評価: “single-photoのみ”では壁はかなり本質的

あなた方の「本命レンジでbiasほぼゼロ、grams:densityが約50:50」という分解は、かなり納得できます。ただし、そこから「残るleverはself-consistencyか実データだけ」と絞るのは狭いです。

単一写真の重量推定が難しいことは、最新のfood portion estimation整理でも明確です。絶対スケールと奥行きがないと、同じ2D投影から無数の3D体積があり得ます。([arXiv][2]) Nutrition5kが、回転side-angle videos、overhead RGB-D、per-ingredient mass、total calories、macrosを含めているのも、単なるRGB一枚ではportion GTを作る・学習するのが難しいからです。([GitHub][10])

### 現実的な改善レバー

**P0: ユーザー補助入力を1問だけ入れる**

最も費用対効果が高いです。毎回聞くのではなく、uncertaintyが高い時だけでよいです。

例:

* 「食べた量は全部・半分・少し残した？」
* 「これはシングル/ダブルパティ？」
* 「皿の直径はだいたい何cm？」
* 「市販品・レストラン名・メニュー名はある？」
* 「ドレッシングは別添えを全部かけた？」

2026年のDietDeltaも、単一pre-consumption画像だけでは実際に食べた量を決められず、before/afterペアで消費量を推定する方向を提示しています。([arXiv][11]) 高単価トラッカーなら、before/afterや「食べ残し」入力は検討価値があります。

**P1: scale/depth/multiview**

DepthCalorieCamのようなRGB-D/volumeベース手法は、少数カテゴリながら2D size-basedより大きく誤差を下げた報告があります。([mm.cs.uec.ac.jp][12]) ただしユーザー負担とデバイス依存が増えるため、常時必須ではなく「高精度モード」にするのが現実的です。

推奨UIは、

* 通常: 1枚写真
* 不確実性高: 「もう1枚、真上から撮ってください」
* 高精度モード: カード/箸/フォーク/皿サイズをscale referenceにする
* iPhone対応: depth/ARKit/LiDARが取れる端末では自動利用

です。

**P1: composite-vs-component selector**

ハンバーガー、ピザ、burrito、pasta、stew、saladは、FNDDS composite recordをまず当てるべきです。component分解は、可視で独立している時だけにします。これでdensity error側が下がる可能性があります。

**P1: uncertainty-aware Monte Carlo**

`weight_g`点推定ではなく、`low/likely/high`、DB top-k、food density priorsを持ち、総カロリー分布を出してください。ユーザーには「推定 620 kcal、範囲 480–820 kcal」と出し、内部KPIではinterval coverageも測ります。biasがないなら、点推定より不確実性管理が重要です。

**P2: in-domain measured data + conditional calibration**

global affine calibration VOIDには賛成です。しかし、calibration一般をVOIDにしてはいけません。必要なのは、

* food category別
* composite/component別
* camera angle別
* plate-size known/unknown別
* `portion_confidence`別
* `kcal/g density`別

の階層/条件付き補正です。20〜50枚は方向性確認にはよいですが、最終判断には小さいです。少なくともblind holdoutを分け、100〜300枚へ増やす設計にしたいです。

**P2: direct VLM calorieを“主系”ではなくfeatureにする**

VLMに直接カロリーを出させるのは主系にすべきではありません。ただし、`USDA積み上げ total`、`VLM direct total`、`dish_type`、`weight_total`、`density_prior`、`confidence` を特徴量にした小さなregressor/stackerは試す価値があります。RAG/DB groundingを維持したまま、相殺誤差を検出できます。

---

## (6) 評価KPI設計

### 評価: 測定GT重視とpaired CIは良い。ただしKPI哲学に矛盾がある

READMEでは「KPIの主役 = total calorie MAE」とあります。一方、`05_kpis_and_eval/EVAL_RUBRIC.md` では「最終KPIは総カロリー精度ではなく USER CONVICTION」と書かれています。この2つは、そのままだと矛盾します。

高単価カロリートラッカーなら、私は次の階層にします。

1. **Scientific primary**: 実測GTに対する total calorie MAE / MdAPE / high-error-rate。
2. **Product primary**: ユーザーが修正後にログした値の有用性、継続率、修正負荷。
3. **Safety/quality guards**: recognition recall/precision、DB match、portion bands、PFC error、interval coverage。
4. **UX trust**: user conviction。これは重要だが、測定GTの代替ではない。

`user conviction` は「間違っているのに自信満々」な出力を防ぐguardrailとして有用です。ただし、judgeが人間goldenで検証されるまではpromote gateにしてはいけません。あなた方のrubricにも「未検証judgeはadvisory」とあるので、この姿勢は正しいです。

### 追加すべきKPI

* **PFC MAE / macro calorie share error**: sample hamburgerのように総カロリーが近くてもPFCが崩れるケースを落とす。
* **kcal/g density error**: DB matchの良し悪しを calorieに直結させる。
* **portion interval coverage**: 80%区間がGTを含むか。
* **one-question improvement**: ユーザーに1問聞いた後、MAEが何pt下がるか。
* **selective abstention KPI**: 「不確実なので確認が必要」と出した時のprecision。
* **category/bucket別MAE**: burger, salad, pasta, mixed dish, beverage, sauce-heavy, small snack, large plate。
* **tail metrics**: p90/p95 absolute % error、>30% error rate、>50% error rate。
* **retrieval-only benchmark**: VLM出力クエリ→FDC/FNDDS goldのHit@1/Recall@10/Recall@50。

### 評価セット運用

Nutrition5kは、5,006 plates、side-angle videos、overhead RGB-D、per-ingredient mass、total mass/calories、macrosを含む優れた実測データですが、Google cafeteria/scan rigという分布差があります。([GitHub][10]) したがって、あなた方の「Nutrition5kを唯一の本番評価にしない」は正しいです。

NutritionVerse-RealのID join事故を見つけたのも重要です。今後は外部datasetごとに、metadata joinのvisual spot-checkを正式チェックリスト化してください。

---

## (7) PDCA結論の誤り・見落とし

### 賛成する結論

* **frozen-50のLLM推定GTを実測扱いしない**: 完全に賛成。
* **pro撤回・flash復帰**: 現状データでは賛成。
* **v14不採用**: 本命レンジに効いていないなら賛成。
* **global calibration VOID**: 賛成。
* **self-consistency K=3 medianはrobustだが小さい**: 賛成。
* **embedding 8B serverless cold startが最大ボトルネック**: 賛成。
* **最終arbiterは実mozu measured data**: 強く賛成。

### 修正すべき結論

**1. 「prompt-tuningでは動かない」は言い過ぎ**

v14のportion anchor変更が効かなかった、という結論は正しいです。しかし、schemaを変えて不確実性・composite mode・visual_label/search_query分離を入れるのは、単なるprompt tuningではなくpipeline設計変更です。ここはまだ試す価値があります。

**2. 「calibrationは不可」はglobal calibrationに限るべき**

bias符号がdatasetで反転するならglobal補正は危険です。ただし、real mozu measured dataで、food type・confidence・density・angle別のconditional calibrationを行う余地はあります。

**3. 「recognitionは十分」は危険**

NVReal COCOでrecall ~82%は悪くないですが、CVPR 2025のFoodNExTDB研究でも、現在のVLMは単一食品では高い一方、調理法や見た目が似た食品の細粒度識別が課題とされています。([CVF Open Access][13]) カロリー/PFCでは、grilled/fried、regular/low-fat、cream/oilの違いが大きいので、recognitionを“ほぼ解決”扱いしない方がよいです。

**4. 「self-consistencyが唯一のlever」は狭い**

正確には「入力情報を増やさない場合のrobust lever」です。scale、depth、before/after、ユーザー1問、menu/package/barcode、実測データの方が大きいleverです。

**5. embedding/reranker結論は方向性は正しいが、SSOT化は早い**

8Bをやめるのは正しいです。ただし、Voyage/gteに固定する前に、USDA gold retrieval setでA/Bしてください。2026年時点ではVoyage、Gemini Embedding 2、Qwen3-0.6B、EmbeddingGemma系など候補が多く、一般ベンチだけで食材検索の勝者は決められません。([Voyage AI][8])

**6. `grams:density=50:50` は有用だが、因果分解として過信しない**

density errorにはDB matchだけでなく、composite vs component表現、raw/cooked、ソースの含め方、VLMの食品名誘導が混ざります。改善施策は「食材マッチング」ではなく、**料理表現モードの選択** まで含めるべきです。

---

## 実装上の重大指摘

同梱スナップショット基準ですが、コード上で気になった点です。

1. **`services.vlm_service.py` が `settings.VLM_MODEL_ID` を参照していますが、`config.settings.py` 側は `DEFAULT_VLM_MODEL_ID` です。** `MealAnalysisPipeline.__init__()` は通常 `vlm_model_id=None` で `VLMService` を作るので、このままだと環境によっては初期化時に `AttributeError` になる可能性があります。実運用コードで別定義があるならよいですが、同梱物だけ見るとP0修正です。

2. **`DEFAULT_PROMPT_FILE` が同梱prompt名と一致していません。** settings側は長い旧ファイル名、ZIP側は `02_prompts/v13_CURRENT.txt` です。デプロイパッケージでpromptが別管理なら問題ありませんが、レビュー用一式だけではpackaging riskがあります。

3. **self-consistencyが共有 `vlm_service` 状態を変更する前提で逐次実行されています。** 並列化するなら、sampleごとにimmutable config/service instanceを使うべきです。今の設計で単純parallelにすると、model/prompt/seedのrace conditionを起こし得ます。

4. **`user_context` が精度leverなのに、画像解析promptに十分使われていないように見えます。** ユーザーの「半分食べた」「店名」「メニュー名」「大盛り」などは、写真より強い情報です。P0でprompt/schemaに入れるべきです。

5. **`match_rate_percent` が dish単位で、ingredient単位ではありません。** 1 dishに1 ingredientでもあれば100%扱いになり得るため、API指標として誤解を生みます。

6. **USDA検索失敗時に全体失敗へ寄りすぎです。** 1 ingredientのDB match失敗で落とすより、partial result + warning + user correction pathを返す方がプロダクト向きです。

---

## 優先ロードマップ

### P0: すぐ直す

* `VLM_MODEL_ID` / `DEFAULT_VLM_MODEL_ID`、prompt file packaging、verify prompt同梱を修正。
* VLM出力をPydantic/JSON Schemaで検証。
* v13.5 schemaとして `visual_label`、`usda_query_candidates`、`weight_low/likely/high`、`portion_confidence`、`composite/component role` を追加。
* retrieval gold set 500件を作成し、Qwen3-8B vs 小型embedderをA/B。
* `match_rate_percent` を ingredient-level / weighted-levelに変更。
* partial failureを許容し、warningつきで返す。

### P1: 27% MAE突破に効く

* composite dish検索とcomponent分解のdual pathを実装。
* Monte Carloでcalorie/PFC範囲を返す。
* uncertaintyが高い時だけ1問聞くUI/APIを作る。
* self-consistency K=3は全件ではなく、uncertainty highのselective実行にする。
* real mozu measured setをblind holdout込みで100枚以上へ増やす。

### P2: 20%未満を狙う

* top-down追加写真、before/after、scale object、depth/ARKitを高精度モードとして導入。
* portion専用モデルを、実測mozuデータ + Nutrition5k系データで学習。
* food category別・confidence別のconditional calibrationを構築。
* menu/barcode/branded food連携を追加。Branded Foodsは月次更新されるため、包装食品・チェーン商品ではUSDA genericより強いです。([USDA FoodData Central][3])

---

## 最終判定

あなた方のPDCAは、かなり健全です。特に **LLM-GT幻想から撤退したこと、pro採用を撤回したこと、global calibrationをVOIDにしたこと** は正しいです。

ただし、次の一手を「さらに良いVLM」「さらに良いprompt」「さらに速いembedding」に置きすぎると、27%の壁は大きく動かないと思います。根本は、**単一写真から点推定する設計そのもの** です。

mozuが高単価アプリなら、目指すべき体験はこれです。

> 写真だけなら正直な範囲推定。
> 不確実なら1問だけ聞く。
> scale/depth/menu/食べ残し情報があれば精度を上げる。
> DB groundingで説明可能にし、PFCまで破綻しない。

この方向なら、27% MAEは「promptの壁」ではなく「入力情報と不確実性設計の壁」として突破できます。

[1]: https://www.nature.com/articles/s43856-025-01159-0 "DietAI24 as a framework for comprehensive nutrition estimation using multimodal large language models | Communications Medicine"
[2]: https://arxiv.org/html/2602.05078v1 "Food Portion Estimation: From Pixels to Calories"
[3]: https://fdc.nal.usda.gov/faq "FAQs | USDA FoodData Central"
[4]: https://fdc.nal.usda.gov/download-datasets "Downloadable Data | USDA FoodData Central"
[5]: https://ai.google.dev/gemini-api/docs/models "Models  |  Gemini API  |  Google AI for Developers"
[6]: https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview "Gemini 3.1 Pro Preview  |  Gemini API  |  Google AI for Developers"
[7]: https://qwenlm.github.io/blog/qwen3-embedding/ "Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models | Qwen"
[8]: https://docs.voyageai.com/docs/embeddings "Text Embeddings"
[9]: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/embedding-2 "Gemini Embedding 2  |  Gemini Enterprise Agent Platform  |  Google Cloud Documentation"
[10]: https://github.com/google-research-datasets/Nutrition5k "GitHub - google-research-datasets/Nutrition5k: Detailed visual + nutritional data for over 5,000 plates of food. · GitHub"
[11]: https://arxiv.org/abs/2604.06352 "[2604.06352] DietDelta: A Vision-Language Approach for Dietary Assessment via Before-and-After Images"
[12]: https://mm.cs.uec.ac.jp/e/pub/conf19/191021ando_0.pdf "DepthCalorieCam: A Mobile Application for Volume-Based Food Calorie Estimation using Depth Cameras"
[13]: https://openaccess.thecvf.com/content/CVPR2025W/MTF/html/Romero-Tapiador_Are_Vision-Language_Models_Ready_for_Dietary_Assessment_Exploring_the_Next_CVPRW_2025_paper.html "CVPR 2025 Open Access Repository"
