from apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval import (
    detect_prompt_leakage,
    gate_decision,
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
