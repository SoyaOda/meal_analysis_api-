"""Post-hoc calorie calibration layer.

General VLMs systematically under-estimate meal calories (measured calibration
slope ~0.47, signed bias ~-6%). A held-out-fit affine map corrects the systematic
component: corrected_total = slope * raw_total + intercept. This is the cheapest
lever that removes the directional bias (held-out validation: MAE 18.7%->15.0%,
signed -6.5%->-0.5%). It does NOT fix the weak pred-vs-true correlation (R^2~0.16)
— that needs better portion estimation. Disabled by default; the (slope, intercept)
MUST be fit on data DISJOINT from any benchmark used to judge it (anti-overfit).
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
        logger.info(
            "Calorie calibration ENABLED: corrected = %.4f*raw + %.2f (%s)",
            cal.slope,
            cal.intercept,
            cal.provenance or "no provenance",
        )
    return cal
