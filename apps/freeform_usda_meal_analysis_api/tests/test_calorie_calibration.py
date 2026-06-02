"""Tests for the post-hoc calorie calibration layer."""

import json

import pytest

# core/__init__ pulls in tenacity/faiss-class deps; skip cleanly if the env lacks them
# (the project venv has them and runs these for real).
_cal = pytest.importorskip(
    "apps.freeform_usda_meal_analysis_api.core.calorie_calibration"
)
CalorieCalibration = _cal.CalorieCalibration
load_calibration = _cal.load_calibration


def test_disabled_is_noop() -> None:
    cal = CalorieCalibration(enabled=False, slope=0.33, intercept=469.0)
    assert cal.scale_factor(1000.0) == 1.0
    assert cal.scale_factor(300.0) == 1.0


def test_corrected_total_affine() -> None:
    cal = CalorieCalibration(enabled=True, slope=0.33, intercept=469.0)
    assert abs(cal.corrected_total(1000.0) - 799.0) < 1e-6


def test_scale_factor_matches_corrected_over_raw() -> None:
    cal = CalorieCalibration(
        enabled=True, slope=0.33, intercept=469.0, min_factor=0.5, max_factor=2.5
    )
    raw = 686.0
    expected = (0.33 * raw + 469.0) / raw
    assert abs(cal.scale_factor(raw) - expected) < 1e-6


def test_scale_factor_clamped() -> None:
    # small raw -> intercept dominates -> factor would be huge -> clamp to max_factor.
    cal = CalorieCalibration(
        enabled=True, slope=0.33, intercept=469.0, min_factor=0.5, max_factor=2.5
    )
    assert cal.scale_factor(50.0) == 2.5
    # large raw with low slope -> factor would be tiny -> clamp to min_factor.
    cal2 = CalorieCalibration(
        enabled=True, slope=0.1, intercept=0.0, min_factor=0.5, max_factor=2.5
    )
    assert cal2.scale_factor(5000.0) == 0.5


def test_nonpositive_raw_is_noop() -> None:
    cal = CalorieCalibration(enabled=True, slope=0.33, intercept=469.0)
    assert cal.scale_factor(0.0) == 1.0
    assert cal.scale_factor(-10.0) == 1.0


def test_load_missing_file_returns_disabled(tmp_path) -> None:
    cal = load_calibration(tmp_path / "nope.json")
    assert cal.enabled is False
    assert cal.scale_factor(1000.0) == 1.0


def test_load_enabled_config(tmp_path) -> None:
    p = tmp_path / "cal.json"
    p.write_text(
        json.dumps(
            {"enabled": True, "slope": 0.5, "intercept": 100.0, "provenance": "test"}
        )
    )
    cal = load_calibration(p)
    assert cal.enabled is True
    assert abs(cal.corrected_total(1000.0) - 600.0) < 1e-6


def test_pipeline_calibration_scales_consistently() -> None:
    # Integration: the pipeline method scales total + per-dish + per-ingredient +
    # weights by one factor so the response stays internally consistent.
    pipeline_mod = pytest.importorskip(
        "apps.freeform_usda_meal_analysis_api.services.pipeline"
    )
    Pipeline = pipeline_mod.MealAnalysisPipeline

    class _Stub:
        calorie_calibration = CalorieCalibration(
            enabled=True, slope=1.0, intercept=500.0, max_factor=3.0
        )

    dishes = [
        {
            "main_food": {
                "weight_g": 100,
                "nutrition": {
                    "calories": 500,
                    "protein_g": 10,
                    "fat_g": 5,
                    "carbs_g": 20,
                },
            },
            "extras": [
                {
                    "weight_g": 20,
                    "nutrition": {
                        "calories": 100,
                        "protein_g": 1,
                        "fat_g": 2,
                        "carbs_g": 3,
                    },
                }
            ],
        }
    ]
    total = {"calories": 600.0, "protein_g": 11.0, "fat_g": 7.0, "carbs_g": 23.0}
    out_dishes, out_total = Pipeline._apply_calorie_calibration(_Stub(), dishes, total)

    # corrected = 1.0*600 + 500 = 1100 -> factor = 1100/600
    assert abs(out_total["calories"] - 1100.0) < 0.5
    mf = out_dishes[0]["main_food"]
    ex = out_dishes[0]["extras"][0]
    # internal consistency: dishes sum == total
    assert (
        abs(
            mf["nutrition"]["calories"]
            + ex["nutrition"]["calories"]
            - out_total["calories"]
        )
        < 0.5
    )
    # weights scaled by the same factor
    assert abs(mf["weight_g"] - 100 * (1100 / 600)) < 0.5

    # disabled -> no-op
    class _Off:
        calorie_calibration = CalorieCalibration(enabled=False)

    same_total = {"calories": 500.0}
    _, t = Pipeline._apply_calorie_calibration(
        _Off(), [{"main_food": {"nutrition": {"calories": 500}}}], same_total
    )
    assert t["calories"] == 500.0
