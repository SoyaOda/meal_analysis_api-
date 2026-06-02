"""Tests for the paired BCa bootstrap promote gate and stability verdict."""

from apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval import (
    bootstrap_mean_ci,
    config_fidelity_mismatch,
    gate_decision,
    paired_calorie_deltas,
    sign_flip_pvalue,
)
from apps.freeform_usda_meal_analysis_api.scripts.run_pdca_repeated_eval import (
    stability_verdict,
)

_FAST = 2000


def test_bootstrap_ci_none_for_empty() -> None:
    assert bootstrap_mean_ci([], n_resamples=_FAST) is None


def test_bootstrap_ci_degenerate_for_zero_variance() -> None:
    ci = bootstrap_mean_ci([3.0, 3.0, 3.0, 3.0], n_resamples=_FAST)
    assert ci is not None
    assert ci["method"] == "degenerate"
    assert ci["ci_low"] == ci["ci_high"] == 3.0


def test_bootstrap_ci_all_negative_is_entirely_below_zero() -> None:
    deltas = [-5.0, -4.0, -6.0, -3.0, -5.5, -4.5, -5.0, -6.0, -4.0, -5.0]
    ci = bootstrap_mean_ci(deltas, n_resamples=_FAST)
    assert ci is not None and ci["method"] == "bca"
    assert ci["ci_high"] < 0.0


def test_bootstrap_ci_all_positive_is_entirely_above_zero() -> None:
    deltas = [5.0, 4.0, 6.0, 3.0, 5.5, 4.5, 5.0, 6.0, 4.0, 5.0]
    ci = bootstrap_mean_ci(deltas, n_resamples=_FAST)
    assert ci is not None and ci["ci_low"] > 0.0


def test_bootstrap_ci_straddles_zero_for_symmetric_high_variance() -> None:
    deltas = [-20.0, -15.0, -10.0, 10.0, 15.0, 20.0, -18.0, 18.0, -12.0, 12.0]
    ci = bootstrap_mean_ci(deltas, n_resamples=_FAST)
    assert ci is not None
    assert ci["ci_low"] < 0.0 < ci["ci_high"]


def test_bootstrap_ci_is_deterministic_given_seed() -> None:
    deltas = [-2.0, -3.0, 1.0, -4.0, -1.0, -2.5, -3.5, 0.5]
    a = bootstrap_mean_ci(deltas, n_resamples=_FAST, seed=99)
    b = bootstrap_mean_ci(deltas, n_resamples=_FAST, seed=99)
    assert a == b


def test_paired_calorie_deltas_pairs_only_shared_successes() -> None:
    candidate_rows = [
        {"image": "test_food1.jpg", "success": True, "calorie_abs_percent_error": 8.0},
        {"image": "test_food2.jpg", "success": True, "calorie_abs_percent_error": 12.0},
        {"image": "test_food3.jpg", "success": False},
    ]
    baseline_rows = [
        {"image": "test_food1.jpg", "success": True, "calorie_abs_percent_error": 10.0},
        {"image": "test_food2.jpg", "success": True, "calorie_abs_percent_error": 10.0},
        {"image": "test_food3.jpg", "success": True, "calorie_abs_percent_error": 5.0},
    ]
    deltas, images = paired_calorie_deltas(candidate_rows, baseline_rows)
    assert images == ["test_food1.jpg", "test_food2.jpg"]
    assert deltas == [-2.0, 2.0]


def test_sign_flip_pvalue_small_for_shifted_and_large_for_symmetric() -> None:
    shifted = [-5.0, -4.0, -6.0, -3.0, -5.5, -4.5, -5.0, -6.0, -4.0, -5.0]
    symmetric = [-5.0, 5.0, -4.0, 4.0, -6.0, 6.0, -3.0, 3.0]
    assert sign_flip_pvalue(shifted, n_resamples=_FAST) < 0.05
    assert sign_flip_pvalue(symmetric, n_resamples=_FAST) > 0.5


def _full_summary(mae: float, high30: float = 5.0) -> dict:
    return {
        "calorie_mae_percent": mae,
        "high_error_rate_30_percent": high30,
        "avg_latency_sec": 9.0,
        "avg_cost_usd": 0.005,
        "evaluated_image_count": 50,
        "expected_image_count": 50,
        "coverage_complete": True,
        "all_success": True,
        "failure_count": 0,
    }


def _baseline() -> dict:
    return {
        "calorie_mae_percent": 12.0,
        "high_error_rate_30_percent": 6.0,
        "avg_latency_sec": 10.0,
        "avg_cost_usd": 0.01,
    }


def _paired(ci_low: float, ci_high: float) -> dict:
    return {
        "baseline_candidate": "base",
        "n_paired": 50,
        "mean_delta": (ci_low + ci_high) / 2,
        "ci": {
            "point": (ci_low + ci_high) / 2,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "n": 50,
            "n_resamples": _FAST,
            "alpha": 0.05,
            "method": "bca",
        },
        "sign_flip_pvalue": 0.001,
    }


def test_paired_gate_promotes_when_ci_entirely_below_zero() -> None:
    # MAE only 0.2pt better than baseline (would FAIL the legacy 1.0pt margin),
    # but the paired CI is entirely below zero -> promote.
    decision = gate_decision(
        _full_summary(mae=11.8),
        _baseline(),
        {"max_avg_cost_usd_per_image": 0.05},
        required_image_count=50,
        paired=_paired(ci_low=-2.5, ci_high=-0.4),
    )
    assert decision["decision"] == "promote"
    assert decision["gate_mode"] == "paired"


