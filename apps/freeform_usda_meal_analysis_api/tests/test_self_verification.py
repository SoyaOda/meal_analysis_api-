"""Tests for apply_verification: the self-verification 2nd pass filters items the model
marked 'not_present', keeps 'present'/'unsure', drops emptied dishes, and is fail-safe
(a verdict whose name does not match a real item never silently drops it)."""

from apps.freeform_usda_meal_analysis_api.services.vlm_service import apply_verification


def _resp():
    return {
        "meal_title": "Test",
        "dishes": [
            {
                "dish_name": "Salad",
                "main_food": {"search_name": "Mixed greens, raw", "weight_g": 80},
                "extras": [
                    {"search_name": "Apples, raw", "weight_g": 60},
                    {"search_name": "Tomatoes, raw", "weight_g": 30},
                ],
            },
            {
                "dish_name": "Phantom side",
                "main_food": {"search_name": "Rice, white, cooked", "weight_g": 200},
                "extras": [],
            },
        ],
    }


def test_drops_not_present_items() -> None:
    verdicts = [
        {"item": "Mixed greens, raw", "verdict": "present"},
        {"item": "Apples, raw", "verdict": "not_present"},
        {"item": "Tomatoes, raw", "verdict": "unsure"},
        {"item": "Rice, white, cooked", "verdict": "not_present"},
    ]
    out, n_dropped = apply_verification(_resp(), verdicts)
    assert n_dropped == 2  # phantom apple + phantom rice
    # Salad keeps greens (present) + tomatoes (unsure kept); apples removed.
    salad = out["dishes"][0]
    extras = [e["search_name"] for e in salad["extras"]]
    assert extras == ["Tomatoes, raw"]
    assert salad["main_food"]["search_name"] == "Mixed greens, raw"
    # Phantom-rice dish had only a not_present main_food -> whole dish removed.
    assert len(out["dishes"]) == 1


def test_drop_unsure_flag() -> None:
    verdicts = [{"item": "Tomatoes, raw", "verdict": "unsure"}]
    out, n_dropped = apply_verification(_resp(), verdicts, drop_unsure=True)
    assert n_dropped == 1
    assert all(
        e["search_name"] != "Tomatoes, raw" for d in out["dishes"] for e in d["extras"]
    )


def test_name_mismatch_is_fail_safe_keeps_item() -> None:
    # A verdict that paraphrases the name must NOT drop the real item.
    verdicts = [{"item": "apple slices", "verdict": "not_present"}]
    out, n_dropped = apply_verification(_resp(), verdicts)
    assert n_dropped == 0
    names = [e["search_name"] for d in out["dishes"] for e in d["extras"]]
    assert "Apples, raw" in names


def test_empty_verdicts_no_change() -> None:
    out, n_dropped = apply_verification(_resp(), [])
    assert n_dropped == 0
    assert len(out["dishes"]) == 2
