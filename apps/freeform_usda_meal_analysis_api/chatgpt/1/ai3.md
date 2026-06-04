## 総評

**結論として、私は御社のPDCA結論に「大筋では賛成」です。** 特に、**frozen-50のGPT推定GTを真の精度評価に使えない、Gemini Pro採用撤回、v14不採用、global calibration無効化、8B embedding過剰、実測mozuデータが最終判断軸**という判断は妥当です。

ただし、重要な修正点があります。今のパイプラインは「VLMが食品名とグラムを一点推定 → USDA top-1に寄せる → 合計 kcal」としてはかなり整理されていますが、**27% MAEの壁を破るには、プロンプト改善ではなく、入力情報・不確実性・検索候補分布・実測データ校正を設計の中心に置く必要があります。** 単一2D画像から絶対スケールと3D形状を復元すること自体が難しく、2026年時点のportion estimationレビューでも、2D画像では物理スケールと形状復元が本質課題であり、depth/multi-view/model-basedの方向が整理されています。([arXiv][1]) また、単一画像のボウル内容量推定でも、容器が既知・測定済みであるなどの強い前提があるときに初めて量推定が成立しやすいことが示されています。([サイエンスダイレクト][2])

私の評価を一言でまとめると、**「現在のmozuは、監査可能なVLM+DB型カロリー推定として正しい方向にある。しかし、まだ“単一写真の点推定器”であり、高価格帯プロダクトに必要な“測定補助・不確実性提示・ユーザー追加入力・実測校正ループ”が弱い」**です。

---

## 0. 賛否サマリ

| 論点                                  |     私の賛否 | コメント                                                                                                    |
| ----------------------------------- | -------: | ------------------------------------------------------------------------------------------------------- |
| frozen-50のGPT推定GTは危険                | **強く賛成** | これは評価ではなく、GPT-5-proとの一致度です。実測GTへ寄せる判断は正しいです。                                                            |
| Gemini 3.1 Pro採用撤回、Flash継続          |   **賛成** | 御社実測ではPro優位が非ロバスト。費用・再現性・速度を考えるとFlash基準が妥当。ただし2026年6月時点ではGemini 3.5 Flashも候補に入れるべきです。([blog.google][3]) |
| v13継続、v14不採用                        | **概ね賛成** | v14は大皿tailには効くが、200–1500 kcal帯には効いていない。だがv13の80g下限・不確実性欠如・USDA名強制は修正すべきです。                              |
| global calibrationはVOID             | **強く賛成** | バイアス符号がセットで反転するなら、global slope/interceptは危険です。                                                          |
| self-consistency K=3は限定採用           |   **賛成** | 2pt前後の改善なら、全件常時ではなく高不確実・高価値ケースに絞るのが妥当です。                                                                |
| Qwen3-Embedding-8B + 4B rerankerは過剰 | **強く賛成** | 13.5k件・短文検索・rerankありなら、8B serverless cold startは設計ミスマッチです。                                              |
| 20–50件の実測mozuデータを最終判断軸にする           | **半分賛成** | pilotとしては良いですが、校正・promotion gateには少なすぎます。最低でも層化200–500件規模を目標にすべきです。                                     |
| 27%は「ほぼ不可避の壁」                       | **反対寄り** | 単一写真・追加入力なしではかなり硬い壁です。ただしmulti-view/depth/reference/user context/候補分布化でまだ突破余地があります。                     |

---

## 1. 根本のパイプライン設計レビュー

現在の設計は、README上では以下の流れです。

`VLM v13 → query normalization/extraction → hybrid search → reranker → nutrition aggregation → calibration OFF → optional self-consistency`

これは、**直接VLMに総カロリーを言わせる設計よりは良い**です。理由は、食品名・グラム・USDA/FDC候補・栄養値を分解でき、誤差要因を監査できるからです。Nutrition5kのような代表的な実測データセットも、料理画像だけでなく、食品ごとの質量、総質量、カロリー、主要栄養素などを含む形で設計されており、評価対象を「見た目の印象」ではなく「測定された質量・栄養値」に置くことが重要です。([GitHub][4])

ただし、現在の根本設計には大きな構造問題が3つあります。

### 1.1 「食品認識」「量推定」「密度推定」がまだ強く結合しすぎている

現行では、VLMが `search_name` と `weight_g` を出し、検索側がUSDA/FDCのtop候補を選び、そこで kcal/g がほぼ決まります。つまり誤差は大きく分けて、

1. 食品を何だと見たか
2. 何グラムと見たか
3. どのUSDA/FDC密度に対応づけたか

の3つですが、実装上は「VLM出力 + top-1検索」でかなり早い段階に一点化されています。

