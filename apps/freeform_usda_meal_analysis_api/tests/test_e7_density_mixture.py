"""E7: NutritionCalculator.calculate_mixture — top-k density mixture.

E[nutrition] = E[kcal/100g] × (weight_g/100): grams fixed (VLM), density = softmax(score/τ)
weighted mean over the top-k candidates' per-100g nutrition. Verifies the mixing math,
score weighting, single-candidate degenerate case, and skipping candidates with no nutrition.
"""

from apps.freeform_usda_meal_analysis_api.services.nutrition_service import (
    NutritionCalculator,
)


class _StubNutritionService:
    """get_nutrition_per_100g(fdc_id) -> per-100g dict or None (None = not in DB)."""

    def __init__(self, table):
        self._t = table

    def get_nutrition_per_100g(self, fdc_id):
        return self._t.get(fdc_id)


def _calc(table):
    return NutritionCalculator(_StubNutritionService(table))


D = {
    "a": {"calories": 100.0, "protein_g": 10.0, "fat_g": 1.0, "carbs_g": 5.0},
    "b": {"calories": 300.0, "protein_g": 0.0, "fat_g": 20.0, "carbs_g": 40.0},
}


def test_single_candidate_equals_top1():
    calc = _calc(D)
    out = calc.calculate_mixture([{"fdc_id": "a", "rerank_score": 0.9}], 200.0)
    # density 100 kcal/100g × 200g = 200 kcal
    assert out["calories"] == 200.0
    assert out["protein_g"] == 20.0


def test_equal_scores_average_density():
    calc = _calc(D)
    # equal scores → softmax weights 0.5/0.5 → density (100+300)/2 = 200 kcal/100g × 100g = 200
    out = calc.calculate_mixture(
        [{"fdc_id": "a", "rerank_score": 1.0}, {"fdc_id": "b", "rerank_score": 1.0}],
        100.0,
    )
    assert abs(out["calories"] - 200.0) < 1e-6


def test_score_weighting_favors_higher():
    calc = _calc(D)
    # 'a' (100) heavily favored over 'b' (300) → mixed density well below the 200 midpoint
    out = calc.calculate_mixture(
        [{"fdc_id": "a", "rerank_score": 5.0}, {"fdc_id": "b", "rerank_score": 0.0}],
        100.0,
        temperature=1.0,
    )
    assert 100.0 < out["calories"] < 150.0  # close to 'a'


def test_missing_nutrition_skipped():
    calc = _calc(D)
    # 'z' not in DB → dropped; weights renormalized over {a,b}
    out = calc.calculate_mixture(
        [
            {"fdc_id": "z", "rerank_score": 9.0},
            {"fdc_id": "a", "rerank_score": 1.0},
            {"fdc_id": "b", "rerank_score": 1.0},
        ],
        100.0,
    )
    assert abs(out["calories"] - 200.0) < 1e-6  # avg of a,b only


def test_none_when_no_valid_candidate():
    calc = _calc(D)
    assert calc.calculate_mixture([{"fdc_id": "z", "rerank_score": 1.0}], 100.0) is None
