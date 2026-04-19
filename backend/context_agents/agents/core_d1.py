"""
Agent `core_d1`: compact sidereal D1 + name/date/time + lagna + planets + house lordships.

Does NOT compute divisionals, dasha, transits, nakshatra names, yogas, or KP.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List

from calculators.chart_calculator import ChartCalculator
from context_agents.base import AgentContext, ContextAgent
from context_agents.compact_vedic import (
    PLANET_ORDER,
    house_lordships_from_ascendant,
    sign_1_12_from_lon,
    sign_name_from_1_12,
    sign_name_from_index_0,
)


class CoreD1Agent(ContextAgent):
    agent_id = "core_d1"
    schema_version = 3

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        birth = ctx.birth_data or {}
        birth_obj = SimpleNamespace(**birth)

        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)

        asc_deg = float(chart_data.get("ascendant", 0.0))
        asc_sign_0 = int(asc_deg / 30.0) % 12
        lagna_sign_1_12 = asc_sign_0 + 1
        lagna_deg_in_sign = asc_deg % 30.0

        planets = chart_data.get("planets") or {}
        rows: List[List[Any]] = []
        for name in PLANET_ORDER:
            pdata = planets.get(name)
            if not isinstance(pdata, dict):
                continue
            lon = float(pdata.get("longitude", 0.0))
            h = int(pdata.get("house", 0) or 0)
            if "sign" in pdata and pdata.get("sign") is not None:
                s_12 = (int(pdata["sign"]) % 12) + 1
            else:
                s_12 = sign_1_12_from_lon(lon)
            if h < 1 or h > 12:
                p_sign0 = int(lon / 30.0) % 12
                h = (p_sign0 - asc_sign_0) % 12 + 1
            snm = str(pdata.get("sign_name") or "").strip() or sign_name_from_1_12(s_12)
            rows.append([name, round(lon, 4), s_12, snm, h])

        # Identity + clock only in payload (lat/lon/place/tz still read from `birth` for calculation).
        b_compact: Dict[str, Any] = {
            "n": birth.get("name") or "",
            "d": birth.get("date") or "",
            "t": birth.get("time") or "",
        }

        return {
            "a": self.agent_id,
            "v": self.schema_version,
            "b": b_compact,
            "L": {
                "s": lagna_sign_1_12,
                "d": round(lagna_deg_in_sign, 4),
                "nm": sign_name_from_index_0(asc_sign_0),
            },
            "P": rows,
            "H": house_lordships_from_ascendant(asc_sign_0),
        }


if __name__ == "__main__":
    import json

    demo = {
        "name": "Test User",
        "date": "1980-04-02",
        "time": "14:55",
        "latitude": 29.1492,
        "longitude": 75.7217,
        "timezone": "Asia/Kolkata",
        "place": "Test",
    }
    out = CoreD1Agent().build(AgentContext(birth_data=demo, user_question="demo"))
    print(json.dumps(out, indent=2))
