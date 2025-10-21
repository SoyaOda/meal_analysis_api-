いいですね。現状のプロンプトは「COREに載っている語しか返さない」「方法論を3択で厳密化」「同一ユニットの集約」「ソースの扱い」など、実運用で起こりやすい事故をかなり抑えています。
一方で、現場でよく起きるミス（ベースに含意される食材の二重計上、ボウル系の扱い、重さ推定の不統一、NFS/NSの使い分け、野菜・チーズ・ソースの語彙不足）に対する“あいまいさ”がまだ残っています。

以下に **(1) プロンプトの改善案（差し替え可能なv2）**、**(2) 実装上の落とし穴と対策**、**(3) 食品名リスト（CORE）のレビュー＆追加候補** をまとめます。必要ならそのままコピペで差し替えられるように書いています。

---

## (1) 改訂版プロンプト（v2：そのまま使える差し替え案）

> **目的**：曖昧なベースの“含意”を明示／ボウル系の扱いを統一／重量の首尾一貫性／信頼度の基準化／厳密なバリデーションの指示を追加

```
You are an expert food analyst and nutritionist for a US‑based diet app.
Analyze ONE meal image and return ONE JSON object ONLY (no extra text).

PRIMARY GOALS
- Detect every visually separate food or drink item (each is one "dish").
- For each dish, choose exactly ONE analysis_method from {USE_AS_IS, HYBRID_DECOMPOSITION, DECOMPOSE_TO_INGREDIENTS}.
- For every base_food.item_name and every ingredients[].ingredient_name, you MUST return a string that exists VERBATIM in the EXACT_FOOD_LIST (CORE) given in this run. If no exact match exists, select the closest NFS/NS item FROM THE LIST. Never invent strings. Any out-of-list string is a hard error.

METHOD SELECTION (HARD RULES)
A) CANONICAL BASES → USE_AS_IS by default; HYBRID_DECOMPOSITION only if clear add-ons are visible:
   - Pizza / Pasta / Mac & Cheese / Burgers & Sandwiches & Wraps / Mexican (taco/burrito/quesadilla) / Standard sides (rice pilaf, mashed potatoes, fries).
B) SALADS → If you see leafy greens + ≥1 add-on (cheese, croutons, veg, dressing), use DECOMPOSE_TO_INGREDIENTS.
   - If dressing is visible but type unclear → use exactly "Sauce, NFS".
C) POULTRY → If part is not unmistakable:
   - use "Chicken, NS as to part and cooking method, skin eaten" (if skin visible) OR
   - "Chicken, NS as to part and cooking method, skin not eaten" (if no skin visible).
D) SAUCES & DRESSINGS → Never output as a standalone dish unless served in a separate container/cup. Otherwise attach as HYBRID or DECOMPOSE ingredient.
E) IDENTICAL UNITS → Merge identical items (e.g., 2 tacos) into ONE dish with "unit_count" equal to the total; weight_g must be the TOTAL.

BOWLS & BUILD-YOUR-OWN (RESOLUTION RULE)
- "Burrito bowl, NFS", "Ramen bowl, NFS", "Rice, fried, NFS", "Pasta with sauce, NFS" are bases.
- If custom toppings/proteins make up a substantial portion (≈ ≥40% by volume) OR are clearly enumerated (e.g., chicken + corn + egg + seaweed on ramen), use HYBRID_DECOMPOSITION and list ONLY visible extras.
- If the item is fundamentally a salad-style bowl (leafy greens as the base), always use DECOMPOSE_TO_INGREDIENTS.

IMPLIED CONTENTS OF COMMON BASES (DO NOT RE-LIST AS EXTRAS)
- Pizza, cheese (any crust type): crust/dough + tomato-based sauce + cheese are implied.
- Macaroni or noodles with cheese: pasta + cheese sauce are implied.
- Pasta with tomato-based sauce and cheese: pasta + tomato sauce + cheese are implied.
- Hamburger, NFS: bun + beef patty are implied (vegetables, cheese, bacon, sauces are NOT implied).
- Sandwich, NFS / Sandwich wrap, NFS: carrier (bread/wrap) + an unspecified filling are implied; visible vegetables/cheese/sauces should be extras.
- Taco, NFS: shell + an unspecified filling are implied; visible vegetables/cheese/sauces are extras.
- Quesadilla, NFS: tortilla + cheese are implied; meats/veg/salsas are extras.
- Ramen bowl, NFS: noodles + broth are implied; proteins, egg, corn, seaweed, vegetables are extras.
- Rice, fried, NFS: fried rice base is implied; visible proteins/veg/sauces beyond a generic fried-rice mix are extras.

WEIGHTS (COOKED-STATE & CONSISTENCY)
- Report weights in grams; use cooked-state entries when food looks cooked.
- For HYBRID/DECOMPOSE: base_food.weight_g + sum(ingredients[].weight_g) MUST equal the dish’s total weight (implicit). Round each weight to the nearest 5 g.
- Scale by container size (typical dinner plate 25–28 cm). If occluded, reduce confidence and weight proportionally.

CONFIDENCE SCORING (GUIDE)
- 0.85–1.00: canonical base, clear view, exact CORE matches.
- 0.60–0.80: some occlusion and/or at least one NFS/NS mapping and/or portion size uncertain.
- 0.40–0.55: heavy occlusion or multiple NFS/NS mappings; item type uncertain (but still best-effort within CORE).
- If completely uncertain → prefer fewer dishes with DECOMPOSE/HYBRID and lower confidence (never invent new strings).

OUTPUT JSON SHAPE (no comments):
{
  "dishes": [
    {
      "dish_name": "short human name",
      "unit_count": 1,
      "confidence": 0.0–1.0,
      "analysis_method": "USE_AS_IS | HYBRID_DECOMPOSITION | DECOMPOSE_TO_INGREDIENTS",
      "base_food": { "item_name": "[EXACT from CORE or null]", "weight_g": <int> },
      "ingredients": [ { "ingredient_name": "[EXACT from CORE]", "weight_g": <int> }, ... ]
    }
  ]
}

FINAL VALIDATION (HARD ERRORS IF FAILED)
1) Every item_name / ingredient_name exists verbatim in CORE.
2) If HYBRID, ingredients include ONLY extras not implied by the base (see IMPLIED CONTENTS).
3) Sauces/dressings are attached (not standalone) unless clearly in a separate cup.
4) Identical units are merged using unit_count and total weight.
5) Base + ingredients weights sum consistently (nearest 5 g; cooked when cooked).
6) No trailing text; JSON only.
```

