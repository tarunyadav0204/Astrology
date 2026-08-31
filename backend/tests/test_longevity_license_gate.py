import asyncio

import pytest
from fastapi import HTTPException

from auth import User
from longevity.routes import LongevityRequest, calculate_longevity


def test_longevity_route_requires_astrologer_entitlement(monkeypatch):
    checked = {}

    def reject_unlicensed(user, entitlement):
        checked["user"] = user.userid
        checked["entitlement"] = entitlement
        raise HTTPException(status_code=403, detail={"code": "ASTROLOGER_LICENSE_REQUIRED"})

    monkeypatch.setattr("longevity.routes.require_entitlement", reject_unlicensed)
    request = LongevityRequest(
        birth_data={"name": "Gate test"},
        chart_data={"ascendant": 0, "planets": {}},
    )
    user = User(userid=42, name="Tester", phone="000", role="user")

    with pytest.raises(HTTPException) as raised:
        asyncio.run(calculate_longevity(request, user))

    assert raised.value.status_code == 403
    assert raised.value.detail["code"] == "ASTROLOGER_LICENSE_REQUIRED"
    assert checked == {"user": 42, "entitlement": "astrologer_tools"}
