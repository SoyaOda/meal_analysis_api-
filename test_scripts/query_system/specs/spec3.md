結論から先に──**USDAの命名（`main_name`＋カンマ区切りの修飾＝`description`群）を前提に、検索は“主語（main）優先・修飾（desc）補助”、再ランキングは“主語を明示的に強調しつつ全体（main＋desc）を対に入力”**が最適です。
これにより、**Stage1（候補生成）では取り違えを抑えた高リコール**、**Stage2（再ランク）では調理法・皮/脂有無・NFS/NS といった微差の精密判定**が両立します。

---

## なぜ「main優先・desc補助」か（USDA命名規則とIRの知見）

* **USDA/FNDDSの名称は、主名（主食材）＋状態・処理・詳細（raw/cooked, grilled/roasted, skinless, NFS/NS など）の**構造です。**NFS/NS**は詳細不明時の汎用コードとして使われ、**栄養値もその前提で推定**されます。したがって**主名を核に同類集合を作り、descで適切なバリアントを選ぶ**のが合理的です。([ARS][1])
* 情報検索の定石として、**フィールド付き文書の一次検索は“見出し（title/main）を高ウェイト、本文（desc）を補助”的に扱う**のが一般的（BM25F など）。短文クエリ（食品名）は語一致の寄与が高く、**mainを強く当ててからdescで絞る**のが安定します。([Weaviate Documentation][2])
* 一方、**クロスエンコーダ型の再ランカー（MonoT5/BGE-rerankerなど）はクエリと候補テキストの全トークン相互作用**で関連度を判定します。**descを含めた方が調理法・状態の細部差で優劣を付けやすい**ため、Stage2では**main＋descを“フィールド明示”で入力**するのが効果的です。([bge-model.com][3])

---

## 設計の要点（推奨）

### Stage 1（候補生成：ベクトル＋語検索のハイブリッド）

**目的**：主名の取り違え（例：*fried rice* と *fried chicken* を「fried」で誤マッチ）を避けつつ、正解をTop‑Kに必ず入れる。

1. **二系統のベクトル類似度を合成**

* **main埋め込み**：`E_main(item) = embed(main_name)`
* **full埋め込み**：`E_full(item) = embed(main_name + " ; " + desc_concat)`
* クエリ側も同様に `Q_main`, `Q_full` を作り、
  **`S_emb = α·cos(Q_main, E_main) + (1-α)·cos(Q_full, E_full)`**（例：α=0.6〜0.8でmainを厚め）
  → 主名で“集合”に入れ、descで“近傍”を整える。

2. **BM25F（またはフィールド重み付きBM25）を併用**

* インデックスを `name` フィールド（高ウェイト）、`desc` フィールド（低ウェイト）で構成。
* 正規化した BM25F スコアと埋め込みスコアを**線形融合**：
  **`S_stage1 = λ·S_emb + (1-λ)·BM25F_norm`**（λの初期値は0.6前後）
  → **短文の語一致**を拾い、**類義語は埋め込み**が補完。([Weaviate Documentation][2])

> **根拠**：USDA名は「主名＋修飾」の体系。**主名一致**は栄養的な同一集合を作る鍵。**desc**は“調理状態/皮/脂/塩分/ソース有無/NFS/NS”等で栄養密度を左右するため**第二段階で効かせる**のが合理的。([ARS][1])

### Stage 2（再ランキング：クロスエンコーダ/BGE‑reranker など）

**目的**：**同一主名内の細かな差（grilled vs roasted、skinless、with cheese、NFS/NS）**を見分け、**栄養的に適切**な1件を選ぶ。

* **入力テンプレート（フィールド明示）**

  * **Query**

    ```
    name: {search_name}
    description: {description or "N/A"}
    ```
  * **Candidate**

    ```
    name: {main_name_from_db}
    description: {comma_joined_descriptors}   # cooked, grilled, skinless, NFS/NS, etc.
    ```
  * これを**「question/document」形式**で BGE‑reranker などに渡す（pair入力）。
    *BGE系は「question + document」入力を想定*。**フィールドラベル（name:/description:）で主名を強調**しつつ、descの差異も読ませます。([bge-model.com][3])

* **なぜ合算（main＋desc）を渡すのか**
  クロスエンコーダは**全トークン相互作用**を使うため、**descを含めた方が微差で整列しやすい**（MonoT5 などの実装でも、*Query: … Document: …* 形式で本文全体を与えるのが標準）。ただし**フィールド名を付けて主名を明示**し、*fried* のような修飾語が過剰に効くのを抑えます。([arXiv][4])

