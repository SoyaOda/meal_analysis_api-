素晴らしい抽出です（11,104件）。**FoodOn単体には「頻度」や「よく使う一般名」のラベルは設計上ありません**。FoodOnは“**汎用カテゴリを階層化**してラベル／同義語を提供するオントロジ”で、消費量や流通頻度は保持しません【The food product branch has 9,600+ generic categories; objective is unambiguous generic products, not brands.】。従って**COREの候補は FoodOn の構造を使って “料理ベース” と “食材” を機械的に仕分け**し、**外部コーパス（OFFやレシピ）で頻度スコア付け**して上位を採用するのが現実的です。以下に、**どの分岐を使ってどう選ぶか**、**頻度の付け方**、そして**実装の要点**をまとめます。

---

## 1) FoodOnからの機械的な「ベース料理 vs. 食材」切り出し

FoodOnは**食材／料理の区別に役立つ上位概念**を公開しています（SPARQLチュートリアルに親クラス例が明記）。特に：

* **`FOODON_00002501` = Multi‑component food product**（多成分＝**料理**寄り）
* **`FOODON_00002381` = Food product by organism**（単一生物由来＝**単素材食材**寄り）
  → これらを**祖先に持つかどうかで二群に分ける**と、あなたの `base_food`/`ingredients` の役割に直結します。【FoodOn SPARQL #1ページ中の例に両クラスが列挙されています。】([FoodOn][1])

補足として、FoodOn公式は**「food product」ブランチに約9,600の汎用カテゴリ**を持ち、**ブランドではなく一般的な食品カテゴリ**を目標にしていると明記しています（抽出結果が11,104件なのは派生や他分枝の取り込みによる超過があり得ます）【目的・規模の説明】。([FoodOn][2])

> **実装ヒント（owlready2）**
>
> * クラス`c`について `c.is_a` の祖先を再帰走査し、**`FOODON_00002501` 配下なら「ベース料理候補」**、**`FOODON_00002381` 配下なら「食材候補」**に振り分け。
> * FoodOnは**同義語TSV**（`foodon_synonyms.tsv`）を提供しています。ここから**preferred label＋同義語**を取り込み、**文字列の正規化**と**候補の重複排除**に使うのが最短です。([FoodOn][3])

### 属性・ファセットの扱い（“料理名の粒度を安定化”）

FoodOnは**LanguaLのファセット思想**を取り入れており、**調理法・部位・保存などは別軸の特性**として扱えます。**出力文字列は短く（料理名／食材名）**、調理法や部位は内部属性に持たせる設計が堅牢です（誤爆防止）。([FoodOn][4])

---

## 2) 頻度・汎用性による「CORE」選抜は **外部データで重み付け**

FoodOnに頻度は無いので、**公開コーパス**から統計を取り、**候補語にスコア**を与えます。信頼でき、かつ自動集計しやすいのは次の二系統です。

### A) Open Food Facts（OFF）で**流通頻度**（商品数）を取る

* **カテゴリ／食材のタクソノミ**とAPIがあり、**検索結果の`count`（ヒット件数）**を返します。**カテゴリ（例：orange‑juice）での製品数**を手早く取得でき、**“流通の多さ”の代理変数**になります。([Open Food Facts][5])
* OFFは**Ingredients/Global categoriesのタクソノミ**を公開しており、**同義語、階層、ストップワード**等の情報も持ちます。**原材料語の網羅性が高い**ので**ingredient候補の充実**にも有用です。([Open Food Facts][6])

**使い方**
`/api/v2/search?categories_tags_en=<category>` で検索し、`count`を取得 → **FoodOn候補（ベース料理/食材）に名称マッチ**させて**OFF製品数をスコアとして付与**します。([Open Food Facts][5])

### B) レシピ大型コーパスで**調理頻度**（登場回数）を取る

* **Recipe1M/Recipe1M+**：**100万超のレシピと1,300万画像**を収録した定番データセット。**レシピの原材料語彙**があり、**ingredients出現頻度**をカウントしやすい。([Recipe1M][7])
* **Vireo‑Food172**：**353食材アノテーション**付きで、**“料理カテゴリ×主要食材”の関係**が掴みやすい（補助的に有効）。([FVL Laboratory][8])

