# -*- coding: utf-8 -*-
"""
Test module for embedding model
"""

import sys
import json
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.embedding import EmbeddingModel
from src.preprocessing.text_normalizer import normalize_text, build_query_text


def load_test_data():
    """Load prepared test data"""
    data_dir = Path(__file__).parent / "data"

    with open(data_dir / "test_queries.json", 'r', encoding='utf-8') as f:
        queries = json.load(f)

    return queries


def test_model_initialization():
    """Test embedding model initialization"""
    print("\n=== test_model_initialization ===")

    # Test with default parameters
    model = EmbeddingModel()
    assert model is not None, "Model should be initialized"
    assert model.model_name == "sentence-transformers/all-MiniLM-L6-v2", "Default model name should match"
    assert model.device == "cpu", "Default device should be cpu"
    assert model.normalize_embeddings == True, "Default normalization should be True"
    print("Test 1 passed: Default initialization")

    # Test embedding dimension
    dim = model.get_embedding_dim()
    assert dim == 384, f"Expected dimension 384, got {dim}"
    print(f"Test 2 passed: Embedding dimension = {dim}")

    print("All model initialization tests passed!")
    return model


def test_single_text_encoding(model):
    """Test encoding a single text"""
    print("\n=== test_single_text_encoding ===")

    # Test case 1: Simple text
    text = "chicken breast"
    embedding = model.encode(text)

    assert embedding is not None, "Embedding should not be None"
    assert isinstance(embedding, np.ndarray), "Embedding should be numpy array"
    assert embedding.shape == (1, 384), f"Expected shape (1, 384), got {embedding.shape}"
    print(f"Test 1 passed: Single text encoded, shape = {embedding.shape}")

    # Test case 2: Check normalization (vector norm should be ~1.0)
    norm = np.linalg.norm(embedding)
    assert 0.99 < norm < 1.01, f"Normalized vector should have norm ~1.0, got {norm}"
    print(f"Test 2 passed: Vector is normalized, norm = {norm:.6f}")

    # Test case 3: Empty text handling
    empty_embedding = model.encode("")
    assert empty_embedding.shape == (1, 384), "Empty text should still produce embedding"
    print(f"Test 3 passed: Empty text handled, shape = {empty_embedding.shape}")

    print("All single text encoding tests passed!")


def test_batch_encoding(model):
    """Test encoding multiple texts in batch"""
    print("\n=== test_batch_encoding ===")

    # Test case 1: Multiple texts
    texts = [
        "chicken breast grilled",
        "rice with vegetables",
        "beef steak",
        "salad greens",
        "pasta with tomato sauce"
    ]

    embeddings = model.encode(texts, batch_size=2)

    assert embeddings is not None, "Embeddings should not be None"
    assert isinstance(embeddings, np.ndarray), "Embeddings should be numpy array"
    assert embeddings.shape == (5, 384), f"Expected shape (5, 384), got {embeddings.shape}"
    print(f"Test 1 passed: Batch encoding, shape = {embeddings.shape}")

    # Test case 2: Check all vectors are normalized
    norms = np.linalg.norm(embeddings, axis=1)
    assert all(0.99 < norm < 1.01 for norm in norms), "All vectors should be normalized"
    print(f"Test 2 passed: All vectors normalized, norms range = [{norms.min():.6f}, {norms.max():.6f}]")

    # Test case 3: Different texts should have different embeddings
    similarity = np.dot(embeddings[0], embeddings[1])
    assert similarity < 0.99, "Different texts should have different embeddings"
    print(f"Test 3 passed: Different texts produce different embeddings (similarity = {similarity:.4f})")

    print("All batch encoding tests passed!")


def test_similarity_computation(model):
    """Test semantic similarity computation"""
    print("\n=== test_similarity_computation ===")

    # Similar texts should have high similarity
    text1 = "chicken breast grilled"
    text2 = "grilled chicken"
    text3 = "chocolate cake"

    embeddings = model.encode([text1, text2, text3])

    # Compute cosine similarity (dot product since vectors are normalized)
    sim_1_2 = np.dot(embeddings[0], embeddings[1])
    sim_1_3 = np.dot(embeddings[0], embeddings[2])

    print(f"Similarity (chicken vs grilled chicken): {sim_1_2:.4f}")
    print(f"Similarity (chicken vs chocolate cake): {sim_1_3:.4f}")

    assert sim_1_2 > sim_1_3, "Similar texts should have higher similarity"
    assert sim_1_2 > 0.7, "Very similar texts should have similarity > 0.7"
    print("Test passed: Similarity computation works as expected")

    print("All similarity computation tests passed!")


def test_with_real_data(model):
    """Test with actual VLM query data"""
    print("\n=== test_with_real_data ===")

    queries = load_test_data()

    # Prepare query texts
    query_texts = []
    for query in queries[:10]:  # Use first 10 queries
        text = build_query_text(query['search_name'], query['description'])
        normalized = normalize_text(text)
        query_texts.append(normalized)

    print(f"\nEncoding {len(query_texts)} VLM queries...")
    for i, text in enumerate(query_texts[:3], 1):
        print(f"  {i}. '{text}'")

    # Encode all queries
    embeddings = model.encode(query_texts, batch_size=4, show_progress_bar=False)

    assert embeddings.shape == (10, 384), f"Expected shape (10, 384), got {embeddings.shape}"
    print(f"\nTest passed: Encoded {len(query_texts)} queries, shape = {embeddings.shape}")

    # Check normalization
    norms = np.linalg.norm(embeddings, axis=1)
    print(f"Norms range: [{norms.min():.6f}, {norms.max():.6f}]")
    assert all(0.99 < norm < 1.01 for norm in norms), "All vectors should be normalized"

    # Find similar queries
    print("\nFinding similar queries (using first query):")
    query_embedding = embeddings[0]
    similarities = np.dot(embeddings, query_embedding)

    # Get top 3 most similar (excluding itself)
    top_indices = np.argsort(similarities)[::-1][:3]
    for i, idx in enumerate(top_indices, 1):
        print(f"  {i}. '{query_texts[idx]}' (similarity: {similarities[idx]:.4f})")

    print("\nAll real data tests passed!")


def test_embedding_consistency(model):
    """Test that same input produces same output"""
    print("\n=== test_embedding_consistency ===")

    text = "chicken breast grilled"

    # Encode same text twice
    emb1 = model.encode(text)
    emb2 = model.encode(text)

    # Check they are identical
    diff = np.max(np.abs(emb1 - emb2))
    assert diff < 1e-6, f"Same text should produce identical embeddings, max diff = {diff}"
    print(f"Test passed: Embeddings are consistent (max diff = {diff:.10f})")

    print("All consistency tests passed!")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Embedding Model Test Suite")
    print("=" * 60)

    try:
        # Initialize model once for all tests
        model = test_model_initialization()

        # Run other tests
        test_single_text_encoding(model)
        test_batch_encoding(model)
        test_similarity_computation(model)
        test_embedding_consistency(model)
        test_with_real_data(model)

        print("\n" + "=" * 60)
        print("All tests passed successfully!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        return False
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)