御社PDCAの `grams:density = 50:50` という結論は非常に重要で、ここから導くべき設計方針は、**グラムも密度も一点推定してはいけない**です。特に `density perfect still 19.7%、grams perfect still 23.7%` という結果は、「どちらか片方を少し改善する」だけでは20%未満に届きにくいことを示しています。

推奨は、食品ごとに以下を分けることです。

```json
{
  "canonical_food": "cheeseburger",
  "visual_attributes": {
    "cooking_method": "grilled",
    "form": "sandwich",
    "visible_cheese": true,
    "visible_sauce": "some",
    "fried_or_oily": "uncertain"
  },
  "portion_estimate": {
    "likely_g": 210,
    "low_g": 150,
    "high_g": 290,
    "scale_reference": "burger diameter roughly 10-12 cm, no known object",
    "occlusion": "partial",
    "confidence": 0.62
  },
  "retrieval_queries": [
    "cheeseburger, regular, with bun",
    "hamburger with cheese, sandwich",
    "fast food cheeseburger"
  ]
}
```

その後、検索側でtop-1ではなく、**top-k候補の確率分布として kcal/g を持つ**べきです。最終カロリーは、

`E[kcal] = E[grams] × E[kcal/g]`

だけでなく、

`low / likely / high` や `P(error > 30%)` も出せます。

### 1.2 USDA/FDC検索は妥当だが、使っているデータタイプが限定的

御社READMEでは、USDA DBは13,564件で、FNDDS/survey、SR Legacy、Foundationを使っています。一方、USDA FoodData Central自体にはFoundation、Experimental、FNDDS、Branded、SR Legacyなど複数のデータタイプがあります。([USDA FoodData Central][5])

高価格帯のUS/European向けアプリで、ユーザーが撮る食事には、外食、加工食品、ブランド食品、レストランメニュー、地域料理がかなり含まれるはずです。現在のFNDDS/SR/Foundation中心の設計は、家庭料理・一般食品には良い一方で、**ブランド食品・チェーン店・惣菜・欧州系食品名の密度ズレ**に弱くなります。

提案は、USDA/FDCを捨てることではありません。むしろ、

* 汎用食品：FNDDS/SR/Foundation
* 包装・ブランド食品：Branded/FDCまたは外部商品DB
* 外食：menu item DBまたはユーザー入力
* 自社実測：mozu observed calibration table

のように、**食品ソースに層を持たせる**べきです。

### 1.3 高価格帯プロダクトとしては、推定だけで完結しすぎている

現状は「1枚の画像から一発推定」に最適化されています。しかし、カロリー推定は単一画像だけでは物理的に曖昧です。2025年の食事画像LMM研究でも、総重量情報を与えると栄養推定誤差が大きく改善し、真の重量情報や予測重量情報の価値が強調されています。([digitalcommons.odu.edu][6])

したがって、高価格帯アプリなら、全件で追加撮影を強制する必要はありませんが、**不確実性が高いときだけ追加入力を求めるUX**が必要です。

例：

* 「皿の直径はだいたい何cmですか？」
* 「これは1人前ですか、シェア用ですか？」
* 「食べた量は全部ですか、半分ですか？」
* 「横からもう1枚撮ると精度が上がります」
* 「この料理はレストラン/コンビニ/自炊のどれですか？」

現在の `user_context` はAPI/router側で受けられるように見えますが、pipeline内でVLM promptに実質反映されていません。これはかなり大きな見落としです。外部研究でも、food metadataやcontextが栄養推定出力に大きく影響しうることが示されており、使うならリーク管理をしたうえで明示的な評価軸にすべきです。([arXiv][7])

---

## 2. VLMモデル選定レビュー

### 2.1 Gemini Flash継続の判断には賛成

御社の実測PDCAでは、Gemini 3.1 Proはfrozen-50では良く見えたが、Nutrition5k/NutritionVerse-Realでは非ロバストで、認識面でもFlash優位または同等でした。さらにProはコスト・再現性面で不利。したがって、**現時点の実測に基づくFlash継続は正しい判断**です。

Google側のドキュメントでも、Gemini 3 Flash PreviewはFlash系として低遅延・低コスト寄りでありつつ、structured outputや画像入力などをサポートしています。([Google Cloud Documentation][8]) またGeminiは画像理解、captioning、classification、VQA、object detection系の利用が想定されています。([Google AI for Developers][9])

### 2.2 ただし、2026年6月時点ではGemini 3.5 Flashを必ず評価すべき

2026年5月19日にGemini 3.5 Flashが発表され、Gemini API/AI Studio/Vertex AIで利用可能とされています。Googleは3.5 Flashを、Flash速度で大規模モデル級の品質に近づけたモデルとして位置づけています。([blog.google][3])

したがって、2026年6月4日時点のモデル候補は、

