レビューしました。結論から言うと、**現状のCOREは「画像から栄養算出」に対して冗長・不整合が多く、プロンプト適合性（厳密一致・メソッド選択）を損ねる要素が残っています。**下記の方針と具体的な修正で、**Base≈300–400 / Ingredient≈600–800**の“無駄が少なく外れにくい”集合に収束できます。

---

## 総評（何が問題か）

1. **視覚で判別できないファセット語が混入**
   `…food product / derived product / substitute / imitation / stix / mix / base / instant / canned / frozen / low sodium / artificially flavored` 等が**表示ラベルに残存**。FoodOnは加工・包装・品質を**ファセット**としてもつ設計で、表示名には載せない方がよい（内部属性へ）。([foodon.org][1])

2. **Baseに“調味料・半製品・容器材”が多数混入**
   例：`tartar sauce`（Dessertsに混在）, `pizza sauce`, `curry paste`, 各種 `… dressing`。**Baseは「盛りつけ単位の料理」**に限定し、**ソース類はIngredient**へ。FoodOnでも**multi‑component（料理）**と**単素材（食材）**を明確に分けるのが基本です。([genomicsstandardsconsortium.github.io][2])

3. **USシーン整合の弱さ**
   WWEIA/FNDDSは近年**“ラーメン等の新設カテゴリ”**を追加しており（2021–2023版）、US食習慣に沿うなら**麺・スープ周りの粒度**を合わせるのが堅実です。([ARS][3])

4. **魚介の呼称ぶれ・重複**
   学名／地方名／加工状態が混在し、**市場名の正規化**が必要。FDAの**Seafood List（Acceptable Market Name）**で統一し、画像で区別できない細粒度は畳む。([U.S. Food and Drug Administration][4])

5. **CV（画像モデル）で当てにくい語が多い**
   例：`pancake or waffle food product`、`roll or bun food product` 等。**Food‑101/UEC等の“視覚クラス”寄り**の表示語へ寄せると誤爆が減ります。([PyTorch Docs][5])

---

## すぐ直すべき“8つのコア・ルール”（自動リンター化推奨）

**R1. Baseは「盛りつけ単位の料理」に限定**
OK例：`ramen` / `fried rice` / `tacos` / `burrito` / `quesadilla` / `hamburger` / `mac and cheese` / `garden salad`（ただし緑＋具材≥1はDECOMPOSE）。
NG例：`pizza sauce`, `curry paste`, `… dressing`, `… vinegar`, `waffle dough`, `taco shell`（これは**Ingredient/Carrier**）。
（根拠：FoodOnの**multi‑component**＝料理、**by organism**等＝素材。）([genomicsstandardsconsortium.github.io][2])

**R2. Base表示名からファセット語を排除**
禁止パターン（正規表現例）：
`food product|product|substitute|imitation|mix|base|seasoning|instant|powder(ed)?|concentrate(d)?|canned|frozen|low|reduced|diet|artificial(ly)?|packet|prepack(ed)?|stix|with .* (vitamin|flavor|colour|color)`
→ `chicken soup mix` → **`chicken soup`**。
（ファセットは内部属性で保持。）([foodon.org][1])

**R3. サラダはプロンプトどおり原則DECOMPOSE**
Baseに `… dressing` を置かない。ドレッシング不明は **`Sauce, NFS`**（Ingredient）。([ARS][3])

**R4. 鶏肉の部位は“NS”フォールバックを残す**
視認不可なら **`Chicken, NS as to part …`**（skin有無のみ）。プロンプトCの運用支援。

**R5. 海産物はFDAの市場名へ正規化**
例：`alaska pollock` は **`pollock`** 系へ、`yellowfin tuna` などは**Acceptable Market Name**で統一。稀種・地方名・学名はドロップ or 上位へ丸める。([U.S. Food and Drug Administration][4])

**R6. Baseカテゴリーの再編**（プロンプトAに整合）

