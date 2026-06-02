from apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval import (
    detect_prompt_leakage,
    dish_match_metrics,
    gate_decision,
    portion_score_from_bands,
)


def _baseline() -> dict:
    return {
        "calorie_mae_percent": 20.0,
        "high_error_rate_30_percent": 10.0,
        "avg_latency_sec": 10.0,
        "avg_cost_usd": 0.01,
    }


def test_gate_decision_holds_when_required_image_count_not_met() -> None:
    summary = {
        "calorie_mae_percent": 10.0,
        "high_error_rate_30_percent": 5.0,
        "avg_latency_sec": 9.0,
        "avg_cost_usd": 0.005,
        "evaluated_image_count": 25,
        "expected_image_count": 25,
        "coverage_complete": True,
        "all_success": True,
        "failure_count": 0,
    }
    decision = gate_decision(
        summary,
        _baseline(),
        {"max_avg_cost_usd_per_image": 0.05},
        required_image_count=50,
    )
    assert decision["decision"] == "hold"
    assert any("required 50" in reason for reason in decision["reasons"])


def test_gate_decision_promotes_only_when_quality_and_baseline_gates_pass() -> None:
    summary = {
        "calorie_mae_percent": 17.5,
        "high_error_rate_30_percent": 10.0,
        "avg_latency_sec": 11.5,
        "avg_cost_usd": 0.009,
        "evaluated_image_count": 50,
        "expected_image_count": 50,
        "coverage_complete": True,
        "all_success": True,
        "failure_count": 0,
    }
    decision = gate_decision(
        summary,
        _baseline(),
        {"max_avg_cost_usd_per_image": 0.05},
        required_image_count=50,
    )
    assert decision["decision"] == "promote"


def test_prompt_leakage_detection_flags_eval_specific_tokens() -> None:
    prompt = "Use test_food22 and ground truth labels to calibrate calories."
    matches = detect_prompt_leakage(prompt)
    assert "test_image_id" in matches
    assert "ground_truth_word" in matches


def test_portion_score_from_bands_threshold_table() -> None:
    # 5 needs f25==1.0 AND f10>=0.5
    assert portion_score_from_bands({"within_10": 1.0, "within_25": 0.0}, 3) == 5
    # all within 25% but <half within 10% -> 4 (f25==1.0 but f10<0.5)
    assert portion_score_from_bands({"within_10": 0.0, "within_25": 1.0}, 2) == 4
    assert portion_score_from_bands({"within_10": 0.0, "within_25": 0.75}, 4) == 4
    assert portion_score_from_bands({"within_10": 0.0, "within_25": 0.5}, 2) == 3
    assert portion_score_from_bands({"within_10": 0.0, "within_25": 0.25}, 4) == 2
    assert portion_score_from_bands({"within_10": 0.0, "within_25": 0.1}, 10) == 1
    assert (
        portion_score_from_bands({"within_10": 0.0, "within_25": 0.0, "gross": 1.0}, 2)
        == 0
    )
    # matched==0 -> 0 (no identified item to size)
    assert portion_score_from_bands({"within_10": 0.0, "within_25": 0.0}, 0) == 0
    # matched>0 but nothing weighable (banded==0) -> None (no portion signal, not a real 0)
    assert (
        portion_score_from_bands({"within_10": 0.0, "within_25": 0.0, "gross": 0.0}, 2)
        is None
    )


def test_dish_match_metrics_exposes_deterministic_portion_score() -> None:
    pred = [
        {"name": "chicken breast", "weight_g": 160.0, "calories": 264.0},
        {"name": "broccoli", "weight_g": 70.0, "calories": 28.7},
    ]
    gt = [
        {"name": "chicken breast", "weight_g": 150.0, "calories": 247.5},
        {"name": "broccoli", "weight_g": 100.0, "calories": 35.0},
    ]
    m = dish_match_metrics(pred, gt)
    if m is None:  # scipy unavailable in this env
        return
    # chicken 160 vs 150 -> 0.067 (within_10); broccoli 70 vs 100 -> 0.30 (gross).
    # f25 = 0.5 -> score 3; key is present and integer.
    assert "portion_score_0_5" in m
    assert m["portion_score_0_5"] == 3