1. 現行：Gemini 3 Flash Preview
2. 新候補：Gemini 3.5 Flash
3. fallback/expensive judge：Gemini 3.1 Proまたは同等Pro系
4. 低コスト検証：Flash-Lite系

にすべきです。

ただし、**一般ベンチマークで3.5 Flashが良いから即採用、は不可**です。御社のPDCAが示す通り、一般性能と食事カロリーMAEは一致しません。`NVReal target range`、`Nutrition5k`、`mozu measured`で同じpromotion gateを通すべきです。

### 2.3 OpenRouter経由の抽象化は便利だが、Gemini固有機能を取り逃がしている可能性

現行コードは `reasoning_effort=medium` を使っていますが、Google側のGemini 3 Flashドキュメントでは、quality/latency/costを調整する `thinking_level`、画像のtoken/latencyに影響する `media_resolution`、structured outputなどの機能が整理されています。([Google Cloud Documentation][8])

食事写真では、画像解像度・小さな具材・ソース・油・皿サイズが重要なので、**media resolutionを含むネイティブパラメータのA/B**は価値があります。OpenRouter経由でその制御が不完全なら、少なくとも評価系ではGoogle API直叩きも比較すべきです。

### 2.4 Proは常時利用ではなく「難例だけのsecond pass」に落とすべき

Proを完全に捨てる必要はありません。しかし常時Proは、御社データ上では正当化されていません。

推奨は、

* Flashで通常推定
* 不確実性が高いときだけPro/3.5 Flash/別モデルにsecond opinion
* 2モデルの差が大きいときはユーザー確認
* Proは「正解生成器」ではなく「不確実性検知器」として使う

です。

---

## 3. prompt v13レビュー

v13は、プロンプト単体としてはよく整理されています。特に良い点は以下です。

* 3-pass構成：component map → portioning → density correction
* visible components重視
* hidden oil/fatを勝手に足さない
* USDA風の検索名を出す
* strict JSON schema
* integrated dishとseparate clusterの区別

これは、VLMの自由作文を抑え、retrieval pipelineに流すには適切です。

しかし、**v13は「安定した一点推定」には良いが、「精度改善のための情報表現」としては不足**しています。

### 3.1 `main_food.weight_g: 80–400g` は危険

v13ではmain_foodのweightが80–400gに制約されています。これは、普通の一皿には妥当でも、以下で系統誤差を作ります。

* 小さな食品：cookie、small pastry、small side、single sushi、small appetizer
* 軽いが大きく見える食品：salad、leafy vegetables、popcorn
* 大きな皿：pasta bowl、party plate、large salad、shared platter
* 複数個食品：pizza slices、dumplings、wings、sushi pieces

御社v14実験でも、小さい対象の過大推定が残っており、`main lower bound 80g` の影響が疑われています。私は、v13の次バージョンでは、**上限を上げるより先に下限を下げるべき**だと思います。

推奨：

* main_food: 20–900g
* extras: 1–300g
* ただし単なる範囲拡大ではなく、`portion_low_g / portion_likely_g / portion_high_g` を必須化
* `count`、`area_fraction`、`thickness_class`、`container_reference` を出す

### 3.2 USDA名をVLMに直接作らせすぎている

v13では `search_name` にUSDA風のcomma namingを要求しています。これは検索には便利ですが、VLMに「見たものを記述する」仕事と「DBに寄せる」仕事を同時にさせています。

より良い設計は、

```json
{
  "canonical_name": "fried chicken thigh",
  "visual_description": "one crispy fried chicken piece with visible breading",
  "preparation": "fried",
  "state": "cooked",
  "usda_query_candidates": [
    "chicken, broilers or fryers, thigh, meat and skin, fried",
    "fried chicken, dark meat, with skin",
    "chicken thigh, breaded, fried"
  ]
}
```

のように、**認識結果と検索クエリ候補を分ける**ことです。

### 3.3 hidden fat方針は正しいが、不可視油を完全に無視すると密度ズレが残る

「見えない油・バター・マヨを勝手に足さない」は、ユーザー信頼の観点では正しいです。ただし、カロリー精度の観点では、炒め物、パスタ、揚げ物、外食、ソース料理では不可視油が大きな密度要因になります。

ここは二層に分けるべきです。

```json
"visible_fat_oil": {
  "detected": true,
  "description": "glossy sauce visible on pasta",
  "estimated_g": 12
},
"latent_cooking_fat_prior": {
  "level": "medium",
  "reason": "stir-fried dish / restaurant-like",
  "estimated_extra_kcal_range": [40, 160]
}
```

つまり、ユーザーに表示する「見えている材料」と、内部の不確実性として扱う「調理油prior」を分けます。

### 3.4 prompt v13は`user_context`を使う前提に拡張すべき

