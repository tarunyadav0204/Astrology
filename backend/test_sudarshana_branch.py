from ai.parallel_chat.context_slices import build_sudarshan_branch_payload
from calculators.sudarshana_chakra_calculator import SudarshanaChakraCalculator
from calculators.sudarshana_dasha_calculator import SudarshanaDashaCalculator


def _chart_data():
    return {
        "ascendant": 15.0,
        "planets": {
            "Sun": {"longitude": 25.0},
            "Moon": {"longitude": 65.0},
            "Mars": {"longitude": 105.0},
            "Mercury": {"longitude": 145.0},
            "Jupiter": {"longitude": 185.0},
            "Venus": {"longitude": 225.0},
            "Saturn": {"longitude": 265.0},
            "Rahu": {"longitude": 305.0},
            "Ketu": {"longitude": 125.0},
        },
    }


def _context():
    return {
        "birth_details": {"date": "1980-04-02", "time": "14:55"},
        "ascendant_info": {"sign_number": 1},
        "current_date_info": {"current_date": "2026-04-22"},
        "response_format": {"mode": "chat"},
        "intent": {"category": "career"},
        "current_dashas": {
            "mahadasha": {"planet": "Saturn", "start_date": "2015-01-01", "end_date": "2034-01-01"},
            "antardasha": {"planet": "Mercury", "start_date": "2026-01-01", "end_date": "2028-01-01"},
            "pratyantar": {"planet": "Jupiter", "start_date": "2026-04-01", "end_date": "2026-08-01"},
        },
        "sudarshana_chakra": SudarshanaChakraCalculator(_chart_data()).get_sudarshana_view(),
        "sudarshana_dasha": {
            "active_house": 10,
            "year_focus": "Career & Status",
            "precision_triggers": [
                {
                    "date": "2026-10-31",
                    "planet": "Jupiter",
                    "sign": "Libra",
                    "confirmation": "Triple confirmation",
                    "confidence": "very_high",
                    "intensity": "Very High",
                    "perspectives": ["Lagna", "Moon", "Sun"],
                }
            ],
        },
    }


def test_sudarshana_chakra_synthesis_exposes_house_agreement():
    calc = SudarshanaChakraCalculator(_chart_data())
    out = calc.get_sudarshana_view()

    synthesis = out["synthesis"]
    assert "house_agreement" in synthesis
    assert "dominant_houses" in synthesis
    assert isinstance(synthesis["house_agreement"], list) and synthesis["house_agreement"]
    assert isinstance(synthesis["dominant_houses"], list) and synthesis["dominant_houses"]


def test_sudarshana_dasha_merge_no_longer_claims_guaranteed_event():
    calc = SudarshanaDashaCalculator(_chart_data(), {"date": "1980-04-02"})
    merged = calc._merge_triggers(
        [{"planet": "Jupiter", "date": "2026-10-31", "perspective": "Lagna"}],
        [{"planet": "Jupiter", "date": "2026-11-02", "perspective": "Moon"}],
        [{"planet": "Jupiter", "date": "2026-11-04", "perspective": "Sun"}],
    )

    assert merged[0]["confirmation"] == "Triple confirmation"
    assert merged[0]["confidence"] == "very_high"
    assert "Guaranteed" not in merged[0]["confirmation"]


def test_sudarshana_branch_payload_exposes_reasoning_spine_and_dasha_anchor():
    payload = build_sudarshan_branch_payload(_context(), "How is career this year?")

    assert "sx" in payload
    sx = payload["sx"]
    assert sx["cat"] == "career"
    assert sx["hs"] == [10, 6, 2, 11]
    assert sx["topic"]["rows"]
    assert sx["dom"]
    assert sx["triggers"]["rows"]
    assert sx["D"]["md"]["p"] == "Saturn"
    assert sx["D"]["ad"]["p"] == "Mercury"
    assert sx["career"]["rows"]
    assert sx["relationship"]["rows"]
    assert sx["education"]["rows"]
    assert sx["health"]["rows"]
    assert sx["career"]["hs"] == [10, 6, 2, 11]
    assert sx["relationship"]["hs"] == [7, 5, 2, 11]
    assert sx["current"]["topic"]["rows"]
    assert sx["current"]["career"]["rows"]
    assert sx["current"]["relationship"]["rows"]
    assert sx["current"]["topic"]["rows"][0]["lvl"] in {"md", "ad", "pd"}
    assert sx["current"]["career"]["rows"][0]["p"]
