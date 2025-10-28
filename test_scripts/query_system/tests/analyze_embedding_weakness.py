#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Embedding検索の弱点分析

なぜ「prosciutto」クエリで「Ham, prosciutto」が40位圏外になったのか
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def analyze_embedding_weakness():
    """Embedding検索の弱点を分析"""

    print("=" * 80)
    print("Embedding検索の弱点分析: prosciuttoケース")
    print("=" * 80)

    # Stage 1で上位に来た項目
    top_10_items = [
        ("Mortadella", 0.8743),
        ("Italian sausage", 0.8376),
        ("Antipasto with ham, fish, cheese, vegetables", 0.8157),
        ("Pork sausage", 0.7998),
        ("Sausage, Italian, pork, mild, cooked, pan-fried", 0.7980),
        ("Bacon, for use on a sandwich", 0.7915),
        ("Pork jerky", 0.7914),
        ("Ham luncheon meat, loaf type", 0.7907),
        ("Pork bacon, smoked or cured, cooked", 0.7907),
        ("Pork, roll", 0.7905),
    ]

    # 正しい項目
    correct_item = "Ham, prosciutto"

    print("\n【Query】")
    print("  prosciutto")

    print("\n【正しい項目】")
    print(f"  {correct_item}")
    print(f"  Status: 40位圏外 ❌")

    print("\n【Stage 1 Top 10】")
    for i, (item, score) in enumerate(top_10_items, 1):
        print(f"  {i}. {item} (score: {score:.4f})")

    print("\n" + "=" * 80)
    print("根本原因の分析")
    print("=" * 80)

    print("\n1️⃣ Embedding検索の特性")
    print("-" * 80)
    print("Embeddingは「意味的な類似性」で検索します。")
    print("")
    print("【Embedding modelの評価基準】")
    print("  ✅ 意味的な近さ: 文脈・カテゴリーの類似性")
    print("  ✅ トピックの一致: 食品カテゴリー、調理法など")
    print("  ❌ 単語の完全一致: 重視しない")
    print("")
    print("【prosciuttoケースの問題】")
    print("  Query: 'prosciutto' (単一単語)")
    print("  正解: 'Ham, prosciutto' (2単語、Hamが前)")
    print("")
    print("  Embedding modelの視点:")
    print("    - 'prosciutto' vs 'Ham, prosciutto'")
    print("      → 'Ham'が前にあるため、ベクトルの重みが分散")
    print("      → 完全一致を保証しない")
    print("")
    print("    - 'prosciutto' vs 'Mortadella'")
    print("      → どちらもイタリアの加工肉")
    print("      → 食文化的コンテキストが類似")
    print("      → Embedding空間で近い位置にある可能性 ✅")

    print("\n2️⃣ なぜMortadellaが1位？")
    print("-" * 80)
    print("【意味的類似性の分析】")
    print("")
    print("  Prosciutto (プロシュート):")
    print("    - イタリアの生ハム")
    print("    - 豚肉の加工品")
    print("    - 塩漬け・乾燥熟成")
    print("    - イタリア料理の定番")
    print("")
    print("  Mortadella (モルタデッラ):")
    print("    - イタリアのソーセージ")
    print("    - 豚肉の加工品")
    print("    - スパイス・ピスタチオ入り")
    print("    - イタリア料理の定番")
    print("")
    print("  → Embedding modelの視点では非常に類似！")
    print("  → 単語の一致よりも、意味的コンテキストを重視")

    print("\n3️⃣ Exact Matchの欠如")
    print("-" * 80)
    print("【キーワード検索との比較】")
    print("")
    print("  伝統的なキーワード検索 (BM25など):")
    print("    Query: 'prosciutto'")
    print("    → 'prosciutto'を含む項目に高スコア")
    print("    → 'Ham, prosciutto' → 確実にヒット ✅")
    print("    → 'Mortadella' → スコア 0 ❌")
    print("")
    print("  Embedding検索:")
    print("    Query: 'prosciutto'のベクトル")
    print("    → 全項目のベクトルと比較（コサイン類似度）")
    print("    → 'prosciutto'を含むかどうかは直接評価しない")
    print("    → 'Ham, prosciutto' → 必ずしも上位にならない ❌")
    print("    → 'Mortadella' → 意味的に近ければ上位に ✅")

    print("\n4️⃣ データベース記述形式の影響")
    print("-" * 80)
    print("【USDA項目の形式】")
    print("")
    print("  形式: '主食品名, 詳細説明'")
    print("")
    print("  例:")
    print("    - 'Ham, prosciutto'")
    print("      → 主: Ham")
    print("      → 詳細: prosciutto")
    print("")
    print("    - 'Mortadella'")
    print("      → 主: Mortadella")
    print("")
    print("  Embedding modelの処理:")
    print("    'Ham, prosciutto'全体を1つのテキストとしてembedding")
    print("    → 'Ham'の重みが大きくなる可能性")
    print("    → 'prosciutto'単独との類似度が下がる")

    print("\n" + "=" * 80)
    print("BM25 + Embedding ハイブリッド検索の効果")
    print("=" * 80)

    print("\n【BM25の特性】")
    print("  - キーワードベースの検索")
    print("  - TF-IDF (単語の出現頻度 × 逆文書頻度)")
    print("  - Exact matchを重視")
    print("")
    print("  Query: 'prosciutto'")
    print("    → 'prosciutto'を含む項目に高スコア")
    print("    → 完全一致が保証される ✅")

    print("\n【ハイブリッドスコアのシミュレーション】")
    print("")
    print("  公式: Hybrid = α × BM25 + β × Embedding")
    print("  例: α=0.5, β=0.5")
    print("")
    print("  | 項目                  | BM25  | Embed | Hybrid | 順位 |")
    print("  |----------------------|-------|-------|--------|------|")
    print("  | Ham, prosciutto      | 0.95  | 0.70  | 0.825  | 1位✅|")
    print("  | Mortadella           | 0.00  | 0.87  | 0.435  | 5位  |")
    print("  | Italian sausage      | 0.00  | 0.84  | 0.420  | 8位  |")
    print("  | Ham luncheon meat    | 0.00  | 0.79  | 0.395  | 12位 |")
    print("")
    print("  → 'Ham, prosciutto'が確実に1位に！✅")

    print("\n【なぜハイブリッドが有効か】")
    print("")
    print("  1. 相補性:")
    print("     - BM25: exact match検出 ✅")
    print("     - Embedding: 意味的類似性 ✅")
    print("")
    print("  2. BM25の強み:")
    print("     - 'prosciutto'を含む項目を必ず上位に")
    print("     - 固有名詞・専門用語に強い")
    print("")
    print("  3. Embeddingの強み:")
    print("     - 同義語を検出 (例: 'italian ham' → 'prosciutto')")
    print("     - 綴りの揺れに対応")
    print("")
    print("  4. 相互補完:")
    print("     - BM25だけ → 同義語に弱い")
    print("     - Embeddingだけ → exact matchを見逃す (現在の問題)")
    print("     - Hybrid → 両方の利点を活かす ✅")

    print("\n【他のケースへの影響】")
    print("")
    print("  frittata → Breakfast tart:")
    print("    BM25: 'frittata'を含む項目がDBにない → 効果なし ❌")
    print("    Embedding: 'omelet'系を検出可能 → 効果あり ✅")
    print("    結論: ハイブリッドでも改善しない（DB不足が原因）")
    print("")
    print("  mexican rice → spanish rice:")
    print("    BM25: 'mexican'が含まれない → 低スコア")
    print("    Embedding: 意味的に類似 → 高スコア ✅")
    print("    結論: Embeddingが主導、ハイブリッドでも大きな改善なし")

    print("\n" + "=" * 80)
    print("結論")
    print("=" * 80)
    print("")
    print("【根本原因】")
    print("  Embedding検索は意味的類似性を重視し、")
    print("  単語の完全一致（exact match）を保証しない。")
    print("")
    print("  'prosciutto' vs 'Ham, prosciutto':")
    print("    → 'Ham'が前にあるため、Embeddingベクトルの重みが分散")
    print("    → 'Mortadella'など意味的に近い項目の方が高スコア")
    print("")
    print("【BM25+Embeddingハイブリッドの有効性】")
    print("")
    print("  ✅ prosciuttoケース: 非常に有効")
    print("     → BM25がexact matchを保証")
    print("     → 確実に上位にランクイン")
    print("")
    print("  ✅ 一般的な改善: 固有名詞・専門用語全般に効果")
    print("     → 'quinoa', 'edamame', 'kimchi'など")
    print("")
    print("  ❌ データベース不足ケース: 効果なし")
    print("     → frittata, dinner rollなど")
    print("     → DB自体に項目がない場合は検索できない")
    print("")
    print("【推奨アクション】")
    print("")
    print("  優先度1: BM25+Embeddingハイブリッド検索を実装")
    print("           → 根本解決、prosciutto問題を確実に解決")
    print("")
    print("  優先度2: Stage1 top_kを40→60に増やす")
    print("           → 即効性のある補助策")
    print("")
    print("  優先度3: 同義語辞書（エッジケース対応）")
    print("           → データベース不足を補う")


if __name__ == "__main__":
    analyze_embedding_weakness()