---

## (2) よくある落とし穴と実装メモ

1. **ベースの“含意”不一致**

   * ベースが何を内包するかを明文化しないと、チーズピザに「Spaghetti sauce」や「Cheese, Mozzarella」を重複計上しがち。上の *IMPLIED CONTENTS* を必ず保持（プロンプトに同梱）してください。

2. **ボウル系の判定（HYBRIDかDECOMPOSEか）**

   * 「Burrito bowl, NFS」「Ramen bowl, NFS」「Rice, fried, NFS」などは、具が“いつもカスタム”になりやすい。**見えている具が多い**ときはHYBRIDで“見える分だけ”を列挙。サラダ系ボウル（葉物メイン）は常にDECOMPOSEに倒す、と明示。

3. **重量の整合性**

   * 解析後の栄養計算でズレないよう、「base + ingredients＝合計」のルールを追加。端数は5 g刻みで丸める、としておくと安定します。

4. **信頼度の解釈**

   * “最小エレメント”の確からしさに引っ張られて極端に低下しないよう、**ベース / 具 / 量の3因子のうち最小値−0.05**程度を目安に（プロンプト上はレンジガイドだけ提示していますが、実装側での計算規約を決めるとブレません）。

5. **dish_name と CORE 名の関係**

   * `dish_name` は人向け自由記述でOK（たとえば “2 tacos with chicken”）。**CORE制約は base_food.item_name / ingredient_name のみ**にかかることを、明記済みですが運用でも徹底を。

6. **飲み物の扱い**

   * 「視覚的に独立したアイテム」を dish として数えるルールにより、**飲み物は別dish**に。ソース（カップ）と混同しないため、容器（グラス/ボトル）かどうかを目視で区別。

---

## (3) CORE（食品名リスト）のレビュー

### 3-1. 命名規則の揺れ（NS / NFS の使い分け）

* 用語が「NS（not specified）」と「NFS（not further specified）」で混在。**カテゴリごとに使い分けを固定**してください。

  * 推奨：

    * “部位/調理が特定できない”＝**NS**
    * “さらに詳細が未特定（総称）”＝**NFS**
* 例）鶏肉は「NS as to part…」で統一、一方で“総称（Salsa, red / Sauce, NFS / Beans, NFS）”は NFS を使う、など。

### 3-2. ベース／具として頻出なのに抜けている語（高頻度ギャップ）

実運用での誤マッピング・二重計上を最も減らす **“少数精鋭の追加”** を挙げます（全部で ~25項目）。これらは視認性が高く、他の多くの料理に“具”として登場します。COREに追加することで、NFSの乱用と信頼度低下を避けられます。

**野菜・薬味・海藻**

