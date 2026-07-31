"""Compatibility facade for the canonical Panchang engine.

New code should import ``panchang.panchang_calculator.PanchangCalculator``.
This module remains temporarily so older report/chat modules retain their
public method signatures while the migration is completed.
"""

import warnings

from panchang.panchang_calculator import PanchangCalculator as _CanonicalPanchang


class PanchangCalculator(_CanonicalPanchang):
    """Backward-compatible facade delegating every calculation to the canonical engine."""

    def __init__(self):
        warnings.warn(
            "calculators.panchang_calculator is deprecated; import from panchang.panchang_calculator",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__()

    def calculate_panchang(self, date_str, time_str="12:00:00", latitude=0.0, longitude=0.0, timezone=None, **kwargs):
        """Preserve the legacy positional signature while using canonical modes."""
        reference = kwargs.pop("reference", None)
        if kwargs:
            raise TypeError(f"Unexpected Panchang arguments: {', '.join(kwargs)}")
        return super().calculate_panchang(
            date_str,
            latitude,
            longitude,
            timezone,
            time_str=time_str,
            reference=reference or "moment",
        )