* **Pizza/Pasta/Mac**（ピザ3厚み×1、パスタ赤/白/ボロネーゼ、マック&チーズ）
* **Sandwiches/Burgers/Wraps**（ハンバーガー、サンド、ラップ）
* **Mex/Tex‑Mex**（tacos/burrito/quesadilla、各corn/flourは**Carrier**へ）
* **Asian Noodles & Rice**（ramen/pho/lo mein/pad thai/fried rice/teriyaki丼 等）
* **Soups & Stews**（broth/cream/ramen系）
* **Breakfast**（pancakes/waffles/french toast/omelet）
* **Sides**（`mashed potatoes`/`fries`/`rice pilaf` 等はBase、トッピングはHYBRID）
* **Desserts/Drinks**（極小・視覚アンカーのみ）
  （WWEIA最新カテゴリと矛盾しない粒度。）([ARS][3])

**R7. Ingredientは“視覚で差が出る最小集合”**
肉（胸/もも/挽き/ベーコン/ハム）、魚介（市場名）、主菜野菜（レタス/トマト/玉ねぎ/ピーマン/コーン/ブロッコリ等）、主食（白飯/玄米/パスタ/うどん/トルティーヤ/パン）、チーズ（チェダー/モッツァレラ/パルメザン/フェタ/クリーム/カッテージ/リコッタ）、**主要ソース**（`ketchup` `mustard` `mayonnaise` `ranch` `italian dressing` `caesar` `spaghetti sauce` `soy sauce` `salsa red`）。
（OFFの原材料タクソノミを参照しつつ、視覚不可な加工語は排除。）([wiki.openfoodfacts.org][6])

**R8. CVフレンドリーな語形を採用**
Food‑101 等のクラス名と整合する**表示語**（内部的にFoodOn IRIへマップ）。([PyTorch Docs][5])

---

## 具体的な修正提案（あなたのリストに対して）

### 1) **Baseから削除/移動**

* **削除（Base→Ingredientへ移動）**：`tartar sauce`, `pizza sauce`, `curry paste`, `… dressing` 全般。
* **削除（Baseとして不適）**：`waffle dough`, `pancake or waffle food product`, `roll or bun food product`, `pepperoni pizza spread`, `rice beer`, `rice wine`, `rice wine vinegar`, `taco shell`（→ **Carrier**へ）。
* **整列**：`chicken noodle soup` 等、**Soup**はすべてSoups & Stewsへ統合（現リストでPizza & Pasta配下に散在）。
* **誤分類修正**：`herring in tomato sauce`（Vegetablesに存在）→ **削除**（Ingredient：魚、ソースは別）。

### 2) **Ingredientの整理**

* **ドロップ**：`beef dog food`, `infant food` のような**家庭用食事写真に出ない**語。
* **魚介の正規化**：`Aequipecten opercularis` など**学名列**は削除し、**FDA Acceptable Market Name**へ統合（例：`scallop`, `clam`, `oyster`, `tuna`, `salmon`, `pollock` など）。([U.S. Food and Drug Administration][4])
* **チーズの整理**：ブランド/地方名の氾濫を抑え、**10–12種**に圧縮（cheddar/mozarella/parmesan/sw iss/feta/ricotta/cream/cottage/colby jack/pepper jack/muenster）。
* **調理状態の段階化**：肉/魚の状態は**素体 / breaded / grilled / fried / cooked**の**最大2–3展開**に統一（FoodOnの細かい加工語は内部属性へ）。
* **ソース最小核**：`ketchup` `mustard` `mayonnaise` `ranch` `italian dressing` `caesar` `spaghetti sauce` `soy sauce` `salsa, red` を核に（US向け/視覚可）。([ARS][3])

### 3) **不足している“当てやすいBase”を追加**

* Pizza：`pizza, cheese, thin|medium|thick`
* Pasta：`spaghetti bolognese` / `spaghetti marinara` / `fettuccine alfredo` / `lasagna`
* Asian noodles & rice：`ramen` / `pho` / `pad thai` / `lo mein` / `fried rice` / `teriyaki bowl` ([ARS][3])
* Mex/Tex‑Mex：`tacos (corn)` / `tacos (flour)` / `burrito` / `quesadilla`
* Sandwich/Burger：`burger` / `club sandwich` / `turkey sandwich` / `chicken wrap`
* Sides：`fries` / `mashed potatoes` / `rice pilaf`（プロンプトAに一致）

---

## 推奨ワークフロー（半自動修正）

