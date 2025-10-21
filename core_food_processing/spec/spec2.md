了解しました。最新の公開情報を確認したうえで、**FoodOnを起点にした“Base food（料理）”と“Ingredient（食材）”のCORE構築方針**をアップデートします。

---

## 1) Webで確認できる事実（要点）

* **FoodOnの基幹分岐**
  FoodOnは「food product」分岐の下に、

  * **food product by organism**（= 単一原料系の“食材”アンカー）← *foodon:00002381*
  * **multi‑component food product**（= 複合料理の“ベース料理”アンカー）← *foodon:00002501*
    を明示しており、FoodOn公式のSPARQL例でもこの2軸が“~single component food / multi‑component food”として掲示されています。([FoodOn][1])

* **「food product by organism (FOODON:00002381)」は現行でも利用されている**
  CDNOやFoodKGなど、近年の論文・プロジェクトが 00002381 を「食材（生物起源別）」の基点として参照しています。**obsolete扱いではありません**（あなたのローカルOWLで0件だったのは、版差・依存インポート未解決・Reasoner設定等の可能性が高いです）。([OBO Foundry][2])

* **“food material / harvested food material”は補助的ファセット**
  FoodOnの設計文書では“food material/harvested food material”は収穫状態などの**ファセット**で、主たる「食材名」集合は**food product by organism＋part of organism**側で取り扱うのが基本です。([FoodOn][3])

* **動物性・植物性の上位クラス**
  例：**animal food product** (*FOODON:00004242*) などの上位カテゴリも現行で有効。食材集合の整列に使えます。([ols.monarchinitiative.org][4])

* **頻度・汎用性の外部根拠**

  * **Open Food Facts (OFF)**：カテゴリ／原材料タグの**ファセット検索**で件数を取得可能（無償・CC‑BY‑SA／オープンAPI）。([Open Food Facts][5])
  * **Recipe1M+**：**100万超レシピ＋1300万画像**の公開データで、食材出現回数や料理名の頻度推定に最適。([MIT CSAIL People][6])
  * **USDA FNDDS / WWEIAカテゴリ**：米国食習慣に沿った**172カテゴリ**の粒度を与える“消費側の枠組み”（頻度データそのものではないが、北米向けダイエットアプリの整合性に有用）。([ARS][7])

---

## 2) 改訂版・実装方針（確定版）

### A. クラスの出発点（正規化ポリシー）

* **Base food（料理）候補**

  * ルート：**multi‑component food product** (*FOODON:00002501*) の**子孫**。
  * ただし「加工工程の記述だけ」や「容器・保存状態等のファセットに偏った語」は除外（*has quality / food production*系のみで規定される語を除外）。([FoodOn][8])

* **Ingredient（食材）候補**

  * ルート：**food product by organism** (*FOODON:00002381*) の**子孫**。
  * 併せて **part of organism** ファセット（部位・可食部位）で“肉の部位・葉・根菜”等を補完。
  * 動物・植物などの上位（例：*animal food product*）を**正規化の親**として採用し、食材集合のカバレッジ検証に使用。([FoodOn][9])

> 注：ローカルOWLで 00002381 配下が空になる場合は、**最新リリース（2025‑06‑07版等）**を取得し、**インポート解決**と**reasoning**を有効にして再試行してください。([ontobee.org][10])

---

### B. スコアリング（頻度×汎用性）

**目的**：BaseとIngredientの候補 > 上位N件に絞ってCOREを構築（目安：Base 500–800、Ingredient 800–1200）

1. **外部頻度の集計**

   * **Open Food Facts**

     * *facet* APIでカテゴリ・原材料の**ヒット件数**を取得（例：`facets=categories,ingredients&nocache=1`）。
     * 地域フィルタ（`countries=United States`）や言語も考慮。([Open Food Facts][11])
   * **Recipe1M+**

     * **食材トークン頻度**、**料理タイトルのn‑gram頻度**、**画像ラベル（クラスタ）頻度**を算出。([MIT CSAIL People][6])
   * （任意）**FNDDS/WWEIA**

     * 172カテゴリへ**マッピング率**を評価指標として加点（“米国消費シーン適合度”）。([ARS][7])

