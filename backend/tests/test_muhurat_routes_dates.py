import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from types import SimpleNamespace

import muhurat_routes
from muhurat_routes import GeneralMuhuratRequest, _parse_calendar_date, _process_muhurat


@pytest.mark.parametrize(
    "raw",
    [
        "1981-03-22",
        "1981-03-22T00:00:00.000Z",
        "1981-03-22T12:30:00+05:30",
        "1981-03-22 00:00:00",
    ],
)
def test_parse_calendar_date_accepts_current_and_legacy_birth_dates(raw):
    parsed = _parse_calendar_date(raw)
    assert (parsed.year, parsed.month, parsed.day) == (1981, 3, 22)


@pytest.mark.parametrize("raw", ["", "22-03-1981", "not-a-date"])
def test_parse_calendar_date_rejects_invalid_values(raw):
    with pytest.raises(ValueError, match="Birth date must be"):
        _parse_calendar_date(raw)


@pytest.mark.asyncio
async def test_process_muhurat_normalizes_legacy_iso_date_for_calculator(monkeypatch):
    monkeypatch.setattr(muhurat_routes.credit_service, "get_credit_setting", lambda _key: 5)
    monkeypatch.setattr(muhurat_routes.credit_service, "get_effective_cost", lambda *_args: 5)
    monkeypatch.setattr(muhurat_routes.credit_service, "get_user_credits", lambda _userid: 50)
    monkeypatch.setattr(muhurat_routes, "parse_timezone_offset", lambda *_args: 5.5)
    monkeypatch.setattr(muhurat_routes.swe, "julday", lambda *_args: 1.0)
    monkeypatch.setattr(muhurat_routes.swe, "set_sid_mode", lambda *_args: None)
    monkeypatch.setattr(muhurat_routes.swe, "calc_ut", lambda *_args: ((10.0,),))

    seen = {}

    def calculate(*_args, **kwargs):
        seen["birth_data"] = kwargs["birth_data"]
        return {"recommendations": []}

    request = GeneralMuhuratRequest(
        start_date="2026-08-13",
        end_date="2026-08-14",
        latitude=29.15,
        longitude=75.72,
        user_dob="1981-03-22T00:00:00.000Z",
        user_time="05:06:00",
        user_lat=28.61,
        user_lon=77.20,
    )

    result = await _process_muhurat(
        request,
        SimpleNamespace(userid=42),
        "vehicle_purchase",
        calculate,
    )

    assert result["status"] == "success"
    assert seen["birth_data"]["date"] == "1981-03-22"
