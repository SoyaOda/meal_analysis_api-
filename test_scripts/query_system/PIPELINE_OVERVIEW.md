# 全体パイプライン概要

## アーキテクチャ図

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STEP 1: VLM処理                              │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
    test_images/*.jpg  →  test_vlm_all_images.py  →  VLM Result JSON
                                  │
                                  │ --freeform-usda フラグ
                                  ↓
                    freeform_prompt_usda_format_ver.txt
                          (VLMプロンプト)
                                  ↓
                        DeepInfra API (VLM)
                        (Qwen3-VL-235B-A22B-Thinking)
                                  ↓
                    vlm_test_results_*.json
                    {
                      "dishes": [
                        {
                          "main_food": {
                            "search_name": "chicken breast",
                            "description": "grilled, boneless",
                            "weight_g": 150,
                            "confidence": 0.9
                          },
                          "extras": [...]
                        }
                      ]
                    }

┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 2: クエリ抽出                                │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
    vlm_test_results_*.json  →  extract_vlm_queries.py  →  test_queries.json
                                                              │
                    全main_food + extrasを抽出                 │
                    (今回: 125 main + 175 extras = 300クエリ)  │
                                                              ↓
                                                    test_queries.json
                                                    [
                                                      {
                                                        "search_name": "chicken breast",
                                                        "description": "grilled, boneless",
                                                        "weight_g": 150,
                                                        "confidence": 0.9,
                                                        "image_file": "test_food1.jpg",
                                                        "food_type": "main_food"
                                                      },
                                                      ...
                                                    ]

┌─────────────────────────────────────────────────────────────────────┐
│                 STEP 3: USDA DB検索 (2段階)                          │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
    test_queries.json  →  evaluate_300_full_only.py  →  USDA DB検索
                                  │
                                  ↓
                        FoodSearchPipeline.search()
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
            ┌───────▼────────┐         ┌───────▼────────┐
            │  Stage 1:       │         │  Stage 2:       │
            │  Embedding検索  │         │  Reranker       │
            └───────┬────────┘         └───────┬────────┘
                    │                           │
                    │ Two-Stream Weighted       │ BGE Reranker
                    │ Search (Full-only)        │ (DeepInfra API)
                    │                           │
                    │ weight_main=0.0           │ Field-labeled
                    │ weight_full=1.0           │ Templates
                    │                           │
                    │ "prosciutto sliced"       │ Query: [MAIN]prosciutto[/MAIN]
                    │       ↓                   │        [DESC]sliced[/DESC]
                    │ Top 40候補                │ Candidate: [MAIN]Ham, prosciutto[/MAIN]
                    └───────┬────────┘                    [DESC][/DESC]
                            │                           │
                            │                           │
                            └──────────┬────────────────┘
                                       ↓
                                Best Match Result
                                {
                                  "fdc_id": 2705879,
                                  "description": "Ham, prosciutto",
                                  "rerank_score": 0.9806,
                                  "stage1_score": 0.8768
                                }

┌─────────────────────────────────────────────────────────────────────┐
│                      STEP 4: 結果評価                                │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
    evaluation_results_300_full_only.json  →  analyze_nutrition_accuracy.py
                                                         ↓
                                              栄養学的カテゴリ分類:
                                              - PERFECT: 37件
                                              - ACCEPTABLE: 142件
                                              - MINOR_DIFFERENCE: 121件
                                              - MAJOR_DIFFERENCE: 0件
                                              - WRONG_FOOD: 0件

                                              → 栄養学的許容率: 100%
```

---

## 各コンポーネント詳細

### 1. VLM処理 (`test_vlm_all_images.py`)

**役割**: 食事画像をVLMに入力し、構造化されたJSON形式で食事情報を取得

**実行例**:
```bash
python test_scripts/test_vlm_all_images.py \
  --freeform-usda \
  --model Qwen/Qwen3-VL-235B-A22B-Thinking \
  --max-tokens 8192 \
  --parallel \
  --batch-size 5
```

**処理フロー**:
1. `test_images/`ディレクトリから画像を読み込み
2. `prompt_base/freeform_prompt_usda_format_ver.txt` をプロンプトとして使用
3. DeepInfra API経由でVLMを呼び出し
4. JSON形式で結果を取得 (main_food + extras構造)
5. `output/vlm_test_results_*.json` に保存

**プロンプトの特徴**:
- **USDA-friendly naming**: search_name (コア食材名) + description (調理法等の修飾語)
- **main_food/extras構造**:
  - main_food: 単一ユニットとして認識される料理 (e.g., "cheeseburger", "slice of pizza")
  - extras: 非標準の追加トッピング (e.g., extra bacon, avocado add-on)
- **重量推定**: weight_g で可食部重量をグラム単位で推定
- **信頼度**: confidence (0.0-1.0) で識別と重量の確実性を評価

**出力JSON構造**:
```json
{
  "test_metadata": {
    "model_id": "Qwen/Qwen3-VL-235B-A22B-Thinking",
    "prompt_type": "freeform_usda",
    "total_cost_usd": 0.xx
  },
  "results": [
    {
      "image_file": "test_food1.jpg",
      "success": true,
      "vlm_response": {
        "dishes": [
          {
            "main_food": {
              "search_name": "chicken breast",
              "description": "grilled, boneless, skinless",
              "weight_g": 150,
              "confidence": 0.9
            },
            "extras": [
              {
                "search_name": "mixed salad greens",
                "description": "raw",
                "weight_g": 50,
                "confidence": 0.85
              }
            ]
          }
        ]
      }
    }
  ]
}
```

---

### 2. クエリ抽出 (`extract_vlm_queries.py`)

**役割**: VLM結果JSONから検索用クエリ情報を抽出

**実行例**:
```bash
python test_scripts/query_system/scripts/extract_vlm_queries.py \
  /path/to/vlm_test_results_*.json
```

**処理フロー**:
1. VLM結果JSONを読み込み
2. 全dishes配列をループ
   - main_foodがあればクエリとして抽出
   - 各extrasもクエリとして抽出
3. `tests/data/test_queries.json` に保存

**抽出されるクエリ情報**:
```json
[
  {
    "search_name": "chicken breast",
    "description": "grilled, boneless, skinless",
    "weight_g": 150,
    "confidence": 0.9,
    "image_file": "test_food1.jpg",
    "dish_index": 0,
    "food_type": "main_food"
  },
  {
    "search_name": "mixed salad greens",
    "description": "raw",
    "weight_g": 50,
    "confidence": 0.85,
    "image_file": "test_food1.jpg",
    "dish_index": 0,
    "extra_index": 0,
    "food_type": "extra"
  }
]
```

**今回の結果**:
- 総クエリ数: 300
  - main_food: 125件
  - extras: 175件

---

### 3. USDA DB検索 (2段階パイプライン)

#### 3-1. Stage 1: Two-Stream Weighted Embedding検索 (`IndexSearcher`)

**役割**: FAISSインデックスを使った高速な近似最近傍探索

**アーキテクチャ**:
```python
# Two-Stream Weighted Search
# Main-only stream: "prosciutto" のみで検索
# Full stream: "prosciutto sliced" で検索

scores = weight_main * scores_main + weight_full * scores_full
# Full-only設定: weight_main=0.0, weight_full=1.0
```

**実装** (`src/index/searcher.py`):
```python
class IndexSearcher:
    def __init__(self, weight_main=0.6, weight_full=0.4):
        # Load FAISS indexes
        self.index_main = faiss.read_index("main_index.faiss")
        self.index_full = faiss.read_index("full_index.faiss")

        # Load embedding model
        self.embedding_model = SentenceTransformer("Qwen/Qwen3-Embedding-8B")

    def search(self, query_main, query_descriptors, top_k=40):
        # Build query texts
        text_main = normalize_text(build_main_only_text(query_main))
        text_full = normalize_text(build_full_text(query_main, query_descriptors))

        # Encode
        emb_main = self.embedding_model.encode(text_main)
        emb_full = self.embedding_model.encode(text_full)

        # Search both indexes
        k_search = min(top_k * 2, self.index_main.ntotal)
        scores_main, indices_main = self.index_main.search(emb_main, k_search)
        scores_full, indices_full = self.index_full.search(emb_full, k_search)

        # Combine scores
        combined_scores = {}
        for idx, score in zip(indices_main[0], scores_main[0]):
            combined_scores[idx] = self.weight_main * score
        for idx, score in zip(indices_full[0], scores_full[0]):
            if idx in combined_scores:
                combined_scores[idx] += self.weight_full * score
            else:
                combined_scores[idx] = self.weight_full * score

        # Sort and return top_k
        sorted_indices = sorted(combined_scores.items(),
                               key=lambda x: x[1],
                               reverse=True)[:top_k]

        return [self.items[idx] for idx, score in sorted_indices]
```

**データベース**:
- **USDA Unified Database**: 5,772件のUSDA FNDDS食品
- **インデックス構築**:
  - `main_index.faiss`: main_nameのみでベクトル化
  - `full_index.faiss`: main_name + descriptorsでベクトル化

**今回の設定** (Full-only):
- `weight_main = 0.0`
- `weight_full = 1.0`
- `stage1_top_k = 40` (上位40候補を取得)

**Prosciuttoケースでの動作**:
```
Query: "prosciutto" | "sliced"

Main-only search: "prosciutto"
  → Ham, prosciutto: 100位圏外 ❌

Full search: "prosciutto sliced"
  → Ham, prosciutto: 1位 (score: 0.8768) ✅

Combined score (Full-only):
  = 0.0 * 0.0 + 1.0 * 0.8768
  = 0.8768 ✅

→ Stage 1で40候補中1位として取得成功
```

#### 3-2. Stage 2: BGE Reranker (DeepInfra API)

**役割**: Stage 1の候補を精密にrerank

**実装** (`src/models/reranker.py`):
```python
class DeepInfraReranker:
    def __init__(self, model_id="Qwen/Qwen3-Reranker-8B"):
        self.api_url = "https://api.deepinfra.com/v1/inference/{model_id}"

    def rerank(self, query, candidates, return_scores=True):
        # Build field-labeled texts
        query_text = build_rerank_text(query_main, query_desc, is_query=True)
        # "[MAIN]prosciutto[/MAIN][DESC]sliced[/DESC]"

        candidate_texts = [
            build_rerank_text(cand_main, cand_desc, is_query=False)
            # "[MAIN]Ham, prosciutto[/MAIN][DESC][/DESC]"
            for cand_main, cand_desc in candidates
        ]

        # Call DeepInfra API with retry logic
        response = self._call_api_with_retry(query_text, candidate_texts)

        # Extract scores and return best match
        scores = response['scores']
        best_idx = np.argmax(scores)

        return best_idx, scores
```

**Field-labeled Template**:
```
Query: [MAIN]prosciutto[/MAIN][DESC]sliced[/DESC]
Candidate: [MAIN]Ham, prosciutto[/MAIN][DESC][/DESC]
```

**APIコスト**:
- Embedding: Qwen3-Embedding-8B ($0.025/1M tokens)
- Reranker: Qwen3-Reranker-8B ($0.050/1M tokens)
- 300クエリ平均: $0.000752/query

**リトライロジック**:
```python
def _call_api_with_retry(self, query, candidates, max_retries=10):
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                time.sleep(delay)
            else:
                self.failed_requests += 1
                raise
```

---

### 4. 結果評価 (`analyze_nutrition_accuracy.py`)

**役割**: マッチング結果の栄養学的正確性を評価

**評価カテゴリ**:

| カテゴリ | 説明 | 栄養影響 | 例 |
|---------|------|---------|-----|
| **PERFECT** | 単数形/複数形、形状の違いのみ | なし | tomato → Tomatoes |
| **ACCEPTABLE** | 同じ食品、同じ調理法 | 最小限 | red bell pepper → Peppers, bell, red |
| **MINOR_DIFFERENCE** | 調理法の詳細が違うが栄養素は近い | 最小限 | roasted → cooked, NS as to method |
| **MAJOR_DIFFERENCE** | 調理法が違い栄養素が変わる | 中程度 | raw → cooked (水分量変化) |
| **WRONG_FOOD** | 完全に違う食品 | 大きい | dinner roll → bread |

**今回の結果** (Full-only search):
- ✅ PERFECT: 37件 (12.3%)
- ✅ ACCEPTABLE: 142件 (47.3%)
- ⚠️ MINOR_DIFFERENCE: 121件 (40.3%)
- ⚠️ MAJOR_DIFFERENCE: 0件 (0.0%)
- ❌ WRONG_FOOD: 0件 (0.0%)

**栄養学的許容率: 100%** (300/300)

---

## 実行フロー例

### 完全なエンドツーエンド実行

```bash
# 1. VLM処理 (画像 → JSON)
cd /Users/odasoya/meal_analysis_api_2
python test_scripts/test_vlm_all_images.py \
  --freeform-usda \
  --model Qwen/Qwen3-VL-235B-A22B-Thinking \
  --limit 50 \
  --parallel \
  --batch-size 5

# Output: test_scripts/output/vlm_test_results_*.json

# 2. クエリ抽出 (JSON → クエリリスト)
cd test_scripts/query_system
python scripts/extract_vlm_queries.py \
  /path/to/vlm_test_results_*.json

# Output: tests/data/test_queries.json

# 3. USDA DB検索評価 (クエリ → マッチング結果)
python tests/evaluate_300_full_only.py

# Output: output/evaluation_results_300_full_only.json

# 4. 栄養学的正確性分析
python tests/analyze_nutrition_accuracy.py \
  evaluation_results_300_full_only.json \
  nutrition_analysis_300_full_only.json

# Output: output/nutrition_analysis_300_full_only.json
```

---

## データファイル構造

```
/Users/odasoya/meal_analysis_api_2/
├── test_images/                          # 入力画像
│   ├── test_food1.jpg
│   ├── test_food2.jpg
│   └── ...
├── test_scripts/
│   ├── test_vlm_all_images.py           # STEP 1: VLM処理
│   ├── prompt_base/
│   │   └── freeform_prompt_usda_format_ver.txt  # VLMプロンプト
│   ├── output/
│   │   └── vlm_test_results_*.json       # VLM結果
│   └── query_system/
│       ├── scripts/
│       │   └── extract_vlm_queries.py    # STEP 2: クエリ抽出
│       ├── tests/
│       │   ├── data/
│       │   │   └── test_queries.json     # 抽出されたクエリ
│       │   ├── evaluate_300_full_only.py # STEP 3: DB検索
│       │   └── analyze_nutrition_accuracy.py  # STEP 4: 評価
│       ├── src/
│       │   ├── pipeline.py               # FoodSearchPipeline
│       │   ├── index/
│       │   │   └── searcher.py          # Stage 1: Embedding検索
│       │   └── models/
│       │       └── reranker.py          # Stage 2: Reranker
│       ├── data/
│       │   ├── main_index.faiss         # FAISSインデックス (main)
│       │   ├── full_index.faiss         # FAISSインデックス (full)
│       │   └── metadata.json            # USDA DB metadata (5,772件)
│       └── output/
│           ├── evaluation_results_300_full_only.json
│           ├── nutrition_analysis_300_full_only.json
│           └── query_match_list_300.md
```

---

## パフォーマンス

### 300クエリ評価 (Full-only search)

| 指標 | 値 |
|-----|-----|
| 総クエリ数 | 300 |
| 並列ワーカー数 | 50 |
| 実行時間 | 134.0秒 |
| スループット | 2.24 queries/sec |
| 平均時間/クエリ | 0.45秒 |
| 総APIコスト | $0.2255 |
| 平均コスト/クエリ | $0.000752 |
| Exact Match率 | 79.0% (237/300) |
| **栄養学的許容率** | **100.0% (300/300)** ✅ |

### API使用統計

| API | トークン数 | コスト |
|-----|-----------|--------|
| Embedding (Qwen3-Embedding-8B) | 2,604 | $0.000065 |
| Reranker (Qwen3-Reranker-8B) | 4,508,530 | $0.2254 |
| **合計** | **4,511,134** | **$0.2255** |

---

## 主要な発見

### Prosciutto問題の解決

**問題** (Original: weight_main=0.6, weight_full=0.4):
```
Query: "prosciutto" | "sliced"
Main-only: 100位圏外
Full: 1位 (0.8768)
Combined: 0.6 * 0 + 0.4 * 0.8768 = 0.351
→ 40位圏外で除外 ❌
→ "Ham luncheon meat, loaf type" に誤マッチ
```

**解決** (Full-only: weight_main=0.0, weight_full=1.0):
```
Query: "prosciutto" | "sliced"
Full: 1位 (0.8768)
Combined: 0.0 * 0 + 1.0 * 0.8768 = 0.8768
→ 1位で取得 ✅
→ "Ham, prosciutto" に正しくマッチ (rerank: 0.9806)
```

### 栄養学的評価の改善

| 指標 | Original | Full-only | 変化 |
|------|----------|-----------|------|
| Exact Match | 240 (80%) | 237 (79%) | -3件 |
| **栄養学的許容率** | **98.3%** | **100.0%** | **+1.7% ✅** |
| **WRONG_FOOD** | **5件** | **0件** | **-5件 完全解決！** |

**結論**: Full-only search (weight_full=1.0) を推奨
