import asyncio
from contextlib import contextmanager

import httpx
import pytest
from fastapi import FastAPI
from starlette.routing import Match

from nakshatra import nakshatra_routes


@pytest.mark.parametrize("name", ["Revati", "Purva Phalguni"])
def test_info_url_returns_database_details(monkeypatch, name):
    row = (name, "Mercury", "Deity", "Nature", "Guna", "Description",
           "Characteristics", "Strengths", "Cautions", "Careers", "Compatibility")

    @contextmanager
    def connection():
        yield object()

    class Cursor:
        def fetchone(self):
            return row

    def execute(conn, sql, params):
        assert params == (name,)
        assert "FROM nakshatras" in sql
        return Cursor()

    monkeypatch.setattr(nakshatra_routes, "get_db_connection", connection)
    monkeypatch.setattr(nakshatra_routes, "execute", execute)
    app = FastAPI()
    app.include_router(nakshatra_routes.router, prefix="/api")
    async def request():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.get(f"/api/nakshatra/{name}/info")

    response = asyncio.run(request())
    assert response.status_code == 200
    info = response.json()["nakshatra"]
    assert info["name"] == name
    for field, value in zip(
        ("lord", "deity", "nature", "guna", "description", "characteristics",
         "positive_traits", "negative_traits", "careers", "compatibility"), row[1:]
    ):
        assert info[field] == value


@pytest.mark.parametrize("path,endpoint", [
    ("/nakshatra/Revati/2026", "get_nakshatra_year_data"),
    ("/nakshatra/year/2026", "get_nakshatra_year_by_month"),
])
def test_calendar_urls_still_match(path, endpoint):
    scope = {"type": "http", "path": path, "method": "GET"}
    route = next(route for route in nakshatra_routes.router.routes
                 if route.matches(scope)[0] == Match.FULL)
    assert route.endpoint.__name__ == endpoint
