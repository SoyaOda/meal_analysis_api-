#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepInfra API トークン計算方法の検証

Reranker APIのトークン数が候補数にどう依存するかを検証します。
"""

import sys
import json
from pathlib import Path
import requests
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_reranker_with_different_candidate_counts():
    """
    候補数を変えてReranker APIのトークン使用量を測定
    """
    api_url = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-8B"
    api_token = os.getenv("DEEPINFRA_TOKEN") or os.getenv("DEEPINFRA_API_KEY")

    if not api_token:
        raise ValueError("DEEPINFRA_TOKEN or DEEPINFRA_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # 固定のクエリ
    query = "query\nname: chicken breast\ndescription: cooked, boneless, skinless"

    # 固定の候補テンプレート（実際のUSDAデータに近い長さ）
    candidate_template = "candidate\nname: Chicken, breast, {}\ndescription: cooked, roasted"

    print("=" * 80)
    print("DeepInfra Reranker API Token Calculation Verification")
    print("=" * 80)
    print(f"\nQuery: {query}")
    print(f"Query character count: {len(query)}")
    print(f"Candidate template: {candidate_template.format('SAMPLE')}")
    print(f"Candidate template character count: {len(candidate_template.format('SAMPLE'))}")
    print()

    results = []

    # 異なる候補数でテスト
    candidate_counts = [1, 5, 10, 20, 40, 100]

    for count in candidate_counts:
        # 候補リスト生成
        candidates = [
            candidate_template.format(f"variant {i}")
            for i in range(count)
        ]

        payload = {
            "queries": [query],
            "documents": candidates
        }

        # API呼び出し
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()

        # トークン数取得
        input_tokens = result.get("input_tokens", 0)

        # 候補1つあたりの平均トークン数
        tokens_per_candidate = input_tokens / count if count > 0 else 0

        results.append({
            "candidate_count": count,
            "input_tokens": input_tokens,
            "tokens_per_candidate": tokens_per_candidate
        })

        print(f"Candidates: {count:3d} → Tokens: {input_tokens:6,d} → Tokens/Candidate: {tokens_per_candidate:.1f}")

    print("\n" + "=" * 80)
    print("Analysis")
    print("=" * 80)

    # トークン増加率を計算
    if len(results) >= 2:
        first = results[0]
        last = results[-1]

        token_growth_ratio = last["input_tokens"] / first["input_tokens"]
        candidate_growth_ratio = last["candidate_count"] / first["candidate_count"]

        print(f"\nToken growth: {first['input_tokens']:,} → {last['input_tokens']:,} ({token_growth_ratio:.1f}x)")
        print(f"Candidate growth: {first['candidate_count']} → {last['candidate_count']} ({candidate_growth_ratio:.1f}x)")

        if abs(token_growth_ratio - candidate_growth_ratio) < 0.1 * candidate_growth_ratio:
            print("\n✅ トークン数は候補数にほぼ線形に比例します")
            print("   → Reranker APIのトークン数 = Query tokens + (Candidate_1 tokens + ... + Candidate_N tokens)")
        else:
            print("\n⚠️ トークン数の増加率が候補数の増加率と一致しません")

    # 平均候補あたりトークン数の標準偏差
    avg_tokens_per_candidate = sum(r["tokens_per_candidate"] for r in results) / len(results)
    print(f"\n平均 Tokens/Candidate: {avg_tokens_per_candidate:.1f}")

    # コスト計算
    cost_per_1m = 0.050  # $0.050 / 1M tokens

    print("\n" + "=" * 80)
    print("Cost Estimates (at $0.050 / 1M tokens)")
    print("=" * 80)

    for r in results:
        cost = (r["input_tokens"] / 1_000_000) * cost_per_1m
        print(f"{r['candidate_count']:3d} candidates → ${cost:.6f} per query")

    print("\n💡 結論:")
    print("   - Stage2で100候補をリランクする場合、約100倍のトークン数になる")
    print("   - コスト削減には stage1_top_k を減らすことが最も効果的")

    # Save results
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "token_calculation_verification.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "query": query,
            "candidate_template": candidate_template.format("SAMPLE"),
            "results": results,
            "pricing": {
                "cost_per_1m_tokens": cost_per_1m
            }
        }, f, indent=2)

    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    try:
        test_reranker_with_different_candidate_counts()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
