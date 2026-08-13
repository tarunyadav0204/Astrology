import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from calculators.muhurat_calculator import MuhuratCalculator


@pytest.mark.parametrize(
    ("name", "method_name", "extra_kwargs"),
    [
        ("childbirth", "calculate_childbirth_muhurat", {}),
        (
            "vehicle",
            "calculate_vehicle_muhurat",
            {
                "birth_data": {
                    "date": "1981-03-22",
                    "time": "16:30",
                    "latitude": 28.61,
                    "longitude": 77.20,
                    "timezone": "Asia/Kolkata",
                }
            },
        ),
        ("griha", "calculate_griha_pravesh_muhurat", {}),
        ("gold", "calculate_gold_muhurat", {}),
        ("business", "calculate_business_muhurat", {}),
    ],
)
def test_all_muhurat_planners_can_score_accepted_slots(name, method_name, extra_kwargs):
    calculator = MuhuratCalculator()
    method = getattr(calculator, method_name)

    result = method(
        "2026-08-13",
        "2026-09-12",
        29.15,
        75.72,
        5,
        "Asia/Kolkata",
        **extra_kwargs,
    )

    assert result.get("error") is None, name
    assert result["recommendations"], name
    for day in result["recommendations"]:
        for slot in day["slots"]:
            assert isinstance(slot["score"], int)
            assert slot["rationale"]


def test_childbirth_slot_does_not_use_vehicle_language():
    result = MuhuratCalculator().calculate_childbirth_muhurat(
        "2026-08-13",
        "2026-09-12",
        29.15,
        75.72,
        5,
        "Asia/Kolkata",
    )

    rationales = [
        slot["rationale"]
        for day in result["recommendations"]
        for slot in day["slots"]
    ]
    assert rationales
    assert all("vehicle" not in rationale.lower() for rationale in rationales)
    assert all("Childbirth" in rationale for rationale in rationales)
