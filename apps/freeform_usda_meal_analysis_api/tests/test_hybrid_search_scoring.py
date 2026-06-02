"""Tests for hybrid-search query normalization (cosine-similarity correctness)."""

import numpy as np
import pytest

# bm25s / Stemmer are required to import the module; skip cleanly if unavailable.
hybrid_search = pytest.importorskip(
    "apps.freeform_usda_meal_analysis_api.services.hybrid_search"
)
l2_normalize_rows = hybrid_search.l2_normalize_rows


def test_l2_normalize_rows_produces_unit_norm() -> None:
    matrix = np.array([[3.0, 4.0], [1.0, 0.0]], dtype="float32")
    out = l2_normalize_rows(matrix)
    norms = np.linalg.norm(out, axis=1)
    assert np.allclose(norms, [1.0, 1.0])
    assert np.allclose(out[0], [0.6, 0.8])


def test_l2_normalize_rows_zero_vector_does_not_nan() -> None:
    matrix = np.array([[0.0, 0.0, 0.0]], dtype="float32")
    out = l2_normalize_rows(matrix)
    assert not np.isnan(out).any()
    assert np.allclose(out, 0.0)


def test_normalized_inner_product_equals_cosine() -> None:
    # After normalizing both query and corpus, IndexFlatIP's inner product IS cosine.
    query = np.array([[2.0, 0.0, 0.0]], dtype="float32")
    doc = np.array([[1.0, 1.0, 0.0]], dtype="float32")
    cos = (l2_normalize_rows(query) @ l2_normalize_rows(doc).T).item()
    assert abs(cos - (1.0 / np.sqrt(2))) < 1e-6


def test_higher_cosine_means_higher_score_after_fix() -> None:
    # Sanity: with raw similarities used directly as scores, a more-similar doc
    # outranks a less-similar one (the old 1/(1+sim) transform inverted this).
    query = l2_normalize_rows(np.array([[1.0, 0.0]], dtype="float32"))
    near = l2_normalize_rows(np.array([[0.9, 0.1]], dtype="float32"))
    far = l2_normalize_rows(np.array([[0.1, 0.9]], dtype="float32"))
    sim_near = (query @ near.T).item()
    sim_far = (query @ far.T).item()
    assert sim_near > sim_far  # direct similarity preserves correct ordering
