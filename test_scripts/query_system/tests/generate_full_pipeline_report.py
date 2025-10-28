#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
画像からクエリ生成→検索までの全プロセスをMarkdownレポートにまとめる

Input Files:
1. test_scripts/prompt_base/freeform_prompt_usda_format_ver.txt - VLMプロンプト
2. test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json - VLM結果
3. test_scripts/query_system/tests/data/test_queries.json - クエリデータ
4. Query System Pipeline - Stage 1 & Stage 2結果

Output:
- test_scripts/query_system/output/full_pipeline_report.md
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
    Markdownレポートを生成
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
    md_lines.append("2. [Step 1: VLM Prompt](#step-1-vlm-prompt)")
    md_lines.append("3. [Step 2: VLM Results](#step-2-vlm-results)")
    md_lines.append("4. [Step 3: Query Generation](#step-3-query-generation)")
    md_lines.append("5. [Step 4: Search Pipeline Results](#step-4-search-pipeline-results)")
    md_lines.append("   - [Stage 1: Retriever](#stage-1-retriever)")
    md_lines.append("   - [Stage 2: Reranker](#stage-2-reranker)")
    md_lines.append("6. [Summary](#summary)")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Overview
    md_lines.append("## Overview")
    md_lines.append("")
    md_lines.append("このレポートは、画像から食品クエリを生成し、USDA食品データベースで検索するまでの全プロセスを記録しています。")
    md_lines.append("")
    md_lines.append("### Pipeline Architecture")
    md_lines.append("")
    md_lines.append("```")
    md_lines.append("画像 → VLM (Vision Language Model) → クエリ生成 → 検索パイプライン → 結果")
    md_lines.append("                                                  ├─ Stage 1: Retriever (FAISS + Embedding)")
    md_lines.append("                                                  └─ Stage 2: Reranker (LLM-based)")
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

    # Step 1: VLM Prompt
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

    # Step 2: VLM Results
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

    # Step 3: Query Generation
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

    # Step 4: Search Pipeline Results
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

    # Summary
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

    # Write to file
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"\n✅ Report generated: {output_path}")


def main():
    """Main execution"""
    print("=" * 80)
    print("Full Pipeline Report Generator")
    print("=" * 80)
    print()

    # File paths
    vlm_prompt_path = project_root.parent / "prompt_base" / "freeform_prompt_usda_format_ver.txt"
    vlm_results_path = project_root.parent / "output" / "vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json"
    test_queries_path = project_root / "tests" / "data" / "test_queries.json"
    index_dir = project_root / "data"
    output_path = project_root / "output" / "full_pipeline_report.md"

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
    print("\n📝 Generating Markdown report...")
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