> **ポイント**
>
> * **ベース料理候補**には**OFFカテゴリの製品数**＋**Recipe1Mでの料理名ヒット数**を合算スコア化。
> * **食材候補**には**Recipe1Mのingredients頻度**＋**OFFの原材料出現**（Ingredientタクソノミ）を合算。
> * どちらも**FoodOn同義語（TSV）で正規化**→文字列一致率を上げる。([FoodOn][3])

---

## 3) 実務向け「CORE構築アルゴリズム」（サイズ目安：ベース料理 300–800、食材 500–1200）

### Step 0｜FoodOnから下ごしらえ

1. **FoodOnラベルと同義語**を`foodon_synonyms.tsv`から読み込む（ID, 親, ラベル, 同義語）。([FoodOn][3])
2. **二群分割**：

   * `Multi-component food product (FOODON_00002501)`配下 → **ベース料理候補**
   * `Food product by organism (FOODON_00002381)`配下 → **食材候補**
     ※ OWL上の**祖先に該当IDが存在するか**で判定。([FoodOn][1])
3. **ノイズ除去**：飲料用包装材や加工工程のみの語は除外（FoodOnの“food contact material”“food process”など**別ファセット**）。([FoodOn][2])

### Step 1｜頻度スコア付け

* **OFFスコア**：`/api/v2/search` の `count` を**カテゴリ／食材語**で取得 → `off_count`。([Open Food Facts][5])
* **レシピスコア**：Recipe1M(+)/Vireoなどから**料理名・食材名の出現回数**を集計 → `recipe_count`。([Recipe1M][7])

> **推奨スコア式（例）**
> `score = log(1 + off_count) * w_off  +  log(1 + recipe_count) * w_recipe  +  coverage_penalty`
>
> * **coverage_penalty**：FoodOn階層で**同じ親配下に同義語が密集**している場合に重複を抑えるための減点。
> * 初期重みは `w_off = 0.6`、`w_recipe = 0.4` から開始し、ABテストで最適化。

### Step 2｜しきい値 & 上限で CORE を確定

* **ベース料理**：上位から**300〜800件**を採用。**下位でも“カバーすべき定番”**（例：餃子、フォー等）は**ホワイトリスト**で補完。
* **食材**：上位**500〜1200件**。**ドレッシング／ソース類**は**OFF Ingredients**の語で網羅（例：croutons, chipotle sauce など市販頻出語）。([Open Food Facts][9])

### Step 3｜重複・同義語の正規化

* FoodOnの**preferred label**を**表示名**に採用し、**ID（FOODON_xxx）を内部キー**に。**同義語はサーチ用**に保持。([FoodOn][3])
* OFFタクソノミの**同義語・ストップワード**で**検索前正規化**（「chilli/chili」「tomatoes/tomato」等）。([Open Food Facts][6])

---

## 4) 仕分けルール（プロンプトに組み込みやすい文言）

* **ベース料理**＝`FOODON_00002501`系（多成分）、または「pizza/salad/soup/stew/curry/sandwich/rice…」等の**料理キーワード**。
* **食材**＝`FOODON_00002381`系（単素材）。チーズ・ソース・パン・野菜・肉の**一般名**を中心に。
* **曖昧なもの**は**FoodEx2の“Core/Extended＋ファセット”概念**を参考に、**上位語（NFS/NS）**に丸めてCORE側へ（FoodEx2は「**最低限の一般名はCore、細分類はExtended**」の考え方）。([European Food Safety Authority][10])

---

## 5) 具体的な「頻度付き」選抜の源データ（公開）

* **FoodOn**：**ラベル・親子・同義語**のTSVを提供（`foodon_synonyms.tsv`）。([FoodOn][3])
* **Open Food Facts**：**カテゴリ／食材のタクソノミ**と**API**。検索応答に**`count`（ヒット総数）**が含まれるため、**頻度指標に直結**。([Open Food Facts][5])
* **Recipe1M / Recipe1M+**：**100万超レシピ＋食材語彙**。ingredients頻度を抽出して**汎用性スコア**に。([Recipe1M][7])
* **Vireo‑Food172**：**353 ingredients付き**料理画像データ（**料理×食材**の併存チェックに便利）。([FVL Laboratory][8])