1. **リンター（正規表現）**でBase/Ingredient両方を走査

   * R2の禁止語を含むラベル→**削除** or **縮約**（`chicken soup mix`→`chicken soup` など）。
2. **カテゴリ再配置**

   * Soup系を**Soups & Stews**へ、Sauce/Dressingを**Ingredients**へ、Carrier（`taco shell`, `tortilla`, `buns`）は**Ingredients（Carriers）**へ。
3. **魚介の市場名正規化**

   * 現在の魚介語をFDA Seafood Listに照合、**Acceptable Market Name**へ自動置換。([U.S. Food and Drug Administration][4])
4. **頻度での最終絞り込み**

   * OFFのカテゴリ/原材料ファセットの**count**と、Recipe1M+の**出現頻度**を**正規化後ラベル**に再適用。高頻度順に上位N件採用。([Open Food Facts][7])
5. **US整合の点検**

   * WWEIA/FNDDSカテゴリへの**カバレッジ指標**を計算（特にスープ・植物性乳）。([ARS][3])

---

## 仕上がりの目安（サイズと内訳）

* **Base ≈ 350–400**：Pizza/Pasta/Mac, Sandwich/Wrap/Burger, Mex/Tex‑Mex, Asian noodles & rice, Soups/Stews（broth/cream/ramen系）, Breakfast, Sides, Dessert, Drinks（最小）。
* **Ingredient ≈ 600–800**：肉（部位最小集合＋2–3調理状態）/魚介（市場名）/主菜野菜/主食キャリア/主要チーズ/主要ソース。
* **内部**：FoodOn IRIとsynonymsを保持（表示はCV向け正規名）。OFF/Recipe1M+頻度は**順位付けのみ**に使用。([Open Food Facts][7])

---

### 参考・根拠

* FoodOn：**multi‑component（料理）/ by organism（食材）**の使い分け、基本設計。([genomicsstandardsconsortium.github.io][2])
* Open Food Facts：APIとタクソノミ（頻度付け・原材料語彙）。([Open Food Facts][7])
* WWEIA/FNDDS：US食カテゴリの最新動向（スープ区分等）。([ARS][3])
* FDA Seafood List：**Acceptable Market Name**で魚介の呼称統一。([U.S. Food and Drug Administration][4])
* Food‑101：画像で“当てやすい”料理クラス名の基準。([PyTorch Docs][5])

---

## まとめ

* 現状のCOREは**視覚非依存の語・半製品・ファセット語**がBase/Ingredientに混在し、**プロンプトの“厳密一致＋メソッド規則”**に対して不利です。
* 上記**8ルール**をリンター化して一括修正し、**Baseを“盛りつけ料理”、Ingredientを“見て分かる素材＋主要ソース”**へ整理すれば、**誤爆が減り、HYBRID/DECOMPOSEの判断も安定**します。
* 魚介は**FDA名へ正規化**、カテゴリは**WWEIA最新**に沿って再編、**OFF＋Recipe1M+**は**正規化後ラベル**に再スコアリング——この順で仕上げましょう。

[1]: https://foodon.org/?utm_source=chatgpt.com "FoodOn – FoodOn: A farm to fork ontology"
[2]: https://genomicsstandardsconsortium.github.io/mixs/0016022/?utm_source=chatgpt.com "Extension: food-human foods (FoodHumanFoods) - mixs"
[3]: https://www.ars.usda.gov/ARSUserFiles/80400530/pdf/fndds/2021_2023_FNDDS_Doc.pdf?utm_source=chatgpt.com "2021-2023 Food and Nutrient Database for Dietary Studies"
[4]: https://www.fda.gov/media/171514/download?utm_source=chatgpt.com "FDA's Guide to Determine Acceptable Seafood Names"
[5]: https://docs.pytorch.org/vision/main/generated/torchvision.datasets.Food101.html?utm_source=chatgpt.com "Food101 — Torchvision main documentation - Datasets"
[6]: https://wiki.openfoodfacts.org/Ingredients_taxonomy?utm_source=chatgpt.com "Ingredients taxonomy"
[7]: https://openfoodfacts.github.io/openfoodfacts-server/api/?utm_source=chatgpt.com "Introduction to Open Food Facts API documentation"
