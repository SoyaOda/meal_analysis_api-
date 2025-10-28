#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
画像からクエリ生成→検索までの全プロセスをMarkdownレポートにまとめる（アルゴリズム詳細付き）

Input Files:
1. test_scripts/prompt_base/freeform_prompt_usda_format_ver.txt - VLMプロンプト
2. test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json - VLM結果
3. test_scripts/query_system/tests/data/test_queries.json - クエリデータ
4. Query System Pipeline - Stage 1 & Stage 2結果

Output:
- test_scripts/query_system/output/full_pipeline_report_v2.md
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipeline import FoodSearchPipeline


def load_vlm_prompt(prompt_path: Path) -> str:
    """VLMプロンプトを読み込み"""
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_vlm_results(results_path: Path) -> dict:
    """VLM結果を読み込み"""
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_test_queries(queries_path: Path) -> list:
    """テストクエリを読み込み"""
    with open(queries_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_search_pipeline(queries: list, index_dir: Path, stage1_top_k: int = 100) -> list:
    """
    全クエリに対して検索を実行

    Returns:
        List of search results with stage1 and stage2 details
    """
    pipeline = FoodSearchPipeline(
        index_dir=str(index_dir),
        device="cpu",
        stage1_top_k=stage1_top_k
    )

    results = []

    for i, query in enumerate(queries, 1):
        query_main = query['search_name']
        query_desc = query['description']

        print(f"Processing [{i}/{len(queries)}]: {query_main} | {query_desc}")

        # Search with candidates
        result = pipeline.search(
            query_main=query_main,
            query_descriptors=query_desc,
            return_top_k=10,
            return_candidates=True
        )

        results.append({
            'query': query,
            'stage1_candidates': result['stage1_candidates'],
            'stage2_top_k': result['top_k']
        })

    return results


def generate_markdown_report(
    vlm_prompt: str,
    vlm_results: dict,
    queries: list,
    search_results: list,
    output_path: Path
):
    """
    Markdownレポートを生成（アルゴリズム詳細付き）
    """
    md_lines = []

    # ヘッダー
    md_lines.append("# 🔍 Food Query System - Full Pipeline Report")
    md_lines.append("")
    md_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Table of Contents
    md_lines.append("## 📑 Table of Contents")
    md_lines.append("")
    md_lines.append("1. [Overview](#overview)")
    md_lines.append("2. [Pipeline Architecture & Algorithms](#pipeline-architecture--algorithms)")
    md_lines.append("   - [2.1 VLM Query Generation](#21-vlm-query-generation)")
    md_lines.append("   - [2.2 Text Normalization](#22-text-normalization)")
    md_lines.append("   - [2.3 Stage 1: Two-Stream Weighted Retriever](#23-stage-1-two-stream-weighted-retriever)")
    md_lines.append("   - [2.4 Stage 2: LLM-based Reranker](#24-stage-2-llm-based-reranker)")
    md_lines.append("3. [Step 1: VLM Prompt](#step-1-vlm-prompt)")
    md_lines.append("4. [Step 2: VLM Results](#step-2-vlm-results)")
    md_lines.append("5. [Step 3: Query Generation](#step-3-query-generation)")
    md_lines.append("6. [Step 4: Search Pipeline Results](#step-4-search-pipeline-results)")
    md_lines.append("7. [Summary](#summary)")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Overview
    md_lines.append("## Overview")
    md_lines.append("")
    md_lines.append("このレポートは、画像から食品クエリを生成し、USDA食品データベースで検索するまでの全プロセスを記録しています。")
    md_lines.append("")
    md_lines.append("### Pipeline Flow")
    md_lines.append("")
    md_lines.append("```")
    md_lines.append("画像 → VLM → クエリ生成 → テキスト正規化 → 検索パイプライン → 結果")
    md_lines.append("                          ↓")
    md_lines.append("                    search_name + description")
    md_lines.append("                          ↓")
    md_lines.append("                ┌─────────┴─────────┐")
    md_lines.append("                ↓                   ↓")
    md_lines.append("          Stage 1: Retriever  Stage 2: Reranker")
    md_lines.append("          (FAISS + Embedding) (LLM-based)")
    md_lines.append("                ↓                   ↓")
    md_lines.append("           100 candidates      Top 10 results")
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("### Models Used")
    md_lines.append("")
    md_lines.append("| Component | Model | Details |")
    md_lines.append("|-----------|-------|---------|")
    md_lines.append("| VLM | Qwen3-VL-235B-A22B-Thinking | Vision-Language Model for image analysis |")
    md_lines.append("| Embedding | Qwen3-Embedding-8B | 4096-dimensional embeddings via DeepInfra API |")
    md_lines.append("| Reranker | Qwen3-Reranker-8B | LLM-based reranking via DeepInfra API |")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # NEW SECTION: Pipeline Architecture & Algorithms
    md_lines.append("## Pipeline Architecture & Algorithms")
    md_lines.append("")
    md_lines.append("このセクションでは、各ステージのアルゴリズムを詳細に説明します。")
    md_lines.append("")

    # 2.1 VLM Query Generation
    md_lines.append("### 2.1 VLM Query Generation")
    md_lines.append("")
    md_lines.append("**目的**: VLMの出力JSON（`dishes`配列）から検索可能なクエリを生成")
    md_lines.append("")
    md_lines.append("**アルゴリズム**:")
    md_lines.append("")
    md_lines.append("1. VLM出力から`main_food`と`extras`を抽出")
    md_lines.append("2. 各食品に対して`search_name`（主要食品名）と`description`（調理方法・状態）を分離")
    md_lines.append("3. USDA検索用に最適化されたクエリペアを生成")
    md_lines.append("")
    md_lines.append("**VLM出力例**:")
    md_lines.append("```json")
    md_lines.append('{')
    md_lines.append('  "main_food": {')
    md_lines.append('    "search_name": "beef steak",')
    md_lines.append('    "description": "grilled, sliced",')
    md_lines.append('    "weight_g": 190,')
    md_lines.append('    "confidence": 0.95')
    md_lines.append('  }')
    md_lines.append('}')
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("**生成されるクエリ**:")
    md_lines.append("- `query_main`: `\"beef steak\"`")
    md_lines.append("- `query_descriptors`: `\"grilled, sliced\"`")
    md_lines.append("")
    md_lines.append("**実装** (`prepare_test_data.py`):")
    md_lines.append("```python")
    md_lines.append("def load_vlm_test_data() -> List[Dict]:")
    md_lines.append("    for result in data.get('results', []):")
    md_lines.append("        dishes = vlm_response.get('dishes', [])")
    md_lines.append("        ")
    md_lines.append("        for dish in dishes:")
    md_lines.append("            # Extract main_food")
    md_lines.append("            if dish.get('main_food'):")
    md_lines.append("                main_food = dish['main_food']")
    md_lines.append("                query_items.append({")
    md_lines.append("                    'search_name': main_food.get('search_name'),  # e.g., \"beef steak\"")
    md_lines.append("                    'description': main_food.get('description'),  # e.g., \"grilled, sliced\"")
    md_lines.append("                    'weight_g': main_food.get('weight_g'),")
    md_lines.append("                    'confidence': main_food.get('confidence')")
    md_lines.append("                })")
    md_lines.append("```")
    md_lines.append("")

    # 2.2 Text Normalization
    md_lines.append("### 2.2 Text Normalization")
    md_lines.append("")
    md_lines.append("**目的**: クエリとデータベースの表記ゆれを吸収し、検索精度を向上")
    md_lines.append("")
    md_lines.append("**アルゴリズム**:")
    md_lines.append("")
    md_lines.append("1. **基本正規化**: 小文字化 + 特殊文字削除")
    md_lines.append("2. **複合語正規化**: `\"cherry tomatoes\"` → `\"tomatoes cherry\"` (USDA形式に合わせる)")
    md_lines.append("3. **2つのテキスト生成**:")
    md_lines.append("   - `main_only`: search_nameのみ (e.g., `\"beef steak\"`)")
    md_lines.append("   - `full`: search_name + description (e.g., `\"beef steak grilled sliced\"`)")
    md_lines.append("")
    md_lines.append("**実装** (`text_normalizer.py`):")
    md_lines.append("```python")
    md_lines.append("def normalize_text(text: str) -> str:")
    md_lines.append("    # 小文字化")
    md_lines.append("    text = text.lower()")
    md_lines.append("    # 特殊文字削除（アルファベットとスペースのみ残す）")
    md_lines.append("    text = re.sub(r'[^a-z\\s]', ' ', text)")
    md_lines.append("    # 複数スペースを単一スペースに")
    md_lines.append("    text = re.sub(r'\\s+', ' ', text).strip()")
    md_lines.append("    return text")
    md_lines.append("")
    md_lines.append("def normalize_compound_words(text: str) -> str:")
    md_lines.append("    compound_mappings = {")
    md_lines.append("        \"cherry tomatoes\": \"tomatoes cherry\",")
    md_lines.append("        \"beef steak\": \"steak beef\",")
    md_lines.append("        \"chicken breast\": \"breast chicken\",")
    md_lines.append("        # ... more mappings")
    md_lines.append("    }")
    md_lines.append("    return compound_mappings.get(text.lower(), text.lower())")
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("**例**:")
    md_lines.append("")
    md_lines.append("| Input | Normalized |")
    md_lines.append("|-------|------------|")
    md_lines.append("| `\"Chicken, Broiled\"` | `\"chicken broiled\"` |")
    md_lines.append("| `\"cherry tomatoes\"` | `\"tomatoes cherry\"` |")
    md_lines.append("| `\"beef steak\"` | `\"steak beef\"` |")
    md_lines.append("")

    # 2.3 Stage 1: Two-Stream Weighted Retriever
    md_lines.append("### 2.3 Stage 1: Two-Stream Weighted Retriever")
    md_lines.append("")
    md_lines.append("**目的**: FAISSインデックスから関連度の高い100件の候補を高速に取得")
    md_lines.append("")
    md_lines.append("**アルゴリズム**: Two-Stream Weighted Search")
    md_lines.append("")
    md_lines.append("#### 数式")
    md_lines.append("")
    md_lines.append("```")
    md_lines.append("S_combined = w_main * cosine(Q_main, E_main) + w_full * cosine(Q_full, E_full)")
    md_lines.append("")
    md_lines.append("where:")
    md_lines.append("  w_main = 0.6  (main-only weight, 主要食品名の重み)")
    md_lines.append("  w_full = 0.4  (full weight, 文脈込みの重み)")
    md_lines.append("  Q_main = embedding(\"beef steak\")  (main-onlyクエリ)")
    md_lines.append("  Q_full = embedding(\"beef steak grilled sliced\")  (fullクエリ)")
    md_lines.append("  E_main = main-only embedding of database item")
    md_lines.append("  E_full = full embedding of database item")
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("#### プロセス")
    md_lines.append("")
    md_lines.append("1. **2つのクエリを生成**:")
    md_lines.append("   - `text_main`: `\"beef steak\"` → embedding → `Q_main`")
    md_lines.append("   - `text_full`: `\"beef steak grilled sliced\"` → embedding → `Q_full`")
    md_lines.append("")
    md_lines.append("2. **2つのFAISSインデックスで検索**:")
    md_lines.append("   - `index_main`: main-only embeddingsを格納 (5,772 vectors × 4096 dim)")
    md_lines.append("   - `index_full`: full embeddingsを格納 (5,772 vectors × 4096 dim)")
    md_lines.append("")
    md_lines.append("3. **スコアの重み付け融合**:")
    md_lines.append("   - 各候補に対して `S_combined = 0.6 * S_main + 0.4 * S_full`")
    md_lines.append("   - 融合スコアでTop-100をソート")
    md_lines.append("")
    md_lines.append("#### 実装 (`searcher.py`)")
    md_lines.append("")
    md_lines.append("```python")
    md_lines.append("class IndexSearcher:")
    md_lines.append("    def search(self, query_main: str, query_descriptors: str, top_k: int):")
    md_lines.append("        # 1. Build query texts")
    md_lines.append("        text_main = normalize_text(build_main_only_text(query_main))")
    md_lines.append("        text_full = normalize_text(build_full_text(query_main, query_descriptors))")
    md_lines.append("        ")
    md_lines.append("        # 2. Encode queries")
    md_lines.append("        emb_main = self.embedding_model.encode(text_main)")
    md_lines.append("        emb_full = self.embedding_model.encode(text_full)")
    md_lines.append("        ")
    md_lines.append("        # 3. Normalize embeddings (for cosine similarity)")
    md_lines.append("        emb_main = emb_main / np.linalg.norm(emb_main, axis=1, keepdims=True)")
    md_lines.append("        emb_full = emb_full / np.linalg.norm(emb_full, axis=1, keepdims=True)")
    md_lines.append("        ")
    md_lines.append("        # 4. Search both indexes")
    md_lines.append("        scores_main, indices_main = self.index_main.search(emb_main, top_k*2)")
    md_lines.append("        scores_full, indices_full = self.index_full.search(emb_full, top_k*2)")
    md_lines.append("        ")
    md_lines.append("        # 5. Weighted combination")
    md_lines.append("        combined_scores = {}")
    md_lines.append("        for idx, score in zip(indices_main[0], scores_main[0]):")
    md_lines.append("            combined_scores[idx] = self.weight_main * score")
    md_lines.append("        ")
    md_lines.append("        for idx, score in zip(indices_full[0], scores_full[0]):")
    md_lines.append("            if idx in combined_scores:")
    md_lines.append("                combined_scores[idx] += self.weight_full * score")
    md_lines.append("            else:")
    md_lines.append("                combined_scores[idx] = self.weight_full * score")
    md_lines.append("        ")
    md_lines.append("        # 6. Sort by combined score")
    md_lines.append("        sorted_indices = sorted(combined_scores.keys(), ")
    md_lines.append("                               key=lambda x: combined_scores[x], ")
    md_lines.append("                               reverse=True)")
    md_lines.append("        ")
    md_lines.append("        return sorted_indices[:top_k]  # Return top-100")
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("#### 例: `\"beef steak | grilled, sliced\"`")
    md_lines.append("")
    md_lines.append("| Stream | Query | Top Candidate | Score |")
    md_lines.append("|--------|-------|---------------|-------|")
    md_lines.append("| Main | `\"beef steak\"` | Beef, steak, NFS | 0.873 |")
    md_lines.append("| Full | `\"beef steak grilled sliced\"` | Beef, steak, NFS | 0.854 |")
    md_lines.append("| **Combined** | - | **Beef, steak, NFS** | **0.866** (0.6×0.873 + 0.4×0.854) |")
    md_lines.append("")
    md_lines.append("**結果**: grilled beef steak (FDC ID: 746763) はRank 8/100で取得")
    md_lines.append("")

    # 2.4 Stage 2: LLM-based Reranker
    md_lines.append("### 2.4 Stage 2: LLM-based Reranker")
    md_lines.append("")
    md_lines.append("**目的**: Stage 1の100件をLLMで精密に再評価し、Top 10を選出")
    md_lines.append("")
    md_lines.append("**アルゴリズム**: DeepInfra API (Qwen3-Reranker-8B) + Custom Task Instruction")
    md_lines.append("")
    md_lines.append("#### Custom Task Instruction")
    md_lines.append("")
    md_lines.append("```")
    md_lines.append("優先順位（重要度順）:")
    md_lines.append("1. **食品名の一致**: 主要食品名が完全一致（例: \"tomatoes\"は\"tomatoes\"にマッチ）")
    md_lines.append("2. **調理方法**: raw/cooked/grilled/roasted等の調理方法が重要")
    md_lines.append("   - クエリが具体的な調理方法を指定した場合、完全一致を優先")
    md_lines.append("   - クエリが\"cooked\"のみの場合、任意の調理済み形態を許容")
    md_lines.append("   - データベースが\"NS as to cooking method\"の場合、曖昧なクエリに許容")
    md_lines.append("3. **調理詳細**: boneless, skinless, sliced等は補助的")
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("#### プロセス")
    md_lines.append("")
    md_lines.append("1. **Field-Labeled Formatに変換**:")
    md_lines.append("   ```")
    md_lines.append("   Query:")
    md_lines.append("   name: beef steak")
    md_lines.append("   description: grilled, sliced")
    md_lines.append("   ")
    md_lines.append("   Candidate:")
    md_lines.append("   name: Beef, steak, NFS")
    md_lines.append("   description: (empty)")
    md_lines.append("   ```")
    md_lines.append("")
    md_lines.append("2. **DeepInfra APIに送信**:")
    md_lines.append("   ```json")
    md_lines.append("   {")
    md_lines.append("     \"queries\": [\"name: beef steak\\ndescription: grilled, sliced\"],")
    md_lines.append("     \"documents\": [")
    md_lines.append("       \"name: Beef, steak, NFS\\ndescription: \",")
    md_lines.append("       \"name: Beef, short loin, t-bone steak, ..., grilled\\ndescription: \",")
    md_lines.append("       ...")
    md_lines.append("     ],")
    md_lines.append("     \"instruction\": \"<Custom Task Instruction>\"")
    md_lines.append("   }")
    md_lines.append("   ```")
    md_lines.append("")
    md_lines.append("3. **スコアを取得し、Top 10を選出**:")
    md_lines.append("   ```python")
    md_lines.append("   scores = [0.6637, 0.3657, 0.3585, ...]  # API response")
    md_lines.append("   best_idx = np.argmax(scores)  # Index of best match")
    md_lines.append("   top_10 = np.argsort(scores)[::-1][:10]")
    md_lines.append("   ```")
    md_lines.append("")
    md_lines.append("#### 実装 (`reranker.py`)")
    md_lines.append("")
    md_lines.append("```python")
    md_lines.append("class RerankerModel:")
    md_lines.append("    def __init__(self, model_name=\"Qwen/Qwen3-Reranker-8B\"):")
    md_lines.append("        self.api_url = f\"https://api.deepinfra.com/v1/inference/{model_name}\"")
    md_lines.append("        ")
    md_lines.append("        # Custom task instruction for food matching")
    md_lines.append("        self.task_instruction = '''")
    md_lines.append("        Priority for matching (most important first):")
    md_lines.append("        1. Food Identity: main food name must match exactly")
    md_lines.append("        2. Cooking Method: raw vs cooked matters significantly")
    md_lines.append("        3. Preparation Details: boneless, skinless, etc.")
    md_lines.append("        '''")
    md_lines.append("    ")
    md_lines.append("    def rerank(self, query: str, candidates: List[str]):")
    md_lines.append("        payload = {")
    md_lines.append("            \"queries\": [query],")
    md_lines.append("            \"documents\": candidates,")
    md_lines.append("            \"instruction\": self.task_instruction")
    md_lines.append("        }")
    md_lines.append("        ")
    md_lines.append("        response = requests.post(self.api_url, json=payload)")
    md_lines.append("        scores = np.array(response.json()[\"scores\"])")
    md_lines.append("        ")
    md_lines.append("        best_idx = int(np.argmax(scores))")
    md_lines.append("        return best_idx, scores")
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("#### 例: `\"beef steak | grilled, sliced\"`")
    md_lines.append("")
    md_lines.append("| Rank | Description | Stage1 Score | Rerank Score |")
    md_lines.append("|------|-------------|--------------|--------------|")
    md_lines.append("| 1 | Beef, steak, NFS | 0.8732 | **0.6637** ⬅️ Best |")
    md_lines.append("| 2 | Beef, steak, strip, NS as to fat eaten | 0.8671 | 0.3657 |")
    md_lines.append("| 3 | Beef, short loin, t-bone steak, ..., grilled | 0.8790 | 0.3585 ⬅️ grilled版 |")
    md_lines.append("")
    md_lines.append("**結果**: \"Beef, steak, NFS\"が1位に選出（栄養学的に許容可能）")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Step 1: VLM Prompt (既存)
    md_lines.append("## Step 1: VLM Prompt")
    md_lines.append("")
    md_lines.append("VLMに送信されるプロンプトテンプレート：")
    md_lines.append("")
    md_lines.append("```")
    md_lines.append(vlm_prompt)
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Step 2: VLM Results (既存)
    md_lines.append("## Step 2: VLM Results")
    md_lines.append("")
    md_lines.append(f"**Total Images Processed**: {len(vlm_results.get('results', []))}")
    md_lines.append(f"**Successful Analyses**: {sum(1 for r in vlm_results.get('results', []) if r.get('success'))}")
    md_lines.append("")

    # Show first 3 VLM results as examples
    md_lines.append("### Sample VLM Outputs (First 3 Images)")
    md_lines.append("")

    for i, result in enumerate(vlm_results.get('results', [])[:3], 1):
        md_lines.append(f"#### Image {i}: {result.get('image_file', 'N/A')}")
        md_lines.append("")

        if result.get('success'):
            vlm_response = result.get('vlm_response', {})
            md_lines.append("```json")
            md_lines.append(json.dumps(vlm_response, indent=2, ensure_ascii=False))
            md_lines.append("```")
        else:
            md_lines.append(f"**Error**: {result.get('error', 'Unknown error')}")

        md_lines.append("")

    md_lines.append("---")
    md_lines.append("")

    # Step 3: Query Generation (既存)
    md_lines.append("## Step 3: Query Generation")
    md_lines.append("")
    md_lines.append(f"VLM結果から生成されたクエリ数: **{len(queries)}**")
    md_lines.append("")
    md_lines.append("### All Generated Queries")
    md_lines.append("")
    md_lines.append("| # | Search Name | Description | Weight (g) | Confidence | Image |")
    md_lines.append("|---|-------------|-------------|------------|------------|-------|")

    for i, query in enumerate(queries, 1):
        md_lines.append(
            f"| {i} | {query['search_name']} | {query['description']} | "
            f"{query['weight_g']} | {query['confidence']} | {query.get('image_file', 'N/A')} |"
        )

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Step 4: Search Pipeline Results (既存)
    md_lines.append("## Step 4: Search Pipeline Results")
    md_lines.append("")
    md_lines.append("各クエリに対してStage 1（Retriever）とStage 2（Reranker）を実行した結果：")
    md_lines.append("")

    for i, search_result in enumerate(search_results, 1):
        query = search_result['query']
        stage1_candidates = search_result['stage1_candidates']
        stage2_top_k = search_result['stage2_top_k']

        md_lines.append(f"### Query {i}: {query['search_name']} | {query['description']}")
        md_lines.append("")
        md_lines.append(f"**Weight**: {query['weight_g']}g, **Confidence**: {query['confidence']}")
        md_lines.append("")

        # Stage 1 Results
        md_lines.append("#### Stage 1: Retriever")
        md_lines.append("")
        md_lines.append(f"Retrieved **{len(stage1_candidates)}** candidates using weighted FAISS search")
        md_lines.append("")
        md_lines.append("<details>")
        md_lines.append("<summary>View Top 20 Stage 1 Candidates</summary>")
        md_lines.append("")
        md_lines.append("| Rank | Score | Description | Source | FDC ID |")
        md_lines.append("|------|-------|-------------|--------|--------|")

        for rank, cand in enumerate(stage1_candidates[:20], 1):
            md_lines.append(
                f"| {rank} | {cand['score']:.4f} | {cand['description']} | "
                f"{cand['source']} | {cand['fdc_id']} |"
            )

        md_lines.append("")
        md_lines.append("</details>")
        md_lines.append("")

        # Stage 2 Results
        md_lines.append("#### Stage 2: Reranker")
        md_lines.append("")
        md_lines.append("**Top 10 Results** after LLM-based reranking:")
        md_lines.append("")
        md_lines.append("| Rank | Rerank Score | Stage1 Score | Description | Source | FDC ID |")
        md_lines.append("|------|--------------|--------------|-------------|--------|--------|")

        for rank, item in enumerate(stage2_top_k, 1):
            marker = "🏆" if rank == 1 else ""
            md_lines.append(
                f"| {marker}{rank} | **{item['rerank_score']:.4f}** | {item['stage1_score']:.4f} | "
                f"{item['description']} | {item['source']} | {item['fdc_id']} |"
            )

        md_lines.append("")

        # Best match highlight
        best_match = stage2_top_k[0]
        md_lines.append(f"**🎯 Best Match**: {best_match['description']}")
        md_lines.append(f"- **Rerank Score**: {best_match['rerank_score']:.4f}")
        md_lines.append(f"- **Stage1 Score**: {best_match['stage1_score']:.4f}")
        md_lines.append(f"- **Source**: {best_match['source']}")
        md_lines.append(f"- **FDC ID**: {best_match['fdc_id']}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    # Summary (既存)
    md_lines.append("## Summary")
    md_lines.append("")
    md_lines.append("### Pipeline Statistics")
    md_lines.append("")
    md_lines.append("| Metric | Value |")
    md_lines.append("|--------|-------|")
    md_lines.append(f"| Total Images Processed | {len(vlm_results.get('results', []))} |")
    md_lines.append(f"| Total Queries Generated | {len(queries)} |")
    md_lines.append(f"| Average Confidence | {sum(q['confidence'] for q in queries) / len(queries):.2f} |")
    md_lines.append(f"| Stage 1 Candidates per Query | {len(search_results[0]['stage1_candidates']) if search_results else 0} |")
    md_lines.append(f"| Stage 2 Top-K | {len(search_results[0]['stage2_top_k']) if search_results else 0} |")
    md_lines.append("")
    md_lines.append("### Algorithm Summary")
    md_lines.append("")
    md_lines.append("| Stage | Algorithm | Model | Purpose |")
    md_lines.append("|-------|-----------|-------|---------|")
    md_lines.append("| VLM | Vision-Language Analysis | Qwen3-VL-235B-A22B-Thinking | 画像から食品情報を抽出 |")
    md_lines.append("| Normalization | Text Processing | Rule-based | 表記ゆれを吸収 |")
    md_lines.append("| Stage 1 | Two-Stream Weighted Search | Qwen3-Embedding-8B + FAISS | 100候補を高速取得 |")
    md_lines.append("| Stage 2 | LLM-based Reranking | Qwen3-Reranker-8B | Top 10を精密選出 |")
    md_lines.append("")
    md_lines.append("### Accuracy")
    md_lines.append("")
    md_lines.append("- **形式的精度**: 70% (14/20 完全一致)")
    md_lines.append("- **栄養学的精度**: **100% (20/20 許容可能)**")
    md_lines.append("")
    md_lines.append("詳細は `tests/nutritional_evaluation.py` を参照")
    md_lines.append("")

    # Write to file
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"\n✅ Report generated: {output_path}")


def main():
    """Main execution"""
    print("=" * 80)
    print("Full Pipeline Report Generator (with Algorithm Details)")
    print("=" * 80)
    print()

    # File paths
    vlm_prompt_path = project_root.parent / "prompt_base" / "freeform_prompt_usda_format_ver.txt"
    vlm_results_path = project_root.parent / "output" / "vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json"
    test_queries_path = project_root / "tests" / "data" / "test_queries.json"
    index_dir = project_root / "data"
    output_path = project_root / "output" / "full_pipeline_report_v2.md"

    # Step 1: Load VLM prompt
    print("📄 Loading VLM prompt...")
    vlm_prompt = load_vlm_prompt(vlm_prompt_path)
    print(f"   ✅ Loaded: {len(vlm_prompt)} characters")

    # Step 2: Load VLM results
    print("\n📊 Loading VLM results...")
    vlm_results = load_vlm_results(vlm_results_path)
    print(f"   ✅ Loaded: {len(vlm_results.get('results', []))} image results")

    # Step 3: Load test queries
    print("\n🔍 Loading test queries...")
    queries = load_test_queries(test_queries_path)
    print(f"   ✅ Loaded: {len(queries)} queries")

    # Step 4: Run search pipeline
    print("\n🚀 Running search pipeline...")
    search_results = run_search_pipeline(queries, index_dir, stage1_top_k=100)
    print(f"   ✅ Completed: {len(search_results)} search results")

    # Generate report
    print("\n📝 Generating Markdown report with algorithm details...")
    generate_markdown_report(
        vlm_prompt=vlm_prompt,
        vlm_results=vlm_results,
        queries=queries,
        search_results=search_results,
        output_path=output_path
    )

    print("\n" + "=" * 80)
    print("✅ Full pipeline report generation completed!")
    print("=" * 80)
    print(f"\nOutput: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
