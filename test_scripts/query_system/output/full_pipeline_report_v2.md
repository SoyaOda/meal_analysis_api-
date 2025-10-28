# 🔍 Food Query System - Full Pipeline Report

**Generated**: 2025-10-26 09:22:08

---

## 📑 Table of Contents

1. [Overview](#overview)
2. [Pipeline Architecture & Algorithms](#pipeline-architecture--algorithms)
   - [2.1 VLM Query Generation](#21-vlm-query-generation)
   - [2.2 Text Normalization](#22-text-normalization)
   - [2.3 Stage 1: Two-Stream Weighted Retriever](#23-stage-1-two-stream-weighted-retriever)
   - [2.4 Stage 2: LLM-based Reranker](#24-stage-2-llm-based-reranker)
3. [Step 1: VLM Prompt](#step-1-vlm-prompt)
4. [Step 2: VLM Results](#step-2-vlm-results)
5. [Step 3: Query Generation](#step-3-query-generation)
6. [Step 4: Search Pipeline Results](#step-4-search-pipeline-results)
7. [Summary](#summary)

---

## Overview

このレポートは、画像から食品クエリを生成し、USDA食品データベースで検索するまでの全プロセスを記録しています。

### Pipeline Flow

```
画像 → VLM → クエリ生成 → テキスト正規化 → 検索パイプライン → 結果
                          ↓
                    search_name + description
                          ↓
                ┌─────────┴─────────┐
                ↓                   ↓
          Stage 1: Retriever  Stage 2: Reranker
          (FAISS + Embedding) (LLM-based)
                ↓                   ↓
           100 candidates      Top 10 results
```

### Models Used

| Component | Model | Details |
|-----------|-------|---------|
| VLM | Qwen3-VL-235B-A22B-Thinking | Vision-Language Model for image analysis |
| Embedding | Qwen3-Embedding-8B | 4096-dimensional embeddings via DeepInfra API |
| Reranker | Qwen3-Reranker-8B | LLM-based reranking via DeepInfra API |

---

## Pipeline Architecture & Algorithms

このセクションでは、各ステージのアルゴリズムを詳細に説明します。

### 2.1 VLM Query Generation

**目的**: VLMの出力JSON（`dishes`配列）から検索可能なクエリを生成

**アルゴリズム**:

1. VLM出力から`main_food`と`extras`を抽出
2. 各食品に対して`search_name`（主要食品名）と`description`（調理方法・状態）を分離
3. USDA検索用に最適化されたクエリペアを生成

**VLM出力例**:
```json
{
  "main_food": {
    "search_name": "beef steak",
    "description": "grilled, sliced",
    "weight_g": 190,
    "confidence": 0.95
  }
}
```

**生成されるクエリ**:
- `query_main`: `"beef steak"`
- `query_descriptors`: `"grilled, sliced"`

**実装** (`prepare_test_data.py`):
```python
def load_vlm_test_data() -> List[Dict]:
    for result in data.get('results', []):
        dishes = vlm_response.get('dishes', [])
        
        for dish in dishes:
            # Extract main_food
            if dish.get('main_food'):
                main_food = dish['main_food']
                query_items.append({
                    'search_name': main_food.get('search_name'),  # e.g., "beef steak"
                    'description': main_food.get('description'),  # e.g., "grilled, sliced"
                    'weight_g': main_food.get('weight_g'),
                    'confidence': main_food.get('confidence')
                })
```

### 2.2 Text Normalization

**目的**: クエリとデータベースの表記ゆれを吸収し、検索精度を向上

**アルゴリズム**:

1. **基本正規化**: 小文字化 + 特殊文字削除
2. **複合語正規化**: `"cherry tomatoes"` → `"tomatoes cherry"` (USDA形式に合わせる)
3. **2つのテキスト生成**:
   - `main_only`: search_nameのみ (e.g., `"beef steak"`)
   - `full`: search_name + description (e.g., `"beef steak grilled sliced"`)

**実装** (`text_normalizer.py`):
```python
def normalize_text(text: str) -> str:
    # 小文字化
    text = text.lower()
    # 特殊文字削除（アルファベットとスペースのみ残す）
    text = re.sub(r'[^a-z\s]', ' ', text)
    # 複数スペースを単一スペースに
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_compound_words(text: str) -> str:
    compound_mappings = {
        "cherry tomatoes": "tomatoes cherry",
        "beef steak": "steak beef",
        "chicken breast": "breast chicken",
        # ... more mappings
    }
    return compound_mappings.get(text.lower(), text.lower())
```

**例**:

| Input | Normalized |
|-------|------------|
| `"Chicken, Broiled"` | `"chicken broiled"` |
| `"cherry tomatoes"` | `"tomatoes cherry"` |
| `"beef steak"` | `"steak beef"` |

### 2.3 Stage 1: Two-Stream Weighted Retriever

**目的**: FAISSインデックスから関連度の高い100件の候補を高速に取得

**アルゴリズム**: Two-Stream Weighted Search

#### 数式

```
S_combined = w_main * cosine(Q_main, E_main) + w_full * cosine(Q_full, E_full)

where:
  w_main = 0.6  (main-only weight, 主要食品名の重み)
  w_full = 0.4  (full weight, 文脈込みの重み)
  Q_main = embedding("beef steak")  (main-onlyクエリ)
  Q_full = embedding("beef steak grilled sliced")  (fullクエリ)
  E_main = main-only embedding of database item
  E_full = full embedding of database item
```

#### プロセス

1. **2つのクエリを生成**:
   - `text_main`: `"beef steak"` → embedding → `Q_main`
   - `text_full`: `"beef steak grilled sliced"` → embedding → `Q_full`

2. **2つのFAISSインデックスで検索**:
   - `index_main`: main-only embeddingsを格納 (5,772 vectors × 4096 dim)
   - `index_full`: full embeddingsを格納 (5,772 vectors × 4096 dim)

3. **スコアの重み付け融合**:
   - 各候補に対して `S_combined = 0.6 * S_main + 0.4 * S_full`
   - 融合スコアでTop-100をソート

#### 実装 (`searcher.py`)

```python
class IndexSearcher:
    def search(self, query_main: str, query_descriptors: str, top_k: int):
        # 1. Build query texts
        text_main = normalize_text(build_main_only_text(query_main))
        text_full = normalize_text(build_full_text(query_main, query_descriptors))
        
        # 2. Encode queries
        emb_main = self.embedding_model.encode(text_main)
        emb_full = self.embedding_model.encode(text_full)
        
        # 3. Normalize embeddings (for cosine similarity)
        emb_main = emb_main / np.linalg.norm(emb_main, axis=1, keepdims=True)
        emb_full = emb_full / np.linalg.norm(emb_full, axis=1, keepdims=True)
        
        # 4. Search both indexes
        scores_main, indices_main = self.index_main.search(emb_main, top_k*2)
        scores_full, indices_full = self.index_full.search(emb_full, top_k*2)
        
        # 5. Weighted combination
        combined_scores = {}
        for idx, score in zip(indices_main[0], scores_main[0]):
            combined_scores[idx] = self.weight_main * score
        
        for idx, score in zip(indices_full[0], scores_full[0]):
            if idx in combined_scores:
                combined_scores[idx] += self.weight_full * score
            else:
                combined_scores[idx] = self.weight_full * score
        
        # 6. Sort by combined score
        sorted_indices = sorted(combined_scores.keys(), 
                               key=lambda x: combined_scores[x], 
                               reverse=True)
        
        return sorted_indices[:top_k]  # Return top-100
```

#### 例: `"beef steak | grilled, sliced"`

| Stream | Query | Top Candidate | Score |
|--------|-------|---------------|-------|
| Main | `"beef steak"` | Beef, steak, NFS | 0.873 |
| Full | `"beef steak grilled sliced"` | Beef, steak, NFS | 0.854 |
| **Combined** | - | **Beef, steak, NFS** | **0.866** (0.6×0.873 + 0.4×0.854) |

**結果**: grilled beef steak (FDC ID: 746763) はRank 8/100で取得

### 2.4 Stage 2: LLM-based Reranker

**目的**: Stage 1の100件をLLMで精密に再評価し、Top 10を選出

**アルゴリズム**: DeepInfra API (Qwen3-Reranker-8B) + Custom Task Instruction

#### Custom Task Instruction

```
優先順位（重要度順）:
1. **食品名の一致**: 主要食品名が完全一致（例: "tomatoes"は"tomatoes"にマッチ）
2. **調理方法**: raw/cooked/grilled/roasted等の調理方法が重要
   - クエリが具体的な調理方法を指定した場合、完全一致を優先
   - クエリが"cooked"のみの場合、任意の調理済み形態を許容
   - データベースが"NS as to cooking method"の場合、曖昧なクエリに許容
3. **調理詳細**: boneless, skinless, sliced等は補助的
```

#### プロセス

1. **Field-Labeled Formatに変換**:
   ```
   Query:
   name: beef steak
   description: grilled, sliced
   
   Candidate:
   name: Beef, steak, NFS
   description: (empty)
   ```

2. **DeepInfra APIに送信**:
   ```json
   {
     "queries": ["name: beef steak\ndescription: grilled, sliced"],
     "documents": [
       "name: Beef, steak, NFS\ndescription: ",
       "name: Beef, short loin, t-bone steak, ..., grilled\ndescription: ",
       ...
     ],
     "instruction": "<Custom Task Instruction>"
   }
   ```

3. **スコアを取得し、Top 10を選出**:
   ```python
   scores = [0.6637, 0.3657, 0.3585, ...]  # API response
   best_idx = np.argmax(scores)  # Index of best match
   top_10 = np.argsort(scores)[::-1][:10]
   ```

#### 実装 (`reranker.py`)

```python
class RerankerModel:
    def __init__(self, model_name="Qwen/Qwen3-Reranker-8B"):
        self.api_url = f"https://api.deepinfra.com/v1/inference/{model_name}"
        
        # Custom task instruction for food matching
        self.task_instruction = '''
        Priority for matching (most important first):
        1. Food Identity: main food name must match exactly
        2. Cooking Method: raw vs cooked matters significantly
        3. Preparation Details: boneless, skinless, etc.
        '''
    
    def rerank(self, query: str, candidates: List[str]):
        payload = {
            "queries": [query],
            "documents": candidates,
            "instruction": self.task_instruction
        }
        
        response = requests.post(self.api_url, json=payload)
        scores = np.array(response.json()["scores"])
        
        best_idx = int(np.argmax(scores))
        return best_idx, scores
```

#### 例: `"beef steak | grilled, sliced"`

| Rank | Description | Stage1 Score | Rerank Score |
|------|-------------|--------------|--------------|
| 1 | Beef, steak, NFS | 0.8732 | **0.6637** ⬅️ Best |
| 2 | Beef, steak, strip, NS as to fat eaten | 0.8671 | 0.3657 |
| 3 | Beef, short loin, t-bone steak, ..., grilled | 0.8790 | 0.3585 ⬅️ grilled版 |

**結果**: "Beef, steak, NFS"が1位に選出（栄養学的に許容可能）

---

## Step 1: VLM Prompt

VLMに送信されるプロンプトテンプレート：

```
You are an expert food analyst for a US‑based diet app.

Your job is to analyze ONE meal image and return ONE JSON object ONLY (no extra text). The JSON will be used to query the USDA FoodData Central (or equivalent) and then sum nutrients for the ENTIRE meal.

──────────────────────────────────────────────────────────────────────────────

GOAL
- Identify all visually separable dishes in the photo (including beverages).
- For EACH dish, output:
  • a single main_food when the dish is commonly understood and nutritionally stable as one unit (e.g., “cheeseburger”, “slice of pepperoni pizza”, “burrito”, “latte”), and  
  • any clearly visible extras (add‑ons/toppings) that are NOT part of the typical default composition.
- If no coherent single‑unit applies (e.g., custom salad/mixed bowl), set main_food to null and list all visible components in extras.
- Do NOT compute nutrition yourself. Provide names and weights only.
- The sum of all weights across all dishes (their main_food + extras) should approximate the total edible food in the image.

──────────────────────────────────────────────────────────────────────────────

USDA‑FRIENDLY NAMING FOR DATABASE QUERY
For EVERY item (both main_food and each extras entry), provide:

1) search_name — core food identity for search (concise noun phrase, American English).
   - Keep it generic and widely recognizable (e.g., “cheeseburger”, “white rice”, “chicken breast”, “greek yogurt”, “fried egg”, “french fries”, “red wine”).
   - Include essential species/cut/type when relevant: “salmon fillet”, “beef sirloin”, “pork bacon”, “chicken thigh”, “brown rice”.
   - Avoid brand names unless the package/logo is clearly visible and central to the item.
   - Do NOT include preparation/state modifiers here; put them in description.

2) description — a SHORT, comma‑separated list of normalized USDA‑style modifiers (use zero or more; choose only what is clear).  
   Use tokens from the sets below; write exactly as shown (lowercase), separated by commas (no “and”):
   • form/state: raw, cooked, fresh, frozen, canned, from dried, instant, powder, concentrate, ready‑to‑serve, drained, undrained, in water, in oil, in syrup  
   • method: boiled, steamed, roasted, grilled, baked, pan‑fried, deep‑fried, stir‑fried, sauteed  
   • fat/salt/sugar: no added fat, fat added, with oil, no oil, with butter, no added salt, reduced sodium, sweetened, unsweetened, plain, with dressing, with cheese  
   • meat/poultry/fish qualifiers: skinless, with skin, boneless, bone‑in, ground, lean 90%, lean 85%, breast, thigh, drumstick, wing, loin, sirloin, ribeye, fillet  
   • grains/dairy/other: whole grain, refined, long‑grain, short‑grain, thin crust, thick crust, whole milk, low fat, nonfat, with vegetables, with meat, with fruit
   • uncertainty (only if visually relevant but unspecified): nfs, ns as to fat, ns as to cooking, ns as to milk type, ns as to sodium
   Notes:
   - Keep description short and only include modifiers you can confidently see or strongly infer.
   - Do NOT repeat the core identity here (e.g., not “rice, cooked rice”).  
   - Examples: “cooked”, “grilled, skinless”, “canned, drained”, “thin crust, with vegetables”, “unsweetened, plain”.

LANGUAGE/FORMAT
- English, lowercase except proper nouns; concise and database‑friendly.
- Avoid vague stand‑alone modifiers as search_name (e.g., not just “fried” or “sauce”).

──────────────────────────────────────────────────────────────────────────────

QUANTITY & CONFIDENCE
- weight_g: estimated edible weight in grams (positive integer; no zeros/negatives; exclude inedible parts/ice).
- confidence: 0.0–1.0 reflecting certainty of the identity AND its weight.
  • 0.85–1.00: clear, typical, well‑seen  
  • 0.60–0.84: some ambiguity/occlusion  
  • 0.40–0.59: low certainty/look‑alike risk

──────────────────────────────────────────────────────────────────────────────

GENERIC GROUPING RULES (keep high‑level; avoid over‑decomposition)
- If a dish is commonly consumed as one unit with predictable internal makeup (e.g., cheeseburger, slice of pizza, burrito, latte, yogurt cup), set that as main_food and DO NOT split typical internal parts.
- Use extras ONLY for non‑standard add‑ons or clearly visible add‑ins (e.g., fried egg on a burger, extra bacon, avocado add‑on, extra cheese, visible sauce on top).
- Sides plated separately (e.g., fries next to a burger, side salad, dipping sauce in a separate cup) should be modeled as separate dishes (their own entry in dishes), not as extras of another dish.
- List items that are visually present or highly likely from strong visual cues. Do NOT list trivial trace ingredients (pinch of salt, minor spices) unless they contribute meaningful weight.

──────────────────────────────────────────────────────────────────────────────

OUTPUT — JSON ONLY (no comments, no extra text)
Return exactly ONE JSON object with this schema:

{
  "dishes": [
    {
      "main_food": null | {
        "search_name": "string",
        "description": "string or null",
        "weight_g": <positive integer>,
        "confidence": <float 0.0-1.0>
      },
      "extras": [
        {
          "search_name": "string",
          "description": "string or null",
          "weight_g": <positive integer>,
          "confidence": <float 0.0-1.0>
        }
      ]
    }
  ]
}

──────────────────────────────────────────────────────────────────────────────

RULES
1) Single JSON object only; no prose, no comments.  
2) Weights must be realistic positive integers; the total across all dishes ≈ total edible food in the image.  
3) Forbidden fields: do NOT output unit_count, found_in_list, nutrition_per_100g, analysis_method, or any fields not in the schema.  
4) If no food is recognizable, return { "dishes": [] }.  
5) Prefer the most natural single‑unit main_food when appropriate; otherwise set main_food: null and list all components in extras.  
6) Keep search_name focused on the core identity; put only modifiers in description using the token list above.

──────────────────────────────────────────────────────────────────────────────

MINIMAL EXAMPLE (format illustration only)

{
  "dishes": [
    {
      "main_food": {
        "search_name": "cheeseburger",
        "description": null,
        "weight_g": 190,
        "confidence": 0.95
      },
      "extras": [
        {
          "search_name": "fried egg",
          "description": null,
          "weight_g": 45,
          "confidence": 0.90
        }
      ]
    },
    {
      "main_food": {
        "search_name": "french fries",
        "description": null,
        "weight_g": 150,
        "confidence": 0.95
      },
      "extras": [
        {
          "search_name": "ketchup",
          "description": null,
          "weight_g": 25,
          "confidence": 0.75
        }
      ]
    }
  ]
}

Return the JSON now.

```

---

## Step 2: VLM Results

**Total Images Processed**: 50
**Successful Analyses**: 50

### Sample VLM Outputs (First 3 Images)

#### Image 1: test_food1.jpg

```json
{
  "dishes": [
    {
      "main_food": null,
      "extras": [
        {
          "search_name": "mixed greens",
          "description": "raw",
          "weight_g": 45,
          "confidence": 0.85
        },
        {
          "search_name": "cherry tomatoes",
          "description": "raw",
          "weight_g": 35,
          "confidence": 0.85
        },
        {
          "search_name": "carrots",
          "description": "raw, sliced",
          "weight_g": 25,
          "confidence": 0.85
        },
        {
          "search_name": "cucumber",
          "description": "raw, sliced",
          "weight_g": 25,
          "confidence": 0.85
        }
      ]
    },
    {
      "main_food": {
        "search_name": "beef steak",
        "description": "grilled, sliced",
        "weight_g": 190,
        "confidence": 0.95
      },
      "extras": []
    },
    {
      "main_food": {
        "search_name": "yellow squash",
        "description": "cooked, sliced",
        "weight_g": 90,
        "confidence": 0.9
      },
      "extras": []
    },
    {
      "main_food": {
        "search_name": "cucumber",
        "description": "raw, sliced",
        "weight_g": 30,
        "confidence": 0.9
      },
      "extras": []
    },
    {
      "main_food": {
        "search_name": "macaroni and cheese",
        "description": "cooked",
        "weight_g": 130,
        "confidence": 0.9
      },
      "extras": []
    }
  ]
}
```

#### Image 2: test_food2.jpg

```json
{
  "dishes": [
    {
      "main_food": {
        "search_name": "macaroni and cheese",
        "description": "cooked",
        "weight_g": 180,
        "confidence": 0.95
      },
      "extras": []
    },
    {
      "main_food": {
        "search_name": "broccoli",
        "description": "cooked",
        "weight_g": 100,
        "confidence": 0.95
      },
      "extras": []
    },
    {
      "main_food": {
        "search_name": "yellow squash",
        "description": "cooked",
        "weight_g": 120,
        "confidence": 0.95
      },
      "extras": []
    },
    {
      "main_food": {
        "search_name": "chicken breast",
        "description": "cooked, boneless, skinless",
        "weight_g": 150,
        "confidence": 0.95
      },
      "extras": []
    },
    {
      "main_food": {
        "search_name": "red wine",
        "description": "ready-to-serve",
        "weight_g": 150,
        "confidence": 0.95
      },
      "extras": []
    }
  ]
}
```

#### Image 3: test_food3.jpg

```json
{
  "dishes": [
    {
      "main_food": {
        "search_name": "beef sirloin",
        "description": "cooked, roasted",
        "weight_g": 180,
        "confidence": 0.9
      },
      "extras": [
        {
          "search_name": "caramelized onion relish",
          "description": "cooked",
          "weight_g": 40,
          "confidence": 0.8
        },
        {
          "search_name": "green onion",
          "description": "raw",
          "weight_g": 10,
          "confidence": 0.9
        }
      ]
    },
    {
      "main_food": {
        "search_name": "potatoes",
        "description": "roasted",
        "weight_g": 150,
        "confidence": 0.95
      },
      "extras": []
    },
    {
      "main_food": {
        "search_name": "asparagus",
        "description": "roasted",
        "weight_g": 100,
        "confidence": 0.95
      },
      "extras": []
    },
    {
      "main_food": {
        "search_name": "creamer",
        "description": "with herbs",
        "weight_g": 30,
        "confidence": 0.8
      },
      "extras": []
    }
  ]
}
```

---

## Step 3: Query Generation

VLM結果から生成されたクエリ数: **20**

### All Generated Queries

| # | Search Name | Description | Weight (g) | Confidence | Image |
|---|-------------|-------------|------------|------------|-------|
| 1 | mixed greens | raw | 45 | 0.85 | test_food1.jpg |
| 2 | cherry tomatoes | raw | 35 | 0.85 | test_food1.jpg |
| 3 | carrots | raw, sliced | 25 | 0.85 | test_food1.jpg |
| 4 | cucumber | raw, sliced | 25 | 0.85 | test_food1.jpg |
| 5 | beef steak | grilled, sliced | 190 | 0.95 | test_food1.jpg |
| 6 | yellow squash | cooked, sliced | 90 | 0.9 | test_food1.jpg |
| 7 | macaroni and cheese | cooked | 130 | 0.9 | test_food1.jpg |
| 8 | broccoli | cooked | 100 | 0.95 | test_food2.jpg |
| 9 | chicken breast | cooked, boneless, skinless | 150 | 0.95 | test_food2.jpg |
| 10 | red wine | ready-to-serve | 150 | 0.95 | test_food2.jpg |
| 11 | beef sirloin | cooked, roasted | 180 | 0.9 | test_food3.jpg |
| 12 | caramelized onion relish | cooked | 40 | 0.8 | test_food3.jpg |
| 13 | green onion | raw | 10 | 0.9 | test_food3.jpg |
| 14 | potatoes | roasted | 150 | 0.95 | test_food3.jpg |
| 15 | asparagus | roasted | 100 | 0.95 | test_food3.jpg |
| 16 | creamer | with herbs | 30 | 0.8 | test_food3.jpg |
| 17 | lettuce | fresh | 50 | 0.85 | test_food4.jpg |
| 18 | tomato | fresh | 45 | 0.85 | test_food4.jpg |
| 19 | onion | fresh | 25 | 0.85 | test_food4.jpg |
| 20 | carrot | shredded, fresh | 20 | 0.85 | test_food4.jpg |

---

## Step 4: Search Pipeline Results

各クエリに対してStage 1（Retriever）とStage 2（Reranker）を実行した結果：

### Query 1: mixed greens | raw

**Weight**: 45g, **Confidence**: 0.85

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.8368 | Mixed salad greens, raw | survey | 2709792 |
| 2 | 0.8131 | Mixed seeds | survey | 2707589 |
| 3 | 0.7813 | Dandelion greens, raw | survey | 2709588 |
| 4 | 0.7782 | Greens, fresh, cooked, no added fat | survey | 2709593 |
| 5 | 0.7706 | Greens, NS as to form, cooked | survey | 2709595 |
| 6 | 0.7694 | Mixed nuts, unroasted | survey | 2707505 |
| 7 | 0.7685 | Greens, fresh, cooked, fat added | survey | 2709596 |
| 8 | 0.7645 | Mustard greens, raw | survey | 2709606 |
| 9 | 0.7614 | Mixed nuts, NFS | survey | 2707504 |
| 10 | 0.7606 | Green peas, raw | survey | 2709797 |
| 11 | 0.7566 | Mixed vegetable juice | survey | 2709810 |
| 12 | 0.7551 | Mixed nuts, with peanuts, unsalted | survey | 2707508 |
| 13 | 0.7499 | Classic mixed vegetables, NS as to form, cooked | survey | 2710015 |
| 14 | 0.7498 | Mixed nuts, without peanuts, unsalted | survey | 2707510 |
| 15 | 0.7460 | Classic mixed vegetables, frozen, cooked, fat added, NS as to fat type | survey | 2710016 |
| 16 | 0.7456 | Classic mixed vegetables, cooked, from restaurant | survey | 2710012 |
| 17 | 0.7455 | Classic mixed vegetables, frozen, cooked with oil | survey | 2710018 |
| 18 | 0.7451 | Dandelion greens, cooked | survey | 2709589 |
| 19 | 0.7420 | Mustard greens, fresh, cooked, no added fat | survey | 2709607 |
| 20 | 0.7411 | Classic mixed vegetables, frozen, cooked with butter or margarine | survey | 2710019 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9991** | 0.8368 | Mixed salad greens, raw | survey | 2709792 |
| 2 | **0.3016** | 0.7813 | Dandelion greens, raw | survey | 2709588 |
| 3 | **0.1385** | 0.7782 | Greens, fresh, cooked, no added fat | survey | 2709593 |
| 4 | **0.1285** | 0.7645 | Mustard greens, raw | survey | 2709606 |
| 5 | **0.0396** | 0.7205 | Beet greens, raw | survey | 2709570 |
| 6 | **0.0346** | 0.7706 | Greens, NS as to form, cooked | survey | 2709595 |
| 7 | **0.0194** | 0.7420 | Mustard greens, fresh, cooked, no added fat | survey | 2709607 |
| 8 | **0.0188** | 0.7173 | Greens with ham or pork | survey | 2706759 |
| 9 | **0.0136** | 0.7122 | Salsa verde or salsa, green | survey | 2709743 |
| 10 | **0.0124** | 0.7030 | Turnip greens, fresh, cooked, no added fat | survey | 2709634 |

**🎯 Best Match**: Mixed salad greens, raw
- **Rerank Score**: 0.9991
- **Stage1 Score**: 0.8368
- **Source**: survey
- **FDC ID**: 2709792

---

### Query 2: cherry tomatoes | raw

**Weight**: 35g, **Confidence**: 0.85

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.8834 | Cherries, raw | survey | 2709231 |
| 2 | 0.8757 | Cherries, sweet, dark red, raw | foundation | 2346399 |
| 3 | 0.8753 | Tomatoes, raw | survey | 2709719 |
| 4 | 0.8553 | Tomatoes, grape, raw | foundation | 321360 |
| 5 | 0.8464 | Cherries, canned | survey | 2709232 |
| 6 | 0.8441 | Cherries, dried | survey | 2709199 |
| 7 | 0.8429 | Tomatillos, dehusked, raw | foundation | 2727582 |
| 8 | 0.8416 | Cherries, frozen | survey | 2709233 |
| 9 | 0.8408 | Tomato, roma | foundation | 1999634 |
| 10 | 0.8304 | Tomatoes, canned, red, ripe, diced | foundation | 333281 |
| 11 | 0.8301 | Tomatoes, whole, canned, solids and liquids, with salt added | foundation | 2685578 |
| 12 | 0.8300 | Cherries, maraschino | survey | 2709229 |
| 13 | 0.8274 | Tomatoes, fresh, cooked | survey | 2709721 |
| 14 | 0.8260 | Tomato, green, pickled | survey | 2709726 |
| 15 | 0.8180 | Tomatoes, crushed, canned | foundation | 2685581 |
| 16 | 0.8172 | Tomato, puree, canned | foundation | 2685582 |
| 17 | 0.8164 | Tomatoes, canned, cooked | survey | 2709722 |
| 18 | 0.8152 | Tomatoes, NS as to form, cooked | survey | 2709720 |
| 19 | 0.8104 | Tomatoes, for use on a sandwich | survey | 2710255 |
| 20 | 0.8100 | Tomato, paste, canned, without salt added | foundation | 2685580 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9987** | 0.8753 | Tomatoes, raw | survey | 2709719 |
| 2 | **0.1441** | 0.8104 | Tomatoes, for use on a sandwich | survey | 2710255 |
| 3 | **0.1303** | 0.8553 | Tomatoes, grape, raw | foundation | 321360 |
| 4 | **0.1192** | 0.8408 | Tomato, roma | foundation | 1999634 |
| 5 | **0.1009** | 0.8274 | Tomatoes, fresh, cooked | survey | 2709721 |
| 6 | **0.0706** | 0.8152 | Tomatoes, NS as to form, cooked | survey | 2709720 |
| 7 | **0.0675** | 0.8033 | Tomatoes, cooked, as ingredient | survey | 2710795 |
| 8 | **0.0136** | 0.8055 | Tomatoes, scalloped | survey | 2709723 |
| 9 | **0.0063** | 0.8834 | Cherries, raw | survey | 2709231 |
| 10 | **0.0052** | 0.7753 | Tomato juice, 100% | survey | 2709728 |

**🎯 Best Match**: Tomatoes, raw
- **Rerank Score**: 0.9987
- **Stage1 Score**: 0.8753
- **Source**: survey
- **FDC ID**: 2709719

---

### Query 3: carrots | raw, sliced

**Weight**: 25g, **Confidence**: 0.85

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9785 | Carrots, raw | survey | 2709660 |
| 2 | 0.9560 | Carrots, mature, raw | foundation | 2258586 |
| 3 | 0.9519 | Carrots, raw, salad | survey | 2709661 |
| 4 | 0.9478 | Carrots, frozen, unprepared | foundation | 746764 |
| 5 | 0.9472 | Carrots, fresh, cooked, no added fat | survey | 2709664 |
| 6 | 0.9414 | Carrots, fresh, cooked with oil | survey | 2709667 |
| 7 | 0.9375 | Carrots, raw, salad with apples | survey | 2709662 |
| 8 | 0.9351 | Carrots, fresh, cooked with butter or margarine | survey | 2709668 |
| 9 | 0.9350 | Carrots, fresh, cooked, fat added, NS as to fat type | survey | 2709670 |
| 10 | 0.9291 | Carrots, baby, raw | foundation | 2258587 |
| 11 | 0.9285 | Carrots, frozen, cooked with oil | survey | 2709673 |
| 12 | 0.9271 | Carrots, frozen, cooked, no added fat | survey | 2709665 |
| 13 | 0.9267 | Carrots, NS as to form, cooked | survey | 2709669 |
| 14 | 0.9253 | Carrots, canned, cooked with oil | survey | 2709675 |
| 15 | 0.9235 | Carrots, frozen, cooked, fat added, NS as to fat type | survey | 2709671 |
| 16 | 0.9217 | Carrots, canned, cooked, fat added, NS as to fat type | survey | 2709672 |
| 17 | 0.9206 | Carrots, glazed, cooked | survey | 2709677 |
| 18 | 0.9204 | Carrots, frozen, cooked with butter or margarine | survey | 2709674 |
| 19 | 0.9202 | Carrots, canned, cooked, no added fat | survey | 2709666 |
| 20 | 0.9197 | Carrots, cooked, as ingredient | survey | 2710793 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9967** | 0.9785 | Carrots, raw | survey | 2709660 |
| 2 | **0.9546** | 0.9519 | Carrots, raw, salad | survey | 2709661 |
| 3 | **0.9372** | 0.9560 | Carrots, mature, raw | foundation | 2258586 |
| 4 | **0.8539** | 0.9291 | Carrots, baby, raw | foundation | 2258587 |
| 5 | **0.4772** | 0.9375 | Carrots, raw, salad with apples | survey | 2709662 |
| 6 | **0.0901** | 0.9267 | Carrots, NS as to form, cooked | survey | 2709669 |
| 7 | **0.0706** | 0.9472 | Carrots, fresh, cooked, no added fat | survey | 2709664 |
| 8 | **0.0610** | 0.9197 | Carrots, cooked, as ingredient | survey | 2710793 |
| 9 | **0.0191** | 0.9351 | Carrots, fresh, cooked with butter or margarine | survey | 2709668 |
| 10 | **0.0154** | 0.9085 | Carrots, cooked, from restaurant | survey | 2709663 |

**🎯 Best Match**: Carrots, raw
- **Rerank Score**: 0.9967
- **Stage1 Score**: 0.9785
- **Source**: survey
- **FDC ID**: 2709660

---

### Query 4: cucumber | raw, sliced

**Weight**: 25g, **Confidence**: 0.85

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9772 | Cucumber, raw | survey | 2709784 |
| 2 | 0.9515 | Cucumber, with peel, raw | foundation | 2346406 |
| 3 | 0.9407 | Cucumber, for use on a sandwich | survey | 2710249 |
| 4 | 0.9225 | Cucumber, cooked | survey | 2709928 |
| 5 | 0.7366 | Cress, raw | survey | 2709586 |
| 6 | 0.7235 | Cucumber and vegetable namasu | survey | 2709818 |
| 7 | 0.7160 | Cabbage, red, raw | foundation | 2346408 |
| 8 | 0.7160 | Cabbage, red, raw | survey | 2709775 |
| 9 | 0.7153 | Cabbage, green, raw | foundation | 2346407 |
| 10 | 0.7153 | Cabbage, green, raw | survey | 2709773 |
| 11 | 0.7152 | Broccoli, raw | foundation | 747447 |
| 12 | 0.7152 | Broccoli, raw | survey | 2709643 |
| 13 | 0.7120 | Lettuce, raw | survey | 2709789 |
| 14 | 0.7119 | Cucumber salad, made with Italian dressing | survey | 2709820 |
| 15 | 0.7115 | Broccoli, chinese, raw | survey | 2709657 |
| 16 | 0.7113 | Carrots, raw | survey | 2709660 |
| 17 | 0.7092 | Lettuce, romaine, green, raw | foundation | 2346389 |
| 18 | 0.7091 | Lettuce, iceberg, raw | foundation | 2346388 |
| 19 | 0.7086 | Cabbage, Chinese, raw | survey | 2709774 |
| 20 | 0.7082 | Lettuce, cos or romaine, raw | foundation | 746769 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9984** | 0.9772 | Cucumber, raw | survey | 2709784 |
| 2 | **0.9450** | 0.9515 | Cucumber, with peel, raw | foundation | 2346406 |
| 3 | **0.6706** | 0.9407 | Cucumber, for use on a sandwich | survey | 2710249 |
| 4 | **0.0995** | 0.7235 | Cucumber and vegetable namasu | survey | 2709818 |
| 5 | **0.0526** | 0.9225 | Cucumber, cooked | survey | 2709928 |
| 6 | **0.0298** | 0.7005 | Cucumber salad made with cucumber and vinegar | survey | 2709821 |
| 7 | **0.0200** | 0.7119 | Cucumber salad, made with Italian dressing | survey | 2709820 |
| 8 | **0.0159** | 0.6995 | Cucumber salad, made with sour cream dressing | survey | 2709819 |
| 9 | **0.0031** | 0.7051 | Peppers, sweet, green, raw | survey | 2709800 |
| 10 | **0.0026** | 0.7037 | Cabbage, bok choy, raw | foundation | 2685572 |

**🎯 Best Match**: Cucumber, raw
- **Rerank Score**: 0.9984
- **Stage1 Score**: 0.9772
- **Source**: survey
- **FDC ID**: 2709784

---

### Query 5: beef steak | grilled, sliced

**Weight**: 190g, **Confidence**: 0.95

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.8948 | Beef, steak, flank | survey | 2705827 |
| 2 | 0.8909 | Beef, steak, cube | survey | 2705826 |
| 3 | 0.8875 | Beef, sandwich steak | survey | 2705852 |
| 4 | 0.8864 | Beef, steak, tenderloin | survey | 2705841 |
| 5 | 0.8856 | Beef, steak, country fried | survey | 2705842 |
| 6 | 0.8817 | Steak, NS as to type of meat, NS as to fat eaten | survey | 2705823 |
| 7 | 0.8814 | Beef, steak, chuck | survey | 2705825 |
| 8 | 0.8790 | Beef, short loin, t-bone steak, bone-in, separable lean only, trimmed to 1/8" fat, choice, cooked, grilled | foundation | 746763 |
| 9 | 0.8769 | Beef, steak, sirloin, lean and fat eaten | survey | 2705833 |
| 10 | 0.8762 | Beef, steak, strip, lean and fat eaten | survey | 2705836 |
| 11 | 0.8755 | Beef, steak, sirloin, lean only eaten | survey | 2705834 |
| 12 | 0.8752 | Beef, ground | survey | 2705854 |
| 13 | 0.8749 | Beef, steak, T-bone,  lean and fat eaten | survey | 2705839 |
| 14 | 0.8737 | Beef, steak, ribeye, lean and fat eaten | survey | 2705829 |
| 15 | 0.8735 | Beef, steak, round | survey | 2705831 |
| 16 | 0.8732 | Beef, steak, NFS | survey | 2705824 |
| 17 | 0.8726 | Beef, top sirloin steak, raw | foundation | 2727574 |
| 18 | 0.8720 | Beef, roast | survey | 2705847 |
| 19 | 0.8712 | Beef, steak, sirloin, NS as to fat eaten | survey | 2705832 |
| 20 | 0.8700 | Beef, sliced, with gravy, potatoes, vegetable, frozen meal | survey | 2707102 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.6637** | 0.8732 | Beef, steak, NFS | survey | 2705824 |
| 2 | **0.3657** | 0.8671 | Beef, steak, strip, NS as to fat eaten | survey | 2705835 |
| 3 | **0.3585** | 0.8790 | Beef, short loin, t-bone steak, bone-in, separable lean only, trimmed to 1/8" fat, choice, cooked, grilled | foundation | 746763 |
| 4 | **0.3337** | 0.8909 | Beef, steak, cube | survey | 2705826 |
| 5 | **0.3320** | 0.8948 | Beef, steak, flank | survey | 2705827 |
| 6 | **0.2744** | 0.8735 | Beef, steak, round | survey | 2705831 |
| 7 | **0.2674** | 0.8620 | Beef, steak, ribeye, NS as to fat eaten | survey | 2705828 |
| 8 | **0.2539** | 0.8864 | Beef, steak, tenderloin | survey | 2705841 |
| 9 | **0.2018** | 0.8602 | Beef, flank, steak, boneless, choice, raw | foundation | 2646175 |
| 10 | **0.1871** | 0.8581 | Beef, ribeye, steak, boneless, choice, raw | foundation | 2646172 |

**🎯 Best Match**: Beef, steak, NFS
- **Rerank Score**: 0.6637
- **Stage1 Score**: 0.8732
- **Source**: survey
- **FDC ID**: 2705824

---

### Query 6: yellow squash | cooked, sliced

**Weight**: 90g, **Confidence**: 0.9

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9003 | Summer squash, yellow or green, fresh, cooked, no added fat | survey | 2709991 |
| 2 | 0.8995 | Summer squash, yellow or green, NS as to form, cooked | survey | 2709993 |
| 3 | 0.8965 | Summer squash, yellow or green, fresh, cooked with oil | survey | 2709997 |
| 4 | 0.8951 | Summer squash, yellow or green, frozen, cooked with oil | survey | 2709999 |
| 5 | 0.8931 | Summer squash, yellow or green, frozen, cooked, no added fat | survey | 2709992 |
| 6 | 0.8927 | Summer squash, yellow or green, canned, cooked, fat added, NS as to fat type | survey | 2709996 |
| 7 | 0.8913 | Summer squash, yellow or green, fresh, cooked, fat added, NS as to fat type | survey | 2709994 |
| 8 | 0.8913 | Squash, summer, yellow, includes skin, raw | foundation | 2685569 |
| 9 | 0.8898 | Summer squash, yellow or green, frozen, cooked, fat added, NS as to fat type | survey | 2709995 |
| 10 | 0.8888 | Summer squash, yellow, raw | survey | 2709807 |
| 11 | 0.8882 | Summer squash, yellow or green, frozen, cooked with butter or margarine | survey | 2710000 |
| 12 | 0.8857 | Summer squash, yellow or green, fresh, cooked with butter or margarine | survey | 2709998 |
| 13 | 0.8853 | Summer squash, cooked, as ingredient | survey | 2710804 |
| 14 | 0.8760 | Fried summer squash, yellow or green | survey | 2710058 |
| 15 | 0.8726 | Summer squash, green, raw | survey | 2709808 |
| 16 | 0.8652 | Squash, summer, casserole, with rice and tomato sauce | survey | 2710060 |
| 17 | 0.8649 | Squash, summer, casserole with tomato and cheese | survey | 2710059 |
| 18 | 0.8621 | Squash, summer, souffle | survey | 2710062 |
| 19 | 0.8594 | Squash, summer, casserole, with cheese sauce | survey | 2710061 |
| 20 | 0.8458 | Squash, winter, butternut, raw | foundation | 2685570 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9989** | 0.8995 | Summer squash, yellow or green, NS as to form, cooked | survey | 2709993 |
| 2 | **0.9919** | 0.8853 | Summer squash, cooked, as ingredient | survey | 2710804 |
| 3 | **0.9912** | 0.9003 | Summer squash, yellow or green, fresh, cooked, no added fat | survey | 2709991 |
| 4 | **0.9897** | 0.8965 | Summer squash, yellow or green, fresh, cooked with oil | survey | 2709997 |
| 5 | **0.9876** | 0.8857 | Summer squash, yellow or green, fresh, cooked with butter or margarine | survey | 2709998 |
| 6 | **0.9806** | 0.8913 | Summer squash, yellow or green, fresh, cooked, fat added, NS as to fat type | survey | 2709994 |
| 7 | **0.9474** | 0.8760 | Fried summer squash, yellow or green | survey | 2710058 |
| 8 | **0.9086** | 0.8931 | Summer squash, yellow or green, frozen, cooked, no added fat | survey | 2709992 |
| 9 | **0.8661** | 0.8882 | Summer squash, yellow or green, frozen, cooked with butter or margarine | survey | 2710000 |
| 10 | **0.8634** | 0.8951 | Summer squash, yellow or green, frozen, cooked with oil | survey | 2709999 |

**🎯 Best Match**: Summer squash, yellow or green, NS as to form, cooked
- **Rerank Score**: 0.9989
- **Stage1 Score**: 0.8995
- **Source**: survey
- **FDC ID**: 2709993

---

### Query 7: macaroni and cheese | cooked

**Weight**: 130g, **Confidence**: 0.9

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.8851 | Macaroni or noodles with cheese | survey | 2708811 |
| 2 | 0.8783 | Macaroni or noodles with cheese, from restaurant | survey | 2708812 |
| 3 | 0.8711 | Macaroni or noodles with cheese, Easy Mac type | survey | 2708815 |
| 4 | 0.8697 | Macaroni or noodles with cheese, canned | survey | 2708814 |
| 5 | 0.8697 | Macaroni or noodles with cheese, made from packaged mix | survey | 2708813 |
| 6 | 0.8665 | Macaroni or pasta salad with cheese | survey | 2708947 |
| 7 | 0.8601 | Macaroni or noodles with cheese, made from reduced fat packaged mix | survey | 2708816 |
| 8 | 0.8597 | Beef and macaroni with cheese sauce | survey | 2706481 |
| 9 | 0.8586 | Chili with macaroni | survey | 2706483 |
| 10 | 0.8577 | Pasta, cooked | survey | 2708357 |
| 11 | 0.8555 | Macaroni or noodles with cheese and meat | survey | 2708818 |
| 12 | 0.8553 | Macaroni or noodles with cheese, whole grain | survey | 2708824 |
| 13 | 0.8485 | Macaroni or noodles with cheese and meat, prepared from Hamburger Helper mix | survey | 2708819 |
| 14 | 0.8435 | Macaroni or noodles with cheese and tomato | survey | 2708820 |
| 15 | 0.8341 | Macaroni or noodles, creamed, with cheese | survey | 2708928 |
| 16 | 0.8339 | Macaroni or noodles with cheese and chicken or turkey | survey | 2708823 |
| 17 | 0.8327 | Pasta, vegetable, cooked | survey | 2708351 |
| 18 | 0.8300 | Macaroni or noodles with cheese and egg | survey | 2708822 |
| 19 | 0.8252 | Pasta with cream sauce, ready-to-heat | survey | 2708857 |
| 20 | 0.8240 | Pasta with cream sauce, poultry, and added vegetables, ready-to-heat | survey | 2708872 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9474** | 0.8341 | Macaroni or noodles, creamed, with cheese | survey | 2708928 |
| 2 | **0.9305** | 0.8711 | Macaroni or noodles with cheese, Easy Mac type | survey | 2708815 |
| 3 | **0.9241** | 0.8851 | Macaroni or noodles with cheese | survey | 2708811 |
| 4 | **0.9208** | 0.8697 | Macaroni or noodles with cheese, made from packaged mix | survey | 2708813 |
| 5 | **0.8888** | 0.8601 | Macaroni or noodles with cheese, made from reduced fat packaged mix | survey | 2708816 |
| 6 | **0.8824** | 0.8300 | Macaroni or noodles with cheese and egg | survey | 2708822 |
| 7 | **0.8597** | 0.8435 | Macaroni or noodles with cheese and tomato | survey | 2708820 |
| 8 | **0.8152** | 0.8553 | Macaroni or noodles with cheese, whole grain | survey | 2708824 |
| 9 | **0.7058** | 0.8555 | Macaroni or noodles with cheese and meat | survey | 2708818 |
| 10 | **0.6732** | 0.8339 | Macaroni or noodles with cheese and chicken or turkey | survey | 2708823 |

**🎯 Best Match**: Macaroni or noodles, creamed, with cheese
- **Rerank Score**: 0.9474
- **Stage1 Score**: 0.8341
- **Source**: survey
- **FDC ID**: 2708928

---

### Query 8: broccoli | cooked

**Weight**: 100g, **Confidence**: 0.95

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9789 | Broccoli, cooked, as ingredient | survey | 2710792 |
| 2 | 0.9710 | Broccoli, cooked, from restaurant | survey | 2709644 |
| 3 | 0.9702 | Broccoli, NS as to form, cooked | survey | 2709647 |
| 4 | 0.9629 | Broccoli, fresh, cooked with oil | survey | 2709650 |
| 5 | 0.9553 | Broccoli, Chinese, cooked | survey | 2709658 |
| 6 | 0.9528 | Broccoli, fresh, cooked, no added fat | survey | 2709645 |
| 7 | 0.9522 | Broccoli, frozen, cooked with oil | survey | 2709652 |
| 8 | 0.9473 | Broccoli, fresh, cooked with butter or margarine | survey | 2709651 |
| 9 | 0.9457 | Broccoli, fresh, cooked, fat added, NS as to fat type | survey | 2709648 |
| 10 | 0.9445 | Broccoli, frozen, cooked with butter or margarine | survey | 2709653 |
| 11 | 0.9426 | Broccoli, frozen, cooked, fat added, NS as to fat type | survey | 2709649 |
| 12 | 0.9418 | Broccoli, frozen, cooked, no added fat | survey | 2709646 |
| 13 | 0.9317 | Broccoli, cauliflower and carrots, cooked, no added fat | survey | 2710033 |
| 14 | 0.9294 | Broccoli, raw | foundation | 747447 |
| 15 | 0.9294 | Broccoli, raw | survey | 2709643 |
| 16 | 0.9251 | Broccoli, cauliflower and carrots, cooked, fat added | survey | 2710034 |
| 17 | 0.9191 | Broccoli, chinese, raw | survey | 2709657 |
| 18 | 0.9158 | Broccoli raab, cooked | survey | 2709573 |
| 19 | 0.9070 | Broccoflower, cooked | survey | 2709880 |
| 20 | 0.8899 | Broccoli and cauliflower, cooked, no added fat | survey | 2710031 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9931** | 0.9789 | Broccoli, cooked, as ingredient | survey | 2710792 |
| 2 | **0.9919** | 0.9702 | Broccoli, NS as to form, cooked | survey | 2709647 |
| 3 | **0.9649** | 0.9528 | Broccoli, fresh, cooked, no added fat | survey | 2709645 |
| 4 | **0.9592** | 0.9710 | Broccoli, cooked, from restaurant | survey | 2709644 |
| 5 | **0.9553** | 0.9473 | Broccoli, fresh, cooked with butter or margarine | survey | 2709651 |
| 6 | **0.9425** | 0.9629 | Broccoli, fresh, cooked with oil | survey | 2709650 |
| 7 | **0.9274** | 0.9553 | Broccoli, Chinese, cooked | survey | 2709658 |
| 8 | **0.9124** | 0.9457 | Broccoli, fresh, cooked, fat added, NS as to fat type | survey | 2709648 |
| 9 | **0.8977** | 0.9418 | Broccoli, frozen, cooked, no added fat | survey | 2709646 |
| 10 | **0.8129** | 0.9070 | Broccoflower, cooked | survey | 2709880 |

**🎯 Best Match**: Broccoli, cooked, as ingredient
- **Rerank Score**: 0.9931
- **Stage1 Score**: 0.9789
- **Source**: survey
- **FDC ID**: 2710792

---

### Query 9: chicken breast | cooked, boneless, skinless

**Weight**: 150g, **Confidence**: 0.95

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9642 | Chicken breast, baked, coated, skin / coating not eaten | survey | 2705981 |
| 2 | 0.9593 | Chicken breast, baked, broiled, or roasted, skin not eaten, from raw | survey | 2705956 |
| 3 | 0.9574 | Chicken breast, NS as to cooking method, skin not eaten | survey | 2705954 |
| 4 | 0.9560 | Chicken breast, sauteed, skin not eaten | survey | 2705972 |
| 5 | 0.9557 | Chicken breast, baked or broiled, skin not eaten, from pre-cooked | survey | 2705958 |
| 6 | 0.9511 | Chicken breast, grilled without sauce, skin not eaten | survey | 2705968 |
| 7 | 0.9509 | Chicken breast, baked, coated, skin / coating eaten | survey | 2705980 |
| 8 | 0.9487 | Chicken breast, stewed, skin not eaten | survey | 2705966 |
| 9 | 0.9482 | Chicken breast, NS as to cooking method, skin eaten | survey | 2705953 |
| 10 | 0.9478 | Chicken breast, baked, broiled, or roasted with marinade, skin not eaten, from raw | survey | 2705962 |
| 11 | 0.9478 | Chicken breast, grilled without sauce, skin eaten | survey | 2705967 |
| 12 | 0.9473 | Chicken breast, fried, coated, skin / coating not eaten, from pre-cooked | survey | 2705977 |
| 13 | 0.9459 | Chicken breast, baked or broiled, skin eaten, from pre-cooked | survey | 2705957 |
| 14 | 0.9456 | Chicken breast, grilled with sauce, skin not eaten | survey | 2705970 |
| 15 | 0.9441 | Chicken breast, fried, coated, skin / coating not eaten, from raw | survey | 2705974 |
| 16 | 0.9440 | Chicken breast, baked, broiled, or roasted, skin eaten, from raw | survey | 2705955 |
| 17 | 0.9418 | Chicken breast, stewed, skin eaten | survey | 2705965 |
| 18 | 0.9410 | Chicken breast, sauteed, skin eaten | survey | 2705971 |
| 19 | 0.9402 | Chicken breast, baked or broiled, skin not eaten, from fast food / restaurant | survey | 2705960 |
| 20 | 0.9398 | Chicken breast, baked, broiled, or roasted with marinade, skin eaten, from raw | survey | 2705961 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9800** | 0.9574 | Chicken breast, NS as to cooking method, skin not eaten | survey | 2705954 |
| 2 | **0.9638** | 0.8817 | Chicken, broiler or fryers, breast, skinless, boneless, meat only, cooked, braised | foundation | 331960 |
| 3 | **0.9408** | 0.9593 | Chicken breast, baked, broiled, or roasted, skin not eaten, from raw | survey | 2705956 |
| 4 | **0.8549** | 0.9482 | Chicken breast, NS as to cooking method, skin eaten | survey | 2705953 |
| 5 | **0.8056** | 0.8785 | Chicken, breast, boneless, skinless, raw | foundation | 2646170 |
| 6 | **0.8044** | 0.9557 | Chicken breast, baked or broiled, skin not eaten, from pre-cooked | survey | 2705958 |
| 7 | **0.8007** | 0.9478 | Chicken breast, baked, broiled, or roasted with marinade, skin not eaten, from raw | survey | 2705962 |
| 8 | **0.6179** | 0.8602 | Chicken, NS as to part, baked, broiled, or roasted, NS as to skin eaten | survey | 2705932 |
| 9 | **0.5946** | 0.9402 | Chicken breast, baked or broiled, skin not eaten, from fast food / restaurant | survey | 2705960 |
| 10 | **0.5875** | 0.9440 | Chicken breast, baked, broiled, or roasted, skin eaten, from raw | survey | 2705955 |

**🎯 Best Match**: Chicken breast, NS as to cooking method, skin not eaten
- **Rerank Score**: 0.9800
- **Stage1 Score**: 0.9574
- **Source**: survey
- **FDC ID**: 2705954

---

### Query 10: red wine | ready-to-serve

**Weight**: 150g, **Confidence**: 0.95

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9327 | Wine, red | survey | 2710688 |
| 2 | 0.9145 | Wine, light | survey | 2710693 |
| 3 | 0.9141 | Wine, white | survey | 2710689 |
| 4 | 0.9117 | Wine, rose | survey | 2710690 |
| 5 | 0.9035 | Wine, sparkling | survey | 2710687 |
| 6 | 0.8929 | Wine, nonalcoholic | survey | 2710609 |
| 7 | 0.8888 | Wine, dessert, sweet | survey | 2710692 |
| 8 | 0.8825 | Wine, rice | survey | 2710691 |
| 9 | 0.8297 | Wine cooler | survey | 2710694 |
| 10 | 0.8130 | Wine spritzer | survey | 2710697 |
| 11 | 0.8061 | Sangria, red | survey | 2710695 |
| 12 | 0.8059 | Grape juice, 100% | survey | 2709325 |
| 13 | 0.7854 | Sangria, white | survey | 2710696 |
| 14 | 0.7776 | Grape juice, white, with added vitamin C, from concentrate, shelf stable | foundation | 2003593 |
| 15 | 0.7728 | Grape juice, 100%, with calcium added | survey | 2709326 |
| 16 | 0.7700 | Grape juice, purple, with added vitamin C, from concentrate, shelf stable | foundation | 2003592 |
| 17 | 0.7684 | Whiskey | survey | 2710700 |
| 18 | 0.7644 | Grape juice drink, light | survey | 2710589 |
| 19 | 0.7528 | Beer | survey | 2710616 |
| 20 | 0.7516 | Whiskey and water | survey | 2710656 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9975** | 0.9327 | Wine, red | survey | 2710688 |
| 2 | **0.2082** | 0.9145 | Wine, light | survey | 2710693 |
| 3 | **0.1500** | 0.8061 | Sangria, red | survey | 2710695 |
| 4 | **0.0637** | 0.8825 | Wine, rice | survey | 2710691 |
| 5 | **0.0534** | 0.8888 | Wine, dessert, sweet | survey | 2710692 |
| 6 | **0.0385** | 0.9117 | Wine, rose | survey | 2710690 |
| 7 | **0.0346** | 0.9035 | Wine, sparkling | survey | 2710687 |
| 8 | **0.0237** | 0.8130 | Wine spritzer | survey | 2710697 |
| 9 | **0.0206** | 0.9141 | Wine, white | survey | 2710689 |
| 10 | **0.0164** | 0.8929 | Wine, nonalcoholic | survey | 2710609 |

**🎯 Best Match**: Wine, red
- **Rerank Score**: 0.9975
- **Stage1 Score**: 0.9327
- **Source**: survey
- **FDC ID**: 2710688

---

### Query 11: beef sirloin | cooked, roasted

**Weight**: 180g, **Confidence**: 0.9

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9023 | Beef, roast | survey | 2705847 |
| 2 | 0.8869 | Beef, loin, tenderloin roast, separable lean only, boneless, trimmed to 0" fat, select, cooked, roasted | foundation | 746758 |
| 3 | 0.8852 | Beef, pot roast | survey | 2705848 |
| 4 | 0.8806 | Beef, steak, sirloin, lean only eaten | survey | 2705834 |
| 5 | 0.8799 | Beef, bacon, cooked | survey | 2705856 |
| 6 | 0.8780 | Beef, steak, sirloin, NS as to fat eaten | survey | 2705832 |
| 7 | 0.8777 | Beef, top sirloin steak, raw | foundation | 2727574 |
| 8 | 0.8775 | Beef, steak, tenderloin | survey | 2705841 |
| 9 | 0.8772 | Beef, steak, sirloin, lean and fat eaten | survey | 2705833 |
| 10 | 0.8723 | Beef, shortribs | survey | 2705845 |
| 11 | 0.8705 | Beef, corned | survey | 2705850 |
| 12 | 0.8700 | Beef, steak, cube | survey | 2705826 |
| 13 | 0.8683 | Beef, roast, hash | survey | 2706476 |
| 14 | 0.8679 | Beef, dried, chipped, cooked in fat | survey | 2705859 |
| 15 | 0.8677 | Beef, round, eye of round roast, boneless, separable lean only, trimmed to 0" fat, select, raw | foundation | 746760 |
| 16 | 0.8677 | Beef, steak, flank | survey | 2705827 |
| 17 | 0.8668 | Beef, brisket | survey | 2705851 |
| 18 | 0.8660 | Beef, for use with vegetables | survey | 2710241 |
| 19 | 0.8638 | Beef, round, top round roast, boneless, separable lean only, trimmed to 0" fat, select, raw | foundation | 746761 |
| 20 | 0.8635 | Beef, stew meat | survey | 2705849 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9185** | 0.9023 | Beef, roast | survey | 2705847 |
| 2 | **0.8615** | 0.8869 | Beef, loin, tenderloin roast, separable lean only, boneless, trimmed to 0" fat, select, cooked, roasted | foundation | 746758 |
| 3 | **0.5006** | 0.8780 | Beef, steak, sirloin, NS as to fat eaten | survey | 2705832 |
| 4 | **0.4881** | 0.8806 | Beef, steak, sirloin, lean only eaten | survey | 2705834 |
| 5 | **0.4369** | 0.8772 | Beef, steak, sirloin, lean and fat eaten | survey | 2705833 |
| 6 | **0.2082** | 0.8598 | Beef, chuck, roast, boneless, choice, raw | foundation | 2646174 |
| 7 | **0.1551** | 0.8683 | Beef, roast, hash | survey | 2706476 |
| 8 | **0.1500** | 0.8458 | Beef, steak, NFS | survey | 2705824 |
| 9 | **0.0815** | 0.8485 | Beef, steak, strip, NS as to fat eaten | survey | 2705835 |
| 10 | **0.0706** | 0.8608 | Beef, short loin, t-bone steak, bone-in, separable lean only, trimmed to 1/8" fat, choice, cooked, grilled | foundation | 746763 |

**🎯 Best Match**: Beef, roast
- **Rerank Score**: 0.9185
- **Stage1 Score**: 0.9023
- **Source**: survey
- **FDC ID**: 2705847

---

### Query 12: caramelized onion relish | cooked

**Weight**: 40g, **Confidence**: 0.8

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.8040 | Onions, cooked, as ingredient | survey | 2710796 |
| 2 | 0.7967 | Onions, cooked, fat added | survey | 2709951 |
| 3 | 0.7964 | Onions, pearl, cooked | survey | 2709952 |
| 4 | 0.7959 | Onions, green, cooked | survey | 2709953 |
| 5 | 0.7928 | Onions, cooked, no added fat | survey | 2709950 |
| 6 | 0.7864 | Onion dip, yogurt based | survey | 2705445 |
| 7 | 0.7825 | Onion dip, regular | survey | 2705621 |
| 8 | 0.7815 | Onion dip, light | survey | 2705622 |
| 9 | 0.7804 | Relish, pickle | survey | 2710079 |
| 10 | 0.7757 | Relish, corn | survey | 2710073 |
| 11 | 0.7706 | Onions, for use on a sandwich | survey | 2710252 |
| 12 | 0.7675 | Cranberry sauce | survey | 2709280 |
| 13 | 0.7646 | Onions, raw | survey | 2709795 |
| 14 | 0.7639 | Duck sauce | survey | 2710298 |
| 15 | 0.7624 | Onions, red, raw | foundation | 790577 |
| 16 | 0.7550 | Horseradish sauce | survey | 2710174 |
| 17 | 0.7539 | Fried onion rings | survey | 2710055 |
| 18 | 0.7498 | Peppers and onions, cooked, no added fat | survey | 2710010 |
| 19 | 0.7484 | Peppers and onions, cooked, fat added | survey | 2710011 |
| 20 | 0.7462 | Pickled sausage | survey | 2706204 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9868** | 0.8040 | Onions, cooked, as ingredient | survey | 2710796 |
| 2 | **0.9497** | 0.7959 | Onions, green, cooked | survey | 2709953 |
| 3 | **0.9208** | 0.7928 | Onions, cooked, no added fat | survey | 2709950 |
| 4 | **0.8429** | 0.7967 | Onions, cooked, fat added | survey | 2709951 |
| 5 | **0.8376** | 0.7964 | Onions, pearl, cooked | survey | 2709952 |
| 6 | **0.2254** | 0.7119 | Mirepoix, cooked, as ingredient | survey | 2710809 |
| 7 | **0.2173** | 0.7706 | Onions, for use on a sandwich | survey | 2710252 |
| 8 | **0.1848** | 0.7804 | Relish, pickle | survey | 2710079 |
| 9 | **0.1082** | 0.4476 | Chutney | survey | 2709309 |
| 10 | **0.0927** | 0.7757 | Relish, corn | survey | 2710073 |

**🎯 Best Match**: Onions, cooked, as ingredient
- **Rerank Score**: 0.9868
- **Stage1 Score**: 0.8040
- **Source**: survey
- **FDC ID**: 2710796

---

### Query 13: green onion | raw

**Weight**: 10g, **Confidence**: 0.9

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9667 | Green onion, (scallion), bulb and greens, root removed, raw | foundation | 2727585 |
| 2 | 0.8734 | Garlic, raw | foundation | 1104647 |
| 3 | 0.8734 | Garlic, raw | survey | 2709786 |
| 4 | 0.8578 | Shallots, bulb, peeled, root removed, raw | foundation | 2727586 |
| 5 | 0.8556 | Onions, raw | survey | 2709795 |
| 6 | 0.8554 | Cilantro, raw | survey | 2709782 |
| 7 | 0.8476 | Leeks, bulb and greens, root removed, raw | foundation | 2727584 |
| 8 | 0.8460 | Onions, green, raw | survey | 2709794 |
| 9 | 0.8432 | Leeks | survey | 2709935 |
| 10 | 0.8350 | Parsley, raw | survey | 2709796 |
| 11 | 0.8348 | Onions, white, raw | foundation | 1104962 |
| 12 | 0.8320 | Onions, red, raw | foundation | 790577 |
| 13 | 0.8227 | Fennel bulb, raw | survey | 2709779 |
| 14 | 0.8222 | Onions, yellow, raw | foundation | 790646 |
| 15 | 0.8161 | Garlic, cooked | survey | 2709932 |
| 16 | 0.8142 | Spinach, raw | survey | 2709614 |
| 17 | 0.8125 | Watercress, raw | survey | 2709639 |
| 18 | 0.8097 | Onions, for use on a sandwich | survey | 2710252 |
| 19 | 0.8077 | Onions, cooked, no added fat | survey | 2709950 |
| 20 | 0.8049 | Asparagus, raw | survey | 2709767 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9958** | 0.9667 | Green onion, (scallion), bulb and greens, root removed, raw | foundation | 2727585 |
| 2 | **0.7326** | 0.8460 | Onions, green, raw | survey | 2709794 |
| 3 | **0.6132** | 0.8476 | Leeks, bulb and greens, root removed, raw | foundation | 2727584 |
| 4 | **0.5296** | 0.8556 | Onions, raw | survey | 2709795 |
| 5 | **0.2798** | 0.8348 | Onions, white, raw | foundation | 1104962 |
| 6 | **0.1956** | 0.8432 | Leeks | survey | 2709935 |
| 7 | **0.1613** | 0.8578 | Shallots, bulb, peeled, root removed, raw | foundation | 2727586 |
| 8 | **0.1571** | 0.8222 | Onions, yellow, raw | foundation | 790646 |
| 9 | **0.1339** | 0.8320 | Onions, red, raw | foundation | 790577 |
| 10 | **0.0656** | 0.8097 | Onions, for use on a sandwich | survey | 2710252 |

**🎯 Best Match**: Green onion, (scallion), bulb and greens, root removed, raw
- **Rerank Score**: 0.9958
- **Stage1 Score**: 0.9667
- **Source**: foundation
- **FDC ID**: 2727585

---

### Query 14: potatoes | roasted

**Weight**: 150g, **Confidence**: 0.95

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9665 | Potato, roasted, ready-to-heat | survey | 2709415 |
| 2 | 0.9607 | Potato, roasted, NFS | survey | 2709402 |
| 3 | 0.9586 | Potato, roasted, from fresh, peel not eaten, no added fat | survey | 2709411 |
| 4 | 0.9566 | Potato, roasted, from fresh, peel not eaten, fat added, NS as to fat type | survey | 2709410 |
| 5 | 0.9525 | Potato, roasted, from fresh, peel eaten, no added fat | survey | 2709404 |
| 6 | 0.9507 | Potato, roasted, from fresh, peel not eaten, made with oil | survey | 2709412 |
| 7 | 0.9501 | Potato, roasted, from fresh, peel not eaten, NS as to fat | survey | 2709409 |
| 8 | 0.9499 | Potato, roasted, from fresh, peel eaten, fat added, NS as to fat type | survey | 2709405 |
| 9 | 0.9472 | Potato, roasted, from fresh, peel eaten, made with oil | survey | 2709406 |
| 10 | 0.9470 | Potato, home fries, with vegetables | survey | 2709476 |
| 11 | 0.9427 | Potato, roasted, from fresh, peel not eaten, made with butter | survey | 2709413 |
| 12 | 0.9413 | Potato, roasted, from fresh, peel eaten, made with butter | survey | 2709407 |
| 13 | 0.9394 | Potato, roasted, from fresh, peel eaten, NS as to fat | survey | 2709403 |
| 14 | 0.9379 | Potato, baked, peel eaten, with butter | survey | 2709525 |
| 15 | 0.9361 | Potato, baked, peel eaten, with meat | survey | 2709528 |
| 16 | 0.9359 | Potato, roasted, from fresh, peel not eaten, made with margarine | survey | 2709414 |
| 17 | 0.9348 | Potato, cooked, as ingredient | survey | 2710790 |
| 18 | 0.9346 | Potato, baked, peel eaten, with vegetables | survey | 2709530 |
| 19 | 0.9322 | Potato, boiled, ready-to-heat | survey | 2709386 |
| 20 | 0.9319 | Potato, roasted, from fresh, peel eaten, made with margarine | survey | 2709408 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9876** | 0.9607 | Potato, roasted, NFS | survey | 2709402 |
| 2 | **0.9855** | 0.9501 | Potato, roasted, from fresh, peel not eaten, NS as to fat | survey | 2709409 |
| 3 | **0.9850** | 0.9586 | Potato, roasted, from fresh, peel not eaten, no added fat | survey | 2709411 |
| 4 | **0.9797** | 0.9525 | Potato, roasted, from fresh, peel eaten, no added fat | survey | 2709404 |
| 5 | **0.9790** | 0.9394 | Potato, roasted, from fresh, peel eaten, NS as to fat | survey | 2709403 |
| 6 | **0.9767** | 0.9566 | Potato, roasted, from fresh, peel not eaten, fat added, NS as to fat type | survey | 2709410 |
| 7 | **0.9763** | 0.9665 | Potato, roasted, ready-to-heat | survey | 2709415 |
| 8 | **0.9736** | 0.9507 | Potato, roasted, from fresh, peel not eaten, made with oil | survey | 2709412 |
| 9 | **0.9684** | 0.9499 | Potato, roasted, from fresh, peel eaten, fat added, NS as to fat type | survey | 2709405 |
| 10 | **0.9669** | 0.9472 | Potato, roasted, from fresh, peel eaten, made with oil | survey | 2709406 |

**🎯 Best Match**: Potato, roasted, NFS
- **Rerank Score**: 0.9876
- **Stage1 Score**: 0.9607
- **Source**: survey
- **FDC ID**: 2709402

---

### Query 15: asparagus | roasted

**Weight**: 100g, **Confidence**: 0.95

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9511 | Asparagus, fresh, cooked with oil | survey | 2709841 |
| 2 | 0.9418 | Asparagus, fresh, cooked, no added fat | survey | 2709834 |
| 3 | 0.9399 | Asparagus, frozen, cooked with oil | survey | 2709843 |
| 4 | 0.9387 | Asparagus, fresh, cooked with butter or margarine | survey | 2709842 |
| 5 | 0.9332 | Asparagus, canned, cooked with oil | survey | 2709845 |
| 6 | 0.9309 | Asparagus, frozen, cooked with butter or margarine | survey | 2709844 |
| 7 | 0.9300 | Asparagus, NS as to form, cooked | survey | 2709837 |
| 8 | 0.9271 | Asparagus, frozen, cooked, no added fat | survey | 2709835 |
| 9 | 0.9265 | Asparagus, green, raw | foundation | 2710823 |
| 10 | 0.9262 | Asparagus, fresh, cooked, fat added, NS as to fat type | survey | 2709838 |
| 11 | 0.9258 | Asparagus, raw | survey | 2709767 |
| 12 | 0.9241 | Asparagus, canned, cooked with butter or margarine | survey | 2709846 |
| 13 | 0.9221 | Asparagus, canned, cooked, no added fat | survey | 2709836 |
| 14 | 0.9193 | Asparagus, frozen, cooked, fat added, NS as to fat type | survey | 2709839 |
| 15 | 0.9160 | Asparagus, canned, cooked, fat added, NS as to fat type | survey | 2709840 |
| 16 | 0.8152 | Spinach, fresh, cooked with oil | survey | 2709618 |
| 17 | 0.8136 | Spinach, fresh, cooked, no added fat | survey | 2709615 |
| 18 | 0.8132 | Spinach, creamed | survey | 2709628 |
| 19 | 0.8132 | Brussels sprouts, fresh, cooked, no added fat | survey | 2709881 |
| 20 | 0.8110 | Broccoli, fresh, cooked, no added fat | survey | 2709645 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9679** | 0.9300 | Asparagus, NS as to form, cooked | survey | 2709837 |
| 2 | **0.9390** | 0.9511 | Asparagus, fresh, cooked with oil | survey | 2709841 |
| 3 | **0.9344** | 0.9418 | Asparagus, fresh, cooked, no added fat | survey | 2709834 |
| 4 | **0.8808** | 0.9387 | Asparagus, fresh, cooked with butter or margarine | survey | 2709842 |
| 5 | **0.7649** | 0.9262 | Asparagus, fresh, cooked, fat added, NS as to fat type | survey | 2709838 |
| 6 | **0.5436** | 0.9399 | Asparagus, frozen, cooked with oil | survey | 2709843 |
| 7 | **0.5426** | 0.9271 | Asparagus, frozen, cooked, no added fat | survey | 2709835 |
| 8 | **0.3739** | 0.9265 | Asparagus, green, raw | foundation | 2710823 |
| 9 | **0.3390** | 0.9309 | Asparagus, frozen, cooked with butter or margarine | survey | 2709844 |
| 10 | **0.3141** | 0.9258 | Asparagus, raw | survey | 2709767 |

**🎯 Best Match**: Asparagus, NS as to form, cooked
- **Rerank Score**: 0.9679
- **Stage1 Score**: 0.9300
- **Source**: survey
- **FDC ID**: 2709837

---

### Query 16: creamer | with herbs

**Weight**: 30g, **Confidence**: 0.8

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.8704 | Coffee creamer, powder, flavored | survey | 2705607 |
| 2 | 0.8700 | Coffee creamer, powder | survey | 2705606 |
| 3 | 0.8683 | Coffee creamer, liquid, flavored | survey | 2705601 |
| 4 | 0.8643 | Coffee creamer, liquid | survey | 2705600 |
| 5 | 0.8589 | Coffee creamer, liquid, fat free, flavored | survey | 2705603 |
| 6 | 0.8564 | Coffee creamer, liquid, sugar free, flavored | survey | 2705605 |
| 7 | 0.8527 | Coffee creamer,powder, sugar free, flavored | survey | 2705609 |
| 8 | 0.8521 | Coffee creamer, liquid, fat free, sugar free, flavored | survey | 2705604 |
| 9 | 0.8496 | Coffee creamer, powder, fat free | survey | 2705608 |
| 10 | 0.8451 | Coffee creamer, soy, liquid | survey | 2705610 |
| 11 | 0.8448 | Coffee creamer, liquid, fat free | survey | 2705602 |
| 12 | 0.8411 | Coffee creamer, NFS | survey | 2705599 |
| 13 | 0.8025 | Cream, half and half, flavored | survey | 2705595 |
| 14 | 0.8019 | Cream, half and half | survey | 2705594 |
| 15 | 0.7990 | Cream, light | survey | 2705593 |
| 16 | 0.7908 | Cream, whipped | survey | 2705598 |
| 17 | 0.7903 | Cream, half and half, fat free | survey | 2705596 |
| 18 | 0.7835 | Coffee and chicory, brewed | survey | 2710470 |
| 19 | 0.7833 | Cream, heavy | foundation | 2346386 |
| 20 | 0.7833 | Cream, heavy | survey | 2705597 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9585** | 0.8683 | Coffee creamer, liquid, flavored | survey | 2705601 |
| 2 | **0.9433** | 0.8643 | Coffee creamer, liquid | survey | 2705600 |
| 3 | **0.9284** | 0.8411 | Coffee creamer, NFS | survey | 2705599 |
| 4 | **0.9149** | 0.8589 | Coffee creamer, liquid, fat free, flavored | survey | 2705603 |
| 5 | **0.8732** | 0.8521 | Coffee creamer, liquid, fat free, sugar free, flavored | survey | 2705604 |
| 6 | **0.8715** | 0.8704 | Coffee creamer, powder, flavored | survey | 2705607 |
| 7 | **0.8322** | 0.8564 | Coffee creamer, liquid, sugar free, flavored | survey | 2705605 |
| 8 | **0.7649** | 0.8451 | Coffee creamer, soy, liquid | survey | 2705610 |
| 9 | **0.7564** | 0.8448 | Coffee creamer, liquid, fat free | survey | 2705602 |
| 10 | **0.7387** | 0.8527 | Coffee creamer,powder, sugar free, flavored | survey | 2705609 |

**🎯 Best Match**: Coffee creamer, liquid, flavored
- **Rerank Score**: 0.9585
- **Stage1 Score**: 0.8683
- **Source**: survey
- **FDC ID**: 2705601

---

### Query 17: lettuce | fresh

**Weight**: 50g, **Confidence**: 0.85

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9724 | Lettuce, raw | survey | 2709789 |
| 2 | 0.9672 | Lettuce, iceberg, raw | foundation | 2346388 |
| 3 | 0.9642 | Lettuce, leaf, green, raw | foundation | 2346391 |
| 4 | 0.9630 | Lettuce, romaine, green, raw | foundation | 2346389 |
| 5 | 0.9612 | Lettuce, cos or romaine, raw | foundation | 746769 |
| 6 | 0.9603 | Lettuce, arugula, raw | survey | 2709791 |
| 7 | 0.9570 | Lettuce, for use on a sandwich | survey | 2710250 |
| 8 | 0.9531 | Lettuce, leaf, red, raw | foundation | 2346390 |
| 9 | 0.9421 | Lettuce, Boston, raw | survey | 2709790 |
| 10 | 0.9421 | Lettuce, cooked | survey | 2709949 |
| 11 | 0.9365 | Lettuce, salad with cheese, tomato and/or carrots, with or without other vegetables, no dressing | survey | 2709825 |
| 12 | 0.9329 | Lettuce, salad with assorted vegetables including tomatoes and/or carrots, no dressing | survey | 2709822 |
| 13 | 0.9300 | Lettuce, salad with avocado, tomato, and/or carrots, with or without other vegetables, no dressing | survey | 2709824 |
| 14 | 0.9298 | Lettuce, salad with egg, tomato, and/or carrots, with or without other vegetables, no dressing | survey | 2709826 |
| 15 | 0.9256 | Lettuce, salad with egg, cheese, tomato, and/or carrots, with or without other vegetables, no dressing | survey | 2709827 |
| 16 | 0.9224 | Lettuce, salad with assorted vegetables excluding tomatoes and carrots, no dressing | survey | 2709823 |
| 17 | 0.9167 | Lettuce, wilted, with bacon dressing | survey | 2709828 |
| 18 | 0.8896 | Romaine lettuce, raw | survey | 2709590 |
| 19 | 0.8487 | Arugula, baby, raw | foundation | 2710822 |
| 20 | 0.8400 | Watercress, raw | survey | 2709639 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9978** | 0.9724 | Lettuce, raw | survey | 2709789 |
| 2 | **0.9900** | 0.9642 | Lettuce, leaf, green, raw | foundation | 2346391 |
| 3 | **0.9425** | 0.9612 | Lettuce, cos or romaine, raw | foundation | 746769 |
| 4 | **0.9060** | 0.8896 | Romaine lettuce, raw | survey | 2709590 |
| 5 | **0.8376** | 0.9672 | Lettuce, iceberg, raw | foundation | 2346388 |
| 6 | **0.8117** | 0.9531 | Lettuce, leaf, red, raw | foundation | 2346390 |
| 7 | **0.7813** | 0.9630 | Lettuce, romaine, green, raw | foundation | 2346389 |
| 8 | **0.7592** | 0.9421 | Lettuce, Boston, raw | survey | 2709790 |
| 9 | **0.7402** | 0.8236 | Mixed salad greens, raw | survey | 2709792 |
| 10 | **0.5894** | 0.9570 | Lettuce, for use on a sandwich | survey | 2710250 |

**🎯 Best Match**: Lettuce, raw
- **Rerank Score**: 0.9978
- **Stage1 Score**: 0.9724
- **Source**: survey
- **FDC ID**: 2709789

---

### Query 18: tomato | fresh

**Weight**: 45g, **Confidence**: 0.85

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9644 | Tomatoes, raw | survey | 2709719 |
| 2 | 0.9622 | Tomatoes, fresh, cooked | survey | 2709721 |
| 3 | 0.9419 | Tomato, roma | foundation | 1999634 |
| 4 | 0.9392 | Tomatoes, grape, raw | foundation | 321360 |
| 5 | 0.9309 | Tomatoes, whole, canned, solids and liquids, with salt added | foundation | 2685578 |
| 6 | 0.9297 | Tomato, green, pickled | survey | 2709726 |
| 7 | 0.9282 | Tomatoes, for use on a sandwich | survey | 2710255 |
| 8 | 0.9247 | Tomatoes, canned, red, ripe, diced | foundation | 333281 |
| 9 | 0.9242 | Tomatoes, NS as to form, cooked | survey | 2709720 |
| 10 | 0.9234 | Tomatoes, crushed, canned | foundation | 2685581 |
| 11 | 0.9220 | Tomato, puree, canned | foundation | 2685582 |
| 12 | 0.9216 | Tomatoes, canned, cooked | survey | 2709722 |
| 13 | 0.9166 | Tomatoes, cooked, as ingredient | survey | 2710795 |
| 14 | 0.9146 | Tomatoes, scalloped | survey | 2709723 |
| 15 | 0.9119 | Tomato, paste, canned, without salt added | foundation | 2685580 |
| 16 | 0.9080 | Tomato, sauce, canned, with salt added | foundation | 2685579 |
| 17 | 0.9058 | Tomatoes, canned, reduced sodium, cooked | survey | 2709724 |
| 18 | 0.8849 | Tomatillos, dehusked, raw | foundation | 2727582 |
| 19 | 0.8533 | Tomato juice, 100% | survey | 2709728 |
| 20 | 0.8356 | Sun-dried tomatoes | survey | 2709727 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9957** | 0.9644 | Tomatoes, raw | survey | 2709719 |
| 2 | **0.6316** | 0.9622 | Tomatoes, fresh, cooked | survey | 2709721 |
| 3 | **0.1981** | 0.9392 | Tomatoes, grape, raw | foundation | 321360 |
| 4 | **0.0981** | 0.9419 | Tomato, roma | foundation | 1999634 |
| 5 | **0.0815** | 0.9282 | Tomatoes, for use on a sandwich | survey | 2710255 |
| 6 | **0.0601** | 0.9242 | Tomatoes, NS as to form, cooked | survey | 2709720 |
| 7 | **0.0526** | 0.9166 | Tomatoes, cooked, as ingredient | survey | 2710795 |
| 8 | **0.0293** | 0.7906 | Tomatoes as ingredient in omelet | survey | 2710807 |
| 9 | **0.0264** | 0.8533 | Tomato juice, 100% | survey | 2709728 |
| 10 | **0.0141** | 0.8162 | Fried green tomatoes | survey | 2709725 |

**🎯 Best Match**: Tomatoes, raw
- **Rerank Score**: 0.9957
- **Stage1 Score**: 0.9644
- **Source**: survey
- **FDC ID**: 2709719

---

### Query 19: onion | fresh

**Weight**: 25g, **Confidence**: 0.85

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9645 | Onions, raw | survey | 2709795 |
| 2 | 0.9503 | Onions, white, raw | foundation | 1104962 |
| 3 | 0.9481 | Onions, green, raw | survey | 2709794 |
| 4 | 0.9471 | Onions, red, raw | foundation | 790577 |
| 5 | 0.9367 | Onions, for use on a sandwich | survey | 2710252 |
| 6 | 0.9350 | Onions, cooked, no added fat | survey | 2709950 |
| 7 | 0.9331 | Onions, yellow, raw | foundation | 790646 |
| 8 | 0.9124 | Onions, cooked, fat added | survey | 2709951 |
| 9 | 0.9082 | Onions, cooked, as ingredient | survey | 2710796 |
| 10 | 0.9071 | Onions, green, cooked | survey | 2709953 |
| 11 | 0.9029 | Onions, pearl, cooked | survey | 2709952 |
| 12 | 0.8564 | Shallots, bulb, peeled, root removed, raw | foundation | 2727586 |
| 13 | 0.8406 | Garlic, raw | foundation | 1104647 |
| 14 | 0.8406 | Garlic, raw | survey | 2709786 |
| 15 | 0.8359 | Leeks | survey | 2709935 |
| 16 | 0.8303 | Green onion, (scallion), bulb and greens, root removed, raw | foundation | 2727585 |
| 17 | 0.8250 | Fried onion rings | survey | 2710055 |
| 18 | 0.8247 | Peppers and onions, cooked, no added fat | survey | 2710010 |
| 19 | 0.8247 | Fennel bulb, raw | survey | 2709779 |
| 20 | 0.8228 | Onion flavored rings | survey | 2708245 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9966** | 0.9645 | Onions, raw | survey | 2709795 |
| 2 | **0.9334** | 0.9481 | Onions, green, raw | survey | 2709794 |
| 3 | **0.9325** | 0.9503 | Onions, white, raw | foundation | 1104962 |
| 4 | **0.8766** | 0.9331 | Onions, yellow, raw | foundation | 790646 |
| 5 | **0.6549** | 0.9471 | Onions, red, raw | foundation | 790577 |
| 6 | **0.4535** | 0.8303 | Green onion, (scallion), bulb and greens, root removed, raw | foundation | 2727585 |
| 7 | **0.2494** | 0.9367 | Onions, for use on a sandwich | survey | 2710252 |
| 8 | **0.1824** | 0.9350 | Onions, cooked, no added fat | survey | 2709950 |
| 9 | **0.1259** | 0.9082 | Onions, cooked, as ingredient | survey | 2710796 |
| 10 | **0.0427** | 0.9071 | Onions, green, cooked | survey | 2709953 |

**🎯 Best Match**: Onions, raw
- **Rerank Score**: 0.9966
- **Stage1 Score**: 0.9645
- **Source**: survey
- **FDC ID**: 2709795

---

### Query 20: carrot | shredded, fresh

**Weight**: 20g, **Confidence**: 0.85

#### Stage 1: Retriever

Retrieved **100** candidates using weighted FAISS search

<details>
<summary>View Top 20 Stage 1 Candidates</summary>

| Rank | Score | Description | Source | FDC ID |
|------|-------|-------------|--------|--------|
| 1 | 0.9520 | Carrots, raw | survey | 2709660 |
| 2 | 0.9507 | Carrots, fresh, cooked, no added fat | survey | 2709664 |
| 3 | 0.9482 | Carrots, frozen, unprepared | foundation | 746764 |
| 4 | 0.9421 | Carrots, mature, raw | foundation | 2258586 |
| 5 | 0.9402 | Carrots, fresh, cooked, fat added, NS as to fat type | survey | 2709670 |
| 6 | 0.9392 | Carrots, fresh, cooked with oil | survey | 2709667 |
| 7 | 0.9358 | Carrots, fresh, cooked with butter or margarine | survey | 2709668 |
| 8 | 0.9336 | Carrots, frozen, cooked with oil | survey | 2709673 |
| 9 | 0.9325 | Carrots, frozen, cooked, no added fat | survey | 2709665 |
| 10 | 0.9285 | Carrots, frozen, cooked, fat added, NS as to fat type | survey | 2709671 |
| 11 | 0.9274 | Carrots, canned, cooked with oil | survey | 2709675 |
| 12 | 0.9264 | Carrots, frozen, cooked with butter or margarine | survey | 2709674 |
| 13 | 0.9257 | Carrots, raw, salad | survey | 2709661 |
| 14 | 0.9251 | Carrots, canned, cooked, fat added, NS as to fat type | survey | 2709672 |
| 15 | 0.9236 | Carrots, canned, cooked with butter or margarine | survey | 2709676 |
| 16 | 0.9231 | Carrots, canned, cooked, no added fat | survey | 2709666 |
| 17 | 0.9224 | Carrots, NS as to form, cooked | survey | 2709669 |
| 18 | 0.9211 | Carrots, canned, reduced sodium, cooked with oil | survey | 2709680 |
| 19 | 0.9185 | Carrots, canned, reduced sodium, cooked with butter or margarine | survey | 2709681 |
| 20 | 0.9185 | Carrots, cooked, as ingredient | survey | 2710793 |

</details>

#### Stage 2: Reranker

**Top 10 Results** after LLM-based reranking:

| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |
|------|--------------|--------------|-------------|--------|--------|
| 🏆1 | **0.9787** | 0.9520 | Carrots, raw | survey | 2709660 |
| 2 | **0.9219** | 0.9257 | Carrots, raw, salad | survey | 2709661 |
| 3 | **0.7130** | 0.9421 | Carrots, mature, raw | foundation | 2258586 |
| 4 | **0.4196** | 0.9507 | Carrots, fresh, cooked, no added fat | survey | 2709664 |
| 5 | **0.3451** | 0.9064 | Carrots, baby, raw | foundation | 2258587 |
| 6 | **0.2942** | 0.9139 | Carrots, raw, salad with apples | survey | 2709662 |
| 7 | **0.1931** | 0.9185 | Carrots, cooked, as ingredient | survey | 2710793 |
| 8 | **0.1510** | 0.9358 | Carrots, fresh, cooked with butter or margarine | survey | 2709668 |
| 9 | **0.1375** | 0.9392 | Carrots, fresh, cooked with oil | survey | 2709667 |
| 10 | **0.1192** | 0.9224 | Carrots, NS as to form, cooked | survey | 2709669 |

**🎯 Best Match**: Carrots, raw
- **Rerank Score**: 0.9787
- **Stage1 Score**: 0.9520
- **Source**: survey
- **FDC ID**: 2709660

---

## Summary

### Pipeline Statistics

| Metric | Value |
|--------|-------|
| Total Images Processed | 50 |
| Total Queries Generated | 20 |
| Average Confidence | 0.89 |
| Stage 1 Candidates per Query | 100 |
| Stage 2 Top-K | 10 |

### Algorithm Summary

| Stage | Algorithm | Model | Purpose |
|-------|-----------|-------|---------|
| VLM | Vision-Language Analysis | Qwen3-VL-235B-A22B-Thinking | 画像から食品情報を抽出 |
| Normalization | Text Processing | Rule-based | 表記ゆれを吸収 |
| Stage 1 | Two-Stream Weighted Search | Qwen3-Embedding-8B + FAISS | 100候補を高速取得 |
| Stage 2 | LLM-based Reranking | Qwen3-Reranker-8B | Top 10を精密選出 |

### Accuracy

- **形式的精度**: 70% (14/20 完全一致)
- **栄養学的精度**: **100% (20/20 許容可能)**

詳細は `tests/nutritional_evaluation.py` を参照
