#!/usr/bin/env python3
"""
Novita AI プロバイダーのテストスクリプト
"""
import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

async def test_embedding_provider():
    """Embeddingプロバイダーのテスト"""
    print("\n" + "="*50)
    print("🧪 Novita AI Embedding Provider Test")
    print("="*50)

    from apps.freeform_usda_meal_analysis_api.services.embedding_providers import EmbeddingProviderFactory

    try:
        provider = EmbeddingProviderFactory.create("novita")
        print(f"✅ Provider created: {type(provider).__name__}")

        # テストテキスト
        test_texts = [
            "grilled chicken breast",
            "steamed rice",
            "mixed vegetables"
        ]

        print(f"\n📝 Test texts: {test_texts}")

        embeddings = await provider.generate_embeddings(test_texts)

        print(f"\n✅ Generated {len(embeddings)} embeddings")
        for i, emb in enumerate(embeddings):
            print(f"  - Text {i+1}: dimension={len(emb)}, first 3 values={emb[:3]}")

        return True

    except Exception as e:
        print(f"\n❌ Embedding test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_reranker_provider():
    """Rerankerプロバイダーのテスト"""
    print("\n" + "="*50)
    print("🧪 Novita AI Reranker Provider Test")
    print("="*50)

    from apps.freeform_usda_meal_analysis_api.services.reranker_providers import RerankerProviderFactory

    try:
        provider = RerankerProviderFactory.create("novita")
        print(f"✅ Provider created: {type(provider).__name__}")

        # テストクエリとドキュメント
        query = "grilled chicken"
        documents = [
            "Chicken, broilers or fryers, breast, meat only, cooked, grilled",
            "Chicken, roasting, meat only, cooked, roasted",
            "Beef, ground, 80% lean meat / 20% fat, patty, cooked, broiled",
            "Fish, salmon, Atlantic, wild, cooked, dry heat"
        ]

        print(f"\n📝 Query: {query}")
        print(f"📝 Documents ({len(documents)}):")
        for i, doc in enumerate(documents):
            print(f"  {i+1}. {doc}")

        best_idx, scores = await provider.rerank(query, documents, top_n=4)

        print(f"\n✅ Reranking results:")
        print(f"  Best match index: {best_idx}")
        print(f"  Scores:")
        for i, score in enumerate(scores):
            marker = "👑" if i == best_idx else "  "
            print(f"  {marker} Doc {i+1}: {score:.4f}")

        return True

    except Exception as e:
        print(f"\n❌ Reranker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """メインテスト関数"""
    print("\n🚀 Novita AI Provider Tests")
    print("="*60)

    # 環境変数チェック
    novita_key = os.getenv("NOVITA_API_KEY")
    if not novita_key:
        print("❌ NOVITA_API_KEY not set!")
        return
    print(f"✅ NOVITA_API_KEY found: {novita_key[:20]}...")

    embedding_ok = await test_embedding_provider()
    reranker_ok = await test_reranker_provider()

    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    print(f"  Embedding: {'✅ PASS' if embedding_ok else '❌ FAIL'}")
    print(f"  Reranker:  {'✅ PASS' if reranker_ok else '❌ FAIL'}")
    print("="*60)

    if embedding_ok and reranker_ok:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed")


if __name__ == "__main__":
    asyncio.run(main())