def test_paired_gate_holds_when_ci_straddles_zero_even_if_mae_lower() -> None:
    # MAE looks much better (would PASS the legacy margin), but the paired CI
    # straddles zero -> not statistically significant -> hold.
    decision = gate_decision(
        _full_summary(mae=9.0),
        _baseline(),
        {"max_avg_cost_usd_per_image": 0.05},
        required_image_count=50,
        paired=_paired(ci_low=-3.0, ci_high=1.5),
    )
    assert decision["decision"] == "hold"
    assert decision["gate_mode"] == "paired"


def _paired_degenerate(n: int = 2) -> dict:
    return {
        "baseline_candidate": "base",
        "n_paired": n,
        "mean_delta": -1.0,
        "ci": {
            "point": -1.0,
            "ci_low": -1.0,
            "ci_high": -1.0,
            "n": n,
            "n_resamples": 0,
            "alpha": 0.05,
            "method": "degenerate",
        },
        "sign_flip_pvalue": None,
    }


def test_paired_requested_but_degenerate_ci_holds_no_silent_fallback() -> None:
    # MAE is 3pt better (would PASS the legacy margin), but a paired test was
    # requested and the CI is degenerate -> HOLD, do not silently downgrade.
    decision = gate_decision(
        _full_summary(mae=9.0),
        _baseline(),
        {"max_avg_cost_usd_per_image": 0.05},
        required_image_count=50,
        paired=_paired_degenerate(),
        paired_requested=True,
    )
    assert decision["decision"] == "hold"
    assert decision["gate_mode"] == "paired_unavailable"


def test_paired_requested_but_none_holds() -> None:
    decision = gate_decision(
        _full_summary(mae=9.0),
        _baseline(),
        {"max_avg_cost_usd_per_image": 0.05},
        required_image_count=50,
        paired=None,
        paired_requested=True,
    )
    assert decision["decision"] == "hold"
    assert decision["gate_mode"] == "paired_unavailable"


def test_paired_requested_with_valid_ci_still_promotes() -> None:
    decision = gate_decision(
        _full_summary(mae=11.8),
        _baseline(),
        {"max_avg_cost_usd_per_image": 0.05},
        required_image_count=50,
        paired=_paired(ci_low=-2.5, ci_high=-0.4),
        paired_requested=True,
    )
    assert decision["decision"] == "promote"
    assert decision["gate_mode"] == "paired"


def test_legacy_gate_unchanged_when_paired_is_none() -> None:
    # No paired data -> legacy fixed 1.0pt margin: 12.0 -> 10.5 is 1.5pt better.
    decision = gate_decision(
        _full_summary(mae=10.5),
        _baseline(),
        {"max_avg_cost_usd_per_image": 0.05},
        required_image_count=50,
    )
    assert decision["decision"] == "promote"
    assert decision["gate_mode"] == "fixed_margin"


def test_config_fidelity_matching_returns_none() -> None:
    candidate = {
        "vlm_model_id": "openrouter:google/gemini-3-flash-preview",
        "prompt_path": "freeform_prompt_v11b.txt",
    }
    payload = {
        "ai_model_used": "google/gemini-3-flash-preview",  # tolerant: provider prefix stripped
        "prompt_file_used": "freeform_prompt_v11b.txt",
    }
    assert config_fidelity_mismatch(candidate, payload) is None


def test_config_fidelity_flags_model_mismatch() -> None:
    candidate = {"vlm_model_id": "openrouter:google/gemini-3-flash-preview"}
    payload = {"ai_model_used": "openai/gpt-5.1"}
    reason = config_fidelity_mismatch(candidate, payload)
    assert reason is not None and "model" in reason


def test_config_fidelity_flags_prompt_file_mismatch() -> None:
    candidate = {
        "vlm_model_id": "openrouter:google/gemini-3-flash-preview",
        "prompt_path": "freeform_prompt_v11b.txt",
    }
    payload = {
        "ai_model_used": "google/gemini-3-flash-preview",
        "prompt_file_used": "freeform_prompt_v7.txt",  # the drift case
    }
    reason = config_fidelity_mismatch(candidate, payload)
    assert reason is not None and "prompt_file" in reason


def test_config_fidelity_skips_prompt_check_for_inline_prompt_text() -> None:
    # An inline prompt_text override has no file name to compare; only model checked.
    candidate = {
        "vlm_model_id": "openrouter:google/gemini-3-flash-preview",
        "prompt_text": "You are an expert food analyst...",
    }
    payload = {
        "ai_model_used": "google/gemini-3-flash-preview",
        "prompt_file_used": "freeform_prompt_v7.txt",
    }
    assert config_fidelity_mismatch(candidate, payload) is None


def test_stability_verdict_stable_and_hold() -> None:
    stable_row = {
        "run_count": 3,
        "success_run_count": 3,
        "mae_mean": 11.0,
        "mae_std": 0.5,
        "high30_mean": 4.0,
        "high30_std": 1.0,
    }
    verdict = stability_verdict(
        stable_row, baseline_mae=12.0, max_mae_std=1.0, max_high30_std=2.0
    )
    assert verdict["decision"] == "stable"

    noisy_row = dict(stable_row, mae_std=2.36)
    verdict = stability_verdict(
        noisy_row, baseline_mae=12.0, max_mae_std=1.0, max_high30_std=2.0
    )
    assert verdict["decision"] == "hold"
    assert any("mae_std" in r for r in verdict["reasons"])