高精度化の観点では、ユーザーが一言くれるだけで精度が大きく改善するケースがあります。

* 「これは半分食べた後」
* 「大皿を2人でシェア」
* 「直径26cmの皿」
* 「スタバのラテ」
* 「チキンは150gパック」
* 「ご飯は茶碗1杯」

現行コードでは `user_context` を受ける口はありますが、VLM promptに反映されていないように見えます。これはP0級の改善余地です。2025年のLMM栄養推定研究でも、context/metadataが推定に大きく影響しうるため、リーク管理と評価設計を前提に活用すべきです。([arXiv][7])

### 3.5 v14不採用には賛成。ただしv13.1を作るべき

v14は「大皿スケーリング」には少し効いたが、target range 200–1500 kcalではほぼ改善していません。したがって、v14をそのまま採用しない判断は妥当です。

ただし、次はv14方向の単なるscale proseではなく、**schemaを変えるv13.1**にするべきです。

最小変更案：

* `weight_g` を `portion_likely_g` に改名
* `portion_low_g`, `portion_high_g` を追加
* `scale_reference` を追加
* `portion_basis` を追加：`count`, `area`, `plate_fraction`, `known_container`, `typical_serving`
* `hidden_density_risk` を追加：`low/medium/high`
* main lower boundを80gから20gへ
* USDA検索名とcanonical foodを分離

---

## 4. embedding / reranker構成レビュー

ここは御社PDCAに**強く賛成**です。Qwen3-Embedding-8B + Qwen3-Reranker-4Bは、能力としては高いが、mozuのユースケースには重すぎます。

Qwen3 Embedding 8BはMTEB等で強いモデルとして位置づけられ、0.6B/4B/8Bのサイズ展開や最大4096次元、MRL、instruction supportを持っています。([Hugging Face][10]) しかし、mozuの検索対象は13.5k件程度で、クエリも短く、BM25+rerankもあるため、8B embedding serverless cold startに30秒払うのは明らかに過剰です。

### 4.1 推奨構成

私なら以下にします。

#### Stage 0: ルール/辞書候補生成

まずembedding以前に、食品DBは閉じた13.5k件なので、以下の候補生成を強化します。

* exact normalized match
* singular/plural
* cooked/raw/fried/grilled/baked synonym
* FNDDS food group
* comma-name permutation
* common aliases
* typo補正
* ingredient-to-dish map
* density prior bucket

これは高速で、説明可能で、cold startがありません。

#### Stage 1: 軽量embedding

候補：

* Voyage 3.5-lite
* Gemini embedding-2
* Qwen3-Embedding-0.6B self-host
* bge-m3系
* EmbeddingGemma系

Voyage 3.5/3.5-liteはMatryoshka対応で、2048/1024/512/256次元に対応し、低コスト・低次元運用を想定しやすいモデルです。([Voyage AI][11]) Gemini APIのembeddingは2026年時点で `gemini-embedding-2` がmultimodal embeddingとして提供され、text-onlyの `gemini-embedding-001` も存在します。([Google AI for Developers][12]) ただし `gemini-embedding-001` は2026年7月14日にshutdown予定とされ、replacementは `gemini-embedding-2` とされているため、新規採用は避けるべきです。([Google AI for Developers][13])

#### Stage 2: 軽量reranker

4B rerankerは重いです。候補は、

* Qwen3-Reranker-0.6B
* gte/ModernBERT系reranker
* Voyage rerank系
* Jina reranker系

で十分比較価値があります。重要なのはMTEB順位ではなく、**USDA/FNDDS top-1/top-3密度誤差が改善するか**です。

### 4.2 評価KPIはretrieval専用に分けるべき

retrievalは総カロリーMAEだけで評価すると、VLMグラム誤差と混ざります。別に以下を測るべきです。

* `food_code_hit@1`
* `food_code_hit@3`
* `food_group_hit@1`
* `density_abs_error@1`
* `density_oracle@3`
* `reranker top1 vs top3 expected kcal`
* `fried/raw/cooked/sauce mismatch rate`
* `high-density false positive rate`

特に御社のPDCAでdensityが誤差の約半分なら、**density_oracle@3** は非常に重要です。もしtop3内に正しい密度があるなら、reranker/selector問題です。top3にもなければ、query/schema/DB coverage問題です。

### 4.3 コード上の懸念

静的レビュー上、以下はかなり気になります。

* `services.embedding_providers.py` に、PDCAで推奨しているVoyage/Gemini/EmbeddingGemma系providerがまだありません。
* `services.reranker_providers.py` に、gte-modernbert等の推奨候補がまだありません。
* `food_search_service.py` のdefault weightが `bm25=0.6/vector=0.4` で、settings側の `bm25=0.4/vector=0.6` とズレています。main pathでは設定を渡しているようですが、fallback/direct pathで挙動差が出ます。
* `food_search_service.py` の一部direct search pathで `reranker_model` が渡っていないように見えます。
* `ConfigManager.detect_config_drift()` がVLM周りしか見ておらず、embedding model、reranker model、search weights、self_consistency、calibration状態を見ていません。

