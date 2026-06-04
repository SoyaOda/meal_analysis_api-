"""Unit tests for self-consistency median-calorie selection (pipeline wrapper).

Validates the pure selection logic that backs the K-sample self-consistency
recipe (flash, K=3 seeds, median total-calorie) — see
evals/lessons/20260604_self_consistency_median_ensemble_significant_calorie_win.md
"""

import pytest

# services.pipeline pulls heavy deps (vlm_service -> tenacity/faiss); skip if absent.
_pipe_mod = pytest.importorskip(
    "apps.freeform_usda_meal_analysis_api.services.pipeline"
)
Pipeline = _pipe_mod.MealAnalysisPipeline


class _Nutri:
    """Stand-in for NutritionInfo (object with .calories)."""

    def __init__(self, calories: float) -> None:
        self.calories = calories


def _r(cal: float, tag: int, *, as_obj: bool = False) -> dict:
    total = _Nutri(cal) if as_obj else {"calories": cal}
    return {"total_nutrition": total, "tag": tag}


def test_result_calories_reads_dict_and_object() -> None:
    assert Pipeline._result_calories(_r(512.5, 0)) == 512.5
    assert Pipeline._result_calories(_r(512.5, 0, as_obj=True)) == 512.5
    # missing/None -> 0.0 (no crash)
    assert Pipeline._result_calories({"total_nutrition": None}) == 0.0
    assert Pipeline._result_calories({}) == 0.0


def test_median_selection_odd_k_returns_middle_sample() -> None:
    # totals 300/500/400 -> median 400 -> the result tagged with 400
    results = [_r(300, 0), _r(500, 1), _r(400, 2)]
    sel = Pipeline._select_median_calorie_result(results)
    assert sel["tag"] == 2
    assert Pipeline._result_calories(sel) == 400


def test_median_selection_k5() -> None:
    results = [_r(100, 0), _r(500, 1), _r(300, 2), _r(200, 3), _r(400, 4)]
    sel = Pipeline._select_median_calorie_result(results)
    assert Pipeline._result_calories(sel) == 300
    assert sel["tag"] == 2


def test_median_returns_an_actual_sample_object() -> None:
    # the selected result must BE one of the inputs (self-consistent foods/macros)
    results = [_r(420, 7), _r(610, 8), _r(515, 9)]
    sel = Pipeline._select_median_calorie_result(results)
    assert sel is results[2]  # 515 is the median


def test_empty_raises() -> None:
    with pytest.raises(ValueError):
        Pipeline._select_median_calorie_result([])
