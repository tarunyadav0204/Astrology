from nudge_engine.moon_tara_daily import _tara
from nudge_engine.trigger_registry import TRIGGERS


def test_navataara_cycle_uses_janma_nakshatra_as_the_first_tara():
    assert _tara(4, 4)["name"] == "Janma Tara"
    assert _tara(4, 10)["name"] == "Naidhana Tara"
    # The ninth Tara restarts the cycle at the next group of nine nakshatras.
    assert _tara(4, 13)["name"] == "Janma Tara"


def test_generic_moon_notification_is_not_fanned_out_by_daily_scan():
    assert "moon_nakshatra" not in TRIGGERS