2. **スコア式（実装容易・再現性重視）**

   ```
   score = 0.5 * log1p(OFF_count) 
         + 0.4 * log1p(Recipe1M_count) 
         + 0.1 * WWEIA_coverage (0/1)
   ```

   * “料理”はRecipe1M寄与を、**“食材”はOFF寄与**をやや強めに重み付けすると実運用で安定。

3. **サニティフィルタ**

   * **語の具体性**：上位語（“meat product”, “vegetable food product”のような汎概念）は除外、**最下位付近の過細粒度**（例：固有野草・地域限定魚介）も外す。
   * **画像認識実用性**：**視覚的に識別しやすい**名称を優先（例：*romaine lettuce* > “leafy greens (general)”）。
   * **重複・同義語**：FoodOnの *hasExactSynonym / hasRelatedSynonym* を使い、**代表ラベル**へ正規化。([AgroPortal][12])

---

### C. “Base food vs Ingredient”の線引きルール

* **Base food** = 皿/器単位・調理集合を表す語（例：pizza, burger, stir‑fry, salad, curry, stew, taco/burrito, ramen, fried rice 等）。
  → FoodOnの multi‑component subtrees を優先抽出。([FoodOn][1])

* **Ingredient** = 生物起源×部位×加工最小の語（例：*chicken thigh*, *salmon fillet*, *romaine lettuce*, *potato (whole)*, *onion*）。
  → 00002381配下＋part‑of‑organismで正規化。([FoodOn][9])

---

### D. 生成物（CORE）構成・粒度

* **Base**：~600語

  * ピザ/パスタ/バーガー/丼・麺/アジア系米麺/メキシカン/カレー/スープ/サラダ/朝食（パンケーキ等）/デザート/飲料の**実メニュー系**を中心に。
* **Ingredient**：~1000語

  * 肉（部位別）・魚介（種別/加工）・野菜（作物別/葉茎根）・穀類/豆類・チーズ/乳製品・ソースの**単体**。
* **同義語辞書**（検索用）

  * FoodOnの**同義語注釈**とRecipe1Mの頻出表記を併合して**マッピング表**を出力（UI検索/曖昧同定に使用）。([AgroPortal][12])

---

### E. 推奨パイプライン（実装順）

1. **FoodOn最新OWL取り込み**（2025‑06‑07版等）。**Reasoner有効**・**インポート解決**。([ontobee.org][10])
2. **候補抽出**

   * Base：`descendants(FOODON:00002501)`
   * Ingredient：`descendants(FOODON:00002381)` ＋ `part of organism` 関連の*label*を付加。([FoodOn][1])
3. **外部頻度付与**

   * OFF facets件数をバッチ取得（カテゴリ・原材料・国/言語フィルタ）。([Open Food Facts][11])
   * Recipe1M+でタイトル/食材頻度を算出。([MIT CSAIL People][6])
4. **スコアリング→上位N件選抜**（Base/Ingredient別に閾値最適化）。
5. **サニティチェック**

   * 視覚識別性、重複・同義語、粒度のばらつき、WWEIAカテゴリ・カバレッジ確認。([ARS][7])
6. **CORE出力**

   * 「表示名（FoodOnラベル）／内部ID（IRI）／上位カテゴリ／同義語／外部頻度」付きでエクスポート。
   * VLM用の**“NFS/NSフォールバック名”**は別テーブルに明示し、**プロンプトのSTRICT NAME COPY**を崩さずに網羅性を担保。

---

### F. 既存プロンプトとの整合

