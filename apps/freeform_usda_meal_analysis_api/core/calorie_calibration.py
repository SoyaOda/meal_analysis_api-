"""Post-hoc calorie calibration layer.

🔴 GLOBAL AFFINE CALIBRATION IS VOID (2026-06-04). The earlier "slope ~0.47,
bias ~-6%, MAE 18.7%->15.0%" came from the frozen-50 set whose GT turned out to be
GPT-5-pro ESTIMATES, not measurements; on independent MEASURED sets the calorie bias
SIGN FLIPS by distribution (N5k over-estimates, NutritionVerse-Real under-estimates),
so a single global (slope, intercept) is unsafe and over-fits one distribution. See
evals/lessons/20260603_frozen50_gt_is_gpt5pro_estimate_two_gate_strategy.md and
20260604_realistic_range_error_decomposition_grams_vs_density.md (realistic-range
error is near-zero-bias VARIANCE, ~50/50 grams vs density).

This module is therefore DISABLED and GUARDED (F1-e): it may only be enabled with a
provenance string containing IN_DOMAIN_MEASURED_MARKER (a fit on real mozu measured
data); enabling with any other provenance RAISES. A future correction should be
CONDITIONAL/hierarchical (food-group x container x size x confidence), applied as a
separate corrected-calorie field — NOT a global factor that scales displayed weights.
corrected_total = slope * raw_total + intercept.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "config" / "calorie_calibration.json"
)

# F1-e: a calibration may only be enabled if its provenance marks an in-domain
# MEASURED fit (real mozu data). Global affine fits on benchmark sets are VOID.
IN_DOMAIN_MEASURED_MARKER = "mozu_measured"


@dataclass(frozen=True)
class CalorieCalibration:
    """Affine calorie calibration: corrected = slope * raw + intercept."""

    enabled: bool = False
    slope: float = 1.0
    intercept: float = 0.0
    # Guard rails so a bad fit cannot produce a pathological scaling.
    min_factor: float = 0.5
    max_factor: float = 2.5
    provenance: str = ""

    def corrected_total(self, raw_calories: float) -> float:
        return self.slope * raw_calories + self.intercept

    def scale_factor(self, raw_calories: float) -> float:
        """Multiplicative factor to apply to nutrition/weights for a consistent response.

        Returns 1.0 (no-op) when disabled or raw is non-positive. The affine map is
        applied as a per-meal factor (= corrected/raw) so per-dish, per-ingredient and
        total all scale together; the factor is clamped to [min_factor, max_factor].
        """
        if not self.enabled or raw_calories <= 0:
            return 1.0
        factor = self.corrected_total(raw_calories) / raw_calories
        if factor < self.min_factor:
            return self.min_factor
        if factor > self.max_factor:
            return self.max_factor
        return factor


def load_calibration(path: Optional[Path] = None) -> CalorieCalibration:
    """Load calibration config; returns a disabled no-op calibration if absent/invalid.

    Fail-soft on a MISSING file (calibration is opt-in), but fail-LOUD on a malformed
    one if it is explicitly enabled (do not silently serve uncalibrated when asked to).
    """
    cfg_path = path or DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        return CalorieCalibration()
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    cal = CalorieCalibration(
        enabled=bool(data.get("enabled", False)),
        slope=float(data.get("slope", 1.0)),
        intercept=float(data.get("intercept", 0.0)),
        min_factor=float(data.get("min_factor", 0.5)),
        max_factor=float(data.get("max_factor", 2.5)),
        provenance=str(data.get("provenance", "")),
    )
    if cal.enabled:
        # F1-e guard: global affine calibration is VOID. Only an in-domain MEASURED
        # fit (real mozu data) may be enabled; refuse loudly otherwise so the old
        # frozen-50 / N5k fits cannot be silently re-enabled.
        if IN_DOMAIN_MEASURED_MARKER not in cal.provenance.lower():
            raise ValueError(
                "Calorie calibration is enabled but its provenance "
                f"({cal.provenance or 'empty'!r}) does not contain "
                f"'{IN_DOMAIN_MEASURED_MARKER}'. Global affine calibration is VOID; "
                "only a fit on in-domain MEASURED mozu data may be enabled. "
                "See core/calorie_calibration.py module docstring."
            )
        logger.info(
            "Calorie calibration ENABLED: corrected = %.4f*raw + %.2f (%s)",
            cal.slope,
            cal.intercept,
            cal.provenance or "no provenance",
        )
    return cal
