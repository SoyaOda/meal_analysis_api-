ありがとうございます。提示いただいた**最終成果物（BASE600 / INGREDIENTS1000）**は、FoodOn＋OFF頻度の自動抽出としては良い出発点ですが、**画像解析での“厳密一致”運用にはそのままでは合いません**。理由は主に：

* FoodOn用語には**加工状態・包装・品質ファセット**（powdered / canned / artificially flavored / low‑sodium など）が大量に含まれ、**視覚で識別できない差分**がラベルに混入しやすい（＝プロンプトの“EXACT文字列”に向かない）。FoodOn自身が、食品を**本体（single / multi‑component）とファセット**に分ける設計であることを明言しています。([foodon.org][1])
* FoodOnには**multi‑component food product (FOODON:00002501)** と **food product by organism (FOODON:00002381)** の2軸があり（例示付きの公式SPARQLに明記）、**前者は“料理”、後者は“食材”の母集団**です。抽出はこの2軸を軸にし、**ファセット語（加工・包装・品質）はCOREラベルから外す**のが適切です。([foodon.org][2])
* 頻度付けに使える外部ソースは存在しますが（**Open Food Facts API**のファセット件数、**Recipe1M+**のレシピ／食材頻度）、**そのまま文字列転写すると製造・包装寄りの語が上位に来やすい**ため、**“視覚で区別できる正規名”への正規化**が必須です。([Open Food Facts][3])
* “料理名”は**Food‑101 / UEC‑Food256 / Vireo‑Food172**のような**画像認識ベンチマークのクラス名**を下支えにすると、**視覚的に当てやすい粒度**に揃えやすいです。([TensorFlow][4])

---

## 改訂方針（現行Web情報に基づく、プロンプト適合版）

### 0) 骨子（変えない前提）

* **Base food**＝**multi‑component food product (FOODON:00002501)** の子孫、
  **Ingredient**＝**food product by organism (FOODON:00002381)** の子孫。([foodon.org][2])
* **同義語の正規化**には FoodOn 提供の **`foodon_synonyms.tsv`** を一次ソースに使う。([foodon.org][5])

---

### 1) 「画像で判別できる正規名」への**強制正規化ルール**

**A. ファセット語はCOREラベルから除去**（内部属性へ）

* 除外（例）：`powdered|concentrate|artificially flavored|low sodium|reduced fat|canned|frozen|pasteurized|instant|mix|base|seasoning|broth base|shelf stable|dehydrated` など。
* 根拠：FoodOnは**ファセット（加工・包装・品質等）**を別軸として定義しており、**ベースの食名とは切り分ける**べき、という設計。([foodon.org][1])

**B. 視覚アンカーのないラベルは落とす**

* 例：`beverage (aromatized, wine-based)`, `alcoholic beverage (powdered)` → 外す。
* 代替：`beer`, `wine, red|white`, `soft drink, NFS`, `tea, iced, unsweetened` のような**視覚で区別しやすい上位語**だけ採用（飲料は限定集合に）。

**C. 同意義バリエーションの縮約**

* 例：`ice cream (artificially flavored)`, `ice cream (lowfat)` → **`ice cream`** に統一。
* 例：`shrimp (raw|cooked|frozen|breaded...)` → **ingredients側**は **`shrimp`** と **`shrimp, breaded`** 程度に**2–3段階**へ集約。
* 目的：**厳密一致**を維持しつつ、**VLMが選びやすい少数の代表語**に寄せる。

**D. 料理名の粒度をCV準拠に**

* **Food‑101 / UEC / Vireo**のクラスを“許容表示名”の候補に採用（例：`spaghetti bolognese`, `ramen`, `tacos`, `fried rice`, `sushi`, `pizza margherita`, `waffles`等）。**FoodOnの該当語へ紐付け**（内部ID保持）して、**表示はCVフレンドリーな語**に。([data.vision.ee.ethz.ch][6])

---

### 2) スコアリング（頻度×汎用性）— ただし**視覚正規化の後に**適用

1. **Open Food Facts**：カテゴリ／原材料ファセットの**件数（count）**で流通頻度の代理値を取得。([Open Food Facts][3])
2. **Recipe1M+**：レシピタイトル・ingredients出現回数で**調理頻度**を付与。([arXiv][7])
3. （任意）**米国の食習慣枠**を補助指標に（WWEIAカテゴリへのカバレッジ）。([Open Food Facts][8])

