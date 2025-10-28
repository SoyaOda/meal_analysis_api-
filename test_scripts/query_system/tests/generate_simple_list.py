#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
300例のクエリと結果のシンプルなリスト生成
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_simple_list():
    """300例のクエリと結果をシンプルに列挙"""

    # Load evaluation results
    results_file = project_root / "output" / "evaluation_results_300_full_only.json"

    with open(results_file, 'r', encoding='utf-8') as f:
        eval_data = json.load(f)

    results = eval_data['results']

    # Generate Markdown report
    output_file = project_root / "output" / "query_match_list_300.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 300例クエリとマッチング結果\n\n")
        f.write(f"総件数: {len(results)}\n\n")
        f.write("---\n\n")

        for result in results:
            query_id = result['query_id']
            query_name = result['query_name']
            query_desc = result['query_desc']
            matched_description = result['matched_description']
            matched_name = result['matched_name']
            matched_desc = result['matched_desc']
            fdc_id = result['fdc_id']
            rerank_score = result['rerank_score']

            f.write(f"## {query_id}. Query: {query_name} | {query_desc}\n\n")
            f.write(f"**Matched**: {matched_description}\n\n")
            f.write(f"- FDC ID: {fdc_id}\n")
            f.write(f"- Rerank Score: {rerank_score:.4f}\n")
            f.write(f"- Main Name: {matched_name}\n")
            f.write(f"- Descriptors: {matched_desc}\n")
            f.write("\n---\n\n")

    print(f"✅ Simple list generated: {output_file}")
    file_size_kb = output_file.stat().st_size / 1024
    print(f"   File size: {file_size_kb:.2f} KB")


if __name__ == "__main__":
    generate_simple_list()