---

## 具体仕様（推奨パイプライン）

### 1) データ保持

* **フィールド分離**で保存：`main_name`、`descriptors[]`（カンマ分割）、`aliases[]`、`NFS/NSフラグ`。
* **二種の埋め込みを事前計算**：`E_main` と `E_full`。
* **BM25F**：`name` フィールドに高ウェイト、`desc` に低ウェイト。([Weaviate Documentation][2])

### 2) クエリ正規化と生成

* VLM出力 → `search_name`（主語）と`description`（修飾）を正規化（小文字化/記号標準化）。
* **二系統クエリ埋め込み**：`Q_main`, `Q_full` を生成。
* **BM25Fクエリ**：`name:search_name^w_name  desc:description^w_desc`。

### 3) 候補取得（Top‑K）

* `S_emb` と `BM25F_norm` を融合して **Top‑K（5〜10）** 取得。Kは再ランカのレイテンシ目標で調整。([Weaviate Documentation][2])

### 4) 再ランク（BGE‑reranker推奨）

* **入力整形**（前述テンプレート）で **K件をスコアリング**。([bge-model.com][3])
* **最終スコア**：
  **`S_final = β·S_rerank + (1-β)·S_emb + ϕ·P(consistency)`**

  * `S_rerank`：BGEの出力（必要なら Sigmoid）
  * `S_emb`：Stage1の埋め込みスコア
  * `P(consistency)`：**整合性ペナルティ/ボーナス**。例：

    * **主名一致/同義語一致**ボーナス
    * **raw vs cooked の齟齬**ペナルティ（画像が“cooked”示唆、候補が“raw”なら減点）
    * **skin/boneless/with cheese 等の齟齬**ペナルティ
      → **“主名を軸”に“descで最終決着”**の思想を数式化。

### 5) NFS/NSの扱い（曖昧時の安全側）

* 画像やテキストで**調理状態が不明**なら、**NFS/NS候補を許容**。FNDDSも**詳細不明時にNFS/NSコードを使う**運用のため、一致しない極端な候補（raw↔cooked）を避けられます。([ARS][5])

---

## どこで「合算」し、どこで「主名優先」するか（設計方針の整理）

| 段階               | テキストの使い方                        | 目的                  | 推奨理由                                                      |
| ---------------- | ------------------------------- | ------------------- | --------------------------------------------------------- |
| **Stage1: 取得**   | **主名強調**（二系統埋め込み＋BM25Fのフィールド重み） | 正解をTop‑Kに入れる（高リコール） | 短文は語一致の寄与が高い／USDAは主名が栄養集合の核。([Weaviate Documentation][2]) |
| **Stage2: 再ランク** | **main＋desc合算**（ただし**フィールド明示**） | 微差の精密判定（トップ1決定）     | クロスエンコーダは全トークン相互作用で調理法や皮/脂等の差を判定。([bge-model.com][3])     |

> つまり、**「取得は主名重視」「決着は合算」**がベストプラクティスです。

---

## 実装スニペット（疑似コード）

```python
# Stage 1: 二系統の埋め込み＋BM25F 融合
cos_main = cosine(Q_main, E_main_db)     # main_nameのみ
cos_full = cosine(Q_full, E_full_db)     # main+desc
S_emb = 0.7 * cos_main + 0.3 * cos_full

BM25F = bm25f(query={"name": q_search_name, "desc": q_desc}, weights={"name": 2.0, "desc": 0.5})
S_stage1 = 0.6 * S_emb + 0.4 * normalize(BM25F)
topk = top_k_items(S_stage1, K=5)

# Stage 2: BGE-reranker でペアスコア
def make_pair(q_name, q_desc, cand_name, cand_desc):
    q = f"name: {q_name}\ndescription: {q_desc or 'N/A'}"
    d = f"name: {cand_name}\ndescription: {cand_desc or 'N/A'}"
    return q, d

pairs = [make_pair(q_name, q_desc, it.main, it.desc) for it in topk]
S_rerank = bge_reranker.score(pairs)  # 例：FlagEmbedding/BAAI bge-reranker-base

# 整合性ペナルティ
pen = penalty_raw_cooked_mismatch(q_desc, it.desc) + penalty_skin_boneless(q_desc, it.desc)
S_final = 0.7 * S_rerank + 0.3 * S_emb[topk_idx] + 0.1 * pen
best = argmax(S_final)
```