このあたりは、実験結果の再現性を壊すので、model selection以前に直すべきです。

---

## 5. 27% MAEの壁を破る手法

御社の「target range 200–1500 kcalで約27%、biasは小さく、gramsとdensityが半々」という診断はかなり有用です。ここから導くべき結論は、**単一レバーではなく、gramsとdensityを同時に改善する必要がある**ということです。

### 5.1 最も効くのは、入力情報を増やすこと

最有力は以下です。

1. 横からもう1枚撮る
2. 短い動画にする
3. 皿・容器サイズを聞く
4. 手・フォーク・カードなどのreference objectを使う
5. phone depth / ARKit / ARCore / LiDARを使う
6. 「何人前か」「何割食べたか」を聞く

単一2D画像では絶対スケールと3D形状が曖昧である、という制約はプロンプトでは消せません。portion estimationのレビューでも、metric 3D structure、absolute physical scale、shape geometryが中心課題として整理されています。([arXiv][1])

### 5.2 総重量を先に推定し、その後に食品へ配分する

現在は食品ごとにグラムを推定して足し上げる構造です。別ルートとして、

1. 画像全体から総food massを推定
2. 食品別の面積・体積比で配分
3. retrieval densityでカロリー化

を試すべきです。

2025年のLMM食事推定研究では、予測または真の総重量情報を追加すると栄養推定誤差が大きく改善しており、重量情報が根本レバーであることが示されています。([digitalcommons.odu.edu][6])

### 5.3 top-1 USDAではなく、密度分布を使う

現在は、検索・rerank後のtop候補で栄養値がほぼ決まります。しかし、例えば同じ「chicken」でも、

* grilled chicken breast
* fried chicken thigh with skin
* chicken salad with mayo
* chicken curry
* chicken sandwich

ではkcal/gが大きく違います。

御社のdensity誤差が大きいなら、top-1を当てに行くより、

```text
candidate 1: grilled chicken breast, p=0.45, 1.65 kcal/g
candidate 2: fried chicken, p=0.30, 2.60 kcal/g
candidate 3: chicken with sauce, p=0.25, 2.10 kcal/g
```

のように分布化し、期待値と区間を返すべきです。

特に、`fried/oily/creamy/cheesy/sauce` のvisual attributeをretrieval scoringに直接入れると、density側の改善余地があります。

### 5.4 mozu実測データで、global calibrationではなく階層校正する

global calibrationがVOIDという判断は正しいです。やるべきは、

* food group別
* plate/bowl別
* small/medium/large別
* sauce/fried/high-fat別
* image angle別
* confidence別
* restaurant/home/packaged別

の**階層ベイズ的な校正**です。

例：

```text
predicted_grams_corrected =
  predicted_grams
  × food_group_factor
  × container_factor
  × size_bucket_factor
  × confidence_factor
```

densityも同様に、

```text
density_prior_adjustment =
  food_group_density_prior
  + preparation_method_adjustment
  + sauce/oil/cheese risk
```

と分けるべきです。

ここで重要なのは、御社のPDCAが示す通り、grams underとdensity overが相殺している可能性があることです。**片方だけ雑に補正すると、むしろ総カロリーは悪化します。**

### 5.5 self-consistencyは「全件」ではなく「不確実ケース」に使う

K=3 medianで約2pt改善するというPDCA結論は価値があります。ただし、latency 3倍なら全件適用は重いです。

推奨は、

* low confidence
* high calorie meal
* top-k density varianceが大きい
* portion interval幅が大きい
* VLM direct estimateとDB estimateが大きく乖離
* ユーザーがpremium/high accuracy modeを選択

の場合だけK=3にすることです。

さらに、現行はsequential実行のため遅いようなので、VLMServiceをstateless/isolatedにしてparallel K=3にできる設計へ寄せるべきです。

### 5.6 27%突破の現実的ロードマップ

私なら、以下の順にやります。

| 優先 | 施策                                          | 期待効果                      |
| -: | ------------------------------------------- | ------------------------- |
| P0 | `user_context`をVLM promptに反映                | 低コストで大きい。既にAPI口があるのに未使用。  |
| P0 | v13.1でweight rangeをlow/likely/high化、80g下限撤廃 | 小皿・小物・uncertainty改善。      |
| P0 | top-1 USDAからtop-k density distributionへ     | density側の50%誤差に直接効く。      |
| P1 | 不確実時の追加質問/追加写真UX                            | 単一写真の物理限界を超える。            |
| P1 | mozu実測200–500件の層化収集                         | 校正・promotion gateの母集団を作る。 |
| P1 | Gemini 3.5 Flash / native Gemini params A/B | モデル更新による差分確認。             |
| P2 | segmentation + depth/reference object       | 量推定の本命。                   |
| P2 | personalized correction loop                | ユーザーの皿・食習慣に適応。            |

