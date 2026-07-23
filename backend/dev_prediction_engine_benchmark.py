#!/usr/bin/env python3
"""Repeatable local benchmark for the deterministic Parashari engine."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from time import perf_counter

from prediction_engine import PredictionRequest, PredictionService
from prediction_engine.contracts import BirthChartInput


FIXTURE = (
    Path(__file__).resolve().parent
    / "tests"
    / "fixtures"
    / "parashari_prediction_calibration.json"
)


def main() -> None:
    fixture = json.loads(FIXTURE.read_text())
    service = PredictionService()
    suite_started = perf_counter()
    for case in fixture["cases"]:
        request = PredictionRequest(
            birth=BirthChartInput.from_mapping(case["birth"]),
            as_of=date.fromisoformat(fixture["as_of"]),
            horizon_days=int(fixture["horizon_days"]),
            trace=True,
        )
        started = perf_counter()
        result = service.generate(request)
        duration_ms = (perf_counter() - started) * 1000.0
        print(
            f"{case['key']} duration_ms={duration_ms:.1f} "
            f"windows={result.diagnostics['windows']} "
            f"eligible_activation_windows={result.diagnostics['eligible_activation_windows']} "
            f"final={len(result.candidates)}"
        )
    print(f"suite_duration_ms={(perf_counter() - suite_started) * 1000.0:.1f}")


if __name__ == "__main__":
    main()