* **BGE‑rerankerの使い方**は公式チュートリアル参照。`question, document`を与えるクロスエンコーダで、**pairごとのスコア**を返します。([bge-model.com][3])
* **BM25F**のフィールド重み付けは Weaviate のドキュメントが分かりやすい（概念として`name`に高重み、`desc`に低重み）。([Weaviate Documentation][2])

---

## よくある疑問への回答

* **Q. 仕様書は“合算”前提に見えるが？**
  → **Stage2では合算（main＋desc）**が妥当です。ただし**Stage1は“主名優先・desc補助”**の二段設計にしてください。**両方で合算にすると、主名取り違え（fried語が強すぎる等）が起こりやすい**ため推奨しません。([Weaviate Documentation][2])

* **Q. 再ランカーにdescを入れると“修飾で釣られる”のでは？**
  → **フィールド見出し**（`name:`/`description:`）を付け、**一致/不一致のルールベース整合性項目**（raw/cooked、skin/boneless など）を**最終合成スコアに加える**ことで抑制します。USDAでも調理状態・NFS/NSが栄養値に直結するため、この整合性項目は理にかないます。([ARS][1])

* **Q. mainだけで良いのでは？**
  → **Top‑K候補生成までは“ほぼmainだけ”でも動きます**が、**最終1件の確定**には**desc（調理法/皮/脂/塩）の寄与が大**。**合算＋フィールド明示**が安全策です。([bge-model.com][3])

---

## ミニ評価計画（A/B）

1. **Stage1**：

   * A：`S_emb = cos(full)` 単独
   * B：`S_emb = 0.7·cos(main) + 0.3·cos(full)`（推奨）
   * C：B＋BM25F 融合（推奨最有力）
2. **Stage2**（BGE‑reranker）：

   * A：`nameのみ`
   * B：`name + desc（生合算）`
   * C：`name + desc（フィールド明示）`（推奨）
3. **指標**：Top‑1精度、Recall@5、raw↔cooked取り違え率、皮/脂/チーズ有無の取り違え率。
   → **Cが最も栄養的に安全**であるはず。

---

## 参考（一次情報）

* **USDA/FNDDS の命名と NFS/NS の定義**：主名（Main food description）と追加記述、NFS/NS の運用。([ARS][1])
* **FoodData Central の Food Descriptions（raw/cooked などの属性を保持）**。([FoodData Central][6])
* **BM25F（フィールド重み付け）の概念と活用**。([Weaviate Documentation][2])
* **クロスエンコーダ再ランク（BGE‑reranker/MonoT5）の入力と位置づけ**。([bge-model.com][3])

---

### 最終提案（短く）

* **Stage1**：**主名70%＋合算30%**の埋め込みスコアに**BM25F（name重み高）**を融合しTop‑K。
* **Stage2**：**BGE‑reranker**に**`name:`/`description:`**の**フィールド明示で合算入力**。
* **最終スコア**：再ランク＋埋め込み＋**調理/皮/脂/NFS整合性ペナルティ**で決定。

こうすれば、**“主名で外さず”・“descで精密に栄養的に正しい1件へ”**という要件を両立できます。

[1]: https://www.ars.usda.gov/ARSUserFiles/80400530/pdf/fndds/fndds3_doc.pdf?utm_source=chatgpt.com "the usda food and nutrient database for dietary studies, 3.0"
[2]: https://docs.weaviate.io/weaviate/concepts/search/keyword-search?utm_source=chatgpt.com "Keyword Search (BM25)"
[3]: https://bge-model.com/tutorial/5_Reranking/5.1.html?utm_source=chatgpt.com "Reranker — BGE documentation"
[4]: https://arxiv.org/pdf/2101.05667?utm_source=chatgpt.com "The Expando-Mono-Duo Design Pattern for Text Ranking ..."
[5]: https://www.ars.usda.gov/ARSUserFiles/80400530/pdf/fndds/2021_2023_FNDDS_Doc.pdf?utm_source=chatgpt.com "2021-2023 Food and Nutrient Database for Dietary Studies"
[6]: https://fdc.nal.usda.gov/Foundation_Foods_Documentation?utm_source=chatgpt.com "FoodData Central Foundation Foods Documentation"