---

## 6. 評価KPI設計レビュー

評価設計はかなり良いですが、**READMEとEVAL_RUBRICの間にKPIのSSOT矛盾があります。**

READMEではmain metricが total calorie MAE% とされています。一方、EVAL_RUBRICでは「final KPI is USER CONVICTION」と読める記述があり、その後に「convictionはcalorie MAEを置き換えない」とあります。これはプロダクト組織では危険です。モデル改善会議のたびに「何を勝ちとするか」が揺れます。

### 6.1 KPIは二層に分けるべき

#### Model promotion KPI

これは実測GTに対する客観評価です。

* total kcal MAE%
* median APE
* p90 APE
* signed bias
* slope
* 30%+ error rate
* absolute kcal MAE
* macro absolute gram error
* density error
* portion gram error
* recognition semantic match
* latency/cost

#### Product KPI

これはユーザー価値です。

* correction rate
* user acceptance
* user trust/conviction
* retention
* manual edit burden
* number of clarification prompts accepted
* perceived usefulness
* safety complaint rate

この2つは両方必要ですが、**promotion gateで混ぜすぎない**ほうがいいです。

### 6.2 LLM judgeは補助であり、真のカロリー評価ではない

これは御社も理解している通りです。LLM judgeは、

* 食品名が妥当か
* 見えている具材を落としていないか
* UIとして納得感があるか
* 料理説明が自然か

を見るには使えます。しかし、実測カロリーMAEの代替にはなりません。

DietAI24のような評価でも、nutrient estimation、food code inference、portion size、usabilityなどを分けており、食品コード推定もexact/close/far/mismatchのように段階評価されています。([Nature][14]) mozuも、recognitionを単純な文字列F1ではなく、食品グループ・調理法・密度クラスの近さで評価すべきです。

### 6.3 macro KPIは相対誤差だけだと壊れる

sample NVRealではfat MAE%が非常に大きく出ています。脂質やタンパク質は分母が小さいケースで相対誤差が爆発するため、以下を併用すべきです。

* protein/fat/carbs absolute gram MAE
* kcal contribution MAE
* macro ratio error
* relative error with denominator floor
* high-fat miss rate
* hidden oil/sauce miss rate

### 6.4 推奨promotion gate

私なら以下をAND条件にします。

```text
1. measured total kcal MAE% improves by >= 2.0pt
2. paired BCa bootstrap CI upper < 0
3. p90 APE does not regress
4. signed bias absolute value does not worsen
5. 30%+ error rate does not worsen
6. recognition semantic close-or-better does not regress
7. latency p90 and cost remain within product budget
8. subgroup regression guard passes:
   - small meals <300 kcal
   - target 300–700
   - target 700–1500
   - large >1500
   - bowl
   - plate
   - fried/high-fat
   - mixed dishes
```

加えて、intervalを出すなら、

* 80% prediction interval coverage
* 90% prediction interval coverage
* calibration error

も見るべきです。

---

## 7. PDCA結論の誤り・見落とし

### 7.1 正しい結論

以下は同意です。

#### frozen-50 GTは使えない

GPT-5-pro推定をGTにした評価は、真のカロリー精度ではなく、GPT-5-proとの一致度です。Nutrition5kのように測定された質量・栄養値を持つデータセットを重視する転換は正しいです。([GitHub][4])

#### Pro優位は非ロバスト

御社のNVReal/Nutrition5k結果を見る限り、Proの常時採用は正当化されません。Flash基準は妥当です。

#### v14は不採用でよい

target rangeで改善していないなら、採用しないのが正しいです。大皿tailだけを改善しても、主戦場のMAEが動かないならpromotion不可です。

#### global calibrationは危険

bias signがセットで反転するなら、global補正は評価セット依存の過学習です。

#### 8B embeddingは過剰

13.5k件の短文食品検索で30秒cold startは、検索品質以前にプロダクト要件と合っていません。

### 7.2 修正すべき結論

#### 「20–50件のmozu実測が最終arbiter」は弱い

20–50件はpilotとしては良いです。しかし、

* 食品カテゴリ
* 撮影角度
* 皿/ボウル
* 大小
* 国/料理
* 外食/自炊
* 高脂質/低脂質

に層化すると、すぐに各セル数が足りなくなります。