> **推奨式**
> `score = 0.5*log1p(OFF_count) + 0.5*log1p(Recipe_count)`
> ※ 飲料や加工品はOFF寄り、料理はRecipe1M+寄りに重みを微調整。

---

### 3) コア語彙の**サイズと内訳**（プロンプト親和）

* **Base foods（~350–500語）**

  * ピザ/パスタ/マック&チーズ/サンド/バーガー/丼・麺/炒飯・カレー/メキシカン（タコ/ブリトー/ケサディーヤ）/スープ/サラダ/朝食/サイド（`mashed potatoes`, `fries`, `rice pilaf` など）/デザート/飲料（極少数）。
  * 例：`spaghetti bolognese`, `ramen`, `fried rice`, `tacos (flour)`, `burrito`, `quesadilla`, `pizza, cheese, thin`, `lasagna`, `mac and cheese`, `hamburger`, `chicken katsu`, `sushi roll, california`, `clam chowder`, `garden salad`, `mashed potatoes`, `rice pilaf`, `soft drink, NFS`, `tea, iced, unsweetened`, `beer`, `wine, red`.（FoodOn IDにマップ）

* **Ingredients（~600–900語）**

  * たんぱく（部位別・代表加工2～3段階）、野菜（作物名中心）、穀類・豆、チーズ種、主要ソース（`ketchup`, `mayonnaise`, `ranch`, `salsa` 等）。
  * 例：`chicken thigh`, `chicken breast`, `beef, ground`, `pork chop`, `salmon`, `shrimp`, `egg`, `romaine lettuce`, `tomato`, `onion`, `potato`, `rice, cooked`, `black beans`, `cheddar cheese`, `parmesan`, `croutons`, `ranch dressing`, `spaghetti sauce`（OFFタクソノミで食材名を補完）。([Open Food Facts][9])

> **重要**：加工状態（`canned/frozen/low‑fat`等）は**内部属性**で保持し、**表示名には出さない**。これはFoodOnの**ファセット**設計に沿います。([foodon.org][1])

---

### 4) 自動フィルタの具体規則（実装向け）

**(A) 除外ストップワード**（BASE/INGR共通・表示名から排除）
`powder|mix|base|seasoning|artificial|low|reduced|diet|concentrate|instant|dehydrated|freeze-dried|pasteurized|canned|frozen|packet|shelf stable|prepacked|ready-to-bake|with.*(vitamin|flavor|colour)` …
→ 例：`ice cream (artificially flavored)` → **`ice cream`**、`chicken soup mix` → **`chicken soup`**。

**(B) 料理・食材の分岐**

* **BASE**：`descendants(FOODON:00002501)` の **正規化後**ラベル。
* **INGR**：`descendants(FOODON:00002381)` の **正規化後**ラベル（＋組織部位）。([foodon.org][2])

**(C) 視覚アンカー判定**

* `soup|stew|curry|pizza|pasta|noodle|ramen|rice|taco|burrito|quesadilla|salad|burger|sandwich|fries|dumpling|roll|waffle|pancake|omelet|kebab|skewer` 等を**肯定辞書**に。
* `sauce|dressing` は**ingredients側**（HYBRID/DECOMPOSEで付与）。

**(D) 同義語統合**

* FoodOnの**synonyms.tsv**を利用し、**preferred label**に正規化。([foodon.org][5])

**(E) CVクラス補強**

* Food‑101/UEC/Vireo の**クラス名を白名簿**として、FoodOnラベルに**マッピング**（足りない料理名の救済）。([data.vision.ee.ethz.ch][6])

---

### 5) 品質保証（プロンプト整合チェック）

* **一意文字列**：出力させる`item_name`は**この正規化後CORE**のみ。未知語→**NFS/NSフォールバック**へ。
* **BASE優先＋HYBRID最小**：ピザ/パスタ/タコス/標準サイドは**USE_AS_IS**。可視トッピングのみ**HYBRID**（プロンプト規則A/D）。
* **SALADはDECOMPOSE**（greeny＋具材1つ以上）— ドレッシング不明は **`Sauce, NFS`**（プロンプト規則B）。
* **POULTRYの部位**：不明時は **`Chicken, NS as to part ...`**（プロンプト規則C）。
* **複数同一ユニット**：**`unit_count`**で集約（プロンプト規則E）。
  ※ 料理／食材の区分と“追加トッピングのみ”原則は、FoodOnの**has ingredient**関係の設計とも整合します。([foodon.org][10])

