"""Tests for diagnostic metric decomposition (signed bias, calibration, dish-match)."""

from apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval import (
    _name_similarity,
    compute_decomposed_metrics,
    dish_match_metrics,
    extract_pred_items,
)


def _row(label_cal, pred_cal, macros=None):
    macros = macros or {}
    return {
        "success": True,
        "label": {
            "calories": label_cal,
            "protein": macros.get("lp", 0),
            "fat": macros.get("lf", 0),
            "carbs": macros.get("lc", 0),
        },
        "prediction": {
            "calories": pred_cal,
            "protein": macros.get("pp", 0),
            "fat": macros.get("pf", 0),
            "carbs": macros.get("pc", 0),
        },
    }


def test_decomposition_detects_underestimation_and_slope() -> None:
    # pred = 0.5 * label exactly -> slope 0.5, intercept 0, signed -50%.
    rows = [_row(lc, lc * 0.5) for lc in (200.0, 400.0, 600.0, 800.0, 1000.0)]
    m = compute_decomposed_metrics(rows)
    assert m["signed_mean_error_percent"] == -50.0
    assert m["signed_median_error_percent"] == -50.0
    assert abs(m["calibration_slope"] - 0.5) < 1e-6
    assert abs(m["calibration_intercept"]) < 1e-6
    assert abs(m["calibration_r2"] - 1.0) < 1e-6


def test_decomposition_robust_slope_matches_known_slope() -> None:
    # pred = 0.5 * label exactly -> OLS and Theil-Sen slopes both ~0.5.
    rows = [_row(lc, lc * 0.5) for lc in (200.0, 400.0, 600.0, 800.0, 1000.0)]
    m = compute_decomposed_metrics(rows)
    assert abs(m["calibration_slope"] - 0.5) < 1e-6
    assert abs(m["theil_sen_slope"] - 0.5) < 1e-3


def test_decomposition_overestimation_positive_signed() -> None:
    rows = [_row(lc, lc * 1.2) for lc in (300.0, 500.0, 900.0)]
    m = compute_decomposed_metrics(rows)
    assert m["signed_mean_error_percent"] > 0  # over-estimation


def test_decomposition_macro_and_abs_kcal() -> None:
    rows = [
        _row(
            1000.0, 900.0, {"lp": 50, "pp": 40, "lf": 30, "pf": 30, "lc": 100, "pc": 80}
        )
    ]
    m = compute_decomposed_metrics(rows)
    assert m["abs_kcal_mae"] == 100.0
    assert m["macro_mae_percent"]["protein"] == 20.0  # |40-50|/50*100
    assert m["macro_mae_percent"]["fat"] == 0.0
    assert m["macro_mae_percent"]["carbs"] == 20.0  # |80-100|/100*100


def test_decomposition_empty() -> None:
    m = compute_decomposed_metrics([])
    assert m["signed_mean_error_percent"] is None
    assert m["abs_kcal_mae"] is None


def test_name_similarity_matches_usda_verbose_to_short_gt() -> None:
    import difflib

    pred = "Chicken, broilers or fryers, breast, meat only, cooked, roasted"
    gt = "chicken breast"
    # old char-only difflib is weak; the new token-overlap term rescues it.
    char_only = difflib.SequenceMatcher(None, pred.lower(), gt.lower()).ratio()
    assert char_only < 0.5
    assert _name_similarity(pred, gt) >= 0.75


def test_dish_match_recall_high_on_usda_style_names() -> None:
    # Predicted items carry verbose USDA names/matched_desc; GT names are short.
    pred = [
        {
            "name": "Chicken, broilers or fryers, breast, meat only, cooked, roasted",
            "matched_desc": "Chicken, broilers or fryers, breast, cooked, roasted",
            "weight_g": 150,
            "calories": 248,
        },
        {
            "name": "Broccoli, cooked, boiled, drained, without salt",
            "matched_desc": "Broccoli, cooked, boiled",
            "weight_g": 100,
            "calories": 35,
        },
    ]
    gt = [
        {"name": "chicken breast", "weight_g": 150, "calories": 247.5},
        {"name": "broccoli", "weight_g": 100, "calories": 35.0},
    ]
    m = dish_match_metrics(pred, gt)
    assert m is not None
    assert m["recall"] == 1.0 and m["f1"] == 1.0  # difflib gave ~0
    assert m["portion_bands"]["within_10"] == 1.0
    assert (
        m["nutrient_self_consistency"] == 1.0
    )  # ~1.65 and 0.35 kcal/g, both plausible


def test_nutrient_self_consistency_flags_implausible_density() -> None:
    pred = [
        {
            "name": "salad",
            "weight_g": 100,
            "calories": 1500,
        },  # 15 kcal/g -> implausible
        {"name": "rice", "weight_g": 150, "calories": 195},  # 1.3 kcal/g -> ok
    ]
    gt = [{"name": "salad", "weight_g": 100, "calories": 50}]
    m = dish_match_metrics(pred, gt)
    assert m["nutrient_self_consistency"] == 0.5


def test_dish_match_perfect() -> None:
    pred = [
        {"name": "chicken breast", "weight_g": 150},
        {"name": "broccoli", "weight_g": 90},
    ]
    gt = [
        {"name": "chicken breast", "weight_g": 150},
        {"name": "broccoli", "weight_g": 100},
    ]
    m = dish_match_metrics(pred, gt)
    assert m is not None
    assert m["recall"] == 1.0 and m["precision"] == 1.0 and m["f1"] == 1.0
    assert m["matched"] == 2
    assert m["matched_weight_mae_g"] == 5.0  # mean(|150-150|, |90-100|) = 5


def test_dish_match_no_prediction() -> None:
    m = dish_match_metrics([], [{"name": "rice", "weight_g": 100}])
    assert m is not None and m["recall"] == 0.0 and m["n_pred"] == 0


def test_dish_match_empty_gt_returns_none() -> None:
    assert dish_match_metrics([{"name": "x", "weight_g": 1}], []) is None


def test_extract_pred_items_from_payload() -> None:
    payload = {
        "dishes": [
            {
                "ingredients": [
                    {
                        "ingredient_name": "grilled chicken",
                        "matched_db_description": "Chicken, grilled",
                        "fdc_id": 12345,
                        "weight_g": 150,
                        "calculated_nutrition": {"calories": 247.5},
                    }
                ]
            }
        ]
    }
    items = extract_pred_items(payload)
    assert len(items) == 1
    assert items[0]["name"] == "grilled chicken"
    assert items[0]["fdc_id"] == 12345
    assert items[0]["weight_g"] == 150
    assert items[0]["calories"] == 247.5