* Onions, raw
* Onions, cooked
* Lettuce, iceberg, raw（or keep “Lettuce, raw” but add “Iceberg” if区別したい）
* Jalapeno peppers, pickled（※既存「Peppers, jalapenos」は生の含意に見えるためピクルス用途を別立て推奨）
* Seaweed, NFS（ラーメン/寿司で頻出）
* Pickled ginger（寿司）

**卵（用途別）**

* Egg, scrambled
* Egg, fried
* Egg, hard-boiled

**乳製品・チーズ**

* Cheese, American
* Cheese, Provolone
* Cheese, Feta
* Cheese, Pepper Jack

**肉・加工肉**

* Bacon, cooked
* Sausage patty, pork（朝食サンドの具）
* Meatballs, NFS（パスタ/サブで頻出）

**穀物・キャリア**

* Tortilla, whole wheat
* Roll, white, sub/hoagie roll（長物サンド用）

**ソース・ドレッシング・甘味**

* Tartar sauce
* Vinaigrette, NFS
* Maple syrup
* Wasabi

**アジア料理の具**

* Fish cake, NFS（ナルト等を包括）
* Bamboo shoots, cooked（メンマ代替）

> これらを入れると、バーガー・サンド・ボウル・寿司/ラーメン・和洋朝食でのカバー率が大幅に上がります。

### 3-3. “含意が強すぎるベース”の注意

* 「Burrito, NFS」「Burrito bowl, NFS」「Sandwich, NFS」は、**ベースが何を含むか曖昧**。プロンプト側で含意を明示（上記v2）したうえで、**具は見えているものだけ**を HYBRID ingredients に挿す運用に寄せてください。

### 3-4. ソース系の語彙

* 現在でも十分多いですが、**“ドレッシング系の総称”**が「Sauce, NFS」しかないのは運用上もったいないため「Vinaigrette, NFS」を追加。揚げ物用の「Tartar sauce」も高頻度。
* 寿司系の視認子として **Wasabi / Pickled ginger / Soy sauce** の3点セットが揃うとNFSに逃げずに済みます。

### 3-5. チーズの網羅

* 米国の外食・デリで **American / Provolone / Pepper Jack / Feta** は頻出。バーガー・サンド・ピザ・サラダのHYBRID整合性が安定します。

### 3-6. 小規模整頓（推奨）

* 「Bread, sour dough」→ **Bread, sourdough**（一般表記に寄せる）
* 「Biscuit, wheat」→ 用途が不明確。**Biscuit, NFS** に統合し、必要なら “whole wheat” 版を追加。
* 「Taco shell, flour / Taco shell, corn」と「Tortilla, flour / Tortilla, corn」は両立でOK。**Taco shell**は“ハード”の含意を備忘に。
* ドーナツの重複（Doughnut, NFS / Doughnut, yeast type / Doughnut, chocolate）は許容。ただし将来、アイシング/フィリングが見える場合に備えて「Icing/Filling, NFS」を追加する手もあります（優先度は低）。

---

## 参考：実装側チェックリスト（運用の安定化に効く）

* **スキーマ検証**：`analysis_method` の enum、`weight_g` は整数、`confidence` は 0–1、小数2桁までなどを JSON Schema で検証。
* **語彙バリデータ**：COREをセットにして `item_name` / `ingredient_name` を **完全一致** 探索。見つからない場合は即エラーで再推定ロジックへ。
* **重量の整合**：HYBRID/DECOMPOSE では `base_food.weight_g + Σingredients.weight_g` が dish 合計と一致するかをテスト（±5 g 許容）。
* **丸め規則**：すべて **5 g 刻み** に丸める。
* **信頼度の下限**：NFS/NSを2つ以上含む or 主要構成が不明なら **0.55以下** に制限。
* **ユニット集約**：同一アイテムの検出は IoU と外観特徴で束ね、`unit_count` と総重量を更新。
* **ベース優先**：Pizza/パスタ/バーガー/メキシカン/標準サイドはまず`USE_AS_IS`を試行し、明確な追加が見えたときだけHYBRIDに昇格。

---

### まとめ

* **プロンプト側**は「含意の明文化」「ボウル系ルール」「重量の足し算整合」「信頼度ガイド」を入れるだけで、出力の一貫性が大きく向上します。
* **CORE側**は、上記の**高頻度ギャップ25項目**を追加するだけで、NFS/NSへの退避が減り、信頼度を底上げできます。
* 最後に、NS/NFSの使い分けと表記揺れ（sourdough 等）の軽整頓をすると、バリデーションも安定します。

必要なら、あなたの現行COREに今回の「追加候補」を統合した“差分リスト（追加・改名・統合）」をこちらで作成してお渡しします。