---

## 典型NG→OKの例（今回の成果物から）

* **NG**: `ice cream (artificially flavored)` → **OK**: `ice cream`（BASE/INGRのどちらにも可、通常はデザートBASE）
* **NG**: `chicken soup mix (instant)` → **OK**: `chicken soup`（BASE）
* **NG**: `shrimp (raw, peeled, deveined, frozen)` → **OK**: `shrimp`（INGR）
* **NG**: `mayonnaise (low calorie)` → **OK**: `mayonnaise`（INGR）
* **NG**: `beverage (aromatized, wine-based)` → **OK**: `wine, red` / `wine, white` / `soft drink, NFS`（BASEではなく**飲料カテゴリ限定集合**）

---

## 最終アウトプットの目安

* **BASE**：350–500語（CVクラス＋FoodOnマップ中心、視覚アンカー有り）
* **INGR**：600–900語（部位・代表加工を2–3段階に縮約、ソースは必要最小限）
* **内部**：FoodOn IRI / preferred label / synonyms / FACET属性（包装・加工・脂肪分等）

> FoodOnは**“9,600+の汎用カテゴリを提供し、ブランドではなく一般カテゴリを目指す”**と明記。ここを背骨に、**ファセットを表示名から外す**・**CVクラスで補強**・**OFF/Recipe1M+で頻度順位を付ける**、というのが**現行最適**です。([foodon.org][11])

---

### 参考（根拠・利用元）

* FoodOn SPARQL例：**00002381（single component）/ 00002501（multi‑component）**の根拠。([foodon.org][2])
* FoodOn **synonyms.tsv**（正規化に必須）。([foodon.org][5])
* FoodOnの**ファセット設計**とLanguaLとの対応。([foodon.org][1])
* FoodOnの目的・規模（**9,600+汎用カテゴリ**）。([foodon.org][11])
* **Open Food Facts API/タクソノミ**（外部頻度）。([Open Food Facts][3])
* **Recipe1M+**（レシピ・食材頻度）。([arXiv][7])
* **Food‑101 / UEC‑Food256 / Vireo‑Food172**（視覚的に当てやすい料理名）。([data.vision.ee.ethz.ch][6])

---

### まとめ

* **はい、現状のリストはプロンプト適合性に欠けます。**
* **解決策**は、FoodOnの**multi‑component / by organism**を軸に抽出し、**ファセット語を表示名から排除**→**CVクラスで料理名を補強**→**OFF/Recipe1M+で頻度順位**→**BASE 350–500 / INGR 600–900の厳密集合**を作ることです。
* これにより、**“EXACT_FOOD_LIST（CORE）”へ厳密一致**しつつ、**画像から選びやすい名称だけ**にできます。

[1]: https://foodon.org/food-facets/?utm_source=chatgpt.com "Food Facets"
[2]: https://foodon.org/reuse-project/reuse-technical/query-with-sparql/?utm_source=chatgpt.com "SPARQL #1: Basic Querying"
[3]: https://openfoodfacts.github.io/openfoodfacts-server/api/?utm_source=chatgpt.com "Introduction to Open Food Facts API documentation"
[4]: https://www.tensorflow.org/datasets/catalog/food101?utm_source=chatgpt.com "food101 bookmark_border - Datasets"
[5]: https://foodon.org/reuse-project/reuse-technical/foodon-instant-formula/?utm_source=chatgpt.com "FoodOn Instant Formula"
[6]: https://data.vision.ee.ethz.ch/cvl/datasets_extra/food-101/?utm_source=chatgpt.com "Food-101 -- Mining Discriminative Components with ..."
[7]: https://arxiv.org/abs/1810.06553?utm_source=chatgpt.com "Recipe1M+: A Dataset for Learning Cross-Modal Embeddings for Cooking Recipes and Food Images"
[8]: https://wiki.openfoodfacts.org/Data_fields?utm_source=chatgpt.com "Data fields - Open Food Facts wiki"
[9]: https://wiki.openfoodfacts.org/Ingredients_taxonomy?utm_source=chatgpt.com "Ingredients taxonomy"
[10]: https://foodon.org/design/foodon-relations/?utm_source=chatgpt.com "FoodOn Relations"
[11]: https://foodon.org/?utm_source=chatgpt.com "FoodOn – FoodOn: A farm to fork ontology"