* これまでの「USE_AS_IS / HYBRID / DECOMPOSE」運用はそのまま活かせます。
* **ベース**は *multi‑component* 由来語、**追加トッピング**は *Ingredient* 由来語、**DECOMPOSE**は *Ingredient* 群のみ――という役割分担に一本化すると、**過分解の抑制**と**名称のぶれ抑制**が両立します（FoodOnの“has ingredient / has defining ingredient”関係とも整合）。([FoodOn][8])

---

## 3) よくある落とし穴と回避策

* **00002381が空になる**
  → FoodOnの**版差**や**インポート未解決**が原因のことが多いです。FoodOn公式サイトのSPARQL例では現行でも有効なことが明示されています。最新版へ切替・依存解決を。([FoodOn][1])

* **食材名が汎すぎ／細かすぎ**
  → OFF・Recipe1Mの頻度で**閾値**を設け、上位語/希少語を落とす。WWEIAカテゴリとの**二軸チェック**で米国利用に偏りを持たせる。([Open Food Facts][11])

* **北米ローカライズ**
  → WWEIAカテゴリに**最低1カテゴリ以上対応**・OFFの`countries=United States`での件数を併記。([ARS][13])

---

## 4) まとめ（提案の要点）

* **FoodOnの正攻法**は
  **Base**＝*multi‑component food product*、**Ingredient**＝*food product by organism (+ part of organism)*。
  これはFoodOn自身の公開クエリ記述とドキュメントに沿う最新仕様で、**obsoleteではありません**。([FoodOn][1])

* **頻度×汎用性**は**Open Food Facts**＋**Recipe1M+**を核に、**WWEIAカテゴリ**で米国食の整合を取り、スコアで上位をCORE化。([Open Food Facts][11])

* **同義語・表記ゆれ**はFoodOnの**synonym注釈**を一次ソースに正規化。([AgroPortal][12])

この方針で、既存のプロンプト設計（STRICT NAME COPYと分析メソッドの三択）にそのまま適用できます。必要であれば、スコア計算・フィルタ規則をコード化した疑似SQL/擬似Pythonの雛形もすぐに用意します。

[1]: https://foodon.org/reuse-project/reuse-technical/query-with-sparql/?utm_source=chatgpt.com "SPARQL #1: Basic Querying"
[2]: https://obofoundry.org/ontology/cdno.html?utm_source=chatgpt.com "Compositional Dietary Nutrition Ontology"
[3]: https://foodon.org/design/foodon-structure/?utm_source=chatgpt.com "FoodOn Structure"
[4]: https://ols.monarchinitiative.org/ontologies/mondo/classes/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FFOODON_00004242?lang=en&utm_source=chatgpt.com "FOODON:00004242"
[5]: https://openfoodfacts.github.io/openfoodfacts-server/api/?utm_source=chatgpt.com "Introduction to Open Food Facts API documentation"
[6]: https://people.csail.mit.edu/jmarin/docs/tpami19.pdf?utm_source=chatgpt.com "Recipe1M+: A Dataset for Learning Cross-Modal Embeddings ..."
[7]: https://www.ars.usda.gov/ARSUserFiles/80400530/pdf/fndds/2021_2023_FNDDS_Doc.pdf?utm_source=chatgpt.com "2021-2023 Food and Nutrient Database for Dietary Studies"
[8]: https://foodon.org/design/foodon-relations/?utm_source=chatgpt.com "FoodOn Relations"
[9]: https://foodon.org/food-facets/part-of-organism/?utm_source=chatgpt.com "Part of organism facet"
[10]: https://ontobee.org/ontology/foodon "Ontobee: foodon"
[11]: https://wiki.openfoodfacts.org/API/Read/Search?utm_source=chatgpt.com "API/Read/Search"
[12]: https://agroportal.lirmm.fr/ontologies/FOODON?utm_source=chatgpt.com "FOODON | Summary - AgroPortal"
[13]: https://www.ars.usda.gov/northeast-area/beltsville-md-bhnrc/beltsville-human-nutrition-research-center/food-surveys-research-group/docs/dmr-food-categories/?utm_source=chatgpt.com "DMR - Food Categories"