---

## 6) スクリプトへの落とし込み（設計メモ）

1. **祖先チェック**関数

   * `is_under(class, target_uri)` を実装し、`FOODON_00002501` / `FOODON_00002381` への**サブクラス連鎖**を判定（owlready2の`rdfs_subclassof`相当を再帰）。([FoodOn][1])
2. **同義語正規化**

   * `foodon_synonyms.tsv` を読み、**preferred label**↔**synonyms**辞書を構築。検索時は**小文字・記号除去**でマッチ。([FoodOn][3])
3. **頻度フェッチャ**

   * OFF APIでカテゴリ／食材検索→`count`取得。**レート制限対策**で**バッチ化＆キャッシュ**。([Open Food Facts][5])
   * Recipe1M(+)のingredientsをトークナイズ→**頻度辞書**生成。([Recipe1M][7])
4. **スコアリング**

   * `score = log1p(off_count)*0.6 + log1p(recipe_count)*0.4`。
   * 親子重複（例：*cheese* vs *cheddar cheese*）は**子に加点、親は残すが優先度を下げる**。
5. **COREの書き出し**

   * `base_food_core.txt`（FoodOn ID, 表示名, 同義語, 祖先, スコア）
   * `ingredient_core.txt`（同上）
   * 両方で**EXACT名**は**FoodOnのpreferred label**を採用（あなたの「厳密一致」条件を満たす）。

---

## 7) まとめ（Yes/Noで質問に回答）

* **Q. FoodOn内に「頻度・汎用性のラベル」はある？** → **いいえ。**FoodOnは**汎用カテゴリと語彙**を提供するオントロジで、**頻度は保持しません**【目的・設計】。([FoodOn][2])
* **Q. 頻度でCOREを選ぶ方法はある？** → **はい。**
  **Open Food FactsのAPI `count`**（流通頻度の代理）と、**Recipe1M(+)等のレシピ頻度**を組み合わせ、**FoodOn同義語で正規化**して**上位のみ採用**します。([Open Food Facts][5])
* **Q. ベース料理と食材はどう分ける？** → **FoodOnの階層**で
  **`FOODON_00002501`（多成分＝料理）**／**`FOODON_00002381`（単素材＝食材）** を祖先に持つかで分割するのが最も堅牢です。([FoodOn][1])

この方針に沿って抽出→頻度付与→上位採用を行えば、**“少数精鋭のEXACT_FOOD_LIST（CORE）”**を、FoodOn準拠・頻度順で安定運用できます。

[1]: https://foodon.org/reuse-project/reuse-technical/query-with-sparql/ "SPARQL #1: Basic Querying – FoodOn"
[2]: https://foodon.org/food-facets/food-product/ "Food product hierarchy – FoodOn"
[3]: https://foodon.org/reuse-project/reuse-technical/foodon-instant-formula/ "FoodOn Instant Formula – FoodOn"
[4]: https://foodon.org/design/foodon-and-langual/ "FoodOn and LanguaL – FoodOn"
[5]: https://openfoodfacts.github.io/openfoodfacts-server/api/tutorial-off-api/?utm_source=chatgpt.com "Tutorial on using the Open Food Facts API"
[6]: https://wiki.openfoodfacts.org/Global_categories_taxonomy?utm_source=chatgpt.com "Global categories taxonomy"
[7]: https://im2recipe.csail.mit.edu/im2recipe.pdf?utm_source=chatgpt.com "Learning Cross-modal Embeddings for Cooking Recipes ..."
[8]: https://fvl.fudan.edu.cn/dataset/vireofood172/list.htm?utm_source=chatgpt.com "Vireo-Food 172 dataset"
[9]: https://wiki.openfoodfacts.org/Ingredients_taxonomy?utm_source=chatgpt.com "Ingredients taxonomy"
[10]: https://www.efsa.europa.eu/en/data/data-standardisation "Food classification standardisation – The FoodEx2 system | EFSA"