**20–50件は“方向確認”。promotion gateやcalibrationには最低200–500件を目標**にしたほうがいいです。

#### 「promptではもう動かない」は言い過ぎ

v14のprose変更が効かなかった、は正しいです。しかし、schema変更、user_context反映、uncertainty追加、80g下限撤廃、retrieval query候補分離は、単なるprompt tuningではなく**情報設計の変更**です。これはまだ試す価値があります。

#### 「27%はvarianceだから仕方ない」は早い

御社の分解は、現行入力・現行pipelineでのvarianceを示しています。しかし、外部研究から見ても、重量情報・depth・multi-view・metadata/contextは栄養推定に影響しうるため、「単一写真・追加情報なしなら硬い壁」までは言えても、「プロダクトとして突破不能」とはまだ言えません。([digitalcommons.odu.edu][6])

#### 「real measured dataが最終arbiter」なのに、コードがまだ実験駆動になっていない

現在のコードは、config drift検知やprovider実装、retrieval候補分布、user_context反映が不十分です。PDCAの結論をプロダクトコードに落とし切れていません。

---

## 8. コード上の重大指摘

静的レビューなので、ZIP外の実リポジトリに別実装がある場合は読み替えてください。ただし、この添付一式だけを見る限り、以下は優先度が高いです。

### P0: `VLMService` のdefault model参照が壊れている可能性

`services.vlm_service.py` で、`model_id is None` のときに `settings.VLM_MODEL_ID` を参照しています。一方、`config.settings.py` 側では `DEFAULT_VLM_MODEL_ID` が定義されています。ZIP内grepでは `VLM_MODEL_ID` 定義が見当たりません。

これは、default引数で `VLMService()` を作る経路では `AttributeError` になり得ます。`MealAnalysisPipeline.__init__` も `vlm_model_id=None` を許すので、かなり危険です。

修正：

```python
model_id = model_id or settings.DEFAULT_VLM_MODEL_ID
```

さらに、起動時に現在のeffective configを必ずログ/health endpointに出すべきです。

### P0: `user_context` が実質使われていない

router/request/pipelineには `user_context` の口がありますが、VLM promptやqueryに反映されていないように見えます。これは、27% MAE突破に関係する最重要レバーを捨てています。

修正方針：

* `VLMService.analyze_image()` に `user_context` を渡す
* prompt冒頭に `USER PROVIDED CONTEXT` を挿入
* contextあり/なしをevalで分ける
* contextがGTリークにならないよう、評価時は許可フィールドを固定する

### P0: calibrationコードのdocstringがPDCA最終結論と矛盾

`core.calorie_calibration.py` は、古い「系統的過小推定」「slope 0.47」「MAE改善」前提のコメントが残っています。PDCA最終結論ではcalibration VOIDです。

これは将来誰かが誤ってONにするリスクがあります。

修正：

* deprecated扱いにする
* in-domain measured calibration fileがない限り起動不可
* global factorではなくfood-group階層補正へ置換
* grams表示自体をscaleしない。補正後カロリーと元の推定グラムを分ける

### P1: self-consistencyがsequentialで遅い

K=3を本番で使うなら、parallel化すべきです。現状はshared mutable VLM serviceのためsequentialという記述があり、latencyが3倍になります。

修正：

* seedごとにstateless request
* cache keyにseed含有は既に良い
* 並列実行
* high uncertainty時のみK=3

### P1: retrieval providerがPDCA結論に追いついていない

PDCAではVoyage/Gemini/EmbeddingGemma/gte-modernbert等が候補に出ていますが、provider実装はまだDeepInfra/SiliconFlow/Jina/Novita中心です。

実験結論をコードに反映するには、provider追加とA/B gateが必要です。

### P1: `match_rate` が粗い

現在の `match_rate` は、実質「dishにingredientsがあるか」程度に見えます。これは食品認識やUSDA matchの品質を表すには粗すぎます。

必要なのは、

* VLM recognized item count
* retrieval hit@1/hit@3
* food group match
* preparation method match
* density class match
* high-calorie visible component miss

です。

---

## 9. 具体的な次アクション

### 最初の2週間でやるべきこと

1. `settings.VLM_MODEL_ID` バグ修正
2. `user_context` をpromptに反映
3. v13.1を作る

   * low/likely/high grams
   * 80g下限撤廃
   * scale_reference追加
   * canonical nameとUSDA query分離
4. retrievalをtop-k density distribution化
5. config drift検知をVLM以外にも拡張
6. calibration moduleをdeprecated/guardedにする
7. Gemini 3.5 Flashを同一gateでA/B
8. embeddingを8Bから軽量候補へ置換実験
9. measured mozu pilot 50件を、将来の200–500件層化設計に沿って収集
10. KPI SSOTを修正し、model promotion KPIとproduct KPIを分離

### 次のprompt v13.1の方向

```text
You must estimate visible food items for a nutrition retrieval pipeline.
Return JSON only.

For each item:
- canonical visible food name
- preparation/cooking method
- visible components
- count if countable
- portion_low_g
- portion_likely_g
- portion_high_g
- portion_basis
- scale_reference
- occlusion_level
- density_risk: low/medium/high
- visible_oil_sauce_cheese
- possible_hidden_fat_prior, but do not display it as visible ingredient
- usda_query_candidates: 3-5 strings
```

### 次のretrieval設計

```text
candidate_score =
  lexical_score
  + semantic_score
  + prep_method_match
  + food_group_match
  + density_prior_match
  - contradiction_penalty
```

出力はtop-1ではなく、

```json
{
  "selected_candidates": [
    {"fdc_id": "...", "name": "...", "kcal_per_g": 2.1, "p": 0.45},
    {"fdc_id": "...", "name": "...", "kcal_per_g": 2.7, "p": 0.30},
    {"fdc_id": "...", "name": "...", "kcal_per_g": 1.6, "p": 0.25}
  ]
}
```

にします。

### ユーザーUX

推定結果を黙って一点で出すのではなく、信頼度に応じて分けるべきです。

* 高信頼：そのまま表示
* 中信頼：範囲つき表示
* 低信頼：1問だけ確認
* 超低信頼：横写真または料理名入力を依頼

高価格帯プロダクトなら、これは弱点ではなく価値になります。

---

## 最終判断

御社のPDCAは、かなり健全です。特に、**GPT推定GTを捨てたこと、Pro神話を捨てたこと、v14を数字で棄却したこと、global calibrationを止めたこと**は正しいです。

一方で、次の3点は明確に修正すべきです。

1. **27% MAEの壁を、モデル/プロンプトだけで破ろうとしている設計思想を捨てる。**
   本命は、scale/reference/multi-view/user_context/実測校正です。

2. **一点推定をやめる。**
   portionもdensityもtop-k/low-likely-high/uncertaintyで持つべきです。

3. **PDCA結論をコードとKPIに反映し切る。**
   user_context未使用、calibration stale docstring、provider未実装、config drift不足、KPI SSOT矛盾は、次の実験より先に直す価値があります。

したがって、私のレビュー結論はこうです。

**現行mozuは「VLM+USDA型カロリー推定」の良いbaselineです。ただし、27% MAEを超えるには、VLMモデル選定やprompt v13/v14の微調整では足りません。次の勝ち筋は、実測mozuデータ、入力UX、portion uncertainty、density candidate distribution、軽量高速retrievalへの再設計です。**

[1]: https://arxiv.org/html/2602.05078v1 "Food Portion Estimation: From Pixels to Calories"
[2]: https://www.sciencedirect.com/science/article/abs/pii/S0260877424000098 "Image-based volume estimation for food in a bowl - ScienceDirect"
[3]: https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-5/ "Gemini 3.5: frontier intelligence with action"
[4]: https://github.com/google-research-datasets/Nutrition5k "GitHub - google-research-datasets/Nutrition5k: Detailed visual + nutritional data for over 5,000 plates of food. · GitHub"
[5]: https://fdc.nal.usda.gov/data-documentation "Data Documentation | USDA FoodData Central"
[6]: https://digitalcommons.odu.edu/computerscience_fac_pubs/417/ "
\"Benchmarking and Improving Foundation Model Dietary Estimates from Mea\" by Yongcheng Mu, Jiangwen Sun et al.
"
[7]: https://arxiv.org/html/2507.07048v1 "Evaluating Large Multimodal Models for Nutrition Analysis: A Benchmark Enriched with Contextual Metadata"
[8]: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-flash "Gemini 3 Flash  |  Gemini Enterprise Agent Platform  |  Google Cloud Documentation"
[9]: https://ai.google.dev/gemini-api/docs/image-understanding "Gemini API  |  Google AI for Developers"
[10]: https://huggingface.co/Qwen/Qwen3-Embedding-8B "Qwen/Qwen3-Embedding-8B · Hugging Face"
[11]: https://blog.voyageai.com/2025/05/20/voyage-3-5/ "voyage-3.5 and voyage-3.5-lite: improved quality for a new retrieval frontier – Voyage AI"
[12]: https://ai.google.dev/gemini-api/docs/embeddings "Embeddings  |  Gemini API  |  Google AI for Developers"
[13]: https://ai.google.dev/gemini-api/docs/deprecations "Gemini deprecations  |  Gemini API  |  Google AI for Developers"
[14]: https://www.nature.com/articles/s43856-025-01159-0 "DietAI24 as a framework for comprehensive nutrition estimation using multimodal large language models | Communications Medicine"
